# Public Codex Skills

可复用、可验证、具有明确安全边界的 Codex Skills。这个仓库聚焦 AI 工程、架构决策、成本治理和软件交付。

Reusable Codex skills with evidence-driven workflows and explicit safety boundaries. The repository focuses on AI engineering, architecture decisions, cost governance, and software delivery.

## Skills

### `open-source-solution-research`

在开始实现之前搜索并比较开源方案，综合功能匹配、架构、维护状态、许可证、安全、运维和集成成本，给出以下决策之一：

- Adopt：直接采用。
- Adapt：二次开发或集成。
- Reference：只借鉴设计。
- Build：自行实现。

该 Skill 的调研阶段默认只读，不会自动克隆、安装或执行未知代码。

### `weekly-metrics-report`

根据两个可比周期的 JSON 或 CSV 指标生成周报、绝对增减、可选相对变化和邮件正文。缺失的对比值或成功率会明确标记为未提供，不会推测或编造。

Generate weekly comparisons and email-ready reports from two comparable periods of JSON or CSV metrics. Missing comparison values and rates stay explicitly unavailable rather than being inferred.

## Repository layout

```text
skills/
  open-source-solution-research/
    SKILL.md
    agents/openai.yaml
    references/evaluation-rubric.md
  weekly-metrics-report/
    SKILL.md
    agents/openai.yaml
    references/input-schema.md
    scripts/generate_report.py
    tests/
```

## Local use

将所需 Skill 目录复制到个人 Codex Skills 目录，然后在新任务中显式调用，或让 Codex 根据描述自动选择。

Copy the selected skill directory into your personal Codex skills directory, then invoke `$open-source-solution-research` in a new task or allow automatic discovery.

Example:

```text
Use $open-source-solution-research to find open-source options for an AI model cost dashboard. Compare licenses, maintenance, deployment complexity, and integration cost, then recommend adopt, adapt, reference, or build.

Use $weekly-metrics-report to compare the last two complete seven-day periods from this CSV and draft a concise weekly email without inventing missing values.
```

## Public-content policy

Examples and tests must use synthetic data. Do not contribute company code, internal domains, credentials, private metrics, customer data, or proprietary operating procedures. See [SECURITY.md](SECURITY.md).

## License

MIT. See [LICENSE](LICENSE).

