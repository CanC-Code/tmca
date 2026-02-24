import os
import re

def patch_source():
    # 1. Patch Entry Point and Virtual Registers (main.c)
    main_path = "src/main.c"
    if os.path.exists(main_path):
        with open(main_path, "r") as f:
            content = f.read()
        content = content.replace("int main(void)", "void main_init(void)")
        content = re.sub(r'\(u16\*\)0x0400[0-9A-Fa-f]+', '((u16*)get_virtual_reg())', content)
        with open(main_path, "w") as f:
            f.write("#include <stdint.h>\nextern uint16_t* get_virtual_reg();\n")
            f.write(content)
            f.write("\nvoid main_step(void) { /* Hooked by JNI */ }\n")

    # 2. Modernize Static Assertions (global.h)
    global_h = "include/global.h"
    if os.path.exists(global_h):
        with open(global_h, "r") as f:
            content = f.read()
        
        # Use NDK-safe _Static_assert
        old_assert = r'#define\s+static_assert\(cond\)\s+extern\s+char\s+assertion\[\(cond\)\s*\?\s*1\s*:\s*-1\]'
        new_assert = '#define static_assert(cond) _Static_assert(cond, "Dimension Mismatch")'
        content = re.sub(old_assert, new_assert, content)
        
        if "#include <stdint.h>" not in content:
            content = "#include <stdint.h>\n" + content
        
        with open(global_h, "w") as f:
            f.write(content)

    # 3. Universal Header Scan for struct sizes (RoomVars, Entity, etc.)
    # This relaxes '==' to '>=' to allow for 64-bit pointer/padding growth
    include_dir = "include"
    if os.path.exists(include_dir):
        for root, _, files in os.walk(include_dir):
            for file in files:
                if file.endswith(".h"):
                    path = os.path.join(root, file)
                    with open(path, "r") as f:
                        h_content = f.read()
                    
                    # Target sizeof assertions (handles 0xCC, 204, 184, etc.)
                    new_h = re.sub(
                        r'static_assert\s*\(\s*sizeof\s*\((.*?)\)\s*==\s*([0-9a-zA-ZxX]+)\s*\)',
                        r'static_assert(sizeof(\1) >= \2)',
                        h_content
                    )
                    
                    if new_h != h_content:
                        with open(path, "w") as f:
                            f.write(new_h)

    # 4. FIX: Pointer Truncation Precision Loss (src/*.c)
    # This specifically fixes the "bad character range" regex error
    src_dir = "src"
    if os.path.exists(src_dir):
        for root, _, files in os.walk(src_dir):
            for file in files:
                if file.endswith(".c"):
                    path = os.path.join(root, file)
                    with open(path, "r") as f:
                        c_content = f.read()
                    
                    # Fixed Regex: Escaped the hyphen (\-) and handled pointer access (->)
                    new_c = re.sub(r'\(u32\)\s*([a-zA-Z_][a-zA-Z0-9_>\-]*)', r'(uintptr_t)(\1)', c_content)
                    
                    if new_c != c_content:
                        with open(path, "w") as f:
                            f.write(new_c)

    print("64-bit Porting Patch Applied Successfully.")

if __name__ == "__main__":
    patch_source()
