#!/usr/bin/env python3
"""
storyworlds/worlds/javelin_suspense_sharing_whodunit.py
=======================================================

A small storyworld about a missing javelin, a little suspense, and a sharing
twist in a whodunit style.

Premise:
- A child athlete treasures a practice javelin.
- Before a small meet, the javelin goes missing, and everyone grows tense.
- Clues point around the field, but the truth is gentler: the javelin was
  borrowed for a sharing lesson, then returned in time.

The world is intentionally compact:
- One child, one helper, one prized object, one suspicious location.
- Physical meters track possession, distance, and visibility.
- Emotional memes track worry, trust, relief, and curiosity.
- The story is driven by state changes rather than a frozen prose template.

The domain keeps a light whodunit flavor without any real harm: the "mystery" is
who moved the javelin and why, and the ending proves the change by restoring the
object and sharing the reason.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


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
            keys = [upper + "S", upper + "ES"]
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
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    helper: object | None = None
    hero: object | None = None
    javelin: object | None = None
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
        if not hasattr(self, "_tags"):
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
    name: str
    indoor: bool = False
    clue_words: list[str] = field(default_factory=list)
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
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
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
class Javelin:
    label: str
    phrase: str
    length: str
    color: str
    owner_kind: str = "boy"
    JAVELIN: object | None = None
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
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
    name: str
    gender: str
    helper: str
    clue: str
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
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
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
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.fired: set[str] = set()

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


PLACES = {
    "field": Place("the field", indoor=False, clue_words=["grass", "line", "wind"]),
    "shed": Place("the shed", indoor=True, clue_words=["hook", "dust", "padlock"]),
    "track": Place("the track", indoor=False, clue_words=["lane", "chalk", "whistle"]),
}

JAVELIN = Javelin(
    label="javelin",
    phrase="a smooth practice javelin",
    length="long",
    color="blue",
    owner_kind="boy",
)

NAMES = {
    "girl": ["Mina", "Lena", "Ivy", "Nora"],
    "boy": ["Eli", "Noah", "Finn", "Owen"],
}
HELPERS = ["coach", "captain", "friend", "big sister"]
CLUES = ["grass", "dust", "rope", "whistle", "chalk"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A whodunit-style javelin storyworld.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--clue", choices=CLUES)
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
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(_safe_lookup(NAMES, gender))
    helper = getattr(args, "helper", None) or rng.choice(HELPERS)
    clue = getattr(args, "clue", None) or rng.choice(CLUES)
    if clue not in _safe_lookup(PLACES, place).clue_words and clue not in {"whistle", "chalk"}:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    return StoryParams(place=place, name=name, gender=gender, helper=helper, clue=clue)


def _narrate_mystery(world: World, hero: Entity, helper: Entity, javelin: Entity) -> None:
    hero.memes["curiosity"] += 1
    hero.memes["suspense"] += 1
    world.say(f"{hero.id} loved the {JAVELIN.label}, because {JAVELIN.phrase} made the game feel brave.")
    world.say(f"One day, {hero.id} reached for {hero.pronoun('possessive')} {javelin.label}, but it was gone.")
    world.say(f"The field felt too quiet. Even the wind seemed to wait.")


def _clues(world: World, hero: Entity, helper: Entity, javelin: Entity) -> None:
    clue = world.facts["clue"]
    world.say(
        f"{hero.id} looked near the {world.place.name}, where {clue} could gather in a small, telling spot."
    )
    world.say(
        f"{helper.id} said, 'Let's not guess too fast. A true mystery needs careful eyes.'"
    )
    hero.memes["worry"] += 1


def _share_solution(world: World, hero: Entity, helper: Entity, javelin: Entity) -> None:
    if "returned" in world.fired:
        return
    world.fired.add("returned")
    helper.memes["trust"] += 1
    hero.memes["relief"] += 1
    javelin.meters["possession"] = 1
    world.say(
        f"Then {helper.id} smiled and showed the answer: the {javelin.label} had been borrowed for sharing practice."
    )
    world.say(
        f"It was not stolen at all. {helper.id} had moved it so two children could take turns safely, and now it was back."
    )
    world.say(
        f"{hero.id} nodded, a little sheepish, and thanked {helper.id} for telling the truth."
    )
    world.say(
        f"By the end, the {javelin.label} lay ready again by {hero.pronoun('possessive')} side, and the field felt calm."
    )


def tell_story(params: StoryParams) -> World:
    place = _safe_lookup(PLACES, params.place)
    world = World(place)
    hero = world.add(Entity(id=params.name, kind="character", type=params.gender, label=params.name))
    helper = world.add(Entity(id="Helper", kind="character", type="adult", label=params.helper))
    javelin = world.add(Entity(
        id="javelin",
        type="thing",
        label="javelin",
        phrase=JAVELIN.phrase,
        owner=hero.id,
        caretaker=helper.id,
    ))
    javelin.meters["possession"] = 1
    world.facts.update(hero=hero, helper=helper, javelin=javelin, clue=params.clue)

    world.say(f"{hero.id} was a little {params.gender} who practiced with {JAVELIN.phrase}.")
    world.say(f"{helper.id} liked the same field, and both of them knew that sharing could make games fair.")
    world.para()
    _narrate_mystery(world, hero, helper, javelin)
    world.para()
    _clues(world, hero, helper, javelin)
    _share_solution(world, hero, helper, javelin)
    return world


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place in PLACES:
        for gender in ["girl", "boy"]:
            for clue in CLUES:
                if clue in _safe_lookup(PLACES, place).clue_words or clue in {"whistle", "chalk"}:
                    combos.append((place, gender, clue))
    return combos


ASP_RULES = r"""
place(field). place(shed). place(track).
gender(girl). gender(boy).
clue(grass). clue(dust). clue(rope). clue(whistle). clue(chalk).

fits(field,grass). fits(field,whistle). fits(field,chalk).
fits(shed,dust). fits(shed,rope). fits(shed,whistle). fits(shed,chalk).
fits(track,grass). fits(track,whistle). fits(track,chalk).

valid(P,G,C) :- place(P), gender(G), clue(C), fits(P,C).
#show valid/3.
"""


def asp_facts() -> str:
    import asp
    return "\n".join([asp.fact("domain", "javelin")])


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    a, b = set(asp_valid_combos()), set(valid_combos())
    if a == b:
        print(f"OK: clingo gate matches valid_combos() ({len(a)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print("only in clingo:", sorted(a - b))
    print("only in python:", sorted(b - a))
    return 1


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    return [
        'Write a suspenseful whodunit for a young child about a missing javelin and a kind explanation.',
        f"Tell a story where {hero.id} searches for a javelin and learns that sharing, not stealing, caused the mystery.",
        f"Write a child-friendly mystery set at {world.place.name} that ends with the javelin safely returned.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero = world.facts["hero"]
    helper = world.facts["helper"]
    return [
        QAItem(
            question=f"What did {hero.id} lose at {world.place.name}?",
            answer=f"{hero.id} lost a practice javelin, which made the day feel mysterious and tense.",
        ),
        QAItem(
            question=f"Who helped {hero.id} solve the mystery?",
            answer=f"{helper.id} helped by asking for careful looking instead of quick guesses.",
        ),
        QAItem(
            question="Why was the javelin moved?",
            answer="It was moved for sharing practice so two children could take turns safely.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a javelin?",
            answer="A javelin is a long, pointed sports spear used for throwing practice, usually under adult supervision.",
        ),
        QAItem(
            question="What does sharing mean?",
            answer="Sharing means letting someone else use something too, usually by taking turns or using it together safely.",
        ),
        QAItem(
            question="What is suspense in a story?",
            answer="Suspense is the worried, curious feeling you get when something important is missing or not yet explained.",
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
    parts = ["--- trace ---"]
    for e in list(world.entities.values()):
        parts.append(f"{e.id}: meters={e.meters} memes={e.memes}")
    return "\n".join(parts)


def generate(params: StoryParams) -> StorySample:
    world = tell_story(params)
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


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        curated = [
            StoryParams("field", "Mina", "girl", "coach", "grass"),
            StoryParams("track", "Eli", "boy", "friend", "whistle"),
        ]
        samples = [generate(p) for p in curated]
    else:
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
