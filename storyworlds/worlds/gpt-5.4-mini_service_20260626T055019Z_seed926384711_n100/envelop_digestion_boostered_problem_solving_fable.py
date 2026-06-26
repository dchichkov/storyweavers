#!/usr/bin/env python3
"""
A small fable-style storyworld about a problem-solving animal helping a friend
with digestion by using an envelop of herbs and a boostered plan.

The world is deliberately tiny:
- a hungry animal feels sluggish because digestion is upset
- a wise helper suggests a gentle, practical fix
- the fix uses an envelop of warm leaves and a boostered routine
- the ending proves the change through action and relief

The story is not a frozen template: meters and memes drive the prose.
"""

from __future__ import annotations

import argparse
import dataclasses
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Any, Optional

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
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self):
        if not self.meters:
            self.meters = {"hunger": 0.0, "heaviness": 0.0, "comfort": 0.0, "strength": 0.0}
        if not self.memes:
            self.memes = {"worry": 0.0, "hope": 0.0, "kindness": 0.0, "pride": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        female = {"hare", "rabbit", "doe", "girl", "mother", "woman"}
        male = {"fox", "boy", "father", "man", "badger", "wolf"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def subj(self) -> str:
        return self.pronoun("subject").capitalize()


@dataclass
class Setting:
    place: str = "the hedge garden"
    smell: str = "sweet thyme"
    affords: set[str] = field(default_factory=lambda: {"rest", "tea", "walk"})


@dataclass
class Remedy:
    id: str
    label: str
    phrase: str
    envelops: str
    boosts: str
    comfort_gain: float = 1.0
    hope_gain: float = 1.0


@dataclass
class StoryParams:
    place: str
    hero: str
    helper: str
    remedy: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, Any] = {}
        self.trace_steps: list[str] = []

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)
            self.trace_steps.append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


def _m(e: Entity, key: str, delta: float) -> None:
    e.meters[key] = e.meters.get(key, 0.0) + delta


def _k(e: Entity, key: str, delta: float) -> None:
    e.memes[key] = e.memes.get(key, 0.0) + delta


def symptoms(world: World, hero: Entity) -> list[str]:
    out = []
    if hero.meters["heaviness"] >= THRESHOLD:
        out.append(f"{hero.subj()} felt heavy in the belly.")
    if hero.memes["worry"] >= THRESHOLD:
        out.append(f"{hero.subj()} frowned and worried about the slow digestion.")
    return out


def tell(world: World, hero: Entity, helper: Entity, remedy: Remedy) -> None:
    world.say(
        f"In {world.setting.place}, {hero.id} was a small, kind {hero.type} who liked to share berries and bread."
    )
    world.say(
        f"One morning, {hero.id} felt a dull ache after lunch. {hero.subj()} moved slowly, and digestion felt stuck."
    )
    for s in symptoms(world, hero):
        world.say(s)
    world.para()
    world.say(
        f"{helper.id} came by with a calm smile and said, "
        f'"A small problem can be solved with a small plan."'
    )
    world.say(
        f"{helper.id} found {remedy.phrase}, made an envelop of warm leaves, and said it would help {remedy.envelops} the belly and {remedy.boosts} the day."
    )
    _k(hero, "hope", remedy.hope_gain)
    _k(helper, "kindness", 1.0)
    _m(hero, "comfort", remedy.comfort_gain)
    world.say(
        f"{hero.id} tried the plan: a slow sip, a quiet rest, and a careful walk beside the herbs."
    )
    _m(hero, "strength", 1.0)
    _m(hero, "heaviness", -1.0)
    if hero.meters["heaviness"] <= 0:
        hero.meters["heaviness"] = 0.0
    _k(hero, "worry", -1.0)
    if hero.memes["worry"] <= 0:
        hero.memes["worry"] = 0.0
    _k(hero, "pride", 1.0)
    world.para()
    world.say(
        f"By sunset, {hero.id} could nibble again, and the little one laughed at how a wise, boostered remedy had solved the trouble."
    )
    world.say(
        f"The envelop of leaves lay empty in the grass, and the garden smelled sweet and peaceful."
    )
    world.facts.update(hero=hero, helper=helper, remedy=remedy, setting=world.setting)


SETTINGS = {
    "garden": Setting(place="the hedge garden", smell="sweet thyme", affords={"rest", "tea", "walk"}),
    "orchard": Setting(place="the orchard lane", smell="ripe apples", affords={"rest", "tea", "walk"}),
    "brook": Setting(place="the brookside", smell="wet reeds", affords={"rest", "tea", "walk"}),
}

HEROES = {
    "hare": ("hare", "Holly", ["gentle", "quick"]),
    "fox": ("fox", "Finn", ["clever", "careful"]),
    "badger": ("badger", "Bram", ["steady", "thoughtful"]),
}

HELPERS = {
    "owl": ("owl", "Mira", ["wise", "calm"]),
    "tortoise": ("tortoise", "Tess", ["patient", "kind"]),
    "mouse": ("mouse", "Milo", ["helpful", "small"]),
}

REMEDIES = {
    "tea": Remedy(
        id="tea",
        label="herb tea",
        phrase="a cup of herb tea",
        envelops="envelop",
        boosts="boostered",
        comfort_gain=1.0,
        hope_gain=1.0,
    ),
    "wrap": Remedy(
        id="wrap",
        label="leaf wrap",
        phrase="an herb leaf wrap",
        envelops="envelop",
        boosts="boostered",
        comfort_gain=1.5,
        hope_gain=1.0,
    ),
    "walk": Remedy(
        id="walk",
        label="slow walk",
        phrase="a slow walk by the path",
        envelops="envelop",
        boosts="boostered",
        comfort_gain=0.5,
        hope_gain=1.5,
    ),
}

CURATED = [
    StoryParams(place="garden", hero="hare", helper="owl", remedy="tea"),
    StoryParams(place="orchard", hero="fox", helper="tortoise", remedy="wrap"),
    StoryParams(place="brook", hero="badger", helper="mouse", remedy="walk"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A fable-style storyworld about digestion and problem solving.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--hero", choices=HEROES)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--remedy", choices=REMEDIES)
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or rng.choice(list(SETTINGS))
    hero = args.hero or rng.choice(list(HEROES))
    helper = args.helper or rng.choice(list(HELPERS))
    remedy = args.remedy or rng.choice(list(REMEDIES))
    if args.hero and args.helper and args.hero == "fox" and args.helper == "mouse":
        raise StoryError("A fox and mouse pairing is too tense for this gentle fable.")
    return StoryParams(place=place, hero=hero, helper=helper, remedy=remedy)


def generate(params: StoryParams) -> StorySample:
    setting = SETTINGS[params.place]
    world = World(setting)
    hero_kind, hero_name, hero_traits = HEROES[params.hero]
    helper_kind, helper_name, helper_traits = HELPERS[params.helper]
    remedy = REMEDIES[params.remedy]

    hero = world.add(Entity(id=hero_name, kind="character", type=hero_kind, label=hero_name, traits=hero_traits))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_kind, label=helper_name, traits=helper_traits))

    _m(hero, "heaviness", 1.5)
    _k(hero, "worry", 1.0)

    tell(world, hero, helper, remedy)

    prompts = [
        f"Write a short fable where a {hero.type} named {hero.id} has trouble with digestion and a friend solves it.",
        f"Tell a child-friendly story in which {helper.id} offers a boostered remedy to help {hero.id}.",
        f"Write a gentle animal story that uses the words envelop, digestion, and boostered.",
    ]

    story_qa = [
        QAItem(
            question=f"What problem did {hero.id} have at the beginning?",
            answer=f"{hero.id} had a sore, heavy belly, and digestion felt slow and stuck.",
        ),
        QAItem(
            question=f"Who helped {hero.id} solve the problem?",
            answer=f"{helper.id} helped by choosing a calm, practical remedy.",
        ),
        QAItem(
            question=f"What did the helper use?",
            answer=f"{helper.id} used {remedy.phrase}, making an envelop of herbs that was boostered by a slow, careful plan.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"By the end, {hero.id} felt lighter, could nibble again, and the garden was peaceful.",
        ),
    ]

    world_qa = [
        QAItem(
            question="What does digestion do?",
            answer="Digestion is the body's way of breaking food into smaller parts so the body can use it for energy and growth.",
        ),
        QAItem(
            question="What is an envelop in this story?",
            answer="It is a gentle wrapping or covering made from leaves or herbs that helps hold warmth and comfort close.",
        ),
        QAItem(
            question="What does boostered mean here?",
            answer="It means given a helpful extra lift, like a small plan that makes a remedy work better.",
        ),
    ]

    return StorySample(params=params, story=world.render(), prompts=prompts, story_qa=story_qa, world_qa=world_qa, world=world)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print()
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: round(v, 3) for k, v in e.meters.items() if abs(v) > 1e-9}
        memes = {k: round(v, 3) for k, v in e.memes.items() if abs(v) > 1e-9}
        lines.append(f"  {e.id:8} ({e.type:8}) meters={meters} memes={memes}")
    lines.append(f"  facts: {world.facts.keys()}")
    return "\n".join(lines)


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


ASP_RULES = r"""
% A simple declarative twin for the reasonableness of this fable.
has_problem(H) :- hungry(H), heavy_belly(H).
has_fix(H,R) :- has_problem(H), remedy(R), helps(R,H).
solvable(H) :- has_problem(H), has_fix(H,_).
compatible(Place,Hero,Helper,Remedy) :- setting(Place), hero(Hero), helper(Helper), remedy(Remedy), solvable(Hero).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for a in sorted(setting.affords):
            lines.append(asp.fact("affords", sid, a))
    for hid, (typ, _, _) in HEROES.items():
        lines.append(asp.fact("hero", hid))
        lines.append(asp.fact("hero_type", hid, typ))
    for hid, (typ, _, _) in HELPERS.items():
        lines.append(asp.fact("helper", hid))
        lines.append(asp.fact("helper_type", hid, typ))
    for rid in REMEDIES:
        lines.append(asp.fact("remedy", rid))
    lines.append(asp.fact("hungry", "hero"))
    lines.append(asp.fact("heavy_belly", "hero"))
    lines.append(asp.fact("helps", "tea", "hero"))
    lines.append(asp.fact("helps", "wrap", "hero"))
    lines.append(asp.fact("helps", "walk", "hero"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    program = asp_program("#show solvable/1.")
    model = asp.one_model(program)
    atoms = set(asp.atoms(model, "solvable"))
    if atoms == {("hero",)}:
        print("OK: ASP twin recognizes the problem-solving fable shape.")
        return 0
    print("MISMATCH: ASP twin did not recognize the intended story shape.")
    return 1


def asp_list() -> list[tuple]:
    import asp
    program = asp_program("#show compatible/4.")
    model = asp.one_model(program)
    return sorted(set(asp.atoms(model, "compatible")))


def generation_choices(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return resolve_params(args, rng)


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show compatible/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        tuples = asp_list()
        for t in tuples:
            print(t)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 40, 40):
            rng = random.Random(base_seed + i)
            i += 1
            params = generation_choices(args, rng)
            params.seed = base_seed + i
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
            header = f"### {p.place} / {p.hero} / {p.helper} / {p.remedy}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
