package gokms

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"net/url"
	"strings"
	"time"
)

type AuthError struct {
	Message string
}

func (e AuthError) Error() string {
	return e.Message
}

type Client struct {
	config     Config
	token      string
	httpClient *http.Client
}

func NewClient(config Config, token string) *Client {
	return NewClientWithHTTP(config, token, nil)
}

func NewClientWithHTTP(config Config, token string, httpClient *http.Client) *Client {
	if httpClient == nil {
		httpClient = &http.Client{Timeout: 20 * time.Second}
	}
	return &Client{config: config, token: token, httpClient: httpClient}
}

func (c *Client) WithToken(token string) *Client {
	return NewClientWithHTTP(c.config, token, c.httpClient)
}

func (c *Client) Me() (map[string]any, error) {
	return c.request("me", nil, nil)
}

func (c *Client) Kbs(page int, pageSize int) (map[string]any, error) {
	return c.request("kbs", nil, map[string]any{"pageNo": page, "pageSize": pageSize})
}

func (c *Client) Channels(knowledgeID string) (map[string]any, error) {
	return c.request("channels", map[string]string{
		"authorityType": "0",
		"knowledgeId":   knowledgeID,
		"type":          "1",
	}, nil)
}

func (c *Client) FAQs(channelID string, page int, pageSize int) (map[string]any, error) {
	return c.request("faqs", nil, map[string]any{
		"categoryId": channelID,
		"channelId":  channelID,
		"pageNo":     page,
		"pageSize":   pageSize,
	})
}

func (c *Client) FAQDetail(faqID string) (map[string]any, error) {
	return c.request("faq_detail", map[string]string{"faqId": faqID}, nil)
}

func (c *Client) request(endpointName string, params map[string]string, body map[string]any) (map[string]any, error) {
	endpoint := c.config.Endpoints[endpointName]
	requestURL := joinURL(c.config.BaseURL, endpoint.Path)
	if len(params) > 0 {
		parsed, err := url.Parse(requestURL)
		if err != nil {
			return nil, err
		}
		query := parsed.Query()
		for key, value := range params {
			query.Set(key, value)
		}
		parsed.RawQuery = query.Encode()
		requestURL = parsed.String()
	}

	var reader io.Reader
	if body != nil {
		encoded, err := json.Marshal(body)
		if err != nil {
			return nil, err
		}
		reader = bytes.NewReader(encoded)
	}

	req, err := http.NewRequest(endpoint.Method, requestURL, reader)
	if err != nil {
		return nil, err
	}
	req.Header.Set("Authorization", "Bearer "+c.token)
	req.Header.Set("tenant-id", "2")
	if body != nil {
		req.Header.Set("Content-Type", "application/json")
	}

	resp, err := c.httpClient.Do(req)
	if err != nil {
		return nil, fmt.Errorf("请求失败: %s (%w)", c.config.BaseURL, err)
	}
	defer resp.Body.Close()

	responseBody, err := io.ReadAll(resp.Body)
	if err != nil {
		return nil, err
	}
	if resp.StatusCode == http.StatusUnauthorized || resp.StatusCode == http.StatusForbidden {
		return nil, AuthError{Message: "认证失败，token 可能已过期"}
	}
	if resp.StatusCode < 200 || resp.StatusCode >= 300 {
		preview := string(responseBody)
		if len(preview) > 200 {
			preview = preview[:200]
		}
		return nil, fmt.Errorf("HTTP %d: %s", resp.StatusCode, preview)
	}

	var data map[string]any
	if err := json.Unmarshal(responseBody, &data); err != nil {
		return nil, fmt.Errorf("接口返回内容不是合法 JSON")
	}
	if data == nil {
		return nil, fmt.Errorf("接口返回 JSON 顶层必须是对象")
	}
	return data, nil
}

func joinURL(baseURL string, path string) string {
	return strings.TrimRight(baseURL, "/") + "/" + strings.TrimLeft(path, "/")
}
