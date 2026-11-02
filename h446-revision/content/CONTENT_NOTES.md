# Content notes

Things to check when verifying content, and decisions about wording or ordering. Newest topic
first.

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
