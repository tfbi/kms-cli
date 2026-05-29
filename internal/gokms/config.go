package gokms

import (
	"encoding/json"
	"errors"
	"fmt"
	"os"
	"path/filepath"
	"runtime"
	"strconv"
	"strings"
)

var requiredEndpoints = []string{"me", "kbs", "channels", "faqs", "faq_detail"}

type EndpointConfig struct {
	Method string
	Path   string
}

type Config struct {
	BaseURL   string
	Token     string
	Endpoints map[string]EndpointConfig
	Path      string
}

func DefaultConfigPath() string {
	home, err := os.UserHomeDir()
	if err != nil || strings.TrimSpace(home) == "" {
		return filepath.Join(".kms", "config.toml")
	}
	if runtime.GOOS == "windows" {
		return filepath.Join(home, ".kms", "config.toml")
	}
	return filepath.Join(home, ".kms", "config.toml")
}

func LoadConfig(path string) (Config, error) {
	text, err := os.ReadFile(path)
	if err != nil {
		if errors.Is(err, os.ErrNotExist) {
			return Config{}, fmt.Errorf("配置文件不存在: %s", path)
		}
		return Config{}, fmt.Errorf("读取配置文件失败: %s", path)
	}

	raw, err := parseSimpleTOML(string(text))
	if err != nil {
		return Config{}, fmt.Errorf("配置文件格式错误: %w", err)
	}

	baseURL := strings.TrimSpace(raw.Root["base_url"])
	if baseURL == "" {
		return Config{}, fmt.Errorf("缺少必填配置: base_url")
	}

	config := Config{
		BaseURL:   strings.TrimRight(baseURL, "/"),
		Token:     strings.TrimSpace(raw.Root["token"]),
		Endpoints: map[string]EndpointConfig{},
		Path:      path,
	}

	for _, name := range requiredEndpoints {
		table := "endpoints." + name
		values, ok := raw.Tables[table]
		if !ok {
			return Config{}, fmt.Errorf("缺少接口配置: endpoints.%s", name)
		}
		method := strings.ToUpper(strings.TrimSpace(values["method"]))
		endpointPath := strings.TrimSpace(values["path"])
		if method != "GET" && method != "POST" {
			return Config{}, fmt.Errorf("接口 endpoints.%s.method 只支持 GET 或 POST", name)
		}
		if !strings.HasPrefix(endpointPath, "/") {
			return Config{}, fmt.Errorf("接口 endpoints.%s.path 必须以 / 开头", name)
		}
		config.Endpoints[name] = EndpointConfig{Method: method, Path: endpointPath}
	}

	return config, nil
}

func SaveToken(path string, token string) error {
	var text string
	if data, err := os.ReadFile(path); err == nil {
		text = string(data)
	} else if !errors.Is(err, os.ErrNotExist) {
		return fmt.Errorf("读取配置文件失败: %s", path)
	}

	tokenLine := "token = " + strconv.Quote(token)
	lines := splitLinesKeepEnd(text)
	updated := false
	for index, line := range lines {
		if strings.HasPrefix(strings.TrimSpace(line), "[") {
			break
		}
		if isRootTokenLine(line) {
			lines[index] = tokenLine + lineEnding(line)
			updated = true
			break
		}
	}
	if updated {
		text = strings.Join(lines, "")
	} else {
		text = tokenLine + "\n" + text
	}

	if err := os.MkdirAll(filepath.Dir(path), 0o700); err != nil {
		return err
	}
	return os.WriteFile(path, []byte(text), 0o600)
}

type simpleTOML struct {
	Root   map[string]string
	Tables map[string]map[string]string
}

func parseSimpleTOML(text string) (simpleTOML, error) {
	result := simpleTOML{
		Root:   map[string]string{},
		Tables: map[string]map[string]string{},
	}
	current := ""

	for lineNumber, rawLine := range strings.Split(text, "\n") {
		line := strings.TrimSpace(stripComment(rawLine))
		if line == "" {
			continue
		}
		if strings.HasPrefix(line, "[") && strings.HasSuffix(line, "]") {
			current = strings.TrimSpace(strings.TrimSuffix(strings.TrimPrefix(line, "["), "]"))
			if current == "" {
				return result, fmt.Errorf("第 %d 行表名为空", lineNumber+1)
			}
			if _, ok := result.Tables[current]; !ok {
				result.Tables[current] = map[string]string{}
			}
			continue
		}

		key, value, ok := strings.Cut(line, "=")
		if !ok {
			return result, fmt.Errorf("第 %d 行缺少 =", lineNumber+1)
		}
		key = strings.TrimSpace(key)
		value = strings.TrimSpace(value)
		parsed, err := strconv.Unquote(value)
		if err != nil {
			return result, fmt.Errorf("第 %d 行只支持字符串值", lineNumber+1)
		}
		if current == "" {
			result.Root[key] = parsed
		} else {
			result.Tables[current][key] = parsed
		}
	}

	return result, nil
}

func stripComment(line string) string {
	inString := false
	escaped := false
	for index, char := range line {
		if escaped {
			escaped = false
			continue
		}
		if char == '\\' && inString {
			escaped = true
			continue
		}
		if char == '"' {
			inString = !inString
			continue
		}
		if char == '#' && !inString {
			return line[:index]
		}
	}
	return line
}

func splitLinesKeepEnd(text string) []string {
	if text == "" {
		return nil
	}
	raw := strings.SplitAfter(text, "\n")
	if raw[len(raw)-1] == "" {
		return raw[:len(raw)-1]
	}
	return raw
}

func isRootTokenLine(line string) bool {
	trimmed := strings.TrimSpace(stripComment(line))
	return strings.HasPrefix(trimmed, "token") && strings.Contains(trimmed, "=")
}

func lineEnding(line string) string {
	if strings.HasSuffix(line, "\r\n") {
		return "\r\n"
	}
	if strings.HasSuffix(line, "\n") {
		return "\n"
	}
	return ""
}

func encodeJSON(data any) string {
	encoded, _ := json.MarshalIndent(data, "", "  ")
	return string(encoded)
}
