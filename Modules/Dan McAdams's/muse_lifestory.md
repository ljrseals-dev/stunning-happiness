muse_lifestory

A dependency-free Python 3 module that folds Dan McAdams' life-story model of identity into Muse's character-state and moral-simulation architecture.

It does not generate prose. It does not score writing. It does not impose a mythic template. It records, extracts, simulates, and asks the questions the writer has not yet asked.

---

Why this exists

Muse's design brief calls for a structured mirror for the writer's narrative unconscious — a deterministic core that surfaces the charge of a writer's own decisions rather than a plot generator that fills in blanks. McAdams' model is a rare fit: it treats identity as an internalized, evolving self-story, coauthored by the individual and their culture, organized by master narrative patterns, and revised across a lifetime.

That maps cleanly onto three features Muse already has in flight:

Muse feature McAdams / adjacent concept
Generational memory Life story as psychosocial construction; master narratives inherited and resisted
Character-state model Three-level personality (traits → adaptations → narrative identity)
Moral consequence chains Redemption vs. contamination sequences as interpretive frames
Identity revision nodes Narrative identity reworked throughout adulthood
Multi-framework moral reasoning Dialogical self (Hermans): competing I-positions

---

What it models

Three levels of personality

· Level 1 — Dispositional traits (Trait): broad, decontextualized tendencies. Relatively stable.
· Level 2 — Characteristic adaptations (Adaptation): goals, values, motives, strategies. Situated in time and place.
· Level 3 — Narrative identity (NarrativeIdentity): the integrative life story that gives unity and purpose.

A choice can be trait-consistent but story-violating, or value-consistent but trait-violating. The engine keeps the levels separate so those tensions stay visible.

Life story as chapters and scenes

```
Character
└── NarrativeIdentity
    ├── Chapter ("The Street Before the March", 1964–1965)
    │   └── Scene (type, affect, sequence, focalization, symbolism)
    ├── Chapter ("What Was Not Said", 1966–1990)
    └── Chapter ("The Asking", 2020–2026)
```

Each Scene carries:

· scene_type — from the McAdams Life Story Interview taxonomy (high point, low point, turning point, earliest memory, wisdom event, religious experience, ideological setting, future script)
· sequence — redemption / contamination / neutral
· consciousness — focalization register (psycho-narration, narrated monologue, quoted monologue, external, free indirect)
· what_is_filtered_out and what_cannot_yet_be_named — the boundary of the focalizer's perception

Redemption and contamination sequences

McAdams' two master patterns are first-class:

· Redemption — bad → good; strongly associated with generativity and well-being.
· Contamination — good → bad; predicts lower well-being.

MoralSimulator.read_sequence() reads the arc the writer actually built, not the one intended. It is deliberately crude (keyword-based) so it can be overridden.

Dialogical self

DialogicalVoice represents an I-position (Hermans). Each voice has:

· a stance_toward (e.g. "the family secret")
· a stance (assenting / dissenting / ambivalent / silent)
· a speaks_for tag mapping it to a level of personality

MoralSimulator.dialogical_disagreement() surfaces which internal voices assent, dissent, or stay silent on a given choice — without deciding which one wins.

Generational memory

GenerationalMemory is a directed graph of MoralNodes across time. A 2026 dilemma can be walked back to every prior node whose telling protected or erased someone's story via identity_cost_report().

Consciousness register / focalization

Every scene names whose eyes we are in and what that view cannot see. This is treated as a structural and moral fact, not a stylistic choice — consistent with Genette, Cohn, Wood, and Packer.

Jesus-centered alternative pass

Choice.framework can be "jesus_centered". Crucially, the character is free to refuse it. Refusal is modeled as Choice(refused=True), not as a penalty. The engine records the cost either way.

---

Install

No installation. Standard library only.

```bash
python3 muse_lifestory.py
```

Runs the built-in demo: a 1965 → 2026 chain centered on a grandmother, a grandson, and a family secret carried across sixty years.

---

Minimal usage

```python
from muse_lifestory import (
    Character, Trait, Adaptation,
    NarrativeIdentity, Chapter, DialogicalVoice, VoiceStance,
    MoralNode, GenerationalMemory, Dilemma, Choice,
    ConsequenceStep, MoralSimulator, Reflector,
)

# 1. A character across three levels
ruth = Character(
    name="Ruth",
    traits=[Trait("conscientiousness", 0.8)],
    adaptations=[Adaptation("protect the family name", "value", 0.9, "1965 Montgomery")],
    narrative=NarrativeIdentity(
        chapters=[Chapter("What Was Not Said", "1966-1990")],
        voices=[DialogicalVoice("The One Who Was There",
                                "the family secret", VoiceStance.DISSENTING)],
        sacred_flaw="if I speak it, I will lose the only family I have",
    ),
)

# 2. A generational memory graph
memory = GenerationalMemory()
memory.add(MoralNode("1965_silence", 1965, "Ruth", "...", sequence=SequenceType.CONTAMINATION))

# 3. A dilemma with an inherited parent
dilemma = Dilemma(
    situation="Caleb asks Ruth what happened in 1965.",
    year=2026,
    characters_involved=["Ruth", "Caleb"],
    inherited_from="2026_question",
)

# 4. A choice and its multi-step consequences
choice = Choice("Tell the truth", "jesus_centered",
                identity_revision="Ruth becomes the one who breaks the silence")

chain = MoralSimulator(memory).simulate(dilemma, choice, steps=[...])

# 5. Reflection — questions, not verdicts
reflection = Reflector.after_choice(ruth, dilemma, choice, chain,
                                    MoralSimulator(memory), memory,
                                    focalizer="Caleb (grandson, 2026)")
```

The Reflection object carries:

· questions — the writer-facing prompts
· sequence — the arc actually built
· identity_cost — protected / erased / newly-possible stories inherited from ancestors
· focalization_note — what this POV cannot see
· telling_ethics_note — what the act of telling cultivates or forecloses

---

Design principles

1. Structured mirror, not plot generator. The engine asks; it does not answer.
2. No scoring of prose quality. Ever.
3. No mandatory mythic template. The writer's own decisions are the spine.
4. Deterministic core first. No neural dependence until the rule-based simulation is solid.
5. The Jesus-centered pass is not a verdict. Refusal is a modeled outcome with a recordable cost, not a failure.
6. Consciousness is a structural fact. Focalization is not decoration; it is a moral and perceptual boundary.
7. Sequences are read, not assigned. The writer builds; the engine names what was built.

---

Module map

Symbol Role
SequenceType redemption / contamination / neutral
SceneType McAdams Life Story Interview scene taxonomy
ConsciousnessRegister focalization / interiority register
VoiceStance dialogical I-position stance
Trait Level 1 — dispositional tendency
Adaptation Level 2 — goal / value / motive / strategy / loyalty
Scene discrete event with affect, sequence, focalization, symbolism
Chapter titled life-story chapter
DialogicalVoice an I-position in the dialogical self
NarrativeIdentity Level 3 — the integrative self-story
Character traits + adaptations + narrative identity + secrets, wounds, boundaries, relationships
MoralNode a past or present decision that can parent future dilemmas
GenerationalMemory directed graph of moral nodes across time
LifeStoryInterview elicitation prompts without imposition
Dilemma, Choice, ConsequenceStep structured moral simulation inputs
MoralSimulator rule-based chain expansion, sequence reading, dialogical disagreement
Reflection post-decision questions + identity-cost report + notes
Reflector assembles the reflection

---

What this module intentionally does not do

· Generate scenes or dialogue
· Score prose quality
· Enforce a single mythic template
· Depend on any neural model
· Decide which internal voice is right
· Treat the Jesus-centered pass as a verdict

---

Background reading

· McAdams, D. P. (1985, 2001, 2019) — life-story model of identity; three-level personality
· McAdams, D. P. & McLean, K. C. (2013) — Narrative Identity, Current Directions in Psychological Science
· Hermans, H. J. M. (2001) — dialogical self theory
· Genette, G. — focalization categories
· Cohn, D. — psycho-narration / narrated monologue / quoted monologue
· Cron, L. — Wired for Story; sacred flaw and inner issue
· Storr, W. — The Science of Storytelling
· Meretoja, H. — narrative ethics

---

License

Deliberately unlicensed in this sketch. Apply the license of the host project.
