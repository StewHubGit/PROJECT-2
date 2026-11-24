"""Cross-check companyfacts values against inline XBRL in the actual latest 10-K."""
import argparse
from decimal import Decimal
from html.parser import HTMLParser
import json
import os
from pathlib import Path
import re
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE / "warren-buffett-expert" / "scripts"))
from buffett import EdgarClient, EdgarError, save_json, sha


class InlineXbrl(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.contexts, self.facts, self.text = {}, [], []
        self.context = self.fact = self.date_field = None

    def handle_starttag(self, tag, attributes):
        attrs = dict(attributes)
        if tag in {"xbrli:context", "context"}:
            self.context = {"id": attrs.get("id"), "dimensioned": False}
        elif self.context is not None:
            short = tag.split(":")[-1]
            if short in {"segment", "scenario", "explicitmember", "typedmember"}:
                self.context["dimensioned"] = True
            if short in {"startdate", "enddate", "instant"}:
                self.date_field = short
        if tag == "ix:nonfraction":
            self.fact = {**attrs, "text": ""}

    def handle_data(self, data):
        if self.context is not None and self.date_field:
            self.context[self.date_field] = self.context.get(self.date_field, "") + data.strip()
        if self.fact is not None:
            self.fact["text"] += data
        if data.strip():
            self.text.append(data.strip())

    def handle_endtag(self, tag):
        if tag in {"xbrli:context", "context"} and self.context is not None:
            self.contexts[self.context["id"]] = self.context
            self.context = None
        if tag.split(":")[-1] in {"startdate", "enddate", "instant"}:
            self.date_field = None
        if tag == "ix:nonfraction" and self.fact is not None:
            self.facts.append(self.fact)
            self.fact = None


def check_inline(report, html):
    parser = InlineXbrl()
    parser.feed(html)
    row = report["annual"][0]
    checks = []
    for metric, fact in row["facts"].items():
        if fact["value"] is None:
            continue
        candidates = []
        for inline in parser.facts:
            if inline.get("name", "").lower() != ("us-gaap:" + fact["tag"]).lower():
                continue
            context = parser.contexts.get(inline.get("contextref"), {})
            if context.get("dimensioned") or (context.get("enddate") or context.get("instant")) != fact["end"] or context.get("startdate") != fact["start"]:
                continue
            text = re.sub(r"[\s,$]", "", inline["text"])
            text = text.replace("(", "-").replace(")", "").replace("−", "-")
            if not re.fullmatch(r"-?\d+(?:\.\d+)?", text):
                continue
            number = Decimal(text) * Decimal(10) ** int(inline.get("scale", "0"))
            if inline.get("sign") == "-":
                number = -number
            candidates.append(number)
        checks.append({"metric": metric, "tag": fact["tag"], "companyfacts_value": fact["value"], "inline_values": [str(x) for x in candidates], "matches": Decimal(str(fact["value"])) in candidates})
    return checks, parser


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--report", type=Path, default=HERE / "outputs/AAPL/evidence.json")
    p.add_argument("--live", action="store_true")
    p.add_argument("--local-filing", type=Path)
    p.add_argument("--manifest", type=Path, help="Existing source manifest, required for a local filing")
    p.add_argument("--user-agent", default=os.getenv("SEC_USER_AGENT", ""))
    a = p.parse_args()
    report = json.loads(a.report.read_text(encoding="utf-8"))
    client = EdgarClient(HERE / "evidence/downloads", a.user_agent, offline=not a.live)
    if a.local_filing:
        if not a.manifest:
            p.error("--local-filing requires --manifest for source integrity")
        raw = a.local_filing.read_bytes()
        source_manifest = json.loads(a.manifest.read_text(encoding="utf-8"))
        record = next((r for r in source_manifest if r["file"] == a.local_filing.name), None)
        if not record or sha(raw) != record["sha256"]:
            p.error("Saved filing does not match the original source manifest")
        html = raw.decode("utf-8")
        client.receipts.append({"source_file": str(a.local_filing.resolve()), "source_manifest": str(a.manifest.resolve()), "sha256": sha(raw), "original_retrieval_date": record.get("retrieved"), "mode": "Previously saved filing; not a fresh HTML download"})
    else:
        try:
            html = client.get(report["annual"][0]["filing_url"], kind="html")
        except EdgarError as exc:
            save_json(HERE / "evidence/filing_crosscheck_unavailable.json", {"status": "unavailable", "reason": str(exc), "filing_url": report["annual"][0]["filing_url"]})
            p.exit(1, f"Cross-check unavailable: {exc}\n")
    checks, parser = check_inline(report, html)
    artifact = {"filing_url": report["annual"][0]["filing_url"], "checks": checks, "receipts": client.receipts}
    cik = report["cik"]
    save_json(HERE / f"evidence/{cik}_filing_crosscheck.json", artifact)
    (HERE / f"evidence/{cik}_filing_text.txt").write_text("\n".join(parser.text), encoding="utf-8")
    print(json.dumps(artifact, indent=2))
    if not checks or not all(x["matches"] for x in checks):
        raise SystemExit("One or more inline filing facts failed to match.")


if __name__ == "__main__":
    main()
