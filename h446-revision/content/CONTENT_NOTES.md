# Content notes

Things to check when verifying content, and decisions about wording or ordering. Newest topic
first.

## Topic 2.3

**Not certain, check first**

- **Bubble sort best case O(n)** assumes the "stop when a pass makes no swaps" version (as in the
  summary's code). Without that check it is O(n²) in every case. Insertion sort's best case O(n) is
  for already sorted data.
- **Quick sort worst case** is given with the example "already sorted data with the first item as
  pivot". That's true for that pivot choice; other pivot strategies change which inputs are worst.
- **Dijkstra's Big O** is left out on purpose: it depends on how the priority queue is implemented,
  and the spec doesn't ask for it.
- **A\* "never overestimates"** (an admissible heuristic) is the condition for A* to guarantee the
  shortest path. The guide doesn't use the word "admissible", so the summary describes it without
  the term.
- **Code examples** (binary search, bubble sort, factorials, the LMC program in 1.2.4) were checked
  by translating them line by line into Python and running them on random data. `items.length` on
  an array isn't in the OCR pseudocode guide (which only shows `.length` for strings), but it's the
  usual way to write it.

**Orderings**

- Big O growth order (O(1) < O(log n) < O(n) < O(n log n) < O(n²) < O(2^n)) is fixed.
- Post-order (left, right, root) is fixed.

## Topic 2.2

**Not certain, check first**

- **"Computable problem"** is defined to include "in a reasonable time with available resources",
  following the guide's practical framing ("features that make a problem solvable by computational
  methods"). Strictly, computability theory only needs a finite number of steps; the definition
  says both.
- **Pipelining (problem solving)** follows the guide's description ("the result from a process
  feeds into the next process").
- **Syntax error / logic error** are included under 2.2.1e (debugging with an IDE). The spec doesn't
  name error types, but you can't discuss debugging without them.

## Topic 2.1

**Not certain, check first**

- **Few keywords on purpose.** 2.1 is about applying techniques to scenarios, so it's mostly key
  points. Paper 2 marks come from applying these ideas, which flashcards alone won't cover; the
  short exact-answer questions in Phase 5 are meant to help.
- **Concurrent processing** is defined in OCR's sense (one task doesn't have to finish before
  another starts), which includes switching between tasks on one processor, unlike parallel
  processing.
- **Precondition** has two senses in the guide: a condition an algorithm needs (e.g. sorted data)
  and "what else you need to know before producing a solution". The summary covers both.

## Topic 1.5

**Not certain, check first**

- **DPA 1998 principles** are paraphrased closely, not quoted from the Act. The eight principles
  and their order are correct as far as I know.
- **CMA offences**: the three original 1990 offences are given. The 2006 amendment (making or
  supplying tools for misuse) and the penalties aren't included, because I can't be sure which
  version your course expects.
- **RIPA** is summarised at the level of the guide ("what this allows in the interception and
  monitoring of electronic communication").
- **1.5.2 key points** are my framing of the issues: the guide gives topics, not answers. They're
  starting points for extended answers, not model answers.

**Orderings:** none in this topic.

## Topic 1.4

**Not certain, check first**

- **D-type flip-flop trigger.** Defined as changing on the **rising** edge of the clock pulse.
  That's the usual A level description, and the guide only says "triggered by a clock pulse". If
  your class notes say "falling edge" or just "on the clock pulse", accept those.
- **Unicode "up to 32 bits".** True for UTF-32 and as the maximum for UTF-8; some books say "16
  bits" (an older simplification).
- **List vs array.** OCR doesn't define "list" precisely. I've followed the usual meaning (ordered,
  can change size and contents); in Python, lists can also mix data types.
- **Collision handling.** Linear probing and chaining are named as examples; the guide doesn't
  list methods.

**Orderings**

- Floating point addition steps (equalise exponents → add mantissas → normalise) are a fixed
  order.
- Karnaugh map Gray code order (00, 01, 11, 10) is fixed.

## Topic 1.3

**Not certain, check first**

- **SQL wildcards.** The spec says learners should know `*` and `%` as wildcards. I've used `*` for
  "all fields" (`SELECT *`) and `%` inside `LIKE` patterns. Some databases (Microsoft Access) use
  `*` inside `LIKE` too; the summary doesn't rely on that.
- **PageRank detail.** The guide says "how PageRank works at a high level". I've described it in
  words (number and importance of incoming links, influence shared across outgoing links) and left
  the formula and damping factor out (see BEYOND_SPEC). If your class used the formula, it may
  come up as an interpretation question.
- **Secondary key** is defined the OCR way (an indexed non-primary field used for fast searching).
  Some books use it to mean any candidate key that isn't the primary key.
- **Redundancy in 1.3.2f** is taken to mean fault-tolerance redundancy, because it's listed with
  transaction processing and record locking. Data redundancy (removed by normalisation) is a
  separate keyword.
- **XML** (1.3.2b) is checklist-only, tagged `"source": "checklist"`.

**Orderings**

- The TCP/IP stack order is fixed (application, transport, internet, link) and is safe for an
  ordering item.
- Normalisation steps (1NF → 2NF → 3NF) are fixed.

## Topic 1.2

**Not certain, check first**

- **BRP branches on zero as well as positive.** That's how LMC implementations behave and how I've
  defined it, but check against your class notes.
- **Multi-level feedback queues.** The details (how many queues, when a process moves up or down)
  vary between textbooks; the definition stays general on purpose.
- **Utility vs device driver.** The OCR guide lists "device driver" as an example of utility
  software (1.2.2b), while most books treat drivers as separate system software (1.2.1g). Both are
  defined; the utility definition doesn't list drivers.
- **Interrupt check timing.** "The processor checks for interrupts at the end of each FDE cycle"
  is the standard A level description; real processors are more complicated.

**Orderings sources disagree on (no ordering items, or every valid order accepted)**

- **Waterfall stages.** Names and number vary (feasibility / requirements / analysis / design /
  implementation / testing / deployment / evaluation / maintenance). An ordering item will only use
  the core stages that are always in the same order: analysis, design, implementation, testing,
  maintenance.
- **Stages of compilation.** The spec lists lexical analysis, syntax analysis, code generation,
  optimisation. Real compilers often optimise before and after code generation, so an ordering
  item will accept "optimisation" either before or after "code generation", or leave it out.

## Topic 1.1

**Things I'm not certain about. Check these first when verifying.**

- **When the PC is incremented in the FDE cycle.** Textbooks differ: some increment it straight
  after copying it to the MAR, others after the instruction arrives in the MDR. The 1.1.1 summary
  says "copied to the MAR and the PC is incremented" without pinning the exact moment against the
  MDR step. I believe OCR credits incrementing at any point during fetch, but I'm not certain.
  **Ordering items (Phase 4):** the fetch-stage sequence will accept the PC increment in any
  position after "PC copied to MAR", or leave it out of the ordering entirely.
- **Contemporary processor architecture (1.1.1e).** The guide says there won't be specific
  questions, only awareness of how modern processors differ from pure Von Neumann. I've used the
  common answer: shared main memory (Von Neumann) with separate instruction and data caches
  (Harvard). That's accurate for typical modern CPUs, but I don't know the exact wording OCR's mark
  schemes credit.
- **Control bus direction.** Given as bidirectional (signals such as interrupts and bus requests
  travel back to the CPU). Some sources call it unidirectional; bidirectional is what I've seen in
  OCR mark schemes.
- **RISC "one clock cycle per instruction".** That's the textbook generalisation and is what's
  expected, but real RISC processors don't guarantee it, so definitions say "typically".
- **Typical uses** (CISC in desktops and laptops; RISC in phones, tablets and embedded systems;
  Harvard in embedded systems) are generalisations that OCR accepts for "uses of" questions, not
  hard rules.
- **Flash write limit.** Flash cells wear out after a limited number of writes. That's true, but it
  rarely limits normal use now, so it's a minor drawback, not a headline one.

**Wording decisions**

- Clock speed is defined as clock **cycles** per second, not "FDE cycles per second". Some revision
  guides say the latter; it's a simplification, because one instruction can take several clock
  cycles.
- "Register" uses the spec's names (PC, ACC, MAR, MDR, CIR). Other names some books use (MBR, IR)
  aren't used.
- "Virtual storage" uses the OCR guide's own definition word for word.

## Ordering items: rules (for sequences.json in Phase 4)

Only genuinely fixed orders become ordering items. Where sources differ, either every valid order
is accepted (`alternative_orders`) or the item is left out, with a note here.
