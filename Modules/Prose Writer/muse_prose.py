```python
"""
muse_prose.py
=============

An HBO-level prose writing agent for the Muse engine.

This module sits *downstream* of muse_lifestory and muse_wizard. The moral
simulation has already run. The reflection has already been assembled. The
identity costs have already been named. This module is a drafter, not an
author. It offers one possible scene. The writer is free to refuse it.

What "HBO level" means here, concretely:

  1.  Nobody says what they mean. Every line of dialogue carries a subtext
      the speaker will not name and may not know.
  2.  The scene knows more than any character in it.
  3.  Power is negotiated in gesture: who pours, who sits, who waits, who
      leaves, who touches what, who refuses to look up.
  4.  Physical specificity is the ground of feeling. Name the objects, the
      weather, the body. No abstractions standing in for sensations.
  5.  Diction is character-specific. The way Ruth talks is not the way
      Caleb talks is not the way the narrator talks.
  6.  Silence does work. A pause, a refusal to answer, a look off-frame
      carries what dialogue cannot.
  7.  The exit is not the entrance. Something has turned.
  8.  No easy catharsis. The wound stays open unless the story has earned
      its closing.
  9.  No narrator judgment. The prose does not tell the reader what to feel.
  10. Register collision is allowed and often necessary: class, region,
      era, profession live in the language.

The module provides:

  * SceneBrief — a compact contract for what the scene must do.
  * Beat — a single unit of scene movement, with subtext attached.
  * ProseBackend — protocol for anything that can turn a brief into prose.
  * DeterministicBackend — assembles a scene *skeleton*, not polished prose.
    Honest about being scaffolding. Useful as a starting frame.
  * PromptAssembler — builds a rich system + user prompt for any LLM
    backend, encoding all ten heuristics above.
  * CraftCheck — a post-hoc critique pass. Never a score. Only questions.
  * ProseWriter — orchestrator.

Standard library only. No network calls. No LLM dependency. The LLM, if
you want one, is a ProseBackend you supply.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict, is_dataclass, fields
from enum import Enum
from typing import Optional, Protocol

# These imports are optional: if muse_lifestory is on the path, the module
# can consume its types directly. If not, the dataclasses below stand alone.
try:
    from muse_lifestory import (
        Character, Dilemma, Choice, Reflection,
        Scene as LifeScene, SceneType, SequenceType,
        ConsciousnessRegister,
    )
    from muse_wizard import WizardState
except ImportError:  # pragma: no cover
    Character = Dilemma = Choice = Reflection = object  # type: ignore
    LifeScene = SceneType = SequenceType = ConsciousnessRegister = object  # type: ignore
    WizardState = object  # type: ignore


# ---------------------------------------------------------------------------
# Scene brief
# ---------------------------------------------------------------------------

class BeatKind(Enum):
    ACTION = "action"          # a body does something in a room
    DIALOGUE = "dialogue"      # spoken lines, with subtext
    INTERIORITY = "interiority"  # what the POV notices and refuses to notice
    SILENCE = "silence"        # a pause that is content
    OBJECT = "object"          # a physical thing doing emotional work
    TURN = "turn"              # the pivot: something has changed


@dataclass
class Beat:
    """
    A single unit of scene movement.

    The `content` field is what is *shown*. The `subtext` field is what is
    *happening beneath it* — the thing no character will say aloud. The
    `register` field names the diction this beat should live in.
    """
    kind: BeatKind
    content: str
    subtext: str = ""
    register: str = ""          # e.g. "working-class Montgomery, 1965"
    speaker: str = ""           # for DIALOGUE beats
    physical: str = ""          # a specific object, gesture, or body detail


@dataclass
class SceneBrief:
    """
    The contract between Muse and the prose writer.

    A SceneBrief is not a summary. It is the structural spine the scene must
    embody, plus the constraints under which it must be written. It is
    deliberately sparse: the actual prose is where the writing happens.
    """
    # Focalization
    pov: str                              # whose eyes we are in
    pov_register: str = ""                # how that POV sounds on the page
    consciousness: str = "narrated_monologue"

    # Setting
    era: str = ""
    place: str = ""
    time_of_day: str = ""
    weather: str = ""

    # Personnel
    characters_present: list[str] = field(default_factory=list)
    offstage_presences: list[str] = field(default_factory=list)  # who is not here but present

    # Dramatic engine
    what_pov_wants: str = ""
    what_pov_hides: str = ""
    what_others_want: dict[str, str] = field(default_factory=dict)
    what_others_hide: dict[str, str] = field(default_factory=dict)
    inherited_node: str = ""              # a MoralNode id, if this scene carries one
    sequence: str = "neutral"             # redemption / contamination / neutral

    # The turn
    entrance_state: str = ""              # how the scene begins emotionally
    exit_state: str = ""                  # how it ends — must differ
    the_turn: str = ""                    # what changes

    # Palette (from Muse's symbolic layer)
    colors: list[str] = field(default_factory=list)
    lights: list[str] = field(default_factory=list)
    objects: list[str] = field(default_factory=list)
    symbols: list[str] = field(default_factory=list)

    # Constraints
    forbidden_moves: list[str] = field(default_factory=list)
    required_moves: list[str] = field(default_factory=list)

    # The skeleton
    beats: list[Beat] = field(default_factory=list)

    def is_ready(self) -> tuple[bool, list[str]]:
        missing: list[str] = []
        if not self.pov:
            missing.append("pov")
        if not self.the_turn:
            missing.append("the_turn")
        if not self.entrance_state or not self.exit_state:
            missing.append("entrance_state/exit_state")
        if self.entrance_state and self.exit_state and self.entrance_state == self.exit_state:
            missing.append("exit_state must differ from entrance_state")
        if not self.beats:
            missing.append("beats")
        return (not missing, missing)


# ---------------------------------------------------------------------------
# Backends
# ---------------------------------------------------------------------------

class ProseBackend(Protocol):
    """Anything that can turn a SceneBrief into a scene."""
    def render(self, brief: SceneBrief) -> str: ...


class DeterministicBackend:
    """
    Assembles a scene *skeleton* from the brief. Not polished prose. The
    skeleton names each beat, its subtext, and its physical anchor, so a
    writer or an LLM can fill it without inventing structure.

    This is deliberately not a prose generator. Stdlib-only prose at HBO
    quality is not a thing. The value of this backend is that it makes the
    brief legible as a scene.
    """

    def __init__(self, indent: str = "    ") -> None:
        self.indent = indent

    def render(self, brief: SceneBrief) -> str:
        ready, missing = brief.is_ready()
        if not ready:
            return (
                "[scene brief is not ready]\n"
                + "\n".join(f"  - missing: {m}" for m in missing)
            )

        out: list[str] = []
        out.append(self._header(brief))
        out.append("")
        for i, beat in enumerate(brief.beats, 1):
            out.append(self._beat(i, beat))
            out.append("")
        out.append(self._footer(brief))
        return "\n".join(out)

    def _header(self, b: SceneBrief) -> str:
        lines = [
            f"[SCENE — {b.era} {b.place}, {b.time_of_day}]",
            f"POV: {b.pov} ({b.consciousness})",
        ]
        if b.pov_register:
            lines.append(f"     register: {b.pov_register}")
        if b.weather:
            lines.append(f"weather: {b.weather}")
        if b.characters_present:
            lines.append(f"present: {', '.join(b.characters_present)}")
        if b.offstage_presences:
            lines.append(f"offstage: {', '.join(b.offstage_presences)}")
        lines.append("")
        lines.append(
            f"wants: {b.what_pov_wants or '—'}   "
            f"hides: {b.what_pov_hides or '—'}"
        )
        lines.append(f"entrance: {b.entrance_state}   exit: {b.exit_state}")
        if b.the_turn:
            lines.append(f"turn: {b.the_turn}")
        return "\n".join(lines)

    def _beat(self, n: int, beat: Beat) -> str:
        tag = beat.kind.value.upper()
        head = f"{n:02d} [{tag}]"
        if beat.speaker:
            head += f" {beat.speaker}"
        lines = [head]
        lines.append(f"{self.indent}show: {beat.content}")
        if beat.physical:
            lines.append(f"{self.indent}body: {beat.physical}")
        if beat.subtext:
            lines.append(f"{self.indent}under: {beat.subtext}")
        if beat.register:
            lines.append(f"{self.indent}register: {beat.register}")
        return "\n".join(lines)

    def _footer(self, b: SceneBrief) -> str:
        lines = [f"[sequence read: {b.sequence}]"]
        if b.symbols or b.colors or b.objects:
            palette = []
            if b.colors:
                palette.append(f"colors={b.colors}")
            if b.lights:
                palette.append(f"lights={b.lights}")
            if b.objects:
                palette.append(f"objects={b.objects}")
            if b.symbols:
                palette.append(f"symbols={b.symbols}")
            lines.append("palette: " + "; ".join(palette))
        if b.required_moves:
            lines.append("required: " + ", ".join(b.required_moves))
        if b.forbidden_moves:
            lines.append("forbidden: " + ", ".join(b.forbidden_moves))
        return "\n".join(lines)


class CallableBackend:
    """
    Wraps any callable that takes a SceneBrief and returns a string. Use
    this to wire in an LLM client without subclassing anything.
    """
    def __init__(self, fn) -> None:
        self._fn = fn

    def render(self, brief: SceneBrief) -> str:
        return self._fn(brief)


# ---------------------------------------------------------------------------
# Prompt assembler
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """\
You are drafting a scene in the register of the best HBO dramatic writing —
The Sopranos, The Wire, Deadwood, Six Feet Under, Chernobyl, Succession,
The Leftovers, The Night Of. You are not writing a treatment, a synopsis,
or a beat sheet. You are writing the scene itself.

The rules of this register:

1. Nobody says what they mean. Every line of dialogue carries a subtext the
   speaker will not name and may not fully know. If a line can be paraphrased
   without loss, cut it.

2. The scene knows more than any character in it. The reader should be able
   to feel the gap between what a character understands and what is true.

3. Power is negotiated in gesture. Who pours the drink. Who sits first. Who
   waits to be asked. Who touches the doorframe on the way out. Who refuses
   to look up. Track these; they are the scene's real dialogue.

4. Physical specificity is the ground of feeling. Name the objects, the
   weather, the body. A specific sensation is worth a page of abstraction.
   No "she felt a wave of grief" — instead: what her hands did, what she
   looked at, what she refused to look at.

5. Diction is character-specific. The way each character talks must be the
   way that character would actually talk — shaped by class, region, era,
   profession, education, and what they are hiding. The narrator has a
   register too, and it is not the same as any character's.

6. Silence does work. A pause, a refusal to answer, a look off-frame, a
   sentence left unfinished, a physical action taken instead of a reply —
   these carry what dialogue cannot.

7. The exit is not the entrance. By the end of the scene, something has
   turned. The characters are not in the same configuration they began in,
   even if nothing "happened."

8. No easy catharsis. Do not resolve the wound. Do not let the characters
   say the thing they have been circling unless the story has earned it. The
   scene is allowed to end in the middle of the thing.

9. No narrator judgment. Do not tell the reader what to feel. Do not use
   adverbs to carry what the action should. Do not editorialize.

10. Register collision is allowed. A churchwoman and a teenager can share
    a room and use different Englishes. A 1965 memory can interrupt a 2026
    kitchen. Do not smooth these collisions out; they are the texture.

Style constraints:
- Third person limited, focalized through the POV named in the brief.
- No scene headings, no camera directions, no stage business in brackets.
- No summary. No telling. Show.
- Length: as long as the scene needs. Trust the reader.

You will receive a scene brief. Produce the scene. Nothing else. No preamble,
no notes, no explanation."""


@dataclass
class AssembledPrompt:
    system: str
    user: str

    def as_messages(self) -> list[dict]:
        return [
            {"role": "system", "content": self.system},
            {"role": "user", "content": self.user},
        ]


class PromptAssembler:
    """
    Builds a system + user prompt for any chat-completions-style LLM. The
    system prompt encodes the ten HBO heuristics. The user prompt carries
    the SceneBrief as structured data, plus any craft notes the writer has
    attached via the brief's required/forbidden moves.
    """

    def __init__(self, system: str = SYSTEM_PROMPT) -> None:
        self.system = system

    def assemble(self, brief: SceneBrief) -> AssembledPrompt:
        ready, missing = brief.is_ready()
        if not ready:
            raise ValueError(
                "SceneBrief is not ready to render. Missing: " + ", ".join(missing)
            )
        return AssembledPrompt(system=self.system, user=self._user_message(brief))

    def _user_message(self, b: SceneBrief) -> str:
        parts: list[str] = []
        parts.append("SCENE BRIEF")
        parts.append("")

        parts.append("FOCALIZATION")
        parts.append(f"  POV: {b.pov}")
        if b.pov_register:
            parts.append(f"  POV register: {b.pov_register}")
        parts.append(f"  Consciousness: {b.consciousness}")
        parts.append("")

        parts.append("SETTING")
        parts.append(f"  Era: {b.era}")
        parts.append(f"  Place: {b.place}")
        if b.time_of_day:
            parts.append(f"  Time: {b.time_of_day}")
        if b.weather:
            parts.append(f"  Weather: {b.weather}")
        parts.append("")

        parts.append("PERSONNEL")
        parts.append(f"  Present: {', '.join(b.characters_present) or '—'}")
        if b.offstage_presences:
            parts.append(f"  Offstage but present: {', '.join(b.offstage_presences)}")
        parts.append("")

        parts.append("DRAMATIC ENGINE")
        parts.append(f"  What {b.pov} wants: {b.what_pov_wants or '—'}")
        parts.append(f"  What {b.pov} hides: {b.what_pov_hides or '—'}")
        for name, want in b.what_others_want.items():
            parts.append(f"  What {name} wants: {want}")
        for name, hide in b.what_others_hide.items():
            parts.append(f"  What {name} hides: {hide}")
        if b.inherited_node:
            parts.append(f"  Inherited moral node: {b.inherited_node}")
        parts.append(f"  Sequence: {b.sequence}")
        parts.append("")

        parts.append("THE TURN")
        parts.append(f"  Entrance state: {b.entrance_state}")
        parts.append(f"  Exit state:     {b.exit_state}")
        parts.append(f"  What turns:     {b.the_turn}")
        parts.append("")

        if any([b.colors, b.lights, b.objects, b.symbols]):
            parts.append("SYMBOLIC PALETTE (use sparingly; these are provocations, not requirements)")
            if b.colors:
                parts.append(f"  Colors: {', '.join(b.colors)}")
            if b.lights:
                parts.append(f"  Lights: {', '.join(b.lights)}")
            if b.objects:
                parts.append(f"  Objects: {', '.join(b.objects)}")
            if b.symbols:
                parts.append(f"  Symbols: {', '.join(b.symbols)}")
            parts.append("")

        if b.required_moves:
            parts.append("REQUIRED MOVES")
            for m in b.required_moves:
                parts.append(f"  - {m}")
            parts.append("")

        if b.forbidden_moves:
            parts.append("FORBIDDEN MOVES")
            for m in b.forbidden_moves:
                parts.append(f"  - {m}")
            parts.append("")

        if b.beats:
            parts.append("SCENE SKELETON (structural spine — feel free to add, reorder, or cut, but do not flatten)")
            for i, beat in enumerate(b.beats, 1):
                line = f"  {i:02d}. [{beat.kind.value}]"
                if beat.speaker:
                    line += f" {beat.speaker}"
                line += f": {beat.content}"
                parts.append(line)
                if beat.physical:
                    parts.append(f"      body: {beat.physical}")
                if beat.subtext:
                    parts.append(f"      under: {beat.subtext}")
                if beat.register:
                    parts.append(f"      register: {beat.register}")
            parts.append("")

        parts.append("Write the scene.")
        return "\n".join(parts)


# ---------------------------------------------------------------------------
# Craft check
# ---------------------------------------------------------------------------

CRAFT_QUESTIONS: tuple[tuple[str, str], ...] = (
    ("Subtext",
     "Does any character say the thing they actually mean? If so, is that "
     "earned, or is it a failure of nerve?"),
    ("Asymmetry",
     "Does the scene know more than any character in it? Can the reader "
     "feel the gap?"),
    ("Gesture",
     "Is power negotiated in bodies and objects, or only in speech? Name "
     "three gestures the scene turns on."),
    ("Specificity",
     "Is there a physical detail here that could only belong to this "
     "character in this room? Or could this scene happen anywhere?"),
    ("Register",
     "Does each character sound like themselves, and does the narrator "
     "sound like no one in the room?"),
    ("Silence",
     "Where does the scene pause? What is not said, and is that silence "
     "doing work or just resting?"),
    ("Turn",
     "What has changed between the entrance and the exit? If nothing, why "
     "is this a scene and not a beat?"),
    ("Catharsis",
     "Has the wound been resolved too cleanly? Is the story earning its "
     "closing, or insisting on it?"),
    ("Judgment",
     "Does the prose tell the reader what to feel anywhere? Circle every "
     "adverb carrying emotional weight."),
    ("Collision",
     "Are there registers colliding in this scene — class, era, region, "
     "profession? If not, could there be?"),
)


class CraftCheck:
    """
    Post-render critique. Never a score. Only questions the writer can
    answer or refuse. The engine's stance holds: it is a mirror, not a
    judge.
    """

    def __init__(self, questions: tuple[tuple[str, str], ...] = CRAFT_QUESTIONS) -> None:
        self.questions = questions

    def pass_on(self, prose: str, brief: SceneBrief) -> list[tuple[str, str]]:
        """Returns (category, question) pairs. No verdicts, no scores."""
        return list(self.questions)

    def render(self, prose: str, brief: SceneBrief) -> str:
        lines = ["CRAFT PASS — questions, not verdicts", ""]
        for cat, q in self.pass_on(prose, brief):
            lines.append(f"  {cat}: {q}")
        lines.append("")
        lines.append(
            "  Note: none of the above implies the scene is wrong. The "
            "engine does not score. Answer, override, or ignore."
        )
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# Prose writer
# ---------------------------------------------------------------------------

class ProseWriter:
    """
    Orchestrator. Consumes a completed WizardState (or a Character + Dilemma
    + Choice + Reflection tuple) plus a SceneBrief skeleton, calls a
    ProseBackend, and returns a scene plus a craft pass.

    The writer is not obligated to accept the scene. The engine is a
    drafter. The writer is the author.
    """

    def __init__(
        self,
        backend: Optional[ProseBackend] = None,
        craft: Optional[CraftCheck] = None,
    ) -> None:
        self.backend: ProseBackend = backend or DeterministicBackend()
        self.craft = craft or CraftCheck()

    def write(self, brief: SceneBrief) -> "WrittenScene":
        ready, missing = brief.is_ready()
        if not ready:
            raise ValueError(
                "SceneBrief is not ready. Missing: " + ", ".join(missing)
            )
        prose = self.backend.render(brief)
        pass_notes = self.craft.pass_on(prose, brief)
        return WrittenScene(brief=brief, prose=prose, craft_notes=pass_notes)

    # -- brief builders -----------------------------------------------------

    @staticmethod
    def brief_from_wizard(
        state: "WizardState",
        era: str,
        place: str,
        time_of_day: str = "",
        weather: str = "",
        offstage: Optional[list[str]] = None,
    ) -> SceneBrief:
        """
        Assemble a starting SceneBrief from a WizardState. The writer fills
        in beats, palette, and forbidden moves by hand; the wizard state
        supplies the character, the inherited node, and the sequence.
        """
        ch = state.character
        n = ch.narrative
        pov = state.focalizer or ch.name
        inherited = state.dilemma.inherited_from if state.dilemma else ""

        brief = SceneBrief(
            pov=pov,
            pov_register=n.ideological_setting,
            era=era,
            place=place,
            time_of_day=time_of_day,
            weather=weather,
            characters_present=list(state.dilemma.characters_involved) if state.dilemma else [],
            offstage_presences=list(offstage or []),
            what_pov_wants=n.chapters[-1].title if n.chapters else "",
            what_pov_hides=ch.secrets[0] if ch.secrets else "",
            inherited_node=inherited or "",
            sequence=(
                state.reflection.sequence.value
                if state.reflection
                else SequenceType.NEUTRAL.value
            ),
            entrance_state="",
            exit_state="",
            the_turn="",
            symbols=[],
        )

        # Populate others' wants/hides from adaptations and secrets.
        for name in brief.characters_present:
            if name == ch.name:
                continue
            brief.what_others_want[name] = "—"
            brief.what_others_hide[name] = "—"

        return brief


@dataclass
class WrittenScene:
    brief: SceneBrief
    prose: str
    craft_notes: list[tuple[str, str]]

    def to_dict(self) -> dict:
        return {
            "brief": _jsonable(self.brief),
            "prose": self.prose,
            "craft_notes": [
                {"category": c, "question": q} for c, q in self.craft_notes
            ],
        }

    def craft_pass_text(self, check: Optional[CraftCheck] = None) -> str:
        check = check or CraftCheck()
        return check.render(self.prose, self.brief)


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

def _demo() -> None:
    """
    A 2026 kitchen scene. Caleb asks Ruth what happened in 1965. The brief
    is built by hand, rendered as a skeleton by the deterministic backend,
    then handed to the PromptAssembler so the reader can see the full
    prompt an LLM would receive.
    """

    brief = SceneBrief(
        pov="Caleb",
        pov_register="Atlanta, 2026, quiet, precise, willing to look",
        consciousness="narrated_monologue",
        era="2026",
        place="Ruth's kitchen, Atlanta",
        time_of_day="late afternoon",
        weather="rain holding off",
        characters_present=["Ruth", "Caleb"],
        offstage_presences=["Ruth's brother (dead, 1990)"],
        what_pov_wants="the true story of 1965",
        what_pov_hides="that he has already read the neighbor's name in a courthouse record",
        what_others_want={"Ruth": "for the afternoon to end without the question being asked"},
        what_others_hide={"Ruth": "that she burned a letter in 1990"},
        inherited_node="1965_silence",
        sequence="contamination",
        entrance_state="Caleb has come to ask; Ruth has come to be asked",
        exit_state="Ruth has answered; Caleb now carries what she carried",
        the_turn="Ruth speaks the neighbor's name, and the kitchen becomes a different room",
        colors=["amber", "gray"],
        lights=["late sun through rain-glass"],
        objects=["a chipped enamel bowl", "a letter-sized rectangle on the counter where no letter is"],
        symbols=["the unspoken name as a third presence at the table"],
        required_moves=["Ruth must not look at Caleb when she speaks the name"],
        forbidden_moves=[
            "No tears from Ruth on the page.",
            "No narrator telling the reader what the moment means.",
            "No dialogue in which either character states their subtext aloud.",
        ],
        beats=[
            Beat(
                kind=BeatKind.OBJECT,
                content="A chipped enamel bowl on the counter, half-filled with water, going nowhere.",
                subtext="Something has been soaking here for days and no one has moved it.",
                physical="Ruth's hands, dry, at her sides.",
            ),
            Beat(
                kind=BeatKind.DIALOGUE,
                speaker="Caleb",
                content="\"Grandma. I found something.\"",
                subtext="He is asking permission to have already looked.",
                register="Atlanta, 2026 — careful, upward, and trying not to be.",
            ),
            Beat(
                kind=BeatKind.SILENCE,
                content="Ruth does not answer. She moves the bowl an inch to the left.",
                subtext="The bowl is the answer she is not giving.",
            ),
            Beat(
                kind=BeatKind.DIALOGUE,
                speaker="Ruth",
                content="\"Sit down, then.\"",
                subtext="She has decided. She has not decided what to say.",
                register="Montgomery that never left her mouth, 1965.",
            ),
            Beat(
                kind=BeatKind.INTERIORITY,
                content="Caleb notices he has not taken his shoes off. He does not take them off. He notices this.",
                subtext="He is already leaving.",
            ),
            Beat(
                kind=BeatKind.OBJECT,
                content="A rectangle of light on the counter where the sun has found the rain-glass. Ruth's hand moves across it and the light bends.",
                subtext="Something is being handled that has no shape yet.",
                physical="The back of Ruth's hand, a vein standing up.",
            ),
            Beat(
                kind=BeatKind.DIALOGUE,
                speaker="Caleb",
                content="\"His name was Ellis. Ellis Parrish.\"",
                subtext="He has already said it. He cannot unsay it. He is watching her to see if she will.",
                register="The register of a man who has read a record and wishes he hadn't.",
            ),
            Beat(
                kind=BeatKind.SILENCE,
                content="Ruth does not turn. Two seconds. Four. The refrigerator hums.",
                subtext="She is deciding whether to be the woman she has been for sixty years or someone else.",
            ),
            Beat(
                kind=BeatKind.TURN,
                content="Ruth speaks the name. She does not look at Caleb while she does.",
                subtext="She has handed him the thing she has carried. He does not yet know he is carrying it.",
                register="Flat. No adverb. The name, and then the room, which is now a different room.",
            ),
        ],
    )

    writer = ProseWriter()  # deterministic backend by default
    written = writer.write(brief)

    print("=" * 72)
    print("SCENE SKELETON (deterministic backend)")
    print("=" * 72)
    print(written.prose)

    print()
    print("=" * 72)
    print("CRAFT PASS")
    print("=" * 72)
    print(written.craft_pass_text())

    print()
    print("=" * 72)
    print("PROMPT FOR AN LLM BACKEND (system + user)")
    print("=" * 72)
    assembled = PromptAssembler().assemble(brief)
    print("--- SYSTEM ---")
    print(assembled.system)
    print()
    print("--- USER ---")
    print(assembled.user)


if __name__ == "__main__":
    _demo()
```

A few structural decisions worth flagging, because they carry the HBO integration rather than just dressing it:

The SceneBrief separates structure from prose. It carries the focalization, the wants and hides, the entrance/exit asymmetry, the turn, the palette, and the beat skeleton — but no prose. This is the contract. It is also why the deterministic backend can render an honest skeleton instead of pretending to write. The brief is the artifact; the prose is a downstream, replaceable rendering.

Every Beat has a subtext and a physical field. These are the two fields that make the skeleton feel like HBO rather than like a beat sheet. A beat without subtext is a beat the scene doesn't need. A beat without a physical anchor is a beat that could happen anywhere.

SystemPrompt encodes the ten heuristics as numbered rules. This is where the "HBO level" actually lives. It is not an adjective — it is an explicit set of constraints the LLM must satisfy. Anyone can read the prompt and see exactly what the module means by "HBO level." Anyone can edit the prompt without touching code.

CraftCheck returns questions, never scores. This is the same stance as Reflector.after_choice in muse_lifestory. The engine does not judge. It asks the writer the questions they may not have asked. The ten questions are the ten heuristics turned back on the writer's own prose.

The deterministic backend does not generate prose. It assembles the skeleton. This is honest: stdlib-only prose at HBO quality is not a thing, and pretending otherwise would be a lie about what the module does. The skeleton is useful — a writer can read it as a scene map, and an LLM can read it as a spine.

ProseWriter.brief_from_wizard bridges the layers. Given a completed WizardState, it produces a starting brief that the writer fills in. It pulls the POV from focalizer, the register from ideological_setting, the hidden thing from secrets, the inherited node from dilemma.inherited_from, and the sequence from reflection.sequence. The writer supplies the era, the place, the weather, the beats, the palette, and the forbidden moves — because those are the writer's decisions, not the engine's.

CallableBackend and the ProseBackend protocol mean the LLM is a wiring choice, not a hard dependency. The module runs entirely offline. When you want HBO-level prose, you wire in an LLM that receives the assembled prompt. When you don't, the skeleton is still useful.

The natural next increments are a SceneBrief builder that walks the writer through beat construction in the same style as muse_wizard (so the brief itself becomes guided), and a from_dict() loader so a saved WrittenScene can be reloaded and re-critiqued against a different CraftCheck. Say the word if you want either.
