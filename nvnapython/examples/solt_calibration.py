#! /usr/bin/python3
##-------------------------------------------------------------------------------\
#   nanoVNA_python (nvnapython)
#   './examples/solt_calibration.py'
#   Walk through a SOLT (Short-Open-Load-Thru) calibration interactively. Prompts
#   you to attach each standard, sends the cal step, finalizes, and optionally
#   saves to a preset slot. This is the workflow that makes measurements trusted.
#       python examples/solt_calibration.py
#       python examples/solt_calibration.py --start 1e6 --stop 900e6 --points 201
#
#   WARNING: this DOES change device calibration state. 'cal reset' is sent first;
#   by default the result is saved to preset slot 0. Attach the thru cable between
#   BOTH ports for the thru step. Requires only the library.
#
#   The sweep is resumed BEFORE the save, and 'save' is sent LAST as a
#   fire-and-forget command: the NanoVNA writes the preset to flash but does NOT
#   acknowledge it over serial, so the script does not wait for a reply. To
#   confirm a save persisted, power-cycle, reconnect, and recall the slot.
#
##-------------------------------------------------------------------------------\

import sys
import os
import argparse

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from nvnapython import nanoVNA          # noqa: E402


def _txt(raw):
    return bytes(raw).decode("utf-8", errors="replace").strip() if raw else ""


def _looks_like_error(raw):
    s = _txt(raw).lower()
    return (raw == bytearray(b"ERROR")) or ("error" in s) or ("usage" in s)


def _prompt_continue(message, auto):
    """Pause for the operator to attach a standard. In --auto mode, skip the
    pause (useful for a dry structural run, though the cal won't be valid)."""
    if auto:
        print(f"   [auto] {message} (not pausing)")
        return True
    try:
        input(f"   >>> {message}, then press Enter (or Ctrl-C to abort)... ")
        return True
    except (KeyboardInterrupt, EOFError):
        print("\n   aborted by operator.")
        return False


def _step(nvna, action, describe, prompt, auto):
    """Prompt, then send one cal step, reporting the device's response."""
    if prompt is not None:
        if not _prompt_continue(prompt, auto):
            return False
    resp = nvna.cal(action)           # e.g. nvna.cal('short')
    if _looks_like_error(resp):
        print(f"   ! device rejected 'cal {action}': {_txt(resp)!r}")
        return False
    print(f"   cal {action}: ok {('(' + _txt(resp) + ')') if _txt(resp) else ''}")
    return True


def main():
    ap = argparse.ArgumentParser(description="Interactive SOLT calibration.")
    ap.add_argument("--port", default=None, help="serial port. Omit to autoconnect.")
    ap.add_argument("--start", type=float, default=None,
                    help="optional sweep start Hz (set the cal range). Omit to keep current.")
    ap.add_argument("--stop", type=float, default=None, help="optional sweep stop Hz")
    ap.add_argument("--points", type=int, default=None, help="optional sweep points")
    ap.add_argument("--slot", type=int, default=0, help="preset slot to save into (default 0)")
    ap.add_argument("--no-save", action="store_true", help="do not persist the calibration")
    ap.add_argument("--auto", action="store_true",
                    help="don't pause for standards (STRUCTURAL DRY RUN ONLY; "
                         "the resulting calibration will NOT be valid)")
    args = ap.parse_args()

    nvna = nanoVNA()
    nvna.set_verbose(True)
    nvna.set_error_byte_return(True)

    if args.port:
        connected = nvna.connect(args.port)
    else:
        _found, connected = nvna.autoconnect()
    if not connected:
        print("ERROR: no NanoVNA connected. Pass --port, free the port, or replug.")
        return 1

    # 'cal done' computes error terms across every sweep point and 'save' writes
    # to flash -- both can take longer than the default serial read timeout, so
    # the read of their acknowledgement may otherwise time out. Give the device
    # generous time to respond to these heavier operations.
    nvna.set_serial_timeout(20.0)

    if args.auto:
        print("\n*** --auto: NOT pausing for standards. This is a structural dry run; "
              "the calibration produced will NOT be valid for measurements. ***\n")

    try:
        # optionally set the sweep range the calibration will cover
        if args.start is not None and args.stop is not None:
            pts = args.points if args.points is not None else 201
            print(f"setting sweep to {args.start:.0f}..{args.stop:.0f} Hz, {pts} points")
            nvna.run_sweep(int(args.start), int(args.stop), pts)
        else:
            print("using the device's current sweep range:", _txt(nvna.get_sweep_params()))

        print("\nStarting SOLT calibration.\n")

        # 1) clear any existing calibration terms
        if not _step(nvna, "reset", "clear old cal", None, args.auto):
            return 1

        # 2) the SOLT standards, each preceded by an operator prompt
        steps = [
            ("short", "attach the SHORT standard to PORT 1"),
            ("open",  "attach the OPEN standard to PORT 1"),
            ("load",  "attach the LOAD (50 ohm) standard to PORT 1"),
            ("thru",  "connect the THRU cable between PORT 1 and PORT 2"),
        ]
        for action, prompt in steps:
            if not _step(nvna, action, action, prompt, args.auto):
                print("calibration aborted; device cal state may be partial. "
                      "Re-run to start over (it sends 'cal reset' first).")
                return 1

        # 3) finalize -- compute and apply the error terms
        if not _step(nvna, "done", "finalize", None, args.auto):
            return 1
        print("\ncalibration computed and applied.")

        # 4) resume the live sweep NOW, while the serial link is healthy.
        # This must happen BEFORE save: 'save' writes to flash and the firmware
        # does not prompt afterward (and can leave the link briefly unusable), so
        # any command issued after save may not get through. Un-freeze first.
        nvna.resume()
        print("sweep resumed.")

        # 5) optionally persist -- LAST, fire-and-forget.
        if args.no_save:
            print("\nnot saving (per --no-save). The calibration is active now but "
                  "will be lost on power cycle unless you save a preset.")
        else:
            # save() is fire-and-forget: it writes to flash and the device does
            # NOT acknowledge over serial, so this returns without waiting for a
            # prompt. The return is not a reliable success signal.
            nvna.save(args.slot)
            print(f"\nsave command sent for preset slot {args.slot}.")
            print("  NOTE: the NanoVNA does not acknowledge a flash write over "
                  "serial, so there is no confirmation here.")
            print("  To verify the calibration persisted: power-cycle the device, "
                  "reconnect, and recall(slot) -- if the cal returns, the save worked.")
            print("  (You can also save from the device's own menu.)")

        print("\nSOLT calibration complete.")
    except KeyboardInterrupt:
        print("\ninterrupted.")
        # try to un-freeze the sweep on an early abort, but never let a teardown
        # serial write block the exit (the link may be in a bad state).
        try:
            nvna.resume()
        except Exception:
            pass
    finally:
        # disconnect only -- release the port. We do NOT issue a serial write
        # here: on the happy path the sweep was already resumed before save, and
        # after a flash write the link may not accept another command.
        nvna.disconnect()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())