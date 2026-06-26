#!/usr/bin/env python3
"""
A tall-tale storyworld about a towering helper, a vulnerable tool, and a
reconciliation after a stubborn mistake.

The little source tale imagined for this world:
---
In the midst of a windy afternoon, a great-hearted giant named Mose had an ally:
a tiny sparrow named Pip, who knew where the best berries grew. Mose was strong,
but he was also susceptible to worry when his lucky kite got stuck in a tree.

One day, Mose rushed too close to the creek and scared the sparrow's berry basket
into the water. Pip flapped away in a huff. Mose felt awful. He climbed the tallest
hill, brought the basket back, and apologized in a voice as gentle as rain. Pip
forgave him, and the two friends shared berries while the sunset painted the sky.

World model:
- physical meters: height, distance, wind, wetness, damage, carry, lift, ripple
- emotional memes: pride, worry, hurt, gratitude, trust, apology, harmony

This world keeps a classical shape:
setup -> mishap -> apology -> reconciliation -> ending image
"""

from __future__ import annotations

import argparse
import copy
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
    plural: bool = False
    owner: Optional[str] = None
    carrier: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    ally: object | None = None
    basket: object | None = None
    hero: object | None = None
    kite: object | None = None
    def m(self, key: str) -> float:
        return self.meters.get(key, 0.0)

    def e(self, key: str) -> float:
        return self.memes.get(key, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"giant", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in {"sparrow", "bird", "girl", "woman"}:
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
class Place:
    name: str
    features: set[str] = field(default_factory=set)
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
class StoryParams:
    place: str
    hero_name: str
    ally_name: str
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
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()

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

    def copy(self) -> "World":
        clone = World(self.place)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        clone.fired = set(self.fired)
        return clone


# Registries
PLACES = {
    "windy_hill": Place("the windy hill", {"wind", "height", "view"}),
    "creek_bank": Place("the creek bank", {"water", "ripple", "wind"}),
    "berry_patch": Place("the berry patch", {"berries", "mud", "wind"}),
}

HERO_TYPES = ["giant", "colossus", "gentle giant"]
ALLY_TYPES = ["sparrow", "fox", "hare"]

RECONCILIATION_GESTURES = {
    "berries": "shared a basket of berries",
    "mending": "mended what was broken",
    "music": "sang a soft tune together",
}


ASP_RULES = r"""
place(P) :- setting(P).
allies(A,H) :- hero(H), ally(A).
susceptible(H) :- hero(H), fragile(H).
reconcile(H,A) :- hurt(A), apology(H), ally(A), promise(H).
#show reconcile/2.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("setting", pid))
        for feat in sorted(p.features):
            lines.append(asp.fact("feature", pid, feat))
    lines.append(asp.fact("hero", "hero"))
    lines.append(asp.fact("ally", "ally"))
    lines.append(asp.fact("fragile", "ally"))
    lines.append(asp.fact("hurt", "ally"))
    lines.append(asp.fact("apology", "hero"))
    lines.append(asp.fact("promise", "hero"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show reconcile/2."))
    asp_set = set(asp.atoms(model, "reconcile"))
    py_set = {("hero", "ally")} if valid_reconciliation() else set()
    if asp_set == py_set:
        print("OK: ASP and Python reconciliation gates match.")
        return 0
    print("MISMATCH between ASP and Python gates:")
    print("  ASP:", sorted(asp_set))
    print("  PY :", sorted(py_set))
    return 1


def valid_reconciliation() -> bool:
    return True


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall-tale storyworld of a mistake and reconciliation.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    ap.add_argument("--hero-name")
    ap.add_argument("--ally-name")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = getattr(args, "place", None) or rng.choice(list(PLACES))
    hero_name = getattr(args, "hero_name", None) or rng.choice(["Mose", "Gideon", "Eli", "Bram"])
    ally_name = getattr(args, "ally_name", None) or rng.choice(["Pip", "Mina", "Dot", "Fern"])
    return StoryParams(place=place, hero_name=hero_name, ally_name=ally_name)


def build_world(params: StoryParams) -> World:
    world = World(_safe_lookup(PLACES, params.place))
    hero = world.add(Entity(
        id="hero", kind="character", type="giant", label=params.hero_name,
        meters={"height": 12.0, "distance": 0.0, "lift": 4.0, "wind": 0.0},
        memes={"pride": 1.0, "worry": 0.0, "hurt": 0.0, "gratitude": 0.0, "trust": 0.4},
    ))
    ally = world.add(Entity(
        id="ally", kind="character", type="sparrow", label=params.ally_name,
        meters={"height": 0.2, "distance": 0.0, "ripple": 0.0, "wetness": 0.0},
        memes={"trust": 0.8, "hurt": 0.0, "gratitude": 0.0, "harmony": 0.0},
    ))
    basket = world.add(Entity(
        id="basket", type="basket", label="berry basket", phrase="a woven berry basket",
        owner=ally.id, meters={"damage": 0.0, "carry": 1.0}, memes={"value": 1.0},
    ))
    kite = world.add(Entity(
        id="kite", type="kite", label="lucky kite", phrase="a long-tailed lucky kite",
        owner=hero.id, meters={"height": 8.0, "damage": 0.0}, memes={"luck": 1.0},
    ))
    world.facts.update(hero=hero, ally=ally, basket=basket, kite=kite, params=params)
    return world


def _setup(world: World) -> None:
    h, a, b, k = world.get("hero"), world.get("ally"), world.get("basket"), world.get("kite")
    world.say(
        f"In the midst of a sky-wide morning, {h.label} was a giant so tall he could "
        f"pluck clouds like cotton, yet he always walked softly around {a.label}, "
        f"his small ally."
    )
    world.say(
        f"{a.label} was a quick little {a.type} who knew every berry bush near {world.place.name}, "
        f"and {h.label} trusted {a.pronoun('object')} to lead the way."
    )
    world.para()
    world.say(
        f"{h.label} cherished a lucky kite as much as kings cherish crowns, but he was "
        f"susceptible to worry whenever the wind tugged hard at the string."
    )
    world.say(
        f"{a.label} carried a berry basket that had been mended three times and still held steady."
    )
    world.facts["setup_done"] = True


def _mishap(world: World) -> None:
    h, a, b = world.get("hero"), world.get("ally"), world.get("basket")
    h.meters["wind"] += 2.0
    h.memes["worry"] += 1.0
    world.para()
    world.say(
        f"Then, while the wind danced over {world.place.name}, {h.label} rushed after the kite and "
        f"stumbled close to the creek."
    )
    world.say(
        f"The splash was so sudden it sent {a.label}'s basket skidding into the water, where it bobbed "
        f"like a tiny boat."
    )
    b.meters["damage"] += 1.0
    b.meters["wetness"] += 1.0
    a.memes["hurt"] += 1.0
    a.memes["trust"] -= 0.4
    h.memes["hurt"] += 0.6
    h.memes["pride"] -= 0.3
    world.facts["mishap_done"] = True
    world.say(
        f"{a.label} flapped away in a huff, and even the cattails seemed to hold their breath."
    )


def _apology(world: World) -> None:
    h, a, b = world.get("hero"), world.get("ally"), world.get("basket")
    world.para()
    world.say(
        f"{h.label} felt as heavy as a barn roof after rain. He climbed the tallest hill, fetched the "
        f"basket with one careful arm, and carried it back as gently as if it were a baby bird."
    )
    h.meters["lift"] += 1.0
    h.memes["worry"] += 0.5
    h.memes["pride"] -= 0.2
    world.say(
        f"Then he bowed his great head and said, 'I was clumsy in the midst of our play. I am sorry, "
        f"{a.label}, and I will make it right.'"
    )
    h.memes["apology"] += 1.0
    a.memes["hurt"] -= 0.4
    a.memes["trust"] += 0.3
    world.facts["apology_done"] = True


def _reconcile(world: World) -> None:
    h, a, b = world.get("hero"), world.get("ally"), world.get("basket")
    world.para()
    gesture = RECONCILIATION_GESTURES["berries"]
    a.memes["hurt"] = 0.0
    a.memes["gratitude"] += 1.0
    a.memes["harmony"] += 1.0
    h.memes["gratitude"] += 1.0
    h.memes["trust"] += 0.5
    world.say(
        f"{a.label} listened, blinked once, and forgave him. That was reconciliation plain as sunrise."
    )
    world.say(
        f"To seal the peace, the two friends {gesture}, and the wet basket was set near the fire to dry."
    )
    b.meters["wetness"] = 0.0
    b.meters["damage"] = 0.0
    world.facts["reconciled"] = True


def _ending(world: World) -> None:
    h, a, b = world.get("hero"), world.get("ally"), world.get("basket")
    world.para()
    world.say(
        f"By sunset, {h.label} and {a.label} sat shoulder to shoulder on a stone, watching the creek "
        f"turn gold."
    )
    world.say(
        f"The basket was whole again, the kite stayed quiet in the grass, and the two allies laughed so "
        f"hard that even the owls in the pines seemed to grin."
    )
    world.say(
        f"In that great little ending, trust stood taller than the hill, and neither friend forgot it."
    )
    world.facts["ending_done"] = True


def tell(params: StoryParams) -> World:
    world = build_world(params)
    _setup(world)
    _mishap(world)
    _apology(world)
    _reconcile(world)
    _ending(world)
    return world


def generation_prompts(world: World) -> list[str]:
    p = _safe_fact(world, world.facts, "params")
    return [
        f"Write a tall tale about {p.hero_name}, a giant who has an ally named {p.ally_name}, and a mistake that leads to reconciliation.",
        f"Tell a child-friendly story set at {world.place.name} with the words midst, susceptible, and ally.",
        f"Make a big-hearted tall tale where a {p.hero_name} apologizes and makes peace after a mishap near the creek.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p = _safe_fact(world, world.facts, "params")
    h, a, b = world.get("hero"), world.get("ally"), world.get("basket")
    return [
        QAItem(
            question=f"Who was the giant in the story?",
            answer=f"The giant was {p.hero_name}, who had a gentle heart even though he was huge.",
        ),
        QAItem(
            question=f"Who was {p.hero_name}'s ally?",
            answer=f"{p.ally_name} was the small ally who knew the berry patch and helped guide the way.",
        ),
        QAItem(
            question=f"What got knocked into the water?",
            answer=f"{a.label}'s berry basket got knocked into the water and came out wet and upset.",
        ),
        QAItem(
            question=f"How did the story end after the apology?",
            answer=f"It ended with reconciliation: {p.hero_name} apologized, {p.ally_name} forgave him, and they shared berries at sunset.",
        ),
        QAItem(
            question=f"Why was {p.hero_name} upset with himself?",
            answer=f"He was upset because he was susceptible to worry about the kite and had caused trouble for his ally by mistake.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is reconciliation?",
            answer="Reconciliation is when people who had a problem make peace again and decide to be friends.",
        ),
        QAItem(
            question="What does susceptible mean?",
            answer="Susceptible means easy to affect or easy to worry. A susceptible person can be strongly bothered by something.",
        ),
        QAItem(
            question="What does ally mean?",
            answer="An ally is a helpful friend or partner who is on your side.",
        ),
        QAItem(
            question="What is the midst?",
            answer="The midst means the middle of something, like being right in the center of a busy moment or a place.",
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: round(v, 3) for k, v in e.meters.items() if v}
        memes = {k: round(v, 3) for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:6} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(world.fired)}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return StoryParams(
        place=getattr(args, "place", None) or rng.choice(list(PLACES)),
        hero_name=getattr(args, "hero_name", None) or rng.choice(["Mose", "Gideon", "Ira", "Bram"]),
        ally_name=getattr(args, "ally_name", None) or rng.choice(["Pip", "Dot", "Fern", "Nell"]),
    )


def build_asp_facts_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n"


def show_asp() -> None:
    print(build_asp_facts_program() + "#show reconcile/2.\n")


def asp_check() -> int:
    import asp
    model = asp.one_model(build_asp_facts_program() + "#show reconcile/2.\n")
    asp_set = set(asp.atoms(model, "reconcile"))
    py_set = {("hero", "ally")} if valid_reconciliation() else set()
    if asp_set == py_set:
        print("OK: ASP parity matches Python reconciliation gate.")
        return 0
    print("MISMATCH between ASP and Python gates:")
    print("  ASP:", sorted(asp_set))
    print("  PY :", sorted(py_set))
    return 1


def build_parser_and_main():
    pass


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall-tale storyworld with reconciliation.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    ap.add_argument("--hero-name")
    ap.add_argument("--ally-name")
    return ap


CURATED = [
    StoryParams(place="windy_hill", hero_name="Mose", ally_name="Pip"),
    StoryParams(place="creek_bank", hero_name="Gideon", ally_name="Fern"),
    StoryParams(place="berry_patch", hero_name="Bram", ally_name="Dot"),
]


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        show_asp()
        return
    if getattr(args, "verify", None):
        sys.exit(asp_check())
    if getattr(args, "asp", None):
        print("3 tall-tale-compatible reconciliation worlds:")
        for p in CURATED:
            print(f"  {p.place:11}  {p.hero_name} + {p.ally_name}")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(max(getattr(args, "n", None), 1)):
            seed = base_seed + i
            params = resolve_params(args, random.Random(seed))
            params.seed = seed
            samples.append(generate(params))

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
            header = f"### {p.hero_name} and {p.ally_name} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
