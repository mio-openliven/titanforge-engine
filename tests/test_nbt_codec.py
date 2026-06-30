import unittest

from titanforge.exporters.nbt_codec import NbtByte, NbtLong, read_nbt, write_nbt


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

    def test_write_and_read_explicit_byte_and_long_tags(self) -> None:
        payload = {
            "difficulty": NbtByte(2),
            "lastPlayed": NbtLong(4_671_000_000),
        }

        encoded = write_nbt("", payload)
        _name, decoded = read_nbt(encoded)

        self.assertEqual(decoded["difficulty"], 2)
        self.assertEqual(decoded["lastPlayed"], 4_671_000_000)
