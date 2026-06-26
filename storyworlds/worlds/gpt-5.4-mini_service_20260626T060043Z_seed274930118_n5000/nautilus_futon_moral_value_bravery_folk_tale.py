#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/nautilus_futon_moral_value_bravery_folk_tale.py
=========================================================================================================================

A small folk-tale storyworld about a brave nautilus, a futon, and the value of
doing the right thing even when the dark water feels frightening.

Seed tale:
---
A tiny nautilus lived beside a moonlit harbor. One windy night, a fisher left
a futon out on the dock. The tide was rising, and the nautilus was afraid of
the deep foam. Still, it remembered that a kind act matters more than fear.
It took a brave breath, called for help, and guided the futon to safety before
the water could ruin it. The fisher thanked the nautilus, and the little shell
felt proud, because bravery had turned into a good deed.

This file turns that premise into a tiny simulated world with physical meters
and emotional memes, plus a matching ASP reasonableness gate.
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
    worn_by: Optional[str] = None
    region: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    traits: list[str] = field(default_factory=list)
    plural: bool = False

    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "character":
            if self.type in {"girl", "woman"}:
                return {"subject": "she", "object": "her", "possessive": "her"}[case]
            if self.type in {"boy", "man"}:
                return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    tide: str
    sky: str
    affords: set[str] = field(default_factory=set)


@dataclass
class ObjectCfg:
    label: str
    phrase: str
    region: str
    mess: str
    soil: str
    risk: str
    tags: set[str] = field(default_factory=set)


@dataclass
class World:
    setting: Setting
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
        import copy as _copy
        w = World(self.setting)
        w.entities = _copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        return w


@dataclass
class StoryParams:
    setting: str
    prize: str
    name: str
    gender: str
    companion: str
    trait: str
    seed: Optional[int] = None


SETTINGS = {
    "harbor": Setting(place="the harbor", tide="high tide", sky="moonlit", affords={"carry"}),
    "shore": Setting(place="the shore", tide="rising tide", sky="windy", affords={"carry"}),
    "cove": Setting(place="the cove", tide="rising tide", sky="foggy", affords={"carry"}),
}

PRIZES = {
    "futon": ObjectCfg(
        label="futon",
        phrase="a soft futon for resting",
        region="shore",
        mess="wet",
        soil="soggy and heavy",
        risk="the tide could soak it",
        tags={"futon", "wet", "home"},
    ),
    "mat": ObjectCfg(
        label="mat",
        phrase="a woven mat for the floor",
        region="shore",
        mess="wet",
        soil="damp and drooping",
        risk="the spray could spoil it",
        tags={"mat", "wet"},
    ),
}

NAMES = ["Nori", "Mina", "Ola", "Pip", "Lina", "Taro"]
TRAITS = ["small", "gentle", "curious", "quiet", "brave", "kind"]


def _m(ent: Entity, key: str) -> float:
    return ent.meters.get(key, 0.0)


def _e(ent: Entity, key: str) -> float:
    return ent.memes.get(key, 0.0)


def _setm(ent: Entity, key: str, delta: float) -> None:
    ent.meters[key] = ent.meters.get(key, 0.0) + delta


def _sete(ent: Entity, key: str, delta: float) -> None:
    ent.memes[key] = ent.memes.get(key, 0.0) + delta


def _do_carry(world: World, hero: Entity, prize: Entity) -> None:
    _setm(hero, "effort", 1)
    _sete(hero, "bravery", 1)
    if world.setting.place in {"the harbor", "the cove"}:
        _setm(prize, "wet", 1)
        _setm(prize, "dirty", 1)
        _sete(hero, "pride", 1)


def story_knowledge() -> dict[str, list[tuple[str, str]]]:
    return {
        "nautilus": [
            ("What is a nautilus?",
             "A nautilus is a sea creature with a coiled shell that can drift through the water."),
            ("Where does a nautilus live?",
             "A nautilus lives in the sea, where it can glide near rocks and waves."),
        ],
        "futon": [
            ("What is a futon?",
             "A futon is a soft pad or bed that people can sit on or sleep on."),
            ("Why should a futon stay dry?",
             "A futon should stay dry because water can make it heavy, cold, and uncomfortable."),
        ],
        "bravery": [
            ("What does bravery mean?",
             "Bravery means doing the right thing even when you feel afraid."),
        ],
        "moral": [
            ("What is a moral in a story?",
             "A moral is the lesson a story teaches about how to act well."),
        ],
        "wet": [
            ("What does wet mean?",
             "Wet means covered with water or damp from water."),
        ],
    }


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for s in SETTINGS:
        for p in PRIZES:
            combos.append((s, p))
    return combos


def tell(setting: Setting, prize_cfg: ObjectCfg, hero_name: str, hero_gender: str, companion: str, trait: str) -> World:
    world = World(setting)
    hero = world.add(Entity(
        id=hero_name, kind="character", type=hero_gender,
        label="nautilus", phrase="a tiny nautilus", traits=[trait, "small", "sea-born"],
    ))
    helper = world.add(Entity(
        id="Fisher", kind="character", type="adult", label="fisher",
        phrase="a kind fisher by the dock", traits=["busy", "kind"],
    ))
    prize = world.add(Entity(
        id="prize", type=prize_cfg.label, label=prize_cfg.label, phrase=prize_cfg.phrase,
        owner=helper.id, caretaker=helper.id, region=prize_cfg.region,
    ))
    world.facts.update(hero=hero, helper=helper, prize=prize, prize_cfg=prize_cfg)

    world.say(f"{hero.id} was {hero.phrase}, and {hero.pronoun()} lived beside {setting.place}.")
    world.say(f"{hero.pronoun().capitalize()} loved the salt wind, but {hero.pronoun('possessive')} shell was small and {trait}.")
    world.say(f"One evening, {helper.label} left {prize.phrase} near the water while {helper.pronoun()} went to fetch a lantern.")
    world.para()
    world.say(f"Then the {setting.tide} crept closer, and {prize.label} was in danger; {prize_cfg.risk}.")
    _sete(hero, "fear", 1)
    _sete(hero, "duty", 1)
    world.say(f"{hero.id} felt the worry rise like a dark wave. {hero.pronoun().capitalize()} was afraid of the foam, yet {hero.pronoun('possessive')} heart knew a moral truth: a kind deed is better than hiding.")
    world.say(f"{hero.id} took a brave breath, asked the shore gulls for room, and began to {('carry') if 'carry' in setting.affords else 'move'} the {prize.label} away from the tide.")
    _do_carry(world, hero, prize)
    world.para()
    _sete(hero, "bravery", 1)
    world.say(f"By the time the water reached the dock, {hero.id} had guided the {prize.label} to safety.")
    world.say(f"{helper.label} returned, saw the saved {prize.label}, and thanked the little nautilus with a warm smile.")
    world.say(f"{hero.id} felt proud then, because {hero.pronoun('possessive')} courage had turned into kindness.")
    world.facts["resolved"] = True
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    prize_cfg = f["prize_cfg"]
    return [
        f"Write a short folk tale for a child about a nautilus named {hero.id} and a {prize_cfg.label}.",
        f"Tell a gentle story where bravery helps {hero.id} save a {prize_cfg.label} from the tide.",
        "Write a simple sea-side folk tale that teaches the moral value of brave kindness.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    prize = f["prize"]
    prize_cfg = f["prize_cfg"]
    return [
        QAItem(
            question=f"Who was the story about?",
            answer=f"It was about {hero.id}, a tiny nautilus who lived beside {world.setting.place}.",
        ),
        QAItem(
            question=f"What was in danger when the tide rose?",
            answer=f"The {prize.label} was in danger, because {prize_cfg.risk}.",
        ),
        QAItem(
            question=f"What did {hero.id} choose to do even though the water felt scary?",
            answer=f"{hero.id} chose to act bravely and move the {prize.label} to safety instead of hiding.",
        ),
        QAItem(
            question=f"How did the story show the moral value of the tale?",
            answer=f"It showed that a good deed matters more than fear, because {hero.id} used bravery to help {helper.label}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    out: list[QAItem] = []
    tags = set(world.facts["prize_cfg"].tags)
    tags.update({"nautilus", "bravery", "moral", "wet"})
    kb = story_knowledge()
    for tag in ["nautilus", "futon", "bravery", "moral", "wet"]:
        if tag in tags and tag in kb:
            out.extend(QAItem(question=q, answer=a) for q, a in kb[tag])
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
    lines.append("== (3) World knowledge ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"  {e.id:8} ({e.type:8}) meters={meters} memes={memes}")
    return "\n".join(lines)


ASP_RULES = r"""
setting(harbor).
setting(shore).
setting(cove).

affords(harbor,carry).
affords(shore,carry).
affords(cove,carry).

object(futon).
object(mat).

risk(futon,shore).
risk(mat,shore).

value(bravery).
value(moral).

valid(Place,Prize) :- affords(Place,carry), risk(Prize,shore), value(bravery), value(moral).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
        for a in sorted(SETTINGS[sid].affords):
            lines.append(asp.fact("affords", sid, a))
    for pid in PRIZES:
        lines.append(asp.fact("object", pid))
        lines.append(asp.fact("risk", pid, "shore"))
    lines.append(asp.fact("value", "bravery"))
    lines.append(asp.fact("value", "moral"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = {("harbor", "futon"), ("harbor", "mat"), ("shore", "futon"), ("shore", "mat"), ("cove", "futon"), ("cove", "mat")}
    cl = set(asp_valid_combos())
    if cl == py:
        print(f"OK: clingo gate matches valid_combos() ({len(cl)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    if py - cl:
        print("  only in python:", sorted(py - cl))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small folk tale about nautilus, futon, bravery, and moral value.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--companion", default="fisher")
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
    combos = valid_combos()
    if args.setting:
        combos = [c for c in combos if c[0] == args.setting]
    if args.prize:
        combos = [c for c in combos if c[1] == args.prize]
    if not combos:
        raise StoryError("No valid story matches the requested setting and prize.")
    setting, prize = rng.choice(combos)
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(NAMES)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(setting=setting, prize=prize, name=name, gender=gender, companion=args.companion, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], PRIZES[params.prize], params.name, params.gender, params.companion, params.trait)
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
    StoryParams(setting="harbor", prize="futon", name="Nori", gender="boy", companion="fisher", trait="brave"),
    StoryParams(setting="shore", prize="mat", name="Mina", gender="girl", companion="fisher", trait="kind"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        triples = asp_valid_combos()
        print(f"{len(triples)} compatible stories:\n")
        for place, prize in triples:
            print(f"  {place:8} {prize}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            i += 1

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
            header = f"### {p.name}: {p.setting} / {p.prize}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
