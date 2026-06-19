import unittest

from titanforge.exporters.nbt_codec import read_nbt, write_nbt


class NbtCodecTests(unittest.TestCase):
    def test_write_and_read_simple_compound(self) -> None:
        payload = {
            "targetVersion": "1.21.11",
            "supported": True,
            "baseY": 64,
            "notes": ["hello", "world"],
            "nested": {"x": 1, "label": "alpha"},
        }

        encoded = write_nbt("TitanForgeFixture", payload)
        name, decoded = read_nbt(encoded)

        self.assertEqual(name, "TitanForgeFixture")
        self.assertEqual(decoded["targetVersion"], "1.21.11")
        self.assertEqual(decoded["supported"], True)
        self.assertEqual(decoded["baseY"], 64)
        self.assertEqual(decoded["notes"], ["hello", "world"])
        self.assertEqual(decoded["nested"]["label"], "alpha")
