#!/usr/bin/env python3
"""
Storyworld: Knack Reconciliation Superhero Story

A tiny superhero story domain about a young hero whose special knack is useful
but causes trouble until a reconciliation turns the day around.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field, asdict
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
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    ally: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    hero: object | None = None
    sidekick: object | None = None
    def __post_init__(self) -> None:
        for k in ("energy", "damage", "trust", "pride", "guilt", "relief", "hope"):
            self.meters.setdefault(k, 0.0)
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "heroine"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "hero"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

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
class City:
    name: str = "Star Harbor"
    danger: str = "glowing debris"
    weather: str = "clear"
    world: object | None = None
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
    def __init__(self, city: City) -> None:
        self.city = city
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

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


# ---------------------------------------------------------------------------
# Parameters
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    hero_name: str
    sidekick_name: str
    city: str
    knack: str
    mishap: str
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


HERO_NAMES = ["Nova", "Milo", "Iris", "Jett", "Zuri", "Pax", "Luna", "Kai"]
SIDEKICK_NAMES = ["Bea", "Timo", "Ada", "Sol", "Rin", "Mina"]
CITIES = ["Star Harbor", "Moon Junction", "Sunrise City"]
KNACKS = {
    "listen_fast": {
        "label": "a knack for listening fast",
        "gift": "heard tiny clues in a crowd",
        "use": "hear the warning before anyone else",
    },
    "build_quick": {
        "label": "a knack for building quick fixes",
        "gift": "could patch broken things in a blink",
        "use": "mend the broken shield",
    },
    "aim_true": {
        "label": "a knack for aiming true",
        "gift": "could toss gadgets exactly where they needed to go",
        "use": "send the rescue rope across the gap",
    },
}
MISHAPS = {
    "tram": "a runaway tram",
    "tower": "a falling tower sign",
    "kite": "a giant tangled kite",
}


@dataclass
class Knack:
    id: str
    label: str
    gift: str
    use: str


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Superhero storyworld about knack and reconciliation.")
    ap.add_argument("--hero-name")
    ap.add_argument("--sidekick-name")
    ap.add_argument("--city", choices=CITIES)
    ap.add_argument("--knack", choices=KNACKS)
    ap.add_argument("--mishap", choices=MISHAPS)
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
    knack = getattr(args, "knack", None) or rng.choice(list(KNACKS))
    mishap = getattr(args, "mishap", None) or rng.choice(list(MISHAPS))
    city = getattr(args, "city", None) or rng.choice(CITIES)
    hero = getattr(args, "hero_name", None) or rng.choice(HERO_NAMES)
    sidekick = getattr(args, "sidekick_name", None) or rng.choice([n for n in SIDEKICK_NAMES if n != hero])
    return StoryParams(hero_name=hero, sidekick_name=sidekick, city=city, knack=knack, mishap=mishap)


def _hero_pronoun_name(name: str) -> str:
    return name


def _knack_obj(knack_id: str) -> Knack:
    k = _safe_lookup(KNACKS, knack_id)
    return Knack(id=knack_id, label=k["label"], gift=k["gift"], use=k["use"])


# ---------------------------------------------------------------------------
# Simulation
# ---------------------------------------------------------------------------
def tell(params: StoryParams) -> World:
    world = World(City(name=params.city))
    hero = world.add(Entity(id=params.hero_name, kind="character", type="hero", label=params.hero_name))
    sidekick = world.add(Entity(id=params.sidekick_name, kind="character", type="sidekick", label=params.sidekick_name))
    knack = _knack_obj(params.knack)

    hero.memes["pride"] += 1
    hero.memes["hope"] += 1
    world.say(f"{hero.id} was a young superhero in {world.city.name} who had {knack.label}.")
    world.say(f"{knack.gift.capitalize()}, and that made {hero.id} feel ready for anything.")
    world.say(f"{hero.id} and {sidekick.id} were friends who always ran toward trouble together.")

    world.para()
    world.say(f"One afternoon, {_safe_lookup(MISHAPS, params.mishap)} burst into the city square.")
    world.say(f"{hero.id} wanted to {knack.use}, but the first try went wrong and made a bigger mess.")
    hero.meters["damage"] += 1
    hero.memes["guilt"] += 1
    sidekick.memes["hurt"] += 1
    sidekick.memes["trust"] -= 1
    world.say(f"{sidekick.id} frowned because the plan had not helped the people waiting nearby.")

    world.para()
    hero.memes["pride"] -= 1
    hero.memes["guilt"] += 1
    world.say(f"{hero.id} took a deep breath and said sorry to {sidekick.id}.")
    world.say(f"{sidekick.id} listened, and then {hero.id} used {knack.label} again, this time more carefully.")
    hero.memes["hope"] += 1
    hero.memes["relief"] += 1
    sidekick.memes["trust"] += 2
    sidekick.memes["relief"] += 1
    hero.meters["damage"] = 0
    world.say(f"Together, they fixed the trouble and saved the day.")
    world.say(f"By sunset, {hero.id} and {sidekick.id} were smiling side by side, after their reconciliation.")

    world.facts.update(hero=hero, sidekick=sidekick, knack=knack, mishap=params.mishap, city=params.city)
    return world


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a short superhero story for a small child about {f['hero'].id}, {f['sidekick'].id}, and a knack that causes trouble before reconciliation.",
        f"Tell a gentle hero story set in {f['city']} where a mistake is fixed by apology, teamwork, and {f['knack'].label}.",
        f"Write a story about a superhero who learns to use a special knack more carefully after upsetting a friend.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    sidekick = _safe_fact(world, f, "sidekick")
    knack: Knack = _safe_fact(world, f, "knack")
    return [
        QAItem(
            question=f"What special thing could {hero.id} do?",
            answer=f"{hero.id} had {knack.label}. It let {hero.pronoun()} {knack.gift}.",
        ),
        QAItem(
            question=f"Why did {sidekick.id} feel upset during the trouble in {f['city']}?",
            answer=f"{sidekick.id} felt upset because the first try went wrong and made a bigger mess instead of fixing the danger.",
        ),
        QAItem(
            question=f"How did {hero.id} and {sidekick.id} finish the story?",
            answer=f"They talked, said sorry, worked together, and reached reconciliation after fixing the problem.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a knack?",
            answer="A knack is a special skill that someone does especially well, almost like a talent that comes naturally.",
        ),
        QAItem(
            question="What is reconciliation?",
            answer="Reconciliation is when people stop feeling upset with each other, make peace, and become friendly again.",
        ),
        QAItem(
            question="Why do superheroes work with teammates?",
            answer="Superheroes work with teammates because together they can solve hard problems faster and keep everyone safer.",
        ),
    ]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
hero(H) :- hero_name(H).
sidekick(S) :- sidekick_name(S).
knack(K) :- knack_id(K).
mishap(M) :- mishap_id(M).

needs_reconciliation(H,S) :- hero(H), sidekick(S), conflict(H,S).
can_fix(H,S) :- needs_reconciliation(H,S), apology(H,S), teamwork(H,S).

#show valid/2.
valid(H,S) :- hero(H), sidekick(S), H != S.
"""

def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    for name in HERO_NAMES:
        lines.append(asp.fact("hero_name", name))
    for name in SIDEKICK_NAMES:
        lines.append(asp.fact("sidekick_name", name))
    for k in KNACKS:
        lines.append(asp.fact("knack_id", k))
    for m in MISHAPS:
        lines.append(asp.fact("mishap_id", m))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp
    program = asp_program("#show valid/2.")
    model = asp.one_model(program)
    clingo_pairs = set(asp.atoms(model, "valid"))
    py_pairs = {(h, s) for h in HERO_NAMES for s in SIDEKICK_NAMES if h != s}
    if clingo_pairs == py_pairs:
        print(f"OK: clingo gate matches Python ({len(py_pairs)} pairs).")
        return 0
    print("MISMATCH between ASP and Python.")
    if clingo_pairs - py_pairs:
        print(" only in ASP:", sorted(clingo_pairs - py_pairs))
    if py_pairs - clingo_pairs:
        print(" only in Python:", sorted(py_pairs - clingo_pairs))
    return 1


# ---------------------------------------------------------------------------
# Emission / CLI
# ---------------------------------------------------------------------------
def format_qa(sample: StorySample) -> str:
    lines = ["== Story questions =="]
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== World questions ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== Prompts ==")
    for p in sample.prompts:
        lines.append(f"- {p}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in list(world.entities.values()):
        lines.append(f"{e.id}: meters={ {k:v for k,v in e.meters.items() if v} } memes={ {k:v for k,v in e.memes.items() if v} }")
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


CURATED = [
    StoryParams("Nova", "Bea", "Star Harbor", "listen_fast", "tram"),
    StoryParams("Iris", "Timo", "Moon Junction", "build_quick", "tower"),
    StoryParams("Kai", "Mina", "Sunrise City", "aim_true", "kite"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import storyworlds.asp as asp
        model = asp.one_model(asp_program("#show valid/2."))
        print(sorted(asp.atoms(model, "valid")))
        return

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
        header = ""
        if len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
