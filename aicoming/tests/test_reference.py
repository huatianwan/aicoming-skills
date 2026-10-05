import importlib.util, json, unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("gen_reference", ROOT / "tools" / "gen_reference.py")
GEN = importlib.util.module_from_spec(SPEC); assert SPEC.loader; SPEC.loader.exec_module(GEN)

class ReferenceTest(unittest.TestCase):
    def test_every_manifest_endpoint_is_rendered(self):
        manifest = json.loads((ROOT / "references" / "manifest.snapshot.json").read_text("utf-8")); rendered = GEN.render(manifest)
        for endpoint in manifest["endpoints"]: self.assertIn(f"`{endpoint['path']}`", rendered)
        self.assertIn("DO NOT EDIT", rendered); self.assertIn("manifest-sha256", rendered)
    def test_tool_routes_are_not_public(self):
        manifest = json.loads((ROOT / "references" / "manifest.snapshot.json").read_text("utf-8"))
        self.assertFalse(any(str(ep["path"]).startswith("/v1/tool/") for ep in manifest["endpoints"]))

if __name__ == "__main__": unittest.main()
