#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/rapids_kindness_curiosity_heartwarming.py
====================================================================

A standalone storyworld about curiosity, kindness, and safe help near river
rapids. A child notices something in trouble beside rushing water, wants to go
closer, and a caring companion steers that curiosity into a safer plan. The
story always aims for a heartwarming ending, but it refuses combinations where
the chosen rescue method could not honestly work.

Run it
------
    python storyworlds/worlds/gpt-5.4/rapids_kindness_curiosity_heartwarming.py
    python storyworlds/worlds/gpt-5.4/rapids_kindness_curiosity_heartwarming.py --setting river_park --trouble duckling
    python storyworlds/worlds/gpt-5.4/rapids_kindness_curiosity_heartwarming.py --method branch
    python storyworlds/worlds/gpt-5.4/rapids_kindness_curiosity_heartwarming.py --all
    python storyworlds/worlds/gpt-5.4/rapids_kindness_curiosity_heartwarming.py -n 5 --seed 7
    python storyworlds/worlds/gpt-5.4/rapids_kindness_curiosity_heartwarming.py --qa --json
    python storyworlds/worlds/gpt-5.4/rapids_kindness_curiosity_heartwarming.py --verify
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

# Make the shared result containers importable when this script is run directly:
# storyworlds/worlds/gpt-5.4/<file>.py -> add storyworlds/ to sys.path.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


# ---------------------------------------------------------------------------
# Entities and world state
# ---------------------------------------------------------------------------
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
        female = {"girl", "mother", "mom", "woman", "sister"}
        male = {"boy", "father", "dad", "man", "brother"}
        neutral_it = {"duckling", "bird", "puppy", "boat", "scarf"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in neutral_it:
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Setting:
    id: str
    place: str
    opening: str
    bank_desc: str
    sound_desc: str
    safe_path: str
    has_bridge: bool = False
    has_ranger: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class Trouble:
    id: str
    label: str
    phrase: str
    type: str
    sound: str
    location: str
    distance: int
    living: bool = False
    cold: bool = False
    ownerless: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class Method:
    id: str
    label: str
    phrase: str
    max_distance: int
    needs_bridge: bool = False
    needs_ranger: bool = False
    gentle_for_living: bool = True
    action_text: str = ""
    qa_text: str = ""
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


# ---------------------------------------------------------------------------
# Causal rules
# ---------------------------------------------------------------------------
@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_edge_danger(world: World) -> list[str]:
    hero = world.entities.get("hero")
    if hero is None or hero.meters["near_edge"] < THRESHOLD:
        return []
    sig = ("edge_danger",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["fear"] += 1
    hero.memes["awe"] += 1
    if "river" in world.entities:
        world.get("river").meters["danger"] += 1
    return ["__edge__"]


def _r_rescue_relief(world: World) -> list[str]:
    trouble = world.entities.get("trouble")
    hero = world.entities.get("hero")
    companion = world.entities.get("companion")
    if trouble is None or trouble.meters["safe"] < THRESHOLD:
        return []
    sig = ("rescue_relief",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    trouble.memes["relief"] += 1
    if hero is not None:
        hero.memes["warmth"] += 1
        hero.memes["relief"] += 1
    if companion is not None:
        companion.memes["warmth"] += 1
    return []


CAUSAL_RULES = [
    Rule(name="edge_danger", tag="physical", apply=_r_edge_danger),
    Rule(name="rescue_relief", tag="emotional", apply=_r_rescue_relief),
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


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------
def compatible_method(setting: Setting, trouble: Trouble, method: Method) -> bool:
    if method.max_distance < trouble.distance:
        return False
    if method.needs_bridge and not setting.has_bridge:
        return False
    if method.needs_ranger and not setting.has_ranger:
        return False
    if trouble.living and not method.gentle_for_living:
        return False
    return True


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for setting_id, setting in SETTINGS.items():
        for trouble_id, trouble in TROUBLES.items():
            for method_id, method in METHODS.items():
                if compatible_method(setting, trouble, method):
                    combos.append((setting_id, trouble_id, method_id))
    return sorted(combos)


def explain_rejection(setting: Setting, trouble: Trouble, method: Method) -> str:
    if method.max_distance < trouble.distance:
        return (
            f"(No story: {method.phrase} cannot reach {trouble.phrase} at {trouble.location}. "
            f"Pick a method that can reach farther than the rapids.)"
        )
    if method.needs_bridge and not setting.has_bridge:
        return (
            f"(No story: {method.phrase} needs a bridge, but {setting.place} has none. "
            f"Choose a setting with a bridge or a different rescue method.)"
        )
    if method.needs_ranger and not setting.has_ranger:
        return (
            f"(No story: {method.phrase} needs a ranger nearby, but {setting.place} does not have one. "
            f"Choose a ranger setting or another safe plan.)"
        )
    if trouble.living and not method.gentle_for_living:
        return (
            f"(No story: {method.phrase} would not be gentle enough for {trouble.phrase}. "
            f"Choose a kinder rescue for a living creature.)"
        )
    return "(No story: this rescue plan does not fit the situation.)"


# ---------------------------------------------------------------------------
# Story verbs
# ---------------------------------------------------------------------------
def introduce(world: World, hero: Entity, companion: Entity, setting: Setting) -> None:
    hero.memes["curiosity"] += 1
    companion.memes["kindness"] += 1
    world.say(
        f"{setting.opening} {hero.id} and {companion.id} walked beside {setting.place}. "
        f"{setting.sound_desc}"
    )
    world.say(
        f"{hero.id} was full of curiosity and kept noticing little things along {setting.bank_desc}. "
        f"{companion.id} stayed close, ready to help if anything needed gentle hands."
    )


def notice(world: World, hero: Entity, trouble: Trouble) -> None:
    hero.memes["wonder"] += 1
    world.say(
        f"Then {hero.id} heard {trouble.sound} and stopped. Near the rapids, {hero.pronoun()} saw "
        f"{trouble.phrase} {trouble.location}."
    )


def move_closer(world: World, hero: Entity, setting: Setting) -> None:
    hero.meters["near_edge"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Curiosity tugged {hero.pronoun('object')} forward. {hero.id} took two quick steps toward "
        f"the water, where {setting.bank_desc} looked bright but slippery."
    )


def warn(world: World, companion: Entity, hero: Entity, trouble: Trouble, setting: Setting) -> None:
    world.facts["predicted_slip"] = True
    companion.memes["care"] += 1
    world.say(
        f'"Wait," {companion.id} said softly, touching {hero.pronoun("possessive")} sleeve. '
        f'"The stones by the rapids are slick, and the water is too fast. '
        f'We can still help {trouble.label}, but not by leaning over the edge."'
    )


def choose_plan(world: World, companion: Entity, method: Method, setting: Setting) -> None:
    world.say(
        f"{companion.id} looked around and chose {method.phrase}. "
        f"{setting.safe_path}"
    )


def rescue(world: World, hero: Entity, companion: Entity, trouble_ent: Entity,
           trouble: Trouble, method: Method) -> None:
    trouble_ent.meters["safe"] += 1
    trouble_ent.meters["in_danger"] = 0.0
    hero.meters["near_edge"] = 0.0
    propagate(world, narrate=False)
    if method.action_text:
        world.say(method.action_text.format(hero=hero.id, companion=companion.id, trouble=trouble.label))
    else:
        world.say(f"Together they used {method.label} and helped {trouble.label} away from the rapids.")
    if trouble.living:
        world.say(
            f"In another moment, {trouble.label} was safe on the bank, small and shaky but no longer trapped by the rushing water."
        )
    else:
        world.say(
            f"In another moment, {trouble.label} was safe again, no longer spinning close to the rushing water."
        )


def comfort(world: World, hero: Entity, companion: Entity, trouble_ent: Entity, trouble: Trouble) -> None:
    hero.memes["kindness"] += 1
    companion.memes["kindness"] += 1
    if trouble.living:
        world.say(
            f"{hero.id} knelt down instead of grabbing. {hero.pronoun().capitalize()} held still until "
            f"{trouble.label} stopped trembling, and {companion.id} smiled at how gentle {hero.pronoun()} had become."
        )
    else:
        owner = trouble_ent.attrs.get("owner", "")
        if owner:
            world.say(
                f"{hero.id} brushed the water from {trouble.label} and looked around until {hero.pronoun()} found {owner}. "
                f"The grateful smile that came back felt warmer than the sun."
            )
        else:
            world.say(
                f"{hero.id} held {trouble.label} carefully and smiled. Helping, {hero.pronoun()} realized, could feel as bright as discovering something new."
            )


def ending(world: World, hero: Entity, companion: Entity, setting: Setting, trouble: Trouble) -> None:
    hero.memes["lesson"] += 1
    world.say(
        f"After that, {hero.id}'s curiosity felt different. It was still bright, but now it walked beside kindness instead of running ahead of it."
    )
    if trouble.living:
        world.say(
            f"They left {setting.place} hand in hand while the rapids kept singing, and behind them {trouble.label} was safe where the water ran calmer."
        )
    else:
        world.say(
            f"They walked on beside {setting.place} with the sound of the rapids behind them, both a little happier because they had chosen a careful kind of help."
        )


# ---------------------------------------------------------------------------
# Screenplay
# ---------------------------------------------------------------------------
def tell(
    *,
    setting: Setting,
    trouble: Trouble,
    method: Method,
    hero_name: str = "Lina",
    hero_type: str = "girl",
    companion_name: str = "Owen",
    companion_type: str = "boy",
    companion_role: str = "sibling",
    parent_type: str = "mother",
    found_owner: str = "",
) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, role="hero", traits=["curious"]))
    companion = world.add(
        Entity(
            id=companion_name,
            kind="character",
            type=companion_type,
            role="companion",
            traits=["kind"],
            attrs={"relation": companion_role},
        )
    )
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, role="parent", label="the parent"))
    river = world.add(Entity(id="river", type="river", label="the rapids"))
    trouble_ent = world.add(
        Entity(
            id="trouble",
            type=trouble.type,
            label=trouble.label,
            phrase=trouble.phrase,
            tags=set(trouble.tags),
            attrs={"owner": found_owner},
        )
    )
    trouble_ent.meters["in_danger"] += 1

    introduce(world, hero, companion, setting)
    notice(world, hero, trouble)

    world.para()
    move_closer(world, hero, setting)
    warn(world, companion, hero, trouble, setting)
    choose_plan(world, companion, method, setting)

    world.para()
    rescue(world, hero, companion, trouble_ent, trouble, method)
    comfort(world, hero, companion, trouble_ent, trouble)
    ending(world, hero, companion, setting, trouble)

    world.facts.update(
        hero=hero,
        companion=companion,
        parent=parent,
        river=river,
        trouble_cfg=trouble,
        trouble=trouble_ent,
        setting=setting,
        method=method,
        found_owner=found_owner,
        rescued=trouble_ent.meters["safe"] >= THRESHOLD,
        relation=companion_role,
    )
    return world


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "river_park": Setting(
        id="river_park",
        place="the river park",
        opening="One golden afternoon,",
        bank_desc="the flat gray stones on the bank",
        sound_desc="The rapids hurried over the rocks with a silver, splashy song.",
        safe_path="There was a wide path back from the edge and a little ranger station nearby.",
        has_bridge=False,
        has_ranger=True,
        tags={"rapids", "river", "park", "ranger"},
    ),
    "pine_bridge": Setting(
        id="pine_bridge",
        place="the pine bridge trail",
        opening="On a cool bright morning,",
        bank_desc="the mossy bank under the tall pines",
        sound_desc="Below the trail, the rapids foamed white between dark stones.",
        safe_path="A wooden footbridge crossed the calmer side of the stream a little way up the path.",
        has_bridge=True,
        has_ranger=False,
        tags={"rapids", "bridge", "forest"},
    ),
    "meadow_bend": Setting(
        id="meadow_bend",
        place="the meadow bend",
        opening="One soft sunny day,",
        bank_desc="the grassy edge where flowers leaned toward the spray",
        sound_desc="The rapids roared a little louder here, making the air smell cool and fresh.",
        safe_path="A ranger dock stood beside the trail, and a safe rope rail marked the edge.",
        has_bridge=False,
        has_ranger=True,
        tags={"rapids", "meadow", "ranger"},
    ),
}

TROUBLES = {
    "duckling": Trouble(
        id="duckling",
        label="the duckling",
        phrase="a tiny duckling",
        type="duckling",
        sound="thin peeping sounds",
        location="on a small rock just beyond the nearest spray",
        distance=2,
        living=True,
        cold=True,
        tags={"duckling", "animal", "rapids"},
    ),
    "puppy": Trouble(
        id="puppy",
        label="the puppy",
        phrase="a soaked little puppy",
        type="puppy",
        sound="a worried yip",
        location="on a driftwood log caught near the rapids",
        distance=3,
        living=True,
        cold=True,
        tags={"puppy", "animal", "rapids"},
    ),
    "toy_boat": Trouble(
        id="toy_boat",
        label="the toy boat",
        phrase="a red toy boat",
        type="boat",
        sound="a small clacking bump against a rock",
        location="circling in a quiet pocket beside the rapids",
        distance=1,
        living=False,
        ownerless=False,
        tags={"boat", "toy", "rapids"},
    ),
    "scarf": Trouble(
        id="scarf",
        label="the scarf",
        phrase="a bright yellow scarf",
        type="scarf",
        sound="a flap of wet cloth in the wind",
        location="snagged on a branch above the rapids",
        distance=2,
        living=False,
        ownerless=False,
        tags={"scarf", "lost_item", "rapids"},
    ),
}

METHODS = {
    "branch": Method(
        id="branch",
        label="a long branch",
        phrase="a long branch from the safe side of the bank",
        max_distance=2,
        needs_bridge=False,
        needs_ranger=False,
        gentle_for_living=True,
        action_text=(
            "{companion} lay on the dry ground and held one end of a long branch while {hero} guided the other. "
            "With slow careful movements, they drew {trouble} closer without stepping into danger."
        ),
        qa_text="used a long branch from the safe bank to draw it closer",
        tags={"branch", "reach", "safety"},
    ),
    "bridge_basket": Method(
        id="bridge_basket",
        label="the footbridge and a picnic basket",
        phrase="the footbridge and a sturdy picnic basket",
        max_distance=3,
        needs_bridge=True,
        needs_ranger=False,
        gentle_for_living=True,
        action_text=(
            "They hurried up to the bridge, crossed where the water ran calmer, and lowered a sturdy basket on its strap. "
            "Soon {trouble} was lifted away from the rush of the rapids."
        ),
        qa_text="crossed the footbridge and lowered a sturdy basket from the calm side",
        tags={"bridge", "basket", "safety"},
    ),
    "ranger_net": Method(
        id="ranger_net",
        label="the ranger's long rescue net",
        phrase="the ranger's long rescue net",
        max_distance=3,
        needs_bridge=False,
        needs_ranger=True,
        gentle_for_living=True,
        action_text=(
            "A ranger came quickly with a long rescue net, and {hero} pointed the way. "
            "With one smooth careful sweep, the ranger brought {trouble} out of the spray."
        ),
        qa_text="called a ranger, who used a long rescue net",
        tags={"ranger", "net", "safety"},
    ),
    "hook_pole": Method(
        id="hook_pole",
        label="a hooked pole",
        phrase="a hooked pole from the rail",
        max_distance=2,
        needs_bridge=False,
        needs_ranger=False,
        gentle_for_living=False,
        action_text=(
            "{companion} reached with a hooked pole and caught {trouble} by its edge, then slid it safely back to shore."
        ),
        qa_text="used a hooked pole to slide it back to shore",
        tags={"pole", "safety"},
    ),
}

GIRL_NAMES = ["Lina", "Maya", "Nora", "Ava", "Ella", "Ruby", "Ivy", "June"]
BOY_NAMES = ["Owen", "Leo", "Finn", "Max", "Theo", "Eli", "Sam", "Ben"]
RELATIONS = ["brother", "sister", "friend"]
OWNER_NAMES = ["a smiling hiker", "a small boy on a bench", "an old woman with a sunhat", "a family by the trail"]


# ---------------------------------------------------------------------------
# Per-world parameters
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    setting: str
    trouble: str
    method: str
    hero_name: str
    hero_type: str
    companion_name: str
    companion_type: str
    companion_role: str
    parent_type: str
    found_owner: str = ""
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Curated set
# ---------------------------------------------------------------------------
CURATED = [
    StoryParams(
        setting="river_park",
        trouble="duckling",
        method="ranger_net",
        hero_name="Lina",
        hero_type="girl",
        companion_name="Owen",
        companion_type="boy",
        companion_role="brother",
        parent_type="mother",
        found_owner="",
    ),
    StoryParams(
        setting="pine_bridge",
        trouble="puppy",
        method="bridge_basket",
        hero_name="Maya",
        hero_type="girl",
        companion_name="Leo",
        companion_type="boy",
        companion_role="friend",
        parent_type="father",
        found_owner="",
    ),
    StoryParams(
        setting="meadow_bend",
        trouble="toy_boat",
        method="branch",
        hero_name="Finn",
        hero_type="boy",
        companion_name="Ruby",
        companion_type="girl",
        companion_role="sister",
        parent_type="mother",
        found_owner="a small boy on a bench",
    ),
    StoryParams(
        setting="pine_bridge",
        trouble="scarf",
        method="bridge_basket",
        hero_name="June",
        hero_type="girl",
        companion_name="Theo",
        companion_type="boy",
        companion_role="friend",
        parent_type="father",
        found_owner="an old woman with a sunhat",
    ),
]


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
KNOWLEDGE = {
    "rapids": [
        (
            "What are rapids?",
            "Rapids are fast, rough parts of a river where water rushes over rocks. They look exciting, but they can be dangerous because the water moves so quickly.",
        )
    ],
    "duckling": [
        (
            "Why does a duckling need gentle help?",
            "A duckling is small and soft, so rough grabbing could scare or hurt it. Gentle, careful help keeps it safer and calmer.",
        )
    ],
    "puppy": [
        (
            "Why can a puppy get scared near rushing water?",
            "A puppy is small and can lose its footing near fast water. The loud noise and slippery ground can make it frightened too.",
        )
    ],
    "bridge": [
        (
            "Why is a bridge safer than climbing near a river edge?",
            "A bridge gives you a steady place to stand above the water. That is much safer than leaning over slippery rocks beside the river.",
        )
    ],
    "ranger": [
        (
            "What does a ranger do in a park?",
            "A ranger helps take care of the park and the people and animals in it. Rangers often know the safest way to solve outdoor problems.",
        )
    ],
    "branch": [
        (
            "When can a long branch help safely?",
            "A long branch can help when something is close enough to reach from solid ground. It lets you help without stepping into danger.",
        )
    ],
    "kindness": [
        (
            "What does kindness mean?",
            "Kindness means caring about how someone else feels and trying to help gently. It is not just noticing trouble, but choosing a good way to help.",
        )
    ],
    "curiosity": [
        (
            "What is curiosity?",
            "Curiosity is the feeling that makes you want to look closer, ask questions, and learn more. Curiosity is wonderful when it walks with care.",
        )
    ],
    "safety": [
        (
            "Why should children ask for safe help near water?",
            "Fast water and slippery rocks can surprise people very quickly. Asking for safe help lets a problem get solved without someone else getting hurt.",
        )
    ],
}
KNOWLEDGE_ORDER = ["rapids", "duckling", "puppy", "bridge", "ranger", "branch", "kindness", "curiosity", "safety"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    companion = f["companion"]
    trouble = f["trouble_cfg"]
    setting = f["setting"]
    return [
        (
            f'Write a heartwarming story for a 3-to-5-year-old that includes the word "rapids" '
            f"and shows curiosity turning into kindness."
        ),
        (
            f"Tell a gentle story where {hero.id} notices {trouble.phrase} near the rapids at "
            f"{setting.place}, wants to go closer, and is guided toward a safer way to help."
        ),
        (
            f"Write a warm story about {hero.id} and {companion.id} learning that being curious is good, "
            f"but being kind and careful is even better near rushing water."
        ),
    ]


def relation_noun(role: str) -> str:
    if role == "friend":
        return "friend"
    return role


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    companion = f["companion"]
    trouble = f["trouble_cfg"]
    method = f["method"]
    setting = f["setting"]
    owner = f["found_owner"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id}, a curious child, and {companion.id}, {hero.pronoun('possessive')} kind {relation_noun(f['relation'])}. Together they noticed trouble near the rapids and chose to help carefully.",
        ),
        (
            f"What did {hero.id} find near the rapids?",
            f"{hero.id} found {trouble.phrase} {trouble.location}. That discovery is what first pulled {hero.pronoun('object')} toward the rushing water.",
        ),
        (
            f"Why did {companion.id} stop {hero.id} from going closer?",
            f"{companion.id} knew the edge near the rapids was slippery and the water was too fast. {companion.pronoun().capitalize()} wanted to help, but not by letting {hero.id} get into danger too.",
        ),
        (
            "How did they help safely?",
            f"They {method.qa_text}. The safe plan mattered because it let them rescue {trouble.label} without climbing onto the slick edge by the rapids.",
        ),
    ]
    if trouble.living:
        qa.append(
            (
                f"How did {hero.id} show kindness after the rescue?",
                f"{hero.id} stayed gentle and still instead of grabbing roughly. That helped {trouble.label} calm down, which shows that kindness can be soft as well as brave.",
            )
        )
    else:
        if owner:
            qa.append(
                (
                    f"What happened after they got {trouble.label} back?",
                    f"{hero.id} and {companion.id} found {owner}, who was grateful to see it again. The happy smile at the end shows their careful help made someone else's day better too.",
                )
            )
        else:
            qa.append(
                (
                    "What did the children learn?",
                    f"They learned that curiosity should walk beside kindness and care. Looking closer was not wrong, but the best choice was helping in a safer way.",
                )
            )
    qa.append(
        (
            "How did the story end?",
            f"It ended warmly, with the sound of the rapids behind them and everyone safer than before. The final feeling is that careful kindness can turn a scary moment into a gentle one.",
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"rapids", "kindness", "curiosity", "safety"} | set(f["setting"].tags) | set(f["trouble_cfg"].tags) | set(f["method"].tags)
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


# ---------------------------------------------------------------------------
# Trace
# ---------------------------------------------------------------------------
def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for ent in world.entities.values():
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits: list[str] = []
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
        lines.append(f"  {ent.id:10} ({ent.type:9}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
compatible(S, T, M) :- setting(S), trouble(T), method(M),
                       distance(T, D), max_distance(M, R), R >= D,
                       not bad_bridge(S, M), not bad_ranger(S, M), not bad_gentle(T, M).

bad_bridge(S, M) :- needs_bridge(M), not has_bridge(S).
bad_ranger(S, M) :- needs_ranger(M), not has_ranger(S).
bad_gentle(T, M) :- living(T), not gentle(M).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for setting_id, setting in SETTINGS.items():
        lines.append(asp.fact("setting", setting_id))
        if setting.has_bridge:
            lines.append(asp.fact("has_bridge", setting_id))
        if setting.has_ranger:
            lines.append(asp.fact("has_ranger", setting_id))
    for trouble_id, trouble in TROUBLES.items():
        lines.append(asp.fact("trouble", trouble_id))
        lines.append(asp.fact("distance", trouble_id, trouble.distance))
        if trouble.living:
            lines.append(asp.fact("living", trouble_id))
    for method_id, method in METHODS.items():
        lines.append(asp.fact("method", method_id))
        lines.append(asp.fact("max_distance", method_id, method.max_distance))
        if method.needs_bridge:
            lines.append(asp.fact("needs_bridge", method_id))
        if method.needs_ranger:
            lines.append(asp.fact("needs_ranger", method_id))
        if method.gentle_for_living:
            lines.append(asp.fact("gentle", method_id))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show compatible/3."))
    return sorted(set(asp.atoms(model, "compatible")))


def asp_verify() -> int:
    rc = 0
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: ASP gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH between ASP and Python valid combos:")
        if clingo_set - python_set:
            print("  only in ASP:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in Python:", sorted(python_set - clingo_set))

    # Smoke-test ordinary story generation.
    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("Generated story was empty during smoke test.")
        print("OK: smoke test generated a normal story.")
    except Exception as err:  # pragma: no cover - verification path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    # Exercise randomized resolution and generation a few times.
    parser = build_parser()
    for seed in range(3):
        try:
            args = parser.parse_args([])
            params = resolve_params(args, random.Random(seed))
            params.seed = seed
            sample = generate(params)
            if not sample.story.strip():
                raise StoryError("Random smoke test produced an empty story.")
        except Exception as err:  # pragma: no cover - verification path
            rc = 1
            print(f"RANDOM SMOKE TEST FAILED at seed {seed}: {err}")
            break
    else:
        print("OK: random smoke tests passed.")

    return rc


# ---------------------------------------------------------------------------
# Interface
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Heartwarming storyworld about curiosity, kindness, and safe help near rapids."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--trouble", choices=TROUBLES)
    ap.add_argument("--method", choices=METHODS)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--hero-name")
    ap.add_argument("--companion-name")
    ap.add_argument("--hero-type", choices=["girl", "boy"])
    ap.add_argument("--companion-type", choices=["girl", "boy"])
    ap.add_argument("--relation", choices=RELATIONS)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible (setting, trouble, method) combos from ASP")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the ASP program")
    return ap


def pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [name for name in pool if name != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.setting and args.trouble and args.method:
        setting = SETTINGS[args.setting]
        trouble = TROUBLES[args.trouble]
        method = METHODS[args.method]
        if not compatible_method(setting, trouble, method):
            raise StoryError(explain_rejection(setting, trouble, method))

    combos = [
        combo
        for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.trouble is None or combo[1] == args.trouble)
        and (args.method is None or combo[2] == args.method)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, trouble_id, method_id = rng.choice(combos)
    hero_type = args.hero_type or rng.choice(["girl", "boy"])
    companion_type = args.companion_type or rng.choice(["girl", "boy"])
    hero_name = args.hero_name or pick_name(rng, hero_type)
    companion_name = args.companion_name or pick_name(rng, companion_type, avoid=hero_name)
    relation = args.relation or rng.choice(RELATIONS)
    parent = args.parent or rng.choice(["mother", "father"])

    found_owner = ""
    if not TROUBLES[trouble_id].ownerless:
        found_owner = rng.choice(OWNER_NAMES)

    return StoryParams(
        setting=setting_id,
        trouble=trouble_id,
        method=method_id,
        hero_name=hero_name,
        hero_type=hero_type,
        companion_name=companion_name,
        companion_type=companion_type,
        companion_role=relation,
        parent_type=parent,
        found_owner=found_owner,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError(f"(Unknown setting '{params.setting}'.)")
    if params.trouble not in TROUBLES:
        raise StoryError(f"(Unknown trouble '{params.trouble}'.)")
    if params.method not in METHODS:
        raise StoryError(f"(Unknown method '{params.method}'.)")

    setting = SETTINGS[params.setting]
    trouble = TROUBLES[params.trouble]
    method = METHODS[params.method]
    if not compatible_method(setting, trouble, method):
        raise StoryError(explain_rejection(setting, trouble, method))

    world = tell(
        setting=setting,
        trouble=trouble,
        method=method,
        hero_name=params.hero_name,
        hero_type=params.hero_type,
        companion_name=params.companion_name,
        companion_type=params.companion_type,
        companion_role=params.companion_role,
        parent_type=params.parent_type,
        found_owner=params.found_owner,
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
        print(asp_program("#show compatible/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, trouble, method) combos:\n")
        for setting_id, trouble_id, method_id in combos:
            print(f"  {setting_id:12} {trouble_id:10} {method_id}")
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
            header = f"### {p.hero_name} and {p.companion_name}: {p.trouble} at {p.setting} with {p.method}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
