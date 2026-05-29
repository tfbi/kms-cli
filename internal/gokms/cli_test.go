package gokms

import (
	"bytes"
	"net/http"
	"os"
	"strings"
	"testing"
)

func TestRunHelpShowsKbsOnly(t *testing.T) {
	var stdout bytes.Buffer
	code := Run([]string{"--help"}, nil, strings.NewReader(""), &stdout, &bytes.Buffer{})

	if code != 0 {
		t.Fatalf("code = %d", code)
	}
	output := stdout.String()
	if !strings.Contains(output, "kbs") {
		t.Fatalf("help missing kbs: %s", output)
	}
	if strings.Contains(output, "knowledge-bases") || strings.Contains(output, "spaces") {
		t.Fatalf("help contains old command: %s", output)
	}
}

func TestRunRetriesWithNewToken(t *testing.T) {
	calls := []string{}
	httpClient := &http.Client{Transport: roundTripFunc(func(request *http.Request) (*http.Response, error) {
		calls = append(calls, request.Header.Get("Authorization"))
		if len(calls) == 1 {
			return jsonResponse(http.StatusUnauthorized, `{"error":"expired"}`), nil
		}
		return jsonResponse(http.StatusOK, `{"id":"u1"}`), nil
	})}

	config := strings.ReplaceAll(testConfig, "https://kms.example.test", "https://kms.example.test")
	configPath := writeConfig(t, config)
	t.Setenv("KNOWLEDGE_TOKEN", "")

	var stdout bytes.Buffer
	var stderr bytes.Buffer
	input := strings.NewReader("new-token\nn\n")
	code := Run([]string{"--config", configPath, "me", "--json"}, httpClient, input, &stdout, &stderr)

	if code != 0 {
		t.Fatalf("code = %d stderr = %s", code, stderr.String())
	}
	if got := strings.Join(calls, ","); got != "Bearer abc,Bearer new-token" {
		t.Fatalf("calls = %s", got)
	}
	if !strings.Contains(stdout.String(), `"id": "u1"`) {
		t.Fatalf("stdout = %s", stdout.String())
	}

	if _, err := os.Stat(configPath); err != nil {
		t.Fatal(err)
	}
}
