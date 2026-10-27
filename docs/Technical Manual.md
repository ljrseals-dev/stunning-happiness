# Muse Agent — Technical Manual

**Version:** Integrated (Engine + Life-Story + Story Creating Wizard)  
**Language:** Python 3.9+  
**Dependencies:** Standard library only  
**Stance:** Structured mirror for the writer’s narrative unconscious — records decisions, extracts symbolic and structural charge, asks questions. Does not generate prose, score writing, or impose a single mythic template.

---

## 1. Purpose and design principles

Muse Agent helps writers explore book (and other long-form) narratives by:

1. Tracking position on a **nine-stage narrative pyramid** (two climaxes and a fall).
2. Reflecting a **symbolic palette** (colors, lights, thoughts, symbols) drawn from the writer’s own decision text.
3. Modeling **character identity** as an evolving life story (Dan McAdams) with dialogical voices and generational moral memory.
4. Walking the writer through a **Story Creating Wizard** that builds a complete blueprint without writing scenes.

**Hard constraints (never violated by the core modules):**

| Constraint | Meaning |
|---|---|
| No prose generation | The engine records, extracts, reflects, and asks |
| No quality scoring | No “good” / “bad” writing judgments |
| No mandatory template dogma | Pyramid and palette are provocations, not prescriptions |
| Standard library only | No pip packages required for core operation |
| Soft module loading | Core runs if `muse_lifestory.py` or `muse_wizard.py` is absent |

---

## 2. Repository layout

```
Muse-Agent-by-Rihanna-main/
├── muse_engine.py              # CLI + pyramid + palette + integration hub
├── muse_lifestory.py           # McAdams life-story / moral simulation layer
├── muse_wizard.py              # Story Creating Wizard
├── README.md
├── Technical Manual.md         # this document
├── LICENSE
├── Modules/
│   ├── Dan McAdams's/
│   │   ├── README.md
│   │   ├── muse_lifestory.md
│   │   └── muse_lifestory.py   # module copy / reference
│   └── Story Creating Wizard/
│       ├── README.md
│       └── muse_wizard.py      # module copy / reference
├── docs/
│   ├── Muse Engine’s narrative psychology.md
│   └── future releases/
│       └── Muse 3.1            # Moral Simulation Room roadmap
├── Muse-Agent-Autonomous-Writers-Room-2.0.zip
└── Muse-Agent-3.0-Moral-Conflict-Writers-Room.zip
```

Runtime expects `muse_engine.py`, `muse_lifestory.py`, and `muse_wizard.py` in the **same directory** (or on `PYTHONPATH`).

---

## 3. Architecture

```
                    ┌─────────────────────┐
                    │   muse_engine.py    │
                    │  (CLI + StoryState  │
                    │   + MuseEngine)     │
                    └──────────┬──────────┘
                               │ soft import
              ┌────────────────┼────────────────┐
              ▼                                 ▼
    ┌──────────────────┐              ┌──────────────────┐
    │ muse_lifestory.py│              │  muse_wizard.py  │
    │ Character, Memory│◄─────────────│ StoryWizard steps│
    │ Simulator,       │   builds     │ TerminalIO /     │
    │ Reflector        │              │ SilentIO         │
    └──────────────────┘              └──────────────────┘
```

| Module | Responsibility |
|---|---|
| **muse_engine** | Project I/O, pyramid stages, palette extraction, `consult` / `decide` / `export`, CLI, persistence (`story.json`, `characters.json`, `memory.json`) |
| **muse_lifestory** | Three-level personality, narrative identity, generational moral graph, moral simulator, post-choice reflection |
| **muse_wizard** | Ordered elicitation of a full blueprint; imports into the engine via `apply_wizard_state` |

Flags set at import time:

- `HAS_LIFESTORY` — `True` if `muse_lifestory` imported successfully  
- `HAS_WIZARD` — `True` if `muse_wizard` imported successfully  

---

## 4. Narrative pyramid

Nine stages (`muse_engine.PYRAMID`). Position is an integer index `0..8` stored in `StoryState.position`.

| Index | Key | Name |
|------:|---|---|
| 0 | `ordinary_world` | The Ordinary World |
| 1 | `inciting_incident` | The Inciting Incident |
| 2 | `rising_action` | The Rising Action |
| 3 | `first_climax` | The First Climax (False Victory) |
| 4 | `the_fall` | The Fall |
| 5 | `dark_night` | The Dark Night |
| 6 | `second_climax` | The Second Climax (True Climax) |
| 7 | `falling_action` | The Falling Action |
| 8 | `resolution` | The Resolution |

Each `Stage` holds three lists:

- **ask** — open questions (belief, perception, sensory atmosphere)
- **warns** — stage-specific failure modes
- **suggests** — craft moves linking structure and palette

**Structural idea:** the first climax is a real victory in miniature; the fall is its cost; the second climax is the harder act the protagonist could not yet perform.

Commands: `advance`, `retreat`, `status`, `consult`.

---

## 5. Symbolic palette

Four registers. Meanings are starting points (Western esoteric / craft associations), not universal truths.

| Register | Examples |
|---|---|
| **Colors** | black, white, red, orange, yellow, green, blue, indigo, violet, silver, gold, grey, brown |
| **Lights** | candlelight, firelight, neon, dawn, dusk, midnight, starlight, moonlight, fluorescent, sunlight, shadow, total dark |
| **Thoughts** | doubt, resolve, grief, ecstasy, fear, wonder, shame, longing, clarity, confusion, rage, peace, guilt, hope |
| **Symbols** | door, mirror, water, fire, bridge, bird, serpent, crown, mask, key, wound, garden, road, house, storm, book, clock, child, animal, threshold |

**Extraction:** `extract_symbols(text)` is deterministic keyword matching (word boundaries, case-insensitive). No LLM.

On `decide`, matches are stored on the `Decision` and accumulated into `StoryState.active_*` lists. `consult` and `suggest` reuse them for reactive prompts.

---

## 6. Persistence model

All paths are under the story directory (`--dir`, default: current working directory).

| File | Contents |
|---|---|
| `story.json` | Title, pyramid position, decisions, active palette lists, `active_character` |
| `characters.json` | Serialized `Character` objects (full life-story) |
| `memory.json` | Generational `MoralNode` graph |
| `wizard_blueprint.json` | Full wizard export after `wizard` completes |
| `story_export.md` | Optional human-readable export (`export`) |

### 6.1 StoryState

```text
title: str
position: int
decisions: list[Decision]
active_colors | active_lights | active_symbols | active_thoughts: list[str]
active_character: str
```

### 6.2 Decision

```text
text, position (stage key), symbols, colors, lights, thoughts, timestamp (UTC ISO)
```

### 6.3 Character serialization

Three McAdams levels plus narrative identity:

- **Level 1 — Traits** (`Trait`: name, intensity, note)
- **Level 2 — Adaptations** (`Adaptation`: name, kind, weight, context, note)
- **Level 3 — NarrativeIdentity**: chapters, scenes, dialogical voices, master narratives inherited/resisted, sacred flaw, inner issue, ideological setting
- Also: secrets, wounds, moral_boundaries, relationships

Enums persisted as string values:

- `SequenceType`: `redemption` | `contamination` | `neutral`
- `VoiceStance`: `assenting` | `dissenting` | `ambivalent` | `silent`
- `SceneType`, `ConsciousnessRegister` (focalization / interiority)

---

## 7. Life-story layer (`muse_lifestory.py`)

### 7.1 Core types

| Type | Role |
|---|---|
| `Character` | Container for traits, adaptations, narrative, secrets, wounds, boundaries, relationships |
| `NarrativeIdentity` | Chapters, scenes, voices, master narratives, sacred flaw, inner issue |
| `DialogicalVoice` | Hermans-style I-position (`stance_toward`, `stance`, `speaks_for`) |
| `Scene` / `Chapter` | Life-story interview units with affect, sequence, consciousness, filtered content |
| `MoralNode` | Past/present decision that can parent future dilemmas |
| `GenerationalMemory` | Directed graph of moral nodes (`add`, `link`, `ancestors`, `identity_cost_report`) |
| `Dilemma` / `Choice` / `ConsequenceStep` | Structured moral situation and multi-step outcomes |
| `MoralSimulator` | Rule-based chain materialization, sequence reading, dialogical disagreement |
| `Reflector` | Post-choice questions, focalization note, telling-ethics note, identity cost — **no verdicts** |
| `LifeStoryInterview` | Prompt protocol (chapter division, high/low/turning points, etc.) |

### 7.2 Sequence reading

`MoralSimulator.read_sequence` classifies the arc the writer actually built (keyword heuristics on step descriptions). Intended to be overridden by the writer’s own rules, not treated as authoritative psychology.

### 7.3 Reflection philosophy

`Reflector.after_choice` returns:

- Open questions (chapter survival, sacred-flaw interaction, sequence honesty)
- Sequence label
- Focalization note (what the audience cannot see from this POV)
- Telling-ethics note (what moral understanding is cultivated or foreclosed)
- Identity-cost report from generational memory ancestors

The character remains free to refuse a Jesus-centered or other framework pass (`Choice.refused`).

---

## 8. Story Creating Wizard (`muse_wizard.py`)

### 8.1 Step order (`STEPS`)

1. `protagonist`  
2. `traits`  
3. `adaptations`  
4. `flaw_and_wound`  
5. `boundaries`  
6. `chapters`  
7. `scenes`  
8. `voices`  
9. `master_narratives`  
10. `moral_nodes`  
11. `dilemma`  
12. `choices`  
13. `consequences`  
14. `finalize` (runs simulator + reflector when dilemma/choice present)

### 8.2 I/O abstraction

| Class | Use |
|---|---|
| `WizardIO` | Protocol: `section`, `tell`, `ask`, `ask_int`, `ask_float`, `ask_yes_no`, `ask_choice` |
| `TerminalIO` | Interactive line-based terminal |
| `SilentIO` | Defaults only (tests / embedding) |
| `ScriptedIO` | Scripted answers for automation |

### 8.3 StoryWizard API

```text
run(skip_completed=True) -> WizardState
to_dict() -> dict
save(path)
summary() -> str
```

`WizardState` holds character, nodes, links, dilemma, chosen_choice, consequence_steps, focalizer, reflection, and a completed-steps log (resumable).

### 8.4 Engine integration

`MuseEngine.apply_wizard_state(wizard)`:

1. Stores character under `characters.json` and sets `active_character`
2. Merges moral nodes/links into `memory.json`
3. Writes `wizard_blueprint.json`
4. Prints summary and next-step hints

CLI:

```bash
python3 muse_engine.py --dir ./my_story wizard          # interactive
python3 muse_engine.py --dir ./my_story wizard --demo   # Ruth / 1965 programmatic demo
```

Standalone:

```bash
python3 muse_wizard.py                 # demo summary + JSON preview
python3 muse_wizard.py --interactive   # terminal session without engine import
```

---

## 9. CLI reference

Global option (parent parser — place **before** the subcommand):

```bash
python3 muse_engine.py --dir ./my_story <command> ...
```

| Command | Description |
|---|---|
| `init --title TITLE` | Create story directory and `story.json` |
| `decide TEXT` | Record decision; extract palette |
| `consult` | Stage questions, warnings, reactive + identity prompts |
| `suggest` | Unused palette + stage suggestions |
| `advance` / `retreat` | Move pyramid position |
| `status` | Position and active palette |
| `export [--out PATH]` | Markdown record |
| `character add --name NAME [--sacred-flaw ...] [--inner-issue ...] [--ideological-setting ...]` | Create character |
| `character list` | List characters |
| `character focus --name NAME` | Set active character |
| `character voice --name NAME --voice V --toward T [--stance S] [--speaks-for L]` | Add dialogical voice |
| `lifestory [--name NAME]` | Life Story Interview prompts |
| `memory --id ID --year Y --actor A --summary S [--sequence ...] [--identity-cost ...] [--identity-gain ...] [--parent ID]` | Add moral node |
| `reflect --situation S --year Y --choice C [--framework F] [--description D] [--focalizer F] [--consequence C]` | Post-choice reflection |
| `wizard [--demo]` | Story Creating Wizard |

Framework values for `reflect` / choices:  
`consequentialist` | `deontological` | `virtue` | `care` | `jesus_centered` | `narrative_ethics`

---

## 10. Typical workflows

### 10.1 Minimal symbolic session

```bash
python3 muse_engine.py --dir ./bridge init --title "The Bridge at Midnight"
python3 muse_engine.py --dir ./bridge decide "Maya opens the door in blue neon"
python3 muse_engine.py --dir ./bridge consult
python3 muse_engine.py --dir ./bridge suggest
python3 muse_engine.py --dir ./bridge advance
```

### 10.2 Character + generational moral chain

```bash
python3 muse_engine.py --dir ./ruth character add --name Ruth \
  --sacred-flaw "Silence keeps the family safe" \
  --inner-issue "She protected her brother by not speaking"

python3 muse_engine.py --dir ./ruth character voice --name Ruth \
  --voice Protector --toward "the family secret" --stance dissenting --speaks-for level_2_value

python3 muse_engine.py --dir ./ruth memory --id 1965_silence --year 1965 --actor Ruth \
  --summary "She does not speak the neighbor's name" \
  --sequence contamination --identity-cost "erases the neighbor's story"

python3 muse_engine.py --dir ./ruth decide "Ruth stands in the blue kitchen light"
python3 muse_engine.py --dir ./ruth consult
python3 muse_engine.py --dir ./ruth reflect \
  --situation "Caleb asks what happened in 1965" --year 2026 \
  --choice "Tell the truth" --framework jesus_centered \
  --consequence "The preferred family story begins to break"
```

### 10.3 Full wizard bootstrap

```bash
python3 muse_engine.py --dir ./ruth init --title "The Neighbor's Name"
python3 muse_engine.py --dir ./ruth wizard --demo
python3 muse_engine.py --dir ./ruth consult
python3 muse_engine.py --dir ./ruth reflect \
  --situation "Caleb asks what happened in 1965" --year 2026 \
  --choice "Tell the truth" --framework jesus_centered
```

---

## 11. Extension points

| Extension | Where to hook |
|---|---|
| Custom sequence classification | Override / replace `MoralSimulator.read_sequence` |
| New ethical frameworks | `Choice.framework` string + disagreement rules in `dialogical_disagreement` |
| Additional wizard steps | Append to `STEPS` in `muse_wizard.py` |
| Non-terminal UI | Implement `WizardIO` (GUI, notebook, web) |
| Resume partial wizard | Load `wizard_blueprint.json` into `WizardState` (extend loader as needed) |
| Muse 3.1 Moral Simulation Room | See `docs/future releases/Muse 3.1` — multi-step consequence graph, media-independent dilemma loop |

Do **not** add scene/dialogue generation or prose scoring to the core path without a deliberate product decision; that breaks the project’s stated stance.

---

## 12. Testing and verification

Smoke checks (no third-party test runner required):

```bash
python3 -m py_compile muse_engine.py muse_lifestory.py muse_wizard.py
python3 muse_wizard.py                    # programmatic demo summary
python3 muse_engine.py --help
python3 muse_engine.py --dir /tmp/muse_t init --title T
python3 muse_engine.py --dir /tmp/muse_t wizard --demo
python3 muse_engine.py --dir /tmp/muse_t consult
```

Optional: exercise `muse_lifestory` demo via `python3 muse_lifestory.py`.

---

## 13. Roadmap notes (Muse 3.1)

Documented in `docs/future releases/Muse 3.1`. Direction of travel:

- Character-state model (already partially present)
- Dilemma generator and multi-framework reasoning engines
- Multi-step “what happens next” simulator as plot mechanics
- Character disagreement as dramatic conflict
- Generational memory across decades
- Moral consequence graph
- Jesus-centered alternative pass that the character may refuse
- Media-independent output (novel / TV / film / sketch)

Preferred path: deterministic simulation framework first; specialized neural models later for prose, dialogue, continuity — not as a replacement for the mirror.

---

## 14. License and attribution

See `LICENSE` in the repository root.  

Theoretical anchors (not code dependencies): Dan McAdams (narrative identity, redemption/contamination sequences), Hubert Hermans (dialogical self), craft traditions reflected in focalization / sacred-flaw language (e.g. Genette, Cohn, Cron-style inner issue), and the project’s own narrative-psychology notes under `docs/`.

---

*End of Technical Manual.*
