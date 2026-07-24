import os
import json
from datetime import datetime, timezone
from pydantic import BaseModel, Field

class ImpactReport(BaseModel):
    objective: str = Field(..., description="L'objectif exact de la modification")
    files_affected: list[str] = Field(default_factory=list, description="Les fichiers modifiés ou créés")
    risks: list[str] = Field(default_factory=list, description="Les risques identifiés")
    guardrails: list[str] = Field(default_factory=list, description="Comment les guardrails couvrent ces risques")
    generated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_terminal(self) -> str:
        """Format the impact report for user display in the console."""
        lines = [
            "\n==================================================",
            "🔥 RAPPORT D'IMPACT SÉMANTIQUE (/grill-me) 🔥",
            "==================================================",
            f"🎯 OBJECTIF :",
            f"   {self.objective}",
            f"📂 IMPACT SYSTÈME (Fichiers affectés) :",
        ]
        for f in self.files_affected:
            lines.append(f"   - {f}")
        lines.append("⚠️ RISQUES IDENTIFIÉS :")
        for r in self.risks:
            lines.append(f"   - {r}")
        lines.append("🛡️ COUVERTURE GUARDRAILS :")
        for g in self.guardrails:
            lines.append(f"   - {g}")
        lines.append("==================================================")
        lines.append("Pour valider et exécuter, relancez l'agent avec l'option --resume.")
        lines.append("==================================================\n")
        return "\n".join(lines)

    def save(self, path: str = ".agent/impact_report.json") -> None:
        """Save the impact report to a JSON file."""
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(self.model_dump_json(indent=2))
