# Content notes

Things to check when verifying content, and decisions about wording or ordering. Newest topic
first.

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
