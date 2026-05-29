package gokms

import (
	"strings"
	"testing"
)

func TestFormatRecordsReadsNestedRows(t *testing.T) {
	output := FormatRecords(map[string]any{
		"data": map[string]any{
			"rows": []any{
				map[string]any{"faqId": "faq-1", "title": "如何重置密码"},
			},
			"total": 1,
		},
	}, "FAQ")

	if strings.Contains(output, "无数据") {
		t.Fatalf("output = %s", output)
	}
	if !strings.Contains(output, "faq-1") || !strings.Contains(output, "如何重置密码") {
		t.Fatalf("output = %s", output)
	}
}

func TestFormatRecordsReadsNestedDataList(t *testing.T) {
	output := FormatRecords(map[string]any{
		"code": 200,
		"data": map[string]any{
			"dataList": []any{
				map[string]any{"faqId": "faq-1", "title": "如何查询订单"},
			},
			"pageNum":  1,
			"pageSize": 10,
			"total":    1,
		},
	}, "FAQ")

	if strings.Contains(output, "无数据") {
		t.Fatalf("output = %s", output)
	}
	if !strings.Contains(output, "faq-1") || !strings.Contains(output, "如何查询订单") {
		t.Fatalf("output = %s", output)
	}
}
