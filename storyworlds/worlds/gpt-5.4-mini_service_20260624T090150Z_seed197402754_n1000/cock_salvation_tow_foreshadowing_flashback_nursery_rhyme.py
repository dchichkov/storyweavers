#!/usr/bin/env python3
"""
A small story world for a nursery-rhyme-style rescue tale.

Seed tale inspiration:
---
A cock on a windy hill tries to boast and go too far, but the ground is soft,
a tow line is needed, and the little flock helps bring him back to safety.
A brief foreshadowing hints at the loose rope; a flashback recalls a warning
about the slippery path. In the end, the cock is saved and the field is calm.
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
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    cock: object | None = None
    ground: object | None = None
    hen: object | None = None
    rope: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "character" and self.type in {"hen", "mother", "girl"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.kind == "character" and self.type in {"cock", "rooster", "father", "boy"}:
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
    place: str
    features: set[str] = field(default_factory=set)
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
class Helper:
    id: str
    label: str
    tail: str
    tool: str
    supports: set[str] = field(default_factory=set)
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
    helper: str
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
    def __init__(self, setting: Setting):
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.facts: dict = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.trace: list[str] = []

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
            self.trace.append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        import copy as _copy

        w = World(self.setting)
        w.entities = _copy.deepcopy(self.entities)
        w.facts = dict(self.facts)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        return w


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "barnyard": Setting(place="the barnyard", features={"mud", "rope", "fence"}),
    "meadow": Setting(place="the meadow", features={"grass", "hill", "rope"}),
}

HELPERS = {
    "towrope": Helper(
        id="towrope",
        label="a tow rope",
        tail="the rope gave a gentle tug, and the path turned safe",
        tool="rope",
        supports={"mud", "ditch"},
    ),
    "wheelbarrow": Helper(
        id="wheelbarrow",
        label="a little wheelbarrow",
        tail="the wheelbarrow rolled carefully home",
        tool="wheel",
        supports={"mud", "hill"},
    ),
    "cart": Helper(
        id="cart",
        label="a small cart",
        tail="the cart trundled along like a toy in a song",
        tool="cart",
        supports={"mud", "fence"},
    ),
}

VALID_HELPERS = {"towrope", "wheelbarrow", "cart"}

VALID_PLACES = set(SETTINGS)


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------

def valid_combo(place: str, helper: str) -> bool:
    if place not in SETTINGS or helper not in HELPERS:
        return False
    setting = _safe_lookup(SETTINGS, place)
    h = _safe_lookup(HELPERS, helper)
    return bool(setting.features & h.supports)


def explain_rejection(place: str, helper: str) -> str:
    if place not in SETTINGS:
        return "(No story: that place is not part of this little world.)"
    if helper not in HELPERS:
        return "(No story: that helper is not part of this little world.)"
    h = _safe_lookup(HELPERS, helper)
    return (
        f"(No story: {h.label} does not fit the dangers of {_safe_lookup(SETTINGS, place).place}. "
        f"Choose a helper that can truly help there.)"
    )


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
place(barnyard).
place(meadow).

feature(barnyard,mud).
feature(barnyard,rope).
feature(barnyard,fence).
feature(meadow,grass).
feature(meadow,hill).
feature(meadow,rope).

helper(towrope).
helper(wheelbarrow).
helper(cart).

supports(towrope,rope).
supports(towrope,mud).
supports(towrope,ditch).
supports(wheelbarrow,mud).
supports(wheelbarrow,hill).
supports(cart,mud).
supports(cart,fence).

valid(P,H) :- place(P), helper(H), feature(P,F), supports(H,F).
#show valid/2.
"""


def asp_facts() -> str:
    import asp

    return "\n".join(
        [asp.fact("place", p) for p in SETTINGS]
        + [asp.fact("feature", p, f) for p, s in SETTINGS.items() for f in sorted(s.features)]
        + [asp.fact("helper", h) for h in HELPERS]
        + [asp.fact("supports", h.id, s) for h in HELPERS.values() for s in sorted(h.supports)]
    )


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple[str, str]]:
    import asp

    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = {c for c in valid_combos()}
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and python:")
    print("  only in python:", sorted(py - cl))
    print("  only in clingo:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# Story building
# ---------------------------------------------------------------------------

def build_world(params: StoryParams) -> World:
    world = World(_safe_lookup(SETTINGS, params.place))
    cock = world.add(Entity(id="Cock", kind="character", type="cock"))
    hen = world.add(Entity(id="Hen", kind="character", type="hen"))
    helper = _safe_lookup(HELPERS, params.helper)
    rope = world.add(Entity(id="Tow", type="tool", label=helper.label, phrase=helper.label, owner="Hen"))
    ground = world.add(Entity(id="Ground", type="thing", label="soft ground"))

    cock.meters["brave"] = 1.0
    cock.memes["pride"] = 1.0
    hen.meters["care"] = 1.0
    world.facts.update(cock=cock, hen=hen, helper=helper, rope=rope, ground=ground)
    return world


def predict_fall(world: World) -> bool:
    cock = world.get("Cock")
    return cock.meters.get("mud", 0.0) + cock.memes.get("dare", 0.0) >= 1.0


def foreshadow(world: World) -> None:
    world.say(
        "By the fence there hung a tow rope, thin and neat, "
        "and it swayed in the breeze like a hint at the feet."
    )
    world.facts["foreshadowed"] = True


def flashback(world: World) -> None:
    world.say(
        "The hen remembered, with a tiny little grin, "
        "how she had warned the cock: 'Slow steps win.'"
    )
    world.facts["flashback"] = True


def trouble(world: World) -> None:
    cock = world.get("Cock")
    cock.memes["dare"] += 1
    cock.meters["mud"] += 1
    world.say(
        "The cock was bold and crowed, 'I can cross that bog!' "
        "But the mud went squish, and he slipped in a jog."
    )


def rescue(world: World) -> None:
    cock = world.get("Cock")
    hen = world.get("Hen")
    helper = _safe_fact(world, world.facts, "helper")
    cock.memes["fear"] += 1
    cock.meters["stuck"] += 1
    world.say(
        f"{hen.pronoun('subject').capitalize()} called, 'Hold still now, friend, don't fret or frown; "
        f"we'll use {helper.label} to tow you down.'"
    )
    cock.memes["hope"] += 1
    cock.meters["stuck"] = 0.0
    cock.meters["safe"] = 1.0
    world.say(
        f"Then {helper.label} gave a tug so light, {cock.pronoun('object')} was saved by dusk's soft light."
    )
    world.say(
        "The mud stayed in the meadow, the cock stood tall and neat, "
        "and every little feather looked airy, clean, and sweet."
    )
    cock.memes["joy"] += 1
    cock.memes["gratitude"] = 1.0
    hen.memes["relief"] = 1.0


def tell(world: World) -> World:
    cock = world.get("Cock")
    hen = world.get("Hen")
    helper = _safe_fact(world, world.facts, "helper")

    world.say(
        "In the barnyard bright, where the daisies grow, lived a little cock who loved to strut and show."
    )
    world.say(
        "He liked to crow at morning, loud and high, as if the sun had answered from the sky."
    )
    world.say(
        f"The {hen.type} watched kindly and kept him in sight, for some paths looked slippery in morning light."
    )
    foreshadow(world)
    world.para()
    flashback(world)
    world.para()
    trouble(world)
    if predict_fall(world):
        rescue(world)
    world.facts["resolved"] = True
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    p = _safe_fact(world, world.facts, "params")
    return [
        f'Write a short nursery-rhyme story about a cock in {p.place} who needs a tow rescue.',
        f'Tell a gentle rhyming story with foreshadowing and flashback, using the word "{p.helper}".',
        "Write a child-friendly rescue tale where pride turns into safety and help arrives in time.",
    ]


def story_qa(world: World) -> list[QAItem]:
    place = _safe_fact(world, world.facts, "params").place
    helper = _safe_fact(world, world.facts, "helper").label
    return [
        QAItem(
            question="Who was the story about?",
            answer="It was about a little cock who loved to crow, and a kind hen who helped him when the path got slippery.",
        ),
        QAItem(
            question=f"What did {helper} do in the story?",
            answer=f"{helper} helped tow the cock out of the muddy trouble and bring him safely back to the barnyard.",
        ),
        QAItem(
            question=f"Why was the cock in danger at {place}?",
            answer="He tried to cross soft mud after acting too bold, and his feet slipped so he got stuck.",
        ),
        QAItem(
            question="What was the foreshadowing?",
            answer="The hanging tow rope by the fence hinted that a rescue might be needed later.",
        ),
        QAItem(
            question="What was the flashback about?",
            answer="It remembered the hen warning the cock to take slow steps on slippery ground.",
        ),
        QAItem(
            question="How did the story end?",
            answer="The cock was towed to safety, the mud stayed behind, and everyone felt relieved and calm.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a tow rope for?",
            answer="A tow rope is used to pull something carefully when it cannot move by itself.",
        ),
        QAItem(
            question="What does foreshadowing do in a story?",
            answer="Foreshadowing gives a small hint about something important that may happen later.",
        ),
        QAItem(
            question="What does a flashback do in a story?",
            answer="A flashback shows or remembers something from before the current moment in the story.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for p in sample.prompts:
        lines.append(f"- {p}")
    lines.append("")
    lines.append("== Story Q&A ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== World Q&A ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------

def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = getattr(args, "place", None) or rng.choice(sorted(SETTINGS))
    helper = getattr(args, "helper", None) or rng.choice(sorted(VALID_HELPERS))
    if not valid_combo(place, helper):
        return _fallback_storyparams(args, rng, StoryParams, globals())
    return StoryParams(place=place, helper=helper, seed=getattr(args, "seed", None))


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    world.facts["params"] = params
    tell(world)
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
        print("\n--- trace ---")
        for line in sample.world.trace:
            print(line)
    if qa:
        print()
        print(format_qa(sample))


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

CURATED = [
    StoryParams(place="barnyard", helper="towrope"),
    StoryParams(place="meadow", helper="wheelbarrow"),
    StoryParams(place="barnyard", helper="cart"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Nursery-rhyme rescue storyworld about a cock and a tow.")
    ap.add_argument("--place", choices=sorted(SETTINGS))
    ap.add_argument("--helper", choices=sorted(HELPERS))
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


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        combos = asp_valid_combos()
        print(f"{len(combos)} valid combos:")
        for p, h in combos:
            print(f"  {p:9} {h}")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        i = 0
        seen: set[str] = set()
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 50):
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

    for idx, sample in enumerate(samples):
        if len(samples) > 1:
            print(f"### variant {idx + 1}")
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None))
        if idx < len(samples) - 1:
            print("\n" + "=" * 72 + "\n")


if __name__ == "__main__":
    main()
