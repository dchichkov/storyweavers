#!/usr/bin/env python3
"""
storyworlds/worlds/becca_foreshadowing_suspense_adventure.py
=============================================================

A compact adventure storyworld centered on Becca, with foreshadowing and
suspense as first-class story instruments.

Premise:
- Becca is an eager little explorer.
- She hears a curious clue, sees warning signs, and follows a trail.
- A small danger builds: a dim path, a rickety bridge, and a missing object.
- The ending pays off the clues with a brave, practical discovery.

The world is intentionally small:
- one hero
- one companion
- one setting path
- one prized object
- one simple tension turn
- one resolution image

The story is driven by simulated state:
- meters model physical conditions like light, noise, distance, wobble, and damage
- memes model feelings like curiosity, fear, suspense, relief, and pride

Foreshadowing:
- early details are recorded as clues
- later text references those clues as meaningful signs

Suspense:
- the path grows dimmer and wobblier before the turn
- the story pauses on a near-miss before the reveal

Adventure:
- movement through a place
- a goal to reach
- a small obstacle overcome with a tool and a companion
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

_storyworlds_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if not os.path.exists(os.path.join(_storyworlds_dir, "results.py")):
    _storyworlds_dir = os.path.dirname(_storyworlds_dir)
sys.path.insert(0, _storyworlds_dir)
from results import QAItem, StoryError, StorySample  # noqa: E402


THRESHOLD = 1.0



def _safe_fact(world, facts, key):
    value = facts.get(key) if hasattr(facts, "get") else None
    if hasattr(value, "id") or hasattr(value, "label") or hasattr(value, "verb") or hasattr(value, "sign"):
        return value
    if isinstance(value, str):
        if hasattr(world, "get"):
            try:
                resolved = world.get(value)
                if resolved is not None:
                    return resolved
            except Exception:
                pass
        upper = key.upper()
        for registry_name in (upper, upper + "S", upper + "ES", upper + "_REGISTRY"):
            registry = globals().get(registry_name)
            if isinstance(registry, dict) and value in registry:
                return registry[value]
        if upper.endswith("Y"):
            registry = globals().get(upper[:-1] + "IES")
            if isinstance(registry, dict) and value in registry:
                return registry[value]
    entities = getattr(world, "entities", {})
    if hasattr(entities, "values"):
        for entity in entities.values():
            if hasattr(entity, "id") or hasattr(entity, "label"):
                return entity
    return value


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
    kind: str = "thing"          # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    portable: bool = True
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    traits: list[str] = field(default_factory=list)
    plural: bool = False

    artifact: object | None = None
    companion: object | None = None
    hero: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "mom"}
        male = {"boy", "man", "father", "dad"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"
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

    @property
    def tags(self):
        if "_tags" not in self.__dict__:
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


@dataclass
class Setting:
    place: str = "the old forest path"
    features: set[str] = field(default_factory=set)
    @property
    def meters(self):
        if "_meters" not in self.__dict__:
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if "_memes" not in self.__dict__:
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if "_tags" not in self.__dict__:
            object.__setattr__(self, "_tags", set())
        return self._tags

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        return None


@dataclass
class Artifact:
    id: str
    label: str
    phrase: str
    type: str = "thing"
    danger: str = "fall"
    clue: str = ""
    value: str = "special"
    region: str = "path"
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def meters(self):
        if "_meters" not in self.__dict__:
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if "_memes" not in self.__dict__:
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if "_tags" not in self.__dict__:
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


@dataclass
class StoryParams:
    place: str = "path"
    artifact: str = "lantern"
    companion: str = "fox"
    name: str = "Becca"
    trait: str = "brave"
    seed: Optional[int] = None
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
        if "_meters" not in self.__dict__:
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if "_memes" not in self.__dict__:
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if "_tags" not in self.__dict__:
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


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.clues: list[str] = []
        self.fired: set[tuple] = set()

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
        import copy
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.clues = list(self.clues)
        clone.fired = set(self.fired)
        return clone


SETTINGS = {
    "path": Setting(place="the old forest path", features={"trees", "bridge", "mist"}),
    "cave": Setting(place="the small echo cave", features={"stones", "dark", "echo"}),
    "harbor": Setting(place="the quiet harbor trail", features={"wind", "rope", "water"}),
}

ARTIFACTS = {
    "lantern": Artifact(
        id="lantern",
        label="lantern",
        phrase="a little brass lantern",
        danger="going dark",
        clue="a warm flicker in the distance",
        value="safe light",
        region="path",
    ),
    "map": Artifact(
        id="map",
        label="map",
        phrase="a folded treasure map",
        danger="getting lost",
        clue="an arrow drawn in blue ink",
        value="a hidden route",
        region="path",
    ),
    "shell": Artifact(
        id="shell",
        label="shell",
        phrase="a smooth shell with a spiral",
        danger="breaking",
        clue="a tiny shimmer beside the water",
        value="a secret signal",
        region="water",
    ),
}

COMPANIONS = {
    "fox": ("fox", "a small fox with a white tail"),
    "dog": ("dog", "a happy dog with muddy paws"),
    "bird": ("bird", "a bright bird with a curious tilt"),
}

TRAITS = ["brave", "curious", "patient", "quick-thinking", "steady"]


@dataclass
class StoryContext:
    hero: Entity
    companion: Entity
    artifact: Entity
    setting: Setting
    clue_text: str = ""
    suspense_peak: str = ""
    resolved: bool = False
    danger_seen: bool = False
    ctx: object | None = None
    @property
    def meters(self):
        if "_meters" not in self.__dict__:
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if "_memes" not in self.__dict__:
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if "_tags" not in self.__dict__:
            object.__setattr__(self, "_tags", set())
        return self._tags

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        return None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Adventure storyworld about Becca, foreshadowing, and suspense."
    )
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--artifact", choices=ARTIFACTS)
    ap.add_argument("--companion", choices=COMPANIONS)
    ap.add_argument("--name")
    ap.add_argument("--trait", choices=TRAITS)
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
    place = getattr(args, "place", None) or rng.choice(list(SETTINGS))
    artifact = getattr(args, "artifact", None) or rng.choice(list(ARTIFACTS))
    companion = getattr(args, "companion", None) or rng.choice(list(COMPANIONS))
    name = getattr(args, "name", None) or "Becca"
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(place=place, artifact=artifact, companion=companion, name=name, trait=trait)


def _entity_pronoun(ent: Entity) -> str:
    return ent.pronoun("subject")


def _object_pronoun(ent: Entity) -> str:
    return ent.pronoun("object")


def _poss_pronoun(ent: Entity) -> str:
    return ent.pronoun("possessive")


def _meter(e: Entity, key: str) -> float:
    return e.meters.get(key, 0.0)


def _mem(e: Entity, key: str) -> float:
    return e.memes.get(key, 0.0)


def _add_meter(e: Entity, key: str, amount: float = 1.0) -> None:
    e.meters[key] = e.meters.get(key, 0.0) + amount


def _add_mem(e: Entity, key: str, amount: float = 1.0) -> None:
    e.memes[key] = e.memes.get(key, 0.0) + amount


def _do_travel(world: World, ctx: StoryContext) -> None:
    hero = ctx.hero
    _add_meter(hero, "distance", 1)
    _add_mem(hero, "curiosity", 1)
    world.say(f"{hero.id} loved adventures, and one day she set off along {world.setting.place} with her {ctx.companion.type}.")
    world.say(f"Earlier, she had noticed {ctx.artifact.phrase if ctx.artifact.phrase else 'a strange clue'} waiting near the trail, and that little sign kept tugging at her thoughts.")


def _foreshadow(world: World, ctx: StoryContext) -> None:
    hero = ctx.hero
    artifact = ctx.artifact
    if artifact.id == "lantern":
        ctx.clue_text = "the warm flicker"
        world.clues.append(ctx.clue_text)
        world.say(f"Before the path grew dim, {hero.id} remembered {artifact.clue}, and that made her look more carefully at the shadows.")
    elif artifact.id == "map":
        ctx.clue_text = "the blue arrow"
        world.clues.append(ctx.clue_text)
        world.say(f"Before the trail twisted, {hero.id} had seen {artifact.clue}. It looked like someone was trying to help her find the way.")
    else:
        ctx.clue_text = "the sparkle by the water"
        world.clues.append(ctx.clue_text)
        world.say(f"Before the wind picked up, {hero.id} had noticed {artifact.clue}. It seemed small, but it meant something was nearby.")


def _build_suspense(world: World, ctx: StoryContext) -> None:
    hero = ctx.hero
    companion = ctx.companion
    _add_meter(hero, "darkness", 1)
    _add_meter(hero, "wobble", 1)
    _add_mem(hero, "suspense", 1)
    ctx.suspense_peak = "the quietest, shakiest part"
    world.say(f"Then the path changed. The trees leaned closer, the air turned still, and {hero.id} slowed down.")
    world.say(f"At {ctx.suspense_peak}, the ground gave a tiny creak under one careful step, and even {companion.id} stopped to listen.")


def _near_miss(world: World, ctx: StoryContext) -> None:
    hero = ctx.hero
    companion = ctx.companion
    _add_mem(hero, "fear", 1)
    _add_mem(companion, "alert", 1)
    world.say(f"A loose board tipped under {hero.id}'s shoe, and for a breath she thought the little adventure might go wrong.")
    world.say(f"But {companion.id} nudged a steady branch toward her, and {hero.id} grabbed it just in time.")


def _resolve(world: World, ctx: StoryContext) -> None:
    hero = ctx.hero
    artifact = ctx.artifact
    companion = ctx.companion
    _add_mem(hero, "relief", 2)
    _add_mem(hero, "pride", 1)
    _add_meter(hero, "safety", 1)
    ctx.resolved = True
    world.say(f"That was the clue's secret: the little danger was only there to guide her to the right spot.")
    world.say(f"At last, {hero.id} found {artifact.phrase}, exactly where the signs had hinted all along.")
    world.say(f"She held it up beside the last ray of light, and {companion.id} danced around her as the trail felt friendly again.")


def tell(params: StoryParams) -> World:
    setting = _safe_lookup(SETTINGS, params.place)
    world = World(setting)
    hero = world.add(Entity(
        id=params.name,
        kind="character",
        type="girl",
        traits=[params.trait, "careful"],
    ))
    companion_type, companion_phrase = _safe_lookup(COMPANIONS, params.companion)
    companion = world.add(Entity(
        id=params.companion,
        kind="character",
        type=companion_type,
        phrase=companion_phrase,
        traits=["loyal", "quick"],
    ))
    artifact_cfg = _safe_lookup(ARTIFACTS, params.artifact)
    artifact = world.add(Entity(
        id=artifact_cfg.id,
        type="thing",
        label=artifact_cfg.label,
        phrase=artifact_cfg.phrase,
        portable=True,
    ))
    ctx = StoryContext(hero=hero, companion=companion, artifact=artifact, setting=setting)
    world.facts.update(hero=hero, companion=companion, artifact=artifact, setting=setting, ctx=ctx)

    world.say(f"{hero.id} was a {params.trait} little explorer who loved a good trail and a mystery to solve.")
    world.say(f"One morning, she noticed {artifact_cfg.clue}, and that was enough to make her smile and start walking.")
    world.para()
    _do_travel(world, ctx)
    _foreshadow(world, ctx)
    world.para()
    _build_suspense(world, ctx)
    _near_miss(world, ctx)
    world.para()
    _resolve(world, ctx)
    return world


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    artifact = _safe_fact(world, f, "artifact")
    return [
        f"Write an adventure story for a young child about {hero.id} following a clue and finding {artifact.label}.",
        f"Tell a suspenseful but gentle story that includes foreshadowing and ends with a brave discovery.",
        f"Write a short story where a curious girl named {hero.id} notices a sign, walks a trail, and solves a small mystery.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero: Entity = _safe_fact(world, world.facts, "hero")
    companion: Entity = _safe_fact(world, world.facts, "companion")
    artifact: Entity = _safe_fact(world, world.facts, "artifact")
    ctx: StoryContext = _safe_fact(world, world.facts, "ctx")
    return [
        QAItem(
            question=f"Who is the story about?",
            answer=f"The story is about {hero.id}, a {hero.traits[0]} little explorer who goes on an adventure.",
        ),
        QAItem(
            question=f"What clue helped {hero.id} keep going?",
            answer=f"{hero.id} noticed {artifact.clue}, and that clue made her pay attention to the path ahead.",
        ),
        QAItem(
            question=f"What made the middle of the story feel suspenseful?",
            answer=f"The middle felt suspenseful because the path got quieter, the ground creaked, and {hero.id} had to cross a wobbly spot carefully.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended with {hero.id} finding {artifact.phrase} and feeling proud after a brave discovery.",
        ),
        QAItem(
            question=f"Who helped {hero.id} when things got tricky?",
            answer=f"{companion.id} helped by staying close and offering a steady bit of support at the risky moment.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is foreshadowing?",
            answer="Foreshadowing is when a story gives a small clue early that helps the reader notice what may matter later.",
        ),
        QAItem(
            question="What is suspense?",
            answer="Suspense is the feeling of wondering what will happen next when something seems a little risky or uncertain.",
        ),
        QAItem(
            question="What is an adventure story?",
            answer="An adventure story is about someone going somewhere, facing a challenge, and learning something important along the way.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id} ({e.type}) {' '.join(bits)}")
    if world.clues:
        lines.append(f"  clues={world.clues}")
    return "\n".join(lines)


def asp_facts() -> str:
    import asp
    lines = []
    for sid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for feat in sorted(setting.features):
            lines.append(asp.fact("feature", sid, feat))
    for aid, art in ARTIFACTS.items():
        lines.append(asp.fact("artifact", aid))
        lines.append(asp.fact("artifact_danger", aid, art.danger))
        if art.clue:
            lines.append(asp.fact("artifact_clue", aid, art.clue))
    for cid, (ctype, _) in COMPANIONS.items():
        lines.append(asp.fact("companion", cid, ctype))
    lines.append(asp.fact("hero", "becca"))
    return "\n".join(lines)


ASP_RULES = r"""
% A story is reasonable when there is a setting, a clue, suspense, and a resolution.
has_foreshadowing(A) :- artifact_clue(A, _).
has_suspense(A) :- artifact_danger(A, _).
adventure_story(S, A) :- setting(S), artifact(A), has_foreshadowing(A), has_suspense(A).
#show adventure_story/2.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show adventure_story/2."))
    return sorted(set(asp.atoms(model, "adventure_story")))


def python_valid() -> list[tuple]:
    return sorted((sid, aid) for sid in SETTINGS for aid in ARTIFACTS)


def asp_verify() -> int:
    a = set(asp_valid())
    p = set(python_valid())
    if a == p:
        print(f"OK: ASP and Python agree on {len(a)} adventure pairs.")
        return 0
    print("MISMATCH:")
    if a - p:
        print(" only in ASP:", sorted(a - p))
    if p - a:
        print(" only in Python:", sorted(p - a))
    return 1


def explain_rejection(place: str, artifact: str) -> str:
    return f"(No story: the chosen setting '{place}' does not support a clean adventure with '{artifact}'.)"


def valid_params(args: argparse.Namespace) -> bool:
    return getattr(args, "place", None) in SETTINGS and getattr(args, "artifact", None) in ARTIFACTS and getattr(args, "companion", None) in COMPANIONS


CURATED = [
    StoryParams(place="path", artifact="lantern", companion="fox", name="Becca", trait="brave"),
    StoryParams(place="path", artifact="map", companion="dog", name="Becca", trait="curious"),
    StoryParams(place="harbor", artifact="shell", companion="bird", name="Becca", trait="steady"),
]


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
    if getattr(args, "show_asp", None):
        print(asp_program("#show adventure_story/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())

    if getattr(args, "asp", None):
        pairs = asp_valid()
        print(f"{len(pairs)} valid adventure pairs:")
        for place, artifact in pairs:
            print(f"  {place:10} {artifact}")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        for p in CURATED:
            samples.append(generate(p))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 50):
            seed = base_seed + i
            i += 1
            rng = random.Random(seed)
            params = resolve_params(args, rng)
            params.seed = seed
            if not valid_params(argparse.Namespace(place=params.place, artifact=params.artifact, companion=params.companion)):
                print(explain_rejection(params.place, params.artifact))
                return
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
        header = ""
        if getattr(args, "all", None):
            p = sample.params
            header = f"### Becca adventure: {p.place} / {p.artifact} / {p.companion}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
