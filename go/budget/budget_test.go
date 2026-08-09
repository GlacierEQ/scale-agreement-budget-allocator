package budget

import "testing"

func TestPrefersUncertain(t *testing.T) {
	out := Allocate([]Item{{"easy", 0.05, 0}, {"hard", 0.9, 0.6}}, 5, 5)
	m := map[string]int{}
	for _, a := range out {
		m[a.ID] = a.Labels
	}
	if m["hard"] <= m["easy"] {
		t.Fatalf("%v", m)
	}
}
