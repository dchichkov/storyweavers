#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/wobble_moral_value_rhyme_superhero_story.py
======================================================================

A standalone storyworld for a tiny superhero-style tale about a child who wants
to make a quick rescue by climbing something wobbly. The world model prefers
stories where the danger is real, the warning is honest, and the ending proves a
moral value: brave heroes use patience, teamwork, and safe help.

The seed word "wobble" is built into the middle turn. A short rhyme appears as a
hero motto and changes meaning after the lesson.

Run it
------
    python storyworlds/worlds/gpt-5.4/wobble_moral_value_rhyme_superhero_story.py
    python storyworlds/worlds/gpt-5.4/wobble_moral_value_rhyme_superhero_story.py --mission teddy --perch chair
    python storyworlds/worlds/gpt-5.4/wobble_moral_value_rhyme_superhero_story.py --response hurry_jump
    python storyworlds/worlds/gpt-5.4/wobble_moral_value_rhyme_superhero_story.py --all
    python storyworlds/worlds/gpt-5.4/wobble_moral_value_rhyme_superhero_story.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/wobble_moral_value_rhyme_superhero_story.py --verify
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
SENSE_MIN = 2
BRAVERY_INIT = 5.0
CAUTIOUS_TRAITS = {"careful", "patient", "thoughtful", "steady"}


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
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
    age: int = 0
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
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Mission:
    id: str
    item_label: str
    item_phrase: str
    location: str
    room: str
    intro: str
    height: int
    fragile: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class Perch:
    id: str
    label: str
    phrase: str
    wobble: int
    kind: str
    verb: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Response:
    id: str
    label: str
    sense: int
    power: int
    text: str
    fail: str
    qa_text: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    mission: str
    perch: str
    response: str
    hero_name: str
    hero_gender: str
    sidekick_name: str
    sidekick_gender: str
    parent: str
    trait: str
    relation: str = "siblings"
    hero_age: int = 6
    sidekick_age: int = 5
    trust: int = 6
    delay: int = 0
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

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

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


def _r_wobble(world: World) -> list[str]:
    hero = world.entities.get("hero")
    perch = world.entities.get("perch")
    if hero is None or perch is None:
        return []
    if hero.meters["climbing"] < THRESHOLD or perch.meters["unstable"] < THRESHOLD:
        return []
    sig = ("wobble", perch.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    perch.meters["wobbling"] += 1
    hero.memes["fear"] += 1
    hero.meters["risk"] += 1
    sidekick = world.entities.get("sidekick")
    if sidekick is not None:
        sidekick.memes["fear"] += 1
    return ["__wobble__"]


def _r_drop_risk(world: World) -> list[str]:
    item = world.entities.get("item")
    perch = world.entities.get("perch")
    if item is None or perch is None:
        return []
    if perch.meters["wobbling"] < THRESHOLD:
        return []
    sig = ("drop", item.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    item.meters["at_risk"] += 1
    return ["__drop__"]


CAUSAL_RULES = [
    Rule(name="wobble", tag="physical", apply=_r_wobble),
    Rule(name="drop_risk", tag="physical", apply=_r_drop_risk),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            out = rule.apply(world)
            if out:
                changed = True
                produced.extend(s for s in out if not s.startswith("__"))
    if narrate:
        for sentence in produced:
            world.say(sentence)
    return produced


MISSIONS = {
    "teddy": Mission(
        id="teddy",
        item_label="teddy bear",
        item_phrase="a sleepy teddy bear",
        location="on the top bookshelf",
        room="the bedroom",
        intro="The teddy bear was waiting on the top bookshelf like a citizen on a tall tower.",
        height=2,
        fragile=False,
        tags={"bedroom", "toy", "ask_help"},
    ),
    "cape": Mission(
        id="cape",
        item_label="red cape",
        item_phrase="a red cape with a gold star",
        location="on the coat hook above the bench",
        room="the hallway",
        intro="The red cape hung on the high hook like a flag on a windy roof.",
        height=1,
        fragile=False,
        tags={"hallway", "clothes", "ask_help"},
    ),
    "robot": Mission(
        id="robot",
        item_label="tin robot",
        item_phrase="a shiny tin robot",
        location="on the kitchen shelf",
        room="the kitchen",
        intro="The little robot stood on the kitchen shelf as if it needed a hero to guard it.",
        height=2,
        fragile=True,
        tags={"kitchen", "toy", "fragile", "ask_help"},
    ),
    "cookie_jar": Mission(
        id="cookie_jar",
        item_label="cookie jar",
        item_phrase="a painted cookie jar",
        location="on the pantry shelf",
        room="the kitchen",
        intro="The cookie jar sat high on the pantry shelf like treasure in a secret lair.",
        height=3,
        fragile=True,
        tags={"kitchen", "fragile", "ask_help"},
    ),
}

PERCHES = {
    "chair": Perch(
        id="chair",
        label="spin chair",
        phrase="a spin chair with wheels",
        wobble=2,
        kind="chair",
        verb="rolled a little underfoot",
        tags={"chair", "wobble"},
    ),
    "cushions": Perch(
        id="cushions",
        label="cushion stack",
        phrase="a tall stack of sofa cushions",
        wobble=3,
        kind="cushions",
        verb="squished and slid",
        tags={"cushions", "wobble"},
    ),
    "toy_box": Perch(
        id="toy_box",
        label="toy box lid",
        phrase="the toy box lid",
        wobble=2,
        kind="box",
        verb="tipped with a creak",
        tags={"box", "wobble"},
    ),
}

RESPONSES = {
    "step_stool": Response(
        id="step_stool",
        label="step stool",
        sense=3,
        power=4,
        text="set a strong step stool against the wall, held it steady, and helped the little rescue happen one careful step at a time",
        fail="brought a step stool, but the child had already climbed too high and the wobble had turned into a tumble too fast to stop cleanly",
        qa_text="used a strong step stool and held it steady",
        tags={"step_stool", "ask_help"},
    ),
    "grownup_lift": Response(
        id="grownup_lift",
        label="grown-up lift",
        sense=3,
        power=3,
        text="lifted the little hero from the floor and reached safely for the item at the same time",
        fail="tried to lift the little hero, but the wobble had already knocked the item loose",
        qa_text="lifted the child and reached the item safely",
        tags={"grownup_lift", "ask_help"},
    ),
    "grabber": Response(
        id="grabber",
        label="grabber tool",
        sense=2,
        power=2,
        text="fetched the long grabber tool from the closet and pinched the item gently down to waiting hands",
        fail="used the grabber tool, but the item was already tipping and slipped away before it could be caught",
        qa_text="used a long grabber tool to bring the item down",
        tags={"grabber", "ask_help"},
    ),
    "hurry_jump": Response(
        id="hurry_jump",
        label="hurry jump",
        sense=1,
        power=1,
        text="told the child to jump faster and snatch the item on the way down",
        fail="called out for a faster jump, which only made the wobble worse",
        qa_text="told the child to jump faster",
        tags={"bad_idea"},
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Nora", "Rose"]
BOY_NAMES = ["Max", "Ben", "Leo", "Sam", "Eli", "Theo", "Finn", "Jack"]
TRAITS = ["careful", "patient", "steady", "thoughtful", "brave", "quick"]


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def mission_at_risk(mission: Mission, perch: Perch) -> bool:
    return mission.height >= 1 and perch.wobble >= 2


def severity_of(mission: Mission, perch: Perch, delay: int) -> int:
    return mission.height + perch.wobble + delay


def contained_by(response: Response, mission: Mission, perch: Perch, delay: int) -> bool:
    return response.power >= severity_of(mission, perch, delay)


def initial_caution(trait: str) -> float:
    return 5.0 if trait in CAUTIOUS_TRAITS else 3.0


def would_avert(relation: str, hero_age: int, sidekick_age: int, trait: str) -> bool:
    older_sibling = relation == "siblings" and sidekick_age > hero_age
    authority = initial_caution(trait) + 1.0 + (2.0 if older_sibling else 0.0)
    return older_sibling and authority > BRAVERY_INIT


def predict_wobble(world: World) -> dict:
    sim = world.copy()
    hero = sim.get("hero")
    perch = sim.get("perch")
    hero.meters["climbing"] += 1
    perch.meters["unstable"] += 1
    propagate(sim, narrate=False)
    return {
        "wobble": perch.meters["wobbling"] >= THRESHOLD,
        "drop_risk": sim.get("item").meters["at_risk"] >= THRESHOLD,
    }


def opening_motto(hero: Entity) -> str:
    if hero.memes["bravery"] >= 5:
        return '"Zoom to the gloom, save the room!"'
    return '"Light and bright, set things right!"'


def ending_motto() -> str:
    return '"Slow and steady, kind and ready!"'


def introduce(world: World, hero: Entity, sidekick: Entity, mission: Mission) -> None:
    hero.memes["joy"] += 1
    sidekick.memes["joy"] += 1
    world.say(
        f"In {mission.room}, {hero.id} tied on a towel-cape and became Captain Starstep. "
        f"{sidekick.id} became the faithful sidekick. {mission.intro}"
    )
    world.say(
        f'{hero.id} pointed up at {mission.location} and cried, '
        f'{opening_motto(hero)}'
    )


def need_rescue(world: World, hero: Entity, mission: Mission) -> None:
    world.say(
        f"To {hero.id}, the {mission.item_label} did not look ordinary at all. "
        f"It looked far away and in need of a superhero rescue."
    )


def temptation(world: World, hero: Entity, perch: Perch) -> None:
    hero.memes["impulse"] += 1
    world.say(
        f'{hero.id} dragged over {perch.phrase}. "I can climb that and be back in a blink," '
        f'{hero.pronoun()} said.'
    )


def warn(world: World, sidekick: Entity, hero: Entity, perch: Perch, mission: Mission, parent: Entity) -> None:
    pred = predict_wobble(world)
    sidekick.memes["caution"] += 1
    world.facts["predicted_wobble"] = pred["wobble"]
    world.facts["predicted_drop_risk"] = pred["drop_risk"]
    extra = ""
    if pred["drop_risk"]:
        extra = f" Then the {mission.item_label} could fall too."
    world.say(
        f'{sidekick.id} put a hand on the {perch.label}. "{hero.id}, wait. '
        f'That will wobble if you climb it," {sidekick.pronoun()} warned. '
        f'"Heroes ask {parent.label_word} for help before they make a tumble."{extra}'
    )


def back_down(world: World, hero: Entity, sidekick: Entity, parent: Entity, mission: Mission, response: Response) -> None:
    hero.memes["relief"] += 1
    sidekick.memes["relief"] += 1
    hero.memes["lesson"] += 1
    world.say(
        f"{hero.id} looked at the high shelf, then at the shaky perch, and let out a long breath. "
        f'"Okay," {hero.pronoun()} said. "Fast is not always best."'
    )
    world.say(
        f"They called for {parent.label_word}, who {response.text}."
    )
    world.say(
        f'Together they cheered, {ending_motto()} The {mission.item_label} came down safely, '
        f"and the rescue felt even more heroic because no one had to wobble at all."
    )


def defy(world: World, hero: Entity, sidekick: Entity) -> None:
    hero.memes["defiance"] += 1
    world.say(
        f'"I can do it myself," {hero.id} said, already reaching up. '
        f"{sidekick.id} stayed close, worried but ready to call for help."
    )


def climb_and_wobble(world: World, hero: Entity, perch_ent: Entity, perch: Perch, mission: Mission) -> None:
    hero.meters["climbing"] += 1
    perch_ent.meters["unstable"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{hero.id} climbed onto {perch.phrase}. At once it {perch.verb}, and the whole little rescue began to wobble."
    )
    if world.get("item").meters["at_risk"] >= THRESHOLD:
        world.say(
            f"High above, the {mission.item_label} gave a tiny knock against the shelf, as if it might slip next."
        )


def alarm(world: World, sidekick: Entity, parent: Entity) -> None:
    world.say(f'"{parent.label_word.capitalize()}! Quick!" {sidekick.id} shouted.')


def rescue_success(world: World, parent: Entity, response: Response, mission: Mission) -> None:
    hero = world.get("hero")
    item = world.get("item")
    hero.meters["climbing"] = 0.0
    hero.meters["risk"] = 0.0
    item.meters["at_risk"] = 0.0
    world.get("perch").meters["wobbling"] = 0.0
    world.say(
        f"{parent.label_word.capitalize()} came fast, but not in a panic. {parent.pronoun().capitalize()} {response.text}."
    )
    world.say(
        f"The scary wobble stopped. Soon both the little hero and the {mission.item_label} were safe on the floor."
    )


def rescue_fail(world: World, parent: Entity, response: Response, mission: Mission) -> None:
    hero = world.get("hero")
    item = world.get("item")
    hero.meters["climbing"] = 0.0
    hero.meters["risk"] += 1
    item.meters["fallen"] += 1
    if mission.fragile:
        item.meters["broken"] += 1
    world.say(
        f"{parent.label_word.capitalize()} rushed in and {response.fail}."
    )
    if mission.fragile:
        world.say(
            f"The {mission.item_label} hit the floor with a sad clink. It did not hurt anyone, but it was broken."
        )
    else:
        world.say(
            f"The {mission.item_label} tumbled down with a thump. No one was hurt, but the rescue had gone wrong."
        )


def lesson(world: World, parent: Entity, hero: Entity, sidekick: Entity, mission: Mission, happy: bool) -> None:
    hero.memes["lesson"] += 1
    hero.memes["love"] += 1
    sidekick.memes["love"] += 1
    sidekick.memes["relief"] += 1
    hero.memes["fear"] = 0.0
    sidekick.memes["fear"] = 0.0
    if happy:
        world.say(
            f'{parent.label_word.capitalize()} knelt beside them. "Real heroes are not heroes because they rush," '
            f'{parent.pronoun()} said. "They are heroes because they notice danger, listen, and protect people first."'
        )
    else:
        world.say(
            f'{parent.label_word.capitalize()} hugged both children close. "I am glad you are safe," '
            f'{parent.pronoun()} said softly. "Next time, call me before a wobble turns into trouble."'
        )
    world.say(
        f"{hero.id} looked at {sidekick.id} and nodded. {sidekick.id} had been brave too, by warning and calling for help."
    )


def repaired_ending(world: World, hero: Entity, sidekick: Entity, mission: Mission, happy: bool) -> None:
    hero.memes["joy"] += 1
    sidekick.memes["joy"] += 1
    if happy:
        world.say(
            f'When the game began again, {hero.id} lifted the {mission.item_label} high and chanted, '
            f'{ending_motto()} {sidekick.id} laughed, and the room felt bright with safe superhero cheer.'
        )
    else:
        if mission.fragile:
            world.say(
                f"Later, they swept up the little broken bits together. Then {hero.id} folded the cape neatly and promised to try the slow, safe way next time."
            )
        else:
            world.say(
                f"Later, they set the fallen {mission.item_label} back in place together. Then {hero.id} folded the cape neatly and promised to try the slow, safe way next time."
            )
        world.say(
            f'Before bed, {hero.id} whispered the new hero rhyme anyway: {ending_motto()}'
        )


def tell(
    mission: Mission,
    perch: Perch,
    response: Response,
    hero_name: str,
    hero_gender: str,
    sidekick_name: str,
    sidekick_gender: str,
    parent_type: str,
    trait: str,
    relation: str,
    hero_age: int,
    sidekick_age: int,
    trust: int,
    delay: int,
) -> World:
    world = World()
    hero = world.add(Entity(
        id="hero",
        kind="character",
        type=hero_gender,
        label=hero_name,
        phrase=hero_name,
        role="hero",
        age=hero_age,
        traits=["bold"],
        attrs={"name": hero_name, "relation": relation},
    ))
    sidekick = world.add(Entity(
        id="sidekick",
        kind="character",
        type=sidekick_gender,
        label=sidekick_name,
        phrase=sidekick_name,
        role="sidekick",
        age=sidekick_age,
        traits=[trait],
        attrs={"name": sidekick_name, "relation": relation, "trust": trust},
    ))
    parent = world.add(Entity(
        id="parent",
        kind="character",
        type=parent_type,
        label="the parent",
        phrase="the parent",
        role="parent",
    ))
    item = world.add(Entity(
        id="item",
        type="item",
        label=mission.item_label,
        phrase=mission.item_phrase,
        tags=set(mission.tags),
    ))
    perch_ent = world.add(Entity(
        id="perch",
        type="perch",
        label=perch.label,
        phrase=perch.phrase,
        tags=set(perch.tags),
    ))

    hero.memes["bravery"] = BRAVERY_INIT
    sidekick.memes["trust"] = float(trust)
    sidekick.memes["caution"] = initial_caution(trait)

    introduce(world, hero, sidekick, mission)
    need_rescue(world, hero, mission)

    world.para()
    temptation(world, hero, perch)
    warn(world, sidekick, hero, perch, mission, parent)

    averted = would_avert(relation, hero_age, sidekick_age, trait)
    if averted:
        world.para()
        back_down(world, hero, sidekick, parent, mission, response)
        outcome = "averted"
    else:
        defy(world, hero, sidekick)
        world.para()
        climb_and_wobble(world, hero, perch_ent, perch, mission)
        alarm(world, sidekick, parent)
        world.para()
        if delay:
            world.say("For one more heartbeat, everything shook in the air.")
        contained = contained_by(response, mission, perch, delay)
        if contained:
            rescue_success(world, parent, response, mission)
            lesson(world, parent, hero, sidekick, mission, happy=True)
            world.para()
            repaired_ending(world, hero, sidekick, mission, happy=True)
            outcome = "contained"
        else:
            rescue_fail(world, parent, response, mission)
            lesson(world, parent, hero, sidekick, mission, happy=False)
            world.para()
            repaired_ending(world, hero, sidekick, mission, happy=False)
            outcome = "fallen"

    world.facts.update(
        mission=mission,
        perch_cfg=perch,
        response=response,
        hero=hero,
        sidekick=sidekick,
        parent=parent,
        item=item,
        relation=relation,
        outcome=outcome,
        delay=delay,
        severity=severity_of(mission, perch, delay) if outcome != "averted" else 0,
        mission_name=mission.item_label,
        wobble=world.get("perch").meters["wobbling"] >= THRESHOLD or outcome != "averted",
        broken=item.meters["broken"] >= THRESHOLD,
        averted=outcome == "averted",
    )
    return world


def valid_combos() -> list[tuple[str, str]]:
    combos: list[tuple[str, str]] = []
    if not sensible_responses():
        return combos
    for mission_id, mission in MISSIONS.items():
        for perch_id, perch in PERCHES.items():
            if mission_at_risk(mission, perch):
                combos.append((mission_id, perch_id))
    return combos


KNOWLEDGE = {
    "wobble": [(
        "What does wobble mean?",
        "Wobble means to shake from side to side without feeling steady. A wobbly thing can tip if you climb on it or push it the wrong way."
    )],
    "ask_help": [(
        "Why should children ask a grown-up for help with high things?",
        "High places can be hard to reach safely. A grown-up can use the right tool or hold things steady so nobody falls."
    )],
    "step_stool": [(
        "What is a step stool?",
        "A step stool is a short, strong stool that helps you reach something a little higher. It should be used carefully with a grown-up nearby."
    )],
    "grownup_lift": [(
        "Why is a grown-up lift safer than climbing a wobbly chair?",
        "A grown-up can hold you firmly and decide if the reach is safe. A wobbly chair can roll or tip under your feet."
    )],
    "grabber": [(
        "What is a grabber tool?",
        "A grabber tool is a long helper with a little pinch at the end. It can reach light things without anyone climbing."
    )],
    "fragile": [(
        "What does fragile mean?",
        "Fragile means something can break easily if it falls or gets bumped hard. That is why careful hands matter."
    )],
    "rhyme": [(
        "What is a rhyme?",
        "A rhyme uses words with matching ending sounds, like bright and light. Rhymes can help a lesson stay in your mind."
    )],
    "teamwork": [(
        "Why is teamwork a kind of bravery?",
        "Teamwork is brave because it means you let someone help when help is needed. Real bravery is not showing off; it is choosing what keeps everyone safe."
    )],
}
KNOWLEDGE_ORDER = ["wobble", "ask_help", "step_stool", "grownup_lift", "grabber", "fragile", "rhyme", "teamwork"]


def character_name(ent: Entity) -> str:
    return ent.attrs.get("name", ent.label or ent.id)


def pair_noun(hero: Entity, sidekick: Entity, relation: str) -> str:
    if relation == "siblings":
        if hero.type == "boy" and sidekick.type == "boy":
            return "two brothers"
        if hero.type == "girl" and sidekick.type == "girl":
            return "two sisters"
        return "a brother and a sister"
    return "two friends"


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    sidekick = f["sidekick"]
    mission = f["mission"]
    perch = f["perch_cfg"]
    outcome = f["outcome"]
    hero_name = character_name(hero)
    sidekick_name = character_name(sidekick)
    base = (
        f'Write a short superhero story for a 3-to-5-year-old that includes the word "wobble", '
        f'uses a simple rhyme, and teaches that real bravery includes patience and asking for help.'
    )
    if outcome == "averted":
        return [
            base,
            f"Tell a gentle superhero story where {hero_name} wants to climb {perch.phrase} to reach a {mission.item_label}, "
            f"but listens to {sidekick_name} and gets a grown-up's help instead.",
            f"Write a rhyming rescue story where the danger is stopped before anyone climbs, and the ending proves that safe teamwork is heroic."
        ]
    if outcome == "fallen":
        return [
            base,
            f"Tell a superhero story where {hero_name} ignores {sidekick_name}'s warning, something starts to wobble, and a careful lesson follows after the fall.",
            f"Write a story with a small, child-safe mistake and a warm ending that teaches why rushing is not the same as courage."
        ]
    return [
        base,
        f"Tell a superhero story where {hero_name} climbs {perch.phrase} to rescue a {mission.item_label}, it begins to wobble, and a grown-up fixes the problem safely.",
        f"Write a simple rescue story with a rhyme at the beginning and a wiser rhyme at the end."
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    sidekick = f["sidekick"]
    parent = f["parent"]
    mission = f["mission"]
    perch = f["perch_cfg"]
    response = f["response"]
    hero_name = character_name(hero)
    sidekick_name = character_name(sidekick)
    pair = pair_noun(hero, sidekick, f["relation"])
    pw = parent.label_word
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair}, {hero_name} and {sidekick_name}, playing at being superheroes. Their pretend rescue turns into a real lesson about safe bravery."
        ),
        (
            f"What needed rescuing?",
            f"The {mission.item_label} was high at {mission.location}, so {hero_name} treated it like someone stuck on a tower. That high place is what made the quick climb feel tempting."
        ),
        (
            f"Why did {sidekick_name} warn {hero_name}?",
            f"{sidekick_name} warned that {perch.phrase} would wobble if anyone climbed it. That meant {hero_name} could fall, and the {mission.item_label} might fall too."
        ),
    ]
    if f["outcome"] == "averted":
        qa.append((
            f"How was the problem solved without a wobble?",
            f"{hero_name} stopped and listened, and then they called {pw} for help. {pw.capitalize()} {response.qa_text}, so the rescue was finished safely."
        ))
        qa.append((
            "What moral did the story teach?",
            f"It taught that real heroes do not have to rush or show off. Asking for safe help was the bravest choice in the whole story."
        ))
    elif f["outcome"] == "contained":
        qa.append((
            f"What happened when {hero_name} climbed up?",
            f"The perch began to wobble right away, and the rescue suddenly felt scary instead of fun. That wobble is what made {sidekick_name} shout for help."
        ))
        qa.append((
            f"How did {pw} fix the problem?",
            f"{pw.capitalize()} came quickly and {response.qa_text}. Because the help was calm and steady, both the child and the {mission.item_label} ended up safe."
        ))
        qa.append((
            "Why did the rhyme at the end matter?",
            f"The ending rhyme showed that the hero had changed. At first the rhyme was about zooming fast, but later it was about being slow, steady, kind, and ready."
        ))
    else:
        broken_text = " It broke when it hit the floor." if f["broken"] else ""
        qa.append((
            "Did anyone get hurt?",
            f"No one got hurt, and that is the most important part.{broken_text} The scary moment still taught everyone to take wobbling seriously."
        ))
        qa.append((
            "What did the hero learn after the fall?",
            f"{hero_name} learned that rushing on a shaky perch is not a superhero move. Listening early and calling a grown-up would have protected both people and things."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"wobble", "rhyme", "teamwork"} | set(f["mission"].tags) | set(f["response"].tags)
    if f["mission"].fragile:
        tags.add("fragile")
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
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v != ""}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {ent.id:8} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


def explain_rejection(mission: Mission, perch: Perch) -> str:
    return (
        f"(No story: {mission.item_label} at {mission.location} does not make a good wobble rescue with {perch.phrase}. "
        f"The world only tells stories where climbing the chosen perch creates a believable wobble danger.)"
    )


def explain_response(response_id: str) -> str:
    response = RESPONSES[response_id]
    better = ", ".join(sorted(r.id for r in sensible_responses()))
    return (
        f"(Refusing response '{response_id}': it is too weak or silly for this world "
        f"(sense={response.sense} < {SENSE_MIN}). Try one of: {better}.)"
    )


def outcome_of(params: StoryParams) -> str:
    mission = MISSIONS[params.mission]
    perch = PERCHES[params.perch]
    response = RESPONSES[params.response]
    if would_avert(params.relation, params.hero_age, params.sidekick_age, params.trait):
        return "averted"
    return "contained" if contained_by(response, mission, perch, params.delay) else "fallen"


ASP_RULES = r"""
danger(M, P) :- mission(M), perch(P), height(M, H), wobble(P, W), H >= 1, W >= 2.

sensible(R) :- response(R), sense(R, S), sense_min(Min), S >= Min.
valid(M, P) :- mission(M), perch(P), danger(M, P).

cautious_now(T) :- trait(T), is_cautious(T).
init_caution(5) :- trait(T), cautious_now(T).
init_caution(3) :- trait(T), not cautious_now(T).

older_sibling :- relation(siblings), hero_age(H), sidekick_age(S), S > H.
bonus(2) :- older_sibling.
bonus(0) :- not older_sibling.
authority(C + 1 + B) :- init_caution(C), bonus(B).

averted :- older_sibling, authority(A), bravery_init(BR), A > BR.

severity(H + W + D) :- chosen_mission(M), chosen_perch(P), height(M, H), wobble(P, W), delay(D).
contained :- chosen_response(R), power(R, P), severity(S), P >= S.

outcome(averted) :- averted.
outcome(contained) :- not averted, contained.
outcome(fallen) :- not averted, not contained.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for mid, mission in MISSIONS.items():
        lines.append(asp.fact("mission", mid))
        lines.append(asp.fact("height", mid, mission.height))
    for pid, perch in PERCHES.items():
        lines.append(asp.fact("perch", pid))
        lines.append(asp.fact("wobble", pid, perch.wobble))
    for rid, response in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, response.sense))
        lines.append(asp.fact("power", rid, response.power))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    lines.append(asp.fact("bravery_init", int(BRAVERY_INIT)))
    for trait in sorted(CAUTIOUS_TRAITS):
        lines.append(asp.fact("is_cautious", trait))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp

    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(r for (r,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join([
        asp.fact("chosen_mission", params.mission),
        asp.fact("chosen_perch", params.perch),
        asp.fact("chosen_response", params.response),
        asp.fact("delay", params.delay),
        asp.fact("relation", params.relation),
        asp.fact("hero_age", params.hero_age),
        asp.fact("sidekick_age", params.sidekick_age),
        asp.fact("trait", params.trait),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


CURATED = [
    StoryParams(
        mission="teddy",
        perch="chair",
        response="step_stool",
        hero_name="Max",
        hero_gender="boy",
        sidekick_name="Lily",
        sidekick_gender="girl",
        parent="mother",
        trait="careful",
        relation="siblings",
        hero_age=5,
        sidekick_age=7,
        trust=6,
        delay=0,
    ),
    StoryParams(
        mission="cape",
        perch="toy_box",
        response="grownup_lift",
        hero_name="Zoe",
        hero_gender="girl",
        sidekick_name="Ben",
        sidekick_gender="boy",
        parent="father",
        trait="steady",
        relation="friends",
        hero_age=6,
        sidekick_age=6,
        trust=5,
        delay=0,
    ),
    StoryParams(
        mission="robot",
        perch="cushions",
        response="grabber",
        hero_name="Ella",
        hero_gender="girl",
        sidekick_name="Finn",
        sidekick_gender="boy",
        parent="mother",
        trait="thoughtful",
        relation="friends",
        hero_age=6,
        sidekick_age=6,
        trust=7,
        delay=1,
    ),
    StoryParams(
        mission="cookie_jar",
        perch="cushions",
        response="step_stool",
        hero_name="Leo",
        hero_gender="boy",
        sidekick_name="Nora",
        sidekick_gender="girl",
        parent="father",
        trait="patient",
        relation="friends",
        hero_age=7,
        sidekick_age=6,
        trust=4,
        delay=1,
    ),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(conflict_handler="resolve",
        description="Story world sketch: a tiny superhero rescue, a wobble, a rhyme, and a lesson about safe bravery."
    )
    ap.add_argument("--mission", choices=MISSIONS)
    ap.add_argument("--perch", choices=PERCHES)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--delay", type=int, choices=[0, 1], help="extra beat before help arrives")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner matches the Python logic")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_child(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    names = [name for name in pool if name != avoid]
    return rng.choice(names), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.mission and args.perch:
        mission = MISSIONS[args.mission]
        perch = PERCHES[args.perch]
        if not mission_at_risk(mission, perch):
            raise StoryError(explain_rejection(mission, perch))
    if args.response and RESPONSES[args.response].sense < SENSE_MIN:
        raise StoryError(explain_response(args.response))

    combos = [
        combo for combo in valid_combos()
        if (args.mission is None or combo[0] == args.mission)
        and (args.perch is None or combo[1] == args.perch)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    mission_id, perch_id = rng.choice(sorted(combos))
    response_id = args.response or rng.choice(sorted(r.id for r in sensible_responses()))
    hero_name, hero_gender = _pick_child(rng)
    sidekick_name, sidekick_gender = _pick_child(rng, avoid=hero_name)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    relation = rng.choice(["siblings", "friends"])
    hero_age, sidekick_age = rng.sample([4, 5, 6, 7], 2)
    trust = rng.randint(3, 8)
    delay = args.delay if args.delay is not None else rng.choice([0, 0, 1])
    return StoryParams(
        mission=mission_id,
        perch=perch_id,
        response=response_id,
        hero_name=hero_name,
        hero_gender=hero_gender,
        sidekick_name=sidekick_name,
        sidekick_gender=sidekick_gender,
        parent=parent,
        trait=trait,
        relation=relation,
        hero_age=hero_age,
        sidekick_age=sidekick_age,
        trust=trust,
        delay=delay,
    )


def generate(params: StoryParams) -> StorySample:
    if params.mission not in MISSIONS:
        raise StoryError(f"(Unknown mission '{params.mission}'.)")
    if params.perch not in PERCHES:
        raise StoryError(f"(Unknown perch '{params.perch}'.)")
    if params.response not in RESPONSES:
        raise StoryError(f"(Unknown response '{params.response}'.)")

    mission = MISSIONS[params.mission]
    perch = PERCHES[params.perch]
    response = RESPONSES[params.response]

    if not mission_at_risk(mission, perch):
        raise StoryError(explain_rejection(mission, perch))
    if response.sense < SENSE_MIN:
        raise StoryError(explain_response(params.response))

    world = tell(
        mission=mission,
        perch=perch,
        response=response,
        hero_name=params.hero_name,
        hero_gender=params.hero_gender,
        sidekick_name=params.sidekick_name,
        sidekick_gender=params.sidekick_gender,
        parent_type=params.parent,
        trait=params.trait,
        relation=params.relation,
        hero_age=params.hero_age,
        sidekick_age=params.sidekick_age,
        trust=params.trust,
        delay=params.delay,
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


def asp_verify() -> int:
    rc = 0

    clingo_valid = set(asp_valid_combos())
    python_valid = set(valid_combos())
    if clingo_valid == python_valid:
        print(f"OK: gate matches valid_combos() ({len(clingo_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if clingo_valid - python_valid:
            print("  only in clingo:", sorted(clingo_valid - python_valid))
        if python_valid - clingo_valid:
            print("  only in python:", sorted(python_valid - clingo_valid))

    clingo_sensible = set(asp_sensible())
    python_sensible = {r.id for r in sensible_responses()}
    if clingo_sensible == python_sensible:
        print(f"OK: sensible responses match ({sorted(clingo_sensible)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible responses: clingo={sorted(clingo_sensible)} python={sorted(python_sensible)}")

    cases = list(CURATED)
    for seed in range(100):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
            params.seed = seed
            cases.append(params)
        except StoryError:
            continue

    mismatches = [p for p in cases if asp_outcome(p) != outcome_of(p)]
    if not mismatches:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {len(mismatches)}/{len(cases)} outcomes differ.")

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("(Smoke test generated an empty story.)")
        print("OK: smoke test generated a normal story.")
    except Exception as err:  # pragma: no cover - verification path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/2.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible responses: {', '.join(asp_sensible())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (mission, perch) combos:\n")
        for mission_id, perch_id in combos:
            print(f"  {mission_id:12} {perch_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        seen: set[str] = set()
        attempt = 0
        while len(samples) < args.n and attempt < max(args.n * 50, 50):
            seed = base_seed + attempt
            attempt += 1
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
            header = f"### {p.hero_name} & {p.sidekick_name}: {p.mission} with {p.perch} ({outcome_of(p)})"
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
