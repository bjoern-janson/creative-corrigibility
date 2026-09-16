import ast
import pathlib
import unittest

from creative_corrigibility.model import ApparatusStatus, Phenotype


ROOT = pathlib.Path(__file__).resolve().parents[1]


class ArchitectureTests(unittest.TestCase):
    def test_apparatus_status_and_scientific_phenotype_are_distinct_types(self):
        self.assertIsNot(ApparatusStatus, Phenotype)
        self.assertNotEqual(ApparatusStatus.CALIBRATION_PASS.value, Phenotype.CONTROL.value)

    def test_measurement_has_no_calibration_or_prospective_runtime_dependency(self):
        path = ROOT / "src" / "creative_corrigibility" / "measurement.py"
        tree = ast.parse(path.read_text(encoding="utf-8"))
        banned = {"calibration", "prospective", "mechanism"}
        seen = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                seen.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                seen.add(node.module or "")
        for name in seen:
            self.assertFalse(any(part in name.split(".") for part in banned), name)

    def test_engine_does_not_import_measurement(self):
        path = ROOT / "src" / "creative_corrigibility" / "engine.py"
        tree = ast.parse(path.read_text(encoding="utf-8"))
        seen = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                seen.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                seen.add(node.module or "")
        self.assertFalse(any("measurement" in name.split(".") for name in seen))


if __name__ == "__main__":
    unittest.main()
