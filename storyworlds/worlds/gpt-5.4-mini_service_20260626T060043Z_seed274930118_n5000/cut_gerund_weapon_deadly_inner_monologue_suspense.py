#!/usr/bin/env python3
"""
A standalone storyworld: adventure, suspense, friendship, and a dangerous
find that must be handled carefully.

The world model tracks a small hike, a hidden weapon, a cutting action, and the
emotional turn from worry to trust.
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
    carried_by: Optional[str] = None
    dangerous: bool = False
    cuttable: bool = False
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    friend: object | None = None
    hero: object | None = None
    weapon: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
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
class Place:
    id: str
    name: str
    indoors: bool = False
    tags: set[str] = field(default_factory=set)
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
class Challenge:
    id: str
    setup: str
    inner_monologue: str
    suspense_line: str
    action: str
    resolution: str
    keyword: str
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
class StoryParams:
    place: str
    challenge: str
    hero_name: str
    hero_type: str
    friend_name: str
    friend_type: str
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
    def __init__(self, place: Place, challenge: Challenge) -> None:
        self.place = place
        self.challenge = challenge
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
        import copy
        w = World(self.place, self.challenge)
        w.entities = copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        w.fired = set(self.fired)
        return w


PLACES = {
    "old_bridge": Place("old_bridge", "the old bridge", tags={"rope", "ravine", "hike"}),
    "pine_path": Place("pine_path", "the pine path", tags={"trees", "trail", "hike"}),
    "cave_mouth": Place("cave_mouth", "the cave mouth", tags={"dark", "echo", "hike"}),
}

CHALLENGES = {
    "vine": Challenge(
        id="vine",
        setup="A thick vine had wrapped across the trail like a green rope.",
        inner_monologue="If they could cut the vine, the path would open again.",
        suspense_line="But something shiny lay under the leaves, and nobody could tell if it was a tool or a weapon.",
        action="carefully cut the vine",
        resolution="The trail opened, and the hidden weapon stayed where the ranger could find it later.",
        keyword="cutting",
    ),
    "rope": Challenge(
        id="rope",
        setup="A frayed rope blocked the little bridge over the ravine.",
        inner_monologue="One snip could help them cross, but only if the blade stayed far from their hands.",
        suspense_line="The rope creaked, and the rusty object beside it looked deadly in the dim light.",
        action="slice the rope free",
        resolution="The bridge held, and the dangerous thing was left untouched.",
        keyword="cutting",
    ),
    "brush": Challenge(
        id="brush",
        setup="A thorny brush wall had swallowed the narrow trail.",
        inner_monologue="Cutting a narrow door through it might save time, but the hidden metal glinted like a weapon.",
        suspense_line="Their lantern shook, and the shadow on the ground looked deadly for one nervous second.",
        action="cut a safe opening",
        resolution="The friends slipped through together, and the weapon turned out to be an old iron hook.",
        keyword="cutting",
    ),
}

GIRL_NAMES = ["Mina", "Lila", "Tara", "Nina", "Zoe"]
BOY_NAMES = ["Owen", "Eli", "Finn", "Noah", "Leo"]


def _p(name: str, who: Entity) -> str:
    return f"{name}"


def _third(name: str, kind: str) -> str:
    return name


def _intro(world: World, hero: Entity, friend: Entity) -> None:
    world.say(
        f"{hero.id} and {friend.id} were best friends on a small adventure, "
        f"walking with quick steps and bright eyes."
    )
    world.say(
        f"They loved finding new paths, and today they were exploring {world.place.name}."
    )


def _build_up(world: World, hero: Entity, friend: Entity) -> None:
    ch = world.challenge
    world.say(ch.setup)
    hero.memes["curiosity"] += 1
    friend.memes["curiosity"] += 1
    world.say(
        f"{hero.id} looked at the blocked trail and thought, "
        f"'{ch.inner_monologue}'"
    )
    world.say(ch.suspense_line)
    hero.memes["worry"] += 1
    friend.memes["worry"] += 1


def _turn(world: World, hero: Entity, friend: Entity, weapon: Entity) -> None:
    ch = world.challenge
    hero.memes["fear"] += 1
    hero.memes["friendship"] += 1
    friend.memes["friendship"] += 1
    world.say(
        f"{friend.id} stayed close and whispered, "
        f'"We can do this together, and we do not have to touch the weapon."'
    )
    world.say(
        f"{hero.id} took a breath, listened to that brave little voice inside, and "
        f"reached for a small branch instead."
    )
    hero.meters["cutting"] += 1
    world.say(
        f"With the branch as a guide, {hero.id} made {ch.action} while {friend.id} held the lantern steady."
    )


def _resolution(world: World, hero: Entity, friend: Entity, weapon: Entity) -> None:
    hero.memes["relief"] += 1
    friend.memes["relief"] += 1
    weapon.meters["hidden"] = 1
    world.say(
        f"At last, the path was open again. {hero.id} and {friend.id} smiled at each other, "
        f"and the scary weapon stayed on the ground, far away from their hands."
    )
    world.say(
        f"They hurried on together, side by side, with the little adventure turning safe again."
    )
    world.say(world.challenge.resolution)


def tell(params: StoryParams) -> World:
    place = _safe_lookup(PLACES, params.place)
    challenge = _safe_lookup(CHALLENGES, params.challenge)
    world = World(place, challenge)

    hero = world.add(Entity(
        id=params.hero_name,
        kind="character",
        type=params.hero_type,
        meters={"tired": 0.0},
        memes={"curiosity": 0.0, "worry": 0.0, "fear": 0.0, "friendship": 0.0, "relief": 0.0},
    ))
    friend = world.add(Entity(
        id=params.friend_name,
        kind="character",
        type=params.friend_type,
        meters={"tired": 0.0},
        memes={"curiosity": 0.0, "worry": 0.0, "fear": 0.0, "friendship": 0.0, "relief": 0.0},
    ))
    weapon = world.add(Entity(
        id="weapon",
        label="weapon",
        phrase="an old hidden weapon",
        dangerous=True,
        meters={"hidden": 1.0},
    ))

    world.facts.update(hero=hero, friend=friend, weapon=weapon, place=place, challenge=challenge)
    _intro(world, hero, friend)
    world.para()
    _build_up(world, hero, friend)
    world.para()
    _turn(world, hero, friend, weapon)
    world.para()
    _resolution(world, hero, friend, weapon)
    return world


def generation_prompts(world: World) -> list[str]:
    ch = _safe_fact(world, world.facts, "challenge")
    place = _safe_fact(world, world.facts, "place")
    hero = _safe_fact(world, world.facts, "hero")
    return [
        f'Write a short adventure story for a child where two friends explore {place.name} and face suspense about a hidden weapon.',
        f"Tell a gentle suspense story where {hero.id} thinks about {ch.keyword} while helping a friend safely clear a path.",
        f"Write an adventure about friendship, a dangerous object, and a careful cutting moment in {place.name}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero = _safe_fact(world, world.facts, "hero")
    friend = _safe_fact(world, world.facts, "friend")
    place = _safe_fact(world, world.facts, "place")
    challenge = _safe_fact(world, world.facts, "challenge")
    return [
        QAItem(
            question=f"Who were the two friends in the story?",
            answer=f"The friends were {hero.id} and {friend.id}. They explored {place.name} together.",
        ),
        QAItem(
            question=f"What problem blocked the trail?",
            answer=f"{challenge.setup}",
        ),
        QAItem(
            question=f"Why did the story feel suspenseful?",
            answer=f"It felt suspenseful because the friends saw something shiny that might be a tool or a weapon, and they did not know if it was deadly until they looked closer.",
        ),
        QAItem(
            question=f"How did {hero.id} and {friend.id} solve the problem?",
            answer=f"They stayed calm, trusted each other, and used a small branch to do the cutting while leaving the weapon alone.",
        ),
        QAItem(
            question=f"What changed by the end of the story?",
            answer=f"The trail was open, the friends felt relieved, and the dangerous object stayed safely on the ground for an adult to find.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does cutting mean?",
            answer="Cutting means making something separate into pieces or making a path open with a blade or a sharp edge.",
        ),
        QAItem(
            question="What is a weapon?",
            answer="A weapon is something that can hurt someone, so people should not play with it.",
        ),
        QAItem(
            question="What does deadly mean?",
            answer="Deadly means something could cause serious harm or death, so it must be treated with great care.",
        ),
        QAItem(
            question="Why is friendship important on an adventure?",
            answer="Friendship helps friends stay brave, share ideas, and keep each other safe when a path feels scary.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(f"- {p}")
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
    lines = ["--- world trace ---"]
    for e in list(world.entities.values()):
        lines.append(
            f"{e.id}: kind={e.kind} type={e.type} meters={dict(e.meters)} memes={dict(e.memes)} dangerous={e.dangerous}"
        )
    return "\n".join(lines)


ASP_RULES = r"""
place(old_bridge).
place(pine_path).
place(cave_mouth).

challenge(vine).
challenge(rope).
challenge(brush).

friendship(hero, friend) :- hero_1(hero), friend_1(friend).
suspense(X) :- weapon(X).
dangerous(X) :- weapon(X).
cut_action(vine).
cut_action(rope).
cut_action(brush).

valid_story(P, C) :- place(P), challenge(C).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for p in PLACES:
        lines.append(asp.fact("place", p))
    for c in CHALLENGES:
        lines.append(asp.fact("challenge", c))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = {(p, c) for p in PLACES for c in CHALLENGES}
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches Python ({len(py)} combos).")
        return 0
    print("MISMATCH")
    print("only python:", sorted(py - cl))
    print("only clingo:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Adventure storyworld with suspense, friendship, and a dangerous find.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--challenge", choices=CHALLENGES)
    ap.add_argument("--name")
    ap.add_argument("--friend")
    ap.add_argument("--hero-type", choices=["girl", "boy"], dest="hero_type")
    ap.add_argument("--friend-type", choices=["girl", "boy"], dest="friend_type")
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
    place = getattr(args, "place", None) or rng.choice(list(PLACES))
    challenge = getattr(args, "challenge", None) or rng.choice(list(CHALLENGES))
    hero_type = getattr(args, "hero_type", None) or rng.choice(["girl", "boy"])
    friend_type = getattr(args, "friend_type", None) or ("boy" if hero_type == "girl" else "girl")
    hero_name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if hero_type == "girl" else BOY_NAMES)
    friend_name = getattr(args, "friend", None) or rng.choice([n for n in (GIRL_NAMES + BOY_NAMES) if n != hero_name])
    return StoryParams(place=place, challenge=challenge, hero_name=hero_name, hero_type=hero_type, friend_name=friend_name, friend_type=friend_type)


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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


CURATED = [
    StoryParams(place="old_bridge", challenge="rope", hero_name="Mina", hero_type="girl", friend_name="Owen", friend_type="boy"),
    StoryParams(place="pine_path", challenge="vine", hero_name="Leo", hero_type="boy", friend_name="Tara", friend_type="girl"),
    StoryParams(place="cave_mouth", challenge="brush", hero_name="Zoe", hero_type="girl", friend_name="Finn", friend_type="boy"),
]


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        print(asp_valid_combos())
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(getattr(args, "n", None)):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))

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
