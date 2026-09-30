import time
import sys
from engine.vfs import VirtualFS
from engine.terminal import Shell

BOOT_SEQUENCE = [
    "[OK] Booting my-server OS v0.1...",
    "[OK] Loading core drivers: acpi, pci, storage...",
    "[OK] Mounting root filesystem...",
    "[OK] Starting telemetry service...",
    "[..] Connecting to cluster core node...",
    "[FAIL] Connection rejected: node authentication failed",
    "[WARN] Service 'core-node' terminated unexpectedly.",
    "[WARN] Diagnostics written to /telemetry logs.",
    "[FATAL] System halted. Dropping to emergency recovery shell."
]

def type_text(text, delay=0.01):
    for char in text:
        sys.stdout.write(char)
        sys.stdout.flush()
        time.sleep(delay)
    print()

def simulate_boot():
    print()
    for line in BOOT_SEQUENCE:
        type_text(line, delay=0.01)
        if "FAIL" in line or "FATAL" in line or "WARN" in line:
            time.sleep(0.3)
        else:
            time.sleep(0.1)

    print("\n------------------------------------------------------------")
    print(" >>> KERNEL PANIC <<< ")
    print(" Dropping to emergency recovery shell.")
    print(" Type 'help' to see available commands.")
    print(" Type 'reboot' when system config is fixed.")
    print("------------------------------------------------------------\n")
    time.sleep(0.5)

def main():
    simulate_boot()
    vfs = VirtualFS()
    shell = Shell(vfs)
    shell.run()

if __name__ == "__main__":
    main()
