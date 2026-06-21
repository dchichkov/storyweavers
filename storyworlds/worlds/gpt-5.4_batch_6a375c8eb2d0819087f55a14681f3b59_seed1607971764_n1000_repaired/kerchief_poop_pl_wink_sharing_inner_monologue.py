#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/kerchief_poop_pl_wink_sharing_inner_monologue.py
============================================================================

A standalone story world for a small rhyming tale about **sharing**.

Seed ingredients:
- must include the words "kerchief", "poop-pl", and "wink"
- must use Sharing and Inner Monologue
- style target: Rhyming Story

This world models a child who carries a treat in a kerchief, meets a hungry
friend, wrestles with a selfish thought, and then decides whether and how to
share. The physical state tracks treat pieces, crumbs, and neatness; the
emotional state tracks hunger, greed, worry, kindness, and relief. The story's
turn comes from inner-monologue beats grounded in those meters/memes, followed by
a sharing action whose feasibility depends on the treat and the chosen method.

Run it
------
    python storyworlds/worlds/gpt-5.4/kerchief_poop_pl_wink_sharing_inner_monologue.py
    python storyworlds/worlds/gpt-5.4/kerchief_poop_pl_wink_sharing_inner_monologue.py --treat muffin --method break
    python storyworlds/worlds/gpt-5.4/kerchief_poop_pl_wink_sharing_inner_monologue.py --treat soup
    python storyworlds/worlds/gpt-5.4/kerchief_poop_pl_wink_sharing_inner_monologue.py --all
    python storyworlds/worlds/gpt-5.4/kerchief_poop_pl_wink_sharing_inner_monologue.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/kerchief_poop_pl_wink_sharing_inner_monologue.py --verify
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


# ---------------------------------------------------------------------------
# Entities
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"            # "character" | "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


# ---------------------------------------------------------------------------
# Domain registries
# ---------------------------------------------------------------------------
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
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Setting:
    id: str
    place: str
    path: str
    sound_line: str
    sky_line: str
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
class Treat:
    id: str
    label: str
    phrase: str
    piece_word: str
    split_ok: bool
    spill_risk: int
    crumbly: bool
    rhyme_line: str
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
class ShareMethod:
    id: str
    verb: str
    good_for_split: bool
    good_for_liquid: bool
    neatness: int
    text: str
    fail_text: str
    qa_text: str
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
class Helper:
    id: str
    kind: str
    arrival: str
    hint: str
    closing: str
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


SETTINGS = {
    "lane": Setting(
        id="lane",
        place="the clover lane",
        path="a pebbly lane by a low stone wall",
        sound_line='Tiny shoes went "poop-pl, poop-pl" on the damp spring ground.',
        sky_line="The clouds were pearly and light, and the day felt soft and round.",
        tags={"lane", "outdoors"},
    ),
    "orchard": Setting(
        id="orchard",
        place="the plum orchard path",
        path="a winding path beneath plum trees",
        sound_line='Little steps went "poop-pl, poop-pl" where old plums had kissed the ground.',
        sky_line="A breeze stirred leaves like green silk flags, with bees making a humming sound.",
        tags={"orchard", "outdoors", "plum"},
    ),
    "brook": Setting(
        id="brook",
        place="the brookside path",
        path="a grassy path beside the brook",
        sound_line='Tiny shoes went "poop-pl, poop-pl" by puddles shiny and round.',
        sky_line="The water flashed like a silver ribbon, and sun-dots hopped around.",
        tags={"brook", "outdoors"},
    ),
}

TREATS = {
    "muffin": Treat(
        id="muffin",
        label="plum muffin",
        phrase="a warm plum muffin",
        piece_word="half",
        split_ok=True,
        spill_risk=1,
        crumbly=True,
        rhyme_line="Its sugared top looked soft and sweet, a small and sunny crown.",
        tags={"muffin", "plum", "snack"},
    ),
    "scone": Treat(
        id="scone",
        label="berry scone",
        phrase="a round berry scone",
        piece_word="half",
        split_ok=True,
        spill_risk=1,
        crumbly=True,
        rhyme_line="Its berry dots peeped ruby-red, like jewels tucked in brown.",
        tags={"scone", "berry", "snack"},
    ),
    "dumpling": Treat(
        id="dumpling",
        label="apple dumpling",
        phrase="a warm apple dumpling",
        piece_word="half",
        split_ok=True,
        spill_risk=2,
        crumbly=False,
        rhyme_line="Its little top was glossy-bright, with cinnamon dripped down.",
        tags={"dumpling", "apple", "snack"},
    ),
    "soup": Treat(
        id="soup",
        label="plum soup",
        phrase="a small cup of plum soup",
        piece_word="sip",
        split_ok=False,
        spill_risk=3,
        crumbly=False,
        rhyme_line="The purple soup smelled sweet and warm, and steamed in swirls of brown.",
        tags={"soup", "plum", "liquid"},
    ),
}

METHODS = {
    "break": ShareMethod(
        id="break",
        verb="broke it into two fair parts",
        good_for_split=True,
        good_for_liquid=False,
        neatness=2,
        text="broke the treat into two fair parts on the kerchief",
        fail_text="tried to break the treat apart, but it was the wrong kind of snack for that",
        qa_text="broke the treat into two fair parts on the kerchief",
        tags={"break", "sharing"},
    ),
    "slice": ShareMethod(
        id="slice",
        verb="cut it with a picnic spoon edge",
        good_for_split=True,
        good_for_liquid=False,
        neatness=3,
        text="used the smooth edge of a picnic spoon to divide the treat neatly on the kerchief",
        fail_text="scraped at the treat with a spoon edge, but that could not divide it safely",
        qa_text="used a picnic spoon edge to divide the treat neatly on the kerchief",
        tags={"slice", "sharing"},
    ),
    "sip": ShareMethod(
        id="sip",
        verb="took turns with tiny sips",
        good_for_split=False,
        good_for_liquid=True,
        neatness=2,
        text="set the cup on the kerchief and took turns with tiny sips",
        fail_text="offered little sips, but this treat was not something to share that way",
        qa_text="set the cup on the kerchief and took turns with tiny sips",
        tags={"sip", "sharing"},
    ),
}

HELPERS = {
    "grandma": Helper(
        id="grandma",
        kind="grandma",
        arrival="Grandma looked over the garden gate with a twinkle in her eye.",
        hint='She gave a tiny wink, as if to say, "A kind heart makes the sweetest pie."',
        closing="Grandma's wink felt warm as toast.",
        tags={"grandma", "wink"},
    ),
    "sparrow": Helper(
        id="sparrow",
        kind="sparrow",
        arrival="A sparrow bobbed upon the wall and tilted its neat brown head.",
        hint='It gave a bright little winky blink, and the child thought of kind words instead.',
        closing="The sparrow hopped once, pleased as could be.",
        tags={"sparrow", "wink", "bird"},
    ),
    "auntie": Helper(
        id="auntie",
        kind="auntie",
        arrival="Auntie peeped from under the porch roof with smile-lines by each eye.",
        hint='She sent a playful wink through the rain-washed air, and kindness seemed to fly.',
        closing="Auntie's wink made the whole lane glow.",
        tags={"auntie", "wink"},
    ),
}

GIRL_NAMES = ["Mina", "Lila", "Poppy", "Nora", "Tess", "Ruby", "June", "Ella"]
BOY_NAMES = ["Milo", "Owen", "Finn", "Jude", "Theo", "Benji", "Rowan", "Ned"]
TRAITS = ["thoughtful", "gentle", "eager", "bouncy", "bright", "careful"]


# ---------------------------------------------------------------------------
# World / rules
# ---------------------------------------------------------------------------
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


def _r_lonely_to_worry(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    friend = world.get("friend")
    if friend.memes["hunger"] < THRESHOLD:
        return out
    if child.memes["greed"] < THRESHOLD:
        return out
    sig = ("worry",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["worry"] += 1
    out.append("__worry__")
    return out


def _r_share_brings_relief(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    friend = world.get("friend")
    treat = world.get("treat")
    if world.facts.get("shared") is not True:
        return out
    sig = ("relief",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["kindness"] += 1
    child.memes["relief"] += 1
    friend.memes["relief"] += 1
    friend.memes["trust"] += 1
    child.memes["greed"] = 0.0
    if treat.meters["mess"] < THRESHOLD:
        child.meters["neatness"] += 1
    out.append("__relief__")
    return out


CAUSAL_RULES = [
    Rule(name="lonely_to_worry", tag="emotional", apply=_r_lonely_to_worry),
    Rule(name="share_brings_relief", tag="emotional", apply=_r_share_brings_relief),
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
        for s in produced:
            world.say(s)
    return produced


# ---------------------------------------------------------------------------
# Constraint helpers
# ---------------------------------------------------------------------------
def method_works(treat: Treat, method: ShareMethod) -> bool:
    if treat.split_ok and method.good_for_split:
        return True
    if (not treat.split_ok) and method.good_for_liquid:
        return True
    return False


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for setting_id in SETTINGS:
        for treat_id, treat in TREATS.items():
            for method_id, method in METHODS.items():
                if method_works(treat, method):
                    for helper_id in HELPERS:
                        combos.append((setting_id, treat_id, method_id, helper_id))
    return combos


def explain_rejection(treat: Treat, method: ShareMethod) -> str:
    if treat.split_ok and not method.good_for_split:
        return (
            f"(No story: {treat.phrase} is best shared by dividing it, but "
            f"'{method.id}' is a sip-style method. Pick break or slice.)"
        )
    if (not treat.split_ok) and not method.good_for_liquid:
        return (
            f"(No story: {treat.phrase} is liquid, so it cannot be fairly shared by "
            f"'{method.id}'. Pick sip.)"
        )
    return "(No story: that treat and sharing method do not fit together.)"


# ---------------------------------------------------------------------------
# Prediction / verbs
# ---------------------------------------------------------------------------
def predict_share(world: World, treat: Treat, method: ShareMethod) -> dict:
    sim = world.copy()
    if method_works(treat, method):
        do_share(sim, treat, method, narrate=False)
    return {
        "works": method_works(treat, method),
        "mess": sim.get("treat").meters["mess"],
        "friend_relief": sim.get("friend").memes["relief"],
        "child_relief": sim.get("child").memes["relief"],
    }


def open_scene(world: World, setting: Setting, child: Entity, treat: Treat) -> None:
    child.memes["joy"] += 1
    world.say(
        f"{child.id} skipped along {setting.path}. {setting.sound_line} {setting.sky_line}"
    )
    world.say(
        f"In {child.pronoun('possessive')} hand was a blue kerchief tied in a tidy knot, "
        f"and inside it nestled {treat.phrase}. {treat.rhyme_line}"
    )


def meet_friend(world: World, child: Entity, friend: Entity) -> None:
    friend.memes["hunger"] += 1
    child.memes["notice"] += 1
    world.say(
        f"By the bend stood {friend.id}, quiet and slow, with a tummy making a tiny song."
    )
    world.say(
        f"{friend.id} smiled, but only a little. \"That smells nice,\" {friend.pronoun()} said, "
        f"\"and I have been walking a long time along.\""
    )


def selfish_thought(world: World, child: Entity, treat: Treat) -> None:
    child.memes["greed"] += 1
    propagate(world, narrate=False)
    world.say(
        f'Inside, {child.id} thought, "Oh dear, oh me, this treat is mine, and not very wide. '
        f'If I share it now, will I still have enough tucked safe by my side?"'
    )
    if child.memes["worry"] >= THRESHOLD:
        world.say(
            f'Another thought came tiptoeing in: "But {friend_name(world)} looks hungry and pale. '
            f'Keeping it all may fill my hand, yet leave my heart feeling small as a snail."'
        )


def friend_name(world: World) -> str:
    return world.get("friend").id


def helper_hint(world: World, helper: Helper) -> None:
    world.say(helper.arrival)
    world.say(helper.hint)


def choose_kindness(world: World, child: Entity) -> None:
    child.memes["resolve"] += 1
    world.say(
        f'{child.id} took a breath and had a second secret thought: '
        f'"Kind hands make room. I can share and still be glad."'
    )


def do_share(world: World, treat_cfg: Treat, method: ShareMethod, narrate: bool = True) -> None:
    child = world.get("child")
    friend = world.get("friend")
    treat = world.get("treat")
    world.facts["shared"] = True
    world.facts["shared_with"] = friend.id

    if treat_cfg.split_ok:
        treat.meters["pieces"] = 2.0
        child.meters["portion"] = 1.0
        friend.meters["portion"] = 1.0
    else:
        treat.meters["sips"] = 2.0
        child.meters["portion"] = 1.0
        friend.meters["portion"] = 1.0

    if treat_cfg.spill_risk > method.neatness:
        treat.meters["mess"] += 1
    propagate(world, narrate=False)

    if narrate:
        world.say(
            f"So {child.id} untied the kerchief, spread it flat, and {method.text}."
        )
        if treat.meters["mess"] >= THRESHOLD:
            world.say(
                f"A little sweetness dribbled and dabbed the cloth, but nobody frowned at the stain."
            )
        else:
            world.say(
                f"Not a crumb went tumbling far; the sharing was gentle and plain."
            )
        if treat_cfg.split_ok:
            world.say(
                f"{child.id} passed one {treat_cfg.piece_word} to {friend.id}, and kept one {treat_cfg.piece_word} near."
            )
        else:
            world.say(
                f"{child.id} held the cup while they took tiny turns, each careful and bright with cheer."
            )


def grateful_end(world: World, child: Entity, friend: Entity, helper: Helper) -> None:
    world.say(
        f'{friend.id} took the offered share and smiled much wider. '
        f'"Now the path feels merry," {friend.pronoun()} said.'
    )
    world.say(
        f'{child.id} felt the worry melt away and thought, '
        f'"A shared bite can make two faces bright instead."'
    )
    world.say(
        f"{helper.closing} Soon the two went on together, side by side in spring-soft light, "
        f"while the blue kerchief fluttered between them, and the day seemed twice as bright."
    )


def tell(
    setting: Setting,
    treat: Treat,
    method: ShareMethod,
    helper: Helper,
    *,
    child_name: str = "Mina",
    child_gender: str = "girl",
    friend_name_value: str = "Milo",
    friend_gender: str = "boy",
    trait: str = "thoughtful",
) -> World:
    world = World()
    child = world.add(Entity(
        id="child",
        kind="character",
        type=child_gender,
        label=child_name,
        role="owner",
        traits=[trait],
        attrs={"name": child_name},
    ))
    friend = world.add(Entity(
        id="friend",
        kind="character",
        type=friend_gender,
        label=friend_name_value,
        role="friend",
        attrs={"name": friend_name_value},
    ))
    world.add(Entity(
        id="treat",
        kind="thing",
        type="treat",
        label=treat.label,
        attrs={"phrase": treat.phrase},
    ))

    # stable facts read by prose and rules
    world.facts["shared"] = False
    world.facts["setting"] = setting
    world.facts["treat_cfg"] = treat
    world.facts["method"] = method
    world.facts["helper"] = helper
    world.facts["child_name"] = child_name
    world.facts["friend_name"] = friend_name_value

    open_scene(world, setting, NamedEntityView(child, child_name), treat)
    meet_friend(world, NamedEntityView(child, child_name), NamedEntityView(friend, friend_name_value))

    world.para()
    selfish_thought(world, NamedEntityView(child, child_name), treat)
    helper_hint(world, helper)
    choose_kindness(world, NamedEntityView(child, child_name))

    world.para()
    do_share(world, treat, method, narrate=True)
    grateful_end(world, NamedEntityView(child, child_name), NamedEntityView(friend, friend_name_value), helper)

    world.facts.update(
        child=child,
        friend=friend,
        helper_ent=helper,
        outcome="shared" if world.facts["shared"] else "kept",
        messy=world.get("treat").meters["mess"] >= THRESHOLD,
    )
    return world


class NamedEntityView:
    """A thin prose-safe wrapper exposing a display name while reusing pronouns."""
    def __init__(self, ent: Entity, display: str) -> None:
        self._ent = ent
        self.id = display
        self.type = ent.type
        self.attrs = ent.attrs
        self.meters = ent.meters
        self.memes = ent.memes

    def pronoun(self, case: str = "subject") -> str:
        return self._ent.pronoun(case)


# ---------------------------------------------------------------------------
# Story params
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    setting: str
    treat: str
    method: str
    helper: str
    child_name: str
    child_gender: str
    friend_name: str
    friend_gender: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
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
    "kerchief": [(
        "What is a kerchief?",
        "A kerchief is a small square cloth that can be tied, folded, or used to wrap something. People can use it to carry a snack neatly."
    )],
    "sharing": [(
        "Why is sharing kind?",
        "Sharing lets another person have some of what you have. It can turn one happy moment into a happy moment for two people."
    )],
    "inner": [(
        "What is an inner thought?",
        "An inner thought is something a person says quietly inside their mind. Other people cannot hear it unless the person chooses to tell them."
    )],
    "wink": [(
        "What is a wink?",
        "A wink is a quick close-and-open of one eye. People sometimes use a wink as a playful little sign."
    )],
    "muffin": [(
        "How can you share a muffin fairly?",
        "You can split it into two parts so each person gets some. Putting it on a cloth or plate can help keep crumbs from falling."
    )],
    "soup": [(
        "How can two people share a cup of soup carefully?",
        "They can take turns with small sips. Setting the cup down on something steady helps stop spills."
    )],
}
KNOWLEDGE_ORDER = ["kerchief", "sharing", "inner", "wink", "muffin", "soup"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    treat = f["treat_cfg"]
    helper = f["helper"]
    child_name = f["child_name"]
    friend_name_value = f["friend_name"]
    return [
        'Write a short rhyming story for a 3-to-5-year-old that includes the words "kerchief", "poop-pl", and "wink".',
        f"Tell a gentle sharing story in rhyme where {child_name} carries {treat.phrase} in a kerchief, meets {friend_name_value}, and has an inner monologue before choosing kindness.",
        f"Write a musical little tale where a helpful {helper.kind} gives a wink-like hint, and the ending shows that sharing can make the path feel brighter.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = world.get("child")
    friend = world.get("friend")
    treat = f["treat_cfg"]
    method = f["method"]
    helper = f["helper"]
    child_name = f["child_name"]
    friend_name_value = f["friend_name"]

    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child_name}, who was carrying {treat.phrase} in a blue kerchief, and {friend_name_value}, who met {child.pronoun('object')} on the path."
        ),
        (
            "What did the sound \"poop-pl\" describe?",
            "It described the small sound of the child's steps on the damp path. The silly sound helped the story feel bouncy and musical."
        ),
        (
            f"What was {child_name} thinking before sharing?",
            f"{child_name} first thought about keeping the whole treat because it was small and special. Then {child.pronoun('subject')} also thought about how hungry {friend_name_value} looked, which made the choice feel important."
        ),
        (
            f"How did the wink help {child_name}?",
            f"The wink was a tiny sign that nudged {child_name} toward kindness. It came right when {child.pronoun('subject')} was arguing inside {child.pronoun('possessive')} own mind, so it helped the generous thought grow stronger."
        ),
        (
            f"How did {child_name} share the treat?",
            f"{child_name} untied the kerchief and {method.qa_text}. That gave both children a fair share instead of leaving one child hungry."
        ),
    ]
    if f.get("messy"):
        qa.append((
            "Did sharing make a mess?",
            "A little. The treat was a bit tricky, so some sweetness dabbed the kerchief while they shared, but they were still glad to do it."
        ))
    else:
        qa.append((
            "Did sharing stay neat?",
            "Yes. The kerchief helped hold the treat steady while they shared it, so the kind plan worked neatly."
        ))
    qa.append((
        "How did the story end?",
        f"It ended with both children walking on together, brighter than before. The ending image of the fluttering blue kerchief shows that the treat was shared and the mood had changed."
    ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"kerchief", "sharing", "inner", "wink"}
    treat = world.facts["treat_cfg"]
    if treat.id == "muffin":
        tags.add("muffin")
    if treat.id == "soup":
        tags.add("soup")
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
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


# ---------------------------------------------------------------------------
# Trace / curated
# ---------------------------------------------------------------------------
def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if e.role:
            bits.append(f"role={e.role}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        setting="lane",
        treat="muffin",
        method="break",
        helper="grandma",
        child_name="Mina",
        child_gender="girl",
        friend_name="Milo",
        friend_gender="boy",
        trait="thoughtful",
    ),
    StoryParams(
        setting="orchard",
        treat="scone",
        method="slice",
        helper="sparrow",
        child_name="Poppy",
        child_gender="girl",
        friend_name="Finn",
        friend_gender="boy",
        trait="bright",
    ),
    StoryParams(
        setting="brook",
        treat="soup",
        method="sip",
        helper="auntie",
        child_name="Theo",
        child_gender="boy",
        friend_name="June",
        friend_gender="girl",
        trait="gentle",
    ),
]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
works(Treat, Method) :- split_ok(Treat), method_split(Method).
works(Treat, Method) :- liquid_treat(Treat), method_liquid(Method).
valid(Setting, Treat, Method, Helper) :- setting(Setting), treat(Treat), method(Method), helper(Helper), works(Treat, Method).

outcome(shared) :- chosen_treat(T), chosen_method(M), works(T, M).
:- chosen_treat(T), chosen_method(M), not works(T, M).

#show valid/4.
#show outcome/1.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for tid, treat in TREATS.items():
        lines.append(asp.fact("treat", tid))
        if treat.split_ok:
            lines.append(asp.fact("split_ok", tid))
        else:
            lines.append(asp.fact("liquid_treat", tid))
    for mid, method in METHODS.items():
        lines.append(asp.fact("method", mid))
        if method.good_for_split:
            lines.append(asp.fact("method_split", mid))
        if method.good_for_liquid:
            lines.append(asp.fact("method_liquid", mid))
    for hid in HELPERS:
        lines.append(asp.fact("helper", hid))
    return "\n".join(lines)


def asp_program(extra: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join([
        asp.fact("chosen_treat", params.treat),
        asp.fact("chosen_method", params.method),
    ])
    model = asp.one_model(asp_program(extra))
    outs = asp.atoms(model, "outcome")
    return outs[0][0] if outs else "?"


def asp_verify() -> int:
    rc = 0
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: ASP gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    cases = list(CURATED)
    for seed in range(20):
        try:
            p = resolve_params(build_parser().parse_args([]), random.Random(seed))
        except StoryError:
            continue
        p.seed = seed
        cases.append(p)

    bad = 0
    for p in cases:
        if asp_outcome(p) != "shared":
            bad += 1
    if bad == 0:
        print(f"OK: ASP outcome matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differed.")

    # smoke test normal generation + emit
    try:
        sample = generate(CURATED[0])
        emit(sample, trace=False, qa=False, header="### smoke")
        print("OK: smoke test generate/emit passed.")
    except Exception as err:  # pragma: no cover - verify path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


# ---------------------------------------------------------------------------
# Standard interface
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world: a child with a kerchief-wrapped treat learns that sharing can brighten a day."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--treat", choices=TREATS)
    ap.add_argument("--method", choices=METHODS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--child-name")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--friend-name")
    ap.add_argument("--friend-gender", choices=["girl", "boy"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [n for n in pool if n != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.treat and args.method:
        treat = TREATS[args.treat]
        method = METHODS[args.method]
        if not method_works(treat, method):
            raise StoryError(explain_rejection(treat, method))

    combos = [
        c for c in valid_combos()
        if (args.setting is None or c[0] == args.setting)
        and (args.treat is None or c[1] == args.treat)
        and (args.method is None or c[2] == args.method)
        and (args.helper is None or c[3] == args.helper)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, treat_id, method_id, helper_id = rng.choice(sorted(combos))
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    friend_gender = args.friend_gender or rng.choice(["girl", "boy"])
    child_name = args.child_name or _pick_name(rng, child_gender)
    friend_name = args.friend_name or _pick_name(rng, friend_gender, avoid=child_name)
    trait = rng.choice(TRAITS)

    return StoryParams(
        setting=setting_id,
        treat=treat_id,
        method=method_id,
        helper=helper_id,
        child_name=child_name,
        child_gender=child_gender,
        friend_name=friend_name,
        friend_gender=friend_gender,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError(f"(Unknown setting: {params.setting})")
    if params.treat not in TREATS:
        raise StoryError(f"(Unknown treat: {params.treat})")
    if params.method not in METHODS:
        raise StoryError(f"(Unknown method: {params.method})")
    if params.helper not in HELPERS:
        raise StoryError(f"(Unknown helper: {params.helper})")

    treat = TREATS[params.treat]
    method = METHODS[params.method]
    if not method_works(treat, method):
        raise StoryError(explain_rejection(treat, method))

    world = tell(
        SETTINGS[params.setting],
        treat,
        method,
        HELPERS[params.helper],
        child_name=params.child_name,
        child_gender=params.child_gender,
        friend_name_value=params.friend_name,
        friend_gender=params.friend_gender,
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
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, treat, method, helper) combos:\n")
        for setting_id, treat_id, method_id, helper_id in combos:
            print(f"  {setting_id:8} {treat_id:8} {method_id:6} {helper_id}")
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
            header = f"### {p.child_name} shares {p.treat} by {p.method} at {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
