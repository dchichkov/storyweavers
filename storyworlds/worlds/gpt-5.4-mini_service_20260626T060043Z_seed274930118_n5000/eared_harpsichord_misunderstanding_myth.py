#!/usr/bin/env python3
"""
A small myth-style story world about a misunderstood eared harpsichord:
a creature, a missing sound, a mistaken warning, and a gentle reveal.

The world is built as a classical simulation with meters and memes.
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
    worn_by: Optional[str] = None
    plural: bool = False
    protective: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    artifact: object | None = None
    elder: object | None = None
    hero: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"king", "boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in {"queen", "girl", "woman", "mother", "maiden"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
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
    place: str
    tag: str = "myth"
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
class Artifact:
    label: str
    phrase: str
    type: str
    mood: str
    sound: str
    risk: str
    guards: set[str] = field(default_factory=set)
    room: str = "hall"
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
class Helper:
    id: str
    label: str
    phrase: str
    fix_word: str
    clears: set[str]
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


def _narrate_misunderstanding(world: World, listener: Entity, artifact: Entity) -> list[str]:
    out: list[str] = []
    if listener.memes.get("doubt", 0) < THRESHOLD:
        return out
    sig = ("misunderstanding", listener.id, artifact.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    listener.memes["fear"] = listener.memes.get("fear", 0) + 1
    out.append(f"{listener.id} took the silence for a warning and stepped back.")
    out.append(f"That made the hall feel colder, as if a shadow had touched the strings.")
    return out


def _narrate_reveal(world: World, listener: Entity, artifact: Entity) -> list[str]:
    out: list[str] = []
    sig = ("reveal", listener.id, artifact.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    listener.memes["fear"] = max(0.0, listener.memes.get("fear", 0) - 1)
    listener.memes["wonder"] = listener.memes.get("wonder", 0) + 1
    out.append(
        f"Then the truth came clear: the {artifact.label} had been built with little ears "
        f"to catch the air, not with a beast hidden inside."
    )
    return out


def tell(world: World, hero: Entity, elder: Entity, artifact: Entity, helper: Helper) -> None:
    world.say(
        f"In the old {world.setting.place}, {hero.id} kept watch over the {artifact.label}, "
        f"a gift with {artifact.phrase}."
    )
    world.say(
        f"It was said that the {artifact.label} sang only when the right hands touched it, "
        f"and when they did, its {artifact.sound} would fill the stones."
    )
    hero.memes["love"] = hero.memes.get("love", 0) + 1
    world.say(
        f"{hero.id} loved the instrument, yet often listened to its quiet face and wondered "
        f"why the tiny ears on its frame seemed to watch the room."
    )

    world.para()
    world.say(
        f"One dusk, {elder.id} heard the stillness and frowned. "
        f'"The {artifact.label} has lost its spirit," {elder.pronoun("subject")} said. '
        f'"Those ears mean a watcher has come to steal the song."'
    )
    elder.memes["doubt"] = elder.memes.get("doubt", 0) + 1
    world.say(
        f"{hero.id} heard the warning and grew worried, because the old words of the court "
        f"could turn a small doubt into a heavy fear."
    )
    world.say("So the hall became quiet, and even the torches seemed to hold their breath.")
    for line in _narrate_misunderstanding(world, elder, artifact):
        world.say(line)

    world.para()
    world.say(
        f"Then {helper.id} came forward with a calm face and a light step. "
        f'"Wait," {helper.id} said, "the ears are not a curse. They are a craft."'
    )
    world.say(
        f"{helper.id} lifted the veil from the side of the {artifact.label} and showed how the "
        f"{helper.phrase} kept the strings tuned. "
        f"It was not a warning at all, but a clever way to listen better."
    )
    elder.memes["doubt"] = 0
    for line in _narrate_reveal(world, elder, artifact):
        world.say(line)

    world.say(
        f"{elder.id} lowered {elder.pronoun('possessive')} head and let the mistake fall away. "
        f'"I mistook a sign for a threat," {elder.pronoun("subject")} said.'
    )
    world.say(
        f"At last {hero.id} played, and the {artifact.label} answered with a bright and steady song. "
        f"The ears on its frame did not hide danger; they carried music home."
    )


SETTING = Setting(place="mythic hall")

ARTIFACTS = {
    "eared_harpsichord": Artifact(
        label="eared harpsichord",
        phrase="small carved ears at its sides",
        type="harpsichord",
        mood="mysterious",
        sound="silver notes",
        risk="misunderstanding",
        guards={"silence"},
        room="hall",
    )
}

HELPERS = {
    "sage": Helper(
        id="Sage",
        label="sage",
        phrase="little hollow channels",
        fix_word="explain",
        clears={"doubt", "fear"},
    )
}


@dataclass
class StoryParams:
    artifact: str = "eared_harpsichord"
    helper: str = "sage"
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mythic misunderstanding around an eared harpsichord.")
    ap.add_argument("--artifact", choices=ARTIFACTS, default="eared_harpsichord")
    ap.add_argument("--helper", choices=HELPERS, default="sage")
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
    return StoryParams(artifact=getattr(args, "artifact", None) or rng.choice(list(ARTIFACTS)), helper=getattr(args, "helper", None) or rng.choice(list(HELPERS)))


def generation_prompts(world: World) -> list[str]:
    return [
        "Write a short myth where a strange instrument is misunderstood before a wiser voice reveals the truth.",
        "Tell a gentle legend about an eared harpsichord, a fear born from silence, and a clearing of doubt.",
        "Write a child-friendly myth in which a misunderstood music-making object is finally understood.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    artifact: Entity = _safe_fact(world, f, "artifact")
    hero: Entity = _safe_fact(world, f, "hero")
    elder: Entity = _safe_fact(world, f, "elder")
    return [
        QAItem(
            question="What was the important object in the story?",
            answer=f"It was the {artifact.label}, a {artifact.type} with small ears on its sides.",
        ),
        QAItem(
            question="Why did the elder worry at first?",
            answer=f"{elder.id} thought the silence meant the {artifact.label} had lost its spirit, but that was a misunderstanding.",
        ),
        QAItem(
            question="What changed at the end?",
            answer=f"The truth was explained, the fear went away, and {hero.id} heard the {artifact.label} sing again.",
        ),
    ]


WORLD_KNOWLEDGE = [
    QAItem(
        question="What is a harpsichord?",
        answer="A harpsichord is an old keyboard instrument that makes bright, plucked sounds when it is played.",
    ),
    QAItem(
        question="What is a misunderstanding?",
        answer="A misunderstanding happens when someone thinks something means one thing, but it really means another.",
    ),
    QAItem(
        question="Why do people tell myths?",
        answer="People tell myths to share old stories that explain wonders, fears, and lessons in a memorable way.",
    ),
]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return WORLD_KNOWLEDGE


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"  {e.id:10} ({e.type:12}) meters={meters} memes={memes}")
    lines.append(f"  fired rules: {sorted({x[0] for x in world.fired})}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== (3) World-knowledge questions ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


ASP_RULES = r"""
artifact(A) :- artifact(A).
misunderstanding(A) :- artifact(A), not understood(A).
understood(A) :- revealed(A).
resolved(A) :- understood(A), not misunderstanding(A).
"""


def asp_facts() -> str:
    import asp
    lines = [asp.fact("artifact", "eared_harpsichord"), asp.fact("revealed", "eared_harpsichord")]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    return 0


def valid_combos() -> list[tuple[str, str]]:
    return [("eared_harpsichord", "sage")]


CURATED = [
    StoryParams(artifact="eared_harpsichord", helper="sage", seed=274930118),
]


def generate(params: StoryParams) -> StorySample:
    world = World(SETTING)
    hero = world.add(Entity(id="Lyra", kind="character", type="girl"))
    elder = world.add(Entity(id="Orion", kind="character", type="man"))
    artifact = world.add(Entity(
        id="harpsichord", kind="thing", type="harpsichord",
        label="eared harpsichord", phrase="small carved ears at its sides",
    ))
    helper = _safe_lookup(HELPERS, params.helper)

    tell(world, hero, elder, artifact, helper)

    world.facts.update(hero=hero, elder=elder, artifact=artifact, helper=helper)
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
        print(asp_program("#show misunderstanding/1.\n#show resolved/1."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())

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
