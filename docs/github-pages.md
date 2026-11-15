# 在线报告页

GitHub Pages 提供可直接在浏览器阅读的报告归档，GitHub Actions 负责定时分析和更新网页。

## 部署

1. 按现有 Actions 指南配置模型 Secret、自选股和每日分析任务。
2. 在仓库 Settings → Pages 中选择 GitHub Actions 作为发布来源。
3. 至少成功运行一次「每日股票分析」，确保产物包含 `reports/report_YYYYMMDD.md` 或 `reports/market_review_YYYYMMDD.md`。
4. 运行「发布在线研报」。发布结果中的 `github-pages` 链接就是网站地址。

之后每次每日分析成功，发布工作流会自动更新网页。网站支持日期切换、股票代码或全文搜索、个股／大盘筛选、原文下载和打印；选中报告的地址可以收藏或分享。

## 数据与能力边界

- 页面公开可访问，发布内容仅来自报告文件。密钥、日志、数据库和配置文件不进入网站。
- 只读取同仓库默认分支上由定时或手动触发且成功完成的每日分析产物，最多检查最近 100 次成功运行。同日期同类型的报告使用最新一次结果。
- 历史范围取决于分析产物保留期，当前为 30 天。产物失效后会在下一次成功发布时从归档移除；没有可用报告时发布失败，保留原网站。
- 网站显示报告日期和页面发布时间，不提供实时行情。交易日以报告正文为准。
- 此页用于在线阅读报告。原项目的即时分析、配置管理和 Agent 问股需要持续运行的 Python 服务，GitHub Pages 不承载该后端。
- 此功能不调用模型，不需要额外模型密钥，也不会修改已有每日分析流程。

## 验证与回滚

在 `apps/dsa-web` 执行 `npm ci`、`npm run lint`、`npm run build` 和 `npm run build:pages`。运行 `python -m unittest discover -s tests -p test_pages_reports.py` 检查发布文件边界。

生成页面位于 `.tmp/pages/`。运行 `python scripts/collect_pages_reports.py --repository OWNER/REPOSITORY --output .tmp/pages/data` 可汇总报告；本地预览时使用静态 HTTP 服务打开该目录。

需要停止发布时，禁用「发布在线研报」工作流；需要下线网站时，在 Settings → Pages 取消发布。每日分析任务不受影响。

本页是当前部署的中文操作说明，尚未提供英文副本；未改变既有英文部署指南或原应用行为。
