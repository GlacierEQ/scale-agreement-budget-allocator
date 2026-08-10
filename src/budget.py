"""Agreement budget allocator — spend finite annotation budget where need is highest.

The allocator owns deterministic budget allocation only. It does not infer label
truth, measure annotator quality, detect collusion, or execute labeling jobs.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Sequence


@dataclass(frozen=True)
class ItemNeed:
    item_id: str
    model_uncertainty: float  # normalized to 0..1
    prior_disagreement: float  # normalized to 0..1


@dataclass(frozen=True)
class Allocation:
    item_id: str
    labels: int


class AgreementBudgetAllocator:
    """Allocate a bounded label budget with deterministic uncertainty priority."""

    def __init__(self, total_labels: int, max_per_item: int = 5):
        if total_labels < 1:
            raise ValueError("total_labels must be positive")
        if max_per_item < 1:
            raise ValueError("max_per_item must be positive")
        self.total = total_labels
        self.max_per_item = max_per_item

    @staticmethod
    def _score(item: ItemNeed) -> float:
        return item.model_uncertainty * 0.7 + item.prior_disagreement * 0.3

    @staticmethod
    def _validate(items: Sequence[ItemNeed]) -> None:
        seen: set[str] = set()
        for item in items:
            if not item.item_id.strip():
                raise ValueError("item_id must be non-empty")
            if item.item_id in seen:
                raise ValueError(f"duplicate item_id: {item.item_id}")
            seen.add(item.item_id)
            for name, value in (
                ("model_uncertainty", item.model_uncertainty),
                ("prior_disagreement", item.prior_disagreement),
            ):
                if not math.isfinite(value) or not 0.0 <= value <= 1.0:
                    raise ValueError(f"{name} must be finite and in [0,1]")

    def allocate(self, items: Sequence[ItemNeed]) -> list[Allocation]:
        if not items:
            return []
        self._validate(items)

        # Highest need wins; item_id is an explicit deterministic tie-breaker so
        # allocations do not depend on caller iteration order.
        scored = sorted(items, key=lambda item: (-self._score(item), item.item_id))
        allocated = {item.item_id: 0 for item in scored}
        remaining = self.total

        # Baseline coverage follows priority if the global budget cannot provide
        # one label to every item.
        for item in scored:
            if remaining == 0:
                break
            allocated[item.item_id] = 1
            remaining -= 1

        # Additional agreement labels are spent only on items with material
        # uncertainty/disagreement, while respecting the per-item ceiling.
        while remaining > 0:
            progressed = False
            for item in scored:
                if remaining == 0:
                    break
                if allocated[item.item_id] >= self.max_per_item:
                    continue
                if item.model_uncertainty < 0.4 and item.prior_disagreement < 0.3:
                    continue
                allocated[item.item_id] += 1
                remaining -= 1
                progressed = True
            if not progressed:
                break

        result = [
            Allocation(item.item_id, allocated[item.item_id])
            for item in scored
            if allocated[item.item_id] > 0
        ]
        if sum(allocation.labels for allocation in result) > self.total:
            raise AssertionError("allocator exceeded global label budget")
        if any(allocation.labels > self.max_per_item for allocation in result):
            raise AssertionError("allocator exceeded per-item label budget")
        return result
