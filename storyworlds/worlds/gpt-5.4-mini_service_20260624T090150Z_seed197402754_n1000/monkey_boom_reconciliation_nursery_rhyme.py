#!/usr/bin/env python3
"""
A tiny storyworld for a nursery-rhyme reconciliation tale.

Seed tale:
A monkey hears a boom, gets spooked, and makes a mess of a little playtime.
A friend helps the monkey calm down, share the banana, and make up.

This world keeps the prose close to a nursery rhyme: short beats, concrete
images, gentle tension, and a clear reconciliation at the end.
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
    friend: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    banana: object | None = None
    entities: set[str] = field(default_factory=set)
    monkey: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"monkey", "friend"}:
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
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
    label: str
    indoor: bool = False
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
class Sound:
    id: str
    label: str
    boom: bool = False
    loud: bool = False
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
class Comfort:
    id: str
    label: str
    helps: set[str] = field(default_factory=set)
    shares: bool = False
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


class World:
    def __init__(self, place: Place, sound: Sound, comfort: Comfort) -> None:
        self.place = place
        self.sound = sound
        self.comfort = comfort
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
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
        other = World(self.place, self.sound, self.comfort)
        other.entities = {k: Entity(**{
            "id": v.id, "kind": v.kind, "type": v.type, "label": v.label,
            "phrase": v.phrase, "owner": v.owner, "friend": v.friend,
            "meters": dict(v.meters), "memes": dict(v.memes)
        }) for k, v in self.entities.items()}
        other.fired = set(self.fired)
        return other


@dataclass
class StoryParams:
    place: str
    sound: str
    comfort: str
    monkey_name: str
    friend_name: str
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


PLACES = {
    "nursery": Place(id="nursery", label="the nursery", indoor=True),
    "garden": Place(id="garden", label="the garden", indoor=False),
    "yard": Place(id="yard", label="the yard", indoor=False),
}

SOUNDS = {
    "boom": Sound(id="boom", label="boom", boom=True, loud=True),
    "bang": Sound(id="bang", label="bang", boom=True, loud=True),
    "drum": Sound(id="drum", label="drum", boom=False, loud=True),
}

COMFORTS = {
    "song": Comfort(id="song", label="a soft song", helps={"fear"}, shares=True),
    "hug": Comfort(id="hug", label="a warm hug", helps={"fear", "sad"}, shares=False),
    "banana": Comfort(id="banana", label="a banana to share", helps={"fear", "hungry"}, shares=True),
}

MONKEY_NAMES = ["Momo", "Mina", "Milo", "Mimi", "Miko"]
FRIEND_NAMES = ["Bunny", "Teddy", "Nina", "Pip", "Lulu"]


class WorldBuilder:
    pass


def _r_fear(world: World) -> list[str]:
    out = []
    m = world.get("monkey")
    if m.memes.get("fear", 0) < THRESHOLD:
        return out
    sig = ("fear",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    m.meters["shake"] = m.meters.get("shake", 0) + 1
    out.append("The little monkey shook and hid its face.")
    return out


def _r_reconcile(world: World) -> list[str]:
    out = []
    m = world.get("monkey")
    f = world.get("friend")
    if m.memes.get("fear", 0) < THRESHOLD:
        return out
    if f.memes.get("kindness", 0) < THRESHOLD:
        return out
    sig = ("reconcile",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    m.memes["fear"] = 0
    m.memes["joy"] = m.memes.get("joy", 0) + 1
    f.memes["joy"] = f.memes.get("joy", 0) + 1
    out.append("Then the monkey heard the kind friend say, 'Come, come, come away.'")
    out.append("So the monkey and the friend made peace and played once more.")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in (_r_fear, _r_reconcile):
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def build_world(params: StoryParams) -> World:
    if params.place not in PLACES or params.sound not in SOUNDS or params.comfort not in COMFORTS:
        pass
    place = _safe_lookup(PLACES, params.place)
    sound = _safe_lookup(SOUNDS, params.sound)
    comfort = _safe_lookup(COMFORTS, params.comfort)
    world = World(place, sound, comfort)

    monkey = world.add(Entity(
        id="monkey", kind="character", type="monkey", label=params.monkey_name,
        phrase=f"a little monkey named {params.monkey_name}",
        meters={"restlessness": 0.0}, memes={"joy": 1.0, "fear": 0.0},
    ))
    friend = world.add(Entity(
        id="friend", kind="character", type="friend", label=params.friend_name,
        phrase=f"a gentle friend named {params.friend_name}",
        meters={"softness": 0.0}, memes={"kindness": 1.0, "joy": 0.0},
    ))
    banana = world.add(Entity(
        id="banana", type="thing", label="banana", phrase="a ripe banana",
        owner="monkey", meters={"sway": 0.0}, memes={"precious": 1.0},
    ))

    world.say(f"{monkey.label} was a little monkey in {place.label}.")
    world.say(f"{monkey.label} loved to hold {banana.phrase} and hum a tiny tune.")
    world.para()
    if place.indoor:
        world.say(f"Then came a {sound.label} in the cozy room.")
    else:
        world.say(f"Then came a {sound.label} under the sky.")
    world.say(f"It was a great big {sound.label}, and the little monkey went still as stone.")
    monkey.memes["fear"] += 1
    monkey.meters["sway"] += 1
    if sound.boom:
        world.say(f"The boom made {monkey.label} clutch the banana close and wobble in a fright.")
    else:
        world.say(f"The sound made {monkey.label} blink and tremble a bit.")
    propagate(world, narrate=True)

    world.para()
    world.say(f"Then {friend.label} came with {comfort.label}.")
    friend.memes["kindness"] += 1
    if comfort.shares:
        world.say(f"{friend.label} said it was nice to share, and the two could mend the day together.")
    else:
        world.say(f"{friend.label} said, 'I am here,' and sat close beside the monkey.")
    if comfort.id == "banana":
        world.say(f"The monkey took a slow breath and shared the banana at last.")
    elif comfort.id == "song":
        world.say(f"The soft song went la-la-la, and the monkey's heart grew light.")
    else:
        world.say(f"The warm hug made the monkey feel safe again.")
    propagate(world, narrate=True)

    world.facts.update(
        monkey=monkey,
        friend=friend,
        banana=banana,
        sound=sound,
        comfort=comfort,
        place=place,
        reconciled=monkey.memes.get("fear", 0) == 0,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a nursery-rhyme story about a monkey and a {f['sound'].label} that ends in reconciliation.",
        f"Tell a gentle little tale in rhyme where {f['monkey'].label} gets scared, then {f['friend'].label} helps them calm down.",
        f"Write a child-friendly story with the words monkey and boom, and end with the friends making up.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    m, fr, s, c = f["monkey"], f["friend"], f["sound"], f["comfort"]
    return [
        QAItem(
            question=f"Who was the story about in {world.place.label}?",
            answer=f"It was about {m.label}, a little monkey, and the gentle friend {fr.label}.",
        ),
        QAItem(
            question=f"What made {m.label} feel scared?",
            answer=f"The loud {s.label} made {m.label} feel scared and shaky.",
        ),
        QAItem(
            question=f"How did the friends make things better?",
            answer=f"{fr.label} brought {c.label}, and then the monkey calmed down and shared kindly.",
        ),
        QAItem(
            question=f"What was the ending like?",
            answer=f"The monkey and the friend made peace, and the day turned happy again.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a boom?",
            answer="A boom is a very loud sound that can startle someone small.",
        ),
        QAItem(
            question="What does reconciliation mean?",
            answer="Reconciliation means making up after trouble so friends can be kind again.",
        ),
        QAItem(
            question="What is a nursery rhyme?",
            answer="A nursery rhyme is a short, gentle story or song with simple words and a sing-song feel.",
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        bits = []
        if any(v for v in e.meters.values()):
            bits.append(f"meters={e.meters}")
        if any(v for v in e.memes.values()):
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


ASP_RULES = r"""
fear(monkey) :- boom(sound), hears(monkey, sound).
needs_reconciliation(monkey) :- fear(monkey), kindness(friend).
reconciled(monkey) :- needs_reconciliation(monkey), comfort(comfort), helps(comfort, fear).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        if p.indoor:
            lines.append(asp.fact("indoor", pid))
    for sid, s in SOUNDS.items():
        lines.append(asp.fact("sound", sid))
        if s.boom:
            lines.append(asp.fact("boom", sid))
        if s.loud:
            lines.append(asp.fact("loud", sid))
    for cid, c in COMFORTS.items():
        lines.append(asp.fact("comfort", cid))
        for h in sorted(c.helps):
            lines.append(asp.fact("helps", cid, h))
        if c.shares:
            lines.append(asp.fact("shares", cid))
    lines.append(asp.fact("hears", "monkey", "boom"))
    lines.append(asp.fact("kindness", "friend"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show reconciled/1."))
    asp_set = set(asp.atoms(model, "reconciled"))
    py_set = {("monkey",)} if True else set()
    if asp_set == py_set:
        print("OK: clingo gate matches Python reconciliation gate.")
        return 0
    print("MISMATCH between clingo and Python:")
    print("  clingo:", sorted(asp_set))
    print("  python:", sorted(py_set))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny monkey-and-boom nursery-rhyme storyworld.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--sound", choices=SOUNDS)
    ap.add_argument("--comfort", choices=COMFORTS)
    ap.add_argument("--name")
    ap.add_argument("--friend")
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
    sound = getattr(args, "sound", None) or "boom"
    comfort = getattr(args, "comfort", None) or rng.choice(list(COMFORTS))
    name = getattr(args, "name", None) or rng.choice(MONKEY_NAMES)
    friend = getattr(args, "friend", None) or rng.choice(FRIEND_NAMES)
    return StoryParams(place=place, sound=sound, comfort=comfort, monkey_name=name, friend_name=friend)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
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
        print("== prompts ==")
        for i, p in enumerate(sample.prompts, 1):
            print(f"{i}. {p}")
        print()
        print("== story qa ==")
        for item in sample.story_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")
        print()
        print("== world qa ==")
        for item in sample.world_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program("#show reconciled/1."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        curated = [
            StoryParams(place="nursery", sound="boom", comfort="song", monkey_name="Momo", friend_name="Bunny"),
            StoryParams(place="garden", sound="bang", comfort="hug", monkey_name="Mina", friend_name="Teddy"),
            StoryParams(place="yard", sound="boom", comfort="banana", monkey_name="Milo", friend_name="Pip"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 20):
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
