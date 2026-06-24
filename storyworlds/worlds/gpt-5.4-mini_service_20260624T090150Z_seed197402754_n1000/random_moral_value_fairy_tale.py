#!/usr/bin/env python3
"""
random_moral_value_fairy_tale.py
===============================

A small fairy-tale story world about kindness, honesty, and the little moral
turn that changes a day. A childlike hero finds something shiny, feels the tug
of keeping it, and ends by choosing the kinder path.

The simulation tracks:
- physical state: who carries what, where objects are, and whether a gift is
  found or returned
- emotional state: pride, worry, relief, gratitude, and a moral_value meter

The prose is generated from the state, not from a frozen template.
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
    carrier: Optional[str] = None
    carried_by: Optional[str] = None
    place: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "queen", "witch", "mother", "princess"}
        male = {"boy", "king", "wizard", "father", "prince"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    weather: str
    detail: str


@dataclass
class Gift:
    id: str
    label: str
    phrase: str
    type: str
    owner_kind: str
    story_seed: str


@dataclass
class MoralChoice:
    id: str
    want_verb: str
    good_verb: str
    wrong_verb: str
    moral_gain: float
    moral_loss: float
    problem: str
    resolution: str
    tags: set[str] = field(default_factory=set)


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

    def copy(self) -> "World":
        clone = World(self.setting)
        clone.entities = {
            k: Entity(**{
                **vars(v),
                "meters": dict(v.meters),
                "memes": dict(v.memes),
            })
            for k, v in self.entities.items()
        }
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]


def _inc(ent: Entity, key: str, delta: float = 1.0) -> None:
    ent.meters[key] = ent.meters.get(key, 0.0) + delta


def _mem(ent: Entity, key: str, delta: float = 1.0) -> None:
    ent.memes[key] = ent.memes.get(key, 0.0) + delta


def _r_moral_shift(world: World) -> list[str]:
    out: list[str] = []
    for char in world.characters():
        if char.memes.get("temptation", 0.0) < THRESHOLD:
            continue
        sig = ("moral_shift", char.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        char.meters["moral_value"] = char.meters.get("moral_value", 0.0) - 1.0
        char.memes["uneasy"] = char.memes.get("uneasy", 0.0) + 1.0
        out.append(f"{char.id}'s heart felt a little cloudy.")
    return out


def _r_relief(world: World) -> list[str]:
    out: list[str] = []
    for char in world.characters():
        if char.memes.get("relief_trigger", 0.0) < THRESHOLD:
            continue
        sig = ("relief", char.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        char.meters["moral_value"] = char.meters.get("moral_value", 0.0) + 2.0
        char.memes["joy"] = char.memes.get("joy", 0.0) + 1.0
        out.append(f"{char.id} felt warm and brave all at once.")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in (_r_moral_shift, _r_relief):
            sents = rule(world)
            if sents:
                changed = True
                out.extend(sents)
    if narrate:
        for s in out:
            world.say(s)
    return out


SETTINGS = {
    "forest": Setting("the forest", "misty", "Tall ferns leaned over the path."),
    "village": Setting("the village green", "golden", "A little well sat beside the road."),
    "cottage": Setting("the cottage garden", "soft", "A rosebush climbed the fence."),
}

GIFT_REGISTRY = {
    "lost_ring": Gift("lost_ring", "ring", "a silver ring with a blue stone", "ring", "villager", "ring"),
    "lost_crown": Gift("lost_crown", "crown", "a tiny golden crown", "crown", "queen", "crown"),
    "lost_bread": Gift("lost_bread", "bread", "a round loaf still warm from the oven", "bread", "baker", "bread"),
    "lost_flower": Gift("lost_flower", "flower", "a bright flower tied with ribbon", "flower", "child", "flower"),
}

CHOICES = {
    "keep": MoralChoice(
        id="keep",
        want_verb="keep it",
        good_verb="return it",
        wrong_verb="hide it",
        moral_gain=2.0,
        moral_loss=1.0,
        problem="The hero wanted to keep the pretty thing for themself.",
        resolution="The hero chose to give it back where it belonged.",
        tags={"kindness", "honesty"},
    ),
    "share": MoralChoice(
        id="share",
        want_verb="save it for later",
        good_verb="share it",
        wrong_verb="snatch it away",
        moral_gain=2.0,
        moral_loss=1.0,
        problem="The hero was tempted to keep the nice thing all alone.",
        resolution="The hero chose to share it with the one who needed it.",
        tags={"kindness", "sharing"},
    ),
    "return": MoralChoice(
        id="return",
        want_verb="show it off",
        good_verb="take it home to ask around",
        wrong_verb="walk away with it",
        moral_gain=2.0,
        moral_loss=1.0,
        problem="The hero was tempted to walk away with the found treasure.",
        resolution="The hero chose to search for the rightful owner.",
        tags={"honesty", "helpfulness"},
    ),
}

HERO_TYPES = ["girl", "boy"]
HERO_NAMES = {
    "girl": ["Mira", "Lina", "Tessa", "Nora", "Ivy", "Elsa"],
    "boy": ["Pip", "Theo", "Finn", "Rowan", "Luca", "Jasper"],
}
COMPANIONS = ["a mouse", "a sparrow", "a lamb", "a cat", "a rabbit"]


@dataclass
class StoryParams:
    setting: str
    gift: str
    choice: str
    name: str
    gender: str
    companion: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny fairy tale about a moral choice.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--gift", choices=GIFT_REGISTRY)
    ap.add_argument("--choice", choices=CHOICES)
    ap.add_argument("--gender", choices=HERO_TYPES)
    ap.add_argument("--name")
    ap.add_argument("--companion", choices=COMPANIONS)
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


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for setting in SETTINGS:
        for gift in GIFT_REGISTRY:
            for choice in CHOICES:
                combos.append((setting, gift, choice))
    return combos


def explain_rejection(setting: str, gift: str, choice: str) -> str:
    return f"(No story: the choice '{choice}' does not fit the fairy-tale turn for {gift} in {setting}.)"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.setting and args.gift and args.choice:
        if (args.setting, args.gift, args.choice) not in valid_combos():
            raise StoryError(explain_rejection(args.setting, args.gift, args.choice))
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.gift is None or c[1] == args.gift)
              and (args.choice is None or c[2] == args.choice)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, gift, choice = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(HERO_TYPES)
    name = args.name or rng.choice(HERO_NAMES[gender])
    companion = args.companion or rng.choice(COMPANIONS)
    return StoryParams(setting=setting, gift=gift, choice=choice, name=name, gender=gender, companion=companion)


def world_intro(world: World, hero: Entity, gift: Entity, companion: str) -> None:
    world.say(
        f"Once upon a time, {hero.id} was a little {hero.type} who wandered by "
        f"{world.setting.place} with {companion} for company."
    )
    world.say(
        f"{hero.id} loved shiny things, and one day {hero.pronoun('subject')} "
        f"found {gift.phrase} beside the path."
    )


def world_tension(world: World, hero: Entity, gift: Entity, choice: MoralChoice) -> None:
    _mem(hero, "temptation", 1.0)
    world.say(
        f"{hero.id} held the treasure close and wondered whether to {choice.want_verb}."
    )
    world.say(choice.problem)
    propagate(world, narrate=True)


def world_turn(world: World, hero: Entity, gift: Entity, choice: MoralChoice) -> None:
    witness = world.get("witness")
    _mem(witness, "plea", 1.0)
    world.say(
        f"Then {witness.id} came hurrying along the path and said the {gift.label} had been lost."
    )
    _mem(hero, "relief_trigger", 1.0)
    hero.meters["moral_value"] = hero.meters.get("moral_value", 0.0) + choice.moral_gain
    world.say(
        f"{hero.id} remembered how it felt to lose something dear, and {hero.pronoun('subject')} chose to {choice.good_verb}."
    )
    propagate(world, narrate=True)


def world_resolution(world: World, hero: Entity, gift: Entity, choice: MoralChoice) -> None:
    witness = world.get("witness")
    gift.carried_by = witness.id
    gift.owner = witness.id
    _mem(witness, "relief_trigger", 1.0)
    hero.meters["moral_value"] = max(hero.meters.get("moral_value", 0.0), 2.0)
    world.say(
        f"{witness.id} smiled so widely that the whole lane seemed brighter."
    )
    world.say(
        f"By the end, {hero.id}'s hands were empty, but {hero.pronoun('possessive')} heart felt full."
    )


def tell(params: StoryParams) -> World:
    setting = SETTINGS[params.setting]
    gift_cfg = GIFT_REGISTRY[params.gift]
    choice = CHOICES[params.choice]
    world = World(setting)
    hero = world.add(Entity(id=params.name, kind="character", type=params.gender))
    witness = world.add(Entity(id="witness", kind="character", type=gift_cfg.owner_kind))
    gift = world.add(Entity(id="gift", type=gift_cfg.type, label=gift_cfg.label, phrase=gift_cfg.phrase, owner=None, carried_by=hero.id))
    world.facts.update(hero=hero, witness=witness, gift=gift, choice=choice, gift_cfg=gift_cfg)

    hero.meters["moral_value"] = 0.0
    hero.memes["temper"] = 0.0
    witness.meters["moral_value"] = 0.0

    world_intro(world, hero, gift, params.companion)
    world.para()
    world_tension(world, hero, gift, choice)
    world.para()
    world_turn(world, hero, gift, choice)
    world_resolution(world, hero, gift, choice)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    gift_cfg = f["gift_cfg"]
    choice = f["choice"]
    return [
        f'Write a short fairy tale where a little {hero.type} named {hero.id} finds {gift_cfg.phrase} and must choose whether to {choice.want_verb}.',
        f"Tell a gentle moral story about {hero.id} at {world.setting.place} who sees {gift_cfg.phrase} and learns to make the kind choice.",
        f'Write a child-friendly fairy tale with the word "random" in the background of a surprising discovery and a moral choice.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    gift_cfg = f["gift_cfg"]
    choice = f["choice"]
    witness = f["witness"]
    qas = [
        QAItem(
            question=f"What did {hero.id} find in the story?",
            answer=f"{hero.id} found {gift_cfg.phrase} by the path at {world.setting.place}.",
        ),
        QAItem(
            question=f"What did {hero.id} want to do before making the kind choice?",
            answer=f"{hero.id} wanted to {choice.want_verb} before choosing the kinder path.",
        ),
        QAItem(
            question=f"Who came to speak up about the lost item?",
            answer=f"{witness.id} came hurrying along and explained that the {gift_cfg.label} had been lost.",
        ),
        QAItem(
            question=f"How did the story end for {hero.id}?",
            answer=f"{hero.id} gave the {gift_cfg.label} back, and {hero.id}'s heart felt full at the end.",
        ),
    ]
    return qas


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is moral value in a fairy tale?",
            answer="Moral value is the part of a character's state that shows how kind, honest, and fair their choices are.",
        ),
        QAItem(
            question="Why can finding something make a character feel tempted?",
            answer="A character can feel tempted because a shiny or special thing seems easy to keep, even when it belongs to someone else.",
        ),
        QAItem(
            question="What helps a fairy-tale hero make a good choice?",
            answer="A good choice is often helped by remembering another person's feelings and choosing kindness over selfishness.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== Generation prompts =="]
    for p in sample.prompts:
        out.append(p)
    out.append("")
    out.append("== Story QA ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== World QA ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


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
        if e.carried_by:
            bits.append(f"carried_by={e.carried_by}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
#show valid/3.

valid(S,G,C) :- setting(S), gift(G), choice(C).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for g in GIFT_REGISTRY:
        lines.append(asp.fact("gift", g))
    for c in CHOICES:
        lines.append(asp.fact("choice", c))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


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


CURATED = [
    StoryParams(setting="forest", gift="lost_ring", choice="return", name="Mira", gender="girl", companion="a mouse"),
    StoryParams(setting="village", gift="lost_bread", choice="share", name="Pip", gender="boy", companion="a sparrow"),
    StoryParams(setting="cottage", gift="lost_flower", choice="keep", name="Nora", gender="girl", companion="a rabbit"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("\n".join(str(t) for t in asp_valid_combos()))
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.gift} in {p.setting} (choice: {p.choice})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
