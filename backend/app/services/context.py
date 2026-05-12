import json

def parse_context(raw: str | dict | list | None) -> dict:
    if raw is None:
        return {"course": "", "lesson": "", "summary": ""}

    if isinstance(raw, dict):
        return _normalize(raw)

    if isinstance(raw, list):
        return {"course": "", "lesson": "", "documents": raw, "summary": ""}

    # string — try JSON first, then plain text
    raw_str = raw.strip()
    if raw_str.startswith("{"):
        try:
            return _normalize(json.loads(raw_str))
        except json.JSONDecodeError:
            pass
    if raw_str.startswith("["):
        try:
            docs = json.loads(raw_str)
            return {"course": "", "lesson": "", "documents": docs, "summary": ""}
        except json.JSONDecodeError:
            pass

    # plain text — could be "course - lesson" or just "course"
    if " - " in raw_str:
        parts = raw_str.split(" - ", 1)
        return {"course": parts[0].strip(), "lesson": parts[1].strip(), "summary": raw_str}
    return {"course": raw_str, "lesson": "", "summary": raw_str}


def _normalize(d: dict) -> dict:
    return {
        "course": d.get("course", d.get("context", "")),
        "lesson": d.get("lesson", ""),
        "documents": d.get("documents", d.get("docs", [])),
        "summary": d.get("summary", ""),
    }


def build_prompt(ctx: dict) -> str:
    parts = []
    if ctx["course"]:
        parts.append(f"Corso: {ctx['course']}")
    if ctx["lesson"]:
        parts.append(f"Lezione: {ctx['lesson']}")
    if ctx.get("documents"):
        parts.append(f"Documenti allegati: {len(ctx['documents'])}")
    if ctx["summary"] and not parts:
        parts.append(ctx["summary"])

    context_str = " | ".join(parts) if parts else "Conversazione generale"
    return f"""Sei un tutor AI amichevole. Rispondi in modo chiaro e coinvolgente, adattandoti al livello dello studente.
Contesto attuale: {context_str}"""
