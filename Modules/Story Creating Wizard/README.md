muse_wizard

A step-by-step Story Creation Wizard built on top of muse_lifestory. It walks a writer through the structural and psychological decisions the Muse engine consumes — protagonist, traits, adaptations, sacred flaw, chapters, scenes, dialogical voices, inherited master narratives, generational moral nodes, a present dilemma, choices, and consequences — and returns a completed blueprint ready for MoralSimulator and Reflector.

It does not generate prose. It does not score writing. It asks.

---

Why a wizard

muse_lifestory gives you a rigorous data model and a reflective engine, but no path into it. A writer facing an empty Character() and a blank NarrativeIdentity() has no obvious first move.

The wizard provides that move. It sequences the elicitation so that each answer informs the next: traits before adaptations, adaptations before chapters, chapters before scenes, scenes before voices, voices before the present dilemma. It is resumable — state carries a completed-steps log, so a writer can stop mid-session, save to JSON, and pick up later without re-answering anything.

It is also not a chatbot. No conversation loop, no hidden state, no scoring. Just ordered prompts against a plain dataclass.

---

Install

No installation. Standard library only.

```bash
python3 muse_wizard.py                # programmatic demo + JSON preview
python3 muse_wizard.py --interactive  # terminal wizard
```

Requires muse_lifestory.py in the same directory.

---

The fourteen steps

# Step What it gathers
1 protagonist A name. Enough to begin.
2 traits Level 1 — broad dispositional tendencies (Big Five territory).
3 adaptations Level 2 — situated goals, values, motives, strategies, loyalties.
4 flaw_and_wound Sacred flaw, inner issue, wounds, secrets.
5 boundaries Moral boundaries; relationships and their bonds.
6 chapters Life-story chapters, titled in the character's own idiom.
7 scenes High point / low point / turning point per chapter, with focalization.
8 voices Dialogical I-positions (Hermans) with stance and level-of-personality tag.
9 master_narratives Inherited and resisted cultural narratives; ideological setting.
10 moral_nodes Generational decisions across time, plus parent → child links.
11 dilemma The present situation, its year, its participants, its inherited parent node.
12 choices The options available under named ethical frameworks; which one is taken.
13 consequences Multi-step forward chain, each with year, sequence, identity revision, effects.
14 finalize Hands everything to MoralSimulator and Reflector; prints the reflection.

Steps 1–10 build the character and their inherited world. Steps 11–13 stage the present moral decision. Step 14 is where muse_lifestory's engine runs — the wizard itself produces no questions there; it only relays them.

---

Design principles

1. Resumable, not linear. Every step checks state.is_done(name) before running. StoryWizard.run(skip_completed=True) skips what is already done.
2. State is separate from the wizard. WizardState is a plain dataclass; StoryWizard is a thin orchestrator over a list of (name, fn) pairs. Nothing is hidden.
3. I/O is swappable. TerminalIO, SilentIO, and ScriptedIO all implement the same WizardIO protocol. The step functions never read stdin directly.
4. Defaults everywhere. Every prompt has a sensible default. SilentIO returns defaults unconditionally, so every loop terminates on the first "blank to stop" — that is why the programmatic demo finalizes without a single input.
5. No prose. The wizard asks for labels, sequences, and notes. It never asks the writer to write the scene.
6. The engine runs once. Only finalize invokes MoralSimulator and Reflector. Everything before is elicitation.
7. Standard library only. JSON serialization uses a recursive _jsonable that walks dataclasses and enums. No custom encoders.

---

Minimal usage

Programmatic

```python
from muse_wizard import WizardState, StoryWizard, SilentIO

state = WizardState()
state.character.name = "Ruth"
state.character.traits = [Trait("conscientiousness", 0.8)]
# ...populate the rest directly...

wizard = StoryWizard(state, SilentIO()).run()

print(wizard.summary())
print(wizard.to_dict())   # JSON-ready dict
wizard.save("ruth.json")
```

SilentIO answers every remaining prompt with its default. Because all the data is already present, the wizard's loops have nothing left to ask and simply finalize.

Interactive

```python
from muse_wizard import StoryWizard, TerminalIO

wizard = StoryWizard(io=TerminalIO())
state = wizard.run()
print(wizard.summary())
```

Scripted (tests, reproducibility)

```python
from muse_wizard import StoryWizard, ScriptedIO

io = ScriptedIO([
    "Ruth",                    # name
    "conscientiousness",       # trait name
    "0.8",                     # intensity
    "",                        # end traits
    # ... etc ...
], echo=True)

wizard = StoryWizard(io=io).run()
```

ScriptedIO returns canned answers in order and falls back to defaults when exhausted. Pass "__DEFAULT__" to accept a prompt's own default explicitly.

---

The I/O protocol

Every wizard step talks to a WizardIO implementation. Three ship in the box:

Class Purpose
TerminalIO Line-based interactive I/O with validation and defaults.
SilentIO Returns defaults only. Headless / programmatic runs.
ScriptedIO Replays a canned list of answers. Tests and reproducibility.

Custom implementations need only these methods:

```python
class MyIO(WizardIO):
    def section(self, title: str) -> None: ...
    def tell(self, msg: str) -> None: ...
    def ask(self, prompt: str, default: str = "") -> str: ...
    def ask_int(self, prompt: str, default: int = 0,
                lo: int = 0, hi: int = 10) -> int: ...
    def ask_float(self, prompt: str, default: float = 0.0,
                  lo: float = -1.0, hi: float = 1.0) -> float: ...
    def ask_yes_no(self, prompt: str, default: bool = True) -> bool: ...
    def ask_choice(self, prompt: str, options: list[str],
                   default: int = 0) -> int: ...
```

Steps never read input() directly, so embedding the wizard in a web app, a notebook, or a test harness requires no changes to step logic.

---

The WizardState

WizardState is a single dataclass holding everything the writer has built:

```python
@dataclass
class WizardState:
    character: Character
    nodes: list[MoralNode]
    links: list[tuple[str, str]]
    dilemma: Optional[Dilemma]
    chosen_choice: Optional[Choice]
    consequence_steps: list[ConsequenceStep]
    focalizer: str
    reflection: Optional[Reflection]
    _completed_steps: list[str]
```

Two methods worth knowing:

· build_memory() — reconstructs a GenerationalMemory from the flat nodes and links lists. Called only at finalize, so nodes can be added in any order and linked afterward.
· node_ids() — set of node identifiers, used for validating parent links and inherited-from references during elicitation.

---

Serialization

StoryWizard.to_dict() returns a JSON-ready structure; StoryWizard.save(path) writes it. The recursive _jsonable helper walks dataclasses and enum members, so the full blueprint — including nested Chapter and Scene objects inside Character — round-trips without custom encoders.

```python
wizard.save("ruth.json")
```

A WizardState.from_dict() loader is the natural next increment. The schema is already JSON-shaped; only the reconstruction of dataclasses and enums from strings is missing.

---

Summary output

StoryWizard.summary() returns a compact human-readable view:

```
Protagonist: Ruth
  traits: 2  adaptations: 2  chapters: 3  voices: 3
  sacred flaw: if I speak it, I will lose the only family I have
  inner issue: a brother's silence she has never been allowed to grieve
Generational nodes: 1  links: 0
Dilemma: Caleb asks Ruth what happened in 1965.
Choice: Tell the truth, and lose the family's preferred story
Consequence steps: 2
Focalizer: Caleb (grandson, 2026)
Sequence read: redemption
```

Sequence read comes from MoralSimulator.read_sequence(), so the summary reflects the arc the writer actually built, not the one intended.

---

What the wizard intentionally does not do

· Generate prose or dialogue
· Score the writer's choices
· Enforce a single mythic template
· Hide its steps behind a conversation loop
· Require any network or neural dependency
· Decide which dialogical voice is right
· Treat the Jesus-centered pass as a verdict rather than a modeled option

---

Module map

Symbol Role
WizardState Accumulating blueprint; completed-steps log; build_memory(), node_ids()
WizardIO Protocol base class for I/O
TerminalIO Interactive terminal implementation
SilentIO Defaults-only implementation
ScriptedIO Canned-answers implementation
StoryWizard Orchestrator; run(), to_dict(), save(), summary()
STEPS Ordered list of (name, fn) pairs the wizard runs
step_* functions One per elicitation step
_jsonable Recursive stdlib JSON helper

---

Extending

Adding a new step is three lines:

```python
def step_new_thing(state: WizardState, io: WizardIO) -> None:
    io.section("N. New thing")
    # ask whatever you need, write it into state
    state.mark("new_thing")

STEPS.insert(-1, ("new_thing", step_new_thing))   # before finalize
```

Skipping a step is a matter of passing a pre-populated state with state.mark("that_step") already called, or subclassing StoryWizard and overriding run().

Reordering the wizard means reordering STEPS. The step functions themselves have no coupling to their position.

---

Companion module

muse_wizard consumes muse_lifestory. See that module's README for the underlying model: McAdams' three-level personality, redemption and contamination sequences, dialogical self, generational memory, focalization registers, and the reflection layer.

---

License

Deliberately unlicensed in this sketch. Apply the license of the host project.
