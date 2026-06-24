#!/usr/bin/env python3
"""
A small folk-tale storyworld about wonder and kindness.

Initial seed tale:
---
In a little valley, a child found a wonder-seed that glowed like a star.
The child wanted to keep it on the windowsill and watch it shine every night.
But an old neighbor's lamp had gone out, and the child could hear the neighbor shiver in the dark.

The child brought the wonder-seed to the neighbor instead of keeping it.
The seed warmed the room, the lamp lit again, and the valley garden burst into a glowing bloom.
The child learned that kindness can make wonder grow brighter when it is shared.
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
# World model
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
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    child: object | None = None
    elder: object | None = None
    wonder: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "grandmother", "elderwoman"}
        male = {"boy", "man", "father", "grandfather", "elderman"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

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
    place: str
    indoors: bool = False
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
class WonderThing:
    id: str
    label: str
    phrase: str
    glow: str
    warmth: str
    bloom: str
    gives: str
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
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

    clone: object | None = None
    world: object | None = None
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
        clone.facts = dict(self.facts)
        return clone
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


THRESHOLD = 1.0


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "valley": Setting(place="the little valley"),
    "cottage": Setting(place="the cottage by the hill", indoors=True),
    "lantern_lane": Setting(place="Lantern Lane"),
}

WONDER_THINGS = {
    "wonder_seed": WonderThing(
        id="wonder_seed",
        label="wonder-seed",
        phrase="a wonder-seed that glowed like a star",
        glow="glowed",
        warmth="warmed",
        bloom="bloomed",
        gives="a soft shining garden",
    ),
    "moon_bell": WonderThing(
        id="moon_bell",
        label="moon-bell",
        phrase="a moon-bell that hummed like a lullaby",
        glow="hummed",
        warmth="murmured",
        bloom="rang",
        gives="a quiet silver song",
    ),
    "small_star": WonderThing(
        id="small_star",
        label="small star",
        phrase="a small star caught in a glass jar",
        glow="shone",
        warmth="brightened",
        bloom="sparkled",
        gives="a bright window of light",
    ),
}

GIVERS = {
    "girl": ["Ava", "Mina", "Rose", "Elin", "Lila"],
    "boy": ["Finn", "Owen", "Theo", "Perry", "Nico"],
}

ELDERS = {
    "grandmother": "Grandma Wren",
    "grandfather": "Grandpa Bram",
    "old neighbor": "Old Nessa",
}

TRACES = ["gentle", "curious", "brave", "soft-hearted", "thoughtful"]


# ---------------------------------------------------------------------------
# Params
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    setting: str
    wonder: str
    giver_gender: str
    giver_name: str
    giver_trait: str
    elder_role: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Rule engine
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


def _spark(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    wonder = world.get("wonder")
    if child.memes.get("guarding_wonder", 0) >= THRESHOLD and wonder.meters.get("glow", 0) >= THRESHOLD:
        sig = ("spark",)
        if world.facts.get("sparked"):
            return out
        world.facts["sparked"] = True
        wonder.meters["warmth"] = wonder.meters.get("warmth", 0) + 1
        child.memes["awe"] = child.memes.get("awe", 0) + 1
        out.append(f"The wonder found room to grow brighter.")
    return out


def _share_bloom(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    elder = world.get("elder")
    wonder = world.get("wonder")
    if child.memes.get("kindness", 0) >= THRESHOLD and elder.meters.get("lamp_out", 0) >= THRESHOLD:
        if world.facts.get("bloomed"):
            return out
        world.facts["bloomed"] = True
        elder.meters["warmth"] = elder.meters.get("warmth", 0) + 1
        elder.meters["lamp_on"] = 1
        wonder.meters["bloom"] = wonder.meters.get("bloom", 0) + 1
        child.memes["joy"] = child.memes.get("joy", 0) + 1
        child.memes["awe"] = child.memes.get("awe", 0) + 1
        out.append("Kindness turned the dark room bright.")
    return out


RULES = [_spark, _share_bloom]


def propagate(world: World) -> None:
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in RULES:
            res = rule(world)
            if res:
                changed = True
                for line in res:
                    world.say(line)


# ---------------------------------------------------------------------------
# Story beats
# ---------------------------------------------------------------------------
def _intro(world: World, child: Entity, elder: Entity, wonder: Entity) -> None:
    world.say(
        f"In {world.setting.place}, {child.id} was a {world.facts['trait']} child who "
        f"noticed every small shining thing."
    )
    world.say(
        f"One day {child.id} found {wonder.phrase}; it seemed to whisper, "
        f"'{wonder.gives}.'"
    )
    world.say(
        f"{child.id} wanted to keep the {wonder.label} by the window and watch it shine."
    )
    child.memes["wonder"] = child.memes.get("wonder", 0) + 1
    child.memes["want_keep"] = child.memes.get("want_keep", 0) + 1
    wonder.meters["glow"] = wonder.meters.get("glow", 0) + 1


def _problem(world: World, child: Entity, elder: Entity, wonder: Entity) -> None:
    world.para()
    world.say(
        f"But the lantern in {elder.id}'s room had gone out, and the old room was cold."
    )
    elder.meters["lamp_out"] = 1
    elder.meters["cold"] = elder.meters.get("cold", 0) + 1
    child.memes["concern"] = child.memes.get("concern", 0) + 1
    world.say(
        f"{child.id} heard {elder.id} cough softly in the dark and felt a tug in {child.pronoun('possessive')} chest."
    )
    world.say(
        f"{child.id} could keep the {wonder.label}, or {child.id} could share it and help."
    )


def _turn(world: World, child: Entity, elder: Entity, wonder: Entity) -> None:
    world.para()
    child.memes["kindness"] = child.memes.get("kindness", 0) + 1
    child.memes["guarding_wonder"] = 0
    world.say(
        f"{child.id} wrapped the {wonder.label} in a little cloth and brought it to {elder.id}."
    )
    world.say(
        f'"Please take it," {child.id} said. "I can love wonder more when someone else gets warm."'
    )
    propagate(world)


def _end(world: World, child: Entity, elder: Entity, wonder: Entity) -> None:
    world.para()
    world.say(
        f"The {wonder.label} {wonder.warmth} the room, and the lamp blinked back to life."
    )
    world.say(
        f"Outside, the garden at {world.setting.place} {wonder.bloom} with a silver glow."
    )
    world.say(
        f"{elder.id} smiled and shared a sweet bun, while {child.id} watched the light and felt wonder grow inside."
    )


def tell(setting: Setting, wonder_t: WonderThing, giver_name: str, giver_gender: str,
         giver_trait: str, elder_role: str) -> World:
    world = World(setting)

    child = world.add(Entity(
        id=giver_name,
        kind="character",
        type=giver_gender,
    ))
    elder_name = _safe_lookup(ELDERS, elder_role)
    elder_type = "grandmother" if elder_role == "grandmother" else (
        "grandfather" if elder_role == "grandfather" else "woman"
    )
    elder = world.add(Entity(
        id=elder_name,
        kind="character",
        type=elder_type,
    ))
    wonder = world.add(Entity(
        id="wonder",
        kind="thing",
        type="wonder",
        label=wonder_t.label,
        phrase=wonder_t.phrase,
        owner=child.id,
        meters={},
        memes={},
    ))

    world.facts.update(
        trait=giver_trait,
        elder_role=elder_role,
        child=child,
        elder=elder,
        wonder=wonder,
        wonder_t=wonder_t,
    )

    _intro(world, child, elder, wonder)
    _problem(world, child, elder, wonder)
    _turn(world, child, elder, wonder)
    _end(world, child, elder, wonder)
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short folk tale for a young child about {f["child"].id}, a {f["trait"]} child, and a {f["wonder_t"].label}.',
        f"Tell a gentle story where {f['child'].id} chooses kindness instead of keeping the {f['wonder_t'].label} to {f['child'].pronoun('possessive')}self.",
        f"Write a simple wonder tale that begins with a glowing gift and ends with a warm act of kindness.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child: Entity = _safe_fact(world, f, "child")
    elder: Entity = _safe_fact(world, f, "elder")
    wonder: WonderThing = _safe_fact(world, f, "wonder_t")
    return [
        QAItem(
            question=f"What did {child.id} find in the valley?",
            answer=f"{child.id} found {wonder.phrase}.",
        ),
        QAItem(
            question=f"Why did {child.id} bring the {wonder.label} to {elder.id}?",
            answer=(
                f"{elder.id}'s lamp had gone out and the room was cold, so {child.id} chose kindness "
                f"instead of keeping the {wonder.label} alone."
            ),
        ),
        QAItem(
            question=f"What happened after {child.id} shared the {wonder.label}?",
            answer=(
                f"The {wonder.label} warmed the room, the lamp lit again, and the garden outside "
                f"grew bright with a bloom of wonder."
            ),
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    wonder: WonderThing = _safe_fact(world, f, "wonder_t")
    return [
        QAItem(
            question="What is kindness?",
            answer="Kindness is doing something caring for someone else, especially when it helps them feel safe or glad.",
        ),
        QAItem(
            question="What is wonder?",
            answer="Wonder is the feeling of surprise and delight when something seems magical, beautiful, or full of mystery.",
        ),
        QAItem(
            question=f"What kind of thing is a {wonder.label} in this story?",
            answer=f"In this story, the {wonder.label} is a magical little treasure that can glow, warm a room, and help a garden bloom.",
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


# ---------------------------------------------------------------------------
# ASP
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A wonder item is present in the storyworld.
wonder_item(W) :- wonder(W).

% Kindness and wonder can together produce a bloom.
bloomed(W) :- wonder_item(W), kind_act(kindness), helps(W, elder).

% The story is reasonable only if the child can either keep the wonder or share it.
reasonable_story(S, W, E) :- setting(S), wonder_item(W), elder(E), kind_act(kindness).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for wid, w in WONDER_THINGS.items():
        lines.append(asp.fact("wonder", wid))
        lines.append(asp.fact("gives", wid, w.gives))
    lines.append(asp.fact("kind_act", "kindness"))
    lines.append(asp.fact("helps", "wonder_seed", "elder"))
    for er in ELDERS:
        lines.append(asp.fact("elder", er))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show reasonable_story/3."))
    clingo_set = set(asp.atoms(model, "reasonable_story"))
    python_set = {(s, w, e) for s in SETTINGS for w in WONDER_THINGS for e in ELDERS}
    if clingo_set == python_set:
        print(f"OK: clingo gate matches python ({len(clingo_set)} story combinations).")
        return 0
    print("MISMATCH between clingo and python:")
    print("  only in clingo:", sorted(clingo_set - python_set))
    print("  only in python:", sorted(python_set - clingo_set))
    return 1


# ---------------------------------------------------------------------------
# Params / generation
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Folk tale storyworld about wonder and kindness.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--wonder", choices=WONDER_THINGS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--trait", choices=TRACES)
    ap.add_argument("--elder", choices=list(ELDERS))
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
    setting = getattr(args, "setting", None) or rng.choice(list(SETTINGS))
    wonder = getattr(args, "wonder", None) or rng.choice(list(WONDER_THINGS))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(_safe_lookup(GIVERS, gender))
    trait = getattr(args, "trait", None) or rng.choice(TRACES)
    elder = getattr(args, "elder", None) or rng.choice(list(ELDERS))
    return StoryParams(setting=setting, wonder=wonder, giver_gender=gender, giver_name=name, giver_trait=trait, elder_role=elder)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        _safe_lookup(SETTINGS, params.setting),
        _safe_lookup(WONDER_THINGS, params.wonder),
        params.giver_name,
        params.giver_gender,
        params.giver_trait,
        params.elder_role,
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
        lines.append(f"  {e.id:16} ({e.type:10}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams("valley", "wonder_seed", "girl", "Ava", "gentle", "old neighbor"),
    StoryParams("cottage", "moon_bell", "boy", "Finn", "thoughtful", "grandmother"),
    StoryParams("lantern_lane", "small_star", "girl", "Mina", "soft-hearted", "grandfather"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show reasonable_story/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())

    if getattr(args, "asp", None):
        import storyworlds.asp as asp
        model = asp.one_model(asp_program("#show reasonable_story/3."))
        combos = sorted(set(asp.atoms(model, "reasonable_story")))
        print(f"{len(combos)} reasonable story combinations:")
        for item in combos:
            print(" ", item)
        return

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        base = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
        samples = []
        seen = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(getattr(args, "n", None) * 20, 20):
            params = resolve_params(args, random.Random(base + i))
            params.seed = base + i
            sample = generate(params)
            if sample.story in seen:
                i += 1
                continue
            seen.add(sample.story)
            samples.append(sample)
            i += 1

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
            header = f"### {p.giver_name}: {p.wonder} in {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
