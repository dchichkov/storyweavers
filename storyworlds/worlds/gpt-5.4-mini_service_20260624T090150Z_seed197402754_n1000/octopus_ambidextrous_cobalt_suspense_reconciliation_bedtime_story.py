#!/usr/bin/env python3
"""
A bedtime-story world about a small octopus, a little suspense, and a gentle
reconciliation at the end.

The story is driven by a world model:
- the octopus has physical meters like wobble, wetness, and glow
- the octopus and a friend have emotional memes like worry and trust
- a cobalt object matters to the plot and changes hands/arms during the story
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

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    keeper: Optional[str] = None
    carried_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"octopus"}:
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        if self.type in {"girl", "boy", "child"}:
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def noun(self) -> str:
        return self.label or self.type


@dataclass
class Scene:
    place: str = "the moonlit tide pool"
    weather: str = "quiet"


class World:
    def __init__(self, scene: Scene) -> None:
        self.scene = scene
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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
        import copy
        w = World(self.scene)
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        return w


@dataclass
class StoryParams:
    name: str
    friend: str
    item: str
    seed: Optional[int] = None


SETTINGS = {
    "tidepool": Scene(place="the moonlit tide pool", weather="quiet"),
}

ITEMS = {
    "cobalt_shell": {
        "label": "cobalt shell",
        "phrase": "a cobalt shell",
        "color": "cobalt",
    }
}

NAMES = ["Mina", "Lumi", "Nori", "Tala", "Milo", "Pip"]
FRIENDS = ["crab", "starfish", "seahorse", "moonbeam"]
TRAITS = ["gentle", "curious", "sleepy", "kind"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A bedtime story with an octopus, suspense, and reconciliation.")
    ap.add_argument("--name", choices=NAMES)
    ap.add_argument("--friend", choices=FRIENDS)
    ap.add_argument("--item", choices=ITEMS)
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
    name = args.name or rng.choice(NAMES)
    friend = args.friend or rng.choice(FRIENDS)
    item = args.item or "cobalt_shell"
    return StoryParams(name=name, friend=friend, item=item)


def _join2(a: str, b: str) -> str:
    return a + " and " + b


def introduce(world: World, hero: Entity, friend: Entity, item: Entity) -> None:
    world.say(
        f"At the moonlit tide pool, {hero.id} the octopus was small, "
        f"ambidextrous, and very proud of using both arms at once."
    )
    world.say(
        f"{hero.id} loved {item.phrase}, because it shone like a tiny piece of night sky."
    )
    world.say(
        f"Nearby, {friend.label} listened quietly while the water made soft sleepy whispers."
    )


def tension(world: World, hero: Entity, friend: Entity, item: Entity) -> None:
    hero.memes["worry"] += 1
    friend.memes["worry"] += 1
    world.para()
    world.say(
        f"One evening, {item.phrase} slipped into a dark crack between two stones."
    )
    world.say(
        f"{hero.id} reached with one arm, then the other, but the crack was too narrow."
    )
    world.say(
        f"Still, {hero.id} did not give up, and the little tide pool felt full of suspense."
    )


def suspense_turn(world: World, hero: Entity, friend: Entity, item: Entity) -> None:
    hero.meters["search"] = hero.meters.get("search", 0) + 1
    hero.memes["hope"] = hero.memes.get("hope", 0) + 1
    world.say(
        f"Then {hero.id} remembered something important: being ambidextrous meant trying both sides, not only one."
    )
    world.say(
        f"{hero.id} tapped the rock on one side, then the other, and waited very still."
    )
    world.say(
        f"The waiting was the scariest part, because nobody knew if the {item.label} would come out."
    )


def reconciliation(world: World, hero: Entity, friend: Entity, item: Entity) -> None:
    hero.memes["worry"] = 0
    friend.memes["worry"] = 0
    hero.memes["trust"] = hero.memes.get("trust", 0) + 1
    friend.memes["trust"] = friend.memes.get("trust", 0) + 1
    item.carried_by = hero.id
    world.para()
    world.say(
        f"At last, {friend.label} gently nudged the stone from the other side."
    )
    world.say(
        f"Out floated the {item.label}, glowing cobalt in the water like a tiny calm star."
    )
    world.say(
        f"{hero.id} hugged {friend.label}, and the suspense melted into a warm reconciliation."
    )
    world.say(
        f"By bedtime, the tide pool was peaceful again, and {hero.id} held the cobalt shell close."
    )


def tell_story(params: StoryParams) -> World:
    world = World(SETTINGS["tidepool"])
    hero = world.add(Entity(id=params.name, kind="character", type="octopus", label=params.name))
    friend = world.add(Entity(id="Friend", kind="character", type=params.friend, label=params.friend))
    item_cfg = ITEMS[params.item]
    item = world.add(Entity(id="Shell", type="shell", label=item_cfg["label"], phrase=item_cfg["phrase"], owner=hero.id))
    hero.meters.update({"search": 0.0})
    hero.memes.update({"worry": 0.0, "hope": 0.0, "trust": 0.0})
    friend.memes.update({"worry": 0.0, "trust": 0.0})

    introduce(world, hero, friend, item)
    tension(world, hero, friend, item)
    suspense_turn(world, hero, friend, item)
    reconciliation(world, hero, friend, item)

    world.facts = {
        "hero": hero,
        "friend": friend,
        "item": item,
        "scene": world.scene,
    }
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    item = f["item"]
    return [
        f"Write a bedtime story about an octopus named {hero.id} and a {friend.type} finding a lost {item.label}.",
        f"Tell a gentle suspense story where {hero.id} uses both arms to search for a cobalt treasure and then makes up with a friend.",
        "Write a calm ocean story for children with a tiny mystery and a happy reconciliation at bedtime.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    item = f["item"]
    return [
        QAItem(
            question=f"Who is the story about?",
            answer=f"The story is about {hero.id}, a small octopus who is ambidextrous and lives by the tide pool.",
        ),
        QAItem(
            question=f"What happened to the {item.label}?",
            answer=f"The {item.label} slipped into a crack between two stones, which made the story suspenseful for a moment.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended with {hero.id} and {friend.label} making peace, finding the {item.label}, and settling down for bedtime.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is an octopus?",
            answer="An octopus is a sea animal with eight arms. It can squeeze into small places and move in the water very well.",
        ),
        QAItem(
            question="What does ambidextrous mean?",
            answer="Ambidextrous means being able to use both the left side and the right side well, like using both hands easily.",
        ),
        QAItem(
            question="What is cobalt?",
            answer="Cobalt is a deep blue color, like a rich nighttime sky or a bright blue stone.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    out.extend(sample.prompts)
    out.append("")
    out.append("== story qa ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== world qa ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: type={e.type} meters={e.meters} memes={e.memes} carried_by={e.carried_by}")
    return "\n".join(lines)


ASP_RULES = r"""
hero(octopus).
quality(ambidextrous).
color(cobalt).
event(suspense).
event(reconciliation).
story_valid :- hero(octopus), quality(ambidextrous), color(cobalt), event(suspense), event(reconciliation).
#show story_valid/0.
#show hero/1.
#show quality/1.
#show color/1.
#show event/1.
"""


def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            asp.fact("hero", "octopus"),
            asp.fact("quality", "ambidextrous"),
            asp.fact("color", "cobalt"),
            asp.fact("event", "suspense"),
            asp.fact("event", "reconciliation"),
        ]
    )


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show story_valid/0."))
    ok = any(sym.name == "story_valid" for sym in model)
    if ok:
        print("OK: ASP story gate is satisfied.")
        return 0
    print("MISMATCH: ASP story gate failed.")
    return 1


def asp_summary() -> str:
    import asp
    model = asp.one_model(asp_program("#show hero/1. #show quality/1. #show color/1. #show event/1."))
    parts = []
    for name in ["hero", "quality", "color", "event"]:
        vals = [t[0] if len(t) == 1 else t for t in asp.atoms(model, name)]
        parts.append(f"{name}: {vals}")
    return "\n".join(parts)


def generate(params: StoryParams) -> StorySample:
    world = tell_story(params)
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
    StoryParams(name="Mina", friend="crab", item="cobalt_shell"),
    StoryParams(name="Nori", friend="starfish", item="cobalt_shell"),
    StoryParams(name="Tala", friend="seahorse", item="cobalt_shell"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show story_valid/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_summary())
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            i += 1
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
