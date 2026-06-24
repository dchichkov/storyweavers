#!/usr/bin/env python3
"""
storyworlds/worlds/retrieve_scarf_kindness_humor_heartwarming.py
===============================================================

A small heartwarming story world about a child, a missing scarf, and a kind,
slightly funny search that ends well.

The simulated domain is built from a simple source tale:
a child notices a scarf is missing, asks for help, searches with a helper,
and retrieves it through kindness and a little humor. The story state tracks
where the scarf is, who is looking, what clues they notice, and how their
moods change as the search unfolds.

The world is intentionally narrow:
- one small household setting
- one missing scarf
- one helpful search path
- one gentle resolution

This keeps the prose authored and grounded in state changes rather than in
template swapping.
"""

from __future__ import annotations

import argparse
import dataclasses
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
    held_by: Optional[str] = None
    location: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the house"
    rooms: tuple[str, ...] = ("hall", "bedroom", "laundry room", "cozy chair")


@dataclass
class StoryParams:
    place: str
    name: str
    gender: str
    helper: str
    trait: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[str] = set()
        self.facts: dict[str, object] = {}

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
        clone.entities = dataclasses.replace(self)  # type: ignore[arg-type]
        raise RuntimeError("copy() not used in this world")


def make_entity(word: str, *, kind: str = "character", type_: str = "child") -> Entity:
    return Entity(id=word, kind=kind, type=type_, label=word)


def build_world(params: StoryParams) -> World:
    world = World(SETTING)
    hero = world.add(Entity(
        id=params.name,
        kind="character",
        type=params.gender,
        label=params.name,
        meters={"search": 0.0},
        memes={"worry": 0.0, "kindness": 0.0, "humor": 0.0, "joy": 0.0},
    ))
    helper = world.add(Entity(
        id="Helper",
        kind="character",
        type=params.helper,
        label=params.helper,
        meters={"search": 0.0},
        memes={"kindness": 0.0, "humor": 0.0, "joy": 0.0},
    ))
    scarf = world.add(Entity(
        id="Scarf",
        kind="thing",
        type="scarf",
        label="scarf",
        phrase="a striped scarf with soft tassels",
        owner=hero.id,
        held_by=None,
        location="laundry basket",
    ))
    world.facts.update(hero=hero, helper=helper, scarf=scarf)
    return world


def scene_intro(world: World) -> None:
    hero: Entity = world.facts["hero"]  # type: ignore[assignment]
    scarf: Entity = world.facts["scarf"]  # type: ignore[assignment]
    helper: Entity = world.facts["helper"]  # type: ignore[assignment]

    world.say(
        f"{hero.id} was a little {hero.type} who loved a warm, striped {scarf.label}."
    )
    world.say(
        f"It was the kind of {scarf.label} that made even a chilly morning feel kind."
    )
    hero.memes["kindness"] += 1
    helper.memes["kindness"] += 1


def lose_scarf(world: World) -> None:
    scarf: Entity = world.facts["scarf"]  # type: ignore[assignment]
    hero: Entity = world.facts["hero"]  # type: ignore[assignment]
    scarf.location = "somewhere in the house"
    hero.memes["worry"] += 1
    world.say(
        f"One morning, {hero.id} looked for the {scarf.label} and could not find {scarf.it()}."
    )
    world.say(
        f"{hero.pronoun('subject').capitalize()} checked the chair, the bed, and the basket, but the {scarf.label} was nowhere in sight."
    )


def ask_for_help(world: World) -> None:
    hero: Entity = world.facts["hero"]  # type: ignore[assignment]
    helper: Entity = world.facts["helper"]  # type: ignore[assignment]
    world.say(
        f"{hero.id} asked {helper.label} for help, and {helper.label} smiled right away."
    )
    helper.memes["kindness"] += 1
    hero.memes["kindness"] += 1


def funny_search(world: World) -> None:
    hero: Entity = world.facts["hero"]  # type: ignore[assignment]
    helper: Entity = world.facts["helper"]  # type: ignore[assignment]
    scarf: Entity = world.facts["scarf"]  # type: ignore[assignment]

    world.para()
    world.say(
        f"They searched room by room. In the hall, {helper.label} lifted a hat and said, "
        f'"No scarf here, only a very surprised hat."'
    )
    helper.memes["humor"] += 1
    hero.memes["humor"] += 1
    world.say(
        f"{hero.id} giggled, and the giggle made the search feel less scary."
    )
    world.say(
        f"They looked in the bedroom next, under the blanket, behind the pillow, and by the laundry basket."
    )
    scarf.location = "behind the pillow"
    world.say(
        f"There, tucked behind the pillow, was the {scarf.label}, as quiet as a mouse."
    )


def retrieve_scarf(world: World) -> None:
    hero: Entity = world.facts["hero"]  # type: ignore[assignment]
    helper: Entity = world.facts["helper"]  # type: ignore[assignment]
    scarf: Entity = world.facts["scarf"]  # type: ignore[assignment]

    world.para()
    scarf.held_by = hero.id
    scarf.location = "on the hero's neck"
    hero.memes["worry"] = 0.0
    hero.memes["joy"] += 1
    helper.memes["joy"] += 1
    world.say(
        f"{hero.id} reached in and retrieved the {scarf.label} with gentle hands."
    )
    world.say(
        f"{helper.label} laughed, because the {scarf.label} had been hiding in the easiest place to miss."
    )
    world.say(
        f"{hero.id} wrapped {hero.pronoun('possessive')} {scarf.label} around {hero.pronoun('possessive')} neck and felt warm again."
    )


def ending_image(world: World) -> None:
    hero: Entity = world.facts["hero"]  # type: ignore[assignment]
    helper: Entity = world.facts["helper"]  # type: ignore[assignment]
    scarf: Entity = world.facts["scarf"]  # type: ignore[assignment]

    world.say(
        f"In the end, {hero.id} had the {scarf.label} back, {helper.label} had a smile, "
        f"and the whole house felt a little brighter."
    )


SETTING = Setting(place="the house", rooms=("hall", "bedroom", "laundry room", "cozy chair"))


GIRL_NAMES = ["Mia", "Lily", "Nora", "Ava", "Ruby", "Ella"]
BOY_NAMES = ["Finn", "Leo", "Milo", "Noah", "Ben", "Theo"]
TRAITS = ["gentle", "curious", "cheerful", "patient", "playful"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A heartwarming story world about retrieving a missing scarf."
    )
    ap.add_argument("--place", choices=["house"], default="house")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--helper", choices=["mother", "father", "grandparent", "neighbor"])
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    helper = args.helper or rng.choice(["mother", "father", "grandparent", "neighbor"])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place="house", name=name, gender=gender, helper=helper, trait=trait)


def generation_prompts(world: World) -> list[str]:
    hero: Entity = world.facts["hero"]  # type: ignore[assignment]
    helper: Entity = world.facts["helper"]  # type: ignore[assignment]
    return [
        "Write a short heartwarming story about a child who cannot find a scarf and retrieves it with help.",
        f"Tell a gentle story where {hero.id} loses a scarf, asks {helper.label} for help, and finds it again.",
        "Write a simple story that includes kindness, a little humor, and the recovery of a missing scarf.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero: Entity = world.facts["hero"]  # type: ignore[assignment]
    helper: Entity = world.facts["helper"]  # type: ignore[assignment]
    scarf: Entity = world.facts["scarf"]  # type: ignore[assignment]
    return [
        QAItem(
            question=f"What was {hero.id} looking for?",
            answer=f"{hero.id} was looking for the {scarf.label}.",
        ),
        QAItem(
            question=f"Who helped {hero.id} search?",
            answer=f"{helper.label} helped {hero.id} search for the {scarf.label}.",
        ),
        QAItem(
            question=f"Where did they find the {scarf.label}?",
            answer=f"They found the {scarf.label} behind the pillow.",
        ),
        QAItem(
            question=f"How did the search feel?",
            answer="It felt kind and a little funny, because everyone stayed calm and the helper made a joke about a surprised hat.",
        ),
        QAItem(
            question=f"What changed at the end?",
            answer=f"{hero.id} got the {scarf.label} back, felt warm again, and everyone smiled.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a scarf for?",
            answer="A scarf is a soft piece of clothing worn around the neck to help keep you warm.",
        ),
        QAItem(
            question="Why can a little joke help when someone is upset?",
            answer="A little joke can help because it makes people smile and feel calmer, so a problem feels easier to handle.",
        ),
        QAItem(
            question="What does kindness mean?",
            answer="Kindness means being gentle, helpful, and caring toward someone else.",
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.held_by:
            bits.append(f"held_by={e.held_by}")
        if e.location:
            bits.append(f"location={e.location}")
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    scene_intro(world)
    lose_scarf(world)
    ask_for_help(world)
    funny_search(world)
    retrieve_scarf(world)
    ending_image(world)
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


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = [
        asp.fact("setting", "house"),
        asp.fact("room", "hall"),
        asp.fact("room", "bedroom"),
        asp.fact("room", "laundry_room"),
        asp.fact("room", "cozy_chair"),
        asp.fact("object", "scarf"),
        asp.fact("action", "retrieve"),
        asp.fact("feature", "kindness"),
        asp.fact("feature", "humor"),
        asp.fact("style", "heartwarming"),
    ]
    return "\n".join(lines)


ASP_RULES = r"""
setting_ok(house).
story_theme(retrieve_scarf_kindness_humor_heartwarming).

compatible_story(S) :- setting_ok(S), story_theme(retrieve_scarf_kindness_humor_heartwarming).

#show compatible_story/1.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show compatible_story/1."))
    facts = set(asp.atoms(model, "compatible_story"))
    expected = {("house",)}
    if facts == expected:
        print("OK: ASP gate matches Python reasonableness gate.")
        return 0
    print("MISMATCH: ASP and Python reasonableness gates differ.")
    print("ASP:", sorted(facts))
    print("PY :", sorted(expected))
    return 1


def valid_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.place != "house":
        raise StoryError("This storyworld only supports the house setting.")
    return resolve_params(args, rng)


def generate_all() -> list[StoryParams]:
    out = []
    for gender in ["girl", "boy"]:
        for helper in ["mother", "father", "grandparent", "neighbor"]:
            for trait in TRAITS:
                out.append(StoryParams(place="house", name="Mia" if gender == "girl" else "Finn", gender=gender, helper=helper, trait=trait))
    return out


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show compatible_story/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import storyworlds.asp as asp
        model = asp.one_model(asp_program("#show compatible_story/1."))
        print(sorted(set(asp.atoms(model, "compatible_story"))))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        params_list = generate_all()
        samples = [generate(p) for p in params_list]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            seed = base_seed + i
            i += 1
            try:
                params = valid_params(args, random.Random(seed))
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
