# Delete Document 功能扩展

## 概述

已成功扩展 `delete_document` 工具，现在支持：
- ✅ 批量删除多个文档
- ✅ 删除上传目录中的文件
- ✅ 删除 LLM 缓存结果
- ✅ 保持向后兼容性

## 新功能

### 1. 批量删除

现在可以一次删除多个文档：

```json
{
  "tool": "delete_document",
  "arguments": {
    "document_ids": ["doc_1", "doc_2", "doc_3"],
    "delete_file": false,
    "delete_llm_cache": false
  }
}
```

### 2. 高级删除选项

- `delete_file`: 是否删除上传目录中的文件
- `delete_llm_cache`: 是否删除 LLM 缓存的提取结果

### 3. 向后兼容性

原有的单文档删除方式仍然有效：

```json
{
  "tool": "delete_document",
  "arguments": {
    "document_id": "doc_123",
    "delete_file": true,
    "delete_llm_cache": true
  }
}
```

## 参数说明

| 参数 | 类型 | 必需 | 默认值 | 描述 |
|------|------|------|--------|------|
| `document_id` | string | 与 `document_ids` 二选一 | - | 单个文档 ID（向后兼容） |
| `document_ids` | array<string> | 与 `document_id` 二选一 | - | 批量文档 ID 数组 |
| `delete_file` | boolean | 否 | false | 是否删除上传目录中的文件 |
| `delete_llm_cache` | boolean | 否 | false | 是否删除 LLM 缓存结果 |

## 使用示例

### 示例 1: 删除单个文档（向后兼容）
```json
{
  "tool": "delete_document",
  "arguments": {
    "document_id": "doc_12345"
  }
}
```

### 示例 2: 批量删除多个文档
```json
{
  "tool": "delete_document",
  "arguments": {
    "document_ids": ["doc_1", "doc_2", "doc_3", "doc_4"]
  }
}
```

### 示例 3: 完全清理文档
```json
{
  "tool": "delete_document",
  "arguments": {
    "document_id": "doc_12345",
    "delete_file": true,
    "delete_llm_cache": true
  }
}
```

### 示例 4: 批量完全清理
```json
{
  "tool": "delete_document",
  "arguments": {
    "document_ids": ["doc_1", "doc_2", "doc_3"],
    "delete_file": true,
    "delete_llm_cache": true
  }
}
```

## 验证规则

- 必须提供 `document_id` 或 `document_ids` 中的一个
- 不能同时提供 `document_id` 和 `document_ids`
- `document_ids` 不能为空数组
- 所有文档 ID 必须是非空字符串
- `delete_file` 和 `delete_llm_cache` 必须是布尔值

## 实现细节

### 更新的文件

1. **`src/daniel_lightrag_mcp/models.py`**
   - 扩展 `DeleteDocRequest` 模型

2. **`src/daniel_lightrag_mcp/client.py`**
   - 更新 `delete_document` 方法支持新参数
   - 保持向后兼容性

3. **`src/daniel_lightrag_mcp/server.py`**
   - 更新工具定义和参数验证
   - 增强处理逻辑

4. **测试文件**
   - 添加新的测试用例
   - 更新现有测试

### API 调用

最终发送到 LightRAG API 的请求格式：

```json
{
  "doc_ids": ["doc_1", "doc_2", "doc_3"],
  "delete_file": true,
  "delete_llm_cache": true
}
```

## 日志输出

新功能提供详细的日志记录：

```
DELETE_DOCUMENT PARAMETERS:
  - Deletion type: batch
  - Document IDs to delete: ['doc_1', 'doc_2', 'doc_3']
  - Number of documents: 3
  - Delete files: true
  - Delete LLM cache: true
```

## 性能考虑

- 批量删除比多次单独删除更高效
- 删除文件和缓存会增加操作时间
- 建议根据实际需要选择合适的删除选项

## 注意事项

1. **删除操作不可逆** - 请谨慎使用
2. **批量删除** - 确保文档 ID 列表正确
3. **文件删除** - 会删除上传目录中的原始文件
4. **缓存删除** - 会删除 LLM 提取的缓存，可能影响性能