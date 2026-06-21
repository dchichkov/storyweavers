#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/note_honorary_misunderstanding_surprise_fable.py
===========================================================================

A standalone story world for a small fable-shaped tale about a humble little
animal, a note about an "honorary guest," a misunderstanding, and a warm
surprise.

Core premise
------------
A helpful animal does a quiet good deed in a small woodland place. Later the
animal finds a note asking someone to "bring the honorary guest" to the evening
gathering. Because the hero is modest, the hero assumes the honorary guest must
be someone grander and spends the day preparing for that unknown visitor. The
surprise is that the note was about the hero all along.

Reasonableness constraint
-------------------------
Not every helpful deed fits every place, and not every honorary title fits every
deed. This world refuses mismatched combinations. For example, you cannot make a
bridge-keeper story in an orchard, and you cannot award an honorary gardener
title for mending a boat rope.

Run it
------
python storyworlds/worlds/gpt-5.4/note_honorary_misunderstanding_surprise_fable.py
python storyworlds/worlds/gpt-5.4/note_honorary_misunderstanding_surprise_fable.py --place riverside --deed rope --honor keeper
python storyworlds/worlds/gpt-5.4/note_honorary_misunderstanding_surprise_fable.py --place orchard --deed rope
python storyworlds/worlds/gpt-5.4/note_honorary_misunderstanding_surprise_fable.py --all
python storyworlds/worlds/gpt-5.4/note_honorary_misunderstanding_surprise_fable.py -n 5 --seed 7 --qa
python storyworlds/worlds/gpt-5.4/note_honorary_misunderstanding_surprise_fable.py --verify
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
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
    role: str = ""
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "hen"}
        male = {"boy"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Place:
    id: str
    label: str
    opening: str
    gathering: str
    note_spot: str
    closing_image: str
    supports: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Deed:
    id: str
    label: str
    act: str
    past: str
    result: str
    suits: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Honor:
    id: str
    title: str
    phrase: str
    token: str
    reveal: str
    suits: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    place: str
    deed: str
    honor: str
    hero_name: str
    hero_type: str
    elder_type: str
    trait: str
    seed: Optional[int] = None


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


def _r_notice(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    if hero.meters["helped"] >= THRESHOLD:
        sig = ("notice", "hero")
        if sig not in world.fired:
            world.fired.add(sig)
            hero.memes["earned_honor"] += 1
            out.append("__earned__")
    if hero.memes["misunderstanding"] >= THRESHOLD:
        sig = ("worry", "hero")
        if sig not in world.fired:
            world.fired.add(sig)
            hero.memes["worry"] += 1
            out.append("__worry__")
    return out


CAUSAL_RULES = [
    Rule(name="notice", tag="social", apply=_r_notice),
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
                produced.extend(x for x in sents if not x.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


PLACES = {
    "meadow": Place(
        id="meadow",
        label="the clover meadow",
        opening="where bees hummed above the grass",
        gathering="the lantern picnic",
        note_spot="on the old stump beside the path",
        closing_image="the lanterns shone low over the clover",
        supports={"path", "garden"},
        tags={"meadow", "lantern"},
    ),
    "riverside": Place(
        id="riverside",
        label="the willow riverside",
        opening="where the water spoke softly against the bank",
        gathering="the moon-bridge supper",
        note_spot="on the post by the little bridge",
        closing_image="the moon laid a silver road on the river",
        supports={"bridge", "rope"},
        tags={"river", "bridge"},
    ),
    "orchard": Place(
        id="orchard",
        label="the apple orchard",
        opening="where sweet wind moved through the branches",
        gathering="the basket feast",
        note_spot="on the ladder by the oldest tree",
        closing_image="red apples glowed like little lamps in the leaves",
        supports={"basket", "garden"},
        tags={"orchard", "apple"},
    ),
}

DEEDS = {
    "path": Deed(
        id="path",
        label="swept the path",
        act="sweep the pebbly path clear of burrs and leaves",
        past="swept the pebbly path clear of burrs and leaves",
        result="so small paws and claws could walk without stumbling",
        suits={"meadow"},
        tags={"sweeping", "helping"},
    ),
    "garden": Deed(
        id="garden",
        label="watered the seedlings",
        act="carry dew in nutshell cups to the thirsty seedlings",
        past="carried dew in nutshell cups to the thirsty seedlings",
        result="so the little green shoots would not droop in the sun",
        suits={"meadow", "orchard"},
        tags={"garden", "helping"},
    ),
    "bridge": Deed(
        id="bridge",
        label="mended the bridge slat",
        act="fit a loose bridge slat back into place",
        past="fit a loose bridge slat back into place",
        result="so no one would trip crossing the little bridge",
        suits={"riverside"},
        tags={"bridge", "repair"},
    ),
    "rope": Deed(
        id="rope",
        label="tied the boat rope",
        act="retie the boat rope before the current could tug it away",
        past="retied the boat rope before the current could tug it away",
        result="so the ferry boat stayed waiting at the bank",
        suits={"riverside"},
        tags={"river", "repair"},
    ),
    "basket": Deed(
        id="basket",
        label="gathered the fallen apples",
        act="gather the fallen apples into neat baskets",
        past="gathered the fallen apples into neat baskets",
        result="so the path under the trees was tidy again",
        suits={"orchard"},
        tags={"orchard", "helping"},
    ),
}

HONORS = {
    "guide": Honor(
        id="guide",
        title="Honorary Guide",
        phrase="the honorary guide",
        token="a little bell on a blue ribbon",
        reveal="for keeping the way clear for everyone else",
        suits={"path", "bridge"},
        tags={"guide", "honor"},
    ),
    "keeper": Honor(
        id="keeper",
        title="Honorary Keeper",
        phrase="the honorary keeper",
        token="a willow-leaf badge",
        reveal="for quietly taking care of what everyone needed",
        suits={"garden", "rope", "basket"},
        tags={"keeper", "honor"},
    ),
    "helper": Honor(
        id="helper",
        title="Honorary Helper",
        phrase="the honorary helper",
        token="a daisy wreath",
        reveal="for doing a small good deed before anyone even asked",
        suits={"path", "garden", "bridge", "rope", "basket"},
        tags={"helper", "honor"},
    ),
}

SMALL_NAMES = {
    "mouse": ["Pip", "Mimi", "Nip", "Tansy"],
    "rabbit": ["Clover", "Thimble", "Moss", "Poppy"],
    "squirrel": ["Hazel", "Pipkin", "Tumble", "Nutmeg"],
    "duck": ["Dabble", "Pebble", "Sunny", "Mallow"],
}

TRAITS = ["modest", "careful", "busy", "gentle", "quiet"]

KNOWLEDGE = {
    "note": [
        (
            "What is a note?",
            "A note is a short written message. People leave notes to tell someone something when they are not standing there to say it aloud.",
        )
    ],
    "honor": [
        (
            "What does honorary mean?",
            "Honorary means given as a special sign of respect. It is a way of saying, 'We are honoring you for what you did.'",
        )
    ],
    "misunderstanding": [
        (
            "What is a misunderstanding?",
            "A misunderstanding happens when someone gets the wrong idea about what words or actions mean. Then the person may act on that mistaken idea until the truth becomes clear.",
        )
    ],
    "surprise": [
        (
            "What is a surprise in a story?",
            "A surprise is something important that characters and readers do not expect at first. When it arrives, it changes how the earlier parts of the story feel.",
        )
    ],
    "bridge": [
        (
            "Why is it kind to fix a loose bridge board?",
            "A loose board can make someone trip. Fixing it helps everyone cross more safely.",
        )
    ],
    "garden": [
        (
            "Why do seedlings need water?",
            "Seedlings are very young plants, and they can droop if they dry out. Water helps them stay alive and keep growing.",
        )
    ],
    "orchard": [
        (
            "What is an orchard?",
            "An orchard is a place where many fruit trees grow together. People or animals may gather fruit there when it is ripe.",
        )
    ],
}
KNOWLEDGE_ORDER = ["note", "honor", "misunderstanding", "surprise", "bridge", "garden", "orchard"]


def valid_combo(place_id: str, deed_id: str, honor_id: str) -> bool:
    place = PLACES[place_id]
    deed = DEEDS[deed_id]
    honor = HONORS[honor_id]
    return deed_id in place.supports and deed_id in honor.suits and place_id in deed.suits


def valid_combos() -> list[tuple[str, str, str]]:
    out: list[tuple[str, str, str]] = []
    for place_id in sorted(PLACES):
        for deed_id in sorted(DEEDS):
            for honor_id in sorted(HONORS):
                if valid_combo(place_id, deed_id, honor_id):
                    out.append((place_id, deed_id, honor_id))
    return out


def explain_rejection(place: Place, deed: Deed, honor: Honor) -> str:
    if deed.id not in place.supports or place.id not in deed.suits:
        return (
            f"(No story: in {place.label}, it is not reasonable that someone {deed.act}. "
            f"Pick a deed that belongs in that place.)"
        )
    return (
        f"(No story: {honor.title} does not fit a hero who {deed.past}. "
        f"Choose an honorary title that matches the deed.)"
    )


def introduce(world: World, hero: Entity, place: Place) -> None:
    trait = hero.attrs.get("trait", "quiet")
    world.say(
        f"In {place.label}, {place.opening}, lived {hero.id}, a {trait} little {hero.type}."
    )
    world.say(
        f"{hero.pronoun().capitalize()} was so small that many neighbors forgot to look down, "
        f"but never so small that {hero.pronoun()} forgot to be useful."
    )


def quiet_deed(world: World, hero: Entity, deed: Deed) -> None:
    hero.meters["helped"] += 1
    hero.memes["kindness"] += 1
    propagate(world, narrate=False)
    world.say(
        f"That morning, when no one was asking for praise, {hero.id} stopped to {deed.act}. "
        f"{deed.result.capitalize()}."
    )


def find_note(world: World, hero: Entity, place: Place, honor: Honor) -> None:
    hero.meters["found_note"] += 1
    note = world.get("note")
    note.meters["visible"] += 1
    world.say(
        f"A little later, {hero.id} found a note {place.note_spot}. "
        f'In neat berry-ink it said, "Please bring {honor.phrase} to {place.gathering} at dusk."'
    )


def misunderstand(world: World, hero: Entity, honor: Honor) -> None:
    hero.memes["misunderstanding"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{hero.id} read the note twice and then once more. Being humble, {hero.pronoun()} thought, "
        f'"An {honor.phrase} must be some grand creature with a shining tail or a booming voice. '
        f'It cannot be me."'
    )


def prepare_for_guest(world: World, hero: Entity, place: Place, honor: Honor) -> None:
    hero.meters["prepared"] += 1
    hero.memes["worry"] += 1
    world.say(
        f"So instead of wondering whether the note belonged to {hero.pronoun('object')}, {hero.id} hurried about. "
        f"{hero.pronoun().capitalize()} brushed the meeting stone, straightened cups, and made room for "
        f"{honor.token}, certain that a splendid visitor would soon arrive."
    )


def ask_around(world: World, hero: Entity) -> None:
    hero.memes["worry"] += 1
    world.say(
        f"All afternoon {hero.id} peeped at paws, feathers, and tails, searching for someone who looked honorary. "
        f"But everyone only smiled in a mysterious way and told {hero.pronoun('object')} to come at dusk."
    )


def reveal(world: World, hero: Entity, elder: Entity, honor: Honor, place: Place, deed: Deed) -> None:
    hero.memes["surprise"] += 1
    hero.memes["joy"] += 1
    hero.memes["pride"] += 1
    hero.memes["worry"] = 0.0
    hero.meters["honored"] += 1
    world.get("token").meters["worn"] += 1
    world.say(
        f"When dusk finally gathered, the neighbors circled the lanterns. Then the old {elder.type} stepped forward, "
        f"lifted {honor.token}, and called, \"Please welcome our {honor.title}!\""
    )
    world.say(
        f"Every face turned toward {hero.id}. {hero.id} stared so hard that {hero.pronoun('possessive')} whiskers trembled. "
        f"\"Me?\" {hero.pronoun()} whispered."
    )
    world.say(
        f"\"You,\" said the {elder.type}, settling the token gently on {hero.pronoun('possessive')} shoulders, "
        f"\"because you {deed.past}, {honor.reveal}.\""
    )
    world.say(
        f"At once the misunderstanding melted like mist. {hero.id} had spent the whole day preparing a place for another, "
        f"only to learn that kindness had quietly prepared a place for {hero.pronoun('object')}."
    )
    world.say(
        f"And in {place.label}, {place.closing_image}, the smallest creature stood a little taller."
    )
    world.say("From then on, the neighbors remembered that the truest honor often walks in on soft feet.")
    world.facts["moral"] = "The truest honor often walks in on soft feet."


def tell(
    place: Place,
    deed: Deed,
    honor: Honor,
    hero_name: str,
    hero_type: str,
    elder_type: str,
    trait: str,
) -> World:
    world = World()
    hero = world.add(
        Entity(
            id="hero",
            kind="character",
            type=hero_type,
            label=hero_name,
            phrase=hero_name,
            role="hero",
            attrs={"name": hero_name, "trait": trait},
        )
    )
    elder = world.add(
        Entity(
            id="elder",
            kind="character",
            type=elder_type,
            label=f"the old {elder_type}",
            phrase=f"the old {elder_type}",
            role="elder",
        )
    )
    world.add(Entity(id="note", type="thing", label="note", phrase="a folded note"))
    world.add(Entity(id="token", type="thing", label=honor.token, phrase=honor.token))

    introduce(world, hero, place)
    quiet_deed(world, hero, deed)

    world.para()
    find_note(world, hero, place, honor)
    misunderstand(world, hero, honor)
    prepare_for_guest(world, hero, place, honor)
    ask_around(world, hero)

    world.para()
    reveal(world, hero, elder, honor, place, deed)

    world.facts.update(
        place=place,
        deed=deed,
        honor=honor,
        hero=hero,
        elder=elder,
        hero_name=hero_name,
        note_found=world.get("note").meters["visible"] >= THRESHOLD,
        misunderstood=hero.memes["misunderstanding"] >= THRESHOLD,
        honored=hero.meters["honored"] >= THRESHOLD,
    )
    return world


def hero_name_from_world(world: World) -> str:
    return str(world.facts.get("hero_name", world.get("hero").label or "the hero"))


def generation_prompts(world: World) -> list[str]:
    place = world.facts["place"]
    deed = world.facts["deed"]
    honor = world.facts["honor"]
    hero_name = hero_name_from_world(world)
    return [
        f'Write a short fable for a 3-to-5-year-old that includes the word "note" and the word "honorary".',
        f"Tell a woodland story where {hero_name} finds a note about {honor.phrase}, misunderstands it, and learns at dusk that the note was really about {hero_name}.",
        f"Write a gentle surprise story in {place.label} where a small animal who {deed.past} is honored in the end.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    hero = world.get("hero")
    place = world.facts["place"]
    deed = world.facts["deed"]
    honor = world.facts["honor"]
    elder = world.get("elder")
    hero_name = hero_name_from_world(world)
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero_name}, a little {hero.type} in {place.label}. The story is also about the neighbors who noticed a quiet kind deed.",
        ),
        (
            f"What good deed did {hero_name} do?",
            f"{hero_name} {deed.past}. {deed.result.capitalize()}, so the deed helped everyone even though nobody asked for it first.",
        ),
        (
            "What did the note say?",
            f"The note asked someone to bring {honor.phrase} to {place.gathering} at dusk. Those words started the whole misunderstanding.",
        ),
    ]
    if world.facts.get("misunderstood"):
        qa.append(
            (
                f"Why did {hero_name} misunderstand the note?",
                f"{hero_name} was so humble that {hero.pronoun()} assumed the honorary guest had to be someone grander. Because of that mistaken idea, {hero.pronoun()} spent the day preparing for another creature instead of expecting honor for {hero.pronoun('object')}.",
            )
        )
    if world.facts.get("honored"):
        qa.append(
            (
                f"What was the surprise at dusk?",
                f"The surprise was that the honorary guest was {hero_name}. The old {elder.type} placed {honor.token} on {hero.pronoun('object')} because {hero.pronoun()} had quietly helped everyone earlier.",
            )
        )
        qa.append(
            (
                f"What lesson did {hero_name} learn?",
                f"{hero_name} learned that quiet kindness can be seen and remembered. The ending shows that real honor does not always go to the loudest creature.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"note", "honor", "misunderstanding", "surprise"}
    tags |= set(world.facts["place"].tags)
    tags |= set(world.facts["deed"].tags)
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags and tag in KNOWLEDGE:
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
        if e.role:
            bits.append(f"role={e.role}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {e.id:8} ({e.type:9}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
fits_place(P, D) :- place(P), deed(D), supports(P, D), suited_place(D, P).
fits_honor(D, H) :- deed(D), honor(H), suited_honor(H, D).
valid(P, D, H) :- fits_place(P, D), fits_honor(D, H).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for place_id, place in PLACES.items():
        lines.append(asp.fact("place", place_id))
        for deed_id in sorted(place.supports):
            lines.append(asp.fact("supports", place_id, deed_id))
    for deed_id, deed in DEEDS.items():
        lines.append(asp.fact("deed", deed_id))
        for place_id in sorted(deed.suits):
            lines.append(asp.fact("suited_place", deed_id, place_id))
    for honor_id, honor in HONORS.items():
        lines.append(asp.fact("honor", honor_id))
        for deed_id in sorted(honor.suits):
            lines.append(asp.fact("suited_honor", honor_id, deed_id))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def validate_params(params: StoryParams) -> None:
    if params.place not in PLACES:
        raise StoryError(f"(Unknown place: {params.place})")
    if params.deed not in DEEDS:
        raise StoryError(f"(Unknown deed: {params.deed})")
    if params.honor not in HONORS:
        raise StoryError(f"(Unknown honor: {params.honor})")
    if not valid_combo(params.place, params.deed, params.honor):
        raise StoryError(
            explain_rejection(PLACES[params.place], DEEDS[params.deed], HONORS[params.honor])
        )


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a note, an honorary guest, a misunderstanding, and a surprise."
    )
    ap.add_argument("--place", choices=sorted(PLACES))
    ap.add_argument("--deed", choices=sorted(DEEDS))
    ap.add_argument("--honor", choices=sorted(HONORS))
    ap.add_argument("--hero-type", choices=sorted(SMALL_NAMES), dest="hero_type")
    ap.add_argument("--hero-name", dest="hero_name")
    ap.add_argument("--elder", choices=["owl", "tortoise", "badger"], dest="elder_type")
    ap.add_argument("--trait", choices=sorted(TRAITS))
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the valid combos derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP gate and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.deed and args.honor:
        if not valid_combo(args.place, args.deed, args.honor):
            raise StoryError(explain_rejection(PLACES[args.place], DEEDS[args.deed], HONORS[args.honor]))

    combos = [
        c
        for c in valid_combos()
        if (args.place is None or c[0] == args.place)
        and (args.deed is None or c[1] == args.deed)
        and (args.honor is None or c[2] == args.honor)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, deed_id, honor_id = rng.choice(combos)
    hero_type = args.hero_type or rng.choice(sorted(SMALL_NAMES))
    hero_name = args.hero_name or rng.choice(SMALL_NAMES[hero_type])
    elder_type = args.elder_type or rng.choice(["owl", "tortoise", "badger"])
    trait = args.trait or rng.choice(TRAITS)
    params = StoryParams(
        place=place_id,
        deed=deed_id,
        honor=honor_id,
        hero_name=hero_name,
        hero_type=hero_type,
        elder_type=elder_type,
        trait=trait,
    )
    validate_params(params)
    return params


def generate(params: StoryParams) -> StorySample:
    validate_params(params)
    world = tell(
        place=PLACES[params.place],
        deed=DEEDS[params.deed],
        honor=HONORS[params.honor],
        hero_name=params.hero_name,
        hero_type=params.hero_type,
        elder_type=params.elder_type,
        trait=params.trait,
    )
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


CURATED = [
    StoryParams(
        place="meadow",
        deed="path",
        honor="guide",
        hero_name="Pip",
        hero_type="mouse",
        elder_type="owl",
        trait="modest",
    ),
    StoryParams(
        place="riverside",
        deed="rope",
        honor="keeper",
        hero_name="Clover",
        hero_type="rabbit",
        elder_type="badger",
        trait="careful",
    ),
    StoryParams(
        place="orchard",
        deed="basket",
        honor="helper",
        hero_name="Hazel",
        hero_type="squirrel",
        elder_type="tortoise",
        trait="busy",
    ),
    StoryParams(
        place="meadow",
        deed="garden",
        honor="keeper",
        hero_name="Pebble",
        hero_type="duck",
        elder_type="owl",
        trait="gentle",
    ),
]


def asp_verify() -> int:
    rc = 0
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: ASP gate matches valid_combos() ({len(python_set)} combos).")
    else:
        rc = 1
        print("MISMATCH between ASP and Python valid combos:")
        if clingo_set - python_set:
            print("  only in ASP:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in Python:", sorted(python_set - clingo_set))

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("(Smoke test failed: generated story was empty.)")
        print("OK: smoke test generated a normal story.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    try:
        rng = random.Random(123)
        params = resolve_params(build_parser().parse_args([]), rng)
        sample = generate(params)
        if not sample.story.strip():
            raise StoryError("(Random smoke test failed: empty story.)")
        print("OK: random resolve/generate smoke test passed.")
    except Exception as err:
        rc = 1
        print(f"RANDOM SMOKE TEST FAILED: {err}")

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return

    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} valid (place, deed, honor) combos:\n")
        for place_id, deed_id, honor_id in combos:
            print(f"  {place_id:10} {deed_id:8} {honor_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        samples: list[StorySample] = []
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
            header = f"### {p.hero_name}: {p.deed} at {p.place} ({p.honor})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
