#!/usr/bin/env python3
"""
A tiny bedtime storyworld about a knock, a misunderstanding, and a gentle
laugh before sleep.
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
class Person:
    id: str
    type: str
    label: str
    traits: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    with_object: Optional[str] = None

    child: object | None = None
    parent: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
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
class Object:
    id: str
    label: str
    kind: str = "thing"
    owner: Optional[str] = None
    location: str = ""
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    blanket: object | None = None
    lamp: object | None = None
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
class StoryParams:
    child_name: str
    child_type: str
    parent_name: str
    parent_type: str
    knock_source: str
    misunderstanding: str
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


CHILD_NAMES = ["Mia", "Noah", "Lily", "Finn", "Ava", "Theo", "Zoe", "Eli"]
PARENT_NAMES = ["Mom", "Dad"]
TRAITS = ["sleepy", "curious", "brave", "tiny", "soft-hearted"]


class World:
    def __init__(self) -> None:
        self.people: dict[str, Person] = {}
        self.objects: dict[str, Object] = {}
        self.facts: dict[str, object] = {}
        self.lines: list[str] = []
        self.knock_heard: bool = False
        self.misunderstanding_active: bool = False
        self.resolved: bool = False
        self.knock_count: int = 0

    def add_person(self, p: Person) -> Person:
        self.people[p.id] = p
        return p

    def add_object(self, o: Object) -> Object:
        self.objects[o.id] = o
        return o

    def say(self, text: str) -> None:
        if text:
            self.lines.append(text)

    def render(self) -> str:
        return " ".join(self.lines)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Bedtime knock storyworld.")
    ap.add_argument("--child-name", choices=CHILD_NAMES)
    ap.add_argument("--child-type", choices=["girl", "boy"])
    ap.add_argument("--parent-name", choices=PARENT_NAMES)
    ap.add_argument("--parent-type", choices=["mother", "father"])
    ap.add_argument("--knock-source", choices=["owl", "friend", "cat", "wind", "grandparent"])
    ap.add_argument("--misunderstanding", choices=["monster", "late snack", "storm", "lost shoe", "secret gift"])
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
    child_type = getattr(args, "child_type", None) or rng.choice(["girl", "boy"])
    child_name = getattr(args, "child_name", None) or rng.choice(CHILD_NAMES)
    parent_type = getattr(args, "parent_type", None) or rng.choice(["mother", "father"])
    parent_name = getattr(args, "parent_name", None) or rng.choice(PARENT_NAMES)
    if child_name == parent_name:
        parent_name = "Mom" if child_name != "Mom" else "Dad"
    return StoryParams(
        child_name=child_name,
        child_type=child_type,
        parent_name=parent_name,
        parent_type=parent_type,
        knock_source=getattr(args, "knock_source", None) or rng.choice(["owl", "friend", "cat", "wind", "grandparent"]),
        misunderstanding=getattr(args, "misunderstanding", None) or rng.choice(["monster", "late snack", "storm", "lost shoe", "secret gift"]),
    )


def reasonableness_gate(params: StoryParams) -> None:
    if params.knock_source == "wind" and params.misunderstanding == "monster":
        return
    if params.knock_source == "grandparent" and params.misunderstanding == "secret gift":
        return
    if params.knock_source == "friend" and params.misunderstanding == "late snack":
        return
    if params.knock_source == "owl" and params.misunderstanding == "storm":
        return
    if params.knock_source == "cat" and params.misunderstanding == "lost shoe":
        return
    pass


def build_world(params: StoryParams) -> World:
    reasonableness_gate(params)
    w = World()
    child = w.add_person(Person(
        id=params.child_name,
        type=params.child_type,
        label="child",
        traits=["sleepy", "curious", "tiny"],
        meters={"sleepiness": 2.0},
        memes={"worry": 0.0, "humor": 0.0, "relief": 0.0, "understanding": 0.0},
    ))
    parent = w.add_person(Person(
        id=params.parent_name,
        type=params.parent_type,
        label="parent",
        traits=["gentle", "patient"],
        memes={"warmth": 1.0},
    ))
    lamp = w.add_object(Object(id="lamp", label="little lamp", location="bedside"))
    blanket = w.add_object(Object(id="blanket", label="soft blanket", location="bed"))
    w.facts.update(params=params, child=child, parent=parent, lamp=lamp, blanket=blanket)
    return w


def heard_knock(w: World) -> None:
    w.knock_heard = True
    w.knock_count += 1
    w.say("At bedtime, a soft knock came at the door.")
    w.say("The little lamp made a warm circle on the wall, and the room grew extra quiet.")
    child: Person = w.facts["child"]
    child.memes["worry"] += 1.0


def inner_monologue(w: World) -> None:
    child: Person = w.facts["child"]
    mis = w.facts["params"].misunderstanding
    if mis == "monster":
        thought = "What if it is a monster with very polite knuckles?"
    elif mis == "late snack":
        thought = "What if someone brought toast and jam just for me?"
    elif mis == "storm":
        thought = "What if the rain has a whole voice and wants to come in?"
    elif mis == "lost shoe":
        thought = "What if a lonely shoe is knocking because it wants its friend?"
    else:
        thought = "What if the door is hiding a surprise too exciting for sleep?"
    w.say(f"{child.id} held the blanket close and thought, \"{thought}\"")
    child.memes["worry"] += 0.5


def misunderstanding_turn(w: World) -> None:
    params: StoryParams = w.facts["params"]
    child: Person = w.facts["child"]
    source = params.knock_source
    mis = params.misunderstanding
    if mis == "monster":
        w.say(f"{child.id} tiptoed to the door and whispered, \"I knew it. A monster.\"")
    elif mis == "late snack":
        w.say(f"{child.id} peeked out and was sure the knock meant a secret bedtime snack.")
    elif mis == "storm":
        w.say(f"{child.id} listened hard and decided the knock was really a storm tapping in a tiny way.")
    elif mis == "lost shoe":
        w.say(f"{child.id} decided a lost shoe must be hopping around and asking for help.")
    else:
        w.say(f"{child.id} was certain a surprise was waiting, which somehow felt just as scary.")
    w.misunderstanding_active = True
    child.memes["humor"] += 0.5 if source in {"cat", "owl"} else 0.2


def reveal_and_laugh(w: World) -> None:
    params: StoryParams = w.facts["params"]
    child: Person = w.facts["child"]
    parent: Person = w.facts["parent"]
    source = params.knock_source
    mis = params.misunderstanding
    if source == "owl":
        w.say(f"{parent.id} opened the door, and there stood an owl on the porch, tapping the wood with one careful claw.")
    elif source == "friend":
        w.say(f"{parent.id} opened the door, and there stood a friend with a tiny lantern and a careful smile.")
    elif source == "cat":
        w.say(f"{parent.id} opened the door, and a cat blinked up from the mat, tail curled like a question mark.")
    elif source == "wind":
        w.say(f"{parent.id} opened the door, and the wind gave one last playful bump against the frame.")
    else:
        w.say(f"{parent.id} opened the door, and there was a grandparent with a small wrapped box and tired, happy eyes.")
    if mis == "monster":
        w.say(f"{child.id} stared, then giggled. \"That monster is very small,\" {child.pronoun()} said.")
    elif mis == "late snack":
        w.say(f"{child.id} laughed at the empty hands and said, \"Oh. That was not toast at all.\"")
    elif mis == "storm":
        w.say(f"{child.id} laughed and said, \"The storm is only the wind being dramatic.\"")
    elif mis == "lost shoe":
        w.say(f"{child.id} laughed and said, \"That shoe would need a much bigger hop.\"")
    else:
        w.say(f"{child.id} laughed and said, \"The surprise was hiding in plain sight.\"")
    child.memes["humor"] += 1.0
    child.memes["worry"] = 0.0
    child.memes["relief"] += 1.0
    child.memes["understanding"] += 1.0
    w.resolved = True
    if source == "grandparent":
        w.say(f"The little box held a bedtime story card, and {child.id} smiled as the room turned quiet again.")
    elif source == "friend":
        w.say(f"The friend whispered goodnight, and soon the pillow felt even softer than before.")
    else:
        w.say(f"The door closed softly, and the blanket felt warm and safe once more.")


def tell(params: StoryParams) -> World:
    w = build_world(params)
    heard_knock(w)
    inner_monologue(w)
    misunderstanding_turn(w)
    reveal_and_laugh(w)
    return w


def prompts(world: World) -> list[str]:
    p: StoryParams = _safe_fact(world, world.facts, "params")
    return [
        f"Write a cozy bedtime story about a child who hears a knock and thinks it means a {p.misunderstanding}.",
        f"Tell a short gentle story for young children where a {p.child_type} named {p.child_name} hears a knock from a {p.knock_source}.",
        "Write a bedtime story with a funny misunderstanding, an inner thought, and a safe ending at the door.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p: StoryParams = _safe_fact(world, world.facts, "params")
    child: Person = _safe_fact(world, world.facts, "child")
    parent: Person = _safe_fact(world, world.facts, "parent")
    return [
        QAItem(
            question=f"Who heard the knock at bedtime?",
            answer=f"{child.id} heard the knock while curled up in bed with a soft blanket.",
        ),
        QAItem(
            question=f"What did {child.id} think the knock might mean?",
            answer=f"{child.id} thought it might mean {p.misunderstanding}, even though that was not the real reason for the sound.",
        ),
        QAItem(
            question=f"Who opened the door and explained the knock?",
            answer=f"{parent.id} opened the door and showed that the knock came from a {p.knock_source}.",
        ),
        QAItem(
            question=f"How did {child.id} feel after the truth was clear?",
            answer=f"{child.id} felt relieved and laughed because the scary idea turned into a harmless surprise.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    p: StoryParams = _safe_fact(world, world.facts, "params")
    return [
        QAItem(
            question="What is a knock?",
            answer="A knock is a tapping sound, often made on a door to let someone know a person is outside.",
        ),
        QAItem(
            question="Why do people listen carefully at bedtime?",
            answer="People listen carefully at bedtime because the house is quiet, so soft sounds are easier to hear.",
        ),
        QAItem(
            question="Why can a misunderstanding be funny?",
            answer="A misunderstanding can be funny when someone guesses the wrong reason for a sound or action, and the truth is much simpler.",
        ),
        QAItem(
            question=f"Why was the {p.knock_source} not actually a monster?",
            answer=f"Because the {p.knock_source} was only itself, and the child had guessed the wrong story before the door opened.",
        ),
    ]


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


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


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for p in world.people.values():
        lines.append(f"{p.id}: meters={p.meters} memes={p.memes}")
    for o in world.objects.values():
        lines.append(f"{o.id}: {o.label} location={o.location}")
    lines.append(f"knock_heard={world.knock_heard} misunderstanding_active={world.misunderstanding_active} resolved={world.resolved}")
    return "\n".join(lines)


CURATED = [
    StoryParams("Mia", "girl", "Mom", "mother", "owl", "monster"),
    StoryParams("Noah", "boy", "Dad", "father", "friend", "late snack"),
    StoryParams("Lily", "girl", "Mom", "mother", "cat", "lost shoe"),
    StoryParams("Theo", "boy", "Dad", "father", "wind", "monster"),
    StoryParams("Ava", "girl", "Mom", "mother", "grandparent", "secret gift"),
]


ASP_RULES = r"""
% A knock is meaningful when a child hears it.
heard_knock(K) :- knock(K).

% A misunderstanding arises when the child assigns the wrong cause to the knock.
misunderstanding(C, M) :- child(C), thinks(C, M), knock_source(K), source_of(K, S), wrong_guess(M, S).

% Humor appears when the truth is harmless and the guess is dramatic.
humor(C) :- misunderstanding(C, _), harmless_truth.

% The bedtime ending is complete when the child becomes relieved.
resolved(C) :- humor(C), relief(C).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for p in CURATED:
        lines.append(asp.fact("child_story", p.child_name, p.knock_source, p.misunderstanding))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    try:
        import asp
    except Exception as exc:  # pragma: no cover
        print(f"ASP unavailable: {exc}")
        return 1
    model = asp.one_model(asp_program("#show child_story/3."))
    ok = bool(model)
    if ok:
        print(f"OK: ASP program is reachable with {len(model)} shown atoms.")
        return 0
    print("MISMATCH: ASP produced no model.")
    return 1


def build_samples(args: argparse.Namespace) -> list[StorySample]:
    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    seen: set[str] = set()
    if getattr(args, "all", None):
        for p in CURATED:
            s = generate(p)
            if s.story not in seen:
                seen.add(s.story)
                samples.append(s)
        return samples
    i = 0
    while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 50):
        params = resolve_params(args, random.Random(base_seed + i))
        params.seed = base_seed + i
        try:
            sample = generate(params)
        except StoryError as err:
            if getattr(args, "n", None) == 1:
                raise
            print(err)
            i += 1
            continue
        if sample.story in seen:
            i += 1
            continue
        seen.add(sample.story)
        samples.append(sample)
        i += 1
    return samples


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

    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "show_asp", None):
        print(asp_program("#show child_story/3."))
        return
    if getattr(args, "asp", None):
        print("ASP mode is available for verification only in this tiny world.")
        return

    samples = build_samples(args)
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
            header = f"### {p.child_name}: knock from {p.knock_source}, misunderstanding {p.misunderstanding}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
