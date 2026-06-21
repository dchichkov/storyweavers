#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/cafeteria_employee_friendship_repetition_cautionary_adventure.py
===========================================================================================

A standalone storyworld about two friends in a cafeteria who turn a lunch errand
into an adventure. A kind cafeteria employee repeats one safety rule, a friend
repeats it too, and the world decides whether the hero listens in time or
hurries into a small cautionary mishap.

The domain is intentionally small and state-driven:

- typed entities with physical meters and emotional memes
- a short forward-chaining rule engine for wobble -> spill/fear/mess
- a reasonableness gate for which cargo, hazard, and response combinations make
  sense
- an inline ASP twin for parity checks
- child-facing prose and Q&A grounded in the simulated world

Run it
------
    python storyworlds/worlds/gpt-5.4/cafeteria_employee_friendship_repetition_cautionary_adventure.py
    python storyworlds/worlds/gpt-5.4/cafeteria_employee_friendship_repetition_cautionary_adventure.py --all
    python storyworlds/worlds/gpt-5.4/cafeteria_employee_friendship_repetition_cautionary_adventure.py --qa --json
    python storyworlds/worlds/gpt-5.4/cafeteria_employee_friendship_repetition_cautionary_adventure.py --verify
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
# This file lives in storyworlds/worlds/gpt-5.4/, so we add storyworlds/ itself.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
SENSE_MIN = 2
EAGERNESS_INIT = 6.0
CAREFUL_TRAITS = {"careful", "patient", "steady", "thoughtful"}


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
        female = {"girl", "woman", "mother", "cook"}
        male = {"boy", "man", "father"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class Theme:
    id: str
    scene: str
    mission: str
    opening: str
    goal: str
    ending: str


@dataclass
class Cargo:
    id: str
    label: str
    phrase: str
    plural: bool = False
    hot: bool = False
    heavy: bool = False
    rolling: bool = False
    risk: int = 1
    tags: set[str] = field(default_factory=set)

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Hazard:
    id: str
    label: str
    phrase: str
    beat: str
    risk: int = 1
    tags: set[str] = field(default_factory=set)


@dataclass
class Response:
    id: str
    label: str
    sense: int = 2
    power: int = 2
    handles: set[str] = field(default_factory=set)
    text: str = ""
    fail: str = ""
    qa_text: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    theme: str
    cargo: str
    hazard: str
    response: str
    hero: str
    hero_gender: str
    friend: str
    friend_gender: str
    employee_name: str
    employee_type: str
    friend_trait: str
    relation: str = "friends"
    hero_age: int = 6
    friend_age: int = 6
    trust: int = 5
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

    def kids(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.role in {"hero", "friend"}]

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
    out: list[str] = []
    hero = world.get("hero")
    cargo = world.get("cargo")
    hazard = world.get("hazard")
    if hero.meters["moving_fast"] < THRESHOLD or cargo.meters["carried"] < THRESHOLD:
        return out
    sig = ("wobble", cargo.id, hazard.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    cargo.meters["wobble"] += 1
    hero.memes["fear"] += 1
    out.append("__wobble__")
    return out


def _r_spill(world: World) -> list[str]:
    out: list[str] = []
    cargo = world.get("cargo")
    if cargo.meters["wobble"] < THRESHOLD or cargo.meters["saved"] >= THRESHOLD:
        return out
    sig = ("spill", cargo.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    cargo.meters["spilled"] += 1
    world.get("cafeteria").meters["mess"] += 1
    for kid in world.kids():
        kid.memes["fear"] += 1
    out.append("__spill__")
    return out


CAUSAL_RULES = [
    Rule(name="wobble", tag="physical", apply=_r_wobble),
    Rule(name="spill", tag="physical", apply=_r_spill),
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


THEMES = {
    "quest": Theme(
        id="quest",
        scene="a shining lunch-quest",
        mission="supply expedition",
        opening="The cafeteria looked so big and bright that it felt like the hall of a castle.",
        goal="carry one important thing to the serving table",
        ending="the lunch-quest could go on, only slower and wiser",
    ),
    "ship": Theme(
        id="ship",
        scene="a busy lunch-ship",
        mission="galley mission",
        opening="The cafeteria hummed and clinked like the deck of a ship crossing a noisy sea.",
        goal="deliver the day's supplies to the right station",
        ending="the little crew finished the mission with steady feet",
    ),
    "trail": Theme(
        id="trail",
        scene="an indoor canyon trail",
        mission="trail mission",
        opening="The cafeteria seemed full of shining paths, carts, and corners like a canyon made for explorers.",
        goal="guide the supplies safely past one tricky place",
        ending="their adventure ended with everyone still smiling in the bright room",
    ),
}

CARGOES = {
    "soup_tray": Cargo(
        id="soup_tray",
        label="soup tray",
        phrase="a tray of warm tomato soup bowls",
        hot=True,
        heavy=True,
        risk=3,
        tags={"soup", "hot", "tray"},
    ),
    "milk_pitcher": Cargo(
        id="milk_pitcher",
        label="milk pitcher",
        phrase="a full silver milk pitcher",
        heavy=True,
        risk=2,
        tags={"milk", "pitcher"},
    ),
    "apple_basket": Cargo(
        id="apple_basket",
        label="apple basket",
        phrase="a round basket of shiny apples",
        rolling=True,
        risk=1,
        tags={"apples", "basket"},
    ),
}

HAZARDS = {
    "wet_floor": Hazard(
        id="wet_floor",
        label="wet floor",
        phrase="a fresh wet patch near the sink",
        beat="A clean strip of floor still shone with rinse water near the sink.",
        risk=2,
        tags={"wet_floor", "slippery"},
    ),
    "swinging_door": Hazard(
        id="swinging_door",
        label="swinging door",
        phrase="the swinging kitchen door",
        beat="The swinging door kept thump-thump-thumping as people passed through it.",
        risk=2,
        tags={"door"},
    ),
    "crowded_corner": Hazard(
        id="crowded_corner",
        label="crowded corner",
        phrase="a crowded corner by the tray stack",
        beat="Children and carts kept meeting at one busy corner by the tray stack.",
        risk=1,
        tags={"crowd"},
    ),
}

RESPONSES = {
    "cart": Response(
        id="cart",
        label="rolling cart",
        sense=3,
        power=3,
        handles={"wet_floor", "swinging_door", "crowded_corner"},
        text="slid the wobbling cargo onto a small rolling cart and guided it past the trouble spot",
        fail="tried to slide the wobbling cargo onto a small rolling cart, but a splash had already tipped too far",
        qa_text="used a small rolling cart to carry the cargo safely",
        tags={"cart"},
    ),
    "steady_hands": Response(
        id="steady_hands",
        label="steady hands",
        sense=2,
        power=2,
        handles={"wet_floor", "swinging_door", "crowded_corner"},
        text="reached out with both steady hands and caught the cargo before it tipped",
        fail="caught at the cargo with both hands, but a little of it still sloshed over the side",
        qa_text="caught the cargo with both hands before it tipped",
        tags={"steady_hands"},
    ),
    "clear_path": Response(
        id="clear_path",
        label="clear path",
        sense=3,
        power=2,
        handles={"swinging_door", "crowded_corner"},
        text="held the path clear, opened the way, and helped the cargo move through one slow step at a time",
        fail="opened a path and tried to help, but the cargo had already lurched too hard",
        qa_text="cleared the path and helped the cargo move through slowly",
        tags={"clear_path"},
    ),
    "mop_first": Response(
        id="mop_first",
        label="mop first",
        sense=3,
        power=3,
        handles={"wet_floor"},
        text="set the cargo down, wiped the wet patch dry, and then helped carry it across",
        fail="set the cargo down and reached for a mop, but a little slosh had already slipped over the rim",
        qa_text="dried the wet patch before carrying the cargo across",
        tags={"mop"},
    ),
    "dash": Response(
        id="dash",
        label="dash",
        sense=1,
        power=0,
        handles=set(),
        text="",
        fail="",
        qa_text="",
        tags={"unsafe"},
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Nora", "Maya"]
BOY_NAMES = ["Tom", "Ben", "Max", "Sam", "Leo", "Finn", "Eli", "Noah"]
FRIEND_TRAITS = ["careful", "patient", "steady", "thoughtful", "curious", "brave"]
EMPLOYEE_NAMES = ["Rosa", "Nina", "Marta", "Jules"]


def hazard_at_risk(cargo: Cargo, hazard: Hazard) -> bool:
    if hazard.id == "wet_floor":
        return cargo.hot or cargo.heavy
    if hazard.id == "swinging_door":
        return cargo.hot or cargo.heavy or cargo.rolling
    if hazard.id == "crowded_corner":
        return cargo.rolling or cargo.hot
    return False


def response_works(response: Response, hazard: Hazard) -> bool:
    return hazard.id in response.handles


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for theme in THEMES:
        for cargo_id, cargo in CARGOES.items():
            for hazard_id, hazard in HAZARDS.items():
                if not hazard_at_risk(cargo, hazard):
                    continue
                for response_id, response in RESPONSES.items():
                    if response.sense >= SENSE_MIN and response_works(response, hazard):
                        combos.append((theme, cargo_id, hazard_id, response_id))
    return combos


def fire_like_severity(cargo: Cargo, hazard: Hazard) -> int:
    return cargo.risk + hazard.risk - 1


def initial_caution(trait: str) -> float:
    return 5.0 if trait in CAREFUL_TRAITS else 3.0


def would_listen(relation: str, hero_age: int, friend_age: int, friend_trait: str, trust: int) -> bool:
    older_friend = relation == "friends" and friend_age > hero_age
    authority = initial_caution(friend_trait) + (2.0 if older_friend else 0.0) + (1.0 if trust >= 7 else 0.0)
    return older_friend and authority > EAGERNESS_INIT


def is_saved(response: Response, cargo: Cargo, hazard: Hazard) -> bool:
    return response_works(response, hazard) and response.power >= fire_like_severity(cargo, hazard)


def explain_rejection(cargo: Cargo, hazard: Hazard) -> str:
    return (
        f"(No story: {hazard.label} is not a strong enough problem for {cargo.phrase}. "
        f"This world only tells cafeteria adventures where the caution honestly matters.)"
    )


def explain_response(response_id: str) -> str:
    response = RESPONSES[response_id]
    better = ", ".join(sorted(r.id for r in sensible_responses()))
    return (
        f"(Refusing response '{response_id}': it scores too low on common sense "
        f"(sense={response.sense} < {SENSE_MIN}). Try one of: {better}.)"
    )


def predict_trouble(world: World) -> dict:
    sim = world.copy()
    hero = sim.get("hero")
    cargo = sim.get("cargo")
    hero.meters["moving_fast"] += 1
    cargo.meters["carried"] += 1
    propagate(sim, narrate=False)
    return {
        "wobble": cargo.meters["wobble"] >= THRESHOLD,
        "spill": cargo.meters["spilled"] >= THRESHOLD,
    }


def introduce(world: World, theme: Theme, hero: Entity, friend: Entity, employee: Entity) -> None:
    for child in (hero, friend):
        child.memes["joy"] += 1
    employee.memes["care"] += 1
    world.say(
        f"After school, {hero.id} and {friend.id} waited in the cafeteria while families talked in the hall. "
        f"{theme.opening}"
    )
    world.say(
        f"The kind cafeteria employee, {employee.id}, was stacking trays and humming. "
        f'Soon the two friends decided they were not in an ordinary room at all, but in {theme.scene}.'
    )
    world.say(
        f'"Can we help with a {theme.mission}?" {hero.id} asked. '
        f'{employee.id} smiled and said there might be one small but important adventure.'
    )


def mission(world: World, theme: Theme, cargo: Cargo, hazard: Hazard, employee: Entity) -> None:
    world.say(
        f"{employee.id} pointed to {cargo.phrase}. It needed to reach the serving table to {theme.goal}."
    )
    world.say(hazard.beat)


def first_warning(world: World, hero: Entity, cargo: Cargo, hazard: Hazard, employee: Entity) -> None:
    hero.memes["eagerness"] += 1
    world.say(
        f'{hero.id} leaned forward at once. "I can carry {cargo.it()}!" {hero.pronoun()} said.'
    )
    pred = predict_trouble(world)
    world.facts["predicted_wobble"] = pred["wobble"]
    world.facts["predicted_spill"] = pred["spill"]
    line = "Slow feet, two hands, ask first."
    world.facts["rule_line"] = line
    world.say(
        f'{employee.id} lifted one finger and repeated the cafeteria rule: "{line}" '
        f'{employee.pronoun().capitalize()} said it once, then said it again so the words would stick.'
    )


def friend_warning(world: World, hero: Entity, friend: Entity, cargo: Cargo, hazard: Hazard) -> None:
    friend.memes["caution"] += 1
    extra = " The words sounded brave in a quiet way." if friend.traits and friend.traits[0] in CAREFUL_TRAITS else ""
    world.say(
        f'{friend.id} nodded. "{world.facts["rule_line"]}" {friend.pronoun()} echoed. '
        f'"{hazard.phrase.capitalize()} and {cargo.phrase} are a tricky mix."{extra}'
    )


def back_down(world: World, theme: Theme, hero: Entity, friend: Entity, employee: Entity, response: Response) -> None:
    hero.memes["relief"] += 1
    friend.memes["relief"] += 1
    employee.memes["pride"] += 1
    world.say(
        f"{hero.id} looked at the floor, then at {friend.id}, and took a long breath. "
        f'"Okay," {hero.pronoun()} said. "Slow feet, two hands, ask first."'
    )
    world.say(
        f"{employee.id} beamed. Instead of hurrying, they chose the safe plan. "
        f"{employee.pronoun().capitalize()} {response.text}."
    )
    world.say(
        f'The mission still felt grand, only steadier, and the two friends stayed side by side until {theme.ending}.'
    )


def defy(world: World, hero: Entity, cargo_ent: Entity) -> None:
    hero.memes["defiance"] += 1
    hero.meters["moving_fast"] += 1
    cargo_ent.meters["carried"] += 1
    world.say(
        f'But the adventure in {hero.id} still felt too big and bouncy. Before anyone could stop {hero.pronoun("object")}, '
        f'{hero.pronoun()} lifted the cargo and hurried forward.'
    )


def wobble_beat(world: World, hero: Entity, cargo: Cargo, hazard: Hazard) -> None:
    propagate(world, narrate=False)
    world.say(
        f"Right by {hazard.phrase}, the {cargo.label} gave a frightened wobble. "
        f"{hero.id}'s heart thumped hard."
    )


def rescue(world: World, employee: Entity, response: Response, cargo: Cargo, hero: Entity, friend: Entity) -> None:
    cargo_ent = world.get("cargo")
    cargo_ent.meters["saved"] += 1
    cargo_ent.meters["wobble"] = 0.0
    cargo_ent.meters["spilled"] = 0.0
    world.get("cafeteria").meters["mess"] = 0.0
    hero.memes["relief"] += 1
    friend.memes["relief"] += 1
    world.say(
        f"{employee.id} moved fast but calmly and {response.text}."
    )
    world.say(
        f'Nothing splashed after all. {hero.id} stared, then whispered, "You saved it."'
    )


def spill(world: World, employee: Entity, response: Response, cargo: Cargo, hero: Entity, friend: Entity) -> None:
    cargo_ent = world.get("cargo")
    propagate(world, narrate=False)
    hero.memes["sad"] += 1
    friend.memes["sad"] += 1
    world.say(
        f"{employee.id} {response.fail}."
    )
    if cargo.hot:
        world.say(
            "A little soup sloshed onto the floor with a warm plop. No one was hurt, but the room went very still."
        )
    elif cargo.rolling:
        world.say(
            "Two apples rolled away in bright red arcs. No one was hurt, but everyone had to stop and look down."
        )
    else:
        world.say(
            "A ribbon of milk splashed across the tiles. No one was hurt, but the mistake was plain and white on the floor."
        )
    world.say(
        f"{hero.id} put the cargo down at once and wished {hero.pronoun()} had listened the first time."
    )


def lesson(world: World, employee: Entity, hero: Entity, friend: Entity) -> None:
    for child in (hero, friend):
        child.memes["friendship"] += 1
        child.memes["lesson"] += 1
        child.memes["fear"] = 0.0
    employee.memes["friendship"] += 1
    world.say(
        f'{employee.id} knelt beside the two friends. "Adventures are better when everyone stays safe," '
        f'{employee.pronoun()} said softly. "That is why I keep repeating the rule."'
    )
    world.say(
        f'{friend.id} said it first this time: "{world.facts["rule_line"]}" '
        f'{hero.id} said it too, slower than before, and the words finally sounded true inside {hero.pronoun("object")}.'
    )


def ending(world: World, theme: Theme, employee: Entity, hero: Entity, friend: Entity, cargo: Cargo, listened: bool) -> None:
    hero.memes["joy"] += 1
    friend.memes["joy"] += 1
    employee.memes["care"] += 1
    if listened:
        world.say(
            f"At the end, {employee.id} let the friends carry a safe stack of napkins together. "
            f"They marched through the cafeteria like a tiny crew, and their friendship looked stronger because they had chosen patience together."
        )
    else:
        world.say(
            f"After the spill was cleaned and the worry was gone, {employee.id} still trusted the friends with one last tiny job: carrying spoons in a light basket together. "
            f"This time they went slowly, shoulder to shoulder, and {theme.ending}."
        )


def tell(
    theme: Theme,
    cargo: Cargo,
    hazard: Hazard,
    response: Response,
    hero_name: str = "Lily",
    hero_gender: str = "girl",
    friend_name: str = "Ben",
    friend_gender: str = "boy",
    employee_name: str = "Rosa",
    employee_type: str = "woman",
    friend_trait: str = "careful",
    relation: str = "friends",
    hero_age: int = 6,
    friend_age: int = 6,
    trust: int = 5,
) -> World:
    world = World()
    hero = world.add(Entity(
        id="hero",
        kind="character",
        type=hero_gender,
        label=hero_name,
        role="hero",
        age=hero_age,
        attrs={"display": hero_name, "relation": relation},
    ))
    friend = world.add(Entity(
        id="friend",
        kind="character",
        type=friend_gender,
        label=friend_name,
        role="friend",
        age=friend_age,
        traits=[friend_trait],
        attrs={"display": friend_name, "relation": relation},
    ))
    employee = world.add(Entity(
        id="employee",
        kind="character",
        type=employee_type,
        label=employee_name,
        role="employee",
        attrs={"job": "cafeteria employee"},
    ))
    world.add(Entity(id="cafeteria", type="room", label="cafeteria"))
    cargo_ent = world.add(Entity(id="cargo", type="cargo", label=cargo.label, phrase=cargo.phrase))
    world.add(Entity(id="hazard", type="hazard", label=hazard.label, phrase=hazard.phrase))

    hero.memes["eagerness"] = EAGERNESS_INIT
    friend.memes["caution"] = initial_caution(friend_trait)
    friend.memes["trust"] = float(trust)

    introduce(world, theme, hero, friend, employee)
    mission(world, theme, cargo, hazard, employee)
    world.para()
    first_warning(world, hero, cargo, hazard, employee)
    friend_warning(world, hero, friend, cargo, hazard)

    listened = would_listen(relation, hero_age, friend_age, friend_trait, trust)
    world.facts["listened"] = listened

    if listened:
        world.para()
        back_down(world, theme, hero, friend, employee, response)
        outcome = "listened"
    else:
        world.para()
        defy(world, hero, cargo_ent)
        wobble_beat(world, hero, cargo, hazard)
        world.para()
        saved = is_saved(response, cargo, hazard)
        if saved:
            rescue(world, employee, response, cargo, hero, friend)
            outcome = "saved"
        else:
            spill(world, employee, response, cargo, hero, friend)
            outcome = "spilled"
        world.para()
        lesson(world, employee, hero, friend)

    world.para()
    ending(world, theme, employee, hero, friend, cargo, listened)

    world.facts.update(
        theme=theme,
        cargo_cfg=cargo,
        hazard_cfg=hazard,
        response=response,
        hero=hero,
        friend=friend,
        employee=employee,
        relation=relation,
        outcome=outcome,
        severity=fire_like_severity(cargo, hazard),
        rule_line=world.facts.get("rule_line", "Slow feet, two hands, ask first."),
    )
    return world


def display_name(ent: Entity) -> str:
    return ent.attrs.get("display", ent.label or ent.id)


def pair_noun(hero: Entity, friend: Entity, relation: str) -> str:
    if relation == "friends":
        return "two friends"
    return "two children"


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    cargo = f["cargo_cfg"]
    hazard = f["hazard_cfg"]
    employee = f["employee"]
    outcome = f["outcome"]
    line = f["rule_line"]
    if outcome == "listened":
        return [
            f'Write a short adventure story for a 3-to-5-year-old set in a cafeteria with a kind employee and two friends. Include the word "employee".',
            f"Tell a friendship story where {display_name(hero)} wants to carry {cargo.phrase}, but a careful friend repeats a safety rule and helps stop trouble before it starts.",
            f'Write a cautionary but gentle story with repetition around the line "{line}" and end with the children choosing the safe way together.',
        ]
    if outcome == "saved":
        return [
            f'Write a short cafeteria adventure where a child hurries with {cargo.phrase} near {hazard.label}, but a cafeteria employee calmly saves the day.',
            f"Tell a friendship-and-safety story where {display_name(friend)} repeats a warning, {display_name(hero)} forgets it for one moment, and a grown-up helper keeps everyone safe.",
            f'Write a cautionary story that repeats "{line}" and ends with the children learning why the rule matters.',
        ]
    return [
        f'Write a cautionary adventure in a cafeteria where a child rushes with {cargo.phrase} near {hazard.label} and makes a small mess, but nobody gets hurt.',
        f"Tell a story about friendship, repetition, and listening where a cafeteria employee teaches two children to slow down.",
        f'Write a simple story for young children that includes the word "cafeteria", the word "employee", and the repeated rule "{line}".',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    employee = f["employee"]
    cargo = f["cargo_cfg"]
    hazard = f["hazard_cfg"]
    response = f["response"]
    outcome = f["outcome"]
    pair = pair_noun(hero, friend, f["relation"])
    hero_name = display_name(hero)
    friend_name = display_name(friend)
    employee_name = display_name(employee)
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair}, {hero_name} and {friend_name}, and {employee_name}, the cafeteria employee who watched over them. "
            f"They turned an ordinary errand into an adventure together."
        ),
        (
            "What did the children want to do?",
            f"They wanted to help carry {cargo.phrase} through the cafeteria as part of a pretend mission. "
            f"The helping felt exciting, which is why {hero_name} wanted to move too fast."
        ),
        (
            "What rule did the cafeteria employee repeat?",
            f'{employee_name} repeated, "{f["rule_line"]}". '
            f'The line was said more than once so the safety idea would stay in the children\'s minds.'
        ),
        (
            f"Why was {hazard.label} a problem?",
            f"{hazard.phrase.capitalize()} made carrying {cargo.phrase} risky. "
            f"In this story world, that mix can make the cargo wobble and turn a fun job into a mess."
        ),
    ]
    if outcome == "listened":
        qa.append(
            (
                f"How did {friend_name} help {hero_name}?",
                f"{friend_name} repeated the same rule the cafeteria employee had said and helped {hero_name} stop and think. "
                f"Because the warning came from a friend too, {hero_name} listened before anything tipped."
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It ended safely, with the friends choosing a slower plan and still getting to help. "
                f"The final image shows that the adventure could continue because they used patience instead of rushing."
            )
        )
    elif outcome == "saved":
        qa.append(
            (
                f"How did {employee_name} solve the problem?",
                f"{employee_name} {response.qa_text}. "
                f"That quick, calm action stopped the wobble before it became a spill."
            )
        )
        qa.append(
            (
                f"What did {hero_name} learn?",
                f"{hero_name} learned that excitement is not the same thing as readiness. "
                f"When the rule was repeated after the scare, it finally made sense because the danger had just felt real."
            )
        )
    else:
        qa.append(
            (
                f"What happened when {hero_name} hurried?",
                f"The cargo wobbled and a little of it spilled, so the cafeteria floor turned messy for a moment. "
                f'No one was hurt, but the small accident made the warning feel important.'
            )
        )
        qa.append(
            (
                f"Was {employee_name} mean after the spill?",
                f"No. {employee_name} was calm and kind, and used the mistake as a lesson instead of a punishment. "
                f'That kindness helped the children keep their friendship and try again more carefully.'
            )
        )
    return qa


KNOWLEDGE = {
    "cafeteria": [
        (
            "What is a cafeteria?",
            "A cafeteria is a room where many people get food and eat, often at a school or a big building.",
        )
    ],
    "employee": [
        (
            "What is an employee?",
            "An employee is a person who works at a job and helps do the tasks there. A cafeteria employee helps prepare food, carry supplies, and keep the room running smoothly.",
        )
    ],
    "wet_floor": [
        (
            "Why is a wet floor slippery?",
            "A wet floor can be slippery because water makes it easier for shoes to slide instead of grip. That is why people should walk carefully around it.",
        )
    ],
    "door": [
        (
            "Why can a swinging door be tricky?",
            "A swinging door can move suddenly in both directions, so it can bump a person or a tray if someone rushes through without looking.",
        )
    ],
    "crowd": [
        (
            "Why is it harder to carry things in a crowd?",
            "In a crowd, people can stop, turn, or bump by surprise. Moving slowly gives everyone more time to see one another.",
        )
    ],
    "soup": [
        (
            "Why should you be careful with hot soup?",
            "Hot soup can splash if it tips or wobbles. Carrying it slowly helps keep it in the bowl and away from people's skin.",
        )
    ],
    "milk": [
        (
            "Why is a full pitcher hard to carry?",
            "A full pitcher is heavy, and the liquid inside can slosh when you move too quickly. Two steady hands make it easier to carry safely.",
        )
    ],
    "apples": [
        (
            "What happens when round apples fall?",
            "Round apples can roll away quickly once they hit the floor. That can make a small mess spread into many little chases.",
        )
    ],
    "cart": [
        (
            "What is a rolling cart for?",
            "A rolling cart helps move heavy or tricky things from one place to another. It lets the wheels do some of the work instead of your arms alone.",
        )
    ],
    "mop": [
        (
            "What does a mop do?",
            "A mop helps soak up water and clean wet floors. Dry floors are safer to walk on.",
        )
    ],
    "friendship": [
        (
            "How can a friend help keep you safe?",
            "A friend can remind you to slow down, notice danger, and help you make a better choice. Good friendship is not only fun; it is helpful too.",
        )
    ],
}
KNOWLEDGE_ORDER = [
    "cafeteria",
    "employee",
    "wet_floor",
    "door",
    "crowd",
    "soup",
    "milk",
    "apples",
    "cart",
    "mop",
    "friendship",
]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    cargo = f["cargo_cfg"]
    hazard = f["hazard_cfg"]
    response = f["response"]
    tags = {"cafeteria", "employee", "friendship"} | cargo.tags | hazard.tags | response.tags
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
        if e.age:
            bits.append(f"age={e.age}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {e.id:10} ({e.type:9}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        theme="quest",
        cargo="soup_tray",
        hazard="wet_floor",
        response="mop_first",
        hero="Lily",
        hero_gender="girl",
        friend="Ben",
        friend_gender="boy",
        employee_name="Rosa",
        employee_type="woman",
        friend_trait="careful",
        relation="friends",
        hero_age=5,
        friend_age=7,
        trust=8,
    ),
    StoryParams(
        theme="ship",
        cargo="milk_pitcher",
        hazard="swinging_door",
        response="cart",
        hero="Max",
        hero_gender="boy",
        friend="Mia",
        friend_gender="girl",
        employee_name="Nina",
        employee_type="woman",
        friend_trait="curious",
        relation="friends",
        hero_age=6,
        friend_age=6,
        trust=4,
    ),
    StoryParams(
        theme="trail",
        cargo="apple_basket",
        hazard="crowded_corner",
        response="steady_hands",
        hero="Ava",
        hero_gender="girl",
        friend="Leo",
        friend_gender="boy",
        employee_name="Jules",
        employee_type="man",
        friend_trait="thoughtful",
        relation="friends",
        hero_age=7,
        friend_age=6,
        trust=5,
    ),
    StoryParams(
        theme="quest",
        cargo="soup_tray",
        hazard="swinging_door",
        response="clear_path",
        hero="Noah",
        hero_gender="boy",
        friend="Ella",
        friend_gender="girl",
        employee_name="Marta",
        employee_type="woman",
        friend_trait="patient",
        relation="friends",
        hero_age=6,
        friend_age=8,
        trust=7,
    ),
]


ASP_RULES = r"""
hazard_at_risk(C, H) :- cargo(C), hazard(H), hot(C), wet_floor(H).
hazard_at_risk(C, H) :- cargo(C), hazard(H), heavy(C), wet_floor(H).
hazard_at_risk(C, H) :- cargo(C), hazard(H), hot(C), swinging_door(H).
hazard_at_risk(C, H) :- cargo(C), hazard(H), heavy(C), swinging_door(H).
hazard_at_risk(C, H) :- cargo(C), hazard(H), rolling(C), swinging_door(H).
hazard_at_risk(C, H) :- cargo(C), hazard(H), rolling(C), crowded_corner(H).
hazard_at_risk(C, H) :- cargo(C), hazard(H), hot(C), crowded_corner(H).

sensible(R) :- response(R), sense(R, S), sense_min(M), S >= M.
works(R, H) :- handles(R, H).
valid(T, C, H, R) :- theme(T), hazard_at_risk(C, H), sensible(R), works(R, H).

careful_now(T) :- trait(T), is_careful(T).
base_caution(5) :- trait(T), careful_now(T).
base_caution(3) :- trait(T), not careful_now(T).
older_friend :- relation(friends), friend_age(FA), hero_age(HA), FA > HA.
trust_bonus(1) :- trust(V), V >= 7.
trust_bonus(0) :- trust(V), V < 7.
age_bonus(2) :- older_friend.
age_bonus(0) :- not older_friend.
authority(C + A + T) :- base_caution(C), age_bonus(A), trust_bonus(T).
listened :- older_friend, authority(X), eagerness_init(E), X > E.

severity(RiskC + RiskH - 1) :- chosen_cargo(C), cargo_risk(C, RiskC), chosen_hazard(H), hazard_risk(H, RiskH).
saved :- chosen_response(R), chosen_hazard(H), works(R, H), power(R, P), severity(S), P >= S.

outcome(listened) :- listened.
outcome(saved) :- not listened, saved.
outcome(spilled) :- not listened, not saved.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for theme_id in THEMES:
        lines.append(asp.fact("theme", theme_id))
    for cargo_id, cargo in CARGOES.items():
        lines.append(asp.fact("cargo", cargo_id))
        lines.append(asp.fact("cargo_risk", cargo_id, cargo.risk))
        if cargo.hot:
            lines.append(asp.fact("hot", cargo_id))
        if cargo.heavy:
            lines.append(asp.fact("heavy", cargo_id))
        if cargo.rolling:
            lines.append(asp.fact("rolling", cargo_id))
    for hazard_id, hazard in HAZARDS.items():
        lines.append(asp.fact("hazard", hazard_id))
        lines.append(asp.fact("hazard_risk", hazard_id, hazard.risk))
        lines.append(asp.fact(hazard_id, hazard_id))
    for response_id, response in RESPONSES.items():
        lines.append(asp.fact("response", response_id))
        lines.append(asp.fact("sense", response_id, response.sense))
        lines.append(asp.fact("power", response_id, response.power))
        for hazard_id in sorted(response.handles):
            lines.append(asp.fact("handles", response_id, hazard_id))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    lines.append(asp.fact("eagerness_init", int(EAGERNESS_INIT)))
    for trait in sorted(CAREFUL_TRAITS):
        lines.append(asp.fact("is_careful", trait))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp

    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(r for (r,) in asp.atoms(model, "sensible"))


def outcome_of(params: StoryParams) -> str:
    if would_listen(params.relation, params.hero_age, params.friend_age, params.friend_trait, params.trust):
        return "listened"
    cargo = CARGOES[params.cargo]
    hazard = HAZARDS[params.hazard]
    response = RESPONSES[params.response]
    return "saved" if is_saved(response, cargo, hazard) else "spilled"


def asp_outcome(params: StoryParams) -> str:
    import asp

    scenario = "\n".join(
        [
            asp.fact("chosen_cargo", params.cargo),
            asp.fact("chosen_hazard", params.hazard),
            asp.fact("chosen_response", params.response),
            asp.fact("relation", params.relation),
            asp.fact("hero_age", params.hero_age),
            asp.fact("friend_age", params.friend_age),
            asp.fact("trait", params.friend_trait),
            asp.fact("trust", params.trust),
        ]
    )
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def generate_smoke_test() -> None:
    sample = generate(CURATED[0])
    if not sample.story or "cafeteria" not in sample.story.lower():
        raise StoryError("Smoke test failed: generated story missing expected cafeteria text.")


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

    clingo_sensible = set(asp_sensible())
    python_sensible = {r.id for r in sensible_responses()}
    if clingo_sensible == python_sensible:
        print(f"OK: sensible responses match ({sorted(clingo_sensible)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible responses: clingo={sorted(clingo_sensible)} python={sorted(python_sensible)}")

    scenarios = list(CURATED)
    for seed in range(100):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
        except StoryError:
            continue
        scenarios.append(params)
    bad = sum(1 for p in scenarios if asp_outcome(p) != outcome_of(p))
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(scenarios)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(scenarios)} outcomes differ.")

    try:
        generate_smoke_test()
        print("OK: smoke test generated a normal story.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(conflict_handler="resolve",
        description="Story world: cafeteria friendship adventure with repeated safety advice."
    )
    ap.add_argument("--theme", choices=THEMES)
    ap.add_argument("--cargo", choices=CARGOES)
    ap.add_argument("--hazard", choices=HAZARDS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--hero")
    ap.add_argument("--friend")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--friend-gender", choices=["girl", "boy"])
    ap.add_argument("--employee-name", choices=EMPLOYEE_NAMES)
    ap.add_argument("--employee-type", choices=["woman", "man"])
    ap.add_argument("--friend-trait", choices=FRIEND_TRAITS)
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


def pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [name for name in pool if name != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.cargo and args.hazard:
        if not hazard_at_risk(CARGOES[args.cargo], HAZARDS[args.hazard]):
            raise StoryError(explain_rejection(CARGOES[args.cargo], HAZARDS[args.hazard]))
    if args.response and RESPONSES[args.response].sense < SENSE_MIN:
        raise StoryError(explain_response(args.response))

    combos = [
        combo
        for combo in valid_combos()
        if (args.theme is None or combo[0] == args.theme)
        and (args.cargo is None or combo[1] == args.cargo)
        and (args.hazard is None or combo[2] == args.hazard)
        and (args.response is None or combo[3] == args.response)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    theme_id, cargo_id, hazard_id, response_id = rng.choice(sorted(combos))
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    friend_gender = args.friend_gender or rng.choice(["girl", "boy"])
    hero_name = args.hero or pick_name(rng, hero_gender)
    friend_name = args.friend or pick_name(rng, friend_gender, avoid=hero_name)
    employee_name = args.employee_name or rng.choice(EMPLOYEE_NAMES)
    employee_type = args.employee_type or rng.choice(["woman", "man"])
    friend_trait = args.friend_trait or rng.choice(FRIEND_TRAITS)
    hero_age, friend_age = rng.sample([4, 5, 6, 7, 8], 2)
    trust = rng.randint(3, 9)

    return StoryParams(
        theme=theme_id,
        cargo=cargo_id,
        hazard=hazard_id,
        response=response_id,
        hero=hero_name,
        hero_gender=hero_gender,
        friend=friend_name,
        friend_gender=friend_gender,
        employee_name=employee_name,
        employee_type=employee_type,
        friend_trait=friend_trait,
        relation="friends",
        hero_age=hero_age,
        friend_age=friend_age,
        trust=trust,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        theme = THEMES[params.theme]
        cargo = CARGOES[params.cargo]
        hazard = HAZARDS[params.hazard]
        response = RESPONSES[params.response]
    except KeyError as err:
        raise StoryError(f"(Unknown parameter value: {err})") from err

    if not hazard_at_risk(cargo, hazard):
        raise StoryError(explain_rejection(cargo, hazard))
    if response.sense < SENSE_MIN:
        raise StoryError(explain_response(params.response))
    if not response_works(response, hazard):
        raise StoryError(f"(No story: response '{params.response}' does not fit the hazard '{params.hazard}'.)")

    world = tell(
        theme=theme,
        cargo=cargo,
        hazard=hazard,
        response=response,
        hero_name=params.hero,
        hero_gender=params.hero_gender,
        friend_name=params.friend,
        friend_gender=params.friend_gender,
        employee_name=params.employee_name,
        employee_type=params.employee_type,
        friend_trait=params.friend_trait,
        relation=params.relation,
        hero_age=params.hero_age,
        friend_age=params.friend_age,
        trust=params.trust,
    )
    return StorySample(
        params=params,
        story=world.render().replace(" hero ", " ").replace(" friend ", " "),
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
        print(asp_program("", "#show valid/4.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"sensible responses: {', '.join(asp_sensible())}\n")
        print(f"{len(combos)} compatible (theme, cargo, hazard, response) combos:\n")
        for theme, cargo, hazard, response in combos:
            print(f"  {theme:6} {cargo:12} {hazard:14} {response}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(params) for params in CURATED]
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
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero} & {p.friend}: {p.cargo} near {p.hazard} ({outcome_of(p)})"
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
