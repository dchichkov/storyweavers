#!/usr/bin/env python3
"""
A small storyworld for a power-ful elephant in a rhyming, happy-ending tale.

Seed premise:
A power-ful elephant wants to help a friend by moving something heavy, but the
thing gets stuck. The elephant tries, learns a better way, and ends with a
bright, cheerful success.

The world is intentionally small:
- one elephant hero
- one friend/helper
- one heavy object that can be moved
- one location where the action happens
- one safe tool or method that makes the ending happy

The prose stays close to a rhyming, child-facing style while still being driven
by simulated world state.
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


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    helper: Optional[str] = None
    portable: bool = False
    heavy: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"stuck": 0.0, "moved": 0.0}
        if not self.memes:
            self.memes = {"hope": 0.0, "worry": 0.0, "joy": 0.0, "pride": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        if self.type == "elephant":
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Setting:
    place: str
    surface: str
    supports: set[str] = field(default_factory=set)


@dataclass
class HeavyThing:
    id: str
    label: str
    phrase: str
    size: str
    moves_with: str
    happy_result: str


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    action: str
    fix: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.trace_notes: list[str] = []

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

    def copy(self) -> "World":
        import copy as _copy
        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        return clone


def rhyme(*parts: str) -> str:
    return " ".join(parts)


def introduce(hero: Entity, friend: Entity, obj: Entity) -> str:
    return (
        f"In a bright green glen where the grass grew neat, "
        f"lived a power-ful elephant, strong on his feet. "
        f"He loved to help with a lift and a shove, "
        f"and he did it with kindness and big trunk love."
    )


def object_rhyme(obj: HeavyThing) -> str:
    return {
        "log": "A log by the brook, long, brown, and wide,",
        "cart": "A cart by the lane with a creaky old side,",
        "rock": "A rock on the path, round, gray, and slow,",
    }[obj.id]


SETTINGS = {
    "glen": Setting(place="the green glen", surface="soft grass", supports={"log", "cart", "rock"}),
    "lane": Setting(place="the sunny lane", surface="dusty road", supports={"cart", "rock"}),
    "brook": Setting(place="the brookside bank", surface="muddy edge", supports={"log", "rock"}),
}

HEAVY_THINGS = {
    "log": HeavyThing(
        id="log",
        label="log",
        phrase="a big old log",
        size="heavy",
        moves_with="a steady push and a helpful tug",
        happy_result="rolled aside for a clear path",
    ),
    "cart": HeavyThing(
        id="cart",
        label="cart",
        phrase="a squeaky little cart",
        size="heavy",
        moves_with="a careful pull and a strong, sure shove",
        happy_result="moved along with a merry squeak",
    ),
    "rock": HeavyThing(
        id="rock",
        label="rock",
        phrase="a round stone rock",
        size="heavy",
        moves_with="a rocking push and a lift in a groove",
        happy_result="nudged off the road and out of the way",
    ),
}

TOOLS = {
    "branch": Tool(
        id="branch",
        label="a long branch",
        phrase="a long, smooth branch",
        action="make a lever",
        fix="the object could tip and turn",
    ),
    "rope": Tool(
        id="rope",
        label="a soft rope",
        phrase="a soft rope loop",
        action="pull together",
        fix="the pull could be shared",
    ),
    "stone": Tool(
        id="stone",
        label="a flat stone",
        phrase="a flat, steady stone",
        action="make a ramp",
        fix="the heavy thing could slide",
    ),
}

GENTLE_NAMES = ["Milo", "Nina", "Tia", "Ollie", "Pippa", "Rani", "Juno", "Toby"]
FRIEND_TYPES = ["mouse", "rabbit", "deer", "bird"]
TRAITS = ["cheery", "brave", "tiny", "kind"]


@dataclass
class StoryParams:
    setting: str
    heavy: str
    tool: str
    hero_name: str
    friend_name: str
    friend_type: str
    trait: str
    seed: Optional[int] = None


def reasonableness_gate(setting: Setting, heavy: HeavyThing, tool: Tool) -> bool:
    if heavy.id not in setting.supports:
        return False
    if heavy.id == "log" and tool.id != "branch":
        return False
    if heavy.id == "cart" and tool.id != "rope":
        return False
    if heavy.id == "rock" and tool.id != "stone":
        return False
    return True


def explain_rejection(setting: Setting, heavy: HeavyThing, tool: Tool) -> str:
    return (
        f"(No story: {heavy.phrase} at {setting.place} does not fit with {tool.label}. "
        f"Try a matching pair so the elephant can solve the trouble in a fair and clear way.)"
    )


def build_world(params: StoryParams) -> World:
    setting = SETTINGS[params.setting]
    heavy = HEAVY_THINGS[params.heavy]
    tool = TOOLS[params.tool]

    world = World(setting)
    hero = world.add(Entity(id=params.hero_name, kind="character", type="elephant", label=params.hero_name))
    friend = world.add(Entity(id=params.friend_name, kind="character", type=params.friend_type, label=params.friend_name))
    obj = world.add(Entity(id=heavy.id, kind="thing", type=heavy.label, label=heavy.label, phrase=heavy.phrase, heavy=True))
    t = world.add(Entity(id=tool.id, kind="thing", type="tool", label=tool.label, phrase=tool.phrase, portable=True))

    world.facts.update(hero=hero, friend=friend, obj=obj, tool=t, heavy=heavy, setting=setting)
    return world


def simulate(world: World) -> None:
    hero: Entity = world.facts["hero"]
    friend: Entity = world.facts["friend"]
    obj: Entity = world.facts["obj"]
    heavy: HeavyThing = world.facts["heavy"]
    tool: Entity = world.facts["tool"]

    world.say(
        f"In {world.setting.place}, there was an elephant named {hero.id}, "
        f"with a trunk so strong and a heart so light."
    )
    world.say(
        f"He met {friend.id}, who frowned at {obj.phrase}, "
        f"for it blocked the path and stuck in place."
    )
    world.para()
    world.say(
        f"{hero.id} tried to move it with a push and a pry, "
        f"but the heavy thing only gave a sad old sigh."
    )
    hero.memes["worry"] += 1.0
    obj.meters["stuck"] += 1.0

    world.say(
        f"Then {friend.id} brought {tool.phrase}, and said, "
        f'"Let\'s use this just right."'
    )
    if heavy.id == "log":
        world.say(
            f"{hero.id} set the branch beneath the log with care, "
            f"and made a small lever in the air."
        )
    elif heavy.id == "cart":
        world.say(
            f"{hero.id} tied the rope and took a kind deep breath, "
            f"then pulled with a friend so the cart did its best."
        )
    else:
        world.say(
            f"{hero.id} laid the stone to make a smooth little slope, "
            f"and gave the round rock a rolling hope."
        )

    obj.meters["moved"] += 1.0
    obj.meters["stuck"] = 0.0
    hero.memes["joy"] += 1.0
    hero.memes["pride"] += 1.0
    friend.memes["joy"] += 1.0

    world.para()
    world.say(
        f"At last, the heavy thing moved with a happy sound, "
        f"and the path was clear all around."
    )
    world.say(
        f"{heavy.happy_result.capitalize()}, and {friend.id} cheered, "
        f"while {hero.id} gave a trumpet of delight. "
        f"With teamwork and rhythm, the day turned bright."
    )
    world.say(
        f"So the little friend skipped on, the elephant grinned, "
        f"and the glen felt warm where the good deed had been."
    )


def tell(params: StoryParams) -> World:
    world = build_world(params)
    simulate(world)
    return world


def generation_prompts(world: World) -> list[str]:
    hero: Entity = world.facts["hero"]
    heavy: HeavyThing = world.facts["heavy"]
    tool: Entity = world.facts["tool"]
    setting: Setting = world.facts["setting"]
    return [
        f'Write a rhyming story for young children about a power-ful elephant in {setting.place} who helps move {heavy.phrase}.',
        f"Tell a happy-ending tale where {hero.id} uses {tool.phrase} to solve a heavy problem with a friend.",
        f'Create a short story with soft rhyme, a kind elephant, and a bright ending about {heavy.phrase}.',
    ]


def story_qa(world: World) -> list[QAItem]:
    hero: Entity = world.facts["hero"]
    friend: Entity = world.facts["friend"]
    obj: Entity = world.facts["obj"]
    heavy: HeavyThing = world.facts["heavy"]
    tool: Entity = world.facts["tool"]
    setting: Setting = world.facts["setting"]

    return [
        QAItem(
            question=f"Who was the power-ful helper in the story?",
            answer=f"The power-ful helper was {hero.id}, the elephant. He used his strong trunk and kind heart to help.",
        ),
        QAItem(
            question=f"What blocked the path in {setting.place}?",
            answer=f"{obj.phrase} blocked the path and got stuck until the friends found a better way.",
        ),
        QAItem(
            question=f"What did {friend.id} bring to help?",
            answer=f"{friend.id} brought {tool.phrase}, which helped {hero.id} solve the problem in a safe, smart way.",
        ),
        QAItem(
            question="How did the story end?",
            answer=(
                f"It ended happily. The heavy thing moved, the path was clear, "
                f"and {hero.id} and {friend.id} felt glad and proud."
            ),
        ),
    ]


KNOWLEDGE = {
    "elephant": [
        (
            "What is an elephant?",
            "An elephant is a very big animal with a trunk, big ears, and strong legs.",
        ),
        (
            "Why can an elephant be helpful?",
            "An elephant can be helpful because it is strong, careful, and can lift or push heavy things.",
        ),
    ],
    "log": [
        (
            "What is a log?",
            "A log is a thick piece of a tree trunk, often cut or fallen down.",
        )
    ],
    "cart": [
        (
            "What is a cart?",
            "A cart is a small vehicle or wagon that can carry things and be pulled by a person or animal.",
        )
    ],
    "rope": [
        (
            "What does a rope do?",
            "A rope can be used to tie, pull, or help hold things together.",
        )
    ],
    "branch": [
        (
            "What can a branch be used for?",
            "A branch can sometimes be used as a stick, a lever, or a tool for simple play and work.",
        )
    ],
    "stone": [
        (
            "What is a stone?",
            "A stone is a hard piece of rock, and some stones are flat enough to help make a path smoother.",
        )
    ],
}

KNOWLEDGE_ORDER = ["elephant", "log", "cart", "rope", "branch", "stone"]


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = {world.facts["heavy"].id, world.facts["tool"].id, "elephant"}
    out: list[QAItem] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
            out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE[tag])
    return out


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
    lines.append("== (3) World knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if any(v for v in e.meters.values()):
            bits.append(f"meters={e.meters}")
        if any(v for v in e.memes.values()):
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
        for sup in sorted(SETTINGS[sid].supports):
            lines.append(asp.fact("supports", sid, sup))
    for hid, heavy in HEAVY_THINGS.items():
        lines.append(asp.fact("heavy", hid))
        lines.append(asp.fact("matches_tool", hid, heavy.moves_with.split()[0]))
    for tid, tool in TOOLS.items():
        lines.append(asp.fact("tool", tid))
    return "\n".join(lines)


ASP_RULES = r"""
valid(S,H,T) :- setting(S), heavy(H), tool(T), supports(S,H), match(H,T).
match(log,branch).
match(cart,rope).
match(rock,stone).
#show valid/3.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    clingo_set = set(asp_valid_combos())
    python_set = {
        (sid, hid, tid)
        for sid, setting in SETTINGS.items()
        for hid, heavy in HEAVY_THINGS.items()
        for tid, tool in TOOLS.items()
        if reasonableness_gate(setting, heavy, tool)
    }
    if clingo_set == python_set:
        print(f"OK: clingo gate matches Python gate ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and Python gates:")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


@dataclass
class StoryParams:
    setting: str
    heavy: str
    tool: str
    hero_name: str
    friend_name: str
    friend_type: str
    trait: str
    seed: Optional[int] = None


CURATED = [
    StoryParams("glen", "log", "branch", "Milo", "Pippa", "mouse", "cheery"),
    StoryParams("lane", "cart", "rope", "Nina", "Toby", "rabbit", "kind"),
    StoryParams("brook", "rock", "stone", "Juno", "Rani", "deer", "brave"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Power-ful elephant rhyming storyworld with a happy ending.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--heavy", choices=HEAVY_THINGS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--name")
    ap.add_argument("--friend-name")
    ap.add_argument("--friend-type", choices=["mouse", "rabbit", "deer", "bird"])
    ap.add_argument("--trait", choices=TRAITS)
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
    heavy = args.heavy or rng.choice(list(HEAVY_THINGS))
    tool = args.tool or rng.choice(list(TOOLS))
    if args.setting and args.heavy and args.tool:
        if not reasonableness_gate(SETTINGS[args.setting], HEAVY_THINGS[args.heavy], TOOLS[args.tool]):
            raise StoryError(explain_rejection(SETTINGS[args.setting], HEAVY_THINGS[args.heavy], TOOLS[args.tool]))
    valid_tools = [t for t in TOOLS if reasonableness_gate(SETTINGS[setting], HEAVY_THINGS[heavy], TOOLS[t])]
    if tool not in valid_tools:
        tool = rng.choice(valid_tools)
    hero_name = args.name or "Pomu"
    friend_name = args.friend_name or rng.choice(GENTLE_NAMES)
    friend_type = args.friend_type or rng.choice(FRIEND_TYPES)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(setting, heavy, tool, hero_name, friend_name, friend_type, trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        triples = asp_valid_combos()
        print(f"{len(triples)} compatible combos:\n")
        for s, h, t in triples:
            print(f"  {s:8} {h:8} {t:8}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero_name}: {p.heavy} with {p.tool} in {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
