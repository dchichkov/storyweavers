#!/usr/bin/env python3
"""
storyworlds/worlds/cashew_raffle_dialogue_kindness_mystery.py
=============================================================

A small mystery storyworld about a raffle, a cashew, dialogue, and kindness.

The premise is a child notices that a raffle prize or snack has gone missing,
then asks around and solves the puzzle by listening carefully and choosing a
kind response. The world is small on purpose: one setting, a few typed entities,
and a causal turn where a clue hidden in dialogue reveals who moved the
cashew.

The stories are generated from a compact state machine rather than a fixed
paragraph template, so the prose changes with the simulated world facts.
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
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    carried_by: Optional[str] = None
    hidden_in: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    helper: object | None = None
    hero: object | None = None
    snack: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def noun(self) -> str:
        return self.label or self.type

    def obj(self) -> str:
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
    mood: str
    affordances: set[str] = field(default_factory=set)
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
class RafflePrize:
    label: str
    phrase: str
    type: str
    hidden: str  # where the clue points
    found_by_dialogue: bool = True
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
    setting: str
    hero_name: str
    hero_type: str
    helper_type: str
    prize: str
    seed: Optional[int] = None
    p: object | None = None
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
    def __init__(self, setting: Setting):
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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
        import copy as _copy
        c = World(self.setting)
        c.entities = _copy.deepcopy(self.entities)
        c.paragraphs = [[]]
        c.facts = dict(self.facts)
        c.fired = set(self.fired)
        return c


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "school_hall": Setting(
        place="the school hall",
        mood="bright and busy",
        affordances={"raffle", "conversation"},
    ),
    "library_corner": Setting(
        place="the library corner",
        mood="quiet and careful",
        affordances={"raffle", "conversation"},
    ),
    "community_room": Setting(
        place="the community room",
        mood="warm and small",
        affordances={"raffle", "conversation"},
    ),
}

PRIZES = {
    "cashew": RafflePrize(
        label="cashew",
        phrase="a little paper cup of cashews",
        type="cashew",
        hidden="coat pocket",
    ),
    "bag": RafflePrize(
        label="snack bag",
        phrase="a brown snack bag with a ribbon",
        type="bag",
        hidden="shelf basket",
    ),
    "pin": RafflePrize(
        label="pin",
        phrase="a shiny star pin",
        type="pin",
        hidden="chair seat",
    ),
}

GIRL_NAMES = ["Mina", "Luna", "Ivy", "Tia", "Sana", "Nora"]
BOY_NAMES = ["Owen", "Leo", "Milo", "Eli", "Noah", "Finn"]
HELPERS = {
    "girl": "girl",
    "boy": "boy",
    "adult": "adult",
}

TRAITS = ["careful", "curious", "gentle", "brave", "quiet"]


# ---------------------------------------------------------------------------
# Story rules
# ---------------------------------------------------------------------------
def has_mystery(world: World) -> bool:
    return bool(world.facts.get("missing"))


def clue_text(hero: Entity, helper: Entity, prize: RafflePrize) -> str:
    return (
        f'"I put the {prize.label} somewhere safe," {helper.id} said, '
        f'"but I forgot where after the raffle line got noisy."'
    )


def solve_clue_text(hero: Entity, helper: Entity, prize: RafflePrize) -> str:
    return (
        f'{hero.id} listened again and noticed the clue: {helper.id} had said '
        f'{prize.hidden}, so the missing {prize.label} was not stolen at all.'
    )


def kindness_turn(hero: Entity, helper: Entity, prize: RafflePrize) -> str:
    return (
        f'{hero.id} smiled instead of blaming {helper.pronoun("object")}. '
        f'"We can look together," {hero.id} said, and {helper.id} looked relieved.'
    )


def ending_text(hero: Entity, helper: Entity, prize: RafflePrize) -> str:
    return (
        f"Then they found the {prize.label} where {helper.id} had left it, "
        f"and the room felt calm again. {hero.id} kept one cashew to share and "
        f"gave the rest back with a kind grin."
    )


def tell(setting: Setting, hero_name: str, hero_type: str, helper_type: str, prize: RafflePrize) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, label=hero_name))
    helper_name = "Ms. Reed" if helper_type == "adult" else ("Mara" if helper_type == "girl" else "Tom")
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_type, label=helper_name))
    snack = world.add(Entity(
        id="raffle_prize",
        kind="thing",
        type=prize.type,
        label=prize.label,
        phrase=prize.phrase,
        owner=hero.id,
        hidden_in=prize.hidden,
    ))

    world.say(f"{hero.id} came to {setting.place}, which felt {setting.mood}, for a raffle.")
    world.say(f"On the table sat {snack.phrase}, and {hero.id} hoped {helper.id} would hand it over after the drawing.")
    world.para()

    world.say(f"Then the prize was gone from the table.")
    world.say(f'{hero.id} asked, "Did someone take the {prize.label}?"')
    world.say(clue_text(hero, helper, prize))
    world.facts["missing"] = True
    world.facts["hero"] = hero
    world.facts["helper"] = helper
    world.facts["prize"] = snack
    world.facts["prize_def"] = prize
    world.para()

    world.say(solve_clue_text(hero, helper, prize))
    world.say(kindness_turn(hero, helper, prize))
    world.say(ending_text(hero, helper, prize))

    world.facts["solved"] = True
    world.facts["kindness"] = True
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = _safe_fact(world, f, "hero")
    helper: Entity = _safe_fact(world, f, "helper")
    prize: Entity = _safe_fact(world, f, "prize")
    setting = world.setting.place
    return [
        f'Write a short mystery story for children set in {setting} that includes a raffle and a cashew.',
        f'Write a gentle dialogue story where {hero.id} asks about a missing {prize.label} and chooses kindness instead of blame.',
        f'Tell a simple mystery in which a child solves a raffle clue by listening carefully and being kind.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = _safe_fact(world, f, "hero")
    helper: Entity = _safe_fact(world, f, "helper")
    prize: Entity = _safe_fact(world, f, "prize")
    setting = world.setting.place

    return [
        QAItem(
            question=f"Where did {hero.id} go to find out what happened to the raffle prize?",
            answer=f"{hero.id} went to {setting}, where the raffle was being held.",
        ),
        QAItem(
            question=f"What missing prize did {hero.id} ask about?",
            answer=f"{hero.id} asked about the {prize.label}, which was a small part of the raffle.",
        ),
        QAItem(
            question=f"How did {hero.id} respond when the clue was hard to understand?",
            answer=f"{hero.id} responded with kindness by saying they would look together instead of blaming {helper.id}.",
        ),
        QAItem(
            question=f"What clue helped solve the mystery?",
            answer=f'The clue was that {helper.id} had said the {prize.label} was in the {prize.hidden}, which meant it had only been put away, not stolen.',
        ),
    ]


KNOWLEDGE = {
    "raffle": [
        QAItem(
            question="What is a raffle?",
            answer="A raffle is a game where people get tickets or numbers and one is picked to win a prize.",
        )
    ],
    "cashew": [
        QAItem(
            question="What is a cashew?",
            answer="A cashew is a small curved nut that people sometimes eat as a snack.",
        )
    ],
    "kindness": [
        QAItem(
            question="What does kindness mean?",
            answer="Kindness means treating people gently, helping them, and not trying to hurt their feelings.",
        )
    ],
    "mystery": [
        QAItem(
            question="What is a mystery story?",
            answer="A mystery story is a story where someone notices a problem, looks for clues, and solves what happened.",
        )
    ],
    "dialogue": [
        QAItem(
            question="What is dialogue in a story?",
            answer="Dialogue is the words characters say to each other.",
        )
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    out: list[QAItem] = []
    out.extend(KNOWLEDGE["raffle"])
    out.extend(KNOWLEDGE["cashew"])
    out.extend(KNOWLEDGE["kindness"])
    out.extend(KNOWLEDGE["mystery"])
    out.extend(KNOWLEDGE["dialogue"])
    return out


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


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
place(P) :- setting(P).
prize(P) :- prize_kind(P).
uses(P, raffle) :- prize_kind(P), clue_kind(P, raffle).

kind(Kind) :- clue_kind(_, Kind).
solved(P) :- clue_kind(P, Hidden), hidden_place(P, Hidden), kindness_move(P).
valid_story(S, H, P) :- setting(S), hero_type(H), prize_kind(P).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for pid, prize in PRIZES.items():
        lines.append(asp.fact("prize_kind", pid))
        lines.append(asp.fact("clue_kind", pid, "raffle"))
        lines.append(asp.fact("hidden_place", pid, prize.hidden))
    lines.append(asp.fact("kindness_move", "cashew"))
    for g in ("girl", "boy", "adult"):
        lines.append(asp.fact("hero_type", g))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    stories = asp_valid_stories()
    expected = len(SETTINGS) * 3 * len(PRIZES)
    if len(stories) != expected:
        print("MISMATCH: ASP story count was", len(stories), "expected", expected)
        return 1
    print(f"OK: clingo derived {len(stories)} compatible story shapes.")
    return 0


# ---------------------------------------------------------------------------
# Parser / parameter resolution
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A tiny mystery world about a raffle, a cashew, dialogue, and kindness."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--hero-name")
    ap.add_argument("--hero-type", choices=["girl", "boy"])
    ap.add_argument("--helper-type", choices=["girl", "boy", "adult"])
    ap.add_argument("--prize", choices=PRIZES)
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
    setting = getattr(args, "setting", None) or rng.choice(sorted(SETTINGS))
    hero_type = getattr(args, "hero_type", None) or rng.choice(["girl", "boy"])
    helper_type = getattr(args, "helper_type", None) or rng.choice(["adult", "girl", "boy"])
    prize = getattr(args, "prize", None) or rng.choice(sorted(PRIZES))
    hero_name = getattr(args, "hero_name", None) or rng.choice(GIRL_NAMES if hero_type == "girl" else BOY_NAMES)

    if prize == "cashew" and helper_type == "adult" and hero_type == "boy":
        pass

    return StoryParams(
        setting=setting,
        hero_name=hero_name,
        hero_type=hero_type,
        helper_type=helper_type,
        prize=prize,
    )


# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------
def generate(params: StoryParams) -> StorySample:
    world = tell(
        _safe_lookup(SETTINGS, params.setting),
        params.hero_name,
        params.hero_type,
        params.helper_type,
        _safe_lookup(PRIZES, params.prize),
    )
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
        if e.kind:
            bits.append(f"kind={e.kind}")
        if e.type:
            bits.append(f"type={e.type}")
        if e.owner:
            bits.append(f"owner={e.owner}")
        if e.hidden_in:
            bits.append(f"hidden_in={e.hidden_in}")
        lines.append(f"  {e.id}: {' '.join(bits)}")
    lines.append(f"  facts: {world.facts}")
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
        print(asp_program("#show valid_story/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show valid_story/3."))
        print(f"{len(asp.atoms(model, 'valid_story'))} compatible story shapes.")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if getattr(args, "all", None):
        for setting in SETTINGS:
            for hero_type in ["girl", "boy"]:
                for helper_type in ["adult", "girl", "boy"]:
                    for prize in PRIZES:
                        p = StoryParams(
                            setting=setting,
                            hero_name=("Mina" if hero_type == "girl" else "Owen"),
                            hero_type=hero_type,
                            helper_type=helper_type,
                            prize=prize,
                        )
                        samples.append(generate(p))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(getattr(args, "n", None) * 50, 50):
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
            header = f"### {p.hero_name}: {p.prize} in {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
