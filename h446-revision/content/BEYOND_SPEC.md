# Beyond the spec

Useful things that aren't in the H446 specification, guide or checklist, so they're kept out of
keywords, cards and tests. Good for understanding, not for marks.

## Topic 1.1

| Idea | Why it's here, not in the app |
|---|---|
| Cache levels (L1, L2, L3) | The spec only says "cache"; the size and speed of cache is enough. |
| "Von Neumann bottleneck" as a named term | The idea (instructions and data competing for one bus) is in the summary; the name isn't in the spec. |
| Superscalar processors, branch prediction, out-of-order execution | Ways real CPUs improve on simple pipelining; not on the spec. |
| Flynn's taxonomy (SISD, MISD, MIMD) | Only SIMD is mentioned, in the guide's GPU clarification. |
| Amdahl's law | Explains why more cores give diminishing returns; the spec only needs the idea that not all tasks can be split. |
| Alternative register names (MBR for MDR, IR for CIR) | OCR uses MDR and CIR. |
| Overclocking, thermal throttling | Extensions of clock speed; not on the spec. |
| Specific CPU families (x86, ARM) by name | Examples of CISC/RISC are fine in answers, but you don't need the names. |
| SSD internals (NAND cells, wear levelling, TRIM), NVMe, RAID | How storage works internally isn't required. |
| Co-processors (e.g. maths co-processors, NPUs) | Not mentioned anywhere in the sources. |
