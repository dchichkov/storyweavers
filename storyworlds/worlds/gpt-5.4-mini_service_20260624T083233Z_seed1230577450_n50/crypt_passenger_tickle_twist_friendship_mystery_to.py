#!/usr/bin/env python3
"""
A small rhyming storyworld about a crypt, a passenger, and a tickle-filled mystery to solve.

Premise:
A careful passenger enters an old crypt with a friend. A little mystery stirs: a hidden door
won't open, and strange giggles echo in the stone. The pair must notice clues, make a twist,
and solve it through friendship instead of fear.

The world is intentionally small and state-driven:
- A passenger explores a crypt
- A soft tickle clue reveals where the mystery hides
- A twist in the path changes the plan
- Friendship helps solve the mystery
"""

from __future__ import annotations

import argparse
import json
import os
import random
import re
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


# ---------------------------------------------------------------------------
# Story model
# ---------------------------------------------------------------------------

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
    plural: bool = False
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    traits: list = field(default_factory=list)
    comp: object | None = None
    hero: object | None = None
    key: object | None = None
    mystery: object | None = None
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
class Setting:
    place: str = "the crypt"
    echo: str = "softly"
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
        return None


@dataclass
class Puzzle:
    title: str
    clue_word: str
    twist_word: str
    solved_by: str
    hidden_item: str
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
        return None


@dataclass
class StoryParams:
    setting: str
    puzzle: str
    name: str
    gender: str
    companion: str
    trait: str
    seed: Optional[int] = None
    params: object | None = None
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
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.lines: list[str] = []
        self.facts: dict[str, object] = {}

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
            self.lines.append(text)

    def render(self) -> str:
        return " ".join(self.lines).strip()


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "crypt": Setting(place="the crypt", echo="softly"),
}

PUZZLES = {
    "tickle_twist": Puzzle(
        title="tickle and twist",
        clue_word="tickle",
        twist_word="twist",
        solved_by="a friendly twist",
        hidden_item="small key",
    ),
    "mystery_light": Puzzle(
        title="mystery light",
        clue_word="mystery",
        twist_word="twist",
        solved_by="a bright twist",
        hidden_item="lantern",
    ),
}

NAMES = ["Mia", "Nora", "Leo", "Finn", "Ava", "Theo", "Zoe", "Mila"]
TRAITS = ["brave", "gentle", "curious", "cheerful", "spry", "kind"]
COMPANIONS = ["friend", "pal", "buddy"]


# ---------------------------------------------------------------------------
# Reasonableness and ASP twin
# ---------------------------------------------------------------------------
def puzzle_reasonable(puzzle: Puzzle) -> bool:
    return "tickle" in puzzle.clue_word and "twist" in puzzle.twist_word


ASP_RULES = r"""
% A puzzle is reasonable when it includes both the seed clue and the twist.
reasonable(P) :- puzzle(P), clue(P, tickle), twist(P, twist).

% A story is valid when it takes place in the crypt and uses a reasonable puzzle.
valid_story(S, P) :- setting(S, crypt), reasonable(P).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = [asp.fact("setting", "crypt")]
    for pid, p in PUZZLES.items():
        lines.append(asp.fact("puzzle", pid))
        lines.append(asp.fact("clue", pid, p.clue_word))
        lines.append(asp.fact("twist", pid, p.twist_word))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = {("crypt", pid) for pid, p in PUZZLES.items() if puzzle_reasonable(p)}
    cl = set(asp_valid_stories())
    if py == cl:
        print(f"OK: ASP matches Python ({len(py)} valid stories).")
        return 0
    print("MISMATCH between ASP and Python")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in asp:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# Narrative helpers
# ---------------------------------------------------------------------------
def rhyme(a: str, b: str) -> str:
    return f"{a} {b}"


def intro_line(hero: Entity, comp: Entity, setting: Setting) -> str:
    return (
        f"In {setting.place}, {hero.id} walked slow and bright, "
        f"with {comp.label} beside {hero.pronoun('object')} through the dim crypt night."
    )


def conflict_line(hero: Entity, puzzle: Puzzle) -> str:
    return (
        f"A hush turned to giggles, a soft little tickle, "
        f"and {hero.id} found a door that would not budge a nickel."
    )


def twist_line(hero: Entity, comp: Entity, puzzle: Puzzle) -> str:
    return (
        f"Then came the twist: {comp.label} tapped the wall with care, "
        f"and the clue hid in a stone seam near the stair."
    )


def resolution_line(hero: Entity, comp: Entity, puzzle: Puzzle) -> str:
    return (
        f"With friendship like lantern-light, they pulled the loose stone free, "
        f"and the {puzzle.hidden_item} was found for all to see."
    )


def ending_line(hero: Entity, comp: Entity) -> str:
    return (
        f"They laughed in the crypt, not scared anymore; "
        f"their friendship solved the mystery and opened the door."
    )


# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------
def build_world(params: StoryParams) -> World:
    setting = _safe_lookup(SETTINGS, params.setting)
    puzzle = _safe_lookup(PUZZLES, params.puzzle)
    world = World(setting)

    hero = world.add(Entity(
        id=params.name,
        kind="character",
        type=params.gender,
        label=params.name,
        traits=[],
        meters={"courage": 1.0},
        memes={"curiosity": 1.0, "friendship": 1.0},
    ))
    comp = world.add(Entity(
        id="Friend",
        kind="character",
        type="friend",
        label=f"a {params.trait} {params.companion}",
        meters={"help": 1.0},
        memes={"friendship": 1.0},
    ))
    mystery = world.add(Entity(
        id="Mystery",
        kind="thing",
        type="mystery",
        label="mystery",
        phrase=f"a {puzzle.title} mystery",
        meters={"hidden": 1.0},
        memes={"unsolved": 1.0},
    ))
    key = world.add(Entity(
        id="Key",
        kind="thing",
        type="key",
        label=puzzle.hidden_item,
        phrase=f"a hidden {puzzle.hidden_item}",
        meters={"hidden": 1.0},
    ))

    world.facts.update(
        hero=hero,
        friend=comp,
        mystery=mystery,
        key=key,
        setting=setting,
        puzzle=puzzle,
    )

    world.say(intro_line(hero, comp, setting))
    world.say(
        f"{hero.id} loved to explore and to solve, "
        f"and {hero.pronoun('subject')} followed the echoes with a gentle shove."
    )
    world.say(
        f"But inside the crypt there was a puzzle to find, "
        f"with a tickle in the stones and a mystery in mind."
    )
    world.say(conflict_line(hero, puzzle))
    world.say(
        f"{hero.id} listened close, then paused to think; "
        f"the clue said to look for a twist near the brink."
    )
    world.say(twist_line(hero, comp, puzzle))
    world.say(
        f"{comp.label} smiled wide and gave a small nod, "
        f"for friendship made brave steps feel easy and odd."
    )
    world.say(resolution_line(hero, comp, puzzle))
    world.say(ending_line(hero, comp))

    mystery.meters["hidden"] = 0.0
    mystery.memes["unsolved"] = 0.0
    key.meters["hidden"] = 0.0
    hero.memes["joy"] = 1.0
    hero.memes["relief"] = 1.0
    hero.memes["friendship"] = 2.0

    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = f["hero"]
    puzzle: Puzzle = f["puzzle"]
    return [
        f'Write a rhyming story for a young child about {hero.id} in a crypt, where a {puzzle.clue_word} clue leads to a twist.',
        f"Tell a gentle mystery story where friendship helps {hero.id} solve what is hidden in the crypt.",
        f'Write a short, musical tale that includes the words "crypt", "{puzzle.clue_word}", and "twist".',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    comp: Entity = f["friend"]
    puzzle: Puzzle = f["puzzle"]
    setting: Setting = f["setting"]

    return [
        QAItem(
            question=f"Where did {hero.id} go to solve the mystery?",
            answer=f"{hero.id} went to {setting.place} with {comp.label} to solve the mystery.",
        ),
        QAItem(
            question=f"What clue word helped {hero.id} notice the puzzle?",
            answer=f"The clue word was '{puzzle.clue_word}', and it led {hero.id} toward the hidden answer.",
        ),
        QAItem(
            question=f"What made the story change in a new direction?",
            answer=f"A twist in the crypt changed the plan, and {comp.label} helped {hero.id} follow the clue.",
        ),
        QAItem(
            question=f"How was the mystery solved?",
            answer=f"It was solved with friendship, careful listening, and a small stone seam that revealed {puzzle.hidden_item}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a crypt?",
            answer="A crypt is a stone room or chamber, often below a church or in an old building, where people may keep things safe.",
        ),
        QAItem(
            question="What is a passenger?",
            answer="A passenger is a person who rides in a car, train, boat, or other vehicle instead of driving it.",
        ),
        QAItem(
            question="What does tickle mean?",
            answer="To tickle is to touch someone lightly in a way that may make them laugh.",
        ),
        QAItem(
            question="What is friendship?",
            answer="Friendship means caring about someone, helping them, and having fun together.",
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


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Story interface
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Rhyming storyworld: crypt, passenger, tickle, twist, friendship, mystery.")
    ap.add_argument("--setting", choices=SETTINGS.keys(), default="crypt")
    ap.add_argument("--puzzle", choices=PUZZLES.keys(), default="tickle_twist")
    ap.add_argument("--name", choices=NAMES)
    ap.add_argument("--gender", choices=["girl", "boy"], default=None)
    ap.add_argument("--companion", choices=COMPANIONS)
    ap.add_argument("--trait", choices=TRAITS)
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
    if getattr(args, "puzzle", None):
        puzzle = _safe_lookup(PUZZLES, getattr(args, "puzzle", None))
        if not puzzle_reasonable(puzzle):
            return _fallback_storyparams(args, rng, StoryParams, globals())
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(NAMES)
    companion = getattr(args, "companion", None) or rng.choice(COMPANIONS)
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(
        setting=getattr(args, "setting", None),
        puzzle=getattr(args, "puzzle", None),
        name=name,
        gender=gender,
        companion=companion,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
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
        stories = asp_valid_stories()
        print(f"{len(stories)} valid stories:")
        for item in stories:
            print("  ", item)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        params = StoryParams(
            setting="crypt",
            puzzle="tickle_twist",
            name="Mia",
            gender="girl",
            companion="friend",
            trait="curious",
        )
        samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 20):
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

    for idx, sample in enumerate(samples):
        header = f"### variant {idx + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
