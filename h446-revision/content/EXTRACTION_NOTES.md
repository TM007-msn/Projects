# Extraction notes

Where the two PDFs disagree, don't line up, or leave a gap. Nothing listed here was guessed into
`spec.json`; decisions still needed from Taylor are marked **DECIDE**.

Sources:

- **Guide:** `spec/ocr-h446-clarification-guide.pdf`, OCR "Subject content clarification",
  Version 1, © OCR 2017 (PDF created 30/08/2018).
- **Checklist:** `spec/revision-checklist.pdf`, Craig'n'Dave "OCR A-Level Computer Science Revision
  check list" (undated; refers to "Full A'Level ONLY" topics, so it dates from the AS/A level era).

Full statement-by-statement mapping with match scores: `content/_extracted/mapping_report.txt`.

---

## 1. Decisions needed

1. **DECIDE: Appendix 5d / 5g are referenced but not supplied.** The guide says "See appendix 5d"
   for 1.2.4c (Little Man Computer instruction set), 1.2.4e (OOP pseudocode style), 1.3.2d (SQL
   commands), 1.3.4a (HTML/CSS/JavaScript), 1.4.3a and 1.4.3d (Boolean notation, logic gates), and
   "appendix 5g" for 1.3.2a (ERD notation). These appendices are in the full H446 specification,
   not in either PDF. Without them I can't source LMC mnemonics, the exact SQL keyword list, the
   HTML tag list or the exam's Boolean symbols from the spec. Options: (a) you add the H446
   specification PDF (or just appendix 5d/5g) to `spec/`, and I extract from it; (b) I leave these
   out. I recommend (a): LMC and SQL are high-yield for both papers.
2. **DECIDE: are checklist-only additions in scope?** The checklist adds a few things the OCR guide
   doesn't say (section 3 below). My recommendation: treat additions that only restate OCR wording
   more specifically as in scope (Topic 8 items under 1.2.4b, records/lists/tuples under 1.4.2a,
   LIFO/FIFO under 1.4.2b), but treat **XML as an exchange format (1.3.2b)** as beyond spec unless
   you confirm it, because only the checklist mentions it.
3. **DECIDE: are these PDFs current for 2027 exams?** The guide is Version 1 from 2017. I can't
   tell from the PDFs whether OCR has since changed the spec wording. The obvious candidate is
   1.5.1a "Data Protection Act 1998": UK law has since moved on (Data Protection Act 2018 / UK
   GDPR), and I'm not sure whether the current H446 specification still names the 1998 Act. The
   guide itself says answers are accepted based on the law "when the specification was started or
   when the examination was sat". Worth checking the current spec's version history on OCR's site.
4. **DECIDE: granularity of three bullet-list points.** 1.5.2a (9 bullets: workforce, automated
   decisions, AI, environment, censorship, monitoring, personal information, piracy, layout/colour/
   character sets), 2.2.2f (6 bullets: backtracking, data mining, heuristics, performance modelling,
   pipelining, visualisation) and 1.3.3b (5 bullets: TCP/IP stack, DNS, protocol layering, LANs and
   WANs, packet and circuit switching) are each a single spec point. A single self-rating for "all
   of ethics" is coarse. I can add optional sub-items in the tracker (e.g. "1.5.2a • AI") that roll
   up to the official point, without changing the spec ids. Your call.

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
