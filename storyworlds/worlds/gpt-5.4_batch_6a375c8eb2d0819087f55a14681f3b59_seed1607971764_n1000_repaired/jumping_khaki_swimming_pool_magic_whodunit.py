#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/jumping_khaki_swimming_pool_magic_whodunit.py
=========================================================================

A standalone storyworld about a tiny poolside mystery: during a swimming lesson,
a poolside object disappears after a big jump and a child detective solves the
case with gentle reasoning and a touch of magic.

Seed requirements honored:
- setting: swimming pool
- required words: "jumping", "khaki"
- feature: magic
- style: whodunit

The world models:
- children taking turns jumping into the pool
- a pool teacher who keeps a small object beside a khaki bag
- splash physics strong enough to push only plausible objects to plausible places
- a magical helper that reveals the true wet trail
- a detective-style investigation whose answer comes from simulated state

Run it
------
    python storyworlds/worlds/gpt-5.4/jumping_khaki_swimming_pool_magic_whodunit.py
    python storyworlds/worlds/gpt-5.4/jumping_khaki_swimming_pool_magic_whodunit.py --jump cannonball --item whistle_charm --hideout skimmer_basket
    python storyworlds/worlds/gpt-5.4/jumping_khaki_swimming_pool_magic_whodunit.py --item paper_clue
    python storyworlds/worlds/gpt-5.4/jumping_khaki_swimming_pool_magic_whodunit.py --all
    python storyworlds/worlds/gpt-5.4/jumping_khaki_swimming_pool_magic_whodunit.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/jumping_khaki_swimming_pool_magic_whodunit.py --verify
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
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
    owner: Optional[str] = None
    attrs: dict = field(default_factory=dict)
    movable: bool = False
    floatable: bool = False
    water_safe: bool = True
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return {"teacher": "teacher", "lifeguard": "lifeguard"}.get(self.type, self.type)
    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class JumpStyle:
    id: str
    label: str
    splash_power: int
    sentence: str
    shout: str
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
class LostItem:
    id: str
    label: str
    phrase: str
    drift_need: int
    floatable: bool
    water_safe: bool
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


@dataclass
class Hideout:
    id: str
    label: str
    phrase: str
    water_place: bool
    min_power: int
    supports_floatable: bool = True
    supports_sinkable: bool = True
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


@dataclass
class MagicAid:
    id: str
    label: str
    phrase: str
    verb: str
    clue_text: str
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


def _r_splash_moves_item(world: World) -> list[str]:
    item = world.get("item")
    jump = world.facts["jump_cfg"]
    hideout = world.facts["hideout_cfg"]
    if world.facts.get("jump_done", 0) < THRESHOLD:
        return []
    sig = ("move_item", jump.id, item.id, hideout.id)
    if sig in world.fired:
        return []
    if not can_land(jump, world.facts["item_cfg"], hideout):
        return []
    world.fired.add(sig)
    item.meters["moved"] += 1
    item.meters["missing"] += 1
    item.attrs["location"] = hideout.id
    item.attrs["found_at"] = hideout.id
    world.get("pool").meters["splash"] += float(jump.splash_power)
    world.get("teacher").memes["worry"] += 1
    return []


def _r_missing_stirs_search(world: World) -> list[str]:
    item = world.get("item")
    if item.meters["missing"] < THRESHOLD:
        return []
    sig = ("search_starts", item.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    world.get("detective").memes["curiosity"] += 1
    world.get("detective").memes["care"] += 1
    world.get("teacher").memes["worry"] += 1
    return []


def _r_magic_reveals_clue(world: World) -> list[str]:
    if world.facts.get("magic_used", 0) < THRESHOLD:
        return []
    item = world.get("item")
    if item.meters["moved"] < THRESHOLD:
        return []
    sig = ("magic_clue", item.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hideout = world.facts["hideout_cfg"]
    world.get("detective").memes["hope"] += 1
    world.get("magic").meters["glow"] += 1
    world.facts["clue_revealed"] = hideout.id
    return []


CAUSAL_RULES = [
    Rule(name="splash_moves_item", tag="physical", apply=_r_splash_moves_item),
    Rule(name="missing_stirs_search", tag="social", apply=_r_missing_stirs_search),
    Rule(name="magic_reveals_clue", tag="magic", apply=_r_magic_reveals_clue),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            out = rule.apply(world)
            if out:
                changed = True
                produced.extend(out)
            elif any(sig[0] == rule.name for sig in world.fired):
                changed = True
    if narrate:
        for line in produced:
            world.say(line)
    return produced


JUMPS = {
    "frog_hop": JumpStyle(
        id="frog_hop",
        label="frog hop",
        splash_power=1,
        sentence="did a small frog-like hop from the low edge",
        shout='"Boing!"',
        tags={"jumping", "small_splash"},
    ),
    "straight_jump": JumpStyle(
        id="straight_jump",
        label="straight jump",
        splash_power=2,
        sentence="jumped in with knees tucked and toes pointed",
        shout='"Ready? Jumping!"',
        tags={"jumping", "medium_splash"},
    ),
    "cannonball": JumpStyle(
        id="cannonball",
        label="cannonball",
        splash_power=3,
        sentence="curled up into a giant cannonball and crashed into the water",
        shout='"Cannonball!"',
        tags={"jumping", "big_splash"},
    ),
}

ITEMS = {
    "whistle_charm": LostItem(
        id="whistle_charm",
        label="whistle charm",
        phrase="a tiny silver whistle charm",
        drift_need=2,
        floatable=True,
        water_safe=True,
        tags={"whistle", "pool_item"},
    ),
    "star_ribbon": LostItem(
        id="star_ribbon",
        label="star ribbon",
        phrase="a little blue star ribbon",
        drift_need=1,
        floatable=True,
        water_safe=True,
        tags={"ribbon", "pool_item"},
    ),
    "paper_clue": LostItem(
        id="paper_clue",
        label="paper clue",
        phrase="a folded paper clue with a gold star on it",
        drift_need=1,
        floatable=False,
        water_safe=False,
        tags={"paper", "clue"},
    ),
}

HIDEOUTS = {
    "towel_cubby": Hideout(
        id="towel_cubby",
        label="towel cubby",
        phrase="the warm towel cubby beside the bench",
        water_place=False,
        min_power=1,
        supports_floatable=True,
        supports_sinkable=True,
        tags={"dry_place", "towels"},
    ),
    "kickboard_stack": Hideout(
        id="kickboard_stack",
        label="kickboard stack",
        phrase="the leaning stack of kickboards near the ladder",
        water_place=False,
        min_power=2,
        supports_floatable=True,
        supports_sinkable=True,
        tags={"pool_gear", "dry_place"},
    ),
    "lane_rope": Hideout(
        id="lane_rope",
        label="lane rope",
        phrase="the striped lane rope at the shallow end",
        water_place=True,
        min_power=2,
        supports_floatable=True,
        supports_sinkable=False,
        tags={"water_place", "pool_gear"},
    ),
    "skimmer_basket": Hideout(
        id="skimmer_basket",
        label="skimmer basket",
        phrase="the little skimmer basket by the wall",
        water_place=True,
        min_power=3,
        supports_floatable=True,
        supports_sinkable=False,
        tags={"water_place", "pool_gear"},
    ),
}

MAGIC = {
    "moon_goggles": MagicAid(
        id="moon_goggles",
        label="Moon Goggles",
        phrase="the Moon Goggles from the lesson box",
        verb="slipped on",
        clue_text="silver drops began to shine in a secret line",
        tags={"goggles", "magic"},
    ),
    "ripple_wand": MagicAid(
        id="ripple_wand",
        label="Ripple Wand",
        phrase="the Ripple Wand shaped like a seahorse",
        verb="raised",
        clue_text="a pale blue arrow trembled over the wet tiles",
        tags={"wand", "magic"},
    ),
    "echo_shell": MagicAid(
        id="echo_shell",
        label="Echo Shell",
        phrase="the Echo Shell with a pearly curl",
        verb="held up",
        clue_text="the shell whispered where the last splash had run",
        tags={"shell", "magic"},
    ),
}

DETECTIVE_NAMES = ["Mina", "Ruby", "Nora", "Zoe", "Liam", "Ben", "Theo", "Leo"]
JUMPER_NAMES = ["Pip", "Tess", "Milo", "Ava", "June", "Finn", "Ivy", "Max"]
TRAITS = ["careful", "curious", "thoughtful", "patient", "gentle"]


def can_land(jump: JumpStyle, item: LostItem, hideout: Hideout) -> bool:
    if jump.splash_power < hideout.min_power:
        return False
    if jump.splash_power < item.drift_need:
        return False
    if hideout.water_place:
        if not item.floatable:
            return False
        if not hideout.supports_floatable:
            return False
        if not item.water_safe:
            return False
        return True
    if item.floatable and not hideout.supports_floatable:
        return False
    if (not item.floatable) and not hideout.supports_sinkable:
        return False
    return True


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for jump_id, jump in JUMPS.items():
        for item_id, item in ITEMS.items():
            for hideout_id, hideout in HIDEOUTS.items():
                if can_land(jump, item, hideout):
                    for magic_id in MAGIC:
                        combos.append((jump_id, item_id, hideout_id, magic_id))
    return combos


@dataclass
class StoryParams:
    jump: str
    item: str
    hideout: str
    magic: str
    detective: str
    detective_gender: str
    jumper: str
    jumper_gender: str
    teacher_type: str
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


def pool_image(item: LostItem, hideout: Hideout) -> str:
    if hideout.water_place:
        return f"the water held {item.phrase} against {hideout.phrase}"
    return f"{item.phrase} rested safely in {hideout.phrase}"


def predict_case(jump: JumpStyle, item: LostItem, hideout: Hideout) -> dict:
    moved = can_land(jump, item, hideout)
    return {
        "moved": moved,
        "wet_clue": moved,
        "water_place": hideout.water_place if moved else False,
    }


def setup_story(world: World, detective: Entity, jumper: Entity, teacher: Entity,
                jump: JumpStyle, item: LostItem) -> None:
    detective.memes["care"] += 1
    jumper.memes["joy"] += 1
    world.say(
        f"The swimming pool was bright and blue, and the lesson bench stood nearby with "
        f"a khaki pool bag folded beside the towels. On top of it rested {item.phrase}, "
        f"which {teacher.id} used to mark the turn for the next game."
    )
    world.say(
        f"{detective.id} loved mysteries almost as much as swimming, so {detective.pronoun()} "
        f"noticed little things: the echo in the room, the neat line of kickboards, and the way "
        f"everyone was waiting for a turn at the jumping game."
    )
    world.say(
        f'Then {jumper.id} {jump.sentence}. {jump.shout} Water leapt up in a sparkling wall and '
        f"slapped the tiles by the bench."
    )


def discover_missing(world: World, detective: Entity, teacher: Entity, item: LostItem) -> None:
    world.facts["jump_done"] = 1.0
    propagate(world, narrate=False)
    world.para()
    world.say(
        f"A moment later, {teacher.id} reached for {item.phrase} and blinked. "
        f'"Oh dear," {teacher.pronoun()} said. "My {item.label} was right here a second ago."'
    )
    world.say(
        f"{detective.id} looked at the bench, then at the shining water, then at the puddled tiles. "
        f"This was not a scary mystery, only a small one, but it still felt like a proper whodunit."
    )


def suspect_talk(world: World, detective: Entity, jumper: Entity, teacher: Entity,
                 jump: JumpStyle, item: LostItem) -> None:
    pred = predict_case(jump, item, world.facts["hideout_cfg"])
    world.facts["predicted_moved"] = pred["moved"]
    world.say(
        f'"Let us think before we blame anybody," {detective.id} said. {detective.pronoun().capitalize()} '
        f"knew the strongest clue in a mystery is the one that matches what really happened."
    )
    world.say(
        f'{jumper.id} pushed wet hair back and whispered, "I only did my jump. I did not take it." '
        f"{teacher.id} nodded. Nobody had sneaked away; everyone had been watching the pool."
    )


def use_magic(world: World, detective: Entity, magic: MagicAid, hideout: Hideout) -> None:
    world.para()
    world.facts["magic_used"] = 1.0
    propagate(world, narrate=False)
    world.say(
        f"So {detective.id} {magic.verb} {magic.phrase}. It was lesson magic, the kind used for games, "
        f"and when it touched the damp air, {magic.clue_text}."
    )
    if hideout.water_place:
        world.say(
            f"The glowing trail did not point to any pocket or sneaky hand. It pointed straight toward "
            f"{hideout.phrase}."
        )
    else:
        world.say(
            f"The magical gleam skipped over the tiles, curved around the bench, and stopped at "
            f"{hideout.phrase}."
        )


def find_and_explain(world: World, detective: Entity, jumper: Entity, teacher: Entity,
                     item: LostItem, hideout: Hideout, jump: JumpStyle) -> None:
    item_ent = world.get("item")
    item_ent.meters["found"] += 1
    teacher.memes["relief"] += 1
    detective.memes["pride"] += 1
    jumper.memes["relief"] += 1
    world.para()
    if hideout.water_place:
        world.say(
            f"There it was: {item.phrase}, bobbing where the magic had shown. {teacher.id} lifted it up, "
            f"and drops of pool water slid back into the lane."
        )
    else:
        world.say(
            f"There it was: {item.phrase}, tucked exactly where the magic had shown. {teacher.id} picked it up "
            f"from {hideout.phrase} and laughed with relief."
        )
    world.say(
        f'"Case solved," said {detective.id}. "{jumper.id} did not steal anything. The big {jump.label} splash '
        f"pushed it off the khaki bag and sent it drifting away."
    )
    if hideout.water_place:
        world.say(
            f"{teacher.id} smiled and agreed. The water, not a thief, had carried the clue away."
        )
    else:
        world.say(
            f"{teacher.id} smiled and agreed. The splash, not a thief, had nudged it across the tiles."
        )


def safer_end(world: World, detective: Entity, jumper: Entity, teacher: Entity,
              item: LostItem) -> None:
    detective.memes["calm"] += 1
    jumper.memes["joy"] += 1
    teacher.memes["care"] += 1
    world.say(
        f"After that, {teacher.id} clipped the {item.label} high on the scoreboard instead of leaving it on "
        f"the khaki bag by the water."
    )
    world.say(
        f"The lesson started again. {jumper.id} still got to practice jumping, {detective.id} still got a mystery, "
        f"and this time everyone knew where the missing thing belonged."
    )
    world.say(
        f"By the end of the hour, the pool shone softly, the case was closed, and {pool_image(world.facts['item_cfg'], world.facts['hideout_cfg'])} "
        f"had become the story everyone retold with a smile."
    )


def tell(jump: JumpStyle, item: LostItem, hideout: Hideout, magic: MagicAid,
         detective_name: str = "Mina", detective_gender: str = "girl",
         jumper_name: str = "Pip", jumper_gender: str = "boy",
         teacher_type: str = "woman", trait: str = "curious") -> World:
    world = World()
    detective = world.add(Entity(
        id=detective_name,
        kind="character",
        type=detective_gender,
        role="detective",
        traits=[trait],
    ))
    jumper = world.add(Entity(
        id=jumper_name,
        kind="character",
        type=jumper_gender,
        role="jumper",
        traits=["brave"],
    ))
    teacher = world.add(Entity(
        id="Coach Nia" if teacher_type == "woman" else "Coach Ben",
        kind="character",
        type="woman" if teacher_type == "woman" else "man",
        role="teacher",
        label="the teacher",
    ))
    world.add(Entity(
        id="pool",
        type="pool",
        label="the swimming pool",
    ))
    magic_ent = world.add(Entity(
        id="magic",
        type="magic",
        label=magic.label,
    ))
    item_ent = world.add(Entity(
        id="item",
        type="item",
        label=item.label,
        movable=True,
        floatable=item.floatable,
        water_safe=item.water_safe,
        attrs={"location": "khaki_bag", "found_at": ""},
    ))

    world.facts.update(
        jump_cfg=jump,
        item_cfg=item,
        hideout_cfg=hideout,
        magic_cfg=magic,
        detective=detective,
        jumper=jumper,
        teacher=teacher,
        jump_done=0.0,
        magic_used=0.0,
        clue_revealed="",
    )

    setup_story(world, detective, jumper, teacher, jump, item)
    discover_missing(world, detective, teacher, item)
    suspect_talk(world, detective, jumper, teacher, jump, item)
    use_magic(world, detective, magic, hideout)
    find_and_explain(world, detective, jumper, teacher, item, hideout, jump)
    safer_end(world, detective, jumper, teacher, item)
    world.facts["solved"] = True
    return world


KNOWLEDGE = {
    "jumping": [
        (
            "Why can jumping into a pool move things near the edge?",
            "A big jump can make a strong splash and push water onto the tiles or toward nearby things. Water can nudge light objects even when nobody touches them."
        )
    ],
    "khaki": [
        (
            "What does khaki mean?",
            "Khaki is a light brown or dusty tan color. Bags, hats, and clothes can all be khaki."
        )
    ],
    "goggles": [
        (
            "What are swim goggles for?",
            "Swim goggles help protect your eyes in the water so you can see more clearly. They make swimming games and lessons easier."
        )
    ],
    "wand": [
        (
            "What is a wand in a pretend magic story?",
            "A wand is a special stick or tool used to make magic happen in the story. In pretend play, it often helps point the way or reveal clues."
        )
    ],
    "shell": [
        (
            "What is a shell?",
            "A shell is the hard outside home of some sea animals, like snails or clams. People sometimes keep pretty shells because they are smooth and shiny."
        )
    ],
    "whistle": [
        (
            "What is a whistle for at a pool?",
            "A whistle helps a grown-up call attention quickly with a sharp sound. At a pool, it can help keep lessons safe and orderly."
        )
    ],
    "ribbon": [
        (
            "What is a ribbon?",
            "A ribbon is a soft strip of cloth or shiny material. People use ribbons to tie, decorate, or mark something special."
        )
    ],
    "paper": [
        (
            "Why is paper not a good thing to leave by a pool?",
            "Paper gets soggy very quickly when it touches water. Wet paper can tear, wrinkle, and be hard to read."
        )
    ],
    "pool_gear": [
        (
            "What are kickboards used for?",
            "Kickboards help swimmers practice kicking while they hold on with their hands. They are common tools in swimming lessons."
        )
    ],
}
KNOWLEDGE_ORDER = ["jumping", "khaki", "goggles", "wand", "shell", "whistle", "ribbon", "paper", "pool_gear"]


def generation_prompts(world: World) -> list[str]:
    jump = world.facts["jump_cfg"]
    item = world.facts["item_cfg"]
    magic = world.facts["magic_cfg"]
    detective = world.facts["detective"]
    return [
        f'Write a gentle whodunit for a 3-to-5-year-old set at a swimming pool. Include the words "jumping" and "khaki".',
        f"Tell a small magical mystery where {detective.id} investigates what happened to {item.phrase} after a {jump.label} splash.",
        f"Write a child-facing pool story in which {magic.label} helps reveal that a missing thing was moved by water and not by a thief.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    detective = world.facts["detective"]
    jumper = world.facts["jumper"]
    teacher = world.facts["teacher"]
    jump = world.facts["jump_cfg"]
    item = world.facts["item_cfg"]
    hideout = world.facts["hideout_cfg"]
    magic = world.facts["magic_cfg"]
    qa: list[tuple[str, str]] = [
        (
            "Where does the story happen?",
            "The story happens at a swimming pool during a lesson. The bench, the kickboards, and the wet tiles all matter because the mystery begins right beside the water."
        ),
        (
            f"What went missing?",
            f"{item.phrase} went missing from the top of a khaki pool bag. It looked like a tiny theft at first, which is why the mystery began."
        ),
        (
            f"Why did {detective.id} think before blaming anyone?",
            f"{detective.id} knew everybody had been watching the pool and nobody had sneaked away. That made a splashy accident more likely than a secret thief."
        ),
        (
            f"How did the magic help solve the case?",
            f"{magic.label} showed the true wet trail after the splash. The magical clue pointed to {hideout.phrase}, so the search followed the water instead of blaming a person."
        ),
        (
            f"Who moved the {item.label}?",
            f"No person stole it. {jumper.id}'s {jump.label} made such a strong splash that the water knocked the {item.label} away from the khaki bag."
        ),
        (
            "How did the story end?",
            f"The case ended happily when {teacher.id} found the missing thing and moved it to a safer place. Everyone returned to the lesson knowing the mystery had a water-made answer."
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags: set[str] = {"jumping", "khaki"}
    item = world.facts["item_cfg"]
    magic = world.facts["magic_cfg"]
    hideout = world.facts["hideout_cfg"]
    tags |= set(item.tags)
    tags |= set(magic.tags)
    tags |= set(hideout.tags)
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
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if ent.floatable:
            bits.append("floatable=True")
        if ent.movable:
            bits.append("movable=True")
        lines.append(f"  {ent.id:12} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(sig[0] for sig in world.fired))}")
    return "\n".join(lines)


def explain_rejection(jump: JumpStyle, item: LostItem, hideout: Hideout) -> str:
    if jump.splash_power < item.drift_need:
        return (
            f"(No story: a {jump.label} is too small to move {item.phrase}. "
            f"The mystery needs a splash strong enough to send the missing thing somewhere real.)"
        )
    if jump.splash_power < hideout.min_power:
        return (
            f"(No story: a {jump.label} does not throw water far enough to reach {hideout.phrase}. "
            f"Pick a stronger jump or a nearer hiding place.)"
        )
    if hideout.water_place and not item.floatable:
        return (
            f"(No story: {item.phrase} would not float to {hideout.phrase}. "
            f"A water hideout needs an item that can ride the splash or drift on the surface.)"
        )
    if hideout.water_place and not item.water_safe:
        return (
            f"(No story: {item.phrase} would be ruined in pool water, so this watery hiding place is unreasonable for the mystery.)"
        )
    return "(No story: this splash path is not reasonable.)"


ASP_RULES = r"""
moved_by_splash(J,I,H) :- jump(J), item(I), hideout(H),
                          splash_power(J,P), drift_need(I,D), P >= D,
                          min_power(H,M), P >= M,
                          dry(H).
moved_by_splash(J,I,H) :- jump(J), item(I), hideout(H),
                          splash_power(J,P), drift_need(I,D), P >= D,
                          min_power(H,M), P >= M,
                          water(H), floatable(I), water_safe(I).

valid(J,I,H,Mg) :- moved_by_splash(J,I,H), magic(Mg).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for jump_id, jump in JUMPS.items():
        lines.append(asp.fact("jump", jump_id))
        lines.append(asp.fact("splash_power", jump_id, jump.splash_power))
    for item_id, item in ITEMS.items():
        lines.append(asp.fact("item", item_id))
        lines.append(asp.fact("drift_need", item_id, item.drift_need))
        if item.floatable:
            lines.append(asp.fact("floatable", item_id))
        if item.water_safe:
            lines.append(asp.fact("water_safe", item_id))
    for hideout_id, hideout in HIDEOUTS.items():
        lines.append(asp.fact("hideout", hideout_id))
        lines.append(asp.fact("min_power", hideout_id, hideout.min_power))
        if hideout.water_place:
            lines.append(asp.fact("water", hideout_id))
        else:
            lines.append(asp.fact("dry", hideout_id))
    for magic_id in MAGIC:
        lines.append(asp.fact("magic", magic_id))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP gate matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combinations:")
        if cl - py:
            print("  only in clingo:", sorted(cl - py))
        if py - cl:
            print("  only in python:", sorted(py - cl))

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("generated empty story")
        print("OK: smoke test generation succeeded.")
    except Exception as err:  # pragma: no cover - defensive verify path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    try:
        parser = build_parser()
        params = resolve_params(parser.parse_args([]), random.Random(123))
        params.seed = 123
        sample = generate(params)
        if not sample.story.strip():
            raise StoryError("default resolved story was empty")
        print("OK: default resolve_params() generation succeeded.")
    except Exception as err:  # pragma: no cover - defensive verify path
        rc = 1
        print(f"DEFAULT GENERATION FAILED: {err}")
    return rc


CURATED = [
    StoryParams(
        jump="cannonball",
        item="whistle_charm",
        hideout="skimmer_basket",
        magic="moon_goggles",
        detective="Mina",
        detective_gender="girl",
        jumper="Finn",
        jumper_gender="boy",
        teacher_type="woman",
        trait="curious",
    ),
    StoryParams(
        jump="straight_jump",
        item="star_ribbon",
        hideout="kickboard_stack",
        magic="echo_shell",
        detective="Theo",
        detective_gender="boy",
        jumper="Ava",
        jumper_gender="girl",
        teacher_type="man",
        trait="thoughtful",
    ),
    StoryParams(
        jump="frog_hop",
        item="paper_clue",
        hideout="towel_cubby",
        magic="ripple_wand",
        detective="Ruby",
        detective_gender="girl",
        jumper="Max",
        jumper_gender="boy",
        teacher_type="woman",
        trait="patient",
    ),
    StoryParams(
        jump="cannonball",
        item="star_ribbon",
        hideout="lane_rope",
        magic="ripple_wand",
        detective="Leo",
        detective_gender="boy",
        jumper="June",
        jumper_gender="girl",
        teacher_type="woman",
        trait="gentle",
    ),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a magical poolside whodunit. Unspecified choices are picked at random (seeded)."
    )
    ap.add_argument("--jump", choices=JUMPS)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--hideout", choices=HIDEOUTS)
    ap.add_argument("--magic", choices=MAGIC)
    ap.add_argument("--teacher", choices=["woman", "man"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid combinations derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = [n for n in (DETECTIVE_NAMES if gender == "girl" else DETECTIVE_NAMES) if n != avoid]
    if not pool:
        pool = [n for n in DETECTIVE_NAMES if n != avoid]
    return rng.choice(pool), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.jump and args.item and args.hideout:
        if not can_land(JUMPS[args.jump], ITEMS[args.item], HIDEOUTS[args.hideout]):
            raise StoryError(explain_rejection(JUMPS[args.jump], ITEMS[args.item], HIDEOUTS[args.hideout]))

    combos = [
        combo for combo in valid_combos()
        if (args.jump is None or combo[0] == args.jump)
        and (args.item is None or combo[1] == args.item)
        and (args.hideout is None or combo[2] == args.hideout)
        and (args.magic is None or combo[3] == args.magic)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    jump_id, item_id, hideout_id, magic_id = rng.choice(sorted(combos))
    detective, detective_gender = _pick_name(rng)
    jumper, jumper_gender = _pick_name(rng, avoid=detective)
    teacher_type = args.teacher or rng.choice(["woman", "man"])
    trait = rng.choice(TRAITS)
    return StoryParams(
        jump=jump_id,
        item=item_id,
        hideout=hideout_id,
        magic=magic_id,
        detective=detective,
        detective_gender=detective_gender,
        jumper=jumper,
        jumper_gender=jumper_gender,
        teacher_type=teacher_type,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.jump not in JUMPS:
        raise StoryError(f"(Unknown jump style: {params.jump})")
    if params.item not in ITEMS:
        raise StoryError(f"(Unknown item: {params.item})")
    if params.hideout not in HIDEOUTS:
        raise StoryError(f"(Unknown hideout: {params.hideout})")
    if params.magic not in MAGIC:
        raise StoryError(f"(Unknown magic aid: {params.magic})")
    jump = JUMPS[params.jump]
    item = ITEMS[params.item]
    hideout = HIDEOUTS[params.hideout]
    magic = MAGIC[params.magic]
    if not can_land(jump, item, hideout):
        raise StoryError(explain_rejection(jump, item, hideout))

    world = tell(
        jump=jump,
        item=item,
        hideout=hideout,
        magic=magic,
        detective_name=params.detective,
        detective_gender=params.detective_gender,
        jumper_name=params.jumper,
        jumper_gender=params.jumper_gender,
        teacher_type=params.teacher_type,
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
        print(f"{len(combos)} valid (jump, item, hideout, magic) combos:\n")
        for jump_id, item_id, hideout_id, magic_id in combos:
            print(f"  {jump_id:14} {item_id:14} {hideout_id:16} {magic_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        samples: list[StorySample] = []
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
            header = f"### {p.detective}: {p.jump} / {p.item} / {p.hideout} / {p.magic}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
