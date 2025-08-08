# GitHub Actions CI/CD 配置说明

本项目配置了完整的 GitHub Actions CI/CD 流水线，支持自动化测试、构建、安全扫描和部署。

## 工作流文件

### 1. `.github/workflows/docker-image.yml`
- **功能**: 专门用于 Docker 镜像构建和发布
- **触发条件**: 
  - 推送到 `master` 或 `develop` 分支
  - 创建版本标签 (`v*`)
  - Pull Request 到 `master` 分支

### 2. `.github/workflows/ci-cd.yml`
- **功能**: 完整的 CI/CD 流水线
- **触发条件**:
  - 推送到 `master` 或 `develop` 分支
  - Pull Request 到 `master` 分支
  - 发布新版本

## 工作流阶段

### 测试阶段 (test)
- 多 Python 版本测试 (3.9, 3.10, 3.11)
- 代码覆盖率报告
- 自动上传到 Codecov

### 代码质量检查 (lint)
- **Black**: 代码格式检查
- **isort**: 导入排序检查
- **flake8**: 代码风格检查
- **mypy**: 类型检查

### 安全检查 (security)
- **bandit**: Python 安全漏洞扫描
- **safety**: 依赖包安全漏洞检查
- 生成安全报告并上传为构建产物

### 构建阶段 (build)
- 多架构 Docker 镜像构建 (linux/amd64, linux/arm64)
- 自动推送到 GitHub Container Registry
- 智能标签管理

### Docker 测试 (test-docker)
- 构建测试镜像
- 启动容器并验证服务健康状态
- 测试 API 端点功能

### 安全扫描 (security-scan)
- **Trivy**: 容器镜像漏洞扫描
- 自动上传扫描结果到 GitHub Security 页面

### 部署阶段 (deploy)
- 仅在发布新版本时触发
- 支持生产环境部署
- 可配置部署策略

### 通知阶段 (notify)
- 成功/失败通知
- 支持自定义通知渠道

## 使用方法

### 1. 启用 GitHub Actions

确保在仓库设置中启用了 GitHub Actions：

1. 进入仓库设置
2. 选择 "Actions" → "General"
3. 确保 "Allow all actions and reusable workflows" 已启用

### 2. 配置 Secrets

如果需要自定义部署，可以配置以下 Secrets：

```bash
# 生产环境部署配置
PRODUCTION_HOST=your-server.com
PRODUCTION_USER=deploy
PRODUCTION_KEY=your-ssh-key

# 通知配置
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/...
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/...
```

### 3. 触发构建

#### 自动触发
- 推送代码到 `master` 或 `develop` 分支
- 创建 Pull Request 到 `master` 分支
- 创建版本标签 (如 `v1.0.0`)

#### 手动触发
1. 进入 "Actions" 标签页
2. 选择对应的工作流
3. 点击 "Run workflow"
4. 选择分支和参数

### 4. 查看结果

#### 构建状态
- 在仓库主页查看构建状态徽章
- 进入 "Actions" 标签页查看详细日志

#### 镜像信息
- 构建的 Docker 镜像会自动推送到 GitHub Container Registry
- 镜像地址: `ghcr.io/your-username/your-repo:tag`

#### 安全报告
- 在 "Security" 标签页查看安全扫描结果
- 下载安全报告构建产物

## 配置说明

### 环境变量

```yaml
env:
  REGISTRY: ghcr.io                    # 容器注册表
  IMAGE_NAME: ${{ github.repository }} # 镜像名称
  PYTHON_VERSION: "3.9"               # Python 版本
```

### 缓存配置

```yaml
# pip 依赖缓存
- uses: actions/cache@v3
  with:
    path: ~/.cache/pip
    key: ${{ runner.os }}-pip-${{ matrix.python-version }}-${{ hashFiles('**/requirements.txt') }}

# Docker 构建缓存
- uses: docker/build-push-action@v5
  with:
    cache-from: type=gha
    cache-to: type=gha,mode=max
```

### 标签策略

```yaml
tags: |
  type=ref,event=branch              # 分支标签
  type=ref,event=pr                  # PR 标签
  type=semver,pattern={{version}}    # 版本标签
  type=semver,pattern={{major}}.{{minor}}  # 主次版本标签
  type=sha,prefix={{branch}}-        # SHA 标签
```

## 故障排除

### 常见问题

1. **构建失败**
   - 检查 Python 依赖是否正确
   - 验证 Dockerfile 语法
   - 查看详细错误日志

2. **测试失败**
   - 确保所有测试用例通过
   - 检查测试环境配置
   - 验证 API 密钥设置

3. **安全扫描失败**
   - 更新有安全漏洞的依赖
   - 修复代码中的安全问题
   - 查看 Trivy 扫描报告

4. **部署失败**
   - 检查部署环境配置
   - 验证 SSH 密钥设置
   - 确认目标服务器可访问

### 调试技巧

1. **本地测试**
   ```bash
   # 本地运行测试
   pytest tests/ -v
   
   # 本地构建 Docker 镜像
   docker build -t e-websearch:test .
   
   # 本地运行容器
   docker run -p 8000:8000 e-websearch:test
   ```

2. **查看日志**
   - 在 Actions 页面查看详细构建日志
   - 下载构建产物进行分析
   - 使用 `act` 工具本地运行 Actions

3. **性能优化**
   - 启用缓存减少构建时间
   - 使用多阶段构建优化镜像大小
   - 并行执行独立任务

## 自定义配置

### 添加新的测试

```yaml
- name: Run custom tests
  run: |
    python -m pytest custom_tests/
    python -m mypy custom_module/
```

### 配置通知

```yaml
- name: Send Slack notification
  if: always()
  run: |
    curl -X POST ${{ secrets.SLACK_WEBHOOK_URL }} \
      -H 'Content-type: application/json' \
      --data '{"text":"Build ${{ job.status }}"}'
```

### 自定义部署

```yaml
- name: Deploy to server
  run: |
    ssh ${{ secrets.PRODUCTION_USER }}@${{ secrets.PRODUCTION_HOST }} \
      "docker pull ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:${{ github.sha }} && \
       docker-compose up -d"
```

## 最佳实践

1. **分支策略**
   - 使用 `master` 分支作为生产分支
   - 使用 `develop` 分支进行开发
   - 通过 Pull Request 合并代码

2. **版本管理**
   - 使用语义化版本号
   - 创建版本标签触发发布
   - 维护 CHANGELOG

3. **安全考虑**
   - 定期更新依赖
   - 启用安全扫描
   - 使用最小权限原则

4. **监控和告警**
   - 配置构建状态通知
   - 监控部署成功率
   - 设置性能指标

## 相关链接

- [GitHub Actions 文档](https://docs.github.com/en/actions)
- [Docker 官方文档](https://docs.docker.com/)
- [GitHub Container Registry](https://docs.github.com/en/packages/working-with-a-github-packages-registry/working-with-the-container-registry)
- [Trivy 安全扫描](https://aquasecurity.github.io/trivy/)
