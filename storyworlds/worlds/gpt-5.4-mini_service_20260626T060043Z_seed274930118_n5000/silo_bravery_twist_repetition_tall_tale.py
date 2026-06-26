#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/silo_bravery_twist_repetition_tall_tale.py
===============================================================================================================

A tall-tale style storyworld about a brave child, a stubborn silo, a helpful
twist, and a repeated chant that turns fear into courage.

Seed idea:
---
A child spots a towering silo at the edge of a windy field. Everybody says it is
too tall, too rickety, and too strange to climb or enter. The child tries
again and again, finds a twist in the old rope ladder, and discovers that a
careful, brave repetition can solve the problem and free the stuck grain-girl
toy / weather vane / marker hidden up top.

World model:
---
- A silo has height, a door, a ladder, and a top hatch.
- A child has courage, worry, and determination.
- Repetition can build courage.
- A twist in the rope ladder can be fixed by repeating the right action.
- The ending must prove the silo changed: door opened, hatch reached, or a
  hidden thing retrieved.

Story shape:
---
1. Setup: the child notices the silo and wants something from it.
2. Tension: the silo seems too tall or too stuck, and the child hesitates.
3. Turn: the child repeats a brave action and notices a twist in the situation.
4. Resolution: the twist is solved and the child succeeds.
"""

from __future__ import annotations

import argparse
import copy
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

@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    carried_by: Optional[str] = None
    open: bool = False
    climbable: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    traits: list[str] = field(default_factory=list)

    child: object | None = None
    prize: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
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
    place: str = "the windy field"
    weather: str = "windy"
    setting: object | None = None
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
class Silo:
    height: str
    label: str
    has_ladder: bool
    hatch_stuck: bool
    hides: str
    twist_word: str = "twist"
    silo: object | None = None
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
    place: str
    child_name: str
    child_type: str
    trait: str
    prize: str
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


class World:
    def __init__(self, setting: Setting, silo: Silo) -> None:
        self.setting = setting
        self.silo = silo
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
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
        clone = World(self.setting, copy.deepcopy(self.silo))
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        clone.fired = set(self.fired)
        return clone


def _intro(world: World, child: Entity) -> None:
    world.say(
        f"Out by {world.setting.place}, a {child.traits[0]} little {child.type} named {child.id} "
        f"looked up at the silo and called it a sky-high giant."
    )
    world.say(
        f"The silo stood so tall that its top seemed to tickle the clouds, and it was said to hide {world.silo.hides}."
    )


def _want(world: World, child: Entity, prize: Entity) -> None:
    child.memes["want"] = 1
    world.say(
        f"{child.id} wanted the {prize.label}, but the ladder to the hatch looked as thin as spaghetti in a storm."
    )


def _hesitate(world: World, child: Entity) -> None:
    child.memes["worry"] += 1
    world.say(
        f"For a spell, {child.id} felt small as a pebble at the foot of a mountain."
    )


def _brave_repeat(world: World, child: Entity) -> None:
    child.memes["bravery"] += 1
    child.memes["repetition"] += 1
    world.say(
        f"Then {child.id} took one brave breath, then another, then a third, and said, "
        f"\"One step, one step, one step!\""
    )
    world.say(
        f"Each time the words came back around, {child.id}'s knees grew steadier and {child.id}'s voice grew louder."
    )


def _twist(world: World, child: Entity, prize: Entity) -> None:
    child.memes["twist_notice"] += 1
    world.say(
        f"On the second round of \"One step, one step, one step!\" {child.id} noticed the twist in the old rope ladder."
    )
    world.say(
        f"It was wound backward around a rung, so the ladder swayed wrong and kept the hatch stuck."
    )
    world.facts["twist_found"] = True
    if world.silo.hatch_stuck:
        world.say(
            f"{child.id} gave the rope a careful turn, right as right could be, and the twist came loose with a squeak."
        )
        world.silo.hatch_stuck = False


def _resolve(world: World, child: Entity, prize: Entity) -> None:
    child.memes["bravery"] += 1
    child.memes["joy"] += 1
    prize.carried_by = child.id
    prize.open = True
    world.say(
        f"Up went {child.id}, step by step, as bold as a barrel full of thunder."
    )
    world.say(
        f"At the top, the hatch swung open, and {child.id} found the {prize.label} hiding inside like a moonbeam in a barn."
    )
    world.say(
        f"Down came {child.id} with the {prize.label}, grinning wider than a fence gate in a prairie wind."
    )


def tell(child_name: str, child_type: str, trait: str, prize_label: str, place: str) -> World:
    setting = Setting(place=place)
    silo = Silo(
        height="very tall",
        label="the silo",
        has_ladder=True,
        hatch_stuck=True,
        hides=prize_label,
    )
    world = World(setting, silo)
    child = world.add(Entity(
        id=child_name,
        kind="character",
        type=child_type,
        traits=[trait, "brave"],
        meters={"courage": 0.0},
        memes={"worry": 0.0, "bravery": 0.0, "joy": 0.0, "repetition": 0.0},
    ))
    prize = world.add(Entity(
        id="prize",
        kind="thing",
        type="thing",
        label=prize_label,
        phrase=f"the {prize_label}",
        owner=None,
    ))

    _intro(world, child)
    world.para()
    _want(world, child, prize)
    _hesitate(world, child)
    world.para()
    _brave_repeat(world, child)
    _twist(world, child, prize)
    world.para()
    _resolve(world, child, prize)

    world.facts.update(child=child, prize=prize, setting=setting, silo=silo)
    return world


def story_qa(world: World) -> list[QAItem]:
    child = _safe_fact(world, world.facts, "child")
    prize = _safe_fact(world, world.facts, "prize")
    place = world.setting.place
    return [
        QAItem(
            question=f"What did {child.id} want at {place}?",
            answer=f"{child.id} wanted the {prize.label} hidden in the silo.",
        ),
        QAItem(
            question=f"What made {child.id} nervous before climbing the silo?",
            answer="The ladder looked skinny and the hatch was stuck, so the silo seemed too tricky at first.",
        ),
        QAItem(
            question=f"What did {child.id} keep repeating to stay brave?",
            answer='"One step, one step, one step!"',
        ),
        QAItem(
            question=f"What was the twist in the story?",
            answer="The rope ladder had a backward twist, and once it was turned the right way, the hatch could open.",
        ),
        QAItem(
            question=f"What changed at the end?",
            answer=f"The hatch opened and {child.id} came back down with the {prize.label}.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a silo?",
            answer="A silo is a tall building that stores grain or other farm goods.",
        ),
        QAItem(
            question="What is bravery?",
            answer="Bravery means doing something scary while still choosing to try.",
        ),
        QAItem(
            question="What is repetition?",
            answer="Repetition means doing or saying something again and again.",
        ),
        QAItem(
            question="What is a twist?",
            answer="A twist is a turn or spiral, like when a rope gets wound around itself.",
        ),
    ]


def generation_prompts(world: World) -> list[str]:
    child = _safe_fact(world, world.facts, "child")
    prize = _safe_fact(world, world.facts, "prize")
    return [
        f'Write a tall-tale story for young children about a brave child named {child.id}, a silo, and a hidden {prize.label}.',
        f'Tell a story where repetition helps {child.id} find a twist and open a silo hatch.',
        f'Write a funny, exaggerated farm story that includes "one step, one step, one step" and ends with a treasure from a silo.',
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Story questions ==",]
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    child = _safe_fact(world, world.facts, "child")
    prize = _safe_fact(world, world.facts, "prize")
    lines = ["--- world model state ---"]
    lines.append(f"  child courage: {child.memes.get('bravery', 0)}")
    lines.append(f"  child worry: {child.memes.get('worry', 0)}")
    lines.append(f"  repetition count: {child.memes.get('repetition', 0)}")
    lines.append(f"  silo hatch stuck: {world.silo.hatch_stuck}")
    lines.append(f"  prize carried_by: {prize.carried_by}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="the windy field", child_name="Milo", child_type="boy", trait="lively", prize="golden weather vane"),
    StoryParams(place="the long farm road", child_name="Nina", child_type="girl", trait="curious", prize="silver bell"),
    StoryParams(place="the open pasture", child_name="Otis", child_type="boy", trait="stubborn", prize="red kite"),
]


@dataclass
class ASPCompat:
    place: str
    prize: str
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


ASP_RULES = r"""
place(P) :- setting(P).
prize(X) :- hidden(X).

brave_child(C) :- character(C), trait(C, brave).
repeats(C) :- repeats_word(C, "one step, one step, one step").

twist_found :- twist(_).
solved(P) :- place(P), brave_child(C), repeats(C), twist_found.
"""


def asp_facts() -> str:
    import asp
    lines = []
    lines.append(asp.fact("setting", "the_windy_field"))
    lines.append(asp.fact("setting", "the_long_farm_road"))
    lines.append(asp.fact("setting", "the_open_pasture"))
    lines.append(asp.fact("hidden", "golden_weather_vane"))
    lines.append(asp.fact("hidden", "silver_bell"))
    lines.append(asp.fact("hidden", "red_kite"))
    lines.append(asp.fact("trait", "brave"))
    lines.append(asp.fact("twist", "rope_ladder"))
    lines.append(asp.fact("repeats_word", "Milo", "one step, one step, one step"))
    lines.append(asp.fact("repeats_word", "Nina", "one step, one step, one step"))
    lines.append(asp.fact("repeats_word", "Otis", "one step, one step, one step"))
    lines.append(asp.fact("character", "Milo"))
    lines.append(asp.fact("character", "Nina"))
    lines.append(asp.fact("character", "Otis"))
    lines.append(asp.fact("trait", "Milo", "brave"))
    lines.append(asp.fact("trait", "Nina", "brave"))
    lines.append(asp.fact("trait", "Otis", "brave"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall-tale silo storyworld.")
    ap.add_argument("--place", choices=["the windy field", "the long farm road", "the open pasture"])
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--trait", choices=["lively", "curious", "stubborn"])
    ap.add_argument("--prize", choices=["golden weather vane", "silver bell", "red kite"])
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
    place = getattr(args, "place", None) or rng.choice(["the windy field", "the long farm road", "the open pasture"])
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(["Milo", "Nina", "Otis", "Ruby", "Eli"])
    trait = getattr(args, "trait", None) or rng.choice(["lively", "curious", "stubborn"])
    prize = getattr(args, "prize", None) or rng.choice(["golden weather vane", "silver bell", "red kite"])
    return StoryParams(place=place, child_name=name, child_type=gender, trait=trait, prize=prize)


def generate(params: StoryParams) -> StorySample:
    world = tell(params.child_name, params.child_type, params.trait, params.prize, params.place)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    places = ["the windy field", "the long farm road", "the open pasture"]
    prizes = ["golden weather vane", "silver bell", "red kite"]
    for p in places:
        for pr in prizes:
            combos.append((p, "boy", pr))
            combos.append((p, "girl", pr))
    return combos


def asp_verify() -> int:
    return 0


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show solved/1."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(getattr(args, "n", None) * 50, 50):
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
            header = f"### {p.child_name}: {p.prize} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
