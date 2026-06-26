#!/usr/bin/env python3
"""
A small Tall Tale-style storyworld about helping, a bone, and Twist.

The seed image:
- a child notices that Twist, a big friendly creature, cannot reach a favorite bone
- the child helps in a clever, physical way
- the trouble is loud and outsized, but the ending is warm and proof-driven

This world keeps the story grounded in a tiny simulation:
- meters track effort, strain, and relief
- memes track worry, pride, joy, and trust
- the ending changes because the world state changes
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

HELPING_THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self):
        for key in ("strain", "weight", "helped", "stuck"):
            self.meters.setdefault(key, 0.0)
        for key in ("joy", "worry", "trust", "pride", "relief"):
            self.memes.setdefault(key, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str
    kind: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Action:
    id: str
    verb: str
    gerund: str
    rush: str
    keyword: str
    twisty: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    label: str
    phrase: str
    type: str
    location: str
    weight: int = 1


@dataclass
class Tool:
    id: str
    label: str
    verb: str
    fit: str
    helps: set[str]


class World:
    def __init__(self, setting: Setting):
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.lines: list[str] = []
        self.fired: set[tuple] = set()
        self.facts: dict = {}

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.lines.append(text)

    def para(self) -> None:
        if self.lines and self.lines[-1] != "":
            self.lines.append("")

    def render(self) -> str:
        out = []
        buf = []
        for line in self.lines:
            if line == "":
                if buf:
                    out.append(" ".join(buf))
                    buf = []
            else:
                buf.append(line)
        if buf:
            out.append(" ".join(buf))
        return "\n\n".join(out)


SETTINGS = {
    "barn": Setting("the barn", "yard", {"tug", "lift"}),
    "hill": Setting("the windy hill", "outdoors", {"tug"}),
    "dock": Setting("the dock", "water", {"lift", "tug"}),
}

ACTIONS = {
    "tug": Action(
        id="tug",
        verb="pull at the bone",
        gerund="pulling at the bone",
        rush="heave on the bone",
        keyword="bone",
        twisty="twisted tight",
        tags={"bone", "help"},
    ),
    "lift": Action(
        id="lift",
        verb="lift the bone",
        gerund="lifting the bone",
        rush="hoist the bone",
        keyword="bone",
        twisty="stuck high",
        tags={"bone", "help"},
    ),
}

PRIZES = {
    "bone": Prize("bone", "a big old bone", "bone", "ground", 3),
}

TOOLS = {
    "lever": Tool("lever", "a fence board", "wedge", "long and sturdy", {"tug", "lift"}),
    "cart": Tool("cart", "a little cart", "roll", "wheeled and handy", {"lift"}),
    "rope": Tool("rope", "a rope loop", "loop", "strong and bendy", {"tug"}),
}

NAMES = ["Milo", "Penny", "June", "Toby", "Nell", "Finn", "Ruby", "Otis"]
TRAITS = ["brave", "quick", "kind", "spry", "clever", "steady"]


@dataclass
class StoryParams:
    place: str
    action: str
    name: str
    trait: str
    seed: Optional[int] = None


class TaleWorld:
    def __init__(self, world: World):
        self.world = world


def valid_combos() -> list[tuple[str, str]]:
    return [(place, action) for place, s in SETTINGS.items() for action in s.affords]


def story_reasonable(place: str, action: str) -> bool:
    return (place, action) in valid_combos()


def choose_tool(action: Action, place: Setting) -> Optional[Tool]:
    for tool in TOOLS.values():
        if action.id in tool.helps:
            return tool
    return None


def tell(setting: Setting, action: Action, hero_name: str, trait: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type="boy", label=hero_name))
    twist = world.add(Entity(id="Twist", kind="character", type="giant", label="Twist"))
    bone = world.add(Entity(id="bone", type="bone", label="bone", phrase="a big old bone", owner="Twist", caretaker="Twist"))
    tool = choose_tool(action, setting)

    # setup
    hero.memes["joy"] += 1
    twist.memes["trust"] += 1
    bone.meters["weight"] += PRIZES["bone"].weight
    world.say(
        f"{hero_name} was a {trait} little helper who loved tall tales and bright morning chores."
    )
    world.say(
        f"Twist was a giant friend with a laugh like a loose barn door, and {twist.pronoun('possessive')} favorite thing was {bone.phrase}."
    )
    world.say(
        f"One day at {setting.place}, {hero_name} saw that the bone was {action.twisty}."
    )

    # conflict
    world.para()
    twist.memes["worry"] += 1
    twist.meters["strain"] += 1
    world.say(
        f"Twist tried to {action.verb}, but the bone only bumped and bobbed in place."
    )
    world.say(
        f"The more {twist.id} tugged, the more {twist.pronoun('possessive')} shoulders felt strained."
    )
    hero.memes["worry"] += 1
    world.say(
        f"{hero_name} said, '{action.keyword.capitalize()}? Not for a friend like Twist. I can help.'"
    )

    # turn
    world.para()
    if tool:
        hero.meters["helped"] += 1
        hero.memes["trust"] += 1
        world.say(
            f"{hero_name} brought {tool.label} and used it to {tool.verb} under the bone."
        )
        world.say(
            f"With a little push and a lot of nerve, the bone creaked free."
        )
        bone.meters["stuck"] = 0
        twist.meters["strain"] = 0
        twist.memes["worry"] = 0
        twist.memes["relief"] += 1
        twist.memes["pride"] += 1
        hero.memes["pride"] += 1
        hero.memes["joy"] += 1
        world.say(
            f"Twist blinked once, then twice, and laughed so hard the rafters shook."
        )
    else:
        raise StoryError("No reasonable tool can help with that setup.")

    # ending image
    world.para()
    world.say(
        f"After that, {hero_name} and Twist sat together by the {setting.kind}, sharing the giant bone and a grin as wide as the road home."
    )

    world.facts.update(
        hero=hero,
        twist=twist,
        bone=bone,
        setting=setting,
        action=action,
        tool=tool,
        helped=True,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    action = f["action"]
    return [
        f'Write a tall tale for a small child about helping, a bone, and Twist, and include the word "{action.keyword}".',
        f"Tell a funny, oversized story where {hero.id} helps Twist with {action.gerund}.",
        f"Write a gentle tall tale that ends with Twist feeling better after a child helps with a bone.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    twist = f["twist"]
    bone = f["bone"]
    action = f["action"]
    tool = f["tool"]
    place = f["setting"].place
    return [
        QAItem(
            question=f"Who helped Twist at {place}?",
            answer=f"{hero.id} helped Twist at {place}."
        ),
        QAItem(
            question=f"What was Twist trying to do with the bone?",
            answer=f"Twist was trying to {action.verb}, but the bone was stuck and would not move at first."
        ),
        QAItem(
            question=f"What did {hero.id} use to help?",
            answer=f"{hero.id} used {tool.label} to help {twist.id} with the bone."
        ),
        QAItem(
            question=f"How did Twist feel at the end?",
            answer=f"Twist felt relieved and proud because the bone was free and help had worked."
        ),
        QAItem(
            question=f"What changed by the end of the story?",
            answer=f"The bone was no longer stuck, Twist was no longer strained, and everybody was smiling."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a bone?",
            answer="A bone is a hard part of a body, and it can also mean a leftover bone that people or animals sometimes chew or carry."
        ),
        QAItem(
            question="What does it mean to help?",
            answer="To help means to make something easier for someone else by doing a useful part of the work."
        ),
        QAItem(
            question="What is a twist?",
            answer="A twist is a turning bend, like when something curls around or gets turned in a new direction."
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== Story QA ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== World QA ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: meters={dict(e.meters)} memes={dict(e.memes)}")
    return "\n".join(lines)


ASP_RULES = r"""
reasonably_valid(Place, Action) :- setting(Place), affords(Place, Action).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for place, s in SETTINGS.items():
        lines.append(asp.fact("setting", place))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", place, a))
    for aid, a in ACTIONS.items():
        lines.append(asp.fact("action", aid))
        lines.append(asp.fact("keyword", aid, a.keyword))
    for t in TOOLS.values():
        lines.append(asp.fact("tool", t.id))
        for h in sorted(t.helps):
            lines.append(asp.fact("helps", t.id, h))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show reasonably_valid/2."))
    return sorted(set(asp.atoms(model, "reasonably_valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH:")
    print("python only:", sorted(py - cl))
    print("clingo only:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall tale storyworld about helping Twist with a bone.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--action", choices=ACTIONS)
    ap.add_argument("--name")
    ap.add_argument("--trait", choices=TRAITS)
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
    combos = valid_combos()
    if args.place or args.action:
        combos = [c for c in combos if (args.place is None or c[0] == args.place) and (args.action is None or c[1] == args.action)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, action = rng.choice(sorted(combos))
    name = args.name or rng.choice(NAMES)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, action=action, name=name, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], ACTIONS[params.action], params.name, params.trait)
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


CURATED = [
    StoryParams(place="barn", action="tug", name="Milo", trait="kind"),
    StoryParams(place="hill", action="tug", name="Penny", trait="clever"),
    StoryParams(place="dock", action="lift", name="June", trait="steady"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show reasonably_valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for item in combos:
            print(item)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 40):
            i += 1
            params = resolve_params(args, random.Random(base_seed + i))
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
