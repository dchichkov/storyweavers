#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/lucid_bounty_litter_moral_value_teamwork_rhyming.py
================================================================================

A standalone story world about two children who find litter near a small natural
bounty and choose teamwork over rushing. The prose aims for a gentle rhyming
style while remaining driven by simulated state.

Run it
------
    python storyworlds/worlds/gpt-5.4/lucid_bounty_litter_moral_value_teamwork_rhyming.py
    python storyworlds/worlds/gpt-5.4/lucid_bounty_litter_moral_value_teamwork_rhyming.py --place orchard --bounty apples --litter bottles --tool grabber --amount big
    python storyworlds/worlds/gpt-5.4/lucid_bounty_litter_moral_value_teamwork_rhyming.py --asp
    python storyworlds/worlds/gpt-5.4/lucid_bounty_litter_moral_value_teamwork_rhyming.py --verify
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
TEAM_BASE = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
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
    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)


@dataclass
class Setting:
    id: str
    label: str
    path: str
    breeze: str
    affords_bounty: set[str] = field(default_factory=set)
    allows_litter: set[str] = field(default_factory=set)
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
class Bounty:
    id: str
    label: str
    phrase: str
    gather_verb: str
    color: str
    place_bit: str
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
class LitterKind:
    id: str
    label: str
    plural: bool
    harm: str
    rustle: str
    effort_small: int
    effort_big: int
    tags: set[str] = field(default_factory=set)

    def effort(self, amount: str) -> int:
        return self.effort_big if amount == "big" else self.effort_small

    def it(self) -> str:
        return "them" if self.plural else "it"
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
    bonus: int
    handles: set[str] = field(default_factory=set)
    method: str = ""
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

    def kids(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.role in {"leader", "helper"}]

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


def _r_risk(world: World) -> list[str]:
    patch = world.get("patch")
    litter = world.get("litter")
    out: list[str] = []
    if patch.meters["littered"] >= THRESHOLD:
        sig = ("risk",)
        if sig not in world.fired:
            world.fired.add(sig)
            patch.meters["blocked"] += 1
            patch.meters["spoil"] += 1
            for kid in world.kids():
                kid.memes["worry"] += 1
            out.append("__risk__")
    if litter.attrs.get("sharp_or_tangly"):
        sig = ("animal_risk",)
        if sig not in world.fired:
            world.fired.add(sig)
            world.get("bird").meters["risk"] += 1
            out.append("__animal_risk__")
    return out


def _r_clear(world: World) -> list[str]:
    patch = world.get("patch")
    litter = world.get("litter")
    out: list[str] = []
    if litter.meters["collected"] >= THRESHOLD and patch.meters["clear"] < THRESHOLD:
        sig = ("clear",)
        if sig not in world.fired:
            world.fired.add(sig)
            patch.meters["littered"] = 0.0
            patch.meters["blocked"] = 0.0
            patch.meters["clear"] += 1
            patch.meters["spoil"] = 0.0
            for kid in world.kids():
                kid.memes["pride"] += 1
                kid.memes["calm"] += 1
                kid.memes["worry"] = 0.0
            world.get("bird").meters["risk"] = 0.0
            out.append("__clear__")
    return out


def _r_harvest(world: World) -> list[str]:
    patch = world.get("patch")
    basket = world.get("basket")
    out: list[str] = []
    if patch.meters["clear"] >= THRESHOLD and basket.meters["full"] < THRESHOLD:
        sig = ("harvest",)
        if sig not in world.fired:
            world.fired.add(sig)
            basket.meters["full"] += 1
            for kid in world.kids():
                kid.memes["joy"] += 1
                kid.memes["teamwork"] += 1
            out.append("__harvest__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="risk", tag="physical", apply=_r_risk),
    Rule(name="clear", tag="physical", apply=_r_clear),
    Rule(name="harvest", tag="physical", apply=_r_harvest),
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


def valid_combo(place: str, bounty: str, litter: str, tool: str, amount: str) -> bool:
    if place not in SETTINGS or bounty not in BOUNTIES or litter not in LITTER or tool not in TOOLS:
        return False
    if amount not in {"small", "big"}:
        return False
    setting = SETTINGS[place]
    litter_cfg = LITTER[litter]
    tool_cfg = TOOLS[tool]
    if bounty not in setting.affords_bounty:
        return False
    if litter not in setting.allows_litter:
        return False
    if litter not in tool_cfg.handles:
        return False
    return TEAM_BASE + tool_cfg.bonus >= litter_cfg.effort(amount)


def valid_combos() -> list[tuple[str, str, str, str, str]]:
    combos: list[tuple[str, str, str, str, str]] = []
    for place, setting in SETTINGS.items():
        for bounty in sorted(setting.affords_bounty):
            for litter in sorted(setting.allows_litter):
                for tool in sorted(TOOLS):
                    for amount in ("small", "big"):
                        if valid_combo(place, bounty, litter, tool, amount):
                            combos.append((place, bounty, litter, tool, amount))
    return combos


def cleanup_effort(litter_cfg: LitterKind, amount: str) -> int:
    return litter_cfg.effort(amount)


def cleanup_power(tool_cfg: Tool) -> int:
    return TEAM_BASE + tool_cfg.bonus


def outcome_of(params: "StoryParams") -> str:
    if not valid_combo(params.place, params.bounty, params.litter, params.tool, params.amount):
        raise StoryError("(No story: the chosen place, bounty, litter, tool, and amount do not make a workable cleanup together.)")
    return "hard_won" if cleanup_effort(LITTER[params.litter], params.amount) >= 4 else "bright"


def predict_harm(world: World) -> dict:
    sim = world.copy()
    propagate(sim, narrate=False)
    return {
        "bird_risk": sim.get("bird").meters["risk"] >= THRESHOLD,
        "bounty_spoiled": sim.get("patch").meters["spoil"] >= THRESHOLD,
        "worry": sum(k.memes["worry"] for k in sim.kids()),
    }


def morning_opening(world: World, a: Entity, b: Entity, parent: Entity, bounty_cfg: Bounty) -> None:
    world.say(
        f"On a lucid morning light and bright, {a.id} and {b.id} stepped out in delight."
    )
    world.say(
        f"With {parent.label_word} close and day so fair, they hoped to find {bounty_cfg.phrase} there."
    )
    world.say(
        f"The {world.setting.label} hummed a gentle tune, with {world.setting.breeze} beneath the moon-faded noon."
    )


def spot_bounty(world: World, a: Entity, b: Entity, bounty_cfg: Bounty) -> None:
    world.say(
        f'Soon {a.id} cried, "What lovely bounty grows!" as {bounty_cfg.color} {bounty_cfg.label} peeped in rows.'
    )
    world.say(
        f"{b.id} smiled wide at the promised treat, for sharing a basket would be sweet."
    )


def discover_litter(world: World, litter_cfg: LitterKind, amount: str, bounty_cfg: Bounty) -> None:
    size = "a little" if amount == "small" else "a big"
    world.say(
        f"But near the {bounty_cfg.place_bit} they came to a stop: {size} pile of litter had dropped with a flop."
    )
    world.say(
        f"{litter_cfg.label.capitalize()} {litter_cfg.rustle}, untidy and bitter, turning a kind little patch into cluttered litter."
    )


def rush_idea(world: World, a: Entity, bounty_cfg: Bounty) -> None:
    a.memes["hurry"] += 1
    world.say(
        f'"Let us pick first and clean later," said {a.id} with a hop. "If we hurry along, we need never stop."'
    )


def lucid_warning(world: World, b: Entity, litter_cfg: LitterKind, tool_cfg: Tool, bounty_cfg: Bounty) -> None:
    pred = predict_harm(world)
    world.facts["predicted_bird_risk"] = pred["bird_risk"]
    world.facts["predicted_bounty_spoiled"] = pred["bounty_spoiled"]
    concern = f"It could {litter_cfg.harm}"
    extra = ""
    if pred["bird_risk"]:
        extra = " A robin could tug at it and end up in fright."
    world.say(
        f'{b.id} looked down with a lucid, clear stare. "The bounty is lovely, but first we should care."'
    )
    world.say(
        f'"{concern}, and spoil what we came here to share.{extra} If we work side by side, this patch can be fair."'
    )
    world.say(
        f'"We brought {tool_cfg.phrase}; with teamwork and cheer, we can make this whole corner clean, safe, and clear."'
    )


def agree_to_help(world: World, a: Entity, b: Entity) -> None:
    a.memes["care"] += 1
    b.memes["care"] += 1
    world.say(
        f"{a.id} grew quiet, then gave a small nod. {b.id} was right; care for the ground was a good, steady job."
    )
    world.say(
        f"Hand joined with hand, they made one little team, and the work felt lighter than it had seemed."
    )


def clean_patch(world: World, a: Entity, b: Entity, litter_cfg: LitterKind, tool_cfg: Tool, amount: str) -> None:
    litter = world.get("litter")
    patch = world.get("patch")
    basket = world.get("basket")
    power = cleanup_power(tool_cfg)
    effort = cleanup_effort(litter_cfg, amount)
    world.facts["power"] = power
    world.facts["effort"] = effort
    if amount == "big":
        world.say(
            f"They worked in a rhythm, a tidy-up song: {a.id} lifted and {b.id} carried along."
        )
        world.say(
            f"{tool_cfg.method.capitalize()}, then one more trip back; no one gave up when the pile still looked stacked."
        )
    else:
        world.say(
            f"They worked with quick care, not a shove and not a clatter; {tool_cfg.method}, and each small piece ceased to matter."
        )
    litter.meters["collected"] += 1
    basket.meters["cleanup_load"] += effort
    patch.meters["clearing"] += power
    propagate(world, narrate=False)
    world.say(
        "Bit by bit the ground looked bright, and what had been wrong turned kindly right."
    )


def gather_bounty(world: World, a: Entity, b: Entity, bounty_cfg: Bounty, parent: Entity) -> None:
    basket = world.get("basket")
    basket.attrs["bounty"] = bounty_cfg.label
    world.say(
        f"Then {a.id} and {b.id} began to {bounty_cfg.gather_verb}, filling their basket with careful delight."
    )
    world.say(
        f'''{parent.label_word.capitalize()} smiled and said, \"The sweetest share is gathered best when the place is clean and all can rest.\"'''
    )
    world.say(
        f"So home they went with bounty to share, and cleaner ground than they found out there."
    )


def closing_image(world: World, bounty_cfg: Bounty) -> None:
    bird = world.get("bird")
    if bird.meters["risk"] < THRESHOLD:
        world.say(
            f"A robin hopped near the {bounty_cfg.place_bit} at dusk's soft light, and the tidy earth made the ending bright."
        )
    else:
        world.say(
            "The path lay calm in evening light, and the children remembered how teamwork made it right."
        )

def tell(
    bounty_cfg: Bounty,
    litter_cfg: Litter,
    tool_cfg: Tool,
    amount: Amount,
    kid1: Kid1,
    kid1_gender: str,
    kid2: Kid2,
    kid2_gender: str,
    parent_type: ParentType,
    setting=None,
) -> World:
    world = World(setting=setting)
    a = world.add(Entity(id=kid1, kind="character", type=kid1_gender, label=kid1, role="leader"))
    b = world.add(Entity(id=kid2, kind="character", type=kid2_gender, label=kid2, role="helper"))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label="the parent", role="parent"))
    patch = world.add(Entity(id="patch", type="patch", label="the patch"))
    litter = world.add(Entity(
        id="litter",
        type="litter",
        label=litter_cfg.label,
        attrs={"sharp_or_tangly": "bird_risk" in litter_cfg.tags},
    ))
    bird = world.add(Entity(id="bird", type="bird", label="the robin"))
    basket = world.add(Entity(id="basket", type="basket", label="the basket"))

    patch.meters["littered"] = 1.0
    patch.meters["blocked"] = 0.0
    patch.meters["spoil"] = 0.0
    patch.meters["clear"] = 0.0
    patch.meters["clearing"] = 0.0
    litter.meters["collected"] = 0.0
    bird.meters["risk"] = 0.0
    basket.meters["full"] = 0.0
    basket.meters["cleanup_load"] = 0.0
    a.memes["worry"] = 0.0
    b.memes["worry"] = 0.0
    a.memes["joy"] = 0.0
    b.memes["joy"] = 0.0
    a.memes["teamwork"] = 0.0
    b.memes["teamwork"] = 0.0

    world.facts.update(
        setting=setting,
        bounty_cfg=bounty_cfg,
        litter_cfg=litter_cfg,
        tool_cfg=tool_cfg,
        amount=amount,
        parent=parent,
        kid1=a,
        kid2=b,
        patch=patch,
        litter=litter,
        bird=bird,
        basket=basket,
    )

    morning_opening(world, a, b, parent, bounty_cfg)
    spot_bounty(world, a, b, bounty_cfg)

    world.para()
    discover_litter(world, litter_cfg, amount, bounty_cfg)
    propagate(world, narrate=False)
    rush_idea(world, a, bounty_cfg)
    lucid_warning(world, b, litter_cfg, tool_cfg, bounty_cfg)

    world.para()
    agree_to_help(world, a, b)
    clean_patch(world, a, b, litter_cfg, tool_cfg, amount)

    world.para()
    gather_bounty(world, a, b, bounty_cfg, parent)
    closing_image(world, bounty_cfg)

    world.facts["outcome"] = outcome_of(
        StoryParams(
            place=setting.id,
            bounty=bounty_cfg.id,
            litter=litter_cfg.id,
            tool=tool_cfg.id,
            amount=amount,
            kid1=kid1,
            kid1_gender=kid1_gender,
            kid2=kid2,
            kid2_gender=kid2_gender,
            parent=parent_type,
            seed=None,
        )
    )
    return world
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


SETTINGS = {
    "orchard": Setting(
        id="orchard",
        label="orchard path",
        path="between the apple trees",
        breeze="a soft breeze through the leaves",
        affords_bounty={"apples"},
        allows_litter={"wrappers", "cans", "bottles"},
        tags={"orchard"},
    ),
    "berry_patch": Setting(
        id="berry_patch",
        label="berry patch",
        path="beside the low berry rows",
        breeze="a sweet breeze over the vines",
        affords_bounty={"berries"},
        allows_litter={"wrappers", "string"},
        tags={"berries"},
    ),
    "pumpkin_field": Setting(
        id="pumpkin_field",
        label="pumpkin field",
        path="by the round orange vines",
        breeze="a cool breeze across the rows",
        affords_bounty={"pumpkins"},
        allows_litter={"cans", "bottles", "string"},
        tags={"pumpkins"},
    ),
}

BOUNTIES = {
    "apples": Bounty(
        id="apples",
        label="apples",
        phrase="a red apple bounty",
        gather_verb="pick the apples",
        color="red",
        place_bit="tree roots",
        tags={"fruit", "apples"},
    ),
    "berries": Bounty(
        id="berries",
        label="berries",
        phrase="a berry bounty",
        gather_verb="pick the berries",
        color="purple",
        place_bit="berry rows",
        tags={"fruit", "berries"},
    ),
    "pumpkins": Bounty(
        id="pumpkins",
        label="pumpkins",
        phrase="a pumpkin bounty",
        gather_verb="gather the pumpkins",
        color="orange",
        place_bit="vine patch",
        tags={"pumpkins", "harvest"},
    ),
}

LITTER = {
    "wrappers": LitterKind(
        id="wrappers",
        label="wrappers",
        plural=True,
        harm="blow into the plants and smother the little shoots",
        rustle="fluttered and whispered",
        effort_small=1,
        effort_big=2,
        tags={"litter", "recycling"},
    ),
    "cans": LitterKind(
        id="cans",
        label="cans",
        plural=True,
        harm="roll under small feet and make someone trip",
        rustle="clinked in the grass",
        effort_small=2,
        effort_big=3,
        tags={"litter", "recycling"},
    ),
    "bottles": LitterKind(
        id="bottles",
        label="bottles",
        plural=True,
        harm="glint sharply and make the path unsafe",
        rustle="shone hard in the sun",
        effort_small=2,
        effort_big=4,
        tags={"litter", "recycling", "bird_risk"},
    ),
    "string": LitterKind(
        id="string",
        label="string",
        plural=False,
        harm="tangle around little legs and tender stems",
        rustle="lay curled like a tricky line",
        effort_small=2,
        effort_big=4,
        tags={"litter", "bird_risk"},
    ),
}

TOOLS = {
    "gloves": Tool(
        id="gloves",
        label="gloves",
        phrase="their gloves",
        bonus=1,
        handles={"wrappers", "string"},
        method="they pinched and lifted each piece with their gloves",
        tags={"gloves"},
    ),
    "bag": Tool(
        id="bag",
        label="trash bag",
        phrase="a sturdy bag",
        bonus=1,
        handles={"wrappers", "cans"},
        method="they held the bag wide and dropped the mess inside",
        tags={"bag"},
    ),
    "grabber": Tool(
        id="grabber",
        label="grabber",
        phrase="a long grabber",
        bonus=2,
        handles={"wrappers", "cans", "bottles", "string"},
        method="they reached, gripped, and carried each piece away with the grabber",
        tags={"grabber"},
    ),
    "crate": Tool(
        id="crate",
        label="recycling crate",
        phrase="a blue recycling crate",
        bonus=2,
        handles={"cans", "bottles"},
        method="they lifted each hard piece and stacked it into the crate",
        tags={"recycling"},
    ),
}

GIRL_NAMES = ["Mia", "Lily", "Nora", "Ava", "Ella", "Zoe", "Ruby", "Anna"]
BOY_NAMES = ["Ben", "Leo", "Max", "Sam", "Theo", "Eli", "Noah", "Finn"]


def pair_label(a: Entity, b: Entity) -> str:
    if a.type == "girl" and b.type == "girl":
        return "two friends"
    if a.type == "boy" and b.type == "boy":
        return "two friends"
    return "two friends"


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    k1, k2 = f["kid1"], f["kid2"]
    setting, bounty_cfg, litter_cfg = f["setting"], f["bounty_cfg"], f["litter_cfg"]
    return [
        f'Write a short rhyming story for a 3-to-5-year-old that includes the words "lucid", "bounty", and "litter".',
        f"Tell a gentle teamwork story where {k1.id} and {k2.id} find {litter_cfg.label} in an {setting.id.replace('_', ' ')} before gathering {bounty_cfg.label}, and they choose caring action over rushing.",
        "Write a child-facing moral story in rhyme where children clean a messy place together and learn that sharing work helps everyone share joy.",
    ]


KNOWLEDGE = {
    "litter": [
        (
            "What is litter?",
            "Litter is trash left on the ground where it does not belong. It can make a place dirty and unsafe for people, plants, and animals.",
        )
    ],
    "recycling": [
        (
            "What does recycling mean?",
            "Recycling means putting some used things, like cans or bottles, where they can be made into new things. It helps keep useful materials out of the grass and away from animals.",
        )
    ],
    "gloves": [
        (
            "Why do people wear gloves when they clean up?",
            "Gloves help protect your hands from dirt and rough edges. They also make it easier to pick up messy things carefully.",
        )
    ],
    "grabber": [
        (
            "What is a grabber tool?",
            "A grabber is a long tool that helps you pick things up without bending down or touching them directly. It is useful for cleanup jobs.",
        )
    ],
    "fruit": [
        (
            "What does bounty mean in a harvest story?",
            "Bounty means there is plenty of something good to gather, like fruit or vegetables. It often means nature has given a rich, happy harvest.",
        )
    ],
    "teamwork": [
        (
            "Why is teamwork helpful?",
            "Teamwork helps people share a job so it feels smaller and gets done better. Working together can also help everyone feel proud and included.",
        )
    ],
    "bird": [
        (
            "Why can litter be bad for birds?",
            "Birds may peck at shiny trash or get tangled in string and plastic. That can scare them or hurt them.",
        )
    ],
}
KNOWLEDGE_ORDER = ["litter", "recycling", "gloves", "grabber", "fruit", "teamwork", "bird"]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    a, b = f["kid1"], f["kid2"]
    parent = f["parent"]
    setting = f["setting"]
    bounty_cfg = f["bounty_cfg"]
    litter_cfg = f["litter_cfg"]
    tool_cfg = f["tool_cfg"]
    amount = f["amount"]
    hard = f["outcome"] == "hard_won"
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair_label(a, b)}, {a.id} and {b.id}, who went with their {parent.label_word} to look for {bounty_cfg.label}. They found something messy first and had to decide what kind of helpers they would be.",
        ),
        (
            f"What did the children hope to gather?",
            f"They hoped to gather {bounty_cfg.phrase}. The bounty was waiting in the patch, but the litter stood in the way.",
        ),
        (
            "What problem did they find?",
            f"They found {litter_cfg.label} on the ground near the {bounty_cfg.place_bit}. The litter made the place feel wrong and could {litter_cfg.harm}.",
        ),
        (
            f"Why did {b.id} ask to clean before picking the bounty?",
            f"{b.id} looked at the mess with a lucid, careful thought and saw that the patch could be spoiled if they ignored it. {b.pronoun().capitalize()} wanted the place to be safe for the harvest and for small animals too.",
        ),
        (
            "How did teamwork help?",
            f"They used {tool_cfg.phrase} and worked side by side instead of leaving the job to one person. Because they shared the work, the patch became clean enough for gathering and everyone felt proud.",
        ),
    ]
    if f.get("predicted_bird_risk"):
        qa.append(
            (
                "How could the litter have hurt an animal?",
                f"The story hinted that a robin could have been in danger, especially near the {litter_cfg.label}. Trash on the ground can trap or scare a small animal before people even notice.",
            )
        )
    if hard:
        qa.append(
            (
                "Was the cleanup easy or hard?",
                f"It was a hard job because the pile was big and took more than one quick lift. The children kept going together, and that steady teamwork is what changed the ending.",
            )
        )
    else:
        qa.append(
            (
                "How did the story end?",
                f"It ended brightly: the children cleaned the patch, gathered the bounty, and walked home with something good to share. The clean ground at the end showed that kind choices can spread outward.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags: set[str] = {"litter", "teamwork", "fruit"}
    litter_cfg = world.facts["litter_cfg"]
    tool_cfg = world.facts["tool_cfg"]
    tags |= set(litter_cfg.tags)
    tags |= set(tool_cfg.tags)
    if world.facts.get("predicted_bird_risk"):
        tags.add("bird")
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
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:8} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)
@dataclass
class StoryParams:
    place: str
    bounty: str
    litter: str
    tool: str
    amount: str
    kid1: str
    kid1_gender: str
    kid2: str
    kid2_gender: str
    parent: str
    seed: Optional[int] = None




CURATED = [
    StoryParams(
        place="orchard",
        bounty="apples",
        litter="wrappers",
        tool="bag",
        amount="small",
        kid1="Mia",
        kid1_gender="girl",
        kid2="Ben",
        kid2_gender="boy",
        parent="mother",
    ),
    StoryParams(
        place="berry_patch",
        bounty="berries",
        litter="string",
        tool="grabber",
        amount="big",
        kid1="Nora",
        kid1_gender="girl",
        kid2="Leo",
        kid2_gender="boy",
        parent="father",
    ),
    StoryParams(
        place="pumpkin_field",
        bounty="pumpkins",
        litter="bottles",
        tool="crate",
        amount="big",
        kid1="Ava",
        kid1_gender="girl",
        kid2="Sam",
        kid2_gender="boy",
        parent="mother",
    ),
    StoryParams(
        place="orchard",
        bounty="apples",
        litter="cans",
        tool="grabber",
        amount="small",
        kid1="Ella",
        kid1_gender="girl",
        kid2="Max",
        kid2_gender="boy",
        parent="father",
    ),
    StoryParams(
        place="berry_patch",
        bounty="berries",
        litter="wrappers",
        tool="gloves",
        amount="small",
        kid1="Ruby",
        kid1_gender="girl",
        kid2="Finn",
        kid2_gender="boy",
        parent="mother",
    ),
]


def explain_rejection(place: str, bounty: str, litter: str, tool: str, amount: str) -> str:
    if place in SETTINGS and bounty in BOUNTIES and bounty not in SETTINGS[place].affords_bounty:
        return f"(No story: {SETTINGS[place].label} does not offer a believable {BOUNTIES[bounty].label} bounty.)"
    if place in SETTINGS and litter in LITTER and litter not in SETTINGS[place].allows_litter:
        return f"(No story: {LITTER[litter].label} are not part of the plausible messes for {SETTINGS[place].label}.)"
    if tool in TOOLS and litter in LITTER and litter not in TOOLS[tool].handles:
        return f"(No story: {TOOLS[tool].label} is not a good tool for {LITTER[litter].label}.)"
    if tool in TOOLS and litter in LITTER and amount in {"small", "big"}:
        need = cleanup_effort(LITTER[litter], amount)
        have = cleanup_power(TOOLS[tool])
        if have < need:
            return f"(No story: this cleanup is too big for teamwork plus {TOOLS[tool].label}. Pick a stronger tool or a smaller mess.)"
    return "(No story: the requested choices do not make a reasonable cleanup story.)"


ASP_RULES = r"""
valid(P,B,L,T,A) :- setting(P), bounty(B), litter(L), tool(T), amount(A),
                    affords(P,B), allows(P,L), handles(T,L),
                    effort(L,A,E), team_base(Bs), bonus(T,Bn), Bs + Bn >= E.

hard_won(P,B,L,T,A) :- valid(P,B,L,T,A), effort(L,A,E), E >= 4.
bright(P,B,L,T,A)   :- valid(P,B,L,T,A), effort(L,A,E), E < 4.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for pid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        for bid in sorted(setting.affords_bounty):
            lines.append(asp.fact("affords", pid, bid))
        for lid in sorted(setting.allows_litter):
            lines.append(asp.fact("allows", pid, lid))
    for bid in BOUNTIES:
        lines.append(asp.fact("bounty", bid))
    for lid, litter_cfg in LITTER.items():
        lines.append(asp.fact("litter", lid))
        lines.append(asp.fact("effort", lid, "small", litter_cfg.effort_small))
        lines.append(asp.fact("effort", lid, "big", litter_cfg.effort_big))
    for tid, tool_cfg in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        lines.append(asp.fact("bonus", tid, tool_cfg.bonus))
        for lid in sorted(tool_cfg.handles):
            lines.append(asp.fact("handles", tid, lid))
    for amount in ("small", "big"):
        lines.append(asp.fact("amount", amount))
    lines.append(asp.fact("team_base", TEAM_BASE))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/5."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    scenario = "\n".join(
        [
            asp.fact("chosen", params.place, params.bounty, params.litter, params.tool, params.amount),
            f"want_hard :- chosen({asp.term(params.place)},{asp.term(params.bounty)},{asp.term(params.litter)},{asp.term(params.tool)},{asp.term(params.amount)}), hard_won({asp.term(params.place)},{asp.term(params.bounty)},{asp.term(params.litter)},{asp.term(params.tool)},{asp.term(params.amount)}).",
            f"want_bright :- chosen({asp.term(params.place)},{asp.term(params.bounty)},{asp.term(params.litter)},{asp.term(params.tool)},{asp.term(params.amount)}), bright({asp.term(params.place)},{asp.term(params.bounty)},{asp.term(params.litter)},{asp.term(params.tool)},{asp.term(params.amount)}).",
        ]
    )
    model = asp.one_model(asp_program(scenario, "#show want_hard/0.\n#show want_bright/0."))
    names = {sym.name for sym in model}
    if "want_hard" in names:
        return "hard_won"
    if "want_bright" in names:
        return "bright"
    return "?"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a lucid cleanup, a shared bounty, and the moral power of teamwork."
    )
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--bounty", choices=BOUNTIES)
    ap.add_argument("--litter", choices=LITTER)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--amount", choices=["small", "big"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP model matches the Python logic")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_child(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [n for n in pool if n != avoid]
    return rng.choice(choices), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.bounty and args.litter and args.tool and args.amount:
        if not valid_combo(args.place, args.bounty, args.litter, args.tool, args.amount):
            raise StoryError(explain_rejection(args.place, args.bounty, args.litter, args.tool, args.amount))

    combos = [
        c
        for c in valid_combos()
        if (args.place is None or c[0] == args.place)
        and (args.bounty is None or c[1] == args.bounty)
        and (args.litter is None or c[2] == args.litter)
        and (args.tool is None or c[3] == args.tool)
        and (args.amount is None or c[4] == args.amount)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place, bounty, litter, tool, amount = rng.choice(sorted(combos))
    kid1, kid1_gender = _pick_child(rng)
    kid2, kid2_gender = _pick_child(rng, avoid=kid1)
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(
        place=place,
        bounty=bounty,
        litter=litter,
        tool=tool,
        amount=amount,
        kid1=kid1,
        kid1_gender=kid1_gender,
        kid2=kid2,
        kid2_gender=kid2_gender,
        parent=parent,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in SETTINGS or params.bounty not in BOUNTIES or params.litter not in LITTER or params.tool not in TOOLS:
        raise StoryError("(No story: one or more requested ids are unknown.)")
    if params.amount not in {"small", "big"}:
        raise StoryError("(No story: amount must be 'small' or 'big'.)")
    if not valid_combo(params.place, params.bounty, params.litter, params.tool, params.amount):
        raise StoryError(explain_rejection(params.place, params.bounty, params.litter, params.tool, params.amount))

    world = tell(
        setting=SETTINGS[params.place],
        bounty_cfg=BOUNTIES[params.bounty],
        litter_cfg=LITTER[params.litter],
        tool_cfg=TOOLS[params.tool],
        amount=params.amount,
        kid1=params.kid1,
        kid1_gender=params.kid1_gender,
        kid2=params.kid2,
        kid2_gender=params.kid2_gender,
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


def asp_verify() -> int:
    rc = 0

    py_valid = set(valid_combos())
    asp_valid = set(asp_valid_combos())
    if py_valid == asp_valid:
        print(f"OK: gate matches valid_combos() ({len(py_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if asp_valid - py_valid:
            print("  only in clingo:", sorted(asp_valid - py_valid))
        if py_valid - asp_valid:
            print("  only in python:", sorted(py_valid - asp_valid))

    cases = list(CURATED)
    for seed in range(50):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
            params.seed = seed
            cases.append(params)
        except StoryError:
            rc = 1
            print(f"Unexpected resolution failure for seed {seed}.")
            break

    mismatches = 0
    for params in cases:
        try:
            py = outcome_of(params)
            asp = asp_outcome(params)
            if py != asp:
                mismatches += 1
        except StoryError as err:
            mismatches += 1
            print(f"Outcome error on {params}: {err}")
    if mismatches == 0:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {mismatches}/{len(cases)} outcomes differ.")

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("smoke test produced an empty story")
        emit(smoke, trace=False, qa=False, header="-- smoke test --")
        print("OK: smoke test generate/emit succeeded.")
    except Exception as err:  # pragma: no cover - verify path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/5.\n#show bright/5.\n#show hard_won/5."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, bounty, litter, tool, amount) combos:\n")
        for place, bounty, litter, tool, amount in combos:
            print(f"  {place:13} {bounty:9} {litter:9} {tool:8} {amount}")
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
            header = f"### {p.kid1} & {p.kid2}: {p.bounty} at {p.place} with {p.litter} ({p.tool}, {p.amount}, {outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
