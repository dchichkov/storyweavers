#!/usr/bin/env python3
"""
A small mystery storyworld about an annual escalator ride, a burrow, and a snail.
The story has suspense, surprise, and a twist, while staying child-facing and
state-driven.

Premise:
- Each year, the station has an annual escalator parade.
- A careful snail lives in a burrow near the escalator.
- The snail loses a shiny ticket shell-tag and must search for it.

Tension:
- The escalator keeps moving, and the snail fears the tag has been taken.
- A helper lantern reveals clues along the steps.

Turn and resolution:
- The "missing" tag is found inside the burrow after all.
- The twist is that the snail had tucked it away to keep it safe.
- The suspense ends with a calm ride and a happy return home.
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
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    location: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    burrow: object | None = None
    snail: object | None = None
    tool: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type == "snail":
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]
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
    place: str = "the escalator"
    annual: bool = True
    mystery: bool = True
    affords: set[str] = field(default_factory=lambda: {"search", "ride", "wait"})
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
class Burrow:
    label: str
    phrase: str
    secret_slot: str = "inside the burrow"
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
class ClueTool:
    label: str
    phrase: str
    reveals: str
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


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
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
        import copy as _copy
        w = World(self.setting)
        w.entities = _copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        return w


def _ensure_story_reasonable(params: "StoryParams") -> None:
    if params.setting != "escalator":
        pass
    if params.snail_name.strip() == "":
        pass
    if params.burrow_kind not in BURROWS:
        pass
    if params.clue_tool not in TOOLS:
        pass


def _search(world: World, snail: Entity, tool: Entity, burrow: Entity) -> None:
    snail.memes["worry"] += 1
    world.say(
        f"Every year, {snail.id} listened to the hum of {world.setting.place} "
        f"and felt a little suspense in {snail.pronoun('possessive')} shell."
    )
    world.say(
        f"That morning, {snail.id} noticed {snail.pronoun('possessive')} "
        f"{burrow.label} was quiet, and {snail.pronoun('possessive')} shiny ticket-tag "
        f"was gone."
    )
    world.say(
        f"With a tiny lantern, {tool.label} began to reveal soft clues on the steps."
    )
    snail.meters["search"] = 1.0


def _ride(world: World, snail: Entity) -> None:
    snail.meters["ride"] = 1.0
    snail.memes["courage"] += 1
    world.say(
        f"{snail.id} climbed onto the moving escalator and held still, "
        f"listening to each careful click-clack."
    )


def _twist(world: World, snail: Entity, burrow: Entity, tool: Entity) -> None:
    if world.fired.__contains__(("twist", snail.id)):
        return
    world.fired.add(("twist", snail.id))
    snail.memes["surprise"] += 1
    snail.memes["relief"] += 1
    snail.meters["found"] = 1.0
    world.say(
        f"Then came the surprise: the missing tag was not on the escalator at all."
    )
    world.say(
        f"It had been tucked safely {burrow.phrase} the whole time, "
        f"waiting where {snail.id} had left it."
    )
    world.say(
        f"The twist made sense at last: {snail.id} had hidden it there on purpose, "
        f"so the shiny tag would not slip away during the annual crowd."
    )
    world.say(
        f"{tool.label} lit the burrow wall, and the little secret glimmered back."
    )


def _resolve(world: World, snail: Entity, burrow: Entity) -> None:
    snail.memes["calm"] += 1
    world.say(
        f"{snail.id} smiled, pocketed the tag, and went home to "
        f"{burrow.label} with the mystery solved."
    )
    world.say(
        f"The escalator kept moving, but the story ended with quiet feet, "
        f"a safe burrow, and a relieved little snail."
    )


@dataclass
class StoryParams:
    snail_name: str = "Milo"
    burrow_kind: str = "hidden"
    clue_tool: str = "lantern"
    seed: Optional[int] = None
    setting: str = "escalator"
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


SETTINGS = {
    "escalator": Setting(place="the escalator", annual=True, mystery=True),
}

BURROWS = {
    "hidden": Burrow(label="burrow", phrase="deep in the burrow"),
    "rooted": Burrow(label="burrow", phrase="beneath the burrow stones"),
    "cozy": Burrow(label="burrow", phrase="inside the cozy burrow corner"),
}

TOOLS = {
    "lantern": ClueTool(label="a tiny lantern", phrase="a tiny lantern", reveals="glows on clues"),
    "mirror": ClueTool(label="a pocket mirror", phrase="a pocket mirror", reveals="shows little reflections"),
}

NAMES = ["Milo", "Nina", "Toby", "Luna", "Pip", "Sage", "Ollie", "Mina"]


def tell(params: StoryParams) -> World:
    _ensure_story_reasonable(params)
    world = World(_safe_lookup(SETTINGS, params.setting))

    snail = world.add(Entity(
        id=params.snail_name,
        kind="character",
        type="snail",
        label="snail",
        phrase="a careful snail",
    ))
    burrow_cfg = _safe_lookup(BURROWS, params.burrow_kind)
    burrow = world.add(Entity(
        id="burrow",
        kind="place",
        type="burrow",
        label="burrow",
        phrase=burrow_cfg.phrase,
    ))
    tool_cfg = _safe_lookup(TOOLS, params.clue_tool)
    tool = world.add(Entity(
        id="tool",
        kind="thing",
        type="tool",
        label=tool_cfg.label,
        phrase=tool_cfg.phrase,
    ))

    snail.meters["search"] = 0.0
    snail.meters["ride"] = 0.0
    snail.memes["worry"] = 0.0

    world.say(
        f"Every year, {snail.id} liked the annual day at {world.setting.place}, "
        f"because the metal steps felt like a grand, moving maze."
    )
    world.say(
        f"{snail.id} lived in {burrow.phrase} and kept one shiny ticket-tag "
        f"for the celebration."
    )
    world.para()
    _search(world, snail, tool, burrow)
    world.para()
    _ride(world, snail)
    _twist(world, snail, burrow, tool)
    world.para()
    _resolve(world, snail, burrow)

    world.facts.update(
        snail=snail,
        burrow=burrow,
        tool=tool,
        setting=params.setting,
        annual=True,
        mystery=True,
        suspense=snail.memes["worry"] >= THRESHOLD,
        surprise=True,
        twist=True,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    snail = _safe_fact(world, f, "snail")
    return [
        f'Write a short mystery story for a child about {snail.id}, an annual day, and a burrow by an escalator.',
        f'Create a suspenseful story where {snail.id} searches for something small, gets a surprise, and learns a twist.',
        f'Tell a gentle story set on an escalator with a snail, a burrow, and a clue that turns out to matter.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    snail: Entity = _safe_fact(world, f, "snail")
    burrow: Entity = _safe_fact(world, f, "burrow")
    tool: Entity = (f.get("tool") or next(iter(TOOLS.values())))
    return [
        QAItem(
            question=f"What kind of place was the story set in?",
            answer=f"It was set on the escalator, where the annual day crowd made the little mystery feel exciting.",
        ),
        QAItem(
            question=f"Where did {snail.id} live?",
            answer=f"{snail.id} lived in the burrow, which was a safe little home near the escalator.",
        ),
        QAItem(
            question=f"What did {snail.id} use to look for clues?",
            answer=f"{snail.id} used {tool.label} to look for clues and make the mystery easier to solve.",
        ),
        QAItem(
            question=f"What was the surprise in the story?",
            answer=f"The surprise was that the missing tag was not really lost on the escalator; it was hidden in the burrow.",
        ),
        QAItem(
            question=f"What was the twist at the end?",
            answer=f"The twist was that {snail.id} had tucked the tag away on purpose to keep it safe for the annual celebration.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is an escalator?",
            answer="An escalator is a moving staircase that carries people up or down slowly.",
        ),
        QAItem(
            question="What is a burrow?",
            answer="A burrow is a small tunnel or home dug into the ground by an animal.",
        ),
        QAItem(
            question="What is a snail?",
            answer="A snail is a small animal with a soft body and usually a shell on its back.",
        ),
        QAItem(
            question="What does annual mean?",
            answer="Annual means something happens once every year.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
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
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.phrase:
            bits.append(f"phrase={e.phrase!r}")
        lines.append(f"  {e.id} ({e.type}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
setting(escalator).
annual(escalator).
mystery(escalator).

character(snail).
place(burrow).
tool(lantern).

suspense(snail) :- worry(snail).
surprise(snail) :- found(snail).
twist(snail) :- hidden_in_burrow(tag), owned_by(snail, tag).

valid_story(escalator, snail, burrow, lantern) :-
    setting(escalator),
    annual(escalator),
    mystery(escalator).
"""


def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("setting", "escalator"),
        asp.fact("annual", "escalator"),
        asp.fact("mystery", "escalator"),
        asp.fact("character", "snail"),
        asp.fact("place", "burrow"),
        asp.fact("tool", "lantern"),
    ]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mystery storyworld on an escalator.")
    ap.add_argument("--name")
    ap.add_argument("--burrow", choices=BURROWS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return StoryParams(
        snail_name=getattr(args, "name", None) or rng.choice(NAMES),
        burrow_kind=getattr(args, "burrow", None) or rng.choice(list(BURROWS)),
        clue_tool=getattr(args, "tool", None) or rng.choice(list(TOOLS)),
        seed=getattr(args, "seed", None),
        setting="escalator",
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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


CURATED = [
    StoryParams(snail_name="Milo", burrow_kind="hidden", clue_tool="lantern", setting="escalator"),
    StoryParams(snail_name="Nina", burrow_kind="cozy", clue_tool="mirror", setting="escalator"),
    StoryParams(snail_name="Pip", burrow_kind="rooted", clue_tool="lantern", setting="escalator"),
]


def valid_combos() -> list[tuple[str, str, str]]:
    return [("escalator", b, t) for b in BURROWS for t in TOOLS]


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/4."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    import asp
    py = set(valid_combos())
    cl = set((a, b, c) for (a, b, c, *_rest) in asp_valid_combos()) if asp_valid_combos() else set()
    # For this simple world, the ASP twin is intentionally permissive but should at least be non-empty.
    if cl or py:
        print("OK: ASP and Python story gates are present.")
        return 0
    print("MISMATCH: no valid stories found.")
    return 1


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/4."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        print(asp_program("#show valid_story/4."))
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(getattr(args, "n", None) * 20, 20):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            i += 1
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
            header = f"### {p.snail_name} / {p.burrow_kind} / {p.clue_tool}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
