import copy

INITIAL_FILESYSTEM = {
    "bin": {
        "help": "Built-in command manual.",
        "reboot": "System restart utility.",
    },
    "core": {
        "kernel.conf": "MAX_THREADS=64\nCACHE_SIZE=1024M\n",
        "node.conf": (
            "# CORE NODE CONFIGURATION\n"
            "NODE_ID=STATION-01\n"
            "SYNC_PORT=8080\n"
            "STATUS=CORRUPTED\n"
            "AUTH_TOKEN=0xDEADBEEF\n"
            "# [ERROR] Checksum mismatch. Token rejected by cluster.\n"
        ),
        "data": {
            "sensors.dat": "TEMP: 24C | PRESS: 1013hPa\n"
        },
    },
    "archive": {
        "snapshots": {
            "node.conf.bak": (
                "# CORE NODE CONFIGURATION (BACKUP)\n"
                "NODE_ID=STATION-01\n"
                "SYNC_PORT=8080\n"
                "STATUS=ACTIVE\n"
                "AUTH_TOKEN=0x99B4F1A\n"
            ),
        },
    },
    "telemetry": {
        "boot.log": (
            "[00:00:01] Boot sequence initiated...\n"
            "[00:00:02] Loading core modules... OK\n"
            "[00:00:03] Mounting virtual filesystem... OK\n"
            "[00:00:04] Starting telemetry daemon... OK\n"
        ),
        "incident.log": (
            "[03:14:00] [SYSTEM] Rack 2 power anomaly detected.\n"
            "[03:14:01] [WARN] Sudden shutdown during node sync cycle.\n"
            "[03:14:02] [ERROR] Node service startup failed: invalid authentication token.\n"
            "[03:14:02] [ERROR] Corrupted configuration detected in /core/node.conf (checksum mismatch).\n"
            "[03:14:03] [CRITICAL] System halted to prevent network partition.\n"
            "[03:14:03] [NOTICE] Dropping to emergency recovery shell.\n"
        ),
    },
    "operator": {
        "shift_notes.txt": (
            "--- Operator Shift Notes (Alex - 09/28) ---\n"
            "- Power on rack 2 is fluctuating. Ticket #402 logged.\n"
            "- A clean snapshot of the core node configuration was archived before maintenance.\n"
            "- If the active configuration becomes corrupted, recover the archived snapshot before restarting the node.\n"
            "- Run 'reboot' to verify cluster synchronization.\n"
        )
    },
}

def resolve_path(current_path, path_str):
    path_str = path_str.strip()
    if path_str == "" or path_str == ".":
        return list(current_path)

    if path_str == "~":
        return ["operator"]
    
    if path_str.startswith("~/"):
        parts = ["operator"] + path_str[2:].split("/")
    elif path_str.startswith("/"):
        parts = path_str.split("/")
    else:
        parts = current_path + path_str.split("/")
        
    result = []
    for part in parts:
        if part == "" or part == ".":
            continue
        if part == "..":
            if len(result) > 0:
                result.pop()
        else:
            result.append(part)
            
    return result

def get_node(root, parts):
    current = root
    for part in parts:
        if not isinstance(current, dict) or part not in current:
            return None
        current = current[part]
    return current

def search_dict(node_dict, current_prefix, target_name):
    files = []
    for name, value in sorted(node_dict.items()):
        if current_prefix == "/":
            child_path = "/" + name
        elif current_prefix.endswith("/"):
            child_path = current_prefix + name
        else:
            child_path = current_prefix + "/" + name
            
        if name == target_name:
            files.append(child_path)
            
        if isinstance(value, dict):
            files += search_dict(value, child_path, target_name)
            
    return files

class VirtualFS:
    def __init__(self):
        self.root = copy.deepcopy(INITIAL_FILESYSTEM)
        self.current_path = []

    def get_pwd_str(self):
        if len(self.current_path) == 0:
            return "/"
        return "/" + "/".join(self.current_path)

    def list_dir(self, path_str=""):
        target = path_str.strip()
        if target == "":
            target = "."
            
        parts = resolve_path(self.current_path, target)
        node = get_node(self.root, parts)

        if node is None:
            return None, f"ls: cannot access '{path_str}': No such file or directory"
            
        if not isinstance(node, dict):
            name = parts[-1] if len(parts) > 0 else target
            return [name], None

        items = []
        for name, content in sorted(node.items()):
            if isinstance(content, dict):
                items.append(name + "/")
            else:
                items.append(name)
        return items, None

    def change_dir(self, path_str):
        target = path_str.strip()
        if target == "" or target == "~":
            self.current_path = ["operator"]
            return True, None

        parts = resolve_path(self.current_path, target)
        node = get_node(self.root, parts)

        if node is None:
            return False, f"cd: no such file or directory: {path_str}"
            
        if not isinstance(node, dict):
            return False, f"cd: not a directory: {path_str}"

        self.current_path = parts
        return True, None

    def read_file(self, path_str):
        parts = resolve_path(self.current_path, path_str.strip())
        node = get_node(self.root, parts)
        
        if node is None:
            return None, f"cat: {path_str}: No such file or directory"
            
        if isinstance(node, dict):
            return None, f"cat: {path_str}: Is a directory"
            
        return node, None

    def find_files(self, start_path, target_name):
        parts = resolve_path(self.current_path, start_path.strip())
        node = get_node(self.root, parts)
        
        if node is None:
            return None, f"find: '{start_path}': No such file or directory"

        if not isinstance(node, dict):
            name = parts[-1] if len(parts) > 0 else start_path.strip()
            if name == target_name:
                return [start_path.strip()], None
            return [], None

        start_str = start_path.strip()
        if start_str == "/":
            prefix = "/"
        elif start_str.endswith("/"):
            prefix = start_str[:-1]
        else:
            prefix = start_str

        results = search_dict(node, prefix, target_name)
        return results, None

    def copy_file(self, src_str, dst_str):
        src_parts = resolve_path(self.current_path, src_str.strip())
        src_node = get_node(self.root, src_parts)
        
        if src_node is None:
            return False, f"cp: cannot stat '{src_str}': No such file or directory"
            
        if isinstance(src_node, dict):
            return False, f"cp: -r not supported: '{src_str}' is a directory"

        dst_parts = resolve_path(self.current_path, dst_str.strip())
        if len(dst_parts) == 0:
            return False, "cp: cannot overwrite root directory"

        dst_node = get_node(self.root, dst_parts)
        if dst_node is not None and isinstance(dst_node, dict):
            file_name = src_parts[-1] if len(src_parts) > 0 else "file"
            dst_node[file_name] = copy.deepcopy(src_node)
            return True, None

        parent_parts = dst_parts[:-1]
        parent_node = get_node(self.root, parent_parts)
        
        if parent_node is None:
            return False, f"cp: cannot create '{dst_str}': No such directory"
            
        if not isinstance(parent_node, dict):
            return False, f"cp: cannot create '{dst_str}': Not a directory"

        target_file_name = dst_parts[-1]
        parent_node[target_file_name] = copy.deepcopy(src_node)
        return True, None
