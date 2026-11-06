#!/usr/bin/env python3
"""Independent discrete WDT counter; NOT the 8.5 software command watchdog.
Ideal synthetic 1-ms ticks, nominal 16-tick deadline, 5-tick progress/kick cadence.
Only first reset is recorded (stop, not a simulated reboot). Timer ISR can run
while main logic is stuck; an ISR kick then hides that hang. Real oscillator
variation, boot/fuse setup and CPU cycle timing are not simulated.
Generic window extension is NOT an ATmega328P hardware feature claim.
"""
TIMEOUT, DURATION, WDRF = 16,100,0x08
ARMS=("no_kick","main_loop","isr_timer")
# Opened ATmega328P 7810D Table 10-3: WDP3..0, oscillator cycles, typical ms at5V.
PRESCALE=((0,2048,16),(1,4096,32),(2,8192,64),(3,16384,125),
          (4,32768,250),(5,65536,500),(6,131072,1000),(7,262144,2000),
          (8,524288,4000),(9,1048576,8000))


def run(arm, hang_at=None, kick_period=5, window_min=None):
    if arm not in ARMS:
        raise ValueError("unknown kick source")
    last_kick=progress=0
    reset_at,reason=None,"none"
    for now in range(1,DURATION+1):
        # Expiration wins a tie: a kick at the upper deadline is too late here.
        if now-last_kick>=TIMEOUT:
            reset_at,reason=now,"timeout"
            break
        running=hang_at is None or now<hang_at
        progress+=int(running)
        kick=now%kick_period==0 and (arm=="isr_timer" or (arm=="main_loop" and running))
        if kick:
            if window_min is not None and now-last_kick<window_min:
                reset_at,reason=now,"window_early"
                break
            last_kick=now
    # Snapshot models early boot read of WDRF only; generic window has no AVR flag.
    saved_mcusr=WDRF if reset_at is not None and window_min is None else 0
    cleared_mcusr=0
    hidden=hang_at is not None and reset_at is None
    return dict(reset_at=reset_at,reason=reason,progress=progress,hidden=hidden,
                saved_mcusr=saved_mcusr,cleared_mcusr=cleared_mcusr)


def main():
    print("Independent HW WDT surrogate; ideal tick=1ms nominal timeout=16 ticks duration=100")
    print("same hang at30 or no hang; kick cadence5; expire-before-kick tie; first reset stops run")
    print("scenario arm reset_tick cause main_progress saved_MCUSR cleared_MCUSR hidden_hang")
    for scenario,hang in (("healthy",None),("main_hang",30)):
        for arm in ARMS:
            r=run(arm,hang)
            when="none" if r["reset_at"] is None else str(r["reset_at"])
            print(f"{scenario} {arm} {when} {r['reason']} {r['progress']} 0x{r['saved_mcusr']:02X} 0x{r['cleared_mcusr']:02X} {int(r['hidden'])}")
    print("Opened 7810D Table10-3: WDP3..0 cycles typical_ms_at5V (not precision deadlines)")
    for code,cycles,ms in PRESCALE:
        print(f"{code:04b} {cycles} {ms}")
    print("generic window model ONLY: min_age=8 upper=16; NOT ATmega328P window hardware")
    for label,period,hang in (("too_early",5,None),("in_window",10,None),("hung",10,30)):
        r=run("main_loop",hang,period,8)
        when="none" if r["reset_at"] is None else str(r["reset_at"])
        print(f"{label} period={period} reset={when} cause={r['reason']}")
    print("WDE reset mode / WDIE interrupt-only differ; capture MCUSR.WDRF before clearing")
    print("Synthetic timing; no certification or e-stop claim; AVR fuse/reset lab: 本页未运行")


if __name__=="__main__":
    main()
