#!/usr/bin/env python3
"""
A standalone storyworld for an ineffable, comedy-leaning transformation mystery.

Premise:
A small, polite magic mishap turns everyday objects or characters into absurdly
different forms. The hero must notice clues, solve who/what caused the change,
and reverse it with a funny but grounded fix.

The world is state-driven:
- bodies and objects have physical meters and emotional memes
- transformations change meters, ownership, usefulness, and mood
- the mystery is solved by tracing clues from a prop, a pattern, and a helper
- the ending proves the change happened and then got resolved
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
    transformed_from: Optional[str] = None
    transformed_to: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def noun(self) -> str:
        return self.label or self.type

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    indoors: bool
    vibe: str


@dataclass
class Mystery:
    id: str
    clue: str
    cause: str
    fix: str
    transformed_type: str
    ending_image: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.facts: dict[str, object] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()

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

        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.facts = dict(self.facts)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        return clone


SETTINGS = {
    "attic": Setting(place="the attic", indoors=True, vibe="dusty"),
    "kitchen": Setting(place="the kitchen", indoors=True, vibe="bright"),
    "garden": Setting(place="the garden shed", indoors=False, vibe="rain-speckled"),
}

MYSTERIES = {
    "teapot_toe": Mystery(
        id="teapot_toe",
        clue="a trail of cinnamon and one tiny blue sticker",
        cause="the blue sticker had drifted into the sparkle fan",
        fix="the fan’s switch needed to be flipped off and the sticker peeled away",
        transformed_type="teapot",
        ending_image="the teapot sat safely on the table again, warm and ordinary",
        tags={"kitchen", "blue", "sticker"},
    ),
    "hat_to_hamster": Mystery(
        id="hat_to_hamster",
        clue="a squeak, a crumb, and a hatband full of sunflower seeds",
        cause="a seed mix had been tucked inside the hat by mistake",
        fix="the seeds had to be tipped out and the hat patted flat",
        transformed_type="hamster",
        ending_image="the hat lay calm on the bench, no longer twitching",
        tags={"hat", "seeds", "squeak"},
    ),
    "spoon_to_star": Mystery(
        id="spoon_to_star",
        clue="a glittery spoon print and a wink of silver dust",
        cause="the spoon had been left beside the moon-salt jar",
        fix="the jar must be closed and the spoon washed once",
        transformed_type="star",
        ending_image="the spoon shone like a spoon again, not a bedtime star",
        tags={"silver", "moon-salt", "spoon"},
    ),
}

HERO_NAMES = ["Mina", "Theo", "Luna", "Nico", "Ari", "Milo"]
HELPER_NAMES = ["Dot", "Pip", "June", "Moss"]
TRAITS = ["curious", "cheerful", "careful", "sly", "gentle"]


ASP_RULES = r"""
entity(hero).
entity(helper).
entity(clue).
entity(cause).
entity(fix).

mystery(M) :- clue(M,_), cause(M,_), fix(M,_).
solved(M) :- mystery(M), clue_seen(M), cause_found(M), fix_done(M).
"""


@dataclass
class StoryParams:
    place: str
    mystery: str
    hero: str
    helper: str
    trait: str
    seed: Optional[int] = None


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if setting.indoors:
            lines.append(asp.fact("indoors", sid))
    for mid, m in MYSTERIES.items():
        lines.append(asp.fact("mystery", mid))
        lines.append(asp.fact("clue", mid, m.clue))
        lines.append(asp.fact("cause", mid, m.cause))
        lines.append(asp.fact("fix", mid, m.fix))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp

    model = asp.one_model(asp_program("#show mystery/1.\n#show solved/1."))
    has_mystery = {a[0] for a in asp.atoms(model, "mystery")}
    if has_mystery == set(MYSTERIES):
        print(f"OK: ASP sees {len(has_mystery)} mysteries.")
        return 0
    print("MISMATCH: ASP did not see all mysteries.")
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="An ineffable transformation mystery comedy world.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--name", choices=HERO_NAMES)
    ap.add_argument("--helper-name", choices=HELPER_NAMES)
    ap.add_argument("--trait", choices=TRAITS)
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


def valid_combo(place: str, mystery: str) -> bool:
    m = MYSTERIES[mystery]
    return place in m.tags or not any(t in SETTINGS[place].vibe for t in ["impossible"])


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    choices = []
    for place in SETTINGS:
        for mystery in MYSTERIES:
            if args.place and place != args.place:
                continue
            if args.mystery and mystery != args.mystery:
                continue
            if not valid_combo(place, mystery):
                continue
            choices.append((place, mystery))
    if not choices:
        raise StoryError("No reasonable mystery matches the given options.")
    place, mystery = rng.choice(choices)
    hero = args.name or rng.choice(HERO_NAMES)
    helper = args.helper_name or rng.choice([n for n in HELPER_NAMES if n != hero])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, mystery=mystery, hero=hero, helper=helper, trait=trait)


def transform(world: World, hero: Entity, mystery: Mystery) -> Entity:
    transformed = world.add(
        Entity(
            id="object",
            kind="thing",
            type=mystery.transformed_type,
            label=mystery.transformed_type,
            phrase=f"a very wrong {mystery.transformed_type}",
            owner=hero.id,
            transformed_from="ordinary_object",
            transformed_to=mystery.transformed_type,
        )
    )
    transformed.meters["odd"] = 1.0
    transformed.meters["attention"] = 1.0
    transformed.memes["embarrassed"] = 1.0
    return transformed


def solve_mystery(world: World, hero: Entity, helper: Entity, mystery: Mystery, transformed: Entity) -> None:
    hero.memes["confused"] = 1.0
    hero.memes["determined"] = 1.0
    helper.memes["amused"] = 1.0
    world.say(
        f"{hero.noun().capitalize()} was {world.setting.vibe} in {world.setting.place}, "
        f"and something utterly {mystery.id.replace('_', ' ')}-ish happened."
    )
    world.say(
        f"Then {hero.noun()} noticed {mystery.clue}, while {helper.noun()} tried not to giggle."
    )
    world.para()
    world.say(
        f'"This is an ineffable problem," {helper.noun()} said, which was a fancy way of saying, '
        f'"That is definitely not a normal {transformed.label}."'
    )
    world.say(
        f"{hero.noun().capitalize()} checked the clue, traced the oddness, and remembered the likely cause: "
        f"{mystery.cause}."
    )
    world.say(
        f"So they did the fix: {mystery.fix}."
    )
    transformed.transformed_to = "ordinary_object"
    transformed.label = "ordinary object"
    transformed.phrase = "an ordinary object"
    transformed.meters["odd"] = 0.0
    transformed.memes["embarrassed"] = 0.0
    hero.memes["relief"] = 1.0
    helper.memes["joy"] = 1.0
    world.para()
    world.say(
        f"At last, {mystery.ending_image}, and {hero.noun()} and {helper.noun()} laughed at the whole affair."
    )
    world.facts.update(
        hero=hero,
        helper=helper,
        mystery=mystery,
        transformed=transformed,
    )


def make_story(world: World, params: StoryParams) -> StorySample:
    hero = world.add(Entity(id=params.hero, kind="character", type="child", label=params.hero))
    helper = world.add(Entity(id=params.helper, kind="character", type="helper", label=params.helper))
    mystery = MYSTERIES[params.mystery]
    transformed = transform(world, hero, mystery)
    solve_mystery(world, hero, helper, mystery, transformed)
    prompts = [
        f"Write a small comedy story about an ineffable transformation mystery in {world.setting.place}.",
        f"Tell a child-friendly story where {hero.id} and {helper.id} solve a strange change with a clue.",
        "Make the ending prove the strange transformation was fixed.",
    ]
    story_qa = [
        QAItem(
            question=f"What strange thing happened to the object in {world.setting.place}?",
            answer=f"It turned into {mystery.transformed_type} for a while, which made the whole scene very silly.",
        ),
        QAItem(
            question=f"What clue helped {hero.id} solve the mystery?",
            answer=f"{mystery.clue.capitalize()}. That clue pointed them toward the real cause.",
        ),
        QAItem(
            question=f"How did they fix the problem?",
            answer=f"They used this fix: {mystery.fix}. After that, the object became ordinary again.",
        ),
    ]
    world_qa = [
        QAItem(
            question="What does a clue do in a mystery?",
            answer="A clue is a little piece of information that helps someone figure out what happened.",
        ),
        QAItem(
            question="What is a transformation?",
            answer="A transformation is a change from one form into another form.",
        ),
    ]
    return StorySample(
        params=params,
        story=world.render(),
        prompts=prompts,
        story_qa=story_qa,
        world_qa=world_qa,
        world=world,
    )


def generate(params: StoryParams) -> StorySample:
    world = World(SETTINGS[params.place])
    return make_story(world, params)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        for i, p in enumerate(sample.prompts, 1):
            print(f"P{i}: {p}")
        print()
        for item in sample.story_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")
        print()
        for item in sample.world_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in world.entities.values():
        lines.append(
            f"{e.id}: type={e.type} meters={{{', '.join(f'{k}:{v}' for k, v in e.meters.items() if v)}}} "
            f"memes={{{', '.join(f'{k}:{v}' for k, v in e.memes.items() if v)}}} "
            f"from={e.transformed_from} to={e.transformed_to}"
        )
    return "\n".join(lines)


CURATED = [
    StoryParams(place="kitchen", mystery="teapot_toe", hero="Mina", helper="Dot", trait="curious"),
    StoryParams(place="attic", mystery="hat_to_hamster", hero="Theo", helper="Pip", trait="cheerful"),
    StoryParams(place="garden", mystery="spoon_to_star", hero="Luna", helper="June", trait="careful"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show mystery/1.\n#show solved/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_program("#show mystery/1.\n#show solved/1."))
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
            rng = random.Random(seed)
            params = resolve_params(args, rng)
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

    for idx, sample in enumerate(samples):
        header = ""
        if len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


def _asp_support() -> None:
    pass


if __name__ == "__main__":
    main()
