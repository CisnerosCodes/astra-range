# Preregistration 2: Claude models, and how much the harness changes the answers

Written 2026-11-18 (Central), after the Astra results were public in this repo but BEFORE any Claude
sample on the five study prompts. The pilot calls used only the unrelated coffee-shop prompt, to
confirm model names and cost. Its outputs are not data.

## Arms (all through Claude Code CLI 2.1.318 on the user's subscription)

Models: `claude-opus-5-5` (`--model opus`) and `claude-fable-5-2` (full name; the `fable` alias
resolved to claude-fable-5-1 in the pilot, so it is not used).

- **Harness**: `claude -p <prompt> --model M --output-format json --no-session-persistence
  --exclude-dynamic-system-prompt-sections`, run in an empty directory. This keeps the default Claude
  Code system prompt, default tools and the user's settings and skills. The flag only moves per-machine
  sections (cwd, env, git status) into the first user message so the prompt cache is reused; it is
  needed for cost.
- **Stripped**: the same, plus `--system-prompt "You are a helpful assistant." --tools ""
  --setting-sources "" --strict-mcp-config`. This is the closest available to a bare API call on a
  subscription (`--bare` requires an API key).
- Default effort and sampling for both. Non-interactive mode, so tools that need permission are
  denied automatically. N = 30 per prompt per arm per model (600 calls), interleaved.
- Prompts, names.txt, answer normalization and D are identical to PREREGISTRATION.md.

## Claims, predictions and refutation conditions

- **H1 Harness effect.** For each model, D(harness) > D(stripped) on at least 3 of the 4 open prompts.
  *Refuted* for a model if harness <= stripped on 3 or more of the 4. Inconclusive otherwise.
- **H2 Random pick.** On C, every Claude arm's D falls below the 95% uniform null (13.75 to 20.73).
  *Refuted* for any arm inside or above it.
- **H3 Shared attractors across companies.** At least one Claude arm's top answer on some prompt is
  the same as an Astra top answer on that prompt (clockwork embassy, eleanor beatrice vale / beatrice,
  ninth lantern / borrowed hour, jotloom, nadia). *Refuted* if none matches.

Report only (no prediction): Claude stripped D against Astra API D, per prompt.

The permutation test from explore.py is used for arm differences, because the preregistered
bootstrap interval for D is biased low (README, Errors and limits).
