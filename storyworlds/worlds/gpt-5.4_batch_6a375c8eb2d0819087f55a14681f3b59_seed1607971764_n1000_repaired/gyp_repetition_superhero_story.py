#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/gyp_repetition_superhero_story.py
============================================================

A standalone story world for a tiny superhero-style domain: a child in a cape
spots a neighborhood problem, almost treats it like a comic-book leap, then
learns that real heroes think first, ask for help, and use the right tool.

This world is built around deliberate repetition in the prose:

    "Cape tight, eyes bright, help in sight!"

The line appears as a playful boast, then as a warning reminder, and finally as
a changed ending motto that proves the hero learned what being brave really
means.

The required seed word appears as the name of the hero's little robot sidekick:
gyp.

Run it
------
    python storyworlds/worlds/gpt-5.4/gyp_repetition_superhero_story.py
    python storyworlds/worlds/gpt-5.4/gyp_repetition_superhero_story.py --setting courtyard --trouble kitten --tool ladder
    python storyworlds/worlds/gpt-5.4/gyp_repetition_superhero_story.py --trouble kitten --tool long_grabber
    python storyworlds/worlds/gpt-5.4/gyp_repetition_superhero_story.py --all
    python storyworlds/worlds/gpt-5.4/gyp_repetition_superhero_story.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/gyp_repetition_superhero_story.py --verify
"""

from __future__ import annotations

import argparse
import contextlib
import copy
import io
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
MOTTO = "Cape tight, eyes bright, help in sight!"
CAREFUL_TRAITS = {"careful", "thoughtful", "steady", "gentle"}


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "aunt", "librarian"}
        male = {"boy", "father", "man", "janitor"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type
    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)


@dataclass
class Setting:
    id: str
    place: str
    skyline: str
    helper_name: str
    helper_type: str
    helper_label: str
    affords: set[str] = field(default_factory=set)
    stores: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


@dataclass
class Trouble:
    id: str
    label: str
    the: str
    owner_kind: str
    cry: str
    spot: str
    height: int
    living: bool = False
    fragile: bool = False
    heavy: bool = False
    tags: set[str] = field(default_factory=set)

    @property
    def The(self) -> str:
        return self.the[0].upper() + self.the[1:]
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    reach: int
    adult_only: bool
    handles_living: bool
    handles_fragile: bool
    handles_heavy: bool
    action: str
    team_action: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


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
        clone = World(self.setting)
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
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


def _r_stuck_worry(world: World) -> list[str]:
    out: list[str] = []
    trouble = world.get("trouble")
    hero = world.get("hero")
    owner = world.get("owner")
    if trouble.meters["stuck"] >= THRESHOLD and ("stuck_worry",) not in world.fired:
        world.fired.add(("stuck_worry",))
        hero.memes["concern"] += 1
        owner.memes["worry"] += 1
        out.append("__worry__")
    return out


def _r_jump_risk(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    trouble = world.get("trouble")
    scene = world.get("scene")
    if hero.meters["jump_attempt"] >= THRESHOLD and trouble.attrs.get("height", 0) >= 2:
        if ("jump_risk",) not in world.fired:
            world.fired.add(("jump_risk",))
            scene.meters["risk"] += 1
            trouble.meters["wobble"] += 1
            hero.memes["alarm"] += 1
            out.append("__risk__")
    return out


def _r_rescue_relief(world: World) -> list[str]:
    out: list[str] = []
    trouble = world.get("trouble")
    hero = world.get("hero")
    owner = world.get("owner")
    if trouble.meters["rescued"] >= THRESHOLD and ("rescue_relief",) not in world.fired:
        world.fired.add(("rescue_relief",))
        trouble.meters["stuck"] = 0.0
        owner.memes["relief"] += 1
        hero.memes["pride"] += 1
        hero.memes["care"] += 1
        out.append("__relief__")
    return out


CAUSAL_RULES = [
    Rule(name="stuck_worry", tag="emotion", apply=_r_stuck_worry),
    Rule(name="jump_risk", tag="physical", apply=_r_jump_risk),
    Rule(name="rescue_relief", tag="emotion", apply=_r_rescue_relief),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
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


def compatible(setting: Setting, trouble: Trouble, tool: Tool) -> bool:
    if trouble.id not in setting.affords:
        return False
    if tool.id not in setting.stores:
        return False
    if tool.reach < trouble.height:
        return False
    if trouble.living and not tool.handles_living:
        return False
    if trouble.fragile and not tool.handles_fragile:
        return False
    if trouble.heavy and not tool.handles_heavy:
        return False
    return True


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for setting_id, setting in SETTINGS.items():
        for trouble_id, trouble in TROUBLES.items():
            for tool_id, tool in TOOLS.items():
                if compatible(setting, trouble, tool):
                    combos.append((setting_id, trouble_id, tool_id))
    return combos


def outcome_of(params: "StoryParams") -> str:
    if params.trait in CAREFUL_TRAITS:
        return "steady"
    trouble = TROUBLES[params.trouble]
    tool = TOOLS[params.tool]
    if trouble.height >= 2 or tool.adult_only:
        return "leap_stopped"
    return "quick_reach"


def predict_jump(world: World) -> dict:
    sim = world.copy()
    hero = sim.get("hero")
    hero.meters["jump_attempt"] += 1
    propagate(sim, narrate=False)
    return {
        "risk": sim.get("scene").meters["risk"],
        "wobble": sim.get("trouble").meters["wobble"],
    }


def introduce(world: World, hero: Entity, gyp: Entity) -> None:
    world.say(
        f"{hero.id} liked to tie on a bright cape and race through {world.setting.place} "
        f"as if the whole block were a comic book. At {hero.pronoun('possessive')} heel "
        f"rolled a little silver robot named {gyp.id}, whose eyes blinked blue when a mission began."
    )
    world.say(
        f'Together they always whispered the same line before doing anything brave: '
        f'"{MOTTO}"'
    )


def show_place(world: World) -> None:
    world.say(world.setting.skyline)


def reveal_trouble(world: World, owner: Entity, trouble: Entity, trouble_cfg: Trouble) -> None:
    trouble.meters["stuck"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Then a small cry cut through the afternoon. {owner.id} pointed and gasped, "
        f'"{trouble_cfg.cry}" {trouble_cfg.The} was {trouble_cfg.spot}.'
    )
    if trouble_cfg.living:
        world.say(
            f"{trouble_cfg.The} made a tiny frightened sound, and {owner.id}'s eyes filled with tears."
        )
    else:
        world.say(
            f"It bobbed and trembled there, too far up for little hands to reach."
        )


def vow_help(world: World, hero: Entity, owner: Entity, trouble_cfg: Trouble) -> None:
    hero.memes["bravery"] += 1
    world.say(
        f'{hero.id} put a hand on {owner.id}\'s shoulder. "I see it," {hero.pronoun()} said. '
        f'"{MOTTO}"'
    )
    if trouble_cfg.living:
        world.say(
            f"But because {trouble_cfg.the} was alive and scared, {hero.id} kept {hero.pronoun('possessive')} voice soft."
        )
    else:
        world.say(
            f"The words sounded big and shiny, the way superhero words are supposed to sound."
        )


def risky_idea(world: World, hero: Entity, gyp: Entity, trouble_cfg: Trouble, outcome: str) -> None:
    if outcome == "steady":
        hero.memes["restraint"] += 1
        world.say(
            f"{hero.id} bent {hero.pronoun('possessive')} knees for one second, then looked more carefully. "
            f"{gyp.id}'s blue eyes reflected in the cape buckle, and {hero.pronoun()} remembered that a real hero thinks before leaping."
        )
        return
    hero.meters["jump_attempt"] += 1
    prediction = predict_jump(world)
    world.facts["predicted_risk"] = prediction["risk"]
    world.facts["predicted_wobble"] = prediction["wobble"]
    propagate(world, narrate=False)
    world.say(
        f"{hero.id} backed up three quick steps. {hero.pronoun().capitalize()} was ready for a super jump."
    )
    if prediction["risk"] >= THRESHOLD:
        world.say(
            f'But {gyp.id} beeped and flashed a warning on {gyp.pronoun("possessive")} tiny screen: '
            f'"Too wobbly. Too risky. {MOTTO}"'
        )
        hero.memes["restraint"] += 1
        hero.meters["jump_attempt"] = 0.0
        world.say(
            f"The repeated words landed differently that time. They did not mean jump higher. "
            f"They meant look harder and help smarter."
        )
    else:
        world.say(
            f"{gyp.id} made a bright happy trill. This one looked close enough from the ground."
        )


def call_helper(world: World, hero: Entity, helper: Entity, tool_cfg: Tool, outcome: str) -> None:
    hero.memes["trust"] += 1
    if tool_cfg.adult_only or outcome == "leap_stopped":
        world.say(
            f'{hero.id} raised {hero.pronoun("possessive")} hand and called to {helper.id}, '
            f'"We need {tool_cfg.phrase}!"'
        )
    else:
        world.say(
            f'{hero.id} spotted {tool_cfg.phrase} nearby and waved to {helper.id} just in case.'
        )
    world.say(
        f"{helper.id}, {world.setting.helper_label}, came over at once instead of laughing at the cape."
    )


def rescue(world: World, hero: Entity, owner: Entity, helper: Entity,
           trouble: Entity, trouble_cfg: Trouble, tool_cfg: Tool, outcome: str) -> None:
    trouble.attrs["tool"] = tool_cfg.id
    if tool_cfg.adult_only:
        world.say(
            f"{helper.id} steadied {tool_cfg.phrase}, and {hero.id} stood below with arms ready and eyes wide."
        )
        if trouble_cfg.living:
            world.say(
                f"{hero.id} spoke in a calm whisper. Then {helper.id} {tool_cfg.team_action.format(target=trouble_cfg.label)}."
            )
        else:
            world.say(
                f"With one careful reach, {helper.id} {tool_cfg.team_action.format(target=trouble_cfg.label)}."
            )
    else:
        world.say(
            f"{helper.id} handed {hero.id} {tool_cfg.phrase}. {hero.pronoun().capitalize()} took a slow breath and {tool_cfg.action.format(target=trouble_cfg.label)}."
        )
    trouble.meters["rescued"] += 1
    propagate(world, narrate=False)
    if trouble_cfg.living:
        world.say(
            f"{trouble_cfg.The} came down safe at last and tucked itself against warm arms."
        )
    else:
        world.say(
            f"{trouble_cfg.The} came down without a rip, splash, or bump."
        )
    world.say(
        f"{owner.id}'s face changed from crumpled worry to a bright, round smile."
    )


def ending(world: World, hero: Entity, gyp: Entity, owner: Entity,
           trouble_cfg: Trouble, tool_cfg: Tool, outcome: str) -> None:
    hero.memes["joy"] += 1
    world.say(
        f'"Thank you, Super {hero.id}!" {owner.id} said.'
    )
    if outcome == "steady":
        world.say(
            f'{hero.id} touched the cape, then smiled at {gyp.id}. "{MOTTO}" {hero.pronoun()} said again, '
            f"and now the words felt quieter and truer."
        )
    elif outcome == "quick_reach":
        world.say(
            f'{gyp.id} spun in a happy circle. "{MOTTO}" {hero.id} repeated, this time with both feet planted safely on the ground.'
        )
    else:
        world.say(
            f'{hero.id} looked up at the place where {trouble_cfg.the} had been and whispered, '
            f'"{MOTTO}" One more time, the line no longer sounded like a boast. It sounded like a plan.'
        )
    if tool_cfg.adult_only:
        world.say(
            f"From then on, whenever a mission looked tall or tricky, {hero.id} remembered that asking a grown-up to join the team was part of being brave."
        )
    else:
        world.say(
            f"From then on, {hero.id} remembered that the best superhero move was not the flashiest one. It was the one that brought everyone home safe."
        )


def tell(setting: Setting, trouble_cfg: Trouble, tool_cfg: Tool,
         hero_name: str = "Maya", hero_type: str = "girl",
         owner_name: str = "Nico", owner_type: str = "boy",
         trait: str = "careful") -> World:
    world = World(setting)
    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type=hero_type,
        role="hero",
        traits=[trait, "imaginative"],
    ))
    gyp = world.add(Entity(
        id="gyp",
        kind="character",
        type="robot",
        role="sidekick",
        tags={"robot"},
    ))
    owner = world.add(Entity(
        id=owner_name,
        kind="character",
        type=owner_type,
        role="owner",
        attrs={"owner_kind": trouble_cfg.owner_kind},
    ))
    helper = world.add(Entity(
        id=setting.helper_name,
        kind="character",
        type=setting.helper_type,
        role="helper",
        label=setting.helper_label,
    ))
    scene = world.add(Entity(
        id="scene",
        type="place",
        label=setting.place,
    ))
    trouble = world.add(Entity(
        id="trouble",
        type="trouble",
        label=trouble_cfg.label,
        attrs={
            "height": trouble_cfg.height,
            "living": trouble_cfg.living,
            "fragile": trouble_cfg.fragile,
            "heavy": trouble_cfg.heavy,
        },
        tags=set(trouble_cfg.tags),
    ))
    tool = world.add(Entity(
        id="tool",
        type="tool",
        label=tool_cfg.label,
        attrs={
            "reach": tool_cfg.reach,
            "adult_only": tool_cfg.adult_only,
        },
        tags=set(tool_cfg.tags),
    ))
    world.facts.update(
        setting=setting,
        trouble_cfg=trouble_cfg,
        tool_cfg=tool_cfg,
        hero=hero,
        gyp=gyp,
        owner=owner,
        helper=helper,
        scene=scene,
        trouble=trouble,
        tool=tool,
        motto=MOTTO,
    )

    outcome = "steady" if trait in CAREFUL_TRAITS else (
        "leap_stopped" if (trouble_cfg.height >= 2 or tool_cfg.adult_only) else "quick_reach"
    )
    world.facts["outcome"] = outcome

    introduce(world, hero, gyp)
    show_place(world)
    reveal_trouble(world, owner, trouble, trouble_cfg)

    world.para()
    vow_help(world, hero, owner, trouble_cfg)
    risky_idea(world, hero, gyp, trouble_cfg, outcome)
    call_helper(world, hero, helper, tool_cfg, outcome)

    world.para()
    rescue(world, hero, owner, helper, trouble, trouble_cfg, tool_cfg, outcome)
    ending(world, hero, gyp, owner, trouble_cfg, tool_cfg, outcome)
    world.facts["rescued"] = trouble.meters["rescued"] >= THRESHOLD
    world.facts["risk_seen"] = world.get("scene").meters["risk"] >= THRESHOLD
    return world


SETTINGS = {
    "courtyard": Setting(
        id="courtyard",
        place="the apartment courtyard",
        skyline="Laundry lines fluttered overhead, and the brick walls made every shout bounce back like a comic-book echo.",
        helper_name="Mrs. Vale",
        helper_type="woman",
        helper_label="the neighbor with the key ring",
        affords={"kitten", "balloon"},
        stores={"ladder", "rescue_net"},
        tags={"courtyard"},
    ),
    "playground": Setting(
        id="playground",
        place="the playground by the fence",
        skyline="The slide flashed in the sun, and the monkey bars stretched across the sandbox like silver training beams.",
        helper_name="Coach Ben",
        helper_type="man",
        helper_label="the playground coach",
        affords={"balloon", "hat"},
        stores={"rescue_net", "ladder"},
        tags={"playground"},
    ),
    "schoolyard": Setting(
        id="schoolyard",
        place="the schoolyard after class",
        skyline="Paper rockets still lay near the blacktop, and the flag rope clicked softly in the breeze.",
        helper_name="Mr. Hall",
        helper_type="janitor",
        helper_label="the janitor with the tool cart",
        affords={"hat", "backpack"},
        stores={"long_grabber", "rescue_net"},
        tags={"school"},
    ),
    "parade_route": Setting(
        id="parade_route",
        place="the little parade route on Maple Street",
        skyline="Silver streamers snapped above the curb, and every window seemed to watch the street like a row of friendly eyes.",
        helper_name="Officer Luz",
        helper_type="woman",
        helper_label="the crossing guard in a bright vest",
        affords={"balloon", "backpack"},
        stores={"rescue_net", "long_grabber"},
        tags={"street"},
    ),
}

TROUBLES = {
    "kitten": Trouble(
        id="kitten",
        label="kitten",
        the="the kitten",
        owner_kind="pet",
        cry="My kitten!",
        spot="stuck on a low tree branch near the wall",
        height=3,
        living=True,
        fragile=True,
        heavy=False,
        tags={"kitten", "tree", "pet"},
    ),
    "balloon": Trouble(
        id="balloon",
        label="balloon",
        the="the balloon",
        owner_kind="toy",
        cry="My balloon!",
        spot="hooked high on a signpost string",
        height=3,
        living=False,
        fragile=True,
        heavy=False,
        tags={"balloon", "air"},
    ),
    "hat": Trouble(
        id="hat",
        label="hat",
        the="the hat",
        owner_kind="clothes",
        cry="My hat!",
        spot="resting on the stone hand of a tall statue",
        height=2,
        living=False,
        fragile=False,
        heavy=False,
        tags={"hat", "clothes"},
    ),
    "backpack": Trouble(
        id="backpack",
        label="backpack",
        the="the backpack",
        owner_kind="school thing",
        cry="My backpack!",
        spot="slid into a puddle behind the curb",
        height=1,
        living=False,
        fragile=False,
        heavy=True,
        tags={"backpack", "school"},
    ),
}

TOOLS = {
    "ladder": Tool(
        id="ladder",
        label="ladder",
        phrase="the folding ladder",
        reach=3,
        adult_only=True,
        handles_living=True,
        handles_fragile=True,
        handles_heavy=False,
        action="",
        team_action="climbed carefully and lifted the {target} down in steady hands",
        tags={"ladder", "tool"},
    ),
    "rescue_net": Tool(
        id="rescue_net",
        label="rescue net",
        phrase="the long rescue net",
        reach=3,
        adult_only=False,
        handles_living=False,
        handles_fragile=True,
        handles_heavy=False,
        action="slid the net under the {target} and guided it down gently",
        team_action="",
        tags={"net", "tool"},
    ),
    "long_grabber": Tool(
        id="long_grabber",
        label="long grabber",
        phrase="the long grabber",
        reach=2,
        adult_only=False,
        handles_living=False,
        handles_fragile=False,
        handles_heavy=True,
        action="hooked the strap with the grabber and pulled the {target} back without stepping into the puddle",
        team_action="",
        tags={"grabber", "tool"},
    ),
}

GIRL_NAMES = ["Maya", "Lina", "Ava", "Zoe", "Nora", "Ivy", "Ella", "Rina"]
BOY_NAMES = ["Leo", "Nico", "Sam", "Eli", "Theo", "Max", "Ben", "Owen"]
TRAITS = ["careful", "thoughtful", "steady", "gentle", "bold", "eager", "swift", "sparky"]


@dataclass
class StoryParams:
    setting: str
    trouble: str
    tool: str
    hero_name: str
    hero_type: str
    owner_name: str
    owner_type: str
    trait: str
    seed: Optional[int] = None
    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


KNOWLEDGE = {
    "kitten": [
        (
            "How should you help a scared kitten in a tree?",
            "Move slowly and use calm voices so the kitten does not get more frightened. A grown-up with the right safe tool should help bring it down."
        )
    ],
    "balloon": [
        (
            "Why can a balloon pop easily?",
            "A balloon is made of thin stretchy rubber, so sharp edges and hard pulls can make it burst. That is why gentle hands matter."
        )
    ],
    "hat": [
        (
            "Why can wind carry a hat away?",
            "A hat is light, so a gust of wind can lift it or slide it along until it lands somewhere hard to reach."
        )
    ],
    "backpack": [
        (
            "Why is a backpack harder to pick up than a balloon?",
            "A backpack is heavier and usually has books or other things inside. Heavy things need a stronger tool and steadier pulling."
        )
    ],
    "ladder": [
        (
            "Why should a grown-up help with a ladder?",
            "Ladders can tip if they are used the wrong way. A grown-up can steady them and make sure everyone stays safe."
        )
    ],
    "net": [
        (
            "What does a rescue net do?",
            "A rescue net gives a soft place to catch or guide something light. It helps bring delicate things down gently."
        )
    ],
    "grabber": [
        (
            "What is a long grabber for?",
            "A long grabber lets you reach something without climbing or stepping into a messy place. It is good for hooks, straps, and other sturdy parts."
        )
    ],
    "tool": [
        (
            "Why do heroes use the right tool instead of just jumping?",
            "The right tool matches the job, so the helper does not make the problem bigger. Careful tools often solve things faster than flashy moves."
        )
    ],
}
KNOWLEDGE_ORDER = ["kitten", "balloon", "hat", "backpack", "ladder", "net", "grabber", "tool"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    trouble_cfg = f["trouble_cfg"]
    tool_cfg = f["tool_cfg"]
    setting = f["setting"]
    outcome = f["outcome"]
    base = (
        f'Write a short superhero story for a 3-to-5-year-old that includes the word "gyp" '
        f'and the repeated line "{MOTTO}".'
    )
    if outcome == "steady":
        return [
            base,
            f"Tell a gentle superhero story where {hero.id} spots {trouble_cfg.the} in trouble at {setting.place} and thinks first instead of jumping first.",
            f"Write a story about a caped child and a tiny robot named gyp who learn that careful help is a real superpower, using {tool_cfg.phrase} to save {trouble_cfg.the}.",
        ]
    if outcome == "quick_reach":
        return [
            base,
            f"Tell a superhero story where {hero.id} uses a safe reach tool from the ground to save {trouble_cfg.the} at {setting.place}.",
            f"Write a repetitive, child-facing rescue story where gyp reminds the hero to keep both feet safe while using {tool_cfg.phrase}.",
        ]
    return [
        base,
        f"Tell a superhero story where {hero.id} almost tries a comic-book leap, but gyp's warning changes the plan and leads to a safer rescue.",
        f"Write a rescue story with repetition where the line '{MOTTO}' first sounds like a boast and later sounds like real wisdom after {trouble_cfg.the} is saved with {tool_cfg.phrase}.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    owner = f["owner"]
    helper = f["helper"]
    trouble_cfg = f["trouble_cfg"]
    tool_cfg = f["tool_cfg"]
    outcome = f["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id}, a child who likes to feel like a superhero, and a little robot named gyp. It is also about {owner.id}, who needed help when {trouble_cfg.the} got stuck."
        ),
        (
            "What problem started the mission?",
            f"{trouble_cfg.The} was {trouble_cfg.spot}, so {owner.id} could not reach it. That is what turned an ordinary afternoon into a rescue mission."
        ),
        (
            f"Why did {hero.id} stop to think before acting?",
            f"{hero.id} wanted to help fast, but gyp made {hero.pronoun('object')} notice the risk. The repeated motto changed from a shout about being brave into a reminder to help the smart way."
        ),
    ]
    if outcome == "leap_stopped":
        qa.append(
            (
                f"What did gyp warn {hero.id} about?",
                f"gyp warned that a big jump could make the rescue wobblier and riskier. Because the problem was high or tricky, the safer plan was to get the right tool and extra help."
            )
        )
    elif outcome == "steady":
        qa.append(
            (
                f"How did {hero.id} act like a real hero before the rescue even began?",
                f"{hero.pronoun().capitalize()} paused and looked carefully instead of rushing. That showed courage with self-control, not just excitement."
            )
        )
    else:
        qa.append(
            (
                f"How did {hero.id} solve the problem safely?",
                f"{hero.id} kept both feet on the ground and used {tool_cfg.phrase}. That let {hero.pronoun('object')} bring {trouble_cfg.the} down without climbing."
            )
        )
    qa.append(
        (
            f"How was {trouble_cfg.the} rescued?",
            f"{helper.id} helped, and together they used {tool_cfg.phrase} to bring {trouble_cfg.the} down safely. The tool fit the problem, which is why the rescue worked without anyone getting hurt."
        )
    )
    qa.append(
        (
            "How did the story end?",
            f"It ended with smiles and relief after the rescue. The ending image shows that {hero.id} learned a real superhero protects people first and saves the day safely."
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = set(f["trouble_cfg"].tags) | set(f["tool_cfg"].tags)
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
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v or v == 0}
            if shown:
                bits.append(f"attrs={shown}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.tags:
            bits.append(f"tags={sorted(ent.tags)}")
        lines.append(f"  {ent.id:10} ({ent.type:9}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        setting="courtyard",
        trouble="kitten",
        tool="ladder",
        hero_name="Maya",
        hero_type="girl",
        owner_name="Leo",
        owner_type="boy",
        trait="careful",
    ),
    StoryParams(
        setting="playground",
        trouble="balloon",
        tool="rescue_net",
        hero_name="Nora",
        hero_type="girl",
        owner_name="Max",
        owner_type="boy",
        trait="bold",
    ),
    StoryParams(
        setting="schoolyard",
        trouble="backpack",
        tool="long_grabber",
        hero_name="Eli",
        hero_type="boy",
        owner_name="Ava",
        owner_type="girl",
        trait="swift",
    ),
    StoryParams(
        setting="playground",
        trouble="hat",
        tool="ladder",
        hero_name="Theo",
        hero_type="boy",
        owner_name="Ivy",
        owner_type="girl",
        trait="eager",
    ),
]


def explain_rejection(setting: Optional[Setting], trouble: Trouble, tool: Tool) -> str:
    place = setting.place if setting else "this place"
    if setting and trouble.id not in setting.affords:
        return (
            f"(No story: {trouble.the} does not fit {place}. Pick a trouble that plausibly happens there.)"
        )
    if setting and tool.id not in setting.stores:
        return (
            f"(No story: {tool.phrase} is not available at {place}. Pick one of the tools that setting actually has.)"
        )
    if tool.reach < trouble.height:
        return (
            f"(No story: {tool.phrase} cannot reach {trouble.the}. The problem is too high for that tool.)"
        )
    if trouble.living and not tool.handles_living:
        return (
            f"(No story: {tool.phrase} is not gentle enough for {trouble.the}. Living, frightened animals need a safer method.)"
        )
    if trouble.fragile and not tool.handles_fragile:
        return (
            f"(No story: {tool.phrase} is too rough for {trouble.the}. Delicate things need a gentler rescue.)"
        )
    if trouble.heavy and not tool.handles_heavy:
        return (
            f"(No story: {tool.phrase} is too flimsy for {trouble.the}. Heavy things need a stronger tool.)"
        )
    return "(No story: that combination is not reasonable in this world.)"


ASP_RULES = r"""
compatible(S,T,U) :- setting(S), trouble(T), tool(U),
                     affords(S,T), stores(S,U),
                     height(T,H), reach(U,R), R >= H,
                     not bad_living(T,U),
                     not bad_fragile(T,U),
                     not bad_heavy(T,U).

bad_living(T,U) :- living(T), not handles_living(U).
bad_fragile(T,U) :- fragile(T), not handles_fragile(U).
bad_heavy(T,U) :- heavy(T), not handles_heavy(U).

careful_trait(T) :- trait(T), careful(T).
tall_trouble :- chosen_trouble(T), height(T,H), H >= 2.
adult_plan   :- chosen_tool(U), adult_only(U).

outcome(steady) :- chosen_trait(T), careful_trait(T).
outcome(leap_stopped) :- chosen_trait(T), not careful_trait(T), tall_trouble.
outcome(leap_stopped) :- chosen_trait(T), not careful_trait(T), adult_plan.
outcome(quick_reach) :- chosen_trait(T), not careful_trait(T), not tall_trouble, not adult_plan.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for setting_id, setting in SETTINGS.items():
        lines.append(asp.fact("setting", setting_id))
        for trouble_id in sorted(setting.affords):
            lines.append(asp.fact("affords", setting_id, trouble_id))
        for tool_id in sorted(setting.stores):
            lines.append(asp.fact("stores", setting_id, tool_id))
    for trouble_id, trouble in TROUBLES.items():
        lines.append(asp.fact("trouble", trouble_id))
        lines.append(asp.fact("height", trouble_id, trouble.height))
        if trouble.living:
            lines.append(asp.fact("living", trouble_id))
        if trouble.fragile:
            lines.append(asp.fact("fragile", trouble_id))
        if trouble.heavy:
            lines.append(asp.fact("heavy", trouble_id))
    for tool_id, tool in TOOLS.items():
        lines.append(asp.fact("tool", tool_id))
        lines.append(asp.fact("reach", tool_id, tool.reach))
        if tool.adult_only:
            lines.append(asp.fact("adult_only", tool_id))
        if tool.handles_living:
            lines.append(asp.fact("handles_living", tool_id))
        if tool.handles_fragile:
            lines.append(asp.fact("handles_fragile", tool_id))
        if tool.handles_heavy:
            lines.append(asp.fact("handles_heavy", tool_id))
    for trait in sorted(TRAITS):
        lines.append(asp.fact("trait", trait))
    for trait in sorted(CAREFUL_TRAITS):
        lines.append(asp.fact("careful", trait))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show compatible/3."))
    return sorted(set(asp.atoms(model, "compatible")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    scenario = "\n".join([
        asp.fact("chosen_trouble", params.trouble),
        asp.fact("chosen_tool", params.tool),
        asp.fact("chosen_trait", params.trait),
    ])
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a child superhero, a stuck problem, and the right kind of help."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--trouble", choices=TROUBLES)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--hero-type", choices=["girl", "boy"])
    ap.add_argument("--owner-type", choices=["girl", "boy"])
    ap.add_argument("--hero-name")
    ap.add_argument("--owner-name")
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = [n for n in (GIRL_NAMES if gender == "girl" else BOY_NAMES) if n != avoid]
    return rng.choice(pool)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    setting = SETTINGS.get(args.setting) if args.setting else None
    if args.trouble and args.tool:
        trouble = TROUBLES[args.trouble]
        tool = TOOLS[args.tool]
        if not compatible(setting or next(iter(SETTINGS.values())), trouble, tool):
            if args.setting:
                raise StoryError(explain_rejection(setting, trouble, tool))
            matching_settings = [s for s in SETTINGS.values() if compatible(s, trouble, tool)]
            if not matching_settings:
                raise StoryError(explain_rejection(None, trouble, tool))
    combos = [
        combo for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.trouble is None or combo[1] == args.trouble)
        and (args.tool is None or combo[2] == args.tool)
    ]
    if not combos:
        if args.setting and args.trouble and args.tool:
            raise StoryError(explain_rejection(SETTINGS[args.setting], TROUBLES[args.trouble], TOOLS[args.tool]))
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, trouble_id, tool_id = rng.choice(sorted(combos))
    hero_type = args.hero_type or rng.choice(["girl", "boy"])
    owner_type = args.owner_type or rng.choice(["girl", "boy"])
    hero_name = args.hero_name or _pick_name(rng, hero_type)
    owner_name = args.owner_name or _pick_name(rng, owner_type, avoid=hero_name)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(
        setting=setting_id,
        trouble=trouble_id,
        tool=tool_id,
        hero_name=hero_name,
        hero_type=hero_type,
        owner_name=owner_name,
        owner_type=owner_type,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError(f"(Unknown setting: {params.setting})")
    if params.trouble not in TROUBLES:
        raise StoryError(f"(Unknown trouble: {params.trouble})")
    if params.tool not in TOOLS:
        raise StoryError(f"(Unknown tool: {params.tool})")
    if params.hero_type not in {"girl", "boy"}:
        raise StoryError(f"(Unknown hero type: {params.hero_type})")
    if params.owner_type not in {"girl", "boy"}:
        raise StoryError(f"(Unknown owner type: {params.owner_type})")
    if params.trait not in TRAITS:
        raise StoryError(f"(Unknown trait: {params.trait})")
    setting = SETTINGS[params.setting]
    trouble = TROUBLES[params.trouble]
    tool = TOOLS[params.tool]
    if not compatible(setting, trouble, tool):
        raise StoryError(explain_rejection(setting, trouble, tool))
    world = tell(
        setting=setting,
        trouble_cfg=trouble,
        tool_cfg=tool,
        hero_name=params.hero_name,
        hero_type=params.hero_type,
        owner_name=params.owner_name,
        owner_type=params.owner_type,
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
    parser = build_parser()
    for s in range(80):
        try:
            ns = parser.parse_args([])
            params = resolve_params(ns, random.Random(s))
            params.seed = s
            cases.append(params)
        except StoryError:
            rc = 1
            print(f"Unexpected resolve failure for seed {s}.")
            break

    mismatch = 0
    for params in cases:
        if asp_outcome(params) != outcome_of(params):
            mismatch += 1
    if mismatch == 0:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {mismatch}/{len(cases)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("(Smoke test produced an empty story.)")
        sink = io.StringIO()
        with contextlib.redirect_stdout(sink):
            emit(sample, trace=False, qa=True, header="### smoke test")
        rendered = sink.getvalue()
        if "gyp" not in sample.story.lower():
            raise StoryError("(Smoke test story did not include required word 'gyp'.)")
        if "smoke test" not in rendered:
            raise StoryError("(Smoke test emit() did not print the header.)")
        print("OK: generate()/emit() smoke test passed.")
    except Exception as err:  # pragma: no cover - verify path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show compatible/3.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, trouble, tool) combos:\n")
        for setting_id, trouble_id, tool_id in combos:
            print(f"  {setting_id:12} {trouble_id:10} {tool_id}")
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
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero_name}: {p.trouble} at {p.setting} with {p.tool} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
