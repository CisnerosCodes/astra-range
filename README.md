# astra-range: did GPT-6.2 Astra lose range?

300 fresh API calls on 2026-11-18. Each of 5 prompts was run 30 times on each of 2 models, at medium
reasoning effort, through OpenRouter (provider: OpenAI), with no system prompt. Total cost: $1.07.
The claims, predictions and analysis were committed before any sample was read (see the git log and
`PREREGISTRATION.md`).

## Results (preregistered)

| Claim | Verdict | Number |
|---|---|---|
| C1: 6.2 has fewer effective answers than 6 on 3 or more of 4 open prompts | **REFUTED** | 6.2 was equal or higher on spy setting, detective and space station; lower only on startup name (12.0 vs 12.6) |
| C1a: on the spy prompt, 6.2's top answer takes 25% or more | SUPPORTED | "Clockwork Embassy", 10 of 30 |
| C2: one answer word recurs across genres for 6.2 | SUPPORTED (weak) | "borrowed" and "unsent" in both spy settings and station names |
| C3: neither model can pick at random from a list of 30 | SUPPORTED, both | 6.2 picked "Nadia" 21 of 30, D = 3.0. 6 picked "Nadia" 22 of 30, D = 2.0. A truly random picker has D between 13.8 and 20.7 (95%) |

Effective number of answers D = exp(Shannon entropy). The maximum is 30.

| Prompt | 6.2 Astra D | 6 Astra D | 6.2 top answer | 6 top answer |
|---|---|---|---|---|
| Spy game setting | 9.5 | 5.7 | clockwork embassy (10) | clockwork embassy (12) |
| Detective name | 19.4 | 4.7 | beatrice eleanor vale (4) | eleanor beatrice vale (19) |
| Space station | 10.8 | 5.9 | borrowed hour (11) | ninth lantern (12) |
| Startup name | 12.0 | 12.6 | jotloom (8) | jotloom (6) |
| Pick at random | 3.0 | 2.0 | nadia (21) | nadia (22) |

## Exploratory (not preregistered, written after reading results)

- Permutation test of the D difference: only the detective prompt is clearly different
  (p = 0.001). The other differences are not distinguishable at N = 30 (p = 0.19 to 0.89).
- The detective result is narrower than it looks: 27 of 30 detective names contain "Beatrice" on
  BOTH versions. 6.2 varies the rest of the name; it did not escape the attractor.
- 6.2 used "clockwork" in 18 of 30 spy settings (6: 12 of 30). Both versions share their top answer on
  the spy and startup prompts.
- "Bellwether" appeared in 0 of 300 outputs. This setup did not reproduce @emollick's observation,
  which came from a different prompt and the ChatGPT or Codex product, not a bare API call.

## Errors and limits

- **Method error in the preregistered analysis:** the bootstrap interval for D is biased low.
  Resampling with replacement loses rare answers, so some observed values sit above their own interval.
  Those intervals are reported in results.json but should not be used. The permutation test in
  `explore.py` replaces them.
- N = 30 per cell, one effort level, one day, one provider route.
- Answers are exact strings after light normalization, so near-duplicates ("beatrice vale" and
  "beatrice eleanor vale") count as different. This inflates D where names vary in small ways.
- 6.2 Astra at medium effort used a median of 0 reasoning tokens (6 Astra: 42). The effort setting
  does not guarantee that the model thinks.

## Reproduce

`python run.py 8` (needs OPENROUTER_API_KEY), then `python analyze.py` and `python explore.py`.
Files: `raw.jsonl` (every output, unedited), `results.json`, `explore.json`, `chart.png`.
