#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/anemone_offer_ammonia_happy_ending_space_adventure.py
=================================================================================

A standalone storyworld about two young spacefarers caring for a sea anemone in
a shipboard tank. One child makes an eager offer to feed it extra food before a
night of star-watching, the other foresees an ammonia problem, and the crew
learns a safer way to help.

The world model keeps the story honest:

    extra feeding + rich food in a small habitat -> waste
    waste in water                              -> ammonia
    ammonia                                     -> anemone stress + child worry

A near-miss ending happens when the warning lands in time and no ammonia rises.
Otherwise a calm grown-up uses a sensible aquarium response, and the story still
ends happily with a healthier tank and a clear plan.

Run it
------
    python storyworlds/worlds/gpt-5.4/anemone_offer_ammonia_happy_ending_space_adventure.py
    python storyworlds/worlds/gpt-5.4/anemone_offer_ammonia_happy_ending_space_adventure.py --habitat reef_globe --food shrimp_pellet
    python storyworlds/worlds/gpt-5.4/anemone_offer_ammonia_happy_ending_space_adventure.py --food cracker
    python storyworlds/worlds/gpt-5.4/anemone_offer_ammonia_happy_ending_space_adventure.py --all
    python storyworlds/worlds/gpt-5.4/anemone_offer_ammonia_happy_ending_space_adventure.py --qa --json
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
SENSE_MIN = 2
TRUST_TO_LISTEN = 7


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
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
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Theme:
    id: str
    station: str
    room: str
    window_view: str
    opening: str
    mission: str
    ending_line: str


@dataclass
class Habitat:
    id: str
    label: str
    phrase: str
    liters: int
    shimmer: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Food:
    id: str
    label: str
    phrase: str
    suitable: bool
    waste: int
    cloud: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Response:
    id: str
    sense: int
    power: int
    text: str
    qa_text: str
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
        return self.entities[eid]

    def kids(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.role in {"instigator", "cautioner"}]

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
        clone.facts = dict(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def hazard_level(habitat: Habitat, food: Food) -> int:
    if not food.suitable:
        return 0
    if habitat.liters <= 6:
        return food.waste + 1
    if habitat.liters <= 10:
        return food.waste
    return max(food.waste - 1, 0)


def would_listen(relation: str, instigator_age: int, cautioner_age: int,
                 trait: str, trust: int) -> bool:
    strong_trait = trait in {"careful", "patient", "studious"}
    older = relation == "siblings" and cautioner_age > instigator_age
    return trust >= TRUST_TO_LISTEN and (strong_trait or older)


def _r_ammonia(world: World) -> list[str]:
    tank = world.get("tank")
    if tank.meters["waste"] < THRESHOLD:
        return []
    sig = ("ammonia",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    tank.meters["ammonia"] += tank.meters["waste"]
    return []


def _r_stress(world: World) -> list[str]:
    tank = world.get("tank")
    anemone = world.get("anemone")
    if tank.meters["ammonia"] < THRESHOLD:
        return []
    sig = ("stress",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    anemone.meters["stress"] += 1
    for kid in world.kids():
        kid.memes["worry"] += 1
    return []


CAUSAL_RULES = [
    Rule(name="ammonia", tag="physical", apply=_r_ammonia),
    Rule(name="stress", tag="emotional", apply=_r_stress),
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
                produced.extend(out)
            else:
                if any(sig[0] == rule.name for sig in world.fired):
                    pass
        fired_now = len(world.fired)
        if fired_now:
            changed = changed or False
        stable = True
        for rule in CAUSAL_RULES:
            before = len(world.fired)
            rule.apply(world)
            if len(world.fired) > before:
                stable = False
        if not stable:
            changed = True
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def hazard_at_risk(habitat: Habitat, food: Food) -> bool:
    return food.suitable and hazard_level(habitat, food) >= 1


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def is_fixed(response: Response, habitat: Habitat, food: Food) -> bool:
    return response.power >= hazard_level(habitat, food)


def predict_ammonia(world: World, habitat: Habitat, food: Food) -> dict:
    sim = world.copy()
    tank = sim.get("tank")
    tank.meters["waste"] += hazard_level(habitat, food)
    propagate(sim, narrate=False)
    return {
        "ammonia": tank.meters["ammonia"],
        "stress": sim.get("anemone").meters["stress"],
    }


def setup(world: World, theme: Theme, a: Entity, b: Entity, habitat: Habitat) -> None:
    for kid in (a, b):
        kid.memes["wonder"] += 1
    world.say(
        f"{theme.opening} At {theme.room}, {a.id} and {b.id} pressed close to "
        f"{habitat.phrase}. Beyond them, {theme.window_view}."
    )
    world.say(
        f"Inside the little water world lived an anemone named Bloom. "
        f"It waved soft arms through {habitat.shimmer} as if answering their mission."
    )
    world.say(f'"Tonight," {a.id} whispered, "after our chores, we can {theme.mission}."')


def notice(world: World, b: Entity) -> None:
    world.say(
        f"{b.id} checked the tank log and the tiny feeding scoop hanging beside the glass."
    )


def offer_extra(world: World, a: Entity, food: Food) -> None:
    a.memes["eager"] += 1
    world.say(
        f'{a.id} grinned. "I have an offer," {a.pronoun()} said. '
        f'"Let\'s give Bloom extra {food.label} before we go. '
        f'Then the anemone will have a feast while we watch the stars."'
    )


def warn(world: World, b: Entity, a: Entity, parent: Entity,
         habitat: Habitat, food: Food) -> None:
    pred = predict_ammonia(world, habitat, food)
    b.memes["care"] += 1
    world.facts["predicted_ammonia"] = pred["ammonia"]
    world.say(
        f'{b.id} shook {b.pronoun("possessive")} head. "{a.id}, extra food can rot '
        f'in a small tank. That can make ammonia in the water, and ammonia hurts sea '
        f'animals even when we cannot see it right away."'
    )
    if pred["ammonia"] >= 2:
        world.say(
            f'{b.pronoun().capitalize()} tapped the tank log. "{parent.label_word.capitalize()} said '
            f'this {habitat.label} is beautiful because it stays balanced. Too much food would tip it."'
        )


def back_down(world: World, a: Entity, b: Entity, parent: Entity) -> None:
    a.memes["relief"] += 1
    b.memes["relief"] += 1
    world.say(
        f'{a.id} looked at Bloom, then at the tiny scoop, and let out a slow breath. '
        f'"You\'re right," {a.pronoun()} said. "My offer sounded kind, but it was too much."'
    )
    world.say(
        f"They used only the right little scoop and called {parent.label_word} over to check the chart with them."
    )


def defy(world: World, a: Entity, food: Food) -> None:
    a.memes["defiance"] += 1
    world.say(
        f'But excitement hummed too loudly in {a.id}\'s chest. '
        f'Before anyone could stop {a.pronoun("object")}, {a.pronoun()} tipped extra {food.label} into the tank.'
    )


def overfeed(world: World, habitat: Habitat, food: Food) -> None:
    tank = world.get("tank")
    tank.meters["waste"] += hazard_level(habitat, food)
    propagate(world, narrate=False)
    world.say(
        f"The bits of {food.label} drifted past the rocks. Soon the water looked {food.cloud}, not clean and bright."
    )
    if tank.meters["ammonia"] >= THRESHOLD:
        world.say(
            "The test strip near the filter shifted from pale yellow toward green. "
            "Something in the water had changed."
        )


def distress(world: World, a: Entity, b: Entity) -> None:
    anemone = world.get("anemone")
    if anemone.meters["stress"] >= THRESHOLD:
        world.say(
            f"Bloom pulled in a little, and both children went still. {b.id} reached for {a.id}'s sleeve."
        )
        world.say(f'"We need help now," {b.id} said.')


def fix_tank(world: World, parent: Entity, response: Response) -> None:
    tank = world.get("tank")
    anemone = world.get("anemone")
    tank.meters["waste"] = 0.0
    tank.meters["ammonia"] = 0.0
    anemone.meters["stress"] = 0.0
    for kid in world.kids():
        kid.memes["worry"] = 0.0
        kid.memes["relief"] += 1
    world.say(
        f"{parent.label_word.capitalize()} came over at once and {response.text}."
    )
    world.say(
        "Fresh water hummed through the filter, the warning color faded, and Bloom slowly opened again like a tiny flower in tide."
    )


def lesson(world: World, parent: Entity, a: Entity, b: Entity, food: Food) -> None:
    for kid in (a, b):
        kid.memes["lesson"] += 1
        kid.memes["love"] += 1
    world.say(
        f'{parent.label_word.capitalize()} knelt beside them. "A kind heart still needs a careful plan," '
        f'{parent.pronoun()} said. "In water this small, extra {food.label} can turn into waste, and waste can become ammonia."'
    )
    world.say(
        f'{a.id} nodded. "{food.label.capitalize()} is for feeding the anemone the right amount," '
        f'{a.pronoun()} said softly, "not the biggest amount."'
    )


def safe_end(world: World, theme: Theme, a: Entity, b: Entity, parent: Entity,
             habitat: Habitat) -> None:
    for kid in (a, b):
        kid.memes["joy"] += 1
        kid.memes["safety"] += 1
    world.say(
        f"Together they clipped a bright feeding chart beside the {habitat.label} and circled one tiny scoop for tomorrow."
    )
    world.say(
        f"Then the three of them dimmed the room lights. Beyond the glass, {theme.window_view}, "
        f"and Bloom swayed calmly in the clear water."
    )
    world.say(theme.ending_line)


def tell(theme: Theme, habitat: Habitat, food: Food, response: Response,
         instigator: str = "Nova", instigator_gender: str = "girl",
         cautioner: str = "Leo", cautioner_gender: str = "boy",
         parent_type: str = "mother", trait: str = "careful",
         relation: str = "siblings", instigator_age: int = 6,
         cautioner_age: int = 7, trust: int = 8) -> World:
    world = World()
    a = world.add(Entity(
        id=instigator,
        kind="character",
        type=instigator_gender,
        role="instigator",
        age=instigator_age,
        attrs={"relation": relation},
    ))
    b = world.add(Entity(
        id=cautioner,
        kind="character",
        type=cautioner_gender,
        role="cautioner",
        age=cautioner_age,
        traits=[trait],
        attrs={"relation": relation, "trust": trust},
    ))
    parent = world.add(Entity(
        id="Parent",
        kind="character",
        type=parent_type,
        role="parent",
        label="the parent",
    ))
    tank = world.add(Entity(
        id="tank",
        type="tank",
        label=habitat.label,
        phrase=habitat.phrase,
        attrs={"liters": habitat.liters},
    ))
    anemone = world.add(Entity(
        id="anemone",
        type="animal",
        label="anemone",
        phrase="the sea anemone Bloom",
        tags={"anemone"},
    ))

    setup(world, theme, a, b, habitat)
    notice(world, b)

    world.para()
    offer_extra(world, a, food)
    warn(world, b, a, parent, habitat, food)

    listened = would_listen(relation, instigator_age, cautioner_age, trait, trust)
    if listened:
        back_down(world, a, b, parent)
        outcome = "averted"
    else:
        defy(world, a, food)
        world.para()
        overfeed(world, habitat, food)
        distress(world, a, b)
        world.para()
        fix_tank(world, parent, response)
        lesson(world, parent, a, b, food)
        outcome = "fixed"

    world.para()
    safe_end(world, theme, a, b, parent, habitat)

    world.facts.update(
        theme=theme,
        habitat=habitat,
        food=food,
        response=response,
        instigator=a,
        cautioner=b,
        parent=parent,
        tank=tank,
        anemone=anemone,
        outcome=outcome,
        relation=relation,
        trust=trust,
        listened=listened,
        ammonia=tank.meters["ammonia"],
        stress=anemone.meters["stress"],
        corrected=outcome == "fixed",
    )
    return world


THEMES = {
    "station": Theme(
        id="station",
        station="the Lantern Ring",
        room="the life-science deck",
        window_view="a slow river of stars curved around the station windows",
        opening="On the spinning science station Lantern Ring, evening bells chimed for the young crew.",
        mission="watch the comet shower from the observation bubble",
        ending_line="The station sailed on, the stars kept falling in silver lines, and the little anemone danced in safe water.",
    ),
    "moonlab": Theme(
        id="moonlab",
        station="Moonbase Lark",
        room="the blue biolab",
        window_view="the gray moon plain shone under a black sky full of stars",
        opening="At Moonbase Lark, bedtime was still a little way off, and the biolab glowed like a secret cave.",
        mission="count the first bright meteors above the moon plain",
        ending_line="Outside, the moon stayed quiet and wide, while inside the anemone waved in healthy water under the lab lights.",
    ),
    "ship": Theme(
        id="ship",
        station="the starship Marigold",
        room="the garden bay",
        window_view="nebula light spilled in soft colors beyond the ship's round windows",
        opening="Far from Earth, the starship Marigold purred through the dark between worlds.",
        mission="look for the green comet from the bow dome",
        ending_line="The ship flew on through the velvet dark, and Bloom floated open and peaceful in the clear tank.",
    ),
}

HABITATS = {
    "pocket_tank": Habitat(
        id="pocket_tank",
        label="pocket tank",
        phrase="a round pocket tank no wider than a helmet",
        liters=5,
        shimmer="blue station light",
        tags={"tank", "small_tank"},
    ),
    "reef_globe": Habitat(
        id="reef_globe",
        label="reef globe",
        phrase="a glass reef globe strapped into a silver frame",
        liters=8,
        shimmer="green and gold instrument light",
        tags={"tank"},
    ),
    "bio_dome": Habitat(
        id="bio_dome",
        label="bio dome",
        phrase="a clear bio dome with a gentle circulation loop",
        liters=14,
        shimmer="soft moon-pale light",
        tags={"tank"},
    ),
}

FOODS = {
    "plankton_gel": Food(
        id="plankton_gel",
        label="plankton gel",
        phrase="a ribbon of plankton gel",
        suitable=True,
        waste=1,
        cloud="a little dusty",
        tags={"feeding"},
    ),
    "shrimp_pellet": Food(
        id="shrimp_pellet",
        label="shrimp pellets",
        phrase="two rich shrimp pellets",
        suitable=True,
        waste=2,
        cloud="cloudy and busy with crumbs",
        tags={"feeding"},
    ),
    "krill_cube": Food(
        id="krill_cube",
        label="krill cubes",
        phrase="extra krill cubes",
        suitable=True,
        waste=3,
        cloud="murky with tiny drifting specks",
        tags={"feeding"},
    ),
    "cracker": Food(
        id="cracker",
        label="cracker crumbs",
        phrase="cracker crumbs from a snack pouch",
        suitable=False,
        waste=0,
        cloud="crumbly",
        tags={"snack"},
    ),
}

RESPONSES = {
    "test_and_change": Response(
        id="test_and_change",
        sense=3,
        power=4,
        text="tested the water, changed part of it, and tucked a fresh filter pad into place",
        qa_text="tested the water and changed part of it",
        tags={"ammonia", "water_change"},
    ),
    "siphon_and_filter": Response(
        id="siphon_and_filter",
        sense=3,
        power=3,
        text="used a little siphon to lift out the extra food and then started the backup filter",
        qa_text="lifted out the extra food and started the backup filter",
        tags={"ammonia", "filter"},
    ),
    "wish_it_better": Response(
        id="wish_it_better",
        sense=1,
        power=0,
        text="closed the lid and wished for the best",
        qa_text="only wished for the best",
        tags={"bad_idea"},
    ),
}


GIRL_NAMES = ["Nova", "Mina", "Tara", "Luna", "Zoe", "Ivy", "Ayla", "Rhea"]
BOY_NAMES = ["Leo", "Milo", "Finn", "Orion", "Kai", "Eli", "Jules", "Noah"]
TRAITS = ["careful", "patient", "studious", "curious", "gentle", "thoughtful"]


@dataclass
class StoryParams:
    theme: str
    habitat: str
    food: str
    response: str
    instigator: str
    instigator_gender: str
    cautioner: str
    cautioner_gender: str
    parent: str
    trait: str
    relation: str = "siblings"
    instigator_age: int = 6
    cautioner_age: int = 7
    trust: int = 8
    seed: Optional[int] = None


CURATED = [
    StoryParams(
        theme="station",
        habitat="pocket_tank",
        food="shrimp_pellet",
        response="test_and_change",
        instigator="Nova",
        instigator_gender="girl",
        cautioner="Leo",
        cautioner_gender="boy",
        parent="mother",
        trait="careful",
        relation="siblings",
        instigator_age=6,
        cautioner_age=8,
        trust=9,
    ),
    StoryParams(
        theme="ship",
        habitat="reef_globe",
        food="krill_cube",
        response="test_and_change",
        instigator="Milo",
        instigator_gender="boy",
        cautioner="Ayla",
        cautioner_gender="girl",
        parent="father",
        trait="curious",
        relation="friends",
        instigator_age=6,
        cautioner_age=6,
        trust=4,
    ),
    StoryParams(
        theme="moonlab",
        habitat="bio_dome",
        food="plankton_gel",
        response="siphon_and_filter",
        instigator="Luna",
        instigator_gender="girl",
        cautioner="Finn",
        cautioner_gender="boy",
        parent="mother",
        trait="patient",
        relation="friends",
        instigator_age=5,
        cautioner_age=6,
        trust=8,
    ),
    StoryParams(
        theme="station",
        habitat="reef_globe",
        food="shrimp_pellet",
        response="siphon_and_filter",
        instigator="Kai",
        instigator_gender="boy",
        cautioner="Rhea",
        cautioner_gender="girl",
        parent="father",
        trait="studious",
        relation="siblings",
        instigator_age=7,
        cautioner_age=9,
        trust=8,
    ),
]


KNOWLEDGE = {
    "anemone": [
        (
            "What is an anemone?",
            "An anemone is a sea animal with soft waving arms. It is not a flower, even though it can look like one.",
        )
    ],
    "ammonia": [
        (
            "What is ammonia in aquarium water?",
            "Ammonia is a harmful waste chemical that can build up in water when leftover food and waste break down. Fish and other sea animals can get sick from it.",
        )
    ],
    "water_change": [
        (
            "Why does changing some tank water help?",
            "Changing part of the water takes away waste and lowers harmful chemicals. Clean water helps sea animals breathe and stay healthy.",
        )
    ],
    "filter": [
        (
            "What does a tank filter do?",
            "A filter moves water and helps trap dirt and waste. It helps keep the water cleaner for the animals living there.",
        )
    ],
    "feeding": [
        (
            "Why is too much food a problem in a tank?",
            "Extra food can sink, rot, and turn into waste. In a small tank, that can make the water dirty very fast.",
        )
    ],
}
KNOWLEDGE_ORDER = ["anemone", "feeding", "ammonia", "water_change", "filter"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for theme in THEMES:
        for habitat_id, habitat in HABITATS.items():
            for food_id, food in FOODS.items():
                if hazard_at_risk(habitat, food):
                    combos.append((theme, habitat_id, food_id))
    return combos


def explain_rejection(habitat: Habitat, food: Food) -> str:
    if not food.suitable:
        return (
            f"(No story: {food.label} is not sensible anemone food, so the child would not have a real caretaking choice. "
            f"Pick actual tank food like plankton gel or shrimp pellets.)"
        )
    return (
        f"(No story: extra {food.label} in the {habitat.label} would not create enough ammonia risk for this world model, "
        f"so there is no honest warning to build the story around.)"
    )


def explain_response(rid: str) -> str:
    r = RESPONSES[rid]
    good = ", ".join(sorted(x.id for x in sensible_responses()))
    return (
        f"(Refusing response '{rid}': it scores too low on common sense "
        f"(sense={r.sense} < {SENSE_MIN}). Try one of: {good}.)"
    )


def outcome_of(params: StoryParams) -> str:
    if would_listen(
        params.relation,
        params.instigator_age,
        params.cautioner_age,
        params.trait,
        params.trust,
    ):
        return "averted"
    return "fixed" if is_fixed(RESPONSES[params.response], HABITATS[params.habitat], FOODS[params.food]) else "bad"


ASP_RULES = r"""
hazard(H, F) :- habitat(H), food(F), suitable(F), risk(H, F, R), R >= 1.
valid(T, H, F) :- theme(T), hazard(H, F).

sensible(Rp) :- response(Rp), sense(Rp, S), sense_min(M), S >= M.

older_cautioner :- relation(siblings), cautioner_age(CA), instigator_age(IA), CA > IA.
strong_trait :- trait(T), strong(T).
listens :- trust(V), listen_min(M), V >= M, strong_trait.
listens :- trust(V), listen_min(M), V >= M, older_cautioner.

fixed :- chosen_habitat(H), chosen_food(F), chosen_response(Rp),
         risk(H, F, R), power(Rp, P), P >= R.

outcome(averted) :- listens.
outcome(fixed) :- not listens, fixed.
outcome(bad) :- not listens, not fixed.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for theme_id in THEMES:
        lines.append(asp.fact("theme", theme_id))
    for habitat_id, habitat in HABITATS.items():
        lines.append(asp.fact("habitat", habitat_id))
        lines.append(asp.fact("liters", habitat_id, habitat.liters))
    for food_id, food in FOODS.items():
        lines.append(asp.fact("food", food_id))
        if food.suitable:
            lines.append(asp.fact("suitable", food_id))
        lines.append(asp.fact("waste", food_id, food.waste))
        for habitat_id, habitat in HABITATS.items():
            lines.append(asp.fact("risk", habitat_id, food_id, hazard_level(habitat, food)))
    for rid, response in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, response.sense))
        lines.append(asp.fact("power", rid, response.power))
    for trait in sorted({"careful", "patient", "studious"}):
        lines.append(asp.fact("strong", trait))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    lines.append(asp.fact("listen_min", TRUST_TO_LISTEN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp

    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(r for (r,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen_habitat", params.habitat),
            asp.fact("chosen_food", params.food),
            asp.fact("chosen_response", params.response),
            asp.fact("relation", params.relation),
            asp.fact("instigator_age", params.instigator_age),
            asp.fact("cautioner_age", params.cautioner_age),
            asp.fact("trait", params.trait),
            asp.fact("trust", params.trust),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a space-station anemone, an eager offer, and a careful fix."
    )
    ap.add_argument("--theme", choices=THEMES)
    ap.add_argument("--habitat", choices=HABITATS)
    ap.add_argument("--food", choices=FOODS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible combos from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_child(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    names = [n for n in pool if n != avoid]
    return rng.choice(names), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.food and args.habitat:
        habitat = HABITATS[args.habitat]
        food = FOODS[args.food]
        if not hazard_at_risk(habitat, food):
            raise StoryError(explain_rejection(habitat, food))
    if args.response and RESPONSES[args.response].sense < SENSE_MIN:
        raise StoryError(explain_response(args.response))

    combos = [
        combo for combo in valid_combos()
        if (args.theme is None or combo[0] == args.theme)
        and (args.habitat is None or combo[1] == args.habitat)
        and (args.food is None or combo[2] == args.food)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    theme, habitat, food = rng.choice(sorted(combos))
    response = args.response or rng.choice(sorted(r.id for r in sensible_responses()))
    instigator, instigator_gender = _pick_child(rng)
    cautioner, cautioner_gender = _pick_child(rng, avoid=instigator)
    relation = rng.choice(["siblings", "friends"])
    instigator_age, cautioner_age = rng.sample([5, 6, 7, 8], 2)
    trust = rng.randint(3, 10)
    trait = rng.choice(TRAITS)
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(
        theme=theme,
        habitat=habitat,
        food=food,
        response=response,
        instigator=instigator,
        instigator_gender=instigator_gender,
        cautioner=cautioner,
        cautioner_gender=cautioner_gender,
        parent=parent,
        trait=trait,
        relation=relation,
        instigator_age=instigator_age,
        cautioner_age=cautioner_age,
        trust=trust,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    a = f["instigator"]
    b = f["cautioner"]
    theme = f["theme"]
    food = f["food"]
    return [
        f'Write a short space adventure for a 3-to-5-year-old that includes the words "anemone", "offer", and "ammonia".',
        f"Tell a gentle story where {a.id} makes an eager offer to feed a shipboard anemone extra {food.label}, and {b.id} helps keep the tank safe.",
        f"Write a happy-ending story on {theme.station} where children learn that caring for a small sea creature means choosing the right amount, not the biggest amount.",
    ]


def pair_noun(a: Entity, b: Entity, relation: str) -> str:
    if relation == "siblings":
        if a.type == "girl" and b.type == "girl":
            return "two sisters"
        if a.type == "boy" and b.type == "boy":
            return "two brothers"
        return "a brother and a sister"
    return "two young friends"


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    a = f["instigator"]
    b = f["cautioner"]
    parent = f["parent"]
    theme = f["theme"]
    habitat = f["habitat"]
    food = f["food"]
    response = f["response"]
    pair = pair_noun(a, b, f["relation"])
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair}, {a.id} and {b.id}, caring for Bloom the anemone on {theme.station}. Their {parent.label_word} helps them keep the tank safe.",
        ),
        (
            "What offer did the excited child make?",
            f"{a.id} offered to give Bloom extra {food.label} before the children went to watch the stars. {a.pronoun().capitalize()} thought a bigger meal would be a kinder treat.",
        ),
        (
            f"Why did {b.id} worry about ammonia?",
            f"{b.id} knew leftover food can turn into waste in a small habitat like the {habitat.label}. That waste can become ammonia in the water, which can hurt an anemone.",
        ),
    ]
    if f["outcome"] == "averted":
        qa.append(
            (
                f"What changed {a.id}'s mind?",
                f"{a.id} listened when {b.id} explained what extra food could do to the water. The children chose the right little scoop instead, so the danger never had a chance to grow.",
            )
        )
    else:
        qa.append(
            (
                "What happened after the extra food went in?",
                "The water turned cloudy, the test strip changed color, and Bloom pulled in a little. Those signs showed the tank chemistry was shifting in a bad way.",
            )
        )
        qa.append(
            (
                f"How did their {parent.label_word} fix the problem?",
                f"{parent.label_word.capitalize()} {response.qa_text}. That lowered the ammonia danger and helped the water become clear again.",
            )
        )
    qa.append(
        (
            "How did the story end?",
            f"It ended happily with a bright feeding chart beside the tank and Bloom waving in clear water. The final image shows the children learned a safer way to care for the anemone.",
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"anemone", "feeding"}
    if f["outcome"] == "fixed":
        tags.add("ammonia")
        tags |= set(f["response"].tags)
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
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if e.role:
            bits.append(f"role={e.role}")
        if e.age:
            bits.append(f"age={e.age}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(sig[0] for sig in world.fired))}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    if params.theme not in THEMES:
        raise StoryError(f"(Unknown theme: {params.theme})")
    if params.habitat not in HABITATS:
        raise StoryError(f"(Unknown habitat: {params.habitat})")
    if params.food not in FOODS:
        raise StoryError(f"(Unknown food: {params.food})")
    if params.response not in RESPONSES:
        raise StoryError(f"(Unknown response: {params.response})")

    habitat = HABITATS[params.habitat]
    food = FOODS[params.food]
    response = RESPONSES[params.response]

    if not hazard_at_risk(habitat, food):
        raise StoryError(explain_rejection(habitat, food))
    if response.sense < SENSE_MIN:
        raise StoryError(explain_response(params.response))
    if not is_fixed(response, habitat, food) and outcome_of(params) == "bad":
        raise StoryError("(This response is too weak for the chosen ammonia problem.)")

    world = tell(
        theme=THEMES[params.theme],
        habitat=habitat,
        food=food,
        response=response,
        instigator=params.instigator,
        instigator_gender=params.instigator_gender,
        cautioner=params.cautioner,
        cautioner_gender=params.cautioner_gender,
        parent_type=params.parent,
        trait=params.trait,
        relation=params.relation,
        instigator_age=params.instigator_age,
        cautioner_age=params.cautioner_age,
        trust=params.trust,
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

    clingo_set, python_set = set(asp_valid_combos()), set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    c_sens, p_sens = set(asp_sensible()), {r.id for r in sensible_responses()}
    if c_sens == p_sens:
        print(f"OK: sensible responses match ({sorted(c_sens)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible responses: clingo={sorted(c_sens)} python={sorted(p_sens)}")

    cases = list(CURATED)
    for seed in range(40):
        try:
            p = resolve_params(build_parser().parse_args([]), random.Random(seed))
            p.seed = seed
            cases.append(p)
        except StoryError:
            continue
    bad = 0
    for params in cases:
        py = outcome_of(params)
        asp = asp_outcome(params)
        if py != asp:
            bad += 1
    if bad == 0:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("(Smoke test failed: generated empty story.)")
        print("OK: smoke test generated a normal story.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/3.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible responses: {', '.join(asp_sensible())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (theme, habitat, food) combos:\n")
        for theme, habitat, food in combos:
            print(f"  {theme:8} {habitat:12} {food}")
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
            header = f"### {p.instigator} & {p.cautioner}: {p.food} in {p.habitat} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
