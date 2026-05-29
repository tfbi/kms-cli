package gokms

import (
	"fmt"
	"io"
	"net/http"
	"strconv"
)

type commandOptions struct {
	configPath string
	command    string
	args       []string
	asJSON     bool
	page       int
	pageSize   int
}

func Run(argv []string, httpClient *http.Client, stdin io.Reader, stdout io.Writer, stderr io.Writer) int {
	options, helpShown, err := parseArgs(argv, stdout)
	if helpShown {
		return 0
	}
	if err != nil {
		_, _ = fmt.Fprintf(stderr, "错误: %v\n", err)
		return 2
	}

	config, err := LoadConfig(options.configPath)
	if err != nil {
		_, _ = fmt.Fprintf(stderr, "错误: %v\n", err)
		return 1
	}

	tokenManager := NewTokenManager(config, stdin, stderr)
	token, err := tokenManager.GetToken()
	if err != nil {
		_, _ = fmt.Fprintf(stderr, "错误: %v\n", err)
		return 1
	}

	client := NewClientWithHTTP(config, token, httpClient)
	data, err := execute(options, client)
	if err != nil {
		if _, ok := err.(AuthError); ok {
			token, refreshErr := tokenManager.RefreshToken()
			if refreshErr != nil {
				_, _ = fmt.Fprintf(stderr, "错误: %v\n", refreshErr)
				return 1
			}
			data, err = execute(options, client.WithToken(token))
		}
		if err != nil {
			_, _ = fmt.Fprintf(stderr, "错误: %v\n", err)
			return 1
		}
	}

	_, _ = fmt.Fprintln(stdout, formatOutput(options, data))
	return 0
}

func parseArgs(argv []string, stdout io.Writer) (commandOptions, bool, error) {
	options := commandOptions{configPath: DefaultConfigPath(), page: 1, pageSize: 20}
	index := 0
	for index < len(argv) {
		arg := argv[index]
		if arg == "-h" || arg == "--help" {
			printMainHelp(stdout)
			return options, true, nil
		}
		if arg == "--config" {
			if index+1 >= len(argv) {
				return options, false, fmt.Errorf("--config 需要配置文件路径")
			}
			options.configPath = argv[index+1]
			index += 2
			continue
		}
		if len(arg) > 9 && arg[:9] == "--config=" {
			options.configPath = arg[9:]
			index++
			continue
		}
		break
	}
	if index >= len(argv) {
		return options, false, fmt.Errorf("缺少命令")
	}

	options.command = argv[index]
	options.args = argv[index+1:]
	if len(options.args) > 0 && (options.args[0] == "-h" || options.args[0] == "--help") {
		printCommandHelp(stdout, options.command)
		return options, true, nil
	}
	if err := parseCommandOptions(&options); err != nil {
		return options, false, err
	}
	return options, false, nil
}

func parseCommandOptions(options *commandOptions) error {
	positionals := []string{}
	for index := 0; index < len(options.args); index++ {
		arg := options.args[index]
		switch arg {
		case "--json":
			options.asJSON = true
		case "--page":
			value, err := readIntFlag(options.args, &index, "--page")
			if err != nil {
				return err
			}
			options.page = value
		case "--page-size":
			value, err := readIntFlag(options.args, &index, "--page-size")
			if err != nil {
				return err
			}
			options.pageSize = value
		default:
			if len(arg) > 0 && arg[0] == '-' {
				return fmt.Errorf("未知选项: %s", arg)
			}
			positionals = append(positionals, arg)
		}
	}
	options.args = positionals

	switch options.command {
	case "me", "kbs":
		if len(positionals) != 0 {
			return fmt.Errorf("命令 %s 不需要参数", options.command)
		}
	case "channels", "faqs", "faq":
		if len(positionals) != 1 {
			return fmt.Errorf("命令 %s 需要 1 个参数", options.command)
		}
	default:
		return fmt.Errorf("未知命令: %s", options.command)
	}
	return nil
}

func readIntFlag(args []string, index *int, name string) (int, error) {
	if *index+1 >= len(args) {
		return 0, fmt.Errorf("%s 需要数值", name)
	}
	value, err := strconv.Atoi(args[*index+1])
	if err != nil {
		return 0, fmt.Errorf("%s 需要整数", name)
	}
	*index++
	return value, nil
}

func execute(options commandOptions, client *Client) (map[string]any, error) {
	switch options.command {
	case "me":
		return client.Me()
	case "kbs":
		return client.Kbs(options.page, options.pageSize)
	case "channels":
		return client.Channels(options.args[0])
	case "faqs":
		return client.FAQs(options.args[0], options.page, options.pageSize)
	case "faq":
		return client.FAQDetail(options.args[0])
	default:
		return nil, fmt.Errorf("未知命令: %s", options.command)
	}
}

func formatOutput(options commandOptions, data map[string]any) string {
	if options.asJSON {
		return FormatDetail(data)
	}
	switch options.command {
	case "me", "faq":
		return FormatDetail(data)
	case "kbs":
		return FormatRecords(data, "知识库")
	case "channels":
		return FormatRecords(data, "渠道")
	case "faqs":
		return FormatRecords(data, "FAQ")
	default:
		return FormatDetail(data)
	}
}

func printMainHelp(writer io.Writer) {
	_, _ = fmt.Fprint(writer, `usage: kms [-h] [--config CONFIG] {me,kbs,channels,faqs,faq} ...

命令:
  me                  查询当前用户信息
  kbs                 分页获取知识库列表
  channels            获取指定知识库下的渠道列表
  faqs                分页获取指定渠道下的 FAQ 列表
  faq                 获取指定 FAQ 详情

选项:
  -h, --help          显示帮助信息并退出
  --config CONFIG     配置文件路径
`)
}

func printCommandHelp(writer io.Writer, command string) {
	switch command {
	case "channels":
		_, _ = fmt.Fprint(writer, "usage: kms channels [-h] [--json] knowledgeId\n\n参数:\n  knowledgeId  知识库 ID\n\n选项:\n  -h, --help   显示帮助信息并退出\n  --json       输出原始 JSON\n")
	case "faqs":
		_, _ = fmt.Fprint(writer, "usage: kms faqs [-h] [--page PAGE] [--page-size PAGE_SIZE] [--json] channelId\n\n参数:\n  channelId             渠道 ID\n\n选项:\n  -h, --help            显示帮助信息并退出\n  --page PAGE           页码\n  --page-size PAGE_SIZE 每页数量\n  --json                输出原始 JSON\n")
	case "faq":
		_, _ = fmt.Fprint(writer, "usage: kms faq [-h] [--json] faqId\n\n参数:\n  faqId       FAQ ID\n\n选项:\n  -h, --help  显示帮助信息并退出\n  --json      输出原始 JSON\n")
	default:
		printMainHelp(writer)
	}
}
