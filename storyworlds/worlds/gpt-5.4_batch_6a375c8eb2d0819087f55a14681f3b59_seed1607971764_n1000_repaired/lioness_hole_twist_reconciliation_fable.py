#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/lioness_hole_twist_reconciliation_fable.py
=====================================================================

A standalone story world for a small fable domain: a lioness thinks a neighbor
has taken her cub's treasured toy, but the toy has really slipped into a hole.
The twist is the discovered mistake; the resolution is an apology, shared help,
and reconciliation.

The domain is intentionally narrow and constraint-checked. A story is only valid
when the lost object can plausibly fit into the chosen hole and the accused
neighbor has a natural way to reach it safely. The simulated world then drives
the prose: worry rises, suspicion causes hurt, the hidden object is found, and
trust is rebuilt through apology and help.

Run it
------
    python storyworlds/worlds/gpt-5.4/lioness_hole_twist_reconciliation_fable.py
    python storyworlds/worlds/gpt-5.4/lioness_hole_twist_reconciliation_fable.py --item bead_ring --hole burrow --neighbor monkey
    python storyworlds/worlds/gpt-5.4/lioness_hole_twist_reconciliation_fable.py --item drum --hole burrow
    python storyworlds/worlds/gpt-5.4/lioness_hole_twist_reconciliation_fable.py --all
    python storyworlds/worlds/gpt-5.4/lioness_hole_twist_reconciliation_fable.py --qa --json
    python storyworlds/worlds/gpt-5.4/lioness_hole_twist_reconciliation_fable.py --verify
"""

from __future__ import annotations

import argparse
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
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"lioness", "mother", "girl", "hen"}
        male = {"boy", "he"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]
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
class Item:
    id: str
    label: str
    phrase: str
    shine: str
    size: int
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
class Hole:
    id: str
    label: str
    phrase: str
    width: int
    depth: int
    clue: str
    ending_image: str
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
class Neighbor:
    id: str
    label: str
    type: str
    admiration: str
    method: str
    reach: int
    manner: str
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


def _r_missing_worry(world: World) -> list[str]:
    item = world.get("item")
    lioness = world.get("lioness")
    cub = world.get("cub")
    if item.meters["in_hole"] < THRESHOLD:
        return []
    sig = ("missing_worry",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    lioness.memes["worry"] += 1
    cub.memes["guilt"] += 1
    return []


def _r_suspicion_hurts(world: World) -> list[str]:
    lioness = world.get("lioness")
    neighbor = world.get("neighbor")
    if lioness.memes["suspicion"] < THRESHOLD:
        return []
    sig = ("suspicion_hurts",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    neighbor.memes["hurt"] += 1
    return []


def _r_apology_restores(world: World) -> list[str]:
    lioness = world.get("lioness")
    neighbor = world.get("neighbor")
    if lioness.memes["apology"] < THRESHOLD:
        return []
    sig = ("apology_restores",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    lioness.memes["regret"] = 0.0
    lioness.memes["suspicion"] = 0.0
    neighbor.memes["hurt"] = 0.0
    neighbor.memes["trust"] += 1
    lioness.memes["trust"] += 1
    return []


CAUSAL_RULES: list[Rule] = [
    Rule(name="missing_worry", tag="emotion", apply=_r_missing_worry),
    Rule(name="suspicion_hurts", tag="social", apply=_r_suspicion_hurts),
    Rule(name="apology_restores", tag="social", apply=_r_apology_restores),
]


def propagate(world: World) -> None:
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            out = rule.apply(world)
            if out is not None and any(True for _ in out):
                pass
            if rule.name in {name for name, *_ in world.fired}:
                continue
        count_before = len(world.fired)
        for rule in CAUSAL_RULES:
            rule.apply(world)
        changed = len(world.fired) > count_before


ITEMS = {
    "bead_ring": Item(
        id="bead_ring",
        label="bead ring",
        phrase="a bright bead ring",
        shine="blue beads that winked in the sun",
        size=1,
        tags={"beads", "toy"},
    ),
    "shell_ball": Item(
        id="shell_ball",
        label="shell ball",
        phrase="a little shell ball",
        shine="tiny pale shells tied in a neat round bundle",
        size=1,
        tags={"shell", "toy"},
    ),
    "reed_flute": Item(
        id="reed_flute",
        label="reed flute",
        phrase="a short reed flute",
        shine="a smooth, polished side that caught the light",
        size=2,
        tags={"flute", "music"},
    ),
    "drum": Item(
        id="drum",
        label="drum",
        phrase="a small drum",
        shine="a painted rim with red lines around it",
        size=3,
        tags={"drum", "music"},
    ),
}

HOLES = {
    "burrow": Hole(
        id="burrow",
        label="burrow hole",
        phrase="a rabbit burrow at the edge of the grass",
        width=1,
        depth=2,
        clue="a tiny sparkle deep in the burrow hole",
        ending_image="beside the burrow hole, now marked with a ring of white stones",
        tags={"burrow", "hole"},
    ),
    "root_hole": Hole(
        id="root_hole",
        label="root hole",
        phrase="a dark hole under an old tree root",
        width=2,
        depth=2,
        clue="a glimmer under the tree root",
        ending_image="by the old root hole, where sunlight reached in thin gold lines",
        tags={"tree", "hole"},
    ),
    "bank_hole": Hole(
        id="bank_hole",
        label="bank hole",
        phrase="a narrow hole in the dry riverbank",
        width=2,
        depth=3,
        clue="a flash of color inside the riverbank hole",
        ending_image="near the riverbank hole, with reeds whispering in the wind",
        tags={"riverbank", "hole"},
    ),
}

NEIGHBORS = {
    "monkey": Neighbor(
        id="monkey",
        label="Monkey",
        type="monkey",
        admiration="had clapped and said it was the prettiest plaything in the clearing",
        method="slid a long arm into the hole and curled careful fingers around the lost thing",
        reach=3,
        manner="lightly and without scratching the earth loose",
        tags={"monkey", "help"},
    ),
    "meerkat": Neighbor(
        id="meerkat",
        label="Meerkat",
        type="meerkat",
        admiration="had laughed and said the little treasure looked clever and bright",
        method="dug with quick, neat paws until the lost thing could be lifted free",
        reach=2,
        manner="patiently, pushing the sand aside in tidy little scoops",
        tags={"meerkat", "help"},
    ),
    "elephant": Neighbor(
        id="elephant",
        label="Elephant",
        type="elephant",
        admiration="had rumbled that the treasure was fine enough for a feast-day game",
        method="lowered a gentle trunk into the hole and drew the lost thing out",
        reach=4,
        manner="slowly and gently, so nothing cracked or bent",
        tags={"elephant", "help"},
    ),
}

CUB_NAMES = ["Kito", "Tamu", "Nia", "Suri", "Pili", "Zuri"]
TRAITS = ["proud", "eager", "bouncy", "curious", "quick", "playful"]


def item_fits_hole(item: Item, hole: Hole) -> bool:
    return item.size <= hole.width


def neighbor_can_reach(neighbor: Neighbor, hole: Hole) -> bool:
    return neighbor.reach >= hole.depth


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for item_id, item in ITEMS.items():
        for hole_id, hole in HOLES.items():
            if not item_fits_hole(item, hole):
                continue
            for neighbor_id, neighbor in NEIGHBORS.items():
                if neighbor_can_reach(neighbor, hole):
                    combos.append((item_id, hole_id, neighbor_id))
    return sorted(combos)


@dataclass
class StoryParams:
    item: str
    hole: str
    neighbor: str
    cub_name: str
    cub_trait: str
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


CURATED = [
    StoryParams(
        item="bead_ring",
        hole="burrow",
        neighbor="monkey",
        cub_name="Kito",
        cub_trait="proud",
        seed=101,
    ),
    StoryParams(
        item="shell_ball",
        hole="root_hole",
        neighbor="meerkat",
        cub_name="Nia",
        cub_trait="playful",
        seed=102,
    ),
    StoryParams(
        item="reed_flute",
        hole="bank_hole",
        neighbor="elephant",
        cub_name="Zuri",
        cub_trait="curious",
        seed=103,
    ),
    StoryParams(
        item="reed_flute",
        hole="root_hole",
        neighbor="monkey",
        cub_name="Tamu",
        cub_trait="eager",
        seed=104,
    ),
]


def explain_rejection(item: Item, hole: Hole, neighbor: Optional[Neighbor] = None) -> str:
    if not item_fits_hole(item, hole):
        return (
            f"(No story: {item.phrase} is too large to slip into {hole.phrase}. "
            f"The twist depends on the object truly vanishing into a hole.)"
        )
    if neighbor is not None and not neighbor_can_reach(neighbor, hole):
        return (
            f"(No story: {neighbor.label} cannot naturally reach into {hole.phrase}. "
            f"The reconciliation needs a helper who can actually recover the lost thing.)"
        )
    return "(No story: this combination does not support the hidden-object twist.)"


def tell(item_cfg: Item, hole_cfg: Hole, neighbor_cfg: Neighbor,
         cub_name: str = "Kito", cub_trait: str = "proud") -> World:
    world = World()

    lioness = world.add(Entity(
        id="lioness",
        kind="character",
        type="lioness",
        label="Lioness",
        role="mother",
        traits=["watchful", "strong"],
        attrs={"voice": "steady"},
    ))
    cub = world.add(Entity(
        id="cub",
        kind="character",
        type="cub",
        label=cub_name,
        role="child",
        traits=[cub_trait],
        attrs={"carelessness": cub_trait in {"proud", "bouncy", "eager"}},
    ))
    neighbor = world.add(Entity(
        id="neighbor",
        kind="character",
        type=neighbor_cfg.type,
        label=neighbor_cfg.label,
        role="neighbor",
        traits=[neighbor_cfg.manner],
        attrs={"method": neighbor_cfg.method},
    ))
    item = world.add(Entity(
        id="item",
        kind="thing",
        type="toy",
        label=item_cfg.label,
        role="prize",
        attrs={"size": item_cfg.size},
    ))
    hole = world.add(Entity(
        id="hole",
        kind="thing",
        type="hole",
        label=hole_cfg.label,
        role="place",
        attrs={"width": hole_cfg.width, "depth": hole_cfg.depth},
    ))

    lioness.memes["trust"] = 1.0
    neighbor.memes["trust"] = 1.0
    cub.memes["love_item"] = 1.0
    item.meters["held"] = 1.0
    item.meters["in_hole"] = 0.0
    item.meters["recovered"] = 0.0
    world.facts.update(
        item_cfg=item_cfg,
        hole_cfg=hole_cfg,
        neighbor_cfg=neighbor_cfg,
        lioness=lioness,
        cub=cub,
        neighbor=neighbor,
        item=item,
        hole=hole,
        accusation=False,
        recovered=False,
        reconciled=False,
    )

    world.say(
        f"One warm morning, a lioness rested beneath an acacia tree while her cub, {cub.label}, "
        f"played in the grass with {item_cfg.phrase}. It had {item_cfg.shine}, and {cub.label} "
        f"was proud to carry it from patch to patch of sun."
    )
    world.say(
        f"{neighbor_cfg.label} passed by and {neighbor_cfg.admiration}. "
        f"The lioness heard the praise and gave a small nod."
    )

    world.para()
    world.say(
        f"After a while, {cub.label} began tossing the {item_cfg.label} a little too high. "
        f"It bounced once, skipped twice, and vanished beside {hole_cfg.phrase}."
    )
    item.meters["held"] = 0.0
    item.meters["in_hole"] = 1.0
    propagate(world)
    world.say(
        f"{cub.label} pawed at the dust, but the treasure was gone. The lioness saw only the empty ground, "
        f"and worry tightened her chest."
    )

    world.para()
    lioness.memes["suspicion"] = 1.0
    lioness.memes["regret"] = 1.0
    propagate(world)
    world.facts["accusation"] = True
    world.say(
        f'Because {neighbor_cfg.label} had admired the toy, the lioness turned to {neighbor_cfg.label} and said, '
        f'"Did you take the {item_cfg.label}? My cub had it just now."'
    )
    world.say(
        f"{neighbor_cfg.label} stepped back, hurt but calm. "
        f'"No," {neighbor.pronoun()} said. "I liked it, but I did not take it."'
    )

    world.para()
    world.say(
        f"Then {neighbor_cfg.label} tilted {neighbor.pronoun('possessive')} head. "
        f'"Wait," {neighbor.pronoun()} said softly. "Look there."'
    )
    world.say(
        f"In the shadow by {hole_cfg.phrase}, they saw {hole_cfg.clue}. "
        f"The lost thing had never been stolen at all. It had fallen into the hole."
    )

    world.para()
    world.say(
        f"At once the lioness understood her mistake, and {cub.label} hid behind her foreleg. "
        f"The cub remembered the reckless toss and whispered that the game had grown too wild."
    )
    world.say(
        f"But {neighbor_cfg.label} did not walk away. {neighbor.pronoun().capitalize()} {neighbor_cfg.method}, "
        f"{neighbor_cfg.manner}. Soon the {item_cfg.label} was back in the cub's paws."
    )
    item.meters["in_hole"] = 0.0
    item.meters["recovered"] = 1.0
    world.facts["recovered"] = True

    world.para()
    lioness.memes["apology"] = 1.0
    propagate(world)
    world.facts["reconciled"] = True
    world.say(
        f'The lioness bowed her head. "I judged too quickly," she said. '
        f'"You were wronged, and yet you still helped us. Forgive me."'
    )
    world.say(
        f'{neighbor_cfg.label} smiled. "A lost thing can hide in a hole," {neighbor.pronoun()} said, '
        f'"and a hasty thought can hide the truth even faster. Let us be friends again."'
    )
    world.say(
        f"So they sat together {hole_cfg.ending_image}, while {cub.label} rolled the {item_cfg.label} only on flat ground. "
        f"And the lioness remembered that the strongest heart is not the quickest to accuse, but the quickest to make peace after learning the truth."
    )

    return world


KNOWLEDGE = {
    "hole": [(
        "Why can a hole hide something so quickly?",
        "A hole can hide something because it drops below the ground, where light is dim and little objects are hard to see. If a toy rolls in, it may vanish from sight in one moment."
    )],
    "monkey": [(
        "Why might a monkey be good at reaching into a small place?",
        "A monkey can be good at that because its arms and fingers are nimble. It can reach carefully where a larger paw might not fit."
    )],
    "meerkat": [(
        "Why is a meerkat good at digging?",
        "A meerkat is good at digging because it uses quick paws to move sand and earth. That helps it open a small space without making a big mess."
    )],
    "elephant": [(
        "How can an elephant help pick up something gently?",
        "An elephant can use its trunk like a careful hand. Even though the animal is large, the trunk can move slowly and lift delicate things."
    )],
    "beads": [(
        "What makes beads easy to lose?",
        "Beads are small and smooth, so they can slip and roll away quickly. That is why people often keep them in a string or ring."
    )],
    "shell": [(
        "Why might a shell ball roll away?",
        "A round little toy rolls because its shape keeps moving when it is nudged. On uneven ground, one bounce can send it farther than you expect."
    )],
    "music": [(
        "Why should you handle a small instrument carefully?",
        "A small instrument can be cracked or bent if it is tossed around. Careful hands help it keep making its clear sound."
    )],
    "toy": [(
        "Why is it good to play gently with a favorite toy?",
        "Gentle play helps a favorite toy last longer. It also makes it less likely to get lost or broken."
    )],
    "help": [(
        "Why does helping someone matter even after a mistake?",
        "Helping matters because kindness can mend hurt feelings. When someone chooses help over anger, friendship has a chance to grow again."
    )],
}
KNOWLEDGE_ORDER = ["hole", "toy", "beads", "shell", "music", "monkey", "meerkat", "elephant", "help"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    cub = f["cub"]
    item_cfg = f["item_cfg"]
    hole_cfg = f["hole_cfg"]
    neighbor_cfg = f["neighbor_cfg"]
    return [
        f'Write a short fable for young children that includes the words "lioness" and "hole".',
        f"Tell a fable where a lioness wrongly suspects {neighbor_cfg.label} after {cub.label}'s {item_cfg.label} disappears by {hole_cfg.phrase}, then learns the truth and makes peace.",
        f"Write a gentle twist story about a lost {item_cfg.label}, a mistaken accusation, and reconciliation after the hidden object is found.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    cub = f["cub"]
    lioness = f["lioness"]
    neighbor = f["neighbor"]
    item_cfg = f["item_cfg"]
    hole_cfg = f["hole_cfg"]
    neighbor_cfg = f["neighbor_cfg"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about a lioness, her cub {cub.label}, and {neighbor_cfg.label}. The trouble begins when the cub loses {item_cfg.phrase} near a hole."
        ),
        (
            f"Why did the lioness think {neighbor_cfg.label} had taken the {item_cfg.label}?",
            f"She remembered that {neighbor_cfg.label} had admired it just before it went missing. Because the toy vanished suddenly, her worry turned into suspicion before she looked carefully."
        ),
        (
            "What was the twist in the story?",
            f"The twist was that nobody had stolen the toy at all. It had slipped into {hole_cfg.phrase}, where a small glimmer gave away the truth."
        ),
        (
            f"How was the {item_cfg.label} brought back?",
            f"{neighbor_cfg.label} helped get it back by using a natural skill: {neighbor_cfg.method}. That kind help solved the problem and showed that the accusation had been unfair."
        ),
        (
            "How did the lioness and the neighbor reconcile?",
            f"The lioness bowed her head and admitted she had judged too quickly. {neighbor_cfg.label} accepted the apology and chose friendship over hurt, so peace returned between them."
        ),
        (
            f"What did the cub learn?",
            f"{cub.label} learned to play more carefully with treasured things. The cub also saw that a quick guess can wound a friend, while truth and apology can heal the harm."
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = set(f["item_cfg"].tags) | set(f["hole_cfg"].tags) | set(f["neighbor_cfg"].tags)
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
        lines.append(f"  {ent.id:8} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
fits(I,H) :- item(I), hole(H), item_size(I,S), hole_width(H,W), S <= W.
reachable(N,H) :- neighbor(N), hole(H), reach(N,R), hole_depth(H,D), R >= D.
valid(I,H,N) :- fits(I,H), reachable(N,H).

#show valid/3.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for item_id, item in ITEMS.items():
        lines.append(asp.fact("item", item_id))
        lines.append(asp.fact("item_size", item_id, item.size))
    for hole_id, hole in HOLES.items():
        lines.append(asp.fact("hole", hole_id))
        lines.append(asp.fact("hole_width", hole_id, hole.width))
        lines.append(asp.fact("hole_depth", hole_id, hole.depth))
    for neighbor_id, neighbor in NEIGHBORS.items():
        lines.append(asp.fact("neighbor", neighbor_id))
        lines.append(asp.fact("reach", neighbor_id, neighbor.reach))
    return "\n".join(lines)


def asp_program(show: str = "#show valid/3.") -> str:
    base = asp_facts()
    rules = ASP_RULES.replace("#show valid/3.", "")
    return f"{base}\n{rules}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def outcome_of(params: StoryParams) -> str:
    return "reconciled"


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

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("empty story")
        print("OK: smoke-test generation succeeded.")
    except Exception as err:  # pragma: no cover
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    parser = build_parser()
    for seed in range(10):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(seed))
            generated = generate(params)
            if "lioness" not in generated.story or "hole" not in generated.story:
                rc = 1
                print(f"Generated story missing required seed words for seed {seed}.")
                break
        except Exception as err:  # pragma: no cover
            rc = 1
            print(f"Random generation failed for seed {seed}: {err}")
            break

    if rc == 0:
        print("OK: random generation smoke tests passed.")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a lioness, a hidden object in a hole, a twist, and reconciliation."
    )
    ap.add_argument("--item", choices=sorted(ITEMS))
    ap.add_argument("--hole", choices=sorted(HOLES))
    ap.add_argument("--neighbor", choices=sorted(NEIGHBORS))
    ap.add_argument("--cub-name")
    ap.add_argument("--cub-trait", choices=sorted(TRAITS))
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP gate and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.item and args.hole:
        item = ITEMS[args.item]
        hole = HOLES[args.hole]
        if not item_fits_hole(item, hole):
            raise StoryError(explain_rejection(item, hole))
    if args.item and args.hole and args.neighbor:
        item = ITEMS[args.item]
        hole = HOLES[args.hole]
        neighbor = NEIGHBORS[args.neighbor]
        if not (item_fits_hole(item, hole) and neighbor_can_reach(neighbor, hole)):
            raise StoryError(explain_rejection(item, hole, neighbor))

    combos = [
        combo for combo in valid_combos()
        if (args.item is None or combo[0] == args.item)
        and (args.hole is None or combo[1] == args.hole)
        and (args.neighbor is None or combo[2] == args.neighbor)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    item_id, hole_id, neighbor_id = rng.choice(combos)
    cub_name = args.cub_name or rng.choice(CUB_NAMES)
    cub_trait = args.cub_trait or rng.choice(TRAITS)
    return StoryParams(
        item=item_id,
        hole=hole_id,
        neighbor=neighbor_id,
        cub_name=cub_name,
        cub_trait=cub_trait,
        seed=None,
    )


def generate(params: StoryParams) -> StorySample:
    if params.item not in ITEMS:
        raise StoryError(f"(Unknown item: {params.item})")
    if params.hole not in HOLES:
        raise StoryError(f"(Unknown hole: {params.hole})")
    if params.neighbor not in NEIGHBORS:
        raise StoryError(f"(Unknown neighbor: {params.neighbor})")

    item_cfg = ITEMS[params.item]
    hole_cfg = HOLES[params.hole]
    neighbor_cfg = NEIGHBORS[params.neighbor]
    if not item_fits_hole(item_cfg, hole_cfg):
        raise StoryError(explain_rejection(item_cfg, hole_cfg))
    if not neighbor_can_reach(neighbor_cfg, hole_cfg):
        raise StoryError(explain_rejection(item_cfg, hole_cfg, neighbor_cfg))

    world = tell(
        item_cfg=item_cfg,
        hole_cfg=hole_cfg,
        neighbor_cfg=neighbor_cfg,
        cub_name=params.cub_name,
        cub_trait=params.cub_trait,
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
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (item, hole, neighbor) combos:\n")
        for item_id, hole_id, neighbor_id in combos:
            print(f"  {item_id:10} {hole_id:10} {neighbor_id}")
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
            header = f"### {p.cub_name}: {p.item} / {p.hole} / {p.neighbor}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
