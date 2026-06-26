#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T055509Z_seed1837429065_n100/surprise_visitor_bravery_tall_tale.py
===============================================================================================================

A small Tall Tale-style story world about a surprise visitor and brave choices.

Premise:
- A child hears that a mysterious visitor is coming to a windy little farm.
- The visitor seems huge and strange at first, which stirs a jolt of fear.
- A brave act turns the surprise into a friendly, helpful visit.

The simulation tracks:
- physical meters: distance traveled, wind, dust, supplies carried
- emotional memes: worry, courage, trust, relief, admiration

The story stays child-facing and concrete, but it is still a state-driven
simulation rather than a frozen paragraph template.
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
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    guest: object | None = None
    hero: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]
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
    indoors: bool = False
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
class Visitor:
    id: str
    label: str
    phrase: str
    tall: bool = False
    friendly: bool = True
    carries: str = ""
    brings: str = ""
    feats: set[str] = field(default_factory=set)
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
    place: str
    hero_name: str
    hero_gender: str
    hero_trait: str
    visitor: str
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
        self.fired: set[tuple] = set()
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


PLACES = {
    "farm": Place("the windy farm", features={"barn", "yard", "gate", "hayloft"}),
    "porch": Place("the old porch", features={"steps", "screen door", "bench"}),
    "schoolyard": Place("the schoolyard", features={"flagpole", "bench", "fence"}),
}

VISITORS = {
    "giant_traveler": Visitor(
        id="giant_traveler",
        label="a giant traveler",
        phrase="a giant traveler with a wide hat and a long coat",
        tall=True,
        friendly=True,
        carries="a lantern",
        brings="news and a warm apple pie",
        feats={"news", "pie", "tall"},
    ),
    "high_wind_courier": Visitor(
        id="high_wind_courier",
        label="a courier",
        phrase="a courier on a tall horse with a bag of letters",
        tall=True,
        friendly=True,
        carries="a leather satchel",
        brings="letters and a ribbon",
        feats={"letters", "tall"},
    ),
    "bearded_lumber": Visitor(
        id="bearded_lumber",
        label="a lumberjack",
        phrase="a bearded lumberjack with boots as big as buckets",
        tall=False,
        friendly=True,
        carries="a bundle of kindling",
        brings="kindling and a song",
        feats={"kindling", "song"},
    ),
}

HERO_TRAITS = ["brave", "curious", "spunky", "steady", "cheerful"]
GIRL_NAMES = ["Mina", "Ruby", "Ivy", "Nora", "Hazel", "Lena"]
BOY_NAMES = ["Jasper", "Theo", "Eli", "Otis", "Milo", "Finn"]


def reasonableness_gate(place: Place, visitor: Visitor) -> None:
    if "barn" not in place.features and visitor.id == "giant_traveler":
        pass
    if not visitor.friendly:
        pass


ASP_RULES = r"""
place(farm). place(porch). place(schoolyard).

visitor(giant_traveler). visitor(high_wind_courier). visitor(bearded_lumber).

tall(giant_traveler). tall(high_wind_courier).
friendly(giant_traveler). friendly(high_wind_courier). friendly(bearded_lumber).

feature(farm,barn). feature(farm,yard). feature(farm,gate). feature(farm,hayloft).
feature(porch,steps). feature(porch,screen_door). feature(porch,bench).
feature(schoolyard,flagpole). feature(schoolyard,bench). feature(schoolyard,fence).

needs_room(giant_traveler) :- tall(giant_traveler).
reasonable(P,V) :- place(P), visitor(V), friendly(V), not bad(P,V).
bad(P,giant_traveler) :- place(P), not feature(P,barn), needs_room(giant_traveler).

#show reasonable/2.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
        for feat in sorted(_safe_lookup(PLACES, pid).features):
            lines.append(asp.fact("feature", pid, feat))
    for vid, v in VISITORS.items():
        lines.append(asp.fact("visitor", vid))
        if v.tall:
            lines.append(asp.fact("tall", vid))
        if v.friendly:
            lines.append(asp.fact("friendly", vid))
    return "\n".join(lines)


def asp_program(show: str = "#show reasonable/2.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_reasonable() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "reasonable")))


def asp_verify() -> int:
    py = {(p, v) for p in PLACES for v in VISITORS if is_reasonable(_safe_lookup(PLACES, p), _safe_lookup(VISITORS, v))}
    cl = set(asp_reasonable())
    if py == cl:
        print(f"OK: ASP and Python agree on {len(py)} reasonable pair(s).")
        return 0
    print("MISMATCH:")
    print(" only python:", sorted(py - cl))
    print(" only asp:", sorted(cl - py))
    return 1


def is_reasonable(place: Place, visitor: Visitor) -> bool:
    try:
        reasonableness_gate(place, visitor)
    except StoryError:
        return False
    if visitor.id == "giant_traveler":
        return "barn" in place.features
    return True


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall tale story world: a surprise visitor and bravery.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--visitor", choices=VISITORS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--trait", choices=HERO_TRAITS)
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
    pairs = [(p, v) for p in PLACES for v in VISITORS if is_reasonable(_safe_lookup(PLACES, p), _safe_lookup(VISITORS, v))]
    if getattr(args, "place", None):
        pairs = [pv for pv in pairs if pv[0] == getattr(args, "place", None)]
    if getattr(args, "visitor", None):
        pairs = [pv for pv in pairs if pv[1] == getattr(args, "visitor", None)]
    if not pairs:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, visitor = rng.choice(sorted(pairs))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    trait = getattr(args, "trait", None) or rng.choice(HERO_TRAITS)
    return StoryParams(place=place, hero_name=name, hero_gender=gender, hero_trait=trait, visitor=visitor)


def make_world(params: StoryParams) -> World:
    place = _safe_lookup(PLACES, params.place)
    visitor = _safe_lookup(VISITORS, params.visitor)
    world = World(place)
    hero = world.add(Entity(id=params.hero_name, kind="character", type=params.hero_gender, traits=["little", params.hero_trait]))
    guest = world.add(Entity(id=visitor.id, kind="character", type="man" if visitor.tall else "woman", label=visitor.label))
    guest.meters["height"] = 3.0 if visitor.tall else 2.0
    hero.memes["worry"] += 1
    world.say(f"{hero.id} was a little {params.hero_trait} {params.hero_gender} who loved the wide sky over {place.name}.")
    world.say(f"{hero.id} had heard that a surprise visitor was coming, and the news made {hero.pronoun('possessive')} ears prick up like a rabbit's.")
    world.say(f"That visitor was {visitor.phrase}, and {visitor.brings} rode along with {visitor.pronoun('possessive') if visitor.tall else 'their'} shadow.")
    world.para()
    world.say(f"At the farm gate, the wind blew so hard it could have combed a horse's mane.")
    world.say(f"{hero.id} climbed onto a fence rail and looked out, trying to be steady as a nail in a board.")
    if visitor.id == "giant_traveler":
        hero.memes["fear"] += 1
        world.say(f"Then the giant traveler came loping down the road, tall as a barn ladder and twice as strange.")
    elif visitor.id == "high_wind_courier":
        hero.memes["fear"] += 1
        world.say(f"Then the courier thundered up on a horse so tall it seemed to kiss the clouds.")
    else:
        hero.memes["fear"] += 0.5
        world.say(f"Then the lumberjack strode in, carrying kindling and singing in a voice that rattled the cups in the kitchen.")
    world.say(f"{hero.id}'s knees went wobbly, but {hero.id} took one brave breath after another.")
    hero.memes["courage"] += 1
    world.para()
    world.say(f"When a loose gate latch clanged open, the visitor reached for it first, but the wind shoved the gate sideways.")
    hero.meters["distance"] += 1
    world.say(f"{hero.id} sprang forward anyway, braver than a mouse in a moonlit barn, and slammed the gate shut before it could bang itself to pieces.")
    hero.memes["admiration"] += 1
    hero.memes["trust"] += 1
    if visitor.id == "giant_traveler":
        world.say(f"The giant traveler laughed in a thunder-soft voice and said {hero.id} had a heart stout enough to stop a stampede.")
    elif visitor.id == "high_wind_courier":
        world.say(f"The courier tipped a hat and said {hero.id} moved like a sparrow with lightning in its wings.")
    else:
        world.say(f"The lumberjack grinned and said {hero.id} was brave enough to chase a bear off a biscuit.")
    world.para()
    hero.memes["relief"] += 1
    world.say(f"After that, the surprise was no longer a fright. It was a grand visit, full of {visitor.brings}.")
    world.say(f"{hero.id} and the visitor shared the porch light, and the wind felt smaller, as if it had been told to sit in the corner.")
    world.facts.update(hero=hero, visitor=guest, visitor_def=visitor, place=place)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, visitor = f["hero"], f["visitor_def"]
    return [
        f'Write a short tall tale for a young child about a surprise visitor and a brave child named {hero.id}.',
        f"Tell a windy farm story where {hero.id} sees {visitor.label} and finds courage fast.",
        f"Write a simple story that starts with a surprise visitor and ends with bravery making the visit friendly.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, visitor, place = f["hero"], f["visitor_def"], f["place"]
    qa = [
        QAItem(
            question=f"Who was the story about?",
            answer=f"It was about {hero.id}, a little {hero.traits[1]} child at {place.name}, and a surprise visitor who came with a big, bold entrance.",
        ),
        QAItem(
            question=f"Why did {hero.id} feel nervous when the visitor arrived?",
            answer=f"{hero.id} felt nervous because the visitor seemed very large and sudden, and the windy day made everything feel even bigger.",
        ),
        QAItem(
            question=f"What brave thing did {hero.id} do?",
            answer=f"{hero.id} ran to the gate and shut it before the wind could fling it open again, which kept the place safe for the visitor.",
        ),
        QAItem(
            question=f"How did the visit end?",
            answer=f"It ended happily, with {hero.id} feeling proud and the visitor turning out to be friendly and full of good things to share.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is bravery?",
            answer="Bravery is doing the right thing even when you feel scared or nervous.",
        ),
        QAItem(
            question="What is a visitor?",
            answer="A visitor is someone who comes to see a place or the people there for a while.",
        ),
        QAItem(
            question="What is a surprise?",
            answer="A surprise is something you did not expect to happen, so it can make you gasp or smile.",
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.traits:
            bits.append(f"traits={e.traits}")
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:12} ({e.kind:9}) {' '.join(bits)}")
    return "\n".join(lines)


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


def generate(params: StoryParams) -> StorySample:
    world = make_world(params)
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
        print(asp_program())
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program())
        print(f"{len(set(asp.atoms(model, 'reasonable')))} reasonable pair(s)")
        for p, v in sorted(set(asp.atoms(model, "reasonable"))):
            print(f"  {p}: {v}")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if getattr(args, "all", None):
        curated = [
            StoryParams(place="farm", hero_name="Mina", hero_gender="girl", hero_trait="brave", visitor="giant_traveler"),
            StoryParams(place="farm", hero_name="Jasper", hero_gender="boy", hero_trait="curious", visitor="high_wind_courier"),
            StoryParams(place="porch", hero_name="Ivy", hero_gender="girl", hero_trait="steady", visitor="bearded_lumber"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 20):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError:
                continue
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
        header = f"### variant {i + 1}" if len(samples) > 1 and not getattr(args, "all", None) else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
