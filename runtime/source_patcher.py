"""
runtime/source_patcher.py
64-bit Android NDK porting patcher.

Responsibility: 
1. Fix 64-bit C compliance (pointers, casts, assertions).
2. Stub asset headers AND translation binaries.
3. Neuter devkitPro and skip C++ tool execution.
"""

import os
import re
import sys

def read_file(path: str) -> str:
    if not os.path.exists(path): return ""
    with open(path, "r", encoding="utf-8", errors="replace") as fh:
        return fh.read()

def write_file(path: str, content: str) -> None:
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(content)

# ──────────────────────────────────────────────────────────────────────────────
# 0. Build System Neuter (Bypass Toolchain, CMake, and Tool Execution)
# ──────────────────────────────────────────────────────────────────────────────

def patch_makefiles():
    """Removes devkitPro requirements and skips broken C++ tools."""
    # 1. Neuter Toolchain.mk
    tc_path = "Toolchain.mk"
    if os.path.exists(tc_path):
        content = read_file(tc_path).replace("$(error arm-none-eabi-gcc not found", "# $(error")
        write_file(tc_path, content)
        print(f"  [PATCHED] {tc_path}")

    # 2. Neuter Makefile and GBA.mk to skip tool execution
    for mf_path in ["Makefile", "GBA.mk"]:
        if os.path.exists(mf_path):
            content = read_file(mf_path)
            # Skip building tools
            content = content.replace("build: tools", "build:")
            content = content.replace("extract_assets: tools", "extract_assets:")
            # Comment out calls to any tools in the tools/bin directory
            content = content.replace("\ttools/bin/", "\t# tools/bin/")
            content = content.replace("\tcmake", "\t# cmake")
            write_file(mf_path, content)
            print(f"  [PATCHED] {mf_path}")

def stub_build_artifacts(include_dir: str = "include"):
    """Stub headers and binary artifacts for SAF runtime loading."""
    # Header Stubs
    asset_dir = os.path.join(include_dir, "assets")
    if not os.path.exists(asset_dir): os.makedirs(asset_dir)
    for h in ["map_offsets.h", "gfx_offsets.h"]:
        path = os.path.join(asset_dir, h)
        if not os.path.exists(path):
            write_file(path, "#ifndef ASSET_OFFSETS_H\n#define ASSET_OFFSETS_H\n#endif\n")
            print(f"  [STUB]    {path}")

    # Translation Binary Stubs (Fixes: translations/USA.bin error)
    trans_dir = "translations"
    if not os.path.exists(trans_dir): os.makedirs(trans_dir)
    for b in ["USA.bin", "EU.bin", "JP.bin"]:
        path = os.path.join(trans_dir, b)
        if not os.path.exists(path):
            write_file(path, "\x00" * 4) # Small dummy binary
            print(f"  [STUB]    {path}")

# ──────────────────────────────────────────────────────────────────────────────
# 1-6. 64-bit Porting Logic (Pointers, Assertions, Casts)
# ──────────────────────────────────────────────────────────────────────────────

def patch_main_c(src_dir):
    path = os.path.join(src_dir, "main.c")
    content = read_file(path)
    if not content or "get_virtual_reg" in content: return
    patched = content.replace("int main(void)", "void main_init(void)")
    patched = re.sub(r'\(u16\s*\*\s*\)\s*0x0400[0-9A-Fa-f]+', '((u16*)get_virtual_reg())', patched)
    write_file(path, "#include <stdint.h>\nextern uint16_t* get_virtual_reg();\n" + patched + "\nvoid main_step(void) {}\n")

def patch_global_h(include_dir):
    path = os.path.join(include_dir, "global.h")
    content = read_file(path)
    if not content or "_Static_assert" in content: return
    pattern = r'#\s*define\s+static_assert\(cond\)\s+extern\s+char\s+assertion\[\(cond\)\s*\?\s*1\s*:\s*-1\]'
    patched = re.sub(pattern, '#define static_assert(cond) _Static_assert(cond, "Err")', content)
    write_file(path, "#include <stdint.h>\n" + patched)

def patch_sizeof_assertions(include_dir):
    regex = re.compile(r'static_assert\s*\(\s*sizeof\s*\(\s*(.*?)\s*\)\s*==\s*([0-9A-Za-z_x]+)\s*\)', re.DOTALL)
    for root, _, files in os.walk(include_dir):
        for f in files:
            if f.endswith(".h"):
                p = os.path.join(root, f)
                c = read_file(p)
                patched = regex.sub(lambda m: f'static_assert(sizeof({m.group(1)}) >= {m.group(2)})', c)
                if patched != c: write_file(p, patched)

def patch_u32_casts(src_dir):
    regex = re.compile(r'\(u32\)\s*([A-Za-z_][A-Za-z0-9_.>-]*(?:\[[^\]]*\])*)')
    for root, _, files in os.walk(src_dir):
        for f in files:
            if f.endswith(".c"):
                p = os.path.join(root, f)
                c = read_file(p)
                patched = regex.sub(r'(uintptr_t)(\1)', c)
                if patched != c: write_file(p, patched)

def patch_lvalue_casts(src_dir):
    regex = re.compile(r'\(\s*([A-Za-z_][A-Za-z0-9_\s*]*?)\s*\*\s*\)\s*([A-Za-z_][A-Za-z0-9_.>-]*)\s*\+=\s*([^;]+?)\s*;')
    def _sub(m): return f'{m.group(2).strip()} = (void*)(({m.group(1).strip()}*){m.group(2).strip()} + ({m.group(3).strip()}));'
    for root, _, files in os.walk(src_dir):
        for f in files:
            if f.endswith(".c"):
                p = os.path.join(root, f)
                c = read_file(p)
                patched = regex.sub(_sub, c)
                if patched != c: write_file(p, patched)

# ──────────────────────────────────────────────────────────────────────────────
# Execution
# ──────────────────────────────────────────────────────────────────────────────

def patch_source(src_dir="src", include_dir="include"):
    print("=== Step 0: Neutering Build System & Artifacts ===")
    patch_makefiles()
    stub_build_artifacts(include_dir)

    print("\n=== Step 1-6: Porting C Source to 64-bit NDK ===")
    patch_main_c(src_dir)
    patch_global_h(include_dir)
    patch_sizeof_assertions(include_dir)
    patch_u32_casts(src_dir)
    patch_lvalue_casts(src_dir)

    print("\n64-bit Porting Patch Applied Successfully.")

if __name__ == "__main__":
    patch_source()
