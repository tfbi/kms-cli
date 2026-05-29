package gokms

import (
	"os"
	"path/filepath"
	"testing"
)

const testConfig = `
base_url = "https://kms.example.test"
token = "abc"

[endpoints.me]
method = "GET"
path = "/me"

[endpoints.kbs]
method = "POST"
path = "/kbs"

[endpoints.channels]
method = "GET"
path = "/channels"

[endpoints.faqs]
method = "POST"
path = "/faqs"

[endpoints.faq_detail]
method = "GET"
path = "/faq"
`

func writeConfig(t *testing.T, text string) string {
	t.Helper()
	path := filepath.Join(t.TempDir(), "config.toml")
	if err := os.WriteFile(path, []byte(text), 0o600); err != nil {
		t.Fatal(err)
	}
	return path
}

func TestLoadConfigReadsRequiredFields(t *testing.T) {
	config, err := LoadConfig(writeConfig(t, testConfig))
	if err != nil {
		t.Fatal(err)
	}

	if config.BaseURL != "https://kms.example.test" {
		t.Fatalf("BaseURL = %q", config.BaseURL)
	}
	if config.Token != "abc" {
		t.Fatalf("Token = %q", config.Token)
	}
	if config.Endpoints["kbs"] != (EndpointConfig{Method: "POST", Path: "/kbs"}) {
		t.Fatalf("kbs endpoint = %#v", config.Endpoints["kbs"])
	}
}

func TestLoadConfigRequiresKbsEndpoint(t *testing.T) {
	_, err := LoadConfig(writeConfig(t, `
base_url = "https://kms.example.test"

[endpoints.me]
method = "GET"
path = "/me"
`))
	if err == nil {
		t.Fatal("expected missing endpoint error")
	}
}
