#!/usr/bin/env python3
"""
storyworlds/worlds/subscription_sound_effects_teamwork_cautionary_heartwarming.py
=================================================================================

A small, self-contained story world about a child, a subscription box, and a
careful teamwork moment that ends warmly.

Seed tale premise:
- A child is excited about a monthly subscription box.
- The box makes fun sound effects when it arrives and opens.
- The parent warns the child to be cautious with one fragile surprise.
- The child and a helper work together, slow down, and enjoy the result.

This world models:
- Physical state: a subscription box, tape, fragile items, and an opened box.
- Emotional state: excitement, caution, teamwork, relief, and warmth.
- Narrative progression: arrival -> caution -> careful teamwork -> happy ending.

The prose is driven by the simulated world state, not a frozen template.
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
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    plural: bool = False
    fragile: bool = False
    openable: bool = False
    opened: bool = False
    delivered: bool = False
    shared: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "sister"}
        male = {"boy", "father", "dad", "man", "brother"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


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

    def copy(self) -> "World":
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class StoryParams:
    name: str
    gender: str
    helper: str
    parent: str
    subscription: str
    package: str
    seed: Optional[int] = None


@dataclass
class Setting:
    place: str = "the front steps"


@dataclass
class Subscription:
    id: str
    label: str
    service: str
    arrival_sound: str
    opening_sound: str
    theme: str
    fragile_item: str
    fragile_label: str
    caution: str
    teamwork_tool: str
    teamwork_action: str
    ending_image: str


SETTINGS = {
    "front_steps": Setting(place="the front steps"),
    "kitchen_table": Setting(place="the kitchen table"),
    "porch": Setting(place="the porch"),
}

SUBSCRIPTIONS = {
    "science": Subscription(
        id="science",
        label="science subscription box",
        service="subscription",
        arrival_sound="ding-dong!",
        opening_sound="snip-snip!",
        theme="science surprises",
        fragile_item="a tiny glass prism",
        fragile_label="glass prism",
        caution="careful",
        teamwork_tool="soft cloth",
        teamwork_action="lifted it together",
        ending_image="the prism made a rainbow on the wall",
    ),
    "art": Subscription(
        id="art",
        label="art subscription box",
        service="subscription",
        arrival_sound="thump-thump!",
        opening_sound="zip-zip!",
        theme="art supplies",
        fragile_item="a little jar of glitter paint",
        fragile_label="jar of glitter paint",
        caution="gentle",
        teamwork_tool="paper tray",
        teamwork_action="carried it together",
        ending_image="the paint jar sparkled like a tiny star",
    ),
    "music": Subscription(
        id="music",
        label="music subscription box",
        service="subscription",
        arrival_sound="tap-tap!",
        opening_sound="click!",
        theme="music surprises",
        fragile_item="a small tuning fork",
        fragile_label="tuning fork",
        caution="steady",
        teamwork_tool="padded box",
        teamwork_action="set it down together",
        ending_image="the tuning fork hummed softly in the light",
    ),
}

HELPERS = {
    "sister": {"type": "sister", "name_pool": ["Mia", "Lily", "Nora", "Ella"]},
    "brother": {"type": "brother", "name_pool": ["Ben", "Noah", "Leo", "Max"]},
}


class WorldError(StoryError):
    pass


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Story world: subscription, sound effects, teamwork, caution, heartwarming.")
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper", choices=list(HELPERS))
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--subscription", choices=list(SUBSCRIPTIONS))
    ap.add_argument("--package", choices=list(SETTINGS))
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
    sub_id = args.subscription or rng.choice(list(SUBSCRIPTIONS))
    pack = args.package or rng.choice(list(SETTINGS))
    gender = args.gender or rng.choice(["girl", "boy"])
    helper = args.helper or rng.choice(list(HELPERS))
    parent = args.parent or rng.choice(["mother", "father"])
    name = args.name or rng.choice(["Ava", "Maya", "Theo", "Finn", "Iris", "Ruby", "Jack", "Owen"])
    return StoryParams(
        name=name,
        gender=gender,
        helper=helper,
        parent=parent,
        subscription=sub_id,
        package=pack,
    )


def _title_name(ent: Entity) -> str:
    return ent.id


def _build_world(params: StoryParams) -> World:
    if params.subscription not in SUBSCRIPTIONS:
        raise WorldError("Unknown subscription type.")
    if params.helper not in HELPERS:
        raise WorldError("Unknown helper.")
    world = World()
    sub = SUBSCRIPTIONS[params.subscription]
    setting = SETTINGS[params.package]

    hero = world.add(Entity(id=params.name, kind="character", type=params.gender, meters={"joy": 0.0}, memes={"excitement": 0.0, "caution": 0.0, "warmth": 0.0}))
    helper_info = HELPERS[params.helper]
    helper = world.add(Entity(id=helper_info["name_pool"][0], kind="character", type=helper_info["type"], meters={"joy": 0.0}, memes={"teamwork": 0.0, "patience": 0.0}))
    parent = world.add(Entity(id=params.parent.title(), kind="character", type=params.parent, meters={"work": 0.0}, memes={"worry": 0.0, "relief": 0.0}))
    box = world.add(Entity(id="box", type="box", label=sub.label, phrase=f"a new {sub.label}", owner=hero.id, delivered=False, openable=True, opened=False))
    fragile = world.add(Entity(id="fragile", type="object", label=sub.fragile_label, phrase=f"the {sub.fragile_label}", owner=hero.id, fragile=True))
    tool = world.add(Entity(id="tool", type="thing", label=sub.teamwork_tool, phrase=f"a {sub.teamwork_tool}", owner=helper.id))

    world.facts = {
        "hero": hero,
        "helper": helper,
        "parent": parent,
        "box": box,
        "fragile": fragile,
        "tool": tool,
        "subscription": sub,
        "setting": setting,
    }
    return world


def _arrive(world: World) -> None:
    f = world.facts
    hero, parent, box, sub, setting = f["hero"], f["parent"], f["box"], f["subscription"], f["setting"]
    hero.memes["excitement"] += 1
    box.delivered = True
    world.say(f"One afternoon, a {sub.service} box arrived at {setting.place}. {sub.arrival_sound} the door seemed to say.")
    world.say(f"{hero.id} bounced over right away because the box was full of {sub.theme}.")
    parent.memes["worry"] += 1
    world.say(f"{parent.id} smiled, but {parent.pronoun('possessive')} eyes stayed on the box. \"Let's be {sub.caution},\" {parent.pronoun()} said.")


def _warn_and_careful(world: World) -> None:
    f = world.facts
    hero, helper, parent, fragile, sub = f["hero"], f["helper"], f["parent"], f["fragile"], f["subscription"]
    hero.memes["caution"] += 1
    world.say(f"When the tape made a loud {sub.opening_sound}, {parent.id} held up a hand.")
    world.say(f"\"Easy,\" {parent.id} said. \"There is {fragile.phrase} inside, and it needs careful hands.\"")
    hero.memes["excitement"] += 1
    helper.memes["patience"] += 1
    world.say(f"{hero.id} nodded and took a slow breath. {helper.id} came closer, ready to help.")


def _teamwork_open(world: World) -> None:
    f = world.facts
    hero, helper, parent, fragile, tool, sub = f["hero"], f["helper"], f["parent"], f["fragile"], f["tool"], f["subscription"]
    fragile.meters["safety"] = 1.0
    helper.memes["teamwork"] += 1
    hero.memes["warmth"] += 1
    world.say(f"Together they used the {tool.label} and {sub.teamwork_action} with slow, steady hands.")
    world.say(f"With a soft {sub.opening_sound}, the box opened without a bump.")
    fragile.opened = True
    world.say(f"Inside was {fragile.phrase}, wrapped up safely and waiting to shine.")


def _resolve(world: World) -> None:
    f = world.facts
    hero, helper, parent, fragile, sub = f["hero"], f["helper"], f["parent"], f["fragile"], f["subscription"]
    hero.meters["joy"] += 1
    helper.meters["joy"] = helper.meters.get("joy", 0.0) + 1
    parent.memes["relief"] += 1
    world.say(f"{hero.id} grinned, and {helper.id} grinned too.")
    world.say(f"{parent.id} let out a happy sigh because everyone had been so careful.")
    world.say(f"In the end, {sub.ending_image}, and {hero.id} felt proud of how well they worked together.")


def tell(params: StoryParams) -> World:
    world = _build_world(params)
    _arrive(world)
    world.para()
    _warn_and_careful(world)
    _teamwork_open(world)
    world.para()
    _resolve(world)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, sub = f["hero"], f["subscription"]
    return [
        f'Write a heartwarming story about a child and a {sub.service} box with fun sound effects.',
        f"Tell a gentle cautionary story where {hero.id} opens a {sub.label} with help from a sibling.",
        f"Write a short story about teamwork, careful hands, and a surprise from a {sub.label}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, helper, parent, box, fragile, sub = f["hero"], f["helper"], f["parent"], f["box"], f["fragile"], f["subscription"]
    return [
        QAItem(
            question=f"What arrived for {hero.id} at the beginning of the story?",
            answer=f"A {sub.service} box arrived for {hero.id} at the front steps, and it was full of {sub.theme}.",
        ),
        QAItem(
            question=f"Why did {parent.id} tell {hero.id} to be careful when opening the box?",
            answer=f"{parent.id} warned {hero.id} to be careful because there was {fragile.phrase} inside, and it could get hurt if the box was rushed.",
        ),
        QAItem(
            question=f"How did {hero.id} and {helper.id} open the box safely?",
            answer=f"They worked together, used the {f['tool'].label}, and opened the {sub.label} with slow, steady hands.",
        ),
        QAItem(
            question=f"What was the happy ending of the story?",
            answer=f"The fragile surprise stayed safe, everyone felt proud, and {hero.id} got to enjoy the {sub.label} with the family.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a subscription box?",
            answer="A subscription box is a package that arrives again and again, usually on a regular schedule, and it often has a surprise inside.",
        ),
        QAItem(
            question="Why should fragile things be handled carefully?",
            answer="Fragile things can break if they are bumped, dropped, or squeezed too hard, so gentle hands help keep them safe.",
        ),
        QAItem(
            question="What does teamwork mean?",
            answer="Teamwork means people help each other and do a task together so it becomes easier and safer.",
        ),
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
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.label:
            bits.append(f"label={e.label}")
        if e.fragile:
            bits.append("fragile=True")
        if e.delivered:
            bits.append("delivered=True")
        if e.opened:
            bits.append("opened=True")
        lines.append(f"  {e.id:10} ({e.kind:9}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
arrival(box) :- delivered(box).
careful_story(H) :- cautious(H), teamwork(H).
safe_open(B) :- arrival(B), opened(B), careful(B).
heartwarming(H) :- safe_open(B), enjoys(H,B).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SUBSCRIPTIONS:
        lines.append(asp.fact("subscription", sid))
    for kid in HELPERS:
        lines.append(asp.fact("helper_kind", kid))
    for pname in SETTINGS:
        lines.append(asp.fact("place", pname))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    try:
        import asp
    except Exception as exc:
        print(f"ASP unavailable: {exc}")
        return 1
    model = asp.one_model(asp_program("#show arrival/1. #show safe_open/1. #show heartwarming/1."))
    _ = model
    print("OK: ASP twin loads and solves a trivial program.")
    return 0


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


CURATED = [
    StoryParams(name="Mia", gender="girl", helper="brother", parent="mother", subscription="science", package="front_steps"),
    StoryParams(name="Leo", gender="boy", helper="sister", parent="father", subscription="art", package="kitchen_table"),
    StoryParams(name="Nora", gender="girl", helper="brother", parent="mother", subscription="music", package="porch"),
]


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
        print(asp_program("#show arrival/1. #show safe_open/1. #show heartwarming/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("3 subscription kinds are available via ASP twin.")
        for key, sub in SUBSCRIPTIONS.items():
            print(f"  {key}: {sub.label}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            seed = base_seed + i
            i += 1
            params = resolve_params(args, random.Random(seed))
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
            header = f"### {p.name}: {p.subscription} subscription at {p.package}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
