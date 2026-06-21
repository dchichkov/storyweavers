#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/compliant_foreshadowing_bedtime_story.py
===================================================================

A small bedtime storyworld about a child who wants to sleep with the window open.
Tiny signs in the night foreshadow a coming shower. A grown-up predicts what the
rain would do, offers a safer substitute that meets the same bedtime need, and
the child either agrees before the rain arrives or learns from a small soggy
mistake.

Run it
------
python storyworlds/worlds/gpt-5.4/compliant_foreshadowing_bedtime_story.py
python storyworlds/worlds/gpt-5.4/compliant_foreshadowing_bedtime_story.py --motive moonlight
python storyworlds/worlds/gpt-5.4/compliant_foreshadowing_bedtime_story.py --all
python storyworlds/worlds/gpt-5.4/compliant_foreshadowing_bedtime_story.py -n 5 --seed 7
python storyworlds/worlds/gpt-5.4/compliant_foreshadowing_bedtime_story.py --qa --json
python storyworlds/worlds/gpt-5.4/compliant_foreshadowing_bedtime_story.py --verify
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
COMPLIANCE_BASE = 4
CALM_BONUS = {"easygoing": 2, "gentle": 1, "thoughtful": 1, "stubborn": -1, "spirited": -1}
LIGHT_LEVEL = {"far_thunder": 1, "restless_leaves": 1, "lightning_flicker": 2, "first_raindrops": 2}


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    plural: bool = False
    openable: bool = False
    vulnerable: bool = False
    soothing: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

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

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Motive:
    id: str
    need: str
    wish: str
    line: str
    bedtime_image: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Sign:
    id: str
    severity: int
    hint: str
    room_effect: str
    warning_line: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Keepsake:
    id: str
    label: str
    phrase: str
    soak_text: str
    rescued_text: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Remedy:
    id: str
    need: str
    label: str
    phrase: str
    action: str
    ending: str
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


def _r_open_window_risk(world: World) -> list[str]:
    out: list[str] = []
    window = world.get("window")
    room = world.get("room")
    keepsake = world.get("keepsake")
    if window.meters["open"] >= THRESHOLD and room.meters["storm"] >= THRESHOLD:
        sig = ("rain_risk", keepsake.id)
        if sig not in world.fired:
            world.fired.add(sig)
            keepsake.meters["risk"] += 1
            out.append("__risk__")
    return out


def _r_rain_soaks(world: World) -> list[str]:
    out: list[str] = []
    window = world.get("window")
    room = world.get("room")
    keepsake = world.get("keepsake")
    if window.meters["open"] >= THRESHOLD and room.meters["rain_inside"] >= THRESHOLD:
        sig = ("soak", keepsake.id)
        if sig not in world.fired:
            world.fired.add(sig)
            keepsake.meters["wet"] += 1
            room.meters["mess"] += 1
            out.append("__soak__")
    return out


CAUSAL_RULES = [
    Rule(name="open_window_risk", tag="physical", apply=_r_open_window_risk),
    Rule(name="rain_soaks", tag="physical", apply=_r_rain_soaks),
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
            if not sent.startswith("__"):
                world.say(sent)
    return produced


MOTIVES = {
    "moonlight": Motive(
        id="moonlight",
        need="light",
        wish="keep the window open so the moon could shine across the blanket",
        line='"Please leave it open a little," said {child}. "I like the moon making a silver road on my bed."',
        bedtime_image="a silver stripe from the moon",
        tags={"moon", "window"},
    ),
    "breeze": Motive(
        id="breeze",
        need="air",
        wish="keep the window open for the cool night breeze",
        line='"Please leave it open a little," said {child}. "I like the cool air on my cheeks when I get sleepy."',
        bedtime_image="the cool air on sleepy cheeks",
        tags={"air", "window"},
    ),
    "night_sounds": Motive(
        id="night_sounds",
        need="sound",
        wish="keep the window open to hear the little night sounds outside",
        line='"Please leave it open a little," said {child}. "I like hearing the crickets and the leaves while I fall asleep."',
        bedtime_image="soft little sounds from outside",
        tags={"sound", "window"},
    ),
}

SIGNS = {
    "far_thunder": Sign(
        id="far_thunder",
        severity=1,
        hint="Far away, thunder rolled so softly it sounded like a giant turning over in bed.",
        room_effect="The curtain gave one small shiver at the window.",
        warning_line="That kind of rumble usually means a shower is walking this way.",
        tags={"thunder", "storm"},
    ),
    "restless_leaves": Sign(
        id="restless_leaves",
        severity=1,
        hint="The leaves outside rubbed together in a quick, restless whisper instead of their usual sleepy hush.",
        room_effect="The curtain kept lifting and settling again.",
        warning_line="When the leaves start fussing like that at bedtime, rain is often close behind.",
        tags={"leaves", "storm"},
    ),
    "lightning_flicker": Sign(
        id="lightning_flicker",
        severity=2,
        hint="A pale flicker blinked behind the clouds and was gone before the child could count to two.",
        room_effect="For a moment the room turned white, then soft and dim again.",
        warning_line="A sky that flickers like that does not stay dry for long.",
        tags={"lightning", "storm"},
    ),
    "first_raindrops": Sign(
        id="first_raindrops",
        severity=2,
        hint="At the sill came the first tiny taps of rain, light as fingertips.",
        room_effect="The air by the bed smelled cool and wet.",
        warning_line="Those first drops are the rain asking to come in.",
        tags={"rain", "storm"},
    ),
}

KEEPSAKES = {
    "library_book": Keepsake(
        id="library_book",
        label="library book",
        phrase="a library book with a bear on the cover",
        soak_text="The book's corners curled and the bear on the cover looked sadly wrinkled.",
        rescued_text="lifted the library book away before more drops could touch it",
        tags={"book"},
    ),
    "paper_stars": Keepsake(
        id="paper_stars",
        label="paper stars",
        phrase="a chain of paper stars taped beside the bed",
        soak_text="The paper stars sagged on their string, and a little blue star peeled loose.",
        rescued_text="peeled the paper stars gently from the wall before they could tear",
        tags={"paper", "stars"},
    ),
    "quilt": Keepsake(
        id="quilt",
        label="quilt",
        phrase="a patchwork quilt sewn by Grandma",
        soak_text="A dark damp patch spread over the sleepy patchwork squares.",
        rescued_text="pulled the quilt back from the window before the wet patch could grow",
        tags={"blanket", "quilt"},
    ),
}

REMEDIES = {
    "nightlight": Remedy(
        id="nightlight",
        need="light",
        label="night-light",
        phrase="a moon-shaped night-light",
        action="plugged in the moon-shaped night-light, and a warm pearl glow bloomed near the bed",
        ending="The little lamp made its own moon in the room.",
        tags={"nightlight", "light"},
    ),
    "fan": Remedy(
        id="fan",
        need="air",
        label="fan",
        phrase="a small humming fan",
        action="set the small fan on the dresser, and a cool gentle breeze brushed the blanket",
        ending="The fan sent a safe little breeze through the room.",
        tags={"fan", "air"},
    ),
    "music_box": Remedy(
        id="music_box",
        need="sound",
        label="music box",
        phrase="a tiny music box",
        action="wound the tiny music box, and a soft tune drifted through the room like slow footsteps",
        ending="The music box filled the room with soft bedtime sounds.",
        tags={"music", "sound"},
    ),
}


def compatible(motive: Motive, remedy: Remedy) -> bool:
    return motive.need == remedy.need


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for motive_id, motive in MOTIVES.items():
        for sign_id in SIGNS:
            for keepsake_id in KEEPSAKES:
                for remedy_id, remedy in REMEDIES.items():
                    if compatible(motive, remedy):
                        combos.append((motive_id, sign_id, keepsake_id, remedy_id))
    return combos


def initial_compliance(trait: str) -> int:
    return COMPLIANCE_BASE + CALM_BONUS.get(trait, 0)


def will_comply(trait: str, sign: Sign, closeness: int) -> bool:
    return initial_compliance(trait) + sign.severity + closeness >= 6


def predict_open_window(world: World) -> dict:
    sim = world.copy()
    sim.get("window").meters["open"] = 1
    sim.get("room").meters["storm"] = 1
    if sim.facts["sign"].severity >= 2:
        sim.get("room").meters["rain_inside"] = 1
    propagate(sim, narrate=False)
    return {
        "risk": sim.get("keepsake").meters["risk"] >= THRESHOLD,
        "wet": sim.get("keepsake").meters["wet"] >= THRESHOLD,
    }


def introduce(world: World, child: Entity, parent: Entity, keepsake: Entity) -> None:
    world.say(
        f"In a small quiet bedroom, {child.id} was getting ready for sleep while "
        f"{child.pronoun('possessive')} {parent.label_word} tucked {keepsake.phrase} near the bed."
    )
    world.say(
        f"The sheets were cool, the lamp was low, and the whole room felt as if it were already whispering good night."
    )


def bedtime_wish(world: World, child: Entity, motive: Motive) -> None:
    child.memes["desire"] += 1
    world.say(motive.line.format(child=child.id))


def foreshadow(world: World, sign: Sign) -> None:
    world.say(sign.hint)
    world.say(sign.room_effect)
    world.get("room").meters["storm"] = 1
    propagate(world, narrate=False)


def warn(world: World, parent: Entity, child: Entity, sign: Sign, motive: Motive) -> None:
    pred = predict_open_window(world)
    world.facts["predicted_risk"] = pred["risk"]
    world.facts["predicted_wet"] = pred["wet"]
    keepsake = world.get("keepsake")
    world.say(
        f'{parent.label_word.capitalize()} listened for a moment and said, "{sign.warning_line} '
        f'If the window stays open, the rain could reach the {keepsake.label}."'
    )
    child.memes["caution"] += 1


def offer(world: World, parent: Entity, remedy: Remedy, motive: Motive) -> None:
    need_words = {
        "light": "light without the open window",
        "air": "a breeze without the open window",
        "sound": "soft bedtime sounds without the open window",
    }
    world.say(
        f'"We can still have {need_words[motive.need]}," said {parent.label_word}. '
        f'"Let me get {remedy.phrase}."'
    )


def agree(world: World, child: Entity, parent: Entity) -> None:
    child.memes["trust"] += 1
    child.memes["calm"] += 1
    child.memes["compliant"] += 1
    world.get("window").meters["open"] = 0
    world.say(
        f"{child.id} looked at the dark window and then at {child.pronoun('possessive')} {parent.label_word}. "
        f"{child.pronoun().capitalize()} gave a small nod and grew quiet and compliant."
    )
    world.say(f'"All right," {child.pronoun()} whispered. "Let\'s do the cozy way."')


def hesitate(world: World, child: Entity) -> None:
    child.memes["reluctance"] += 1
    world.get("window").meters["open"] = 1
    world.say(
        f"But {child.id} still wanted the window open. {child.pronoun().capitalize()} pulled the blanket to {child.pronoun('possessive')} chin and said, "
        f'"Just for one little minute more."'
    )


def rain_turn(world: World, child: Entity, sign: Sign, keepsake_cfg: Keepsake) -> None:
    room = world.get("room")
    room.meters["rain_inside"] = 1
    propagate(world, narrate=False)
    child.memes["surprise"] += 1
    child.memes["fear"] += 1
    world.say(
        f"Then the night stopped hinting and began. Rain pattered through the open gap, and a cold sprinkle reached the bed."
    )
    world.say(keepsake_cfg.soak_text)


def rescue(world: World, parent: Entity, remedy: Remedy, keepsake_cfg: Keepsake) -> None:
    keepsake = world.get("keepsake")
    keepsake.meters["wet"] = max(0.0, keepsake.meters["wet"])
    world.get("window").meters["open"] = 0
    world.say(
        f"{parent.label_word.capitalize()} moved quickly, shut the window, and {keepsake_cfg.rescued_text}."
    )
    world.say(
        f"Then {parent.pronoun()} {remedy.action}."
    )


def soothe(world: World, child: Entity, parent: Entity) -> None:
    child.memes["fear"] = 0.0
    child.memes["calm"] += 1
    child.memes["trust"] += 1
    child.memes["compliant"] += 1
    world.say(
        f'{parent.label_word.capitalize()} sat on the edge of the bed and rubbed slow circles on the blanket. '
        f'"See?" {parent.pronoun()} said softly. "We can make the room cozy and keep our dear things dry too."'
    )
    world.say(
        f"{child.id} nodded again, this time even more compliant than before, and snuggled down."
    )


def settle(world: World, child: Entity, remedy: Remedy, motive: Motive, soaked: bool) -> None:
    world.say(remedy.ending)
    if soaked:
        world.say(
            f"Soon the room was warm and gentle again, and {child.id}'s breathing slowed until sleep found {child.pronoun('object')}."
        )
    else:
        world.say(
            f"With the window safely shut, {child.id} listened, watched, or felt what {child.pronoun()} had hoped for in a safer way, and sleep came softly at last."
        )


def tell(
    motive: Motive,
    sign: Sign,
    keepsake_cfg: Keepsake,
    remedy: Remedy,
    *,
    child_name: str = "Lina",
    child_gender: str = "girl",
    parent_type: str = "mother",
    trait: str = "gentle",
    closeness: int = 1,
) -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="child", traits=[trait]))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, role="parent", label="the parent"))
    room = world.add(Entity(id="room", type="room", label="bedroom"))
    window = world.add(Entity(id="window", type="window", label="window", openable=True))
    keepsake = world.add(
        Entity(
            id="keepsake",
            type="keepsake",
            label=keepsake_cfg.label,
            phrase=keepsake_cfg.phrase,
            vulnerable=True,
        )
    )
    helper = world.add(
        Entity(
            id="remedy",
            type="helper",
            label=remedy.label,
            phrase=remedy.phrase,
            soothing=True,
        )
    )
    room.meters["quiet"] = 1
    world.facts.update(
        child=child,
        parent=parent,
        room=room,
        window=window,
        keepsake=keepsake,
        motive=motive,
        sign=sign,
        keepsake_cfg=keepsake_cfg,
        remedy=remedy,
        trait=trait,
        closeness=closeness,
    )

    introduce(world, child, parent, keepsake)
    bedtime_wish(world, child, motive)

    world.para()
    foreshadow(world, sign)
    warn(world, parent, child, sign, motive)
    offer(world, parent, remedy, motive)

    outcome = "compliant" if will_comply(trait, sign, closeness) else "soaked"

    world.para()
    if outcome == "compliant":
        agree(world, child, parent)
        world.say(f"{parent.label_word.capitalize()} {remedy.action}.")
        settle(world, child, remedy, motive, soaked=False)
    else:
        hesitate(world, child)
        rain_turn(world, child, sign, keepsake_cfg)
        rescue(world, parent, remedy, keepsake_cfg)
        soothe(world, child, parent)
        settle(world, child, remedy, motive, soaked=True)

    world.facts.update(
        outcome=outcome,
        sign_severity=sign.severity,
        complied=(outcome == "compliant") or child.memes["compliant"] >= THRESHOLD,
        wet=world.get("keepsake").meters["wet"] >= THRESHOLD,
        risk=world.get("keepsake").meters["risk"] >= THRESHOLD,
    )
    return world


@dataclass
class StoryParams:
    motive: str
    sign: str
    keepsake: str
    remedy: str
    child_name: str
    child_gender: str
    parent: str
    trait: str
    closeness: int
    seed: Optional[int] = None


GIRL_NAMES = ["Lina", "Mira", "Nora", "Ava", "Lily", "Elsie", "Ruby", "Maya"]
BOY_NAMES = ["Owen", "Milo", "Theo", "Ben", "Noah", "Eli", "Finn", "Leo"]
TRAITS = ["easygoing", "gentle", "thoughtful", "spirited", "stubborn"]

CURATED = [
    StoryParams(
        motive="moonlight",
        sign="far_thunder",
        keepsake="library_book",
        remedy="nightlight",
        child_name="Lina",
        child_gender="girl",
        parent="mother",
        trait="gentle",
        closeness=1,
    ),
    StoryParams(
        motive="breeze",
        sign="restless_leaves",
        keepsake="quilt",
        remedy="fan",
        child_name="Milo",
        child_gender="boy",
        parent="father",
        trait="easygoing",
        closeness=1,
    ),
    StoryParams(
        motive="night_sounds",
        sign="lightning_flicker",
        keepsake="paper_stars",
        remedy="music_box",
        child_name="Nora",
        child_gender="girl",
        parent="mother",
        trait="spirited",
        closeness=0,
    ),
    StoryParams(
        motive="moonlight",
        sign="first_raindrops",
        keepsake="quilt",
        remedy="nightlight",
        child_name="Theo",
        child_gender="boy",
        parent="father",
        trait="stubborn",
        closeness=0,
    ),
]


KNOWLEDGE = {
    "moon": [(
        "Why does moonlight look soft in a bedroom?",
        "Moonlight is sunlight bouncing off the moon, so by the time it reaches a bedroom it feels pale and gentle instead of bright like daytime."
    )],
    "window": [(
        "Why should a window be shut before rain blows in?",
        "Rain can come through an open window when the wind pushes it sideways. That can make books, blankets, and paper things wet."
    )],
    "thunder": [(
        "What is thunder?",
        "Thunder is the big rumbling sound that comes after lightning. It happens when lightning heats the air very fast."
    )],
    "lightning": [(
        "Why can lightning be a sign that rain is coming?",
        "Lightning often happens in storm clouds, so it can mean rain is nearby or already on the way."
    )],
    "rain": [(
        "What are the first raindrops like?",
        "The first raindrops can sound like tiny taps on a roof or windowsill. They are often the first sign that a shower is beginning."
    )],
    "book": [(
        "Why do books get wrinkly when they get wet?",
        "Paper soaks up water. When paper dries again, it can curl and wrinkle."
    )],
    "paper": [(
        "Why is paper easy to damage with water?",
        "Paper is thin and thirsty, so it soaks up water quickly and can tear or sag."
    )],
    "quilt": [(
        "What is a quilt?",
        "A quilt is a blanket made from pieces of cloth sewn together. Many quilts feel special because someone made them with care."
    )],
    "nightlight": [(
        "What does a night-light do?",
        "A night-light gives a small gentle glow in the dark. It helps a room feel cozy without needing a bright lamp or an open window."
    )],
    "fan": [(
        "What does a fan do at bedtime?",
        "A fan moves air around the room. That can make a child feel cooler without opening the window."
    )],
    "music": [(
        "What is a music box?",
        "A music box is a small object that plays a soft tune. Its gentle sound can help make bedtime feel calm."
    )],
}
KNOWLEDGE_ORDER = [
    "moon", "window", "thunder", "lightning", "rain",
    "book", "paper", "quilt", "nightlight", "fan", "music",
]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    motive = f["motive"]
    sign = f["sign"]
    remedy = f["remedy"]
    if f["outcome"] == "compliant":
        return [
            f'Write a bedtime story for a 3-to-5-year-old that includes the word "compliant" and uses foreshadowing with {sign.id.replace("_", " ")}.',
            f"Tell a gentle story where {child.id} wants the window open for {motive.need}, but a parent notices signs of rain and helps {child.pronoun('object')} choose {remedy.phrase} instead.",
            f"Write a sleepy story with a small warning in the middle and a cozy safe ending."
        ]
    return [
        f'Write a bedtime story for a 3-to-5-year-old that includes the word "compliant" and uses foreshadowing before a small rainy mishap.',
        f"Tell a gentle bedtime story where {child.id} wants the window open, the storm is hinted at first, and a parent fixes a soggy problem with {remedy.phrase}.",
        f"Write a calm story with a tiny mistake, a quick rescue, and a soft bedtime ending."
    ]


def story_qa_items(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    parent = f["parent"]
    motive = f["motive"]
    sign = f["sign"]
    keepsake = f["keepsake_cfg"]
    remedy = f["remedy"]
    pw = parent.label_word
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id} at bedtime and {child.pronoun('possessive')} {pw}. They were trying to make the room feel cozy for sleep."
        ),
        (
            "What did the child want?",
            f"{child.id} wanted to keep the window open because {motive.bedtime_image} felt comforting. That wish is what started the bedtime problem."
        ),
        (
            "What foreshadowed the trouble?",
            f"{sign.hint} {sign.room_effect} Those little signs warned that the room might not stay dry."
        ),
        (
            f"Why did {child.id}'s {pw} worry about the window?",
            f"{pw.capitalize()} knew rain might blow in through the open window and reach the {keepsake.label}. The warning came from the storm signs and from seeing how close the keepsake was to the bed."
        ),
    ]
    if f["outcome"] == "compliant":
        qa.append(
            (
                f"How did {child.id} solve the problem?",
                f"{child.id} became quiet and compliant and agreed to shut the window before the rain came. Then {pw} used {remedy.phrase} to give the room the same comfort in a safer way."
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It ended peacefully with the window shut, the {remedy.label} helping the room feel cozy, and {child.id} falling asleep dry and calm. The ending shows that bedtime felt safe after the choice changed."
            )
        )
    else:
        qa.append(
            (
                "What happened when the child waited too long?",
                f"Rain blew in through the open window and wet the {keepsake.label}. The small soggy mess proved that the warning had been true."
            )
        )
        qa.append(
            (
                f"What did {child.id}'s {pw} do then?",
                f"{pw.capitalize()} shut the window, rescued the {keepsake.label}, and used {remedy.phrase} to make the room cozy again. After that, {child.id} felt calmer and more compliant."
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It ended gently even after the mistake. The room was dry again, the grown-up had fixed what could be fixed, and {child.id} settled down to sleep."
            )
        )
    return qa


def world_knowledge_items(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = set()
    tags |= f["motive"].tags
    tags |= f["sign"].tags
    tags |= f["keepsake_cfg"].tags
    tags |= f["remedy"].tags
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags and tag in KNOWLEDGE:
            out.extend(KNOWLEDGE[tag])
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, prompt in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {prompt}")
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
    for entity in list(world.entities.values()):
        meters = {k: v for k, v in entity.meters.items() if v}
        memes = {k: v for k, v in entity.memes.items() if v}
        bits = []
        if entity.role:
            bits.append(f"role={entity.role}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        flags = [name for name, on in (
            ("openable", entity.openable),
            ("vulnerable", entity.vulnerable),
            ("soothing", entity.soothing),
        ) if on]
        if flags:
            bits.append(f"flags={flags}")
        lines.append(f"  {entity.id:8} ({entity.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


def explain_rejection(motive_id: str, remedy_id: str) -> str:
    motive = MOTIVES[motive_id]
    remedy = REMEDIES[remedy_id]
    return (
        f"(No story: {remedy.phrase} does not answer the child's bedtime need for "
        f"{motive.need}. Pick a remedy that truly replaces what the open window was for.)"
    )


def outcome_of(params: StoryParams) -> str:
    if params.sign not in SIGNS or params.trait not in TRAITS:
        raise StoryError("(No story: invalid sign or trait for outcome check.)")
    return "compliant" if will_comply(params.trait, SIGNS[params.sign], params.closeness) else "soaked"


ASP_RULES = r"""
compatible(M, R) :- motive(M), remedy(R), needs(M, N), serves(R, N).
valid(M, S, K, R) :- motive(M), sign(S), keepsake(K), compatible(M, R).

temper_score(T, V) :- trait(T), temper_value(T, V).
compliance_total(V + Sev + C) :- chosen_trait(T), temper_score(T, V),
                                 chosen_sign(S), severity(S, Sev),
                                 closeness(C).
outcome(compliant) :- compliance_total(T), T >= 6.
outcome(soaked) :- compliance_total(T), T < 6.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for motive_id, motive in MOTIVES.items():
        lines.append(asp.fact("motive", motive_id))
        lines.append(asp.fact("needs", motive_id, motive.need))
    for sign_id, sign in SIGNS.items():
        lines.append(asp.fact("sign", sign_id))
        lines.append(asp.fact("severity", sign_id, sign.severity))
    for keepsake_id in KEEPSAKES:
        lines.append(asp.fact("keepsake", keepsake_id))
    for remedy_id, remedy in REMEDIES.items():
        lines.append(asp.fact("remedy", remedy_id))
        lines.append(asp.fact("serves", remedy_id, remedy.need))
    for trait in TRAITS:
        lines.append(asp.fact("trait", trait))
        lines.append(asp.fact("temper_value", trait, initial_compliance(trait)))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp
    scenario = "\n".join([
        asp.fact("chosen_trait", params.trait),
        asp.fact("chosen_sign", params.sign),
        asp.fact("closeness", params.closeness),
    ])
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0

    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: valid combos match ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    cases = list(CURATED)
    parser = build_parser()
    for seed in range(30):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(seed))
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
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("empty story")
        print("OK: smoke test generated a normal story.")
    except Exception as exc:
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: bedtime, foreshadowed rain, and a safer cozy choice."
    )
    ap.add_argument("--motive", choices=sorted(MOTIVES))
    ap.add_argument("--sign", choices=sorted(SIGNS))
    ap.add_argument("--keepsake", choices=sorted(KEEPSAKES))
    ap.add_argument("--remedy", choices=sorted(REMEDIES))
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("--closeness", type=int, choices=[0, 1], help="how immediate the storm feels")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible-story combos from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP parity and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.motive and args.remedy and not compatible(MOTIVES[args.motive], REMEDIES[args.remedy]):
        raise StoryError(explain_rejection(args.motive, args.remedy))

    combos = [
        combo for combo in valid_combos()
        if (args.motive is None or combo[0] == args.motive)
        and (args.sign is None or combo[1] == args.sign)
        and (args.keepsake is None or combo[2] == args.keepsake)
        and (args.remedy is None or combo[3] == args.remedy)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    motive_id, sign_id, keepsake_id, remedy_id = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = args.trait or rng.choice(TRAITS)
    closeness = args.closeness if args.closeness is not None else rng.choice([0, 1])
    return StoryParams(
        motive=motive_id,
        sign=sign_id,
        keepsake=keepsake_id,
        remedy=remedy_id,
        child_name=name,
        child_gender=gender,
        parent=parent,
        trait=trait,
        closeness=closeness,
    )


def generate(params: StoryParams) -> StorySample:
    for field_name, registry in (
        ("motive", MOTIVES),
        ("sign", SIGNS),
        ("keepsake", KEEPSAKES),
        ("remedy", REMEDIES),
    ):
        value = getattr(params, field_name)
        if value not in registry:
            raise StoryError(f"(No story: invalid {field_name} '{value}'.)")
    if params.trait not in TRAITS:
        raise StoryError(f"(No story: invalid trait '{params.trait}'.)")
    if params.child_gender not in {"girl", "boy"}:
        raise StoryError(f"(No story: invalid gender '{params.child_gender}'.)")
    if params.parent not in {"mother", "father"}:
        raise StoryError(f"(No story: invalid parent '{params.parent}'.)")
    if params.closeness not in {0, 1}:
        raise StoryError(f"(No story: invalid closeness '{params.closeness}'.)")
    if not compatible(MOTIVES[params.motive], REMEDIES[params.remedy]):
        raise StoryError(explain_rejection(params.motive, params.remedy))

    world = tell(
        MOTIVES[params.motive],
        SIGNS[params.sign],
        KEEPSAKES[params.keepsake],
        REMEDIES[params.remedy],
        child_name=params.child_name,
        child_gender=params.child_gender,
        parent_type=params.parent,
        trait=params.trait,
        closeness=params.closeness,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa_items(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_items(world)],
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
        print(asp_program("", "#show valid/4.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (motive, sign, keepsake, remedy) combos:\n")
        for motive_id, sign_id, keepsake_id, remedy_id in combos:
            print(f"  {motive_id:12} {sign_id:16} {keepsake_id:12} {remedy_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        samples: list[StorySample] = []
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
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = (
                f"### {p.child_name}: {p.motive} with {p.sign} "
                f"({outcome_of(p)}, {p.remedy})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
