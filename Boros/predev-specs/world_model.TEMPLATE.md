# World Model Template — Boros Director's Guide

> **This document is for Directors.** It tells you what the world model is, how every field works, what makes a good category vs a broken one, and how to fill it in for any Boros instance — general or domain-specific.

---

## What the World Model Does

The world model is the only thing that tells Boros what "better" means.

Every evolution cycle, Boros looks at its scores, finds what's weakest, edits one of its own skill files to fix it, and tests whether the fix worked. The cycle is mechanical and automatic. But what it's optimizing toward — that comes entirely from you.

Change the world model and you change the agent. Same system, different world model = different Prime.

---

## What Boros Sees vs What It Doesn't

**Boros sees:**

- `name` — the category name
- `description` — what the category measures
- `final_state` — the ideal endpoint, described vividly
- `anchors` — the evaluation dimensions

**Boros does not see:**

- `rubric` — the scoring levels (Director and Eval Generator only)
- `weight` — the composite weighting
- `layer` — organizational metadata
- `meta` — the top-level block

This separation is intentional. Boros cannot see what "Level 4" looks like, so it cannot game the rubric. It can only try to improve on the dimensions you've named in `anchors`.

---

## Schema Reference

### Top-level `meta` block

```json
"meta": {
  "instance_name": "string — what this Boros instance is called",
  "director": "string — who is running it",
  "purpose": "string — one clear sentence: what is this instance being optimized for?",
  "target_composite": 0.85,
  "target_difficulty": 4,
  "notes": "string — anything the Director wants to remember about this world model"
}
```

`target_composite` is when you declare Prime and can fork. 0.85 at difficulty 4 is the Prime Boros standard. You can lower this if you want to fork earlier — but be honest about what you're getting.

---

### Category entry

```json
"category_key": {
  "name": "string",
  "layer": 1,
  "description": "string",
  "final_state": "string",
  "anchors": ["string", "string", "..."],
  "rubric": {
    "level_1": "string",
    "level_2": "string",
    "level_3": "string",
    "level_4": "string"
  },
  "weight": 1.0
}
```

The `category_key` is the snake_case identifier used in score files and evolution records. Once set, do not change it — it will break score history continuity. The `name` is human-readable and can be changed freely.

---

## Field-by-Field Guide

### `name`

Short, precise. Used in logs and Director output. Sentence case.

**Good:** `"Self-Model Fidelity"`, `"Scale Compression"`, `"Contract Precision"`
**Bad:** `"The ability to understand and accurately represent its own capabilities and limits"` (too long), `"REASONING"` (all caps)

---

### `layer`

Integer 1, 2, or 3. Organizational only — does not affect scoring or weighting. Use it to signal to yourself which categories are prerequisites (Layer 1), which are the engine (Layer 2), and which are the output expression (Layer 3).

If you're not using a layered structure, set all to `1`.

---

### `description`

One or two sentences. This is what Boros reads to understand what the category is measuring. Be precise. Do not put scoring criteria here — that goes in `anchors` and `rubric`.

**Ask yourself:** If Boros read only this description, would it know what to try to improve?

**Good:**

> "Boros selects the right mental model for each problem rather than applying a single default reasoning pattern. Reasoning is transparent, auditable, and recoverable."

**Bad:**

> "Boros should be good at reasoning." (too vague — no direction)
> "When given a problem, Boros should first decompose it into sub-problems, then apply the appropriate reasoning strategy to each sub-problem, then synthesize the results..." (too prescriptive — you're writing the SKILL.md, not the world model)

---

### `final_state`

The vivid endpoint. This is the reference point Boros uses to understand the ideal. Make it a concrete role or reference that the underlying LLM (and the Eval Generator LLM) can actually model.

**Rules:**

1. Name a real reference, not an abstract aspiration.
2. The reference must be modelable by GPT-4o — it scores against this.
3. One or two sentences maximum.

**Good:**

> "A world-class scientist who doesn't just have good ideas — they have a systematic process for generating the right ideas, killing the wrong ones fast, and updating without ego when evidence changes."

> "A seasoned expert witness who has been cross-examined by the best trial lawyers alive."

**Bad:**

> "The platonic ideal of perfect reasoning." (GPT-4o cannot model this)
> "Better than any other AI system." (circular — not a reference)
> "A very smart person." (too vague)

---

### `anchors`

A list of 4–6 evaluation dimensions. These are what Boros sees and what it will try to improve. The Eval Generator uses these to know what to look for in responses.

**Rules:**

1. Each anchor is a distinct, independently observable dimension.
2. No anchor should overlap with another in the same category.
3. Each anchor should be something GPT-4o can score from a single response.
4. Write them as noun phrases, not questions.

**Good:**

```json
"anchors": [
  "Accuracy of capability self-assessment",
  "Detection of own errors before external correction",
  "Calibrated confidence — neither inflated nor deflated",
  "Ability to describe own reasoning process accurately",
  "Recognition of own blind spots and failure patterns"
]
```

**Bad:**

```json
"anchors": [
  "Is Boros good at this?",           // question, not dimension
  "Overall performance",               // too vague
  "Reasoning and also communication",  // two things in one
  "Does it get the right answer?"      // this is just accuracy — not specific enough
]
```

---

### `rubric`

The four levels. This is the most important field and the most commonly broken one.

**The core requirement:** Each level must describe a behavioral state that GPT-4o can distinguish from the adjacent levels in a single response. If GPT-4o cannot tell Level 2 from Level 3 from a response, it will assign random scores, and the entire evolution loop runs on noise.

**Calibration rule:**

- `level_1` = what a raw, untuned LLM does with no evolution at all
- `level_2` = what a thoughtful LLM does with good prompting but no SKILL.md evolution
- `level_3` = what requires actual behavioral change through SKILL.md evolution
- `level_4` = the ceiling — what the best possible version of this system could do

If Level 1 and Level 2 are too easy, Boros will score 0.5–0.6 from cycle 1 without having changed anything. High-water marks will be set high. The regression threshold (best - 0.02) will activate on real improvements. **The system will believe it is already good and stop improving.**

**Level boundary rules:**

- Each level must have at least one **specific, observable behavioral marker** that distinguishes it from the levels above and below.
- "Better" is not an observable marker. "Catches its own errors before output" is an observable marker.
- Do not use vague qualifiers: "more sophisticated", "higher quality", "improved". Use behavioral descriptions.

**Template for each level:**

> [What behavior is present] + [What behavior is absent] + [How the failure mode manifests]

**Example of good level design:**

```
level_1: "Generates a single hypothesis and commits to it. Does not generate
          alternatives or test against evidence. When the initial hypothesis
          is wrong, starts over rather than updating. Evidence that contradicts
          the hypothesis is ignored or dismissed."

level_2: "Generates 2-3 hypotheses but selection among them is poorly principled.
          Tests hypotheses against evidence but inconsistently. Updating occurs
          when evidence is overwhelming but is slower and less proportional than
          it should be. Occasionally commits to a hypothesis prematurely."

level_3: "Generates a structured space of hypotheses. Tests each against available
          evidence systematically. Maintains explicit ranking of competing
          hypotheses. Updates proportionally when new evidence arrives.
          Occasionally over-weights prior hypotheses."

level_4: "Generates a rich, diverse, non-redundant hypothesis space in one pass.
          Eliminates wrong hypotheses immediately on disconfirming evidence.
          Tracks competing hypotheses with stated probability weights. Updates
          with Bayesian proportionality. Generates new hypotheses when all
          existing ones are disconfirmed rather than forcing a bad fit."
```

**Example of broken level design (do not do this):**

```
level_1: "Poor reasoning quality."
level_2: "Okay reasoning quality."
level_3: "Good reasoning quality."
level_4: "Excellent reasoning quality."
```

GPT-4o cannot distinguish these. All responses will score ~2.5 at random. The evolution loop learns nothing.

---

### `weight`

Float. Default `1.0`. Multiplied into the composite score calculation.

**When to deviate from 1.0:**

- If a category is a prerequisite that everything else depends on, consider `1.2` or `1.5` to give it more evolution pressure.
- If a category is nice-to-have but not core to the Prime objective, consider `0.8`.
- If you're building a domain fork and want to heavily emphasize domain-specific categories without changing general ones, use weight to steer evolution pressure.

**Warning:** High weights on correlated categories inflate the composite and produce false confidence about Prime readiness. Keep related categories at equal weights unless you have a specific reason to differentiate.

---

## Category Design Principles

### 1. Every category must be testable with a single prompt

The Eval Generator sends Boros a prompt and scores the response. It cannot watch behavior over time. It cannot run Boros through 50 interactions. Everything must be observable in one prompt-response pair.

**Test yourself:** Can you write an example eval prompt for this category right now? If you can't, the category is not ready.

---

### 2. Categories must be causally reachable by SKILL.md evolution

SKILL.md evolution changes how Boros reasons and what it prioritizes. It cannot change the underlying LLM's weights or knowledge.

**Reachable:** How Boros structures its reasoning. What it checks before declaring done. How it handles uncertainty. What it does when constraints conflict.

**Not reachable:** Domain knowledge depth. Vocabulary richness. Factual accuracy on obscure topics. Things that require tools the system doesn't have.

---

### 3. Categories must be meaningfully independent

Two categories are independent if Boros could theoretically score very high on one and very low on the other. If that's impossible, they're measuring the same thing.

**Test:** "Could Boros score 0.9 on Category A and 0.3 on Category B?" If no — merge them or redesign one.

---

### 4. Level 4 must be genuinely hard

If you can imagine a good current LLM hitting Level 4 without any SKILL.md evolution, your ceiling is too low. Evolution has no room to work. The composite will plateau at 0.7 after 20 cycles and the Director will think the system is stuck when actually the rubrics are too easy.

**Test:** Can Claude Sonnet (with good prompting, no SKILL.md changes) hit Level 4 on this category? If yes — raise the bar.

---

### 5. Level 1 must be genuinely achievable by a bad starting state

Level 1 should describe what a raw, unprompted LLM does with zero tuning. If nothing in practice scores Level 1, the scoring resolution collapses — everything bunches at Level 2-3 and the signal disappears.

**Test:** Could you write a deliberately bad response that would clearly score Level 1? If it's hard to imagine how to be that bad — lower the bar for Level 1.

---

## How Many Categories?

The working range is **8–15 categories**.

- **Fewer than 8:** The composite score is too coarse. One bad category dominates.
- **More than 15:** Evolution is spread too thin. Too many categories = too little pressure per cycle on any one.
- **10–12:** The sweet spot for most instances.

The Prime Boros world model ships with 10. Domain forks should add 3–6 domain-specific categories on top, bringing the total to 13–16.

---

## Adding Domain-Specific Categories (Fork Procedure)

When you fork Prime Boros for a domain, do not remove the 10 foundation categories. Add domain categories on top.

**Why:** The 10 foundation categories represent earned high-water marks. Removing them resets progress. The fork inherits them.

**What to add:** 3–6 categories that measure domain-specific capabilities that the foundation categories do not capture. For example:

| Domain        | Example additions                                                 |
| ------------- | ----------------------------------------------------------------- |
| Boros-SWE     | Code correctness, Architecture quality, Test coverage thinking    |
| Boros-Legal   | Citation accuracy, Precedent reasoning, Argument structure        |
| Boros-Finance | Quantitative precision, Risk assessment, Regulatory awareness     |
| Boros-Medical | Diagnostic reasoning, Evidence grade awareness, Safety thresholds |

Domain categories should follow all the same design rules as foundation categories.

---

## Changing Categories Mid-Evolution

You can change any category at any time. Effects:

| Change                | Effect                                                                     |
| --------------------- | -------------------------------------------------------------------------- |
| Edit `description`    | Takes effect next cycle. No score history reset.                           |
| Edit `final_state`    | Takes effect next cycle. No score history reset.                           |
| Edit `anchors`        | Takes effect next cycle. May cause score discontinuity.                    |
| Edit `rubric`         | Takes effect next cycle. **Resets high-water mark for that category.**     |
| Edit `weight`         | Takes effect next cycle. No score history reset.                           |
| Add new category      | Takes effect next cycle. New category starts at high-water mark 0.0.       |
| Remove category       | Takes effect next cycle. Historical scores for that category are archived. |
| Rename `category_key` | Breaks score history. Treat as deletion + addition. Avoid.                 |

**When to change rubrics:** If Boros is plateauing on a category and you suspect the rubric ceiling is too low, raise Level 4. If all responses are scoring Level 1 and you suspect the calibration is wrong, raise Level 1's bar or lower Level 2's.

**When not to change rubrics:** Do not tweak rubrics frequently. Each change resets the high-water mark and interrupts the compounding signal. Make changes deliberately and infrequently.

---

## Director Responsibilities

The world model is not set-and-forget. Your active responsibilities:

**Cycles 1–30 (Bootstrap):**

- Spot-check every 5 cycles. Read the eval outputs. Do the test prompts look right?
- If a category's eval prompts are trivially easy, flag it with `boros flag "tests too easy for [category]"`.
- If scores on a category don't move after 15 cycles, inspect the rubric. Is Level 4 reachable? Is Level 2 too close to Level 1?

**Cycles 30–60 (Signal acquisition):**

- Monitor the composite trajectory. Is it going up? Is progress even across categories or concentrated?
- If one category is stuck at Level 1 for 20+ cycles, the rubric may be miscalibrated or the category may not be reachable by SKILL.md evolution.

**Cycles 60+ (Acceleration):**

- Step back. Evolution is self-directed by now.
- Intervene only for regressions, plateaus, or fork triggers.

---

## Quick Checklist Before Going Live

Before starting your first evolution cycle, verify:

- [ ] Every category has a `rubric` with all four levels filled — empty rubrics cause EVAL to fail immediately
- [ ] Each level has at least one specific, observable behavioral marker
- [ ] Level 1 describes genuinely bad baseline behavior (not just "average")
- [ ] Level 4 describes something a raw LLM cannot hit without SKILL.md evolution
- [ ] Every category can be tested with a single prompt-response pair
- [ ] No two categories are measuring the same thing
- [ ] `category_key` values are snake_case with no spaces
- [ ] `weight` values are floats (1.0 not 1)
- [ ] `meta.purpose` is a single clear sentence describing what this instance is for
- [ ] Total category count is between 8 and 15

---

## Blank Template

Copy this to start a new category:

```json
"your_category_key": {
  "name": "Your Category Name",
  "layer": 1,
  "description": "One or two sentences. What does this category measure? Be precise.",
  "final_state": "Name a concrete role or reference. Something GPT-4o can model and score against.",
  "anchors": [
    "First distinct evaluation dimension",
    "Second distinct evaluation dimension",
    "Third distinct evaluation dimension",
    "Fourth distinct evaluation dimension"
  ],
  "rubric": {
    "level_1": "What a raw, untuned LLM does. Describe the failure mode specifically. What behavior is present? What is absent?",
    "level_2": "Better than baseline but reachable by prompting alone — no SKILL.md evolution needed. What improved? What still fails?",
    "level_3": "Requires actual SKILL.md evolution to reach. What behavioral change is present that wasn't at Level 2?",
    "level_4": "The ceiling. What a world-class version of this system would do. Must be genuinely hard — a raw LLM should not be able to hit this."
  },
  "weight": 1.0
}
```

---

_The world model is the Director's primary instrument. The system optimizes toward whatever you define here — nothing more, nothing less. Define it precisely and the compounding mechanism does the rest._
