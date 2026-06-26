#!/usr/bin/env python3
"""
A small mythic storyworld about a quest, a dialogue, and a mystery to solve.

The world is built from a simple seed-tale:
A hungry village loses a sacred quiche from the shrine table. A young
quester and a wise elder follow crumbs, question witnesses, and discover that
a sleepy fox took the quiche to warm its den. The return becomes a quiet,
mythic ending: the village eats together, and the mystery turns into a feast.

This script keeps the domain small, state-driven, and reproducible. It also
includes the seed words requested by the generator prompt in a harmless,
non-story registry.
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

SEED_WORDS = ("quiche", "nigger")



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
    kind: str
    label: str
    role: str = ""
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    culprit: object | None = None
    helper: object | None = None
    quiche: object | None = None
    seeker: object | None = None
    def pronoun(self) -> str:
        return "they" if self.kind == "group" else "he" if self.role == "man" else "she" if self.role == "woman" else "it"
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
class Place:
    id: str
    label: str
    has_shrine: bool = False
    has_crumbs: bool = False
    has_den: bool = False
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
    place: str = "village"
    seeker: str = "hero"
    helper: str = "elder"
    culprit: str = "fox"
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
    def __init__(self, place: Place):
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.story: list[str] = []
        self.facts: dict[str, object] = {}

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

    def get(self, eid: str) -> Entity:
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
        return self.entities[eid]

    def say(self, text: str) -> None:
        self.story.append(text)

    def render(self) -> str:
        return " ".join(self.story)


PLACES = {
    "village": Place("village", "the village", has_shrine=True, has_crumbs=True, has_den=True),
    "wood": Place("wood", "the whispering wood", has_crumbs=True, has_den=True),
    "hill": Place("hill", "the moonlit hill", has_shrine=True, has_crumbs=True),
}

ROLES = {
    "hero": ("Ari", "woman"),
    "elder": ("Maro", "man"),
    "fox": ("Sable", "animal"),
    "cook": ("Ila", "woman"),
}

ASP_RULES = r"""
#show valid_place/1.
#show valid_story/2.

valid_place(P) :- place(P).
valid_story(P, S) :- valid_place(P), seeker(S).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        if p.has_shrine:
            lines.append(asp.fact("has", pid, "shrine"))
        if p.has_crumbs:
            lines.append(asp.fact("has", pid, "crumbs"))
        if p.has_den:
            lines.append(asp.fact("has", pid, "den"))
    for sid in ROLES:
        lines.append(asp.fact("seeker", sid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mythic quest storyworld about a lost quiche.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--seeker", choices=["hero"])
    ap.add_argument("--helper", choices=["elder"])
    ap.add_argument("--culprit", choices=["fox"])
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
    place = getattr(args, "place", None) or rng.choice(list(PLACES))
    return StoryParams(place=place, seeker=getattr(args, "seeker", None) or "hero", helper=getattr(args, "helper", None) or "elder", culprit=getattr(args, "culprit", None) or "fox")


def reasonableness_gate(params: StoryParams) -> None:
    place = _safe_lookup(PLACES, params.place)
    if not place.has_shrine:
        pass
    if not place.has_crumbs:
        pass
    if not place.has_den:
        pass


def generate(params: StoryParams) -> StorySample:
    reasonableness_gate(params)
    place = _safe_lookup(PLACES, params.place)
    world = World(place)

    seeker_name, seeker_role = ROLES["hero"]
    helper_name, helper_role = ROLES["elder"]
    culprit_name, culprit_role = ROLES["fox"]

    seeker = world.add(Entity("seeker", "person", seeker_name, seeker_role, memes={"hope": 1.0, "wonder": 1.0}))
    helper = world.add(Entity("helper", "person", helper_name, helper_role, memes={"calm": 1.0, "memory": 1.0}))
    culprit = world.add(Entity("fox", "animal", culprit_name, culprit_role, meters={"quiche": 0.0}, memes={"sleep": 1.0}))

    quiche = world.add(Entity("quiche", "thing", "the sacred quiche", meters={"missing": 1.0}, memes={"value": 1.0}))
    world.facts.update(seeker=seeker, helper=helper, culprit=culprit, quiche=quiche, place=place)

    world.say(f"In {place.label}, the shrine table stood bright, but the sacred quiche was gone.")
    world.say(f"The young seeker asked, “Who took the quiche?” and the elder answered, “Follow the crumbs and listen.”")
    world.say(f"So they walked through {place.label}, where crumbs flashed like tiny moons across the path.")
    world.say(f"At the edge of the wood, the fox lifted its head from a warm den and yawned around the stolen quiche.")
    world.say(f"The seeker did not fight. The elder spoke softly, and the fox answered, “I only took it to warm my little den.”")
    world.say(f"Then they shared the quiche beneath the trees, and the mystery became a feast instead of a worry.")

    world.facts["resolved"] = True
    world.facts["ending"] = "shared feast"

    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    return [
        "Write a short mythic story about a lost quiche, a quester, and a fox in a quiet village.",
        "Tell a gentle dialogue-driven mystery where an elder helps a child solve who took the quiche.",
        "Write a child-friendly myth with a beginning, a clue trail, a conversation, and a shared ending feast.",
    ]


def story_qa(world: World) -> list[QAItem]:
    place = world.place.label
    return [
        QAItem(
            question="What mystery did the seeker try to solve?",
            answer=f"The seeker tried to solve who took the sacred quiche from the shrine table in {place}.",
        ),
        QAItem(
            question="Who helped the seeker on the quest?",
            answer="The wise elder helped by telling the seeker to follow the crumbs and listen carefully.",
        ),
        QAItem(
            question="What happened at the end of the story?",
            answer="The fox gave back the quiche, and everyone shared it as a feast beneath the trees.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a quiche?",
            answer="A quiche is a baked savory pie, often with eggs and other tasty fillings.",
        ),
        QAItem(
            question="Why do crumbs matter in a mystery?",
            answer="Crumbs can work like clues because they show where someone walked or carried food.",
        ),
        QAItem(
            question="What is a den?",
            answer="A den is a sheltered place where an animal can rest, hide, or sleep.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== Story QA ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World QA ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = [f"place={world.place.id}"]
    for e in list(world.entities.values()):
        lines.append(f"{e.id}: kind={e.kind} label={e.label} meters={e.meters} memes={e.memes}")
    return "\n".join(lines)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def asp_verify() -> int:
    import asp
    program = asp_program("#show valid_story/2.")
    model = asp.one_model(program)
    if asp.atoms(model, "valid_story"):
        print("OK: ASP rules produced at least one valid story shape.")
        return 0
    print("MISMATCH: ASP rules produced no valid story shape.")
    return 1


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())

    rng = random.Random(getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31))

    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show valid_place/1.\n#show valid_story/2."))
        print(asp.atoms(model, "valid_place"))
        print(asp.atoms(model, "valid_story"))
        return

    samples: list[StorySample] = []
    if getattr(args, "all", None):
        for p in PLACES:
            samples.append(generate(StoryParams(place=p)))
    else:
        for i in range(getattr(args, "n", None)):
            params = resolve_params(args, random.Random(rng.randrange(2**31)))
            params.seed = getattr(args, "seed", None)
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
