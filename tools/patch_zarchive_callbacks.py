#!/usr/bin/env python3
"""Repair missing ZArchiveReader::OpenFromCallbacks in pinned Rodrigo Cemu dependency.

The Cemu UWP fork reads WUA archives through VirtualFile::Stream and depends on
a callback-based ZArchiveReader API that the pinned Exzap/ZArchive submodule
does not provide. This patch ADDS that reader API; never copies entire WUAs
to temporary disk storage. Applied to checkout only, without mutating upstream.
"""
from pathlib import Path
import sys

root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("ports/Cemu")
header = root / "dependencies/ZArchive/include/zarchive/zarchivereader.h"
source = root / "dependencies/ZArchive/src/zarchivereader.cpp"

def change(text, old, new, expected=1):
    found = text.count(old)
    if found != expected:
        raise RuntimeError(f"ZArchive source mismatch: {old[:95]!r} expected {expected}, got {found}")
    return text.replace(old, new)

h = header.read_text(encoding="utf-8-sig")
s = source.read_text(encoding="utf-8-sig")

h = change(h, "#include <fstream>", "#include <fstream>\n#include <functional>")
h = change(h,
    "static ZArchiveReader* OpenFromFile(const std::filesystem::path& path);",
    """using ReadCallback = std::function<bool(uint64_t, void*, uint32_t)>;
\tstatic ZArchiveReader* OpenFromFile(const std::filesystem::path& path);
\tstatic ZArchiveReader* OpenFromCallbacks(uint64_t fileSize, ReadCallback readBytes);""")
h = change(h, "ZArchiveReader(std::ifstream&& file,",
           "ZArchiveReader(ReadCallback readBytes,")
h = change(h, "std::ifstream m_file;", "ReadCallback m_reader;")

# Keep the original validation and parsing code after the '// read footer'
# marker. Replace only its file opening setup with a closure retained by the
# reader, so both on-disk and WinRT-brokered archives use identical bounds checks.
start = s.index("ZArchiveReader* ZArchiveReader::OpenFromFile(const std::filesystem::path& path)")
end = s.index("\t// read footer", start)
new_open = """ZArchiveReader* ZArchiveReader::OpenFromFile(const std::filesystem::path& path)
{
\tauto file = std::make_shared<std::ifstream>(path, std::ios_base::in | std::ios_base::binary);
\tif (!file->is_open())
\t\treturn nullptr;
\tfile->seekg(0, std::ios_base::end);
\tconst std::streampos pos = file->tellg();
\tif (pos < 0)
\t\treturn nullptr;
\tconst uint64_t size = static_cast<uint64_t>(pos);
\treturn OpenFromCallbacks(size, [file](uint64_t offset, void* buffer, uint32_t bytes) {
\t\tif (offset > static_cast<uint64_t>((std::numeric_limits<std::streamoff>::max)()))
\t\t\treturn false;
\t\tfile->clear();
\t\tfile->seekg(static_cast<std::streamoff>(offset), std::ios_base::beg);
\t\tif (!*file)
\t\t\treturn false;
\t\tfile->read(static_cast<char*>(buffer), bytes);
\t\treturn file->gcount() == static_cast<std::streamsize>(bytes);
\t});
}

ZArchiveReader* ZArchiveReader::OpenFromCallbacks(uint64_t fileSize, ReadCallback readBytes)
{
\tif (!readBytes || fileSize <= sizeof(_ZARCHIVE::Footer))
\t\treturn nullptr;
"""
s=s[:start]+new_open+s[end:]
s=change(s, "#include <fstream>", "#include <fstream>\n#include <memory>\n#include <limits>")
s=change(s, "_ifstream_readBytes(file, ", "readBytes(", 4)
s=change(s, "new ZArchiveReader(std::move(file),",
           "new ZArchiveReader(std::move(readBytes),")
s=change(s, "ZArchiveReader::ZArchiveReader(std::ifstream&& file,",
           "ZArchiveReader::ZArchiveReader(ReadCallback readBytes,")
s=change(s, "m_file(std::move(file))", "m_reader(std::move(readBytes))")
s=change(s, "_ifstream_readBytes(m_file, ", "m_reader(", 2)

# Fail closed rather than compiling a partially converted random-access path.
assert "OpenFromCallbacks(uint64_t fileSize, ReadCallback readBytes)" in s
assert "_ifstream_readBytes(m_file" not in s
assert "m_file(std::move(file))" not in s
assert "OpenFromCallbacks(uint64_t fileSize, ReadCallback readBytes);" in h
header.write_text(h, encoding="utf-8", newline="\n")
source.write_text(s, encoding="utf-8", newline="\n")
print("ZArchive FIX: callback-based WUA reader added; pinned dependency now matches Rodrigo Cemu API.")
