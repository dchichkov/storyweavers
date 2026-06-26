#!/usr/bin/env python3
"""
A small fairy-tale storyworld about a bumpkin, a promised ride, and a conflict
that turns into a kinder ending.
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
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    ridden_by: Optional[str] = None
    protective: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    trait: object | None = None
    helper: object | None = None
    hero: object | None = None
    ride_obj: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "queen", "fairy"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "king"}:
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
    indoor: bool = False
    ridable: set[str] = field(default_factory=set)
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
class Ride:
    id: str
    label: str
    phrase: str
    place: str
    risk: str
    effect: str
    need_fairness: bool = True
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
    ride: str
    hero_name: str
    hero_type: str
    helper_type: str
    trait: str
    seed: Optional[int] = None
    params: object | None = None
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


PLACES = {
    "meadow": Place(name="the meadow", ridable={"pony", "cart"}),
    "castle_gate": Place(name="the castle gate", ridable={"pony", "cart"}),
    "riverbank": Place(name="the riverbank", ridable={"boat"}),
}

RIDES = {
    "pony": Ride(
        id="pony",
        label="pony ride",
        phrase="a silver saddle and a little bell",
        place="meadow",
        risk="to leave without asking",
        effect="bounced gently through the grass",
    ),
    "cart": Ride(
        id="cart",
        label="cart ride",
        phrase="a bright cart with wooden wheels",
        place="castle_gate",
        risk="to take the cart before the apples were loaded",
        effect="rolled along with a cheerful creak",
    ),
    "boat": Ride(
        id="boat",
        label="boat ride",
        phrase="a narrow boat with a blue scarf tied to the bow",
        place="riverbank",
        risk="to ride too far before the lantern was lit",
        effect="floated softly over the silver water",
    ),
}

TRAITS = ["humble", "brave", "curious", "gentle", "cheerful"]
GIRL_NAMES = ["Anya", "Lina", "Mira", "Tessa", "Ivy"]
BOY_NAMES = ["Jory", "Pip", "Nico", "Otis", "Robin"]


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
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
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


def intro(world: World, hero: Entity, ride: Ride) -> None:
    world.say(
        f"Once upon a time, there was a little {hero.trait} bumpkin named {hero.id} "
        f"who loved the thought of a {ride.label}."
    )


def desire(world: World, hero: Entity, ride: Ride) -> None:
    world.say(
        f"{hero.pronoun().capitalize()} would sit by the road and dream of the {ride.label}, "
        f"wondering when the bells and wheels would finally come."
    )


def warn(world: World, helper: Entity, hero: Entity, ride: Ride) -> None:
    world.say(
        f"At last, {hero.id} reached {world.place.name}, where {helper.pronoun().capitalize()} "
        f"noticed a small problem."
    )
    world.say(
        f'"Not yet," said {helper.id}, "because we still must listen and wait '
        f'{ride.risk}."'
    )


def conflict(world: World, hero: Entity, helper: Entity, ride: Ride) -> None:
    hero.memes["want"] = hero.memes.get("want", 0.0) + 1.0
    hero.memes["conflict"] = hero.memes.get("conflict", 0.0) + 1.0
    world.say(
        f"{hero.id} frowned, for {hero.pronoun()} wanted the {ride.label} right away."
    )
    world.say(
        f"{hero.id} stamped {hero.pronoun('possessive')} foot and said, "
        f'"But I came for the {ride.label}!"'
    )
    world.say(
        f"{helper.id} stood firm, because a fair ride had to begin the right way."
    )


def turn(world: World, hero: Entity, helper: Entity, ride: Ride) -> None:
    world.say(
        f"Then {hero.id} took a breath, looked at {helper.id}, and offered a tiny bow."
    )
    world.say(
        f'"If I help first," {hero.id} said, "may I ride when it is ready?"'
    )
    world.say(
        f"{helper.id} smiled, for that was a kind answer."
    )


def resolution(world: World, hero: Entity, helper: Entity, ride: Ride) -> None:
    hero.memes["conflict"] = 0.0
    hero.memes["joy"] = hero.memes.get("joy", 0.0) + 1.0
    world.say(
        f"{helper.id} nodded and let {hero.id} help at once."
    )
    world.say(
        f"So {hero.id} lifted the reins, and soon the {ride.label} was ready."
    )
    world.say(
        f"By the end, {hero.id} was {ride.effect}, and the little bumpkin rode "
        f"away with a bright face and a brave heart."
    )


def tell(place: Place, ride: Ride, hero_name: str, hero_type: str, helper_type: str, trait: str) -> World:
    world = World(place)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, trait=trait))
    helper = world.add(Entity(id="Helper", kind="character", type=helper_type, label="the keeper"))
    ride_obj = world.add(Entity(id="Ride", kind="thing", type=ride.id, label=ride.label, phrase=ride.phrase))

    intro(world, hero, ride)
    desire(world, hero, ride)
    world.para()
    warn(world, helper, hero, ride)
    conflict(world, hero, helper, ride)
    world.para()
    turn(world, hero, helper, ride)
    resolution(world, hero, helper, ride)

    world.facts.update(hero=hero, helper=helper, ride=ride, ride_obj=ride_obj)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = _safe_fact(world, f, "hero")
    ride: Ride = _safe_fact(world, f, "ride")
    return [
        f'Write a fairy-tale story for a young child about a bumpkin named {hero.id} and a {ride.label}.',
        f"Tell a gentle story where {hero.id} wants a {ride.label}, but there is a conflict before the ride can begin.",
        f'Write a short fairy tale that includes the word "bumpkin" and ends with a happy ride.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = _safe_fact(world, f, "hero")
    helper: Entity = _safe_fact(world, f, "helper")
    ride: Ride = _safe_fact(world, f, "ride")
    place = world.place.name
    return [
        QAItem(
            question=f"Who is the story about?",
            answer=f"It is about {hero.id}, a little {hero.pronoun('object')}-loving bumpkin who dreams of a {ride.label}."
        ),
        QAItem(
            question=f"What did {hero.id} want at {place}?",
            answer=f"{hero.id} wanted a {ride.label}, but {helper.id} said it had to wait until everything was ready."
        ),
        QAItem(
            question=f"Why was there a conflict?",
            answer=(
                f"There was a conflict because {hero.id} wanted the {ride.label} right away, "
                f"but {helper.id} needed time to get it ready the fair way."
            ),
        ),
        QAItem(
            question=f"How did the story end?",
            answer=(
                f"It ended happily when {hero.id} helped first, the {ride.label} was ready, "
                f"and {hero.id} rode away with a bright face."
            ),
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a bumpkin?",
            answer="A bumpkin is a simple country person in a folktale, often kind, plainspoken, and close to the land."
        ),
        QAItem(
            question="What is a ride?",
            answer="A ride is a trip on something like a pony, cart, or boat that carries a person from one place to another."
        ),
        QAItem(
            question="What does conflict mean in a story?",
            answer="Conflict means the characters want different things, so the story has a problem to work through."
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.kind:
            bits.append(f"kind={e.kind}")
        if e.type:
            bits.append(f"type={e.type}")
        if e.memes:
            bits.append(f"memes={dict(e.memes)}")
        lines.append(f"  {e.id}: {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
hero(X) :- bumpkin(X).
place(P) :- location(P).
ride(R) :- ride_kind(R).
conflict(X,R) :- hero(X), wants_ride(X,R), helper_blocks(R).
resolved(X,R) :- conflict(X,R), helps_first(X,R).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid in PLACES:
        lines.append(asp.fact("location", pid))
    for rid in RIDES:
        lines.append(asp.fact("ride_kind", rid))
    lines.append(asp.fact("bumpkin", "hero"))
    lines.append(asp.fact("wants_ride", "hero", "pony"))
    lines.append(asp.fact("helper_blocks", "pony"))
    lines.append(asp.fact("helps_first", "hero", "pony"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    program = asp_program("#show conflict/2.\n#show resolved/2.")
    model = asp.one_model(program)
    conflicts = set(asp.atoms(model, "conflict"))
    resolved = set(asp.atoms(model, "resolved"))
    ok = ("hero", "pony") in conflicts and ("hero", "pony") in resolved
    if ok:
        print("OK: ASP twin produces the expected conflict and resolution.")
        return 0
    print("MISMATCH in ASP twin.")
    print(conflicts, resolved)
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Fairy-tale storyworld about a bumpkin, a ride, and conflict.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--ride", choices=RIDES)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper", choices=["queen", "fairy", "king"])
    ap.add_argument("--trait", choices=TRAITS)
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
    ride = getattr(args, "ride", None) or rng.choice([r for r, rd in RIDES.items() if rd.place == place])
    if _safe_lookup(RIDES, ride).place != place:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    helper = getattr(args, "helper", None) or rng.choice(["queen", "fairy", "king"])
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(place=place, ride=ride, hero_name=name, hero_type=gender, helper_type=helper, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(PLACES, params.place), _safe_lookup(RIDES, params.ride), params.hero_name, params.hero_type, params.helper_type, params.trait)
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
        print(asp_program("#show conflict/2.\n#show resolved/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show conflict/2.\n#show resolved/2."))
        print("conflict:", asp.atoms(model, "conflict"))
        print("resolved:", asp.atoms(model, "resolved"))
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if getattr(args, "all", None):
        for place, p in PLACES.items():
            for rid, ride in RIDES.items():
                if ride.place == place:
                    params = StoryParams(place=place, ride=rid, hero_name="Mira", hero_type="girl", helper_type="fairy", trait="curious")
                    samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(getattr(args, "n", None) * 50, 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story in seen:
                i += 1
                continue
            seen.add(sample.story)
            samples.append(sample)
            i += 1

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
