import errno
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import factory


class PersistenceTests(unittest.TestCase):
    def test_disk_failure_preserves_previous_ledger(self):
        with tempfile.TemporaryDirectory() as root:
            path=Path(root)/'budget.json';factory.save(path,{'reserved':1})
            original=path.read_bytes()
            with patch('factory.os.replace',side_effect=OSError(errno.ENOSPC,'full')):
                with self.assertRaises(OSError):factory.save(path,{'reserved':2})
            self.assertEqual(path.read_bytes(),original)
            self.assertEqual(list(Path(root).iterdir()),[path])


if __name__=='__main__':unittest.main()
