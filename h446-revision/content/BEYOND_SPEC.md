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

## Topic 1.2

| Idea | Why it's here |
|---|---|
| Semantic analysis as a separate compilation stage | Some books add it; the spec's four stages don't include it. |
| UEFI (the modern replacement for BIOS) | The spec says BIOS. |
| Hypervisors (type 1/type 2), containers such as Docker | The spec only needs "virtual machine". |
| Specific licences (GPL, MIT, Creative Commons) | Open vs closed source is enough. |
| Just-in-time (JIT) compilation | Not on the spec; intermediate code plus virtual machine is. |
| Relative addressing, register addressing | Only immediate, direct, indirect and indexed are on the spec. |
| Abstract classes, interfaces, static methods, multiple inheritance | The pseudocode guide says static methods aren't expected; the others aren't mentioned. |
| Scrum, Kanban, sprints | Agile is required, and extreme programming specifically; other agile frameworks aren't. |

## Topic 1.3

| Idea | Why it's here |
|---|---|
| The OSI model | The guide says explicitly that it isn't expected. |
| Digital signatures and certificates | Uses of asymmetric encryption, but not in the spec or guide. |
| Salting password hashes | A real-world best practice; the spec only mentions storing passwords as hashes. |
| Specific ciphers (Caesar, Vernam, AES, RSA) and compression algorithms (Huffman, LZW) | Only symmetric/asymmetric, RLE and dictionary coding are on the spec. |
| Details of specific protocols (HTTP, FTP, SMTP, POP3, IMAP), IPv4 vs IPv6, subnetting | The guide says you won't be asked to recall information about any specific protocol. |
| MAC addresses in detail | Mentioned in the link layer and NIC definitions only. |
| Outer, left and right joins | Appendix 5d says there's no expectation to know them. |
| BCNF and higher normal forms | The spec stops at 3NF. |
| The PageRank formula and damping factor | "High level" only. |
