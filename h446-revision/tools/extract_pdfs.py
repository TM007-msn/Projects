"""Step 1 of spec extraction: pull raw, verbatim text out of the two spec PDFs.

Run from the project root:
    pip install -r tools/requirements-dev.txt
    python tools/extract_pdfs.py

Writes:
    content/_extracted/clarification.json  - OCR guide, one entry per subtopic
    content/_extracted/checklist.json      - Craig'n'Dave checklist, one entry per topic

Nothing here interprets the content; it only reads it. The judgement calls
(which paragraph/statement belongs to which lettered spec point) live in
tools/build_spec.py so they can be reviewed separately.
"""

import json
import re
from pathlib import Path

import pdfplumber

ROOT = Path(__file__).resolve().parent.parent
GUIDE_PDF = ROOT / "spec" / "ocr-h446-clarification-guide.pdf"
CHECKLIST_PDF = ROOT / "spec" / "revision-checklist.pdf"
OUT_DIR = ROOT / "content" / "_extracted"

# A vertical gap between two text lines bigger than this (in PDF points) means
# a new paragraph. Measured: ~2.0pt inside a paragraph, ~4.8pt between them.
PARAGRAPH_GAP = 3.5


def join_lines(lines):
    """Join wrapped lines into one string.

    A line ending in a hyphen is joined without a space ("fixed-" + "size"
    -> "fixed-size"), because in these PDFs a trailing hyphen is always a
    real compound-word hyphen, never a soft line-break hyphen.
    """
    out = ""
    for line in lines:
        line = line.strip()
        if not line:
            continue
        if not out:
            out = line
        elif out.endswith("-"):
            out += line
        else:
            out += " " + line
    # Collapse double spaces that some PDF lines contain.
    return re.sub(r"\s{2,}", " ", out).strip()


def lines_in(page, bbox):
    """Text lines (with positions) inside a bounding box on a page."""
    return page.crop(bbox).extract_text_lines(strip=True)


def paragraphs_in(page, bbox):
    """Split the text in a box into paragraphs using vertical gaps."""
    paras, current, prev_bottom = [], [], None
    for line in lines_in(page, bbox):
        text = line["text"]
        if text.startswith(". . . continues"):
            continue
        if prev_bottom is not None and line["top"] - prev_bottom > PARAGRAPH_GAP:
            paras.append(join_lines(current))
            current = []
        current.append(text)
        prev_bottom = line["bottom"]
    if current:
        paras.append(join_lines(current))
    return [p for p in paras if p]


def rotated_title(page, bbox):
    """Read the sideways subtopic title in column 0 (e.g. '1.1.1 Structure ...').

    The text is rotated 90 degrees anticlockwise, so it reads bottom-to-top;
    a title that wraps has its first line further left.
    """
    chars = [
        c for c in page.chars
        if bbox[0] <= c["x0"] <= bbox[2] and bbox[1] <= c["top"] <= bbox[3]
        and not c["upright"]
    ]
    chars.sort(key=lambda c: (round(c["x0"] / 6), -c["top"]))
    return re.sub(r"\s+", " ", "".join(c["text"] for c in chars)).strip()


def split_points(text_lines):
    """Split column 1 into lettered points: 'a) ...', 'b) ...'.

    Bullet lines ('• DNS') stay inside their point, each on its own line,
    so the wording is preserved exactly.
    """
    points, letter, buf = [], None, []

    def flush():
        if letter is None:
            return
        # Keep bullets as separate lines; join ordinary wrapped lines.
        chunks, cur = [], []
        for ln in buf:
            if ln.startswith("•"):
                if cur:
                    chunks.append(join_lines(cur))
                cur = [ln]
            else:
                cur.append(ln)
        if cur:
            chunks.append(join_lines(cur))
        points.append({"letter": letter, "wording": "\n".join(chunks)})

    for ln in text_lines:
        m = re.match(r"^([a-z])\)\s*(.*)$", ln)
        if m:
            flush()
            letter, buf = m.group(1), [m.group(2)]
        else:
            buf.append(ln)
    flush()
    return points


def links_column(page, bbox):
    """Column 3: cross-topic links (bold '1.2.4 ...' text) and resource URLs.

    URLs are read from the PDF's link annotations rather than the visible
    text, because the visible text wraps long URLs across several lines.
    """
    lines = [l["text"] for l in lines_in(page, bbox)]
    topic_lines = []
    for ln in lines:
        if re.match(r"^(https?://|www\.)", ln):
            break
        topic_lines.append(ln)
    # Re-split on subtopic numbers because one link can wrap onto two lines.
    joined = join_lines(topic_lines)
    cross = [s.strip() for s in re.split(r"(?=\b\d\.\d\.\d\s)", joined) if s.strip()]

    urls = []
    for h in page.hyperlinks:
        uri = h.get("uri")
        if not uri:
            continue
        if bbox[0] - 2 <= h["x0"] <= bbox[2] + 2 and bbox[1] - 2 <= h["top"] <= bbox[3] + 2:
            if uri not in urls:
                urls.append(uri)
    # Visible URL text, kept so build_spec.py can check nothing was missed.
    visible = join_lines(lines[len(topic_lines):]).replace(" ", "")
    return cross, urls, visible


def parse_contents(pdf):
    """Topic titles from the contents page, e.g. '1.1' -> 'The characteristics ...'."""
    text = pdf.pages[1].extract_text()
    topics = {}
    for m in re.finditer(r"^\s*(\d\.\d)\.?\s+(.+?)\s+\d+\s*$", text, re.M):
        topics[m.group(1)] = m.group(2).strip()
    return topics


def extract_guide():
    pdf = pdfplumber.open(GUIDE_PDF)
    topics = parse_contents(pdf)
    subtopics = []
    for page_no, page in enumerate(pdf.pages, start=1):
        tables = page.find_tables()
        if not tables:
            continue
        table = tables[0]
        header_cells = table.rows[0].cells
        header_text = page.crop(header_cells[0]).extract_text() if header_cells[0] else ""
        for row in table.rows:
            cells = row.cells
            if len(cells) < 4 or cells[2] is None:
                continue
            col2_first = lines_in(page, cells[2])
            if col2_first and col2_first[0]["text"] == "Content clarification":
                continue  # the header row
            title = rotated_title(page, cells[0]) if cells[0] else ""
            cross, urls, visible = links_column(page, cells[3]) if cells[3] else ([], [], "")
            paras = paragraphs_in(page, cells[2])
            if not title:
                # Continuation of the previous subtopic onto a new page.
                prev = subtopics[-1]
                prev["clarification_paragraphs"] += paras
                prev["cross_topic_links"] += [c for c in cross if c not in prev["cross_topic_links"]]
                prev["resource_urls"] += [u for u in urls if u not in prev["resource_urls"]]
                prev["visible_url_text"] += visible
                prev["pages"].append(page_no)
                continue
            m = re.match(r"^(\d\.\d\.\d)\s*(.*)$", title)
            sub_id, sub_title = m.group(1), m.group(2)
            point_lines = [l["text"] for l in lines_in(page, cells[1])]
            subtopics.append({
                "id": sub_id,
                "topic": sub_id[:3],
                "topic_title": topics.get(sub_id[:3], ""),
                "topic_heading": join_lines(header_text.splitlines()),
                "title": sub_title,
                "points": split_points(point_lines),
                "clarification_paragraphs": paras,
                "cross_topic_links": cross,
                "resource_urls": urls,
                "visible_url_text": visible,
                "pages": [page_no],
            })
    return {"source": GUIDE_PDF.name, "topics": topics, "subtopics": subtopics}


def extract_checklist():
    """Pull topics and their statements out of the checklist.

    Only every other table row has a background fill, so row boundaries are
    taken from the tops and bottoms of the filled rectangles plus the table
    border; the unfilled rows are the gaps between them. Anything that is not
    a topic header, video link or statement (paper headings, "Additional
    notes") is recognised by its text.
    """
    pdf = pdfplumber.open(CHECKLIST_PDF)
    topics, current, paper, in_notes = [], None, None, False
    for page_no, page in enumerate(pdf.pages, start=1):
        bounds = set()
        for r in page.rects:
            x0, x1 = round(r["x0"]), round(r["x1"])
            if r["bottom"] - r["top"] < 6:
                continue
            if x0 in (28, 29) and x1 in (29, 432, 567):
                bounds.add(round(r["top"], 1))
                bounds.add(round(r["bottom"], 1))
        bounds.add(0.0)
        bounds.add(round(float(page.height), 1))
        edges = sorted(bounds)
        for top, bottom in zip(edges, edges[1:]):
            if bottom - top < 4:
                continue
            crop = page.crop((20, top, float(page.width) - 1, bottom))
            raw = (crop.extract_text() or "").replace("☐", "")
            text = join_lines(raw.splitlines()).strip()
            # Paper headings share a band with the page banner, so search
            # for them before throwing banner text away.
            pm = re.search(r"Paper (\d) – \d", text)
            if pm:
                paper = int(pm.group(1))
                if current is not None:
                    in_notes = False
            if not text or pm or text.startswith(("OCR A-Level Computer Science Revision check list",
                                                   "More revision videos")):
                continue
            tm = re.match(r"^Topic\s*(\d+)\s*:\s*(.+)$", text)
            if tm:
                current = {
                    "number": int(tm.group(1)),
                    "title": tm.group(2).strip(),
                    "paper": paper,
                    "video_url": None,
                    "statements": [],
                    "additional_notes": [],
                    "pages": [page_no],
                }
                topics.append(current)
                in_notes = False
                continue
            if current is None:
                continue
            if page_no not in current["pages"]:
                current["pages"].append(page_no)
            if text.startswith("Video revision link:"):
                current["video_url"] = text.split(":", 1)[1].strip()
            elif "Specific knowledge required" in text:
                in_notes = False  # header row (also repeated after a page break)
            elif text.startswith("Additional notes:"):
                # The heading is its own row; the note text follows in later rows.
                in_notes = True
                rest = text.split(":", 1)[1].strip()
                if rest:
                    current["additional_notes"].append(rest)
            elif in_notes:
                current["additional_notes"].append(text)
            else:
                current["statements"].append(text)
    return {"source": CHECKLIST_PDF.name, "topics": topics}


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    guide = extract_guide()
    checklist = extract_checklist()
    (OUT_DIR / "clarification.json").write_text(json.dumps(guide, indent=2, ensure_ascii=False) + "\n")
    (OUT_DIR / "checklist.json").write_text(json.dumps(checklist, indent=2, ensure_ascii=False) + "\n")
    print(f"Guide: {len(guide['subtopics'])} subtopics, "
          f"{sum(len(s['points']) for s in guide['subtopics'])} points")
    print(f"Checklist: {len(checklist['topics'])} topics, "
          f"{sum(len(t['statements']) for t in checklist['topics'])} statements")


if __name__ == "__main__":
    main()
