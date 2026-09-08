#!/usr/bin/env python3
"""
A tiny superhero storyworld about a doofus, a toupee, and a promise kept.
"""

from __future__ import annotations

# Locate the shared StoryWorld helpers from any batch depth.
from pathlib import Path as _StoryPath
import sys as _StorySys
_storyworlds_root = next(parent for parent in _StoryPath(__file__).resolve().parents
                        if (parent / 'results.py').is_file() and (parent / 'asp.py').is_file())
_StorySys.path.insert(0, str(_storyworlds_root.parent))
_StorySys.path.insert(0, str(_storyworlds_root))


import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
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
class Entity:
    id: str
    kind: str
    type: str
    label: str
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    city: object | None = None
    doofus: object | None = None
    hero: object | None = None
    toupee: object | None = None
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

    def __getitem__(self, key):
        if isinstance(key, int):
            if key == 0:
                return self
            raise IndexError(key)
        if isinstance(key, str):
            if hasattr(self, key):
                return getattr(self, key)
            for attr in ("meters", "memes"):
                mapping = getattr(self, attr, None)
                if hasattr(mapping, "get") and key in mapping:
                    return mapping.get(key)
        raise KeyError(key)

    def __iter__(self):
        yield self

    def __hash__(self):
        return hash(getattr(self, "id", id(self)))


@dataclass
class StoryParams:
    hero: str = ""
    doofus: str = ""
    toupee_color: str = ""
    city: str = ""
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


@dataclass
class Crisis:
    danger: str
    warning: str
    repeated_call: str
    rescue: str
    lesson: str
    ending: str
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


CRISES = [
    Crisis(
        danger="a gust lifted the mayor's parade balloon toward the clock tower",
        warning="three loose ribbons trembled beside the fountain",
        repeated_call="Toupee, toupee, hold on!",
        rescue="used the toupee's hidden silver comb as a tiny grappling hook",
        lesson="Even a silly-looking thing can become useful when a brave friend notices its true strength.",
        ending="the mayor's balloon bobbed safely above the cheering crowd",
    ),
    Crisis(
        danger="the bakery's warm delivery cart began rolling down the hill",
        warning="the cart bell rang once, then twice, then once again",
        repeated_call="Toupee, toupee, stay with me!",
        rescue="pulled the toupee free and used its elastic band to loop around the cart handle",
        lesson="A repeated warning deserves attention, and a friend deserves patience.",
        ending="fresh buns reached the children before they grew cold",
    ),
    Crisis(
        danger="a little robot tumbled from the science fair roof",
        warning="a red warning light blinked three times over the empty stage",
        repeated_call="Toupee, toupee, guide the way!",
        rescue="turned the toupee into a soft landing pad beneath the robot",
        lesson="Courage is not looking perfect; courage is helping when help is needed.",
        ending="the rescued robot beeped a happy tune for everyone",
    ),
    Crisis(
        danger="a runaway kite tangled around the library's rooftop weather vane",
        warning="the vane squeaked whenever the wind changed direction",
        repeated_call="Toupee, toupee, fly straight!",
        rescue="tossed the toupee's long hairpin through the kite's loop",
        lesson="A careful hero listens to small clues before making a big move.",
        ending="the kite sailed free above the library roof",
    ),
]


CITIES = ["Brighton", "Moonbeam City", "Copperville", "Sunrise Square"]
HEROES = ["Luna", "Nova", "Spark", "Captain Mica"]
DOOFUSES = ["Bobo", "Dudley", "Pip", "Gus"]
COLORS = ["purple", "golden", "blue", "green"]


class World:
    def __init__(self, params: StoryParams) -> None:
        self.params = params
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple[str, ...]] = set()
        self.facts: dict[str, object] = {}

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity
    def get(self, eid: str):
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
        return self.entities[eid]
    def copy(self):
        clone = __import__("copy").deepcopy(self)
        return clone


def build_world(params: StoryParams) -> World:
    world = World(params)
    hero = world.add(Entity("hero", "character", "hero", params.hero))
    doofus = world.add(Entity("doofus", "character", "doofus", params.doofus))
    toupee = world.add(Entity("toupee", "object", "toupee", f"{params.toupee_color} toupee"))
    city = world.add(Entity("city", "place", "city", params.city))

    hero.meters.update(bravery=1, speed=1)
    hero.memes.update(compassion=0, confidence=0)
    doofus.meters.update(balance=0, helpfulness=1)
    doofus.memes.update(worry=0, embarrassment=1, relief=0)
    toupee.meters.update(grip=1, stretch=1, usefulness=0)
    toupee.memes.update(pride=0)
    city.meters.update(safety=0)

    seed = params.seed
    if seed is None:
        seed = sum((i + 1) * ord(c) for i, c in enumerate("|".join([
            params.hero, params.doofus, params.toupee_color, params.city
        ])))
    rng = random.Random(seed ^ 0xBEEF48)
    crisis = rng.choice(CRISES)
    world.facts["crisis"] = crisis
    world.facts["rng"] = rng
    return world


def tell(world: World) -> str:
    p = world.params
    crisis: Crisis = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "crisis")  # type: ignore[assignment]
    hero = world.get("hero")
    doofus = world.get("doofus")
    toupee = world.get("toupee")
    city = world.get("city")

    hero.memes["confidence"] = 1
    world.fired.add(("hero_arrived",))

    paragraphs = [
        (
            f"In {city.label}, {hero.label} watched over the rooftops with a bright cape "
            f"and a promise to help anyone in trouble. Nearby lived {doofus.label}, a "
            f"lovable doofus who wore a {toupee.label} that never sat quite straight."
        ),
        (
            f"Every morning, {doofus.label} patted the toupee and said, "
            f'"Stay on, little friend." The toupee slid left. {doofus.label} patted it again '
            f'and said, "Stay on, little friend."'
        ),
        (
            f"That morning, {crisis.warning}. {hero.label} noticed the warning before the "
            f'crowd did, because small clues often arrived before big trouble. Then {crisis.danger}.'
        ),
        (
            f'{doofus.label} pointed upward. "{crisis.repeated_call}" '
            f'"Do not worry," said {hero.label}. "Tell me what you noticed." '
            f'"The bell, the wind, and my toupee all moved the same way," said {doofus.label}.'
        ),
        (
            f"The repeated signs gave {hero.label} an idea. {hero.label} flew beside "
            f"{doofus.label}, while the doofus held the {toupee.label} firmly. Together they "
            f"{crisis.rescue}."
        ),
        (
            f"The danger passed. {city.label} grew safe again, and {hero.label}'s compassion "
            f"rose as {doofus.label}'s worry melted into relief. {doofus.label} touched the "
            f"toupee and whispered, 'Stay on, little friend.' This time, it did."
        ),
        (
            f"Everyone cheered because {crisis.ending}. {hero.label} smiled and said, "
            f'"A hero listens, even when the clue wears a toupee." {crisis.lesson}'
        ),
    ]

    hero.memes["compassion"] = 1
    doofus.memes["worry"] = 0
    doofus.memes["relief"] = 1
    toupee.meters["usefulness"] = 1
    toupee.memes["pride"] = 1
    city.meters["safety"] = 1
    world.fired.update({("warning_seen",), ("dialogue_changed_plan",), ("danger_resolved",)})
    return "\n\n".join(paragraphs)


def generation_prompts(world: World) -> list[str]:
    p = world.params
    return [
        f"Write a child-friendly superhero story about {p.doofus}, a {p.toupee_color} toupee, and {p.hero}.",
        "Use repetition, spoken dialogue, and a warning clue that foreshadows the danger.",
        f"Show how {p.doofus}'s unusual toupee helps save someone in {p.city}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p = world.params
    crisis: Crisis = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "crisis")  # type: ignore[assignment]
    return [
        QAItem(
            question=f"Who was the doofus in the story?",
            answer=f"{p.doofus} was the lovable doofus who wore the {p.toupee_color} toupee.",
        ),
        QAItem(
            question="What warning did the heroes notice before the danger?",
            answer=f"They noticed that {crisis.warning}.",
        ),
        QAItem(
            question="How did dialogue change what the hero decided to do?",
            answer=f"{p.doofus} explained the repeated signs, so {p.hero} used that information to plan the rescue.",
        ),
        QAItem(
            question="How did the toupee help?",
            answer=f"{p.hero} and {p.doofus} {crisis.rescue}.",
        ),
        QAItem(
            question="What happened at the end?",
            answer=f"{crisis.ending}, and {p.doofus}'s toupee stayed on.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a superhero?",
            answer="A superhero is a brave helper who uses special abilities, kindness, or clever ideas to protect others.",
        ),
        QAItem(
            question="What is a toupee?",
            answer="A toupee is a piece of hair worn on the head.",
        ),
        QAItem(
            question="What is foreshadowing?",
            answer="Foreshadowing is a clue early in a story that hints at something important later.",
        ),
    ]


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    story = tell(world)
    return StorySample(
        params=params,
        story=story,
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


ASP_RULES = r"""
safe(C) :- city(C), resolved(C).
helpful(D) :- doofus(D), useful(T), wears(D,T).
resolved(C) :- danger(C), helpful(D), hero(H), rescued(H,C).
#show safe/1.
#show helpful/1.
#show resolved/1.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for city in CITIES:
        lines.append(asp.fact("city", city.lower().replace(" ", "_")))
    for name in DOOFUSES:
        lines.append(asp.fact("doofus", name.lower()))
    lines.append(asp.fact("hero", "hero"))
    lines.append(asp.fact("toupee", "toupee"))
    lines.append(asp.fact("useful", "toupee"))
    lines.append(asp.fact("wears", "bobo", "toupee"))
    lines.append(asp.fact("danger", "brighton"))
    lines.append(asp.fact("rescued", "hero", "brighton"))
    lines.append(asp.fact("resolved", "brighton"))
    return "\n".join(lines)


def asp_program(extra: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="A superhero story about a doofus and a toupee.")
    parser.add_argument("--hero", choices=HEROES)
    parser.add_argument("--doofus", choices=DOOFUSES)
    parser.add_argument("--toupee-color", choices=COLORS)
    parser.add_argument("--city", choices=CITIES)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--seed", type=int)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random, index: int = 0) -> StoryParams:
    return StoryParams(
        hero=getattr(args, "hero", None) or rng.choice(HEROES),
        doofus=getattr(args, "doofus", None) or rng.choice(DOOFUSES),
        toupee_color=getattr(args, "toupee_color", None) or rng.choice(COLORS),
        city=getattr(args, "city", None) or rng.choice(CITIES),
        seed=(getattr(args, "seed", None) + index) if getattr(args, "seed", None) is not None else None,
    )


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for entity in list(world.entities.values()):
        lines.append(
            f"{entity.id}: kind={entity.kind} type={entity.type} "
            f"meters={dict(entity.meters)} memes={dict(entity.memes)}"
        )
    lines.append(f"fired={sorted(world.fired)}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    lines.extend(sample.prompts)
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def emit(sample: StorySample, trace: bool = False, qa: bool = False, header: str = "") -> None:
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
    model = asp.one_model(asp_program("#show city/1.\n#show doofus/1.\n#show toupee/1."))
    cities = {item[0] for item in asp.atoms(model, "city")}
    doofuses = {item[0] for item in asp.atoms(model, "doofus")}
    toupees = {item[0] for item in asp.atoms(model, "toupee")}
    expected_cities = {c.lower().replace(" ", "_") for c in CITIES}
    if cities != expected_cities or doofuses != {d.lower() for d in DOOFUSES} or toupees != {"toupee"}:
        print("MISMATCH: ASP/Python registry parity failed.")
        return 1
    if not any(generate(StoryParams("Luna", "Bobo", "purple", "Brighton", 7)).story):
        print("MISMATCH: story generation failed.")
        return 1
    print("OK: ASP/Python registry parity and story generation.")
    return 0


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program())
        return
    if getattr(args, "verify", None):
        try:
            import asp  # noqa: F401
        except ImportError:
            print("ASP verification requires clingo.")
            sys.exit(1)
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        print(asp_program())
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        curated = [
            StoryParams("Luna", "Bobo", "purple", "Brighton", base_seed),
            StoryParams("Nova", "Dudley", "golden", "Moonbeam City", base_seed + 1),
            StoryParams("Spark", "Pip", "blue", "Copperville", base_seed + 2),
            StoryParams("Captain Mica", "Gus", "green", "Sunrise Square", base_seed + 3),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        for i in range(max(1, getattr(args, "n", None))):
            params = resolve_params(args, random.Random(base_seed + i), i)
            if params.seed is None:
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
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for index, sample in enumerate(samples):
        emit(
            sample,
            trace=getattr(args, "trace", None),
            qa=getattr(args, "qa", None),
            header=f"### variant {index + 1}" if len(samples) > 1 else "",
        )
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
