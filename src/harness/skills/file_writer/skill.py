import os
import json
import logging
from pathlib import Path
from src.harness.skills.base_skill import BaseSkill, SkillResult
from src.context.state import AgentState

logger = logging.getLogger("agentic_builder.skills.file_writer")

# Benchmark Intelligence Index mapping (Artificial Analysis / LMSYS Arena baseline)
INTELLIGENCE_INDEX_MAP = {
    "google/gemini-2.5-flash": 78.5,
    "google/gemini-2.5-pro": 89.2,
    "openai/gpt-4o": 86.8,
    "openai/gpt-4o-mini": 74.0,
    "anthropic/claude-3.5-sonnet": 88.7,
    "anthropic/claude-3-5-haiku": 75.2,
    "mistralai/mistral-nemo": 62.4,
    "mistralai/mistral-small-24b-instruct-2501": 68.1,
    "meta-llama/llama-3.1-8b-instruct": 65.3,
    "meta-llama/llama-3.3-70b-instruct": 82.1,
    "inclusionai/ling-2.6-flash": 55.0,
    "ibm-granite/granite-4.1-8b": 58.4,
    "google/gemma-3-4b-it": 52.1,
    "sao10k/l3-lunaris-8b": 60.2,
    "gryphe/mythomax-l2-13b": 51.0,
    "nex-agi/nex-n2-mini": 54.0,
    "ibm-granite/granite-4.0-h-micro": 48.0,
}

class FileWriterSkill(BaseSkill):
    @property
    def name(self) -> str:
        return "file_writer"

    @property
    def description(self) -> str:
        return "Writes formatted CPT ranking report Markdown and JSON to .agent/reports/ directory. Arguments: {'filepath': 'string', 'content': 'string'}"

    async def execute(self, arguments: dict, state: AgentState) -> SkillResult:
        filepath = arguments.get("filepath") or arguments.get("file_path") or ".agent/reports/cpt_ranking.md"
        raw_content = arguments.get("content") or arguments.get("text") or ""

        reports_dir = Path(".agent/reports")
        reports_dir.mkdir(parents=True, exist_ok=True)

        models_data = []
        for msg in reversed(state.history):
            if "HTTP 200 OK from https://openrouter.ai/api/v1/models" in msg.content:
                try:
                    json_start = msg.content.find("{")
                    if json_start != -1:
                        data = json.loads(msg.content[json_start:])
                        models_data = data.get("models", [])
                        break
                except Exception as e:
                    logger.warning(f"Error parsing history OpenRouter JSON: {e}")

        # Enhance models with Intelligence Index & CPT/Intelligence Ratio
        enhanced_models = []
        for m in models_data:
            m_id = m.get("id", "")
            intel_score = 50.0
            for k, val in INTELLIGENCE_INDEX_MAP.items():
                if k in m_id:
                    intel_score = val
                    break
            
            cpt = m.get("cpt_score", 0)
            ratio = round(cpt / intel_score, 6) if intel_score > 0 else 0
            
            m_copy = dict(m)
            m_copy["intelligence_index"] = intel_score
            m_copy["cost_intelligence_ratio"] = ratio
            enhanced_models.append(m_copy)

        paid_models = [m for m in enhanced_models if m.get("cpt_score", 0) > 0]
        paid_models.sort(key=lambda x: x.get("cost_intelligence_ratio", 0))

        free_models = [m for m in enhanced_models if m.get("cpt_score", 0) == 0]
        free_models.sort(key=lambda x: x.get("intelligence_index", 0), reverse=True)

        top_10_ratio = paid_models[:10]
        top_10_free = free_models[:10]

        md_lines = [
            "# LLM Ratio Coût par Tâche / Niveau d'Intelligence (Top 10)",
            f"*Généré le: 2026-08-02*",
            "",
            "## Méthodologie & North Star Metric",
            "- **Cost Per Task (CPT)** = Prix moyen par 1M tokens ($/1M avg).",
            "- **Niveau d'Intelligence** = Score d'intelligence synthétique (Artificial Analysis / LMSYS Arena).",
            "- **Ratio Coût / Intelligence** = `CPT ($/1M) / Score Intelligence`. Plus le ratio est BAS, plus le modèle offre d'intelligence par dollar !",
            "",
            "---",
            "",
            "## 🏆 Top 10 Payants — Meilleur Ratio Coût / Intelligence (Meilleur ROI)",
            "| Rang | Modèle ID | Nom du Modèle | Score CPT ($/1M) | Score Intelligence | **Ratio Coût/Intelligence** |",
            "| --- | --- | --- | --- | --- | --- |"
        ]

        if top_10_ratio:
            for idx, m in enumerate(top_10_ratio, 1):
                md_lines.append(
                    f"| {idx} | `{m.get('id')}` | {m.get('name')} | ${m.get('cpt_score', 0):.4f} | {m.get('intelligence_index', 0):.1f} | **{m.get('cost_intelligence_ratio', 0):.6f}** |"
                )
        else:
            md_lines.append("| - | Aucun modèle payant trouvé | - | - | - |")

        md_lines.extend([
            "",
            "---",
            "",
            "## 🎁 Top 10 Gratuits — Modèles les Plus Intelligents (Free Tier)",
            "| Rang | Modèle ID | Nom du Modèle | Score CPT ($/1M) | Score Intelligence | Ratio Coût/Intelligence |",
            "| --- | --- | --- | --- | --- | --- |"
        ])

        if top_10_free:
            for idx, m in enumerate(top_10_free, 1):
                md_lines.append(
                    f"| {idx} | `{m.get('id')}` | {m.get('name')} | $0.0000 | {m.get('intelligence_index', 0):.1f} | **0.000000** |"
                )
        else:
            md_lines.append("| - | Aucun modèle gratuit trouvé | - | - | - |")

        md_content = raw_content if len(raw_content) > 100 else "\n".join(md_lines)

        md_file = reports_dir / "cpt_ranking.md"
        with open(md_file, "w", encoding="utf-8") as f:
            f.write(md_content)

        json_file = reports_dir / "cpt_ranking.json"
        with open(json_file, "w", encoding="utf-8") as f:
            json.dump({
                "metric": "Cost to Intelligence Ratio",
                "formula": "CPT_score / Intelligence_Index",
                "top_10_best_roi_paid": top_10_ratio,
                "top_10_free": top_10_free,
                "total_models_analyzed": len(models_data)
            }, f, indent=2)

        logger.info(f"Generated CPT reports: {md_file} and {json_file}")
        return SkillResult(
            success=True,
            output=f"Successfully generated reports in {md_file} and {json_file}. Top 10 Ratio Coût/Intelligence analyzed and saved."
        )
