package budget

import (
	"math"
	"reflect"
	"testing"
)

func labels(out []Alloc) map[string]int {
	result := map[string]int{}
	for _, allocation := range out {
		result[allocation.ID] = allocation.Labels
	}
	return result
}

func TestPrefersUncertain(t *testing.T) {
	out, err := AllocateChecked([]Item{{"easy", 0.05, 0}, {"hard", 0.9, 0.6}}, 5, 5)
	if err != nil {
		t.Fatal(err)
	}
	m := labels(out)
	if m["hard"] <= m["easy"] {
		t.Fatalf("%v", m)
	}
}

func TestDeterministicTieBreak(t *testing.T) {
	first, err := AllocateChecked([]Item{{"z", 0.5, 0.5}, {"a", 0.5, 0.5}}, 1, 5)
	if err != nil {
		t.Fatal(err)
	}
	second, err := AllocateChecked([]Item{{"a", 0.5, 0.5}, {"z", 0.5, 0.5}}, 1, 5)
	if err != nil {
		t.Fatal(err)
	}
	if !reflect.DeepEqual(first, second) || len(first) != 1 || first[0].ID != "a" {
		t.Fatalf("nondeterministic allocation: first=%v second=%v", first, second)
	}
}

func TestBudgetAndPerItemCeilings(t *testing.T) {
	out, err := AllocateChecked([]Item{{"a", 1, 1}, {"b", 1, 1}, {"c", 1, 1}}, 20, 2)
	if err != nil {
		t.Fatal(err)
	}
	used := 0
	for _, allocation := range out {
		used += allocation.Labels
		if allocation.Labels > 2 {
			t.Fatalf("per-item ceiling violated: %v", out)
		}
	}
	if used != 6 {
		t.Fatalf("expected six usable labels, got %d: %v", used, out)
	}
}

func TestInvalidInputsFailClosed(t *testing.T) {
	cases := [][]Item{
		{{"same", 0.2, 0.2}, {"same", 0.8, 0.8}},
		{{"", 0.2, 0.2}},
		{{"x", -0.1, 0.2}},
		{{"x", 1.1, 0.2}},
		{{"x", math.NaN(), 0.2}},
	}
	for _, items := range cases {
		if out, err := AllocateChecked(items, 2, 5); err == nil || out != nil {
			t.Fatalf("expected refusal for %v, got out=%v err=%v", items, out, err)
		}
	}
	if out, err := AllocateChecked([]Item{{"x", 0.2, 0.2}}, 0, 5); err == nil || out != nil {
		t.Fatalf("invalid total did not refuse: out=%v err=%v", out, err)
	}
	if out := Allocate([]Item{{"x", 2, 0.2}}, 2, 5); out != nil {
		t.Fatalf("compatibility API must fail closed on invalid input: %v", out)
	}
}
