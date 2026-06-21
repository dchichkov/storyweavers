#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/napkin_medal_bad_ending_animal_story.py
==================================================================

A standalone storyworld about a small animal who wants to keep a shiny medal
clean at a picnic, makes an unwise choice with a napkin, and ends up losing the
medal in a bad ending. The world model prefers a tight set of plausible stories:
a napkin can wrap a medal, wind can tug a loose napkin, and a careful helper can
prevent trouble only in some combinations.

The story shape is state-driven:
- setup: picnic play and pride in the medal
- tension: snack time creates a sticky problem
- turn: the hero chooses a risky cleanup or wrapping idea
- resolution: with a bad ending, the medal blows or rolls away and is lost

Run it
------
    python storyworlds/worlds/gpt-5.4/napkin_medal_bad_ending_animal_story.py
    python storyworlds/worlds/gpt-5.4/napkin_medal_bad_ending_animal_story.py --hero fox --place hill
    python storyworlds/worlds/gpt-5.4/napkin_medal_bad_ending_animal_story.py --wind still
    python storyworlds/worlds/gpt-5.4/napkin_medal_bad_ending_animal_story.py --all
    python storyworlds/worlds/gpt-5.4/napkin_medal_bad_ending_animal_story.py --qa --json
    python storyworlds/worlds/gpt-5.4/napkin_medal_bad_ending_animal_story.py --verify
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

# Make the shared result containers importable when this script is run directly.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
RISK_MIN = 1


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        male = {"boy", "father", "dad", "man", "fox_m", "bear_m", "rabbit_m", "beaver_m", "otter_m"}
        female = {"girl", "mother", "mom", "woman", "fox_f", "bear_f", "rabbit_f", "beaver_f", "otter_f"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class AnimalKind:
    id: str
    noun: str
    home: str
    snack: str
    step: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Place:
    id: str
    label: str
    ground: str
    edge: str
    loss_place: str
    spread: int
    tags: set[str] = field(default_factory=set)


@dataclass
class Wind:
    id: str
    adjective: str
    gust_word: str
    power: int
    tags: set[str] = field(default_factory=set)


@dataclass
class Choice:
    id: str
    label: str
    wraps_medal: bool
    ties_tight: bool
    rubs_sticky: bool
    risk: int
    intro: str
    bad_turn: str
    lesson: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
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
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def medal_in_danger(choice: Choice, wind: Wind) -> bool:
    return choice.wraps_medal and (choice.risk + wind.power) >= RISK_MIN and not choice.ties_tight


def medal_lost(place: Place, choice: Choice, wind: Wind) -> bool:
    return medal_in_danger(choice, wind) and (place.spread + wind.power + choice.risk) >= 3


def _r_sticky_to_worry(world: World) -> list[str]:
    hero = world.get("hero")
    if hero.meters["sticky"] < THRESHOLD:
        return []
    sig = ("sticky_worry", "hero")
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["worry"] += 1
    return []


def _r_loose_wrap(world: World) -> list[str]:
    medal = world.get("medal")
    napkin = world.get("napkin")
    wind = world.get("wind")
    if medal.meters["wrapped"] < THRESHOLD or napkin.meters["loose"] < THRESHOLD:
        return []
    if wind.meters["gust"] < THRESHOLD:
        return []
    sig = ("gust_pulls", "medal")
    if sig in world.fired:
        return []
    world.fired.add(sig)
    medal.meters["moving"] += 1
    medal.meters["danger"] += 1
    return []


def _r_roll_or_blow(world: World) -> list[str]:
    medal = world.get("medal")
    place = world.get("place")
    if medal.meters["moving"] < THRESHOLD:
        return []
    sig = ("lost", "medal")
    if sig in world.fired:
        return []
    world.fired.add(sig)
    medal.meters["lost"] += 1
    place.meters["searched"] += 1
    return []


CAUSAL_RULES = [
    Rule(name="sticky_worry", tag="emotion", apply=_r_sticky_to_worry),
    Rule(name="gust_pulls", tag="physical", apply=_r_loose_wrap),
    Rule(name="lost", tag="physical", apply=_r_roll_or_blow),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for sent in produced:
            world.say(sent)
    return produced


ANIMALS = {
    "rabbit": AnimalKind(
        id="rabbit",
        noun="rabbit",
        home="burrow",
        snack="jam bun",
        step="quick little hops",
        tags={"rabbit", "picnic"},
    ),
    "fox": AnimalKind(
        id="fox",
        noun="fox",
        home="den",
        snack="berry tart",
        step="light quick paws",
        tags={"fox", "picnic"},
    ),
    "beaver": AnimalKind(
        id="beaver",
        noun="beaver",
        home="lodge",
        snack="apple slice stack",
        step="flat busy feet",
        tags={"beaver", "picnic"},
    ),
    "otter": AnimalKind(
        id="otter",
        noun="otter",
        home="nest by the reeds",
        snack="honey biscuit",
        step="slippery little steps",
        tags={"otter", "picnic"},
    ),
}

PLACES = {
    "hill": Place(
        id="hill",
        label="the sunny hill",
        ground="short green grass",
        edge="the slope",
        loss_place="down the long hill",
        spread=2,
        tags={"hill", "outside"},
    ),
    "riverbank": Place(
        id="riverbank",
        label="the riverbank",
        ground="smooth pebbles",
        edge="the water's edge",
        loss_place="between the pebbles and into the reeds",
        spread=2,
        tags={"river", "outside"},
    ),
    "meadow": Place(
        id="meadow",
        label="the flower meadow",
        ground="soft flowers and grass",
        edge="the thick daisies",
        loss_place="under the flowers",
        spread=1,
        tags={"meadow", "outside"},
    ),
}

WINDS = {
    "still": Wind(
        id="still",
        adjective="still",
        gust_word="hardly stirred",
        power=0,
        tags={"still"},
    ),
    "breezy": Wind(
        id="breezy",
        adjective="breezy",
        gust_word="gave one playful tug",
        power=1,
        tags={"wind"},
    ),
    "gusty": Wind(
        id="gusty",
        adjective="gusty",
        gust_word="gave a strong naughty yank",
        power=2,
        tags={"wind", "gust"},
    ),
}

CHOICES = {
    "wipe_and_wear": Choice(
        id="wipe_and_wear",
        label="wipe the sticky paws and keep wearing the medal",
        wraps_medal=False,
        ties_tight=False,
        rubs_sticky=True,
        risk=0,
        intro="used the napkin to wipe the jam from the ribbon and from the little paws",
        bad_turn="The medal stayed on, but the ribbon turned slick and slid.",
        lesson="A sticky ribbon is not safer just because it looks cleaner.",
        tags={"napkin", "medal", "sticky"},
    ),
    "wrap_loose": Choice(
        id="wrap_loose",
        label="wrap the medal in a napkin and tuck it under one arm",
        wraps_medal=True,
        ties_tight=False,
        rubs_sticky=False,
        risk=1,
        intro="folded the medal inside the napkin and tucked the bundle under one small arm",
        bad_turn="The napkin was soft and loose, not a pocket and not a box.",
        lesson="A napkin can hide something shiny, but it cannot hold it safely in the wind.",
        tags={"napkin", "medal", "wind"},
    ),
    "swing_bundle": Choice(
        id="swing_bundle",
        label="wrap the medal in a napkin and swing it by one corner",
        wraps_medal=True,
        ties_tight=False,
        rubs_sticky=False,
        risk=2,
        intro="twisted the napkin around the medal and swung it like a tiny white flag",
        bad_turn="A napkin corner is a poor handle for something hard and heavy.",
        lesson="Showing off with a loose bundle makes a small problem into a bigger one.",
        tags={"napkin", "medal", "wind"},
    ),
}


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for animal_id in ANIMALS:
        for place_id, place in PLACES.items():
            for wind_id, wind in WINDS.items():
                for choice_id, choice in CHOICES.items():
                    if medal_lost(place, choice, wind):
                        combos.append((animal_id, place_id, wind_id, choice_id))
    return combos


@dataclass
class StoryParams:
    hero: str
    name: str
    helper_name: str
    place: str
    wind: str
    choice: str
    medal_kind: str
    seed: Optional[int] = None


CURATED = [
    StoryParams(
        hero="rabbit",
        name="Pip",
        helper_name="Moss",
        place="hill",
        wind="gusty",
        choice="wrap_loose",
        medal_kind="racing",
    ),
    StoryParams(
        hero="fox",
        name="Fern",
        helper_name="Brindle",
        place="riverbank",
        wind="gusty",
        choice="swing_bundle",
        medal_kind="berry-pie",
    ),
    StoryParams(
        hero="otter",
        name="Tumble",
        helper_name="Reed",
        place="meadow",
        wind="breezy",
        choice="swing_bundle",
        medal_kind="diving",
    ),
]


def pick_names(animal_id: str) -> tuple[str, str]:
    pools = {
        "rabbit": [("Pip", "Moss"), ("Nib", "Clover"), ("Bramble", "Fern")],
        "fox": [("Fern", "Bramble"), ("Rusty", "Moss"), ("Poppy", "Shade")],
        "beaver": [("Chip", "Twig"), ("Maple", "Ripple"), ("Nettle", "Dock")],
        "otter": [("Tumble", "Reed"), ("Pebble", "Willow"), ("Drift", "Minnow")],
    }
    return random.choice(pools[animal_id])


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Animal-story world: a picnic, a napkin, a medal, and a bad ending."
    )
    ap.add_argument("--hero", choices=ANIMALS)
    ap.add_argument("--name")
    ap.add_argument("--helper-name")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--wind", choices=WINDS)
    ap.add_argument("--choice", choices=CHOICES)
    ap.add_argument("--medal-kind", choices=["racing", "berry-pie", "diving", "dancing"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid bad-ending combos from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def explain_rejection(place: Place, wind: Wind, choice: Choice) -> str:
    if not medal_in_danger(choice, wind):
        return (
            f"(No story: with {wind.adjective} air, choosing '{choice.id}' does not put the medal in danger. "
            f"This world only tells versions where the napkin choice can really send the medal away.)"
        )
    return (
        f"(No story: at {place.label}, choosing '{choice.id}' in {wind.adjective} air is risky, "
        f"but not risky enough to lose the medal. Pick a windier place or a looser choice.)"
    )


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [
        combo for combo in valid_combos()
        if (args.hero is None or combo[0] == args.hero)
        and (args.place is None or combo[1] == args.place)
        and (args.wind is None or combo[2] == args.wind)
        and (args.choice is None or combo[3] == args.choice)
    ]
    if args.place and args.wind and args.choice:
        place = PLACES[args.place]
        wind = WINDS[args.wind]
        choice = CHOICES[args.choice]
        if not medal_lost(place, choice, wind):
            raise StoryError(explain_rejection(place, wind, choice))
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    hero_id, place_id, wind_id, choice_id = rng.choice(sorted(combos))
    name_default, helper_default = {
        "rabbit": [("Pip", "Moss"), ("Nib", "Clover"), ("Bramble", "Fern")],
        "fox": [("Fern", "Bramble"), ("Rusty", "Moss"), ("Poppy", "Shade")],
        "beaver": [("Chip", "Twig"), ("Maple", "Ripple"), ("Nettle", "Dock")],
        "otter": [("Tumble", "Reed"), ("Pebble", "Willow"), ("Drift", "Minnow")],
    }[hero_id][rng.randrange(3)]
    return StoryParams(
        hero=hero_id,
        name=args.name or name_default,
        helper_name=args.helper_name or helper_default,
        place=place_id,
        wind=wind_id,
        choice=choice_id,
        medal_kind=args.medal_kind or rng.choice(["racing", "berry-pie", "diving", "dancing"]),
    )


def introduce(world: World, hero: Entity, helper: Entity, animal: AnimalKind, place: Place, medal_kind: str) -> None:
    hero.memes["pride"] += 1
    world.say(
        f"{hero.id} the little {animal.noun} lived in a cozy {animal.home}. "
        f"One bright afternoon, {hero.pronoun()} went with {helper.id} to {place.label} for a picnic."
    )
    world.say(
        f"A round {medal_kind} medal hung on a ribbon across {hero.pronoun('possessive')} chest. "
        f"{hero.id} had won it that morning and kept touching it to make sure it was real."
    )


def picnic(world: World, hero: Entity, helper: Entity, animal: AnimalKind, place: Place, wind: Wind) -> None:
    hero.memes["joy"] += 1
    world.say(
        f"They sat on {place.ground}, shared {animal.snack}, and laughed whenever the air {wind.gust_word} at the picnic cloth."
    )
    world.say(
        f'"Do not drop your medal," {helper.id} said. "{place.edge.capitalize()} is a terrible place to chase shiny things."'
    )


def sticky_problem(world: World, hero: Entity, animal: AnimalKind) -> None:
    hero.meters["sticky"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Soon a bit of sweet jam got on the ribbon and on {hero.pronoun('possessive')} paws. "
        f"{hero.id} did not like the sticky feeling at all."
    )


def risky_choice(world: World, hero: Entity, helper: Entity, choice: Choice) -> None:
    hero.memes["impulse"] += 1
    napkin = world.get("napkin")
    medal = world.get("medal")
    world.say(
        f"Beside the lunch basket lay a white napkin. Instead of asking {helper.id} for help, "
        f"{hero.id} {choice.intro}."
    )
    if choice.wraps_medal:
        napkin.meters["used"] += 1
        medal.meters["wrapped"] += 1
        napkin.meters["loose"] += 1
    if choice.rubs_sticky:
        medal.meters["slick"] += 1
    world.facts["choice_text"] = choice.label


def helper_warning(world: World, helper: Entity, hero: Entity, choice: Choice, wind: Wind) -> None:
    worry = "too loose" if choice.wraps_medal else "too slippery"
    world.say(
        f'{helper.id} blinked. "That napkin looks {worry}," {helper.pronoun()} warned. '
        f'"And the {wind.adjective} air is not being gentle today."'
    )
    hero.memes["stubborn"] += 1
    world.say(
        f'But {hero.id} lifted {hero.pronoun("possessive")} chin. "I can manage it myself," {hero.pronoun()} said.'
    )


def trigger_loss(world: World, hero: Entity, place: Place, wind: Wind, choice: Choice) -> None:
    wind_ent = world.get("wind")
    wind_ent.meters["gust"] += float(wind.power > 0)
    propagate(world, narrate=False)
    medal = world.get("medal")
    if choice.wraps_medal:
        world.say(
            f"Then the wind {wind.gust_word} at the napkin. {choice.bad_turn} "
            f"The bundle slipped from {hero.pronoun('possessive')} grasp and shot {place.loss_place}."
        )
    else:
        medal.meters["moving"] += 1
        medal.meters["lost"] += 1
        world.say(
            f"{choice.bad_turn} The ribbon slithered off {hero.pronoun('possessive')} neck, "
            f"and the medal rolled {place.loss_place} before anyone could grab it."
        )


def search_and_fail(world: World, hero: Entity, helper: Entity, place: Place) -> None:
    hero.memes["fear"] += 1
    hero.memes["sadness"] += 1
    helper.memes["sadness"] += 1
    world.say(
        f"{hero.id} and {helper.id} ran after it with {hero.attrs['step']}, searching near {place.edge} and under every leaf."
    )
    world.say(
        f"But the medal was gone. The bright little prize was too small, and {place.label} was too big."
    )


def bad_ending(world: World, hero: Entity, helper: Entity, choice: Choice) -> None:
    hero.memes["lesson"] += 1
    world.say(
        f"{hero.id} sat down on the picnic blanket and held the empty napkin in both paws. "
        f"{helper.id} put an arm around {hero.pronoun('object')}, but that did not bring the medal back."
    )
    world.say(
        f"On the walk home, the little animal did not skip or sing. {choice.lesson} "
        f"{hero.id} had wanted to save the shiny medal, and instead {hero.pronoun()} had lost it."
    )


def tell(params: StoryParams) -> World:
    if params.hero not in ANIMALS:
        raise StoryError(f"(Unknown hero: {params.hero})")
    if params.place not in PLACES:
        raise StoryError(f"(Unknown place: {params.place})")
    if params.wind not in WINDS:
        raise StoryError(f"(Unknown wind: {params.wind})")
    if params.choice not in CHOICES:
        raise StoryError(f"(Unknown choice: {params.choice})")

    animal = ANIMALS[params.hero]
    place = PLACES[params.place]
    wind = WINDS[params.wind]
    choice = CHOICES[params.choice]
    if not medal_lost(place, choice, wind):
        raise StoryError(explain_rejection(place, wind, choice))

    world = World()
    hero = world.add(Entity(
        id=params.name,
        kind="character",
        type=f"{params.hero}_m",
        label=params.name,
        role="hero",
        attrs={"animal": animal.noun, "step": animal.step},
        tags=set(animal.tags),
    ))
    helper = world.add(Entity(
        id=params.helper_name,
        kind="character",
        type="friend",
        label=params.helper_name,
        role="helper",
    ))
    world.add(Entity(id="medal", type="medal", label="medal", phrase=f"{params.medal_kind} medal", tags={"medal"}))
    world.add(Entity(id="napkin", type="napkin", label="napkin", phrase="white napkin", tags={"napkin"}))
    world.add(Entity(id="wind", type="wind", label=wind.adjective, phrase=wind.adjective, tags=set(wind.tags)))
    world.add(Entity(id="place", type="place", label=place.label, phrase=place.label, tags=set(place.tags)))

    introduce(world, hero, helper, animal, place, params.medal_kind)
    picnic(world, hero, helper, animal, place, wind)

    world.para()
    sticky_problem(world, hero, animal)
    risky_choice(world, hero, helper, choice)
    helper_warning(world, helper, hero, choice, wind)

    world.para()
    trigger_loss(world, hero, place, wind, choice)
    search_and_fail(world, hero, helper, place)

    world.para()
    bad_ending(world, hero, helper, choice)

    world.facts.update(
        hero=hero,
        helper=helper,
        animal=animal,
        place_cfg=place,
        wind_cfg=wind,
        choice_cfg=choice,
        medal_kind=params.medal_kind,
        lost=world.get("medal").meters["lost"] >= THRESHOLD,
        outcome="lost",
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    animal = f["animal"]
    place = f["place_cfg"]
    choice = f["choice_cfg"]
    medal_kind = f["medal_kind"]
    return [
        'Write a short animal story for a 3-to-5-year-old that includes the words "napkin" and "medal" and has a bad ending.',
        f"Tell a gentle but sad story about a little {animal.noun} named {hero.id} who takes a {medal_kind} medal to {place.label} and makes one risky choice with a napkin.",
        f"Write an animal story where a shiny prize seems safe at first, but {choice.label} turns into a loss by the end.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    animal = f["animal"]
    place = f["place_cfg"]
    wind = f["wind_cfg"]
    choice = f["choice_cfg"]
    medal_kind = f["medal_kind"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id}, a little {animal.noun}, and {helper.id}, a friend at a picnic. "
            f"{hero.id} is proud of a shiny {medal_kind} medal."
        ),
        (
            "Why did the medal become a problem during the picnic?",
            f"Jam made the ribbon and paws sticky, so {hero.id} worried about the medal getting messy. "
            f"That sticky problem pushed {hero.pronoun('object')} toward a quick choice with the napkin."
        ),
        (
            f"What did {hero.id} do with the napkin?",
            f"{hero.id} decided to {choice.label}. {choice.lesson}"
        ),
        (
            f"Why did {helper.id} warn {hero.id}?",
            f"{helper.id} could see that the napkin plan was unsafe in the {wind.adjective} air. "
            f"The warning came before the medal slipped away, but {hero.id} did not listen."
        ),
        (
            "How did the story end?",
            f"It ended sadly because the medal was lost at {place.label}. "
            f"{hero.id} went home without the prize and with a heavy, sorry heart."
        ),
    ]
    return qa


KNOWLEDGE = {
    "napkin": [
        (
            "What is a napkin?",
            "A napkin is a soft piece of cloth or paper used to wipe hands and faces during meals. It is good for cleaning small messes, but it is not a safe bag for carrying heavy things.",
        )
    ],
    "medal": [
        (
            "What is a medal?",
            "A medal is a small prize, often made of metal, given for doing something well. People often wear it on a ribbon around the neck.",
        )
    ],
    "wind": [
        (
            "Why can wind carry light things away?",
            "Wind pushes on light things like paper, leaves, and loose cloth. If something is not held tightly, a gust can tug it away very quickly.",
        )
    ],
    "picnic": [
        (
            "What is a picnic?",
            "A picnic is a meal eaten outside, often on a blanket. People bring food, sit together, and enjoy the fresh air.",
        )
    ],
    "loss": [
        (
            "What should you do if something important feels unsafe outside?",
            "You should stop, ask for help, and put it somewhere secure. Trying a quick fix all by yourself can make the problem worse.",
        )
    ],
}
KNOWLEDGE_ORDER = ["napkin", "medal", "wind", "picnic", "loss"]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"napkin", "medal", "picnic", "loss"}
    if world.facts["wind_cfg"].power > 0:
        tags.add("wind")
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
            out.extend(KNOWLEDGE[tag])
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
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        lines.append(f"  {e.id:10} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
animal(A) :- animal_id(A).
dangerous_choice(C, W) :- wraps_medal(C), risk(C, R), wind_power(W, P), ties_tight(C, 0), R + P >= risk_min.
lost_story(Pl, C, W) :- place(Pl), choice(C), wind(W), dangerous_choice(C, W),
                        place_spread(Pl, S), risk(C, R), wind_power(W, P), S + R + P >= 3.
valid(A, Pl, W, C) :- animal_id(A), lost_story(Pl, C, W).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = [asp.fact("risk_min", RISK_MIN)]
    for animal_id in ANIMALS:
        lines.append(asp.fact("animal_id", animal_id))
    for place_id, place in PLACES.items():
        lines.append(asp.fact("place", place_id))
        lines.append(asp.fact("place_spread", place_id, place.spread))
    for wind_id, wind in WINDS.items():
        lines.append(asp.fact("wind", wind_id))
        lines.append(asp.fact("wind_power", wind_id, wind.power))
    for choice_id, choice in CHOICES.items():
        lines.append(asp.fact("choice", choice_id))
        lines.append(asp.fact("wraps_medal", choice_id) if choice.wraps_medal else asp.fact("wraps_medal", choice_id, 0))
        lines.append(asp.fact("ties_tight", choice_id, 1 if choice.ties_tight else 0))
        lines.append(asp.fact("risk", choice_id, choice.risk))
    return "\n".join(lines)

def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"

def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))

def asp_verify() -> int:
    rc = 0
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("(Smoke test failed: generated story was empty.)")
        print("OK: smoke-test generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa(world)],
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
        print(asp_program("", "#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (hero, place, wind, choice) combos:\n")
        for hero, place, wind, choice in combos:
            print(f"  {hero:8} {place:10} {wind:7} {choice}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

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
            header = f"### {p.name}: {p.choice} at {p.place} ({p.wind})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
