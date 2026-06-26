#!/usr/bin/env python3
"""
A small storyworld: a child, a misunderstanding, and a mystery to solve in a
ghost-story mood.

Premise:
- A curious child hears odd sounds in an old house.
- They misunderstand the sounds as a ghost.
- They scrounge for clues and plumb the house's hidden places.
- The mystery resolves into a harmless, tender explanation.

This world models:
- physical meters: distance, hiddenness, noise, cold, clutter
- emotional memes: fear, curiosity, relief, trust, confusion
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
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
    location: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.meters = dict(self.meters)
        self.memes = dict(self.memes)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the old house"
    afford: set[str] = field(default_factory=lambda: {"scrounge", "plumb", "wrap_gerund"})


@dataclass
class Mystery:
    id: str
    title: str
    clue: str
    reveal: str
    source_kind: str
    source_label: str


@dataclass
class StoryParams:
    setting: str
    mystery: str
    name: str
    gender: str
    caregiver: str
    trait: str
    seed: Optional[int] = None


SETTINGS = {
    "old_house": Setting(place="the old house", afford={"scrounge", "plumb", "wrap_gerund"}),
    "attic": Setting(place="the attic", afford={"scrounge", "plumb", "wrap_gerund"}),
    "cellar": Setting(place="the cellar", afford={"scrounge", "plumb", "wrap_gerund"}),
}

MYSTERIES = {
    "wind_chimes": Mystery(
        id="wind_chimes",
        title="the mystery of the midnight tapping",
        clue="a soft tapping near the window",
        reveal="wind chimes that clicked against the sill",
        source_kind="object",
        source_label="wind chimes",
    ),
    "loose_pipe": Mystery(
        id="loose_pipe",
        title="the mystery of the sighing wall",
        clue="a slow sigh from under the floor",
        reveal="a loose pipe that hummed when the boiler warmed up",
        source_kind="pipe",
        source_label="a loose pipe",
    ),
    "clock_chain": Mystery(
        id="clock_chain",
        title="the mystery of the rattling dark",
        clue="a tiny rattle from upstairs",
        reveal="an old clock chain swaying in the draft",
        source_kind="clock",
        source_label="an old clock chain",
    ),
}

GIRL_NAMES = ["Maya", "Nina", "Ivy", "Lucy", "Mila"]
BOY_NAMES = ["Eli", "Noah", "Finn", "Theo", "Owen"]
TRAITS = ["curious", "brave", "quiet", "soft-hearted", "careful"]


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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
        c = World(self.setting)
        c.entities = copy.deepcopy(self.entities)
        c.facts = copy.deepcopy(self.facts)
        c.paragraphs = [[]]
        return c


def _mood_up(e: Entity, key: str, amt: float = 1.0) -> None:
    e.memes[key] = e.memes.get(key, 0.0) + amt


def _mood_down(e: Entity, key: str, amt: float = 1.0) -> None:
    e.memes[key] = max(0.0, e.memes.get(key, 0.0) - amt)


def setup_world(params: StoryParams) -> World:
    world = World(SETTINGS[params.setting])
    hero = world.add(Entity(
        id=params.name,
        kind="character",
        type=params.gender,
        label=params.name,
        location=world.setting.place,
        memes={"curiosity": 1.0},
    ))
    caregiver = world.add(Entity(
        id="Caregiver",
        kind="character",
        type=params.caregiver,
        label="the grown-up",
        location=world.setting.place,
        memes={"watchfulness": 1.0},
    ))
    mystery = MYSTERIES[params.mystery]
    source = world.add(Entity(
        id="Source",
        kind="thing",
        type=mystery.source_kind,
        label=mystery.source_label,
        phrase=mystery.reveal,
        location=world.setting.place,
    ))
    world.facts.update(hero=hero, caregiver=caregiver, source=source, mystery=mystery)
    return world


def intro(world: World) -> None:
    hero: Entity = world.facts["hero"]
    world.say(
        f"{hero.id} was a little {next(t for t in ['curious','brave','quiet','soft-hearted','careful'] if t == world.facts.get('trait', 'curious'))} {hero.type} who lived near {world.setting.place}."
    )
    world.say(
        f"At night, the house felt sleepy and strange, and {hero.id} liked listening for tiny sounds in the dark."
    )


def mystery_hook(world: World) -> None:
    hero: Entity = world.facts["hero"]
    mystery: Mystery = world.facts["mystery"]
    _mood_up(hero, "fear")
    _mood_up(hero, "confusion")
    world.say(
        f"One night, {hero.id} heard {mystery.clue}."
    )
    world.say(
        f"{hero.id} thought, for a shaky moment, that a ghost might be hiding in the walls."
    )


def scrounge_for_clues(world: World) -> None:
    hero: Entity = world.facts["hero"]
    source: Entity = world.facts["source"]
    _mood_up(hero, "curiosity")
    world.say(
        f"Instead of running away, {hero.id} began to scrounge for clues with a flashlight and a careful mind."
    )
    world.say(
        f"{hero.id} checked the hallway, then the dusty shelf, and finally the place where the sound kept repeating."
    )
    world.facts["clue_found"] = True
    world.facts["search_path"] = ["hallway", "shelf", "source"]
    source.meters["hiddenness"] = 0.0


def plumb_the_house(world: World) -> None:
    hero: Entity = world.facts["hero"]
    source: Entity = world.facts["source"]
    world.say(
        f"{hero.id} decided to plumb the house's secrets all the way to the floorboards and pipes."
    )
    world.say(
        f"At the end of the search, {hero.id} found that the sound came from {source.phrase}."
    )
    world.facts["reveal"] = True


def wrap_gerund_phrase() -> str:
    return "wrapping a blanket around their shoulders while listening"


def resolution(world: World) -> None:
    hero: Entity = world.facts["hero"]
    caregiver: Entity = world.facts["caregiver"]
    source: Entity = world.facts["source"]
    _mood_down(hero, "fear", 1.0)
    _mood_up(hero, "relief", 1.0)
    _mood_up(hero, "trust", 1.0)
    world.say(
        f"Then {caregiver.label} smiled and showed {hero.id} the truth: the noise was only {source.phrase}."
    )
    world.say(
        f"The ghost was just a misunderstanding, and {hero.id} laughed with relief."
    )
    world.say(
        f"By the end, {hero.id} was {wrap_gerund_phrase()}, and the old house felt warm instead of eerie."
    )
    world.facts["resolved"] = True


def tell_story(params: StoryParams) -> World:
    world = setup_world(params)
    world.facts["trait"] = params.trait
    intro(world)
    world.para()
    mystery_hook(world)
    scrounge_for_clues(world)
    world.para()
    plumb_the_house(world)
    resolution(world)
    return world


def story_qa(world: World) -> list[QAItem]:
    hero: Entity = world.facts["hero"]
    caregiver: Entity = world.facts["caregiver"]
    mystery: Mystery = world.facts["mystery"]
    source: Entity = world.facts["source"]
    return [
        QAItem(
            question=f"What did {hero.id} think the strange sound might be at first?",
            answer="At first, {0} thought it might be a ghost hiding in the walls.".format(hero.id),
        ),
        QAItem(
            question=f"What did {hero.id} do to find out what the noise really was?",
            answer=(
                f"{hero.id} scrounged for clues, looked in several places, and then plumbed the house's secrets until the sound made sense."
            ),
        ),
        QAItem(
            question=f"What was the mystery really caused by?",
            answer=f"It was really caused by {source.phrase}, not by a ghost.",
        ),
        QAItem(
            question=f"How did {hero.id} feel at the end?",
            answer=f"{hero.id} felt relieved and happy because the scary sound turned out to be harmless.",
        ),
        QAItem(
            question=f"Who helped explain the misunderstanding?",
            answer=f"{caregiver.label} helped by showing the truth and calming {hero.id}.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a misunderstanding?",
            answer="A misunderstanding happens when someone thinks something is true, but they are wrong.",
        ),
        QAItem(
            question="What does it mean to solve a mystery?",
            answer="To solve a mystery means to look for clues until you learn what is really happening.",
        ),
        QAItem(
            question="What does it mean to scrounge?",
            answer="To scrounge means to search around for useful things or clues, often in a careful, busy way.",
        ),
        QAItem(
            question="What does it mean to plumb something?",
            answer="To plumb something means to explore it deeply and try to find out its hidden truth.",
        ),
    ]


def generation_prompts(world: World) -> list[str]:
    hero: Entity = world.facts["hero"]
    mystery: Mystery = world.facts["mystery"]
    return [
        f"Write a gentle ghost-story for children about {hero.id} and {mystery.title}.",
        "Tell a short story with a misunderstanding, a clue hunt, and a calm ending image.",
        "Write a spooky-but-kind tale where a child scrounges for clues and plumbs the mystery until the truth is found.",
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        lines.append(f"  {e.id}: kind={e.kind} type={e.type} location={e.location} memes={e.memes} meters={e.meters}")
    lines.append(f"  facts: {sorted(world.facts.keys())}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Ghost-story world: misunderstanding and mystery.")
    ap.add_argument("--setting", choices=SETTINGS.keys())
    ap.add_argument("--mystery", choices=MYSTERIES.keys())
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--caregiver", choices=["mother", "father"])
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
    setting = args.setting or rng.choice(list(SETTINGS.keys()))
    mystery = args.mystery or rng.choice(list(MYSTERIES.keys()))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    caregiver = args.caregiver or rng.choice(["mother", "father"])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(setting=setting, mystery=mystery, name=name, gender=gender, caregiver=caregiver, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell_story(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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


ASP_RULES = r"""
setting(old_house).
setting(attic).
setting(cellar).

mystery(wind_chimes).
mystery(loose_pipe).
mystery(clock_chain).

valid_setting(S) :- setting(S).
valid_mystery(M) :- mystery(M).

#show valid_setting/1.
#show valid_mystery/1.
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for m in MYSTERIES:
        lines.append(asp.fact("mystery", m))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    try:
        import storyworlds.asp as asp
    except Exception as exc:
        print(f"ASP unavailable: {exc}")
        return 1
    model = asp.one_model(asp_program("#show valid_setting/1.\n#show valid_mystery/1."))
    if model:
        print("OK: ASP program solved.")
        return 0
    print("ASP program produced no model.")
    return 1


CURATED = [
    StoryParams(setting="old_house", mystery="wind_chimes", name="Maya", gender="girl", caregiver="mother", trait="curious"),
    StoryParams(setting="attic", mystery="clock_chain", name="Eli", gender="boy", caregiver="father", trait="careful"),
    StoryParams(setting="cellar", mystery="loose_pipe", name="Nina", gender="girl", caregiver="mother", trait="brave"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.verify:
        sys.exit(asp_verify())
    if args.show_asp:
        print(asp_program(""))
        return
    if args.asp:
        print(asp_program("#show valid_setting/1.\n#show valid_mystery/1."))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
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
