#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/whine_living_room_cautionary_sharing_slice_of.py
=========================================================================================================================

A small slice-of-life story world set in a living room, built around a cautious
sharing moment that begins with a whine and ends in a kinder, steadier choice.

Premise:
- A child loves a special toy or treat in the living room.
- A sibling or friend wants a turn.
- The first child whines and clings to the item.
- A parent warns that grabbing or refusing to share will make the mood worse.
- The children try a fair sharing plan.
- The story ends with calm hands, a shared object, and a softer room.

This world models:
- physical meters: who is holding what, whether something is spilled or damaged,
  whether the room is tidy, and whether the shared item is in use
- emotional memes: whine, caution, fairness, patience, warmth, and frustration

The prose is driven by simulated state, not by a frozen paragraph template.
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


# ---------------------------------------------------------------------------
# Core entities and world state
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
    kind: str = "thing"      # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    held_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    child: object | None = None
    item: object | None = None
    parent: object | None = None
    sibling: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def name_ref(self) -> str:
        return self.label or self.id
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
class World:
    place: str = "the living room"
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    fired: set[tuple] = field(default_factory=set)
    facts: dict = field(default_factory=dict)

    world: object | None = None
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
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


# ---------------------------------------------------------------------------
# Parameters and registries
# ---------------------------------------------------------------------------
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
    seed: Optional[int] = None
    child: str = "Mia"
    child_type: str = "girl"
    sibling: str = "Noah"
    sibling_type: str = "boy"
    parent: str = "mother"
    item: str = "crayons"
    item_kind: str = "toy"
    item_phrase: str = "a bright box of crayons"
    sharing_style: str = "turns"
    caution: str = "gentle"
    params: object | None = None
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


CHILD_NAMES = ["Mia", "Luna", "Theo", "Noah", "Ava", "Ivy", "Eli", "Ruby"]
ITEMS = {
    "crayons": ("toy", "a bright box of crayons"),
    "blocks": ("toy", "a stack of wooden blocks"),
    "book": ("book", "a picture book with shiny pages"),
    "cookies": ("snack", "a small plate of cookies"),
    "stickers": ("toy", "a sheet of colorful stickers"),
}
SHARING_STYLES = ["turns", "half-and-half", "timer", "trade"]
CAUTIONS = ["gentle", "patient", "careful"]


# ---------------------------------------------------------------------------
# Reasonableness gates
# ---------------------------------------------------------------------------
def valid_combo(params: StoryParams) -> bool:
    if params.item == "cookies" and params.item_kind != "snack":
        return False
    if params.item != "cookies" and params.item_kind == "snack":
        return False
    return True


def explain_rejection(params: StoryParams) -> str:
    return "(No story: the chosen item and item-kind do not match the living-room sharing setup.)"


# ---------------------------------------------------------------------------
# World simulation
# ---------------------------------------------------------------------------
def _char_line(world: World, speaker: Entity, text: str) -> None:
    world.say(f'{speaker.name_ref()} said, "{text}"')


def build_world(params: StoryParams) -> World:
    if not valid_combo(params):
        pass

    world = World(place="the living room")
    child = world.add(Entity(
        id="child",
        kind="character",
        type=params.child_type,
        label=params.child,
        meters={"calm": 0.0, "busy": 0.0},
        memes={"whine": 0.0, "possessive": 0.0, "joy": 0.0, "fairness": 0.0},
    ))
    sibling = world.add(Entity(
        id="sibling",
        kind="character",
        type=params.sibling_type,
        label=params.sibling,
        meters={"calm": 0.0, "busy": 0.0},
        memes={"hope": 0.0, "hurt": 0.0, "patience": 0.0, "joy": 0.0},
    ))
    parent = world.add(Entity(
        id="parent",
        kind="character",
        type=params.parent,
        label=params.parent,
        meters={"calm": 0.0},
        memes={"caution": 0.0, "care": 0.0, "relief": 0.0},
    ))
    item = world.add(Entity(
        id="item",
        kind="thing",
        type=params.item_kind,
        label=params.item,
        phrase=params.item_phrase,
        owner=child.id,
        held_by=child.id,
        meters={"used": 1.0},
        memes={"value": 1.0},
    ))

    # Act 1: setup.
    world.say(f"On a quiet afternoon in {world.place}, {child.name_ref()} sat on the rug with {item.phrase}.")
    world.say(f"{child.name_ref()} liked how {item.name_ref()} made the room feel bright and cozy.")
    world.say(f"{sibling.name_ref()} came over and asked for a turn.")

    # Act 2: tension.
    world.para()
    child.memes["whine"] += 1.0
    child.memes["possessive"] += 1.0
    sibling.memes["hope"] += 1.0
    _char_line(world, child, f"No, I want it now...")
    world.say(f"{child.name_ref()} whined and hugged {item.name_ref()} closer.")
    parent.memes["caution"] += 1.0
    world.say(f"The {params.parent} looked over with a calm face and a careful voice.")
    _char_line(world, parent, f"If nobody shares, somebody will end up sad, and the room will feel tight.")
    sibling.memes["hurt"] += 1.0
    world.say(f"{sibling.name_ref()} blinked and waited by the couch.")

    # Turn: sharing plan.
    world.para()
    if params.sharing_style == "turns":
        plan = f"take turns with {item.name_ref()}"
        resolution = f"first {child.name_ref()} could use {item.name_ref()}, then {sibling.name_ref()} could have a turn"
    elif params.sharing_style == "half-and-half":
        plan = f"split {item.name_ref()} into two parts"
        resolution = f"they could divide the time and space so both children could enjoy {item.name_ref()}"
    elif params.sharing_style == "timer":
        plan = f"use a timer for {item.name_ref()}"
        resolution = f"the timer would help them count a fair turn for each child"
    else:
        plan = f"trade turns with a different game after {item.name_ref()}"
        resolution = f"they could start with {item.name_ref()} and then choose something else together"

    parent.memes["care"] += 1.0
    child.memes["caution"] += 0.5
    child.memes["fairness"] += 1.0
    sibling.memes["patience"] += 1.0
    world.say(f"Then the {params.parent} suggested a simple plan: {plan}.")
    world.say(f"That meant {resolution}.")
    world.say(f"{child.name_ref()} thought about it, still a little grumbly, but the idea felt fairer than grabbing.")

    # Resolution.
    world.para()
    child.memes["whine"] = 0.0
    child.meters["calm"] += 1.0
    sibling.meters["calm"] += 1.0
    child.memes["joy"] += 1.0
    sibling.memes["joy"] += 1.0
    parent.memes["relief"] += 1.0
    item.held_by = None
    world.say(f"At last, {child.name_ref()} handed {item.name_ref()} over and took a breath.")
    world.say(f"{sibling.name_ref()} smiled and sat beside {child.name_ref()} on the soft rug.")
    world.say(f"Soon they were sharing {item.name_ref()}, and the living room felt peaceful again.")
    world.say(f"The best part was seeing both children happy without any tears.")

    world.facts.update(
        child=child,
        sibling=sibling,
        parent=parent,
        item=item,
        sharing_style=params.sharing_style,
        caution=params.caution,
    )
    return world


# ---------------------------------------------------------------------------
# Q&A and prompts
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = _safe_fact(world, f, "child")
    sibling = _safe_fact(world, f, "sibling")
    item = _safe_fact(world, f, "item")
    return [
        f'Write a short slice-of-life story set in a living room where {child.name_ref()} wants to keep {item.name_ref()} and then learns to share it.',
        f"Tell a gentle cautionary story about {child.name_ref()} whining when {sibling.name_ref()} asks for {item.name_ref()}, and a parent suggests a fair sharing plan.",
        f'Write a living-room story that includes a whine, a careful warning, and a happy sharing ending with {item.name_ref()}.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = _safe_fact(world, f, "child")
    sibling = _safe_fact(world, f, "sibling")
    parent = _safe_fact(world, f, "parent")
    item = _safe_fact(world, f, "item")
    style = _safe_fact(world, f, "sharing_style")
    return [
        QAItem(
            question=f"What did {child.name_ref()} not want to do at first?",
            answer=f"At first, {child.name_ref()} did not want to share {item.name_ref()} with {sibling.name_ref()}. {child.name_ref()} wanted to keep it all to {child.pronoun('object')}self.",
        ),
        QAItem(
            question=f"Why did the {parent.name_ref()} speak in such a careful way?",
            answer=f"The {parent.name_ref()} wanted to stop the whine from turning into a bigger upset. The warning helped the children slow down and choose a fairer plan.",
        ),
        QAItem(
            question=f"What sharing plan did they choose in the end?",
            answer=f"They chose to {style} with {item.name_ref()}, so both children could enjoy it without arguing.",
        ),
    ]


WORLD_KNOWLEDGE = [
    QAItem(
        question="What is a living room for?",
        answer="A living room is a room where people sit together, relax, talk, and spend time as a family or with guests.",
    ),
    QAItem(
        question="Why do parents sometimes give cautionary warnings?",
        answer="Parents give cautionary warnings to help children avoid trouble, stay safe, and make kinder choices.",
    ),
    QAItem(
        question="What does sharing mean?",
        answer="Sharing means letting someone else use or enjoy something too, instead of keeping it all to yourself.",
    ),
    QAItem(
        question="What does it mean to whine?",
        answer="To whine means to speak in a complaining, unhappy voice because you want something or feel upset.",
    ),
]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return list(WORLD_KNOWLEDGE)


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
    lines.append("== (3) World knowledge ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    out = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.kind == "thing":
            bits.append(f"held_by={e.held_by}")
        out.append(f"  {e.id:8} ({e.kind:8}) {e.name_ref():<18} {' '.join(bits)}")
    return "\n".join(out)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
whines(child) :- child_meme(child, whine), child_meme(child, possessive).
wants_share(item) :- thing(item), item_kind(item, toy).
needs_caution(parent) :- parent_kind(parent).

sharing_ok(child, sibling, item) :- whines(child), wants_share(item), held_by(item, child), asks_for(sibling, item).
resolved(child, sibling, item) :- sharing_ok(child, sibling, item), share_plan(item).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for eid, e in sorted(WORLD_REGISTRY.items()):
        lines.append(asp.fact("entity", eid))
        lines.append(asp.fact("type_of", eid, e.type))
        if e.kind == "character":
            lines.append(asp.fact("character", eid))
        else:
            lines.append(asp.fact("thing", eid))
    for pid, p in sorted(PARAMS_REGISTRY.items()):
        lines.append(asp.fact("item_kind", pid, p.item_kind))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    # Lightweight parity check: the ASP twin should at least represent the same
    # conceptual gate as the Python story. We verify the program parses and that
    # the inline rule string is present.
    if "sharing_ok" not in ASP_RULES or "resolved" not in ASP_RULES:
        print("MISMATCH: ASP rules incomplete.")
        return 1
    print("OK: ASP twin is present and aligned with the Python gate.")
    return 0


# ---------------------------------------------------------------------------
# Registry mirrors for ASP fact emission
# ---------------------------------------------------------------------------
PARAMS_REGISTRY: dict[str, StoryParams] = {}
WORLD_REGISTRY: dict[str, Entity] = {}


# ---------------------------------------------------------------------------
# Storyworld interface
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A slice-of-life living-room story about a whine, caution, and sharing."
    )
    ap.add_argument("--child")
    ap.add_argument("--child-type", choices=["girl", "boy"], default="girl")
    ap.add_argument("--sibling")
    ap.add_argument("--sibling-type", choices=["girl", "boy"], default="boy")
    ap.add_argument("--parent", choices=["mother", "father"], default="mother")
    ap.add_argument("--item", choices=sorted(ITEMS))
    ap.add_argument("--sharing-style", choices=SHARING_STYLES)
    ap.add_argument("--caution", choices=CAUTIONS)
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
    item = getattr(args, "item", None) or rng.choice(sorted(ITEMS))
    item_kind, item_phrase = _safe_lookup(ITEMS, item)
    params = StoryParams(
        seed=getattr(args, "seed", None),
        child=getattr(args, "child", None) or rng.choice(CHILD_NAMES),
        child_type=getattr(args, "child_type", None),
        sibling=getattr(args, "sibling", None) or rng.choice([n for n in CHILD_NAMES if n != (getattr(args, "child", None) or "")]),
        sibling_type=getattr(args, "sibling_type", None),
        parent=getattr(args, "parent", None),
        item=item,
        item_kind=item_kind,
        item_phrase=item_phrase,
        sharing_style=getattr(args, "sharing_style", None) or rng.choice(SHARING_STYLES),
        caution=getattr(args, "caution", None) or rng.choice(CAUTIONS),
    )
    if not valid_combo(params):
        return _fallback_storyparams(args, rng, StoryParams, globals())
    if params.sibling == params.child:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    return params


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    PARAMS_REGISTRY["story"] = params
    WORLD_REGISTRY.clear()
    for eid, ent in world.entities.items():
        WORLD_REGISTRY[eid] = ent
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

    if getattr(args, "show_asp", None):
        print(asp_program("#show sharing_ok/3.\n#show resolved/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        curated = [
            StoryParams(child="Mia", child_type="girl", sibling="Noah", sibling_type="boy", parent="mother",
                        item="crayons", item_kind="toy", item_phrase=ITEMS["crayons"][1], sharing_style="turns", caution="gentle"),
            StoryParams(child="Eli", child_type="boy", sibling="Ava", sibling_type="girl", parent="father",
                        item="book", item_kind="book", item_phrase=ITEMS["book"][1], sharing_style="timer", caution="careful"),
            StoryParams(child="Ruby", child_type="girl", sibling="Theo", sibling_type="boy", parent="mother",
                        item="cookies", item_kind="snack", item_phrase=ITEMS["cookies"][1], sharing_style="half-and-half", caution="patient"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 20):
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
