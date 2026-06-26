#!/usr/bin/env python3
"""
territory_bike_lane_foreshadowing_tall_tale.py

A tiny storyworld about a child defending a bike-lane territory in a tall-tale
style, with foreshadowing that hints at a much bigger ride to come.
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
# Shared physical / emotional model.
# ---------------------------------------------------------------------------

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
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    carried_by: Optional[str] = None
    near: str = ""
    plural: bool = False
    protective: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    giant: object | None = None
    hero: object | None = None
    marker: object | None = None
    parent: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
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
class Territory:
    place: str = "the bike lane"
    boundary: str = "the white line"
    markers: tuple[str, ...] = ("cones", "chalk", "flag")
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
class Foreshadow:
    sign: str
    meaning: str
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
    def __init__(self, territory: Territory) -> None:
        self.territory = territory
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}

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

    def copy(self) -> "World":
        import copy as _copy
        w = World(self.territory)
        w.entities = _copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        return w


# ---------------------------------------------------------------------------
# Registries.
# ---------------------------------------------------------------------------

TERRITORIES = {
    "bike_lane": Territory(place="the bike lane", boundary="the white line", markers=("cones", "chalk", "flag")),
}

FORESHADOWS = {
    "bell": Foreshadow(
        sign="a faraway bicycle bell",
        meaning="a bigger ride was coming",
    ),
    "shadow": Foreshadow(
        sign="a long moving shadow",
        meaning="something tall would soon roll by",
    ),
    "wind": Foreshadow(
        sign="a gust that fluttered the little flag",
        meaning="the lane would not stay quiet for long",
    ),
}


@dataclass
class StoryParams:
    territory: str
    foreshadow: str
    hero_name: str
    hero_type: str
    parent_type: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Reasoning rules.
# ---------------------------------------------------------------------------
    params: object | None = None
    sample: object | None = None
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


def territory_is_marked(world: World) -> bool:
    return any(world.entities[eid].meters.get("set", 0) >= THRESHOLD for eid in world.entities if eid.startswith("marker_"))


def _r_intrusion(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    giant = world.get("giant_wheel")
    if hero.meters.get("guarding", 0) < THRESHOLD:
        return out
    if giant.meters.get("approach", 0) < THRESHOLD:
        return out
    if ("intrusion",) in world.fired:
        return out
    world.fired.add(("intrusion",))
    hero.memes["alarm"] = hero.memes.get("alarm", 0) + 1
    out.append("A bigger ride was coming close to the white line.")
    return out


def _r_solution(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    parent = world.get("parent")
    giant = world.get("giant_wheel")
    if hero.memes.get("alarm", 0) < THRESHOLD:
        return out
    if hero.meters.get("moved_markers", 0) < THRESHOLD:
        return out
    if giant.meters.get("pass", 0) < THRESHOLD:
        return out
    if ("solution",) in world.fired:
        return out
    world.fired.add(("solution",))
    hero.memes["pride"] = hero.memes.get("pride", 0) + 1
    parent.memes["admire"] = parent.memes.get("admire", 0) + 1
    out.append("The lane stayed safe because the markers were moved and the big wheels passed by.")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in (_r_intrusion, _r_solution):
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


# ---------------------------------------------------------------------------
# Story actions.
# ---------------------------------------------------------------------------

def introduce(world: World, hero: Entity) -> None:
    world.say(f"{hero.id} was a little {hero.type} with a bright stare and a big sense of territory.")
    world.say(f"{hero.pronoun().capitalize()} loved the bike lane because it felt like {hero.pronoun('possessive')} own long road to adventure.")


def mark_territory(world: World, hero: Entity) -> None:
    hero.meters["guarding"] = hero.meters.get("guarding", 0) + 1
    for i, m in enumerate(TERRITORIES["bike_lane"].markers, 1):
        marker = world.add(Entity(id=f"marker_{i}", type=m, label=m, near=TERRITORIES["bike_lane"].boundary))
        marker.meters["set"] = 1
    world.say(f"{hero.id} lined up three markers beside {TERRITORIES['bike_lane'].boundary} and claimed the lane with a nod.")
    world.say("The lane looked neat and brave, like a narrow ribbon waiting for a parade.")


def foreshadow(world: World, sign: Foreshadow, hero: Entity) -> None:
    world.say(f"Before long, {sign.sign} drifted down the street.")
    world.say(f"{hero.id} looked up, and the air seemed to whisper that {sign.meaning}.")
    world.facts["foreshadow_sign"] = sign.sign
    world.facts["foreshadow_meaning"] = sign.meaning


def giant_arrives(world: World) -> None:
    giant = world.add(Entity(id="giant_wheel", kind="thing", type="bicycle", label="giant bicycle", near="the bike lane"))
    giant.meters["approach"] = 1
    world.say("Then came a bicycle so tall that its front wheel looked like a moon with spokes.")
    world.say("It rolled closer and closer, and even the painted line seemed to hold its breath.")
    propagate(world, narrate=True)
    giant.meters["pass"] = 1


def move_markers(world: World, hero: Entity, parent: Entity) -> None:
    hero.meters["moved_markers"] = 1
    hero.memes["courage"] = hero.memes.get("courage", 0) + 1
    parent.memes["help"] = parent.memes.get("help", 0) + 1
    world.say(f"{hero.id} did not bolt. {hero.pronoun().capitalize()} scooped up the markers and slid them back from the edge.")
    world.say(f"{parent.id} pointed to a safer strip and said the territory could be smart as well as bold.")


def ending(world: World, hero: Entity, parent: Entity) -> None:
    world.say("The giant bicycle thundered by, but it stayed in its own track.")
    world.say(f"When the wind settled, {hero.id} stood by the lane with {hero.pronoun('possessive')} markers in place, grinning like a tiny sheriff.")
    world.say(f"{parent.id} laughed and said the bike lane had never looked more peaceful.")


def tell(params: StoryParams) -> World:
    world = World(_safe_lookup(TERRITORIES, params.territory))
    hero = world.add(Entity(id=params.hero_name, kind="character", type=params.hero_type))
    parent = world.add(Entity(id="parent", kind="character", type=params.parent_type, label="parent"))

    introduce(world, hero)
    world.para()
    mark_territory(world, hero)
    foreshadow(world, _safe_lookup(FORESHADOWS, params.foreshadow), hero)
    world.para()
    giant_arrives(world)
    move_markers(world, hero, parent)
    propagate(world, narrate=True)
    world.para()
    ending(world, hero, parent)

    world.facts.update(
        hero=hero,
        parent=parent,
        territory=world.territory,
        foreshadow=_safe_lookup(FORESHADOWS, params.foreshadow),
        giant=world.get("giant_wheel"),
        resolved=True,
    )
    return world


# ---------------------------------------------------------------------------
# QA and prompts.
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    hero: Entity = _safe_fact(world, world.facts, "hero")
    foreshadow: Foreshadow = _safe_fact(world, world.facts, "foreshadow")
    return [
        f"Write a short tall tale for children set in the bike lane, where {hero.id} notices {foreshadow.sign} before a huge surprise arrives.",
        f"Tell a foreshadowing story about a child who defends a bike lane territory and keeps it safe with markers.",
        "Write a playful tall tale in which a little guardian reads the signs and makes a clever choice before the big wheels roll through.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero: Entity = _safe_fact(world, world.facts, "hero")
    parent: Entity = _safe_fact(world, world.facts, "parent")
    foreshadow: Foreshadow = _safe_fact(world, world.facts, "foreshadow")
    return [
        QAItem(
            question=f"What kind of place was {hero.id} guarding?",
            answer=f"{hero.id} was guarding the bike lane, a narrow stretch of territory by the white line.",
        ),
        QAItem(
            question=f"What sign hinted that something bigger was coming?",
            answer=f"The story hinted at {foreshadow.sign}, which meant {foreshadow.meaning}.",
        ),
        QAItem(
            question=f"How did {hero.id} and {parent.id} keep the lane safe?",
            answer=f"They moved the markers back from the edge so the giant bicycle could pass without trouble.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended with {hero.id} still smiling beside the marked lane, while {parent.id} laughed and the road stayed calm.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a bike lane?",
            answer="A bike lane is a part of the road set aside for bicycles, so riders have a safer place to go.",
        ),
        QAItem(
            question="What is foreshadowing in a story?",
            answer="Foreshadowing is a clue that hints something important may happen later in the story.",
        ),
        QAItem(
            question="Why do people use cones or chalk to mark a space?",
            answer="People use cones or chalk to show where a space begins and ends, so everyone can see the boundary clearly.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
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


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.near:
            bits.append(f"near={e.near}")
        lines.append(f"  {e.id:12} ({e.type:10}) {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin.
# ---------------------------------------------------------------------------

ASP_RULES = r"""
territory(bike_lane).
marker(cones).
marker(chalk).
marker(flag).

foreshadow(bell).
foreshadow(shadow).
foreshadow(wind).

acts_as_sign(bell, hearing).
acts_as_sign(shadow, seeing).
acts_as_sign(wind, feeling).

valid_story(T, F) :- territory(T), foreshadow(F).
"""


def asp_facts() -> str:
    import asp
    lines = [asp.fact("territory", "bike_lane")]
    for m in ("cones", "chalk", "flag"):
        lines.append(asp.fact("marker", m))
    for f in ("bell", "shadow", "wind"):
        lines.append(asp.fact("foreshadow", f))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    asp_set = set(asp.atoms(model, "valid_story"))
    py_set = {("bike_lane", k) for k in FORESHADOWS}
    if asp_set != py_set:
        print("MISMATCH between clingo and Python:")
        print("  only in asp:", sorted(asp_set - py_set))
        print("  only in python:", sorted(py_set - asp_set))
        return 1
    sample = generate(StoryParams(territory="bike_lane", foreshadow="bell", hero_name="Nia", hero_type="girl", parent_type="father"))
    if not sample.story or "bike lane" not in sample.story:
        print("Story verification failed.")
        return 1
    print("OK: ASP parity and generated story check passed.")
    return 0


# ---------------------------------------------------------------------------
# Parameters, generation, emit.
# ---------------------------------------------------------------------------

NAMES = ["Nia", "Milo", "June", "Owen", "Piper", "Jasper", "Lena", "Rowan"]
HERO_TYPES = ["girl", "boy"]
PARENT_TYPES = ["mother", "father"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall-tale storyworld about territory, foreshadowing, and a bike lane.")
    ap.add_argument("--territory", choices=TERRITORIES)
    ap.add_argument("--foreshadow", choices=FORESHADOWS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
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
    territory = getattr(args, "territory", None) or "bike_lane"
    foreshadow = getattr(args, "foreshadow", None) or rng.choice(list(FORESHADOWS))
    gender = getattr(args, "gender", None) or rng.choice(HERO_TYPES)
    name = getattr(args, "name", None) or rng.choice(NAMES)
    parent = getattr(args, "parent", None) or rng.choice(PARENT_TYPES)
    if territory not in TERRITORIES:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    if foreshadow not in FORESHADOWS:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    return StoryParams(territory=territory, foreshadow=foreshadow, hero_name=name, hero_type=gender, parent_type=parent)


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
        print(asp_program("#show valid_story/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show valid_story/2."))
        atoms = sorted(set(asp.atoms(model, "valid_story")))
        print(f"{len(atoms)} compatible stories:")
        for t in atoms:
            print(" ", t)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if getattr(args, "all", None):
        for f in FORESHADOWS:
            params = StoryParams("bike_lane", f, random.choice(NAMES), random.choice(HERO_TYPES), random.choice(PARENT_TYPES))
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 50):
            rng = random.Random(base_seed + i)
            i += 1
            try:
                params = resolve_params(args, rng)
            except StoryError:
                continue
            params.seed = base_seed + i
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
