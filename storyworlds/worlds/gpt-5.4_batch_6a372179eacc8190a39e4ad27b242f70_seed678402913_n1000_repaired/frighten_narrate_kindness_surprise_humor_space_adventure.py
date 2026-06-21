#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/frighten_narrate_kindness_surprise_humor_space_adventure.py
======================================================================================

A standalone story world for a tiny "Space Adventure" domain.

Premise
-------
Two children play a space mission in a cardboard rocket or moon camp. A strange
sound or shadow gives one child a fright. The other child chooses how to handle
the moment. In the good stories this is done with kindness: the brave child
narrates what they are doing in a calm voice, uses a gentle tool, and discovers
that the "monster" is really a funny, harmless little visitor or helper.

The world model carries both physical state (*meters*) and feeling state
(*memes*). The prose is driven by that state: fear rises, calm spreads, trust
returns, and the ending image proves the change.

Run it
------
    python storyworlds/worlds/gpt-5.4/frighten_narrate_kindness_surprise_humor_space_adventure.py
    python storyworlds/worlds/gpt-5.4/frighten_narrate_kindness_surprise_humor_space_adventure.py --mission rocket --signal clank --reveal robot
    python storyworlds/worlds/gpt-5.4/frighten_narrate_kindness_surprise_humor_space_adventure.py --reveal moon_mouse --signal shadow
    python storyworlds/worlds/gpt-5.4/frighten_narrate_kindness_surprise_humor_space_adventure.py --approach tease
    python storyworlds/worlds/gpt-5.4/frighten_narrate_kindness_surprise_humor_space_adventure.py --all
    python storyworlds/worlds/gpt-5.4/frighten_narrate_kindness_surprise_humor_space_adventure.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/frighten_narrate_kindness_surprise_humor_space_adventure.py --verify
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
KIND_MIN = 2


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
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Mission:
    id: str
    scene: str
    build: str
    goal: str
    dark_place: str
    crew_word: str
    launch_line: str
    ending_line: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Signal:
    id: str
    label: str
    sound_text: str
    warn_text: str
    needs_light: bool = False
    needs_hatch: bool = False
    matches: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Reveal:
    id: str
    label: str
    phrase: str
    funny: str
    calm_text: str
    surprise_text: str
    sound_kind: str = ""
    hidden_in_dark: bool = False
    behind_hatch: bool = False
    kind_tags: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Approach:
    id: str
    label: str
    kindness: int
    helps_dark: bool = False
    helps_hatch: bool = False
    narrates: bool = False
    text: str = ""
    calm_bonus: int = 0
    trust_bonus: int = 0
    fear_penalty: int = 0
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
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
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_fright_spreads(world: World) -> list[str]:
    out: list[str] = []
    pilot = world.get("pilot")
    if pilot.memes["fear"] < THRESHOLD:
        return out
    sig = ("fright_spreads",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    room = world.get("room")
    room.memes["hush"] += 1
    narrator = world.get("narrator")
    narrator.memes["care"] += 1
    out.append("__fright__")
    return out


def _r_kindness_calms(world: World) -> list[str]:
    out: list[str] = []
    pilot = world.get("pilot")
    narrator = world.get("narrator")
    if narrator.memes["kindness"] < THRESHOLD or pilot.memes["fear"] < THRESHOLD:
        return out
    sig = ("kindness_calms",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    pilot.memes["fear"] = max(0.0, pilot.memes["fear"] - 1.0)
    pilot.memes["trust"] += 1
    narrator.memes["bravery"] += 1
    out.append("__calm__")
    return out


def _r_reveal_joy(world: World) -> list[str]:
    out: list[str] = []
    visitor = world.get("visitor")
    if visitor.meters["seen"] < THRESHOLD:
        return out
    sig = ("reveal_joy",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    for eid in ("pilot", "narrator"):
        world.get(eid).memes["joy"] += 1
        world.get(eid).memes["wonder"] += 1
    out.append("__surprise__")
    return out


CAUSAL_RULES = [
    Rule(name="fright_spreads", tag="emotion", apply=_r_fright_spreads),
    Rule(name="kindness_calms", tag="emotion", apply=_r_kindness_calms),
    Rule(name="reveal_joy", tag="emotion", apply=_r_reveal_joy),
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
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for sent in produced:
            world.say(sent)
    return produced


MISSIONS = {
    "rocket": Mission(
        id="rocket",
        scene="a silver cardboard rocket",
        build="The laundry basket was the cockpit, a blanket was the star map, and shiny spoon-buttons blinked along the side.",
        goal="to zip past the moon and bring back a brave report",
        dark_place="the shadowy cargo nook behind the captain's seat",
        crew_word="crew",
        launch_line='"Countdown to the comet lane!"',
        ending_line="Soon the rocket hummed with laughing again.",
        tags={"space", "rocket"},
    ),
    "moon_base": Mission(
        id="moon_base",
        scene="a moon base under the table",
        build="Chair legs became landing towers, a mixing bowl became the moon dome, and round cushions turned into bumpy little craters.",
        goal="to check the night side of the moon for mystery signals",
        dark_place="the dim supply tunnel under the moon dome",
        crew_word="explorers",
        launch_line='"Moon boots ready!"',
        ending_line="Soon the moon base felt friendly instead of spooky.",
        tags={"space", "moon"},
    ),
    "star_bus": Mission(
        id="star_bus",
        scene="a rumbling star bus",
        build="Two dining chairs were the front seats, a scarf was the glowing route map, and a box of blocks became cargo for Saturn.",
        goal="to drive across the Milky Way and deliver giggles to every stop",
        dark_place="the sleepy parcel hold behind the back seat",
        crew_word="crew",
        launch_line='"Next stop, Jupiter Junction!"',
        ending_line="Soon the star bus rolled on full of jokes and sparkly crumbs.",
        tags={"space", "bus"},
    ),
}

SIGNALS = {
    "clank": Signal(
        id="clank",
        label="metal clank",
        sound_text='From the dark came clink-clank, clink-clank, as if a tiny wrench were tap-dancing.',
        warn_text="The sound was sudden enough to frighten the pilot.",
        needs_light=False,
        needs_hatch=True,
        matches={"robot"},
        tags={"sound", "robot"},
    ),
    "squeak": Signal(
        id="squeak",
        label="soft squeak",
        sound_text='Then came a squeak-squeak, quick and tiny, like a crumb with a voice.',
        warn_text="The little noise was enough to frighten the pilot because it came from where nobody was supposed to be.",
        needs_light=True,
        needs_hatch=False,
        matches={"moon_mouse"},
        tags={"sound", "mouse"},
    ),
    "shadow": Signal(
        id="shadow",
        label="wobbling shadow",
        sound_text="A round shadow wobbled across the wall and bobbled over the maps.",
        warn_text="The moving shape could easily frighten the pilot because it looked bigger than it really was.",
        needs_light=True,
        needs_hatch=False,
        matches={"star_blob"},
        tags={"shadow", "dark"},
    ),
}

REVEALS = {
    "robot": Reveal(
        id="robot",
        label="repair robot",
        phrase="a tiny repair robot",
        funny="Its spoon-shaped arms kept saluting the wrong buttons.",
        calm_text="It only wanted to fix loose tape on the ship.",
        surprise_text="The scary clank turned out to be something helpful.",
        sound_kind="clank",
        hidden_in_dark=False,
        behind_hatch=True,
        kind_tags={"tools", "helping"},
        tags={"robot", "surprise"},
    ),
    "moon_mouse": Reveal(
        id="moon_mouse",
        label="moon mouse",
        phrase="a moon mouse with silver whiskers",
        funny="It tried to sit inside a measuring cup as if it were a royal throne.",
        calm_text="It had been following the smell of cheese crackers.",
        surprise_text="The mystery noise turned out to be a tiny hungry visitor.",
        sound_kind="squeak",
        hidden_in_dark=True,
        behind_hatch=False,
        kind_tags={"snack", "gentle"},
        tags={"mouse", "surprise"},
    ),
    "star_blob": Reveal(
        id="star_blob",
        label="star blob",
        phrase="a jelly-bright star blob",
        funny="Every time it hiccupped, a puff of glittery dust jumped out and landed on its own nose.",
        calm_text="It was only bouncing after a hiccup, not trying to scare anyone.",
        surprise_text="The giant-looking shadow turned out to be a tiny bouncy blob.",
        sound_kind="shadow",
        hidden_in_dark=True,
        behind_hatch=False,
        kind_tags={"gentle", "light"},
        tags={"blob", "surprise"},
    ),
}

APPROACHES = {
    "narrate_lantern": Approach(
        id="narrate_lantern",
        label="narrate with a star lantern",
        kindness=3,
        helps_dark=True,
        helps_hatch=False,
        narrates=True,
        text='"{pilot}, I will narrate every step," {narrator} said. "{step_one} Then {step_two}." {narrator_cap} clicked on the little star lantern so the dark would have corners again.',
        calm_bonus=2,
        trust_bonus=2,
        fear_penalty=1,
        tags={"lantern", "kindness", "narrate"},
    ),
    "narrate_hatch": Approach(
        id="narrate_hatch",
        label="narrate and open the hatch gently",
        kindness=3,
        helps_dark=False,
        helps_hatch=True,
        narrates=True,
        text='"{pilot}, listen while I narrate," {narrator} said. "{step_one} Then {step_two}." {narrator_cap} lifted the little cardboard hatch with two careful fingers instead of yanking it.',
        calm_bonus=2,
        trust_bonus=2,
        fear_penalty=1,
        tags={"hatch", "kindness", "narrate"},
    ),
    "share_snack": Approach(
        id="share_snack",
        label="offer a snack and speak softly",
        kindness=2,
        helps_dark=False,
        helps_hatch=False,
        narrates=False,
        text='{narrator_cap} held out a cheese cracker and said, "If someone small is hiding there, this is for sharing, not for shooing."',
        calm_bonus=1,
        trust_bonus=2,
        fear_penalty=1,
        tags={"snack", "kindness"},
    ),
    "tease": Approach(
        id="tease",
        label="make fun of the fear",
        kindness=0,
        helps_dark=False,
        helps_hatch=False,
        narrates=False,
        text='"It is probably just a sneezy asteroid," {narrator} said with a little laugh, but the joke landed badly.',
        calm_bonus=0,
        trust_bonus=0,
        fear_penalty=0,
        tags={"unkind"},
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Anna", "Maya", "Nora", "Rose"]
BOY_NAMES = ["Tom", "Ben", "Max", "Sam", "Leo", "Jack", "Finn", "Noah", "Eli", "Theo"]
TRAITS = ["careful", "gentle", "curious", "cheerful", "thoughtful", "brave"]


def reveal_fits_signal(signal: Signal, reveal: Reveal) -> bool:
    return reveal.id in signal.matches and reveal.sound_kind == signal.id


def approach_works(signal: Signal, reveal: Reveal, approach: Approach) -> bool:
    if approach.kindness < KIND_MIN:
        return False
    if signal.needs_light and not (approach.helps_dark or "light" in reveal.kind_tags):
        return False
    if signal.needs_hatch and not approach.helps_hatch:
        return False
    if reveal.id == "moon_mouse" and "snack" not in approach.tags and not approach.helps_dark:
        return False
    if approach.narrates:
        return True
    return approach.kindness >= 2


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for mission_id in MISSIONS:
        for signal_id, signal in SIGNALS.items():
            for reveal_id, reveal in REVEALS.items():
                if not reveal_fits_signal(signal, reveal):
                    continue
                for approach_id, approach in APPROACHES.items():
                    if approach_works(signal, reveal, approach):
                        combos.append((mission_id, signal_id, reveal_id, approach_id))
    return combos


def predict_reveal(world: World, signal_id: str, reveal_id: str, approach_id: str) -> dict:
    sim = world.copy()
    signal = SIGNALS[signal_id]
    reveal = REVEALS[reveal_id]
    approach = APPROACHES[approach_id]
    pilot = sim.get("pilot")
    narrator = sim.get("narrator")
    signal_fright(sim, pilot, signal, narrate=False)
    do_approach(sim, narrator, pilot, approach, narrate=False)
    success = approach_works(signal, reveal, approach)
    if success:
        see_reveal(sim, reveal, narrate=False)
    return {
        "fear_after": pilot.memes["fear"],
        "trust_after": pilot.memes["trust"],
        "success": success,
    }


def introduce(world: World, narrator: Entity, pilot: Entity, mission: Mission) -> None:
    for kid in (narrator, pilot):
        kid.memes["joy"] += 1
        kid.memes["wonder"] += 1
    world.say(
        f"On a bright afternoon, {narrator.id} and {pilot.id} turned the room into {mission.scene}. {mission.build}"
    )
    world.say(
        f'{mission.launch_line} {narrator.id} cried. They were on a mission {mission.goal}.'
    )


def setup_dark(world: World, pilot: Entity, mission: Mission) -> None:
    world.say(
        f"But beyond the blinking buttons lay {mission.dark_place}, and that corner looked much deeper than cardboard ought to look."
    )
    world.say(
        f'{pilot.id} leaned closer, then stopped. "Did you hear that?" {pilot.pronoun()} whispered.'
    )


def signal_fright(world: World, pilot: Entity, signal: Signal, narrate: bool = True) -> None:
    pilot.memes["fear"] += 1
    world.get("room").meters["mystery"] += 1
    propagate(world, narrate=narrate)
    if narrate:
        world.say(signal.sound_text)
        world.say(signal.warn_text)


def choose_kindness(world: World, narrator: Entity, pilot: Entity, approach: Approach,
                    signal: Signal, reveal: Reveal) -> None:
    pred = predict_reveal(world, signal.id, reveal.id, approach.id)
    world.facts["predicted_fear_after"] = pred["fear_after"]
    world.facts["predicted_success"] = pred["success"]
    narrator.memes["thinking"] += 1
    if approach.narrates:
        step_one = "First I will peek slowly"
        step_two = "I will keep talking so nothing jumps as a surprise"
    elif reveal.id == "moon_mouse":
        step_one = "First I will set down a crumb"
        step_two = "we will wait to see who wants it"
    else:
        step_one = "First I will be gentle"
        step_two = "we will find out what is really there"
    text = approach.text.format(
        pilot=pilot.id,
        narrator=narrator.id,
        narrator_cap=narrator.id,
        step_one=step_one,
        step_two=step_two,
    )
    world.say(text)


def do_approach(world: World, narrator: Entity, pilot: Entity, approach: Approach,
                narrate: bool = True) -> None:
    narrator.memes["kindness"] += 1
    narrator.memes["kindness"] += max(0, approach.kindness - 1)
    pilot.memes["fear"] += 0
    if approach.fear_penalty:
        pilot.memes["fear"] = max(0.0, pilot.memes["fear"] - float(approach.fear_penalty))
    if approach.trust_bonus:
        pilot.memes["trust"] += float(approach.trust_bonus)
    if approach.calm_bonus:
        pilot.memes["calm"] += float(approach.calm_bonus)
    if approach.id == "tease":
        pilot.memes["fear"] += 1
        pilot.memes["hurt"] += 1
        narrator.memes["kindness"] = 0.0
    propagate(world, narrate=narrate)


def hesitate(world: World, pilot: Entity, narrator: Entity, approach: Approach) -> None:
    if approach.id == "tease":
        world.say(
            f"{pilot.id} did not laugh. {pilot.pronoun().capitalize()} scooted closer to {narrator.id} instead, and the small joke made the room feel bigger and lonelier."
        )
    else:
        world.say(
            f"{pilot.id} took a breath and listened. Because {narrator.id} stayed gentle, the fright stopped growing."
        )


def see_reveal(world: World, reveal: Reveal, narrate: bool = True) -> None:
    visitor = world.get("visitor")
    visitor.label = reveal.label
    visitor.phrase = reveal.phrase
    visitor.tags |= set(reveal.tags)
    visitor.meters["seen"] += 1
    visitor.meters["harmless"] += 1
    propagate(world, narrate=narrate)
    if narrate:
        world.say(
            f"Out popped {reveal.phrase}. {reveal.surprise_text} {reveal.funny}"
        )


def kind_resolution(world: World, narrator: Entity, pilot: Entity, mission: Mission,
                    reveal: Reveal, approach: Approach) -> None:
    for kid in (narrator, pilot):
        kid.memes["joy"] += 1
        kid.memes["friendship"] += 1
    visitor = world.get("visitor")
    world.say(
        f'{pilot.id} blinked, then laughed so hard that {pilot.pronoun("possessive")} shoulders bounced. "That did not frighten me after all," {pilot.pronoun()} said, "it only surprised me."'
    )
    if approach.narrates:
        world.say(
            f"{narrator.id} grinned. \"Narrate first, panic later,\" {narrator.pronoun()} said, and that made them both laugh."
        )
    else:
        world.say(
            f"{narrator.id} smiled and crouched down kindly. {reveal.calm_text}"
        )
    if visitor.label == "moon mouse":
        world.say(
            "The moon mouse nibbled the cracker, squeaked thanks, and washed its whiskers with queenly seriousness."
        )
    elif visitor.label == "repair robot":
        world.say(
            "The repair robot patted one loose strip of tape flat and then saluted a sock by mistake."
        )
    else:
        world.say(
            "The star blob hiccupped one more sparkly puff, then hid behind the map as if it had embarrassed itself."
        )
    world.say(
        f"Together the {mission.crew_word} made room for their new little passenger, and {mission.ending_line}"
    )


def lonely_resolution(world: World, narrator: Entity, pilot: Entity, mission: Mission) -> None:
    narrator.memes["regret"] += 1
    pilot.memes["fear"] += 1
    world.say(
        f"{narrator.id} heard the wobble in {pilot.id}'s breathing and wished {narrator.pronoun()} had chosen kindness instead."
    )
    world.say(
        f"They called for {pilot.pronoun('possessive')} {world.get('parent').label_word}, who came with a warm lamp and found only a loose flap of cardboard tapping the wall."
    )
    world.say(
        f"The mission was not ruined, but it went quiet. Next time, {narrator.id} promised to speak more gently before trying to be funny."
    )
    world.say(
        f"After that, the two {mission.crew_word} launched again side by side, and the jokes felt warmer because nobody was left alone with a fright."
    )


def tell(mission: Mission, signal: Signal, reveal: Reveal, approach: Approach,
         narrator_name: str = "Lily", narrator_gender: str = "girl",
         pilot_name: str = "Tom", pilot_gender: str = "boy",
         parent_type: str = "mother", narrator_trait: str = "gentle",
         pilot_trait: str = "curious") -> World:
    world = World()
    narrator = world.add(Entity(
        id=narrator_name,
        kind="character",
        type=narrator_gender,
        label=narrator_name,
        role="narrator",
        traits=[narrator_trait],
        tags={"child"},
    ))
    pilot = world.add(Entity(
        id=pilot_name,
        kind="character",
        type=pilot_gender,
        label=pilot_name,
        role="pilot",
        traits=[pilot_trait],
        tags={"child"},
    ))
    parent = world.add(Entity(
        id="parent",
        kind="character",
        type=parent_type,
        label="the parent",
        role="parent",
        tags={"adult"},
    ))
    room = world.add(Entity(
        id="room",
        kind="thing",
        type="room",
        label="room",
        phrase="the play room",
        tags={"place"},
    ))
    visitor = world.add(Entity(
        id="visitor",
        kind="thing",
        type="visitor",
        label="mystery",
        phrase="something hidden",
    ))
    world.facts["word_narrate_used"] = approach.narrates
    world.facts["word_frighten_used"] = True

    introduce(world, narrator, pilot, mission)
    setup_dark(world, pilot, mission)

    world.para()
    signal_fright(world, pilot, signal)
    choose_kindness(world, narrator, pilot, approach, signal, reveal)
    do_approach(world, narrator, pilot, approach)
    hesitate(world, pilot, narrator, approach)

    success = approach_works(signal, reveal, approach)
    world.para()
    if success:
        see_reveal(world, reveal)
        kind_resolution(world, narrator, pilot, mission, reveal, approach)
        outcome = "kind"
    else:
        lonely_resolution(world, narrator, pilot, mission)
        outcome = "lonely"

    world.facts.update(
        mission=mission,
        signal=signal,
        reveal=reveal,
        approach=approach,
        narrator=narrator,
        pilot=pilot,
        parent=parent,
        outcome=outcome,
        success=success,
        visitor=visitor,
    )
    return world


@dataclass
class StoryParams:
    mission: str
    signal: str
    reveal: str
    approach: str
    narrator_name: str
    narrator_gender: str
    pilot_name: str
    pilot_gender: str
    parent: str
    narrator_trait: str
    pilot_trait: str
    seed: Optional[int] = None


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    mission = f["mission"]
    narrator = f["narrator"]
    pilot = f["pilot"]
    signal = f["signal"]
    reveal = f["reveal"]
    outcome = f["outcome"]
    if outcome == "kind":
        return [
            'Write a short story for a 3-to-5-year-old in a Space Adventure style that includes the words "frighten" and "narrate".',
            f"Tell a gentle space adventure where {signal.label} seems scary, but {narrator.id} handles the moment with kindness and a surprise reveal.",
            f"Write a funny, warm mission story where {pilot.id} gets a fright, then discovers that the mystery is really {reveal.phrase}, and end with the {mission.crew_word} laughing together.",
        ]
    return [
        'Write a short story for a 3-to-5-year-old in a Space Adventure style that includes the words "frighten" and "narrate".',
        f"Tell a space adventure where a silly joke is the wrong answer to fear, and the children learn that kindness works better.",
        f"Write a gentle cautionary story where {narrator.id} tries humor first, but then learns not to leave {pilot.id} alone with a fright.",
    ]


def pair_noun(a: Entity, b: Entity) -> str:
    if a.type == "girl" and b.type == "girl":
        return "two girls"
    if a.type == "boy" and b.type == "boy":
        return "two boys"
    return "a girl and a boy"


def story_questions(world: World) -> list[tuple[str, str]]:
    f = world.facts
    narrator = f["narrator"]
    pilot = f["pilot"]
    mission = f["mission"]
    signal = f["signal"]
    reveal = f["reveal"]
    approach = f["approach"]
    outcome = f["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair_noun(narrator, pilot)}, {narrator.id} and {pilot.id}, pretending to be space {mission.crew_word}. Their game becomes a real little problem when a strange signal gives {pilot.id} a fright.",
        ),
        (
            "What were they pretending to do?",
            f"They had turned the room into {mission.scene} and were on a mission {mission.goal}. The pretend adventure made the dark corner feel important and mysterious.",
        ),
        (
            f"What happened that could frighten {pilot.id}?",
            f"{signal.sound_text} {signal.warn_text} Because the noise or shadow came from the mission's dark place, it felt bigger and stranger than it really was.",
        ),
    ]
    if outcome == "kind":
        if approach.narrates:
            qa.append((
                f"How did {narrator.id} help when {pilot.id} was scared?",
                f"{narrator.id} chose kindness and said {narrator.pronoun()} would narrate each step in a calm voice. That helped {pilot.id} know what was happening next, so the fright stopped growing."
            ))
        else:
            qa.append((
                f"How did {narrator.id} help when {pilot.id} was scared?",
                f"{narrator.id} answered the fear gently instead of teasing. The soft voice and sharing idea made the hiding place feel safe enough to check."
            ))
        qa.append((
            "What was the surprise?",
            f"The scary mystery turned out to be {reveal.phrase}. The surprise is funny because it seemed huge and spooky at first, but it was really small and harmless."
        ))
        qa.append((
            "Why is the ending happy?",
            f"The children solve the mystery with kindness, and then they laugh together. The final image shows that the space mission keeps going, but now the room feels friendly instead of scary."
        ))
    else:
        qa.append((
            f"Why did the joke not help {pilot.id}?",
            f"The joke came before comfort, so {pilot.id} still felt alone with the fear. When someone is frightened, gentle help works better than laughing at the moment."
        ))
        qa.append((
            "What did the children learn?",
            f"They learned that humor is nicest when everyone feels safe first. Afterward, {narrator.id} promised to choose kindness before making a joke."
        ))
    return qa


KNOWLEDGE = {
    "space": [
        (
            "What is a rocket?",
            "A rocket is a vehicle that can travel up into space. In pretend play, children often make one from boxes, blankets, and imagination.",
        )
    ],
    "moon": [
        (
            "What is the moon?",
            "The moon is the round world that circles Earth. At night it can look bright, silver, and a little mysterious.",
        )
    ],
    "robot": [
        (
            "What does a repair robot do?",
            "A repair robot fixes small problems, like loose parts or wobbly pieces. In a story, that can make a clanking sound seem less scary once you know what it is.",
        )
    ],
    "mouse": [
        (
            "Why can a tiny squeak sound bigger in the dark?",
            "In the dark, you cannot see what made the sound, so your mind may imagine something huge. Once you look carefully, the sound often belongs to something small.",
        )
    ],
    "dark": [
        (
            "Why can shadows look scary?",
            "Shadows can stretch and wobble, which makes them look bigger than the real thing. A soft light helps your eyes understand what you are seeing.",
        )
    ],
    "kindness": [
        (
            "How can kindness help when someone feels scared?",
            "Kindness helps by making the scared person feel less alone. A calm voice, gentle steps, or sharing something safe can turn fear into trust.",
        )
    ],
    "narrate": [
        (
            "What does narrate mean?",
            "To narrate means to tell what is happening. Saying each step out loud can help someone know what comes next and feel calmer.",
        )
    ],
    "humor": [
        (
            "When is humor kind?",
            "Humor is kind when everyone can laugh together. If someone is still scared, it is better to comfort them first and joke later.",
        )
    ],
    "surprise": [
        (
            "What is a surprise in a story?",
            "A surprise is something unexpected that changes what you thought was happening. A good surprise can turn a scary moment into a funny one.",
        )
    ],
}

KNOWLEDGE_ORDER = ["space", "moon", "robot", "mouse", "dark", "kindness", "narrate", "humor", "surprise"]


def world_knowledge_questions(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = set(f["mission"].tags) | set(f["signal"].tags) | set(f["reveal"].tags) | set(f["approach"].tags)
    if "kindness" not in tags:
        tags.add("kindness")
    if f["approach"].narrates:
        tags.add("narrate")
    tags.add("humor")
    tags.add("surprise")
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
        if ent.traits:
            bits.append(f"traits={ent.traits}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.tags:
            bits.append(f"tags={sorted(ent.tags)}")
        lines.append(f"  {ent.id:8} ({ent.type:9}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        mission="rocket",
        signal="clank",
        reveal="robot",
        approach="narrate_hatch",
        narrator_name="Lily",
        narrator_gender="girl",
        pilot_name="Tom",
        pilot_gender="boy",
        parent="mother",
        narrator_trait="gentle",
        pilot_trait="curious",
    ),
    StoryParams(
        mission="moon_base",
        signal="squeak",
        reveal="moon_mouse",
        approach="narrate_lantern",
        narrator_name="Max",
        narrator_gender="boy",
        pilot_name="Mia",
        pilot_gender="girl",
        parent="father",
        narrator_trait="thoughtful",
        pilot_trait="careful",
    ),
    StoryParams(
        mission="star_bus",
        signal="shadow",
        reveal="star_blob",
        approach="narrate_lantern",
        narrator_name="Nora",
        narrator_gender="girl",
        pilot_name="Ben",
        pilot_gender="boy",
        parent="mother",
        narrator_trait="brave",
        pilot_trait="gentle",
    ),
    StoryParams(
        mission="moon_base",
        signal="squeak",
        reveal="moon_mouse",
        approach="share_snack",
        narrator_name="Ella",
        narrator_gender="girl",
        pilot_name="Leo",
        pilot_gender="boy",
        parent="father",
        narrator_trait="gentle",
        pilot_trait="curious",
    ),
    StoryParams(
        mission="rocket",
        signal="shadow",
        reveal="star_blob",
        approach="tease",
        narrator_name="Sam",
        narrator_gender="boy",
        pilot_name="Ava",
        pilot_gender="girl",
        parent="mother",
        narrator_trait="cheerful",
        pilot_trait="careful",
    ),
]


def explain_rejection(signal: Signal, reveal: Reveal, approach: Approach) -> str:
    if not reveal_fits_signal(signal, reveal):
        return (
            f"(No story: {signal.label} does not sensibly lead to {reveal.label}. "
            f"This world only allows reveals that match the clue the children heard or saw.)"
        )
    if approach.kindness < KIND_MIN:
        return (
            f"(No story: approach '{approach.id}' is too unkind for this world "
            f"(kindness={approach.kindness} < {KIND_MIN}). This domain prefers calm, kind help.)"
        )
    if signal.needs_hatch and not approach.helps_hatch:
        return (
            f"(No story: {signal.label} is trapped behind a hatch, so the chosen approach "
            f"must open it gently to learn the truth.)"
        )
    if signal.needs_light and not (approach.helps_dark or 'light' in reveal.kind_tags):
        return (
            f"(No story: {signal.label} happens in the dark, so the children need a gentle "
            f"way to see clearly before the surprise can be revealed.)"
        )
    if reveal.id == "moon_mouse" and "snack" not in approach.tags and not approach.helps_dark:
        return (
            "(No story: the moon mouse either needs a soft light to be spotted or a shared snack to coax it out.)"
        )
    return "(No story: this combination is not reasonable in this world.)"


ASP_RULES = r"""
valid_reveal(S, R) :- signal(S), reveal(R), match(S, R), sound_kind(R, S).

kind_enough(A) :- approach(A), kindness(A, K), kind_min(M), K >= M.

approach_works(S, R, A) :-
    valid_reveal(S, R), kind_enough(A),
    not needs_light(S).

approach_works(S, R, A) :-
    valid_reveal(S, R), kind_enough(A),
    needs_light(S), helps_dark(A).

approach_works(S, R, A) :-
    valid_reveal(S, R), kind_enough(A),
    needs_light(S), reveal_has_light(R).

:- approach_works(S, R, A), needs_hatch(S), not helps_hatch(A).

:- approach_works(S, moon_mouse, A), not offers_snack(A), not helps_dark(A).

valid(M, S, R, A) :- mission(M), approach_works(S, R, A).

kind_outcome :- chosen_signal(S), chosen_reveal(R), chosen_approach(A), approach_works(S, R, A).
lonely_outcome :- chosen_approach(A), approach(A), not kind_outcome.
outcome(kind) :- kind_outcome.
outcome(lonely) :- lonely_outcome.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for mission_id in MISSIONS:
        lines.append(asp.fact("mission", mission_id))
    for signal_id, signal in SIGNALS.items():
        lines.append(asp.fact("signal", signal_id))
        if signal.needs_light:
            lines.append(asp.fact("needs_light", signal_id))
        if signal.needs_hatch:
            lines.append(asp.fact("needs_hatch", signal_id))
        for reveal_id in sorted(signal.matches):
            lines.append(asp.fact("match", signal_id, reveal_id))
    for reveal_id, reveal in REVEALS.items():
        lines.append(asp.fact("reveal", reveal_id))
        lines.append(asp.fact("sound_kind", reveal_id, reveal.sound_kind))
        if "light" in reveal.kind_tags:
            lines.append(asp.fact("reveal_has_light", reveal_id))
    for approach_id, approach in APPROACHES.items():
        lines.append(asp.fact("approach", approach_id))
        lines.append(asp.fact("kindness", approach_id, approach.kindness))
        if approach.helps_dark:
            lines.append(asp.fact("helps_dark", approach_id))
        if approach.helps_hatch:
            lines.append(asp.fact("helps_hatch", approach_id))
        if "snack" in approach.tags:
            lines.append(asp.fact("offers_snack", approach_id))
    lines.append(asp.fact("kind_min", KIND_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen_signal", params.signal),
            asp.fact("chosen_reveal", params.reveal),
            asp.fact("chosen_approach", params.approach),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def outcome_of(params: StoryParams) -> str:
    signal = SIGNALS[params.signal]
    reveal = REVEALS[params.reveal]
    approach = APPROACHES[params.approach]
    return "kind" if approach_works(signal, reveal, approach) else "lonely"


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
    for seed in range(50):
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
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("smoke test produced empty story")
        print("OK: smoke test generated a normal story.")
    except Exception as err:  # pragma: no cover - verify path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a fright in a pretend space mission, then kindness, surprise, and humor."
    )
    ap.add_argument("--mission", choices=MISSIONS)
    ap.add_argument("--signal", choices=SIGNALS)
    ap.add_argument("--reveal", choices=REVEALS)
    ap.add_argument("--approach", choices=APPROACHES)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner matches the Python logic")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [name for name in pool if name != avoid]
    return rng.choice(choices), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.signal and args.reveal and args.approach:
        signal = SIGNALS[args.signal]
        reveal = REVEALS[args.reveal]
        approach = APPROACHES[args.approach]
        if not (reveal_fits_signal(signal, reveal) and approach_works(signal, reveal, approach)):
            raise StoryError(explain_rejection(signal, reveal, approach))

    combos = [
        combo
        for combo in valid_combos()
        if (args.mission is None or combo[0] == args.mission)
        and (args.signal is None or combo[1] == args.signal)
        and (args.reveal is None or combo[2] == args.reveal)
        and (args.approach is None or combo[3] == args.approach)
    ]

    if not combos and args.approach == "tease":
        mission = args.mission or rng.choice(sorted(MISSIONS))
        signal = args.signal or rng.choice(sorted(SIGNALS))
        reveal = args.reveal or next(iter(sorted(SIGNALS[signal].matches)))
        narrator_name, narrator_gender = _pick_name(rng)
        pilot_name, pilot_gender = _pick_name(rng, avoid=narrator_name)
        return StoryParams(
            mission=mission,
            signal=signal,
            reveal=reveal,
            approach="tease",
            narrator_name=narrator_name,
            narrator_gender=narrator_gender,
            pilot_name=pilot_name,
            pilot_gender=pilot_gender,
            parent=args.parent or rng.choice(["mother", "father"]),
            narrator_trait=rng.choice(TRAITS),
            pilot_trait=rng.choice(TRAITS),
        )

    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    mission_id, signal_id, reveal_id, approach_id = rng.choice(sorted(combos))
    narrator_name, narrator_gender = _pick_name(rng)
    pilot_name, pilot_gender = _pick_name(rng, avoid=narrator_name)
    return StoryParams(
        mission=mission_id,
        signal=signal_id,
        reveal=reveal_id,
        approach=approach_id,
        narrator_name=narrator_name,
        narrator_gender=narrator_gender,
        pilot_name=pilot_name,
        pilot_gender=pilot_gender,
        parent=args.parent or rng.choice(["mother", "father"]),
        narrator_trait=rng.choice(TRAITS),
        pilot_trait=rng.choice(TRAITS),
    )


def generate(params: StoryParams) -> StorySample:
    if params.mission not in MISSIONS:
        raise StoryError(f"(Unknown mission '{params.mission}')")
    if params.signal not in SIGNALS:
        raise StoryError(f"(Unknown signal '{params.signal}')")
    if params.reveal not in REVEALS:
        raise StoryError(f"(Unknown reveal '{params.reveal}')")
    if params.approach not in APPROACHES:
        raise StoryError(f"(Unknown approach '{params.approach}')")

    mission = MISSIONS[params.mission]
    signal = SIGNALS[params.signal]
    reveal = REVEALS[params.reveal]
    approach = APPROACHES[params.approach]

    if approach.id != "tease" and not (reveal_fits_signal(signal, reveal) and approach_works(signal, reveal, approach)):
        raise StoryError(explain_rejection(signal, reveal, approach))

    world = tell(
        mission=mission,
        signal=signal,
        reveal=reveal,
        approach=approach,
        narrator_name=params.narrator_name,
        narrator_gender=params.narrator_gender,
        pilot_name=params.pilot_name,
        pilot_gender=params.pilot_gender,
        parent_type=params.parent,
        narrator_trait=params.narrator_trait,
        pilot_trait=params.pilot_trait,
    )

    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_questions(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_questions(world)],
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
        print(f"{len(combos)} compatible (mission, signal, reveal, approach) combos:\n")
        for mission_id, signal_id, reveal_id, approach_id in combos:
            print(f"  {mission_id:10} {signal_id:8} {reveal_id:10} {approach_id}")
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
            header = f"### {p.narrator_name} & {p.pilot_name}: {p.signal} -> {p.reveal} ({p.mission}, {p.approach}, {outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
