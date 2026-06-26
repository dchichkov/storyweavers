#!/usr/bin/env python3
"""
storyworlds/worlds/hand_pl_dim_feat_transformation_animal_story.py
===================================================================

A small animal-story world about a surprising Transformation: a young animal,
a tricky feat, and a magical change that teaches care, courage, and belonging.

Seed words:
- hand-pl-dim
- feat

Style:
- Animal Story
- child-facing
- concrete, causal, and state-driven
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
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    plural: bool = False
    worn_by: Optional[str] = None
    carries: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"fox", "rabbit", "bunny", "deer", "squirrel", "bear", "mouse"}:
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
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
class Creature:
    type: str
    name: str
    trait: str
    size: str
    tail: str
    habitat: str
    feet: int
    hands: int
    ears: int
    nose: int
    color: str
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


@dataclass
class Charm:
    id: str
    label: str
    phrase: str
    effect: str
    target: str
    change: str
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
    creature: str
    charm: str
    feat: str
    name: str
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


CREATURES = {
    "rabbit": Creature("rabbit", "Pip", "curious", "small", "a fluffy tail", "meadow", 4, 2, 2, 1, "white"),
    "fox": Creature("fox", "Fenn", "clever", "small", "a bushy tail", "woodland", 4, 2, 2, 1, "red"),
    "bear": Creature("bear", "Moss", "gentle", "big", "a round tail", "forest", 4, 2, 2, 1, "brown"),
    "squirrel": Creature("squirrel", "Tiki", "quick", "small", "a curly tail", "oak tree", 4, 2, 2, 1, "gray"),
}

CHARMS = {
    "leaf": Charm("leaf", "a silver leaf", "a silver leaf that shimmered in moonlight", "grow", "up", "taller"),
    "shell": Charm("shell", "a tiny shell", "a tiny shell that glowed softly", "shrink", "down", "smaller"),
    "glowberry": Charm("glowberry", "a glowberry", "a warm glowberry that hummed like a song", "change", "shape", "different"),
}

FEATS = {
    "cross_stream": "cross the cold stream by stepping on stones",
    "reach_honey": "reach the honey high in the beehive tree",
    "dance_gate": "dance three turns to wake the sleepy garden gate",
    "fetch_star": "fetch the bright star-fruit from the highest branch",
}

GROWTH_REASON = {
    "cross_stream": "needed steadier feet to cross the stream",
    "reach_honey": "needed to reach high enough for the honey",
    "dance_gate": "wanted to be just the right size for the gate",
    "fetch_star": "needed longer arms to reach the fruit",
}


class World:
    def __init__(self, creature: Creature, charm: Charm, feat_key: str) -> None:
        self.creature = creature
        self.charm = charm
        self.feat_key = feat_key
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[str] = set()
        self.facts: dict[str, object] = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


def _entity_size_word(size: str) -> str:
    return {"small": "small", "big": "big", "tiny": "tiny"}[size]


def _feat_sentence(feat: str) -> str:
    return _safe_lookup(FEATS, feat)


def _transformation_goal(charm: Charm, feat: str) -> str:
    if feat == "cross_stream" and charm.id == "leaf":
        return "a little taller"
    if feat == "reach_honey" and charm.id == "leaf":
        return "tall enough to reach the honey"
    if feat == "dance_gate" and charm.id == "shell":
        return "smaller and lighter"
    if feat == "fetch_star" and charm.id == "leaf":
        return "tall enough to reach the star-fruit"
    return charm.change


def narrate_setup(world: World) -> None:
    c = world.creature
    world.say(
        f"{c.name} was a {c.trait} little {c.type} who lived in the {c.habitat}. "
        f"{c.name} liked small adventures and never wanted to miss a chance to try a new feat."
    )
    world.say(
        f"One day, {c.name} found {world.charm.phrase} resting on a mossy stone."
    )
    world.say(
        f"A tiny path of light pointed toward a place where {c.name} had to {_feat_sentence(world.feat_key)}."
    )


def narrate_need(world: World) -> None:
    c = world.creature
    reason = GROWTH_REASON[world.feat_key]
    world.say(
        f"{c.name} looked at the path and understood the problem right away: {reason}."
    )
    world.say(
        f"{c.name} held the charm in {c.name}'s paws and whispered, "
        f'"Please help me become {_transformation_goal(world.charm, world.feat_key)}."'
    )


def apply_transformation(world: World) -> None:
    c = world.creature
    if world.charm.effect == "grow":
        world.facts["before_size"] = c.size
        c.size = "big"
        world.facts["changed"] = "grown"
        world.say(
            f"The silver leaf warmed like a sunbeam. {c.name}'s ears lifted, "
            f"its legs lengthened, and its whole body stretched bigger and steadier."
        )
    elif world.charm.effect == "shrink":
        world.facts["before_size"] = c.size
        c.size = "tiny"
        world.facts["changed"] = "shrunk"
        world.say(
            f"The tiny shell gave a soft chime. {c.name} became smaller and lighter, "
            f"just right for slipping through the narrow places."
        )
    else:
        world.facts["before_size"] = c.size
        c.size = "small"
        world.say(
            f"The glowberry hummed, and {c.name} changed shape in a gentle swirl of light."
        )


def narrate_feat(world: World) -> None:
    c = world.creature
    if world.feat_key == "cross_stream":
        world.say(
            f"Then {c.name} stepped across the stream on the round stones, one careful paw at a time."
        )
        world.say(
            f"The water splashed below, but {c.name} stayed balanced and crossed safely to the other side."
        )
    elif world.feat_key == "reach_honey":
        world.say(
            f"Then {c.name} climbed the beehive tree and stretched high enough to reach the honey."
        )
        world.say(
            f"The sticky pot came free with a pop, and {c.name} smiled at the sweet smell."
        )
    elif world.feat_key == "dance_gate":
        world.say(
            f"Then {c.name} danced three quick turns before the sleepy garden gate."
        )
        world.say(
            f"The gate creaked open with a yawn, as if it liked the little performance."
        )
    elif world.feat_key == "fetch_star":
        world.say(
            f"Then {c.name} reached the highest branch and picked the star-fruit with one careful paw."
        )
        world.say(
            f"The bright fruit gleamed in the evening light, and the whole tree seemed to cheer."
        )


def narrate_end(world: World) -> None:
    c = world.creature
    world.say(
        f"When the feat was done, the charm's glow faded, but {c.name} kept the brave feeling inside."
    )
    world.say(
        f"{c.name} tucked the {world.charm.label} into a pocket of leaves and went home feeling proud."
    )


ASP_RULES = r"""
creature(X) :- has_creature(X).
charm(X) :- has_charm(X).
feat(X) :- has_feat(X).

needs_growth(F) :- feat(F), requires_growing(F).
needs_shrink(F) :- feat(F), requires_shrinking(F).

compatible(C, F) :- charm(C), feat(F), charm_grows(C), needs_growth(F).
compatible(C, F) :- charm(C), feat(F), charm_shrinks(C), needs_shrink(F).
compatible(C, F) :- charm(C), feat(F), charm_changes(C), generic_ok(C, F).

#show compatible/2.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for cid in CREATURES:
        lines.append(asp.fact("has_creature", cid))
    for ch in CHARMS.values():
        lines.append(asp.fact("has_charm", ch.id))
        if ch.effect == "grow":
            lines.append(asp.fact("charm_grows", ch.id))
        elif ch.effect == "shrink":
            lines.append(asp.fact("charm_shrinks", ch.id))
        else:
            lines.append(asp.fact("charm_changes", ch.id))
    for fid in FEATS:
        lines.append(asp.fact("has_feat", fid))
    lines.append(asp.fact("requires_growing", "cross_stream"))
    lines.append(asp.fact("requires_growing", "reach_honey"))
    lines.append(asp.fact("requires_shrinking", "dance_gate"))
    lines.append(asp.fact("requires_growing", "fetch_star"))
    lines.append(asp.fact("generic_ok", "glowberry", "dance_gate"))
    return "\n".join(lines)


def asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n"


def asp_compatible() -> set[tuple[str, str]]:
    import asp

    model = asp.one_model(asp_program())
    return set(asp.atoms(model, "compatible"))


def py_compatible() -> set[tuple[str, str]]:
    out: set[tuple[str, str]] = set()
    for ch in CHARMS.values():
        for feat in FEATS:
            if ch.effect == "grow" and feat in {"cross_stream", "reach_honey", "fetch_star"}:
                out.add((ch.id, feat))
            elif ch.effect == "shrink" and feat == "dance_gate":
                out.add((ch.id, feat))
            elif ch.effect == "change" and feat == "dance_gate":
                out.add((ch.id, feat))
    return out


def asp_verify() -> int:
    a, p = asp_compatible(), py_compatible()
    if a == p:
        print(f"OK: clingo parity matches Python gate ({len(a)} compatible pairs).")
        return 0
    print("MISMATCH between clingo and Python gate:")
    if a - p:
        print("  only in clingo:", sorted(a - p))
    if p - a:
        print("  only in python:", sorted(p - a))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal transformation story world.")
    ap.add_argument("--creature", choices=CREATURES)
    ap.add_argument("--charm", choices=CHARMS)
    ap.add_argument("--feat", choices=FEATS)
    ap.add_argument("--name")
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
    if getattr(args, "feat", None) and getattr(args, "charm", None):
        pair = (getattr(args, "charm", None), getattr(args, "feat", None))
        if pair not in py_compatible():
            return _fallback_storyparams(args, rng, StoryParams, globals())
    candidates = []
    for feat in FEATS:
        if getattr(args, "feat", None) and feat != getattr(args, "feat", None):
            continue
        for charm in CHARMS:
            if getattr(args, "charm", None) and charm != getattr(args, "charm", None):
                continue
            if (charm, feat) not in py_compatible():
                continue
            candidates.append((charm, feat))
    if not candidates:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    charm, feat = rng.choice(sorted(candidates))
    creature = getattr(args, "creature", None) or rng.choice(sorted(CREATURES))
    name = getattr(args, "name", None) or _safe_lookup(CREATURES, creature).name
    return StoryParams(creature=creature, charm=charm, feat=feat, name=name)


def generate(params: StoryParams) -> StorySample:
    creature = _safe_lookup(CREATURES, params.creature)
    charm = _safe_lookup(CHARMS, params.charm)
    world = World(creature, charm, params.feat)
    narrate_setup(world)
    world.para()
    narrate_need(world)
    apply_transformation(world)
    narrate_feat(world)
    world.para()
    narrate_end(world)
    world.facts.update(
        creature=creature,
        charm=charm,
        feat=params.feat,
        changed=world.facts.get("changed", ""),
        before_size=world.facts.get("before_size", creature.size),
    )
    story_qa = [
        QAItem(
            question=f"Who is the story about?",
            answer=f"It is about {creature.name}, a {creature.trait} little {creature.type} from the {creature.habitat}.",
        ),
        QAItem(
            question=f"What magical thing did {creature.name} find?",
            answer=f"{creature.name} found {charm.phrase}, which helped with the feat in the story.",
        ),
        QAItem(
            question=f"What feat did {creature.name} try to do?",
            answer=f"{creature.name} tried to {_feat_sentence(params.feat)}.",
        ),
        QAItem(
            question=f"What changed about {creature.name} after the magic?",
            answer=(
                f"{creature.name} changed from {world.facts['before_size']} to {creature.size} "
                f"so {creature.pronoun('subject')} could finish the feat."
            ),
        ),
    ]
    world_qa = [
        QAItem(
            question="What is a transformation?",
            answer="A transformation is when something changes into a different form or size.",
        ),
        QAItem(
            question="Why might an animal need to grow bigger?",
            answer="An animal might need to grow bigger to reach something high or stand more steadily.",
        ),
        QAItem(
            question="Why might an animal need to become smaller?",
            answer="An animal might need to become smaller to fit through a narrow place or move carefully.",
        ),
    ]
    prompts = [
        f"Write a gentle animal story about {creature.name} and a magical transformation.",
        f"Tell a short story where a little {creature.type} tries to {_feat_sentence(params.feat)}.",
        f"Make a child-friendly story with a clear change, a brave attempt, and a happy ending.",
    ]
    return StorySample(params=params, story=world.render(), prompts=prompts, story_qa=story_qa, world_qa=world_qa, world=world)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    c = world.creature
    lines.append(f"creature={c.name} type={c.type} size={c.size} trait={c.trait}")
    lines.append(f"charm={world.charm.id} effect={world.charm.effect}")
    lines.append(f"feat={world.feat_key}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== story qa ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


CURATED = [
    StoryParams(creature="rabbit", charm="leaf", feat="cross_stream", name="Pip"),
    StoryParams(creature="fox", charm="leaf", feat="fetch_star", name="Fenn"),
    StoryParams(creature="squirrel", charm="shell", feat="dance_gate", name="Tiki"),
    StoryParams(creature="bear", charm="leaf", feat="reach_honey", name="Moss"),
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
        print(asp_program())
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp

        print(sorted(asp_compatible()))
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
            try:
                params = resolve_params(args, random.Random(seed))
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
        header = f"### variant {i+1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
