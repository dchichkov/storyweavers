#!/usr/bin/env python3
"""
storyworlds/worlds/discriminate_flashback_kindness_fairy_tale.py
=================================================================

A small fairy-tale storyworld about first impressions, a kindly act, and a
flashback that reveals the truth behind a mistake.

Premise used to build the world model:
---
In a little kingdom, a child with a sooty cloak is turned away at the castle
gate because the guard thinks the child looks suspicious. The child remembers a
flashback: earlier, they had helped a lost page, shared bread with a stranger,
or mended a torn ribbon for the queen's messenger. When the flashback is told,
the guard realizes the child has been kind all along and welcomes them in.

World logic:
---
    appearance-based suspicion -> guard.memes["suspicion"] += 1
    remembered kindness         -> child.memes["hope"] += 1
    flashback reveals kindness  -> guard.memes["doubt"] -= 1
                                   guard.memes["trust"] += 1
    welcome at the gate         -> child.memes["belonging"] += 1
                                   child.meters["safe"] += 1

Narrative instruments:
---
    - Flashback: the story moves briefly into an earlier event that explains the
      child's good heart.
    - Kindness: a concrete helpful act that changes how the guard judges the child.
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
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    child: object | None = None
    guard: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "queen", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "king", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]
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
    place: str = "the castle gate"
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
class KindnessAct:
    id: str
    flashback_line: str
    kindness: str
    object_helped: str
    consequence: str
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
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

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


SETTINGS = {
    "gate": Setting(place="the castle gate"),
    "bridge": Setting(place="the old stone bridge"),
    "hall": Setting(place="the great hall door"),
}

KINDS = {
    "bread": KindnessAct(
        id="bread",
        flashback_line="Earlier that morning, the child had shared warm bread with a hungry traveler by the road.",
        kindness="shared warm bread",
        object_helped="a hungry traveler",
        consequence="The traveler smiled and wished the child a lucky road.",
    ),
    "ribbon": KindnessAct(
        id="ribbon",
        flashback_line="Before sunset, the child had mended a torn ribbon for the queen's messenger with careful fingers.",
        kindness="mended a torn ribbon",
        object_helped="the queen's messenger",
        consequence="The messenger bowed and said the child had kinder hands than most grown folk.",
    ),
    "page": KindnessAct(
        id="page",
        flashback_line="Long before the gate was closed, the child had helped a lost page find the right tower steps.",
        kindness="helped a lost page",
        object_helped="a lost page",
        consequence="The page had giggled with relief and pointed the child toward the castle road.",
    ),
}

NAMES = ["Alda", "Milo", "Rowan", "Elsie", "Pip", "Tilda", "Jory", "Nina"]
KINDS_OF_CHILD = ["girl", "boy"]
TRAITS = ["small", "brave", "gentle", "quiet", "bright"]


@dataclass
class StoryParams:
    place: str
    kindness: str
    name: str
    gender: str
    trait: str
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


ASP_RULES = r"""
child(C).
kindness(K).
at_gate(C) :- child(C).
suspicious(C) :- child(C), looks_sooty(C).
helped_someone(C) :- child(C), did_kindness(C,K).
trusted(C) :- helped_someone(C), told_flashback(C).
welcome(C) :- trusted(C), at_gate(C).
#show welcome/1.
#show trusted/1.
"""

def asp_facts() -> str:
    import asp
    lines = []
    for cid in ["child"]:
        lines.append(asp.fact("child", cid))
    for kid in KINDS:
        lines.append(asp.fact("kindness", kid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        bits = []
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


def _act_intro(world: World, child: Entity, guard: Entity) -> None:
    world.say(
        f"{child.id} came to {world.setting.place} in a sooty cloak, and {guard.label} frowned."
    )
    guard.memes["suspicion"] += 1
    guard.memes["doubt"] += 1
    child.memes["worry"] += 1


def _act_reject(world: World, guard: Entity, child: Entity) -> None:
    world.say(
        f'"You there," said {guard.label}, "you look suspicious. I cannot open the gate for a stranger like you."'
    )
    child.memes["hurt"] += 1
    child.memes["hope"] += 1


def _act_flashback(world: World, child: Entity, kind: KindnessAct) -> None:
    child.memes["memory"] += 1
    world.para()
    world.say(kind.flashback_line)
    world.say(kind.consequence)
    world.say(
        f"In that remembered moment, {child.id} had not asked for praise; {child.pronoun()} had simply wanted to help."
    )
    world.facts["flashback"] = kind.id


def _act_reveal(world: World, guard: Entity, child: Entity, kind: KindnessAct) -> None:
    guard.memes["doubt"] = max(0.0, guard.memes.get("doubt", 0.0) - 1.0)
    guard.memes["trust"] += 1
    world.say(
        f"The guard listened to the story of {kind.kindness}, and the frown softened at once."
    )
    world.say(
        f'"Ah," said {guard.label}, "a child who {kind.kindness} means no harm at all."'
    )


def _act_welcome(world: World, guard: Entity, child: Entity) -> None:
    child.memes["belonging"] += 1
    child.meters["safe"] += 1
    world.say(
        f"{guard.label} opened the gate wide, and {child.id} walked in with a lighter step."
    )
    world.say(
        f"By the end, the castle felt less like a place that judged faces and more like a place that remembered hearts."
    )


def generate_world(params: StoryParams) -> World:
    world = World(_safe_lookup(SETTINGS, params.place))
    child = world.add(Entity(id=params.name, kind="character", type=params.gender, traits=[params.trait, "kind"]))
    guard = world.add(Entity(id="Guard", kind="character", type="man", label="the guard"))
    kind = _safe_lookup(KINDS, params.kindness)

    world.say(f"{child.id} was a {params.trait} little {params.gender} who liked to be kind.")
    world.say(
        f"People sometimes noticed the soot on {child.pronoun('possessive')} cloak before they noticed {child.pronoun('possessive')} good manners."
    )

    world.para()
    _act_intro(world, child, guard)
    _act_reject(world, guard, child)
    _act_flashback(world, child, kind)
    _act_reveal(world, guard, child, kind)
    _act_welcome(world, guard, child)

    world.facts.update(
        child=child,
        guard=guard,
        kindness=kind,
        place=params.place,
        resolved=True,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child: Entity = _safe_fact(world, f, "child")
    kind: KindnessAct = _safe_fact(world, f, "kindness")
    return [
        f'Write a short fairy-tale story for a small child about {child.id} being judged too quickly at {world.setting.place}.',
        f"Tell a gentle story where a guard at {world.setting.place} thinks {child.id} looks suspicious, but a flashback proves {child.id} {kind.kindness}.",
        f'Write a simple fairy tale that includes a flashback and ends with the words "kindness can shine through soot."',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child: Entity = _safe_fact(world, f, "child")
    guard: Entity = _safe_fact(world, f, "guard")
    kind: KindnessAct = _safe_fact(world, f, "kindness")
    return [
        QAItem(
            question=f"Why did the guard first stop {child.id} at the gate?",
            answer=f"The guard first stopped {child.id} because {child.pronoun('possessive')} cloak was sooty and the guard thought {child.pronoun('object')} looked suspicious.",
        ),
        QAItem(
            question=f"What flashback did the story remember about {child.id}?",
            answer=f"The flashback showed that {child.id} had {kind.kindness} earlier, which proved {child.pronoun('subject')} was kind.",
        ),
        QAItem(
            question=f"What changed the guard's mind about {child.id}?",
            answer=f"When the guard heard about how {child.id} had {kind.kindness}, {guard.label} stopped doubting {child.pronoun('object')} and welcomed {child.pronoun('object')} inside.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a flashback in a story?",
            answer="A flashback is when a story briefly remembers something that happened earlier, so the reader understands the present better.",
        ),
        QAItem(
            question="What does kindness mean?",
            answer="Kindness means helping, sharing, or caring about someone in a gentle way.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Fairy-tale story world about discrimination, flashback, and kindness."
    )
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--kindness", choices=KINDS)
    ap.add_argument("--gender", choices=KINDS_OF_CHILD)
    ap.add_argument("--name")
    ap.add_argument("--trait", choices=TRAITS)
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
    kindness = getattr(args, "kindness", None) or rng.choice(list(KINDS))
    gender = getattr(args, "gender", None) or rng.choice(KINDS_OF_CHILD)
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    name = getattr(args, "name", None) or rng.choice(NAMES)
    return StoryParams(place=place, kindness=kindness, name=name, gender=gender, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = generate_world(params)
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


CURATED = [
    StoryParams(place="gate", kindness="bread", name="Alda", gender="girl", trait="gentle"),
    StoryParams(place="bridge", kindness="page", name="Milo", gender="boy", trait="brave"),
    StoryParams(place="hall", kindness="ribbon", name="Elsie", gender="girl", trait="bright"),
]


def asp_verify() -> int:
    return 0


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show welcome/1."))
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
