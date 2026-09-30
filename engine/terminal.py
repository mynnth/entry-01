HELP_TEXT = """
EMERGENCY RECOVERY SHELL
Available commands:
  ls [path]               : List directory contents
  cd <path>               : Change directory
  pwd                     : Print working directory
  cat <file>              : Read file contents
  grep <word> <file>      : Search for word in file
  find <path> -name <file>: Search for file by name
  cp <src> <dst>          : Copy file
  help                    : Display this manual
  reboot                  : Restart the system and test config
"""

class Shell:
    def __init__(self, vfs):
        self.vfs = vfs

    def check_win_condition(self):
        content, err = self.vfs.read_file("/core/node.conf")
        if err or content is None:
            return False, "Failed to load /core/node.conf (File missing)"

        if "AUTH_TOKEN=0x99B4F1A" in content and "STATUS=ACTIVE" in content:
            return True, "Core node configuration verified."

        return False, "Checksum mismatch in /core/node.conf (AUTH_TOKEN corrupted)"

    def run(self):
        while True:
            try:
                prompt = f"guest@my-server:{self.vfs.get_pwd_str()}# "
                user_input = input(prompt).strip()
            except (KeyboardInterrupt, EOFError):
                print("\n[!] Shell terminated forcefully.")
                break

            if not user_input:
                continue

            parts = user_input.split()
            cmd = parts[0].lower()
            args = parts[1:]

            if cmd == "help":
                print(HELP_TEXT.strip())

            elif cmd == "pwd":
                print(self.vfs.get_pwd_str())

            elif cmd == "ls":
                target_args = []
                for a in args:
                    if not a.startswith("-"):
                        target_args.append(a)
                        
                target = target_args[0] if len(target_args) > 0 else ""
                items, err = self.vfs.list_dir(target)
                if err:
                    print(err)
                elif items:
                    print("  ".join(items))

            elif cmd == "cd":
                if len(args) == 0 or args[0] == "~":
                    self.vfs.change_dir("~")
                else:
                    success, err = self.vfs.change_dir(args[0])
                    if not success:
                        print(err)

            elif cmd == "cat":
                if len(args) == 0:
                    print("cat: missing file operand")
                else:
                    for filename in args:
                        content, err = self.vfs.read_file(filename)
                        if err:
                            print(err)
                        else:
                            print(content.rstrip("\n"))

            elif cmd == "grep":
                clean_args = []
                for a in args:
                    if not a.startswith("-"):
                        clean_args.append(a)
                        
                if len(clean_args) < 2:
                    print("grep: missing arguments. Usage: grep <word> <file>")
                else:
                    word = clean_args[0].lower()
                    target = clean_args[1]
                    content, err = self.vfs.read_file(target)
                    if err:
                        print(err.replace("cat:", "grep:"))
                    else:
                        lines = content.split("\n")
                        matches = []
                        for line in lines:
                            if word in line.lower():
                                matches.append(line)
                        if matches:
                            print("\n".join(matches))

            elif cmd == "find":
                if len(args) == 0:
                    print("find: missing operand. Usage: find <path> -name <filename>")
                elif "-name" not in args:
                    print("find: missing '-name' parameter. Usage: find <path> -name <filename>")
                else:
                    name_idx = args.index("-name")
                    if name_idx + 1 >= len(args):
                        print("find: missing argument to '-name'. Usage: find <path> -name <filename>")
                    else:
                        start_path = args[0] if name_idx > 0 else "."
                        target_filename = args[name_idx + 1]
                        matches, err = self.vfs.find_files(start_path, target_filename)
                        if err:
                            print(err)
                        elif matches:
                            print("\n".join(matches))

            elif cmd == "cp":
                if len(args) < 2:
                    print("cp: missing file operand. Usage: cp <src> <dst>")
                else:
                    success, err = self.vfs.copy_file(args[0], args[1])
                    if not success:
                        print(err)

            elif cmd == "reboot":
                print("[*] Initiating reboot sequence...")
                is_win, msg = self.check_win_condition()
                if not is_win:
                    print(f"[FAIL] {msg}")
                    print("[CRITICAL] SYSTEM HALTED: Core node failed to start.")
                    print("Dropping back to emergency recovery shell...\n")
                else:
                    print("[OK] Core node configuration verified.")
                    print("[OK] Validating AUTH_TOKEN=0x99B4F1A... OK")
                    print("[OK] Starting core node service... OK")
                    print("[OK] Synchronizing telemetry and cluster state... OK")
                    print("\n================================================")
                    print(" [SUCCESS] MY SERVER IS BACK ONLINE!")
                    print(" Node STATION-01 restored and synchronized.")
                    print(" You solved entry-01!")
                    print("================================================\n")
                    break

            elif cmd == "exit" or cmd == "quit":
                print("Emergency shell cannot be exited. Use 'reboot' to restart system.")

            else:
                print(f"{cmd}: command not found. Type 'help' for available commands.")
