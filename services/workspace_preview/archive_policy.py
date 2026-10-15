"""Fail closed on ZIP content the engine may skip; never extract to disk.

This is a completeness gate, not a malware verdict. Nested archives remain held
until independently bounded recursive scanning has been accepted.
"""
import io
import struct
import time
import zipfile


def zip_complete(data):
    """Return False for unsupported, malformed, encrypted or over-budget ZIPs."""
    signatures = (b'PK\x03\x04', b'PK\x05\x06', b'PK\x07\x08')
    end = data.rfind(b'PK\x05\x06', max(0, len(data) - 65557))
    if end < 0:
        return not data.startswith(signatures)
    try:
        # Bound central-directory allocation before ZipFile constructs its list.
        disk, central_disk, local_count, count, size, offset, comment = struct.unpack_from('<4H2IH', data, end + 4)
        if (disk or central_disk or local_count != count or count > 1000
                or end + 22 + comment != len(data) or offset + size != end
                or b'PK\x06\x07' in data[max(0, end - 20):end]):
            return False
        cursor = offset
        for _ in range(count):
            if data[cursor:cursor + 4] != b'PK\x01\x02' or cursor + 46 > end:
                return False
            name_size, extra_size, comment_size = struct.unpack_from('<3H', data, cursor + 28)
            cursor += 46 + name_size + extra_size + comment_size
            if cursor > end:
                return False
        if cursor != end:
            return False
        deadline = time.monotonic() + 5
        total = 0
        with zipfile.ZipFile(io.BytesIO(data)) as archive:
            entries = archive.infolist()
            if len(entries) != count:
                return False
            for entry in entries:
                if (entry.flag_bits & 1 or entry.file_size > 10 * 1024 * 1024
                        or entry.compress_type not in (zipfile.ZIP_STORED, zipfile.ZIP_DEFLATED)):
                    return False
                expanded = 0
                tail = b''
                with archive.open(entry) as member:
                    while True:
                        if time.monotonic() > deadline:
                            return False
                        chunk = member.read(65536)
                        if not chunk:
                            break
                        expanded += len(chunk)
                        total += len(chunk)
                        if expanded > 10 * 1024 * 1024 or total > 50 * 1024 * 1024:
                            return False
                        # Conservative hold for nested ZIP, including embedded ZIPs.
                        window = tail + chunk
                        if any(marker in window for marker in signatures):
                            return False
                        tail = window[-3:]
                if expanded != entry.file_size:
                    return False
        return True
    except (OSError, ValueError, RuntimeError, EOFError, NotImplementedError, struct.error, zipfile.BadZipFile):
        return False
