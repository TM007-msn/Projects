"""Checks on the revision content JSON. These guard the content rules:

- every spec_id must exist in spec.json (no off-spec content)
- ids are unique across all content files
- every generated item has a boolean 'verified' field
- definitions are short (1-2 sentences)
- summaries have 4-8 key points and only reference existing keywords
- British spelling in prose
"""

import json
import re
from pathlib import Path

import pytest

CONTENT = Path(__file__).resolve().parent.parent / "content"


def load(name):
    return json.loads((CONTENT / name).read_text())


SPEC = load("spec.json")
SPEC_IDS = {p["id"] for p in SPEC["points"]} | {s["id"] for p in SPEC["points"] for s in p["sub_items"]}
SUBTOPIC_IDS = {s["id"] for s in SPEC["subtopics"]}
KEYWORDS = load("keywords.json")["keywords"]
KEYWORD_IDS = {k["id"] for k in KEYWORDS}
SUMMARY_FILES = sorted(p for p in (CONTENT / "summaries").glob("*.json") if p.name != "index.json")
SUMMARIES = [json.loads(p.read_text()) for p in SUMMARY_FILES]

# Common US spellings to keep out of prose. Checked as whole words.
US_SPELLINGS = [
    "color", "colors", "behavior", "behaviors", "organization", "organize", "optimize", "optimization",
    "recognize", "minimize", "maximize", "summarize", "analyze", "center", "modeling", "modeled",
    "favor", "labeled", "catalog", "fiber", "defense", "artifact",
]
# Items that quote code where US spelling is correct (CSS's `color` property).
SPELLING_EXEMPT = {"kw-inline-css", "sum-1.3.4-03"}
US_RE = re.compile(r"\b(" + "|".join(re.escape(w) for w in US_SPELLINGS) + r")\b", re.I)


def all_items():
    """Every generated item that carries an id and 'verified'."""
    yield from KEYWORDS
    for s in SUMMARIES:
        yield from s["key_points"]
        yield from s["dont_confuse"]


def test_spec_has_111_points_and_unique_ids():
    ids = [p["id"] for p in SPEC["points"]]
    assert len(ids) == 111 and len(set(ids)) == 111


def test_every_spec_id_exists():
    for item in all_items():
        assert item["spec_ids"], f"{item['id']} has no spec_ids"
        for sid in item["spec_ids"]:
            assert sid in SPEC_IDS, f"{item['id']} references unknown spec point {sid}"


def test_ids_unique_across_content():
    ids = [item["id"] for item in all_items()]
    dupes = {i for i in ids if ids.count(i) > 1}
    assert not dupes, dupes


def test_verified_field_is_boolean():
    for item in all_items():
        assert isinstance(item.get("verified"), bool), item["id"]


def test_keyword_shape():
    for k in KEYWORDS:
        assert k["id"].startswith("kw-")
        assert k["term"].strip()
        assert set(k) >= {"id", "term", "acronym", "definition", "spec_ids", "related", "dont_confuse_with", "verified"}
        for r in k["related"]:
            assert r in KEYWORD_IDS, f"{k['id']} relates to missing {r}"
            assert r != k["id"]


def test_optional_keyword_fields():
    for k in KEYWORDS:
        if "source" in k:
            assert k["source"] == "checklist", k["id"]
        if "alternative_acronyms" in k:
            assert isinstance(k["alternative_acronyms"], list) and all(isinstance(a, str) for a in k["alternative_acronyms"])


def test_every_keyword_is_in_a_summary():
    listed = {kid for s in SUMMARIES for kid in s["keyword_ids"]}
    missing = sorted(KEYWORD_IDS - listed)
    assert not missing, f"keywords not in any summary: {missing}"


def test_definitions_are_one_or_two_sentences():
    for k in KEYWORDS:
        d = k["definition"]
        # Count sentence ends: a full stop/question mark followed by a space and a capital.
        sentences = 1 + len(re.findall(r"[.?!]\s+[A-Z]", d))
        assert sentences <= 2, f"{k['id']}: {sentences} sentences"
        assert len(d) <= 320, f"{k['id']}: definition too long ({len(d)} chars)"
        assert d.endswith("."), k["id"]


def test_terms_unique():
    terms = [k["term"].lower() for k in KEYWORDS]
    assert len(terms) == len(set(terms))


def test_acronyms_unique():
    acronyms = [k["acronym"] for k in KEYWORDS if k["acronym"]]
    acronyms += [a for k in KEYWORDS for a in k.get("alternative_acronyms", [])]
    assert len(acronyms) == len(set(acronyms))


@pytest.mark.parametrize("summary", SUMMARIES, ids=[s["subtopic"] for s in SUMMARIES])
def test_summary_shape(summary):
    assert summary["subtopic"] in SUBTOPIC_IDS
    assert 4 <= len(summary["key_points"]) <= 8
    for kid in summary["keyword_ids"]:
        assert kid in KEYWORD_IDS, f"{summary['subtopic']} lists missing keyword {kid}"
    for dc in summary["dont_confuse"]:
        for kid in dc["keyword_ids"]:
            assert kid in KEYWORD_IDS
    for kp in summary["key_points"]:
        assert isinstance(kp.get("code", ""), str), kp["id"]
        assert "\n" not in kp["text"], f"{kp['id']}: put code in the 'code' field, not 'text'"
    # Key points must stay within the summary's own subtopic.
    for kp in summary["key_points"]:
        for sid in kp["spec_ids"]:
            assert sid.startswith(summary["subtopic"]), f"{kp['id']} points outside its subtopic: {sid}"


def test_summary_index_matches_files():
    index = load("summaries/index.json")["subtopics"]
    assert sorted(index) == sorted(s["subtopic"] for s in SUMMARIES)


def test_every_point_in_a_summarised_subtopic_is_covered():
    """Each spec point of a written summary should be covered by a key point or keyword."""
    for s in SUMMARIES:
        covered = {sid for kp in s["key_points"] for sid in kp["spec_ids"]}
        covered |= {sid for k in KEYWORDS if k["id"] in s["keyword_ids"] for sid in k["spec_ids"]}
        points = {p["id"] for p in SPEC["points"] if p["subtopic"] == s["subtopic"]}
        assert points <= covered, f"{s['subtopic']} misses {sorted(points - covered)}"


def test_british_spelling_in_prose():
    texts = []
    for k in KEYWORDS:
        texts += [(k["id"], k["definition"]), (k["id"], k["dont_confuse_with"] or "")]
    for s in SUMMARIES:
        texts += [(i["id"], i["text"]) for i in s["key_points"] + s["dont_confuse"]]
    for item_id, text in texts:
        if item_id in SPELLING_EXEMPT:
            continue
        m = US_RE.search(text)
        assert not m, f"{item_id}: US spelling '{m.group(0)}'"
