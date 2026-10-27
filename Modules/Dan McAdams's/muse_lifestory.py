```python
"""
muse_lifestory.py
=================

A dependency-free Python 3 sketch that folds Dan McAdams' life-story model
into Muse's character-state and moral-simulation architecture.

Design constraints (matching the Muse brief):
  - No prose generation. The engine records, extracts, and asks questions.
  - No scoring of "good" or "bad" writing.
  - No mandatory mythic template. The writer's own decisions are the spine.
  - Standard library only.

Concepts modeled:
  * Three-level personality (McAdams): traits / adaptations / narrative identity
  * Life story as chapters -> scenes -> meaning-making
  * Redemption vs. contamination sequences
  * Dialogical self (Hermans): multiple I-positions in conflict
  * Generational memory: narrative identity as a psychosocial construction
  * Consciousness register / focalization as a structural fact
  * Identity revision nodes as first-class events in the consequence graph
  * A Jesus-centered alternative pass that leaves the character free to refuse
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, Iterable, Optional


# ---------------------------------------------------------------------------
# Enumerations
# ---------------------------------------------------------------------------

class SequenceType(Enum):
    """McAdams' master narrative patterns."""
    REDEMPTION = "redemption"      # bad -> good; often generativity-linked
    CONTAMINATION = "contamination"  # good -> bad; often well-being-lowering
    NEUTRAL = "neutral"            # neither arc yet claimed by the character


class SceneType(Enum):
    """Scene categories from the McAdams Life Story Interview."""
    HIGH_POINT = "high_point"
    LOW_POINT = "low_point"
    TURNING_POINT = "turning_point"
    EARLIEST_MEMORY = "earliest_memory"
    POSITIVE_CHILDHOOD = "positive_childhood"
    NEGATIVE_CHILDHOOD = "negative_childhood"
    WISDOM_EVENT = "wisdom_event"
    RELIGIOUS_EXPERIENCE = "religious_experience"
    IDEOLOGICAL_SETTING = "ideological_setting"
    FUTURE_SCRIPT = "future_script"


class ConsciousnessRegister(Enum):
    """Focalization / interiority cues (Genette, Cohn, Wood, Packer)."""
    PSYCHO_NARRATION = "psycho_narration"    # narrator describes inner life
    NARRATED_MONOLOGUE = "narrated_monologue"  # third person, character's idiom
    QUOTED_MONOLOGUE = "quoted_monologue"    # first person, direct
    EXTERNAL = "external"                    # behavior only; interiority withheld
    FREE_INDIRECT = "free_indirect"          # slippage between narrator and character


class VoiceStance(Enum):
    """How a dialogical I-position relates to the present decision."""
    ASSENTING = "assenting"
    DISSENTING = "dissentng"
    AMBIVALENT = "ambivalent"
    SILENT = "silent"


# ---------------------------------------------------------------------------
# Level 1: Dispositional traits (the social actor)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Trait:
    """A broad, decontextualized dispositional tendency (Big Five territory)."""
    name: str
    intensity: float  # 0.0 .. 1.0
    note: str = ""


# ---------------------------------------------------------------------------
# Level 2: Characteristic adaptations (the motivated agent)
# ---------------------------------------------------------------------------

@dataclass
class Adaptation:
    """A goal, value, motive, or strategy, socially and temporally situated."""
    name: str
    kind: str           # "goal" | "value" | "motive" | "strategy" | "loyalty"
    weight: float       # 0.0 .. 1.0
    context: str = ""   # e.g. "1965 Montgomery", "2026 Atlanta"
    note: str = ""


# ---------------------------------------------------------------------------
# Level 3: Narrative identity (the autobiographical author)
# ---------------------------------------------------------------------------

@dataclass
class Scene:
    """A discrete remembered or anticipated event within a chapter."""
    label: str
    scene_type: SceneType
    setting: str
    characters_present: list[str] = field(default_factory=list)
    affect: float = 0.0               # -1.0 .. 1.0 felt valence
    sequence: SequenceType = SequenceType.NEUTRAL
    consciousness: ConsciousnessRegister = ConsciousnessRegister.NARRATED_MONOLOGUE
    what_is_filtered_out: str = ""    # focalization: what the POV cannot see
    what_cannot_yet_be_named: str = ""  # repression / pre-verbal
    symbolism: list[str] = field(default_factory=list)  # palette hooks


@dataclass
class Chapter:
    """A life-story chapter, as the character would title it."""
    title: str
    era: str
    scenes: list[Scene] = field(default_factory=list)
    dominant_sequence: SequenceType = SequenceType.NEUTRAL


@dataclass
class DialogicalVoice:
    """An I-position (Hermans). Identity is negotiated among these."""
    name: str
    stance_toward: str       # e.g. "the family secret", "the church", "the self"
    stance: VoiceStance = VoiceStance.AMBIVALENT
    speaks_for: str = ""     # which level of personality it draws on


@dataclass
class NarrativeIdentity:
    """The internalized, evolving self-story that constitutes identity."""
    chapters: list[Chapter] = field(default_factory=list)
    voices: list[DialogicalVoice] = field(default_factory=list)
    master_narratives_inherited: list[str] = field(default_factory=list)
    master_narratives_resisted: list[str] = field(default_factory=list)
    sacred_flaw: str = ""          # Cron: the lie the character believes
    inner_issue: str = ""          # Cron: the wound the flaw protects
    ideological_setting: str = ""  # McAdams: the belief frame

    def dominant_sequence(self) -> SequenceType:
        counts: dict[SequenceType, int] = {}
        for ch in self.chapters:
            counts[ch.dominant_sequence] = counts.get(ch.dominant_sequence, 0) + 1
        if not counts:
            return SequenceType.NEUTRAL
        return max(counts, key=counts.get)


# ---------------------------------------------------------------------------
# The character as a whole
# ---------------------------------------------------------------------------

@dataclass
class Character:
    name: str
    traits: list[Trait] = field(default_factory=list)
    adaptations: list[Adaptation] = field(default_factory=list)
    narrative: NarrativeIdentity = field(default_factory=NarrativeIdentity)
    secrets: list[str] = field(default_factory=list)
    wounds: list[str] = field(default_factory=list)
    moral_boundaries: list[str] = field(default_factory=list)
    relationships: dict[str, str] = field(default_factory=dict)  # name -> bond

    def trait(self, name: str) -> Optional[Trait]:
        for t in self.traits:
            if t.name == name:
                return t
        return None

    def adaptation(self, name: str) -> Optional[Adaptation]:
        for a in self.adaptations:
            if a.name == name:
                return a
        return None


# ---------------------------------------------------------------------------
# Generational memory: narrative identity as psychosocial construction
# ---------------------------------------------------------------------------

@dataclass
class MoralNode:
    """A past or present decision that can parent future dilemmas."""
    node_id: str
    year: int
    actor: str
    summary: str
    sequence: SequenceType
    identity_cost: str = ""     # whose story is protected / erased
    identity_gain: str = ""     # what new self-story becomes possible
    consequences: list[str] = field(default_factory=list)
    children: list[str] = field(default_factory=list)  # downstream node_ids


class GenerationalMemory:
    """A directed graph of moral nodes across time."""

    def __init__(self) -> None:
        self._nodes: dict[str, MoralNode] = {}

    def add(self, node: MoralNode) -> None:
        self._nodes[node.node_id] = node

    def link(self, parent_id: str, child_id: str) -> None:
        self._nodes[parent_id].children.append(child_id)

    def ancestors(self, node_id: str) -> list[MoralNode]:
        """Walk the causal parents of a present dilemma."""
        out: list[MoralNode] = []
        seen: set[str] = set()
        stack = [node_id]
        while stack:
            current = stack.pop()
            node = self._nodes.get(current)
            if node is None or current in seen:
                continue
            seen.add(current)
            out.append(node)
            for pid, pnode in self._nodes.items():
                if current in pnode.children:
                    stack.append(pid)
        return sorted(out, key=lambda n: n.year)

    def identity_cost_report(self, node_id: str) -> dict[str, list[str]]:
        """Summarize whose stories are protected, erased, or newly possible."""
        report: dict[str, list[str]] = {"protected": [], "erased": [], "possible": []}
        for node in self.ancestors(node_id):
            if node.identity_cost:
                report["erased"].append(f"{node.year} {node.actor}: {node.identity_cost}")
            if node.identity_gain:
                report["possible"].append(f"{node.year} {node.actor}: {node.identity_gain}")
        return report


# ---------------------------------------------------------------------------
# Life Story Interview: elicitation without imposition
# ---------------------------------------------------------------------------

class LifeStoryInterview:
    """
    A structured protocol that asks for chapters and scenes without dictating
    their number or content. Mirrors McAdams' 22-segment instrument, reduced
    to the questions that generate structured data Muse can consume.
    """

    PROMPTS: tuple[str, ...] = (
        "Picture this life as if it were a book. Divide it into chapters.",
        "Of these chapters, which is the high point? The low point? The turning point?",
        "What is the earliest scene still charged with feeling?",
        "Where is the wisdom event—the moment something was understood that cannot be un-understood?",
        "What is the religious or ideological setting the character stands inside?",
        "What is the future chapter the character is already rehearsing?",
    )

    @staticmethod
    def chapter_prompt(index: int) -> str:
        return f"Chapter {index}: what is this chapter's title, and what does it cost to name it that?"

    @staticmethod
    def sequence_prompt(scene: Scene) -> str:
        if scene.sequence is SequenceType.REDEMPTION:
            return "Is the good at the end of this scene earned, or merely asserted?"
        if scene.sequence is SequenceType.CONTAMINATION:
            return "Is the ruin in this scene authored, or suffered, or both?"
        return "Does this scene still refuse a sequence? What would it mean to assign one?"

    @staticmethod
    def focalization_prompt(scene: Scene) -> str:
        return (
            f"Whose eyes are we in for '{scene.label}'? "
            f"What is filtered out: {scene.what_is_filtered_out or '[unnamed]'}? "
            f"What can the focalizer not yet name: {scene.what_cannot_yet_be_named or '[unnamed]'}?"
        )


# ---------------------------------------------------------------------------
# Moral Simulation Room (structured, rule-based, no scoring)
# ---------------------------------------------------------------------------

@dataclass
class Choice:
    label: str
    framework: str          # "consequentialist" | "deontological" | "virtue" |
                            # "care" | "jesus_centered" | "narrative_ethics"
    description: str
    foreseen_consequences: list[str] = field(default_factory=list)
    identity_revision: str = ""   # what self-story this requires
    refused: bool = False         # the Jesus-centered pass may be refused


@dataclass
class Dilemma:
    situation: str
    year: int
    characters_involved: list[str]
    inherited_from: Optional[str] = None  # a MoralNode id
    choices: list[Choice] = field(default_factory=list)


@dataclass
class ConsequenceStep:
    """One link in a multi-step consequence chain."""
    year: int
    description: str
    affected: list[str]
    sequence: SequenceType = SequenceType.NEUTRAL
    identity_revision: Optional[str] = None
    relationship_effects: list[str] = field(default_factory=list)
    psychological_effects: list[str] = field(default_factory=list)
    community_effects: list[str] = field(default_factory=list)


class MoralSimulator:
    """
    Deterministic, rule-based expansion of a choice into a multi-step
    consequence chain. No LLM required. The writer supplies the rules of
    their own world; the simulator only records and reflects.
    """

    def __init__(self, memory: GenerationalMemory | None = None) -> None:
        self.memory = memory or GenerationalMemory()

    def simulate(
        self,
        dilemma: Dilemma,
        choice: Choice,
        steps: Iterable[ConsequenceStep],
    ) -> list[ConsequenceStep]:
        materialized = list(steps)
        # Propagate sequence type along the chain if a step is neutral.
        for i, step in enumerate(materialized):
            if step.sequence is SequenceType.NEUTRAL and i > 0:
                step.sequence = materialized[i - 1].sequence
        return materialized

    def read_sequence(self, steps: list[ConsequenceStep]) -> SequenceType:
        """Classify the arc the writer has actually built, not the one intended."""
        if not steps:
            return SequenceType.NEUTRAL
        first, last = steps[0], steps[-1]
        opening_negative = any(
            k in first.description.lower() for k in ("loss", "wound", "fall", "secret", "shame")
        )
        closing_positive = any(
            k in last.description.lower() for k in ("restore", "repair", "give", "welcome", "free")
        )
        if opening_negative and closing_positive:
            return SequenceType.REDEMPTION
        if not opening_negative and not closing_positive:
            return SequenceType.CONTAMINATION
        return SequenceType.NEUTRAL

    def dialogical_disagreement(
        self, character: Character, choice: Choice
    ) -> list[tuple[DialogicalVoice, VoiceStance]]:
        """
        Surface which I-positions assent, dissent, or stay silent.
        The writer decides which voice wins; the engine only names the cost.
        """
        out: list[tuple[DialogicalVoice, VoiceStance]] = []
        for voice in character.narrative.voices:
            stance = voice.stance
            if choice.framework == "jesus_centered" and voice.speaks_for == "level_2_value":
                # A value-rooted voice resists a cost-bearing Jesus choice
                stance = VoiceStance.AMBIVALENT
            if "secret" in choice.description.lower() and "the family secret" in voice.stance_toward:
                stance = VoiceStance.DISSENTING
            out.append((voice, stance))
        return out


# ---------------------------------------------------------------------------
# Reflection passes: the mirror the writer looks into
# ---------------------------------------------------------------------------

@dataclass
class Reflection:
    questions: list[str]
    sequence: SequenceType
    identity_cost: dict[str, list[str]] = field(default_factory=dict)
    focalization_note: str = ""
    telling_ethics_note: str = ""


class Reflector:
    """Assemble the post-decision reflection. No verdicts, only questions."""

    @staticmethod
    def after_choice(
        character: Character,
        dilemma: Dilemma,
        choice: Choice,
        steps: list[ConsequenceStep],
        simulator: MoralSimulator,
        memory: GenerationalMemory,
        focalizer: str,
    ) -> Reflection:
        questions: list[str] = []
        sequence = simulator.read_sequence(steps)

        questions.append(
            f"If this decision is a scene in {character.name}'s life story, "
            f"what chapter does it belong to, and does the chapter title survive it?"
        )

        if sequence is SequenceType.REDEMPTION:
            questions.append(
                "Is the good at the end of this chain earned by what was paid, "
                "or asserted by what the writer wishes were true?"
            )
        elif sequence is SequenceType.CONTAMINATION:
            questions.append(
                "What good thing is being spoiled here, and who will name the spoiling first?"
            )
        else:
            questions.append(
                "This chain refuses a sequence so far. Is that refusal honest, or a delay?"
            )

        if choice.identity_revision:
            questions.append(
                f"Identity revision required: {choice.identity_revision}. "
                f"Which I-position inside {character.name} refuses it?"
            )

        if character.narrative.sacred_flaw:
            questions.append(
                f"The sacred flaw is '{character.narrative.sacred_flaw}'. "
                f"Does this choice feed it, starve it, or hide it?"
            )

        for step in steps:
            if step.identity_revision:
                questions.append(
                    f"{step.year}: identity revision — {step.identity_revision}. "
                    f"Who is erased by this revision, and who becomes possible?"
                )

        identity_cost = (
            memory.identity_cost_report(dilemma.inherited_from)
            if dilemma.inherited_from
            else {"protected": [], "erased": [], "possible": []}
        )

        focalization_note = (
            f"Focalizer: {focalizer}. "
            f"What the audience cannot see from here: "
            f"{choice.description or '[the choice itself]'}'s cost to those off-page."
        )

        telling_ethics_note = (
            "Telling ethics: if this scene is shown from this focalization, "
            "what moral understanding is cultivated, and what is foreclosed?"
        )

        return Reflection(
            questions=questions,
            sequence=sequence,
            identity_cost=identity_cost,
            focalization_note=focalization_note,
            telling_ethics_note=telling_ethics_note,
        )


# ---------------------------------------------------------------------------
# Demo
# ---------------------------------------------------------------------------

def _demo() -> None:
    # A character spanning 1965 -> 2026.
    ruth = Character(
        name="Ruth",
        traits=[
            Trait("conscientiousness", 0.8, "carries what others set down"),
            Trait("openness", 0.6, "willing to revise the story"),
        ],
        adaptations=[
            Adaptation("protect the family name", "value", 0.9, "1965 Montgomery"),
            Adaptation("tell the truth to the next generation", "goal", 0.7, "2026 Atlanta"),
        ],
        secrets=["a 1965 act of complicity never spoken aloud"],
        wounds=["a brother's silence after the march"],
        moral_boundaries=["never lie to a child about their own blood"],
        relationships={"Caleb (grandson)": "the one who asks"},
        narrative=NarrativeIdentity(
            chapters=[
                Chapter("The Street Before the March", "1964-1965",
                        dominant_sequence=SequenceType.NEUTRAL),
                Chapter("What Was Not Said", "1966-1990",
                        dominant_sequence=SequenceType.CONTAMINATION),
                Chapter("The Asking", "2020-2026",
                        dominant_sequence=SequenceType.NEUTRAL),
            ],
            voices=[
                DialogicalVoice("The Daughter of the Church",
                                "the family secret", VoiceStance.ASSENTING,
                                speaks_for="level_2_value"),
                DialogicalVoice("The One Who Was There",
                                "the family secret", VoiceStance.DISSENTING,
                                speaks_for="level_1_trait"),
                DialogicalVoice("The Grandmother",
                                "the family secret", VoiceStance.AMBIVALENT,
                                speaks_for="level_3_story"),
            ],
            master_narratives_inherited=["we do not air our wounds"],
            master_narratives_resisted=["the past is past"],
            sacred_flaw="if I speak it, I will lose the only family I have",
            inner_issue="a brother's silence she has never been allowed to grieve",
            ideological_setting="a church that taught endurance as virtue",
        ),
    )

    memory = GenerationalMemory()
    memory.add(MoralNode(
        node_id="1965_silence",
        year=1965,
        actor="Ruth",
        summary="Ruth stays silent about a neighbor's arrest.",
        sequence=SequenceType.CONTAMINATION,
        identity_cost="the neighbor's story is erased from the family's telling",
        identity_gain="Ruth keeps the family name intact",
    ))
    memory.add(MoralNode(
        node_id="1990_letter",
        year=1990,
        actor="Ruth",
        summary="Ruth burns a letter that would have named the neighbor.",
        sequence=SequenceType.CONTAMINATION,
        identity_cost="the letter's testimony is lost",
    ))
    memory.link("1965_silence", "1990_letter")
    memory.add(MoralNode(
        node_id="2026_question",
        year=2026,
        actor="Caleb",
        summary="Caleb asks Ruth what happened in 1965.",
        sequence=SequenceType.NEUTRAL,
    ))
    memory.link("1990_letter", "2026_question")

    dilemma = Dilemma(
        situation="Caleb asks Ruth what happened in 1965.",
        year=2026,
        characters_involved=["Ruth", "Caleb"],
        inherited_from="2026_question",
    )

    choice = Choice(
        label="Tell the truth, and lose the family's preferred story",
        framework="jesus_centered",
        description="Ruth speaks the neighbor's name and her own complicity.",
        identity_revision="Ruth becomes the one who breaks the silence, not the one who keeps it",
    )

    steps = [
        ConsequenceStep(
            year=2026,
            description="Ruth speaks; loss of the old family story begins.",
            affected=["Ruth", "Caleb"],
            sequence=SequenceType.REDEMPTION,
            relationship_effects=["Caleb's trust deepens; other relatives pull back"],
            psychological_effects=["Ruth grieves the brother she protected"],
            community_effects=["the church's endurance-as-virtue narrative is questioned"],
        ),
        ConsequenceStep(
            year=2027,
            description="Caleb carries the neighbor's name into a public record.",
            affected=["Caleb", "the neighbor's descendants"],
            sequence=SequenceType.REDEMPTION,
            identity_revision="Caleb becomes a keeper of another family's story",
            community_effects=["a repair neither family expected becomes possible"],
        ),
    ]

    simulator = MoralSimulator(memory)
    chain = simulator.simulate(dilemma, choice, steps)

    disagreement = simulator.dialogical_disagreement(ruth, choice)
    print("Dialogical disagreement:")
    for voice, stance in disagreement:
        print(f"  - {voice.name}: {stance.value}")

    reflection = Reflector.after_choice(
        character=ruth,
        dilemma=dilemma,
        choice=choice,
        steps=chain,
        simulator=simulator,
        memory=memory,
        focalizer="Caleb (grandson, 2026)",
    )

    print("\nReflection:")
    print(f"  Sequence read: {reflection.sequence.value}")
    for q in reflection.questions:
        print(f"  - {q}")
    print(f"\n  {reflection.focalization_note}")
    print(f"  {reflection.telling_ethics_note}")
    print("\n  Identity cost report:")
    for key, items in reflection.identity_cost.items():
        for item in items:
            print(f"    [{key}] {item}")


if __name__ == "__main__":
    _demo()
```

The module runs standalone (python3 muse_lifestory.py) and prints the dialogical disagreement, the reflection questions, the focalization note, and the inherited identity-cost report for the 1965 → 2026 demo chain.

A few structural choices worth flagging, since they carry the McAdams integration rather than just decorating it:

· Character holds all three levels explicitly. Traits (Level 1), adaptations (Level 2), and NarrativeIdentity (Level 3) are separate lists, so a decision can be checked against each level independently — a choice can be trait-consistent but story-violating, or vice versa.
· DialogicalVoice.stance_toward and speaks_for let the disagreement generator reason about which level of the person is dissenting. That is what makes the Jesus-centered pass honest: the engine can show that a Level 2 value is the one refusing the Level 3 revision, without ever scoring which is right.
· GenerationalMemory.identity_cost_report is the concrete payoff of McAdams' "psychosocial construction" claim — a 2026 dilemma can be traced back to every prior node whose telling protected or erased someone's story.
· Reflector.after_choice never produces a verdict. It produces questions, a sequence read, and two notes (focalization and telling ethics), matching the brief's "structured mirror" stance.
· MoralSimulator.read_sequence is deliberately keyword-based and crude — it is meant to be overridden by the writer's own rules, not to be clever. It exists so the engine can name the arc the writer actually built, which is often not the one intended.

If you want, the next increment is a consult prompt emitter that reads a Character and a Dilemma and returns the stage-appropriate focalization and identity-revision questions — a thin function on top of LifeStoryInterview and Reflector that keeps the same dependency-free shape.
