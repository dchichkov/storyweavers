#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/analysis_gust_campground_friendship_superhero_story.py
=================================================================================

A standalone storyworld for a tiny "campground superhero friendship" domain.

Premise
-------
Two friends at a campground are playing superhero rescue. A sudden gust snatches
an important play object away. One child wants to make a daring leap, but the
other pauses for a little analysis and helps choose a safer plan. Depending on
their trust and patience, they either solve the problem right away or after a
small oops moment. Either way, the ending proves that friendship and thinking
together are part of being a hero.

Run it
------
    python storyworlds/worlds/gpt-5.4/analysis_gust_campground_friendship_superhero_story.py
    python storyworlds/worlds/gpt-5.4/analysis_gust_campground_friendship_superhero_story.py --item map --snag roof
    python storyworlds/worlds/gpt-5.4/analysis_gust_campground_friendship_superhero_story.py --method teamwork
    python storyworlds/worlds/gpt-5.4/analysis_gust_campground_friendship_superhero_story.py --all
    python storyworlds/worlds/gpt-5.4/analysis_gust_campground_friendship_superhero_story.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/analysis_gust_campground_friendship_superhero_story.py --trace --seed 22
    python storyworlds/worlds/gpt-5.4/analysis_gust_campground_friendship_superhero_story.py --verify
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
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "ranger_woman"}
        male = {"boy", "father", "dad", "man", "ranger_man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {
            "mother": "mom",
            "father": "dad",
            "ranger_woman": "ranger",
            "ranger_man": "ranger",
        }.get(self.type, self.type)


@dataclass
class Mission:
    id: str
    team_name: str
    opening: str
    mission_line: str
    finish_line: str


@dataclass
class ItemConfig:
    id: str
    label: str
    phrase: str
    importance: str
    weight: str = "light"
    tags: set[str] = field(default_factory=set)


@dataclass
class SnagConfig:
    id: str
    label: str
    the: str
    height: int
    surface: str
    place_line: str
    danger_line: str
    tags: set[str] = field(default_factory=set)

    @property
    def The(self) -> str:
        return self.the[0].upper() + self.the[1:]


@dataclass
class MethodConfig:
    id: str
    label: str
    phrase: str
    sense: int
    helper: str
    success_line: str
    qa_line: str
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


def _r_gust_alarm(world: World) -> list[str]:
    item = world.entities.get("item")
    if item is None or item.meters["displaced"] < THRESHOLD:
        return []
    sig = ("gust_alarm",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    for ent in list(world.entities.values()):
        if ent.role in {"hero", "friend"}:
            ent.memes["worry"] += 1
    return []


def _r_leap_oops(world: World) -> list[str]:
    hero = world.entities.get("hero")
    if hero is None or hero.meters["wobble"] < THRESHOLD:
        return []
    sig = ("leap_oops",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["embarrassed"] += 1
    friend = world.entities.get("friend")
    if friend is not None:
        friend.memes["care"] += 1
    return []


def _r_plan_bonds(world: World) -> list[str]:
    if world.facts.get("plan_chosen") != 1:
        return []
    sig = ("plan_bonds",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    for ent in list(world.entities.values()):
        if ent.role in {"hero", "friend"}:
            ent.memes["trust"] += 1
            ent.memes["teamwork"] += 1
    return []


CAUSAL_RULES = [
    Rule(name="gust_alarm", tag="emotional", apply=_r_gust_alarm),
    Rule(name="leap_oops", tag="emotional", apply=_r_leap_oops),
    Rule(name="plan_bonds", tag="social", apply=_r_plan_bonds),
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


MISSIONS = {
    "stormwatch": Mission(
        id="stormwatch",
        team_name="Stormwatch Friends",
        opening="The pine trees around the campground swayed softly, and the two friends decided the trails needed superhero guards.",
        mission_line='"Stormwatch Friends, on patrol!"',
        finish_line="They marched past the tents like true campground heroes, a little wiser and much closer than before.",
    ),
    "star_rescue": Mission(
        id="star_rescue",
        team_name="Star Rescue Squad",
        opening="Near the picnic tables at the campground, the two friends invented a superhero squad that protected every tiny treasure under the sky.",
        mission_line='"Star Rescue Squad, ready!"',
        finish_line="They crossed the loop road like tiny heroes after sunset, carrying their rescued treasure and their new plan together.",
    ),
    "trail_guard": Mission(
        id="trail_guard",
        team_name="Trail Guard Team",
        opening="Beside the fire ring at the campground, the two friends pretended they were superheroes keeping the whole trail safe.",
        mission_line='"Trail Guard Team, to the rescue!"',
        finish_line="The campground seemed friendlier now, as if even the tall trees trusted them to be careful heroes.",
    ),
}

ITEMS = {
    "map": ItemConfig(
        id="map",
        label="paper map",
        phrase="a crinkly paper map with a red star on it",
        importance="It showed their secret superhero route between the tents and the lake path.",
        tags={"map", "paper"},
    ),
    "cape": ItemConfig(
        id="cape",
        label="red cape",
        phrase="a little red cape clipped with a shiny clothespin",
        importance="It made whoever wore it feel brave enough to rescue anything.",
        tags={"cape", "cloth"},
    ),
    "badge": ItemConfig(
        id="badge",
        label="hero badge",
        phrase="a cardboard hero badge covered in silver stars",
        importance="The two friends had made it together that morning and promised to share it.",
        tags={"badge", "cardboard"},
    ),
}

SNAGS = {
    "branch": SnagConfig(
        id="branch",
        label="pine branch",
        the="the low pine branch",
        height=2,
        surface="scratchy",
        place_line="The gust twirled it upward until it caught on a low pine branch beside the campsite.",
        danger_line="The branch was high enough to tempt a jump, but scratchy needles and loose roots waited underneath.",
        tags={"tree", "branch"},
    ),
    "puddle": SnagConfig(
        id="puddle",
        label="puddle edge",
        the="the muddy puddle edge",
        height=1,
        surface="muddy",
        place_line="The gust slapped it sideways and dropped it near a muddy puddle edge by the water pump.",
        danger_line="The mud looked slick, and one wrong step would smear the treasure.",
        tags={"puddle", "mud"},
    ),
    "roof": SnagConfig(
        id="roof",
        label="picnic shelter roof",
        the="the picnic shelter roof",
        height=3,
        surface="high",
        place_line="The gust lofted it up and over the picnic table until it landed on the edge of the picnic shelter roof.",
        danger_line="That roof was far too high for children, no matter how superhero they felt.",
        tags={"roof", "shelter"},
    ),
}

METHODS = {
    "stick": MethodConfig(
        id="stick",
        label="walking stick",
        phrase="a long walking stick",
        sense=2,
        helper="the two friends",
        success_line="tipped a long walking stick just right and guided the lost item safely down",
        qa_line="used a long walking stick to guide it down safely",
        tags={"stick", "tool"},
    ),
    "teamwork": MethodConfig(
        id="teamwork",
        label="teamwork reach",
        phrase="a careful teamwork reach",
        sense=2,
        helper="the two friends",
        success_line="held hands, braced their boots, and made one careful teamwork reach instead of a wild leap",
        qa_line="used a careful teamwork reach instead of jumping",
        tags={"teamwork", "friendship"},
    ),
    "ranger": MethodConfig(
        id="ranger",
        label="park ranger grabber",
        phrase="the ranger's long grabber",
        sense=3,
        helper="a park ranger",
        success_line="asked the park ranger for help, and the ranger used a long grabber to lift the lost item down",
        qa_line="asked the park ranger, who used a long grabber to get it down",
        tags={"ranger", "helper"},
    ),
}

SUITABLE = {
    ("branch", "stick"),
    ("branch", "ranger"),
    ("puddle", "stick"),
    ("puddle", "teamwork"),
    ("roof", "ranger"),
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Anna", "Maya", "Nora", "Rose"]
BOY_NAMES = ["Tom", "Ben", "Max", "Sam", "Leo", "Jack", "Finn", "Noah", "Eli", "Theo"]
TRAITS = ["brave", "bouncy", "careful", "curious", "thoughtful", "steady"]
ANALYSIS_TRAITS = {"careful", "thoughtful", "steady"}


def suitable_method(snag_id: str, method_id: str) -> bool:
    return (snag_id, method_id) in SUITABLE and METHODS[method_id].sense >= SENSE_MIN


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for mission_id in MISSIONS:
        for item_id in ITEMS:
            for snag_id in SNAGS:
                for method_id in METHODS:
                    if suitable_method(snag_id, method_id):
                        combos.append((mission_id, item_id, snag_id, method_id))
    return combos


def initial_analysis(trait: str) -> int:
    return 5 if trait in ANALYSIS_TRAITS else 3


def would_listen(friend_trait: str, trust: int) -> bool:
    return initial_analysis(friend_trait) + trust >= 10


def predict_oops(world: World, snag_id: str) -> dict:
    sim = world.copy()
    hero = sim.get("hero")
    hero.meters["wobble"] += 1 if snag_id in {"puddle", "roof", "branch"} else 0
    if snag_id == "roof":
        hero.meters["too_high"] += 1
    propagate(sim, narrate=False)
    return {
        "wobble": hero.meters["wobble"] >= THRESHOLD,
        "too_high": hero.meters["too_high"] >= THRESHOLD,
    }


def introduce(world: World, mission: Mission, hero: Entity, friend: Entity, item: Entity) -> None:
    world.say(
        f"{mission.opening} {hero.id} wore {item.phrase if item.label != 'hero badge' else 'the hero badge on a string'}, "
        f"and {friend.id} trotted beside {hero.pronoun('object')} as {hero.pronoun('possessive')} best teammate."
    )
    world.say(f'{mission.mission_line} shouted {hero.id}. "{mission.team_name} never quits!"')
    world.say(item.attrs["importance"])


def gust_snatches(world: World, hero: Entity, friend: Entity, item: Entity, snag: SnagConfig) -> None:
    item.meters["displaced"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Then a sudden gust rushed through the campground and yanked at the {item.label}. "
        f"{snag.place_line}"
    )
    world.say(f'{friend.id} gasped. "Our mission piece!"')
    world.say(snag.danger_line)


def reckless_idea(world: World, hero: Entity, snag: SnagConfig) -> None:
    hero.memes["bravado"] += 1
    jump_line = {
        "branch": f'"I can spring up and grab it!" said {hero.id}.',
        "puddle": f'"I can dash across the mud and snatch it!" said {hero.id}.',
        "roof": f'"I can climb up there like a sky hero!" said {hero.id}.',
    }[snag.id]
    world.say(jump_line)


def analysis_warning(world: World, friend: Entity, hero: Entity, item: Entity, snag: SnagConfig) -> None:
    pred = predict_oops(world, snag.id)
    friend.memes["analysis"] += 1
    world.facts["predicted_wobble"] = pred["wobble"]
    world.facts["predicted_too_high"] = pred["too_high"]
    extra = ""
    if pred["too_high"]:
        extra = " The roof was too high for children."
    elif pred["wobble"]:
        extra = " A wild leap would end in a wobble, not a rescue."
    world.say(
        f'{friend.id} touched {hero.id}\'s sleeve. "Wait. Let\'s do a little analysis," '
        f'{friend.pronoun()} said. "The wind is still pushing, and {snag.the} is tricky.{extra} '
        f'Heroes use their heads first."'
    )


def direct_listen(world: World, hero: Entity, friend: Entity) -> None:
    hero.memes["calm"] += 1
    friend.memes["relief"] += 1
    world.say(
        f"{hero.id} took a breath and looked again. The brave idea was still there, "
        f"but now the careful idea was louder."
    )
    world.say(f'"You are right," said {hero.id}. "Let\'s rescue it together."')


def oops_attempt(world: World, hero: Entity, friend: Entity, snag: SnagConfig) -> None:
    hero.meters["wobble"] += 1
    if snag.id == "roof":
        hero.meters["too_high"] += 1
    propagate(world, narrate=False)
    if snag.id == "puddle":
        world.say(
            f"{hero.id} took one fast step toward the mud, but {hero.pronoun()} skidded and windmilled "
            f"{hero.pronoun('possessive')} arms before stopping."
        )
    elif snag.id == "branch":
        world.say(
            f"{hero.id} bent {hero.pronoun('possessive')} knees for a big superhero bounce, "
            f"but a root rolled under one shoe and made {hero.pronoun('object')} wobble."
        )
    else:
        world.say(
            f"{hero.id} hurried to the picnic table bench, then froze. Up close, the roof looked much higher "
            f"than it had from the ground."
        )
    world.say(
        f"{friend.id} stayed close instead of laughing. That made {hero.id} stop pretending for a moment and really think."
    )


def choose_plan(world: World, method: MethodConfig) -> None:
    world.facts["plan_chosen"] = 1
    propagate(world, narrate=False)
    if method.id == "stick":
        world.say(
            "Together they searched beside the firewood stack until they found a long walking stick that could reach without climbing."
        )
    elif method.id == "teamwork":
        world.say(
            "They planted their boots on the dry ground and promised to move slowly, like a real superhero team."
        )
    else:
        world.say(
            'Instead of trying to be bigger than the problem, they asked for help like wise heroes. A park ranger nearby looked up from a map and smiled.'
        )


def recover_item(world: World, hero: Entity, friend: Entity, item: Entity, method: MethodConfig) -> None:
    item.meters["safe"] += 1
    item.meters["displaced"] = 0.0
    hero.memes["joy"] += 1
    friend.memes["joy"] += 1
    hero.memes["friendship"] += 1
    friend.memes["friendship"] += 1
    world.say(
        f"{method.helper.capitalize()} {method.success_line}. The {item.label} came down without tearing or splashing."
    )
    world.say(
        f"{hero.id} brushed it off and grinned at {friend.id}. The rescue felt even better because they had done it as friends."
    )


def ending(world: World, mission: Mission, hero: Entity, friend: Entity, item: Entity) -> None:
    if item.label == "paper map":
        proof = "This time the map stayed tucked safely between them, and both of them checked the breeze before running on."
    elif item.label == "red cape":
        proof = "This time they clipped the cape snugly and took turns wearing it, because heroes look after shared things."
    else:
        proof = "This time the badge rode in the middle between them, swinging safely while they walked."
    world.say(
        f'Soon {friend.id} laughed. "Superheroes with friendship powers are better than superheroes who only leap."'
    )
    world.say(
        f'{hero.id} nodded. "And analysis powers," {hero.pronoun()} added.'
    )
    world.say(proof)
    world.say(mission.finish_line)


def tell(
    mission: Mission,
    item_cfg: ItemConfig,
    snag: SnagConfig,
    method: MethodConfig,
    hero_name: str = "Lily",
    hero_gender: str = "girl",
    friend_name: str = "Tom",
    friend_gender: str = "boy",
    parent_type: str = "mother",
    friend_trait: str = "careful",
    trust: int = 5,
) -> World:
    world = World()
    hero = world.add(Entity(
        id="hero",
        kind="character",
        type=hero_gender,
        label=hero_name,
        phrase=hero_name,
        role="hero",
        traits=["bold"],
        attrs={"name": hero_name},
    ))
    friend = world.add(Entity(
        id="friend",
        kind="character",
        type=friend_gender,
        label=friend_name,
        phrase=friend_name,
        role="friend",
        traits=[friend_trait],
        attrs={"name": friend_name},
    ))
    parent = world.add(Entity(
        id="parent",
        kind="character",
        type=parent_type,
        label="the grown-up at camp",
        phrase="the grown-up at camp",
        role="parent",
    ))
    item = world.add(Entity(
        id="item",
        kind="thing",
        type="item",
        label=item_cfg.label,
        phrase=item_cfg.phrase,
        role="item",
        attrs={"importance": item_cfg.importance},
        tags=set(item_cfg.tags),
    ))

    hero.memes["trust"] = float(trust)
    friend.memes["analysis"] = float(initial_analysis(friend_trait))
    world.facts["campground"] = "campground"

    introduce(world, mission, hero, friend, item)

    world.para()
    gust_snatches(world, hero, friend, item, snag)
    reckless_idea(world, hero, snag)
    analysis_warning(world, friend, hero, item, snag)

    listened = would_listen(friend_trait, trust)
    world.facts["listened"] = listened

    world.para()
    if listened:
        direct_listen(world, hero, friend)
    else:
        oops_attempt(world, hero, friend, snag)
        world.say(f'"Okay," said {hero.id} at last. "No more wild leaps. What is the smart rescue?"')

    choose_plan(world, method)
    recover_item(world, hero, friend, item, method)

    world.para()
    ending(world, mission, hero, friend, item)

    outcome = "direct" if listened else "oops_then_fix"
    world.facts.update(
        mission=mission,
        hero=hero,
        friend=friend,
        parent=parent,
        item=item,
        item_cfg=item_cfg,
        snag=snag,
        method=method,
        outcome=outcome,
        trust=trust,
        friend_trait=friend_trait,
        friendship_grew=hero.memes["friendship"] >= THRESHOLD,
    )
    return world


@dataclass
class StoryParams:
    mission: str
    item: str
    snag: str
    method: str
    hero_name: str
    hero_gender: str
    friend_name: str
    friend_gender: str
    parent: str
    friend_trait: str
    trust: int = 5
    seed: Optional[int] = None


KNOWLEDGE = {
    "gust": [
        (
            "What is a gust?",
            "A gust is a quick, strong push of wind. It can grab light things and move them suddenly."
        )
    ],
    "analysis": [
        (
            "What does analysis mean?",
            "Analysis means stopping to think carefully about what is happening. It helps you notice the problem before you choose what to do."
        )
    ],
    "friendship": [
        (
            "How can friendship help in a problem?",
            "A good friend can stay calm, share ideas, and help you make a safer choice. Working together often solves problems better than showing off."
        )
    ],
    "campground": [
        (
            "What is a campground?",
            "A campground is a place where people stay outside in tents or campers. It often has picnic tables, trails, and shared places like water pumps or shelters."
        )
    ],
    "ranger": [
        (
            "What does a park ranger do?",
            "A park ranger helps care for a park or campground and keeps people safe. Rangers can answer questions and help when something is too high or tricky."
        )
    ],
    "stick": [
        (
            "Why can a long stick help reach something?",
            "A long stick lets you reach farther without climbing. That can make a rescue safer when an object is only a little too high."
        )
    ],
    "teamwork": [
        (
            "What is teamwork?",
            "Teamwork is when people help each other on the same job. They move carefully together instead of each person acting alone."
        )
    ],
    "map": [
        (
            "What is a paper map for?",
            "A paper map shows where places are and how to get from one spot to another. It can help people plan a route."
        )
    ],
    "cape": [
        (
            "What is a cape?",
            "A cape is a piece of cloth that hangs from your shoulders. In pretend play, children often wear one to feel like superheroes."
        )
    ],
    "badge": [
        (
            "What is a badge?",
            "A badge is a small sign or token that shows a role or team. Children can make pretend badges for games."
        )
    ],
}
KNOWLEDGE_ORDER = ["gust", "analysis", "friendship", "campground", "ranger", "stick", "teamwork", "map", "cape", "badge"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    item_cfg = f["item_cfg"]
    snag = f["snag"]
    method = f["method"]
    base = (
        f'Write a superhero-style friendship story for a 3-to-5-year-old set at a campground. '
        f'Include the words "analysis" and "gust".'
    )
    return [
        base,
        f"Tell a gentle story where {hero.attrs['name']} and {friend.attrs['name']} are superhero friends at a campground, "
        f"a gust blows away {item_cfg.phrase}, and they solve the problem with careful thinking.",
        f"Write a child-facing story where a daring leap looks tempting near {snag.the}, but the friends choose {method.phrase} instead and end happily.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    item_cfg = f["item_cfg"]
    snag = f["snag"]
    method = f["method"]
    hero_name = hero.attrs["name"]
    friend_name = friend.attrs["name"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about two friends at a campground, {hero_name} and {friend_name}, who were pretending to be superheroes together."
        ),
        (
            "What problem did the friends have?",
            f"A sudden gust blew away the {item_cfg.label} and left it at {snag.the}. That mattered because {item_cfg.importance}"
        ),
        (
            f"Why did {friend_name} say they needed analysis?",
            f"{friend_name} could see that {snag.the} was tricky and that a wild leap might go wrong. The analysis helped the friends think about wind, height, and footing before acting."
        ),
    ]
    if f["outcome"] == "direct":
        qa.append(
            (
                f"What did {hero_name} do after hearing {friend_name}'s warning?",
                f"{hero_name} listened right away and chose the careful plan. That showed bravery was changing into teamwork."
            )
        )
    else:
        qa.append(
            (
                f"Did {hero_name} listen right away?",
                f"Not at first. {hero_name} made a quick try, felt how tricky the spot was, and then listened to {friend_name}'s safer idea."
            )
        )
    qa.append(
        (
            "How did they get the lost item back?",
            f"They {method.qa_line}. The rescue worked because the plan matched the real problem instead of only looking dramatic."
        )
    )
    qa.append(
        (
            "How did friendship matter in the ending?",
            f"The friends stayed kind to each other while they solved the problem. By the end, they felt closer because they had rescued the item together."
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"gust", "analysis", "friendship", "campground"}
    tags |= set(f["method"].tags)
    tags |= set(f["item_cfg"].tags)
    if f["method"].id == "ranger":
        tags.add("ranger")
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
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {ent.id:8} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *rest in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        mission="stormwatch",
        item="map",
        snag="branch",
        method="stick",
        hero_name="Lily",
        hero_gender="girl",
        friend_name="Tom",
        friend_gender="boy",
        parent="mother",
        friend_trait="careful",
        trust=6,
    ),
    StoryParams(
        mission="star_rescue",
        item="cape",
        snag="puddle",
        method="teamwork",
        hero_name="Max",
        hero_gender="boy",
        friend_name="Mia",
        friend_gender="girl",
        parent="father",
        friend_trait="thoughtful",
        trust=3,
    ),
    StoryParams(
        mission="trail_guard",
        item="badge",
        snag="roof",
        method="ranger",
        hero_name="Zoe",
        hero_gender="girl",
        friend_name="Sam",
        friend_gender="boy",
        parent="mother",
        friend_trait="steady",
        trust=5,
    ),
]


def explain_rejection(snag_id: str, method_id: str) -> str:
    snag = SNAGS[snag_id]
    method = METHODS[method_id]
    return (
        f"(No story: {method.label} is not a reasonable way to rescue something from {snag.the}. "
        f"Pick a method that matches the height and the place.)"
    )


def validate_params(params: StoryParams) -> None:
    if params.mission not in MISSIONS:
        raise StoryError(f"(Unknown mission: {params.mission})")
    if params.item not in ITEMS:
        raise StoryError(f"(Unknown item: {params.item})")
    if params.snag not in SNAGS:
        raise StoryError(f"(Unknown snag: {params.snag})")
    if params.method not in METHODS:
        raise StoryError(f"(Unknown method: {params.method})")
    if params.parent not in {"mother", "father"}:
        raise StoryError(f"(Unknown parent type: {params.parent})")
    if not suitable_method(params.snag, params.method):
        raise StoryError(explain_rejection(params.snag, params.method))


ASP_RULES = r"""
sensible_method(M) :- method(M), sense(M, S), sense_min(K), S >= K.
valid(Mis, I, Sg, Md) :- mission(Mis), item(I), snag(Sg), method(Md),
                         suitable(Sg, Md), sensible_method(Md).

strong_analysis(T) :- trait(T), analysis_score(T, A), A >= 5.
listened :- chosen_trait(T), analysis_score(T, A), trust(V), A + V >= 10.
outcome(direct) :- listened.
outcome(oops_then_fix) :- not listened.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for mission_id in MISSIONS:
        lines.append(asp.fact("mission", mission_id))
    for item_id in ITEMS:
        lines.append(asp.fact("item", item_id))
    for snag_id in SNAGS:
        lines.append(asp.fact("snag", snag_id))
    for method_id, method in METHODS.items():
        lines.append(asp.fact("method", method_id))
        lines.append(asp.fact("sense", method_id, method.sense))
    for snag_id, method_id in sorted(SUITABLE):
        lines.append(asp.fact("suitable", snag_id, method_id))
    for trait in sorted(TRAITS):
        lines.append(asp.fact("trait", trait))
        lines.append(asp.fact("analysis_score", trait, initial_analysis(trait)))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    scenario = "\n".join(
        [
            asp.fact("chosen_trait", params.friend_trait),
            asp.fact("trust", params.trust),
        ]
    )
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def outcome_of(params: StoryParams) -> str:
    return "direct" if would_listen(params.friend_trait, params.trust) else "oops_then_fix"


def asp_verify() -> int:
    rc = 0
    c_set = set(asp_valid_combos())
    p_set = set(valid_combos())
    if c_set == p_set:
        print(f"OK: ASP gate matches valid_combos() ({len(c_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if c_set - p_set:
            print("  only in clingo:", sorted(c_set - p_set))
        if p_set - c_set:
            print("  only in python:", sorted(p_set - c_set))

    cases = list(CURATED)
    for seed in range(25):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
        except StoryError:
            continue
        params.seed = seed
        cases.append(params)
    mismatches = [p for p in cases if asp_outcome(p) != outcome_of(p)]
    if not mismatches:
        print(f"OK: ASP outcome matches Python on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {len(mismatches)} outcome differences.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("(Smoke test failed: empty story.)")
        emit(sample, trace=False, qa=False, header="")
        print("OK: smoke test generation and emit succeeded.")
    except Exception as err:  # pragma: no cover - explicit verify guard
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(conflict_handler="resolve",
        description="Story world sketch: superhero friendship at a campground, with a gust, some analysis, and a safe rescue."
    )
    ap.add_argument("--mission", choices=sorted(MISSIONS))
    ap.add_argument("--item", choices=sorted(ITEMS))
    ap.add_argument("--snag", choices=sorted(SNAGS))
    ap.add_argument("--method", choices=sorted(METHODS))
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible stories derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner matches the Python logic")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = [n for n in (GIRL_NAMES if gender == "girl" else BOY_NAMES) if n != avoid]
    return rng.choice(pool), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.snag and args.method and not suitable_method(args.snag, args.method):
        raise StoryError(explain_rejection(args.snag, args.method))

    combos = [
        combo for combo in valid_combos()
        if (args.mission is None or combo[0] == args.mission)
        and (args.item is None or combo[1] == args.item)
        and (args.snag is None or combo[2] == args.snag)
        and (args.method is None or combo[3] == args.method)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    mission_id, item_id, snag_id, method_id = rng.choice(sorted(combos))
    hero_name, hero_gender = _pick_name(rng)
    friend_name, friend_gender = _pick_name(rng, avoid=hero_name)
    parent = args.parent or rng.choice(["mother", "father"])
    friend_trait = rng.choice(TRAITS)
    trust = rng.randint(2, 7)
    params = StoryParams(
        mission=mission_id,
        item=item_id,
        snag=snag_id,
        method=method_id,
        hero_name=hero_name,
        hero_gender=hero_gender,
        friend_name=friend_name,
        friend_gender=friend_gender,
        parent=parent,
        friend_trait=friend_trait,
        trust=trust,
    )
    validate_params(params)
    return params


def generate(params: StoryParams) -> StorySample:
    validate_params(params)
    world = tell(
        mission=MISSIONS[params.mission],
        item_cfg=ITEMS[params.item],
        snag=SNAGS[params.snag],
        method=METHODS[params.method],
        hero_name=params.hero_name,
        hero_gender=params.hero_gender,
        friend_name=params.friend_name,
        friend_gender=params.friend_gender,
        parent_type=params.parent,
        friend_trait=params.friend_trait,
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/4.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (mission, item, snag, method) combos:\n")
        for mission_id, item_id, snag_id, method_id in combos:
            print(f"  {mission_id:12} {item_id:6} {snag_id:7} {method_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

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
            header = f"### {p.hero_name} & {p.friend_name}: {p.item} at {p.snag} ({outcome_of(p)})"
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
