#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/slap_sharing_teamwork_animal_story.py
===============================================================

A standalone story world for gentle animal stories about sharing and teamwork.

Premise
-------
Two young animals find a tasty, heavy treat and want to bring it to a cozy
eating spot. One child first tries to keep the treat to themself and carry it
alone. That fails in a concrete, physical way: the load tips, something lands
with a slap, and the treat nearly gets spoiled. The turn comes when the child
chooses to share, the pair use the carrying tool together, and the ending image
shows them eating side by side.

Reasonableness constraint
-------------------------
Not every treat can be moved with every tool in every place. A story is only
generated when the carrying tool fits the place's terrain and is strong enough
for the treat's weight. Invalid explicit choices raise StoryError with a plain
explanation.

Run it
------
python storyworlds/worlds/gpt-5.4/slap_sharing_teamwork_animal_story.py
python storyworlds/worlds/gpt-5.4/slap_sharing_teamwork_animal_story.py --setting meadow --cargo pumpkin --tool bark_sled
python storyworlds/worlds/gpt-5.4/slap_sharing_teamwork_animal_story.py --setting riverbank --tool vine_sling
python storyworlds/worlds/gpt-5.4/slap_sharing_teamwork_animal_story.py -n 5 --seed 7 --qa
python storyworlds/worlds/gpt-5.4/slap_sharing_teamwork_animal_story.py --all
python storyworlds/worlds/gpt-5.4/slap_sharing_teamwork_animal_story.py --verify
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


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "doe", "hen"}
        male = {"boy", "buck", "drake"}
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


@dataclass
class Setting:
    id: str
    place: str
    path: str
    snack_spot: str
    terrain: str
    detail: str
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
class Cargo:
    id: str
    label: str
    phrase: str
    weight: int
    edible: str
    mishap: str
    rescue: str
    ending: str
    fragile: bool = False
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
class Tool:
    id: str
    label: str
    phrase: str
    capacity: int
    terrains: set[str]
    teamwork_text: str
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
        self.facts: dict = {
            "setting": setting,
            "mishap_happened": False,
            "shared": False,
            "teamwork": False,
        }

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


def _r_heavy_solo_tip(world: World) -> list[str]:
    cargo = world.get("cargo")
    if cargo.attrs.get("carriers", []) != [world.facts["selfish"].id]:
        return []
    if cargo.attrs.get("weight", 0) <= 1:
        return []
    sig = ("heavy_solo_tip", tuple(cargo.attrs.get("carriers", [])))
    if sig in world.fired:
        return []
    world.fired.add(sig)
    cargo.meters["tipped"] += 1
    cargo.meters["messy"] += 1
    world.facts["mishap_happened"] = True
    world.facts["slap_sound"] = True
    world.facts["selfish"].memes["embarrassed"] += 1
    world.facts["sharer"].memes["concern"] += 1
    return ["__tip__"]


def _r_shared_teamwork_moves(world: World) -> list[str]:
    cargo = world.get("cargo")
    carriers = cargo.attrs.get("carriers", [])
    wanted = sorted([world.facts["selfish"].id, world.facts["sharer"].id])
    if sorted(carriers) != wanted:
        return []
    if not world.get("tool").attrs.get("shared_handles", False):
        return []
    sig = ("shared_teamwork_moves", tuple(sorted(carriers)))
    if sig in world.fired:
        return []
    world.fired.add(sig)
    cargo.meters["moved"] += 1
    cargo.meters["steady"] += 1
    cargo.meters["tipped"] = 0.0
    world.facts["teamwork"] = True
    for kid in (world.facts["selfish"], world.facts["sharer"]):
        kid.memes["proud"] += 1
        kid.memes["joy"] += 1
    return ["__moved__"]


CAUSAL_RULES = [
    Rule(name="heavy_solo_tip", tag="physical", apply=_r_heavy_solo_tip),
    Rule(name="shared_teamwork_moves", tag="social", apply=_r_shared_teamwork_moves),
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


def combo_valid(setting: Setting, cargo: Cargo, tool: Tool) -> bool:
    return setting.terrain in tool.terrains and tool.capacity >= cargo.weight


def explain_rejection(setting: Setting, cargo: Cargo, tool: Tool) -> str:
    if setting.terrain not in tool.terrains:
        supported = ", ".join(sorted(tool.terrains))
        return (
            f"(No story: {tool.label} is for {supported} ground, but {setting.place} "
            f"has a {setting.terrain} path. Pick a tool that fits the place.)"
        )
    if tool.capacity < cargo.weight:
        return (
            f"(No story: {cargo.phrase} is too heavy for {tool.label}. "
            f"The tool can carry {tool.capacity}, but the treat weighs {cargo.weight}.)"
        )
    return "(No story: this carrying plan does not make sense.)"


def valid_combos() -> list[tuple[str, str, str]]:
    out: list[tuple[str, str, str]] = []
    for sid, setting in SETTINGS.items():
        for cid, cargo in CARGOES.items():
            for tid, tool in TOOLS.items():
                if combo_valid(setting, cargo, tool):
                    out.append((sid, cid, tid))
    return sorted(out)


def predict_mishap(world: World) -> dict:
    sim = world.copy()
    cargo = sim.get("cargo")
    cargo.attrs["carriers"] = [sim.facts["selfish"].id]
    propagate(sim, narrate=False)
    return {
        "tips": cargo.meters["tipped"] >= THRESHOLD,
        "messy": cargo.meters["messy"] >= THRESHOLD,
    }


def introduce(world: World, selfish: Entity, sharer: Entity, cargo: Cargo, tool: Tool) -> None:
    world.say(
        f"On a bright morning at {world.setting.place}, {selfish.id} and {sharer.id} "
        f"found {cargo.phrase} beside {world.setting.detail}."
    )
    world.say(
        f"They wanted to take it along {world.setting.path} to {world.setting.snack_spot}, "
        f"and a nearby {tool.label} looked just right for the job."
    )


def describe_animals(world: World, selfish: Entity, sharer: Entity) -> None:
    world.say(
        f"{selfish.id} was eager and a little grabby that day, while {sharer.id} was "
        f"patient and liked doing things together."
    )


def claim(world: World, selfish: Entity, sharer: Entity, cargo: Cargo) -> None:
    selfish.memes["greedy"] += 1
    world.say(
        f'"I found it first," said {selfish.id}. "I can carry {cargo.label} by myself, '
        f"and maybe I will eat the biggest part too."
    )
    world.say(
        f'{sharer.id} blinked and said, "It will taste better if we share, and it looks '
        f'heavy for one pair of paws."'
    )


def warn(world: World, selfish: Entity, cargo: Cargo, tool: Tool) -> None:
    pred = predict_mishap(world)
    world.facts["predicted_tip"] = pred["tips"]
    if pred["tips"]:
        world.say(
            f'{selfish.id} still grabbed both sides of the {tool.label}. Even before lifting, '
            f"the load looked wobbly."
        )


def solo_attempt(world: World, selfish: Entity, cargo_ent: Entity, tool_ent: Entity) -> None:
    selfish.meters["strain"] += float(cargo_ent.attrs["weight"])
    cargo_ent.attrs["carriers"] = [selfish.id]
    tool_ent.attrs["shared_handles"] = False
    propagate(world, narrate=False)


def mishap(world: World, selfish: Entity, sharer: Entity, cargo: Cargo, tool: Tool) -> None:
    world.say(
        f"{selfish.id} tugged hard. The {tool.label} twisted, one side dropped with a slap, "
        f"and {cargo.mishap}"
    )
    world.say(
        f"{selfish.id} froze with hot cheeks. {sharer.id} hurried close instead of scolding."
    )


def rescue_and_share(world: World, selfish: Entity, sharer: Entity, cargo: Cargo) -> None:
    selfish.memes["generous"] += 1
    sharer.memes["kindness"] += 1
    world.facts["shared"] = True
    world.say(
        f'"I was not making it better," {selfish.id} admitted. "Let\'s wash it and share."'
    )
    world.say(
        f"Together they {cargo.rescue}, and the treat looked good again."
    )


def teamwork_carry(world: World, selfish: Entity, sharer: Entity, cargo_ent: Entity, tool_ent: Entity, tool: Tool) -> None:
    selfish.memes["cooperate"] += 1
    sharer.memes["cooperate"] += 1
    cargo_ent.attrs["carriers"] = [selfish.id, sharer.id]
    tool_ent.attrs["shared_handles"] = True
    propagate(world, narrate=False)
    world.say(
        f"{selfish.id} took one side and {sharer.id} took the other. {tool.teamwork_text}"
    )


def ending(world: World, selfish: Entity, sharer: Entity, cargo: Cargo) -> None:
    selfish.memes["peace"] += 1
    sharer.memes["peace"] += 1
    world.say(
        f"At {world.setting.snack_spot}, they sat shoulder to shoulder and {cargo.ending}"
    )
    world.say(
        f"From then on, whenever a job looked big, {selfish.id} remembered that sharing and "
        f"teamwork made small paws feel strong."
    )
@dataclass
class StoryParams:
    setting: str
    cargo: str
    tool: str
    selfish_name: str
    selfish_type: str
    sharer_name: str
    sharer_type: str
    species: str
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
    "sharing_food": [
        (
            "Why is sharing food kind?",
            "Sharing food is kind because everyone gets a turn and no one feels left out. It also helps friends enjoy the treat together instead of arguing over it.",
        )
    ],
    "teamwork_tool": [
        (
            "What is teamwork?",
            "Teamwork is when two or more friends help with the same job together. Big jobs often get easier when everyone carries a part."
        )
    ],
    "pumpkin": [
        (
            "Why is a pumpkin hard for one small animal to carry?",
            "A pumpkin is round and heavy, so it can roll if one side drops. Two friends can keep it steadier than one friend alone."
        )
    ],
    "berries": [
        (
            "Why do berries spill easily?",
            "Berries are small and round, so they can bounce out when a basket tips. Carrying a basket level helps keep them inside."
        )
    ],
    "seed_cake": [
        (
            "Why should a wrapped cake stay flat?",
            "A wrapped cake can slide if it tilts too much. Keeping it flat helps the crumbs and filling stay in place."
        )
    ],
    "sled": [
        (
            "What does a sled do?",
            "A sled lets you pull something over the ground instead of lifting all of it. That makes a heavy load easier to move."
        )
    ],
    "sling": [
        (
            "Why can a sling wobble?",
            "A sling hangs from its handles, so if one side pulls harder, the middle swings. Matching your steps helps the load stay steadier."
        )
    ],
    "tray": [
        (
            "Why do trays need level hands?",
            "A tray works best when both sides stay even. If one side dips, the things on top can slide or spill."
        )
    ],
    "river": [
        (
            "What is a riverbank?",
            "A riverbank is the ground beside a river. It can have pebbles, reeds, and wet places near the water."
        )
    ],
    "pond": [
        (
            "What grows near a pond?",
            "You often see lily pads, reeds, moss, and muddy ground near a pond. Many small animals like to play there."
        )
    ],
    "meadow": [
        (
            "What is a meadow?",
            "A meadow is an open grassy place with flowers and soft ground. It is a good place for little animals to walk and snack."
        )
    ],
}
KNOWLEDGE_ORDER = [
    "sharing_food",
    "teamwork_tool",
    "pumpkin",
    "berries",
    "seed_cake",
    "sled",
    "sling",
    "tray",
    "river",
    "pond",
    "meadow",
]


def generation_prompts(world: World) -> list[str]:
    selfish = world.facts["selfish"]
    sharer = world.facts["sharer"]
    cargo = world.facts["cargo_cfg"]
    tool = world.facts["tool_cfg"]
    species = world.facts["species"]
    return [
        f'Write a short Animal Story for a 3-to-5-year-old that includes the word "slap" and shows sharing and teamwork.',
        f"Tell a gentle story about two young {species}s, {selfish.id} and {sharer.id}, trying to carry {cargo.phrase} with a {tool.label}.",
        f"Write a simple animal story where one friend first tries to keep a treat alone, then learns to share and work together.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    selfish = world.facts["selfish"]
    sharer = world.facts["sharer"]
    cargo = world.facts["cargo_cfg"]
    tool = world.facts["tool_cfg"]
    setting = world.facts["setting"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {selfish.id} and {sharer.id}, two young {world.facts['species']}s at {setting.place}. They found {cargo.phrase} and wanted to carry it to {setting.snack_spot}.",
        ),
        (
            f"Why did {selfish.id} get into trouble?",
            f"{selfish.id} wanted to keep the treat and carry it alone, even though it was too heavy and wobbly for one small animal. Because one side dropped, the load tipped and a mishap happened with a slap.",
        ),
        (
            "What did the sound slap happen during?",
            f"The word slap happened when one side of the {tool.label} dropped to the ground during the solo try. That sound showed the carrying plan had gone wrong.",
        ),
        (
            f"How did {sharer.id} help fix the problem?",
            f"{sharer.id} hurried over and helped save the treat instead of teasing {selfish.pronoun('object')}. Then the two of them cleaned it up and carried it properly together.",
        ),
        (
            "How did sharing change the story?",
            f"When {selfish.id} chose to share, the quarrel stopped and the treat became something for both friends instead of just one. Sharing also made it easier to trust each other for the bigger job.",
        ),
        (
            "How did teamwork help them succeed?",
            f"Each friend took one side, so the load stayed level and steady. Because they worked together, they reached {setting.snack_spot} and could enjoy the food side by side.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = set(world.facts["cargo_cfg"].tags) | set(world.facts["tool_cfg"].tags) | set(world.facts["setting"].tags)
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
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
        parts = []
        if ent.role:
            parts.append(f"role={ent.role}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v or k == "carriers"}
            if shown:
                parts.append(f"attrs={shown}")
        if meters:
            parts.append(f"meters={dict(meters)}")
        if memes:
            parts.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:8} ({ent.type:7}) {' '.join(parts)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        setting="meadow",
        cargo="pumpkin",
        tool="bark_sled",
        selfish_name="Pip",
        selfish_type="boy",
        sharer_name="Moss",
        sharer_type="girl",
        species="rabbit",
    ),
    StoryParams(
        setting="riverbank",
        cargo="berry_basket",
        tool="reed_tray",
        selfish_name="Otis",
        selfish_type="boy",
        sharer_name="Daisy",
        sharer_type="girl",
        species="otter",
    ),
    StoryParams(
        setting="pond_edge",
        cargo="seed_cake",
        tool="bark_sled",
        selfish_name="Tad",
        selfish_type="boy",
        sharer_name="Wren",
        sharer_type="girl",
        species="duck",
    ),
    StoryParams(
        setting="meadow",
        cargo="berry_basket",
        tool="vine_sling",
        selfish_name="Bram",
        selfish_type="boy",
        sharer_name="Poppy",
        sharer_type="girl",
        species="beaver",
    ),
]


ASP_RULES = r"""
movable(S, C, T) :- setting(S), cargo(C), tool(T),
                    terrain(S, R), supports(T, R),
                    weight(C, W), capacity(T, K), K >= W.
valid(S, C, T) :- movable(S, C, T).

heavy(C) :- weight(C, W), W > 1.
solo_tips :- chosen_cargo(C), heavy(C).
shared_success :- chosen_setting(S), chosen_cargo(C), chosen_tool(T), valid(S, C, T).
outcome(mishap_then_share) :- solo_tips, shared_success.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        lines.append(asp.fact("terrain", sid, setting.terrain))
    for cid, cargo in CARGOES.items():
        lines.append(asp.fact("cargo", cid))
        lines.append(asp.fact("weight", cid, cargo.weight))
    for tid, tool in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        lines.append(asp.fact("capacity", tid, tool.capacity))
        for terrain in sorted(tool.terrains):
            lines.append(asp.fact("supports", tid, terrain))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen_setting", params.setting),
            asp.fact("chosen_cargo", params.cargo),
            asp.fact("chosen_tool", params.tool),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def outcome_of(params: StoryParams) -> str:
    if not combo_valid(SETTINGS[params.setting], CARGOES[params.cargo], TOOLS[params.tool]):
        return "invalid"
    return "mishap_then_share"


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

    cases = list(CURATED)
    for seed in range(20):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
            params.seed = seed
            cases.append(params)
        except StoryError:
            rc = 1
            print(f"Resolve failed unexpectedly for seed {seed}.")
            break

    bad = [p for p in cases if asp_outcome(p) != outcome_of(p)]
    if not bad:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {len(bad)} outcomes differ.")

    try:
        sample = generate(cases[0])
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            emit(sample, trace=True, qa=True, header="### smoke")
        if not sample.story.strip():
            raise StoryError("smoke test generated an empty story")
        print("OK: smoke test generate()/emit() succeeded.")
    except Exception as err:  # pragma: no cover
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Animal story world: a heavy treat, a selfish try, a slap, and a shared teamwork ending."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--cargo", choices=CARGOES)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--species", choices=SPECIES)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid (setting, cargo, tool) combos from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [n for n in pool if n != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.setting and args.cargo and args.tool:
        setting = SETTINGS[args.setting]
        cargo = CARGOES[args.cargo]
        tool = TOOLS[args.tool]
        if not combo_valid(setting, cargo, tool):
            raise StoryError(explain_rejection(setting, cargo, tool))

    combos = [
        combo
        for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.cargo is None or combo[1] == args.cargo)
        and (args.tool is None or combo[2] == args.tool)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, cargo_id, tool_id = rng.choice(combos)
    selfish_type = rng.choice(["boy", "girl"])
    sharer_type = "girl" if selfish_type == "boy" else "boy"
    selfish_name = _pick_name(rng, selfish_type)
    sharer_name = _pick_name(rng, sharer_type, avoid=selfish_name)
    species = args.species or rng.choice(SPECIES)
    return StoryParams(
        setting=setting_id,
        cargo=cargo_id,
        tool=tool_id,
        selfish_name=selfish_name,
        selfish_type=selfish_type,
        sharer_name=sharer_name,
        sharer_type=sharer_type,
        species=species,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        setting = SETTINGS[params.setting]
        cargo = CARGOES[params.cargo]
        tool = TOOLS[params.tool]
    except KeyError as err:
        raise StoryError(f"(Unknown story parameter: {err.args[0]})") from None

    if params.species not in SPECIES:
        raise StoryError(f"(Unknown species: {params.species})")
    if not combo_valid(setting, cargo, tool):
        raise StoryError(explain_rejection(setting, cargo, tool))

    world = tell(
        setting=setting,
        cargo=cargo,
        tool=tool,
        selfish_name=params.selfish_name,
        selfish_type=params.selfish_type,
        sharer_name=params.sharer_name,
        sharer_type=params.sharer_type,
        species=params.species,
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
        print(asp_program("", "#show valid/3.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} valid (setting, cargo, tool) combos:\n")
        for setting, cargo, tool in combos:
            print(f"  {setting:10} {cargo:12} {tool}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

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
            header = f"### {p.selfish_name} and {p.sharer_name}: {p.cargo} at {p.setting} with {p.tool}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")






def tell(
    setting: Setting,
    cargo: Cargo,
    tool: Tool,
    selfish_name: str = "Pip",
    selfish_type: str = "boy",
    sharer_name: str = "Moss",
    sharer_type: str = "girl",
    species: str = "otter",
) -> World:
    world = World(setting)
    selfish = world.add(
        Entity(
            id=selfish_name,
            kind="character",
            type=selfish_type,
            label=species,
            role="selfish",
            traits=["eager"],
            attrs={},
            tags={species},
        )
    )
    sharer = world.add(
        Entity(
            id=sharer_name,
            kind="character",
            type=sharer_type,
            label=species,
            role="sharer",
            traits=["patient"],
            attrs={},
            tags={species},
        )
    )
    cargo_ent = world.add(
        Entity(
            id="cargo",
            type="cargo",
            label=cargo.label,
            attrs={"weight": cargo.weight, "carriers": []},
            tags=set(cargo.tags),
        )
    )
    tool_ent = world.add(
        Entity(
            id="tool",
            type="tool",
            label=tool.label,
            attrs={"shared_handles": False},
            tags=set(tool.tags),
        )
    )

    world.facts.update(
        selfish=selfish,
        sharer=sharer,
        cargo_cfg=cargo,
        tool_cfg=tool,
        species=species,
    )

    introduce(world, selfish, sharer, cargo, tool)
    describe_animals(world, selfish, sharer)

    world.para()
    claim(world, selfish, sharer, cargo)
    warn(world, selfish, cargo, tool)
    solo_attempt(world, selfish, cargo_ent, tool_ent)

    world.para()
    mishap(world, selfish, sharer, cargo, tool)
    rescue_and_share(world, selfish, sharer, cargo)

    world.para()
    teamwork_carry(world, selfish, sharer, cargo_ent, tool_ent, tool)
    ending(world, selfish, sharer, cargo)

    world.facts["outcome"] = "mishap_then_share"
    return world


SETTINGS = {
    "meadow": Setting(
        id="meadow",
        place="the clover meadow",
        path="the soft grass path",
        snack_spot="a flat sunny stone",
        terrain="grass",
        detail="a patch of clover and daisies",
        tags={"meadow", "grass"},
    ),
    "riverbank": Setting(
        id="riverbank",
        place="the riverbank",
        path="the pebbly bank",
        snack_spot="a dry log by the reeds",
        terrain="pebbles",
        detail="the shining water",
        tags={"river", "water"},
    ),
    "pond_edge": Setting(
        id="pond_edge",
        place="the pond edge",
        path="the damp mud path",
        snack_spot="a mossy stump",
        terrain="mud",
        detail="the round green lily pads",
        tags={"pond", "mud"},
    ),
}

CARGOES = {
    "pumpkin": Cargo(
        id="pumpkin",
        label="the pumpkin",
        phrase="a round little pumpkin",
        weight=3,
        edible="pumpkin slices",
        mishap="the pumpkin rolled into the grass and came back with green smudges",
        rescue="wiped the pumpkin clean with cool leaves and a splash of water",
        ending="shared sweet pumpkin slices, each taking the same warm orange pieces",
        fragile=False,
        tags={"pumpkin", "sharing_food"},
    ),
    "berry_basket": Cargo(
        id="berry_basket",
        label="the berry basket",
        phrase="a full berry basket",
        weight=2,
        edible="berries",
        mishap="three shiny berries bounced out and dotted the ground with red juice",
        rescue="picked up the good berries and rinsed the basket at the water's edge",
        ending="ate the berries one by one, passing the biggest ones back and forth",
        fragile=True,
        tags={"berries", "sharing_food"},
    ),
    "seed_cake": Cargo(
        id="seed_cake",
        label="the seed cake",
        phrase="a seed cake wrapped in leaves",
        weight=2,
        edible="seed cake",
        mishap="the leaf wrapping slid loose, and the seed cake leaned crookedly against a stone",
        rescue="re-wrapped the seed cake neatly and brushed off the crumbs",
        fragile=True,
        tags={"seed_cake", "sharing_food"},
    ),
}

TOOLS = {
    "bark_sled": Tool(
        id="bark_sled",
        label="bark sled",
        phrase="a smooth bark sled",
        capacity=3,
        terrains={"grass", "mud", "pebbles"},
        teamwork_text="The load stayed level, and the bark sled slid along without tipping.",
        tags={"sled", "teamwork_tool"},
    ),
    "vine_sling": Tool(
        id="vine_sling",
        label="vine sling",
        phrase="a looped vine sling",
        capacity=2,
        terrains={"grass"},
        teamwork_text="The sling stopped swinging once they matched their steps and carried together.",
        tags={"sling", "teamwork_tool"},
    ),
    "reed_tray": Tool(
        id="reed_tray",
        label="reed tray",
        phrase="a woven reed tray",
        capacity=2,
        terrains={"mud", "pebbles"},
        teamwork_text="With one friend on each side, the reed tray stayed flat and steady.",
        tags={"tray", "teamwork_tool"},
    ),
}

GIRL_NAMES = ["Moss", "Daisy", "Tula", "Nell", "Poppy", "Wren"]
BOY_NAMES = ["Pip", "Otis", "Bram", "Tad", "Rufus", "Nico"]
SPECIES = ["otter", "beaver", "rabbit", "duck"]
TRAITS = ["eager", "bouncy", "patient", "cheerful"]

if __name__ == "__main__":
    main()
