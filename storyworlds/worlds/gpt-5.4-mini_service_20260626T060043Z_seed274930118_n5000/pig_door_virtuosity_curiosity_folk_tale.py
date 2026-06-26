#!/usr/bin/env python3
"""
A folk-tale storyworld about a curious pig, a closed door, and a skillful turn.

Seed premise:
- A pig is drawn to a mysterious door.
- Curiosity pushes the pig to investigate.
- Mere pushing does not solve the problem.
- Virtuosity: a skillful, careful method opens the way.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    carried_by: Optional[str] = None
    open: bool = False
    lockable: bool = False
    locked: bool = False
    playable: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type == "pig":
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def short(self) -> str:
        return self.label or self.type


@dataclass
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


# ---------------------------------------------------------------------------
# Content registries
# ---------------------------------------------------------------------------

@dataclass
class Setting:
    place: str
    mood: str


@dataclass
class Door:
    id: str
    label: str
    phrase: str
    locked: bool
    lockable: bool = True


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    use: str
    helps_with: set[str] = field(default_factory=set)


SETTINGS = {
    "cottage": Setting(place="the old cottage", mood="warm and quiet"),
    "orchard": Setting(place="the orchard path", mood="windy and bright"),
    "barnyard": Setting(place="the barnyard", mood="busy and sunlit"),
}

DOORS = {
    "green_door": Door(
        id="green_door",
        label="green door",
        phrase="a green door with a sleepy brass latch",
        locked=True,
    ),
    "blue_door": Door(
        id="blue_door",
        label="blue door",
        phrase="a blue door painted with tiny stars",
        locked=True,
    ),
}

TOOLS = {
    "latch_key": Tool(
        id="latch_key",
        label="little key",
        phrase="a little key on a string",
        use="unlock the latch",
        helps_with={"locked"},
    ),
    "fiddle": Tool(
        id="fiddle",
        label="small fiddle",
        phrase="a small fiddle with a bright sound",
        use="play a tune",
        helps_with={"shy", "stuck"},
    ),
    "brush": Tool(
        id="brush",
        label="paint brush",
        phrase="a paint brush with a clean tip",
        use="paint a sign",
        helps_with={"blank"},
    ),
}

PIG_NAMES = ["Pippa", "Mabel", "Nell", "Rosie", "Dottie", "Tilda", "Pearl"]


# ---------------------------------------------------------------------------
# Story parameters
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    setting: str = "cottage"
    door: str = "green_door"
    tool: str = "fiddle"
    name: str = "Pippa"
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% A story is reasonable when the pig has curiosity, there is a door to notice,
% and there is a skillful tool that can help with the door's problem.
curious_story(S) :- pig(S), door(S,D), curiosity(S), helps(S,T,D).

reasonably_open(S) :- curious_story(S), tool(S,T), useful(T,D), door_problem(D,locked).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        lines.append(asp.fact("mood", sid, setting.mood))
    for did, door in DOORS.items():
        lines.append(asp.fact("door", did))
        lines.append(asp.fact("door_problem", did, "locked" if door.locked else "open"))
    for tid, tool in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        for flag in sorted(tool.helps_with):
            lines.append(asp.fact("useful", tid, flag))
    lines.append(asp.fact("feature", "curiosity"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show reasonably_open/1."))
    asp_set = set(asp.atoms(model, "reasonably_open"))
    py_set = set((params.setting,) for params in valid_params())
    if asp_set == py_set:
        print(f"OK: ASP gate matches Python gate ({len(asp_set)} stories).")
        return 0
    print("MISMATCH between ASP and Python gates.")
    print("ASP:", sorted(asp_set))
    print("PY :", sorted(py_set))
    return 1


# ---------------------------------------------------------------------------
# Reasonableness / validation
# ---------------------------------------------------------------------------

def valid_params() -> list[StoryParams]:
    out: list[StoryParams] = []
    for setting in SETTINGS:
        for door in DOORS:
            for tool in TOOLS:
                if door in {"green_door", "blue_door"} and tool in {"latch_key", "fiddle"}:
                    out.append(StoryParams(setting=setting, door=door, tool=tool))
    return out


def explain_invalid(door: Door, tool: Tool) -> str:
    if door.locked and tool.id == "brush":
        return "(No story: a paint brush cannot open a locked door.)"
    return "(No story: this combination does not create a believable folk-tale problem and fix.)"


# ---------------------------------------------------------------------------
# Simulation
# ---------------------------------------------------------------------------

def build_world(params: StoryParams) -> World:
    world = World()
    setting = SETTINGS[params.setting]
    door_cfg = DOORS[params.door]
    tool_cfg = TOOLS[params.tool]

    pig = world.add(Entity(
        id=params.name,
        kind="character",
        type="pig",
        label=params.name,
        meters={"steps": 0.0},
        memes={"curiosity": 0.0, "worry": 0.0, "joy": 0.0, "pride": 0.0},
    ))
    door = world.add(Entity(
        id=door_cfg.id,
        type="door",
        label=door_cfg.label,
        phrase=door_cfg.phrase,
        open=False,
        lockable=True,
        locked=door_cfg.locked,
    ))
    tool = world.add(Entity(
        id=tool_cfg.id,
        type="tool",
        label=tool_cfg.label,
        phrase=tool_cfg.phrase,
        playable=(tool_cfg.id == "fiddle"),
        meters={"shine": 1.0 if tool_cfg.id == "fiddle" else 0.0},
    ))

    world.facts.update(
        pig=pig,
        door=door,
        tool=tool,
        setting=setting,
        tool_cfg=tool_cfg,
        door_cfg=door_cfg,
        params=params,
    )

    # Act 1
    world.say(f"In {setting.place}, the day felt {setting.mood}.")
    world.say(f"There was {door.phrase}.")
    world.say(f"{pig.label} was a curious pig, and curiosity kept tugging at her hooves.")
    world.para()

    # Act 2
    pig.memes["curiosity"] += 1
    pig.meters["steps"] += 3
    world.say(f"{pig.label} trotted closer and listened at the door.")
    if door.locked:
        pig.memes["worry"] += 1
        world.say(f"The latch would not move, so {pig.label} could not simply push it open.")
        if tool.id == "latch_key":
            world.say(f"Then {pig.label} noticed {tool.phrase} hanging nearby.")
            world.say(f"She tried it on the latch, but careful hands mattered more than force.")
        else:
            world.say(f"Then {pig.label} noticed {tool.phrase} waiting by the wall.")
            world.say(f"She picked it up and let her feet settle before trying anything else.")
    world.para()

    # Act 3: skillful turn / virtuosity
    if tool.id == "fiddle":
        pig.memes["pride"] += 1
        pig.memes["joy"] += 1
        door.locked = False
        door.open = True
        world.say(f"{pig.label} lifted the small fiddle and played a bright, careful tune.")
        world.say(f"The tune was full of virtuosity, clear and sure, like a bird finding morning.")
        world.say(f"The sleepy brass latch clicked, and {door.label} swung open at last.")
        world.say(f"Behind it was a little room with a warm lamp, and {pig.label} smiled at the gentle surprise.")
    elif tool.id == "latch_key":
        pig.memes["joy"] += 1
        door.locked = False
        door.open = True
        world.say(f"{pig.label} slid the little key into the latch and turned it just so.")
        world.say(f"The lock gave way with a neat little click, and the door opened.")
        world.say(f"{pig.label} stood straight and proud, glad that patience had won the day.")
    else:
        pig.memes["worry"] += 1
        world.say(f"The paint brush could not help, so {pig.label} set it down again.")
        world.say(f"After that, the pig had to find a better way and the story could not finish kindly.")

    return world


# ---------------------------------------------------------------------------
# Text generation
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    pig = f["pig"]
    door = f["door"]
    tool = f["tool"]
    return [
        f"Write a short folk tale about a curious pig and {door.label} that ends in a skillful surprise.",
        f"Tell a gentle story where {pig.label} is curious about {door.phrase} and uses {tool.label} with virtuosity.",
        "Write a child-friendly folk tale in which curiosity leads a pig to a door and skill matters more than force.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    pig = f["pig"]
    door = f["door"]
    tool = f["tool"]
    setting = f["setting"]
    out = [
        QAItem(
            question=f"Who was curious about the door in {setting.place}?",
            answer=f"{pig.label} was the curious pig who wanted to know about the door.",
        ),
        QAItem(
            question=f"What did {pig.label} do when she reached {door.label}?",
            answer=f"She went closer, listened, and then tried to find a careful way to open it.",
        ),
        QAItem(
            question=f"What helped the pig solve the problem?",
            answer=f"{tool.label} helped, because it let the pig use skill instead of force.",
        ),
        QAItem(
            question="What changed by the end of the story?",
            answer=f"The locked door opened, and the pig ended the tale feeling proud and happy.",
        ),
    ]
    if tool.id == "fiddle":
        out.append(QAItem(
            question="Why did the story mention virtuosity?",
            answer="Because the pig used a skillful tune, and that careful musical skill opened the door.",
        ))
    return out


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is curiosity?",
            answer="Curiosity is the feeling that makes someone want to look, ask, and learn more.",
        ),
        QAItem(
            question="What is a door for?",
            answer="A door helps people or animals pass into a room, house, or other place, and it can be opened or closed.",
        ),
        QAItem(
            question="What does virtuosity mean?",
            answer="Virtuosity means doing something with impressive skill and control.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story QA ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World QA ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.type == "door":
            bits.append(f"locked={e.locked}")
            bits.append(f"open={e.open}")
        lines.append(f"  {e.id} ({e.type}) {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Public interface
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Folk-tale storyworld: pig, door, virtuosity, curiosity.")
    ap.add_argument("--setting", choices=sorted(SETTINGS))
    ap.add_argument("--door", choices=sorted(DOORS))
    ap.add_argument("--tool", choices=sorted(TOOLS))
    ap.add_argument("--name", choices=PIG_NAMES)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    setting = args.setting or rng.choice(list(SETTINGS))
    door = args.door or rng.choice(list(DOORS))
    tool = args.tool or rng.choice(list(TOOLS))
    name = args.name or rng.choice(PIG_NAMES)

    if door == "green_door" and tool == "brush":
        raise StoryError(explain_invalid(DOORS[door], TOOLS[tool]))
    if tool == "brush":
        raise StoryError(explain_invalid(DOORS[door], TOOLS[tool]))
    return StoryParams(setting=setting, door=door, tool=tool, name=name)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show reasonably_open/1."))
        return
    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show reasonably_open/1."))
        print(sorted(asp.atoms(model, "reasonably_open")))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    if args.all:
        samples = [generate(p) for p in valid_params()]
    else:
        samples: list[StorySample] = []
        seen: set[str] = set()
        for i in range(max(args.n * 40, 40)):
            if len(samples) >= args.n:
                break
            rng = random.Random(base_seed + i)
            try:
                params = resolve_params(args, rng)
            except StoryError as e:
                print(e)
                return
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
