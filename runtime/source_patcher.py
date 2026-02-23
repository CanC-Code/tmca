import os
import re

# Set paths relative to the current working directory (Repository Root)
SRC_DIR = "src"
INC_DIR = "include"

def patch_global_h():
    path = os.path.join(INC_DIR, "global.h")
    if not os.path.exists(path):
        print(f"Skipping: {path} not found.")
        return

    with open(path, 'r') as f:
        content = f.read()

    # Ensure compat header is the very first line to define PACKED and GBA_PTR
    if 'include "android_compat.h"' not in content:
        content = '#include "android_compat.h"\n' + content
        with open(path, 'w') as f:
            f.write(content)
        print(f"Patched {path}")

def patch_lvalue_casts():
    # Targets patterns like (u8*)d += offset;
    # Replaces with ADVANCE_PTR(d, offset);
    pattern = re.compile(r'\((u8|u16|u32|void)\*\)\s*(\w+)\s*\+=\s*([^;]+);')

    for root, _, files in os.walk(SRC_DIR):
        for file in files:
            if file.endswith(('.c', '.cpp')):
                path = os.path.join(root, file)
                with open(path, 'r') as f:
                    content = f.read()

                new_content = pattern.sub(r'ADVANCE_PTR(\2, \3);', content)

                if new_content != content:
                    with open(path, 'w') as f:
                        f.write(new_content)
                    print(f"Fixed lvalue casts in {path}")

def patch_pointer_casts():
    """
    Finds (u32)ptr or (uint32_t)ptr casts that cause precision loss on 64-bit.
    Replaces them with (ptr_t) to ensure the address width matches the host.
    """
    # Pattern looks for (u32) or (uint32_t) followed by a variable or pointer expression
    # We target common patterns like (u32)pEntity, (u32)this, (u32)&var
    cast_pattern = re.compile(r'\(u32\)\s*([\w\->&*.()]+)')
    
    for root, _, files in os.walk(SRC_DIR):
        for file in files:
            if file.endswith(('.c', '.cpp')):
                path = os.path.join(root, file)
                with open(path, 'r') as f:
                    content = f.read()
                
                # Update the cast to use our width-safe ptr_t (uintptr_t)
                new_content = cast_pattern.sub(r'(ptr_t)\1', content)
                
                if new_content != content:
                    with open(path, 'w') as f:
                        f.write(new_content)
                    print(f"Fixed 64-bit pointer casts in {path}")

def patch_pointers_in_structs():
    """
    Identifies pointers inside structs that are subject to static_asserts.
    Converts 'Type* name;' to 'GBA_PTR(Type) name;' to maintain 32-bit size.
    """
    ptr_pattern = re.compile(r'(\w+\s*\*?)\s*\*(\w+)\s*;')

    for root, _, files in os.walk(INC_DIR):
        for file in files:
            if file.endswith('.h'):
                path = os.path.join(root, file)
                with open(path, 'r') as f:
                    lines = f.readlines()

                new_lines = []
                in_packed_struct = False
                changed = False

                for line in lines:
                    if 'typedef struct' in line:
                        in_packed_struct = True

                    if in_packed_struct and '*' in line and ';' in line:
                        substituted = ptr_pattern.sub(r'GBA_PTR(\1) \2;', line)
                        if substituted != line:
                            line = substituted
                            changed = True

                    if '}' in line and 'static_assert' in line:
                        in_packed_struct = False

                    new_lines.append(line)

                if changed:
                    with open(path, 'w') as f:
                        f.writelines(new_lines)
                    print(f"Compressed pointers in {path}")

def patch_struct_packing():
    pattern = re.compile(r'(typedef\s+struct\s*\{.*?\})\s*(\w+)\s*;\s*static_assert', re.DOTALL)

    for root, _, files in os.walk(INC_DIR):
        for file in files:
            if file.endswith('.h'):
                path = os.path.join(root, file)
                with open(path, 'r') as f:
                    content = f.read()

                new_content = pattern.sub(r'\1 PACKED \2; static_assert', content)

                if new_content != content:
                    with open(path, 'w') as f:
                        f.write(new_content)
                    print(f"Applied PACKED to structs in {path}")

if __name__ == "__main__":
    patch_global_h()
    patch_lvalue_casts()
    patch_struct_packing()
    patch_pointers_in_structs()
    patch_pointer_casts() # Final pass to fix the precision errors
