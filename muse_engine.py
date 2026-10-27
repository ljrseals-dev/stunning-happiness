Muse Engine

A symbolic exploration chatbot for writers.

Named for the practice, not the person. Built for Tina. Inspired by the writers who work with a symbolic sub-layer while drafting.

The tool takes a writer's decisions and prompts them to explore those decisions through a symbolic lens — colors, lights, thoughts, and recurring images — while tracking where the story sits in the pyramid of narrative structure. First climax. Fall. Second climax. Resolution.

One file. Standard library only.

---

muse_engine.py

```python
#!/usr/bin/env python3
"""
muse_engine.py

A symbolic exploration chatbot for writers.

The writer makes decisions. The engine prompts the writer to explore
those decisions through a symbolic lens — colors, lights, thoughts,
symbols — while tracking the story's position in the narrative pyramid.

The pyramid has two climaxes and a fall:
    Ordinary World -> Inciting Incident -> Rising Action
    -> First Climax -> The Fall -> Dark Night
    -> Second Climax -> Falling Action -> Resolution

One file. Standard library only.

Usage:
    python3 muse_engine.py init --dir ./my_story --title "Working Title"
    python3 muse_engine.py decide "Maya opens the door and finds her brother"
    python3 muse_engine.py consult
    python3 muse_engine.py suggest
    python3 muse_engine.py advance
    python3 muse_engine.py status
    python3 muse_engine.py export
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import textwrap
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional


# ---------------------------------------------------------------------------
# The symbolic palette.
# ---------------------------------------------------------------------------

COLORS = {
    "black":   "void, potential, the unformed, night, death before rebirth",
    "white":   "purity, revelation, clarity, the blank page, the shroud",
    "red":     "passion, violence, blood, life force, sacrifice, warning",
    "orange":  "creativity, warmth, sunset, the threshold between states",
    "yellow":  "intellect, illumination, gold, the sun, betrayal, sickness",
    "green":   "growth, envy, nature, rebirth, the heart's slow work",
    "blue":    "truth, melancholy, the sea, distance, the unspoken",
    "indigo":  "intuition, the third eye, dreams, the veil thinning",
    "violet":  "spirit, royalty, transformation, the crown, the last threshold",
    "silver":  "reflection, the moon, the subconscious, what mirrors reveal",
    "gold":    "achievement, the sun, the divine, the prize, the false prize",
    "grey":    "ambiguity, boredom, the in-between, the not-yet-chosen",
    "brown":   "earth, decay, the body, the inherited, the unexamined",
}

LIGHTS = {
    "candlelight":  "intimacy, fragility, hope against the dark, the small flame",
    "firelight":    "passion, danger, the ancient, the circle gathered close",
    "neon":         "artificiality, modern alienation, the false promise, the city",
    "dawn":         "beginning, hope, revelation, the thing that could not wait",
    "dusk":         "ending, transition, loss, the thing that will not return",
    "midnight":     "the peak of darkness, despair, the hidden truth, the mirror",
    "starlight":    "guidance, distant hope, the cold, the indifferent cosmos",
    "moonlight":    "mystery, the feminine, the unconscious, the tide",
    "fluorescent":  "sterility, the institution, the modern, the exposed",
    "sunlight":     "truth, exposure, the unbearable, the gift",
    "shadow":       "the unacknowledged, the repressed, the shape without a source",
    "total dark":   "oblivion, surrender, the erasure, the rest before the rise",
}

THOUGHTS = {
    "doubt":     "the crack in the belief",
    "resolve":   "the will hardening into action",
    "grief":     "the weight that does not lift",
    "ecstasy":   "the moment of union, brief and dangerous",
    "fear":      "the body's anticipation of harm",
    "wonder":    "the mind opening past its edges",
    "shame":     "the self turning against itself",
    "longing":   "the reach toward what is not here",
    "clarity":   "the sudden removal of fog",
    "confusion": "the honest state of not knowing",
    "rage":      "the energy that burns its container",
    "peace":     "the stillness that is earned or stolen",
    "guilt":     "the debt that cannot be paid",
    "hope":      "the wager on a better outcome",
}

SYMBOLS = {
    "door":     "threshold, choice, the irreversible step",
    "mirror":   "identity, reflection, the double, the truth that looks back",
    "water":    "emotion, the unconscious, cleansing, drowning",
    "fire":     "transformation, destruction, purification, the trial",
    "bridge":   "transition, the span between states, the risk of crossing",
    "bird":     "freedom, the soul, the message, the thing that leaves",
    "serpent":  "knowledge, temptation, healing, the coiled threat",
    "crown":    "authority, the price of rule, the false or true sovereign",
    "mask":     "the performed self, the hidden face, the social contract",
    "key":      "access, the answer, the thing that opens or locks",
    "wound":    "the injury that shapes the self, the unhealed, the proof",
    "garden":   "innocence, cultivation, the enclosed world, the fall",
    "road":     "the journey, the choice of direction, the leaving",
    "house":    "the self, the family, the inherited structure, the shelter",
    "storm":    "upheaval, the forces beyond control, the clearing",
    "crown":    "sovereignty, the burden of the head that wears it",
    "book":     "the record, the inherited knowledge, the thing that can be burned",
    "clock":    "time, mortality, the mechanical, the thing that cannot be stopped",
    "child":    "the future, the vulnerable, the self before the wound",
    "animal":   "the instinctual, the untamed, the honest body",
    "threshold": "the place between, the moment before, the crossing",
}


# ---------------------------------------------------------------------------
# The narrative pyramid.
# ---------------------------------------------------------------------------

@dataclass
class Stage:
    key: str
    name: str
    position: int
    ask: list[str]
    warns: list[str]
    suggests: list[str]


PYRAMID = [
    Stage(
        key="ordinary_world",
        name="The Ordinary World",
        position=0,
        ask=[
            "What does the protagonist believe about themselves that is not true?",
            "What color is the room they are in, and what does that color say about their comfort?",
            "What light is present? Is it natural or made?",
            "What small ritual do they perform that they would not notice?",
            "What is the thing they would never say out loud?",
        ],
        warns=[
            "If the ordinary world is too pleasant, the fall will not land.",
            "If the ordinary world is too bleak, the reader will not want to stay.",
            "If nothing is wrong here, nothing can go wrong later.",
        ],
        suggests=[
            "Give the ordinary world one small flaw the protagonist has learned to live with.",
            "Let a color recur here that will return at the second climax.",
            "Let the light source be the one they will lose.",
        ],
    ),
    Stage(
        key="inciting_incident",
        name="The Inciting Incident",
        position=1,
        ask=[
            "What breaks the pattern?",
            "What enters that was not invited?",
            "What color does the world turn when the change arrives?",
            "What does the protagonist do first, before thinking?",
            "What do they choose not to see?",
        ],
        warns=[
            "If the inciting incident is too large, the rest of the story has nowhere to rise.",
            "If it is too small, the reader will not believe the protagonist's response.",
            "If the protagonist could walk away and does not, the reason must be on the page.",
        ],
        suggests=[
            "Let the inciting incident arrive through a door — literal or figurative.",
            "Give the protagonist one moment of refusal before they accept.",
            "Let a light change when the incident lands.",
        ],
    ),
    Stage(
        key="rising_action",
        name="The Rising Action",
        position=2,
        ask=[
            "What is being tested?",
            "What does the protagonist want, and what do they need?",
            "What symbol keeps recurring, and what does it want?",
            "What is the cost of each step forward?",
            "Who is the ally, and who is the obstacle, and are they the same person?",
        ],
        warns=[
            "If the rising action does not escalate, it is not rising.",
            "If the protagonist is not changed by the middle, the ending will feel unearned.",
            "If the antagonist is weaker than the protagonist, the climax will be flat.",
        ],
        suggests=[
            "Let each chapter change the protagonist's relationship to a recurring symbol.",
            "Let one ally become an obstacle, and one obstacle become an ally.",
            "Let the light grow dimmer as the action rises.",
        ],
    ),
    Stage(
        key="first_climax",
        name="The First Climax (The False Victory)",
        position=3,
        ask=[
            "What has the protagonist won?",
            "What do they believe they have learned?",
            "What color is the room when they think they have won?",
            "What did they not notice?",
            "Who is watching, and what do they know that the protagonist does not?",
        ],
        warns=[
            "If the first climax is as large as the second, the second will feel redundant.",
            "If the protagonist is genuinely satisfied here, the fall will feel arbitrary.",
            "If the victory is total, there is no fall to write.",
        ],
        suggests=[
            "Let the protagonist be honest about what they have won and what they have not.",
            "Let one detail be wrong in the victory scene — a wrong color, a wrong light.",
            "Let the false victory be a real victory in miniature.",
        ],
    ),
    Stage(
        key="the_fall",
        name="The Fall",
        position=4,
        ask=[
            "What is lost?",
            "What color is the loss?",
            "What light is present, if any?",
            "What does the protagonist do with their hands?",
            "Who do they turn to, and who turns away?",
        ],
        warns=[
            "If the fall is caused by an outside force alone, the story is melodrama.",
            "If the fall is caused by the protagonist's flaw alone, the story is a moral lesson.",
            "If the fall is immediate, the reader will not feel it.",
        ],
        suggests=[
            "Let the fall take a full scene, or two.",
            "Let the protagonist be alone for part of it and not alone for the rest.",
            "Let a color from the ordinary world return here, corrupted.",
        ],
    ),
    Stage(
        key="dark_night",
        name="The Dark Night",
        position=5,
        ask=[
            "What is the protagonist's deepest belief about themselves?",
            "What is the light source, and is it enough?",
            "What is the one thing they cannot lose and are afraid they will?",
            "What is the small act they perform that keeps them alive?",
            "What is the question they cannot answer?",
        ],
        warns=[
            "If the dark night is too short, the second climax will feel unearned.",
            "If the dark night is too long, the reader will abandon the story.",
            "If the protagonist does not change here, the second climax is not theirs to win.",
        ],
        suggests=[
            "Let the dark night be a single long scene, not a montage.",
            "Let the protagonist find one small light and tend it.",
            "Let a symbol from the inciting incident return, changed.",
        ],
    ),
    Stage(
        key="second_climax",
        name="The Second Climax (The True Climax)",
        position=6,
        ask=[
            "What is the true sacrifice?",
            "What symbol resolves?",
            "What color is the final room?",
            "What light is present, and who carries it?",
            "What does the protagonist do that they could not do at the first climax?",
        ],
        warns=[
            "If the second climax is the same kind of action as the first, it is not a second climax.",
            "If the protagonist is saved from outside, they did not win.",
            "If the sacrifice is not real, the climax is not real.",
        ],
        suggests=[
            "Let the protagonist choose the harder thing, not the easier thing.",
            "Let the recurring symbol return one last time and be transformed.",
            "Let the light be earned, not given.",
        ],
    ),
    Stage(
        key="falling_action",
        name="The Falling Action",
        position=7,
        ask=[
            "What is the cost of the victory?",
            "Who is missing from the room?",
            "What is the new ordinary?",
            "What color is the world now?",
            "What does the protagonist do with their hands?",
        ],
        warns=[
            "If the falling action is too long, the story loses its momentum.",
            "If the falling action is too short, the reader feels cheated of the aftermath.",
            "If nothing has changed, the climax was not a climax.",
        ],
        suggests=[
            "Let one small thing be different than it was in the ordinary world.",
            "Let one small thing be the same.",
            "Let a light from the ordinary world return, changed by what it illuminates.",
        ],
    ),
    Stage(
        key="resolution",
        name="The Resolution",
        position=8,
        ask=[
            "What has changed?",
            "What is the final image?",
            "What color is the last thing the reader sees?",
            "What light is present, and what does it reveal?",
            "What is the last thing the protagonist thinks?",
        ],
        warns=[
            "If the resolution explains what the story meant, it is a lecture.",
            "If the resolution adds new information, it is a sequel.",
            "If the resolution is only happy, it is a lie.",
            "If the resolution is only sad, it is a punishment.",
        ],
        suggests=[
            "Let the final image echo the first image, changed.",
            "Let the last line be short.",
            "Let the final light be the one the story earned.",
        ],
    ),
]


# ---------------------------------------------------------------------------
# Data model.
# ---------------------------------------------------------------------------

@dataclass
class Decision:
    text: str
    position: str
    symbols: list
    colors: list
    lights: list
    thoughts: list
    timestamp: str = ""

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now(timezone.utc).isoformat(timespec="seconds")


@dataclass
class StoryState:
    title: str = "Working Title"
    position: int = 0
    decisions: list = field(default_factory=list)
    active_colors: list = field(default_factory=list)
    active_lights: list = field(default_factory=list)
    active_symbols: list = field(default_factory=list)
    active_thoughts: list = field(default_factory=list)

    def to_json(self) -> str:
        return json.dumps(
            {
                "title": self.title,
                "position": self.position,
                "decisions": [asdict(d) for d in self.decisions],
                "active_colors": self.active_colors,
                "active_lights": self.active_lights,
                "active_symbols": self.active_symbols,
                "active_thoughts": self.active_thoughts,
            },
            indent=2,
        )

    @classmethod
    def from_json(cls, raw: str) -> "StoryState":
        data = json.loads(raw)
        state = cls(
            title=data.get("title", "Working Title"),
            position=data.get("position", 0),
            active_colors=data.get("active_colors", []),
            active_lights=data.get("active_lights", []),
            active_symbols=data.get("active_symbols", []),
            active_thoughts=data.get("active_thoughts", []),
        )
        state.decisions = [Decision(**d) for d in data.get("decisions", [])]
        return state


# ---------------------------------------------------------------------------
# Symbol extraction. Deterministic. No LLM.
# ---------------------------------------------------------------------------

def extract_symbols(text: str) -> dict:
    """Find any palette symbols referenced in the writer's decision text."""
    lower = text.lower()
    found = {
        "colors":   [c for c in COLORS   if re.search(rf"\b{re.escape(c)}\b", lower)],
        "lights":   [l for l in LIGHTS   if re.search(rf"\b{re.escape(l)}\b", lower)],
        "symbols":  [s for s in SYMBOLS  if re.search(rf"\b{re.escape(s)}\b", lower)],
        "thoughts": [t for t in THOUGHTS if re.search(rf"\b{re.escape(t)}\b", lower)],
    }
    return found


# ---------------------------------------------------------------------------
# The engine.
# ---------------------------------------------------------------------------

class MuseEngine:
    STATE_FILE = "story.json"

    def __init__(self, project_dir: Path):
        self.dir = Path(project_dir).resolve()
        self.state_path = self.dir / self.STATE_FILE
        self.state = self._load()

    def _load(self) -> StoryState:
        if self.state_path.exists():
            return StoryState.from_json(self.state_path.read_text(encoding="utf-8"))
        return StoryState()

    def _save(self) -> None:
        self.dir.mkdir(parents=True, exist_ok=True)
        self.state_path.write_text(self.state.to_json(), encoding="utf-8")

    # ---- init ----

    def init(self, title: str) -> None:
        self.state = StoryState(title=title)
        self._save()

    # ---- decide ----

    def decide(self, text: str) -> str:
        stage = PYRAMID[self.state.position]
        found = extract_symbols(text)

        decision = Decision(
            text=text,
            position=stage.key,
            symbols=found["symbols"],
            colors=found["colors"],
            lights=found["lights"],
            thoughts=found["thoughts"],
        )
        self.state.decisions.append(decision)

        # Update active palette (deduplicated, capped at 5 each).
        for key, store in (
            ("colors", "active_colors"),
            ("lights", "active_lights"),
            ("symbols", "active_symbols"),
            ("thoughts", "active_thoughts"),
        ):
            current = getattr(self.state, store)
            for v in found[key]:
                if v not in current:
                    current.append(v)
            setattr(self.state, store, current[-5:])

        self._save()
        return self._render_decision(stage, decision)

    def _render_decision(self, stage: Stage, decision: Decision) -> str:
        lines = []
        lines.append(f"# Decision recorded at: {stage.name}")
        lines.append("")
        lines.append(f"> {decision.text}")
        lines.append("")
        if any([decision.colors, decision.lights,
                decision.symbols, decision.thoughts]):
            lines.append("## Symbols present")
            lines.append("")
            if decision.colors:
                lines.append(f"- **Colors:** {', '.join(decision.colors)}")
                for c in decision.colors:
                    lines.append(f"  - {c}: {COLORS[c]}")
            if decision.lights:
                lines.append(f"- **Lights:** {', '.join(decision.lights)}")
                for l in decision.lights:
                    lines.append(f"  - {l}: {LIGHTS[l]}")
            if decision.symbols:
                lines.append(f"- **Symbols:** {', '.join(decision.symbols)}")
                for s in decision.symbols:
                    lines.append(f"  - {s}: {SYMBOLS[s]}")
            if decision.thoughts:
                lines.append(f"- **Thoughts:** {', '.join(decision.thoughts)}")
                for t in decision.thoughts:
                    lines.append(f"  - {t}: {THOUGHTS[t]}")
        else:
            lines.append("_No palette symbols detected in this decision._")
            lines.append("")
            lines.append("Consider: what color is the room? what light is")
            lines.append("present? what does the character believe right now?")
        return "\n".join(lines)

    # ---- consult ----

    def consult(self) -> str:
        stage = PYRAMID[self.state.position]
        lines = [f"# Consult: {stage.name}", ""]
        lines.append("## Questions to explore")
        lines.append("")
        for q in stage.ask:
            lines.append(f"- {q}")
        lines.append("")
        lines.append("## Warnings for this stage")
        lines.append("")
        for w in stage.warns:
            lines.append(f"- {w}")
        lines.append("")
        if self.state.decisions:
            last = self.state.decisions[-1]
            lines.append("## Based on your last decision")
            lines.append("")
            lines.append(f"> {last.text}")
            lines.append("")
            lines.append(self._reactive_prompt(last, stage))
        return "\n".join(lines)

    def _reactive_prompt(self, decision: Decision, stage: Stage) -> str:
        """A specific prompt based on what the writer decided."""
        parts = []
        if decision.colors:
            c = decision.colors[0]
            parts.append(
                f"You named the color **{c}**. {COLORS[c].capitalize()}. "
                f"Where else in the story will {c} appear? What will it mean then?"
            )
        if decision.lights:
            l = decision.lights[0]
            parts.append(
                f"You named the light **{l}**. {LIGHTS[l].capitalize()}. "
                f"Is this light rising or falling in the scene? Who controls it?"
            )
        if decision.symbols:
            s = decision.symbols[0]
            parts.append(
                f"You named the symbol **{s}**. {SYMBOLS[s].capitalize()}. "
                f"Where has this symbol appeared before? Where will it appear next?"
            )
        if decision.thoughts:
            t = decision.thoughts[0]
            parts.append(
                f"You named the thought **{t}**. {THOUGHTS[t].capitalize()}. "
                f"Is this thought the protagonist's own, or inherited from someone else?"
            )
        if not parts:
            parts.append(
                "You did not name a color, a light, a symbol, or a thought. "
                "That is not a problem — but the story may be running on plot alone. "
                "Consider: what is the character seeing, and what does it mean to them?"
            )
        return "\n\n".join(parts)

    # ---- suggest ----

    def suggest(self) -> str:
        stage = PYRAMID[self.state.position]
        lines = [f"# Suggestions for: {stage.name}", ""]
        for s in stage.suggests:
            lines.append(f"- {s}")
        lines.append("")
        lines.append("## Palette extensions")
        lines.append("")
        lines.append("Colors not yet used:")
        used = set(self.state.active_colors)
        for c in COLORS:
            if c not in used:
                lines.append(f"- {c}: {COLORS[c]}")
        lines.append("")
        lines.append("Lights not yet used:")
        used = set(self.state.active_lights)
        for l in LIGHTS:
            if l not in used:
                lines.append(f"- {l}: {LIGHTS[l]}")
        return "\n".join(lines)

    # ---- advance ----

    def advance(self) -> str:
        if self.state.position >= len(PYRAMID) - 1:
            return "You are at the final stage. The story is at its resolution."
        self.state.position += 1
        self._save()
        stage = PYRAMID[self.state.position]
        return f"Advanced to: {stage.name}\n\nUse `consult` to explore this stage."

    def retreat(self) -> str:
        if self.state.position <= 0:
            return "You are at the first stage."
        self.state.position -= 1
        self._save()
        stage = PYRAMID[self.state.position]
        return f"Returned to: {stage.name}"

    # ---- status ----

    def status(self) -> str:
        stage = PYRAMID[self.state.position]
        lines = [f"# {self.state.title}"]
        lines.append("")
        lines.append(f"Position: {stage.position + 1} of {len(PYRAMID)} — **{stage.name}**")
        lines.append(f"Decisions recorded: {len(self.state.decisions)}")
        lines.append("")
        if self.state.active_colors:
            lines.append(f"Active colors: {', '.join(self.state.active_colors)}")
        if self.state.active_lights:
            lines.append(f"Active lights: {', '.join(self.state.active_lights)}")
        if self.state.active_symbols:
            lines.append(f"Active symbols: {', '.join(self.state.active_symbols)}")
        if self.state.active_thoughts:
            lines.append(f"Active thoughts: {', '.join(self.state.active_thoughts)}")
        lines.append("")
        lines.append("## Pyramid")
        for i, s in enumerate(PYRAMID):
            marker = " <-- you are here" if i == self.state.position else ""
            lines.append(f"  {i + 1}. {s.name}{marker}")
        return "\n".join(lines)

    # ---- export ----

    def export(self, out_path: Path) -> Path:
        lines = [f"# {self.state.title}", ""]
        lines.append(f"_A symbolic record of {len(self.state.decisions)} decisions._")
        lines.append("")
        for i, d in enumerate(self.state.decisions, start=1):
            stage = next((s for s in PYRAMID if s.key == d.position), PYRAMID[0])
            lines.append(f"## Decision {i}: {stage.name}")
            lines.append("")
            lines.append(f"> {d.text}")
            lines.append("")
            if d.colors:
                lines.append(f"- Colors: {', '.join(d.colors)}")
            if d.lights:
                lines.append(f"- Lights: {', '.join(d.lights)}")
            if d.symbols:
                lines.append(f"- Symbols: {', '.join(d.symbols)}")
            if d.thoughts:
                lines.append(f"- Thoughts: {', '.join(d.thoughts)}")
            lines.append("")
            lines.append(f"_{d.timestamp}_")
            lines.append("")
        lines.append("---")
        lines.append("")
        lines.append("## Active palette")
        lines.append("")
        if self.state.active_colors:
            lines.append(f"**Colors:** {', '.join(self.state.active_colors)}")
        if self.state.active_lights:
            lines.append(f"**Lights:** {', '.join(self.state.active_lights)}")
        if self.state.active_symbols:
            lines.append(f"**Symbols:** {', '.join(self.state.active_symbols)}")
        if self.state.active_thoughts:
            lines.append(f"**Thoughts:** {', '.join(self.state.active_thoughts)}")
        out_path.write_text("\n".join(lines), encoding="utf-8")
        return out_path


# ---------------------------------------------------------------------------
# CLI.
# ---------------------------------------------------------------------------

def _project_dir(args) -> Path:
    return Path(args.dir) if args.dir else Path.cwd()


def cmd_init(args) -> None:
    engine = MuseEngine(_project_dir(args))
    engine.init(args.title)
    print(f"Initialized: {engine.state.title}")
    print(f"State file: {engine.state_path}")
    print("Begin at: The Ordinary World")
    print("Record your first decision with: muse_engine.py decide \"...\"")


def cmd_decide(args) -> None:
    engine = MuseEngine(_project_dir(args))
    print(engine.decide(args.text))


def cmd_consult(args) -> None:
    engine = MuseEngine(_project_dir(args))
    print(engine.consult())


def cmd_suggest(args) -> None:
    engine = MuseEngine(_project_dir(args))
    print(engine.suggest())


def cmd_advance(args) -> None:
    engine = MuseEngine(_project_dir(args))
    print(engine.advance())


def cmd_retreat(args) -> None:
    engine = MuseEngine(_project_dir(args))
    print(engine.retreat())


def cmd_status(args) -> None:
    engine = MuseEngine(_project_dir(args))
    print(engine.status())


def cmd_export(args) -> None:
    engine = MuseEngine(_project_dir(args))
    out = Path(args.out) if args.out else engine.dir / "story_export.md"
    engine.export(out)
    print(f"Exported to: {out}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="muse_engine",
        description="A symbolic exploration chatbot for writers.",
    )
    parser.add_argument("--dir", default=None, help="Story directory. Default: current directory.")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("init", help="Initialize a new story.")
    p.add_argument("--title", default="Working Title")
    p.set_defaults(func=cmd_init)

    p = sub.add_parser("decide", help="Record a writer's decision.")
    p.add_argument("text", help="The decision, in the writer's own words.")
    p.set_defaults(func=cmd_decide)

    p = sub.add_parser("consult", help="Get questions for the current stage.")
    p.set_defaults(func=cmd_consult)

    p = sub.add_parser("suggest", help="Get palette extensions and suggestions.")
    p.set_defaults(func=cmd_suggest)

    p = sub.add_parser("advance", help="Move to the next stage in the pyramid.")
    p.set_defaults(func=cmd_advance)

    p = sub.add_parser("retreat", help="Move to the previous stage.")
    p.set_defaults(func=cmd_retreat)

    p = sub.add_parser("status", help="Show current position and active palette.")
    p.set_defaults(func=cmd_status)

    p = sub.add_parser("export", help="Export the story record.")
    p.add_argument("--out", default=None)
    p.set_defaults(func=cmd_export)

    return parser


def main(argv: Optional[list] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    args.func(args)
    return 0


if __name__ == "__main__":
    sys.exit(main())
```
