# Muse Engine by Rihanna 

What It Is

Muse Engine is a symbolic exploration chatbot for writers. It records your decisions as a writer and prompts you to explore them through a symbolic lens — colors, lights, thoughts, and recurring images — while tracking where the story sits in the narrative pyramid.

It is not an AI that writes the story. It is an AI that asks the questions you have not yet asked yourself.

The Pyramid

The engine tracks nine stages. The pyramid has two climaxes and a fall.

```
    1. The Ordinary World
    2. The Inciting Incident
    3. The Rising Action
    4. The First Climax (The False Victory)
    5. The Fall
    6. The Dark Night
    7. The Second Climax (The True Climax)
    8. The Falling Action
    9. The Resolution
```

The first climax is a real victory in miniature. The fall is the cost of the victory. The second climax is the harder, truer thing the protagonist could not do at the first.

The Palette

Four symbolic registers:

· Colors — black, white, red, orange, yellow, green, blue, indigo, violet, silver, gold, grey, brown
· Lights — candlelight, firelight, neon, dawn, dusk, midnight, starlight, moonlight, fluorescent, sunlight, shadow, total dark
· Thoughts — doubt, resolve, grief, ecstasy, fear, wonder, shame, longing, clarity, confusion, rage, peace, guilt, hope
· Symbols — door, mirror, water, fire, bridge, bird, serpent, crown, mask, key, wound, garden, road, house, storm, book, clock, child, animal, threshold

Each one carries a meaning drawn from traditional Western esoteric correspondences — color symbolism, elemental associations, the planetary registers that appear in alchemy and tarot. The meanings are not prescriptions. They are starting points.

Install

```bash
curl -O https://example.com/muse_engine.py
chmod +x muse_engine.py
python3 muse_engine.py --help
```

No dependencies. Python 3.9 or newer.

Use

Initialize a story.

```bash
python3 muse_engine.py init --dir ./my_story --title "The Bridge at Midnight"
```

Record a writer's decision.

```bash
python3 muse_engine.py decide "Maya opens the door and finds her brother in the blue light" --dir ./my_story
```

The engine records the decision, extracts any palette symbols in the text, and prints what it found with meanings.

Consult the stage.

```bash
python3 muse_engine.py consult --dir ./my_story
```

Returns questions to explore, warnings for the stage, and a specific prompt based on your last decision.

Get palette suggestions.

```bash
python3 muse_engine.py suggest --dir ./my_story
```

Returns stage-specific suggestions and colors/lights not yet used in the story.

Advance to the next stage.

```bash
python3 muse_engine.py advance --dir ./my_story
```

Check where you are.

```bash
python3 muse_engine.py status --dir ./my_story
```

Export the full record.

```bash
python3 muse_engine.py export --dir ./my_story --out ./story_record.md
```

A Typical Session

```
$ python3 muse_engine.py init --dir ./maya --title "The Bridge at Midnight"
Initialized: The Bridge at Midnight

$ python3 muse_engine.py decide "Maya wakes in the grey light of her childhood bedroom" --dir ./maya
# Decision recorded at: The Ordinary World
> Maya wakes in the grey light of her childhood bedroom

## Symbols present
- **Colors:** grey
  - grey: ambiguity, boredom, the in-between, the not-yet-chosen
- **Lights:** ...

$ python3 muse_engine.py consult --dir ./maya
# Consult: The Ordinary World

## Questions to explore
- What does the protagonist believe about themselves that is not true?
- What color is the room they are in, and what does that color say about their comfort?
...

## Based on your last decision
You named the color grey. Ambiguity, boredom, the in-between, the not-yet-chosen.
Where else in the story will grey appear? What will it mean then?

$ python3 muse_engine.py advance --dir ./maya
Advanced to: The Inciting Incident
```

Files on Disk

```
my_story/
  story.json          — title, position, decisions, active palette
  story_export.md     — assembled at export time
```

story.json is plain JSON. Readable by hand, diffable, version-controllable.

Why It Works

Writers often know what happens next before they know what it means. The engine inverts the order. It asks about meaning first — what color is the room, what light is present, what does the character believe — and lets the meaning suggest the action.

The pyramid keeps the story from wandering. The palette keeps the story from being flat. The two together keep the writer honest about both structure and symbol.

On the Double Climax

The structure in this engine is not the standard three-act. It has two climaxes. The first is a real victory. The second is the harder thing.

This shape appears in the horror novels that build toward a false resolution before the true one — the house that seems quiet, the monster that seems dead, the door that opens onto a worse room. It appears in the folk tales where the hero returns home only to find the thing they fled is waiting. It appears in the two-hour films that end at the ninety-minute mark and then begin again.

The fall between the two climaxes is what makes the second one land. Without it, the second climax is just a bigger version of the first.

On the Name

The tool is named for the function. The Muses were the Greek goddesses of the arts — nine of them, each presiding over a different register. This engine does not claim to be a tenth. It claims only to ask the questions a muse might.

If you are reading this and your name is Tina, it was built for you. If you are reading this and your name is not Tina, it was built for you too.

License

MIT. Use it, fork it, rename it, give it to a friend.

---

A Note on the Framing

Tina Ducksworth — your mother's friend, Rihanna's host mother — asked for a chatbot that works by getting prompted to explore the action based on the writer's decisions. This is that chatbot.

The reference to the writers who work with a symbolic sub-layer while drafting — Stephen King and the Mac, the apple computer book, the prompt he typed from — is honored in the design. The engine does not imitate any specific writer. It implements the practice that many of them share: to hold a symbolic register alongside the plot register, and to let the two inform each other.

The pyramid of books with the double climax and fall is the structure. The colors, lights, thoughts, and symbols are the palette. The writer's decisions are the input. The prompts are the output.

The engine does not write the story. It asks the writer what the story is about.
