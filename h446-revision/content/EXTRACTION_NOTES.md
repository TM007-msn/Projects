# Extraction notes

Where the three PDFs disagree, don't line up, or leave a gap. Nothing listed here was guessed into
`spec.json`; decisions taken are recorded in section 1.

Sources:

- **Specification:** `spec/ocr-h446-specification.pdf`, Cambridge OCR H446 specification,
  Version 3.0 (April 2026). Authoritative for wording.
- **Guide:** `spec/ocr-h446-clarification-guide.pdf`, OCR "Subject content clarification",
  Version 1, © OCR 2017 (PDF created 30/08/2018).
- **Checklist:** `spec/revision-checklist.pdf`, Craig'n'Dave "OCR A-Level Computer Science Revision
  check list" (undated; refers to "Full A'Level ONLY" topics, so it dates from the AS/A level era).

Full statement-by-statement mapping with match scores: `content/_extracted/mapping_report.txt`.

---

## 1. Decisions (resolved 02/11/2026)

1. **Appendix 5d/5f: resolved.** Taylor added the full specification
   (`spec/ocr-h446-specification.pdf`, **Version 3.0, April 2026**). Appendix 5d (pseudocode, HTML,
   CSS, JavaScript, LMC, SQL, Boolean notation) and 5f (ERD symbols) are transcribed in
   `tools/appendix_5d_5f.json` and merged into `spec.json` under `appendices`. ERDs are appendix
   **5f** in v3.0 (the 2017 guide said 5g).
2. **The PDFs are current: confirmed.** The specification's summary of updates shows no
   subject-content changes since first teaching (v2 to v3.0 changed only wording, NEA, covers and
   branding). v3.0 still names the Data Protection Act 1998 in 1.5.1a.
3. **Checklist-only additions: in scope when relevant to the spec or good to know.** All current
   checklist additions (Topic 8 programming specifics, records/lists/tuples, LIFO/FIFO, flat file
   set-up, XML as an exchange format, casting) qualify and stay mapped. Content generated from them
   is tagged `"source": "checklist"` so it can be told apart from OCR wording.
4. **Bullet-list points split into tracker sub-items.** 1.3.3b (5), 1.5.2a (9) and 2.2.2f (6) have
   `sub_items` with ids like `1.5.2a.3`. Ratings on sub-items roll up to the official point.

## 1a. Specification v3.0 vs the 2017 guide

`spec_wording` now comes from the specification; the guide's version is kept as `guide_wording`.
Same 24 subtopics, same 111 points, same letters. Differences:

- **1.5.1c** is "The Copyright **Design** and Patents Act 1988" (the guide dropped "Design").
- Subtopic titles: **1.2.1 "Systems Software"** (guide: "Operating Systems"); **1.5.2 "Moral and
  ethical Issues"** (guide: "Ethical, moral and cultural issues"); 1.2.2 "Applications Generation"
  (case only).
- 1.5.2 has **no letter** in the specification; kept as `1.5.2a` and marked `unlettered_in_spec`.
- 1.1.1b: "Cycle; including its effects on registers" (guide: ", including its effect").
- 1.1.3a: "applied to the solution of different problems" (guide: "applied as a solution of").
- 1.4.2c adds "NB"; 1.5.2a drops the brackets ("individual moral, social, ethical and cultural")
  and uses British "behaviour"; 1.3.2a uses "modelling" (guide: "modeling").
- Everything else is capitalisation or punctuation ("Translators:Interpreters" has no space in the
  original).

Appendix 5d errata (kept verbatim, listed in `spec.json` → `appendices.errata`): stray `1` in
`case "B":1`; `subString` vs `substring`; the constructors section is printed twice; the loop
example prints "Hello" but says "hello".

Note for content: the specification's pseudocode guide has no string functions beyond `.length`
and `.substring`, but the checklist (cl-08-09) mentions upper/lower case and character ↔ ASCII
conversion. Questions using other functions "will be specifically introduced", so cards on these
will be marked as checklist-sourced.

## 2. Gaps: spec points with thin or no supporting text

| Point | Gap |
|---|---|
| 1.1.1d Pipelining | No clarification paragraph and no checklist statement. Only the spec wording, plus the subtopic's resource URLs (one of which is an iastate.edu pipelining tutorial). |
| 2.1.2d Reusable program components | No clarification paragraph in the guide. The checklist does cover it (cl-19-04 to cl-19-06). |
| 2.3.1f Insertion sort | Listed in the spec wording, but unlike every other named algorithm it has no clarification sentence and no checklist statement. |
| 1.3.2c Normalisation to 3NF | Clarification exists (inside the first 1.3.2 paragraph), but the checklist has no normalisation statement at all. |

## 3. Checklist vs guide

**Structure**

- Checklist topics are numbered 1 to 26 but **Topic 25 is missing** (24 Computational methods is
  followed by 26 Algorithms). No content appears to be lost: every OCR subtopic has a checklist
  topic except as noted below.
- **Topic 8 "Introduction to programming" has no OCR subtopic.** Mapped to 1.2.4b (procedural
  languages), with flow-control and procedure/function statements also mapped to 2.2.1a/2.2.1d, and
  its assembly/LMC statements to 1.2.4c. It adds specifics not spelled out in the guide: benefits
  of constants over variables; operator lists (`+ - / * MOD DIV`, `AND OR NOT == > < = >= <= !=`,
  assignment `=`); string handling (substrings, upper/lower case, character ↔ ASCII value); reading
  and writing text files. These are all consistent with the 1.2.4b clarification ("variables,
  constants, selection, iteration, sequence, subroutines, string handling, file handling, Boolean
  and arithmetic operators").
- **Topic 12 Web technologies includes three compression statements** (cl-12-05 to cl-12-07). The
  guide's 1.3.4 has no compression; mapped to 1.3.1a.
- Topics 9 and 22 are labelled "(Full A'Level ONLY)". Irrelevant for the full A level; ignored.
- Topic 22's third sentence ("how concurrent processing could be applied to a specific program...")
  is an "Additional note" in the checklist but a normal clarification paragraph in the guide.
- Topic 16 has an extra note (not in the guide) about extended-response questions being marked with
  a level-of-response framework. Kept in `subtopics[1.5.1].checklist_topic.additional_notes`.

**Content added by the checklist**

- Topic 10 (1.3.2): "experience of setting up and using both a flat file, and relational database";
  exchange formats "CSV, JSON **and XML**" (guide: "CSV and JSON").
- Topic 13 (1.4.1): adds "(casting)" for type conversion; ASCII/Unicode "the benefits of each"
  (guide: "how these impact what can be stored").
- Topic 14 (1.4.2): six statements on the purpose and use of records, lists and tuples; "behaviour
  of stacks and queues (i.e. LIFO and FIFO)".
- Topic 6 (1.2.3): writing algorithms "using flow charts, pseudocode and/or program code" (the
  guide's 1.2.3 says "pseudocode and/or program code"; flow charts do appear in the guide under
  2.3.1).

**Content dropped or changed by the checklist**

- Topic 13 omits "using switches" (binary storage) and says "denary" where the guide says
  "decimal/denary".
- Topic 10 omits the normalisation sentences (see section 2).
- Topic 2: "distributed or multiple cores" vs guide "distributed across multiple cores".
- 18 statements are reworded (match score below 1.0 but above the 0.75 threshold); each is listed
  with its score in `mapping_report.txt`.

**Defects in the checklist PDF**

- cl-07-12 is cut off: "...code that makes use of these object-oriented" (the word "techniques" is
  missing).
- One Topic 8 statement is split across two table rows ("...assembly language. Candidates" / "need
  to be familiar with the instructions given in Appendix 5d."). Rejoined as cl-08-11.
- Topic 13 repeats "Candidates should be able to normalise a floating point number." Topic 26
  repeats "Candidates' code is not expected to be syntactically perfect...". Both duplicates kept
  as separate statement ids so the checklist is reproduced faithfully.

## 4. Guide: internal issues (kept verbatim)

The guide is the source of truth, so these are reproduced exactly rather than corrected. The app
will show spec text as-is; my own generated content will use correct wording.

- Typos: "purpose and function **or** registers" (of); "how data and **addressed** are transferred"
  (addresses); "used to find the IP of a URL **is found**"; "the benefits **and** using GPUs";
  "**commons** formats"; "**Candidate** need to understand how a quick sort works"; "**modeling**",
  "Monitor **behavior**" (US spellings in the spec wording).
- 1.2.2 clarification: "how the tokens are checked to ensure they meet during (and after) code
  generation" is garbled in the original.
- 1.3.2 clarification: the data-handling paragraph contains a duplicated, run-on passage ("...is it
  in a table or a list).(such as forms, data mining), selecting data...").
- 2.2.1 clarification: the sentence "read, create and trace code (for example using a trace table)
  that use these three constructs" comes after the recursion paragraph; mapped to 2.2.1a (the three
  constructs), not 2.2.1b.
- 2.3.1: "not expected to write code in syntax" (a word is missing; 1.2.3 says "in this syntax").
- 2.3.1e names only "depth-first (post-order)" traversal of **trees**; pre-order and in-order are not
  mentioned anywhere in either PDF.

## 5. Paragraph-to-point mapping

The guide gives clarification per subtopic. I split it onto lettered points by reading it (table in
`tools/build_spec.py`). Where one paragraph covers several points, every point gets the whole
paragraph and lists the others in `clarification_shared_with`. 31 of 111 points share a paragraph:

- One paragraph for all points: 2.1.1a–d, 2.1.4a–c.
- Shared pairs/groups: 1.2.3a/b; 1.3.2a/c (database terms + normalisation), 1.3.2a/b (data
  methods + indexing); 1.3.4b/c; 1.4.1b/f and 1.4.1e/f (conversions); 1.4.3a/d; 1.5.1a–d (general
  law paragraphs); 2.1.3a/b; 2.2.2b/c/e; 2.3.1b/d and 2.3.1c/d.

46 checklist statements are placed by hand (`STATEMENT_OVERRIDES`) because the automatic match was
wrong or too coarse; the rest are automatic with a match score of 0.75 or above.

## 6. Resource URLs

- `resource_urls` uses the URL **as printed**. The clickable link behind it sometimes differs:
  - 1.4.3: printed `youtu.be/...`, link goes to `youtube.com/watch?v=...&feature=youtu.be` (same
    videos).
  - 1.4.1 and 2.1.1: printed `bbc.co.uk/education/guides/...`, link goes to
    `bbc.com/bitesize/guides/...`.
  - 1.2.4 and 2.2.1: link targets contain a stray space ("teach- ict.com", "Object- Oriented").
  - 1.1.1 (`youtu.be/UdHK35N-Kuo`) and 2.2.2 (`youtu.be/rubdV99bbyo`) are printed with no link
    behind them.
- 1.2.4's printed codeproject URL is truncated in the PDF ("...Programming-Concep"); the full
  version ("...Concepts") is printed under 2.2.1. Kept as printed.
- 1.3.3 prints `youtu.be/1gdrZwBouOs` twice; de-duplicated.
- **Not checked:** whether any of these links still work. Most date from 2016–2017 (teach-ict.com,
  bbc.co.uk/education, studytonight, student.craigndave.org video pages), so expect some to be dead
  or redirected. I haven't checked them.
