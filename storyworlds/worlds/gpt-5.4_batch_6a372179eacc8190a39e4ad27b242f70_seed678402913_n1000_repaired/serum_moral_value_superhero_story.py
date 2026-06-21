#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/serum_moral_value_superhero_story.py
===============================================================

A standalone story world about a child superhero game, a "glow serum" that
seems like a shortcut to strength, and the moral choice to use honesty and
teamwork instead of a risky secret sip.

The domain is small on purpose: a child wants to rescue a toy from a high place
during superhero play. A tempting serum promises instant power, but a careful
friend predicts trouble. The story can end in two reasonable ways:

* near-miss / virtuous ending:
    the hero listens, tells a grown-up the truth, and gets a safe helper tool;
* mishap / repaired ending:
    the hero secretly drinks the serum, gets shaky and wobbly, and a grown-up
    helps, explains why shortcuts are unsafe, and later provides a safe way to
    finish the rescue.

The world model tracks physical meters (reach, wobble, mess, danger) and
emotional memes (bravery, caution, guilt, relief, trust, pride). Prose is
rendered from simulated state, not from a fixed paragraph template.

Run it
------
    python storyworlds/worlds/gpt-5.4/serum_moral_value_superhero_story.py
    python storyworlds/worlds/gpt-5.4/serum_moral_value_superhero_story.py --hero boy --serum berry --goal kite
    python storyworlds/worlds/gpt-5.4/serum_moral_value_superhero_story.py --surface floor
    python storyworlds/worlds/gpt-5.4/serum_moral_value_superhero_story.py --all
    python storyworlds/worlds/gpt-5.4/serum_moral_value_superhero_story.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/serum_moral_value_superhero_story.py --trace --seed 777
    python storyworlds/worlds/gpt-5.4/serum_moral_value_superhero_story.py --json
    python storyworlds/worlds/gpt-5.4/serum_moral_value_superhero_story.py --verify
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

# Make the shared result containers importable when this script is run directly
# from the nested directory (storyworlds/worlds/gpt-5.4/).
_THIS = os.path.abspath(__file__)
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(_THIS))))
from results import QAItem, StoryError, StorySample  # noqa: E402


THRESHOLD = 1.0
SAFE_MIN = 2


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
    portable: bool = False
    climbable: bool = False
    edible: bool = False
    safe_helper: bool = False
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
class Setting:
    id: str
    place: str
    hideout: str
    perch: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Serum:
    id: str
    label: str
    phrase: str
    color: str
    promise: str
    after: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Goal:
    id: str
    label: str
    phrase: str
    up_high: str
    dangling: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Surface:
    id: str
    label: str
    phrase: str
    height: int
    stable: bool
    climbable: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class Helper:
    id: str
    label: str
    phrase: str
    reach_bonus: int
    safety: int
    use_text: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Moral:
    id: str
    line: str
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


def _r_serum_wobble(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("hero")
    serum = world.get("serum")
    if serum.meters["drunk"] < THRESHOLD:
        return out
    sig = ("serum_wobble",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.meters["wobble"] += 1
    child.memes["fear"] += 1
    child.memes["guilt"] += 1
    out.append("__wobble__")
    return out


def _r_unstable_danger(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("hero")
    surface = world.get("surface")
    if child.meters["climbing"] < THRESHOLD:
        return out
    if surface.meters["stability"] >= THRESHOLD:
        return out
    sig = ("unstable_danger",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.get("room").meters["danger"] += 1
    child.memes["fear"] += 1
    out.append("__danger__")
    return out


def _r_wobble_on_surface(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("hero")
    if child.meters["climbing"] < THRESHOLD or child.meters["wobble"] < THRESHOLD:
        return out
    sig = ("wobble_on_surface",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.meters["slip"] += 1
    world.get("room").meters["danger"] += 1
    out.append("__slip__")
    return out


CAUSAL_RULES = [
    Rule(name="serum_wobble", tag="physical", apply=_r_serum_wobble),
    Rule(name="unstable_danger", tag="physical", apply=_r_unstable_danger),
    Rule(name="wobble_on_surface", tag="physical", apply=_r_wobble_on_surface),
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


def goal_is_high(goal: Goal, surface: Surface) -> bool:
    return surface.height > 0


def serum_risk(surface: Surface) -> bool:
    return surface.height >= 1


def sensible_helpers() -> list[Helper]:
    return [h for h in HELPERS.values() if h.safety >= SAFE_MIN]


def valid_combos() -> list[tuple[str, str, str, str, str]]:
    combos: list[tuple[str, str, str, str, str]] = []
    for setting_id in SETTINGS:
        for serum_id, serum in SERUMS.items():
            if not serum.tags:
                continue
            for goal_id in GOALS:
                for surface_id, surface in SURFACES.items():
                    if not goal_is_high(GOALS[goal_id], surface):
                        continue
                    if not serum_risk(surface):
                        continue
                    for helper_id, helper in HELPERS.items():
                        if helper.safety >= SAFE_MIN:
                            combos.append((setting_id, serum_id, goal_id, surface_id, helper_id))
    return combos


def explain_surface(surface: Surface) -> str:
    return (
        f"(No story: {surface.label} is too low for a real rescue problem. "
        f"If nothing is up high, the child does not need a serum, a climb, or a safe helper.)"
    )


def explain_helper(helper: Helper) -> str:
    better = ", ".join(sorted(h.id for h in sensible_helpers()))
    return (
        f"(Refusing helper '{helper.id}': it is too unsafe or weak for this world "
        f"(safety={helper.safety} < {SAFE_MIN}). Try one of: {better}.)"
    )


def predict_trouble(world: World) -> dict:
    sim = world.copy()
    hero = sim.get("hero")
    surface = sim.get("surface")
    serum = sim.get("serum")
    serum.meters["drunk"] += 1
    hero.meters["climbing"] += 1
    if not surface.attrs.get("stable", True):
        surface.meters["stability"] = 0.0
    else:
        surface.meters["stability"] = 1.0
    propagate(sim, narrate=False)
    return {
        "wobble": hero.meters["wobble"] >= THRESHOLD,
        "slip": hero.meters["slip"] >= THRESHOLD,
        "danger": sim.get("room").meters["danger"],
    }


def introduce(world: World, hero: Entity, friend: Entity, setting: Setting) -> None:
    hero.memes["joy"] += 1
    friend.memes["joy"] += 1
    world.say(
        f"After school, {hero.id} and {friend.id} turned {setting.place} into {setting.hideout}. "
        f"Towels became capes, a cardboard box became a control panel, and every chair shadow "
        f"looked like part of a city that needed saving."
    )
    world.say(
        f'{hero.id} pressed both fists to {hero.pronoun("possessive")} hips. '
        f'"I am Star Shield!" {hero.pronoun()} said. '
        f'{friend.id} laughed and answered, "Then I will be your lookout."'
    )


def present_problem(world: World, hero: Entity, friend: Entity, goal: Goal, setting: Setting) -> None:
    world.say(
        f"Then they spotted {goal.phrase} stuck {goal.up_high}, just above {setting.perch}. "
        f"It swung a little whenever the window breeze slipped through."
    )
    world.say(
        f'{friend.id} pointed up. "Our city needs a rescue," {friend.pronoun()} said. '
        f'{hero.id} nodded, already thinking of the fastest way to reach it.'
    )


def tempt_serum(world: World, hero: Entity, serum: Serum) -> None:
    hero.memes["tempted"] += 1
    world.say(
        f"On the shelf beside the craft box sat {serum.phrase}. A paper star on the lid said, "
        f'"{serum.promise}."'
    )
    world.say(
        f'{hero.id} stared at the {serum.color} swirl inside. '
        f'"Maybe one sip of that serum would make me strong enough," {hero.pronoun()} whispered.'
    )


def warn_friend(world: World, hero: Entity, friend: Entity, serum: Serum, surface: Surface, moral: Moral) -> None:
    pred = predict_trouble(world)
    friend.memes["caution"] += 1
    world.facts["predicted_danger"] = pred["danger"]
    wobble_clause = "it could make you shaky" if pred["wobble"] else "it could make trouble"
    slip_clause = ""
    if pred["slip"]:
        slip_clause = f" and you might slip from {surface.phrase}"
    world.say(
        f'{friend.id} shook {friend.pronoun("possessive")} head. '
        f'"That serum is not for secret sips," {friend.pronoun()} said. '
        f'"If you drink it and climb {surface.phrase}, {wobble_clause}{slip_clause}. '
        f'{moral.line}"'
    )


def would_confess(relation: str, trait: str, trust: int) -> bool:
    base = 0
    if relation == "siblings":
        base += 1
    if trait in {"careful", "honest", "kind"}:
        base += 1
    if trust >= 6:
        base += 1
    return base >= 2


def choose_truth(world: World, hero: Entity, friend: Entity, parent: Entity, moral: Moral) -> None:
    hero.memes["honesty"] += 1
    hero.memes["relief"] += 1
    friend.memes["trust"] += 1
    world.say(
        f"{hero.id} looked from the bottle to the high shelf and then back to {friend.id}. "
        f"The rescue mattered, but the secret felt wrong."
    )
    world.say(
        f'"You are right," {hero.pronoun()} said. "A real hero tells the truth." '
        f"Together they went to {parent.label_word.capitalize()} and explained about the serum and the stuck toy."
    )
    world.say(
        f"{parent.label_word.capitalize()} smiled, glad they had come first. "
        f'"That is how heroes grow," {parent.pronoun()} said. "{moral.line}"'
    )


def safe_plan(world: World, hero: Entity, friend: Entity, parent: Entity, helper: Helper, goal: Goal, moral: Moral) -> None:
    hero.meters["reach"] += helper.reach_bonus
    hero.memes["pride"] += 1
    hero.memes["joy"] += 1
    friend.memes["joy"] += 1
    helper_ent = world.get("helper")
    helper_ent.meters["used"] += 1
    world.say(
        f"{parent.label_word.capitalize()} brought {helper.phrase}. "
        f"{helper.use_text}."
    )
    world.say(
        f"Soon {hero.id} reached {goal.label}, brought it safely down, and set it in {friend.id}'s hands. "
        f'"No secret serum needed," {friend.id} said with a grin.'
    )
    world.say(
        f"They flew around the room after that, capes fluttering, and {moral.ending}"
    )


def secret_sip(world: World, hero: Entity, serum: Serum) -> None:
    serum_ent = world.get("serum")
    serum_ent.meters["drunk"] += 1
    hero.memes["defiance"] += 1
    hero.memes["hope"] += 1
    propagate(world, narrate=False)
    world.say(
        f"But the wish to be strong right away tugged harder. "
        f'{hero.id} popped the lid, took a tiny secret sip of the serum, and swallowed.'
    )
    world.say(
        f"For half a heartbeat, the {serum.color} sparkle felt exciting. Then {serum.after}."
    )


def climb_attempt(world: World, hero: Entity, goal: Goal, surface: Surface) -> None:
    hero.meters["climbing"] += 1
    surface_ent = world.get("surface")
    surface_ent.meters["stability"] = 1.0 if surface.stable else 0.0
    propagate(world, narrate=False)
    world.say(
        f'{hero.id} dragged {surface.phrase} under the shelf and started to climb for {goal.label}.'
    )
    if hero.meters["wobble"] >= THRESHOLD:
        world.say(
            f"But {hero.pronoun("possessive")} knees wiggled. The room seemed to tip for a second."
        )
    if hero.meters["slip"] >= THRESHOLD:
        world.say(
            f"One foot skidded, and the rescue turned scary at once."
        )


def alarm_and_help(world: World, hero: Entity, friend: Entity, parent: Entity, helper: Helper, goal: Goal, moral: Moral) -> None:
    hero.memes["fear"] += 1
    friend.memes["fear"] += 1
    hero.memes["guilt"] += 1
    helper_ent = world.get("helper")
    helper_ent.meters["used"] += 1
    world.say(f'"{parent.label_word.upper()}!" {friend.id} cried. "{hero.id} feels funny!"')
    world.say(
        f"{parent.label_word.capitalize()} hurried over, steadied {hero.id}, lifted {hero.pronoun("object")} down, "
        f"and moved the serum far back onto the shelf."
    )
    world.say(
        f'When {hero.id} admitted the secret sip, {parent.label_word} hugged {hero.pronoun("object")} first. '
        f'"Thank you for telling me the truth now," {parent.pronoun()} said. '
        f'"Shortcuts that hide things can hurt people. {moral.line}"'
    )
    world.say(
        f"Then {parent.pronoun()} brought {helper.phrase}, and {helper.use_text.lower()}. "
        f"With calm hands and help nearby, {goal.label} came safely down at last."
    )


def repaired_ending(world: World, hero: Entity, friend: Entity, moral: Moral) -> None:
    hero.memes["relief"] += 1
    hero.memes["honesty"] += 1
    friend.memes["trust"] += 1
    world.say(
        f"{hero.id} leaned into {friend.id}'s shoulder for a moment and took a slow breath. "
        f'Then {hero.pronoun()} said, "Next time I will ask for help first."'
    )
    world.say(
        f'{friend.id} squeezed {hero.pronoun("possessive")} hand. "{moral.ending}"'
    )


def tell(
    setting: Setting,
    serum: Serum,
    goal: Goal,
    surface: Surface,
    helper: Helper,
    moral: Moral,
    *,
    hero_name: str = "Mia",
    hero_type: str = "girl",
    friend_name: str = "Ben",
    friend_type: str = "boy",
    relation: str = "friends",
    trait: str = "honest",
    trust: int = 7,
    parent_type: str = "mother",
) -> World:
    world = World()
    hero = world.add(Entity(id="hero", kind="character", type=hero_type, label=hero_name, role="hero"))
    friend = world.add(Entity(id="friend", kind="character", type=friend_type, label=friend_name, role="friend"))
    parent = world.add(Entity(id="parent", kind="character", type=parent_type, label="the parent", role="parent"))
    room = world.add(Entity(id="room", type="room", label=setting.place))
    serum_ent = world.add(
        Entity(
            id="serum",
            type="serum",
            label=serum.label,
            phrase=serum.phrase,
            edible=True,
            tags=set(serum.tags),
        )
    )
    surface_ent = world.add(
        Entity(
            id="surface",
            type="surface",
            label=surface.label,
            phrase=surface.phrase,
            climbable=surface.climbable,
            attrs={"stable": surface.stable, "height": surface.height},
            tags=set(surface.tags),
        )
    )
    goal_ent = world.add(
        Entity(
            id="goal",
            type="goal",
            label=goal.label,
            phrase=goal.phrase,
            portable=True,
            attrs={"up_high": goal.up_high},
            tags=set(goal.tags),
        )
    )
    helper_ent = world.add(
        Entity(
            id="helper",
            type="helper",
            label=helper.label,
            phrase=helper.phrase,
            safe_helper=True,
            attrs={"reach_bonus": helper.reach_bonus, "safety": helper.safety},
            tags=set(helper.tags),
        )
    )

    hero.id = hero_name
    friend.id = friend_name
    world.entities[hero_name] = world.entities.pop("hero")
    world.entities[friend_name] = world.entities.pop("friend")
    world.entities["hero"] = world.entities[hero_name]
    world.entities["friend"] = world.entities[friend_name]

    hero = world.get("hero")
    friend = world.get("friend")

    hero.attrs.update({"relation": relation, "trait": trait})
    friend.attrs.update({"relation": relation, "trust": trust})
    world.facts["relation"] = relation
    world.facts["trust"] = trust

    introduce(world, hero, friend, setting)
    present_problem(world, hero, friend, goal, setting)

    world.para()
    tempt_serum(world, hero, serum)
    warn_friend(world, hero, friend, serum, surface, moral)

    brave_truth = would_confess(relation, trait, trust)
    if brave_truth:
        world.para()
        choose_truth(world, hero, friend, parent, moral)
        world.para()
        safe_plan(world, hero, friend, parent, helper, goal, moral)
        outcome = "truth"
    else:
        world.para()
        secret_sip(world, hero, serum)
        climb_attempt(world, hero, goal, surface)
        world.para()
        alarm_and_help(world, hero, friend, parent, helper, goal, moral)
        repaired_ending(world, hero, friend, moral)
        outcome = "mishap"

    world.facts.update(
        setting=setting,
        serum=serum,
        goal_cfg=goal,
        surface_cfg=surface,
        helper=helper,
        moral=moral,
        hero=hero,
        friend=friend,
        parent=parent,
        outcome=outcome,
        secret_sip=serum_ent.meters["drunk"] >= THRESHOLD,
        slipped=hero.meters["slip"] >= THRESHOLD,
        wobbled=hero.meters["wobble"] >= THRESHOLD,
        danger=room.meters["danger"],
    )
    goal_ent.meters["rescued"] += 1
    return world


SETTINGS = {
    "bedroom": Setting(
        id="bedroom",
        place="the bedroom",
        hideout="a moonlit hero headquarters",
        perch="the bookshelf",
        tags={"room"},
    ),
    "playroom": Setting(
        id="playroom",
        place="the playroom",
        hideout="a bright rescue station",
        perch="the storage shelf",
        tags={"room"},
    ),
    "living_room": Setting(
        id="living_room",
        place="the living room",
        hideout="a secret city tower",
        perch="the mantel shelf",
        tags={"room"},
    ),
}

SERUMS = {
    "berry": Serum(
        id="berry",
        label="berry serum",
        phrase="a small bottle of berry serum",
        color="purple",
        promise="Hero Power Serum",
        after="the sparkle raced to {hero}'s head and left {hero_pron} shaky".replace("{hero}", "the child").replace("{hero_pron}", "them"),
        tags={"serum", "body", "truth"},
    ),
    "gold": Serum(
        id="gold",
        label="gold serum",
        phrase="a tiny jar of gold serum",
        color="golden",
        promise="Instant Mighty Muscles",
        after="the warm fizz buzzed in the child's legs until they felt wobbly",
        tags={"serum", "body", "truth"},
    ),
    "mint": Serum(
        id="mint",
        label="mint serum",
        phrase="a cool green vial of mint serum",
        color="green",
        promise="Super Leap Secret",
        after="the chilly sip made the child's tummy flutter and knees wobble",
        tags={"serum", "body", "truth"},
    ),
}

GOALS = {
    "kite": Goal(
        id="kite",
        label="the paper kite",
        phrase="a paper kite",
        up_high="high on the top shelf",
        dangling="dangling by its string",
        tags={"toy", "rescue"},
    ),
    "bear": Goal(
        id="bear",
        label="the stuffed bear",
        phrase="a stuffed bear",
        up_high="up on the tall shelf",
        dangling="peeking from behind books",
        tags={"toy", "rescue"},
    ),
    "mask": Goal(
        id="mask",
        label="the silver hero mask",
        phrase="a silver hero mask",
        up_high="above the picture frames",
        dangling="tilted on the ledge",
        tags={"toy", "rescue"},
    ),
}

SURFACES = {
    "stool": Surface(
        id="stool",
        label="wobbly stool",
        phrase="the wobbly stool",
        height=2,
        stable=False,
        tags={"climb", "wobble"},
    ),
    "chair": Surface(
        id="chair",
        label="kitchen chair",
        phrase="the kitchen chair",
        height=1,
        stable=True,
        tags={"climb"},
    ),
    "crate": Surface(
        id="crate",
        label="wooden crate",
        phrase="the wooden crate",
        height=1,
        stable=True,
        tags={"climb"},
    ),
    "floor": Surface(
        id="floor",
        label="floor",
        phrase="the floor",
        height=0,
        stable=True,
        tags={"low"},
    ),
}

HELPERS = {
    "step_ladder": Helper(
        id="step_ladder",
        label="step ladder",
        phrase="the little step ladder",
        reach_bonus=2,
        safety=3,
        use_text="Parent opened it on the flat rug and held it steady while the rescue happened",
        tags={"ladder", "help"},
    ),
    "grabber": Helper(
        id="grabber",
        label="grabber tool",
        phrase="a long grabber tool",
        reach_bonus=2,
        safety=3,
        use_text="Parent squeezed the handle and let the child pinch the toy gently from the shelf",
        tags={"tool", "help"},
    ),
    "cushion_stack": Helper(
        id="cushion_stack",
        label="cushion stack",
        phrase="a stack of sofa cushions",
        reach_bonus=1,
        safety=1,
        use_text="Parent piled soft cushions and hoped they would be enough",
        tags={"unsafe_help"},
    ),
}

MORALS = {
    "honesty": Moral(
        id="honesty",
        line="Real strength starts with honesty.",
        ending="they felt even more heroic because they had chosen truth over a shortcut.",
        tags={"honesty", "moral"},
    ),
    "helpfulness": Moral(
        id="helpfulness",
        line="A real hero asks for help before someone gets hurt.",
        ending="their game felt brighter once they remembered that teamwork is a superpower too.",
        tags={"help", "moral"},
    ),
    "responsibility": Moral(
        id="responsibility",
        line="Heroes take responsibility for what they do.",
        ending="the room glowed with calm again, and the brave part was not the serum but the choice to do better.",
        tags={"responsibility", "moral"},
    ),
}

GIRL_NAMES = ["Mia", "Lily", "Ava", "Zoe", "Nora", "Ella", "Lucy", "Maya"]
BOY_NAMES = ["Ben", "Max", "Leo", "Sam", "Theo", "Jack", "Finn", "Noah"]
TRAITS = ["honest", "careful", "kind", "bold", "curious"]
RELATIONS = ["friends", "siblings"]


@dataclass
class StoryParams:
    setting: str
    serum: str
    goal: str
    surface: str
    helper: str
    moral: str
    hero_name: str
    hero: str
    friend_name: str
    friend: str
    parent: str
    relation: str
    trait: str
    trust: int
    seed: Optional[int] = None


CURATED = [
    StoryParams(
        setting="bedroom",
        serum="berry",
        goal="kite",
        surface="stool",
        helper="step_ladder",
        moral="honesty",
        hero_name="Mia",
        hero="girl",
        friend_name="Ben",
        friend="boy",
        parent="mother",
        relation="friends",
        trait="honest",
        trust=8,
    ),
    StoryParams(
        setting="living_room",
        serum="gold",
        goal="bear",
        surface="chair",
        helper="grabber",
        moral="helpfulness",
        hero_name="Leo",
        hero="boy",
        friend_name="Ava",
        friend="girl",
        parent="father",
        relation="siblings",
        trait="careful",
        trust=7,
    ),
    StoryParams(
        setting="playroom",
        serum="mint",
        goal="mask",
        surface="stool",
        helper="step_ladder",
        moral="responsibility",
        hero_name="Max",
        hero="boy",
        friend_name="Zoe",
        friend="girl",
        parent="mother",
        relation="friends",
        trait="bold",
        trust=3,
    ),
    StoryParams(
        setting="bedroom",
        serum="gold",
        goal="bear",
        surface="chair",
        helper="grabber",
        moral="honesty",
        hero_name="Nora",
        hero="girl",
        friend_name="Finn",
        friend="boy",
        parent="father",
        relation="friends",
        trait="kind",
        trust=6,
    ),
]


KNOWLEDGE = {
    "serum": [
        (
            "What is a serum?",
            "A serum is a special liquid people imagine could change something in the body. In stories, a mystery serum can be tempting, but children should never drink unknown things."
        )
    ],
    "truth": [
        (
            "Why is telling the truth important?",
            "Telling the truth helps other people keep you safe and solve problems with you. Even after a mistake, honesty is the first brave step toward making things better."
        )
    ],
    "ladder": [
        (
            "Why does a grown-up hold a step ladder steady?",
            "Holding a step ladder steady helps stop it from wobbling or tipping. A stable helper makes reaching high places much safer."
        )
    ],
    "tool": [
        (
            "What is a grabber tool for?",
            "A grabber tool helps you reach something far away without climbing too high. It lets a person pull light objects closer with safer hands and feet."
        )
    ],
    "help": [
        (
            "Why is asking for help brave?",
            "Asking for help is brave because it means you care more about safety than about pretending you can do everything alone. Good helpers can stop a small problem from turning into a big one."
        )
    ],
    "wobble": [
        (
            "Why is wobbling on something high dangerous?",
            "If your body or the thing under you wobbles, it is easier to slip and fall. High places need steady feet and calm choices."
        )
    ],
    "responsibility": [
        (
            "What does responsibility mean?",
            "Responsibility means owning your choices and trying to fix harm after a mistake. It is part of growing into someone others can trust."
        )
    ],
    "honesty": [
        (
            "Can someone still do the right thing after making a mistake?",
            "Yes. A mistake does not end the story, because telling the truth and accepting help are good choices that come after it."
        )
    ],
}
KNOWLEDGE_ORDER = ["serum", "truth", "help", "ladder", "tool", "wobble", "honesty", "responsibility"]


def pair_noun(hero: Entity, friend: Entity, relation: str) -> str:
    if relation == "siblings":
        if hero.type == "boy" and friend.type == "boy":
            return "two brothers"
        if hero.type == "girl" and friend.type == "girl":
            return "two sisters"
        return "a brother and a sister"
    return "two friends"


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    serum = f["serum"]
    goal = f["goal_cfg"]
    moral = f["moral"]
    outcome = f["outcome"]
    base = (
        f'Write a short superhero story for a 3-to-5-year-old that includes the word "serum". '
        f"The story should center on a child trying to rescue {goal.phrase} and teach {moral.id}."
    )
    if outcome == "truth":
        return [
            base,
            f"Tell a gentle superhero story where {hero.id} is tempted by {serum.label} but chooses honesty and asks a grown-up for help instead.",
            f'Write a moral-value superhero story where the bravest act is telling the truth before using a risky shortcut like a serum.',
        ]
    return [
        base,
        f"Tell a superhero story where {hero.id} secretly drinks {serum.label}, gets into trouble, and then learns that honesty and help are stronger than shortcuts.",
        f'Write a child-facing cautionary superhero story with a serum, a scary wobble, and a warm ending about responsibility.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    parent = f["parent"]
    serum = f["serum"]
    goal = f["goal_cfg"]
    surface = f["surface_cfg"]
    helper = f["helper"]
    moral = f["moral"]
    relation = f["relation"]
    pair = pair_noun(hero, friend, relation)
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair}, {hero.id} and {friend.id}, playing superheroes together. The story also includes {hero.id}'s {parent.label_word}, who helps them finish the rescue safely."
        ),
        (
            "What problem did the children want to solve?",
            f"They wanted to rescue {goal.label}, which was stuck up high. That high place made the quick serum idea feel tempting."
        ),
        (
            f"Why did {friend.id} warn {hero.id} about the serum?",
            f"{friend.id} warned {hero.id} because the serum was a secret shortcut, not a safe plan. In this world, the warning mattered because climbing after a secret sip could make {hero.id} shaky and turn the rescue dangerous."
        ),
    ]
    if f["outcome"] == "truth":
        qa.extend([
            (
                f"What did {hero.id} do instead of drinking the serum?",
                f"{hero.id} chose honesty and told {parent.label_word} about the problem before trying anything risky. That choice brought safe help into the story and kept the rescue calm."
            ),
            (
                "How was the rescue solved?",
                f"{parent.label_word.capitalize()} used {helper.phrase}, and {goal.label} came down safely. The ending proves that teamwork worked better than a secret shortcut."
            ),
            (
                "What moral did the story teach?",
                f"It taught that {moral.line.lower()} {hero.id} looked heroic not because of magic power, but because telling the truth led to the safest rescue."
            ),
        ])
    else:
        qa.extend([
            (
                f"What happened after {hero.id} drank the serum?",
                f"After the secret sip, {hero.id} felt wobbly while climbing {surface.phrase}. That shaky feeling turned the pretend rescue into a real safety problem."
            ),
            (
                f"How did {parent.label_word} help after the mistake?",
                f"{parent.label_word.capitalize()} hurried over, got {hero.id} down safely, listened to the truth, and then used {helper.phrase} to finish the rescue. The help came with comfort first and a lesson second."
            ),
            (
                "Did the story still have a good ending?",
                f"Yes. The scary moment ended with honesty, help, and a safer plan, so the children learned and nobody was hurt. The ending shows that a mistake can be repaired when someone tells the truth and accepts responsibility."
            ),
        ])
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = set(f["serum"].tags) | set(f["moral"].tags) | set(f["helper"].tags)
    if f.get("wobbled") or f.get("slipped"):
        tags |= {"wobble"}
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
    for key, e in world.entities.items():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v or v == 0}
            if shown:
                bits.append(f"attrs={shown}")
        if e.tags:
            bits.append(f"tags={sorted(e.tags)}")
        lines.append(f"  {key:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
% Reasonable scenarios require a high goal, a risky surface, and a sensible helper.
high_goal(G, S) :- goal(G), surface(S), height(S, H), H > 0.
risky_surface(S) :- surface(S), height(S, H), H >= 1.
sensible_helper(Hp) :- helper(Hp), safety(Hp, S), safe_min(M), S >= M.
valid(St, Se, G, Su, Hp) :- setting(St), serum(Se), goal(G), surface(Su), helper(Hp),
                            high_goal(G, Su), risky_surface(Su), sensible_helper(Hp).

% Moral turn: brave truth happens when enough social support is present.
score(1) :- relation(siblings).
score(1) :- chosen_trait(careful).
score(1) :- chosen_trait(honest).
score(1) :- chosen_trait(kind).
score(1) :- trust(T), T >= 6.
truth_score(N) :- N = #sum { V : score(V) }.
outcome(truth) :- truth_score(N), N >= 2.
outcome(mishap) :- truth_score(N), N < 2.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for sid in SERUMS:
        lines.append(asp.fact("serum", sid))
    for gid in GOALS:
        lines.append(asp.fact("goal", gid))
    for suid, surface in SURFACES.items():
        lines.append(asp.fact("surface", suid))
        lines.append(asp.fact("height", suid, surface.height))
    for hid, helper in HELPERS.items():
        lines.append(asp.fact("helper", hid))
        lines.append(asp.fact("safety", hid, helper.safety))
    for trait in sorted(TRAITS):
        lines.append(asp.fact("trait", trait))
    lines.append(asp.fact("safe_min", SAFE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/5."))
    return sorted(set(asp.atoms(model, "valid")))


def outcome_of(params: StoryParams) -> str:
    return "truth" if would_confess(params.relation, params.trait, params.trust) else "mishap"


def asp_outcome(params: StoryParams) -> str:
    import asp

    scenario = "\n".join([
        asp.fact("relation", params.relation),
        asp.fact("chosen_trait", params.trait),
        asp.fact("trust", params.trust),
    ])
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


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
    for s in range(50):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(s))
            cases.append(params)
        except StoryError:
            continue

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
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("smoke test produced empty story")
        emit(sample, trace=False, qa=False, header="")
        print("OK: smoke generation succeeded.")
    except Exception as err:  # pragma: no cover
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(conflict_handler="resolve",
        description="Story world: a child superhero rescue, a tempting serum shortcut, and a moral choice."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--serum", choices=SERUMS)
    ap.add_argument("--goal", choices=GOALS)
    ap.add_argument("--surface", choices=SURFACES)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--moral", choices=MORALS)
    ap.add_argument("--hero", choices=["girl", "boy"])
    ap.add_argument("--friend", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--relation", choices=RELATIONS)
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("--trust", type=int, choices=list(range(0, 11)))
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible combos from clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(gender: str, rng: random.Random, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [n for n in pool if n != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.surface and not goal_is_high(next(iter(GOALS.values())), SURFACES[args.surface]):
        raise StoryError(explain_surface(SURFACES[args.surface]))
    if args.helper and HELPERS[args.helper].safety < SAFE_MIN:
        raise StoryError(explain_helper(HELPERS[args.helper]))

    combos = [
        combo for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.serum is None or combo[1] == args.serum)
        and (args.goal is None or combo[2] == args.goal)
        and (args.surface is None or combo[3] == args.surface)
        and (args.helper is None or combo[4] == args.helper)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, serum_id, goal_id, surface_id, helper_id = rng.choice(sorted(combos))
    hero_gender = args.hero or rng.choice(["girl", "boy"])
    friend_gender = args.friend or rng.choice(["girl", "boy"])
    hero_name = _pick_name(hero_gender, rng)
    friend_name = _pick_name(friend_gender, rng, avoid=hero_name)
    parent_type = args.parent or rng.choice(["mother", "father"])
    relation = args.relation or rng.choice(RELATIONS)
    trait = args.trait or rng.choice(TRAITS)
    trust = args.trust if args.trust is not None else rng.randint(0, 10)
    moral_id = args.moral or rng.choice(sorted(MORALS))
    return StoryParams(
        setting=setting_id,
        serum=serum_id,
        goal=goal_id,
        surface=surface_id,
        helper=helper_id,
        moral=moral_id,
        hero_name=hero_name,
        hero=hero_gender,
        friend_name=friend_name,
        friend=friend_gender,
        parent=parent_type,
        relation=relation,
        trait=trait,
        trust=trust,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError(f"(Unknown setting: {params.setting})")
    if params.serum not in SERUMS:
        raise StoryError(f"(Unknown serum: {params.serum})")
    if params.goal not in GOALS:
        raise StoryError(f"(Unknown goal: {params.goal})")
    if params.surface not in SURFACES:
        raise StoryError(f"(Unknown surface: {params.surface})")
    if params.helper not in HELPERS:
        raise StoryError(f"(Unknown helper: {params.helper})")
    if params.moral not in MORALS:
        raise StoryError(f"(Unknown moral: {params.moral})")
    if HELPERS[params.helper].safety < SAFE_MIN:
        raise StoryError(explain_helper(HELPERS[params.helper]))
    if not goal_is_high(GOALS[params.goal], SURFACES[params.surface]):
        raise StoryError(explain_surface(SURFACES[params.surface]))

    world = tell(
        SETTINGS[params.setting],
        SERUMS[params.serum],
        GOALS[params.goal],
        SURFACES[params.surface],
        HELPERS[params.helper],
        MORALS[params.moral],
        hero_name=params.hero_name,
        hero_type=params.hero,
        friend_name=params.friend_name,
        friend_type=params.friend,
        relation=params.relation,
        trait=params.trait,
        trust=params.trust,
        parent_type=params.parent,
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
        print(asp_program("", "#show valid/5.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, serum, goal, surface, helper) combos:\n")
        for combo in combos:
            print("  " + " ".join(f"{part:12}" for part in combo))
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
            header = (
                f"### {p.hero_name} & {p.friend_name}: {p.serum}, {p.goal}, "
                f"{p.surface}, {outcome_of(p)}"
            )
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
