#!/usr/bin/env python3
"""
Storyworld: fawn_pin_owie_sound_effects_friendship_problem.py

A tiny nursery-rhyme style story domain about a fawn, a pin, an owie,
friendly help, and a simple problem solved with sound effects.
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
# Core model
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
    carried_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    traits: list[str] = field(default_factory=list)
    plural: bool = False

    fawn: object | None = None
    helper: object | None = None
    pin: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"fawn", "deer"}:
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        if self.type in {"mouse"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"bunny", "rabbit"}:
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
class Place:
    name: str
    sound: str
    has_pin: bool = False
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
    helper: str
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

    def copy(self) -> "World":
        import copy as _copy
        w = World(self.place)
        w.entities = _copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        return w


# ---------------------------------------------------------------------------
# Settings / registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "meadow": Place(name="the meadow", sound="swish-swish", has_pin=True),
    "garden": Place(name="the garden", sound="tippity-tap", has_pin=True),
    "lane": Place(name="the lane", sound="clip-clop", has_pin=True),
    "pond": Place(name="the pond", sound="plip-plop", has_pin=False),
}

HELPERS = {
    "mouse": {"type": "mouse", "label": "mouse", "phrase": "a tiny mouse"},
    "bunny": {"type": "bunny", "label": "bunny", "phrase": "a bright bunny"},
    "sparrow": {"type": "sparrow", "label": "sparrow", "phrase": "a small sparrow"},
}


# ---------------------------------------------------------------------------
# Reasonableness helpers
# ---------------------------------------------------------------------------

def has_pin_problem(place: Place) -> bool:
    return place.has_pin


def helper_can_fix(helper: str) -> bool:
    return helper in HELPERS


def resolve_combo(place: str, helper: str) -> bool:
    return place in SETTINGS and helper in HELPERS and has_pin_problem(_safe_lookup(SETTINGS, place)) and helper_can_fix(helper)


def explain_rejection(place: str, helper: str) -> str:
    if place not in SETTINGS:
        return "(No story: that place is not part of this little world.)"
    if not _safe_lookup(SETTINGS, place).has_pin:
        return "(No story: there is no pin there, so no owie to solve.)"
    if helper not in HELPERS:
        return "(No story: that helper is not part of this little world.)"
    return "(No story: that pairing does not make a clear pin-and-owie problem.)"


# ---------------------------------------------------------------------------
# Story model
# ---------------------------------------------------------------------------

def nursery_sound(place: Place) -> str:
    return place.sound


def _fawn_steps(world: World, fawn: Entity) -> None:
    fawn.meters["restless"] += 1
    world.say(
        f"By {world.place.name}, a little fawn went tip-tap-tap, "
        f"while the grass went {nursery_sound(world.place)}."
    )


def _pin_prick(world: World, fawn: Entity) -> None:
    if not world.place.has_pin:
        return
    sig = ("pin_prick", fawn.id)
    if sig in world.fired:
        return
    world.fired.add(sig)
    fawn.meters["owie"] += 1
    fawn.memes["surprised"] += 1
    world.say("Ouch-tee, ouch-tee, tiny pin!")


def _friends_notice(world: World, fawn: Entity, helper: Entity) -> None:
    if fawn.meters.get("owie", 0.0) < THRESHOLD:
        return
    sig = ("notice", helper.id, fawn.id)
    if sig in world.fired:
        return
    world.fired.add(sig)
    helper.memes["kind"] += 1
    world.say(
        f"{helper.id.capitalize()} heard the little cry and hurried near. "
        f'"Oh dear, oh dear," said {helper.id}, "let us help!"'
    )


def _problem_solve(world: World, fawn: Entity, helper: Entity) -> None:
    if fawn.meters.get("owie", 0.0) < THRESHOLD:
        return
    sig = ("fix", helper.id, fawn.id)
    if sig in world.fired:
        return
    world.fired.add(sig)
    fawn.meters["owie"] = 0.0
    fawn.memes["calm"] += 1
    world.say(
        f"With a soft pat and a careful look, {helper.id} found the pin and moved it away. "
        f"Then it said, \"There, there now.\""
    )
    world.say(
        f"{helper.id.capitalize()} made a wee bandage, and the fawn felt fine again."
    )


def tell(place_name: str, helper_name: str) -> World:
    if place_name not in SETTINGS:
        pass
    if helper_name not in HELPERS:
        pass

    place = _safe_lookup(SETTINGS, place_name)
    helper_cfg = _safe_lookup(HELPERS, helper_name)
    world = World(place)

    fawn = world.add(Entity(
        id="Fawn",
        kind="character",
        type="fawn",
        label="fawn",
        phrase="a little fawn",
        traits=["small", "gentle", "curious"],
    ))
    helper = world.add(Entity(
        id=helper_name,
        kind="character",
        type=helper_cfg["type"],
        label=helper_cfg["label"],
        phrase=helper_cfg["phrase"],
        traits=["kind", "helpful"],
    ))
    pin = world.add(Entity(
        id="Pin",
        kind="thing",
        type="pin",
        label="pin",
        phrase="a shiny pin",
        owner=None,
    ))

    world.facts.update(place=place_name, helper=helper_name, fawn=fawn, pin=pin)

    world.say(
        f"Under {place.name}, a little fawn was wandering in a nursery-rhyme way, "
        f"soft as a puff and light as a breeze."
    )
    world.say(
        f"The ground sang {nursery_sound(place)}, and the fawn bobbed its head to the tune."
    )
    world.para()

    _fawn_steps(world, fawn)
    if place.has_pin:
        world.say("Then came a prickly spark on a tiny foot.")
        _pin_prick(world, fawn)
    else:
        world.say("But the ground had no pin, so there was no little owie at all.")

    world.para()
    _friends_notice(world, fawn, helper)
    _problem_solve(world, fawn, helper)

    if fawn.meters.get("owie", 0.0) < THRESHOLD:
        world.say(
            f"After that, the fawn danced again, and the meadow went {nursery_sound(place)} "
            f"as if nothing had ever hurt."
        )
    else:
        world.say(
            f"The owie stayed small, but the helper stayed close, and that was still a comfort."
        )

    world.facts.update(resolved=fawn.meters.get("owie", 0.0) < THRESHOLD)
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short nursery-rhyme story about a fawn, a pin, and an owie at {SETTINGS[f["place"]].name}.',
        f"Tell a gentle friendship story where a {f['helper']} helps a little fawn after a pin makes an owie.",
        "Write a tiny rhyming story with sound effects, a small problem, and a kind fix.",
    ]


def story_qa(world: World) -> list[QAItem]:
    place = _safe_lookup(SETTINGS, world.facts.get("place")).name
    helper = _safe_fact(world, world.facts, "helper")
    resolved = _safe_fact(world, world.facts, "resolved")
    qa = [
        QAItem(
            question="Who was wandering at the start of the story?",
            answer=f"A little fawn was wandering in {place}.",
        ),
        QAItem(
            question="What made the fawn say owie?",
            answer="A shiny pin made the fawn feel a tiny owie.",
        ),
        QAItem(
            question="Who came to help the fawn?",
            answer=f"The {helper} came close and helped with the problem.",
        ),
    ]
    if resolved:
        qa.append(QAItem(
            question="How did the problem get better?",
            answer="The helper moved the pin away and made a tiny bandage, so the fawn felt fine again.",
        ))
    return qa


WORLD_KNOWLEDGE = {
    "fawn": [
        QAItem(
            question="What is a fawn?",
            answer="A fawn is a young deer.",
        )
    ],
    "pin": [
        QAItem(
            question="What is a pin?",
            answer="A pin is a small sharp object that can poke skin if someone is not careful.",
        )
    ],
    "owie": [
        QAItem(
            question="What is an owie?",
            answer="An owie is a small hurt or sore spot that needs gentle care.",
        )
    ],
    "friendship": [
        QAItem(
            question="What is friendship?",
            answer="Friendship is being kind, helping each other, and caring when a friend feels bad.",
        )
    ],
    "problem": [
        QAItem(
            question="What is problem solving?",
            answer="Problem solving means noticing a trouble and finding a helpful way to fix it.",
        )
    ],
    "sound": [
        QAItem(
            question="What are sound effects in a story?",
            answer="Sound effects are little sound words like tap-tap or swish-swish that help the story feel alive.",
        )
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        *WORLD_KNOWLEDGE["fawn"],
        *WORLD_KNOWLEDGE["pin"],
        *WORLD_KNOWLEDGE["owie"],
        *WORLD_KNOWLEDGE["friendship"],
        *WORLD_KNOWLEDGE["problem"],
        *WORLD_KNOWLEDGE["sound"],
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World knowledge ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


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
        lines.append(f"  {e.id:6} ({e.type}) {' '.join(bits)}")
    lines.append(f"  place={world.place.name}")
    lines.append(f"  fired={sorted(world.fired)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
#show valid/2.
#show valid_story/3.

valid(P,H) :- place(P), helper(H), pin_problem(P), helper_ok(H).
valid_story(P,H,F) :- valid(P,H), fawn(F).
"""

def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    for pid, place in SETTINGS.items():
        lines.append(asp.fact("place", pid))
        if place.has_pin:
            lines.append(asp.fact("pin_problem", pid))
    for hid in HELPERS:
        lines.append(asp.fact("helper", hid))
        lines.append(asp.fact("helper_ok", hid))
    lines.append(asp.fact("fawn", "fawn"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = {(p, h) for p in SETTINGS for h in HELPERS if resolve_combo(p, h)}
    asp_set = set(asp_valid_combos())
    if py == asp_set:
        print(f"OK: clingo gate matches resolve_combo() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and Python gates.")
    print("Python-only:", sorted(py - asp_set))
    print("ASP-only:", sorted(asp_set - py))
    return 1


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Nursery-rhyme story world: a fawn, a pin, and an owie.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--helper", choices=HELPERS)
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
    if getattr(args, "place", None) and getattr(args, "place", None) not in SETTINGS:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    if getattr(args, "helper", None) and getattr(args, "helper", None) not in HELPERS:
        return _fallback_storyparams(args, rng, StoryParams, globals())

    places = [p for p in SETTINGS if getattr(args, "place", None) is None or p == getattr(args, "place", None)]
    helpers = [h for h in HELPERS if getattr(args, "helper", None) is None or h == getattr(args, "helper", None)]
    combos = [(p, h) for p in places for h in helpers if resolve_combo(p, h)]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, helper = rng.choice(list(combos))
    return StoryParams(place=place, helper=helper)


def generate(params: StoryParams) -> StorySample:
    world = tell(params.place, params.helper)
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
        print(asp_program("#show valid_story/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, helper) combos:\n")
        for c in combos:
            print(" ", c)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if getattr(args, "all", None):
        for place in SETTINGS:
            for helper in HELPERS:
                if resolve_combo(place, helper):
                    p = StoryParams(place=place, helper=helper, seed=base_seed)
                    samples.append(generate(p))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 50):
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
