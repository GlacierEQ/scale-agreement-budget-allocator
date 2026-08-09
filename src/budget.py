"""Agreement budget allocator — spend labels where uncertainty is high."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence


@dataclass(frozen=True)
class ItemNeed:
    item_id: str
    model_uncertainty: float  # 0..1
    prior_disagreement: float  # 0..1


@dataclass(frozen=True)
class Allocation:
    item_id: str
    labels: int


class AgreementBudgetAllocator:
    def __init__(self, total_labels: int, max_per_item: int = 5):
        if total_labels < 1:
            raise ValueError("total_labels")
        self.total = total_labels
        self.max_per_item = max_per_item

    def allocate(self, items: Sequence[ItemNeed]) -> list[Allocation]:
        if not items:
            return []
        # score need
        scored = sorted(
            items,
            key=lambda i: i.model_uncertainty * 0.7 + i.prior_disagreement * 0.3,
            reverse=True,
        )
        # baseline 1 each if budget allows
        alloc = {i.item_id: 0 for i in items}
        remaining = self.total
        for i in scored:
            if remaining <= 0:
                break
            alloc[i.item_id] = 1
            remaining -= 1
        # extra rounds on highest need
        while remaining > 0:
            progressed = False
            for i in scored:
                if remaining <= 0:
                    break
                if alloc[i.item_id] < self.max_per_item and (
                    i.model_uncertainty >= 0.4 or i.prior_disagreement >= 0.3
                ):
                    alloc[i.item_id] += 1
                    remaining -= 1
                    progressed = True
            if not progressed:
                break
        return [Allocation(k, v) for k, v in alloc.items() if v > 0]
