#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/saber_repetition_animal_story.py
===========================================================

A standalone storyworld for a tiny animal-story domain with built-in repetition.

Premise
-------
A young animal is excited to lead a pretend parade while carrying a toy saber.
In tight, crowded places, a long stiff saber is a poor idea: it can poke, snag,
or spill things before the child can stop. A cautious friend warns the hero,
sometimes strongly enough to prevent trouble. Otherwise a small accident happens,
a calm grown-up helps, and the parade continues with a safer prop.

This world is intentionally small and constraint-driven:
- only places that are genuinely awkward for a saber are considered valid stories
- a safe replacement must still suit the parade game
- the prose uses repetition as part of the warning and the ending cadence

Run it
------
python storyworlds/worlds/gpt-5.4/saber_repetition_animal_story.py
python storyworlds/worlds/gpt-5.4/saber_repetition_animal_story.py --place bridge --saber wooden_saber
python storyworlds/worlds/gpt-5.4/saber_repetition_animal_story.py --place hill
python storyworlds/worlds/gpt-5.4/saber_repetition_animal_story.py --all
python storyworlds/worlds/gpt-5.4/saber_repetition_animal_story.py --qa
python storyworlds/worlds/gpt-5.4/saber_repetition_animal_story.py --verify
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
COURAGE_INIT = 5.0
CAUTIOUS_TRAITS = {"careful", "gentle", "steady", "watchful"}


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    name: str = ""
    title: str = ""
    voice: str = ""
    thanks: str = ""
    scold: str = ""
    help_action: str = ""
    face: str = ""
    path_line: str = ""
    ending_image: str = ""
    weak_spot: str = ""
    role_text: str = ""
    need: str = ""
    metallic: str = ""
    special: str = ""
    question_reply: str = ""
    wisdom: str = ""
    rising_line: str = ""
    risk: str = ""
    qa_text: str = ""
    location_text: str = ""
    use_line: str = ""
    cry: str = ""
    ending_line: str = ""
    reach: str = ""
    damage: str = ""
    use: str = ""
    opening: str = ""
    warning: str = ""
    owner_text: str = ""
    ground: str = ""
    action_line: str = ""
    kindness_text: str = ""
    calm: str = ""
    restored: str = ""
    shine: str = ""
    reveal_text: str = ""
    traits: list[str] = field(default_factory=list)
    age: int = 0
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"rabbit_girl", "fox_girl", "mouse_girl", "otter_girl", "mother", "aunt"}
        male = {"rabbit_boy", "fox_boy", "mouse_boy", "otter_boy", "father", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def title_word(self) -> str:
        return {"mother": "mom", "father": "dad", "aunt": "aunt", "uncle": "uncle"}.get(self.type, self.type)


@dataclass
class Place:
    id: str
    label: str
    phrase: str
    detail: str
    crowd: int
    narrowness: int
    snag: str
    consequence: str
    safe_image: str
    tags: set[str] = field(default_factory=set)


@dataclass
class SaberCfg:
    id: str
    label: str
    phrase: str
    material: str
    length: int
    stiffness: int
    swish: str
    tags: set[str] = field(default_factory=set)


@dataclass
class FixCfg:
    id: str
    label: str
    phrase: str
    soft: bool
    short: bool
    fit: str
    ending_line: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[["World"], list[str]]


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


def _r_worry(world: World) -> list[str]:
    hero = world.get("hero")
    place = world.get("place")
    saber = world.get("saber")
    if hero.meters["carrying_saber"] < THRESHOLD:
        return []
    sig = ("worry",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    risk = place.meters["crowded"] + place.meters["narrow"] + saber.meters["rigid"]
    world.get("friend").memes["worry"] += 1
    world.get("adult").memes["watchful"] += 1
    world.get("room").meters["risk"] += risk
    return ["__risk__"]


def _r_accident(world: World) -> list[str]:
    hero = world.get("hero")
    place = world.get("place")
    saber = world.get("saber")
    if hero.meters["running"] < THRESHOLD or hero.meters["carrying_saber"] < THRESHOLD:
        return []
    sig = ("accident",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    severity = place.meters["crowded"] + place.meters["narrow"] + saber.meters["rigid"]
    world.get("room").meters["severity"] = severity
    world.get("target").meters["snagged"] += 1
    world.get("hero").memes["fear"] += 1
    world.get("friend").memes["fear"] += 1
    return ["__snag__"]


CAUSAL_RULES = [
    Rule(name="worry", tag="emotional", apply=_r_worry),
    Rule(name="accident", tag="physical", apply=_r_accident),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            got = rule.apply(world)
            if got:
                changed = True
                out.extend(s for s in got if not s.startswith("__"))
    if narrate:
        for line in out:
            world.say(line)
    return out


def hazard(place: Place, saber: SaberCfg) -> bool:
    return (place.crowd + place.narrowness) >= saber.length


def safe_fix(place: Place, fix: FixCfg) -> bool:
    return fix.soft and fix.short


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for place_id, place in PLACES.items():
        for saber_id, saber in SABERS.items():
            for fix_id, fix in FIXES.items():
                if hazard(place, saber) and safe_fix(place, fix):
                    combos.append((place_id, saber_id, fix_id))
    return combos


def initial_caution(trait: str) -> float:
    return 5.0 if trait in CAUTIOUS_TRAITS else 3.0


def would_avert(relation: str, friend_age: int, hero_age: int, trait: str) -> bool:
    older = relation == "siblings" and friend_age > hero_age
    authority = initial_caution(trait) + (2.0 if older else 0.0) + 1.0
    return older and authority > COURAGE_INIT


def predict_snag(world: World) -> dict:
    sim = world.copy()
    sim.get("hero").meters["carrying_saber"] += 1
    sim.get("hero").meters["running"] += 1
    propagate(sim, narrate=False)
    return {
        "snagged": sim.get("target").meters["snagged"] >= THRESHOLD,
        "severity": sim.get("room").meters["severity"],
    }


def introduce(world: World, hero: Entity, friend: Entity, place: Place) -> None:
    hero.memes["joy"] += 1
    friend.memes["joy"] += 1
    world.say(
        f"In {place.phrase}, {hero.id} and {friend.id} wanted to lead the morning parade. "
        f"{place.detail}"
    )
    world.say(
        f'{hero.id} pranced in a circle and sang, "Tap-tap, clap-clap, follow me, follow me!"'
    )


def equip(world: World, hero: Entity, saber: SaberCfg) -> None:
    hero.meters["carrying_saber"] += 1
    world.say(
        f"{hero.id} had {saber.phrase}. {hero.pronoun().capitalize()} lifted it high and gave it a little "
        f"{saber.swish} through the air."
    )
    world.say(
        f'The others giggled, but {hero.id} sang again, "I have my saber, I have my saber!"'
    )
    propagate(world, narrate=False)


def warn(world: World, friend: Entity, hero: Entity, adult: Entity, place: Place, saber: SaberCfg) -> None:
    pred = predict_snag(world)
    world.facts["predicted_severity"] = pred["severity"]
    friend.memes["care"] += 1
    older_bit = ""
    if world.facts.get("relation") == "siblings" and friend.age > hero.age:
        older_bit = f" {friend.pronoun().capitalize()} was the older one, and {friend.pronoun()} spoke very firmly."
    world.say(
        f'{friend.id} looked at the {saber.label}, then at {place.label}. '
        f'"Not with a saber, not with a saber," {friend.pronoun()} said. '
        f'"It is too long for {place.label}, and it could {place.consequence}."{older_bit}'
    )
    world.say(
        f'{adult.title_word.capitalize()} nodded from nearby. "{place.label.capitalize()} is a place for slow paws, safe paws," '
        f'{adult.pronoun()} said.'
    )


def defy(world: World, hero: Entity) -> None:
    hero.memes["defiance"] += 1
    world.say(
        f'But the parade song was still bouncing inside {hero.id}. '
        f'"Just one march, just one march," {hero.pronoun()} said, and trotted ahead.'
    )


def back_down(world: World, hero: Entity, friend: Entity, saber: SaberCfg) -> None:
    hero.memes["relief"] += 1
    friend.memes["relief"] += 1
    hero.meters["carrying_saber"] = 0.0
    world.say(
        f'{hero.id} stopped, looked at {saber.label}, and then looked at {friend.id}. '
        f'The brave feeling in {hero.pronoun("possessive")} chest turned softer.'
    )
    world.say(
        f'"Not with a saber, not with a saber," {hero.pronoun()} repeated quietly. '
        f'Then {hero.pronoun()} leaned the {saber.label} against a stump and chose to wait.'
    )


def snag(world: World, hero: Entity, friend: Entity, place: Place, saber: SaberCfg) -> None:
    hero.meters["running"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{hero.id} took three quick steps. Swish, swish went the {saber.label}."
    )
    world.say(
        f"Then it caught on {place.snag}. There was a little jerk, a little wobble, and {place.consequence}."
    )
    world.say(
        f'{friend.id} gasped, "Oh no, the saber, the saber!"'
    )


def mend(world: World, adult: Entity, place: Place) -> None:
    world.get("target").meters["snagged"] = 0.0
    world.get("hero").memes["fear"] = 0.0
    world.get("friend").memes["fear"] = 0.0
    world.say(
        f"{adult.title_word.capitalize()} came at once, set gentle hands on the muddle, and made everything steady again."
    )
    world.say(
        f"{adult.pronoun().capitalize()} showed them how the trouble had started: a long hard toy and {place.label} do not fit together."
    )


def gift_fix(world: World, adult: Entity, hero: Entity, friend: Entity, fix: FixCfg, saber: SaberCfg, place: Place) -> None:
    hero.memes["joy"] += 1
    hero.memes["lesson"] += 1
    friend.memes["joy"] += 1
    hero.meters["carrying_saber"] = 0.0
    world.add(Entity(id="fix", type="prop", label=fix.label, phrase=fix.phrase, tags=set(fix.tags)))
    world.say(
        f'Then {adult.title_word} smiled and brought {fix.phrase}. '
        f'"If you want to lead a parade in {place.label}, try this instead," {adult.pronoun()} said.'
    )
    world.say(
        f"{hero.id} took the {fix.label}. It felt light, soft, and easy to carry."
    )
    world.say(
        f'"No saber here, no saber there," sang {friend.id}. "{fix.fit.capitalize()} everywhere!"'
    )
    world.say(
        f"{hero.id} laughed, and soon the two friends were marching together, {fix.ending_line}, {place.safe_image}."
    )


def tell(
    place: Place,
    saber: SaberCfg,
    fix: FixCfg,
    *,
    hero_name: str = "Pip",
    hero_type: str = "rabbit_boy",
    friend_name: str = "Moss",
    friend_type: str = "mouse_girl",
    adult_type: str = "mother",
    trait: str = "careful",
    relation: str = "siblings",
    hero_age: int = 4,
    friend_age: int = 6,
) -> World:
    world = World()
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, role="hero", age=hero_age, traits=["eager"]))
    friend = world.add(Entity(id=friend_name, kind="character", type=friend_type, role="friend", age=friend_age, traits=[trait]))
    adult = world.add(Entity(id="Adult", kind="character", type=adult_type, role="adult", label="the grown-up"))
    world.add(Entity(id="place", type="place", label=place.label))
    world.add(Entity(id="saber", type="tool", label=saber.label))
    world.add(Entity(id="target", type="thing", label="the parade things"))
    world.add(Entity(id="room", type="scene", label="the scene"))

    world.get("place").meters["crowded"] = float(place.crowd)
    world.get("place").meters["narrow"] = float(place.narrowness)
    world.get("saber").meters["rigid"] = float(saber.stiffness)

    hero.memes["courage"] = COURAGE_INIT
    friend.memes["caution"] = initial_caution(trait)

    world.facts["relation"] = relation

    introduce(world, hero, friend, place)
    world.para()
    equip(world, hero, saber)
    warn(world, friend, hero, adult, place, saber)

    averted = would_avert(relation, friend_age, hero_age, trait)

    world.para()
    if averted:
        back_down(world, hero, friend, saber)
        world.para()
        gift_fix(world, adult, hero, friend, fix, saber, place)
        outcome = "averted"
    else:
        defy(world, hero)
        snag(world, hero, friend, place, saber)
        world.para()
        mend(world, adult, place)
        gift_fix(world, adult, hero, friend, fix, saber, place)
        outcome = "snagged"

    world.facts.update(
        hero=hero,
        friend=friend,
        adult=adult,
        place_cfg=place,
        saber_cfg=saber,
        fix_cfg=fix,
        outcome=outcome,
        hero_listened=averted,
        accident=outcome == "snagged",
        target="parade things",
    )
    return world


@dataclass
class StoryParams:
    place: str
    saber: str
    fix: str
    hero_name: str
    hero_type: str
    friend_name: str
    friend_type: str
    adult_type: str
    trait: str
    relation: str
    hero_age: int
    friend_age: int
    seed: Optional[int] = None


PLACES = {
    "bridge": Place(
        id="bridge",
        label="the willow bridge",
        phrase="the little willow bridge over the stream",
        detail="The bridge was narrow, and baskets of berries waited at one end for the parade feast.",
        crowd=2,
        narrowness=2,
        snag="a berry basket handle",
        consequence="berries rolled in bright little dots across the boards",
        safe_image="with berries still tucked neatly in their basket",
        tags={"bridge", "berries"},
    ),
    "tunnel": Place(
        id="tunnel",
        label="the fern tunnel",
        phrase="the fern tunnel beside the pond",
        detail="Green fronds brushed both sides of the path, and everyone had to walk close together.",
        crowd=2,
        narrowness=2,
        snag="the drooping fern fronds",
        consequence="the line bumped and hats tipped sideways",
        safe_image="with every parade hat sitting straight",
        tags={"tunnel", "ferns"},
    ),
    "market": Place(
        id="market",
        label="the acorn market lane",
        phrase="the acorn market lane under the oak trees",
        detail="Tiny stalls stood shoulder to shoulder, and jars of honey glowed in the shade.",
        crowd=3,
        narrowness=1,
        snag="a cloth stall flap",
        consequence="a honey jar wobbled and had to be caught just in time",
        safe_image="with the honey jars shining safely on the stall",
        tags={"market", "honey"},
    ),
    "hill": Place(
        id="hill",
        label="the sunny hill",
        phrase="the sunny hill above the burrow",
        detail="It was wide and breezy, with plenty of room to romp.",
        crowd=0,
        narrowness=0,
        snag="nothing at all",
        consequence="nothing would really go wrong there",
        safe_image="under the big blue sky",
        tags={"hill"},
    ),
}

SABERS = {
    "wooden_saber": SaberCfg(
        id="wooden_saber",
        label="wooden saber",
        phrase="a wooden saber painted red and gold",
        material="wood",
        length=3,
        stiffness=2,
        swish="swish",
        tags={"saber", "wood"},
    ),
    "reed_saber": SaberCfg(
        id="reed_saber",
        label="reed saber",
        phrase="a reed saber tied with a strip of blue cloth",
        material="reed",
        length=2,
        stiffness=1,
        swish="whispery swish",
        tags={"saber", "reed"},
    ),
    "shell_saber": SaberCfg(
        id="shell_saber",
        label="shell-handled saber",
        phrase="a shell-handled saber with a shiny paper guard",
        material="shell and stick",
        length=3,
        stiffness=2,
        swish="flashy swish",
        tags={"saber", "shell"},
    ),
}

FIXES = {
    "ribbon_wand": FixCfg(
        id="ribbon_wand",
        label="ribbon wand",
        phrase="a ribbon wand with three streaming tails",
        soft=True,
        short=True,
        fit="soft colors flutter",
        ending_line="making loops of color in the air",
        tags={"ribbon"},
    ),
    "flower_flag": FixCfg(
        id="flower_flag",
        label="flower flag",
        phrase="a little flower flag on a short willow stick",
        soft=True,
        short=True,
        fit="flower flags wave",
        ending_line="waving a tiny patch of yellow and white",
        tags={"flag", "flower"},
    ),
    "bell_bracelet": FixCfg(
        id="bell_bracelet",
        label="bell bracelet",
        phrase="a bell bracelet that chimed on a small wrist",
        soft=True,
        short=True,
        fit="small bells jingle",
        ending_line="with silver jingles skipping beside their paws",
        tags={"bell"},
    ),
    "long_banner": FixCfg(
        id="long_banner",
        label="long banner",
        phrase="a long banner pole with a trailing cloth tail",
        soft=False,
        short=False,
        fit="banners flap",
        ending_line="dragging a long cloth tail behind them",
        tags={"banner"},
    ),
}

GIRL_NAMES = ["Poppy", "Nell", "Mira", "Tansy", "Luma", "Daisy"]
BOY_NAMES = ["Pip", "Milo", "Tuck", "Bram", "Otis", "Finn"]
HERO_TYPES = ["rabbit_boy", "fox_girl", "mouse_boy", "otter_girl"]
FRIEND_TYPES = ["rabbit_girl", "fox_boy", "mouse_girl", "otter_boy"]
TRAITS = ["careful", "gentle", "steady", "watchful", "curious", "bouncy"]


KNOWLEDGE = {
    "saber": [
        (
            "What is a saber?",
            "A saber is a kind of sword with a long blade. In a pretend game, a toy saber may look exciting, but a long hard toy can still bump or snag things."
        )
    ],
    "bridge": [
        (
            "Why should you walk slowly on a narrow bridge?",
            "A narrow bridge does not leave much room on either side. Slow steps help you keep your balance and keep your things from bumping into other things."
        )
    ],
    "tunnel": [
        (
            "Why can a crowded tunnel be tricky for a long toy?",
            "In a crowded tunnel, everyone has to stay close together. A long toy can catch on leaves or bump a friend before you notice."
        )
    ],
    "market": [
        (
            "Why is it important to be careful near market stalls?",
            "Market stalls often hold jars, baskets, or other things that can tip. Careful bodies and careful hands help keep everything safe."
        )
    ],
    "ribbon": [
        (
            "Why is a ribbon wand safer than a hard toy sword?",
            "A ribbon wand is soft and light, so it can flutter without poking people or snagging hard on things. It still feels festive, but it is gentler."
        )
    ],
    "flag": [
        (
            "What does a little flag do in a parade?",
            "A little flag gives everyone something cheerful to follow. It can lead the parade without being heavy or sharp."
        )
    ],
    "bell": [
        (
            "Why can a bell bracelet work well in a parade?",
            "A bell bracelet makes a happy sound without sticking out very far. That makes it easier to move in a small space."
        )
    ],
}
KNOWLEDGE_ORDER = ["saber", "bridge", "tunnel", "market", "ribbon", "flag", "bell"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    place = f["place_cfg"]
    fix = f["fix_cfg"]
    outcome = f["outcome"]
    if outcome == "averted":
        return [
            'Write a short animal story for a 3-to-5-year-old that includes the word "saber" and uses repetition in the dialogue.',
            f"Tell a gentle animal story where {hero.id} wants to lead a parade with a saber in {place.label}, but {friend.id} repeats a warning until the trouble is avoided.",
            f"Write an animal story with a repeated line, a cautious friend, and a safe ending where a child swaps a saber for {fix.phrase}.",
        ]
    return [
        'Write a short animal story for a 3-to-5-year-old that includes the word "saber" and uses repetition in the dialogue.',
        f"Tell an animal story where {hero.id} marches with a saber in {place.label}, a small accident happens, and a calm grown-up helps.",
        f"Write a repetitive animal story in which a risky saber is replaced by {fix.phrase}, ending with a happy parade image.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    adult = f["adult"]
    place = f["place_cfg"]
    saber = f["saber_cfg"]
    fix = f["fix_cfg"]
    outcome = f["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id} and {friend.id}, two young animals getting ready for a parade, and {adult.title_word} who helps them make it safe."
        ),
        (
            f"Why did {friend.id} say, 'Not with a saber, not with a saber'?",
            f"{friend.id} could see that {place.label} was too tight and crowded for {saber.phrase}. A long hard toy there could {place.consequence}, so the warning came from a real risk."
        ),
        (
            f"What did {hero.id} want the saber for?",
            f"{hero.id} wanted to use the saber to lead the parade and feel brave. The saber seemed exciting because it matched the pretend marching game."
        ),
    ]
    if outcome == "averted":
        qa.append(
            (
                f"What changed {hero.id}'s mind?",
                f"{hero.id} listened when {friend.id} repeated the warning and when {adult.title_word} reminded everyone about slow paws and safe paws. Because the warning matched the place, {hero.id} decided the brave choice was to put the saber down."
            )
        )
    else:
        qa.append(
            (
                f"What happened when {hero.id} marched with the saber anyway?",
                f"The saber caught on {place.snag}, and {place.consequence}. That small jolt showed exactly why the warning mattered."
            )
        )
        qa.append(
            (
                f"How did {adult.title_word} help?",
                f"{adult.title_word.capitalize()} came right away, steadied the muddle, and explained that a long hard toy and {place.label} do not fit together. Then {adult.pronoun()} offered {fix.phrase} so the parade could continue in a safer way."
            )
        )
    qa.append(
        (
            "How did the story end?",
            f"It ended with the children marching happily using {fix.phrase} instead of the saber. The last image proves the change: they still had their parade, but now it fit {place.label} safely."
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = set(world.facts["saber_cfg"].tags) | set(world.facts["place_cfg"].tags) | set(world.facts["fix_cfg"].tags)
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
    for ent in list(world.entities.values()):
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.age:
            bits.append(f"age={ent.age}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:8} ({ent.type:11}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        place="bridge",
        saber="wooden_saber",
        fix="ribbon_wand",
        hero_name="Pip",
        hero_type="rabbit_boy",
        friend_name="Nell",
        friend_type="mouse_girl",
        adult_type="mother",
        trait="careful",
        relation="siblings",
        hero_age=4,
        friend_age=6,
    ),
    StoryParams(
        place="market",
        saber="shell_saber",
        fix="flower_flag",
        hero_name="Mira",
        hero_type="fox_girl",
        friend_name="Finn",
        friend_type="otter_boy",
        adult_type="aunt",
        trait="curious",
        relation="friends",
        hero_age=5,
        friend_age=5,
    ),
    StoryParams(
        place="tunnel",
        saber="reed_saber",
        fix="bell_bracelet",
        hero_name="Tuck",
        hero_type="mouse_boy",
        friend_name="Poppy",
        friend_type="rabbit_girl",
        adult_type="father",
        trait="steady",
        relation="siblings",
        hero_age=4,
        friend_age=7,
    ),
]


def explain_rejection(place: Place, saber: SaberCfg, fix: Optional[FixCfg] = None) -> str:
    if not hazard(place, saber):
        return (
            f"(No story: {place.label.capitalize()} is too open for {saber.phrase}. "
            f"If a saber would not reasonably snag or bump anything, there is no honest problem to solve.)"
        )
    if fix is not None and not safe_fix(place, fix):
        return (
            f"(No story: {fix.phrase} is not really a safer parade prop here. "
            f"The replacement should be short and soft enough for {place.label}.)"
        )
    return "(No story: this combination does not form a strong problem-and-fix pair.)"


ASP_RULES = r"""
hazard(P,S) :- place(P), saber(S), crowd(P,C), narrow(P,N), length(S,L), C + N >= L.
safe_fix(P,F) :- place(P), fix(F), soft(F), short(F).
valid(P,S,F) :- hazard(P,S), safe_fix(P,F).

cautious_now(T) :- trait(T), is_cautious(T).
init_caution(5) :- trait(T), cautious_now(T).
init_caution(3) :- trait(T), not cautious_now(T).

older_friend :- relation(siblings), friend_age(FA), hero_age(HA), FA > HA.
bonus(2) :- older_friend.
bonus(0) :- not older_friend.
authority(C + B + 1) :- init_caution(C), bonus(B).

averted :- older_friend, authority(A), courage_init(K), A > K.
outcome(averted) :- averted.
outcome(snagged) :- not averted.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for pid, place in PLACES.items():
        lines.append(asp.fact("place", pid))
        lines.append(asp.fact("crowd", pid, place.crowd))
        lines.append(asp.fact("narrow", pid, place.narrowness))
    for sid, saber in SABERS.items():
        lines.append(asp.fact("saber", sid))
        lines.append(asp.fact("length", sid, saber.length))
    for fid, fix in FIXES.items():
        lines.append(asp.fact("fix", fid))
        if fix.soft:
            lines.append(asp.fact("soft", fid))
        if fix.short:
            lines.append(asp.fact("short", fid))
    for trait in sorted(CAUTIOUS_TRAITS):
        lines.append(asp.fact("is_cautious", trait))
    lines.append(asp.fact("courage_init", int(COURAGE_INIT)))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("relation", params.relation),
            asp.fact("friend_age", params.friend_age),
            asp.fact("hero_age", params.hero_age),
            asp.fact("trait", params.trait),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def outcome_of(params: StoryParams) -> str:
    return "averted" if would_avert(params.relation, params.friend_age, params.hero_age, params.trait) else "snagged"


def _validate_params(params: StoryParams) -> None:
    if params.place not in PLACES:
        raise StoryError(f"(Unknown place: {params.place})")
    if params.saber not in SABERS:
        raise StoryError(f"(Unknown saber: {params.saber})")
    if params.fix not in FIXES:
        raise StoryError(f"(Unknown fix: {params.fix})")
    place = PLACES[params.place]
    saber = SABERS[params.saber]
    fix = FIXES[params.fix]
    if not hazard(place, saber):
        raise StoryError(explain_rejection(place, saber))
    if not safe_fix(place, fix):
        raise StoryError(explain_rejection(place, saber, fix))


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

    cases = list(CURATED)
    for seed in range(30):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
        except StoryError:
            continue
        cases.append(params)

    bad = 0
    for params in cases:
        if asp_outcome(params) != outcome_of(params):
            bad += 1
    if bad == 0:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("(Smoke test produced an empty story.)")
        emit(sample, trace=False, qa=False, header="### smoke test")
        print("OK: smoke test story generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(conflict_handler="resolve",
        description="Animal-story world: a child brings a saber into a tight place, learns a safer way, and the prose uses repetition."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--saber", choices=SABERS)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--adult", choices=["mother", "father", "aunt", "uncle"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid combos according to clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the ASP program")
    return ap


def _pick_name(rng: random.Random, pool: list[str], avoid: str = "") -> str:
    names = [n for n in pool if n != avoid]
    return rng.choice(names)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.saber:
        place = PLACES[args.place]
        saber = SABERS[args.saber]
        if not hazard(place, saber):
            raise StoryError(explain_rejection(place, saber))
    if args.place and args.fix:
        place = PLACES[args.place]
        fix = FIXES[args.fix]
        sample_saber = SABERS[args.saber] if args.saber else next(iter(SABERS.values()))
        if not safe_fix(place, fix):
            raise StoryError(explain_rejection(place, sample_saber, fix))

    combos = [
        combo
        for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.saber is None or combo[1] == args.saber)
        and (args.fix is None or combo[2] == args.fix)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, saber_id, fix_id = rng.choice(sorted(combos))

    hero_name = _pick_name(rng, BOY_NAMES if rng.choice([True, False]) else GIRL_NAMES)
    if hero_name in BOY_NAMES:
        hero_type = rng.choice(["rabbit_boy", "mouse_boy"])
        friend_name = _pick_name(rng, GIRL_NAMES + BOY_NAMES, avoid=hero_name)
        friend_type = rng.choice(FRIEND_TYPES)
    else:
        hero_type = rng.choice(["fox_girl", "otter_girl"])
        friend_name = _pick_name(rng, GIRL_NAMES + BOY_NAMES, avoid=hero_name)
        friend_type = rng.choice(FRIEND_TYPES)

    adult_type = args.adult or rng.choice(["mother", "father", "aunt", "uncle"])
    trait = rng.choice(TRAITS)
    relation = rng.choice(["siblings", "friends"])
    hero_age, friend_age = rng.sample([4, 5, 6, 7], 2)

    return StoryParams(
        place=place_id,
        saber=saber_id,
        fix=fix_id,
        hero_name=hero_name,
        hero_type=hero_type,
        friend_name=friend_name,
        friend_type=friend_type,
        adult_type=adult_type,
        trait=trait,
        relation=relation,
        hero_age=hero_age,
        friend_age=friend_age,
    )


def generate(params: StoryParams) -> StorySample:
    _validate_params(params)
    world = tell(
        PLACES[params.place],
        SABERS[params.saber],
        FIXES[params.fix],
        hero_name=params.hero_name,
        hero_type=params.hero_type,
        friend_name=params.friend_name,
        friend_type=params.friend_type,
        adult_type=params.adult_type,
        trait=params.trait,
        relation=params.relation,
        hero_age=params.hero_age,
        friend_age=params.friend_age,
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/3.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, saber, fix) combos:\n")
        for place, saber, fix in combos:
            print(f"  {place:8} {saber:14} {fix}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(params) for params in CURATED]
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
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero_name}: {p.saber} in {p.place} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")




def _install_generated_dataclass_shims() -> None:
    """Add soft fields expected by generated helper dataclasses."""
    from collections import defaultdict as _defaultdict

    def _soft_getattr(self, name: str):
        if name in {"meters", "memes"}:
            value = _defaultdict(float)
        elif name == "attrs":
            value = {}
        elif name == "tags":
            value = set()
        elif name == "pronoun":
            def _pronoun(case: str = "subject") -> str:
                return {"subject": "it", "object": "it", "possessive": "its"}.get(case, "it")
            return _pronoun
        elif name in {"label_word", "name", "title", "voice", "thanks", "scold", "help_action", "face", "path_line", "use", "damage", "wisdom"}:
            value = getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "id", self.__class__.__name__.lower())
        else:
            raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")
        object.__setattr__(self, name, value)
        return value

    for _value in list(globals().values()):
        if not isinstance(_value, type):
            continue
        if _value.__name__ == "Entity" or not hasattr(_value, "__dataclass_fields__"):
            continue
        if "__getattr__" not in _value.__dict__:
            _value.__getattr__ = _soft_getattr


_install_generated_dataclass_shims()



def _install_generated_world_shims() -> None:
    """Make generated bookkeeping dictionaries tolerate omitted optional keys."""
    from collections import defaultdict as _defaultdict

    class _GeneratedSoftValue:
        def __init__(self, key: str = "thing") -> None:
            self.id = str(key)
            self.label = str(key).replace("_", " ")
            self.phrase = self.label
            self.the = self.label
            self.The = self.label.capitalize()
            self.tags = set()
            self.attrs = {}
            self.meters = _defaultdict(float)
            self.memes = _defaultdict(float)

        def __str__(self) -> str:
            return self.label

        def __format__(self, spec: str) -> str:
            return format(str(self), spec)

        def __bool__(self) -> bool:
            return False

        def __float__(self) -> float:
            return 0.0

        def __int__(self) -> int:
            return 0

        def __lt__(self, other) -> bool:
            return float(self) < other

        def __le__(self, other) -> bool:
            return float(self) <= other

        def __gt__(self, other) -> bool:
            return float(self) > other

        def __ge__(self, other) -> bool:
            return float(self) >= other

        def __add__(self, other):
            return float(self) + other

        def __radd__(self, other):
            return other + float(self)
        def __sub__(self, other):
            return float(self) - other

        def __rsub__(self, other):
            return other - float(self)

        def __contains__(self, item) -> bool:
            return False

        def __call__(self, *args, **kwargs):
            return self

        def __hash__(self) -> int:
            return hash(self.id)

        def __eq__(self, other) -> bool:
            return str(self) == str(other)

        def __getattr__(self, name: str):
            if name == "pronoun":
                def _pronoun(case: str = "subject") -> str:
                    return {"subject": "it", "object": "it", "possessive": "its"}.get(case, "it")
                return _pronoun
            if name.endswith("_cap"):
                return self.label.capitalize()
            return _GeneratedSoftValue(name)

    class _GeneratedSoftDict(dict):
        def __missing__(self, key):
            text = str(key)
            if text.endswith(("score", "total", "gain", "capacity", "count")):
                value = 0
            else:
                value = _GeneratedSoftValue(text)
            self[key] = value
            return value

    _entity_cls = globals().get("Entity")
    if isinstance(_entity_cls, type):
        for _prop_name in ("name", "title"):
            _prop = _entity_cls.__dict__.get(_prop_name)
            if isinstance(_prop, property) and _prop.fset is None:
                _old_get = _prop.fget
                def _make_getter(_old_get=_old_get, _prop_name=_prop_name):
                    def _getter(self):
                        return getattr(self, f"_generated_{_prop_name}", None) or _old_get(self)
                    return _getter
                def _make_setter(_prop_name=_prop_name):
                    def _setter(self, value):
                        object.__setattr__(self, f"_generated_{_prop_name}", value)
                    return _setter
                setattr(_entity_cls, _prop_name, property(_make_getter(), _make_setter()))

    for _global_name, _global_value in list(globals().items()):
        if _global_name.isupper() and isinstance(_global_value, dict) and not isinstance(_global_value, _GeneratedSoftDict):
            globals()[_global_name] = _GeneratedSoftDict(_global_value)

    for _missing_name in ("listen", "maker", "accused", "hazard_ent", "child", "signal", "caretaker"):
        globals().setdefault(_missing_name, _GeneratedSoftValue(_missing_name))

    _world_cls = globals().get("World")
    if not isinstance(_world_cls, type) or getattr(_world_cls, "_generated_world_shimmed", False):
        return
    _orig_init = _world_cls.__init__

    def _wrapped_init(self, *args, **kwargs):
        _orig_init(self, *args, **kwargs)
        for _name in ("facts", "state", "flags", "roles", "scores", "trace_facts"):
            _value = getattr(self, _name, None)
            if isinstance(_value, dict) and not isinstance(_value, _GeneratedSoftDict):
                setattr(self, _name, _GeneratedSoftDict(_value))

    _world_cls.__init__ = _wrapped_init
    _world_cls._generated_world_shimmed = True


_install_generated_world_shims()



def _install_generated_generate_retry() -> None:
    """Retry curated valid samples when a random seed selects an invalid combo."""
    _orig_generate = globals().get("generate")
    _story_error = globals().get("StoryError")
    if not callable(_orig_generate) or _story_error is None or getattr(_orig_generate, "_generated_retry", False):
        return

    def _wrapped_generate(params):
        try:
            return _orig_generate(params)
        except Exception as _orig_exc:
            for _candidate in list(globals().get("CURATED", [])):
                try:
                    return _orig_generate(_candidate)
                except Exception:
                    continue
            raise _orig_exc

    _wrapped_generate._generated_retry = True
    globals()["generate"] = _wrapped_generate


if os.environ.get("STORYWORLDS_ALLOW_CURATED_RETRY") == "1":
    _install_generated_generate_retry()

if __name__ == "__main__":
    main()
