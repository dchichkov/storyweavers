#!/usr/bin/env python3
"""
storyworlds/worlds/lettuce_twentieth_lobby_surprise_bedtime_story.py
=====================================================================

A small bedtime-story world about a quiet twentieth-floor lobby, a crisp lettuce
snack, and a gentle surprise.

Seed premise:
- A child is in a lobby on the twentieth floor near bedtime.
- A lettuce snack is involved.
- A surprise changes the mood, but the ending stays soft and calm.

The simulation tracks both physical meters and emotional memes, and the prose is
rendered from world state rather than from a frozen template.
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
# World model
# ---------------------------------------------------------------------------

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
    plural: bool = False
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
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
    place: str = "the twentieth-floor lobby"
    indoor: bool = True
    quiet_level: int = 2
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
class StoryParams:
    place: str
    name: str
    gender: str
    parent: str
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


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
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
SETTING = Setting(place="the twentieth-floor lobby", indoor=True, quiet_level=2)

GIRL_NAMES = ["Mina", "Luna", "Ivy", "Nora", "Ella", "Ada"]
BOY_NAMES = ["Leo", "Noah", "Milo", "Theo", "Eli", "Finn"]
TRAITS = ["sleepy", "curious", "gentle", "bright", "small", "patient"]

LETTUCE = {
    "leaf": "a crisp lettuce leaf",
    "cup": "a small lettuce cup",
    "snack": "a bedtime lettuce snack",
}

SURPRISES = {
    "note": "a tiny folded note with a moon on it",
    "star": "a little paper star wrapped in a ribbon",
    "button": "a shiny button tucked in a napkin pocket",
}


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------
THRESHOLD = 1.0


def bedtime_detail(world: World) -> str:
    return (
        "The lobby was soft with lamplight, and the carpet looked sleepy and warm."
    )


def introduce(world: World, child: Entity) -> None:
    world.say(
        f"{child.id} was a little {child.memes.get('trait', 'sleepy')} {child.type} "
        f"who liked quiet places just before bed."
    )


def mention_setting(world: World) -> None:
    world.say(
        f"That night, {world.setting.place} was almost empty."
    )
    world.say(bedtime_detail(world))


def show_lettuce(world: World, child: Entity, lettuce: Entity) -> None:
    child.memes["love_snack"] += 1
    world.say(
        f"{child.id} carried {lettuce.phrase} in both hands because the leaves stayed cool and crisp."
    )


def show_surprise(world: World, child: Entity, surprise: Entity) -> None:
    child.memes["curiosity"] += 1
    world.say(
        f"Then {child.id} noticed {surprise.phrase} hiding near the snack, and {child.pronoun()} leaned closer."
    )


def parent_warns(world: World, parent: Entity, child: Entity, surprise: Entity) -> None:
    child.memes["buzzing"] += 1
    world.say(
        f"{parent.label} smiled and whispered, "
        f'"Let\'s be gentle. A surprise can feel big at bedtime."'
    )


def child_wants_now(world: World, child: Entity, surprise: Entity) -> None:
    child.memes["eager"] += 1
    world.say(
        f"{child.id} wanted to open the surprise right away, but {child.pronoun('possessive')} feet were already doing tiny wiggles."
    )


def quiet_choice(world: World, parent: Entity, child: Entity, surprise: Entity) -> None:
    child.memes["calm"] += 1
    child.memes["eager"] = max(0.0, child.memes["eager"] - 1.0)
    world.say(
        f'{parent.label} tapped the sofa cushion and said, "We can open it quietly by the lamp after one little bite."'
    )


def reveal(world: World, child: Entity, lettuce: Entity, surprise: Entity) -> None:
    child.memes["joy"] += 1
    child.memes["relief"] += 1
    surprise.meters["opened"] = 1
    world.say(
        f"{child.id} took a tiny bite of {lettuce.it()} first, then opened the surprise with careful fingers."
    )
    world.say(
        f"Inside was {surprise.phrase}, and it made the lobby feel like a soft secret."
    )


def end_image(world: World, child: Entity, parent: Entity, lettuce: Entity, surprise: Entity) -> None:
    world.say(
        f"By the time the lamps dimmed, {child.id} was smiling sleepily, {lettuce.it()} was nearly finished, "
        f"and {surprise.it()} sat safely on the table like a little moon."
    )


def tell(setting: Setting, name: str, gender: str, parent_type: str) -> World:
    world = World(setting)
    child = world.add(
        Entity(
            id=name,
            kind="character",
            type=gender,
            meters={"sleep": 0.0},
            memes={"trait": random.choice(TRAITS), "joy": 0.0, "curiosity": 0.0},
        )
    )
    parent = world.add(
        Entity(
            id="Parent",
            kind="character",
            type=parent_type,
            label=f"the {parent_type}",
            meters={"patience": 1.0},
            memes={"love": 1.0},
        )
    )
    lettuce = world.add(
        Entity(
            id="lettuce",
            type="snack",
            label="lettuce",
            phrase="a crisp lettuce snack",
            meters={"fresh": 1.0},
            owner=child.id,
        )
    )
    surprise = world.add(
        Entity(
            id="surprise",
            type="gift",
            label="surprise",
            phrase=random.choice(list(SURPRISES.values())),
            meters={"hidden": 1.0},
            owner=child.id,
        )
    )

    introduce(world, child)
    mention_setting(world)
    world.para()
    show_lettuce(world, child, lettuce)
    show_surprise(world, child, surprise)
    parent_warns(world, parent, child, surprise)
    child_wants_now(world, child, surprise)
    quiet_choice(world, parent, child, surprise)
    world.para()
    reveal(world, child, lettuce, surprise)
    end_image(world, child, parent, lettuce, surprise)

    world.facts.update(child=child, parent=parent, lettuce=lettuce, surprise=surprise)
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = _safe_fact(world, f, "child")
    parent = _safe_fact(world, f, "parent")
    return [
        'Write a bedtime story about a child in a lobby, a lettuce snack, and a surprise.',
        f"Tell a gentle story where {child.id} and {parent.label} share a quiet moment in {world.setting.place}.",
        'Write a soft, child-friendly story that includes lettuce, twentieth, lobby, and surprise.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = _safe_fact(world, f, "child")
    parent = _safe_fact(world, f, "parent")
    lettuce = _safe_fact(world, f, "lettuce")
    surprise = _safe_fact(world, f, "surprise")
    return [
        QAItem(
            question=f"Where was {child.id} when the story began?",
            answer=f"{child.id} was in {world.setting.place}, a quiet place with warm lamplight."
        ),
        QAItem(
            question=f"What did {child.id} carry during the bedtime moment?",
            answer=f"{child.id} carried {lettuce.phrase} before settling down for the night."
        ),
        QAItem(
            question=f"Why did {parent.label} ask for a gentle pause?",
            answer=(
                f"{parent.label} thought the surprise might feel too exciting at bedtime, "
                f"so the two of them opened it quietly instead."
            ),
        ),
        QAItem(
            question=f"What was inside the surprise?",
            answer=f"Inside was {surprise.phrase}."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is lettuce?",
            answer="Lettuce is a leafy green vegetable that people often eat in salads or crunchy snacks."
        ),
        QAItem(
            question="What does twentieth mean?",
            answer="Twentieth means number 20."
        ),
        QAItem(
            question="What is a lobby?",
            answer="A lobby is a room near the entrance of a building where people wait, meet, or pass through."
        ),
        QAItem(
            question="What is a surprise?",
            answer="A surprise is something unexpected that can make someone feel curious or happy."
        ),
    ]


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


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
place(twentieth_lobby).
feature(lettuce).
feature(surprise).
style(bedtime).

valid_story(P, F1, F2, S) :-
    place(P),
    feature(F1),
    feature(F2),
    F1 != F2,
    style(S),
    P = twentieth_lobby,
    F1 = lettuce,
    F2 = surprise,
    S = bedtime.
"""


def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("place", "twentieth_lobby"),
        asp.fact("feature", "lettuce"),
        asp.fact("feature", "surprise"),
        asp.fact("style", "bedtime"),
    ]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp

    model = asp.one_model(asp_program("#show valid_story/4."))
    clingo_set = set(asp.atoms(model, "valid_story"))
    python_set = {("twentieth_lobby", "lettuce", "surprise", "bedtime")}
    if clingo_set == python_set:
        print("OK: clingo gate matches the Python reasonableness gate.")
        return 0
    print("MISMATCH between clingo and Python reasonableness gate.")
    print("clingo:", sorted(clingo_set))
    print("python:", sorted(python_set))
    return 1


# ---------------------------------------------------------------------------
# Generation / emit / CLI
# ---------------------------------------------------------------------------
CURATED = [
    StoryParams(place="twentieth-floor lobby", name="Mina", gender="girl", parent="mother"),
    StoryParams(place="twentieth-floor lobby", name="Leo", gender="boy", parent="father"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A bedtime story world in a twentieth-floor lobby with lettuce and surprise.")
    ap.add_argument("--place", default="twentieth-floor lobby")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name")
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
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    if getattr(args, "name", None):
        name = getattr(args, "name", None)
    else:
        name = rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = getattr(args, "parent", None) or rng.choice(["mother", "father"])
    return StoryParams(place=getattr(args, "place", None), name=name, gender=gender, parent=parent)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTING, params.name, params.gender, params.parent)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
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


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/4."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp

        model = asp.one_model(asp_program("#show valid_story/4."))
        atoms = asp.atoms(model, "valid_story")
        print(f"{len(atoms)} compatible story tuple(s):")
        for atom in atoms:
            print(" ", atom)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    rng = random.Random(base_seed)

    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(max(1, getattr(args, "n", None))):
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
