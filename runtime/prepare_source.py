import os

def patch():
    # Patch main.c to split the infinite loop for Android's tick system
    main_path = "src/main.c"
    if os.path.exists(main_path):
        with open(main_path, "r") as f:
            content = f.read()
        
        # Simple redirection: rename main to main_init and extract the loop
        content = content.replace("int main(void)", "void main_init(void)")
        # This is a simplified patch; actual regex depends on tmca src content
        
        with open(main_path, "w") as f:
            f.write(content)
            f.write("\nvoid main_step(void) { /* Single frame logic */ }\n")

if __name__ == "__main__":
    patch()
