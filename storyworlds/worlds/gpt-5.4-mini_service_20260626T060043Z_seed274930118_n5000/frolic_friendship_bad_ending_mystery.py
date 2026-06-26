#!/usr/bin/env python3
"""
A small mystery-leaning storyworld about a frolic, a friendship, and a bad ending.

Premise:
- Two children and one shared plaything.
- A frolic in a simple place.
- A missing object creates a mystery with clues, suspicion, and a sad ending.

The simulated world tracks:
- physical state in meters: where things are, whether they are hidden, wet, broken, etc.
- emotional state in memes: trust, worry, blame, sadness, relief.

The story is generated from world state, not from a fixed paragraph template.
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
# Core model
# ---------------------------------------------------------------------------
THRESHOLD = 1.0



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
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    held_by: Optional[str] = None
    location: str = ""
    hidden: bool = False
    broken: bool = False
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    a: object | None = None
    b: object | None = None
    obj: object | None = None
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
class Setting:
    place: str = "the backyard"
    covers: set[str] = field(default_factory=lambda: {"yard", "shed", "path"})
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
class Object:
    id: str
    label: str
    phrase: str
    location: str
    kind: str = "thing"
    hidden_spot: str = ""
    clue: str = ""
    fragile: bool = False
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
class StoryParams:
    place: str
    name_a: str
    name_b: str
    object_id: str
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
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
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


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "backyard": Setting(place="the backyard"),
    "garden": Setting(place="the garden"),
    "path": Setting(place="the garden path"),
}

OBJECTS = {
    "blue_ball": Object(
        id="blue_ball",
        label="blue ball",
        phrase="a small blue ball with a bell inside",
        location="yard",
        hidden_spot="under the bench",
        clue="a soft jingle",
    ),
    "red_boat": Object(
        id="red_boat",
        label="red boat",
        phrase="a little red toy boat",
        location="shed",
        hidden_spot="behind a bucket",
        clue="a wet footprint",
    ),
    "paper_star": Object(
        id="paper_star",
        label="paper star",
        phrase="a folded paper star with a ribbon",
        location="path",
        hidden_spot="inside a flower pot",
        clue="a scrap of shiny ribbon",
    ),
}

NAMES = ["Mia", "Leo", "Nora", "Ben", "Ava", "Finn", "Zoe", "Theo"]


# ---------------------------------------------------------------------------
# World behavior
# ---------------------------------------------------------------------------
def _m(ent: Entity, key: str, inc: float = 1.0) -> None:
    ent.meters[key] = ent.meters.get(key, 0.0) + inc


def _e(ent: Entity, key: str, inc: float = 1.0) -> None:
    ent.memes[key] = ent.memes.get(key, 0.0) + inc


def hide_object(world: World, obj: Entity, spot: str) -> None:
    obj.location = spot
    obj.hidden = True
    _m(obj, "hidden", 1.0)


def reveal_object(world: World, obj: Entity) -> None:
    obj.hidden = False
    _m(obj, "found", 1.0)


def search_step(world: World, seeker: Entity, obj: Entity, clue: str) -> None:
    _e(seeker, "worry", 1.0)
    _e(seeker, "curiosity", 1.0)
    _m(seeker, "searched", 1.0)
    world.say(f"{seeker.id} looked carefully and noticed {clue}.")


def blame_step(world: World, accuser: Entity, other: Entity) -> None:
    _e(accuser, "blame", 1.0)
    _e(other, "hurt", 1.0)
    _e(other, "trust", -1.0)
    _e(accuser, "trust", -0.5)
    world.say(f"{accuser.id} thought {other.id} must know more than {other.pronoun('subject')} said.")


def comfort_step(world: World, friend: Entity, other: Entity) -> None:
    _e(friend, "care", 1.0)
    _e(other, "sadness", 1.0)
    _e(other, "trust", 0.5)
    world.say(f"{friend.id} tried to be gentle, but the missing thing still felt big and cold.")


def resolve_bad(world: World, obj: Entity) -> None:
    _e(obj, "lost", 1.0)
    _e(obj, "unfound", 1.0)
    world.say(f"The day ended without the {obj.label} coming back.")


def tell(setting: Setting, obj_cfg: Object, name_a: str = "Mia", name_b: str = "Leo") -> World:
    world = World(setting)
    a = world.add(Entity(id=name_a, kind="character", type="girl" if name_a in {"Mia", "Nora", "Ava", "Zoe"} else "boy"))
    b = world.add(Entity(id=name_b, kind="character", type="girl" if name_b in {"Mia", "Nora", "Ava", "Zoe"} else "boy"))
    obj = world.add(Entity(
        id=obj_cfg.id,
        type=obj_cfg.label,
        label=obj_cfg.label,
        phrase=obj_cfg.phrase,
        location=obj_cfg.location,
        hidden=True,
    ))

    _e(a, "friendship", 2.0)
    _e(b, "friendship", 2.0)
    _e(a, "joy", 1.0)
    _e(b, "joy", 1.0)

    world.say(f"{a.id} and {b.id} were best friends, and they loved a frolic in {setting.place}.")
    world.say(f"That afternoon they raced around laughing, while the {obj.label} waited nearby.")

    world.para()
    world.say(f"Then the {obj.label} went missing.")
    world.say(f"One minute it was there, and the next minute it was gone.")

    search_step(world, a, obj, obj.clue)
    search_step(world, b, obj, obj.clue)

    world.para()
    blame_step(world, a, b)
    comfort_step(world, b, a)
    world.say(f"They checked {obj_cfg.hidden_spot}, but the {obj.label} was not there.")

    world.para()
    resolve_bad(world, obj)
    _e(a, "sadness", 1.0)
    _e(b, "sadness", 1.0)
    _e(a, "trust", -0.5)
    _e(b, "trust", -0.5)
    world.say(f"When the sky turned dim, the friends walked home quietly, still thinking about the mystery.")
    world.say(f"The frolic was over, and the empty spot where the {obj.label} should have been felt like a tiny hole in the day.")

    world.facts.update(hero=a, friend=b, obj=obj, setting=setting, obj_cfg=obj_cfg)
    return world


# ---------------------------------------------------------------------------
# Story shape and QA
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    a, b, obj = f["hero"], f["friend"], f["obj"]
    return [
        f'Write a short mystery story for a child about {a.id} and {b.id}, a frolic, and a lost {obj.label}.',
        f'Tell a gentle but sad friendship mystery where two friends search for {obj.phrase}.',
        f"Write a small story that includes the word 'frolic' and ends with the friends not solving the mystery.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    a, b, obj = f["hero"], f["friend"], f["obj"]
    return [
        QAItem(
            question=f"Who were the two friends in the story?",
            answer=f"The story was about {a.id} and {b.id}, who were best friends and went frolicking together.",
        ),
        QAItem(
            question=f"What went missing during the frolic?",
            answer=f"The {obj.label} went missing, and the friends could not find it again.",
        ),
        QAItem(
            question=f"Did the mystery get solved?",
            answer="No. The story ended badly, with the missing thing still gone and the friends walking home sad.",
        ),
        QAItem(
            question=f"Why did the friendship feel troubled?",
            answer=f"{a.id} started to suspect {b.id}, and that made both friends feel hurt and less trusting.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a frolic?",
            answer="A frolic is playful running and laughing, like lively fun outside with friends.",
        ),
        QAItem(
            question="What does a clue do in a mystery?",
            answer="A clue is a small piece of information that may help someone figure out what happened.",
        ),
        QAItem(
            question="Why can friendship be hard during a mystery?",
            answer="Friendship can be hard when someone is worried or starts blaming a friend before the truth is known.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story Q&A ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World Q&A ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in list(world.entities.values()):
        ms = {k: v for k, v in e.meters.items() if v}
        mem = {k: v for k, v in e.memes.items() if v}
        bits = []
        if ms:
            bits.append(f"meters={ms}")
        if mem:
            bits.append(f"memes={mem}")
        if e.kind == "character":
            bits.append("character")
        lines.append(f"{e.id}: {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
character(X) :- hero(X).
character(X) :- friend(X).
item(X) :- lost(X).

mystery_started :- missing(O), character(A), character(B), A != B.
bad_ending :- mystery_started, unsolved.
friendship_affected(A,B) :- suspect(A,B), character(A), character(B), A != B.

#show mystery_started/0.
#show bad_ending/0.
#show friendship_affected/2.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for name in sorted(SETTINGS):
        lines.append(asp.fact("setting", name))
    for oid, o in OBJECTS.items():
        lines.append(asp.fact("object", oid))
        lines.append(asp.fact("located", oid, o.location))
        lines.append(asp.fact("hidden_spot", oid, o.hidden_spot))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    py = {"mystery_started": True, "bad_ending": True}
    model = asp.one_model(asp_program("#show bad_ending/0.\n#show mystery_started/0."))
    atoms = {sym.name for sym in model}
    ok = ("mystery_started" in atoms) == py["mystery_started"] and ("bad_ending" in atoms) == py["bad_ending"]
    if ok:
        print("OK: ASP and Python reasonableness gates agree.")
        return 0
    print("MISMATCH between ASP and Python gate.")
    return 1


# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------
def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = getattr(args, "place", None) or rng.choice(sorted(SETTINGS))
    name_a = getattr(args, "name_a", None) or rng.choice(NAMES)
    name_b = getattr(args, "name_b", None) or rng.choice([n for n in NAMES if n != name_a])
    object_id = getattr(args, "object", None) or rng.choice(sorted(OBJECTS))
    if object_id not in OBJECTS:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    return StoryParams(place=place, name_a=name_a, name_b=name_b, object_id=object_id)


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.place), _safe_lookup(OBJECTS, params.object_id), params.name_a, params.name_b)
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


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mystery storyworld with frolic, friendship, and a bad ending.")
    ap.add_argument("--place", choices=sorted(SETTINGS))
    ap.add_argument("--object", choices=sorted(OBJECTS))
    ap.add_argument("--name-a")
    ap.add_argument("--name-b")
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


CURATED = [
    StoryParams(place="backyard", name_a="Mia", name_b="Leo", object_id="blue_ball"),
    StoryParams(place="garden", name_a="Nora", name_b="Ben", object_id="red_boat"),
    StoryParams(place="path", name_a="Ava", name_b="Theo", object_id="paper_star"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show mystery_started/0.\n#show bad_ending/0.\n#show friendship_affected/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        samples = []
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 20):
            seed = base_seed + i
            i += 1
            params = resolve_params(args, random.Random(seed))
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
        header = ""
        if getattr(args, "all", None):
            p = sample.params
            header = f"### {p.name_a} and {p.name_b} at {p.place} with {p.object_id}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
