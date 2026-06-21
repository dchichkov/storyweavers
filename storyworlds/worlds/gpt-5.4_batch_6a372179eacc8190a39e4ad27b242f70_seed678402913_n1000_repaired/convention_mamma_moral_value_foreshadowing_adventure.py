#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/convention_mamma_moral_value_foreshadowing_adventure.py
==================================================================================

A small storyworld about a child on an outdoor adventure with Mamma, a local
trail convention, an early hint of danger, and a lesson about patience and
listening.

Seed requirements covered
-------------------------
- Includes the words "convention" and "mamma"
- Uses foreshadowing through place details and warnings
- Carries a clear moral value: brave adventures still need good rules
- Adventure tone with paths, bridges, boardwalks, flags, and lookouts
"""

from __future__ import annotations

import argparse
import copy
import io
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
BOLDNESS_INIT = 5.0
CAUTIOUS_TRAITS = {"careful", "patient", "steady", "sensible"}


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
        female = {"girl", "mother", "mamma", "woman"}
        male = {"boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Place:
    id: str
    label: str
    route: str
    vista: str
    hazard: str
    hazard_noun: str
    foreshadow: str
    rule_need: str
    severity: int
    tags: set[str] = field(default_factory=set)


@dataclass
class ConventionRule:
    id: str
    label: str
    text: str
    action: str
    works_for: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class RescueTool:
    id: str
    label: str
    sense: int = 2
    power: int = 1
    success_text: str = ""
    fail_text: str = ""
    qa_text: str = ""
    works_for: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Goal:
    id: str
    label: str
    phrase: str
    image: str
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

    def kids(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.role in {"hero", "helper"}]

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


def _r_mishap_fear(world: World) -> list[str]:
    place = world.facts.get("place_cfg")
    child = world.facts.get("hero")
    if place is None or child is None:
        return []
    if child.meters["mishap"] < THRESHOLD:
        return []
    sig = ("fear", child.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child.memes["fear"] += 1
    for kid in world.kids():
        if kid.id != child.id:
            kid.memes["fear"] += 1
    if "mamma" in world.entities:
        world.get("mamma").memes["alert"] += 1
    return ["__mishap__"]


CAUSAL_RULES = [
    Rule(name="mishap_fear", tag="social", apply=_r_mishap_fear),
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
        for s in produced:
            world.say(s)
    return produced


PLACES = {
    "bridge": Place(
        id="bridge",
        label="the rope bridge",
        route="a rope bridge over a chattering stream",
        vista="the bright lookout flag on the other side",
        hazard="the wet planks could bounce under quick feet",
        hazard_noun="the stream below",
        foreshadow="The ropes hummed in the wind, and one loose plank gave a tiny clack.",
        rule_need="bridge",
        severity=2,
        tags={"bridge", "stream", "trail"},
    ),
    "boardwalk": Place(
        id="boardwalk",
        label="the marsh boardwalk",
        route="a narrow boardwalk over whispering reeds",
        vista="the little watchtower above the cattails",
        hazard="green moss made the boards slick",
        hazard_noun="the muddy marsh",
        foreshadow="A bead of water slid across one board and vanished between the reeds.",
        rule_need="boardwalk",
        severity=2,
        tags={"boardwalk", "marsh", "trail"},
    ),
    "steps": Place(
        id="steps",
        label="the canyon steps",
        route="a line of old stone steps cut into the canyon wall",
        vista="the brass wind-bell hanging at the top",
        hazard="gravel rolled off the edge when anything rushed",
        hazard_noun="the thorny slope below",
        foreshadow="Tiny pebbles kept clicking down the side as if the hill were clearing its throat.",
        rule_need="steps",
        severity=3,
        tags={"steps", "canyon", "trail"},
    ),
}

CONVENTIONS = {
    "one_by_one": ConventionRule(
        id="one_by_one",
        label="one at a time with a hand on the side rope",
        text="cross one at a time with one hand on the side rope",
        action="kept one hand on the side rope and crossed one careful step at a time",
        works_for={"bridge"},
        tags={"patience", "safety"},
    ),
    "stay_center": ConventionRule(
        id="stay_center",
        label="walk in the middle of the boards",
        text="walk in the middle of the boards and never hop to the edge",
        action="walked right in the middle, heel after toe, just as the painted arrows showed",
        works_for={"boardwalk"},
        tags={"patience", "safety"},
    ),
    "red_marks": ConventionRule(
        id="red_marks",
        label="step only on the red marks",
        text="step only on the red marks and keep the wall beside you",
        action="placed each foot on a red mark and kept close to the wall",
        works_for={"steps"},
        tags={"patience", "safety"},
    ),
    "run_fast": ConventionRule(
        id="run_fast",
        label="run fast before the path can wobble",
        text="run fast before the path can wobble",
        action="raced ahead in a blur",
        works_for=set(),
        tags={"unsafe"},
    ),
}

RESCUES = {
    "guide_rope": RescueTool(
        id="guide_rope",
        label="the guide rope",
        sense=3,
        power=3,
        success_text="flipped the spare guide rope across the gap and told {hero} to hold tight while she pulled {hero_obj} back to the safe boards",
        fail_text="threw the guide rope, but it slid away before {hero} could catch it",
        qa_text="used the spare guide rope to pull the child back to safety",
        works_for={"bridge", "steps"},
        tags={"rope", "rescue"},
    ),
    "walking_pole": RescueTool(
        id="walking_pole",
        label="the walking pole",
        sense=3,
        power=2,
        success_text="lay flat, stretched out the walking pole, and hooked it under {hero}'s arm so she could pull {hero_obj} back",
        fail_text="stretched out the walking pole, but the child was just too far to reach",
        qa_text="reached out with the walking pole and pulled the child back",
        works_for={"bridge", "boardwalk", "steps"},
        tags={"pole", "rescue"},
    ),
    "picnic_blanket": RescueTool(
        id="picnic_blanket",
        label="the picnic blanket",
        sense=1,
        power=1,
        success_text="threw the picnic blanket over the wet boards and somehow made a path",
        fail_text="spread the picnic blanket toward the edge, but it only soaked up water and sagged",
        qa_text="tried to use the picnic blanket",
        works_for={"boardwalk"},
        tags={"blanket"},
    ),
}

GOALS = {
    "flag": Goal(
        id="flag",
        label="flag",
        phrase="the bright lookout flag",
        image="the flag snapped in the sunlight like a happy fish tail",
        tags={"flag", "lookout"},
    ),
    "bell": Goal(
        id="bell",
        label="bell",
        phrase="the brass wind-bell",
        image="the bell winked and sang one clear note in the breeze",
        tags={"bell", "lookout"},
    ),
    "map": Goal(
        id="map",
        label="map",
        phrase="the wooden map board",
        image="the map board shone with painted rivers and little star marks",
        tags={"map", "lookout"},
    ),
}


def convention_matches(place_id: str, convention_id: str) -> bool:
    place = PLACES[place_id]
    rule = CONVENTIONS[convention_id]
    return place.rule_need in rule.works_for


def rescue_matches(place_id: str, rescue_id: str) -> bool:
    place = PLACES[place_id]
    tool = RESCUES[rescue_id]
    return place.rule_need in tool.works_for and tool.sense >= SENSE_MIN


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for place_id in sorted(PLACES):
        for convention_id in sorted(CONVENTIONS):
            if not convention_matches(place_id, convention_id):
                continue
            for rescue_id in sorted(RESCUES):
                if not rescue_matches(place_id, rescue_id):
                    continue
                for goal_id in sorted(GOALS):
                    combos.append((place_id, convention_id, rescue_id, goal_id))
    return combos


def initial_caution(trait: str) -> float:
    return 5.0 if trait in CAUTIOUS_TRAITS else 3.0


def would_obey(relation: str, hero_age: int, helper_age: int, trait: str, trust: int) -> bool:
    older_helper = relation == "siblings" and helper_age > hero_age
    authority = initial_caution(trait) + (2.0 if older_helper else 0.0) + (1.0 if trust >= 6 else 0.0)
    return authority > BOLDNESS_INIT


def is_rescued(place_id: str, rescue_id: str) -> bool:
    return RESCUES[rescue_id].power >= PLACES[place_id].severity


@dataclass
class StoryParams:
    place: str
    convention: str
    rescue: str
    goal: str
    hero: str
    hero_gender: str
    helper: str
    helper_gender: str
    parent_gender: str
    helper_trait: str
    relation: str = "siblings"
    hero_age: int = 5
    helper_age: int = 7
    trust: int = 7
    seed: Optional[int] = None


def introduce(world: World, hero: Entity, helper: Entity, mamma: Entity, place: Place, goal: Goal) -> None:
    hero.memes["wonder"] += 1
    helper.memes["wonder"] += 1
    world.say(
        f"{hero.id} and {helper.id} were on an adventure walk with Mamma, following "
        f"{place.route} toward {goal.phrase}. To {hero.id}, it felt like marching toward treasure."
    )
    world.say(f"Far ahead, they could already see {place.vista}.")


def foreshadow(world: World, place: Place) -> None:
    world.say(place.foreshadow)
    world.say(
        f"Mamma noticed it too. {place.hazard.capitalize()}, and that made the old rule feel important."
    )


def explain_convention(world: World, mamma: Entity, place: Place, rule: ConventionRule) -> None:
    mamma.memes["care"] += 1
    world.say(
        f'"On this trail, the convention is simple," Mamma said. "We always {rule.text}."'
    )
    world.say(
        f'"That is how adventurers look after one another," {mamma.pronoun()} added.'
    )


def tempt(world: World, hero: Entity, goal: Goal) -> None:
    hero.memes["boldness"] += 1
    world.say(
        f"Then a gust of wind made {goal.phrase} flash again, and {hero.id} wanted to dash forward first."
    )


def helper_warning(world: World, helper: Entity, hero: Entity, place: Place, rule: ConventionRule) -> None:
    helper.memes["caution"] += 1
    extra = ""
    if helper.memes["caution"] >= 6:
        extra = f" {helper.id} looked hard at the path and did not smile."
    world.say(
        f'"Wait," {helper.id} said. "Mamma told us the convention. If you rush here, {place.hazard}."{extra}'
    )


def obey(world: World, hero: Entity, helper: Entity, rule: ConventionRule, goal: Goal) -> None:
    hero.memes["patience"] += 1
    helper.memes["relief"] += 1
    world.say(
        f"{hero.id} took a breath, slowed down, and {rule.action}. "
        f"{helper.id} came right behind."
    )
    world.say(
        f"Nothing slipped. Nothing wobbled. A moment later they reached {goal.phrase}, and {goal.image}"
    )


def mishap(world: World, hero: Entity, place: Place, goal: Goal) -> None:
    hero.meters["mishap"] += 1
    hero.meters["distance_from_safe"] += 1
    propagate(world, narrate=False)
    if place.id == "bridge":
        world.say(
            f"But {hero.id} forgot the convention and ran. One plank tipped, {hero.pronoun()} skidded, "
            f"and one foot dropped through the space above {place.hazard_noun}."
        )
    elif place.id == "boardwalk":
        world.say(
            f"But {hero.id} forgot the convention and hopped toward the edge. The mossy board kissed "
            f"{hero.pronoun('possessive')} shoe, and {hero.pronoun()} slid down to one knee beside {place.hazard_noun}."
        )
    else:
        world.say(
            f"But {hero.id} forgot the convention and scrambled upward too fast. Gravel rolled away, and "
            f"{hero.pronoun()} slipped against the wall above {place.hazard_noun}."
        )
    world.say(
        f"The shining promise of {goal.phrase} did not feel exciting anymore. It felt far away."
    )


def alarm(world: World, helper: Entity, hero: Entity) -> None:
    helper.memes["fear"] += 1
    world.say(f'"{hero.id}!" {helper.id} cried.')


def rescue_success(world: World, mamma: Entity, hero: Entity, rescue: RescueTool) -> None:
    hero.meters["distance_from_safe"] = 0.0
    hero.meters["mishap"] = 0.0
    hero.memes["fear"] = 0.0
    hero.memes["relief"] += 1
    helper = world.facts["helper"]
    helper.memes["relief"] += 1
    mamma.memes["care"] += 1
    body = rescue.success_text.format(
        hero=hero.id,
        hero_obj=hero.pronoun("object"),
    )
    world.say(f"Mamma moved at once. She {body}.")
    world.say(
        f"When {hero.id} was safe again, {hero.pronoun()} leaned against Mamma and felt {hero.pronoun('possessive')} heart slow down."
    )


def rescue_fail(world: World, mamma: Entity, hero: Entity, rescue: RescueTool, goal: Goal) -> None:
    hero.meters["distance_from_safe"] = 0.0
    hero.memes["fear"] = 0.0
    hero.memes["sadness"] += 1
    helper = world.facts["helper"]
    helper.memes["sadness"] += 1
    body = rescue.fail_text.format(hero=hero.id, hero_obj=hero.pronoun("object"))
    world.say(f"Mamma tried quickly. She {body}.")
    world.say(
        f"Mamma still reached {hero.id} by the arm and brought {hero.pronoun('object')} back to the safe side, "
        f"but the adventure had to stop before they reached {goal.phrase}."
    )


def lesson(world: World, mamma: Entity, hero: Entity, helper: Entity, rule: ConventionRule) -> None:
    hero.memes["lesson"] += 1
    helper.memes["lesson"] += 1
    world.say(
        f'Mamma knelt between them. "Rules like that convention are not there to spoil the fun," '
        f'{mamma.pronoun()} said softly. "They are there so everyone comes home safe after the adventure."'
    )
    world.say(
        f'{hero.id} nodded. "{rule.label.capitalize()}," {hero.pronoun()} whispered, as if saying it properly might help {hero.pronoun("object")} remember.'
    )


def ending_safe(world: World, hero: Entity, helper: Entity, goal: Goal) -> None:
    hero.memes["joy"] += 1
    helper.memes["joy"] += 1
    world.say(
        f"At the top, Mamma let them look out as long as they wanted. The world below seemed huge and bright, "
        f"and {goal.image}"
    )


def ending_rescued(world: World, hero: Entity, helper: Entity, goal: Goal, rule: ConventionRule) -> None:
    hero.memes["joy"] += 1
    helper.memes["joy"] += 1
    world.say(
        f"After a quiet minute, they tried again the right way. This time {hero.id} followed the convention, "
        f"and soon they stood beside {goal.phrase} together."
    )
    world.say(f"From there, the whole path looked smaller, and the lesson looked bigger.")


def ending_turn_back(world: World, hero: Entity, helper: Entity, place: Place) -> None:
    hero.memes["comfort"] += 1
    helper.memes["comfort"] += 1
    world.say(
        f"They did not reach the lookout that day, but they walked home side by side with Mamma. "
        f"When they passed {place.label} again from the safe end, {hero.id} held the rule in {hero.pronoun('possessive')} mind like a lantern."
    )


def tell(
    place: Place,
    rule: ConventionRule,
    rescue: RescueTool,
    goal: Goal,
    hero_name: str = "Nora",
    hero_gender: str = "girl",
    helper_name: str = "Ben",
    helper_gender: str = "boy",
    parent_gender: str = "mother",
    helper_trait: str = "careful",
    relation: str = "siblings",
    hero_age: int = 5,
    helper_age: int = 7,
    trust: int = 7,
) -> World:
    world = World()
    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type=hero_gender,
        role="hero",
        age=hero_age,
        traits=["bold"],
        attrs={"relation": relation},
    ))
    helper = world.add(Entity(
        id=helper_name,
        kind="character",
        type=helper_gender,
        role="helper",
        age=helper_age,
        traits=[helper_trait],
        attrs={"relation": relation},
    ))
    mamma = world.add(Entity(
        id="Mamma",
        kind="character",
        type="mamma" if parent_gender == "mother" else "father",
        label="Mamma" if parent_gender == "mother" else "Papa",
        role="parent",
    ))
    world.add(Entity(id="path", type="path", label=place.label, tags=set(place.tags)))
    world.facts.update(
        place_cfg=place,
        rule_cfg=rule,
        rescue_cfg=rescue,
        goal_cfg=goal,
        hero=hero,
        helper=helper,
        mamma=mamma,
        relation=relation,
        trust=trust,
    )

    hero.memes["boldness"] = BOLDNESS_INIT
    helper.memes["caution"] = initial_caution(helper_trait)
    helper.memes["trust"] = float(trust)

    introduce(world, hero, helper, mamma, place, goal)
    foreshadow(world, place)

    world.para()
    explain_convention(world, mamma, place, rule)
    tempt(world, hero, goal)
    helper_warning(world, helper, hero, place, rule)

    obeyed = would_obey(relation, hero_age, helper_age, helper_trait, trust)
    world.facts["obeyed"] = obeyed

    world.para()
    if obeyed:
        obey(world, hero, helper, rule, goal)
        lesson(world, mamma, hero, helper, rule)
        world.para()
        ending_safe(world, hero, helper, goal)
        outcome = "safe"
    else:
        mishap(world, hero, place, goal)
        alarm(world, helper, hero)
        world.para()
        if is_rescued(place.id, rescue.id):
            rescue_success(world, mamma, hero, rescue)
            lesson(world, mamma, hero, helper, rule)
            world.para()
            ending_rescued(world, hero, helper, goal, rule)
            outcome = "rescued"
        else:
            rescue_fail(world, mamma, hero, rescue, goal)
            lesson(world, mamma, hero, helper, rule)
            world.para()
            ending_turn_back(world, hero, helper, place)
            outcome = "turned_back"

    world.facts.update(
        outcome=outcome,
        reached_goal=outcome in {"safe", "rescued"},
        used_rescue=(outcome != "safe"),
    )
    return world


GIRL_NAMES = ["Nora", "Lily", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Maya"]
BOY_NAMES = ["Ben", "Max", "Sam", "Leo", "Finn", "Noah", "Eli", "Theo"]
TRAITS = ["careful", "patient", "steady", "curious", "thoughtful", "sensible"]


def explain_combo_rejection(place_id: str, convention_id: str, rescue_id: str) -> str:
    place = PLACES[place_id]
    rule = CONVENTIONS[convention_id]
    rescue = RESCUES[rescue_id]
    if not convention_matches(place_id, convention_id):
        return (
            f"(No story: {rule.label} is not the right convention for {place.label}. "
            f"The trail needs a rule that actually fits the path.)"
        )
    if rescue.sense < SENSE_MIN:
        return (
            f"(Refusing rescue '{rescue_id}': it scores too low on common sense "
            f"(sense={rescue.sense} < {SENSE_MIN}).)"
        )
    if not rescue_matches(place_id, rescue_id):
        return (
            f"(No story: {rescue.label} is not a sensible rescue tool for {place.label}.)"
        )
    return "(No valid combination matches the given options.)"


def outcome_of(params: StoryParams) -> str:
    if would_obey(params.relation, params.hero_age, params.helper_age, params.helper_trait, params.trust):
        return "safe"
    return "rescued" if is_rescued(params.place, params.rescue) else "turned_back"


KNOWLEDGE = {
    "bridge": [(
        "Why do people hold a rope on a bridge?",
        "A rope helps your hands and feet work together, so you stay steady when the bridge moves."
    )],
    "boardwalk": [(
        "Why can a boardwalk be slippery?",
        "Water and moss can sit on the boards, so shoes slide more easily there."
    )],
    "steps": [(
        "Why should you slow down on steep steps?",
        "Steep steps can have loose gravel, and slow feet are safer than rushing feet."
    )],
    "rescue": [(
        "Why is listening to a safety rule part of being brave?",
        "Real bravery is not racing without thinking. Real bravery means noticing danger and choosing the safe way forward."
    )],
    "rope": [(
        "What can a rope do in a rescue?",
        "A rope can give someone something strong to hold while a grown-up pulls them back to safety."
    )],
    "pole": [(
        "What is a walking pole for?",
        "A walking pole helps a person balance on rough ground, and sometimes it can reach someone who needs help."
    )],
    "map": [(
        "What does a trail map show?",
        "A trail map shows where the path goes and helps hikers know where they are heading."
    )],
    "bell": [(
        "What does a wind-bell do?",
        "A wind-bell rings when the breeze moves it, making a light singing sound."
    )],
    "flag": [(
        "Why do lookouts sometimes have a flag?",
        "A flag is easy to see from far away, so it can mark a special place on a trail."
    )],
}


def generation_prompts(world: World) -> list[str]:
    place = world.facts["place_cfg"]
    goal = world.facts["goal_cfg"]
    outcome = world.facts["outcome"]
    hero = world.facts["hero"]
    helper = world.facts["helper"]
    rule = world.facts["rule_cfg"]
    if outcome == "safe":
        return [
            f'Write a short adventure story for a 3-to-5-year-old that includes the words "convention" and "mamma".',
            f"Tell a gentle trail adventure where {hero.id} wants to rush toward {goal.phrase}, but listens to Mamma's convention and reaches the lookout safely.",
            f'Write a story with foreshadowing, a clear moral value, and a happy ending where the rule "{rule.text}" matters.',
        ]
    if outcome == "rescued":
        return [
            f'Write a short adventure story for a 3-to-5-year-old that includes the words "convention" and "mamma".',
            f"Tell a story where {hero.id} ignores a trail convention, gets into trouble, and Mamma rescues {hero.pronoun('object')} before they try again the right way.",
            f"Write a foreshadowed adventure where {helper.id}'s warning proves true and the child learns that safe rules protect the fun.",
        ]
    return [
        f'Write a short adventure story for a 3-to-5-year-old that includes the words "convention" and "mamma".',
        f"Tell a gentle cautionary adventure where {hero.id} ignores a trail convention, Mamma brings {hero.pronoun('object')} back to safety, and the family turns back wiser than before.",
        f"Write a story with foreshadowing and moral value where the treasure at the end matters less than getting home safe together.",
    ]


def pair_noun(hero: Entity, helper: Entity, relation: str) -> str:
    if relation == "siblings":
        if hero.type == "girl" and helper.type == "girl":
            return "two sisters"
        if hero.type == "boy" and helper.type == "boy":
            return "two brothers"
        return "a brother and a sister"
    return "two friends"


def story_qa_pairs(world: World) -> list[tuple[str, str]]:
    hero = world.facts["hero"]
    helper = world.facts["helper"]
    place = world.facts["place_cfg"]
    goal = world.facts["goal_cfg"]
    rule = world.facts["rule_cfg"]
    rescue = world.facts["rescue_cfg"]
    outcome = world.facts["outcome"]
    relation = world.facts["relation"]
    pair = pair_noun(hero, helper, relation)
    qa = [
        (
            "Who is the story about?",
            f"It is about {pair}, {hero.id} and {helper.id}, on an adventure walk with Mamma. They were trying to reach {goal.phrase}."
        ),
        (
            "What was the convention on the trail?",
            f"The convention was to {rule.text}. That rule matched the danger of {place.label}, so it was there to keep everyone safe."
        ),
        (
            "How did the story foreshadow trouble?",
            f"The place gave a warning before anything bad happened: {place.foreshadow} Mamma also noticed that {place.hazard}, so the risk was hinted early."
        ),
    ]
    if outcome == "safe":
        qa.append((
            f"Why did {hero.id} stay safe?",
            f"{hero.id} listened to the warning and followed the convention instead of rushing. That patient choice kept the adventure fun and let the family reach the goal safely."
        ))
        qa.append((
            "What is the moral value of the story?",
            f"The story teaches that listening to wise rules is part of being brave. Adventure feels better when everyone comes home safe."
        ))
    elif outcome == "rescued":
        qa.append((
            f"Why did {hero.id} get into trouble, and how did Mamma help?",
            f"{hero.id} rushed instead of following the convention, and the danger Mamma had warned about really happened. Then Mamma {rescue.qa_text}, which let them calm down and try again the right way."
        ))
        qa.append((
            "What changed by the end?",
            f"At first the rule felt slow, but by the end it felt important. After the rescue, {hero.id} understood that the convention protected the adventure instead of ruining it."
        ))
    else:
        qa.append((
            f"Why did the family turn back?",
            f"They turned back because {hero.id} rushed and the path became unsafe. Mamma got everyone safe again, but the adventure had to stop before the goal."
        ))
        qa.append((
            "What is the moral value of the story?",
            f"The story teaches that safety matters more than winning a race to the treasure. A missed lookout is better than someone getting badly hurt."
        ))
    return qa


def world_knowledge_pairs(world: World) -> list[tuple[str, str]]:
    place = world.facts["place_cfg"]
    goal = world.facts["goal_cfg"]
    rescue = world.facts["rescue_cfg"]
    tags: list[str] = []
    if place.id == "bridge":
        tags.append("bridge")
    elif place.id == "boardwalk":
        tags.append("boardwalk")
    else:
        tags.append("steps")
    tags.append("rescue")
    if rescue.id == "guide_rope":
        tags.append("rope")
    if rescue.id == "walking_pole":
        tags.append("pole")
    if goal.id == "map":
        tags.append("map")
    if goal.id == "bell":
        tags.append("bell")
    if goal.id == "flag":
        tags.append("flag")
    out: list[tuple[str, str]] = []
    for tag in ["bridge", "boardwalk", "steps", "rescue", "rope", "pole", "map", "bell", "flag"]:
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
    for ent in list(world.entities.values()):
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.age:
            bits.append(f"age={ent.age}")
        if ent.traits:
            bits.append(f"traits={ent.traits}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v != ""}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {ent.id:10} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    lines.append(f"  outcome: {world.facts.get('outcome')}")
    return "\n".join(lines)


ASP_RULES = r"""
matches_place(P, C) :- place(P), convention(C), need(P, N), works_for_convention(C, N).
sensible_rescue(R)  :- rescue(R), sense(R, S), sense_min(M), S >= M.
rescue_for_place(P, R) :- place(P), rescue(R), need(P, N), works_for_rescue(R, N), sensible_rescue(R).
valid(P, C, R, G) :- place(P), goal(G), matches_place(P, C), rescue_for_place(P, R).

cautious_now(T) :- trait(T), is_cautious(T).
init_caution(5) :- trait(T), cautious_now(T).
init_caution(3) :- trait(T), not cautious_now(T).
older_helper :- relation(siblings), hero_age(H), helper_age(X), X > H.
trust_bonus(1) :- trust(V), V >= 6.
trust_bonus(0) :- trust(V), V < 6.
older_bonus(2) :- older_helper.
older_bonus(0) :- not older_helper.
authority(C + O + T) :- init_caution(C), older_bonus(O), trust_bonus(T).
obeyed :- authority(A), boldness(B), A > B.

rescued :- chosen_place(P), chosen_rescue(R), severity(P, S), power(R, PW), PW >= S.

outcome(safe) :- obeyed.
outcome(rescued) :- not obeyed, rescued.
outcome(turned_back) :- not obeyed, not rescued.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for place_id, place in PLACES.items():
        lines.append(asp.fact("place", place_id))
        lines.append(asp.fact("need", place_id, place.rule_need))
        lines.append(asp.fact("severity", place_id, place.severity))
    for convention_id, rule in CONVENTIONS.items():
        lines.append(asp.fact("convention", convention_id))
        for need in sorted(rule.works_for):
            lines.append(asp.fact("works_for_convention", convention_id, need))
    for rescue_id, rescue in RESCUES.items():
        lines.append(asp.fact("rescue", rescue_id))
        lines.append(asp.fact("sense", rescue_id, rescue.sense))
        lines.append(asp.fact("power", rescue_id, rescue.power))
        for need in sorted(rescue.works_for):
            lines.append(asp.fact("works_for_rescue", rescue_id, need))
    for goal_id in GOALS:
        lines.append(asp.fact("goal", goal_id))
    for trait in sorted(CAUTIOUS_TRAITS):
        lines.append(asp.fact("is_cautious", trait))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    lines.append(asp.fact("boldness", int(BOLDNESS_INIT)))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible_rescues() -> list[str]:
    import asp
    model = asp.one_model(asp_program("", "#show sensible_rescue/1."))
    return sorted(x for (x,) in asp.atoms(model, "sensible_rescue"))


def asp_outcome(params: StoryParams) -> str:
    import asp
    extra = "\n".join([
        asp.fact("chosen_place", params.place),
        asp.fact("chosen_rescue", params.rescue),
        asp.fact("relation", params.relation),
        asp.fact("hero_age", params.hero_age),
        asp.fact("helper_age", params.helper_age),
        asp.fact("trait", params.helper_trait),
        asp.fact("trust", params.trust),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0

    py_valid = set(valid_combos())
    asp_valid = set(asp_valid_combos())
    if py_valid == asp_valid:
        print(f"OK: valid_combos() matches ASP ({len(py_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if py_valid - asp_valid:
            print("  only in python:", sorted(py_valid - asp_valid))
        if asp_valid - py_valid:
            print("  only in asp:", sorted(asp_valid - py_valid))

    py_sensible = {rid for rid, tool in RESCUES.items() if tool.sense >= SENSE_MIN}
    asp_sensible = set(asp_sensible_rescues())
    if py_sensible == asp_sensible:
        print(f"OK: sensible rescues match ({sorted(py_sensible)}).")
    else:
        rc = 1
        print("MISMATCH in sensible rescues:")
        print("  python:", sorted(py_sensible))
        print("  asp:", sorted(asp_sensible))

    cases = list(CURATED)
    for seed in range(30):
        rng = random.Random(seed)
        try:
            params = resolve_params(build_parser().parse_args([]), rng)
        except StoryError:
            continue
        cases.append(params)

    bad = 0
    for params in cases:
        if outcome_of(params) != asp_outcome(params):
            bad += 1
    if bad == 0:
        print(f"OK: outcomes match on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("Smoke test generated an empty story.")
        buf = io.StringIO()
        old = sys.stdout
        sys.stdout = buf
        try:
            emit(sample, trace=False, qa=True, header="smoke")
        finally:
            sys.stdout = old
        print("OK: generate/emit smoke test passed.")
    except Exception as err:  # pragma: no cover
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


CURATED = [
    StoryParams(
        place="bridge",
        convention="one_by_one",
        rescue="guide_rope",
        goal="flag",
        hero="Nora",
        hero_gender="girl",
        helper="Ben",
        helper_gender="boy",
        parent_gender="mother",
        helper_trait="careful",
        relation="siblings",
        hero_age=5,
        helper_age=7,
        trust=8,
    ),
    StoryParams(
        place="boardwalk",
        convention="stay_center",
        rescue="walking_pole",
        goal="map",
        hero="Max",
        hero_gender="boy",
        helper="Mia",
        helper_gender="girl",
        parent_gender="mother",
        helper_trait="curious",
        relation="friends",
        hero_age=6,
        helper_age=6,
        trust=4,
    ),
    StoryParams(
        place="steps",
        convention="red_marks",
        rescue="walking_pole",
        goal="bell",
        hero="Ava",
        hero_gender="girl",
        helper="Leo",
        helper_gender="boy",
        parent_gender="mother",
        helper_trait="patient",
        relation="siblings",
        hero_age=6,
        helper_age=5,
        trust=3,
    ),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Adventure storyworld with Mamma, a trail convention, foreshadowing, and a moral lesson."
    )
    ap.add_argument("--place", choices=sorted(PLACES))
    ap.add_argument("--convention", choices=sorted(CONVENTIONS))
    ap.add_argument("--rescue", choices=sorted(RESCUES))
    ap.add_argument("--goal", choices=sorted(GOALS))
    ap.add_argument("--parent", choices=["mother"], default=None)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible sampling")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid combinations from the ASP twin")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_child(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [name for name in pool if name != avoid]
    return rng.choice(choices), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.convention and not convention_matches(args.place, args.convention):
        rescue_id = args.rescue or next(iter(RESCUES))
        raise StoryError(explain_combo_rejection(args.place, args.convention, rescue_id))
    if args.place and args.rescue:
        if RESCUES[args.rescue].sense < SENSE_MIN or not rescue_matches(args.place, args.rescue):
            convention_id = args.convention or next(iter(CONVENTIONS))
            raise StoryError(explain_combo_rejection(args.place, convention_id, args.rescue))

    combos = [
        combo for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.convention is None or combo[1] == args.convention)
        and (args.rescue is None or combo[2] == args.rescue)
        and (args.goal is None or combo[3] == args.goal)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, convention_id, rescue_id, goal_id = rng.choice(sorted(combos))
    hero_name, hero_gender = _pick_child(rng)
    helper_name, helper_gender = _pick_child(rng, avoid=hero_name)
    helper_trait = rng.choice(TRAITS)
    relation = rng.choice(["siblings", "friends"])
    ages = rng.sample([4, 5, 6, 7], 2)
    hero_age, helper_age = ages[0], ages[1]
    trust = rng.randint(2, 9)
    return StoryParams(
        place=place_id,
        convention=convention_id,
        rescue=rescue_id,
        goal=goal_id,
        hero=hero_name,
        hero_gender=hero_gender,
        helper=helper_name,
        helper_gender=helper_gender,
        parent_gender="mother",
        helper_trait=helper_trait,
        relation=relation,
        hero_age=hero_age,
        helper_age=helper_age,
        trust=trust,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"(Unknown place: {params.place})")
    if params.convention not in CONVENTIONS:
        raise StoryError(f"(Unknown convention: {params.convention})")
    if params.rescue not in RESCUES:
        raise StoryError(f"(Unknown rescue: {params.rescue})")
    if params.goal not in GOALS:
        raise StoryError(f"(Unknown goal: {params.goal})")
    if not convention_matches(params.place, params.convention):
        raise StoryError(explain_combo_rejection(params.place, params.convention, params.rescue))
    if not rescue_matches(params.place, params.rescue):
        raise StoryError(explain_combo_rejection(params.place, params.convention, params.rescue))

    world = tell(
        place=PLACES[params.place],
        rule=CONVENTIONS[params.convention],
        rescue=RESCUES[params.rescue],
        goal=GOALS[params.goal],
        hero_name=params.hero,
        hero_gender=params.hero_gender,
        helper_name=params.helper,
        helper_gender=params.helper_gender,
        parent_gender=params.parent_gender,
        helper_trait=params.helper_trait,
        relation=params.relation,
        hero_age=params.hero_age,
        helper_age=params.helper_age,
        trust=params.trust,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa_pairs(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_pairs(world)],
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
        print(asp_program("", "#show valid/4.\n#show sensible_rescue/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        sensible = asp_sensible_rescues()
        print(f"sensible rescues: {', '.join(sensible)}\n")
        print(f"{len(combos)} compatible (place, convention, rescue, goal) combos:\n")
        for place_id, convention_id, rescue_id, goal_id in combos:
            print(f"  {place_id:10} {convention_id:12} {rescue_id:12} {goal_id}")
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
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero} at {p.place} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
