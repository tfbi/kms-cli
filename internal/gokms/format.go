package gokms

import "fmt"

func FormatDetail(data map[string]any) string {
	return encodeJSON(data)
}

func FormatRecords(data map[string]any, title string) string {
	records := extractRecords(data)
	if len(records) == 0 {
		return title + ": 无数据"
	}

	lines := []string{title + ":"}
	for _, record := range records {
		if item, ok := record.(map[string]any); ok {
			recordID := pick(item, "id", "faqId", "faq_id", "channelId", "channel_id", "knowledgeId", "knowledge_base_id")
			name := pick(item, "name", "title", "question", "questionTitle", "standardQuestion", "faqName")
			if recordID != "" && name != "" {
				lines = append(lines, "- "+recordID+"\t"+name)
			} else if name != "" {
				lines = append(lines, "- "+name)
			} else {
				lines = append(lines, "- "+encodeJSON(item))
			}
		} else {
			lines = append(lines, fmt.Sprintf("- %v", record))
		}
	}
	return joinLines(lines)
}

func extractRecords(data map[string]any) []any {
	for _, key := range []string{"items", "records", "rows", "data", "list"} {
		value, ok := data[key]
		if !ok {
			continue
		}
		if records, ok := value.([]any); ok {
			return records
		}
		if nested, ok := value.(map[string]any); ok {
			if records := extractRecords(nested); len(records) > 0 {
				return records
			}
		}
	}
	return nil
}

func pick(record map[string]any, keys ...string) string {
	for _, key := range keys {
		if value, ok := record[key]; ok && value != nil {
			return fmt.Sprintf("%v", value)
		}
	}
	return ""
}

func joinLines(lines []string) string {
	result := ""
	for index, line := range lines {
		if index > 0 {
			result += "\n"
		}
		result += line
	}
	return result
}
