#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/elite_involve_karate_transformation_twist_adventure.py
======================================================================================

A standalone story world about an adventure in a small dojo: a child discovers an
elite karate challenge, gets involved in a quest, faces a surprising twist, and
comes through a transformation that changes both skill and confidence.

The world is intentionally tiny and classical:
- typed entities with physical meters and emotional memes
- a forward-chained causal model
- a reasonableness gate for valid story combinations
- a Python gate with an inline ASP twin
- story-grounded and world-knowledge QA generated from world state

Seed words: elite, involve, karate
Features: Transformation, Twist
Style: Adventure
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
SKILL_UP = 2.0


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
    tags: set[str] = field(default_factory=set)

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
        return self.label or self.type
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
    detail: str
    adventure: str
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
class HeroConfig:
    id: str
    name: str
    type: str
    age: int
    trait: str
    title: str
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
class ChallengeConfig:
    id: str
    object_name: str
    phrase: str
    risk: str
    reveal: str
    twist: str
    makes_noise: bool = False
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
class TransformationConfig:
    id: str
    from_state: str
    to_state: str
    method: str
    reward: str
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
class AllyConfig:
    id: str
    name: str
    type: str
    role: str
    title: str
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
class StoryParams:
    setting: str
    hero: str
    ally: str
    challenge: str
    transformation: str
    twist: str
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

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        c = World(self.setting)
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = copy.deepcopy(self.facts)
        return c


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


def _r_transformation(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    if hero.meters["training"] < THRESHOLD:
        return out
    sig = ("transformed", hero.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.meters["skill"] += SKILL_UP
    hero.memes["confidence"] += 1
    out.append("__transform__")
    return out


def _r_twist(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    challenge = world.get("challenge")
    if challenge.meters["revealed"] < THRESHOLD:
        return out
    sig = ("twist", challenge.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.memes["surprise"] += 1
    out.append("__twist__")
    return out


CAUSAL_RULES = [
    Rule("transformation", "skill", _r_transformation),
    Rule("twist", "story", _r_twist),
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


def valid_combo(setting: Setting, challenge: ChallengeConfig, transformation: TransformationConfig) -> bool:
    return challenge.object_name in {"dummy", "gate", "torch"} and transformation.id in TRANSFORMATIONS


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid in SETTINGS:
        for cid, challenge in CHALLENGES.items():
            for tid, trans in TRANSFORMATIONS.items():
                if challenge.object_name == "dummy" and trans.id in TRANSFORMATIONS:
                    combos.append((sid, cid, tid))
    return combos


def explore(world: World, hero: Entity, ally: Entity, setting: Setting) -> None:
    hero.memes["curiosity"] += 1
    ally.memes["curiosity"] += 1
    world.say(
        f"In {setting.place}, {hero.id} and {ally.id} set out on an adventure. "
        f"{setting.detail} {setting.adventure}"
    )
    world.say(
        f"{hero.id} wanted to become {hero.title} of the local karate path, and "
        f"{ally.id} agreed to get involved."
    )


def challenge_beckons(world: World, hero: Entity, challenge: ChallengeConfig) -> None:
    hero.memes["drive"] += 1
    world.say(
        f"At the center of the dojo stood {challenge.phrase}. It looked simple, "
        f"but {challenge.risk}."
    )
    world.say(
        f'"If you can solve it," the old coach said, "you may join the elite class."'
    )


def train(world: World, hero: Entity, trans: TransformationConfig) -> None:
    hero.meters["training"] += 1
    hero.meters["focus"] += 1
    world.say(
        f"{hero.id} took a deep breath and practiced karate again and again. "
        f"{hero.id} used {trans.method} to match {trans.reward}."
    )


def reveal_twist(world: World, challenge: ChallengeConfig) -> None:
    challenge.meters["revealed"] += 1
    world.say(
        f"Then came the twist: {challenge.twist}. What had seemed like a test was "
        f"really a secret message."
    )


def transform_hero(world: World, hero: Entity, trans: TransformationConfig) -> None:
    world.say(
        f"Little by little, {hero.id} changed from {trans.from_state} into {trans.to_state}. "
        f"{hero.id} stood taller, moved faster, and felt brave."
    )


def ending(world: World, hero: Entity, ally: Entity, setting: Setting, trans: TransformationConfig) -> None:
    hero.memes["joy"] += 1
    ally.memes["joy"] += 1
    world.say(
        f"At last, the elite door swung open. {hero.id} and {ally.id} crossed the threshold "
        f"of {setting.place}, and the adventure ended with {hero.id} carrying {trans.reward} "
        f"and a new karate smile."
    )


def tell(setting: Setting, hero_cfg: HeroConfig, ally_cfg: AllyConfig,
         challenge: ChallengeConfig, trans: TransformationConfig) -> World:
    world = World(setting)
    hero = world.add(Entity(id="hero", kind="character", type=hero_cfg.type, label=hero_cfg.name,
                            role="hero", traits=[hero_cfg.trait], attrs={"title": hero_cfg.title}))
    ally = world.add(Entity(id="ally", kind="character", type=ally_cfg.type, label=ally_cfg.name,
                            role="ally", attrs={"title": ally_cfg.title}))
    old_coach = world.add(Entity(id="coach", kind="character", type="man", label="the coach",
                                 role="coach"))
    ch = world.add(Entity(id="challenge", type="thing", label=challenge.object_name,
                          attrs={"twist": challenge.twist}))
    world.facts.update(hero=hero, ally=ally, coach=old_coach, challenge=ch,
                       setting=setting, challenge_cfg=challenge, trans=trans)

    explore(world, hero, ally, setting)
    world.para()
    challenge_beckons(world, hero, challenge)
    train(world, hero, trans)
    reveal_twist(world, ch)
    world.para()
    transform_hero(world, hero, trans)
    propagate(world, narrate=True)
    ending(world, hero, ally, setting, trans)

    world.facts.update(
        outcome="transformed",
        hero_skill=hero.meters["skill"],
        hero_confidence=hero.memes["confidence"],
        twist_seen=ch.meters["revealed"] >= THRESHOLD,
    )
    return world


SETTINGS = {
    "dojo": Setting(
        id="dojo",
        place="the old dojo",
        detail="Lanterns glowed beside the mats, and the wooden floor shone like honey.",
        adventure="Inside, every echo sounded like a promise.",
    ),
    "garden": Setting(
        id="garden",
        place="the lantern garden",
        detail="Stone paths curled between tall flowers, and a small gate waited at the end.",
        adventure="Beyond it, the path felt like a hidden quest.",
    ),
    "harbor": Setting(
        id="harbor",
        place="the moon harbor",
        detail="Ropes creaked on the boats, and the waves tapped the dock like tiny drums.",
        adventure="Somewhere past the boats, a secret waited.",
    ),
}

HEROES = {
    "maya": HeroConfig(id="maya", name="Maya", type="girl", age=7, trait="brave", title="an elite fighter"),
    "eli": HeroConfig(id="eli", name="Eli", type="boy", age=8, trait="careful", title="an elite learner"),
    "zoe": HeroConfig(id="zoe", name="Zoe", type="girl", age=6, trait="quick", title="an elite explorer"),
}

ALLIES = {
    "pax": AllyConfig(id="pax", name="Pax", type="boy", role="helper", title="a steady friend"),
    "luna": AllyConfig(id="luna", name="Luna", type="girl", role="helper", title="a watchful friend"),
}

CHALLENGES = {
    "dummy": ChallengeConfig(
        id="dummy",
        object_name="practice dummy",
        phrase="a practice dummy wrapped in red cloth",
        risk="it would wobble if touched too hard",
        reveal="the dummy was hiding a tiny scroll in its sleeve",
        twist="the dummy had been pointing toward the next clue all along",
    ),
    "gate": ChallengeConfig(
        id="gate",
        object_name="gate",
        phrase="a high gate painted gold",
        risk="it would not open unless someone moved with karate balance",
        reveal="a loose stone near the hinge made a soft hollow sound",
        twist="the gate was not locked; it was waiting to be pushed the right way",
    ),
    "torch": ChallengeConfig(
        id="torch",
        object_name="torch",
        phrase="a torch stand beside the path",
        risk="its light was flickering like a warning",
        reveal="a hidden trail shone whenever the torch turned toward the cliffs",
        twist="the torch was a guide, not a danger",
    ),
}

TRANSFORMATIONS = {
    "stance": TransformationConfig(
        id="stance",
        from_state="a nervous beginner",
        to_state="a steady karate adventurer",
        method="careful stances and quiet breathing",
        reward="steady feet",
    ),
    "swiftness": TransformationConfig(
        id="swiftness",
        from_state="a slow watcher",
        to_state="a quick-moving karate hero",
        method="fast turns and sharp steps",
        reward="swift hands",
    ),
    "focus": TransformationConfig(
        id="focus",
        from_state="a distracted traveler",
        to_state="a focused karate helper",
        method="a calm bow and a bright stare",
        reward="clear eyes",
    ),
}

CURATED = [
    StoryParams(setting="dojo", hero="maya", ally="pax", challenge="dummy", transformation="stance", twist="twist", seed=1),
    StoryParams(setting="garden", hero="eli", ally="luna", challenge="gate", transformation="focus", twist="twist", seed=2),
    StoryParams(setting="harbor", hero="zoe", ally="pax", challenge="torch", transformation="swiftness", twist="twist", seed=3),
]

KNOWLEDGE = {
    "karate": [("What is karate?", "Karate is a kind of martial arts practice. It uses balance, focus, and controlled moves.")],
    "elite": [("What does elite mean?", "Elite means the very best or among the top few. An elite group is special and highly skilled.")],
    "transformation": [("What is a transformation?", "A transformation is a big change from one state to another. It can change how someone looks, moves, or feels.")],
    "twist": [("What is a twist in a story?", "A twist is a surprise that changes what you thought was happening. It makes the story turn in a new direction.")],
    "dojo": [("What is a dojo?", "A dojo is a place where people practice karate or other martial arts.")],
}
KNOWLEDGE_ORDER = ["elite", "karate", "dojo", "transformation", "twist"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write an adventure story that uses the words elite, involve, and karate.",
        f"Tell a child-friendly adventure where {f['hero'].label_word} gets involved in a karate challenge and a surprise twist changes the mission.",
        f"Write a story about a small hero who wants to join an elite karate group, faces a twist, and transforms by the end.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero: Entity = f["hero"]
    ally: Entity = f["ally"]
    ch: Entity = f["challenge"]
    trans: TransformationConfig = f["trans"]
    setting: Setting = f["setting"]
    return [
        ("Who is the story about?", f"The story is about {hero.label_word} and {ally.label_word} at {setting.place}. They go on a karate adventure together."),
        ("What did the hero want to do?", f"{hero.label_word} wanted to get involved and become part of the elite karate challenge. That goal pushed the adventure forward."),
        ("What was the twist?", f"The twist was that {ch.attrs['twist']}. The surprise changed the meaning of the challenge and made the path feel magical."),
        ("How did the hero transform?", f"{hero.label_word} changed from {trans.from_state} into {trans.to_state}. The karate practice and the twist helped make that change real."),
        ("How did the story end?", f"It ended with {hero.label_word} crossing into {setting.place} as a stronger karate adventurer. The ending image proves the hero had transformed."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"elite", "karate", "dojo", "transformation", "twist"}
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
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


def explain_rejection(args: argparse.Namespace) -> str:
    return "(No story: this combination does not make a coherent karate adventure.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: an elite karate adventure with a twist and transformation."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--hero", choices=HEROES)
    ap.add_argument("--ally", choices=ALLIES)
    ap.add_argument("--challenge", choices=CHALLENGES)
    ap.add_argument("--transformation", choices=TRANSFORMATIONS)
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


def valid_combo_ids() -> list[tuple[str, str, str]]:
    return [(s, h, c) for s in SETTINGS for h in HEROES for c in CHALLENGES if c in {"dummy", "gate", "torch"}]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [(s, h, a, c, t) for s in SETTINGS for h in HEROES for a in ALLIES for c in CHALLENGES for t in TRANSFORMATIONS]
    combos = [x for x in combos if (args.setting is None or x[0] == args.setting)
              and (args.hero is None or x[1] == args.hero)
              and (args.ally is None or x[2] == args.ally)
              and (args.challenge is None or x[3] == args.challenge)
              and (args.transformation is None or x[4] == args.transformation)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    s, h, a, c, t = rng.choice(sorted(combos))
    return StoryParams(setting=s, hero=h, ally=a, challenge=c, transformation=t, twist="twist")


def generate(params: StoryParams) -> StorySample:
    for key, table in [("setting", SETTINGS), ("hero", HEROES), ("ally", ALLIES), ("challenge", CHALLENGES), ("transformation", TRANSFORMATIONS)]:
        if getattr(params, key) not in table:
            raise StoryError(f"Invalid {key}: {getattr(params, key)}")
    world = tell(SETTINGS[params.setting], HEROES[params.hero], ALLIES[params.ally], CHALLENGES[params.challenge], TRANSFORMATIONS[params.transformation])
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


ASP_RULES = r"""
valid(S,H,A,C,T) :- setting(S), hero(H), ally(A), challenge(C), transformation(T).
twist_happens(C) :- challenge(C).
transformed(H) :- training(H), twist_happens(_).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for hid in HEROES:
        lines.append(asp.fact("hero", hid))
    for aid in ALLIES:
        lines.append(asp.fact("ally", aid))
    for cid in CHALLENGES:
        lines.append(asp.fact("challenge", cid))
    for tid in TRANSFORMATIONS:
        lines.append(asp.fact("transformation", tid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/5."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set((s, h, a, c, t) for s in SETTINGS for h in HEROES for a in ALLIES for c in CHALLENGES for t in TRANSFORMATIONS):
        print("OK: ASP gate matches Python combos.")
    else:
        print("MISMATCH: ASP gate differs.")
        rc = 1
    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise RuntimeError("empty story")
        print("OK: generate() smoke test passed.")
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        rc = 1
    return rc


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/5."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos")
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            p = resolve_params(args, random.Random(base_seed + i))
            p.seed = base_seed + i
            sample = generate(p)
            if sample.story not in seen:
                samples.append(sample)
                seen.add(sample.story)
            i += 1
    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=f"### variant {i+1}" if len(samples) > 1 else "")
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
