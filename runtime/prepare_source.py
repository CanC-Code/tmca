import os
import re

def patch_source():
    # Redirect main and add frame-tick hooks
    main_path = "src/main.c"
    if os.path.exists(main_path):
        with open(main_path, "r") as f:
            content = f.read()
        
        # Rename entry point
        content = content.replace("int main(void)", "void main_init(void)")
        
        # Patch hardware registers (Example: REG_VRAM)
        # We look for direct GBA memory address pointers and redirect them
        content = re.sub(r'\(u16\*\)0x0400[0-9A-Fa-f]+', '((u16*)get_virtual_reg())', content)
        
        with open(main_path, "w") as f:
            f.write("#include <stdint.h>\nextern uint16_t* get_virtual_reg();\n")
            f.write(content)
            f.write("\nvoid main_step(void) { /* Frame logic executed by JNI tick */ }\n")
    
    print("Source patching complete.")

if __name__ == "__main__":
    patch_source()
