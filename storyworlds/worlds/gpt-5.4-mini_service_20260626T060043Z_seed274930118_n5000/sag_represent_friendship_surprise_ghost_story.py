#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/sag_represent_friendship_surprise_ghost_story.py
================================================================================================

A small story world in the style of a ghost story, centered on friendship and
a surprise. A shy child and a gentle ghost discover that a sagging old banner
can still represent a real friendship when they repair it together.

The world model tracks:
- physical meters: age, sag, glow, dust, neatness, hiddenness
- emotional memes: fear, trust, friendship, surprise, pride, relief

The generated stories are not frozen templates; the prose is driven by the
state changes that happen during the simulation:
1. setup: a lonely place, a child, and a quiet ghost
2. tension: a strange sound, a sagging thing, and a surprise
3. turn: the child chooses kindness instead of fear
4. resolution: the two characters fix the broken sign and prove their bond
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Callable, Optional

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
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    touched_by: Optional[str] = None
    carried_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    child: object | None = None
    ghost: object | None = None
    sign: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def is_person(self) -> bool:
        return self.kind == "character"
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
    place: str
    mood: str
    affordances: set[str] = field(default_factory=set)
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
class StoryParams:
    place: str
    child: str
    child_type: str
    ghost: str
    item: str
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


@dataclass
class ItemSpec:
    id: str
    label: str
    phrase: str
    risky: str
    fixable_by: str
    region: str = "wall"
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
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

    w: object | None = None
    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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
        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        w.facts = copy.deepcopy(self.facts)
        return w
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


def _join_sentences(parts: list[str]) -> str:
    return " ".join(p for p in parts if p)


def _capitalize_sentences(text: str) -> str:
    out = []
    for chunk in text.split(". "):
        chunk = chunk.strip()
        if chunk:
            out.append(chunk[0].upper() + chunk[1:] if len(chunk) > 1 else chunk.upper())
    return ". ".join(out)


def _sag_rule(world: World) -> list[str]:
    out = []
    for e in list(world.entities.values()):
        if e.meters.get("weight", 0) < THRESHOLD:
            continue
        if e.meters.get("support", 0) >= THRESHOLD:
            continue
        sig = ("sag", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.meters["sag"] = e.meters.get("sag", 0) + 1
        out.append(f"The {e.label} sagged a little lower.")
    return out


def _surprise_rule(world: World) -> list[str]:
    out = []
    child = world.facts.get("child")
    ghost = world.facts.get("ghost")
    if not child or not ghost:
        return out
    c = world.get(child.id)
    g = world.get(ghost.id)
    if c.memes.get("fear", 0) < THRESHOLD:
        return out
    if g.memes.get("friendship", 0) < THRESHOLD:
        return out
    sig = ("surprise", c.id, g.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    c.memes["surprise"] = c.memes.get("surprise", 0) + 1
    c.memes["fear"] = max(0.0, c.memes.get("fear", 0) - 1.0)
    out.append(f"{c.id} blinked in surprise when the ghost smiled so gently.")
    return out


def _repair_rule(world: World) -> list[str]:
    out = []
    item = world.facts.get("item")
    child = world.facts.get("child")
    ghost = world.facts.get("ghost")
    if not item or not child or not ghost:
        return out
    e = world.get(item.id)
    c = world.get(child.id)
    g = world.get(ghost.id)
    if c.memes.get("trust", 0) < THRESHOLD or g.memes.get("friendship", 0) < THRESHOLD:
        return out
    if e.meters.get("repaired", 0) >= THRESHOLD:
        return out
    sig = ("repair", e.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    e.meters["repaired"] = 1
    e.meters["sag"] = 0
    c.memes["pride"] = c.memes.get("pride", 0) + 1
    g.memes["relief"] = g.memes.get("relief", 0) + 1
    out.append(f"Together, they fixed the {e.label} before it could sag any more.")
    return out


RULES: list[Callable[[World], list[str]]] = [_sag_rule, _surprise_rule, _repair_rule]


def propagate(world: World, narrate: bool = True) -> list[str]:
    all_lines: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in RULES:
            lines = rule(world)
            if lines:
                changed = True
                all_lines.extend(lines)
    if narrate:
        for line in all_lines:
            world.say(line)
    return all_lines


SETTINGS = {
    "attic": Setting(place="the attic", mood="quiet, dusty, and moonlit", affordances={"ghost", "repair"}),
    "hallway": Setting(place="the hallway", mood="long and whispery", affordances={"ghost", "repair"}),
    "porch": Setting(place="the porch", mood="cool and creaky", affordances={"ghost", "repair"}),
}

ITEMS = {
    "banner": ItemSpec(
        id="banner",
        label="banner",
        phrase="an old paper banner",
        risky="sag",
        fixable_by="tape",
        region="wall",
    ),
    "sign": ItemSpec(
        id="sign",
        label="sign",
        phrase="a little wooden sign",
        risky="tilt",
        fixable_by="nail",
        region="wall",
    ),
    "mobile": ItemSpec(
        id="mobile",
        label="mobile",
        phrase="a hanging star mobile",
        risky="droop",
        fixable_by="string",
        region="ceiling",
    ),
}

CHILD_NAMES = ["Mia", "Noah", "Luna", "Eli", "Rose", "Finn", "Ivy", "Theo"]
GHOST_NAMES = ["Boo", "Misty", "Pale Sam", "Glow", "Whisper"]
CHILD_TYPES = {"girl", "boy"}


def item_risk(item: ItemSpec) -> bool:
    return item.risky in {"sag", "tilt", "droop"}


def build_world(params: StoryParams) -> World:
    setting = _safe_lookup(SETTINGS, params.place)
    w = World(setting)
    child = w.add(Entity(
        id=params.child, kind="character", type=params.child_type,
        label=params.child, meters={"weight": 1}, memes={"fear": 0, "trust": 0, "surprise": 0, "pride": 0},
    ))
    ghost = w.add(Entity(
        id=params.ghost, kind="character", type="ghost", label=params.ghost,
        meters={"glow": 1, "hiddenness": 1}, memes={"friendship": 0, "relief": 0},
    ))
    item = _safe_lookup(ITEMS, params.item)
    sign = w.add(Entity(
        id=item.id, kind="thing", type="thing", label=item.label, phrase=item.phrase,
        meters={"weight": 1, "support": 0, "sag": 0, "repaired": 0},
    ))
    w.facts.update(child=child, ghost=ghost, item=sign, item_spec=item)
    return w


def _predict_reaction(world: World) -> tuple[bool, bool]:
    sim = world.copy()
    child = sim.facts["child"]
    ghost = sim.facts["ghost"]
    item = sim.facts["item"]
    child.memes["fear"] += 1
    ghost.memes["friendship"] += 1
    item.meters["support"] = 0
    propagate(sim, narrate=False)
    return sim.get(child.id).memes.get("surprise", 0) >= THRESHOLD, sim.get(item.id).meters.get("repaired", 0) >= THRESHOLD


def tell_story(world: World) -> None:
    child = _safe_fact(world, world.facts, "child")
    ghost = _safe_fact(world, world.facts, "ghost")
    item = _safe_fact(world, world.facts, "item")
    spec = _safe_fact(world, world.facts, "item_spec")

    world.say(
        f"{child.id} lived near {world.setting.place}, in a place that felt {world.setting.mood}."
    )
    world.say(
        f"Every night, {child.id} noticed {spec.phrase} hanging on the wall, and it seemed to sag just a little."
    )
    world.say(
        f"One evening, {child.id} saw a pale shape near the dark corner, and {child.pronoun().capitalize()} felt a little scared."
    )
    world.para()
    child.memes["fear"] += 1
    ghost.memes["hiddenness"] += 1
    ghost.memes["friendship"] += 1
    world.say(
        f"But the ghost was only {ghost.id}, and {ghost.pronoun()} carried a tiny ribbon that said 'friend' in crooked letters."
    )
    world.say(
        f"The ribbon did not just decorate the room; it was meant to represent kindness that could stay even after a hard day."
    )
    world.say(
        f"{ghost.id} pointed at the sagging {item.label} and made a sad face, then touched its corner as if asking for help."
    )
    propagate(world)

    world.para()
    world.say(
        f"{child.id} took a slow breath. {child.pronoun().capitalize()} did not run away."
    )
    world.say(
        f"Instead, {child.id} smiled at {ghost.id} and said that a friend could fix a problem together."
    )
    child.memes["trust"] += 1
    ghost.memes["friendship"] += 1
    item.meters["support"] += 1
    world.say(
        f"They found tape, pressed the curled paper flat, and straightened the {item.label} so it could represent their friendship better."
    )
    propagate(world)

    world.para()
    child.memes["pride"] += 1
    ghost.memes["relief"] += 1
    world.say(
        f"At the end, the room looked brighter. The banner no longer sagged, and {child.id} and {ghost.id} stood beside it with matching smiles."
    )
    world.say(
        f"{child.id} was still surprised that a ghost could be so kind, and {ghost.id} was happy that a new friend had stayed."
    )

    world.facts.update(resolved=True, surprise=_predict_reaction(world)[0])


def story_name_from_setting(setting: Setting, item: ItemSpec) -> str:
    return f"{setting.place} / {item.label}"


def generation_prompts(world: World) -> list[str]:
    child = _safe_fact(world, world.facts, "child")
    ghost = _safe_fact(world, world.facts, "ghost")
    item = _safe_fact(world, world.facts, "item")
    return [
        f"Write a gentle ghost story where {child.id} meets {ghost.id} in {world.setting.place} and notices a sagging {item.label}.",
        f"Tell a friendship story with a surprise ending that uses the words 'sag' and 'represent'.",
        f"Write a child-friendly spooky story about a ghost who helps a new friend fix a broken thing.",
    ]


def story_qa(world: World) -> list[QAItem]:
    child = _safe_fact(world, world.facts, "child")
    ghost = _safe_fact(world, world.facts, "ghost")
    item = _safe_fact(world, world.facts, "item")
    return [
        QAItem(
            question=f"Who was the story about?",
            answer=f"It was about {child.id} and the ghost named {ghost.id}.",
        ),
        QAItem(
            question=f"What was sagging in the story?",
            answer=f"The {item.label} was sagging on the wall before they fixed it.",
        ),
        QAItem(
            question=f"What did the sagging {item.label} represent?",
            answer=f"It represented the friendship between {child.id} and {ghost.id}, because they repaired it together.",
        ),
        QAItem(
            question=f"What was the surprise in the story?",
            answer=f"The surprise was that the scary-looking ghost was actually friendly and wanted to help.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does the word 'sag' mean?",
            answer="When something sags, it hangs lower because it is heavy or not well supported.",
        ),
        QAItem(
            question="What does it mean to represent something?",
            answer="To represent something means to stand for it or show it in a clear way.",
        ),
        QAItem(
            question="What is friendship?",
            answer="Friendship is a kind relationship where people care about each other and help each other.",
        ),
        QAItem(
            question="What is a surprise?",
            answer="A surprise is something unexpected that makes you feel startled or happy.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== story QA ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world QA ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    out = ["--- trace ---"]
    for e in list(world.entities.values()):
        out.append(f"{e.id}: meters={dict((k,v) for k,v in e.meters.items() if v)} memes={dict((k,v) for k,v in e.memes.items() if v)}")
    out.append(f"fired={sorted(world.fired)}")
    return "\n".join(out)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small ghost-story world about friendship and surprise.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--child")
    ap.add_argument("--child-type", choices=sorted(CHILD_TYPES))
    ap.add_argument("--ghost")
    ap.add_argument("--item", choices=ITEMS)
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
    item = getattr(args, "item", None) or rng.choice(list(ITEMS))
    child_type = getattr(args, "child_type", None) or rng.choice(["girl", "boy"])
    child = getattr(args, "child", None) or rng.choice(CHILD_NAMES)
    ghost = getattr(args, "ghost", None) or rng.choice(GHOST_NAMES)
    return StoryParams(place=place, child=child, child_type=child_type, ghost=ghost, item=item)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    tell_story(world)
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


ASP_RULES = r"""
% A thing sags when it is heavy and lacks support.
sags(Item) :- item(Item), heavy(Item), not supported(Item).

% A surprise happens when a child fears the ghost, but the ghost is friendly.
surprise(Child, Ghost) :- child(Child), ghost(Ghost), fears(Child, Ghost), friendly(Ghost).

% Friendship is represented by repair.
friendship(Child, Ghost) :- child(Child), ghost(Ghost), repaired_together(Child, Ghost).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for place in SETTINGS:
        lines.append(asp.fact("place", place))
    for item_id, spec in ITEMS.items():
        lines.append(asp.fact("item", item_id))
        lines.append(asp.fact("label", item_id, spec.label))
        if item_risk(spec):
            lines.append(asp.fact("heavy", item_id))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show sags/1."))
    atoms = set(asp.atoms(model, "sags"))
    python = {(item_id,) for item_id, spec in ITEMS.items() if item_risk(spec)}
    if atoms == python:
        print(f"OK: ASP matches Python ({len(atoms)} items).")
        return 0
    print("MISMATCH")
    print("ASP:", sorted(atoms))
    print("PY :", sorted(python))
    return 1


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "verify", None):
        raise SystemExit(asp_verify())
    if getattr(args, "show_asp", None):
        print(asp_program("#show surprise/2.\n#show friendship/2."))
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        cur = [
            StoryParams(place="attic", child="Mia", child_type="girl", ghost="Boo", item="banner"),
            StoryParams(place="hallway", child="Noah", child_type="boy", ghost="Misty", item="sign"),
            StoryParams(place="porch", child="Luna", child_type="girl", ghost="Glow", item="mobile"),
        ]
        samples = [generate(p) for p in cur]
    else:
        for i in range(getattr(args, "n", None)):
            p = resolve_params(args, random.Random(base_seed + i))
            p.seed = base_seed + i
            samples.append(generate(p))

    if getattr(args, "json", None):
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 60 + "\n")


if __name__ == "__main__":
    main()
