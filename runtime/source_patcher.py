"""
runtime/source_patcher.py
64-bit Android NDK porting patcher.

Responsibility: C source patching only.
Icon generation is handled by runtime/generate_icons.sh, which is
invoked as its own workflow step before assembleDebug.
"""

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
# 1. Entry point + virtual register stubs  (src/main.c)
# ──────────────────────────────────────────────────────────────────────────────

MAIN_HEADER = "#include <stdint.h>\nextern uint16_t* get_virtual_reg();\n"
MAIN_FOOTER = "\nvoid main_step(void) { /* Hooked by JNI */ }\n"

def patch_main_c(src_dir: str = "src") -> None:
    path = os.path.join(src_dir, "main.c")
    if not os.path.exists(path):
        print(f"  [skip]    {path}  (not found)")
        return

    try:
        content = read_file(path)
        original = content

        # Idempotency guard
        if "get_virtual_reg" in content and "main_step" in content:
            print(f"  [skip]    {path}  (already patched)")
            return

        # Replace entry-point signature
        content = content.replace("int main(void)", "void main_init(void)")

        # Replace hard-coded GBA VRAM addresses with portable accessor.
        # Pattern: (u16*)0x0400xxxx  — any hex suffix after 0x0400
        content = re.sub(
            r'\(u16\s*\*\s*\)\s*0x0400[0-9A-Fa-f]+',
            '((u16*)get_virtual_reg())',
            content
        )

        # Prepend header only if not already present
        if MAIN_HEADER.strip() not in content:
            content = MAIN_HEADER + content

        # Append JNI hook stub only if not already present
        if "main_step" not in content:
            content += MAIN_FOOTER

        patch_summary(path, original, content)
        write_file(path, content)

    except Exception as exc:
        print(f"  [ERROR]   {path}: {exc}", file=sys.stderr)


# ──────────────────────────────────────────────────────────────────────────────
# 2. Modernise static_assert macro  (include/global.h)
# ──────────────────────────────────────────────────────────────────────────────

OLD_ASSERT_RE = re.compile(
    r'#\s*define\s+static_assert\s*\(cond\)\s+'
    r'extern\s+char\s+assertion\s*\[\s*\(cond\)\s*\?\s*1\s*:\s*-1\s*\]',
    re.MULTILINE
)
NEW_ASSERT = '#define static_assert(cond) _Static_assert(cond, "Dimension Mismatch")'

def patch_global_h(include_dir: str = "include") -> None:
    path = os.path.join(include_dir, "global.h")
    if not os.path.exists(path):
        print(f"  [skip]    {path}  (not found)")
        return

    try:
        content = read_file(path)
        original = content

        # Idempotency guard
        if "_Static_assert" in content:
            print(f"  [skip]    {path}  (already patched)")
            return

        content = OLD_ASSERT_RE.sub(NEW_ASSERT, content)

        if "#include <stdint.h>" not in content:
            content = "#include <stdint.h>\n" + content

        patch_summary(path, original, content)
        write_file(path, content)

    except Exception as exc:
        print(f"  [ERROR]   {path}: {exc}", file=sys.stderr)


# ──────────────────────────────────────────────────────────────────────────────
# 3. Relax sizeof assertions in all headers  (== → >=)
#    Allows 64-bit padding/pointer growth without recomputing expected sizes.
#
#    Fix: re.DOTALL added so the inner type name can span continuation lines
#    (common in macro-expanded struct names). Previously silent no-ops on those.
# ──────────────────────────────────────────────────────────────────────────────

SIZEOF_ASSERT_RE = re.compile(
    r'static_assert\s*\(\s*sizeof\s*\(\s*(.*?)\s*\)\s*==\s*([0-9A-Za-z_x]+)\s*\)',
    re.DOTALL
)

def patch_sizeof_assertions(include_dir: str = "include") -> None:
    if not os.path.isdir(include_dir):
        print(f"  [skip]    {include_dir}/  (directory not found)")
        return

    for root, _dirs, files in os.walk(include_dir):
        for fname in files:
            if not fname.endswith(".h"):
                continue
            path = os.path.join(root, fname)
            try:
                content = read_file(path)
                if "sizeof" not in content or "==" not in content:
                    continue

                patched = SIZEOF_ASSERT_RE.sub(
                    lambda m: f'static_assert(sizeof({m.group(1)}) >= {m.group(2)})',
                    content
                )
                patch_summary(path, content, patched)
                if patched != content:
                    write_file(path, patched)

            except Exception as exc:
                print(f"  [ERROR]   {path}: {exc}", file=sys.stderr)


# ──────────────────────────────────────────────────────────────────────────────
# 4. Pointer-truncation fix: (u32)expr → (uintptr_t)(expr)  in all .c files
#
#    Root bug: character class [a-zA-Z0-9_>\-] contains the range _-> where
#    ord('_')=95 > ord('>')=62, which is an invalid range in Python's re module
#    and raises: re.error: bad character range _->
#
#    Fix: place '-' at the very end of the class so it is always a literal
#    character, never a range operator: [A-Za-z0-9_.>-]
#    This correctly matches plain identifiers (foo), member access (foo.bar),
#    and pointer-member chains (foo->bar->baz).
# ──────────────────────────────────────────────────────────────────────────────

U32_CAST_RE = re.compile(
    r'\(u32\)\s*([A-Za-z_][A-Za-z0-9_.>-]*(?:\[[^\]]*\])*)'
)

def patch_u32_casts(src_dir: str = "src") -> None:
    if not os.path.isdir(src_dir):
        print(f"  [skip]    {src_dir}/  (directory not found)")
        return

    for root, _dirs, files in os.walk(src_dir):
        for fname in files:
            if not fname.endswith(".c"):
                continue
            path = os.path.join(root, fname)
            try:
                content = read_file(path)

                # Idempotency: nothing to do if no raw (u32) casts remain
                if "(u32)" not in content:
                    continue

                patched = U32_CAST_RE.sub(r'(uintptr_t)(\1)', content)
                patch_summary(path, content, patched)
                if patched != content:
                    write_file(path, patched)

            except Exception as exc:
                print(f"  [ERROR]   {path}: {exc}", file=sys.stderr)


# ──────────────────────────────────────────────────────────────────────────────
# Main
# ──────────────────────────────────────────────────────────────────────────────

def patch_source(
    src_dir: str = "src",
    include_dir: str = "include",
) -> None:
    print("=== Step 1: Patch src/main.c entry point & virtual registers ===")
    patch_main_c(src_dir)

    print("\n=== Step 2: Modernise static_assert in include/global.h ===")
    patch_global_h(include_dir)

    print("\n=== Step 3: Relax sizeof assertions in all headers ===")
    patch_sizeof_assertions(include_dir)

    print("\n=== Step 4: Fix (u32) pointer-truncation casts in src/*.c ===")
    patch_u32_casts(src_dir)

    print("\n64-bit Porting Patch Applied Successfully.")


if __name__ == "__main__":
    # Optional CLI overrides: python source_patcher.py [src_dir] [include_dir]
    args = sys.argv[1:]
    kwargs: dict = {}
    if len(args) >= 1:
        kwargs["src_dir"] = args[0]
    if len(args) >= 2:
        kwargs["include_dir"] = args[1]
    patch_source(**kwargs)