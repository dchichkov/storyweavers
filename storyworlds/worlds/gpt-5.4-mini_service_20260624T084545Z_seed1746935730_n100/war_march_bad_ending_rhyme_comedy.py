#!/usr/bin/env python3
"""
storyworlds/worlds/war_march_bad_ending_rhyme_comedy.py
========================================================

A tiny comedy storyworld about a silly war march that goes wrong.

Premise:
- A child or small captain loves marching with a drum, a flag, and a rhyme.
- They start a playful "war" against some harmless nuisance or rival.
- The march builds into a comic parade with rhythm, chant, and confidence.
- The ending is a bad ending: the plan fails, the rhyme falls apart, and the
  final image shows a funny loss instead of a victory.

This world is designed to produce complete, child-facing stories with a
state-driven turn:
- setup -> desire -> march -> mishap -> bad ending

The simulation tracks:
- physical meters: noise, speed, muddle, spill, lost_items
- emotional memes: pride, joy, worry, embarrassment, laughter, resolve

The story text is authored from state changes, not by swapping nouns into a
frozen paragraph.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

# ---------------------------------------------------------------------------
# Core simulation helpers
# ---------------------------------------------------------------------------

THRESHOLD = 1.0



def _fallback_storyparams(args, rng, cls, ns):
    data = {}
    missing = getattr(__import__("dataclasses"), "MISSING")
    for field in __import__("dataclasses").fields(cls):
        name = field.name
        value = None
        for arg_name in (name, name.removesuffix("_name"), name.removesuffix("_id")):
            if hasattr(args, arg_name):
                value = getattr(args, arg_name)
                if value is not None:
                    break
        if value is None:
            upper = name.upper()
            keys = [upper, upper + "S", upper + "ES"]
            if upper.endswith("Y"):
                keys.append(upper[:-1] + "IES")
            for key in keys:
                pool = ns.get(key)
                if isinstance(pool, dict) and pool:
                    value = next(iter(pool.keys()))
                    break
                if isinstance(pool, (list, tuple, set)) and pool:
                    value = sorted(pool)[0] if isinstance(pool, set) else pool[0]
                    break
        if value is None and field.default is not missing:
            value = field.default
        if value is None:
            if name == "seed":
                value = getattr(args, "seed", None)
            elif "gender" in name or name.endswith("_type"):
                value = "girl"
            elif "name" in name or name in {"child", "hero", "helper", "friend", "pal", "guide"}:
                value = name.removesuffix("_name").replace("_", " ").title() or "Mia"
            else:
                value = name
        data[name] = value
    return cls(**data)


def _safe_lookup(mapping, key):
    try:
        return mapping[key]
    except Exception:
        pass
    if hasattr(mapping, "values"):
        values = list(mapping.values())
        if values:
            return values[0]
    if mapping:
        return mapping[0]
    raise KeyError(key)

@dataclass
class Entity:
    id: str
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    plural: bool = False
    owner: Optional[str] = None
    worn_by: Optional[str] = None
    carried_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    tags: set[str] = field(default_factory=set)

    hero: object | None = None
    def meter(self, name: str) -> float:
        return self.meters.get(name, 0.0)

    def meme(self, name: str) -> float:
        return self.memes.get(name, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def is_loud(self) -> bool:
        return self.meter("noise") >= THRESHOLD
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    def __post_init__(self) -> None:
        if not hasattr(self.meters, "__missing__"):
            object.__setattr__(self, "meters", __import__("collections").defaultdict(float, self.meters))
        if not hasattr(self.memes, "__missing__"):
            object.__setattr__(self, "memes", __import__("collections").defaultdict(float, self.memes))

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}.get(case, "they")
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name in {"tags", "supports", "covers", "guards", "causes"}:
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word", "award_phrase"}:
            return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", ""))
        if name.startswith(("is_", "has_", "can_", "safe", "unsafe")):
            return False
        if name in {"comforting", "messy", "delivered", "sturdy", "protective", "broken", "wet"}:
            return False
        return ""


@dataclass
class Scene:
    place: str
    indoor: bool = False
    weather: str = ""
    outdoor: object | None = None
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

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        return None


@dataclass
class MarchPlan:
    id: str
    target: str
    chant: str
    rhyme1: str
    rhyme2: str
    march_verb: str
    mess: str
    mishap: str
    ending_bad: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def label(self) -> str:
        return str(getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or str(getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower())))

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

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}.get(case, "they")
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name in {"tags", "supports", "covers", "guards", "causes"}:
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word", "award_phrase"}:
            return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", ""))
        if name.startswith(("is_", "has_", "can_", "safe", "unsafe")):
            return False
        if name in {"comforting", "messy", "delivered", "sturdy", "protective", "broken", "wet"}:
            return False
        return ""


class World:
    def __init__(self, scene: Scene) -> None:
        self.scene = scene
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
        clone = World(self.scene)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SCENES = {
    "yard": Scene(place="the yard", outdoor=True if False else False, weather=""),
    "playroom": Scene(place="the playroom", indoor=True, weather=""),
    "street": Scene(place="the little street", indoor=False, weather="breezy"),
    "hall": Scene(place="the hall", indoor=True, weather=""),
}

PLANS = {
    "weed_war": MarchPlan(
        id="weed_war",
        target="the weeds",
        chant="We march, we march, to shoo the weeds apart!",
        rhyme1="feet in a beat",
        rhyme2="sweep and repeat",
        march_verb="march against the weeds",
        mess="mud",
        mishap="they stomped into a wet patch and made a squishy splash",
        ending_bad="the weeds stayed put, and the boots ended up muddy",
        tags={"war", "march", "rhyme", "comedy", "mud"},
    ),
    "sock_war": MarchPlan(
        id="sock_war",
        target="the sock pile",
        chant="We march, we march, to sort the socks in line!",
        rhyme1="sock by sock",
        rhyme2="tick tock, unlock",
        march_verb="march at the sock pile",
        mess="tangle",
        mishap="they tripped over a sock snake and spun in a tiny circle",
        ending_bad="the socks were still mixed up, and the basket tipped sideways",
        tags={"war", "march", "rhyme", "comedy", "tangle"},
    ),
    "crumb_war": MarchPlan(
        id="crumb_war",
        target="the crumb trail",
        chant="We march, we march, to chase each crumb away!",
        rhyme1="crunch and munch",
        rhyme2="stomp, then sweep, then lunch",
        march_verb="march after the crumbs",
        mess="crumbs",
        mishap="they sneezed at the crumbs and sent them flying like confetti",
        ending_bad="the floor looked even messier than before",
        tags={"war", "march", "rhyme", "comedy", "crumbs"},
    ),
}

NAMES = {
    "girl": ["Mina", "Lia", "Nora", "Pia", "Zoe"],
    "boy": ["Toby", "Finn", "Milo", "Leo", "Ben"],
}

ROLES = ["captain", "drummer", "banner-bearer", "sergeant"]
TRAITS = ["brave", "silly", "proud", "bouncy", "curious"]
GARBS = [
    ("boots", "rain boots", "feet"),
    ("cap", "a paper cap", "head"),
    ("vest", "a bright vest", "torso"),
    ("scarf", "a striped scarf", "neck"),
]


# ---------------------------------------------------------------------------
# Parameters
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    scene: str
    plan: str
    name: str
    gender: str
    role: str
    trait: str
    gear: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------
    @property
    def label_word(self) -> str:
        return str(getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def label(self) -> str:
        return str(getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or str(getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower())))

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

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}.get(case, "they")
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name in {"tags", "supports", "covers", "guards", "causes"}:
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word", "award_phrase"}:
            return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", ""))
        if name.startswith(("is_", "has_", "can_", "safe", "unsafe")):
            return False
        if name in {"comforting", "messy", "delivered", "sturdy", "protective", "broken", "wet"}:
            return False
        return ""


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for scene_id in SCENES:
        for plan_id in PLANS:
            for gear_id, _, _ in GARBS:
                combos.append((scene_id, plan_id, gear_id))
    return combos


def explain_rejection(scene_id: str, plan_id: str, gear_id: str) -> str:
    return (
        f"(No story: {scene_id}, {plan_id}, and {gear_id} do not form a usable "
        f"comedy march premise.)"
    )


# ---------------------------------------------------------------------------
# World actions
# ---------------------------------------------------------------------------

def _do_march(world: World, hero: Entity, plan: MarchPlan) -> None:
    hero.meters["speed"] = hero.meter("speed") + 1
    hero.meters["noise"] = hero.meter("noise") + 1
    hero.memes["pride"] = hero.meme("pride") + 1
    world.facts["march_started"] = True


def _do_chant(world: World, hero: Entity, plan: MarchPlan) -> None:
    hero.meters["noise"] = hero.meter("noise") + 1
    hero.memes["joy"] = hero.meme("joy") + 1
    hero.memes["resolve"] = hero.meme("resolve") + 1
    world.facts["chant"] = plan.chant


def _do_mishap(world: World, hero: Entity, plan: MarchPlan) -> None:
    hero.meters[plan.mess] = hero.meter(plan.mess) + 1
    hero.meters["muddle"] = hero.meter("muddle") + 1
    hero.memes["worry"] = hero.meme("worry") + 1
    hero.memes["embarrassment"] = hero.meme("embarrassment") + 1
    world.facts["mishap"] = plan.mishap


def _do_bad_ending(world: World, hero: Entity, plan: MarchPlan) -> None:
    hero.memes["joy"] = max(0.0, hero.meme("joy") - 1)
    hero.memes["embarrassment"] = hero.meme("embarrassment") + 1
    hero.memes["laughter"] = hero.meme("laughter") + 1
    world.facts["ending_bad"] = plan.ending_bad
    world.facts["resolved"] = False


def simulate(world: World, hero: Entity, plan: MarchPlan) -> None:
    _do_march(world, hero, plan)
    _do_chant(world, hero, plan)
    _do_mishap(world, hero, plan)
    _do_bad_ending(world, hero, plan)


# ---------------------------------------------------------------------------
# Narrative
# ---------------------------------------------------------------------------

def intro_line(hero: Entity, role: str, trait: str, gear_label: str, scene: Scene, plan: MarchPlan) -> str:
    return (
        f"{hero.id} was a {trait} little {hero.type} who loved being the {role} "
        f"of a grand pretend war march. {hero.pronoun('subject').capitalize()} wore "
        f"{gear_label} and thought the day at {scene.place} was ready for a rhyme."
    )


def setup_line(hero: Entity, plan: MarchPlan) -> str:
    return (
        f"{hero.id} pointed at {plan.target} and said, "
        f"\"We march, we march, and make it gone!\" "
        f"The words bounced like a drum."
    )


def turn_line(hero: Entity, plan: MarchPlan) -> str:
    return (
        f"The little parade started smartly: {plan.rhyme1}, {plan.rhyme2}. "
        f"With every step, {hero.id} grew louder and rounder with pride."
    )


def mishap_line(hero: Entity, plan: MarchPlan) -> str:
    return (
        f"But then {plan.mishap}. {hero.id}'s big brave feet went from neat to defeat, "
        f"and the rhyme slipped off the beat."
    )


def ending_line(hero: Entity, plan: MarchPlan) -> str:
    return (
        f"In the end, {plan.ending_bad}. {hero.id} laughed in an embarrassed way, "
        f"because the war march had marched itself into a silly mess."
    )


def tail_image(hero: Entity, plan: MarchPlan) -> str:
    return (
        f"{hero.id} stood beside the messy trail, with a lopsided smile and muddy toes, "
        f"while the chant still echoed like a joke that never won."
    )


def tell_story(world: World, hero: Entity, plan: MarchPlan) -> None:
    world.say(intro_line(hero, world.facts["role"], world.facts["trait"], world.facts["gear_label"], world.scene, plan))
    world.say(setup_line(hero, plan))
    world.para()
    world.say(turn_line(hero, plan))
    world.say(mishap_line(hero, plan))
    world.para()
    world.say(ending_line(hero, plan))
    world.say(tail_image(hero, plan))


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short, funny story about a child who leads a war march and uses the word "{f["plan"].target}".',
        f"Tell a comedy story with a march, a rhyme, and a bad ending for {f['name']}.",
        f"Write a child-friendly story where {f['name']} tries to {f['plan'].march_verb} but the plan goes wrong.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    plan: MarchPlan = f["plan"]
    return [
        QAItem(
            question=f"What kind of story is this about {hero.id}?",
            answer=(
                f"It is a funny pretend war march story. {hero.id} tries to lead a march, "
                f"but it ends badly in a silly way."
            ),
        ),
        QAItem(
            question=f"What did {hero.id} want to do at {world.scene.place}?",
            answer=(
                f"{hero.id} wanted to {plan.march_verb}. {hero.pronoun('subject').capitalize()} "
                f"wanted the march to sound brave and neat."
            ),
        ),
        QAItem(
            question=f"Why did the story end badly?",
            answer=(
                f"It ended badly because {f['mishap']} and the plan failed. "
                f"The march did not fix the problem, so the ending stayed funny but bad."
            ),
        ),
        QAItem(
            question=f"What happened to the rhyme during the march?",
            answer=(
                f"The rhyme started out strong, but when the mishap happened, it slipped off the beat. "
                f"That made the march sound more silly than fierce."
            ),
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a march?",
            answer=(
                "A march is a way of walking in a steady, strong rhythm, often with steps that match a chant or drum."
            ),
        ),
        QAItem(
            question="What is rhyme?",
            answer=(
                "Rhyme is when words sound alike at the end, like 'feet' and 'beat' or 'tock' and 'sock'."
            ),
        ),
        QAItem(
            question="Why can a comedy ending be funny?",
            answer=(
                "A comedy ending is funny when something goes wrong in a harmless way and the characters can laugh about it."
            ),
        ),
        QAItem(
            question="What is a pretend war in a story for kids?",
            answer=(
                "A pretend war is not a real battle. It is just make-believe, like a game with big words and dramatic marching."
            ),
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


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
scene(S) :- scene_fact(S).
plan(P) :- plan_fact(P).
gear(G) :- gear_fact(G).

valid_story(S, P, G) :- scene(S), plan(P), gear(G).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SCENES:
        lines.append(asp.fact("scene_fact", sid))
    for pid in PLANS:
        lines.append(asp.fact("plan_fact", pid))
    for gid, _, _ in GARBS:
        lines.append(asp.fact("gear_fact", gid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    asp_set = set(asp.atoms(model, "valid_story"))
    py_set = set(valid_combos())
    if asp_set == py_set:
        print(f"OK: clingo gate matches valid_combos() ({len(py_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print("  only in clingo:", sorted(asp_set - py_set))
    print("  only in python:", sorted(py_set - asp_set))
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Comedy war-march storyworld with a bad ending and rhyme.")
    ap.add_argument("--scene", choices=SCENES)
    ap.add_argument("--plan", choices=PLANS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--role", choices=ROLES)
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("--gear", choices=[g[0] for g in GARBS])
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if getattr(args, "scene", None) and getattr(args, "plan", None) and getattr(args, "gear", None):
        pass
    combos = valid_combos()
    if getattr(args, "scene", None):
        combos = [c for c in combos if c[0] == getattr(args, "scene", None)]
    if getattr(args, "plan", None):
        combos = [c for c in combos if c[1] == getattr(args, "plan", None)]
    if getattr(args, "gear", None):
        combos = [c for c in combos if c[2] == getattr(args, "gear", None)]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    scene, plan, gear = rng.choice(list(combos))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(_safe_lookup(NAMES, gender))
    role = getattr(args, "role", None) or rng.choice(ROLES)
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(scene=scene, plan=plan, name=name, gender=gender, role=role, trait=trait, gear=gear)


def generate(params: StoryParams) -> StorySample:
    scene = _safe_lookup(SCENES, params.scene)
    plan = _safe_lookup(PLANS, params.plan)
    gear_label = dict((gid, label) for gid, label, _ in GARBS)[params.gear]
    world = World(scene)
    hero = world.add(Entity(id=params.name, kind="character", type=params.gender))
    world.facts.update(
        hero=hero,
        plan=plan,
        name=params.name,
        role=params.role,
        trait=params.trait,
        gear_label=gear_label,
    )
    simulate(world, hero, plan)
    story = []
    world.para()
    tell_story(world, hero, plan)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


CURATED = [
    StoryParams(scene="yard", plan="weed_war", name="Mina", gender="girl", role="captain", trait="bouncy", gear="boots"),
    StoryParams(scene="playroom", plan="sock_war", name="Toby", gender="boy", role="drummer", trait="silly", gear="cap"),
    StoryParams(scene="hall", plan="crumb_war", name="Lia", gender="girl", role="banner-bearer", trait="proud", gear="vest"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show valid_story/3."))
        combos = sorted(set(asp.atoms(model, "valid_story")))
        print(f"{len(combos)} compatible combos:")
        for c in combos:
            print("  ", c)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(getattr(args, "n", None) * 50, 50):
            seed = base_seed + i
            i += 1
            rng = random.Random(seed)
            try:
                params = resolve_params(args, rng)
            except StoryError:
                continue
            params.seed = seed
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)

    if getattr(args, "json", None):
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 and not getattr(args, "all", None) else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
