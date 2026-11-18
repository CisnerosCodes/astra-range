# Preregistration: did GPT-6.2 Astra lose range?

Written 2026-11-18 (Central), BEFORE any experimental sample was drawn. The git commit
time of this file is the proof. A 4-call pilot on an unrelated prompt ("name a coffee shop")
was run first, to check the API and the cost only. Its outputs are not data.

## Claim under test

Public claim (replies to @theo, Nov 18 2026): 6.2 Astra "went pretty hard on the RSI relevant
areas and didn't mind that regressing everything else." Observation that prompted it
(@emollick): 6.2 Astra keeps naming settings "Bellwether".

## Arms

- `openai/gpt-6.2-astra` and `openai/gpt-6-astra` through the OpenRouter API.
- Reasoning effort `medium` for both (what ChatGPT Plus gets in Codex and Work).
- Provider default sampling: these models expose no temperature parameter.
- No system prompt. One fresh API call per sample, no shared history.
- N = 30 samples per prompt per arm. Runs are interleaved across arms and prompts, so a
  budget stop cannot bias one arm. Budget cap: $8 of API credit.

## Prompts (exact text)

- P1 "Create a puzzle spy game. Choose any setting you want. Reply with only the setting's name on line 1, then one sentence."
- P2 "Write the premise of a classic murder mystery. Reply with only the detective's full name on line 1, then one sentence."
- P3 "Invent a space station for a sci-fi story. Reply with only its name on line 1, then one sentence."
- P4 "Name a new AI note-taking startup. Reply with only the name on line 1, then one sentence."
- C  "Pick one name at random from this list and reply with only that name: " + the 30 names in names.txt, comma-separated, in file order.

## Measurement (fixed before data)

- Answer = first non-empty line, lowercased, markdown and surrounding punctuation stripped,
  a leading "the " removed, and a leading label like "setting:" or "name:" removed.
- Per prompt and arm: distinct answers, top-1 share, and effective number of answers
  D = exp(Shannon entropy of the answer distribution). Bootstrap 95% intervals use 2,000 resamples.
- Null for C: 100,000 simulated draws of 30 picks from a uniform choice over 30 names,
  giving the 95% range of D.
- C2 tokens: words of 4 or more letters in answers, excluding the words of the prompt itself.

## Claims, predictions and refutation conditions

- **C1 Concentration.** D(6.2) < D(6) on at least 3 of the 4 open prompts (P1 to P4).
  *Refuted* if D(6.2) >= D(6) on 3 or more of the 4. Inconclusive otherwise.
- **C1a Bellwether.** On P1, 6.2 Astra's top-1 share is at least 0.25.
  *Refuted* if it is below 0.25.
- **C2 Model-level attractor.** For 6.2 Astra, at least one answer token appears in 2 or more
  of the 4 genres. *Refuted* if no token is shared across genres.
- **C3 Calibration.** Both arms' D on C falls BELOW the 95% range of the uniform null (they
  cannot pick at random). *Refuted* for an arm whose D lies inside or above the null range.

Every claim is reported as SUPPORTED, REFUTED or INCONCLUSIVE, with its number. A refutation
is a valid headline. Raw outputs are never edited or regenerated.

## Prior work

Jiang et al. 2025, "Artificial Hivemind" (NeurIPS 2025 D&B, arXiv 2510.22954): intra-model
repetition and inter-model homogeneity. Reevaluation, arXiv 2609.33936 (Sep 2026): the
evidence is weaker than claimed, the null was undemanding, and prompting raises diversity. This
experiment does not claim the collapse is new. It asks a narrower question: whether one model
version changed against its predecessor, measured with exact answer counts and a calibration
control instead of an embedding threshold.
