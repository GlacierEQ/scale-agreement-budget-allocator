package budget

import "sort"

type Item struct {
	ID          string
	Uncertainty float64
	Disagreement float64
}

type Alloc struct {
	ID     string
	Labels int
}

func Allocate(items []Item, total, maxPer int) []Alloc {
	type scored struct {
		Item
		score float64
	}
	ss := make([]scored, len(items))
	for i, it := range items {
		ss[i] = scored{it, it.Uncertainty*0.7 + it.Disagreement*0.3}
	}
	sort.Slice(ss, func(i, j int) bool { return ss[i].score > ss[j].score })
	alloc := map[string]int{}
	rem := total
	for _, s := range ss {
		if rem <= 0 {
			break
		}
		alloc[s.ID] = 1
		rem--
	}
	for rem > 0 {
		progress := false
		for _, s := range ss {
			if rem <= 0 {
				break
			}
			if alloc[s.ID] < maxPer && (s.Uncertainty >= 0.4 || s.Disagreement >= 0.3) {
				alloc[s.ID]++
				rem--
				progress = true
			}
		}
		if !progress {
			break
		}
	}
	out := []Alloc{}
	for id, n := range alloc {
		if n > 0 {
			out = append(out, Alloc{id, n})
		}
	}
	return out
}
