package gokms

import (
	"bufio"
	"fmt"
	"io"
	"os"
	"strings"
)

type TokenManager struct {
	config Config
	input  *bufio.Reader
	output io.Writer
	source string
	token  string
}

func NewTokenManager(config Config, input io.Reader, output io.Writer) *TokenManager {
	return &TokenManager{
		config: config,
		input:  bufio.NewReader(input),
		output: output,
	}
}

func (m *TokenManager) GetToken() (string, error) {
	if token := normalizeToken(m.token); token != "" {
		m.token = token
		return token, nil
	}
	if token := normalizeToken(os.Getenv("KNOWLEDGE_TOKEN")); token != "" {
		m.source = "env"
		m.token = token
		return token, nil
	}
	if token := normalizeToken(m.config.Token); token != "" {
		m.source = "config"
		m.token = token
		return token, nil
	}
	token, err := m.promptToken("请输入 token: ")
	if err != nil {
		return "", err
	}
	m.source = "prompt"
	m.token = token
	return token, nil
}

func (m *TokenManager) RefreshToken() (string, error) {
	previousSource := m.source
	if previousSource == "" {
		if normalizeToken(os.Getenv("KNOWLEDGE_TOKEN")) != "" {
			previousSource = "env"
		} else if normalizeToken(m.config.Token) != "" {
			previousSource = "config"
		} else {
			previousSource = "prompt"
		}
	}

	token, err := m.promptToken("认证已过期或无权限，请输入新的 token: ")
	if err != nil {
		return "", err
	}
	m.source = "prompt"
	m.token = token

	if previousSource != "env" && m.confirm("是否把新 token 保存到配置文件？[y/N]: ") {
		if err := SaveToken(m.config.Path, token); err != nil {
			return "", err
		}
	}
	return token, nil
}

func (m *TokenManager) promptToken(prompt string) (string, error) {
	_, _ = fmt.Fprint(m.output, prompt)
	line, err := m.input.ReadString('\n')
	if err != nil && err != io.EOF {
		return "", err
	}
	token := normalizeToken(line)
	if token == "" {
		return "", AuthError{Message: "token 不能为空"}
	}
	return token, nil
}

func (m *TokenManager) confirm(prompt string) bool {
	_, _ = fmt.Fprint(m.output, prompt)
	line, err := m.input.ReadString('\n')
	if err != nil && err != io.EOF {
		return false
	}
	answer := strings.ToLower(strings.TrimSpace(line))
	return answer == "y" || answer == "yes"
}

func normalizeToken(value string) string {
	return strings.TrimSpace(value)
}
