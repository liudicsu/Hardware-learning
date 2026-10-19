// avrrun: run an ATmega328P ELF in simavr, inject pin/ADC events, print UART output.
// usage: avrrun <elf> <end_ms> [events...]  event = <ms>:<port><bit>=<0|1>  or  <ms>:A<n>=<mV>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <simavr/sim_avr.h>
#include <simavr/sim_elf.h>
#include <simavr/avr_ioport.h>
#include <simavr/avr_adc.h>
#include <simavr/avr_uart.h>
#include <simavr/avr_twi.h>
#include <math.h>

typedef struct { double ms; char kind; char port; int bit; int val; int done; } ev_t;
static avr_t *g_avr;
static void pin_watch(struct avr_irq_t *irq, uint32_t value, void *param) { fprintf(stderr, "[%.1f ms] %s=%u\n", g_avr->cycle / 16000.0, (char*)param, value); }
static void uart_out(struct avr_irq_t *irq, uint32_t value, void *param) { putchar((int)value); fflush(stdout); }

// Optional fake MPU-6050 on I2C address 0x68 (MPU=1). The board is held flat, tilted to +30 deg
// between t = 3 s and 4 s, held, and laid flat again between 7 s and 8 s. The gyro has a +1.5 deg/s bias.
static avr_irq_t *mpu_irq; static int mpu_sel = 0, mpu_wcount = 0; static uint8_t mpu_reg = 0, mpu_pwr = 0x40;
static uint32_t rng_state = 12345;
static double gauss(void) {                      // deterministic pseudo-random normal noise
  double u1, u2; rng_state = rng_state * 1103515245u + 12345u; u1 = ((rng_state >> 8) + 1.0) / 16777217.0;
  rng_state = rng_state * 1103515245u + 12345u; u2 = ((rng_state >> 8) + 1.0) / 16777217.0;
  return sqrt(-2 * log(u1)) * cos(2 * M_PI * u2);
}
static double pitch_at(double t) {
  if (t < 3) return 0; if (t < 4) return 30 * (t - 3); if (t < 7) return 30; if (t < 8) return 30 * (8 - t); return 0;
}
static int16_t sat16(double v) { return v > 32767 ? 32767 : v < -32768 ? -32768 : (int16_t)lround(v); }
static uint8_t mpu_byte(uint8_t reg) {
  static int16_t snap[7];
  double t = g_avr->cycle / 16e6;
  if (reg == 0x75) return 0x68;
  if (reg == 0x6B) return mpu_pwr;
  if (reg == 0x3B) {                             // a burst read starts here: sample all axes at once
    double th = pitch_at(t) * M_PI / 180, rate = (pitch_at(t + 0.0005) - pitch_at(t - 0.0005)) / 0.001;
    int awake = !(mpu_pwr & 0x40);
    snap[0] = awake ? sat16(16384 * (sin(th) + 0.02 * gauss())) : 0;
    snap[1] = awake ? sat16(16384 * 0.02 * gauss()) : 0;
    snap[2] = awake ? sat16(16384 * (cos(th) + 0.02 * gauss())) : 0;
    snap[3] = awake ? sat16((36.53 + 25) * 340 - 521) : 0;  // about 25 C
    snap[4] = awake ? sat16(131 * (0.3 * gauss())) : 0;
    snap[5] = awake ? sat16(131 * (rate + 1.5 + 0.3 * gauss())) : 0;
    snap[6] = awake ? sat16(131 * (0.3 * gauss())) : 0;
  }
  if (reg >= 0x3B && reg <= 0x48) { int i = (reg - 0x3B) / 2; return (reg - 0x3B) % 2 == 0 ? (uint8_t)(snap[i] >> 8) : (uint8_t)(snap[i] & 0xFF); }
  return 0;
}
static void mpu_hook(struct avr_irq_t *irq, uint32_t value, void *param) {
  avr_twi_msg_irq_t v; v.u.v = value;
  if (v.u.twi.msg & TWI_COND_STOP) mpu_sel = 0;
  if (v.u.twi.msg & TWI_COND_START) {
    mpu_sel = 0;
    if ((v.u.twi.addr >> 1) == 0x68) { mpu_sel = v.u.twi.addr; mpu_wcount = 0;
      avr_raise_irq(mpu_irq + TWI_IRQ_INPUT, avr_twi_irq_msg(TWI_COND_ACK, mpu_sel, 1)); }
  }
  if (mpu_sel) {
    if (v.u.twi.msg & TWI_COND_WRITE) {
      avr_raise_irq(mpu_irq + TWI_IRQ_INPUT, avr_twi_irq_msg(TWI_COND_ACK, mpu_sel, 1));
      if (mpu_wcount++ == 0) mpu_reg = v.u.twi.data;
      else { if (mpu_reg == 0x6B) mpu_pwr = v.u.twi.data; mpu_reg++; }
    }
    if (v.u.twi.msg & TWI_COND_READ) {
      uint8_t d = mpu_byte(mpu_reg++);
      avr_raise_irq(mpu_irq + TWI_IRQ_INPUT, avr_twi_irq_msg(TWI_COND_READ, mpu_sel, d));
    }
  }
}

// Optional motor+encoder model (MOTOR=<battery volts>): TB6612 on PWMA=D5, AIN1=D7, AIN2=D8; encoder A=D2, B=D3.
static int ain1 = 0, ain2 = 0;
static void on_ain1(struct avr_irq_t *irq, uint32_t v, void *p) { ain1 = v; }
static void on_ain2(struct avr_irq_t *irq, uint32_t v, void *p) { ain2 = v; }
int main(int argc, char **argv) {
  if (argc < 3) { fprintf(stderr, "usage\n"); return 1; }
  elf_firmware_t fw = {0};
  if (elf_read_firmware(argv[1], &fw)) { fprintf(stderr, "elf\n"); return 1; }
  avr_t *avr = avr_make_mcu_by_name("atmega328p");
  avr_init(avr); avr->frequency = 16000000; avr->log = 0; avr->vcc = 5000; avr->avcc = 5000; avr->aref = 5000;
  avr_load_firmware(avr, &fw);
  uint32_t f = 0; avr_ioctl(avr, AVR_IOCTL_UART_GET_FLAGS('0'), &f);
  f &= ~AVR_UART_FLAG_STDIO; avr_ioctl(avr, AVR_IOCTL_UART_SET_FLAGS('0'), &f);
  avr_irq_register_notify(avr_io_getirq(avr, AVR_IOCTL_UART_GETIRQ('0'), UART_IRQ_OUTPUT), uart_out, NULL);
  g_avr = avr;
  char *w = getenv("WATCH");  // e.g. "B5,D3"
  if (w) { char *tok = strtok(strdup(w), ","); while (tok) { avr_irq_register_notify(avr_io_getirq(avr, AVR_IOCTL_IOPORT_GETIRQ(tok[0]), tok[1]-'0'), pin_watch, strdup(tok)); tok = strtok(NULL, ","); } }
  double end = atof(argv[2]);
  int n = argc - 3; ev_t *ev = calloc(n + 1, sizeof(ev_t));
  for (int i = 0; i < n; i++) {
    char *s = argv[3 + i]; char *c = strchr(s, ':'); *c = 0; ev[i].ms = atof(s); c++;
    if (c[0] == 'A') { ev[i].kind = 'A'; ev[i].bit = c[1] - '0'; ev[i].val = atoi(strchr(c, '=') + 1); }
    else { ev[i].kind = 'P'; ev[i].port = c[0]; ev[i].bit = c[1] - '0'; ev[i].val = atoi(strchr(c, '=') + 1); }
  }
  if (getenv("MPU")) {
    static const char *names[2] = {"mpu.in", "mpu.out"};
    mpu_irq = avr_alloc_irq(&avr->irq_pool, 0, 2, names);
    avr_irq_register_notify(mpu_irq + TWI_IRQ_OUTPUT, mpu_hook, NULL);
    avr_connect_irq(mpu_irq + TWI_IRQ_INPUT, avr_io_getirq(avr, AVR_IOCTL_TWI_GETIRQ(0), TWI_IRQ_INPUT));
    avr_connect_irq(avr_io_getirq(avr, AVR_IOCTL_TWI_GETIRQ(0), TWI_IRQ_OUTPUT), mpu_irq + TWI_IRQ_OUTPUT);
  }
  char *motor = getenv("MOTOR");
  double batt = motor ? atof(motor) : 0, speed = 0, pos = 0; long quad = 0; double last_t = 0;
  if (motor) {
    avr_irq_register_notify(avr_io_getirq(avr, AVR_IOCTL_IOPORT_GETIRQ('D'), 7), on_ain1, NULL);
    avr_irq_register_notify(avr_io_getirq(avr, AVR_IOCTL_IOPORT_GETIRQ('B'), 0), on_ain2, NULL);
    avr_ioport_external_t ext0 = { .name = 'D', .mask = 0x0C, .value = 0 };   // encoder starts at phase 00
    avr_ioctl(avr, AVR_IOCTL_IOPORT_SET_EXTERNAL('D'), &ext0);
    avr_raise_irq(avr_io_getirq(avr, AVR_IOCTL_IOPORT_GETIRQ('D'), 2), 0);
    avr_raise_irq(avr_io_getirq(avr, AVR_IOCTL_IOPORT_GETIRQ('D'), 3), 0);
  }
  int state = cpu_Running;
  while (state != cpu_Done && state != cpu_Crashed) {
    double now = avr->cycle / 16000.0;
    if (now >= end) break;
    for (int i = 0; i < n; i++) if (!ev[i].done && now >= ev[i].ms) {
      ev[i].done = 1;
      if (ev[i].kind == 'A') avr_raise_irq(avr_io_getirq(avr, AVR_IOCTL_ADC_GETIRQ, ADC_IRQ_ADC0 + ev[i].bit), ev[i].val);
      else avr_raise_irq(avr_io_getirq(avr, AVR_IOCTL_IOPORT_GETIRQ(ev[i].port), ev[i].bit), ev[i].val);
    }
    if (motor && now - last_t >= 0.05) {   // update the model every 50 us of simulated time
      double dt = (now - last_t) / 1000.0; last_t = now;
      int com0b1 = avr->data[0x44] & (1 << 5);
      double duty = com0b1 ? avr->data[0x48] / 255.0 : ((avr->data[0x2B] >> 5) & 1);
      double dir = (ain1 && !ain2) ? 1 : (ain2 && !ain1) ? -1 : 0;
      double volts = dir * duty * batt;
      double drive = (volts > -0.8 && volts < 0.8) ? 0 : volts;
      double tau = (ain1 && ain2) ? 0.01 : 0.05;   // TB6612 short brake (IN1 = IN2 = HIGH) stops faster than coasting
      if (ain1 && ain2) drive = 0;
      speed += (260.0 * drive - speed) * dt / tau;
      pos += speed * dt;
      long target = (long)(pos >= 0 ? pos + 0.5 : pos - 0.5);
      while (quad != target) {                 // emit quadrature edges: forward 00->10->11->01->00
        quad += (target > quad) ? 1 : -1;
        static const int A[4] = {0, 1, 1, 0}, B[4] = {0, 0, 1, 1};
        int ph = (int)(((quad % 4) + 4) % 4);
        avr_raise_irq(avr_io_getirq(avr, AVR_IOCTL_IOPORT_GETIRQ('D'), 2), A[ph]);
        avr_ioport_external_t ext = { .name = 'D', .mask = 0x0C, .value = (A[ph] << 2) | (B[ph] << 3) };
        avr_ioctl(avr, AVR_IOCTL_IOPORT_SET_EXTERNAL('D'), &ext);   // keep the pull-up from overriding us
        avr_raise_irq(avr_io_getirq(avr, AVR_IOCTL_IOPORT_GETIRQ('D'), 3), B[ph]);
      }
    }
    state = avr_run(avr);
  }
  if (motor) fprintf(stderr, "[model] final wheel position = %ld counts\n", quad);
  return 0;
}
