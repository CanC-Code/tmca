import os
import re

def patch_source():
    # 1. Patch Entry Point and Virtual Registers
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

    # 2. FIX: Comprehensive Structure Size Patching
    # We target both 'struct RoomVars' and 'RoomVars' and change == to >=
    room_h = "include/room.h"
    if os.path.exists(room_h):
        with open(room_h, "r") as f:
            room_content = f.read()
        
        # This regex catches: static_assert(sizeof(struct RoomVars) == 0xCC)
        # AND: static_assert(sizeof(RoomVars) == 0xCC)
        room_content = re.sub(
            r'static_assert\(sizeof\((struct\s+)?RoomVars\)\s*==\s*0xCC\)',
            'static_assert(sizeof(RoomVars) >= 0xCC)',
            room_content
        )
        
        with open(room_h, "w") as f:
            f.write(room_content)

    # 3. FIX: Modernize Static Assertions in global.h
    global_h = "include/global.h"
    if os.path.exists(global_h):
        with open(global_h, "r") as f:
            global_content = f.read()
        
        # Use a regex to find the old macro even if spacing/formatting differs
        old_macro_pattern = r'#define\s+static_assert\(cond\)\s+extern\s+char\s+assertion\[\(cond\)\s*\?\s*1\s*:\s*-1\]'
        new_assert = '#define static_assert(cond) _Static_assert(cond, "Static Assertion Failed")'
        
        global_content = re.sub(old_macro_pattern, new_assert, global_content)
        
        # Fallback: if the above didn't match, try a simpler replacement
        if "_Static_assert" not in global_content:
             global_content = global_content.replace("#define static_assert(cond)", "#define static_assert(cond) _Static_assert(cond, \"failed\") //")

        # Ensure stdint is present
        if "#include <stdint.h>" not in global_content:
            global_content = "#include <stdint.h>\n" + global_content
            
        with open(global_h, "w") as f:
            f.write(global_content)

    print("64-bit Porting Patch Applied (Regex Enhanced).")

if __name__ == "__main__":
    patch_source()
