#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/purr_smirk_repetition_magic_pirate_tale.py
==========================================================================

A small standalone storyworld for a pirate tale with magic, repetition, and the
seed words "purr" and "smirk".

Premise:
A child pirate hears a tiny magical purr coming from a sealed chest, repeats a
charm, makes the chest answer, and discovers a safe treasure that changes the
mood of the deck.

The world is built from typed entities with physical meters and emotional memes.
The story is driven by simulated state, not by swapping nouns into a fixed text.
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
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "queen", "captainess"}
        male = {"boy", "father", "man", "captain"}
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
class Theme:
    id: str
    scene: str
    rig: str
    ship_name: str
    charm_name: str
    treasure_name: str
    ending: str
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
class Charm:
    id: str
    phrase: str
    word: str
    label: str
    magic: bool = True
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

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Container:
    id: str
    label: str
    the: str
    on: str
    purrs: bool = False
    magic_open: bool = False
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
class Response:
    id: str
    sense: int
    power: int
    text: str
    fail: str
    qa_text: str
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


def _r_purr(world: World) -> list[str]:
    out: list[str] = []
    chest = world.entities.get("chest")
    if not chest or chest.meters["touched"] < THRESHOLD:
        return out
    sig = ("purr",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    chest.meters["rumble"] += 1
    world.get("deck").memes["wonder"] += 1
    out.append("__purr__")
    return out


def _r_repeat(world: World) -> list[str]:
    out: list[str] = []
    child = world.entities.get("child")
    charm = world.entities.get("charm")
    if not child or not charm or child.meters["chanted"] < THRESHOLD:
        return out
    sig = ("repeat",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    charm.meters["echo"] += 1
    child.memes["bold"] += 1
    out.append("__repeat__")
    return out


def _r_magic_open(world: World) -> list[str]:
    out: list[str] = []
    chest = world.entities.get("chest")
    charm = world.entities.get("charm")
    if not chest or not charm:
        return out
    if chest.meters["rumble"] < THRESHOLD or charm.meters["echo"] < THRESHOLD:
        return out
    sig = ("magic_open",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    chest.meters["open"] += 1
    chest.meters["glow"] += 1
    out.append("__open__")
    return out


CAUSAL_RULES = [Rule("purr", _r_purr), Rule("repeat", _r_repeat), Rule("magic_open", _r_magic_open)]


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


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for theme in THEMES:
        for cid, charm in CHARMS.items():
            for oid, container in CONTAINERS.items():
                if charm.magic and container.magic_open:
                    combos.append((theme, cid, oid))
    return combos


def can_open(charm: Charm, container: Container) -> bool:
    return charm.magic and container.magic_open


def predict(world: World) -> dict:
    sim = world.copy()
    sim.get("child").meters["chanted"] += 1
    propagate(sim, narrate=False)
    return {"opened": sim.get("chest").meters["open"] >= THRESHOLD, "glow": sim.get("chest").meters["glow"]}


def tell(theme: Theme, charm: Charm, container: Container, response: Response,
         child_name: str, child_type: str, helper_name: str, helper_type: str,
         parent_type: str, delay: int = 0) -> World:
    world = World()
    child = world.add(Entity(id="child", kind="character", type=child_type, label=child_name, role="pirate"))
    helper = world.add(Entity(id="helper", kind="character", type=helper_type, label=helper_name, role="mate"))
    parent = world.add(Entity(id="parent", kind="character", type=parent_type, label="the captain"))
    deck = world.add(Entity(id="deck", type="place", label="the deck"))
    chest = world.add(Entity(id="chest", type="thing", label=container.label, attrs={"on": container.on}))
    charm_ent = world.add(Entity(id="charm", type="thing", label=charm.label))
    world.facts["theme"] = theme
    world.facts["delay"] = delay

    child.memes["curious"] += 1
    helper.memes["careful"] += 1

    world.say(f"On {theme.scene}, {theme.rig}")
    world.say(f"{child_name} was a little pirate who liked {theme.ship_name} games.")
    world.say(f"{helper_name} was there too, and the two of them were hunting for {theme.treasure_name}.")

    world.para()
    world.say(f"But {container.the} sat shut {container.on}, and the dark spot made {helper_name} frown.")
    world.say(f'"We need a way to wake it," {child_name} said, with a smirk.')

    world.para()
    child.meters["touched"] += 1
    child.meters["chanted"] += 1
    world.say(f'{child_name} whispered, "{charm.phrase}."')
    world.say(f'Then {child_name} said it again: "{charm.phrase}."')
    world.say(f'And once more: "{charm.phrase}."')
    propagate(world)

    if chest.meters["open"] >= THRESHOLD:
        world.para()
        world.say(f"The chest gave a soft purr and opened with a gold-and-blue glow.")
        world.say(f"Inside was {theme.treasure_name}, not a sharp blade or a mean trick, but a warm map and a tiny lantern.")
        response_body = response.text
        world.say(f"{parent.label_word.capitalize()} came to see the glow and {response_body}.")
        world.say(f'{parent.label_word.capitalize()} smiled because the magic had stayed gentle.')
        world.para()
        world.say(f'The children copied the old words one last time, " {charm.word}, {charm.word}," and laughed at the little echo.')
        world.say(f"By the end, the deck felt bright, and the chest stayed open with a happy purr.")
    else:
        world.para()
        world.say(f"The chest stayed shut, and the deck only kept its quiet dark.")
        world.say(f"{helper_name} stopped the chant, and the pirate game ended in a grumble.")

    world.facts.update(child=child, helper=helper, parent=parent, deck=deck, chest=chest, charm=charm_ent,
                       outcome="opened" if chest.meters["open"] >= THRESHOLD else "closed",
                       response=response, container=container, charm_cfg=charm)
    return world


THEMES = {
    "decklight": Theme(
        id="decklight",
        scene="the moonlit deck of a little pirate ship",
        rig="the sail snapped softly, a rope ladder rocked by the mast, and a lantern drew a bright circle on the boards.",
        ship_name="deck",
        charm_name="purr-charm",
        treasure_name="a pearl compass",
        ending="a bright, gentle ending",
    ),
    "harbor": Theme(
        id="harbor",
        scene="the harbor dock where gulls circled the rigging",
        rig="the ropes creaked, the waves tapped the pilings, and a painted crate waited by the mast.",
        ship_name="dock",
        charm_name="purr-charm",
        treasure_name="a moon-shell key",
        ending="a bright, gentle ending",
    ),
}

CHARMS = {
    "purrspell": Charm(
        id="purrspell",
        phrase="purr, purr, open up",
        word="purr",
        label="a purr-spell",
    ),
    "smirkspell": Charm(
        id="smirkspell",
        phrase="smirk and sparkle",
        word="smirk",
        label="a smirk-spell",
    ),
}

CONTAINERS = {
    "chest": Container(
        id="chest",
        label="the little chest",
        the="The little chest",
        on="under the mast",
        purrs=True,
        magic_open=True,
    ),
    "crate": Container(
        id="crate",
        label="the painted crate",
        the="The painted crate",
        on="by the mast",
        purrs=True,
        magic_open=True,
    ),
    "barrel": Container(
        id="barrel",
        label="the barrel",
        the="The barrel",
        on="near the rail",
        purrs=False,
        magic_open=False,
    ),
}

RESPONSES = {
    "lamp": Response(
        id="lamp",
        sense=3,
        power=3,
        text="lifted the lantern higher and laughed that the magic was safe enough to share",
        fail="lifted the lantern, but the glow was too small to matter",
        qa_text="lifted the lantern higher and smiled at the safe glow",
    ),
    "cover": Response(
        id="cover",
        sense=2,
        power=2,
        text="covered the chest with a cloth so the magic could rest without flashing too hard",
        fail="covered the chest with a cloth, but the spell stayed sleepy",
        qa_text="covered the chest with a cloth and let the magic rest",
    ),
    "water_bucket": Response(
        id="water_bucket",
        sense=1,
        power=1,
        text="splashed water over the chest, and the magic sputtered into a mess",
        fail="splashed water over the chest, but only made a mess",
        qa_text="splashed water over the chest",
    ),
}

SENSE_MIN = 2

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Nora"]
BOY_NAMES = ["Tom", "Ben", "Max", "Eli", "Finn"]
TRAITS = ["brave", "curious", "cheerful", "clever"]


@dataclass
class StoryParams:
    theme: str
    charm: str
    container: str
    response: str
    child_name: str
    child_type: str
    helper_name: str
    helper_type: str
    parent_type: str
    trait: str
    delay: int = 0
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
        theme="decklight",
        charm="purrspell",
        container="chest",
        response="lamp",
        child_name="Tom",
        child_type="boy",
        helper_name="Lily",
        helper_type="girl",
        parent_type="captain",
        trait="curious",
        delay=0,
    ),
    StoryParams(
        theme="harbor",
        charm="smirkspell",
        container="crate",
        response="cover",
        child_name="Mia",
        child_type="girl",
        helper_name="Ben",
        helper_type="boy",
        parent_type="captain",
        trait="cheerful",
        delay=0,
    ),
]


KNOWLEDGE = {
    "purr": [("What does purr mean?",
              "A purr is a soft, rumbling sound, like a cat making a cozy little hum.")],
    "smirk": [("What is a smirk?",
               "A smirk is a small smile that can look a little sneaky or proud.")],
    "magic": [("What is magic in a story?",
               "Magic is a special pretend power that can make surprising things happen.")],
    "repetition": [("What is repetition?",
                     "Repetition means saying or doing something again and again.")],
    "pirate": [("What is a pirate?",
                  "A pirate is a ship traveler from story books who sails for treasure.")],
    "lantern": [("What does a lantern do?",
                 "A lantern gives light, so people can see in the dark.")],
}

KNOWLEDGE_ORDER = ["pirate", "purr", "smirk", "repetition", "magic", "lantern"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    theme: Theme = f["theme"]
    charm: Charm = f["charm_cfg"]
    return [
        f'Write a pirate tale for a 3-to-5-year-old that uses the words "{charm.word}" and "smirk".',
        f"Tell a story where a little pirate repeats the same magic words three times and a chest answers back.",
        f"Write a gentle treasure story on {theme.scene} with repetition and magic, ending in a safe glow.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child: Entity = f["child"]
    helper: Entity = f["helper"]
    parent: Entity = f["parent"]
    chest: Entity = f["chest"]
    charm_cfg: Charm = f["charm_cfg"]
    resp: Response = f["response"]
    qa = [
        ("Who is the story about?",
         f"It is about {child.id} and {helper.id}, two little pirates on the deck. {parent.label_word.capitalize()} joins them after the magic begins."),
        ("What word did the child repeat?",
         f"{child.id} repeated \"{charm_cfg.phrase}\" again and again. That repetition mattered because the magic needed the words to echo before the chest would answer."),
        ("What did the chest do?",
         f"{chest.label_word.capitalize()} gave a soft purr and opened with a glow. The repeated charm woke the magic safely instead of making trouble."),
        ("How did the grown-up respond?",
         f"{parent.label_word.capitalize()} came to see the glow and {resp.qa_text}. It was a calm response because the magic stayed gentle."),
    ]
    if f["outcome"] == "opened":
        qa.append(("How did the story end?",
                   f"It ended with the chest open, the deck bright, and a happy purr in the air. The children kept the treasure and the magic stayed kind."))
    else:
        qa.append(("How did the story end?",
                   f"The chest stayed shut and the deck stayed dark. The magic did not wake up, so the children had to try a different way."))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = set()
    tags.add("pirate")
    tags.add(world.facts["charm_cfg"].word)
    tags.add("magic")
    tags.add("repetition")
    out: list[tuple[str, str]] = []
    for key in KNOWLEDGE_ORDER:
        if key in tags:
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
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
purr_fire :- touched(chest), not blocked.
repeat_magic :- chanted(child), not echoed.
open_chest :- purr_fire, repeat_magic.
outcome(opened) :- open_chest.
outcome(closed) :- not open_chest.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for tid in THEMES:
        lines.append(asp.fact("theme", tid))
    for cid, c in CHARMS.items():
        lines.append(asp.fact("charm", cid))
        if c.magic:
            lines.append(asp.fact("magic", cid))
    for oid, o in CONTAINERS.items():
        lines.append(asp.fact("container", oid))
        if o.magic_open:
            lines.append(asp.fact("magic_open", oid))
        if o.purrs:
            lines.append(asp.fact("purrs", oid))
    for rid, r in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, r.sense))
        lines.append(asp.fact("power", rid, r.power))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program(show="#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp
    scenario = "\n".join([
        asp.fact("touched", "chest"),
        asp.fact("chanted", "child"),
        asp.fact("blocked") if params.response == "water_bucket" else "",
    ])
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "closed"


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        rc = 1
        print("MISMATCH in gate.")
    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise RuntimeError("empty story")
        print("OK: generate() smoke test produced a story.")
    except Exception as exc:
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Pirate tale storyworld with purr, smirk, repetition, and magic.")
    ap.add_argument("--theme", choices=THEMES)
    ap.add_argument("--charm", choices=CHARMS)
    ap.add_argument("--container", choices=CONTAINERS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--child-name")
    ap.add_argument("--child-type", choices=["girl", "boy"])
    ap.add_argument("--helper-name")
    ap.add_argument("--helper-type", choices=["girl", "boy"])
    ap.add_argument("--parent-type", choices=["captain", "mother", "father"])
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("--delay", type=int, choices=[0, 1, 2])
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
    combos = [c for c in valid_combos()
              if (args.theme is None or c[0] == args.theme)
              and (args.charm is None or c[1] == args.charm)
              and (args.container is None or c[2] == args.container)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    theme, charm, container = rng.choice(sorted(combos))
    child_type = args.child_type or rng.choice(["girl", "boy"])
    helper_type = args.helper_type or rng.choice(["girl", "boy"])
    child_name = args.child_name or rng.choice(GIRL_NAMES if child_type == "girl" else BOY_NAMES)
    helper_pool = [n for n in (GIRL_NAMES if helper_type == "girl" else BOY_NAMES) if n != child_name]
    helper_name = args.helper_name or rng.choice(helper_pool or (GIRL_NAMES if helper_type == "girl" else BOY_NAMES))
    return StoryParams(
        theme=theme,
        charm=charm,
        container=container,
        response=args.response or rng.choice(sorted(s.id for s in sensible_responses())),
        child_name=child_name,
        child_type=child_type,
        helper_name=helper_name,
        helper_type=helper_type,
        parent_type=args.parent_type or "captain",
        trait=args.trait or rng.choice(TRAITS),
        delay=args.delay if args.delay is not None else 0,
    )


def generate(params: StoryParams) -> StorySample:
    if params.theme not in THEMES or params.charm not in CHARMS or params.container not in CONTAINERS or params.response not in RESPONSES:
        raise StoryError("invalid parameters")
    if RESPONSES[params.response].sense < SENSE_MIN:
        raise StoryError("response is too weak for a child story")
    theme = THEMES[params.theme]
    charm = CHARMS[params.charm]
    container = CONTAINERS[params.container]
    if not can_open(charm, container):
        raise StoryError("that charm cannot open that container")
    response = RESPONSES[params.response]
    world = tell(theme, charm, container, response, params.child_name, params.child_type,
                 params.helper_name, params.helper_type, params.parent_type, params.delay)
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
        print(asp_program(show="#show valid/3.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos:")
        for row in asp_valid_combos():
            print(" ", row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            i += 1
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
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
        if len(samples) > 1:
            print(f"### variant {i + 1}")
        emit(sample, trace=args.trace, qa=args.qa)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
