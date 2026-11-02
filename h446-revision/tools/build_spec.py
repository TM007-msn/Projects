"""Step 2 of spec extraction: turn the raw PDF text into content/spec.json.

Run from the project root after tools/extract_pdfs.py:
    python tools/build_spec.py

The OCR guide gives clarification text per SUBTOPIC (e.g. 1.1.1), not per
lettered point (1.1.1a). The checklist gives statements per Craig'n'Dave
TOPIC, which line up with subtopics. So two judgement calls are needed, and
both are written out below where they can be reviewed and corrected:

1. PARAGRAPH_POINTS: which lettered point(s) each clarification paragraph
   belongs to (hand-mapped by reading the text).
2. Checklist statements are matched automatically to the clarification
   paragraph whose words they share most, and inherit that paragraph's
   points. STATEMENT_OVERRIDES fixes the cases the matcher gets wrong or
   cannot match.

Every point in the output carries "clarification_mapping": "inferred" to make
it obvious that the per-point split is ours, not OCR's.
"""

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "content" / "_extracted"
OUT = ROOT / "content" / "spec.json"
REPORT = ROOT / "content" / "_extracted" / "mapping_report.txt"

# --- 1. Clarification paragraph -> point letters, per subtopic -------------
# Index = paragraph number in content/_extracted/clarification.json.
PARAGRAPH_POINTS = {
    "1.1.1": ["a", "a", "a", "a", "b", "b", "c", "e", "e"],          # no paragraph for d (pipelining)
    "1.1.2": ["a", "b", "c", "c", "c"],
    "1.1.3": ["a", "b", "c", "d"],
    "1.2.1": ["a", "b", "c", "d", "e", "f", "g", "h"],
    "1.2.2": ["a", "b", "b", "c", "d", "e", "e", "e", "f"],
    "1.2.3": ["ab", "c"],
    "1.2.4": ["a", "b", "c", "d", "e"],
    "1.3.1": ["a", "b", "c", "d", "d"],
    "1.3.2": ["ac", "a", "ab", "d", "e", "f"],                       # para 2 mixes data methods (b) and indexing (a)
    "1.3.3": ["a", "a", "b", "b", "b", "b", "c", "d", "e", "e"],
    "1.3.4": ["a", "bc", "d"],
    "1.4.1": ["a", "b", "bf", "c", "d", "ef", "g", "g", "h", "i", "i", "j"],
    "1.4.2": ["a", "b", "c", "c"],
    "1.4.3": ["ad", "b", "c", "e", "e"],
    "1.5.1": ["abcd", "a", "b", "c", "d", "abcd", "abcd"],
    "1.5.2": ["a"] * 10,
    "2.1.1": ["abcd"],                                                # one paragraph covers all four
    "2.1.2": ["a", "b", "c"],                                         # no paragraph for d (reusable components)
    "2.1.3": ["ab", "c", "d", "d"],
    "2.1.4": ["abc"],
    "2.1.5": ["a", "b", "b"],
    "2.2.1": ["a", "b", "a", "c", "c", "d", "d", "e", "f"],
    "2.2.2": ["a", "bce", "d", "f", "f", "f", "f", "f", "f"],
    "2.3.1": ["a", "bd", "cd", "e", "e", "e", "e", "e", "e", "f", "f", "f", "f", "f", "f", "f", "f"],
}

# --- 2. Checklist topic number -> OCR subtopic ------------------------------
# Topic 8 ("Introduction to programming") has no OCR subtopic of its own;
# its statements are matched across all subtopics. There is no topic 25.
CHECKLIST_TOPIC_SUBTOPIC = {
    1: "1.1.1", 2: "1.1.2", 3: "1.1.3", 4: "1.2.1", 5: "1.2.2", 6: "1.2.3",
    7: "1.2.4", 8: None, 9: "1.3.1", 10: "1.3.2", 11: "1.3.3", 12: "1.3.4",
    13: "1.4.1", 14: "1.4.2", 15: "1.4.3", 16: "1.5.1", 17: "1.5.2",
    18: "2.1.1", 19: "2.1.2", 20: "2.1.3", 21: "2.1.4", 22: "2.1.5",
    23: "2.2.1", 24: "2.2.2", 26: "2.3.1",
}

# Statements whose automatic match is wrong, too coarse or missing.
# Key: checklist statement id (see mapping_report.txt). Value: point ids.
STATEMENT_OVERRIDES = {
    # Topic 6: split the three model statements between a (models) and b (merits / when used).
    "cl-06-01": ["1.2.3a"],
    "cl-06-02": ["1.2.3a", "1.2.3b"],
    "cl-06-03": ["1.2.3b"],
    # Topic 8 "Introduction to programming" is not an OCR subtopic. Its content
    # matches 1.2.4b (procedural languages), with overlaps into 2.2.1.
    "cl-08-01": ["1.2.4b"],
    "cl-08-02": ["1.2.4b", "2.2.1a"],
    "cl-08-03": ["1.2.4b"],
    "cl-08-04": ["1.2.4b"],
    "cl-08-05": ["1.2.4b", "2.2.1d"],
    "cl-08-06": ["1.2.4b", "2.2.1d"],
    "cl-08-07": ["1.2.4b"],
    "cl-08-08": ["1.2.4b"],
    "cl-08-09": ["1.2.4b"],
    "cl-08-10": ["1.2.4b"],
    # Topic 10: paragraph 0 also covers normalisation (c) and paragraph 2 mixes
    # data-handling methods (b) with indexing (a); place each statement exactly.
    "cl-10-01": ["1.3.2a"],
    "cl-10-02": ["1.3.2a"],
    "cl-10-03": ["1.3.2a"],
    "cl-10-04": ["1.3.2a"],
    "cl-10-08": ["1.3.2b"],
    "cl-10-09": ["1.3.2a", "1.3.2b"],
    "cl-10-10": ["1.3.2a"],
    "cl-10-11": ["1.3.2b"],
    "cl-12-02": ["1.3.4a"],
    "cl-12-09": ["1.3.4c"],
    "cl-13-10": ["1.4.1e"],
    # Topic 14: record / list / tuple statements are 1.4.2a.
    "cl-14-03": ["1.4.2a"],
    "cl-14-04": ["1.4.2a"],
    "cl-14-05": ["1.4.2a"],
    "cl-14-06": ["1.4.2a"],
    "cl-14-07": ["1.4.2a"],
    "cl-14-08": ["1.4.2a"],
    # Topic 18: one OCR paragraph covers 2.1.1a-d; split by sentence meaning.
    "cl-18-01": ["2.1.1a", "2.1.1b"],
    "cl-18-02": ["2.1.1b", "2.1.1d"],
    "cl-18-03": ["2.1.1d"],
    "cl-18-04": ["2.1.1c"],
    "cl-18-05": ["2.1.1c"],
    # Topic 19: the checklist covers 2.1.2d (reusable components), which the
    # OCR guide has no paragraph for.
    "cl-19-04": ["2.1.2d"],
    "cl-19-05": ["2.1.2d"],
    "cl-19-06": ["2.1.2d"],
    "cl-21-02": ["2.1.4c"],
    # Topic 26: split the efficiency statements between b, c and d.
    "cl-26-04": ["2.3.1b"],
    "cl-26-05": ["2.3.1b", "2.3.1d"],
    "cl-26-06": ["2.3.1b", "2.3.1d"],
    "cl-26-07": ["2.3.1c"],
    "cl-26-08": ["2.3.1c"],
    "cl-26-09": ["2.3.1c", "2.3.1d"],
    "cl-26-10": ["2.3.1c"],
}

# A statement matches a paragraph if at least this share of its words appear
# in that paragraph.
MATCH_THRESHOLD = 0.75


def words(text):
    return set(re.findall(r"[a-z0-9]+", text.lower().replace("’", "'")))


def containment(statement, paragraph):
    s = words(statement)
    return len(s & words(paragraph)) / max(1, len(s))


def split_urls(visible):
    """Split the run-together visible URL text into separate URLs."""
    return [u for u in re.split(r"(?=https?://)", visible) if u.startswith("http")]


def norm_url(u):
    return u.rstrip("/").replace("http://", "").replace("https://", "")


def parse_cross_links(labels):
    out = []
    for label in labels:
        m = re.match(r"^(\d\.\d\.\d)\s+(.*)$", label)
        if m:
            out.append({"id": m.group(1), "label": label})
    return out


def main():
    guide = json.loads((RAW / "clarification.json").read_text())
    checklist = json.loads((RAW / "checklist.json").read_text())
    report = []

    subtopics = {s["id"]: s for s in guide["subtopics"]}

    # One checklist statement (topic 8) is split over two PDF rows; the second
    # half starts with a lower-case letter. Rejoin before numbering.
    merge_notes = []
    for topic in checklist["topics"]:
        merged = []
        for text in topic["statements"]:
            if merged and text[:1].islower():
                merge_notes.append(f"Topic {topic['number']}: rejoined '{merged[-1][-30:]}' + '{text[:30]}'")
                merged[-1] = merged[-1] + " " + text
            else:
                merged.append(text)
        topic["statements"] = merged

    # Sanity-check the hand mapping against what was extracted.
    for sid, s in subtopics.items():
        mapping = PARAGRAPH_POINTS[sid]
        if len(mapping) != len(s["clarification_paragraphs"]):
            raise SystemExit(f"{sid}: {len(mapping)} mapped vs "
                             f"{len(s['clarification_paragraphs'])} paragraphs")
        letters = {p["letter"] for p in s["points"]}
        used = set("".join(mapping))
        if not used <= letters:
            raise SystemExit(f"{sid}: mapping uses unknown letters {used - letters}")

    # Resource URLs: the URL as printed in the guide is primary (word for
    # word). The PDF's link annotations sometimes point somewhere slightly
    # different (youtube.com/watch vs youtu.be, bbc.com vs bbc.co.uk, stray
    # spaces); those differences are listed in the report, not used.
    url_notes = []
    for sid, s in subtopics.items():
        printed = split_urls(s["visible_url_text"])
        annotated = s["resource_urls"]
        printed_norm = {norm_url(u) for u in printed}
        annotated_norm = {norm_url(u) for u in annotated}
        for u in printed:
            if norm_url(u) not in annotated_norm:
                url_notes.append(f"{sid}: printed URL has no identical link target: {u}")
        for u in annotated:
            if norm_url(u) not in printed_norm:
                url_notes.append(f"{sid}:     link target not printed as such:      {u}")
        s["resource_urls"] = list(dict.fromkeys(printed))  # de-duplicate, keep order

    # Every paragraph as a flat list for matching.
    all_paras = []
    for sid, s in subtopics.items():
        for i, text in enumerate(s["clarification_paragraphs"]):
            all_paras.append((sid, i, text))

    # Match checklist statements.
    point_statements = {}   # point id -> list of statement dicts
    unmapped = []
    cl_topic_for_sub = {}
    report.append("CHECKLIST STATEMENT MATCHING (score = share of statement words found in paragraph)\n")
    for topic in checklist["topics"]:
        home = CHECKLIST_TOPIC_SUBTOPIC.get(topic["number"])
        if home:
            cl_topic_for_sub[home] = topic
        report.append(f"\n## Topic {topic['number']}: {topic['title']}  -> {home}")
        for n, text in enumerate(topic["statements"], start=1):
            sid_ = f"cl-{topic['number']:02d}-{n:02d}"
            stmt = {"id": sid_, "text": text}
            candidates = [p for p in all_paras if p[0] == home] if home else []
            best = max(candidates, key=lambda p: containment(text, p[2]), default=None)
            score = containment(text, best[2]) if best else 0
            if score < MATCH_THRESHOLD:
                glob = max(all_paras, key=lambda p: containment(text, p[2]))
                gscore = containment(text, glob[2])
                if gscore > score:
                    best, score = glob, gscore
            if sid_ in STATEMENT_OVERRIDES:
                points = STATEMENT_OVERRIDES[sid_]
                how = "override"
            elif best and score >= MATCH_THRESHOLD:
                letters = PARAGRAPH_POINTS[best[0]][best[1]]
                points = [f"{best[0]}{l}" for l in letters]
                how = f"auto {score:.2f} para {best[0]}#{best[1]}"
                if home and best[0] != home:
                    how += "  (CROSS-SUBTOPIC)"
            else:
                points = []
                how = f"UNMATCHED (best {score:.2f} {best[0]}#{best[1]})" if best else "UNMATCHED"
            report.append(f"  {sid_} [{how}] -> {', '.join(points) or '-'}\n      {text[:150]}")
            if not points:
                unmapped.append({**stmt, "checklist_topic": topic["number"]})
            for pid in points:
                point_statements.setdefault(pid, []).append(stmt)

    # Build output.
    topics_out, subtopics_out, points_out = [], [], []
    for tid, title in guide["topics"].items():
        comp = int(tid[0])
        first = next(s for s in guide["subtopics"] if s["topic"] == tid)
        topics_out.append({
            "id": tid, "component": comp, "paper": comp, "title": title,
            "heading": first["topic_heading"],
        })

    for sid, s in subtopics.items():
        comp = int(sid[0])
        cl = cl_topic_for_sub.get(sid)
        checklist_ref = None
        if cl:
            checklist_ref = {
                "topic_number": cl["number"], "title": cl["title"],
                "video_url": cl["video_url"], "additional_notes": cl["additional_notes"],
            }
        cross = parse_cross_links(s["cross_topic_links"])
        subtopics_out.append({
            "id": sid, "component": comp, "paper": comp, "topic": s["topic"],
            "title": s["title"],
            "clarification": s["clarification_paragraphs"],
            "cross_topic_links": cross,
            "resource_urls": s["resource_urls"],
            "checklist_topic": checklist_ref,
            "guide_pages": s["pages"],
            "point_ids": [f"{sid}{p['letter']}" for p in s["points"]],
        })
        mapping = PARAGRAPH_POINTS[sid]
        for p in s["points"]:
            pid = f"{sid}{p['letter']}"
            para_idx = [i for i, letters in enumerate(mapping) if p["letter"] in letters]
            shared = sorted({f"{sid}{l}" for i in para_idx for l in mapping[i]} - {pid})
            points_out.append({
                "id": pid,
                "component": comp,
                "paper": comp,
                "topic": s["topic"],
                "topic_title": guide["topics"][s["topic"]],
                "subtopic": sid,
                "subtopic_title": s["title"],
                "letter": p["letter"],
                "spec_wording": p["wording"],
                "clarification": [s["clarification_paragraphs"][i] for i in para_idx],
                "clarification_mapping": "inferred",
                "clarification_shared_with": shared,
                "checklist_statements": point_statements.get(pid, []),
                "cross_topic_links": cross,
                "resource_urls": s["resource_urls"],
                "video_url": checklist_ref["video_url"] if checklist_ref else None,
            })

    spec = {
        "schema_version": 1,
        "generated_by": "tools/extract_pdfs.py + tools/build_spec.py",
        "sources": {
            "guide": {"file": "spec/ocr-h446-clarification-guide.pdf",
                      "title": "OCR A Level Computer Science H446 Subject content clarification, Version 1 (© OCR 2017)"},
            "checklist": {"file": "spec/revision-checklist.pdf",
                          "title": "Craig'n'Dave OCR A-Level Computer Science Revision check list"},
        },
        "notes": [
            "Clarification text and resource URLs are given by OCR per subtopic; the split of "
            "clarification paragraphs onto lettered points is inferred (see tools/build_spec.py).",
            "resource_urls and cross_topic_links on each point are the subtopic's, repeated for convenience.",
            "Paper 1 = Component 1, Paper 2 = Component 2.",
        ],
        "papers": [
            {"paper": 1, "component": 1, "checklist_heading": "Paper 1 – 2 h 30 min – 140 marks"},
            {"paper": 2, "component": 2, "checklist_heading": "Paper 2 – 2 h 30 min – 140 marks"},
        ],
        "topics": topics_out,
        "subtopics": subtopics_out,
        "points": points_out,
        "checklist_unmapped": unmapped,
    }
    OUT.write_text(json.dumps(spec, indent=2, ensure_ascii=False) + "\n")

    report.append("\n\nMERGED CHECKLIST ROWS")
    report += merge_notes
    report.append("\n\nURL NOTES")
    report += url_notes
    report.append("\n\nPOINTS WITH NO CLARIFICATION PARAGRAPH OF THEIR OWN")
    for p in points_out:
        if not p["clarification"]:
            report.append(f"  {p['id']}: {p['spec_wording'][:80]}")
    report.append("\nPOINTS WITH NO CHECKLIST STATEMENT")
    for p in points_out:
        if not p["checklist_statements"]:
            report.append(f"  {p['id']}: {p['spec_wording'][:80]}")
    REPORT.write_text("\n".join(report) + "\n")

    print(f"{len(points_out)} points, {len(subtopics_out)} subtopics, "
          f"{len(unmapped)} unmapped checklist statements. Report: {REPORT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
