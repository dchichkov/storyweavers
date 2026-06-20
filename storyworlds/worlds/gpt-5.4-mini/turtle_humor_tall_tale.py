#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/turtle_humor_tall_tale.py
========================================================

A standalone story world for a humorous tall tale about a turtle with a giant
job, a boastful problem, and an absurdly practical fix. The world keeps a small
simulation of characters, a race, a runaway pile of river mud, and a turtle whose
slow wisdom turns the ending into a joke that still feels earned.

The seed image is simple: a turtle enters a silly tall tale. The implementation
expands that into a tiny causal domain where a boastful animal tries to outdo a
slow-but-clever turtle, gets into a mess, and then discovers that the turtle's
method is the only one that works.

Run it
------
    python storyworlds/worlds/gpt-5.4-mini/turtle_humor_tall_tale.py
    python storyworlds/worlds/gpt-5.4-mini/turtle_humor_tall_tale.py --all
    python storyworlds/worlds/gpt-5.4-mini/turtle_humor_tall_tale.py -n 5 --seed 7
    python storyworlds/worlds/gpt-5.4-mini/turtle_humor_tall_tale.py --qa --json
    python storyworlds/worlds/gpt-5.4-mini/turtle_humor_tall_tale.py --verify
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    attrs: dict = field(default_factory=dict)

    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]



    @property
    def phrase(self) -> str:
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)
@dataclass
class Setting:
    id: str
    place: str
    river: str
    sky: str
    mud: str

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Challenger:
    id: str
    type: str
    boast: str
    rush: str
    wobble: str
    skill: str
    tripped_by: str
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class TurtleTool:
    id: str
    label: str
    method: str
    fix: str
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Problem:
    id: str
    label: str
    trouble: str
    mess: str
    risky: bool = True
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        c = World(self.setting)
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        return c


@dataclass
@dataclass
class StoryParams:
    setting: str
    challenger: str
    problem: str
    tool: str
    hero: str
    sidekick: str
    seed: Optional[int] = None

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


SETTINGS = {
    "riverbank": Setting("riverbank", "the riverbank", "the river", "a windy sky", "mud"),
    "marsh": Setting("marsh", "the marsh", "the creek", "a bright sky", "mud"),
    "pond": Setting("pond", "the pond edge", "the pond", "a sleepy sky", "mud"),
}

CHALLENGERS = {
    "heron": Challenger("heron", "bird", "boast", "ran faster than the wind", "slid into a puddle", "fly", "the slick mud", tags={"bird", "boast"}),
    "goose": Challenger("goose", "bird", "honked the loudest brag", "sprinted in a huff", "plopped into a muddy ditch", "glide", "the muddy bank", tags={"bird", "boast"}),
    "otter": Challenger("otter", "animal", "twirled a silly challenge", "whirled down the bank", "spun straight into the mud", "slide", "the muddy reeds", tags={"animal", "boast"}),
}

PROBLEMS = {
    "mudslide": Problem("mudslide", "a mudslide", "the bank had turned slick", "the mud kept slithering downhill", tags={"mud", "slick"}),
    "pileup": Problem("pileup", "a pile of driftwood", "the sticks jammed the path", "the sticks stacked up like a wobbling wall", tags={"wood", "jam"}),
    "floodlog": Problem("floodlog", "a flood log", "the log blocked the way", "the log floated and bumped the bank", tags={"water", "block"}),
}

TOOLS = {
    "shellbridge": TurtleTool("shellbridge", "shell bridge", "brace the shells under the load", "made a sturdy path", tags={"turtle", "bridge"}),
    "mudsled": TurtleTool("mudsled", "mud sled", "slide slow and low", "slid the trouble out of the way", tags={"turtle", "slide"}),
    "berryrope": TurtleTool("berryrope", "berry rope", "tie a berry rope and tug in rhythm", "pulled the jam loose one careful inch at a time", tags={"turtle", "rope"}),
}

TALL_TALE = {
    "scale": [
        "The story was so big the crows had to tilt their heads to watch it.",
        "The mud was so deep it could have rented a room under a fence.",
        "The wind was so lively it seemed to brush its own teeth.",
    ],
    "humor": [
        "Even the reeds looked surprised and tried to stand straighter.",
        "A snail nearby gave a slow clap that lasted nearly the whole afternoon.",
        "The goose announced it was not impressed, which was how everyone knew it was nervous.",
    ],
}


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for s in SETTINGS:
        for c in CHALLENGERS:
            for p in PROBLEMS:
                if c == "heron" and p == "pileup":
                    combos.append((s, c, p))
                elif c == "goose" and p in {"mudslide", "floodlog"}:
                    combos.append((s, c, p))
                elif c == "otter":
                    combos.append((s, c, p))
    return combos


def announce(world: World, hero: Entity, sidekick: Entity, challenge: Challenger, problem: Problem) -> None:
    world.say(
        f"On a day when the {world.setting.place} was wider than a wagon road, "
        f"{hero.id} the turtle plodded along beside {sidekick.id}. "
        f"{random.choice(TALL_TALE['scale'])}"
    )
    world.say(
        f"Then {challenge.id} shouted, \"{challenge.boast}!\" and tried to "
        f"{challenge.rush}. {random.choice(TALL_TALE['humor'])}"
    )
    world.say(
        f"But there was {problem.label} ahead: {problem.trouble}, and "
        f"{problem.mess}."
    )


def predict(world: World, tool: TurtleTool, problem: Problem) -> dict:
    sim = world.copy()
    _use_tool(sim, sim.get("hero"), tool, problem, narrate=False)
    return {"fixed": sim.get("problem").meters["fixed"] >= THRESHOLD}


def _use_tool(world: World, hero: Entity, tool: TurtleTool, problem: Problem, narrate: bool = True) -> None:
    problem_ent = world.get("problem")
    problem_ent.meters["fixed"] += 1
    hero.memes["pride"] += 1
    if narrate:
        world.say(f"{hero.id} chose a tall-tale remedy and {tool.method}.")
    world.say(f"{tool.fix}.")


def struggle(world: World, hero: Entity, sidekick: Entity, challenge: Challenger) -> None:
    hero.meters["slow"] += 1
    sidekick.memes["wonder"] += 1
    world.say(
        f"{challenge.id} sped ahead, but the bank answered with a squishy "
        f"sound and {challenge.id} {challenge.wobble}."
    )
    world.say(
        f"{sidekick.id} laughed so hard {sidekick.pronoun('subject')} had to sit "
        f"down on a flat stone."
    )


def rescue(world: World, hero: Entity, sidekick: Entity, tool: TurtleTool, problem: Problem) -> None:
    world.say(
        f"Then {hero.id} nodded and said, \"Slow is just fast enough when the ground is sneaky.\""
    )
    _use_tool(world, hero, tool, problem)
    hero.memes["satisfaction"] += 1
    sidekick.memes["delight"] += 1
    world.say(
        f"The trouble gave up at last, and {problem.label} stopped acting like a "
        f"bossy goblin."
    )
    world.say(
        f"{sidekick.id} cheered, {hero.id} blinked with solemn turtle dignity, "
        f"and the riverbank looked less like a joke and more like a path."
    )


def tell(setting: Setting, challenger: Challenger, problem: Problem, tool: TurtleTool,
         hero_name: str = "Tilda", hero_type: str = "turtle",
         sidekick_name: str = "Milo", sidekick_type: str = "boy") -> World:
    world = World(setting)
    hero = world.add(Entity("hero", "character", hero_type, label="turtle", role="hero"))
    sidekick = world.add(Entity("sidekick", "character", sidekick_type, label="friend", role="sidekick"))
    ch = world.add(Entity("challenger", "character", challenger.type, label=challenger.id, role="challenger"))
    prob = world.add(Entity("problem", "thing", "problem", label=problem.label, role="problem"))

    announce(world, hero, sidekick, challenger, problem)
    world.para()
    struggle(world, hero, sidekick, challenger)
    world.para()
    rescue(world, hero, sidekick, tool, problem)

    world.facts.update(hero=hero, sidekick=sidekick, challenger=ch, problem=prob, tool=tool, setting=setting)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        "Write a funny tall tale for a young child that includes a turtle, a boast, and a silly fix.",
        f"Tell a humorous story where {f['challenger'].id} boasts big, but a turtle solves {f['problem'].label} in a surprising way.",
        "Write a tall tale with a turtle who stays calm, uses a clever tool, and ends with a joke about slow speed.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, sidekick, challenger, problem = f["hero"], f["sidekick"], f["challenger"], f["problem"]
    return [
        QAItem("Who is the story about?", f"It is about {hero.id}, a turtle, and {sidekick.id}, who watched a silly challenge unfold."),
        QAItem(f"What did {challenger.id} do?", f"{challenger.id} made a big boast and rushed ahead, but that only got {challenger.id} into a funny mess."),
        QAItem("How did the turtle help?", f"{hero.id} used a slow, clever method and fixed {problem.label} without fuss. That was the joke: the slowest one was the smartest one."),
        QAItem("How did the story end?", f"It ended with the trouble cleared away, {sidekick.id} laughing, and the turtle looking calm and proud."),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem("What is a turtle?", "A turtle is a slow animal with a shell. Turtles can be patient and very steady."),
        QAItem("Why is mud slippery?", "Mud can be slippery because it is wet and soft, so feet and paws slide easily on it."),
        QAItem("What does it mean to boast?", "To boast means to talk as if you are the biggest, best, or fastest one around."),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    out = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        out.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(out)


CURATED = [
    StoryParams("riverbank", "heron", "pileup", "shellbridge", "Tilda", "Milo"),
    StoryParams("marsh", "goose", "mudslide", "mudsled", "Tilda", "Milo"),
    StoryParams("pond", "otter", "floodlog", "berryrope", "Tilda", "Milo"),
]


def explain_rejection() -> str:
    return "(No story: this combination is too tame for a tall tale or has no funny trouble.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Humorous tall-tale turtle story world.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--challenger", choices=CHALLENGERS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--hero")
    ap.add_argument("--sidekick")
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.challenger is None or c[1] == args.challenger)
              and (args.problem is None or c[2] == args.problem)]
    if not combos:
        raise StoryError(explain_rejection())
    setting, challenger, problem = rng.choice(sorted(combos))
    tool = args.tool or rng.choice(sorted(TOOLS))
    hero = args.hero or rng.choice(["Tilda", "Toby", "Mina", "Otis"])
    sidekick = args.sidekick or rng.choice(["Milo", "Nell", "Pip", "June"])
    return StoryParams(setting, challenger, problem, tool, hero, sidekick)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], CHALLENGERS[params.challenger], PROBLEMS[params.problem], TOOLS[params.tool], params.hero, "turtle", params.sidekick, "boy")
    return StorySample(params=params, story=world.render(), prompts=generation_prompts(world),
                       story_qa=story_qa(world), world_qa=world_knowledge_qa(world), world=world)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


ASP_RULES = r"""
valid(S, C, P) :- setting(S), challenger(C), problem(P), okay(C, P).
okay(heron, pileup).
okay(goose, mudslide).
okay(goose, floodlog).
okay(otter, mudslide).
okay(otter, pileup).
okay(otter, floodlog).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for c in CHALLENGERS:
        lines.append(asp.fact("challenger", c))
    for p in PROBLEMS:
        lines.append(asp.fact("problem", p))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        print("MISMATCH: ASP gate differs from Python valid_combos()")
        rc = 1
    try:
        sample = generate(CURATED[0])
        _ = sample.story
        print("OK: smoke generate() succeeded.")
    except Exception as e:
        print(f"SMOKE FAIL: {e}")
        rc = 1
    return rc


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        for combo in asp_valid_combos():
            print(combo)
        return

    base = args.seed if args.seed is not None else random.randrange(2**31)
    samples = [generate(p) for p in CURATED] if args.all else []
    if not args.all:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            i += 1
            try:
                params = resolve_params(args, random.Random(base + i))
            except StoryError as err:
                print(err)
                return
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)

    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
