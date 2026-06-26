#!/usr/bin/env python3
"""
storyworlds/worlds/contents_spread_commodity_misunderstanding_problem_solving_magic.py
======================================================================================

A tall-tale storyworld about a market day, a magical commodity, and a
misunderstanding that gets solved with cleverness and a little magic.

The seed ideas are:
- contents
- spread
- commodity
- misunderstanding
- problem solving
- magic

This world tells stories about a small town that fears its one precious crate
of honey-spread has been ruined, then discovers that the trouble is only a
misunderstanding. A magical helper and a patient fix turn panic into a feast.
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
    plural: bool = False
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"mess": 0.0, "safe": 0.0}
        if not self.memes:
            self.memes = {"joy": 0.0, "fear": 0.0, "confusion": 0.0, "relief": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        feminine = {"girl", "mother", "mom", "woman"}
        masculine = {"boy", "father", "dad", "man"}
        if self.type in feminine:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in masculine:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    indoor: bool = False
    affords: set[str] = field(default_factory=set)


@dataclass
class Commodity:
    id: str
    label: str
    phrase: str
    mess: str
    zone: set[str]
    taste: str
    keyword: str


@dataclass
class Helper:
    id: str
    label: str
    magic: bool
    fix: str
    tail: str


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
        import copy as _copy
        w = World(self.setting)
        w.entities = _copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        return w

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]


@dataclass
class StoryParams:
    place: str
    commodity: str
    hero: str
    hero_type: str
    elder: str
    seed: Optional[int] = None


SETTINGS = {
    "market": Setting(place="the town market", affords={"jam", "honey", "bread"}),
    "barn": Setting(place="the red barn", affords={"hay", "honey"}),
    "kitchen": Setting(place="the sunny kitchen", indoor=True, affords={"jam", "bread"}),
}

COMMODITIES = {
    "honey": Commodity(
        id="honey",
        label="honey",
        phrase="a jar of golden honey",
        mess="sticky",
        zone={"hands", "table"},
        taste="sweet",
        keyword="honey",
    ),
    "jam": Commodity(
        id="jam",
        label="jam",
        phrase="a jar of bright berry jam",
        mess="sticky",
        zone={"hands", "table"},
        taste="sweet",
        keyword="jam",
    ),
    "bread": Commodity(
        id="bread",
        label="bread",
        phrase="a loaf of crusty bread",
        mess="crumbly",
        zone={"hands", "table"},
        taste="warm",
        keyword="bread",
    ),
    "hay": Commodity(
        id="hay",
        label="hay",
        phrase="a bale of high hay",
        mess="dusty",
        zone={"hands", "floor"},
        taste="dry",
        keyword="hay",
    ),
}

HELPERS = [
    Helper(
        id="mira",
        label="Mira the moon-spark mage",
        magic=True,
        fix="cast a glittering doubling spell",
        tail="twirled her finger and made the missing contents appear in two neat heaps",
    ),
    Helper(
        id="uncle_jeb",
        label="Uncle Jeb the wagon fixer",
        magic=False,
        fix="sort the crates by hand",
        tail="counted every last jar and set the whole load in order",
    ),
]

HEROES = ["Pip", "Nora", "Toby", "Lena", "Molly", "Benny"]
ELDERS = ["Grandpa", "Aunt Bee", "Old Tom", "Mamma June", "Uncle Reed"]
TRAITS = ["lively", "spirited", "curious", "cheerful", "stubborn"]


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for commodity in setting.affords:
            combos.append((place, commodity))
    return combos


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if s.indoor:
            lines.append(asp.fact("indoor", sid))
        for c in sorted(s.affords):
            lines.append(asp.fact("affords", sid, c))
    for cid, c in COMMODITIES.items():
        lines.append(asp.fact("commodity", cid))
        lines.append(asp.fact("mess_of", cid, c.mess))
        for z in sorted(c.zone):
            lines.append(asp.fact("spreads_over", cid, z))
    for h in HELPERS:
        lines.append(asp.fact("helper", h.id))
        if h.magic:
            lines.append(asp.fact("magic_helper", h.id))
    return "\n".join(lines)


ASP_RULES = r"""
at_risk(C, P) :- commodity(C), spreads_over(C, Z), worn_on(P, Z).
valid(Place, C) :- affords(Place, C), commodity(C).
magic_fix(C) :- valid(_, C), at_risk(C, _), magic_helper(_).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Tall-tale storyworld: a commodity, a misunderstanding, and a magic fix."
    )
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--commodity", choices=COMMODITIES)
    ap.add_argument("--name")
    ap.add_argument("--elder", choices=ELDERS)
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
              if (args.place is None or c[0] == args.place)
              and (args.commodity is None or c[1] == args.commodity)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, commodity = rng.choice(sorted(combos))
    hero = args.name or rng.choice(HEROES)
    elder = args.elder or rng.choice(ELDERS)
    return StoryParams(place=place, commodity=commodity, hero=hero, hero_type="child", elder=elder)


def _story(world: World, hero: Entity, elder: Entity, commodity: Entity, helper: Entity) -> None:
    world.say(
        f"{hero.id} was a little {rng_trait := 'curious'} child with a nose for any good bargain, "
        f"and {elder.label} said {hero.pronoun('possessive')} eyes could spot a shiny nickel from the next county."
    )
    world.say(
        f"At {world.setting.place}, the finest thing on the whole wagon was {commodity.phrase}, "
        f"the town's favorite commodity, sweet as a song and shiny as sunrise."
    )
    world.para()
    world.say(
        f"Then came a mighty misunderstanding. A vendor shouted, \"Spread the contents!\" and half the crowd "
        f"thought he meant to smear the jar all over the counter."
    )
    world.say(
        f"{hero.id} frowned, {elder.label} gasped, and the people near the stall feared the {commodity.label} "
        f"would be lost before noon."
    )
    hero.memes["confusion"] += 1
    elder.memes["fear"] += 1
    commodity.meters["mess"] += 1
    world.para()
    if helper.magic:
        world.say(
            f"Just then, {helper.label} came striding in with a hat full of starlight and a grin wide enough to shade the barn."
        )
        world.say(
            f"{helper.label} understood the trouble at once. {helper.fix}, and {helper.tail}."
        )
        world.say(
            f"The crowd blinked hard as two tidy piles of {commodity.label} appeared where one worried jar had stood."
        )
        hero.memes["joy"] += 1
        hero.memes["relief"] += 1
        elder.memes["relief"] += 1
        commodity.meters["safe"] += 1
    else:
        world.say(
            f"{helper.label} did not use magic, but {helper.label} understood the trouble at once and {helper.fix}."
        )
        world.say(
            f"Once the words were sorted, everybody saw the jar had never been ruined at all."
        )
        hero.memes["joy"] += 1
        elder.memes["relief"] += 1
        commodity.meters["safe"] += 1
    world.para()
    world.say(
        f"In the end, the vendor smiled and handed out warm bread, and the whole town learned that a loud word "
        f"can cause more trouble than a storm cloud."
    )
    world.say(
        f"{hero.id} went home proud, {commodity.label} still shining, and the market full of laughter as wide as a prairie sky."
    )


def generate_world(params: StoryParams) -> World:
    setting = SETTINGS[params.place]
    commodity = COMMODITIES[params.commodity]
    world = World(setting)
    hero = world.add(Entity(id=params.hero, kind="character", type=params.hero_type))
    elder = world.add(Entity(id="elder", kind="character", type="elder", label=params.elder))
    item = world.add(Entity(id="commodity", type=commodity.id, label=commodity.label, phrase=commodity.phrase))
    helper = world.add(Entity(id="helper", kind="character", type="woman", label=HELPERS[0].label))

    _story(world, hero, elder, item, helper)
    world.facts.update(hero=hero, elder=elder, item=item, commodity=commodity, helper=HELPERS[0], setting=setting)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    c = f["commodity"]
    return [
        f'Write a tall tale for a child about a misunderstanding involving the word "spread" and the commodity "{c.label}".',
        f"Tell a magical market story where {f['hero'].id} hears a warning wrong, then solves the problem with help.",
        f"Write a funny story in which contents, spread, and commodity all matter, and magic clears up the confusion.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    elder = f["elder"]
    item = f["item"]
    qa = [
        QAItem(
            question=f"Why did {hero.id} and {elder.label} worry at the market?",
            answer=(
                f"They worried because a shout about spreading the contents sounded like the {item.label} might get smeared or lost. "
                f"It was a misunderstanding, not a disaster."
            ),
        ),
        QAItem(
            question=f"What did the magical helper do to solve the problem?",
            answer=(
                f"The helper used magic to sort the trouble out and make the {item.label} appear in neat, safe order again."
            ),
        ),
        QAItem(
            question=f"What was special about the commodity in the story?",
            answer=(
                f"The commodity was {f['commodity'].phrase}, and it was the town's favorite sweet market treasure."
            ),
        ),
    ]
    if f["helper"].magic:
        qa.append(QAItem(
            question="How did the story end for the town?",
            answer=(
                "The town ended happy, because the confusion was cleared up, the commodity stayed safe, and everyone got to laugh about the big mistake."
            ),
        ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    c = f["commodity"]
    out = [
        QAItem(question="What does commodity mean?", answer="A commodity is a useful thing that people buy, sell, or trade, like food or cloth."),
        QAItem(question="What does spread mean?", answer="Spread can mean to lay something out, move it wider, or share it with others."),
    ]
    if c.id == "honey":
        out.append(QAItem(question="What is honey?", answer="Honey is a sweet, sticky food made by bees from flower nectar."))
    if c.id == "jam":
        out.append(QAItem(question="What is jam?", answer="Jam is a sweet fruit spread cooked until it turns thick and shiny."))
    return out


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
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = generate_world(params)
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
    StoryParams(place="market", commodity="honey", hero="Pip", hero_type="boy", elder="Grandpa"),
    StoryParams(place="kitchen", commodity="jam", hero="Nora", hero_type="girl", elder="Aunt Bee"),
    StoryParams(place="barn", commodity="honey", hero="Toby", hero_type="boy", elder="Old Tom"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:\n")
        for place, commodity in combos:
            print(f"  {place:10} {commodity}")
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
            header = f"### {p.hero}: {p.commodity} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
