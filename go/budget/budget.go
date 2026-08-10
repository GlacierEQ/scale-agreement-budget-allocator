package budget

import (
	"fmt"
	"math"
	"sort"
)

type Item struct {
	ID           string
	Uncertainty  float64
	Disagreement float64
}

type Alloc struct {
	ID     string
	Labels int
}

type scored struct {
	Item
	score float64
}

func validate(items []Item, total, maxPer int) error {
	if total < 1 {
		return fmt.Errorf("total must be positive")
	}
	if maxPer < 1 {
		return fmt.Errorf("maxPer must be positive")
	}
	seen := map[string]struct{}{}
	for _, item := range items {
		if item.ID == "" {
			return fmt.Errorf("item ID must be non-empty")
		}
		if _, ok := seen[item.ID]; ok {
			return fmt.Errorf("duplicate item ID: %s", item.ID)
		}
		seen[item.ID] = struct{}{}
		if math.IsNaN(item.Uncertainty) || math.IsInf(item.Uncertainty, 0) || item.Uncertainty < 0 || item.Uncertainty > 1 {
			return fmt.Errorf("uncertainty must be finite and in [0,1]")
		}
		if math.IsNaN(item.Disagreement) || math.IsInf(item.Disagreement, 0) || item.Disagreement < 0 || item.Disagreement > 1 {
			return fmt.Errorf("disagreement must be finite and in [0,1]")
		}
	}
	return nil
}

// AllocateChecked returns a deterministic bounded allocation or an explicit
// validation error. Higher uncertainty is weighted 0.7 and prior disagreement
// 0.3; ID is the deterministic tie-breaker.
func AllocateChecked(items []Item, total, maxPer int) ([]Alloc, error) {
	if err := validate(items, total, maxPer); err != nil {
		return nil, err
	}
	if len(items) == 0 {
		return []Alloc{}, nil
	}

	ss := make([]scored, len(items))
	for i, item := range items {
		ss[i] = scored{Item: item, score: item.Uncertainty*0.7 + item.Disagreement*0.3}
	}
	sort.Slice(ss, func(i, j int) bool {
		if ss[i].score == ss[j].score {
			return ss[i].ID < ss[j].ID
		}
		return ss[i].score > ss[j].score
	})

	allocated := map[string]int{}
	remaining := total
	for _, item := range ss {
		if remaining == 0 {
			break
		}
		allocated[item.ID] = 1
		remaining--
	}

	for remaining > 0 {
		progressed := false
		for _, item := range ss {
			if remaining == 0 {
				break
			}
			if allocated[item.ID] >= maxPer {
				continue
			}
			if item.Uncertainty < 0.4 && item.Disagreement < 0.3 {
				continue
			}
			allocated[item.ID]++
			remaining--
			progressed = true
		}
		if !progressed {
			break
		}
	}

	out := make([]Alloc, 0, len(allocated))
	used := 0
	for _, item := range ss {
		labels := allocated[item.ID]
		if labels == 0 {
			continue
		}
		if labels > maxPer {
			return nil, fmt.Errorf("allocator exceeded per-item budget")
		}
		used += labels
		out = append(out, Alloc{ID: item.ID, Labels: labels})
	}
	if used > total {
		return nil, fmt.Errorf("allocator exceeded global budget")
	}
	return out, nil
}

// Allocate preserves the original simple API. Invalid input fails closed with
// no allocation; callers that need the reason should use AllocateChecked.
func Allocate(items []Item, total, maxPer int) []Alloc {
	out, err := AllocateChecked(items, total, maxPer)
	if err != nil {
		return nil
	}
	return out
}
