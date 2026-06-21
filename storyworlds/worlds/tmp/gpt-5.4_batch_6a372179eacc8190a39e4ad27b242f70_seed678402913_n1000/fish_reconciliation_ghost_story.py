#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/fish_reconciliation_ghost_story.py
=============================================================

A small story world for a gentle ghost story about a quarrel, a fish-shaped
treasure, and reconciliation by dark water. Two children argue, the fish item
slips into a spooky pond or boathouse pool, and a pale ghostly guide will only
help once the children stop blaming each other and make peace. The chosen
recovery method must actually fit the kind of lost item and the place.

The world model carries both physical meters (dropped, submerged, retrieved,
glow) and emotional memes (anger, guilt, fear, trust, relief). The rendered
prose follows the simulated state rather than filling a fixed template.

Run it
------
    python storyworlds/worlds/gpt-5.4/fish_reconciliation_ghost_story.py
    python storyworlds/worlds/gpt-5.4/fish_reconciliation_ghost_story.py --setting boathouse --item whistle --method magnet
    python storyworlds/worlds/gpt-5.4/fish_reconciliation_ghost_story.py --item lantern --method magnet
    python storyworlds/worlds/gpt-5.4/fish_reconciliation_ghost_story.py --all
    python storyworlds/worlds/gpt-5.4/fish_reconciliation_ghost_story.py --qa --json
    python storyworlds/worlds/gpt-5.4/fish_reconciliation_ghost_story.py --verify
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
from contextlib import redirect_stdout
from dataclasses import dataclass, field
from typing import Callable, Optional

# Make the shared result containers importable when this script is run directly.
# This file lives under storyworlds/worlds/gpt-5.4/, so we add storyworlds/.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
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

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Setting:
    id: str
    name: str
    opening: str
    water_name: str
    eerie: str
    ghost_form: str
    difficulty: int = 1
    allows: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class FishItem:
    id: str
    label: str
    phrase: str
    sink_text: str
    clue_text: str
    material: str = "wood"
    floats: bool = False
    fragile: bool = False
    metal: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class Method:
    id: str
    label: str
    phrase: str
    power: int = 1
    gentle: bool = False
    works_with_floaters: bool = False
    works_with_metal: bool = False
    works_with_sturdy: bool = False
    success_text: str = ""
    fail_text: str = ""
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

    def kids(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.role in {"child_a", "child_b"}]

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


def _r_drop_scare(world: World) -> list[str]:
    item = world.get("item")
    ghost = world.get("ghost")
    if item.meters["submerged"] < THRESHOLD:
        return []
    sig = ("drop_scare",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    for kid in world.kids():
        kid.memes["fear"] += 1
        kid.memes["guilt"] += 1
    ghost.meters["noticed"] += 1
    return ["__splash__"]


def _r_reconcile(world: World) -> list[str]:
    a, b = world.get("child_a"), world.get("child_b")
    if a.memes["apology"] < THRESHOLD or b.memes["apology"] < THRESHOLD:
        return []
    sig = ("reconcile",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    a.memes["anger"] = 0.0
    b.memes["anger"] = 0.0
    a.memes["trust"] += 1
    b.memes["trust"] += 1
    a.memes["relief"] += 1
    b.memes["relief"] += 1
    return ["__reconciled__"]


def _r_ghost_clue(world: World) -> list[str]:
    ghost = world.get("ghost")
    a, b = world.get("child_a"), world.get("child_b")
    if ghost.meters["noticed"] < THRESHOLD:
        return []
    if a.memes["trust"] < THRESHOLD or b.memes["trust"] < THRESHOLD:
        return []
    sig = ("ghost_clue",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    ghost.meters["glow"] += 1
    ghost.meters["guiding"] += 1
    return ["__ghostclue__"]


CAUSAL_RULES: list[Rule] = [
    Rule(name="drop_scare", tag="physical", apply=_r_drop_scare),
    Rule(name="reconcile", tag="social", apply=_r_reconcile),
    Rule(name="ghost_clue", tag="supernatural", apply=_r_ghost_clue),
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
        for s in produced:
            world.say(s)
    return produced


def method_compatible(setting: Setting, item: FishItem, method: Method) -> bool:
    if method.id not in setting.allows:
        return False
    if item.fragile and not method.gentle:
        return False
    if item.metal:
        return method.works_with_metal
    if item.floats:
        return method.works_with_floaters
    return method.works_with_sturdy


def loss_severity(setting: Setting, item: FishItem, delay: int) -> int:
    return setting.difficulty + delay + (1 if not item.floats else 0)


def is_recovered(setting: Setting, item: FishItem, method: Method, delay: int) -> bool:
    return method_compatible(setting, item, method) and method.power >= loss_severity(setting, item, delay)


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for sid, setting in SETTINGS.items():
        for iid, item in ITEMS.items():
            for mid, method in METHODS.items():
                if method_compatible(setting, item, method):
                    combos.append((sid, iid, mid))
    return combos


def predict_recovery(world: World, setting: Setting, item: FishItem, method: Method, delay: int) -> dict:
    sim = world.copy()
    sim.get("item").meters["submerged"] = 1
    propagate(sim, narrate=False)
    return {
        "compatible": method_compatible(setting, item, method),
        "severity": loss_severity(setting, item, delay),
        "recovered": is_recovered(setting, item, method, delay),
    }


def scene_opening(world: World, a: Entity, b: Entity, setting: Setting, item: FishItem) -> None:
    for kid in (a, b):
        kid.memes["calm"] += 1
    world.say(
        f"At dusk, {a.id} and {b.id} walked to {setting.name}. {setting.opening}"
    )
    world.say(
        f"In {a.pronoun('possessive')} pocket, they carried {item.phrase}. It was shaped like a fish, "
        f"and even in the dim light its little curve seemed to watch the water."
    )
    world.say(setting.eerie)


def begin_quarrel(world: World, a: Entity, b: Entity, holder: Entity, cause: str, item: FishItem) -> None:
    a.memes["anger"] += 1
    b.memes["anger"] += 1
    if cause == "turn":
        world.say(
            f'"It is my turn to hold the {item.label}," {holder.id} said. '
            f'The words came out sharp instead of playful.'
        )
        other = b if holder.id == a.id else a
        world.say(
            f'"You had it all the way here," {other.id} answered, reaching for it.'
        )
    elif cause == "blame":
        world.say(
            f'"You swung it too close to the water," {b.id} said, and {a.id} frowned at once.'
        )
        world.say(
            f'"I did not," {a.id} answered. "You are the one who bumped me."'
        )
    else:
        world.say(
            f'They both wanted to hear the fish piece click against the railing, and both reached at once.'
        )
        world.say(
            f'Their hands knocked together. What had been a game suddenly felt like a quarrel.'
        )


def drop_item(world: World, a: Entity, b: Entity, item_cfg: FishItem, setting: Setting) -> None:
    item = world.get("item")
    item.meters["dropped"] += 1
    item.meters["submerged"] += 1
    item.meters["lost"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Then the fish slipped free. It struck the wood with a tiny clink, skidded once, and fell into {setting.water_name}."
    )
    world.say(item_cfg.sink_text)
    world.say(
        f"For a second, neither child moved. The black water looked deeper than it had a moment before."
    )


def ghost_arrives(world: World, a: Entity, b: Entity, setting: Setting) -> None:
    ghost = world.get("ghost")
    ghost.meters["present"] += 1
    a.memes["fear"] += 1
    b.memes["fear"] += 1
    world.say(
        f"Out on the water, a pale shape gathered itself into {setting.ghost_form}."
    )
    world.say(
        '"No hands are steady when hearts are cross," the ghost whispered. "The water listens to anger."'
    )


def apologize(world: World, a: Entity, b: Entity) -> None:
    a.memes["apology"] += 1
    b.memes["apology"] += 1
    a.memes["guilt"] += 1
    b.memes["guilt"] += 1
    propagate(world, narrate=False)
    world.say(
        f'{a.id} swallowed hard. "I am sorry I grabbed."'
    )
    world.say(
        f'"And I am sorry I blamed you," {b.id} said. Their shoulders stopped pulling away from each other.'
    )


def ghost_guides(world: World, setting: Setting, item: FishItem, method: Method, delay: int) -> None:
    pred = predict_recovery(world, setting, item, method, delay)
    world.facts["predicted_severity"] = pred["severity"]
    world.facts["predicted_recovered"] = pred["recovered"]
    if world.get("ghost").meters["guiding"] >= THRESHOLD:
        world.say(
            f"The ghost lifted one misty hand. A thin ring of light opened on the water where {item.clue_text}."
        )
        world.say(
            f'"Try with {method.phrase}," it whispered. "Gently now. The pond gives better answers to children who have made peace."'
        )


def recover_success(world: World, a: Entity, b: Entity, setting: Setting, method: Method, item: FishItem) -> None:
    ent = world.get("item")
    ent.meters["retrieved"] += 1
    ent.meters["submerged"] = 0.0
    ent.meters["lost"] = 0.0
    a.memes["relief"] += 1
    b.memes["relief"] += 1
    a.memes["joy"] += 1
    b.memes["joy"] += 1
    world.say(
        method.success_text.format(water=setting.water_name, item=item.label)
    )
    world.say(
        f"When {a.id} passed it to {b.id}, {b.id} did not clutch it away. {b.pronoun().capitalize()} held it carefully, and then held it out to share."
    )
    world.say(
        f"By the time they looked up, the ghost had faded into the dark water, leaving only two small silver ripples shaped like fish."
    )


def recover_fail(world: World, a: Entity, b: Entity, setting: Setting, method: Method, item: FishItem) -> None:
    ent = world.get("item")
    ent.meters["submerged"] += 1
    a.memes["sadness"] += 1
    b.memes["sadness"] += 1
    world.say(
        method.fail_text.format(water=setting.water_name, item=item.label)
    )
    world.say(
        f"The fish was gone too deep for that night. Still, {a.id} and {b.id} stood shoulder to shoulder instead of apart."
    )
    world.say(
        f"The ghost bowed once, as if that mattered too. Then it thinned into moon-pale mist, and the water lay quiet again."
    )


def closing_after_loss(world: World, a: Entity, b: Entity, item: FishItem, setting: Setting) -> None:
    a.memes["trust"] += 1
    b.memes["trust"] += 1
    a.memes["relief"] += 1
    b.memes["relief"] += 1
    world.say(
        f'"We can come back in daylight," {a.id} said softly.'
    )
    world.say(
        f'"Together," {b.id} answered. They walked home with wet sleeves and steadier hearts, and behind them {setting.water_name} kept one last tiny circle of light.'
    )


def tell(
    setting: Setting,
    item_cfg: FishItem,
    method: Method,
    child_a_name: str = "Mina",
    child_a_gender: str = "girl",
    child_b_name: str = "Owen",
    child_b_gender: str = "boy",
    relation: str = "siblings",
    cause: str = "turn",
    holder: str = "child_a",
    delay: int = 0,
) -> World:
    world = World(setting)
    a = world.add(Entity(id="child_a", kind="character", type=child_a_gender, role="child_a", label=child_a_name))
    b = world.add(Entity(id="child_b", kind="character", type=child_b_gender, role="child_b", label=child_b_name))
    world.add(Entity(id="ghost", kind="character", type="ghost", role="ghost", label="the ghost"))
    world.add(Entity(id="item", kind="thing", type="fish_item", label=item_cfg.label, phrase=item_cfg.phrase))
    a.attrs["name"] = child_a_name
    b.attrs["name"] = child_b_name
    a.attrs["relation"] = relation
    b.attrs["relation"] = relation

    holder_ent = a if holder == "child_a" else b

    scene_opening(world, a, b, setting, item_cfg)

    world.para()
    begin_quarrel(world, a, b, holder_ent, cause, item_cfg)
    drop_item(world, a, b, item_cfg, setting)

    world.para()
    ghost_arrives(world, a, b, setting)
    apologize(world, a, b)
    ghost_guides(world, setting, item_cfg, method, delay)

    world.para()
    found = is_recovered(setting, item_cfg, method, delay)
    if found:
        recover_success(world, a, b, setting, method, item_cfg)
        outcome = "found"
    else:
        recover_fail(world, a, b, setting, method, item_cfg)
        world.para()
        closing_after_loss(world, a, b, item_cfg, setting)
        outcome = "lost"

    world.facts.update(
        child_a=a,
        child_b=b,
        child_a_name=child_a_name,
        child_b_name=child_b_name,
        relation=relation,
        cause=cause,
        holder=holder,
        setting=setting,
        item_cfg=item_cfg,
        item=world.get("item"),
        method=method,
        delay=delay,
        outcome=outcome,
        reconciled=("reconcile",) in world.fired or any(sig and sig[0] == "reconcile" for sig in world.fired),
        ghost_helped=world.get("ghost").meters["guiding"] >= THRESHOLD,
    )
    return world


@dataclass
class StoryParams:
    setting: str
    item: str
    method: str
    child_a_name: str
    child_a_gender: str
    child_b_name: str
    child_b_gender: str
    relation: str
    cause: str
    holder: str
    delay: int = 0
    seed: Optional[int] = None


SETTINGS = {
    "pond": Setting(
        id="pond",
        name="the old lily pond",
        opening="The reeds whispered against one another, and the last light made the water look like dark glass.",
        water_name="the pond",
        eerie="Some nights, grown-ups said, a quiet pond-ghost drifted there and watched over lost things.",
        ghost_form="a child-sized figure woven from fog and pond light",
        difficulty=1,
        allows={"net", "magnet", "hook"},
        tags={"pond", "ghost"},
    ),
    "boathouse": Setting(
        id="boathouse",
        name="the old boathouse landing",
        opening="Loose boards creaked under their shoes, and black water moved in the narrow slips below.",
        water_name="the boathouse water",
        eerie="From the rafters hung old ropes and soft shadows, the kind that make brave children speak in whispers.",
        ghost_form="a ferry-keeper made of damp moonlight",
        difficulty=2,
        allows={"magnet", "hook"},
        tags={"boathouse", "ghost"},
    ),
    "millpond": Setting(
        id="millpond",
        name="the millpond path",
        opening="A worn stone wall curved beside the water, and the mill wheel turned so slowly it seemed to sigh in its sleep.",
        water_name="the millpond",
        eerie="The place felt full of old listening, as if the night itself might answer if someone spoke too loudly.",
        ghost_form="a pale ripple that rose into a thin smiling spirit",
        difficulty=2,
        allows={"net", "magnet"},
        tags={"millpond", "ghost"},
    ),
}

ITEMS = {
    "lantern": FishItem(
        id="lantern",
        label="fish lantern",
        phrase="a paper fish lantern with a tiny candle cup inside, though tonight it held no flame",
        sink_text="It bobbed once like a startled silver fish, then drifted against the reeds where it might tear if pulled roughly.",
        clue_text="the lantern had snagged among the reeds, rocking softly",
        material="paper",
        floats=True,
        fragile=True,
        metal=False,
        tags={"fish", "lantern", "fragile"},
    ),
    "whistle": FishItem(
        id="whistle",
        label="tin fish whistle",
        phrase="a tin fish whistle on a faded blue string",
        sink_text="The whistle flashed once, like a scale turning over, and then sank with a small gulp into the dark.",
        clue_text="the whistle lay near a post, glinting faintly below the surface",
        material="tin",
        floats=False,
        fragile=False,
        metal=True,
        tags={"fish", "metal"},
    ),
    "box": FishItem(
        id="box",
        label="wooden fish box",
        phrase="a little wooden fish box carved by a grandparent long ago",
        sink_text="The box spun on one corner and dipped under the black water near the stones.",
        clue_text="the box had settled beside the stones, where a careful reach might catch it",
        material="wood",
        floats=False,
        fragile=False,
        metal=False,
        tags={"fish", "wood"},
    ),
}

METHODS = {
    "net": Method(
        id="net",
        label="landing net",
        phrase="the landing net",
        power=2,
        gentle=True,
        works_with_floaters=True,
        works_with_metal=True,
        works_with_sturdy=False,
        success_text="Using the landing net together, they eased it through {water} until the rim slid under the {item}. One slow lift, and the little treasure came up dripping but safe.",
        fail_text="They swept the landing net through {water} again and again, but the dark water folded over the place where the {item} had been.",
        qa_text="used the landing net together to lift it out",
        tags={"net", "recovery"},
    ),
    "magnet": Method(
        id="magnet",
        label="magnet on a cord",
        phrase="the magnet on a cord",
        power=3,
        gentle=True,
        works_with_floaters=False,
        works_with_metal=True,
        works_with_sturdy=False,
        success_text="They lowered the magnet on its cord into {water}. After one quiet tap below the surface, the line grew heavy, and up came the {item}, shining with drops.",
        fail_text="The magnet kissed the dark water and came back dripping, but it found no hold on the {item}.",
        qa_text="lowered a magnet on a cord until it caught the metal piece",
        tags={"magnet", "metal"},
    ),
    "hook": Method(
        id="hook",
        label="boat hook",
        phrase="the boat hook",
        power=2,
        gentle=False,
        works_with_floaters=False,
        works_with_metal=False,
        works_with_sturdy=True,
        success_text="They reached with the boat hook together, careful now that they were no longer tugging against each other. The hook caught the {item}, and they drew it out of {water} with both hands steady.",
        fail_text="They probed with the boat hook, but each touch sent rings across {water}, and the {item} slipped farther from reach.",
        qa_text="reached together with the boat hook and drew it back",
        tags={"hook", "recovery"},
    ),
}

GIRL_NAMES = ["Mina", "Lila", "Nora", "Tess", "Ivy", "June", "Clara", "Maisie"]
BOY_NAMES = ["Owen", "Ben", "Theo", "Max", "Finn", "Eli", "Jonah", "Sam"]
CAUSES = ["turn", "blame", "grab"]
RELATIONS = ["siblings", "friends"]
HOLDERS = ["child_a", "child_b"]


CURATED = [
    StoryParams(
        setting="pond",
        item="lantern",
        method="net",
        child_a_name="Mina",
        child_a_gender="girl",
        child_b_name="Owen",
        child_b_gender="boy",
        relation="siblings",
        cause="turn",
        holder="child_a",
        delay=0,
    ),
    StoryParams(
        setting="boathouse",
        item="whistle",
        method="magnet",
        child_a_name="Nora",
        child_a_gender="girl",
        child_b_name="Theo",
        child_b_gender="boy",
        relation="friends",
        cause="blame",
        holder="child_b",
        delay=1,
    ),
    StoryParams(
        setting="boathouse",
        item="box",
        method="hook",
        child_a_name="Clara",
        child_a_gender="girl",
        child_b_name="Ben",
        child_b_gender="boy",
        relation="siblings",
        cause="grab",
        holder="child_a",
        delay=1,
    ),
    StoryParams(
        setting="millpond",
        item="lantern",
        method="net",
        child_a_name="June",
        child_a_gender="girl",
        child_b_name="Finn",
        child_b_gender="boy",
        relation="friends",
        cause="turn",
        holder="child_b",
        delay=2,
    ),
    StoryParams(
        setting="pond",
        item="whistle",
        method="magnet",
        child_a_name="Ivy",
        child_a_gender="girl",
        child_b_name="Max",
        child_b_gender="boy",
        relation="siblings",
        cause="grab",
        holder="child_b",
        delay=0,
    ),
]


KNOWLEDGE = {
    "ghost": [
        (
            "What is a ghost story?",
            "A ghost story is a spooky story with a spirit or unexplained visitor in it. In a child-friendly ghost story, the ghost can be strange and eerie without being cruel."
        )
    ],
    "fish": [
        (
            "What is a fish?",
            "A fish is an animal that lives in water and breathes with gills. Many fish move by swishing their tails and fins."
        )
    ],
    "pond": [
        (
            "What is a pond?",
            "A pond is a small body of still water. Reeds, frogs, and fish can live there."
        )
    ],
    "boathouse": [
        (
            "What is a boathouse?",
            "A boathouse is a place by the water where boats and water gear are kept. It can sound creaky and echoey at night."
        )
    ],
    "millpond": [
        (
            "What is a millpond?",
            "A millpond is a pond or pool of water by an old mill. Water there may move slowly around wood and stone."
        )
    ],
    "lantern": [
        (
            "What is a lantern?",
            "A lantern is a light with a cover around it. Some lanterns use candles, and some use batteries."
        )
    ],
    "magnet": [
        (
            "What does a magnet do?",
            "A magnet can pull on certain kinds of metal, like iron or steel. That is why people sometimes use one to pick up metal things."
        )
    ],
    "net": [
        (
            "What is a net used for?",
            "A net is used to scoop or catch something gently. A soft net can lift a floating thing without poking it."
        )
    ],
    "hook": [
        (
            "What is a boat hook?",
            "A boat hook is a pole with a hook at the end. People use it to pull a boat or another sturdy thing closer."
        )
    ],
    "reconcile": [
        (
            "What does it mean to reconcile?",
            "To reconcile means to make peace after an argument. People reconcile when they stop blaming, say sorry, and choose to be kind again."
        )
    ],
}
KNOWLEDGE_ORDER = ["ghost", "fish", "pond", "boathouse", "millpond", "lantern", "magnet", "net", "hook", "reconcile"]


def display_name(ent: Entity) -> str:
    return ent.attrs.get("name", ent.label or ent.id)


def pair_noun(relation: str) -> str:
    return "two siblings" if relation == "siblings" else "two friends"


def explain_rejection(setting: Setting, item: FishItem, method: Method) -> str:
    if method.id not in setting.allows:
        allowed = ", ".join(sorted(setting.allows))
        return (
            f"(No story: {setting.name} does not plausibly have or allow {method.phrase}. "
            f"Try one of: {allowed}.)"
        )
    if item.fragile and not method.gentle:
        return (
            f"(No story: a {item.label} is too delicate for {method.label}. "
            f"The rescue tool would likely tear or crush it instead of saving it.)"
        )
    if item.metal and not method.works_with_metal:
        return (
            f"(No story: the lost item is metal, but {method.label} is not a sensible way to recover it here.)"
        )
    if item.floats and not method.works_with_floaters:
        return (
            f"(No story: the {item.label} floats and needs a gentle scooping tool, not {method.label}.)"
        )
    if (not item.floats) and (not item.metal) and not method.works_with_sturdy:
        return (
            f"(No story: the {item.label} is a sunken sturdy object, and {method.label} is not a good fit for reaching it.)"
        )
    return "(No story: this setting, item, and method do not make a reasonable ghost-story rescue.)"


def outcome_of(params: StoryParams) -> str:
    return "found" if is_recovered(SETTINGS[params.setting], ITEMS[params.item], METHODS[params.method], params.delay) else "lost"


ASP_RULES = r"""
allowed(S, M) :- setting(S), method(M), allows(S, M).

needs_float_tool(I) :- item(I), floats(I).
needs_metal_tool(I) :- item(I), metal(I).
needs_sturdy_tool(I) :- item(I), not floats(I), not metal(I).
needs_gentle(I) :- item(I), fragile(I).

compatible(S, I, M) :- allowed(S, M),
                       needs_float_tool(I), handles_float(M),
                       not needs_gentle(I).
compatible(S, I, M) :- allowed(S, I2), item(I), method(M), false :- S = I2.
compatible(S, I, M) :- allowed(S, M),
                       needs_float_tool(I), handles_float(M),
                       needs_gentle(I), gentle(M).
compatible(S, I, M) :- allowed(S, M),
                       needs_metal_tool(I), handles_metal(M),
                       not needs_gentle(I).
compatible(S, I, M) :- allowed(S, M),
                       needs_metal_tool(I), handles_metal(M),
                       needs_gentle(I), gentle(M).
compatible(S, I, M) :- allowed(S, M),
                       needs_sturdy_tool(I), handles_sturdy(M),
                       not needs_gentle(I).
compatible(S, I, M) :- allowed(S, M),
                       needs_sturdy_tool(I), handles_sturdy(M),
                       needs_gentle(I), gentle(M).

valid(S, I, M) :- compatible(S, I, M).

sink_cost(I, 1) :- item(I), not floats(I).
sink_cost(I, 0) :- item(I), floats(I).
severity(V) :- chosen_setting(S), chosen_item(I), delay(D), difficulty(S, DF), sink_cost(I, SC), V = DF + D + SC.
recovered :- chosen_setting(S), chosen_item(I), chosen_method(M), compatible(S, I, M), power(M, P), severity(V), P >= V.

outcome(found) :- recovered.
outcome(lost) :- not recovered.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        lines.append(asp.fact("difficulty", sid, setting.difficulty))
        for mid in sorted(setting.allows):
            lines.append(asp.fact("allows", sid, mid))
    for iid, item in ITEMS.items():
        lines.append(asp.fact("item", iid))
        if item.floats:
            lines.append(asp.fact("floats", iid))
        if item.fragile:
            lines.append(asp.fact("fragile", iid))
        if item.metal:
            lines.append(asp.fact("metal", iid))
    for mid, method in METHODS.items():
        lines.append(asp.fact("method", mid))
        lines.append(asp.fact("power", mid, method.power))
        if method.gentle:
            lines.append(asp.fact("gentle", mid))
        if method.works_with_floaters:
            lines.append(asp.fact("handles_float", mid))
        if method.works_with_metal:
            lines.append(asp.fact("handles_metal", mid))
        if method.works_with_sturdy:
            lines.append(asp.fact("handles_sturdy", mid))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    scenario = "\n".join(
        [
            asp.fact("chosen_setting", params.setting),
            asp.fact("chosen_item", params.item),
            asp.fact("chosen_method", params.method),
            asp.fact("delay", params.delay),
        ]
    )
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    a = f["child_a"]
    b = f["child_b"]
    setting = f["setting"]
    item = f["item_cfg"]
    outcome = f["outcome"]
    relation = f["relation"]
    pair = "siblings" if relation == "siblings" else "friends"
    prompts = [
        f'Write a gentle ghost story for a 3-to-5-year-old that includes the word "fish" and ends with reconciliation.',
        f"Tell a spooky-but-kind story where {f['child_a_name']} and {f['child_b_name']}, two {pair}, lose a fish-shaped keepsake in dark water after a quarrel and must make peace before they can solve the problem.",
        f'Write a short story set at {setting.name} where a ghost helps children stop blaming each other and work together.'
    ]
    if outcome == "lost":
        prompts.append(
            f"Make the ending bittersweet: the children do not get the {item.label} back that night, but they leave reconciled and calmer than before."
        )
    else:
        prompts.append(
            f"Make the ending comforting: once the children apologize, they recover the {item.label} together."
        )
    return prompts


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    a = f["child_a"]
    b = f["child_b"]
    setting = f["setting"]
    item = f["item_cfg"]
    method = f["method"]
    relation = f["relation"]
    outcome = f["outcome"]
    an = f["child_a_name"]
    bn = f["child_b_name"]
    pair = pair_noun(relation)
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair}, {an} and {bn}. They went to {setting.name} carrying a fish-shaped treasure."
        ),
        (
            f"Why did the fish item fall into the water?",
            f"It fell because the children were quarreling and both let sharp feelings guide their hands. The fish piece slipped free in the middle of the argument."
        ),
        (
            "What made the story feel like a ghost story?",
            f"The place was dark and eerie, and a pale ghost rose from the water to speak to the children. The ghost was strange and spooky, but it was not mean."
        ),
        (
            "How did the children reconcile?",
            f"They stopped blaming each other and both said they were sorry. That apology changed them from two children pulling apart into two children ready to act together."
        ),
    ]
    if f.get("ghost_helped"):
        qa.append(
            (
                "Why did the ghost help after they apologized?",
                "The ghost said angry hearts make unsteady hands. Once the children made peace, the ghost gave them a clue because they were calm enough to work together."
            )
        )
    if outcome == "found":
        qa.append(
            (
                f"How did they get the {item.label} back?",
                f"They {method.qa_text}. Because they had already reconciled, they handled the rescue carefully instead of fighting over it."
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It ended with the children holding the fish treasure carefully and sharing it instead of snatching it. The ghost faded away, leaving a quiet sign on the water that showed the night had changed."
            )
        )
    else:
        qa.append(
            (
                f"Did they get the {item.label} back that night?",
                f"No. They tried with {method.label}, but the dark water kept it out of reach. Even so, they left side by side, which shows the real change was in their hearts."
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It ended in a bittersweet way: the fish treasure stayed lost for the night, but the children walked home reconciled. The last small circle of light on the water showed the ghost had seen their peace."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    setting = f["setting"]
    item = f["item_cfg"]
    method = f["method"]
    tags = {"ghost", "fish", "reconcile"} | set(setting.tags) | set(item.tags) | set(method.tags)
    out: list[tuple[str, str]] = []
    for key in KNOWLEDGE_ORDER:
        if key in tags and key in KNOWLEDGE:
            out.extend(KNOWLEDGE[key])
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
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {e.id:8} ({e.type:9}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(sig[0] for sig in world.fired))}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a fish-shaped keepsake, a ghost, and reconciliation by dark water."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--method", choices=METHODS)
    ap.add_argument("--relation", choices=RELATIONS)
    ap.add_argument("--cause", choices=CAUSES)
    ap.add_argument("--delay", type=int, choices=[0, 1, 2], help="how long the children hesitate after dropping the item")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner matches the Python logic")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [n for n in pool if n != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.setting and args.item and args.method:
        setting = SETTINGS[args.setting]
        item = ITEMS[args.item]
        method = METHODS[args.method]
        if not method_compatible(setting, item, method):
            raise StoryError(explain_rejection(setting, item, method))

    combos = [
        combo
        for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.item is None or combo[1] == args.item)
        and (args.method is None or combo[2] == args.method)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, item_id, method_id = rng.choice(sorted(combos))
    relation = args.relation or rng.choice(RELATIONS)
    cause = args.cause or rng.choice(CAUSES)
    delay = args.delay if args.delay is not None else rng.randint(0, 2)

    child_a_gender = rng.choice(["girl", "boy"])
    child_b_gender = "boy" if child_a_gender == "girl" else "girl" if rng.random() < 0.6 else child_a_gender
    child_a_name = _pick_name(rng, child_a_gender)
    child_b_name = _pick_name(rng, child_b_gender, avoid=child_a_name)
    holder = rng.choice(HOLDERS)

    return StoryParams(
        setting=setting_id,
        item=item_id,
        method=method_id,
        child_a_name=child_a_name,
        child_a_gender=child_a_gender,
        child_b_name=child_b_name,
        child_b_gender=child_b_gender,
        relation=relation,
        cause=cause,
        holder=holder,
        delay=delay,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        setting = SETTINGS[params.setting]
        item = ITEMS[params.item]
        method = METHODS[params.method]
    except KeyError as exc:
        raise StoryError(f"(Invalid parameter key: {exc.args[0]})") from exc

    if not method_compatible(setting, item, method):
        raise StoryError(explain_rejection(setting, item, method))

    world = tell(
        setting=setting,
        item_cfg=item,
        method=method,
        child_a_name=params.child_a_name,
        child_a_gender=params.child_a_gender,
        child_b_name=params.child_b_name,
        child_b_gender=params.child_b_gender,
        relation=params.relation,
        cause=params.cause,
        holder=params.holder,
        delay=params.delay,
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
    python_set = set(valid_combos())
    clingo_set = set(asp_valid_combos())
    if python_set == clingo_set:
        print(f"OK: gate matches valid_combos() ({len(python_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    cases = list(CURATED)
    for seed in range(50):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
        except StoryError:
            continue
        params.seed = seed
        cases.append(params)

    mismatches = []
    for params in cases:
        py_out = outcome_of(params)
        asp_out = asp_outcome(params)
        if py_out != asp_out:
            mismatches.append((params, py_out, asp_out))
    if not mismatches:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {len(mismatches)}/{len(cases)} outcomes differ.")
        for params, py_out, asp_out in mismatches[:5]:
            print(" ", params, py_out, asp_out)

    try:
        sample = generate(CURATED[0])
        buf = io.StringIO()
        with redirect_stdout(buf):
            emit(sample, trace=True, qa=True, header="### smoke")
        if not sample.story.strip():
            raise StoryError("Smoke test generated an empty story.")
        print("OK: generate/emit smoke test passed.")
    except Exception as exc:
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/3.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, item, method) combos:\n")
        for setting, item, method in combos:
            print(f"  {setting:10} {item:8} {method}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        attempts = 0
        while len(samples) < args.n and attempts < max(50, args.n * 50):
            seed = base_seed + attempts
            attempts += 1
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
            header = f"### {p.child_a_name} and {p.child_b_name}: {p.item} at {p.setting} with {p.method} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
