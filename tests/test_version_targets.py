import unittest

from titanforge.versions.targets import ACTIVE_TARGETS, PARKING_LOT_TARGETS, PRIMARY_TARGET


class VersionTargetTests(unittest.TestCase):
    def test_primary_target_is_modern_product_target(self) -> None:
        self.assertEqual(PRIMARY_TARGET.minecraft_version, "1.21.11")

    def test_active_targets_are_narrow(self) -> None:
        versions = {target.minecraft_version for target in ACTIVE_TARGETS}

        self.assertEqual(versions, {"1.21.11", "1.20.1", "1.12.2"})

    def test_deferred_versions_are_parking_lot_only(self) -> None:
        versions = {target.minecraft_version for target in PARKING_LOT_TARGETS}

        self.assertEqual(versions, {"1.19.2", "1.18.2", "1.16.5"})
