"""
muse_wizard.py
==============

A step-by-step Story Creation Wizard built on top of muse_lifestory.

It does not generate prose. It walks the writer through the structural and
psychological decisions the engine consumes: protagonist across three levels,
chapters and scenes, dialogical voices, inherited master narratives,
generational moral nodes, and a present dilemma with its choices and
consequences. The output is a completed WizardState, ready to be handed to
MoralSimulator and Reflector.

Two modes:
  * Interactive — `python3 muse_wizard.py --interactive`
  * Programmatic — build a WizardState directly and call StoryWizard(state).run()

The wizard is resumable: state carries a completed-steps log, and re-running
skips what is already done. Serialization to JSON uses the standard library
only.

Depends on: muse_lifestory.py (same directory).
"""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass, field, fields, is_dataclass
from enum import Enum
from typing import Callable, Optional

from muse_lifestory import (
    Character, Trait, Adaptation,
    Chapter, Scene, SceneType,
    DialogicalVoice, VoiceStance,
    SequenceType, ConsciousnessRegister,
    MoralNode, GenerationalMemory,
    Dilemma, Choice, ConsequenceStep,
    MoralSimulator, Reflector, Reflection,
)


# ---------------------------------------------------------------------------
# State
# ---------------------------------------------------------------------------

@dataclass
class WizardState:
    """Everything the wizard has gathered so far."""
    character: Character = field(default_factory=lambda: Character(name=""))
    nodes: list[MoralNode] = field(default_factory=list)
    links: list[tuple[str, str]] = field(default_factory=list)
    dilemma: Optional[Dilemma] = None
    chosen_choice: Optional[Choice] = None
    consequence_steps: list[ConsequenceStep] = field(default_factory=list)
    focalizer: str = ""
    reflection: Optional[Reflection] = None
    _completed_steps: list[str] = field(default_factory=list)

    def mark(self, step: str) -> None:
        if step not in self._completed_steps:
            self._completed_steps.append(step)

    def is_done(self, step: str) -> bool:
        return step in self._completed_steps

    def build_memory(self) -> GenerationalMemory:
        mem = GenerationalMemory()
        for node in self.nodes:
            mem.add(node)
        for parent, child in self.links:
            mem.link(parent, child)
        return mem

    def node_ids(self) -> set[str]:
        return {n.node_id for n in self.nodes}


# ---------------------------------------------------------------------------
# I/O abstraction
# ---------------------------------------------------------------------------

class WizardIO:
    """Protocol. Override for terminals, tests, or embedding."""
    def section(self, title: str) -> None: ...
    def tell(self, msg: str) -> None: ...

    def ask(self, prompt: str, default: str = "") -> str:
        return default

    def ask_int(self, prompt: str, default: int = 0,
                lo: int = 0, hi: int = 10) -> int:
        return default

    def ask_float(self, prompt: str, default: float = 0.0,
                  lo: float = -1.0, hi: float = 1.0) -> float:
        return default

    def ask_yes_no(self, prompt: str, default: bool = True) -> bool:
        return default

    def ask_choice(self, prompt: str, options: list[str],
                   default: int = 0) -> int:
        return default


class SilentIO(WizardIO):
    """Returns defaults only. Useful for programmatic and headless runs."""
    pass


class TerminalIO(WizardIO):
    """Line-based terminal I/O with validation and sensible defaults."""

    def section(self, title: str) -> None:
        print()
        print("─" * 60)
        print(f"  {title}")
        print("─" * 60)

    def tell(self, msg: str) -> None:
        print(msg)

    def ask(self, prompt: str, default: str = "") -> str:
        suffix = f" [{default}]" if default else ""
        raw = input(f"{prompt}{suffix}: ").strip()
        return raw or default

    def ask_int(self, prompt: str, default: int = 0,
                lo: int = 0, hi: int = 10) -> int:
        while True:
            raw = self.ask(prompt, str(default))
            try:
                val = int(raw)
                if lo <= val <= hi:
                    return val
            except ValueError:
                pass
            print(f"  (enter an integer between {lo} and {hi})")

    def ask_float(self, prompt: str, default: float = 0.0,
                  lo: float = -1.0, hi: float = 1.0) -> float:
        while True:
            raw = self.ask(prompt, str(default))
            try:
                val = float(raw)
                if lo <= val <= hi:
                    return val
            except ValueError:
                pass
            print(f"  (enter a number between {lo} and {hi})")

    def ask_yes_no(self, prompt: str, default: bool = True) -> bool:
        raw = self.ask(f"{prompt} (y/n)", "y" if default else "n").lower()
        return raw.startswith("y")

    def ask_choice(self, prompt: str, options: list[str],
                   default: int = 0) -> int:
        for i, opt in enumerate(options):
            print(f"  {i}) {opt}")
        while True:
            raw = self.ask(prompt, str(default))
            try:
                idx = int(raw)
                if 0 <= idx < len(options):
                    return idx
            except ValueError:
                pass
            print(f"  (enter a number between 0 and {len(options) - 1})")


class ScriptedIO(WizardIO):
    """
    Returns canned answers in order, falling back to defaults when exhausted.
    Useful for tests and reproducibility. Pass "__DEFAULT__" to accept the
    prompt's own default explicitly.
    """

    def __init__(self, answers: list[str], echo: bool = False) -> None:
        self.answers = list(answers)
        self.pos = 0
        self.echo = echo

    def _next(self, default: str) -> str:
        if self.pos >= len(self.answers):
            return default
        val = self.answers[self.pos]
        self.pos += 1
        return default if val == "__DEFAULT__" else val

    def section(self, title: str) -> None:
        if self.echo:
            print(f"\n=== {title} ===")

    def tell(self, msg: str) -> None:
        if self.echo:
            print(msg)

    def ask(self, prompt: str, default: str = "") -> str:
        val = self._next(default)
        if self.echo:
            print(f"{prompt} [{default}]: {val}")
        return val

    def ask_int(self, prompt: str, default: int = 0,
                lo: int = 0, hi: int = 10) -> int:
        val = self._next(str(default))
        try:
            n = int(val)
            if lo <= n <= hi:
                return n
        except ValueError:
            pass
        return default

    def ask_float(self, prompt: str, default: float = 0.0,
                  lo: float = -1.0, hi: float = 1.0) -> float:
        val = self._next(str(default))
        try:
            f = float(val)
            if lo <= f <= hi:
                return f
        except ValueError:
            pass
        return default

    def ask_yes_no(self, prompt: str, default: bool = True) -> bool:
        val = self._next("y" if default else "n")
        return val.lower().startswith("y")

    def ask_choice(self, prompt: str, options: list[str],
                   default: int = 0) -> int:
        val = self._next(str(default))
        try:
            n = int(val)
            if 0 <= n < len(options):
                return n
        except ValueError:
            pass
        return default


# ---------------------------------------------------------------------------
# Wizard steps
# ---------------------------------------------------------------------------

ADAPTATION_KINDS = ["goal", "value", "motive", "strategy", "loyalty"]
FRAMEWORKS = [
    "consequentialist", "deontological", "virtue",
    "care", "jesus_centered", "narrative_ethics",
]
SCENE_TYPE_NAMES = [s.value for s in SceneType]
SEQUENCE_NAMES = [s.value for s in SequenceType]
STANCE_NAMES = [s.value for s in VoiceStance]


def step_protagonist(state: WizardState, io: WizardIO) -> None:
    io.section("1. Protagonist")
    io.tell("Who is this story about? A name is enough to begin.")
    state.character.name = io.ask("Name", state.character.name or "unnamed")
    state.mark("protagonist")


def step_traits(state: WizardState, io: WizardIO) -> None:
    io.section("2. Level 1 — Dispositional traits")
    io.tell("Broad tendencies. Big Five territory. Two to five is plenty.")
    while True:
        name = io.ask("Trait name (blank to stop)", "")
        if not name:
            break
        intensity = io.ask_float(f"  Intensity of '{name}'", 0.5, 0.0, 1.0)
        note = io.ask("  Note (optional)", "")
        state.character.traits.append(Trait(name, intensity, note))
    state.mark("traits")


def step_adaptations(state: WizardState, io: WizardIO) -> None:
    io.section("3. Level 2 — Characteristic adaptations")
    io.tell("Situated goals, values, motives, strategies, loyalties.")
    while True:
        name = io.ask("Name (blank to stop)", "")
        if not name:
            break
        kind = ADAPTATION_KINDS[io.ask_choice("  Kind", ADAPTATION_KINDS, 1)]
        weight = io.ask_float(f"  Weight of '{name}'", 0.7, 0.0, 1.0)
        context = io.ask("  Context (era / place)", "")
        state.character.adaptations.append(Adaptation(name, kind, weight, context))
    state.mark("adaptations")


def step_flaw_and_wound(state: WizardState, io: WizardIO) -> None:
    io.section("4. Sacred flaw, inner issue, wounds, secrets")
    io.tell("Cron: the sacred flaw is the lie the character believes "
            "to protect the wound.")
    n = state.character.narrative
    n.sacred_flaw = io.ask("Sacred flaw", n.sacred_flaw)
    n.inner_issue = io.ask("Inner issue (the wound the flaw protects)",
                           n.inner_issue)

    io.tell("Wounds — charged injuries the story keeps returning to.")
    while True:
        w = io.ask("Wound (blank to stop)", "")
        if not w:
            break
        state.character.wounds.append(w)

    io.tell("Secrets — what is carried but not spoken.")
    while True:
        s = io.ask("Secret (blank to stop)", "")
        if not s:
            break
        state.character.secrets.append(s)

    state.mark("flaw_and_wound")


def step_boundaries(state: WizardState, io: WizardIO) -> None:
    io.section("5. Moral boundaries and relationships")
    io.tell("Boundaries — lines the character will not cross.")
    while True:
        b = io.ask("Boundary (blank to stop)", "")
        if not b:
            break
        state.character.moral_boundaries.append(b)

    io.tell("Relationships — who matters, and how.")
    while True:
        who = io.ask("Person (blank to stop)", "")
        if not who:
            break
        bond = io.ask(f"  Bond with {who}", "")
        state.character.relationships[who] = bond
    state.mark("boundaries")


def step_chapters(state: WizardState, io: WizardIO) -> None:
    io.section("6. Life-story chapters")
    io.tell("Picture the life as a book. Two to seven chapters. "
            "Title each in the character's own idiom.")
    n = state.character.narrative
    while True:
        title = io.ask("Chapter title (blank to stop)", "")
        if not title:
            break
        era = io.ask("  Era (e.g. 1964-1965)", "")
        n.chapters.append(Chapter(title=title, era=era))
    state.mark("chapters")


def step_scenes(state: WizardState, io: WizardIO) -> None:
    io.section("7. Defining scenes")
    io.tell("For each chapter, add at least the high point, low point, "
            "or turning point.")
    for chapter in state.character.narrative.chapters:
        io.tell(f"\nChapter: {chapter.title} ({chapter.era})")
        while True:
            label = io.ask("  Scene label (blank to move on)", "")
            if not label:
                break
            stype = SceneType(
                SCENE_TYPE_NAMES[io.ask_choice("  Scene type", SCENE_TYPE_NAMES, 0)]
            )
            setting = io.ask("  Setting", "")
            affect = io.ask_float("  Affect (-1 to 1)", 0.0, -1.0, 1.0)
            seq = SequenceType(
                SEQUENCE_NAMES[io.ask_choice("  Sequence", SEQUENCE_NAMES, 2)]
            )
            filtered = io.ask("  What is filtered out by this POV", "")
            unnamed = io.ask("  What cannot yet be named", "")
            chapter.scenes.append(Scene(
                label=label,
                scene_type=stype,
                setting=setting,
                affect=affect,
                sequence=seq,
                consciousness=ConsciousnessRegister.NARRATED_MONOLOGUE,
                what_is_filtered_out=filtered,
                what_cannot_yet_be_named=unnamed,
            ))
    state.mark("scenes")


def step_voices(state: WizardState, io: WizardIO) -> None:
    io.section("8. Dialogical voices")
    io.tell("Hermans: identity is negotiated among I-positions. "
            "Three or four is typical.")
    n = state.character.narrative
    while True:
        name = io.ask("Voice name (blank to stop)", "")
        if not name:
            break
        toward = io.ask("  Speaks toward (e.g. 'the family secret')", "")
        stance = VoiceStance(
            STANCE_NAMES[io.ask_choice("  Stance", STANCE_NAMES, 2)]
        )
        speaks_for = io.ask(
            "  Speaks for (level_1_trait / level_2_value / level_3_story)",
            "",
        )
        n.voices.append(DialogicalVoice(name, toward, stance, speaks_for))
    state.mark("voices")


def step_master_narratives(state: WizardState, io: WizardIO) -> None:
    io.section("9. Master narratives")
    io.tell("What stories about this family, this people, this place "
            "does the character inherit? Which do they resist?")
    n = state.character.narrative
    while True:
        m = io.ask("Inherited master narrative (blank to stop)", "")
        if not m:
            break
        n.master_narratives_inherited.append(m)
    while True:
        m = io.ask("Resisted master narrative (blank to stop)", "")
        if not m:
            break
        n.master_narratives_resisted.append(m)
    n.ideological_setting = io.ask("Ideological setting", n.ideological_setting)
    state.mark("master_narratives")


def step_moral_nodes(state: WizardState, io: WizardIO) -> None:
    io.section("10. Generational moral nodes")
    io.tell("Past decisions across generations. Each can parent a future "
            "dilemma. Add at least one to anchor the present.")
    while True:
        node_id = io.ask("Node id (blank to stop)", "")
        if not node_id:
            break
        year = io.ask_int("  Year", 1965, 1800, 2200)
        actor = io.ask("  Actor", state.character.name)
        summary = io.ask("  Summary", "")
        seq = SequenceType(
            SEQUENCE_NAMES[io.ask_choice("  Sequence", SEQUENCE_NAMES, 1)]
        )
        cost = io.ask("  Identity cost (whose story is erased)", "")
        gain = io.ask("  Identity gain (what becomes possible)", "")
        state.nodes.append(MoralNode(node_id, year, actor, summary, seq, cost, gain))

    if len(state.nodes) > 1:
        io.tell("Link nodes: parent → child. Blank parent to stop.")
        while True:
            p = io.ask("  Parent node id (blank to stop)", "")
            if not p or p not in state.node_ids():
                break
            c = io.ask("  Child node id", "")
            if c in state.node_ids():
                state.links.append((p, c))
    state.mark("moral_nodes")


def step_dilemma(state: WizardState, io: WizardIO) -> None:
    io.section("11. Present dilemma")
    situation = io.ask("Situation", "")
    year = io.ask_int("Year", 2026, 1800, 2200)
    involved = io.ask("Characters involved (comma-separated)",
                      state.character.name)
    inherited = io.ask("Inherited from node id (blank for none)", "")
    if inherited and inherited not in state.node_ids():
        io.tell(f"  (no node named '{inherited}' — inheriting from nothing)")
        inherited = ""
    state.dilemma = Dilemma(
        situation=situation,
        year=year,
        characters_involved=[s.strip() for s in involved.split(",") if s.strip()],
        inherited_from=inherited or None,
    )
    state.mark("dilemma")


def step_choices(state: WizardState, io: WizardIO) -> None:
    io.section("12. Choices")
    io.tell("Enumerate the choices available. The wizard will then ask "
            "which one the character takes.")
    if state.dilemma is None:
        io.tell("(no dilemma set — skipping)")
        state.mark("choices")
        return
    while True:
        label = io.ask("Choice label (blank to stop)", "")
        if not label:
            break
        framework = FRAMEWORKS[io.ask_choice("  Framework", FRAMEWORKS, 0)]
        description = io.ask("  Description", label)
        revision = io.ask("  Identity revision required (blank for none)", "")
        state.dilemma.choices.append(
            Choice(label, framework, description,
                   identity_revision=revision)
        )
    if state.dilemma.choices:
        idx = io.ask_choice(
            "Which choice does the character take?",
            [c.label for c in state.dilemma.choices],
            0,
        )
        state.chosen_choice = state.dilemma.choices[idx]
    state.mark("choices")


def step_consequences(state: WizardState, io: WizardIO) -> None:
    io.section("13. Consequence chain")
    io.tell("Walk the chosen choice forward. Each step is a year and a change.")
    if state.dilemma is None or state.chosen_choice is None:
        io.tell("(no choice set — skipping)")
        state.mark("consequences")
        return
    while True:
        desc = io.ask("Step description (blank to stop)", "")
        if not desc:
            break
        year = io.ask_int("  Year", state.dilemma.year, 1800, 2300)
        affected = io.ask("  Affected (comma-separated)", "")
        seq = SequenceType(
            SEQUENCE_NAMES[io.ask_choice("  Sequence", SEQUENCE_NAMES, 2)]
        )
        revision = io.ask("  Identity revision (blank for none)", "")
        state.consequence_steps.append(ConsequenceStep(
            year=year,
            description=desc,
            affected=[s.strip() for s in affected.split(",") if s.strip()],
            sequence=seq,
            identity_revision=revision or None,
        ))
    state.focalizer = io.ask("Focalizer for the reflection",
                             state.character.name)
    state.mark("consequences")


def step_finalize(state: WizardState, io: WizardIO) -> None:
    io.section("14. Reflection")
    if state.dilemma is None or state.chosen_choice is None:
        io.tell("(no dilemma — blueprint saved without reflection)")
        state.mark("finalize")
        return
    memory = state.build_memory()
    sim = MoralSimulator(memory)
    chain = sim.simulate(state.dilemma, state.chosen_choice,
                         state.consequence_steps)
    reflection = Reflector.after_choice(
        character=state.character,
        dilemma=state.dilemma,
        choice=state.chosen_choice,
        steps=chain,
        simulator=sim,
        memory=memory,
        focalizer=state.focalizer or state.character.name,
    )
    io.tell(f"Sequence read: {reflection.sequence.value}")
    io.tell("")
    io.tell("Questions the engine is holding:")
    for q in reflection.questions:
        io.tell(f"  • {q}")
    io.tell("")
    io.tell(reflection.focalization_note)
    io.tell(reflection.telling_ethics_note)
    if any(reflection.identity_cost.values()):
        io.tell("")
        io.tell("Identity cost report:")
        for key, items in reflection.identity_cost.items():
            for item in items:
                io.tell(f"  [{key}] {item}")
    state.reflection = reflection
    state.mark("finalize")


STEPS: list[tuple[str, Callable[[WizardState, WizardIO], None]]] = [
    ("protagonist", step_protagonist),
    ("traits", step_traits),
    ("adaptations", step_adaptations),
    ("flaw_and_wound", step_flaw_and_wound),
    ("boundaries", step_boundaries),
    ("chapters", step_chapters),
    ("scenes", step_scenes),
    ("voices", step_voices),
    ("master_narratives", step_master_narratives),
    ("moral_nodes", step_moral_nodes),
    ("dilemma", step_dilemma),
    ("choices", step_choices),
    ("consequences", step_consequences),
    ("finalize", step_finalize),
]


# ---------------------------------------------------------------------------
# The wizard
# ---------------------------------------------------------------------------

class StoryWizard:
    """
    Walks a writer through the structural decisions the engine consumes.
    Holds no state of its own beyond a reference to WizardState and an IO.
    """

    def __init__(self, state: Optional[WizardState] = None,
                 io: Optional[WizardIO] = None) -> None:
        self.state = state or WizardState()
        self.io = io or TerminalIO()

    def run(self, skip_completed: bool = True) -> WizardState:
        for name, fn in STEPS:
            if skip_completed and self.state.is_done(name):
                continue
            fn(self.state, self.io)
        return self.state

    # -- serialization ------------------------------------------------------

    def to_dict(self) -> dict:
        return _jsonable({
            "character": self.state.character,
            "nodes": self.state.nodes,
            "links": self.state.links,
            "dilemma": self.state.dilemma,
            "chosen_choice": self.state.chosen_choice,
            "consequence_steps": self.state.consequence_steps,
            "focalizer": self.state.focalizer,
            "completed_steps": list(self.state._completed_steps),
        })

    def save(self, path: str) -> None:
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(self.to_dict(), fh, indent=2, ensure_ascii=False)

    def summary(self) -> str:
        s = self.state
        lines = [
            f"Protagonist: {s.character.name}",
            f"  traits: {len(s.character.traits)}  "
            f"adaptations: {len(s.character.adaptations)}  "
            f"chapters: {len(s.character.narrative.chapters)}  "
            f"voices: {len(s.character.narrative.voices)}",
            f"  sacred flaw: {s.character.narrative.sacred_flaw or '—'}",
            f"  inner issue: {s.character.narrative.inner_issue or '—'}",
            f"Generational nodes: {len(s.nodes)}  links: {len(s.links)}",
            f"Dilemma: {s.dilemma.situation if s.dilemma else '—'}",
            f"Choice: {s.chosen_choice.label if s.chosen_choice else '—'}",
            f"Consequence steps: {len(s.consequence_steps)}",
            f"Focalizer: {s.focalizer or '—'}",
            f"Sequence read: "
            f"{s.reflection.sequence.value if s.reflection else '—'}",
        ]
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# JSON helpers (stdlib only)
# ---------------------------------------------------------------------------

def _jsonable(obj):
    if isinstance(obj, Enum):
        return obj.value
    if is_dataclass(obj) and not isinstance(obj, type):
        return {f.name: _jsonable(getattr(obj, f.name)) for f in fields(obj)}
    if isinstance(obj, dict):
        return {k: _jsonable(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_jsonable(x) for x in obj]
    return obj


# ---------------------------------------------------------------------------
# Demo
# ---------------------------------------------------------------------------

def _demo_programmatic() -> WizardState:
    """
    Build a WizardState directly, then hand it to StoryWizard with SilentIO.
    Because all the data is already present, the wizard's loops have nothing
    left to ask and simply finalize.
    """
    state = WizardState()

    # Protagonist
    state.character.name = "Ruth"

    state.character.traits = [
        Trait("conscientiousness", 0.8, "carries what others set down"),
        Trait("openness", 0.6, "willing to revise the story"),
    ]

    state.character.adaptations = [
        Adaptation("protect the family name", "value", 0.9, "1965 Montgomery"),
        Adaptation("tell the truth to the next generation", "goal", 0.7,
                   "2026 Atlanta"),
    ]

    n = state.character.narrative
    n.sacred_flaw = "if I speak it, I will lose the only family I have"
    n.inner_issue = "a brother's silence she has never been allowed to grieve"
    n.master_narratives_inherited = ["we do not air our wounds"]
    n.master_narratives_resisted = ["the past is past"]
    n.ideological_setting = "a church that taught endurance as virtue"

    state.character.wounds = ["a brother's silence after the march"]
    state.character.secrets = ["a 1965 act of complicity never spoken aloud"]
    state.character.moral_boundaries = [
        "never lie to a child about their own blood",
    ]
    state.character.relationships = {
        "Caleb (grandson)": "the one who asks",
    }

    n.chapters = [
        Chapter("The Street Before the March", "1964-1965",
                dominant_sequence=SequenceType.NEUTRAL),
        Chapter("What Was Not Said", "1966-1990",
                dominant_sequence=SequenceType.CONTAMINATION),
        Chapter("The Asking", "2020-2026",
                dominant_sequence=SequenceType.NEUTRAL),
    ]

    n.voices = [
        DialogicalVoice("The Daughter of the Church",
                        "the family secret", VoiceStance.ASSENTING,
                        speaks_for="level_2_value"),
        DialogicalVoice("The One Who Was There",
                        "the family secret", VoiceStance.DISSENTING,
                        speaks_for="level_1_trait"),
        DialogicalVoice("The Grandmother",
                        "the family secret", VoiceStance.AMBIVALENT,
                        speaks_for="level_3_story"),
    ]

    state.nodes = [
        MoralNode(
            "1965_silence", 1965, "Ruth",
            "Ruth stays silent about a neighbor's arrest.",
            SequenceType.CONTAMINATION,
            identity_cost="the neighbor's story is erased from the family's telling",
            identity_gain="Ruth keeps the family name intact",
        ),
    ]

    state.dilemma = Dilemma(
        situation="Caleb asks Ruth what happened in 1965.",
        year=2026,
        characters_involved=["Ruth", "Caleb"],
        inherited_from="1965_silence",
    )
    state.dilemma.choices = [
        Choice(
            label="Tell the truth, and lose the family's preferred story",
            framework="jesus_centered",
            description="Ruth speaks the neighbor's name and her own complicity.",
            identity_revision="Ruth becomes the one who breaks the silence, "
                              "not the one who keeps it",
        ),
        Choice(
            label="Keep the silence",
            framework="care",
            description="Ruth protects the family by not answering.",
            identity_revision="Ruth remains the keeper of the family story",
        ),
    ]
    state.chosen_choice = state.dilemma.choices[0]

    state.consequence_steps = [
        ConsequenceStep(
            year=2026,
            description="Ruth speaks; loss of the old family story begins.",
            affected=["Ruth", "Caleb"],
            sequence=SequenceType.REDEMPTION,
            identity_revision="Ruth grieves the brother she protected",
            relationship_effects=["Caleb's trust deepens; some relatives pull back"],
        ),
        ConsequenceStep(
            year=2027,
            description="Caleb carries the neighbor's name into a public record.",
            affected=["Caleb", "the neighbor's descendants"],
            sequence=SequenceType.REDEMPTION,
            identity_revision="Caleb becomes a keeper of another family's story",
        ),
    ]

    state.focalizer = "Caleb (grandson, 2026)"

    return StoryWizard(state, SilentIO()).run()


def main(argv: list[str]) -> int:
    if "--interactive" in argv:
        wizard = StoryWizard(io=TerminalIO())
        state = wizard.run()
        print()
        print("─" * 60)
        print("  Summary")
        print("─" * 60)
        print(wizard.summary())
        return 0

    # Default: programmatic demo
    state = _demo_programmatic()
    wizard = StoryWizard(state, SilentIO())
    print(wizard.summary())
    print()
    print("JSON export preview (truncated):")
    payload = json.dumps(wizard.to_dict(), indent=2, ensure_ascii=False)
    print(payload[:600] + ("\n  ..." if len(payload) > 600 else ""))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
