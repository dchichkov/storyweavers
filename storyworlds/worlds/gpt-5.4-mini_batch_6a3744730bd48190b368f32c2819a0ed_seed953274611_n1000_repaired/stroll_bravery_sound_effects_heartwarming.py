#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/stroll_bravery_sound_effects_heartwarming.py
===========================================================================

A standalone story world for a heartwarming little tale about a brave child,
a gentle stroll, and a few comforting sound effects.

Premise
-------
A child feels nervous about going on a short evening stroll, because the path is
dark and full of unfamiliar sounds. A kind helper suggests a safe way forward:
listen for the sounds, take small brave steps, and use a simple sound effect
game to make the walk feel friendly. The child grows braver, helps someone, and
finishes the stroll feeling warm, proud, and calm.

This script follows the Storyweavers contract:
- typed entities with physical meters and emotional memes
- world-state-driven narration
- three Q&A sets grounded in simulated state
- inline ASP rules plus a Python gate
- --verify smoke tests normal generation and checks ASP parity

Run
---
    python storyworlds/worlds/gpt-5.4-mini/stroll_bravery_sound_effects_heartwarming.py
    python storyworlds/worlds/gpt-5.4-mini/stroll_bravery_sound_effects_heartwarming.py --qa
    python storyworlds/worlds/gpt-5.4-mini/stroll_bravery_sound_effects_heartwarming.py --all
    python storyworlds/worlds/gpt-5.4-mini/stroll_bravery_sound_effects_heartwarming.py --verify
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
BRAVERY_START = 0.0
FEAR_START = 1.0


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
    detail: str
    soundscape: str
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
class Companion:
    id: str
    label: str
    role: str
    help_line: str
    sound: str
    reassurance: str
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
class Challenge:
    id: str
    worry: str
    worry_line: str
    brave_step: str
    sound_game: str
    finish_image: str
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
class StoryParams:
    setting: str
    companion: str
    challenge: str
    child_name: str
    child_gender: str
    helper_name: str
    helper_gender: str
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


def _r_brave(world: World) -> list[str]:
    out: list[str] = []
    child = world.entities.get("child")
    helper = world.entities.get("helper")
    if not child or not helper:
        return out
    if child.memes["bravery"] < THRESHOLD:
        return out
    sig = ("brave",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["fear"] = 0.0
    helper.memes["pride"] += 1
    out.append("__brave__")
    return out


def _r_sound_comfort(world: World) -> list[str]:
    out: list[str] = []
    child = world.entities.get("child")
    if not child:
        return out
    if child.memes["bravery"] < THRESHOLD:
        return out
    sig = ("sound",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["calm"] += 1
    out.append("__sound__")
    return out


CAUSAL_RULES = [Rule("brave", "social", _r_brave), Rule("sound", "social", _r_sound_comfort)]


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


def setting_by_id(sid: str) -> Setting:
    if sid not in SETTINGS:
        raise StoryError(f"(No story: unknown setting '{sid}'.)")
    return SETTINGS[sid]


def companion_by_id(cid: str) -> Companion:
    if cid not in COMPANIONS:
        raise StoryError(f"(No story: unknown companion '{cid}'.)")
    return COMPANIONS[cid]


def challenge_by_id(cid: str) -> Challenge:
    if cid not in CHALLENGES:
        raise StoryError(f"(No story: unknown challenge '{cid}'.)")
    return CHALLENGES[cid]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid, s in SETTINGS.items():
        for cid, c in COMPANIONS.items():
            for hid, h in CHALLENGES.items():
                if "stroll" in h.tags and {"kind", "warm"}.intersection(s.tags | c.tags | h.tags):
                    combos.append((sid, cid, hid))
    return combos


def _choose_name(rng: random.Random, gender: str) -> str:
    return rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.companion is None or c[1] == args.companion)
              and (args.challenge is None or c[2] == args.challenge)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, companion, challenge = rng.choice(sorted(combos))
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    helper_gender = args.helper_gender or rng.choice(["girl", "boy"])
    return StoryParams(
        setting=setting,
        companion=companion,
        challenge=challenge,
        child_name=args.child_name or _choose_name(rng, child_gender),
        child_gender=child_gender,
        helper_name=args.helper_name or _choose_name(rng, helper_gender),
        helper_gender=helper_gender,
    )


def predict(world: World, challenge: Challenge) -> dict:
    sim = world.copy()
    child = sim.get("child")
    child.memes["bravery"] += 1.0
    child.meters["step"] += 1.0
    return {
        "brave": child.memes["bravery"] >= THRESHOLD,
        "calm": child.memes["calm"] >= THRESHOLD,
        "steps": child.meters["step"],
    }


def tell(setting: Setting, companion: Companion, challenge: Challenge,
         child_name: str, child_gender: str,
         helper_name: str, helper_gender: str) -> World:
    world = World()
    child = world.add(Entity(id="child", kind="character", type=child_gender, label=child_name, role="child"))
    helper = world.add(Entity(id="helper", kind="character", type=helper_gender, label=helper_name, role="helper"))
    place = world.add(Entity(id="place", type="place", label=setting.place))
    path = world.add(Entity(id="path", type="path", label=setting.path))
    child.memes["bravery"] = BRAVERY_START
    child.memes["fear"] = FEAR_START
    helper.memes["warmth"] = 1.0

    world.say(
        f"At {setting.place}, {child.label} and {helper.label} were ready for a little stroll. "
        f"The path was {setting.detail}, and the whole place had a {setting.soundscape}."
    )
    world.say(
        f"{child.label} felt a tiny wobble of worry. The dark path and every unfamiliar sound made "
        f"{child.pronoun().capitalize()} stay close to {helper.label}."
    )

    world.para()
    world.say(
        f"{helper.label} smiled and said, '{companion.help_line}.' "
        f"{helper.label} even made a soft sound effect: {companion.sound}"
    )
    world.say(
        f"That made {child.label} look up. {child.label} took a small brave breath and tried the next step."
    )

    pred = predict(world, challenge)
    world.facts["predicted"] = pred

    world.para()
    child.memes["bravery"] += 1.0
    child.meters["step"] += 1.0
    child.meters["step"] += 1.0
    child.meters["heart"] += 1.0
    child.memes["joy"] += 1.0
    world.say(
        f"{child.label} listened to the sounds of the walk and answered with {challenge.sound_game}. "
        f"Step by step, the stroll felt less scary and more like an adventure."
    )
    propagate(world, narrate=False)
    world.say(
        f"{child.label} kept going with {helper.label}, repeating {challenge.sound_game} again whenever a shadow "
        f"looked too big."
    )

    world.para()
    child.meters["step"] += 1.0
    child.memes["bravery"] += 1.0
    child.memes["fear"] = 0.0
    child.memes["calm"] += 1.0
    helper.memes["pride"] += 1.0
    world.say(
        f"At the end of the stroll, {challenge.finish_image}. {child.label} stood a little taller and smiled at "
        f"{helper.label}, warm and proud."
    )
    world.say(
        f"{companion.reassurance} {child.label} had been brave, and the walk home felt bright and gentle."
    )

    world.facts.update(
        setting=setting, companion=companion, challenge=challenge,
        child=child, helper=helper, place=place, path=path,
        outcome="warm", brave=child.memes["bravery"] >= THRESHOLD,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    challenge = f["challenge"]
    child = f["child"]
    return [
        f'Write a heartwarming story for a small child that includes the word "stroll" and a few cheerful sound effects.',
        f"Tell a gentle story where {child.label} is nervous about a stroll, gets brave step by step, and uses sound effects to feel safe.",
        f'Write a warm story about courage, a night stroll, and the sound effect "{challenge.sound_game}" as a comfort game.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    challenge = f["challenge"]
    pred = f["predicted"]
    return [
        QAItem(
            question=f"What was {child.label} doing?",
            answer=f"{child.label} was taking a stroll with {helper.label}. It started out a little scary, but the walk turned into something kind and brave."
        ),
        QAItem(
            question=f"Why did {child.label} feel nervous at first?",
            answer=f"The path felt dark and the sounds were unfamiliar, so {child.label} stayed close to {helper.label}. That worry was why the little sound game helped so much."
        ),
        QAItem(
            question=f"How did the sound effects help?",
            answer=f"{helper.label} used a soft sound effect and then {challenge.sound_game} made the walk feel friendly. Because {child.label} could listen and answer with playful sounds, the fear eased and bravery grew."
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended warmly, with {child.label} standing a little taller and smiling after the stroll. The final image shows {child.label} feeling proud, calm, and safe."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    setting = f["setting"]
    challenge = f["challenge"]
    return [
        QAItem(
            question="What is a stroll?",
            answer="A stroll is a slow, relaxed walk. People often stroll when they want to enjoy the place around them."
        ),
        QAItem(
            question="What does bravery mean?",
            answer="Bravery means doing something scary or new even when your heart feels shaky. It does not mean feeling no fear at all; it means taking a careful step anyway."
        ),
        QAItem(
            question="Why can sound effects be comforting?",
            answer="Sound effects can make a moment feel playful and friendly. When the sounds are soft and familiar, they can help a worried child feel calmer."
        ),
        QAItem(
            question="Why was the setting important?",
            answer=f"The setting gave the stroll its mood, because {setting.place} had the sounds and details that shaped how the walk felt. That made the little brave ending feel earned."
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
        if e.label:
            bits.append(f"label={e.label}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


SETTINGS = {
    "lantern_lane": Setting(
        id="lantern_lane",
        place="Lantern Lane",
        path="the little brick path",
        detail="lined with porch lights and soft leaves",
        soundscape="rustly trees and distant wind chimes",
        tags={"warm", "kind", "stroll"},
    ),
    "garden_path": Setting(
        id="garden_path",
        place="the garden path",
        path="the stepping-stone path",
        detail="bright with flowers and tiny dewdrops",
        soundscape="a hush of crickets and sleepy birds",
        tags={"warm", "kind", "stroll"},
    ),
    "harbor_walk": Setting(
        id="harbor_walk",
        place="the harbor walk",
        path="the boardwalk",
        detail="glowing under little lamps by the water",
        soundscape="gentle waves and creaking ropes",
        tags={"warm", "kind", "stroll"},
    ),
}

COMPANIONS = {
    "hum": Companion(
        id="hum",
        label="a humming neighbor",
        role="helper",
        help_line="We can let our steps make the rhythm.",
        sound="hum-hum, tap-tap",
        reassurance="The soft humming kept the dark from feeling lonely.",
        tags={"sound", "warm", "kind"},
    ),
    "clap": Companion(
        id="clap",
        label="a cheerful grandparent",
        role="helper",
        help_line="Let's clap our brave little steps.",
        sound="clap, clap, clap",
        reassurance="The clapping made the walk feel like a small celebration.",
        tags={"sound", "warm", "kind"},
    ),
    "whisper": Companion(
        id="whisper",
        label="a kind older cousin",
        role="helper",
        help_line="We can whisper the path into a friendly shape.",
        sound="shh-shh, pitter-pat",
        reassurance="The whispering turned the stroll into a cozy secret.",
        tags={"sound", "warm", "kind"},
    ),
}

CHALLENGES = {
    "night_steps": Challenge(
        id="night_steps",
        worry="the dark path and the unfamiliar shadows",
        worry_line="The dark path felt big at first",
        brave_step="take one small step at a time",
        sound_game="tap-tap, step-step",
        finish_image="the porch light shone on two happy faces",
        tags={"stroll", "bravery", "sound", "heartwarming"},
    ),
    "quiet_river": Challenge(
        id="quiet_river",
        worry="the water whispering beside the path",
        worry_line="The river made every sound seem bigger",
        brave_step="keep walking with steady feet",
        sound_game="swish-swish, pat-pat",
        finish_image="the water looked silver and calm beside the path",
        tags={"stroll", "bravery", "sound", "heartwarming"},
    ),
    "park_breeze": Challenge(
        id="park_breeze",
        worry="the wind shaking the trees",
        worry_line="The leaves fluttered like little surprises",
        brave_step="hold on and move forward",
        sound_game="whoo-whoo, step-step",
        finish_image="the park bench waited under a soft moon",
        tags={"stroll", "bravery", "sound", "heartwarming"},
    ),
}

GIRL_NAMES = ["Mia", "Lena", "Ruby", "Nora", "Ivy", "Ada", "June", "Wren"]
BOY_NAMES = ["Theo", "Owen", "Finn", "Eli", "Noah", "Milo", "Asa", "Luca"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A heartwarming story world about a stroll, bravery, and sound effects.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--companion", choices=COMPANIONS)
    ap.add_argument("--challenge", choices=CHALLENGES)
    ap.add_argument("--child-name")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--helper-name")
    ap.add_argument("--helper-gender", choices=["girl", "boy"])
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


ASP_RULES = r"""
brave(C) :- child(C), bravery(C, B), threshold(T), B >= T.
comforted(C) :- child(C), brave(C), sound_help(C).
outcome(warm) :- brave(child), comforted(child).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for cid in COMPANIONS:
        lines.append(asp.fact("companion", cid))
        lines.append(asp.fact("sound_help", "child"))
    for hid in CHALLENGES:
        lines.append(asp.fact("challenge", hid))
    lines.append(asp.fact("child", "child"))
    lines.append(asp.fact("bravery", "child", 1))
    lines.append(asp.fact("threshold", 1))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_outcome() -> str:
    import asp
    model = asp.one_model(asp_program("", "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    import asp
    rc = 0
    model = asp.one_model(asp_program("", "#show brave/1. #show comforted/1. #show outcome/1."))
    if asp_outcome() != "warm":
        print("MISMATCH: ASP outcome should be warm.")
        rc = 1
    if not asp.atoms(model, "brave"):
        print("MISMATCH: ASP did not infer bravery.")
        rc = 1
    sample = generate(resolve_params(build_parser().parse_args([]), random.Random(0)))
    if not sample.story or "stroll" not in sample.story:
        print("MISMATCH: normal generation failed.")
        rc = 1
    print("OK: ASP and normal generation smoke test passed.")
    return rc


def resolve_params_from_args(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return resolve_params(args, rng)


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError(f"(No story: unknown setting '{params.setting}'.)")
    if params.companion not in COMPANIONS:
        raise StoryError(f"(No story: unknown companion '{params.companion}'.)")
    if params.challenge not in CHALLENGES:
        raise StoryError(f"(No story: unknown challenge '{params.challenge}'.)")
    world = tell(
        SETTINGS[params.setting],
        COMPANIONS[params.companion],
        CHALLENGES[params.challenge],
        params.child_name,
        params.child_gender,
        params.helper_name,
        params.helper_gender,
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
        print(asp_program("", "#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        curated = [
            StoryParams(setting="lantern_lane", companion="hum", challenge="night_steps", child_name="Mia", child_gender="girl", helper_name="Mrs. Bell", helper_gender="girl"),
            StoryParams(setting="garden_path", companion="clap", challenge="quiet_river", child_name="Theo", child_gender="boy", helper_name="Grandpa", helper_gender="boy"),
            StoryParams(setting="harbor_walk", companion="whisper", challenge="park_breeze", child_name="Nora", child_gender="girl", helper_name="Ava", helper_gender="girl"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen = set()
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
            header = f"### {p.child_name}: {p.setting} / {p.companion} / {p.challenge}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
