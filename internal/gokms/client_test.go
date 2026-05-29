package gokms

import (
	"bytes"
	"encoding/json"
	"io"
	"net/http"
	"testing"
)

type roundTripFunc func(*http.Request) (*http.Response, error)

func (f roundTripFunc) RoundTrip(request *http.Request) (*http.Response, error) {
	return f(request)
}

func jsonResponse(status int, body string) *http.Response {
	return &http.Response{
		StatusCode: status,
		Header:     make(http.Header),
		Body:       io.NopCloser(bytes.NewBufferString(body)),
	}
}

func testClientConfig(baseURL string) Config {
	return Config{
		BaseURL: baseURL,
		Token:   "abc",
		Endpoints: map[string]EndpointConfig{
			"me":         {Method: "GET", Path: "/me"},
			"kbs":        {Method: "POST", Path: "/kbs"},
			"channels":   {Method: "GET", Path: "/channels"},
			"faqs":       {Method: "POST", Path: "/faqs"},
			"faq_detail": {Method: "GET", Path: "/faq"},
		},
	}
}

func TestClientSendsExpectedParameters(t *testing.T) {
	var seenMethod string
	var seenPath string
	var seenTenant string
	var seenBody map[string]any

	httpClient := &http.Client{Transport: roundTripFunc(func(request *http.Request) (*http.Response, error) {
		seenMethod = request.Method
		seenPath = request.URL.RequestURI()
		seenTenant = request.Header.Get("tenant-id")
		if request.Body != nil {
			_ = json.NewDecoder(request.Body).Decode(&seenBody)
		}
		return jsonResponse(200, `{"items":[]}`), nil
	})}
	client := NewClientWithHTTP(testClientConfig("https://kms.example.test"), "abc", httpClient)

	if _, err := client.Kbs(3, 40); err != nil {
		t.Fatal(err)
	}
	if seenMethod != "POST" || seenBody["pageNo"] != float64(3) || seenBody["pageSize"] != float64(40) {
		t.Fatalf("kbs request = %s %#v", seenMethod, seenBody)
	}
	if seenTenant != "2" {
		t.Fatalf("tenant-id = %q", seenTenant)
	}

	if _, err := client.Channels("kb-1"); err != nil {
		t.Fatal(err)
	}
	if seenMethod != "GET" || seenPath != "/channels?authorityType=0&knowledgeId=kb-1&type=1" {
		t.Fatalf("channels request = %s %s", seenMethod, seenPath)
	}

	if _, err := client.FAQs("ch-1", 2, 10); err != nil {
		t.Fatal(err)
	}
	if seenMethod != "POST" || seenBody["channelId"] != "ch-1" || seenBody["pageNo"] != float64(2) || seenBody["pageSize"] != float64(10) {
		t.Fatalf("faqs request = %s %#v", seenMethod, seenBody)
	}

	if _, err := client.FAQDetail("faq-1"); err != nil {
		t.Fatal(err)
	}
	if seenMethod != "GET" || seenPath != "/faq?faqId=faq-1" {
		t.Fatalf("faq request = %s %s", seenMethod, seenPath)
	}
}

func TestClientDefaultPaginationUsesPageSizeTen(t *testing.T) {
	var seenBody map[string]any
	httpClient := &http.Client{Transport: roundTripFunc(func(request *http.Request) (*http.Response, error) {
		_ = json.NewDecoder(request.Body).Decode(&seenBody)
		return jsonResponse(200, `{"items":[]}`), nil
	})}
	client := NewClientWithHTTP(testClientConfig("https://kms.example.test"), "abc", httpClient)

	if _, err := client.Kbs(1, 10); err != nil {
		t.Fatal(err)
	}

	if seenBody["pageNo"] != float64(1) || seenBody["pageSize"] != float64(10) {
		t.Fatalf("default pagination body = %#v", seenBody)
	}
}
