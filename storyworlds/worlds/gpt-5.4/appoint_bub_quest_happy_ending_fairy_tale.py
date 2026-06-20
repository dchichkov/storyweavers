#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/appoint_bub_quest_happy_ending_fairy_tale.py
=======================================================================

A small fairy-tale storyworld about a ruler who must appoint little Bub to a
gentle quest. The kingdom has one small problem, Bub receives a fitting helper
and a useful charm, and the world model decides whether the quest is reasonable
and how the story's middle turn resolves.

Seed requirements rebuilt here:
- includes the words "appoint" and "bub"
- has a quest shape
- ends happily
- keeps a fairy-tale tone

Run it
------
    python storyworlds/worlds/gpt-5.4/appoint_bub_quest_happy_ending_fairy_tale.py
    python storyworlds/worlds/gpt-5.4/appoint_bub_quest_happy_ending_fairy_tale.py --realm roses --problem dew
    python storyworlds/worlds/gpt-5.4/appoint_bub_quest_happy_ending_fairy_tale.py --helper squirrel --charm lantern_seed
    python storyworlds/worlds/gpt-5.4/appoint_bub_quest_happy_ending_fairy_tale.py --all
    python storyworlds/worlds/gpt-5.4/appoint_bub_quest_happy_ending_fairy_tale.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/appoint_bub_quest_happy_ending_fairy_tale.py --verify
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


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    can_glow: bool = False
    can_climb: bool = False
    can_float: bool = False
    can_warm: bool = False
    gentle_hands: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        male = {"boy", "king", "man"}
        female = {"girl", "queen", "woman"}
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def title(self) -> str:
        return {"king": "king", "queen": "queen"}.get(self.type, self.type)


@dataclass
class Realm:
    id: str
    crown: str
    place: str
    trail: str
    palace_detail: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Problem:
    id: str
    missing: str
    need_line: str
    source_place: str
    obstacle: str
    obstacle_word: str
    item: str
    item_the: str
    fragile: bool
    terrain: str
    dark: bool = False
    cold: bool = False
    high: bool = False
    story_tags: set[str] = field(default_factory=set)


@dataclass
class Helper:
    id: str
    label: str
    speech: str
    terrain_ok: set[str]
    can_glow: bool = False
    can_climb: bool = False
    can_float: bool = False
    gentle_hands: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class Charm:
    id: str
    label: str
    phrase: str
    helps: set[str]
    glow_text: str = ""
    warmth_text: str = ""
    blessing_text: str = ""
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
        w = World()
        w.entities = copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.fired = set(self.fired)
        w.facts = copy.deepcopy(self.facts)
        return w


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_confidence(world: World) -> list[str]:
    bub = world.get("bub")
    if bub.memes["appointed"] < THRESHOLD:
        return []
    sig = ("confidence", "bub")
    if sig in world.fired:
        return []
    world.fired.add(sig)
    bub.memes["duty"] += 1
    bub.memes["hope"] += 1
    return []


def _r_comfort(world: World) -> list[str]:
    bub = world.get("bub")
    helper = world.get("helper")
    if helper.memes["encouraged"] < THRESHOLD:
        return []
    sig = ("comfort", "bub")
    if sig in world.fired:
        return []
    world.fired.add(sig)
    bub.memes["fear"] = max(0.0, bub.memes["fear"] - 1.0)
    bub.memes["hope"] += 1
    return []


def _r_recover(world: World) -> list[str]:
    item = world.get("item")
    if item.meters["found"] < THRESHOLD:
        return []
    sig = ("recover", item.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    world.get("realm").meters["trouble"] = 0.0
    world.get("realm").meters["brightness"] += 1
    return []


CAUSAL_RULES = [
    Rule("confidence", "social", _r_confidence),
    Rule("comfort", "social", _r_comfort),
    Rule("recover", "physical", _r_recover),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            made = rule.apply(world)
            if made:
                changed = True
                out.extend(made)
    if narrate:
        for line in out:
            world.say(line)
    return out


REALMS = {
    "roses": Realm(
        "roses",
        "the Rose Crown",
        "the rose kingdom",
        "a petal path that curled toward the oldest hedge",
        "The palace windows shone pink over the gardens.",
        tags={"rose", "kingdom"},
    ),
    "reeds": Realm(
        "reeds",
        "the Reed Crown",
        "the reed kingdom",
        "a silver boardwalk that whispered beside the marsh",
        "The palace stood on little stilts above the water grass.",
        tags={"marsh", "kingdom"},
    ),
    "snow": Realm(
        "snow",
        "the Snow Crown",
        "the snow kingdom",
        "a bright path of crunching frost under the moon",
        "The palace chimneys sent warm curls into the winter sky.",
        tags={"snow", "kingdom"},
    ),
}

PROBLEMS = {
    "dew": Problem(
        "dew",
        "the dawn dew pearl",
        '"Without the dawn dew pearl, the roses will wake thirsty," said the queen.',
        "the highest thorn tower in the moon hedge",
        "a thorny wall too high for small boots",
        "thorns",
        "the dew pearl",
        "the dew pearl",
        fragile=True,
        terrain="high",
        high=True,
        story_tags={"dew", "pearl"},
    ),
    "lantern": Problem(
        "lantern",
        "the moon-lantern flame",
        '"Without the moon-lantern flame, the path home will stay dark," said the king.',
        "a cave beneath the willow hill",
        "a tunnel full of dark turns",
        "darkness",
        "the moon-lantern flame",
        "the moon-lantern flame",
        fragile=False,
        terrain="dark",
        dark=True,
        story_tags={"light", "lantern"},
    ),
    "spring": Problem(
        "spring",
        "the spring bell's warm note",
        '"Without the spring bell\'s warm note, the brook will stay asleep under ice," said the queen.',
        "an icy stone in the middle of the brook",
        "a ribbon of cold water and sharp wind",
        "cold",
        "the spring note",
        "the spring note",
        fragile=False,
        terrain="cold",
        cold=True,
        story_tags={"spring", "brook"},
    ),
}

HELPERS = {
    "squirrel": Helper(
        "squirrel",
        "a red squirrel",
        '"Quick paws and a brave tail can help a small heart," chirped the squirrel.',
        {"high"},
        can_climb=True,
        gentle_hands=True,
        tags={"squirrel", "climb"},
    ),
    "firefly": Helper(
        "firefly",
        "a gold firefly",
        '"Even a tiny lamp can make a brave road," hummed the firefly.',
        {"dark"},
        can_glow=True,
        tags={"firefly", "light"},
    ),
    "otter": Helper(
        "otter",
        "a river otter",
        '"Cold water is kinder when shared," laughed the otter.',
        {"cold"},
        can_float=True,
        gentle_hands=True,
        tags={"otter", "water"},
    ),
    "swan": Helper(
        "swan",
        "a white swan",
        '"Sit steady, little bub, and I will carry you like a boat," sang the swan.',
        {"cold"},
        can_float=True,
        gentle_hands=True,
        tags={"swan", "water"},
    ),
}

CHARMS = {
    "lantern_seed": Charm(
        "lantern_seed",
        "lantern seed",
        "a lantern seed in a silver acorn cap",
        {"dark"},
        glow_text="The lantern seed opened like a tiny star and spilled kind gold light.",
        tags={"light", "seed"},
    ),
    "wool_scraf": Charm(
        "wool_scraf",
        "sun-wool scarf",
        "a sun-wool scarf soft as toast steam",
        {"cold"},
        warmth_text="The scarf kept Bub warm even when the brook sent up a cold breath.",
        tags={"warmth", "scarf"},
    ),
    "moss_glove": Charm(
        "moss_glove",
        "moss glove",
        "a moss glove stitched by the palace mice",
        {"fragile"},
        blessing_text="The moss glove made Bub's hands soft and steady, gentle enough for the smallest treasure.",
        tags={"gentle", "glove"},
    ),
}

GIRL_NAMES = ["Lina", "Mira", "Nell", "Ava", "Elsie", "Wren"]
BOY_NAMES = ["Bub", "Pip", "Finn", "Oren", "Theo", "Milo"]
TRAITS = ["small", "kind", "steady", "bright-eyed", "patient", "gentle"]


def helper_fits(problem: Problem, helper: Helper) -> bool:
    return problem.terrain in helper.terrain_ok


def charm_fits(problem: Problem, charm: Charm) -> bool:
    if problem.dark and "dark" not in charm.helps:
        return False
    if problem.cold and "cold" not in charm.helps:
        return False
    if problem.fragile and "fragile" not in charm.helps:
        return False
    if not (problem.dark or problem.cold or problem.fragile):
        return True
    return True


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for realm in REALMS:
        for pid, problem in PROBLEMS.items():
            for hid, helper in HELPERS.items():
                for cid, charm in CHARMS.items():
                    if helper_fits(problem, helper) and charm_fits(problem, charm):
                        combos.append((realm, pid, hid, cid))
    return combos


def explain_rejection(problem: Problem, helper: Helper, charm: Charm) -> str:
    if not helper_fits(problem, helper):
        return (
            f"(No story: {helper.label} is not a good match for {problem.obstacle}. "
            f"This quest needs a helper suited to {problem.obstacle_word}.)"
        )
    if not charm_fits(problem, charm):
        need = []
        if problem.dark:
            need.append("light")
        if problem.cold:
            need.append("warmth")
        if problem.fragile:
            need.append("gentle hands")
        return (
            f"(No story: {charm.label} does not solve the quest's need for "
            f"{', '.join(need)}.)"
        )
    return "(No story: this quest setup is not reasonable.)"


def quest_success(problem: Problem, helper: Helper, charm: Charm) -> bool:
    return helper_fits(problem, helper) and charm_fits(problem, charm)


def predict_success(world: World) -> bool:
    sim = world.copy()
    problem = sim.facts["problem"]
    helper = sim.facts["helper_cfg"]
    charm = sim.facts["charm_cfg"]
    return quest_success(problem, helper, charm)


def opening(world: World, ruler: Entity, bub: Entity, realm: Realm) -> None:
    bub.memes["wonder"] += 1
    world.say(
        f"In {realm.place}, where morning liked to linger on every leaf, there lived a little page named {bub.id}."
    )
    world.say(realm.palace_detail)
    world.say(
        f"{bub.id} was a {bub.attrs['trait']} child, so small that the cooks called {bub.pronoun('object')} their sweet bub and tucked honey crumbs into {bub.pronoun('possessive')} pocket."
    )


def trouble(world: World, ruler: Entity, problem: Problem) -> None:
    world.get("realm").meters["trouble"] += 1
    world.say(
        f"One twilight, a hush drifted through the court: {problem.missing} was missing from {problem.source_place}."
    )
    world.say(problem.need_line)


def appoint_bub(world: World, ruler: Entity, bub: Entity, helper: Helper, charm: Charm) -> None:
    bub.memes["appointed"] += 1
    bub.memes["fear"] += 1
    propagate(world, narrate=False)
    world.say(
        f'The {ruler.title} lifted a hand. "I appoint {bub.id} to the quest," {ruler.pronoun()} said. "A small traveler may pass where heavy boots cannot."'
    )
    world.say(
        f"{bub.id}'s knees shook a little, yet {bub.pronoun()} bowed all the same."
    )
    world.say(
        f"To help, the {ruler.title} sent {helper.label} and gave {bub.pronoun('object')} {charm.phrase}."
    )


def set_out(world: World, bub: Entity, helper: Helper, realm: Realm) -> None:
    helper_ent = world.get("helper")
    helper_ent.memes["encouraged"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Together they followed {realm.trail}. Dew shone, reeds whispered, or frost chimed underfoot, and the whole kingdom seemed to listen."
    )
    world.say(f"{helper.speech}")


def face_obstacle(world: World, bub: Entity, problem: Problem, charm: Charm) -> None:
    world.say(
        f"At last they came to {problem.source_place}, but between them and {problem.item} lay {problem.obstacle}."
    )
    if problem.dark and charm.glow_text:
        world.say(charm.glow_text)
        world.get("charm").meters["used"] += 1
    if problem.cold and charm.warmth_text:
        world.say(charm.warmth_text)
        world.get("charm").meters["used"] += 1
    if problem.fragile and charm.blessing_text:
        world.say(charm.blessing_text)
        world.get("charm").meters["used"] += 1


def retrieve(world: World, bub: Entity, helper: Helper, problem: Problem) -> None:
    item = world.get("item")
    if problem.high:
        world.say(
            f"{helper.label.capitalize()} scrambled up first, and {bub.id} followed the safest little footholds. At the top, {bub.id} cupped {problem.item_the} as carefully as a breath."
        )
    elif problem.dark:
        world.say(
            f"With the golden light before them, {bub.id} and {helper.label} found the hidden niche. {bub.id} reached in and lifted {problem.item_the} before the shadows could swallow it again."
        )
    elif problem.cold:
        world.say(
            f"{helper.label.capitalize()} bore {bub.id} across the cold water. From the icy stone, {bub.id} gathered {problem.item_the} and held it close."
        )
    item.meters["found"] += 1
    world.get("bub").memes["courage"] += 1
    propagate(world, narrate=False)


def return_home(world: World, ruler: Entity, bub: Entity, problem: Problem) -> None:
    world.say(
        f"When they returned to the palace, {bub.id} placed {problem.item_the} in the {ruler.title}'s hands."
    )
    if problem.id == "dew":
        world.say(
            "At once the thirsty roses opened, each cup full of silver sparkle, and the whole garden smelled awake."
        )
    elif problem.id == "lantern":
        world.say(
            "At once the moon-lantern shone again, and every path through the kingdom turned soft and safe and bright."
        )
    else:
        world.say(
            "At once the spring bell rang its warm note, the brook laughed loose from the ice, and little green shoots nodded along the bank."
        )


def reward(world: World, ruler: Entity, bub: Entity, helper: Helper) -> None:
    bub.memes["joy"] += 1
    bub.memes["belonging"] += 1
    world.say(
        f'The {ruler.title} smiled. "You were brave and gentle, {bub.id}. A quest does not ask for the biggest traveler, only the right one."'
    )
    world.say(
        f"Then the court cheered, {helper.label} was given a dish of sugared berries, and {bub.id} was appointed Keeper of Little Roads, so no small good deed would ever be overlooked again."
    )
    world.say(
        f"That night {bub.id} fell asleep under a warm quilt, smiling to think that even a little bub could help a whole kingdom bloom."
    )


def tell(
    realm: Realm,
    problem: Problem,
    helper: Helper,
    charm: Charm,
    bub_name: str = "Bub",
    bub_gender: str = "boy",
    ruler_type: str = "queen",
    trait: str = "kind",
) -> World:
    world = World()
    ruler = world.add(Entity(id="Ruler", kind="character", type=ruler_type, role="ruler", label="the ruler"))
    bub = world.add(Entity(id=bub_name, kind="character", type=bub_gender, role="hero", attrs={"trait": trait}))
    world.add(Entity(id="realm", type="realm", label=realm.place))
    world.add(Entity(
        id="helper",
        type="helper",
        label=helper.label,
        role="helper",
        can_glow=helper.can_glow,
        can_climb=helper.can_climb,
        can_float=helper.can_float,
        gentle_hands=helper.gentle_hands,
    ))
    world.add(Entity(id="charm", type="charm", label=charm.label))
    world.add(Entity(id="item", type="treasure", label=problem.item))
    world.facts.update(realm=realm, problem=problem, helper_cfg=helper, charm_cfg=charm, ruler=ruler, bub=bub)

    opening(world, ruler, bub, realm)
    trouble(world, ruler, problem)
    world.para()
    appoint_bub(world, ruler, bub, helper, charm)
    set_out(world, bub, helper, realm)
    world.para()
    face_obstacle(world, bub, problem, charm)
    retrieve(world, bub, helper, problem)
    world.para()
    return_home(world, ruler, bub, problem)
    reward(world, ruler, bub, helper)

    world.facts.update(
        success=world.get("item").meters["found"] >= THRESHOLD,
        item_label=problem.item,
        obstacle=problem.obstacle,
        used_charm=world.get("charm").meters["used"] >= THRESHOLD,
    )
    return world


@dataclass
class StoryParams:
    realm: str
    problem: str
    helper: str
    charm: str
    bub_name: str
    bub_gender: str
    ruler: str
    trait: str
    seed: Optional[int] = None


KNOWLEDGE = {
    "rose": [(
        "Why do flowers need water or dew?",
        "Flowers need water to stay fresh and stand up strong. Without enough water, their petals can droop."
    )],
    "light": [(
        "Why is a lantern helpful in the dark?",
        "A lantern helps you see where to step and what is around you. Light makes a path safer."
    )],
    "snow": [(
        "Why does a brook freeze in winter?",
        "A brook can freeze when the air is very cold. The water turns to ice on top and may slow underneath."
    )],
    "squirrel": [(
        "Why is a squirrel good at climbing?",
        "A squirrel has quick paws and a balancing tail. That helps it move up trees and high places."
    )],
    "firefly": [(
        "What is a firefly?",
        "A firefly is a little insect that can glow. Its soft light shines in the dark."
    )],
    "otter": [(
        "Why are otters good in water?",
        "Otters are strong swimmers with bodies made for rivers. They can float and paddle very well."
    )],
    "swan": [(
        "How can a swan help on water?",
        "A swan can glide across water smoothly. In a fairy tale, it can carry someone like a little boat."
    )],
    "warmth": [(
        "Why do scarves help in cold weather?",
        "A scarf helps keep your body warm by holding heat close. That makes cold wind feel less sharp."
    )],
    "gentle": [(
        "What does it mean to have gentle hands?",
        "Gentle hands move softly and carefully. They help keep fragile things from breaking."
    )],
    "kingdom": [(
        "What is a kingdom?",
        "A kingdom is a land in stories that is ruled by a king or queen. Fairy tales often begin there."
    )],
}
KNOWLEDGE_ORDER = ["kingdom", "rose", "light", "snow", "squirrel", "firefly", "otter", "swan", "warmth", "gentle"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    bub = f["bub"]
    problem = f["problem"]
    helper = f["helper_cfg"]
    return [
        f'Write a fairy tale for a young child that uses the words "appoint" and "{bub.id.lower()}". Make it a quest with a happy ending.',
        f"Tell a gentle quest story where a ruler must appoint little {bub.id} to recover {problem.item} with help from {helper.label}.",
        f"Write a fairy-tale story in which a small child proves to a whole kingdom that being little can still be exactly right for a quest.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    bub = f["bub"]
    ruler = f["ruler"]
    problem = f["problem"]
    helper = f["helper_cfg"]
    charm = f["charm_cfg"]
    qa = [
        (
            "Who is the story about?",
            f"It is about {bub.id}, a little palace page, and the {ruler.title} who trusted {bub.pronoun('object')} with an important quest. It is also about {helper.label}, who went along to help."
        ),
        (
            f"Why did the {ruler.title} appoint {bub.id}?",
            f"The {ruler.title} appointed {bub.id} because the kingdom needed {problem.item}, and a small traveler could reach the place more easily. The choice showed that the quest needed the right helper, not simply the biggest one."
        ),
        (
            f"What problem did the kingdom have?",
            f"{problem.missing.capitalize()} was missing, and that put the kingdom in trouble. {problem.need_line.strip('\"')}"
        ),
        (
            f"How did {helper.label} and the charm help {bub.id}?",
            f"{helper.label.capitalize()} helped with {problem.obstacle}, and {charm.label} solved the hardest part of the journey. Together they turned a frightening place into one {bub.id} could cross safely."
        ),
    ]
    if f["success"]:
        qa.append((
            f"How did the quest end?",
            f"{bub.id} brought back {problem.item_the}, and the kingdom changed right away for the better. The ending proves the quest worked because the flowers woke, the lantern shone, or the brook ran free again."
        ))
        qa.append((
            f"What did {bub.id} learn?",
            f"{bub.id} learned that being small did not make {bub.pronoun('object')} weak. It made {bub.pronoun('object')} exactly right for a gentle and brave kind of task."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = set(world.facts["realm"].tags) | set(world.facts["problem"].story_tags)
    tags |= set(world.facts["helper_cfg"].tags) | set(world.facts["charm_cfg"].tags)
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
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        flags = []
        for name in ("can_glow", "can_climb", "can_float", "can_warm", "gentle_hands"):
            if getattr(e, name):
                flags.append(name)
        if flags:
            bits.append(f"flags={flags}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams("roses", "dew", "squirrel", "moss_glove", "Bub", "boy", "queen", "gentle"),
    StoryParams("reeds", "lantern", "firefly", "lantern_seed", "Bub", "boy", "king", "steady"),
    StoryParams("snow", "spring", "otter", "wool_scraf", "Bub", "boy", "queen", "kind"),
    StoryParams("snow", "spring", "swan", "wool_scraf", "Bub", "boy", "king", "patient"),
]


ASP_RULES = r"""
fits_helper(P, H) :- problem(P), helper(H), terrain_need(P, T), helper_handles(H, T).
needs_dark(P) :- problem(P), dark(P).
needs_cold(P) :- problem(P), cold(P).
needs_fragile(P) :- problem(P), fragile(P).

fits_charm(P, C) :- problem(P), charm(C),
                    not needs_dark(P), not needs_cold(P), not needs_fragile(P).
fits_charm(P, C) :- problem(P), charm(C), needs_dark(P), helps(C, dark),
                    not needs_cold(P), not needs_fragile(P).
fits_charm(P, C) :- problem(P), charm(C), needs_cold(P), helps(C, cold),
                    not needs_dark(P), not needs_fragile(P).
fits_charm(P, C) :- problem(P), charm(C), needs_fragile(P), helps(C, fragile),
                    not needs_dark(P), not needs_cold(P).

valid(R, P, H, C) :- realm(R), fits_helper(P, H), fits_charm(P, C).
success(P, H, C) :- fits_helper(P, H), fits_charm(P, C).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for rid in REALMS:
        lines.append(asp.fact("realm", rid))
    for pid, p in PROBLEMS.items():
        lines.append(asp.fact("problem", pid))
        lines.append(asp.fact("terrain_need", pid, p.terrain))
        if p.dark:
            lines.append(asp.fact("dark", pid))
        if p.cold:
            lines.append(asp.fact("cold", pid))
        if p.fragile:
            lines.append(asp.fact("fragile", pid))
    for hid, h in HELPERS.items():
        lines.append(asp.fact("helper", hid))
        for t in sorted(h.terrain_ok):
            lines.append(asp.fact("helper_handles", hid, t))
    for cid, c in CHARMS.items():
        lines.append(asp.fact("charm", cid))
        for need in sorted(c.helps):
            lines.append(asp.fact("helps", cid, need))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_success(problem: str, helper: str, charm: str) -> bool:
    import asp

    extra = "\n".join([
        asp.fact("chosen_problem", problem),
        asp.fact("chosen_helper", helper),
        asp.fact("chosen_charm", charm),
        "ok :- chosen_problem(P), chosen_helper(H), chosen_charm(C), success(P,H,C).",
    ])
    model = asp.one_model(asp_program(extra, "#show ok/0."))
    return bool(getattr(model, "symbols", lambda *args, **kwargs: [])(shown=True)) or bool(asp.atoms(model, "ok"))


def asp_verify() -> int:
    rc = 0
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: gate matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if cl - py:
            print("  only in clingo:", sorted(cl - py))
        if py - cl:
            print("  only in python:", sorted(py - cl))

    for params in CURATED:
        py_ok = quest_success(PROBLEMS[params.problem], HELPERS[params.helper], CHARMS[params.charm])
        cl_ok = asp_success(params.problem, params.helper, params.charm)
        if py_ok != cl_ok:
            rc = 1
            print("MISMATCH in success model:", params)
            break
    else:
        print(f"OK: success model matches on {len(CURATED)} curated scenarios.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("Generated empty story during verify smoke test.")
        print("OK: smoke-tested normal story generation.")
    except Exception as exc:  # pragma: no cover
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Fairy-tale quest storyworld: a ruler appoints Bub to a gentle quest."
    )
    ap.add_argument("--realm", choices=REALMS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--charm", choices=CHARMS)
    ap.add_argument("--ruler", choices=["queen", "king"])
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid quest combinations derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.problem and args.helper and args.charm:
        p = PROBLEMS[args.problem]
        h = HELPERS[args.helper]
        c = CHARMS[args.charm]
        if not (helper_fits(p, h) and charm_fits(p, c)):
            raise StoryError(explain_rejection(p, h, c))

    combos = [
        c for c in valid_combos()
        if (args.realm is None or c[0] == args.realm)
        and (args.problem is None or c[1] == args.problem)
        and (args.helper is None or c[2] == args.helper)
        and (args.charm is None or c[3] == args.charm)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    realm, problem, helper, charm = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    if args.name:
        name = args.name
    else:
        if gender == "boy":
            name = rng.choice(BOY_NAMES)
        else:
            name = rng.choice(GIRL_NAMES)
    ruler = args.ruler or rng.choice(["queen", "king"])
    trait = rng.choice(TRAITS)
    return StoryParams(realm, problem, helper, charm, name, gender, ruler, trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        REALMS[params.realm],
        PROBLEMS[params.problem],
        HELPERS[params.helper],
        CHARMS[params.charm],
        bub_name=params.bub_name,
        bub_gender=params.bub_gender,
        ruler_type=params.ruler,
        trait=params.trait,
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
        print(asp_program("", "#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} valid (realm, problem, helper, charm) combos:\n")
        for realm, problem, helper, charm in combos:
            print(f"  {realm:7} {problem:8} {helper:9} {charm}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
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
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.bub_name}: {p.problem} in {p.realm} ({p.helper}, {p.charm})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
