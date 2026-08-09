from __future__ import annotations
import unittest
from src.budget import AgreementBudgetAllocator, ItemNeed

class BudgetTests(unittest.TestCase):
    def test_prefers_uncertain(self):
        items = [
            ItemNeed("easy", 0.05, 0.0),
            ItemNeed("hard", 0.9, 0.6),
        ]
        alloc = {a.item_id: a.labels for a in AgreementBudgetAllocator(5).allocate(items)}
        self.assertGreater(alloc.get("hard", 0), alloc.get("easy", 0))

if __name__ == "__main__":
    unittest.main()
