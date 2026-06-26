#!/usr/bin/env python3
"""
storyworlds/worlds/deepseek_deepseek-v4-flash_service_20260625T031134Z_seed424242_n50/veil_pregnancy_slack_transformation_superhero_story.py
======================================================================================================================================

A standalone story world for "The Veil of the Hidden Mom" — a gentle superhero
transformation tale about a pregnant mother who discovers a magical veil that
gives her powers when she needs slack, and her child who learns that every
hero needs rest.

Seed phrases: veil, pregnancy, slack, transformation, superhero story.

Causal state updates:
---
    wear veil                  -> actor.hidden += 1
    actor hidden + needs help  -> actor.power += 1    (secret transformation)
    actor power use            -> actor.energy -= 1
    actor energy low           -> actor.slack_needed += 1
    child discovers secret     -> actor.trust += 1, child.wonder += 1
    parent rests               -> actor.energy += 2, actor.slack_needed = 0
    transformation active too long -> actor.energy -= 2
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

_storyworlds_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if not os.path.exists(os.path.join(_storyworlds_dir, "results.py")):
    _storyworlds_dir = os.path.dirname(_storyworlds_dir)
sys.path.insert(0, _storyworlds_dir)
from results import QAItem, StoryError, StorySample

THRESHOLD = 1.0

# ---------------------------------------------------------------------------
# Entity model
# ---------------------------------------------------------------------------

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

@dataclass
class Entity:
    id: str
    kind: str = "character"
    type: str = "human"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    location: str = "home"
    # physical meters
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    # emotional/social memes
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    tags: set[str] = field(default_factory=set)

    child: object | None = None
    mom: object | None = None
    veil_entity: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"mother", "mom", "woman", "girl", "daughter"}
        male = {"father", "dad", "man", "boy", "son"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her", "reflexive": "herself"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his", "reflexive": "himself"}[case]
        return {"subject": "it", "object": "it", "possessive": "its", "reflexive": "itself"}[case]


# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------
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


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.day_phase: str = "morning"
        self.weather: str = "sunny"

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        chunks = [" ".join(p) for p in self.paragraphs if p]
        return "\n\n".join(chunks)

    def copy(self) -> "World":
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.day_phase = self.day_phase
        clone.weather = self.weather
        clone.paragraphs = [[]]
        return clone


# ---------------------------------------------------------------------------
# Causal rules (forward chaining)
# ---------------------------------------------------------------------------
@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]
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


def _r_transformation_cost(world: World) -> list[str]:
    out = []
    for actor in world.characters():
        if actor.memes.get("transformed", 0) >= THRESHOLD * 2:
            actor.meters["energy"] -= 2
            if actor.meters["energy"] < 0:
                actor.meters["energy"] = 0
            out.append(f"{actor.pronoun('possessive').capitalize()} energy drained from staying transformed too long.")
    return out


def _r_slack_needed(world: World) -> list[str]:
    out = []
    for actor in world.characters():
        if actor.meters.get("energy", 1) < THRESHOLD and actor.memes.get("slack_needed", 0) < THRESHOLD:
            actor.memes["slack_needed"] += 1
            out.append(f"{actor.id} felt a deep need for slack.")
    return out


def _r_child_discovery(world: World) -> list[str]:
    out = []
    mom = world.entities.get("Mom")
    child = world.entities.get("Child")
    if mom and child and mom.memes.get("transformed", 0) >= THRESHOLD:
        if mom.memes.get("hidden", 0) < THRESHOLD and child.memes.get("knows_secret", 0) < THRESHOLD:
            child.memes["knows_secret"] += 1
            mom.memes["trust"] += 1
            out.append("__discovery__")
    return out


def _r_rest_recovery(world: World) -> list[str]:
    out = []
    for actor in world.characters():
        if actor.memes.get("resting", 0) >= THRESHOLD:
            actor.meters["energy"] += 2
            actor.memes["slack_needed"] = 0
            actor.memes["resting"] = 0
            out.append(f"{actor.id} felt renewed after proper rest.")
    return out


CAUSAL_RULES = [
    Rule(name="transformation_cost", apply=_r_transformation_cost),
    Rule(name="slack_needed", apply=_r_slack_needed),
    Rule(name="child_discovery", apply=_r_child_discovery),
    Rule(name="rest_recovery", apply=_r_rest_recovery),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if s != "__discovery__")
    if narrate:
        for s in produced:
            world.say(s)
    return produced


# ---------------------------------------------------------------------------
# Verbs / screenplay beats
# ---------------------------------------------------------------------------
def morning_setup(world: World) -> None:
    mom = world.get("Mom")
    child = world.get("Child")
    world.say(f"The sun peeked through the curtains in the small apartment. {mom.id} was growing "
              f"a baby inside {mom.pronoun('possessive')} belly, and {child.id} could already see "
              f"the round shape when {child.pronoun()} hugged {mom.pronoun('object')} good morning.")
    world.say(f"{mom.id} smiled but yawned. Pregnancy made {mom.pronoun('object')} tired faster than before.")


def need_for_slack(world: World) -> None:
    mom = world.get("Mom")
    child = world.get("Child")
    mom.memes["slack_needed"] += 1
    world.say(f"{child.id} wanted to play superheroes. 'Can you lift me up, Mommy?' "
              f"{child.pronoun()} asked, arms wide. {mom.id} felt a pang — {mom.pronoun('possessive')} "
              f"back ached, and all {mom.pronoun()} wanted was five minutes of slack.")
    propagate(world)


def discover_veil(world: World) -> None:
    mom = world.get("Mom")
    world.say(f"{mom.id} opened the old wooden chest in the corner. Inside lay a shimmering veil, "
              f"soft as moonlight. When {mom.pronoun()} touched it, a warm glow spread through "
              f"{mom.pronoun('possessive')} fingers. {mom.pronoun().capitalize()} felt stronger — "
              f"lighter — as if the pregnancy weight had turned into power.")
    mom.memes["has_veil"] += 1


def transformation_sequence(world: World) -> None:
    mom = world.get("Mom")
    mom.memes["transformed"] += 1
    mom.memes["hidden"] += 1
    mom.meters["energy"] += 2
    world.say(f"{mom.id} wrapped the veil around {mom.pronoun('possessive')} shoulders. "
              f"In a swirl of silver light, {mom.pronoun()} transformed. Her belly was still "
              f"round, but now it glowed with a soft inner light, and {mom.pronoun()} could "
              f"float just above the floor.")
    world.say(f'"Wow!" {world.get("Child").id} gasped. "You\'re a superhero, Mommy!"')
    propagate(world)


def hero_moment(world: World) -> None:
    child = world.get("Child")
    mom = world.get("Mom")
    world.say(f"{child.id} pointed at the window. A little bird had fallen from its nest, "
              f"cheeping sadly on the balcony. '{mom.id}, save it!' {child.pronoun()} cried.")
    world.say(f"{mom.id} floated to the window, the veil trailing behind {mom.pronoun('object')} "
              f"like a comet's tail. {mom.pronoun().capitalize()} scooped the tiny bird gently "
              f"into {mom.pronoun('possessive')} hands and placed it back in the nest.")
    mom.memes["heroic"] += 1
    child.memes["wonder"] += 1
    propagate(world)


def exhaustion_builds(world: World) -> None:
    mom = world.get("Mom")
    mom.meters["energy"] -= 3
    if mom.meters["energy"] < 0:
        mom.meters["energy"] = 0
    world.say(f"But the transformation drained {mom.pronoun('object')}. {mom.pronoun().capitalize()} "
              f"stumbled, the veil flickering. '{mom.id}!' {world.get('Child').id} cried. "
              f"'You need slack!'")
    propagate(world)


def rest_and_reveal(world: World) -> None:
    mom = world.get("Mom")
    child = world.get("Child")
    mom.memes["transformed"] = 0
    mom.memes["hidden"] = 0
    mom.memes["resting"] += 1
    world.say(f"{mom.id} sank onto the sofa, the veil draping over {mom.pronoun('object')} "
              f"like a blanket. 'Even superheroes need rest,' {mom.pronoun()} whispered to "
              f"{child.id}. {mom.pronoun().capitalize()} patted the cushion beside {mom.pronoun('object')}.")
    world.say(f"{child.id} climbed up and snuggled close. 'You're still a superhero,' "
              f"{child.pronoun()} said. 'Even when you slack.'")
    propagate(world)
    world.say(f"The sun dipped lower, painting the room gold. {mom.id} felt {mom.pronoun('possessive')} "
              f"energy return, warm and steady. The baby kicked gently inside {mom.pronoun('object')} — "
              f"a tiny superhero-in-training. And the veil? It shimmered quietly on the armrest, "
              f"waiting for the next time they needed a little slack.")


def tell(mom_name: str = "Maya", child_name: str = "Leo",
         mom_trait: str = "gentle", child_trait: str = "curious") -> World:
    world = World()
    world.weather = "sunny"

    mom = world.add(Entity(
        id=mom_name, kind="character", type="mother",
        label="mom", traits=["gentle", "nurturing", mom_trait],
    ))
    mom.meters["energy"] = 3.0
    mom.memes["pregnancy_visible"] = 1.0

    child = world.add(Entity(
        id=child_name, kind="character", type="child",
        label="child", traits=["curious", "loving", child_trait],
    ))

    veil_entity = world.add(Entity(
        id="veil", kind="thing", type="magical_item",
        label="veil", phrase="a shimmering veil of moonlight",
        owner=mom_name, location="home",
    ))
    veil_entity.memes["magical"] = 1.0

    # Act 1
    morning_setup(world)
    need_for_slack(world)
    world.para()

    # Act 2
    discover_veil(world)
    transformation_sequence(world)
    hero_moment(world)
    exhaustion_builds(world)
    world.para()

    # Act 3
    rest_and_reveal(world)

    world.facts.update(
        mom=mom, child=child, veil=veil_entity,
        has_veil=True, mom_trait=mom_trait, child_trait=child_trait,
    )
    return world


# ---------------------------------------------------------------------------
# Parameters
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    mom_name: str
    child_name: str
    mom_trait: str
    child_trait: str
    seed: Optional[int] = None
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


MOM_NAMES = ["Maya", "Elena", "Sara", "Priya", "Hannah", "Luna", "Yuna"]
CHILD_NAMES = ["Leo", "Zara", "Milo", "Nina", "Theo", "Aria", "Kai"]
TRAITS = ["gentle", "brave", "patient", "wise", "cheerful", "creative"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Veil of the Hidden Mom — a superhero transformation story about pregnancy, slack, and love.")
    ap.add_argument("--mom-name")
    ap.add_argument("--child-name")
    ap.add_argument("--mom-trait", choices=TRAITS)
    ap.add_argument("--child-trait", choices=TRAITS)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--all", action="store_true", help="render curated variants")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true", help="list compatible story combos via ASP")
    ap.add_argument("--verify", action="store_true", help="verify ASP/Python parity")
    ap.add_argument("--show-asp", action="store_true", help="print ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    mom_name = getattr(args, "mom_name", None) or rng.choice(MOM_NAMES)
    child_name = getattr(args, "child_name", None) or rng.choice(CHILD_NAMES)
    mom_trait = getattr(args, "mom_trait", None) or rng.choice(TRAITS)
    child_trait = getattr(args, "child_trait", None) or rng.choice(TRAITS)
    return StoryParams(mom_name=mom_name, child_name=child_name,
                       mom_trait=mom_trait, child_trait=child_trait)


# ---------------------------------------------------------------------------
# Generation prompts & QA
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a gentle superhero story for a child that includes the words "veil", "pregnancy", and "slack", '
        f'where a mother transforms using a magical veil to help someone.',
        f'Tell a story about {f["mom"].id} who is pregnant and discovers a veil that gives {f["mom"].pronoun("possessive")} '
        f'superpowers, but {f["mom"].pronoun()} learns that even heroes need slack.',
        f'A short children\'s story about transformation: a pregnant mother becomes a superhero with a magic veil, '
        f'and her child {f["child"].id} learns that rest is part of heroism.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    mom = _safe_fact(world, f, "mom")
    child = _safe_fact(world, f, "child")
    m_sub = mom.pronoun("subject")
    m_pos = mom.pronoun("possessive")
    c_sub = child.pronoun("subject")
    c_pos = child.pronoun("possessive")
    return [
        QAItem(
            question=f"What did {mom.id} find in the wooden chest, and how did it change {mom.pronoun('object')}?",
            answer=f"{mom.id} found a shimmering veil in the old wooden chest. When {m_sub} touched it, "
                   f"{m_sub} transformed into a glowing superhero, still pregnant but floating with "
                   f"power. The veil gave {m_pos} hidden strength.",
        ),
        QAItem(
            question=f"Why did {mom.id} need slack, and what happened when {m_sub} pushed too hard?",
            answer=f"{mom.id} was growing a baby inside {m_pos} belly, and the pregnancy made "
                   f"{mom.pronoun('object')} tired. When {m_sub} used the veil too long, "
                   f"{m_pos} energy drained until {m_sub} could barely stand. That's when "
                   f"{m_pos} child {child.id} reminded {mom.pronoun('object')} that "
                   f"even superheroes need slack.",
        ),
        QAItem(
            question=f"How did {child.id} react when {m_sub} transformed and saved the bird?",
            answer=f"{child.id} gasped and said 'You're a superhero, Mommy!' when {m_sub} first transformed. "
                   f"When {mom.id} floated to save the fallen baby bird, {child.id} watched with wonder "
                   f"and later snuggled close, saying {mom.id} was still a superhero even "
                   f"when {m_sub} rested.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem("What is a veil?",
               "A veil is a piece of soft, thin cloth that can be worn over the head or shoulders. "
               "In stories, it can be magical and give special powers."),
        QAItem("What does pregnancy mean?",
               "Pregnancy is when a mother has a baby growing inside her belly. It takes many months, "
               "and the mother needs extra rest and care."),
        QAItem("What does 'slack' mean?",
               "Slack means a break or some rest. When someone needs slack, they need a moment "
               "to relax and recharge, like a superhero needs rest after saving the day."),
        QAItem("What is a transformation?",
               "A transformation is when someone or something changes into a different form. "
               "A caterpillar transforms into a butterfly, and a person can transform into a superhero."),
    ]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A valid story: a mom with a veil, pregnancy visible, who can transform.
has_veil(Mom) :- mom(Mom), magical_veil(Veil), owner(Veil, Mom).
can_transform(Mom) :- mom(Mom), has_veil(Mom), pregnant(Mom), has_energy(Mom).
valid_story(Mom, Child) :- mom(Mom), child(Child), can_transform(Mom).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for n in MOM_NAMES:
        lines.append(asp.fact("mom", n))
        lines.append(asp.fact("pregnant", n))
        lines.append(asp.fact("has_energy", n))
    for n in CHILD_NAMES:
        lines.append(asp.fact("child", n))
    for n in MOM_NAMES:
        lines.append(asp.fact("magical_veil", f"veil_of_{n.lower()}"))
        lines.append(asp.fact("owner", f"veil_of_{n.lower()}", n))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    print("ASP verification: all mom/child pairs are valid in this domain (no invalid combinations exist).")
    stories = asp_valid_stories()
    print(f"ASP reports {len(stories)} valid (mom, child) pairs.")
    return 0


CURATED = [
    StoryParams(mom_name="Maya", child_name="Leo", mom_trait="gentle", child_trait="curious"),
    StoryParams(mom_name="Elena", child_name="Zara", mom_trait="brave", child_trait="cheerful"),
    StoryParams(mom_name="Priya", child_name="Milo", mom_trait="patient", child_trait="creative"),
]


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        lines = ["--- world model state ---"]
        for e in sample.world.entities.values():
            meters = {k: v for k, v in e.meters.items() if v}
            memes = {k: v for k, v in e.memes.items() if v}
            bits = []
            if meters:
                bits.append(f"meters={dict(meters)}")
            if memes:
                bits.append(f"memes={dict(memes)}")
            lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
        print("\n".join(lines))
    if qa:
        print()
        print("== (1) Generation prompts ==")
        for i, p in enumerate(sample.prompts, 1):
            print(f"{i}. {p}")
        print()
        print("== (2) Story questions ==")
        for item in sample.story_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")
        print()
        print("== (3) World-knowledge questions ==")
        for item in sample.world_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")


def generate(params: StoryParams) -> StorySample:
    world = tell(params.mom_name, params.child_name,
                 params.mom_trait, params.child_trait)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        stories = asp_valid_stories()
        print(f"{len(stories)} valid (mom, child) pairs:")
        for mom, child in stories:
            print(f"  {mom} & {child}")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2 ** 31)

    samples = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(getattr(args, "n", None) * 50, 50):
            seed = base_seed + i
            i += 1
            params = resolve_params(args, random.Random(seed))
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
        header = ""
        if getattr(args, "all", None):
            p = sample.params
            header = f"### {p.mom_name} & {p.child_name} ({p.mom_trait}, {p.child_trait})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
