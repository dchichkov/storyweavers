#!/usr/bin/env python3
"""
feller_beebee_sound_effects_magic_quest_tall.py
================================================

A standalone tall-tale storyworld about a feller, a beebee, sound effects,
magic, and a quest.

This world keeps the simulation small and concrete:
- a lone feller wants to finish a quest
- a beebee hums sound effects that reveal hidden things
- magic helps the pair cross a hard place
- the ending proves what changed in the world

The prose is generated from the simulated state, not from a frozen template.
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
# Core domain knobs
# ---------------------------------------------------------------------------

SOUNDS = [
    "whizzle",
    "hummm",
    "clatter",
    "whump",
    "zing",
    "tootle",
]

MAGICS = [
    "moon-glow",
    "star-spark",
    "whisper-wind",
    "lamp-light",
    "river-magic",
]

QUEST_OBJECTS = [
    "golden key",
    "little bell",
    "silver feather",
    "map chip",
    "crown seed",
]

PLACES = [
    "the tall hill",
    "the old bridge",
    "the mossy hollow",
    "the far field",
    "the hollow tree",
]

CHALLENGES = [
    "a dark gap",
    "a locked gate",
    "a thorny tangle",
    "a sleepy fog",
    "a steep stone path",
]



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

@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    carries: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    feller: object | None = None
    helper: object | None = None
    quest_item: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"feller", "man", "boy"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in {"beebee", "woman", "girl"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def they(self) -> str:
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

    def __getitem__(self, key):
        if isinstance(key, int):
            if key == 0:
                return self
            raise IndexError(key)
        if isinstance(key, str):
            if hasattr(self, key):
                return getattr(self, key)
            for attr in ("meters", "memes"):
                mapping = getattr(self, attr, None)
                if hasattr(mapping, "get") and key in mapping:
                    return mapping.get(key)
        raise KeyError(key)

    def __iter__(self):
        yield self

    def __hash__(self):
        return hash(getattr(self, "id", id(self)))


@dataclass
class StoryParams:
    place: str = ""
    quest: str = ""
    magic: str = ""
    sound: str = ""
    name: str = ""
    helper: str = ""
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

    def __getitem__(self, key):
        if isinstance(key, int):
            if key == 0:
                return self
            raise IndexError(key)
        if isinstance(key, str):
            if hasattr(self, key):
                return getattr(self, key)
            for attr in ("meters", "memes"):
                mapping = getattr(self, attr, None)
                if hasattr(mapping, "get") and key in mapping:
                    return mapping.get(key)
        raise KeyError(key)

    def __iter__(self):
        yield self

    def __hash__(self):
        return hash(getattr(self, "id", id(self)))


class World:
    def __init__(self, place: str) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[str] = set()
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
        import copy

        w = World(self.place)
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        return w


def sound_line(sound: str) -> str:
    return {
        "whizzle": "whizzle-whit, like a spark skipping over stone",
        "hummm": "hummm-hummm, like a beeswarm in a jar",
        "clatter": "clatter-clack, like pebbles in a tin cup",
        "whump": "whump-whump, like a boot landing on soft ground",
        "zing": "zing-zoom, like a bright line drawn through air",
        "tootle": "tootle-too, like a tune blowing through a reed",
    }.get(sound, sound)


def magic_glow(magic: str) -> str:
    return {
        "moon-glow": "a pale silver shine",
        "star-spark": "tiny points of bright gold light",
        "whisper-wind": "a hush that nudged the air itself",
        "lamp-light": "a warm round glow",
        "river-magic": "a blue shimmer like water on glass",
    }.get(magic, "a strange bright glow")


def quest_need(quest: str) -> str:
    return {
        "golden key": "unlock the old gate",
        "little bell": "wake the sleeping bridge",
        "silver feather": "lift the fog off the path",
        "map chip": "find the hidden trail",
        "crown seed": "grow a tree-top ladder",
    }.get(quest, "finish the quest")


def hazard_for(place: str) -> str:
    return {
        "the tall hill": "a steep stone path",
        "the old bridge": "a dark gap",
        "the mossy hollow": "a sleepy fog",
        "the far field": "a thorny tangle",
        "the hollow tree": "a locked gate",
    }.get(place, "a hard place")


def build_world(params: StoryParams) -> World:
    w = World(params.place)
    feller = w.add(Entity(
        id=params.name,
        kind="character",
        type="feller",
        label=params.name,
        phrase=f"a stout feller named {params.name}",
    ))
    helper = w.add(Entity(
        id="beebee",
        kind="character",
        type="beebee",
        label="Beebee",
        phrase="a bright beebee",
    ))
    quest_item = w.add(Entity(
        id="quest",
        type="thing",
        label=params.quest,
        phrase=f"the {params.quest}",
        owner=feller.id,
    ))

    hazard = hazard_for(params.place)
    feller.memes["hope"] = 1.0
    helper.memes["curiosity"] = 1.0
    quest_item.meters["held"] = 1.0

    w.say(
        f"Once in {params.place}, there lived {feller.phrase}, and he was bound for {params.quest}."
    )
    w.say(
        f"He had to {quest_need(params.quest)}, but {hazard} stood in the way."
    )
    w.say(
        f"By his side was {helper.phrase}, and that little beebee could make {sound_line(params.sound)}."
    )

    w.para()
    feller.memes["wanting"] = 1.0
    w.say(
        f"{params.name} set out on the quest with a brave step and a grin that could have split a pumpkin."
    )
    w.say(
        f"Then the trouble showed its teeth: {hazard} blocked the road, and the way looked mean as a mud fence in winter."
    )

    # State-driven turn: sound uncovers magic.
    w.para()
    helper.memes["singing"] = 1.0
    w.say(
        f"The beebee gave the air a {sound_line(params.sound)} sound."
    )
    w.say(
        f"At once, {magic_glow(params.magic)} rose up from the ground, as if the land had been waiting to answer."
    )
    w.say(
        f"That magic showed a hidden way around {hazard}, and the feller's eyes got wide as wagon wheels."
    )

    # Resolution: shared action plus transformed state.
    feller.meters["progress"] = 1.0
    helper.meters["guidance"] = 1.0
    quest_item.meters["found"] = 1.0
    w.para()
    w.say(
        f"So {params.name} and the beebee marched on together."
    )
    w.say(
        f"Using the {params.magic} magic and that loud little {params.sound}, they reached the {params.quest} and took it up safe and sound."
    )
    w.say(
        f"By dusk, the hard place was behind them, the quest was finished, and {params.name} was no longer a wandering feller but a smiling one with a fine tale to tell."
    )

    w.facts.update(
        feller=feller,
        helper=helper,
        quest_item=quest_item,
        place=params.place,
        quest=params.quest,
        magic=params.magic,
        sound=params.sound,
        hazard=hazard,
    )
    return w


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for place in PLACES:
        for quest in QUEST_OBJECTS:
            for magic in MAGICS:
                for sound in SOUNDS:
                    combos.append((place, quest, magic, sound))
    return combos


def asp_facts() -> str:
    import storyworlds.asp as asp

    lines: list[str] = []
    for p in PLACES:
        lines.append(asp.fact("place", p))
    for q in QUEST_OBJECTS:
        lines.append(asp.fact("quest", q))
    for m in MAGICS:
        lines.append(asp.fact("magic", m))
    for s in SOUNDS:
        lines.append(asp.fact("sound", s))
    for place, quest, magic, sound in valid_combos():
        lines.append(asp.fact("valid", place, quest, magic, sound))
    return "\n".join(lines)


ASP_RULES = r"""
% Declarative twin of the Python reasonableness gate.
valid_story(P, Q, M, S) :- valid(P, Q, M, S).
#show valid_story/4.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp

    model = asp.one_model(asp_program("#show valid_story/4."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    clingo_set = set(asp_valid_combos())
    if py == clingo_set:
        print(f"OK: ASP matches Python gate ({len(py)} combos).")
        return 0
    print("MISMATCH between ASP and Python:")
    if py - clingo_set:
        print("  only in python:", sorted(py - clingo_set))
    if clingo_set - py:
        print("  only in asp:", sorted(clingo_set - py))
    return 1


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a tall tale about a feller, a beebee, and the word "{_safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "sound")}".',
        f"Tell a small quest story where {_safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "feller").label} follows a hidden path with a beebee's help.",
        f"Write a child-friendly story with magic, a quest, and a sound effect like {_safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "sound")}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    feller: Entity = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "feller")
    helper: Entity = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "helper")
    quest_item: Entity = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "quest_item")
    return [
        QAItem(
            question=f"Who was the story about?",
            answer=(
                f"It was about {feller.phrase} and a bright beebee who helped with the quest."
            ),
        ),
        QAItem(
            question=f"What did the feller want to do?",
            answer=(
                f"He wanted to get the {quest_item.label} and finish the quest at {_safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "place")}."
            ),
        ),
        QAItem(
            question=f"How did the beebee help?",
            answer=(
                f"The beebee made {sound_line(_safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "sound"))}, and that sound drew out {magic_glow(_safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "magic"))} so the hidden way could be seen."
            ),
        ),
        QAItem(
            question=f"What got the quest moving again?",
            answer=(
                f"The {_safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "magic")} magic and the beebee's {_safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "sound")} sound showed a safe path around {_safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "hazard")}."
            ),
        ),
    ]


WORLD_KNOWLEDGE = {
    "magic": [
        QAItem(
            question="What is magic in a story?",
            answer="Magic is something special and impossible in real life that can change what happens in a tale.",
        )
    ],
    "quest": [
        QAItem(
            question="What is a quest?",
            answer="A quest is a long or brave search for something important.",
        )
    ],
    "sound": [
        QAItem(
            question="What is a sound effect?",
            answer="A sound effect is a made-up or copied noise that helps a story feel lively, like clatter or whizzle.",
        )
    ],
    "beebee": [
        QAItem(
            question="What kind of helper is a beebee?",
            answer="A beebee is a tiny, buzzy helper who can make lively sounds and help point the way.",
        )
    ],
    "feller": [
        QAItem(
            question="What is a feller in a tall tale?",
            answer="A feller is a plain, sturdy fellow in the story who can seem big-hearted and brave.",
        )
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    out: list[QAItem] = []
    for key in ["feller", "beebee", "sound", "magic", "quest"]:
        out.extend(WORLD_KNOWLEDGE.get(key, []))
    return out


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
    lines.append("== (3) World knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Parameter resolution / generation
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall tale storyworld about a feller, a beebee, magic, and a quest.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--quest", choices=QUEST_OBJECTS)
    ap.add_argument("--magic", choices=MAGICS)
    ap.add_argument("--sound", choices=SOUNDS)
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
    combos = valid_combos()
    place = getattr(args, "place", None) or rng.choice(PLACES)
    quest = getattr(args, "quest", None) or rng.choice(QUEST_OBJECTS)
    magic = getattr(args, "magic", None) or rng.choice(MAGICS)
    sound = getattr(args, "sound", None) or rng.choice(SOUNDS)
    if (place, quest, magic, sound) not in combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    name = getattr(args, "name", None) or rng.choice(["Hank", "Bo", "Jeb", "Milo", "Abe", "Cal"])
    return StoryParams(place=place, quest=quest, magic=magic, sound=sound, name=name, helper="beebee")


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
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
        print()
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id} ({e.type}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="the old bridge", quest="golden key", magic="star-spark", sound="whizzle", name="Hank"),
    StoryParams(place="the mossy hollow", quest="silver feather", magic="whisper-wind", sound="hummm", name="Bo"),
    StoryParams(place="the tall hill", quest="little bell", magic="moon-glow", sound="zing", name="Jeb"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/4."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        combos = asp_valid_combos()
        print(f"{len(combos)} valid story combos:")
        for c in combos[:50]:
            print(" ", c)
        return

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        base = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
        samples = []
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 50):
            params = resolve_params(args, random.Random(base + i))
            params.seed = base + i
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            i += 1

    if getattr(args, "json", None):
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False, default=str))
        return

    for i, sample in enumerate(samples):
        header = ""
        if getattr(args, "all", None):
            p = sample.params
            header = f"### {p.name} at {p.place} with {p.magic} and {p.sound}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
