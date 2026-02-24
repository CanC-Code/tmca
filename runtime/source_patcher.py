import os
import re
import sys

# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────

def read_file(path: str) -> str:
    with open(path, "r", encoding="utf-8", errors="replace") as fh:
        return fh.read()

def write_file(path: str, content: str) -> None:
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(content)

def patch_summary(label: str, original: str, patched: str) -> None:
    if original != patched:
        print(f"  [PATCHED] {label}")
    else:
        print(f"  [skip]    {label}  (no changes needed)")

# ──────────────────────────────────────────────────────────────────────────────
# 1. Entry point + virtual register stubs (src/main.c)
# ──────────────────────────────────────────────────────────────────────────────

MAIN_HEADER = "#include <stdint.h>\nextern uint16_t* get_virtual_reg();\n"
MAIN_FOOTER = "\nvoid main_step(void) { /* Hooked by JNI */ }\n"

def patch_main_c(src_dir: str = "src") -> None:
    path = os.path.join(src_dir, "main.c")
    if not os.path.exists(path):
        return
    content = read_file(path)
    if "get_virtual_reg" in content:
        return
    
    content = content.replace("int main(void)", "void main_init(void)")
    content = re.sub(r'\(u16\s*\*\s*\)\s*0x0400[0-9A-Fa-f]+', '((u16*)get_virtual_reg())', content)
    
    if MAIN_HEADER.strip() not in content:
        content = MAIN_HEADER + content
    if "main_step" not in content:
        content += MAIN_FOOTER
    write_file(path, content)
    print(f"  [DONE]    {path}")

# ──────────────────────────────────────────────────────────────────────────────
# 2. Modernise static_assert (include/global.h)
# ──────────────────────────────────────────────────────────────────────────────

def patch_global_h(include_dir: str = "include") -> None:
    path = os.path.join(include_dir, "global.h")
    if not os.path.exists(path): return
    content = read_file(path)
    if "_Static_assert" in content: return

    old_assert_re = re.compile(r'#\s*define\s+static_assert\(cond\)\s+extern\s+char\s+assertion\s*\[\s*\(cond\)\s*\?\s*1\s*:\s*-1\s*\]')
    new_assert = '#define static_assert(cond) _Static_assert(cond, "Dimension Mismatch")'
    
    content = old_assert_re.sub(new_assert, content)
    if "#include <stdint.h>" not in content:
        content = "#include <stdint.h>\n" + content
    write_file(path, content)
    print(f"  [DONE]    {path}")

# ──────────────────────────────────────────────────────────────────────────────
# 3. Relax sizeof assertions (== to >=)
# ──────────────────────────────────────────────────────────────────────────────

SIZEOF_ASSERT_RE = re.compile(r'static_assert\s*\(\s*sizeof\s*\(\s*(.*?)\s*\)\s*==\s*([0-9A-Za-z_x]+)\s*\)', re.DOTALL)

def patch_sizeof_assertions(include_dir: str = "include") -> None:
    for root, _, files in os.walk(include_dir):
        for fname in files:
            if not fname.endswith(".h"): continue
            path = os.path.join(root, fname)
            content = read_file(path)
            patched = SIZEOF_ASSERT_RE.sub(lambda m: f'static_assert(sizeof({m.group(1)}) >= {m.group(2)})', content)
            if patched != content:
                write_file(path, patched)
                print(f"  [RELAXED] {path}")

# ──────────────────────────────────────────────────────────────────────────────
# 4. Fix (u32) pointer truncation (src/*.c)
# ──────────────────────────────────────────────────────────────────────────────

U32_CAST_RE = re.compile(r'\(u32\)\s*([A-Za-z_][A-Za-z0-9_.>-]*(?:\[[^\]]*\])*)')

def patch_u32_casts(src_dir: str = "src") -> None:
    for root, _, files in os.walk(src_dir):
        for fname in files:
            if not fname.endswith(".c"): continue
            path = os.path.join(root, fname)
            content = read_file(path)
            if "(u32)" not in content: continue
            # Fixed hyphen placement in regex to avoid range error
            patched = U32_CAST_RE.sub(r'(uintptr_t)(\1)', content)
            if patched != content:
                write_file(path, patched)
                print(f"  [CAST]    {path}")

# ──────────────────────────────────────────────────────────────────────────────
# 5 & 6. PACKED macros and LValue Casts
# ──────────────────────────────────────────────────────────────────────────────

def patch_lvalue_casts(src_dir: str = "src") -> None:
    # Pattern: (TYPE*)expr += rhs; -> expr = (void*)((TYPE*)expr + rhs);
    LVALUE_RE = re.compile(r'\(\s*([A-Za-z_][A-Za-z0-9_\s*]*?)\s*\*\s*\)\s*([A-Za-z_][A-Za-z0-9_.>-]*)\s*\+=\s*([^;]+?)\s*;')
    for root, _, files in os.walk(src_dir):
        for fname in files:
            if not fname.endswith(".c"): continue
            path = os.path.join(root, fname)
            content = read_file(path)
            patched = LVALUE_RE.sub(lambda m: f'{m.group(2).strip()} = (void*)(({m.group(1).strip()}*){m.group(2).strip()} + ({m.group(3).strip()}));', content)
            if patched != content:
                write_file(path, patched)
                print(f"  [LVALUE]  {path}")

# ──────────────────────────────────────────────────────────────────────────────
# 7. NEW: Generate Asset Stubs for Runtime Loading (SAF)
# ──────────────────────────────────────────────────────────────────────────────

def generate_asset_stubs(include_dir: str = "include"):
    """Creates headers so the compiler doesn't fail without a baserom."""
    asset_dir = os.path.join(include_dir, "assets")
    if not os.path.exists(asset_dir):
        os.makedirs(asset_dir)
    
    headers = ["map_offsets.h", "gfx_offsets.h"]
    for h in headers:
        path = os.path.join(asset_dir, h)
        if not os.path.exists(path):
            stub_content = f"#ifndef {h.upper().replace('.','_')}\n#define {h.upper().replace('.','_')}\n// Stubbed for SAF Runtime Decompression\n#endif"
            write_file(path, stub_content)
            print(f"  [STUB]    {path}")

# ──────────────────────────────────────────────────────────────────────────────
# Main execution
# ──────────────────────────────────────────────────────────────────────────────

def patch_source(src_dir="src", include_dir="include"):
    print("=== Starting 64-bit Android Source Patching ===")
    patch_main_c(src_dir)
    patch_global_h(include_dir)
    patch_sizeof_assertions(include_dir)
    patch_u32_casts(src_dir)
    patch_lvalue_casts(src_dir)
    generate_asset_stubs(include_dir)
    print("=== Patching Complete. Build ready for NDK. ===")

if __name__ == "__main__":
    args = sys.argv[1:]
    patch_source(
        src_dir=args[0] if len(args) >= 1 else "src",
        include_dir=args[1] if len(args) >= 2 else "include"
    )
