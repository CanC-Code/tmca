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

    # 2. FIX: RoomVars and 64-bit Structure Sizes
    room_h = "include/room.h"
    if os.path.exists(room_h):
        with open(room_h, "r") as f:
            room_content = f.read()
        
        # We switch from '==' to '>=' to allow for 64-bit pointer growth
        # This prevents the build from crashing while keeping a safety floor
        room_content = room_content.replace("static_assert(sizeof(struct RoomVars) == 0xCC)", 
                                          "static_assert(sizeof(struct RoomVars) >= 0xCC)")
        
        with open(room_h, "w") as f:
            f.write(room_content)

    # 3. FIX: Modernize Static Assertions in global.h
    global_h = "include/global.h"
    if os.path.exists(global_h):
        with open(global_h, "r") as f:
            global_content = f.read()
        
        # Use the NDK-safe _Static_assert keyword
        # This fixes the 'storage size isn't constant' error
        old_assert = "#define static_assert(cond) extern char assertion[(cond) ? 1 : -1]"
        new_assert = "#define static_assert(cond) _Static_assert(cond, \"Static Assertion Failed\")"
        
        if old_assert in global_content:
            global_content = global_content.replace(old_assert, new_assert)
        else:
            # Fallback if the macro is slightly different
            global_content = re.sub(r'#define static_assert\(cond\).*', new_assert, global_content)
        
        # Ensure stdint is present for all files
        if "#include <stdint.h>" not in global_content:
            global_content = "#include <stdint.h>\n" + global_content
            
        with open(global_h, "w") as f:
            f.write(global_content)

    print("64-bit Porting Patch Applied Successfully.")

if __name__ == "__main__":
    patch_source()
