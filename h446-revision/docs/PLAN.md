# H446 Revision App: Plan

This file is updated before each phase. Older phases stay here so the reasoning is traceable.

## Overall shape (all phases)

- **Location:** `h446-revision/` inside the `Projects` repo.
- **Backend:** Python 3.12, FastAPI, SQLite (one file on a mounted volume). Stores progress only.
- **Frontend:** vanilla HTML/CSS/JS ES modules, no build step, served by FastAPI as static files.
- **Content:** versioned JSON in `content/`. `spec.json` is the spine; every other content item
  carries `spec_ids` pointing into it, and a build-time check rejects any item whose `spec_ids`
  are not in `spec.json`.
- **Progress model (Phase 1 onwards):** append-only `events` table (client-generated UUID, client
  timestamp, type, payload). Current state (ratings, SM-2 card state, mastery) is derived by
  replaying events, so offline sync in Phase 6 is "insert events you don't already have", which is
  idempotent by UUID.

---

## Phase 0: extract the spec

### Goal

`content/spec.json` with every spec point: id, component/paper, topic, subtopic, spec wording,
clarification text, mapped checklist statements, cross-topic links and resource URLs, taken word
for word from the two PDFs. No app code.

### What the PDFs actually look like (this drives the design)

- **OCR guide (24 pages):** one table row per **subtopic** (e.g. 1.1.1). Column 1 lists the
  lettered points (a, b, c...). Column 2 is the clarification, written as paragraphs for the
  subtopic as a whole, not per letter. Column 3 holds cross-topic links and resource URLs, also per
  subtopic. Two subtopics (2.2.1, 2.3.1) continue onto a second page.
- **Craig'n'Dave checklist (21 pages):** 25 numbered topics (1 to 26, no 25), each roughly one OCR
  subtopic, each a list of "Candidates need to..." statements. The statements are mostly the OCR
  clarification text cut into sentences, with some additions and omissions.

So the per-point clarification and per-point checklist mapping do not exist in the sources. They
have to be inferred, and that inference must be visible and correctable.

### Approach

Two scripts, so extraction (mechanical) is separate from mapping (judgement):

1. `tools/extract_pdfs.py` (pdfplumber) writes verbatim intermediates to `content/_extracted/`:
   - Guide: table cells per row; the sideways subtopic title is read from rotated characters;
     paragraphs are split on vertical gaps (≈2.0pt within a paragraph, ≈4.8pt between);
     lettered points are split on `a)`, `b)`...; bullet lines are kept as separate lines.
   - Checklist: statement rows are found from the alternating row fills (only every other row is
     filled, so unfilled rows are the gaps between fills); topic headers, video links, paper
     headings and "Additional notes" are recognised by their text.
2. `tools/build_spec.py` builds `content/spec.json`:
   - `PARAGRAPH_POINTS`: a hand-written table saying which point letter(s) each clarification
     paragraph belongs to. Every point gets `"clarification_mapping": "inferred"` and
     `clarification_shared_with` listing other points that share its paragraphs.
   - Checklist statements are matched automatically to the clarification paragraph sharing the
     most words (≥75% of the statement's words), inheriting that paragraph's letters.
     `STATEMENT_OVERRIDES` fixes the 46 statements where that is wrong or too coarse.
   - `content/_extracted/mapping_report.txt` lists every statement with its match score and how it
     was mapped, so the mapping can be audited line by line.
   - Resource URLs use the URL **as printed** (word for word). The PDF's clickable link targets
     sometimes differ; those differences go in the report, not the data.

### Data model: `content/spec.json`

```text
{
  schema_version, generated_by, sources, notes,
  papers:    [{paper, component, checklist_heading}],
  topics:    [{id "1.1", component, paper, title, heading}],
  subtopics: [{id "1.1.1", topic, title, clarification[], cross_topic_links[{id,label}],
               resource_urls[], checklist_topic{topic_number,title,video_url,additional_notes},
               guide_pages[], point_ids[]}],
  points:    [{id "1.1.1a", component, paper, topic, topic_title, subtopic, subtopic_title,
               letter, spec_wording, clarification[], clarification_mapping,
               clarification_shared_with[], checklist_statements[{id,text}],
               cross_topic_links[], resource_urls[], video_url}],
  checklist_unmapped: []
}
```

Points repeat their subtopic's links and URLs so the app can render a point without a join.
Checklist statement ids (`cl-TT-NN`) are stable as long as the PDF doesn't change.

### Risks and how they're handled

| Risk | Mitigation |
|---|---|
| Wrong text extraction (merged columns, lost hyphens, reversed sideways text) | Verified every point's wording and every clarification sentence is present in an independent `pdftotext -raw` dump. The only differences are pdftotext dropping spaces around curly quotes. Visual spot checks of row counts on several checklist pages. |
| Wrong paragraph-to-point mapping | Mapping is a small, readable table in `build_spec.py`; flagged as inferred in the data; shared paragraphs listed per point. |
| Wrong statement-to-point mapping | Score per statement in `mapping_report.txt`; all multi-point and low-score matches reviewed by hand and overridden where needed. |
| PDFs out of date vs the live spec | Can't be checked from the PDFs alone. Flagged in `EXTRACTION_NOTES.md` for Taylor. |
| Content referenced but not in the PDFs (Appendix 5d/5g) | Flagged; no content invented. |

### Not done in Phase 0

No keywords, summaries or app code.

---

## Phase 1 (preview, detailed plan to follow after review)

App shell, auth, Docker, SQLite events schema, spec map with 3-state self-rating, then keywords and
summaries for topic 1.1 only.
