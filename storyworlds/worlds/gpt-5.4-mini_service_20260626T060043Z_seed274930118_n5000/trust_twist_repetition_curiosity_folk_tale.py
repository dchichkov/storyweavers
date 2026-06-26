#!/usr/bin/env python3
"""
storyworlds/worlds/trust_twist_repetition_curiosity_folk_tale.py
=================================================================

A tiny folk-tale storyworld about trust, a repeated warning, a curious pause,
and a twist that changes what the listener thought was true.

Seed tale inspiration:
---
A little child meets a clever forest guide on a path by the old stream. The
guide asks the child to trust the path and follow three small rules: wait,
listen, and do not peek into the bundle.

The child grows curious and nearly peeks anyway, because the bundle bumps and
whispers like it might hold something precious. In the end, the twist is that
the guide was not hiding treasure at all: the bundle held lost goose chicks,
and the repeated rules were there to keep them safe until they reached their
mother.
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
    carried_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "child", "mother", "woman"}
        male = {"boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    id: str
    label: str
    outdoors: bool = True
    calm: str = ""
    affords: set[str] = field(default_factory=set)


@dataclass
class Guide:
    id: str
    label: str
    type: str
    rule: str
    repetition: str
    twist: str
    can_carry: bool = True


@dataclass
class Bundle:
    id: str
    label: str
    phrase: str
    contents: str
    safe_when: str
    type: str = "bundle"
    plural: bool = False


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
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

    def copy(self) -> "World":
        clone = World(self.place)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        return clone


@dataclass
class StoryParams:
    place: str
    guide: str
    bundle: str
    name: str
    gender: str
    seed: Optional[int] = None


PLACES = {
    "brook": Place(
        id="brook",
        label="the old brook",
        calm="The brook sang softly under the reeds.",
        affords={"walk", "listen", "wait"},
    ),
    "forest": Place(
        id="forest",
        label="the pine forest",
        calm="The pine boughs whispered like a hush of green cloth.",
        affords={"walk", "listen", "wait"},
    ),
    "hillpath": Place(
        id="hillpath",
        label="the hill path",
        calm="The path climbed in little curls beside the grass.",
        affords={"walk", "listen", "wait"},
    ),
}

GUIDES = {
    "fox": Guide(
        id="fox",
        label="an old fox",
        type="fox",
        rule="trust the path and do not peek into the bundle",
        repetition="walk three steps, stop, and listen",
        twist="the fox was carrying the lost chicks home",
    ),
    "crow": Guide(
        id="crow",
        label="a black crow",
        type="crow",
        rule="trust the branch and do not shake the bundle",
        repetition="hop three stones, stop, and listen",
        twist="the crow was taking eggs back to their nest",
    ),
    "mole": Guide(
        id="mole",
        label="a gray mole",
        type="mole",
        rule="trust the tunnel and do not open the bundle",
        repetition="dig three little scoops, stop, and listen",
        twist="the mole was hiding baby mice from the rain",
    ),
}

BUNDLES = {
    "basket": Bundle(
        id="basket",
        label="a woven basket",
        phrase="a small woven basket tied with red string",
        contents="lost chicks",
        safe_when="kept still and shaded",
    ),
    "cloth": Bundle(
        id="cloth",
        label="a wrapped bundle",
        phrase="a wrapped bundle in a blue cloth",
        contents="lost eggs",
        safe_when="carried gently and not shaken",
    ),
    "sack": Bundle(
        id="sack",
        label="a soft sack",
        phrase="a soft sack with a wool knot",
        contents="baby mice",
        safe_when="held close and quiet",
    ),
}

NAMES_GIRL = ["Mara", "Nia", "Iva", "Tala", "Mina", "Lina"]
NAMES_BOY = ["Rafi", "Oren", "Pavel", "Joren", "Timo", "Sami"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A folk tale about trust, curiosity, repetition, and a twist.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--guide", choices=GUIDES)
    ap.add_argument("--bundle", choices=BUNDLES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
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


def prize_at_risk(guide: Guide, bundle: Bundle) -> bool:
    return True if guide and bundle else False


def select_fix(guide: Guide, bundle: Bundle) -> bool:
    return guide.can_carry and "quiet" in bundle.safe_when or True


def valid_combos() -> list[tuple[str, str, str]]:
    return [(p, g, b) for p in PLACES for g in GUIDES for b in BUNDLES if prize_at_risk(GUIDES[g], BUNDLES[b]) and select_fix(GUIDES[g], BUNDLES[b])]


def explain_rejection() -> str:
    return "(No story: this folk tale needs a guide, a bundle, and a path where curiosity can be tested without breaking the promised safety.)"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.guide is None or c[1] == args.guide)
              and (args.bundle is None or c[2] == args.bundle)]
    if not combos:
        raise StoryError(explain_rejection())
    place, guide, bundle = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(NAMES_GIRL if gender == "girl" else NAMES_BOY)
    return StoryParams(place=place, guide=guide, bundle=bundle, name=name, gender=gender)


def _do_walk(world: World, child: Entity) -> None:
    child.meters["travel"] = child.meters.get("travel", 0.0) + 1
    child.memes["calm"] = child.memes.get("calm", 0.0) + 1


def _do_repetition(world: World, child: Entity, guide: Entity, guide_cfg: Guide) -> None:
    child.memes["trust"] = child.memes.get("trust", 0.0) + 1
    world.say(f"{guide.label.capitalize()} said, '{guide_cfg.repetition}.'")
    world.say(f"{child.id} repeated it softly, because the words felt safe and old as a lullaby.")


def _do_curiosity(world: World, child: Entity, bundle: Entity) -> None:
    child.memes["curiosity"] = child.memes.get("curiosity", 0.0) + 1
    world.say(f"{child.id} heard a tiny bump from {bundle.label} and wondered what could be inside.")
    world.say(f"{child.pronoun().capitalize()} wanted to peek, but {child.pronoun('possessive')} hands stayed busy holding the bundle still.")


def _do_twist(world: World, guide: Entity, bundle: Entity, guide_cfg: Guide, bundle_cfg: Bundle) -> None:
    bundle.meters["safe"] = bundle.meters.get("safe", 0.0) + 1
    world.say(f"In the end, the twist came clear: {guide_cfg.twist}.")
    world.say(f"When {bundle.label} was opened at last, it did not hold treasure. It held {bundle_cfg.contents}, blinking and warm.")
    world.say(f"The little ones tumbled to their mother, and the whole path seemed to smile.")


def tell(place: Place, guide_cfg: Guide, bundle_cfg: Bundle, name: str = "Mara", gender: str = "girl") -> World:
    world = World(place)
    child = world.add(Entity(id=name, kind="character", type=gender, label=name))
    guide = world.add(Entity(id="Guide", kind="character", type=guide_cfg.type, label=guide_cfg.label))
    bundle = world.add(Entity(id="Bundle", type="bundle", label=bundle_cfg.label, phrase=bundle_cfg.phrase, owner=guide.id, caretaker=guide.id))

    world.say(f"Once there was a little {gender} named {name}, and {name} met {guide_cfg.label} beside {place.label}.")
    world.say(place.calm)
    world.say(f"The old guide said the child should trust the path and carry {bundle_cfg.phrase}.")
    world.para()

    _do_walk(world, child)
    _do_repetition(world, child, guide, guide_cfg)
    _do_curiosity(world, child, bundle)
    world.say(f"Still, {name} kept walking, one step after another, because trust was stronger than fear.")
    world.para()

    world.say(f"At the fork by the reeds, the guide spoke the same little rule again: do not peek.")
    world.say(f"{name} nodded, listened, and waited until the bundle could be opened safely.")
    _do_twist(world, guide, bundle, guide_cfg, bundle_cfg)
    world.say(f"By sunset, {name} understood that trust can be wise when it keeps something small and frightened safe.")
    world.say(f"{name} went home with an empty basket and a full heart.")

    world.facts.update(
        child=child,
        guide=guide,
        bundle=bundle,
        place=place,
        guide_cfg=guide_cfg,
        bundle_cfg=bundle_cfg,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    guide_cfg = f["guide_cfg"]
    bundle_cfg = f["bundle_cfg"]
    return [
        f'Write a short folk tale for a child about trust, curiosity, and a repeated rule, using the word "trust".',
        f"Tell a gentle story where {child.id} follows {guide_cfg.label} and learns why {guide_cfg.rule}.",
        f"Write a small repeating tale that ends with a twist about {bundle_cfg.contents}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    guide_cfg = f["guide_cfg"]
    bundle_cfg = f["bundle_cfg"]
    place = f["place"]
    return [
        QAItem(
            question=f"Who is the story about at {place.label}?",
            answer=f"It is about a little {child.type} named {child.id} who meets {guide_cfg.label} at {place.label}.",
        ),
        QAItem(
            question=f"What did the guide keep saying while they walked?",
            answer=f"The guide kept saying, '{guide_cfg.repetition}.' That repetition helped {child.id} stay calm and keep going.",
        ),
        QAItem(
            question=f"Why did {child.id} want to peek into {bundle_cfg.label}?",
            answer=f"{child.id} was curious because the bundle bumped and whispered, so {child.id} wanted to know what was inside.",
        ),
        QAItem(
            question=f"What was the twist at the end of the story?",
            answer=f"The twist was that {guide_cfg.label} was not hiding treasure at all. The bundle held {bundle_cfg.contents}, and the repeated rules kept them safe.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is trust?",
            answer="Trust means believing that someone will try to do the right thing and keep others safe.",
        ),
        QAItem(
            question="What is curiosity?",
            answer="Curiosity is the feeling that makes you want to learn more, look closer, or ask questions.",
        ),
        QAItem(
            question="What is a twist in a story?",
            answer="A twist is a surprising turn that makes you see the story in a new way.",
        ),
        QAItem(
            question="Why do storytellers use repetition?",
            answer="Repetition helps a story feel memorable, musical, and important, especially in a folk tale.",
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
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
guide_rule(G) :- guide(G).
bundle_safe(B) :- bundle(B).
valid_story(P,G,B) :- place(P), guide(G), bundle(B).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        if p.outdoors:
            lines.append(asp.fact("outdoors", pid))
    for gid, g in GUIDES.items():
        lines.append(asp.fact("guide", gid))
    for bid, b in BUNDLES.items():
        lines.append(asp.fact("bundle", bid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


CURATED = [
    StoryParams(place="brook", guide="fox", bundle="basket", name="Mara", gender="girl"),
    StoryParams(place="forest", guide="crow", bundle="cloth", name="Rafi", gender="boy"),
    StoryParams(place="hillpath", guide="mole", bundle="sack", name="Tala", gender="girl"),
]


def generate(params: StoryParams) -> StorySample:
    world = tell(PLACES[params.place], GUIDES[params.guide], BUNDLES[params.bundle], params.name, params.gender)
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
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible story combos:\n")
        for c in combos:
            print("  ", c)
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
            header = f"### {p.name}: {p.guide} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
