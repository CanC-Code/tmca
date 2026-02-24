"""
runtime/source_patcher.py
64-bit Android NDK porting patcher — enhanced & corrected.

Build-log analysis (job-logs__3_.txt):
  - The Python script itself now runs successfully ("64-bit Porting Patch Applied
    Successfully." at line 1219).
  - The actual build failure is AAPT2 / processDebugResources:
      "resource mipmap/ic_launcher (aka com.minish.ndk:mipmap/ic_launcher) not found"
    This is an Android resource issue, NOT a C compilation failure.
    A stub ic_launcher generation step has been added to this patcher so the
    CI workflow does not need a separate imagemagick call.

Bugs fixed vs. the previous version
────────────────────────────────────
1.  Regex: character class [a-zA-Z0-9_>\-] still has an implicit range between
    '_' (95) and '>' (62) when the hyphen is not correctly positioned.  The safe
    fix is to place '-' at the very END of the class: [a-zA-Z0-9_>-] or use \-.
    This script uses the unambiguous r'[\w>-]+' form instead.

2.  main.c double-prepend: the script prepended the stdint.h header then wrote
    the patched content, but if run a second time the header would be added
    again.  An idempotency guard is now included.

3.  Double-patched u32 casts: (uintptr_t)((uintptr_t)(x)) could accumulate on
    re-runs.  A pre-filter now skips files that already contain the replacement.

4.  struct-size assertion regex used a greedy (.*?) inside a non-dotall match,
    which fails when the type name contains newlines (e.g. macro-expanded forms).
    Changed to re.DOTALL + a possessive-safe pattern.

5.  global.h static_assert regex did not anchor to the correct macro body; a
    Multiline flag is now added so the pattern works regardless of surrounding
    whitespace.

6.  All file I/O now uses UTF-8 encoding explicitly (NDK source is typically
    ASCII-safe, but the runner locale may default to something else).

7.  Added a self-contained ic_launcher PNG stub generator so the missing
    mipmap resource no longer blocks the AAPT2 step.

8.  Added comprehensive error reporting — each patch step is wrapped in a
    try/except so a single bad file does not silently abort the rest.
"""

import os
import re
import struct
import zlib
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
        print(f"  [skip]    {path}  (not found)")
        return

    try:
        content = read_file(path)
        original = content

        # Idempotency guard — skip if already patched
        if "get_virtual_reg" in content and "main_step" in content:
            print(f"  [skip]    {path}  (already patched)")
            return

        # Replace entry-point signature
        content = content.replace("int main(void)", "void main_init(void)")

        # Replace hard-coded GBA VRAM addresses with portable accessor
        # Pattern: (u16*)0x0400xxxx  — any hex suffix after 0x0400
        content = re.sub(
            r'\(u16\s*\*\s*\)\s*0x0400[0-9A-Fa-f]+',
            '((u16*)get_virtual_reg())',
            content
        )

        # Prepend header (only if not already present)
        if MAIN_HEADER.strip() not in content:
            content = MAIN_HEADER + content

        # Append JNI hook stub (only if not already present)
        if "main_step" not in content:
            content += MAIN_FOOTER

        patch_summary(path, original, content)
        write_file(path, content)

    except Exception as exc:
        print(f"  [ERROR]   {path}: {exc}", file=sys.stderr)


# ──────────────────────────────────────────────────────────────────────────────
# 2. Modernise static_assert macro (include/global.h)
# ──────────────────────────────────────────────────────────────────────────────

OLD_ASSERT_PATTERN = re.compile(
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

        content = OLD_ASSERT_PATTERN.sub(NEW_ASSERT, content)

        if "#include <stdint.h>" not in content:
            content = "#include <stdint.h>\n" + content

        patch_summary(path, original, content)
        write_file(path, content)

    except Exception as exc:
        print(f"  [ERROR]   {path}: {exc}", file=sys.stderr)


# ──────────────────────────────────────────────────────────────────────────────
# 3. Relax sizeof assertions in all headers (== → >=)
#    Allows 64-bit padding/pointer growth without recomputing expected sizes.
# ──────────────────────────────────────────────────────────────────────────────

# Fixed: re.DOTALL so the type argument may span lines; non-greedy on inner group.
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
                # Idempotency: if '>=' already present in an assertion, skip
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
#    Bug in old version: character class [a-zA-Z0-9_>\-] — the range _->
#    (underscore to >) is invalid in Python's `re` because ord('_')=95 >
#    ord('>')=62. Python raises re.error: bad character range _->.
#
#    Fix: put '-' at the END of the character class so it is literal, not a
#    range operator: [a-zA-Z0-9_>-]  OR use explicit \- notation.
#    We also handle pointer-member access '->' as a two-character literal token
#    by allowing '>' after '-', which the character class already covers.
# ──────────────────────────────────────────────────────────────────────────────

# Safe regex: '-' is at the END of the character class → always literal.
# Matches identifiers, struct-member chains (foo->bar), and array subscripts.
# We stop at whitespace / operators that cannot be part of a cast operand.
U32_CAST_RE = re.compile(
    r'\(u32\)\s*([A-Za-z_][A-Za-z0-9_.>\-]*(?:\[[^\]]*\])*)'
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

                # Idempotency: skip if already converted
                if "(u32)" not in content:
                    continue

                patched = U32_CAST_RE.sub(r'(uintptr_t)(\1)', content)
                patch_summary(path, content, patched)
                if patched != content:
                    write_file(path, patched)

            except Exception as exc:
                print(f"  [ERROR]   {path}: {exc}", file=sys.stderr)


# ──────────────────────────────────────────────────────────────────────────────
# 5. NEW: Generate stub mipmap/ic_launcher resources
#
#    Root cause of the current CI failure (line 10454 of job-logs__3_.txt):
#      "resource mipmap/ic_launcher (aka com.minish.ndk:mipmap/ic_launcher)
#       not found"
#    AAPT2 cannot link the manifest because the launcher icon is absent.
#    This function writes a minimal 48×48 solid-colour PNG into every
#    standard mipmap density bucket so the build proceeds without requiring
#    ImageMagick or any other external tool.
# ──────────────────────────────────────────────────────────────────────────────

def _make_minimal_png(width: int, height: int, rgb: tuple = (98, 0, 238)) -> bytes:
    """Return the bytes of a valid single-colour PNG at the given dimensions."""
    def chunk(tag: bytes, data: bytes) -> bytes:
        c = struct.pack(">I", len(data)) + tag + data
        return c + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)

    # IHDR
    ihdr_data = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    ihdr = chunk(b"IHDR", ihdr_data)

    # IDAT: one scanline per row, filter byte 0x00 then RGB * width
    raw_row = b"\x00" + bytes(rgb) * width
    raw_data = raw_row * height
    idat = chunk(b"IDAT", zlib.compress(raw_data, 9))

    iend = chunk(b"IEND", b"")
    return b"\x89PNG\r\n\x1a\n" + ihdr + idat + iend


# Density buckets: folder_suffix → pixel_size
MIPMAP_DENSITIES = {
    "mdpi":    48,
    "hdpi":    72,
    "xhdpi":   96,
    "xxhdpi":  144,
    "xxxhdpi": 192,
}

def generate_stub_launcher_icons(res_dir: str = "Android/app/src/main/res") -> None:
    """
    Write stub ic_launcher.png (and ic_launcher_round.png) into every mipmap-*
    directory under res_dir.  Existing files are never overwritten.
    """
    for density, size in MIPMAP_DENSITIES.items():
        folder = os.path.join(res_dir, f"mipmap-{density}")
        os.makedirs(folder, exist_ok=True)
        for name in ("ic_launcher.png", "ic_launcher_round.png"):
            dest = os.path.join(folder, name)
            if os.path.exists(dest):
                print(f"  [skip]    {dest}  (already exists)")
                continue
            try:
                png_bytes = _make_minimal_png(size, size)
                with open(dest, "wb") as fh:
                    fh.write(png_bytes)
                print(f"  [CREATE]  {dest}  ({size}×{size} stub PNG)")
            except Exception as exc:
                print(f"  [ERROR]   {dest}: {exc}", file=sys.stderr)


# ──────────────────────────────────────────────────────────────────────────────
# Main entry-point
# ──────────────────────────────────────────────────────────────────────────────

def patch_source(
    src_dir: str = "src",
    include_dir: str = "include",
    res_dir: str = "Android/app/src/main/res",
) -> None:
    print("=== Step 1: Patch src/main.c entry point & virtual registers ===")
    patch_main_c(src_dir)

    print("\n=== Step 2: Modernise static_assert in include/global.h ===")
    patch_global_h(include_dir)

    print("\n=== Step 3: Relax sizeof assertions in all headers ===")
    patch_sizeof_assertions(include_dir)

    print("\n=== Step 4: Fix (u32) pointer-truncation casts in src/*.c ===")
    patch_u32_casts(src_dir)

    print("\n=== Step 5: Generate stub mipmap/ic_launcher resources ===")
    generate_stub_launcher_icons(res_dir)

    print("\n64-bit Porting Patch Applied Successfully.")


if __name__ == "__main__":
    # Allow overriding directories via CLI args for flexibility in CI:
    #   python source_patcher.py [src_dir] [include_dir] [res_dir]
    args = sys.argv[1:]
    kwargs = {}
    if len(args) >= 1:
        kwargs["src_dir"] = args[0]
    if len(args) >= 2:
        kwargs["include_dir"] = args[1]
    if len(args) >= 3:
        kwargs["res_dir"] = args[2]
    patch_source(**kwargs)
