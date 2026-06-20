#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/compromise_prison_ups_bad_ending_nursery_rhyme.py
==================================================================================

A standalone story world for a tiny nursery-rhyme-like domain with a bad ending.

Seed idea
---------
A little child wants to make a game about a "prison" for a toy bird, and a
careful sibling предлагает a compromise: use a soft nest-box instead. But the
child keeps chasing the noisy "ups" idea instead of listening. The toy game goes
wrong, the bird gets upset and escapes, and the children are left with a broken
game and no happy fix.

This world keeps the story close to a nursery rhyme style: simple repeating
rhythms, concrete objects, a short turn, and a sad ending image that proves what
changed.

Run it
------
    python storyworlds/worlds/gpt-5.4-mini/compromise_prison_ups_bad_ending_nursery_rhyme.py
    python storyworlds/worlds/gpt-5.4-mini/compromise_prison_ups_bad_ending_nursery_rhyme.py --all
    python storyworlds/worlds/gpt-5.4-mini/compromise_prison_ups_bad_ending_nursery_rhyme.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4-mini/compromise_prison_ups_bad_ending_nursery_rhyme.py --verify
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
from typing import Callable, Optional

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
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Setting:
    id: str
    place: str
    rhyme: str
    scene: str


@dataclass
class Toy:
    id: str
    label: str
    kind: str
    fragile: bool = False
    can_hold: bool = False


@dataclass
class Compromise:
    id: str
    label: str
    offer: str
    safety: str
    reason: str
    power: int
    sense: int


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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_scatter(world: World) -> list[str]:
    out = []
    bird = world.entities.get("bird")
    if not bird:
        return out
    if bird.meters["trapped"] >= THRESHOLD and ("scatter", "bird") not in world.fired:
        world.fired.add(("scatter", "bird"))
        bird.memes["fear"] += 1
        bird.meters["flutter"] += 1
        out.append("__flutter__")
    return out


CAUSAL_RULES = [Rule("scatter", "social", _r_scatter)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def is_reasonable(setting: Setting, toy: Toy, compromise: Compromise) -> bool:
    return toy.fragile and compromise.sense >= 2 and compromise.power >= 2


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid, setting in SETTINGS.items():
        for tid, toy in TOYS.items():
            for cid, comp in COMPROMISES.items():
                if toy.fragile and comp.sense >= 2:
                    combos.append((sid, tid, cid))
    return combos


@dataclass
class StoryParams:
    setting: str
    toy: str
    compromise: str
    child: str
    sibling: str
    parent: str
    seed: Optional[int] = None


def nursery_opening(world: World, child: Entity, sibling: Entity, setting: Setting) -> None:
    world.say(
        f"{child.id} and {sibling.id} went a-toddle in {setting.place}, "
        f"under the little rhyme of {setting.rhyme}."
    )
    world.say(
        f"{child.id} had a bright idea, and {sibling.id} had a kinder one; "
        f"{setting.scene} made the morning feel like a song."
    )


def want_prison(world: World, child: Entity, toy: Toy) -> None:
    child.memes["want"] += 1
    world.say(
        f'"Let us make a prison," said {child.id}, "for {toy.label}, '
        f"and lock the game up neat and tight."'
    )
    world.say(f"The little words went tap-tap-tap like a nursery rhyme.")
    child.meters["prison"] += 1


def offer_compromise(world: World, sibling: Entity, comp: Compromise, toy: Toy) -> None:
    sibling.memes["care"] += 1
    world.say(
        f'"No, no," said {sibling.id}. "Let us choose a compromise. '
        f"{comp.offer}, and keep {toy.label} safe.""
    )
    world.say(f"{comp.reason}. That way the fun could stay gentle.")


def reject_help(world: World, child: Entity) -> None:
    child.memes["stubborn"] += 1
    world.say(
        f'But {child.id} shook {child.pronoun("possessive")} head and cried, '
        f'"Ups and ups and up we go!"'
    )
    world.say("The rhyme got louder, but the answer did not get wiser.")


def accident(world: World, toy: Toy) -> None:
    bird = world.get("bird")
    world.say(
        f"The prison door tipped. {toy.label} knocked hard against the bars, "
        f"and little {bird.id} fluttered up with a gasp."
    )
    bird.meters["trapped"] = 1.0
    bird.memes["hurt"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{bird.id} bumped the sill, and the toy prison split right down the seam."
    )


def bad_ending(world: World, parent: Entity, child: Entity, sibling: Entity) -> None:
    parent.memes["sad"] += 1
    child.memes["sad"] += 1
    sibling.memes["sad"] += 1
    world.say(
        f"{parent.label_word.capitalize()} came, but the bird was already gone. "
        f"The prison was only splinters, and the compromise lay forgotten."
    )
    world.say(
        f"By the end, {child.id} stood small and still, while {sibling.id} held "
        f"the broken pieces in quiet hands."
    )


SETTINGS = {
    "nursery": Setting("nursery", "the nursery room", "Hickory Dickory Dock", "soft dolls on the shelf"),
    "garden": Setting("garden", "the flower garden", "Jack and Jill", "little stones and daisies"),
    "playroom": Setting("playroom", "the bright playroom", "Humpty Dumpty", "blocks on the rug"),
}

TOYS = {
    "bird": Toy("bird", "the toy bird", "bird", fragile=True),
    "bear": Toy("bear", "the teddy bear", "bear", fragile=True),
    "car": Toy("car", "the wooden car", "car", fragile=False),
}

COMPROMISES = {
    "nest": Compromise("nest", "nest-box", "put {toy} in a soft nest-box", "soft and safe", "A nest-box lets the game stay kind", 2, 3),
    "basket": Compromise("basket", "little basket", "rest {toy} in a little basket", "easy to carry", "A basket keeps the game from turning rough", 2, 2),
    "blanket": Compromise("blanket", "blanket bed", "tuck {toy} in a blanket bed", "warm and soft", "A blanket bed is gentle for a small toy", 3, 3),
}


GIRL_NAMES = ["Mia", "Lily", "Nora", "Ava", "Zoe"]
BOY_NAMES = ["Tom", "Ben", "Max", "Noah", "Eli"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Nursery-rhyme compromise story world.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--toy", choices=TOYS)
    ap.add_argument("--compromise", choices=COMPROMISES)
    ap.add_argument("--child")
    ap.add_argument("--sibling")
    ap.add_argument("--parent", choices=["mother", "father"])
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
              and (args.toy is None or c[1] == args.toy)
              and (args.compromise is None or c[2] == args.compromise)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, toy, comp = rng.choice(sorted(combos))
    child = args.child or rng.choice(GIRL_NAMES + BOY_NAMES)
    sibling = args.sibling or rng.choice([n for n in GIRL_NAMES + BOY_NAMES if n != child])
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(setting, toy, comp, child, sibling, parent)


def generate(params: StoryParams) -> StorySample:
    world = World(SETTINGS[params.setting])
    child = world.add(Entity(params.child, "character", "child"))
    sibling = world.add(Entity(params.sibling, "character", "child", role="sibling"))
    parent = world.add(Entity("Parent", "character", params.parent, role="parent"))
    toy = world.add(Entity("toy", "thing", TOYS[params.toy].kind, label=TOYS[params.toy].label))
    bird = world.add(Entity("bird", "thing", "bird", label="bird"))
    comp = COMPROMISES[params.compromise]

    nursery_opening(world, child, sibling, SETTINGS[params.setting])
    world.para()
    want_prison(world, child, TOYS[params.toy])
    offer_compromise(world, sibling, comp, TOYS[params.toy])
    reject_help(world, child)
    accident(world, TOYS[params.toy])
    world.para()
    bad_ending(world, parent, child, sibling)

    world.facts.update(child=child, sibling=sibling, parent=parent, toy_cfg=TOYS[params.toy], comp=comp,
                       setting=SETTINGS[params.setting], outcome="bad")
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a nursery-rhyme style story that includes the words "compromise", "prison", and "ups".',
        f"Tell a sad little story where {f['child'].id} wants a prison for {f['toy_cfg'].label}, but {f['sibling'].id} offers a compromise and {f['child'].id} ignores it.",
        "Write a short story with repeating rhythm, a bad ending, and a broken toy game.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child, sibling, toy, comp, parent = f["child"], f["sibling"], f["toy_cfg"], f["comp"], f["parent"]
    return [
        ("Who is the story about?",
         f"It is about {child.id}, {sibling.id}, and the grown-up who came at the end."),
        (f"What did {child.id} want to make?",
         f"{child.id} wanted to make a prison for {toy.label}. The little game was meant to hold the toy still."),
        (f"What compromise did {sibling.id} offer?",
         f"{sibling.id} offered a compromise: {comp.offer.format(toy=toy.label)}. It was a softer way to keep the play safe."),
        ("How did the story end?",
         "It ended badly. The toy game broke, the bird got away, and nobody got a happy fix."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is a compromise?",
         "A compromise is a middle choice that helps two people find a safer or fairer way to keep going."),
        ("What does a prison mean in a story?",
         "A prison is a place where something or someone is kept in and cannot get out easily."),
        ("What does ups mean?",
         "Ups is a short word people can shout when they go upward or when they are excited in a song."),
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
    lines.append("== (3) World knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"  {e.id:8} ({e.type:7}) meters={meters} memes={memes} role={e.role}")
    return "\n".join(lines)


CURATED = [
    StoryParams("nursery", "bird", "nest", "Mia", "Nora", "mother"),
    StoryParams("garden", "bear", "basket", "Tom", "Ben", "father"),
    StoryParams("playroom", "bird", "blanket", "Ava", "Zoe", "mother"),
]


ASP_RULES = r"""
at_risk(T) :- toy(T), fragile(T).
reasonable(C) :- compromise(C), sense(C, S), S >= 2.
valid(S, T, C) :- setting(S), at_risk(T), reasonable(C).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for t, toy in TOYS.items():
        lines.append(asp.fact("toy", t))
        if toy.fragile:
            lines.append(asp.fact("fragile", t))
    for c, comp in COMPROMISES.items():
        lines.append(asp.fact("compromise", c))
        lines.append(asp.fact("sense", c, comp.sense))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import sys
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        rc = 1
        print("MISMATCH in ASP gate")
    try:
        sample = generate(CURATED[0])
        assert sample.story
    except Exception as e:
        rc = 1
        print(f"SMOKE TEST FAILED: {e}")
    else:
        print("OK: smoke test passed.")
    return rc


def explain_rejection() -> str:
    return "(No story: this combo does not fit the tiny nursery-rhyme world.)"


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        for c in asp_valid_combos():
            print(c)
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            i += 1
            try:
                p = resolve_params(args, random.Random(base_seed + i))
            except StoryError as err:
                print(err)
                return
            s = generate(p)
            if s.story in seen:
                continue
            seen.add(s.story)
            samples.append(s)
    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        print(sample.story)
        if args.trace and sample.world:
            print(dump_trace(sample.world))
        if args.qa:
            print()
            print(format_qa(sample))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
