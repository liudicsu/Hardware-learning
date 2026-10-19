#include <stdio.h>
#include <stdint.h>
int main(void) {
  uint32_t last = 4294967000u;   // 296 ms before millis() wraps
  uint32_t now  = 200u;          // 200 ms after the wrap
  printf("now - last  = %lu ms\n", (unsigned long)(uint32_t)(now - last));
  printf("now > last + 250 ? %s\n", (now > last + 250u) ? "yes" : "no");
  printf("wrap after  = %.1f days\n", 4294967296.0 / 1000 / 60 / 60 / 24);
  return 0;
}
