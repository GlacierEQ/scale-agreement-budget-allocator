from __future__ import annotations

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load(path: str):
    return json.loads((ROOT / path).read_text())


CANONICAL = load("machine/canonical-position.json")
CAPABILITIES = load("machine/capabilities.json")
TARGET = load("machine/target-contract.json")
PROOF = load("machine/canonical-position-proof.json")


class CanonicalPositionContractTests(unittest.TestCase):
    def test_repository_owns_only_annotation_budget_allocation(self):
        self.assertEqual(CANONICAL["role"], "CANONICAL_SPECIALIST")
        self.assertEqual(CANONICAL["owns"], "uncertainty_weighted_annotation_budget_allocation")
        self.assertIn("label truth or adjudication", CANONICAL["does_not_own"])
        self.assertIn("annotator collusion detection", CANONICAL["does_not_own"])
        self.assertIn("train/eval contamination detection", CANONICAL["does_not_own"])

    def test_sibling_relationships_do_not_claim_integration(self):
        for edge in CANONICAL["relationships"]:
            self.assertFalse(edge["integration_exercised"])

    def test_capabilities_are_repository_native(self):
        capabilities = set(CAPABILITIES["capabilities"])
        self.assertNotIn("hyper-scaling", capabilities)
        self.assertIn("global_annotation_budget_guard", capabilities)
        self.assertIn("per_item_annotation_ceiling", capabilities)
        self.assertIn("deterministic_need_tie_break", capabilities)
        self.assertIn("python_go_allocation_parity", capabilities)

    def test_target_reflects_earned_canonical_position(self):
        self.assertEqual(TARGET["current"]["state"], "EVOLVING")
        self.assertFalse(TARGET["current"]["canonical_position_pending_exact_head_proof"])
        self.assertEqual(TARGET["promotion"]["next_gate"], "EVOLUTION_CURSOR_DEFINED")
        self.assertTrue(TARGET["evolution"]["cursor"].startswith("next:"))
        self.assertEqual(PROOF["result"], "PASS")
        self.assertEqual(PROOF["tested_source_sha"], "05356e957c2573246438785381bc23bd5c770ca8")

    def test_truth_boundary_excludes_quality_and_execution_claims(self):
        boundary = CAPABILITIES["truth_boundary"]
        self.assertIn("does not infer label truth", boundary)
        self.assertIn("detect collusion", boundary)
        self.assertIn("execute labeling jobs", boundary)


if __name__ == "__main__":
    unittest.main()
