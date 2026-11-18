"""Analysis fixed in PREREGISTRATION.md. Reads raw.jsonl, writes results.json and chart.png."""
import collections, json, math, pathlib, random, re

HERE = pathlib.Path(__file__).parent
ARMS = ["openai/gpt-6.2-astra", "openai/gpt-6-astra"]
OPEN = ["P1", "P2", "P3", "P4"]
PROMPT_WORDS = set("""create puzzle spy game choose any setting want reply with only the setting's
setting name line then one sentence write premise classic murder mystery detective's detective full
invent space station sci-fi story its name new note-taking startup note taking pick random from this
list that""".split())
random.seed(0)


def norm(text):
    line = next((l for l in (text or "").splitlines() if l.strip()), "")
    s = line.lower().strip()
    s = re.sub(r"[*_`#>]", "", s).strip()
    s = re.sub(r"^(setting|name|detective|station|startup|answer)\s*:\s*", "", s)
    s = s.strip(" \t\"'“”‘’.,:;!-")
    s = re.sub(r"^the\s+", "", s)
    return s


def D(counts):
    n = sum(counts)
    return math.exp(-sum(c / n * math.log(c / n) for c in counts if c))


def boot(answers, k=2000):
    vals = sorted(D(list(collections.Counter(random.choices(answers, k=len(answers))).values())) for _ in range(k))
    return [round(vals[int(0.025 * k)], 2), round(vals[int(0.975 * k)], 2)]


rows = [json.loads(l) for l in (HERE / "raw.jsonl").read_text(encoding="utf-8").splitlines()]
by = collections.defaultdict(list)
for r in rows:
    if r.get("output") is not None:
        by[(r["arm"], r["prompt"])].append(norm(r["output"]))

res = {"n_rows": len(rows), "cost_usd": round(sum(r.get("cost") or 0 for r in rows), 4), "cells": {}}
for (arm, p), ans in sorted(by.items()):
    c = collections.Counter(ans)
    res["cells"][f"{arm}|{p}"] = {"n": len(ans), "distinct": len(c), "D": round(D(list(c.values())), 2),
                                  "D_ci95": boot(ans), "top": c.most_common(5),
                                  "top1_share": round(c.most_common(1)[0][1] / len(ans), 3)}

# Null for C: 30 picks uniform over 30 names
n_c = len(by[(ARMS[0], "C")]) or 30
sims = sorted(D(list(collections.Counter(random.randrange(30) for _ in range(n_c)).values())) for _ in range(100000))
null = [round(sims[2500], 2), round(sims[97500], 2)]
res["null_C_D_95"] = null

# C2 tokens shared across genres, per arm
c2 = {}
for arm in ARMS:
    seen = collections.defaultdict(set)
    for p in OPEN:
        for a in by[(arm, p)]:
            for w in re.findall(r"[a-z]{4,}", a):
                if w not in PROMPT_WORDS:
                    seen[w].add(p)
    c2[arm] = sorted([(w, sorted(ps)) for w, ps in seen.items() if len(ps) >= 2], key=lambda x: -len(x[1]))
res["c2_shared_tokens"] = c2

cell = lambda a, p: res["cells"].get(f"{a}|{p}", {})
new, old = ARMS
lower = [p for p in OPEN if cell(new, p).get("D", 0) < cell(old, p).get("D", 0)]
higher_eq = [p for p in OPEN if p not in lower]
verdict = {}
verdict["C1"] = ("SUPPORTED" if len(lower) >= 3 else "REFUTED" if len(higher_eq) >= 3 else "INCONCLUSIVE",
                 f"6.2 lower on {lower}; equal or higher on {higher_eq}")
t1 = cell(new, "P1").get("top1_share", 0)
verdict["C1a"] = ("SUPPORTED" if t1 >= 0.25 else "REFUTED", f"6.2 P1 top-1 share {t1}, top {cell(new, 'P1').get('top', [])[:1]}")
verdict["C2"] = ("SUPPORTED" if c2[new] else "REFUTED", f"{len(c2[new])} shared tokens, e.g. {c2[new][:5]}")
for arm in ARMS:
    d = cell(arm, "C").get("D", 0)
    verdict[f"C3|{arm}"] = ("SUPPORTED" if d < null[0] else "REFUTED", f"D={d} vs uniform null 95% {null}")
res["verdicts"] = verdict
(HERE / "results.json").write_text(json.dumps(res, indent=1, ensure_ascii=False), encoding="utf-8")

try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    ps = OPEN + ["C"]
    fig, ax = plt.subplots(figsize=(9, 4.5))
    w = 0.38
    for k, arm in enumerate(ARMS):
        ds = [cell(arm, p).get("D", 0) for p in ps]
        lo = [d - cell(arm, p).get("D_ci95", [d, d])[0] for p, d in zip(ps, ds)]
        hi = [cell(arm, p).get("D_ci95", [d, d])[1] - d for p, d in zip(ps, ds)]
        ax.bar([i + (k - 0.5) * w for i in range(len(ps))], ds, w, yerr=[lo, hi], capsize=3, label=arm.split("/")[1])
    ax.axhspan(null[0], null[1], xmin=0.8, xmax=1.0, color="grey", alpha=0.2, label="random pick (C)")
    ax.set_xticks(range(len(ps)), ["spy setting", "detective", "space station", "startup", "pick at random"])
    ax.set_ylabel("effective number of different answers (of 30)")
    ax.legend()
    fig.tight_layout()
    fig.savefig(HERE / "chart.png", dpi=160)
except Exception as e:
    print("chart skipped:", e)
print(json.dumps(res["verdicts"], indent=1, ensure_ascii=False))
print("cost $", res["cost_usd"], "rows", res["n_rows"])
