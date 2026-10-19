# 12 · Later: local AI and the 128GB box

**What:** when (and whether) to buy a Mac Studio M5 Max, NVIDIA DGX Spark or AMD Strix Halo (Ryzen AI Max+ 395) machine, and what moves onto it.
**Short answer:** **not yet.** Your own spec ranks raw hardware performance **last (12 of 12)**, says Jarvis alone would be fine on 24GB, and gates Phase 2 on "Phase 1 used daily for 2 weeks". All three machines now cost roughly **£4,000–5,500**, far above your original £600–1,000 guide.

## The decision gate

Buy only when **all** of these are true:

- [ ] Phase 1 (accountability loop, briefings, room voice, research jobs) has been used **daily for 2+ weeks**, measured from the weekly reviews
- [ ] You can name what the box fixes that you've actually hit. For example: "voice latency annoys me daily", "I want behavioural analysis to run locally", or "I want offline Jarvis"
- [ ] It doesn't eat revision time or money you need for the resit year. After exams (summer 2027) is a natural point to decide
- [ ] You've re-checked prices. They moved a lot in 2026

## What 128GB is actually for

| Workload | Memory it needs | Needs 128GB? |
|---|---|---|
| Jarvis's local jobs: intent, summaries, behavioural inference (8–30B models, 4-bit) | 8–24GB | No |
| Whisper + Piper + wake word | < 4GB | No |
| Large private models (70B dense, or 100B+ mixture-of-experts) | 48–100GB+ | **Yes** |

Your spec already spotted this: the extra RAM serves your **separate privacy goal of running big models locally**, not Jarvis. Judge the purchase against that goal.

## Comparison (prices checked 19/10/2026; volatile)

| | Mac Studio M5 Max 128GB | NVIDIA DGX Spark 128GB | Strix Halo (Ryzen AI Max+ 395) 128GB |
|---|---|---|---|
| UK price | No UK 128GB listing found. The 36GB base is £2,499 (Scan); 128GB is €5,859 in Austria and ~$5,399 in the US, so expect **£5,000+** | Scan launch price £3,699.98; recent listings up to **£4,673**, and rising | MSI PRO MAX Edge AI+ **£4,499** list (Scan, Oct 2026); other brands vary a lot |
| Memory bandwidth (drives tokens/s) | Highest of the three (M4 Max was 546 GB/s; check the M5 Max figure) | 273 GB/s | 256 GB/s |
| OS | macOS | DGX OS (Ubuntu, ARM) | Linux or Windows (x86) |
| OpenClaw macOS app: **native Voice Wake + Talk** | ✅ | ❌ | ❌ |
| iMessage (`imsg`) | ✅ | ❌ | ❌ |
| iOS development (Xcode) | ✅ | ❌ | ❌ |
| Local LLM tooling | MLX, llama.cpp, LM Studio, Ollama | CUDA: everything, best for fine-tuning | llama.cpp / Ollama (ROCm or Vulkan), improving |
| Fit for **Jarvis** | **Best** | Weakest: it's a CUDA dev box | Good value on Linux |

**Recommendation if you buy:**
- **Mac Studio**, if Jarvis is the main reason. It's the only option that gives you OpenClaw's native voice stack, iMessage and Xcode, and it has the fastest memory.
- **Strix Halo**, if the main goal is cheap-ish big local models on Linux and you're happy keeping the Python voice daemon.
- **Skip the DGX Spark** unless you specifically want CUDA for ML coursework or experiments.

There's also a cheaper middle path worth pricing at the time: a 64GB machine of any of these covers every Jarvis workload with headroom.

## What moves to the new box

1. **Local models:** run `openclaw onboard` → *Managed local server* (the llama.cpp plugin picks a model that fits), or use LM Studio or Ollama. Add the result as a provider and keep Claude as the primary for hard reasoning.
2. **Private jobs pinned to local:**
   - a weekly behavioural-pattern job: `openclaw automations add … --model <local-model>`
   - dreaming on the local model (`plugins.entries.memory-core.config.dreaming.model`)
   - then lift the "no bulk analysis" rule in `AGENTS.md`
3. **Voice:**
   - **Mac Studio:** use the OpenClaw macOS app's Voice Wake + Talk with a local MLX TTS. Retire the Python daemon (or keep it for the `/say` endpoint).
   - **Strix Halo / Spark:** move `jarvis_voice.py` there and switch Whisper to `small.en`/`medium.en` on the GPU. Wake → first audio should drop to about 1.5–2.5 s.
4. **Offline mode:** a local model as the last entry in `agents.defaults.model.fallbacks`, so basic Q&A, timers and memory keep working when the internet drops.
5. **Where the Gateway lives:** keep it on the OptiPlex at first (proven and always on). Consolidate onto the new box only after a month of stability. Two machines means more to maintain, as your spec notes.
