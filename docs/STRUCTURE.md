# 文档结构说明

## 📁 文档组织

本项目采用分层文档结构，便于用户快速找到所需信息：

```
docs/
├── README.md                    # 文档索引和导航
├── STRUCTURE.md                 # 本文档 - 结构说明
├── api-readme.md               # API 详细文档
├── api-usage-summary.md        # API 使用总结
├── github-actions-readme.md    # CI/CD 配置文档
├── changelog-zai.md            # 更新日志
└── wechat-api-response-example.md  # 微信 API 示例
```

## 🎯 文档分类

### 1. 用户文档
- **api-usage-summary.md** - 面向最终用户，提供快速开始指南
- **api-readme.md** - 完整的 API 参考文档

### 2. 开发者文档
- **github-actions-readme.md** - CI/CD 配置和自动化
- **changelog-zai.md** - 版本更新和变更记录

### 3. 集成文档
- **wechat-api-response-example.md** - 第三方集成示例

## 📋 文档维护原则

### 内容组织
- **README.md** 保留在根目录，作为项目入口
- **详细文档** 放在 `docs/` 文件夹中
- **示例代码** 放在 `examples/` 文件夹中

### 更新策略
- 重大功能变更 → 更新相应的功能文档
- API 变更 → 更新 api-readme.md 和 api-usage-summary.md
- 版本发布 → 更新 changelog-zai.md
- 工具配置变更 → 更新 github-actions-readme.md

### 链接管理
- 所有文档间的链接使用相对路径
- 主 README.md 中的链接指向 docs/ 文件夹
- docs/README.md 作为文档导航中心

## 🔗 文档关系

```
README.md (根目录)
├── 项目概述
├── 快速开始
└── 链接到 docs/

docs/
├── README.md (文档导航)
├── API 文档
├── 开发文档
└── 示例文档
```

## 📝 文档规范

### 命名规范
- 使用 kebab-case 命名文档文件（如：`api-readme.md`）
- 特殊文档使用 PascalCase（如：`README.md`, `STRUCTURE.md`）
- 文件名应清晰表达内容
- 避免使用特殊字符和下划线

### 文件名规范
- **README.md** - 文档索引和导航（保持大写）
- **STRUCTURE.md** - 文档结构说明（保持大写）
- **api-readme.md** - API 详细文档
- **api-usage-summary.md** - API 使用总结
- **github-actions-readme.md** - CI/CD 配置文档
- **changelog-zai.md** - 更新日志
- **wechat-api-response-example.md** - 微信 API 示例

### 内容规范
- 每个文档都有明确的目标读者
- 使用统一的格式和样式
- 包含必要的示例和说明

### 更新规范
- 文档更新与代码变更同步
- 重大变更需要更新多个相关文档
- 保持文档的一致性和准确性
