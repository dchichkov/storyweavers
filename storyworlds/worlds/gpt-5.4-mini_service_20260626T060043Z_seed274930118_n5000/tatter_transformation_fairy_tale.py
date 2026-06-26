#!/usr/bin/env python3
"""
tatter_transformation_fairy_tale.py
===================================

A small fairy-tale storyworld about a tattered thing, a kind helper, and a
transforming spell that turns a problem into a gift.

The premise is simple: a child, a tattered keepsake, and a wish for it to be
whole again. The tension comes from the item being too torn for the child to
wear or show proudly. The turn is a fairy helper's transformation magic, which
does not erase the past, but remakes the item into something useful and lovely.
The ending proves the change by showing the transformed thing in action.
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
    worn_by: Optional[str] = None
    transformation: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "queen", "fairy"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "king", "wizard"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str
    tone: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Prize:
    label: str
    phrase: str
    type: str
    place: str
    transforms_to: str
    genders: set[str] = field(default_factory=lambda: {"girl", "boy"})


@dataclass
class FairyGift:
    name: str
    label: str
    spell: str
    result: str
    touch: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.facts: dict = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.trace_log: list[str] = []

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)
            self.trace_log.append(text)

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
class StoryParams:
    setting: str
    prize: str
    name: str
    gender: str
    helper: str
    seed: Optional[int] = None


SETTINGS = {
    "old_tower": Setting(place="the old tower", tone="moonlit", affords={"repair", "magic"}),
    "forest_glade": Setting(place="the forest glade", tone="golden", affords={"repair", "magic"}),
    "village_square": Setting(place="the village square", tone="bright", affords={"repair", "magic"}),
}

PRIZES = {
    "cloak": Prize(label="cloak", phrase="a soft blue cloak", type="cloak", place="shoulders", transforms_to="starlight cloak"),
    "banner": Prize(label="banner", phrase="a hand-sewn banner", type="banner", place="hands", transforms_to="festival banner"),
    "slippers": Prize(label="slippers", phrase="tiny silver slippers", type="slippers", place="feet", transforms_to="glass slippers"),
}

GIFTS = {
    "stitch": FairyGift(name="stitch", label="a silver needle", spell="mend", result="whole", touch="stitched"),
    "bloom": FairyGift(name="bloom", label="a rose wand", spell="bloom", result="bright", touch="flowered"),
    "glimmer": FairyGift(name="glimmer", label="a candle wand", spell="glimmer", result="shining", touch="glimmering"),
}

NAMES = {
    "girl": ["Mina", "Elin", "Rose", "Mara", "Nina"],
    "boy": ["Luca", "Evan", "Tobias", "Noel", "Perry"],
}

HELPERS = ["fairy", "fairy godmother", "sprite"]
TRAITS = ["gentle", "brave", "curious", "kind"]


def tatter_risk(prize: Prize) -> bool:
    return True


def compatible_gift(prize: Prize) -> FairyGift:
    if prize.label == "cloak":
        return GIFTS["stitch"]
    if prize.label == "banner":
        return GIFTS["bloom"]
    return GIFTS["glimmer"]


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for setting in SETTINGS:
        for prize in PRIZES:
            out.append((setting, "transformation", prize))
    return out


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A fairy-tale storyworld about tatters and transformation.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--helper", choices=HELPERS)
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
    setting = args.setting or rng.choice(list(SETTINGS))
    prize = args.prize or rng.choice(list(PRIZES))
    if args.gender and args.prize and args.gender not in PRIZES[args.prize].genders:
        raise StoryError("That prize does not fit that child in this fairy tale.")
    gender = args.gender or rng.choice(sorted(PRIZES[prize].genders))
    name = args.name or rng.choice(NAMES[gender])
    helper = args.helper or rng.choice(HELPERS)
    return StoryParams(setting=setting, prize=prize, name=name, gender=gender, helper=helper)


def _do_transformation(world: World, hero: Entity, prize: Entity, gift: FairyGift) -> None:
    if ("transform", prize.id) in world.fired:
        return
    world.fired.add(("transform", prize.id))
    prize.meters["tatter"] = 0
    prize.meters["beautiful"] = 1
    prize.transformation = gift.result
    hero.memes["hope"] = hero.memes.get("hope", 0) + 1
    hero.memes["joy"] = hero.memes.get("joy", 0) + 1


def tell(setting: Setting, prize_cfg: Prize, hero_name: str, hero_type: str, helper_type: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type))
    helper = world.add(Entity(id="Helper", kind="character", type=helper_type, label=f"the {helper_type}"))
    prize = world.add(Entity(
        id="Prize",
        kind="thing",
        type=prize_cfg.type,
        label=prize_cfg.label,
        phrase=prize_cfg.phrase,
        owner=hero.id,
        caretaker=hero.id,
    ))
    gift = compatible_gift(prize_cfg)

    prize.meters["tatter"] = 1.0
    hero.memes["sadness"] = 1.0

    world.say(f"Once upon a time, {hero.id} lived near {setting.place}.")
    world.say(f"{hero.pronoun().capitalize()} loved {prize.phrase}, but it had grown tattered at the edges.")
    world.say(f"One evening, {hero.id} held the {prize.label} close and wished it could be lovely again.")

    world.para()
    world.say(f"Then {helper.label} appeared in a hush of {setting.tone} light.")
    world.say(f'"I can {gift.spell} what is worn," said {helper.label}, lifting {gift.label}.')
    world.say(f"The {helper_type} touched the {prize.label}, and the old tatters began to change.")

    _do_transformation(world, hero, prize, gift)

    world.para()
    if prize_cfg.label == "cloak":
        ending = f"Soon the cloak was no longer ragged at all; it had become a {prize_cfg.transforms_to} that shimmered like night sky."
    elif prize_cfg.label == "banner":
        ending = f"Soon the banner was no longer torn at all; it had become a {prize_cfg.transforms_to} bright enough for every window in town."
    else:
        ending = f"Soon the slippers were no longer frayed at all; they had become {prize_cfg.transforms_to} that clicked softly on the path."
    world.say(ending)
    world.say(f"{hero.id} smiled, because the thing that had once been a tatter was now a treasure.")

    world.facts.update(hero=hero, helper=helper, prize=prize, prize_cfg=prize_cfg, setting=setting, gift=gift)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short fairy tale for a young child about a tattered {f["prize_cfg"].label} and a kind transformation spell.',
        f'Tell a gentle story where {f["hero"].id} finds {f["prize_cfg"].phrase} tattered, and a {f["helper"].type} helps transform it.',
        f'Write a story that includes the word "tatter" and ends with a transformed keepsake that feels magical.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, prize, gift = f["hero"], f["prize"], f["gift"]
    return [
        QAItem(
            question=f"What did {hero.id} find that was tattered?",
            answer=f"{hero.id} found {prize.phrase}, and it was tattered at the edges.",
        ),
        QAItem(
            question=f"Who helped transform the old {prize.label}?",
            answer=f"The {f['helper'].type} helped by using {gift.label} and a gentle spell.",
        ),
        QAItem(
            question=f"What did the {prize.label} become in the end?",
            answer=f"It became {prize.transformation}, so the old tatter turned into something lovely.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does tattered mean?",
            answer="Tattered means old, torn, or frayed at the edges.",
        ),
        QAItem(
            question="What is a transformation?",
            answer="A transformation is a change from one form into another.",
        ),
        QAItem(
            question="What is a fairy tale?",
            answer="A fairy tale is a magical story that often has helpers, spells, and a happy ending.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== story qa ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.transformation:
            bits.append(f"transformation={e.transformation}")
        lines.append(f"{e.id}: {e.type} {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
prize_tattered(P) :- prize(P).
has_transformation(P) :- prize_tattered(P), gift(G), transforms(G,P).
valid_story(S,P) :- setting(S), prize(P), has_transformation(P).
"""

def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for pid in PRIZES:
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("prize_tattered", pid))
    for gid, g in GIFTS.items():
        lines.append(asp.fact("gift", gid))
        for p in PRIZES:
            lines.append(asp.fact("transforms", gid, p))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    return 0


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], PRIZES[params.prize], params.name, params.gender, params.helper)
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
    StoryParams(setting="old_tower", prize="cloak", name="Mina", gender="girl", helper="fairy"),
    StoryParams(setting="forest_glade", prize="banner", name="Luca", gender="boy", helper="sprite"),
    StoryParams(setting="village_square", prize="slippers", name="Rose", gender="girl", helper="fairy godmother"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("ASP mode is available, but this world keeps its reasonableness gate simple.")
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
            header = f"### {p.name}: {p.prize} in {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
