from __future__ import annotations

import math
import unittest

from src.budget import AgreementBudgetAllocator, ItemNeed


class BudgetTests(unittest.TestCase):
    def test_prefers_uncertain(self):
        items = [
            ItemNeed("easy", 0.05, 0.0),
            ItemNeed("hard", 0.9, 0.6),
        ]
        allocations = AgreementBudgetAllocator(5).allocate(items)
        alloc = {allocation.item_id: allocation.labels for allocation in allocations}
        self.assertGreater(alloc.get("hard", 0), alloc.get("easy", 0))
        self.assertLessEqual(sum(alloc.values()), 5)

    def test_underfunded_baseline_prioritizes_need(self):
        items = [
            ItemNeed("easy", 0.0, 0.0),
            ItemNeed("hard", 1.0, 1.0),
            ItemNeed("medium", 0.5, 0.2),
        ]
        out = AgreementBudgetAllocator(2).allocate(items)
        self.assertEqual([allocation.item_id for allocation in out], ["hard", "medium"])

    def test_per_item_ceiling_and_global_budget_hold(self):
        items = [ItemNeed(f"item-{idx}", 1.0, 1.0) for idx in range(3)]
        out = AgreementBudgetAllocator(20, max_per_item=2).allocate(items)
        self.assertEqual(sum(allocation.labels for allocation in out), 6)
        self.assertTrue(all(allocation.labels <= 2 for allocation in out))

    def test_easy_items_do_not_consume_extra_rounds(self):
        items = [ItemNeed("a", 0.1, 0.1), ItemNeed("b", 0.2, 0.1)]
        out = AgreementBudgetAllocator(10).allocate(items)
        self.assertEqual({allocation.item_id: allocation.labels for allocation in out}, {"b": 1, "a": 1})

    def test_ties_are_deterministic_by_item_id(self):
        items = [ItemNeed("z", 0.5, 0.5), ItemNeed("a", 0.5, 0.5)]
        first = AgreementBudgetAllocator(1).allocate(items)
        second = AgreementBudgetAllocator(1).allocate(list(reversed(items)))
        self.assertEqual(first, second)
        self.assertEqual(first[0].item_id, "a")

    def test_duplicate_ids_refuse(self):
        with self.assertRaisesRegex(ValueError, "duplicate item_id"):
            AgreementBudgetAllocator(2).allocate(
                [ItemNeed("same", 0.2, 0.2), ItemNeed("same", 0.8, 0.8)]
            )

    def test_invalid_normalized_inputs_refuse(self):
        for value in (-0.1, 1.1, math.inf, math.nan):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    AgreementBudgetAllocator(1).allocate([ItemNeed("x", value, 0.1)])

    def test_invalid_allocator_limits_refuse(self):
        with self.assertRaises(ValueError):
            AgreementBudgetAllocator(0)
        with self.assertRaises(ValueError):
            AgreementBudgetAllocator(1, max_per_item=0)


if __name__ == "__main__":
    unittest.main()
