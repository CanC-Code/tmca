import os
import re

# Paths relative to project root
SRC_DIR = "../src"
INC_DIR = "../include"

def patch_global_h():
    path = os.path.join(INC_DIR, "global.h")
    with open(path, 'r') as f:
        content = f.read()
    
    # Ensure compat header is the very first line
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

def patch_struct_packing():
    # Finds structs that are followed by static_assert and adds PACKED
    # Target: typedef struct { ... } Name; static_assert(sizeof(Name) == ...);
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
