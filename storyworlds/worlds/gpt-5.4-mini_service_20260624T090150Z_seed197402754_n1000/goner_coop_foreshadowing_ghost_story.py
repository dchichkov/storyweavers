#!/usr/bin/env python3
"""
Storyworld: goner coop foreshadowing ghost story

A small, standalone story world about an old coop that looks like a goner,
a spooky night with foreshadowing clues, and a gentle ghost-story turn that
ends in a clear change: the coop is no longer a goner, and the fear settles.
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
    kind: str = "thing"   # character | thing | place
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    coop: object | None = None
    hero: object | None = None
    lantern: object | None = None
    parent: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother", "grandmother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father", "grandfather"}:
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
    place: str
    outdoors: bool = True
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
    hero_name: str
    hero_type: str
    parent_type: str
    seed: Optional[int] = None
    params: list = field(default_factory=list)
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
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


SETTINGS = {
    "farm": Setting(place="the farm"),
    "yard": Setting(place="the back yard"),
    "coop": Setting(place="the old coop"),
}

HERO_NAMES = ["Mina", "Ivy", "Toby", "June", "Eli", "Pip", "Nora", "Theo"]
HERO_TYPES = ["girl", "boy"]
PARENT_TYPES = ["mother", "father", "grandmother", "grandfather"]

# A small ghost-story vocabulary, with the seed words included in prose/world.
FORESHADOW_SIGNS = [
    "a cold draft under the door",
    "a loose board that tapped softly in the dark",
    "one pale feather on the step",
    "a lantern that gave one quick flicker",
    "a hush so deep the chickens did not cluck",
]

ASP_RULES = r"""
% A place is spooky when it contains enough foreshadowing signs.
spooky(P) :- sign(P, cold_draft).
spooky(P) :- sign(P, pale_feather).
spooky(P) :- sign(P, flicker).
safe(P) :- lantern_on(P), locked_door(P).
valid_story(P) :- spooky(P), safe(P).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid in SETTINGS:
        lines.append(asp.fact("place", pid))
    lines.append(asp.fact("sign", "coop", "cold_draft"))
    lines.append(asp.fact("sign", "coop", "pale_feather"))
    lines.append(asp.fact("sign", "coop", "flicker"))
    lines.append(asp.fact("lantern_on", "coop"))
    lines.append(asp.fact("locked_door", "coop"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_combos() -> list[tuple[str]]:
    return [("coop",)]


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/1."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print("  only in python:", sorted(py - cl))
    print("  only in clingo:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small ghost-story world about an old coop.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=PARENT_TYPES)
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
    if place not in valid_places():
        return _fallback_storyparams(args, rng, StoryParams, globals())
    gender = getattr(args, "gender", None) or rng.choice(HERO_TYPES)
    name = getattr(args, "name", None) or rng.choice(HERO_NAMES)
    parent = getattr(args, "parent", None) or rng.choice(PARENT_TYPES)
    return StoryParams(place=place, hero_name=name, hero_type=gender, parent_type=parent)


def valid_places() -> set[str]:
    return {"coop"}


def generate(params: StoryParams) -> StorySample:
    world = World(_safe_lookup(SETTINGS, params.place))
    hero = world.add(Entity(id=params.hero_name, kind="character", type=params.hero_type))
    parent = world.add(Entity(id="Parent", kind="character", type=params.parent_type, label="the parent"))
    coop = world.add(Entity(id="Coop", kind="place", type="place", label="the old coop"))
    lantern = world.add(Entity(id="Lantern", kind="thing", type="lantern", label="lantern", owner=hero.id))
    lantern.worn_by = hero.id

    # Physical/emotional state
    hero.memes.update(fear=0.0, curiosity=0.0, relief=0.0, wonder=0.0)
    coop.meters.update(rots=1.0, creak=1.0, dark=1.0, fixed=0.0)
    coop.memes.update(spooky=0.0)
    lantern.meters.update(light=0.0)

    # Act 1: setup with foreshadowing.
    world.say(f"{hero.id} and {hero.pronoun('possessive')} {parent.label} came to {world.setting.place}.")
    world.say("The old coop looked like a goner, with a bent latch and boards that sighed in the wind.")
    world.say("Even so, a tiny part of the dark seemed to be waiting for them.")
    world.para()
    world.say("First came a cold draft under the door.")
    world.say("Then came one pale feather on the step.")
    world.say("Then came a lantern that gave one quick flicker, as if it knew a secret.")
    hero.memes["curiosity"] += 1.0
    coop.memes["spooky"] += 1.0

    # Act 2: tension.
    world.para()
    world.say(f'{hero.id} whispered, "Is the coop haunted?"')
    hero.memes["fear"] += 1.0
    world.say(f"{hero.pronoun().capitalize()} wanted to run, but {hero.pronoun('possessive')} {parent.label} held up the lantern.")
    lantern.meters["light"] = 1.0
    world.say("The warm light made the shadows shrink, and the floorboards stopped sounding so mean.")
    world.say("From inside came a soft peep, not a boo.")
    world.say("That was the clue the foreshadowing had been saving all along.")
    hero.memes["wonder"] += 1.0

    # Act 3: turn and resolution.
    world.para()
    world.say("Behind a broken crate, they found a tiny chick with one dirty wing and a stuck foot.")
    world.say("The 'ghost' was only a lost little bird that had been hiding in the dark.")
    world.say(f"{hero.id} and {hero.pronoun('possessive')} {parent.label} cleaned the coop, fixed the latch, and made a soft nest of straw.")
    coop.meters["fixed"] = 1.0
    coop.memes["spooky"] = 0.0
    hero.memes["fear"] = 0.0
    hero.memes["relief"] += 1.0
    world.say("Soon the coop did not feel like a goner at all.")
    world.say(f"It looked sturdy in the lantern light, and {hero.id} smiled at the little chick peeking from the straw.")
    world.say(f'{hero.id} said, "I thought it was a ghost, but it was just someone who needed help."')

    world.facts = {
        "hero": hero,
        "parent": parent,
        "coop": coop,
        "lantern": lantern,
    }

    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    return [
        "Write a gentle ghost story for a young child about a coop that looks like a goner but is not.",
        f"Tell a spooky-but-kind story where {hero.id} notices clues, feels scared, and then learns what is really inside the coop.",
        "Write a short story that uses foreshadowing clues like a cold draft, a pale feather, and a flickering lantern.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, parent, coop = f["hero"], f["parent"], f["coop"]
    return [
        QAItem(
            question=f"Why did {hero.id} think the coop might be haunted?",
            answer="Because it was dark, creaky, and full of spooky clues that seemed like foreshadowing."
        ),
        QAItem(
            question=f"What was the scary sound inside the coop really?",
            answer="It was a soft peep from a tiny lost chick, not a ghost."
        ),
        QAItem(
            question=f"How did {hero.id} and {parent.label} help the coop?",
            answer="They cleaned it, fixed the latch, and made a soft nest of straw so it felt safe again."
        ),
        QAItem(
            question=f"Why was the coop no longer a goner at the end?",
            answer="Because it was repaired and safe, and the dark spooky feeling was gone."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is foreshadowing in a story?",
            answer="Foreshadowing is when a story gives small clues early that help you guess what may happen later."
        ),
        QAItem(
            question="Why can a lantern help at night?",
            answer="A lantern gives light, so people can see the path, the door, and what is hiding in the dark."
        ),
        QAItem(
            question="What is a coop?",
            answer="A coop is a small shelter where chickens live and sleep."
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
    lines.append("== (3) World knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:8} ({e.kind:8}) {' '.join(bits)}")
    return "\n".join(lines)


def explain_rejection() -> str:
    return "(No story: this world only tells stories at the old coop.)"


def asp_valid_story() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/1."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_facts_and_rules() -> str:
    return asp_program("")


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
        print(asp_program("#show valid_story/1."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        vals = asp_valid_story()
        print(f"{len(vals)} valid story combo(s):")
        for v in vals:
            print(" ", v)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        params = [StoryParams(place="coop", hero_name="Mina", hero_type="girl", parent_type="mother")]
        samples = [generate(p) for p in params]
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
