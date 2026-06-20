#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/heap_technology_conquer_repetition_teamwork_humor_slice.py
==========================================================================================

A small slice-of-life storyworld about a child, a messy heap, a bit of technology,
and a team effort that conquers repetition with humor.

Seed words:
- heap
- technology
- conquer

Features:
- repetition
- teamwork
- humor

Style:
- slice of life
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
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
    role: str = ""
    traits: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]



    @property
    def phrase(self) -> str:
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)
@dataclass
class Prop:
    id: str
    label: str
    phrase: str
    tag: str
    helpful: bool = False
    noisy: bool = False

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
class Gadget:
    id: str
    label: str
    phrase: str
    action: str
    charm: str
    power: int
    supports_teamwork: bool = True

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
@dataclass
class StoryParams:
    child: str
    child_gender: str
    buddy: str
    buddy_gender: str
    parent: str
    prop: str
    gadget: str
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


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.facts: dict = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.turns: int = 0

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
        c = World()
        c.entities = copy.deepcopy(self.entities)
        c.facts = copy.deepcopy(self.facts)
        c.paragraphs = [[]]
        c.fired = set(self.fired)
        c.turns = self.turns
        return c


PROPS = {
    "laundry_heap": Prop("laundry_heap", "laundry heap", "the laundry heap", "cloth"),
    "block_heap": Prop("block_heap", "block heap", "the block heap", "blocks"),
    "paper_heap": Prop("paper_heap", "paper heap", "the paper heap", "paper", noisy=True),
    "toy_heap": Prop("toy_heap", "toy heap", "the toy heap", "toys"),
}

GADGETS = {
    "robot": Gadget("robot", "robot vacuum", "a robot vacuum", "spin around", "whirred cheerfully", 3),
    "timer": Gadget("timer", "kitchen timer", "a kitchen timer", "take turns", "dinged brightly", 2),
    "labels": Gadget("labels", "label maker", "a label maker", "sort boxes", "clicked like a tiny beetle", 2),
    "music": Gadget("music", "playlist", "a silly cleanup playlist", "dance while sorting", "bopped along", 1),
}

GIRLS = ["Mia", "Lily", "Ava", "Zoe", "Nora", "Ella"]
BOYS = ["Leo", "Max", "Finn", "Theo", "Noah", "Sam"]
PARENTS = ["mom", "dad"]
HUMOR_BEATS = [
    "The robot made a tiny beep like it was proud of itself.",
    "One sock slid off the heap and landed on a chair like a flag.",
    "The timer dinged so happily it sounded like it wanted a turn too.",
    "The label maker printed a sticker that said 'Probably here.'",
]
TECH_WORDS = {
    "robot": [("What does a robot vacuum do?", "A robot vacuum rolls around and helps pick up crumbs and little bits from the floor.")],
    "timer": [("What is a kitchen timer for?", "A kitchen timer helps people take turns or know when to stop and start a job.")],
    "labels": [("What does a label maker do?", "A label maker prints words onto stickers so boxes and bins can be marked clearly.")],
    "music": [("Why can music help with chores?", "Music can make a boring job feel lighter and more fun, especially if people do it together.")],
    "heap": [("What is a heap?", "A heap is a messy pile of things stacked together without much order.")],
    "conquer": [("What does it mean to conquer a problem?", "It means to beat the problem and manage it well, usually by working steadily.")],
    "teamwork": [("What is teamwork?", "Teamwork is when people help each other and finish a job together.")],
    "repetition": [("Why do repeated jobs feel hard?", "Repeated jobs can feel tiring because you have to do the same thing again and again.")],
}


def aspirational_phrase() -> str:
    return "conquer the heap"


def choose_pair(rng: random.Random) -> tuple[str, str, str, str]:
    child_gender = rng.choice(["girl", "boy"])
    buddy_gender = "boy" if child_gender == "girl" else "girl"
    child = rng.choice(GIRLS if child_gender == "girl" else BOYS)
    buddy = rng.choice([n for n in (BOYS if buddy_gender == "boy" else GIRLS) if n != child])
    return child, child_gender, buddy, buddy_gender


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for prop_id, prop in PROPS.items():
        for gadget_id, gadget in GADGETS.items():
            if prop.helpful or gadget.supports_teamwork:
                combos.append((prop_id, gadget_id))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Slice-of-life storyworld: a child, a heap, and a helpful gadget.")
    ap.add_argument("--prop", choices=PROPS)
    ap.add_argument("--gadget", choices=GADGETS)
    ap.add_argument("--name")
    ap.add_argument("--buddy")
    ap.add_argument("--parent", choices=PARENTS)
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


def asp_facts() -> str:
    import asp
    lines = [asp.fact("prop", pid) for pid in PROPS]
    lines += [asp.fact("gadget", gid) for gid in GADGETS]
    lines += [asp.fact("helpful_prop", pid) for pid, p in PROPS.items() if p.helpful]
    lines += [asp.fact("team_gadget", gid) for gid, g in GADGETS.items() if g.supports_teamwork]
    return "\n".join(lines)


ASP_RULES = r"""
valid(P, G) :- prop(P), gadget(G), team_gadget(G).
"""


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    ok = py == cl
    print("OK: ASP matches Python." if ok else "MISMATCH between ASP and Python.")
    return 0 if ok else 1


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.prop is None or c[0] == args.prop)
              and (args.gadget is None or c[1] == args.gadget)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    prop, gadget = rng.choice(sorted(combos))
    child, cg, buddy, bg = choose_pair(rng)
    if args.name:
        child = args.name
    if args.buddy:
        buddy = args.buddy
    parent = args.parent or rng.choice(PARENTS)
    return StoryParams(child, cg, buddy, bg, parent, prop, gadget)


def clean_turn(world: World, child: Entity, buddy: Entity, prop: Prop, gadget: Gadget) -> None:
    child.memes["mischief"] += 1
    world.say(f"{child.id} stared at {prop.phrase} and grinned. It was a heap big enough to feel like a little mountain.")
    world.say(f'"We can {aspirational_phrase()}," {child.id} said, and {buddy.id} laughed because that sounded grand for a pile of socks and shirts.')
    world.say(f"{buddy.id} pointed at the {gadget.label}. " +
              f'"What if we use {gadget.phrase}?"')
    world.facts["attempted"] = True


def warn(world: World, parent: Entity, child: Entity, prop: Prop, gadget: Gadget) -> None:
    world.say(f"{parent.id} looked over the room and said, " +
              f'"That heap is getting bigger every day. If we keep repeating the same pile-up, it will conquer the whole corner."')
    world.say(f'"Let’s make a plan and use the {gadget.label}."')


def repeated_work(world: World, child: Entity, buddy: Entity, gadget: Gadget) -> None:
    child.memes["effort"] += 1
    buddy.memes["effort"] += 1
    world.say(f"So they started the same little routine again and again: pick up, sort, stack, and smile.")
    world.say(f"{gadget.charm.capitalize()} and the {gadget.label} made the room sound busy instead of bossy.")


def humor(world: World) -> None:
    world.say(rng.choice(HUMOR_BEATS) if (rng := random.Random(world.turns + 7)) else HUMOR_BEATS[0])


def resolve(world: World, parent: Entity, child: Entity, buddy: Entity, gadget: Gadget, prop: Prop) -> None:
    child.memes["pride"] += 1
    buddy.memes["pride"] += 1
    world.say(f"In the end, {child.id} and {buddy.id} worked side by side until the heap was only a neat little stack.")
    world.say(f"{parent.id} smiled, because teamwork had done what arguing could not, and even the {gadget.label} seemed pleased.")
    world.say(f"Together, they had used technology to conquer repetition, and the room felt calm again.")


def tell(params: StoryParams) -> World:
    rng = random.Random(params.seed)
    world = World()
    child = world.add(Entity(params.child, "character", params.child_gender, role="child", traits=["curious", "silly"]))
    buddy = world.add(Entity(params.buddy, "character", params.buddy_gender, role="buddy", traits=["helpful", "funny"]))
    parent = world.add(Entity("Parent", "character", params.parent, role="parent"))
    prop = PROPS[params.prop]
    gadget = GADGETS[params.gadget]
    world.facts.update(prop=prop, gadget=gadget, child=child, buddy=buddy, parent=parent)

    world.say(f"After snack time, {child.id} and {buddy.id} found a heap in the living room.")
    world.say(f"It was a heap of {prop.label}, and it looked like it had decided to stay forever.")
    world.para()
    clean_turn(world, child, buddy, prop, gadget)
    warn(world, parent, child, prop, gadget)
    world.para()
    repeated_work(world, child, buddy, gadget)
    humor(world)
    world.para()
    resolve(world, parent, child, buddy, gadget, prop)
    return world


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child, buddy, parent, prop, gadget = f["child"], f["buddy"], f["parent"], f["prop"], f["gadget"]
    return [
        ("What did the children find?", f"They found a heap in the living room, and it was a heap of {prop.label}."),
        ("What helped them?", f"They used {gadget.phrase} and worked together. The gadget made the job easier, but the teamwork was the important part."),
        ("How did they finish?", f"They kept sorting the heap again and again until it became a neat stack. In the end, they conquered the repetition together."),
        ("How did the parent feel?", f"{parent.id} was pleased because the room was calm again and the children had solved the problem without giving up."),
    ]


def world_qa(world: World) -> list[tuple[str, str]]:
    tags = {world.facts["prop"].tag, world.facts["gadget"].id, "teamwork", "repetition", "conquer"}
    out: list[tuple[str, str]] = []
    for k, items in TECH_WORDS.items():
        if k in tags:
            out.extend(items)
    return out


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a slice-of-life story for a young child that includes the words heap, technology, and conquer.",
        f"Tell a gentle humorous story where {f['child'].id} and {f['buddy'].id} use technology to deal with a heap in the home.",
        f"Write a teamwork story about repeating the same chore until the heap is conquered and the room feels tidy again.",
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        lines.append(f"  {e.id:8} ({e.type:7}) role={e.role} memes={dict(e.memes)}")
    return "\n".join(lines)


CURATED = [
    StoryParams("Mia", "girl", "Theo", "boy", "mom", "laundry_heap", "robot", 1),
    StoryParams("Leo", "boy", "Nora", "girl", "dad", "block_heap", "timer", 2),
    StoryParams("Ava", "girl", "Sam", "boy", "mom", "paper_heap", "labels", 3),
]


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_qa(world)],
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.prop is None or c[0] == args.prop)
              and (args.gadget is None or c[1] == args.gadget)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    prop, gadget = rng.choice(sorted(combos))
    child, cg, buddy, bg = choose_pair(rng)
    parent = args.parent or rng.choice(PARENTS)
    return StoryParams(args.name or child, cg, args.buddy or buddy, bg, parent, prop, gadget)


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible (prop, gadget) combos:")
        for p, g in asp_valid_combos():
            print(f"  {p:12} {g}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as err:
                print(err)
                return
            params.seed = seed
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
