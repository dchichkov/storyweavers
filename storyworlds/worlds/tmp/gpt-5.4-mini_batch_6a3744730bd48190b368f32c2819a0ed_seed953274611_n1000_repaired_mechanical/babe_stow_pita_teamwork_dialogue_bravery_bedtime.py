#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/babe_stow_pita_teamwork_dialogue_bravery_bedtime.py
===================================================================================

A tiny bedtime storyworld about a babe, a stowaway picnic, and a pita adventure.

Premise
-------
A small child wants to stow a bedtime snack and a toy into a little basket before sleep.
The child feels shy about asking for help, but a kind helper speaks gently, the child
finds bravery, and together they pack everything neatly for a cozy bedtime ending.

This script follows the Storyweavers storyworld contract:
- typed entities with meters and memes
- state-driven causal changes
- a reasonableness gate and inline ASP twin
- prompts, story QA, and world-knowledge QA
- CLI support for default runs, -n, --all, --seed, --trace, --qa, --json,
  --asp, --verify, and --show-asp
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
BRAVERY_MIN = 2
SOFT_WORDS = {"gentle", "kind", "quiet", "cozy", "warm"}


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "aunt"}
        male = {"boy", "father", "dad", "man", "uncle"}
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

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Setting:
    id: str
    place: str
    mood: str
    bedtime_image: str
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


@dataclass
class Snack:
    id: str
    label: str
    phrase: str
    wraps: str
    yummy: str
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
class Container:
    id: str
    label: str
    phrase: str
    can_stow: bool
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
class Helper:
    id: str
    label: str
    phrase: str
    brave_word: str
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
class Response:
    id: str
    sense: int
    power: int
    text: str
    fail: str
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
        clone.facts = dict(self.facts)
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


def _r_stow(world: World) -> list[str]:
    out: list[str] = []
    kid = world.get("babe")
    basket = world.get("basket")
    if kid.meters["packed"] < THRESHOLD:
        return out
    if basket.meters["stowed"] >= THRESHOLD:
        return out
    sig = ("stow",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    basket.meters["stowed"] += 1
    out.append("__stowed__")
    return out


def _r_comfort(world: World) -> list[str]:
    out: list[str] = []
    kid = world.get("babe")
    helper = world.get("helper")
    if kid.memes["bravery"] < BRAVERY_MIN:
        return out
    sig = ("comfort",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    kid.memes["calm"] += 1
    helper.memes["pride"] += 1
    out.append("__calm__")
    return out


CAUSAL_RULES = [
    Rule("stow", "physical", _r_stow),
    Rule("comfort", "social", _r_comfort),
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


def valid_combo(setting: Setting, snack: Snack, container: Container, helper: Helper) -> bool:
    return setting.id in {"bedtime"} and container.can_stow and "sleep" in helper.tags and snack.id in {"pita"}


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for sid in SETTINGS:
        for nid in SNACKS:
            for cid in CONTAINERS:
                for hid in HELPERS:
                    if valid_combo(SETTINGS[sid], SNACKS[nid], CONTAINERS[cid], HELPERS[hid]):
                        combos.append((sid, nid, cid, hid))
    return combos


def reasonableness_check(snack: Snack, container: Container) -> None:
    if snack.id != "pita":
        raise StoryError("This world is built around pita as the bedtime snack.")
    if not container.can_stow:
        raise StoryError(f"(No story: {container.label} cannot stow anything neatly.)")


def predict(world: World) -> dict:
    sim = world.copy()
    sim.get("babe").meters["packed"] += 1
    propagate(sim, narrate=False)
    return {"stowed": sim.get("basket").meters["stowed"] >= THRESHOLD}


def tell(setting: Setting, snack: Snack, container: Container, helper: Helper,
         babe_name: str = "Babe", helper_name: str = "Mina",
         parent_name: str = "Mom", parent_type: str = "mother") -> World:
    world = World()
    babe = world.add(Entity(id="babe", kind="character", type="girl", label=babe_name, role="child"))
    h = world.add(Entity(id="helper", kind="character", type="girl", label=helper_name, role="helper",
                         traits=["kind", "gentle", "brave"], attrs={"brave_word": helper.brave_word}))
    parent = world.add(Entity(id="parent", kind="character", type=parent_type, label=parent_name, role="parent"))
    basket = world.add(Entity(id="basket", type="container", label=container.label))
    pita = world.add(Entity(id="pita", type="snack", label=snack.label))

    babe.memes["shy"] = 1
    babe.memes["bravery"] = 0
    h.memes["kindness"] = 1

    world.say(
        f"At bedtime in {setting.place}, {babe.label} looked at {snack.phrase} and the little basket. "
        f"The room felt {setting.mood}, and the moon made a sleepy silver patch on the floor."
    )
    world.say(
        f'"Can we stow the {snack.label} with my blanket and toy?" {babe.label} asked softly.'
    )
    world.say(
        f'{h.label} smiled. "{h.brave_word.capitalize()} little {babe.label}, yes. We can do it together."'
    )

    world.para()
    babe.meters["packed"] += 1
    babe.memes["bravery"] += 1
    world.say(
        f"{babe.label} took a breath and picked up the {snack.label}. "
        f"{babe.label} and {h.label} worked side by side, folding, placing, and tucking things in."
    )
    if predict(world)["stowed"]:
        propagate(world, narrate=False)

    world.para()
    world.say(
        f"The {snack.label} stowed neatly in the basket, and {babe.label}'s heart felt less wobbly."
    )
    world.say(
        f"{parent.label_word.capitalize()} came in, saw the tidy basket, and laughed a sleepy little laugh."
    )
    world.say(
        f'"That was brave," {parent.label_word} said. "You asked, you listened, and you helped."'
    )
    world.say(
        f"Then {babe.label} snuggled down as the room stayed {setting.mood}, with the basket by the bed and the pita ready for morning."
    )

    world.facts.update(
        setting=setting,
        snack=snack,
        container=container,
        helper=helper,
        babe=babe,
        parent=parent,
        outcome="stowed",
    )
    return world


SETTINGS = {
    "bedtime": Setting(id="bedtime", place="a cozy bedroom", mood="soft and warm", bedtime_image="moonlight on the quilt"),
}

SNACKS = {
    "pita": Snack(id="pita", label="pita", phrase="a small pita pocket", wraps="wrapped in a napkin", yummy="gentle and warm", tags={"pita", "food"}),
}

CONTAINERS = {
    "basket": Container(id="basket", label="little basket", phrase="a little basket", can_stow=True, tags={"basket", "stow"}),
    "box": Container(id="box", label="cardboard box", phrase="a cardboard box", can_stow=True, tags={"box", "stow"}),
}

HELPERS = {
    "mina": Helper(id="mina", label="Mina", phrase="a kind helper", brave_word="brave", tags={"sleep", "help", "bravery"}),
    "nina": Helper(id="nina", label="Nina", phrase="a gentle helper", brave_word="brave", tags={"sleep", "help", "bravery"}),
}


@dataclass
class StoryParams:
    setting: str = "bedtime"
    snack: str = "pita"
    container: str = "basket"
    helper: str = "mina"
    babe_name: str = "Babe"
    helper_name: str = "Mina"
    parent_name: str = "Mom"
    parent_type: str = "mother"
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
    StoryParams(setting="bedtime", snack="pita", container="basket", helper="mina", babe_name="Babe", helper_name="Mina", parent_name="Mom", parent_type="mother"),
    StoryParams(setting="bedtime", snack="pita", container="box", helper="nina", babe_name="Pia", helper_name="Nina", parent_name="Dad", parent_type="father"),
]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        'Write a bedtime story that includes the words "babe", "stow", and "pita".',
        f"Tell a gentle bedtime story where {f['babe'].label} learns to stow a pita with help from {f['helper'].label}.",
        "Write a cozy story about teamwork, dialogue, and bravery at bedtime.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    babe = f["babe"]
    helper = f["helper"]
    parent = f["parent"]
    return [
        QAItem(
            question="Who asked for help?",
            answer=f"{babe.label} asked for help stowing the pita, and {helper.label} answered kindly. That made the task feel less scary and more like teamwork."
        ),
        QAItem(
            question="What did they do together?",
            answer=f"They stowed the pita in the basket together and tucked the bedtime things in neatly. Because they worked side by side, the room stayed calm and ready for sleep."
        ),
        QAItem(
            question="Why was the ending happy?",
            answer=f"The pita was packed away safely, and the grown-up saw brave teamwork instead of worry. The child could rest with a tidy basket beside the bed."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does it mean to stow something?",
            answer="To stow something means to put it away neatly in a safe place. People do that when they want a room to feel tidy and calm."
        ),
        QAItem(
            question="What is teamwork?",
            answer="Teamwork is when two or more people help each other to do one job. Each person does a part, and the job feels easier."
        ),
        QAItem(
            question="What does bravery look like at bedtime?",
            answer="Bravery at bedtime can mean asking a question, speaking up, or trying a new task with help. It does not have to be loud to be strong."
        ),
    ]


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
        if e.role:
            bits.append(f"role={e.role}")
        if e.traits:
            bits.append(f"traits={e.traits}")
        lines.append(f"  {e.id:8} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


def explain_rejection(container: Container) -> str:
    return f"(No story: {container.label} cannot support a neat bedtime stow.)"


def explain_response(rid: str) -> str:
    r = RESPONSES[rid]
    allowed = ", ".join(sorted(x.id for x in RESPONSES.values() if x.sense >= BRAVERY_MIN))
    return f"(Refusing response '{rid}': sense={r.sense} is too low. Try {allowed}.)"


RESPONSES = {
    "gentle_basket": Response(
        id="gentle_basket",
        sense=3,
        power=3,
        text="lifted the lid, folded the blanket corner, and tucked everything in with a gentle smile",
        fail="tried to tuck things in, but the basket was too small and the pile toppled over",
        qa_text="lifted the lid and tucked everything in with a gentle smile",
        tags={"basket", "gentle", "bedtime"},
    ),
    "teamfold": Response(
        id="teamfold",
        sense=3,
        power=4,
        text="worked together, folded the napkin, and stowed the pita neatly beside the pillow",
        fail="worked together, but the sleepy pile still spilled out onto the floor",
        qa_text="worked together, folded the napkin, and stowed the pita neatly",
        tags={"teamwork", "bedtime"},
    ),
    "quiet_help": Response(
        id="quiet_help",
        sense=2,
        power=2,
        text="quietly made space, put the pita inside, and closed the basket softly",
        fail="closed the basket softly, but the pita did not fit well enough",
        qa_text="made space and put the pita inside",
        tags={"quiet", "bedtime"},
    ),
}


def valid_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= BRAVERY_MIN]


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for nid in SNACKS:
        lines.append(asp.fact("snack", nid))
    for cid, c in CONTAINERS.items():
        lines.append(asp.fact("container", cid))
        if c.can_stow:
            lines.append(asp.fact("can_stow", cid))
    for hid in HELPERS:
        lines.append(asp.fact("helper", hid))
        lines.append(asp.fact("brave", hid))
    for rid, r in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, r.sense))
        lines.append(asp.fact("power", rid, r.power))
    lines.append(asp.fact("bravery_min", BRAVERY_MIN))
    return "\n".join(lines)


ASP_RULES = r"""
valid(S,N,C,H) :- setting(S), snack(N), container(C), helper(H), can_stow(C), brave(H).
sensible(R) :- response(R), sense(R,S), bravery_min(M), S >= M.
"""


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp
    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(r for (r,) in asp.atoms(model, "sensible"))


def asp_verify() -> int:
    import asp
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        print("MISMATCH in valid_combos()")
        rc = 1
    if set(asp_sensible()) != {r.id for r in valid_responses()}:
        print("MISMATCH in sensible responses")
        rc = 1
    try:
        sample = generate(resolve_params(argparse.Namespace(setting=None, snack=None, container=None, helper=None, babe_name=None, helper_name=None, parent_name=None, parent_type=None, seed=None), random.Random(7)))
        if not sample.story.strip():
            raise RuntimeError("empty story")
    except Exception as exc:  # noqa: BLE001
        print(f"SMOKE TEST FAILED: {exc}")
        return 1
    print("OK: ASP and Python checks passed, and generate() produced a story.")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A bedtime storyworld about babe, stow, and pita.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--snack", choices=SNACKS)
    ap.add_argument("--container", choices=CONTAINERS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--babe-name")
    ap.add_argument("--helper-name")
    ap.add_argument("--parent-name")
    ap.add_argument("--parent-type", choices=["mother", "father"])
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.container and not CONTAINERS[args.container].can_stow:
        raise StoryError(explain_rejection(CONTAINERS[args.container]))
    if args.snack and args.snack not in SNACKS:
        raise StoryError("Unknown snack.")
    if args.helper and args.helper not in HELPERS:
        raise StoryError("Unknown helper.")
    combos = valid_combos()
    if args.setting:
        combos = [c for c in combos if c[0] == args.setting]
    if args.snack:
        combos = [c for c in combos if c[1] == args.snack]
    if args.container:
        combos = [c for c in combos if c[2] == args.container]
    if args.helper:
        combos = [c for c in combos if c[3] == args.helper]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, snack, container, helper = rng.choice(sorted(combos))
    return StoryParams(
        setting=setting,
        snack=snack,
        container=container,
        helper=helper,
        babe_name=args.babe_name or "Babe",
        helper_name=args.helper_name or "Mina",
        parent_name=args.parent_name or "Mom",
        parent_type=args.parent_type or "mother",
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS or params.snack not in SNACKS or params.container not in CONTAINERS or params.helper not in HELPERS:
        raise StoryError("Invalid StoryParams.")
    world = tell(
        SETTINGS[params.setting],
        SNACKS[params.snack],
        CONTAINERS[params.container],
        HELPERS[params.helper],
        babe_name=params.babe_name,
        helper_name=params.helper_name,
        parent_name=params.parent_name,
        parent_type=params.parent_type,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
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
        print(asp_program("", "#show valid/4.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible responses: {', '.join(asp_sensible())}")
        print(f"{len(asp_valid_combos())} valid combos.")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
