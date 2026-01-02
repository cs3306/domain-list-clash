# Domain List to Clash Rules Converter

[![Convert Domain Lists](https://github.com/cs3306/domain-list-clash/actions/workflows/convert.yml/badge.svg)](https://github.com/cs3306/domain-list-clash/actions/workflows/convert.yml)

将 [v2fly/domain-list-community](https://github.com/v2fly/domain-list-community) 的域名列表自动转换为 Clash 兼容的 YAML 规则文件。

## 特性

- 🔄 每 24 小时自动更新
- 📦 支持两种 Clash 规则格式：
  - **Classical** (`behavior: classical`) - 完整规则格式
  - **Domain** (`behavior: domain`) - 纯域名格式
- 🚀 通过 GitHub Actions 自动构建和发布
- 📝 支持所有 domain-list-community 规则文件

## 转换规则

| domain-list-community | Clash (Classical) |
|----------------------|-------------------|
| `domain:example.com` | `DOMAIN-SUFFIX,example.com` |
| `example.com` (无前缀) | `DOMAIN-SUFFIX,example.com` |
| `full:www.example.com` | `DOMAIN,www.example.com` |
| `keyword:google` | `DOMAIN-KEYWORD,google` |
| `regexp:...` | ❌ 不支持，跳过 |
| `include:file` | ✅ 递归包含 |

## 使用方法

### 订阅地址

规则文件发布在 `release` 分支，可直接通过 Raw URL 订阅：

```
# Classical 格式
https://raw.githubusercontent.com/YOUR_USERNAME/domain-list-clash/release/classical/{name}.yaml

# Domain 格式  
https://raw.githubusercontent.com/YOUR_USERNAME/domain-list-clash/release/domain/{name}.yaml
```

将 `{name}` 替换为你需要的规则名称，例如 `google`、`twitter`、`gfw` 等。

### Clash 配置示例

#### Classical 格式 (behavior: classical)

适用于需要区分 `DOMAIN`、`DOMAIN-SUFFIX`、`DOMAIN-KEYWORD` 的场景：

```yaml
rule-providers:
  google:
    type: http
    behavior: classical
    url: "https://raw.githubusercontent.com/YOUR_USERNAME/domain-list-clash/release/classical/google.yaml"
    path: ./ruleset/google.yaml
    interval: 86400  # 每24小时更新

  gfw:
    type: http
    behavior: classical
    url: "https://raw.githubusercontent.com/YOUR_USERNAME/domain-list-clash/release/classical/gfw.yaml"
    path: ./ruleset/gfw.yaml
    interval: 86400

rules:
  - RULE-SET,google,PROXY
  - RULE-SET,gfw,PROXY
  - MATCH,DIRECT
```

#### Domain 格式 (behavior: domain)

更高效的纯域名匹配格式：

```yaml
rule-providers:
  google:
    type: http
    behavior: domain
    url: "https://raw.githubusercontent.com/YOUR_USERNAME/domain-list-clash/release/domain/google.yaml"
    path: ./ruleset/google.yaml
    interval: 86400

rules:
  - RULE-SET,google,PROXY
  - MATCH,DIRECT
```

### 常用规则列表

| 名称 | 说明 |
|------|------|
| `google` | Google 相关域名 |
| `twitter` | Twitter/X 相关域名 |
| `facebook` | Facebook/Meta 相关域名 |
| `youtube` | YouTube 相关域名 |
| `telegram` | Telegram 相关域名 |
| `gfw` | GFW 封锁的域名 |
| `geolocation-!cn` | 非中国域名 |
| `cn` | 中国域名 |
| `category-ads` | 广告域名 |
| `category-porn` | 成人内容域名 |

完整列表请查看 [release 分支](https://github.com/YOUR_USERNAME/domain-list-clash/tree/release)。

## 本地运行

### 环境要求

- Python 3.8+
- PyYAML

### 安装依赖

```bash
pip install pyyaml
```

### 运行转换

```bash
# 转换所有文件
python convert.py

# 仅转换指定文件
python convert.py --files google twitter gfw

# 自定义输出目录
python convert.py --output ./my-output
```

### 输出结构

```
output/
├── classical/          # behavior: classical 格式
│   ├── google.yaml
│   ├── google.txt
│   ├── twitter.yaml
│   └── ...
├── domain/             # behavior: domain 格式
│   ├── google.yaml
│   ├── twitter.yaml
│   └── ...
├── index.json          # 规则索引
└── README.md           # 使用说明
```

## GitHub 部署指南

### 1. Fork 或创建新仓库

```bash
# 方式一：直接创建新仓库
mkdir domain-list-clash
cd domain-list-clash
git init
```

### 2. 复制项目文件

将以下文件复制到你的仓库：
- `convert.py`
- `.github/workflows/convert.yml`
- `README.md` (可选)

### 3. 配置 GitHub Actions 权限

1. 进入仓库设置 → Actions → General
2. 找到 "Workflow permissions"
3. 选择 "Read and write permissions"
4. 保存

### 4. 推送到 GitHub

```bash
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/domain-list-clash.git
git push -u origin main
```

### 5. 手动触发首次运行

1. 进入仓库的 Actions 页面
2. 选择 "Convert Domain Lists to Clash Rules"
3. 点击 "Run workflow"

### 6. 获取规则链接

运行完成后，规则文件将发布到 `release` 分支，访问地址格式：

```
https://raw.githubusercontent.com/YOUR_USERNAME/domain-list-clash/release/classical/{name}.yaml
https://raw.githubusercontent.com/YOUR_USERNAME/domain-list-clash/release/domain/{name}.yaml
```

## 自动更新

GitHub Actions 会在以下情况自动运行：

- ⏰ 每天 UTC 时间 02:00（北京时间 10:00）
- 📝 推送 `convert.py` 或工作流配置时
- 🖱️ 手动触发

## 常见问题

### Q: 为什么某些规则没有转换？

A: `regexp:` 类型的规则由于 Clash 不原生支持正则表达式匹配，会被跳过。

### Q: 如何添加自定义规则？

A: 可以 Fork [v2fly/domain-list-community](https://github.com/v2fly/domain-list-community) 添加自定义规则，然后修改 `convert.py` 中的 `REPO_URL`。

### Q: 更新频率可以调整吗？

A: 可以修改 `.github/workflows/convert.yml` 中的 cron 表达式。例如每 12 小时更新：
```yaml
schedule:
  - cron: '0 */12 * * *'
```

## 致谢

- [v2fly/domain-list-community](https://github.com/v2fly/domain-list-community) - 提供域名数据源
- [Clash](https://github.com/Dreamacro/clash) - 优秀的代理工具

## 许可证

MIT License
