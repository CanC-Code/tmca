import os
import re

# REVISION: Define all directories that contain source code or headers
SEARCH_DIRS = ["src", "sound", "data"]
INC_DIR = "include"

def patch_global_h():
    path = os.path.join(INC_DIR, "global.h")
    if not os.path.exists(path): return
    with open(path, 'r') as f:
        content = f.read()
    if 'include "android_compat.h"' not in content:
        content = '#include "android_compat.h"\n' + content
        with open(path, 'w') as f:
            f.write(content)
        print(f"Patched {path}")

def patch_lvalue_casts():
    # Fixes: (u8*)ptr += offset; -> ADVANCE_PTR(ptr, offset);
    pattern = re.compile(r'\((u8|u16|u32|void)\*\)\s*(\w+)\s*\+=\s*([^;]+);')
    for s_dir in SEARCH_DIRS:
        if not os.path.exists(s_dir): continue
        for root, _, files in os.walk(s_dir):
            for file in files:
                if file.endswith(('.c', '.cpp')):
                    path = os.path.join(root, file)
                    with open(path, 'r') as f: content = f.read()
                    new_content = pattern.sub(r'ADVANCE_PTR(\2, \3);', content)
                    if new_content != content:
                        with open(path, 'w') as f: f.write(new_content)
                        print(f"Fixed lvalue casts in {path}")

def patch_pointer_casts():
    # Fixes: (u32)ptr -> (ptr_t)ptr (prevents precision loss on 64-bit)
    cast_pattern = re.compile(r'\(u32\)\s*([\w\->&*.()\[\]]+)')
    for s_dir in SEARCH_DIRS:
        if not os.path.exists(s_dir): continue
        for root, _, files in os.walk(s_dir):
            for file in files:
                if file.endswith(('.c', '.cpp')):
                    path = os.path.join(root, file)
                    with open(path, 'r') as f: content = f.read()
                    new_content = cast_pattern.sub(r'(ptr_t)\1', content)
                    if new_content != content:
                        with open(path, 'w') as f: f.write(new_content)
                        print(f"Fixed 64-bit pointer casts in {path}")

def patch_pointers_in_structs():
    """
    Identifies pointers inside structs and converts them to GBA_PTR.
    Uses brace depth and 'struct' keywords to avoid hitting global variables.
    """
    # Matches indented pointers like '    Entity* next;' or '  struct Sprite* s;'
    ptr_pattern = re.compile(r'^(\s+)(struct\s+\w+|\w+)\s*\*\s*(\w+)\s*;')

    for root, _, files in os.walk(INC_DIR):
        for file in files:
            if not file.endswith('.h'): continue
            path = os.path.join(root, file)
            with open(path, 'r') as f: lines = f.readlines()

            new_lines = []
            brace_depth = 0
            in_struct_block = False
            changed = False

            for line in lines:
                # Detect start of a struct/union
                if ('struct' in line or 'union' in line) and '{' in line:
                    in_struct_block = True
                
                if '{' in line: brace_depth += 1
                
                # REVISION: Only patch if we are inside a struct block and indented
                if in_struct_block and brace_depth > 0:
                    # Ignore 'extern' declarations which are global variables
                    if '*' in line and ';' in line and 'extern' not in line:
                        substituted = ptr_pattern.sub(r'\1GBA_PTR(\2) \3;', line)
                        if substituted != line:
                            line = substituted
                            changed = True

                if '}' in line:
                    brace_depth -= 1
                    if brace_depth <= 0:
                        in_struct_block = False
                        brace_depth = 0
                
                new_lines.append(line)

            if changed:
                with open(path, 'w') as f: f.writelines(new_lines)
                print(f"Safe-compressed pointers in {path}")

def patch_struct_packing():
    # Adds PACKED attribute to structs that have static_assert checks
    pattern = re.compile(r'(typedef\s+struct\s*\{.*?\})\s*(\w+)\s*;\s*static_assert', re.DOTALL)
    for root, _, files in os.walk(INC_DIR):
        for file in files:
            if file.endswith('.h'):
                path = os.path.join(root, file)
                with open(path, 'r') as f: content = f.read()
                new_content = pattern.sub(r'\1 PACKED \2; static_assert', content)
                if new_content != content:
                    with open(path, 'w') as f: f.write(new_content)
                    print(f"Applied PACKED in {path}")

if __name__ == "__main__":
    patch_global_h()
    patch_lvalue_casts()
    patch_struct_packing()
    patch_pointers_in_structs() # Fixed to protect global pointers
    patch_pointer_casts()
