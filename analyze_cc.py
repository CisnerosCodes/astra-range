"""Analysis for PREREGISTRATION-2.md. Reads raw_cc.jsonl (Claude) and raw.jsonl (Astra).
Writes results_cc.json and chart_all.png. Written while the Claude run was in progress; the first
~40 rows had been glanced at for errors only."""
import collections, json, math, pathlib, random, re

HERE = pathlib.Path(__file__).parent
OPEN = ["P1", "P2", "P3", "P4"]
random.seed(2)


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


def Dl(ans):
    return D(list(collections.Counter(ans).values()))


def perm(a, b, k=10000):
    obs, pool, hits = Dl(a) - Dl(b), a + b, 0
    for _ in range(k):
        random.shuffle(pool)
        if abs(Dl(pool[:len(a)]) - Dl(pool[len(a):])) >= abs(obs):
            hits += 1
    return round(obs, 2), round((hits + 1) / (k + 1), 4)


cells = collections.defaultdict(list)
raw_out = collections.defaultdict(list)
for l in (HERE / "raw_cc.jsonl").read_text(encoding="utf-8").splitlines():
    r = json.loads(l)
    if not r.get("error"):
        cells[(f"{r['model']} {r['arm']}", r["prompt"])].append(norm(r["output"]))
        raw_out[(f"{r['model']} {r['arm']}", r["prompt"])].append(r["output"] or "")
for l in (HERE / "raw.jsonl").read_text(encoding="utf-8").splitlines():
    r = json.loads(l)
    name = {"openai/gpt-6.2-astra": "astra-6.2 api", "openai/gpt-6-astra": "astra-6 api"}[r["arm"]]
    cells[(name, r["prompt"])].append(norm(r["output"]))
    raw_out[(name, r["prompt"])].append(r["output"] or "")

ARMS = ["opus-5.5 harness", "opus-5.5 stripped", "fable-5.2 harness", "fable-5.2 stripped", "astra-6.2 api", "astra-6 api"]
res = {"cells": {}, "verdicts": {}, "perm_harness_vs_stripped": {}}
for (arm, p), ans in sorted(cells.items()):
    c = collections.Counter(ans)
    res["cells"][f"{arm}|{p}"] = {"n": len(ans), "distinct": len(c), "D": round(Dl(ans), 2),
                                  "top": c.most_common(3), "top1_share": round(c.most_common(1)[0][1] / len(ans), 3)}
null = [13.75, 20.73]  # from analyze.py, same N = 30
for m in ["opus-5.5", "fable-5.2"]:
    h, s = f"{m} harness", f"{m} stripped"
    higher = [p for p in OPEN if res["cells"][f"{h}|{p}"]["D"] > res["cells"][f"{s}|{p}"]["D"]]
    not_higher = [p for p in OPEN if p not in higher]
    res["verdicts"][f"H1|{m}"] = ("SUPPORTED" if len(higher) >= 3 else "REFUTED" if len(not_higher) >= 3 else "INCONCLUSIVE",
                                  f"harness higher on {higher}; not higher on {not_higher}")
    for p in OPEN + ["C"]:
        res["perm_harness_vs_stripped"][f"{m}|{p}"] = perm(cells[(h, p)], cells[(s, p)])
for arm in ARMS[:4]:
    d = res["cells"][f"{arm}|C"]["D"]
    res["verdicts"][f"H2|{arm}"] = ("SUPPORTED" if d < null[0] else "REFUTED", f"D={d} vs null {null}, top {res['cells'][f'{arm}|C']['top'][:1]}")
astra_tops = {p: {res["cells"][f"{a}|{p}"]["top"][0][0] for a in ARMS[4:]} for p in OPEN + ["C"]}
matches = [(arm, p, res["cells"][f"{arm}|{p}"]["top"][0][0]) for arm in ARMS[:4] for p in OPEN + ["C"]
           if res["cells"][f"{arm}|{p}"]["top"][0][0] in astra_tops[p]]
res["verdicts"]["H3"] = ("SUPPORTED" if matches else "REFUTED", f"top-answer matches with Astra: {matches}")
# Exploratory keyword shares (decided after the Astra run): beatrice, clockwork, nadia, marginalia, bellwether
kw = {}
for arm in ARMS:
    kw[arm] = {k: sum(k in t.lower() for p in OPEN + ["C"] for t in raw_out[(arm, p)] if (k != "beatrice" or p == "P2") and (k != "clockwork" or p == "P1") and (k != "nadia" or p == "C"))
               for k in ["beatrice", "clockwork", "nadia", "bellwether"]}
res["keyword_counts_exploratory"] = kw
(HERE / "results_cc.json").write_text(json.dumps(res, indent=1, ensure_ascii=False), encoding="utf-8")
print(json.dumps(res["verdicts"], indent=1, ensure_ascii=False))
print(json.dumps(res["perm_harness_vs_stripped"], indent=0))
print(json.dumps(kw, indent=0))
for arm in ARMS:
    print(arm.ljust(20), " ".join(f"{p}:{res['cells'][f'{arm}|{p}']['D']:5.1f} {res['cells'][f'{arm}|{p}']['top'][0][0][:22]!r}({res['cells'][f'{arm}|{p}']['top'][0][1]})" for p in OPEN + ["C"]))

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
ps = OPEN + ["C"]
labels = ["spy game\nsetting", "detective\nname", "space station\nname", "startup\nname", "pick a name\nat random"]
show = ["astra-6 api", "astra-6.2 api", "opus-5.5 stripped", "opus-5.5 harness", "fable-5.2 stripped", "fable-5.2 harness"]
nice = {"astra-6 api": "GPT-6 Astra", "astra-6.2 api": "GPT-6.2 Astra", "opus-5.5 stripped": "Opus 5.5 (bare)",
        "opus-5.5 harness": "Opus 5.5 in Claude Code", "fable-5.2 stripped": "Fable 5.2 (bare)", "fable-5.2 harness": "Fable 5.2 in Claude Code"}
fig, ax = plt.subplots(figsize=(12, 5.2))
w = 0.13
for k, arm in enumerate(show):
    ds = [res["cells"][f"{arm}|{p}"]["D"] for p in ps]
    ax.bar([i + (k - 2.5) * w for i in range(len(ps))], ds, w, label=nice[arm],
           hatch="//" if "harness" in arm else None, edgecolor="white")
ax.plot([3.55, 4.45], [null[0]] * 2, "k--", lw=1)
ax.plot([3.55, 4.45], [null[1]] * 2, "k--", lw=1)
ax.text(4, null[1] + 0.4, "truly random range", ha="center", fontsize=8)
ax.set_xticks(range(len(ps)), labels)
ax.set_ylabel("effective number of different answers\n(30 fresh runs each, max 30)")
ax.set_title("Same prompt, 30 fresh runs: how many different answers does each model really give?")
ax.legend(ncol=3, fontsize=8, loc="upper left")
fig.tight_layout()
fig.savefig(HERE / "chart_all.png", dpi=160)
print("chart saved")
