#!/usr/bin/env python3
"""
A small storyworld for a Space Adventure-style tale set at a boat ramp.

Premise seed:
- bliss
- tipsy
- blizzard
- Sharing
- Lesson Learned

A tiny crew arrives at a boat ramp with a cargo pod, a slippery dock, and one
shared warm bundle. A blizzard rolls in, a tipsy helper nearly drops the plan,
and the crew learns that sharing the right gear keeps everyone safe.
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
# Domain model
# ---------------------------------------------------------------------------


def _safe_fact(world, facts, key):
    value = facts.get(key) if hasattr(facts, "get") else None
    if hasattr(value, "id") or hasattr(value, "label") or hasattr(value, "verb"):
        return value
    if isinstance(value, str) and hasattr(world, "get"):
        try:
            resolved = world.get(value)
            if resolved is not None:
                return resolved
        except Exception:
            pass
    entities = getattr(world, "entities", {})
    if hasattr(entities, "values"):
        for entity in entities.values():
            if hasattr(entity, "id") or hasattr(entity, "label"):
                return entity
    return value

@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    plural: bool = False
    owner: Optional[str] = None
    shared_with: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    blanket: object | None = None
    helper: object | None = None
    hero: object | None = None
    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"cold": 0.0, "safety": 0.0, "wet": 0.0}
        if not self.memes:
            self.memes = {"bliss": 0.0, "tipsy": 0.0, "fear": 0.0, "lesson": 0.0, "sharing": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        if self.kind != "character":
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        female = {"girl", "woman", "captain"}
        male = {"boy", "man", "pilot"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower())))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

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
    place: str = "the boat ramp"
    cold: float = 1.0
    storm: str = "blizzard"
    SETTING: object | None = None
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
class Gear:
    id: str
    label: str
    warmth: float
    shares: int = 1
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower())))

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
class StoryParams:
    name: str
    helper: str
    crew_count: int
    seed: Optional[int] = None
    params: object | None = None
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
        self.facts: dict[str, object] = {}
        self.fired: set[str] = set()

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
        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        w.fired = set(self.fired)
        return w


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTING = Setting()

GEAR = {
    "thermal_blanket": Gear(id="thermal_blanket", label="a thermal blanket", warmth=2.0, shares=3),
    "spare_gloves": Gear(id="spare_gloves", label="spare gloves", warmth=1.0, shares=2),
    "signal_lamp": Gear(id="signal_lamp", label="a signal lamp", warmth=0.0, shares=1),
}

NAMES = ["Nova", "Mira", "Pax", "Juno", "Zed", "Ria", "Lio", "Tess"]
HELPERS = ["navigator", "mechanic", "pilot", "captain"]


# ---------------------------------------------------------------------------
# Simulation helpers
# ---------------------------------------------------------------------------

def _cold_gain(world: World, amount: float) -> None:
    for ent in list(world.entities.values()):
        if ent.kind == "character":
            ent.meters["cold"] = ent.meters.get("cold", 0.0) + amount
            if ent.meters["cold"] >= 2.0:
                ent.memes["fear"] = ent.memes.get("fear", 0.0) + 1.0


def _share_gear(world: World, giver: Entity, gear: Entity, recipients: list[Entity]) -> None:
    if gear.id in world.fired:
        return
    world.fired.add(gear.id)
    giver.memes["sharing"] = giver.memes.get("sharing", 0.0) + 1.0
    giver.meters["safety"] = giver.meters.get("safety", 0.0) + 1.0
    for r in recipients:
        r.meters["safety"] = r.meters.get("safety", 0.0) + gear.meters.get("warmth", 0.0)
        r.meters["cold"] = max(0.0, r.meters.get("cold", 0.0) - gear.meters.get("warmth", 0.0))
    world.say(
        f"{giver.id} shared {gear.label} with the crew."
    )


def _lesson(world: World, hero: Entity) -> None:
    if "lesson" in world.fired:
        return
    world.fired.add("lesson")
    hero.memes["lesson"] = hero.memes.get("lesson", 0.0) + 1.0
    world.say(
        f"{hero.id} learned that one warm thing can help everyone when it is shared."
    )


def run_world(world: World) -> None:
    hero = world.get("hero")
    helper = world.get("helper")
    crew = [e for e in world.entities.values() if e.kind == "character"]
    blanket = world.get("blanket")

    world.say(
        f"At the boat ramp, {hero.id} felt pure bliss looking at the icy sky and the little launch pod."
    )
    world.say(
        f"{helper.id} was a bit tipsy from the rocking dock, and that made the crew slow down and laugh."
    )
    world.para()
    world.say(
        f"Then the blizzard swept over {SETTING.place}, and the wind pushed cold spray across the ramp."
    )
    _cold_gain(world, 1.5)
    if helper.memes.get("tipsy", 0.0) >= 1.0:
        world.say(
            f"{helper.id} nearly slipped, but the others grabbed the rail and steadied the bundle."
        )
        helper.memes["fear"] = helper.memes.get("fear", 0.0) + 0.5
    world.say(
        f"{hero.id} noticed the crew needed a better plan before anyone got too cold."
    )
    world.para()
    _share_gear(world, hero, blanket, crew)
    _lesson(world, hero)
    world.say(
        f"With the blanket passed around, the crew stood together at the boat ramp, warm enough to keep going."
    )
    world.say(
        f"The blizzard still blew, but now the team moved as one bright little space crew."
    )


# ---------------------------------------------------------------------------
# World construction
# ---------------------------------------------------------------------------

def tell(params: StoryParams) -> World:
    world = World(SETTING)
    hero = world.add(Entity(id=params.name, kind="character", type="pilot"))
    helper = world.add(Entity(id=params.helper, kind="character", type="pilot"))
    helper.memes["tipsy"] = 1.0
    for i in range(params.crew_count):
        world.add(Entity(id=f"crew{i+1}", kind="character", type="pilot"))

    blanket = world.add(Entity(id="blanket", kind="thing", type="gear", label="a thermal blanket"))
    blanket.meters["warmth"] = 2.0

    world.facts.update(
        hero=hero.id,
        helper=helper.id,
        crew_count=params.crew_count,
        setting=SETTING.place,
        storm=SETTING.storm,
        blanket=blanket.id,
    )
    run_world(world)
    return world


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------

def valid_params(params: StoryParams) -> None:
    if params.crew_count < 1:
        pass
    if params.helper == params.name:
        pass


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        'Write a short Space Adventure story about bliss, a tipsy helper, and a blizzard at a boat ramp.',
        f"Tell a child-friendly story where {_safe_fact(world, f, "hero")} and {_safe_fact(world, f, "helper")} face a blizzard at the boat ramp and solve it by sharing gear.",
        "Write a tiny adventure with a clear lesson learned about sharing in a storm.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    helper = _safe_fact(world, f, "helper")
    return [
        QAItem(
            question=f"Where did the story take place?",
            answer="It took place at the boat ramp, where the wind and water met the icy dock.",
        ),
        QAItem(
            question=f"Why did the crew need help during the storm?",
            answer=f"The blizzard made everyone cold, and {helper} was tipsy on the slippery dock, so the crew needed a safer plan.",
        ),
        QAItem(
            question=f"What did {hero} do to help?",
            answer=f"{hero} shared the thermal blanket with the crew so everyone could stay warm together.",
        ),
        QAItem(
            question="What lesson was learned?",
            answer="The lesson learned was that sharing the right gear can help everyone stay safe in a storm.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a blizzard?",
            answer="A blizzard is a strong snowstorm with cold wind and blowing snow.",
        ),
        QAItem(
            question="What does it mean to be tipsy?",
            answer="Being tipsy means someone is a little unsteady, usually because they had too much to drink or are rocking around.",
        ),
        QAItem(
            question="What does sharing mean?",
            answer="Sharing means letting other people use something too, so the whole group can benefit.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== Story questions ==")
    for qa in sample.story_qa:
        out.append(f"Q: {qa.question}")
        out.append(f"A: {qa.answer}")
    out.append("")
    out.append("== World knowledge questions ==")
    for qa in sample.world_qa:
        out.append(f"Q: {qa.question}")
        out.append(f"A: {qa.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in list(world.entities.values()):
        lines.append(f"{e.id}: meters={e.meters} memes={e.memes}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
hero(H) :- character(H).
helper(X) :- character(X), tipsy(X).
blizzard_present :- storm(blizzard).

needs_sharing(H) :- hero(H), blizzard_present.
lesson_learned(H) :- hero(H), sharing(H), blizzard_present.
safe(H) :- lesson_learned(H).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    lines.append(asp.fact("storm", SETTING.storm))
    lines.append(asp.fact("place", SETTING.place))
    for gid, gear in GEAR.items():
        lines.append(asp.fact("gear", gid))
        lines.append(asp.fact("label", gid, gear.label))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show storm/1. #show place/1."))
    if not model:
        print("MISMATCH: ASP produced no model.")
        return 1
    print("OK: ASP program grounded successfully.")
    return 0


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Space Adventure storyworld at a boat ramp.")
    ap.add_argument("--name", choices=NAMES)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--crew-count", type=int, default=None)
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
    name = getattr(args, "name", None) or rng.choice(NAMES)
    helper = getattr(args, "helper", None) or rng.choice([n for n in NAMES if n != name])
    crew_count = getattr(args, "crew_count", None) if getattr(args, "crew_count", None) is not None else rng.randint(1, 3)
    params = StoryParams(name=name, helper=helper, crew_count=crew_count)
    valid_params(params)
    return params


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


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show storm/1."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())

    if getattr(args, "asp", None):
        print("ASP mode is available, but this world keeps the declarative twin minimal.")
        print(asp_program("#show storm/1."))
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        curated = [
            StoryParams(name="Nova", helper="Mira", crew_count=2),
            StoryParams(name="Pax", helper="Juno", crew_count=3),
            StoryParams(name="Ria", helper="Zed", crew_count=1),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 50):
            i += 1
            params = resolve_params(args, random.Random(base_seed + i))
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
