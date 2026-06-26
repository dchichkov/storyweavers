#!/usr/bin/env python3
"""
Standalone storyworld: allosaurus, inlay, rate.

A small superhero-style domain with a cheerful allosaurus hero, a broken inlay,
and a noisy rate that can run too fast or too slow. Stories are simulated from
world state, with an inner monologue beat, a rhymed rescue beat, and a happy
ending.
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
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    wearable: bool = False
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    hero: object | None = None
    sidekick: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
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
class City:
    place: str
    has_clock_tower: bool = True
    has_museum: bool = True
    has_plaza: bool = True
    activity: str = "repair"
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
class Gear:
    id: str
    label: str
    prep: str
    tail: str
    covers: set[str] = field(default_factory=set)
    fixes: set[str] = field(default_factory=set)
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
    place: str
    hero_name: str
    sidekick_name: str
    broken_part: str
    gear: str
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
    def __init__(self, city: City) -> None:
        self.city = city
        self.entities: dict[str, Entity] = {}
        self.facts: dict = {}
        self.lines: list[str] = []
        self.paragraphs: list[list[str]] = [[]]
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


GADGETS = {
    "polish": Gear(
        id="polish",
        label="polish kit",
        prep="open the polish kit",
        tail="buffed the inlay until it shone",
        covers={"surface"},
        fixes={"inlay"},
    ),
    "glue": Gear(
        id="glue",
        label="glue packet",
        prep="uncap the glue packet",
        tail="pressed the inlay back into place",
        covers={"surface"},
        fixes={"inlay"},
    ),
    "rhythm": Gear(
        id="rhythm",
        label="rhythm clicker",
        prep="tap the rhythm clicker",
        tail="matched the rate to a steady beat",
        covers={"sound"},
        fixes={"rate"},
    ),
}

PLACES = {
    "museum": City(place="the museum", has_museum=True, has_clock_tower=False, has_plaza=True),
    "tower": City(place="the clock tower", has_clock_tower=True, has_museum=False, has_plaza=True),
    "plaza": City(place="the sunny plaza", has_plaza=True, has_clock_tower=False, has_museum=False),
}

BROKEN_PARTS = {
    "inlay": {"problem": "missing", "risk": "the sign looked patchy and plain", "need": "sparkle"},
    "rate": {"problem": "too fast", "risk": "the tower bell was ringing all wrong", "need": "steady"},
}

HEROES = ["Nova", "Rex", "Pip", "Milo", "Zara", "Quill"]
SIDEKICKS = ["Bean", "Toby", "Luma", "Mina", "Dori", "Fenn"]


def _inner_monologue(hero: Entity, broken_part: str) -> str:
    if broken_part == "inlay":
        return f'"I can fix this," thought {hero.id}. "A bright inlay can help the whole place smile."'
    return f'"I can slow this down," thought {hero.id}. "A steady rate keeps the whole city calm."'


def _rhyme_line(broken_part: str) -> str:
    if broken_part == "inlay":
        return "Tap and shine, fit it fine, make the little starry line."
    return "Slow and low, steady go, keep the happy heartbeat flow."


def _setup_story(world: World, hero: Entity, sidekick: Entity, broken_part: str) -> None:
    world.say(
        f"{hero.id} was a brave allosaurus superhero with a big heart and a bright cape."
    )
    world.say(
        f"{hero.id} and {sidekick.id} patrolled {world.city.place}, where people loved the warm sunny streets."
    )
    if broken_part == "inlay":
        world.say(
            f"At the museum, a glass sign had a missing inlay, and the little jewel spot looked lonely."
        )
        hero.memes["worry"] += 1
    else:
        world.say(
            f"At the clock tower, the bell's rate was too fast, and the whole square felt jumpy."
        )
        hero.memes["worry"] += 1


def _act(world: World, hero: Entity, broken_part: str, gear: Gear) -> None:
    world.para()
    world.say(_inner_monologue(hero, broken_part))
    world.say(
        f"{hero.id} zipped into action and used the {gear.label}."
    )
    world.say(_rhyme_line(broken_part))
    world.say(f"Then {hero.id} {gear.tail}.")
    if broken_part == "inlay":
        world.facts["fixed"] = "inlay"
        world.facts["sparkle"] = True
        hero.meters["help"] = 1
    else:
        world.facts["fixed"] = "rate"
        world.facts["steady"] = True
        hero.meters["help"] = 1


def _ending(world: World, hero: Entity, sidekick: Entity, broken_part: str) -> None:
    world.para()
    if broken_part == "inlay":
        world.say(
            f"The sign shone again, with the inlay glowing like a tiny moon."
        )
        world.say(
            f"{sidekick.id} clapped, and {hero.id} smiled at the happy little sparkle."
        )
    else:
        world.say(
            f"The bell found a steady beat, and the tower sounded calm and kind."
        )
        world.say(
            f"{sidekick.id} cheered, and {hero.id} nodded as the city settled into a peaceful rhythm."
        )
    world.say(
        f"It was a happy ending, because the broken thing was fixed and the whole place felt better."
    )


def tell(place: City, hero_name: str, sidekick_name: str, broken_part: str, gear_id: str) -> World:
    if broken_part not in BROKEN_PARTS:
        pass
    if gear_id not in GADGETS:
        pass
    gear = _safe_lookup(GADGETS, gear_id)
    if broken_part not in gear.fixes:
        pass

    world = World(place)
    hero = world.add(Entity(id=hero_name, kind="character", type="allosaurus"))
    sidekick = world.add(Entity(id=sidekick_name, kind="character", type="sidekick"))
    world.facts.update(hero=hero, sidekick=sidekick, broken_part=broken_part, gear=gear)

    _setup_story(world, hero, sidekick, broken_part)
    _act(world, hero, broken_part, gear)
    _ending(world, hero, sidekick, broken_part)
    return world


def build_story(params: StoryParams) -> StorySample:
    world = tell(
        _safe_lookup(PLACES, params.place),
        params.hero_name,
        params.sidekick_name,
        params.broken_part,
        params.gear,
    )
    story = world.render()
    prompts = [
        f"Write a superhero story about an allosaurus named {params.hero_name} who helps in {params.place}.",
        f"Tell a gentle story with the words allosaurus, inlay, and rate, and end with a happy ending.",
        f"Write a rhyming rescue story where {params.hero_name} fixes a problem with a clever tool.",
    ]
    story_qa = [
        QAItem(
            question=f"Who is the superhero in the story?",
            answer=f"The superhero is a brave allosaurus named {params.hero_name}.",
        ),
        QAItem(
            question=f"What problem did {params.hero_name} fix?",
            answer=(
                f"{params.hero_name} fixed the {params.broken_part}, using a {_safe_lookup(GADGETS, params.gear).label}."
            ),
        ),
        QAItem(
            question="How did the story end?",
            answer="It ended happily, with the broken thing repaired and everyone feeling glad.",
        ),
    ]
    world_qa = [
        QAItem(
            question="What is an allosaurus?",
            answer="An allosaurus was a large meat-eating dinosaur, but in this story it is a kind and heroic character.",
        ),
        QAItem(
            question="What is an inlay?",
            answer="An inlay is a small piece set into something else to make it look special or decorative.",
        ),
        QAItem(
            question="What does rate mean?",
            answer="Rate means how fast or slow something happens, like a bell ringing quickly or steadily.",
        ),
    ]
    return StorySample(
        params=params,
        story=story,
        prompts=prompts,
        story_qa=story_qa,
        world_qa=world_qa,
        world=world,
    )


def generate(params: StoryParams) -> StorySample:
    return build_story(params)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:10} ({e.kind:9}) {' '.join(bits)}")
    lines.append(f"  facts: {world.facts}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Superhero storyworld with an allosaurus, an inlay, and a rate problem.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--hero-name", choices=HEROES)
    ap.add_argument("--sidekick-name", choices=SIDEKICKS)
    ap.add_argument("--broken-part", choices=BROKEN_PARTS)
    ap.add_argument("--gear", choices=GADGETS)
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
    broken_part = getattr(args, "broken_part", None) or rng.choice(list(BROKEN_PARTS))
    gear = getattr(args, "gear", None) or rng.choice([g.id for g in GADGETS.values() if broken_part in g.fixes])
    if broken_part not in _safe_lookup(GADGETS, gear).fixes:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    return StoryParams(
        place=getattr(args, "place", None) or rng.choice(list(PLACES)),
        hero_name=getattr(args, "hero_name", None) or rng.choice(HEROES),
        sidekick_name=getattr(args, "sidekick_name", None) or rng.choice(SIDEKICKS),
        broken_part=broken_part,
        gear=gear,
    )


ASP_RULES = r"""
place(museum; tower; plaza).
hero(nova; rex; pip; milo; zara; quill).
sidekick(bean; toby; luma; mina; dori; fenn).
broken(inlay; rate).
gear(polish; glue; rhythm).

fixes(polish, inlay).
fixes(glue, inlay).
fixes(rhythm, rate).

valid(P, H, S, B, G) :- place(P), hero(H), sidekick(S), broken(B), gear(G), fixes(G, B).
#show valid/5.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for p in PLACES:
        lines.append(asp.fact("place", p))
    for h in HEROES:
        lines.append(asp.fact("hero", h))
    for s in SIDEKICKS:
        lines.append(asp.fact("sidekick", s))
    for b in BROKEN_PARTS:
        lines.append(asp.fact("broken", b))
    for g in GADGETS:
        lines.append(asp.fact("gear", g))
    for g in GADGETS.values():
        for b in g.fixes:
            lines.append(asp.fact("fixes", g.id, b))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/5."))
    return sorted(set(asp.atoms(model, "valid")))


def python_valid() -> list[tuple]:
    out = []
    for p in PLACES:
        for h in HEROES:
            for s in SIDEKICKS:
                for b in BROKEN_PARTS:
                    for g, gear in GADGETS.items():
                        if b in gear.fixes:
                            out.append((p, h, s, b, g))
    return sorted(out)


def asp_verify() -> int:
    a = set(asp_valid())
    p = set(python_valid())
    if a == p:
        print(f"OK: clingo gate matches python gate ({len(a)} combinations).")
        return 0
    print("MISMATCH:")
    print("only in asp:", sorted(a - p))
    print("only in python:", sorted(p - a))
    return 1


CURATED = [
    StoryParams(place="museum", hero_name="Nova", sidekick_name="Bean", broken_part="inlay", gear="polish"),
    StoryParams(place="tower", hero_name="Rex", sidekick_name="Toby", broken_part="rate", gear="rhythm"),
    StoryParams(place="plaza", hero_name="Zara", sidekick_name="Luma", broken_part="inlay", gear="glue"),
]


def generate_and_emit(args: argparse.Namespace) -> list[StorySample]:
    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        for p in CURATED:
            samples.append(generate(p))
        return samples

    seen: set[str] = set()
    i = 0
    while len(samples) < getattr(args, "n", None) and i < max(getattr(args, "n", None) * 50, 50):
        params = resolve_params(args, random.Random(base_seed + i))
        params.seed = base_seed + i
        sample = generate(params)
        i += 1
        if sample.story in seen:
            continue
        seen.add(sample.story)
        samples.append(sample)
    return samples


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/5."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        vals = asp_valid()
        print(f"{len(vals)} valid combinations:")
        for row in vals:
            print(" ", row)
        return

    samples = generate_and_emit(args)

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
            header = f"### {p.hero_name}: {p.broken_part} at {p.place} with {p.gear}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
