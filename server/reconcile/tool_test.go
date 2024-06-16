package reconcile

import (
	"os"
	"testing"
)

func Test_ParseToolSpec(t *testing.T) {
	data, err := os.ReadFile("tool.spec.json")
	if err != nil {
		t.Fatal(err)
	}
	_, _, err = parseToolSpec(data)
	if err != nil {
		t.Fatal(err)
	}
}
