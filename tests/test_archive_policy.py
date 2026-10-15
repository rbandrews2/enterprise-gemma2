import io
import os
import struct
import unittest
import zipfile
from unittest.mock import patch

from services.workspace_preview.archive_policy import zip_complete
from services.workspace_preview.clamd_scanner import ClamdScanner
from services.workspace_preview.security import ClamAVScanner


def packed(contents=b'ordinary document', compression=zipfile.ZIP_DEFLATED):
    output = io.BytesIO()
    with zipfile.ZipFile(output, 'w', compression) as archive:
        archive.writestr('document.txt', contents)
    return output.getvalue()


class ArchivePolicyTests(unittest.TestCase):
    def test_plain_and_normal_zip(self):
        self.assertTrue(zip_complete(b'%PDF-1.7 ordinary document'))
        self.assertTrue(zip_complete(packed()))

    def test_oversized_expansion_and_nested_zip_are_held(self):
        self.assertFalse(zip_complete(packed(b'0' * (11 * 1024 * 1024))))
        self.assertFalse(zip_complete(packed(packed())))

    def test_malformed_encrypted_and_excess_entries_are_held(self):
        self.assertFalse(zip_complete(b'PK\x03\x04truncated'))
        data = bytearray(packed())
        central = data.index(b'PK\x01\x02')
        struct.pack_into('<H', data, central + 8, 1)
        self.assertFalse(zip_complete(bytes(data)))
        data = bytearray(packed())
        end = data.rindex(b'PK\x05\x06')
        struct.pack_into('<HH', data, end + 8, 1001, 1001)
        with patch('services.workspace_preview.archive_policy.zipfile.ZipFile') as parser:
            self.assertFalse(zip_complete(bytes(data)))
            parser.assert_not_called()

    def test_crc_failure_unsupported_compression_and_deadline(self):
        data = bytearray(packed(compression=zipfile.ZIP_STORED))
        data[data.index(b'ordinary document')] ^= 1
        self.assertFalse(zip_complete(bytes(data)))
        self.assertFalse(zip_complete(packed(compression=zipfile.ZIP_BZIP2)))
        with patch('services.workspace_preview.archive_policy.time.monotonic', side_effect=[0, 6]):
            self.assertFalse(zip_complete(packed()))

    def test_both_adapters_hold_without_contacting_engine(self):
        data = packed(packed())
        with patch.dict(os.environ, {'WZOS_CLAMD_SOCKET':'/private/clamd.sock',
                                     'WZOS_CLAMSCAN_PATH':'/private/clamscan'}):
            with patch.object(ClamdScanner, 'validate_policy') as validate, patch('services.workspace_preview.security.subprocess.run') as run:
                self.assertEqual(ClamdScanner().scan(data).status, 'error')
                self.assertEqual(ClamAVScanner().scan(data).status, 'error')
                validate.assert_not_called()
                run.assert_not_called()
