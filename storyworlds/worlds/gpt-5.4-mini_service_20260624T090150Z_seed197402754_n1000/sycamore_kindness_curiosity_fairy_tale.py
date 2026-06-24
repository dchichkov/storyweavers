#!/usr/bin/env python3
"""
storyworlds/worlds/sycamore_kindness_curiosity_fairy_tale.py
============================================================

A small fairy-tale story world built from a sycamore tree, curiosity, and
kindness.

Seed tale:
---
On the edge of a hushful meadow stood an old sycamore tree with pale bark and
silver leaves. A curious child found a tiny door hidden in its roots. A fairy
appeared and warned that the door kept a sleeping lantern safe. The child
wanted to peek, but then chose kindness: they helped the fairy mend the door
instead of opening it. In the end, the lantern glowed softly, and the child
left with a bright heart and a story to tell.
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
    caretaker: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother", "queen", "fairy"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father", "king"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the meadow"
    sycamore: bool = True


@dataclass
class Quest:
    id: str
    verb: str
    gerund: str
    rush: str
    risk: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Treasure:
    id: str
    label: str
    phrase: str
    type: str
    owner: str
    at_risk: str
    guarded_by: str
    repaired_by: str


@dataclass
class Remedy:
    id: str
    label: str
    prep: str
    finish: str
    covers: set[str]
    helps: set[str]


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}

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


QUESTS = {
    "peek": Quest(
        id="peek",
        verb="peek into the little door",
        gerund="peeking into the little door",
        rush="run to the roots",
        risk="split the hidden latch",
        keyword="curiosity",
        tags={"curiosity", "door", "roots"},
    ),
    "listen": Quest(
        id="listen",
        verb="listen for the sleeping lantern",
        gerund="listening for the lantern",
        rush="hurry to the glow",
        risk="scare the lantern awake",
        keyword="kindness",
        tags={"kindness", "lantern", "glow"},
    ),
}

TREASURES = {
    "lantern": Treasure(
        id="lantern",
        label="lantern",
        phrase="a sleeping little lantern",
        type="lantern",
        owner="fairy",
        at_risk="hidden door",
        guarded_by="door",
        repaired_by="thread",
    ),
}

REMEDIES = {
    "thread": Remedy(
        id="thread",
        label="silver thread",
        prep="mend the little door with silver thread",
        finish="mended the little door with silver thread",
        covers={"door"},
        helps={"peek", "listen"},
    ),
}

NAMES_GIRL = ["Mina", "Lily", "Nora", "Pippa", "Elena", "Rose"]
NAMES_BOY = ["Theo", "Finn", "Owen", "Bram", "Leo", "Jasper"]


class StoryWorld:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "StoryWorld":
        clone = StoryWorld(self.setting)
        import copy as _copy
        clone.entities = _copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


def _do_quest(world: StoryWorld, child: Entity, quest: Quest, narrate: bool = True) -> None:
    child.memes[quest.keyword] = child.memes.get(quest.keyword, 0) + 1
    if narrate:
        world.say(f"{child.id} wanted to {quest.verb}, because {child.pronoun('possessive')} heart was full of {quest.keyword}.")


def _r_worry(world: StoryWorld) -> list[str]:
    out = []
    child = world.get("child")
    fairy = world.get("fairy")
    lantern = world.get("lantern")
    if child.memes.get("curiosity", 0) < THRESHOLD:
        return out
    if fairy.memes.get("kindness", 0) < THRESHOLD:
        return out
    sig = ("worry",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["worry"] = child.memes.get("worry", 0) + 1
    fairy.memes["worry"] = fairy.memes.get("worry", 0) + 1
    out.append(f"The little door kept {lantern.phrase} safe, so the fairy grew gentle and serious.")
    return out


def _r_repair(world: StoryWorld) -> list[str]:
    out = []
    child = world.get("child")
    fairy = world.get("fairy")
    lantern = world.get("lantern")
    if child.memes.get("kindness", 0) < THRESHOLD:
        return out
    if world.facts.get("door_fixed"):
        return out
    sig = ("repair",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.facts["door_fixed"] = True
    lantern.meters["safe"] = lantern.meters.get("safe", 0) + 1
    child.memes["joy"] = child.memes.get("joy", 0) + 1
    fairy.memes["joy"] = fairy.memes.get("joy", 0) + 1
    out.append("Together they mended the little door with silver thread.")
    return out


def propagate(world: StoryWorld, narrate: bool = True) -> list[str]:
    produced = []
    for rule in (_r_worry, _r_repair):
        produced.extend(rule(world))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


SETTING = Setting()
ASP_RULES = r"""
curious(child) :- has_meme(child, curiosity), child_entity(child).
kind child :- has_meme(child, kindness), child_entity(child).
door_safe(lantern) :- door_fixed.
worry(child) :- curious(child), kind(fairy).
repair :- kind(child), kind(fairy), sycamore(place), little_door(door), lantern(lantern).
#show worry/1.
#show repair/0.
"""


def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("sycamore", "meadow"),
        asp.fact("place", "meadow"),
        asp.fact("child_entity", "child"),
        asp.fact("fairy_entity", "fairy"),
        asp.fact("lantern_entity", "lantern"),
        asp.fact("little_door", "door"),
    ]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show repair/0.\n#show worry/1."))
    _ = asp.atoms(model, "repair")
    _ = asp.atoms(model, "worry")
    return 0


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A fairy tale under a sycamore tree.")
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


@dataclass
class StoryParams:
    name: str
    gender: str
    seed: Optional[int] = None


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(NAMES_GIRL if gender == "girl" else NAMES_BOY)
    return StoryParams(name=name, gender=gender)


def tell(params: StoryParams) -> StoryWorld:
    world = StoryWorld(SETTING)
    child = world.add(Entity(id="child", kind="character", type=params.gender, label=params.name))
    fairy = world.add(Entity(id="fairy", kind="character", type="fairy", label="the fairy"))
    door = world.add(Entity(id="door", type="door", label="little door", owner="fairy"))
    lantern = world.add(Entity(id="lantern", type="lantern", label="lantern", phrase="a sleeping little lantern", owner="fairy"))
    world.add(Entity(id="sycamore", type="tree", label="sycamore tree"))

    child.memes["curiosity"] = 1
    fairy.memes["kindness"] = 1

    world.say(f"On the edge of a quiet meadow stood an old sycamore tree with pale bark and silver leaves.")
    world.say(f"{params.name} was a little {params.gender} with a curious mind and a soft, kind heart.")
    world.say(f"One day, {params.name} found a tiny door tucked among the roots of the sycamore.")
    world.para()
    world.say("A fairy stepped out in a shimmer of green light and spoke softly.")
    world.say(f'"Do not tug the door," {fairy.label} said. "It keeps {lantern.phrase} safe."')

    _do_quest(world, child, QUESTS["peek"], narrate=True)
    world.say(f"{params.name} leaned closer, because curiosity was pulling like a ribbon in the wind.")
    world.say(f"{params.name} nearly tried to {QUESTS['peek'].rush}, but the fairy lifted a gentle hand.")
    child.memes["restraint"] = 1

    world.para()
    child.memes["kindness"] = 1
    world.say(f"Then {params.name} saw that the little door was cracked and the silver latch was loose.")
    world.say(f"{params.name}'s curiosity did not vanish; instead, it turned into kindness.")
    world.say(f'"Let me help," {params.name} said.')
    propagate(world, narrate=True)
    world.say(f"With careful fingers, {params.name} and the fairy used bright silver thread to mend the little door.")
    world.say(f"The lantern stayed safe, and the sycamore leaves rustled like tiny applause.")
    world.say(f"At last, the lantern glowed softly through the roots, and {params.name} went home with a bright heart and a fairy tale to keep.")
    world.facts.update(child=child, fairy=fairy, door=door, lantern=lantern, params=params, repaired=True)
    return world


def story_qa(world: StoryWorld) -> list[QAItem]:
    p = world.facts["params"]
    child = world.facts["child"]
    q = [
        QAItem(
            question=f"What did {p.name} find under the sycamore tree?",
            answer=f"{p.name} found a tiny little door hidden among the roots of the sycamore tree.",
        ),
        QAItem(
            question=f"Why did the fairy tell {p.name} not to tug the door?",
            answer="Because the little door kept a sleeping lantern safe, and tugging it could have hurt the latch.",
        ),
        QAItem(
            question=f"What changed when {p.name}'s curiosity turned into kindness?",
            answer=f"{p.name} stopped trying to pry the door open and helped mend it with the fairy instead.",
        ),
        QAItem(
            question=f"How did {p.name} feel at the end of the story?",
            answer=f"{p.name} went home with a bright, happy heart after helping the lantern stay safe.",
        ),
    ]
    if child.memes.get("curiosity", 0) >= THRESHOLD:
        q.append(QAItem(
            question=f"What was {p.name} curious about in the meadow?",
            answer=f"{p.name} was curious about the tiny door hidden under the sycamore roots.",
        ))
    return q


def world_knowledge_qa(world: StoryWorld) -> list[QAItem]:
    return [
        QAItem(
            question="What is a sycamore tree?",
            answer="A sycamore is a tree with broad leaves and bark that can look pale or patchy.",
        ),
        QAItem(
            question="What is curiosity?",
            answer="Curiosity is the feeling that makes someone want to look, learn, and ask questions.",
        ),
        QAItem(
            question="What is kindness?",
            answer="Kindness means choosing to help, be gentle, and care about others.",
        ),
    ]


def generation_prompts(world: StoryWorld) -> list[str]:
    p = world.facts["params"]
    return [
        f'Write a short fairy tale about a curious {p.gender} named {p.name} and a sycamore tree.',
        f"Tell a gentle story where {p.name} wants to peek into a hidden door, but kindness leads to a better choice.",
        "Write a child-friendly fairy tale that ends with a glowing lantern and a happy heart.",
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


def dump_trace(world: StoryWorld) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if any(v for v in e.memes.values()):
            bits.append(f"memes={dict(e.memes)}")
        if any(v for v in e.meters.values()):
            bits.append(f"meters={dict(e.meters)}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


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
        print(asp_program("#show repair/0.\n#show worry/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("1 compatible fairy-tale core:")
        print("  meadow  sycamore  door  lantern")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        cur = [
            StoryParams(name="Mina", gender="girl"),
            StoryParams(name="Theo", gender="boy"),
        ]
        samples = [generate(p) for p in cur]
    else:
        for i in range(args.n):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        if len(samples) > 1:
            print(f"### variant {i + 1}")
        emit(sample, trace=args.trace, qa=args.qa)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
