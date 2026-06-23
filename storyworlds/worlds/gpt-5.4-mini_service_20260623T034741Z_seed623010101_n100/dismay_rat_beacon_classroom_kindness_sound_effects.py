#!/usr/bin/env python3
"""
storyworlds/worlds/dismay_rat_beacon_classroom_kindness_sound_effects.py
=======================================================================

A tiny classroom storyworld about a sudden rat, a little beacon of light,
kindness from classmates, and sound effects that change the mood.

Seed tale:
---
In a classroom, a child gets in dismay when a rat scurries out by the wall.
A small beacon light flickers under the desk, and the room fills with squeaks,
skids, and gasps. Instead of shouting, one child offers kindness: a calm hand,
a shared snack box, and a soft song. The rat follows the crumbs back to a nook,
the beacon shines steady, and the classroom learns that gentle help can change a
scary moment into a safe one.
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
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
            keys = [upper + "S", upper + "ES"]
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
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    tags: set[str] = field(default_factory=set)

    beacon: object | None = None
    child: object | None = None
    helper: object | None = None
    rat: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "teacher"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]
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
class Classroom:
    name: str = "the classroom"
    place: str = "classroom"
    tone: str = "rhyming"
    tags: set[str] = field(default_factory=lambda: {"classroom", "kindness", "sound_effects"})
    SETTINGS: set[str] = field(default_factory=set)
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
class Choice:
    id: str
    word: str
    sound: str
    tags: set[str] = field(default_factory=set)
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
    def __init__(self, setting: Classroom) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
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

    def copy(self) -> "World":
        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.fired = set(self.fired)
        w.facts = copy.deepcopy(self.facts)
        return w


@dataclass
class StoryParams:
    setting: str = "classroom"
    child: str = "Mina"
    child_gender: str = "girl"
    helper: str = "Theo"
    helper_gender: str = "boy"
    beacon: str = "lamp"
    rat: str = "rat"
    kindness: str = "gentle"
    sound_effect: str = "soft"
    seed: Optional[int] = None
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


SETTINGS = {"classroom": Classroom()}
BEACONS = {
    "lamp": Choice("lamp", "beacon lamp", "glow", {"beacon", "light"}),
    "flashlight": Choice("flashlight", "little beacon", "beam", {"beacon", "light"}),
}
RATS = {
    "rat": Choice("rat", "rat", "squeak", {"rat"}),
}
KINDNESSES = {
    "gentle": Choice("gentle", "kindness", "smile", {"kindness"}),
    "sharing": Choice("sharing", "kindness", "share", {"kindness"}),
}
SOUNDS = {
    "soft": Choice("soft", "sound effects", "swish", {"sound_effects"}),
    "silly": Choice("silly", "sound effects", "skitter", {"sound_effects"}),
}

GIRL_NAMES = ["Mina", "Nora", "Lily", "Ava", "Zoe"]
BOY_NAMES = ["Theo", "Ben", "Milo", "Kai", "Leo"]


def valid_combos() -> list[tuple[str, str, str, str]]:
    out = []
    for s in SETTINGS:
        for b in BEACONS:
            for r in RATS:
                for k in KINDNESSES:
                    out.append((s, b, r, k))
    return out


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Classroom rhyming storyworld.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--beacon", choices=BEACONS)
    ap.add_argument("--rat", choices=RATS)
    ap.add_argument("--kindness", choices=KINDNESSES)
    ap.add_argument("--sound-effect", dest="sound_effect", choices=SOUNDS)
    ap.add_argument("--child")
    ap.add_argument("--helper")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (getattr(args, "setting", None) is None or c[0] == getattr(args, "setting", None))
              and (getattr(args, "beacon", None) is None or c[1] == getattr(args, "beacon", None))
              and (getattr(args, "rat", None) is None or c[2] == getattr(args, "rat", None))
              and (getattr(args, "kindness", None) is None or c[3] == getattr(args, "kindness", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    setting, beacon, rat, kindness = rng.choice(list(combos))
    child = getattr(args, "child", None) or rng.choice(GIRL_NAMES + BOY_NAMES)
    helper = getattr(args, "helper", None) or rng.choice([n for n in GIRL_NAMES + BOY_NAMES if n != child])
    child_gender = "girl" if child in GIRL_NAMES else "boy"
    helper_gender = "girl" if helper in GIRL_NAMES else "boy"
    sound_effect = getattr(args, "sound_effect", None) or rng.choice(sorted(SOUNDS))
    return StoryParams(setting=setting, child=child, child_gender=child_gender,
                       helper=helper, helper_gender=helper_gender, beacon=beacon,
                       rat=rat, kindness=kindness, sound_effect=sound_effect)


def rhyme(a: str, b: str) -> str:
    return f"{a} and {b}"


def tell(params: StoryParams) -> World:
    setting = _safe_lookup(SETTINGS, params.setting)
    world = World(setting)
    child = world.add(Entity(id=params.child, kind="character", type=params.child_gender, role="child",
                             attrs={"dismay": 0.0}, meters={"calm": 0.0}, memes={"dismay": 0.0}))
    helper = world.add(Entity(id=params.helper, kind="character", type=params.helper_gender, role="helper",
                              attrs={"kindness": params.kindness}, meters={"calm": 0.0}, memes={"kindness": 0.0}))
    beacon = world.add(Entity(id="beacon", type="thing", label=_safe_lookup(BEACONS, params.beacon).word,
                              tags=set(_safe_lookup(BEACONS, params.beacon).tags),
                              meters={"light": 1.0}, memes={"hope": 1.0}))
    rat = world.add(Entity(id="rat", type="thing", label="rat", tags={"rat"},
                           meters={"scurry": 0.0, "safety": 0.0}, memes={"startle": 0.0}))

    world.facts.update(child=child, helper=helper, beacon=beacon, rat=rat, params=params)

    world.say(f"In {setting.name}, {child.id} gave a yelp in dismay,")
    world.say(f"for a rat made tracks by the wall that day.")
    world.say(f"A beacon shone bright with a soft little gleam,")
    world.say(f"and sound effects danced like a swishy dream.")

    world.para()
    child.memes["dismay"] += 1
    rat.meters["scurry"] += 1
    rat.memes["startle"] += 1
    world.say(f"{child.id} went still, then whispered, \"Oh no, what a fright!\"")
    world.say(f"{helper.id} came close and kept voice low and light.")
    world.say(f"\"Let's show some kindness,\" {helper.id} said with care,")
    world.say(f"\"A calm little crumb trail can guide the rat there.\"")

    world.para()
    helper.memes["kindness"] += 1
    child.meters["calm"] += 1
    helper.meters["calm"] += 1
    rat.meters["safety"] += 1
    world.say(f"With soft sound effects, like a hush and a hum,")
    world.say(f"they set down a snack and stayed kind, not glum.")
    world.say(f"The beacon kept beaming, a brave little star,")
    world.say(f"and the rat skittered off to its nook near and far.")

    world.para()
    child.memes["dismay"] = 0.0
    child.meters["calm"] += 1
    world.say(f"Then {child.id} smiled wide as the classroom grew bright,")
    world.say(f"for kindness can tidy a scary old sight.")
    world.say(f"The beacon still glowed, and the room felt just right,")
    world.say(f"with a rat now at peace and no worry in sight.")
    return world


def generation_prompts(world: World) -> list[str]:
    p = world.facts["params"]
    return [
        f'Write a rhyming classroom story for a young child that includes the words "{p.rat}", "{p.beacon}", and "dismay".',
        f"Tell a gentle rhyme where {p.child} feels dismay when a rat appears in the classroom, and kindness helps calm the scene.",
        f'Write a classroom rhyme with sound effects and kindness that ends with a beacon shining and the rat leaving safely.',
    ]


def story_qa(world: World) -> list[QAItem]:
    p = world.facts["params"]
    c, h, r, b = world.facts["child"], world.facts["helper"], world.facts["rat"], world.facts["beacon"]
    return [
        QAItem(
            question=f"Why did {c.id} feel dismay in the classroom?",
            answer=f"{c.id} felt dismay because a rat came skittering out by the wall. The sudden sound effects made the moment feel extra startling.",
        ),
        QAItem(
            question=f"How did {h.id} help when the rat appeared?",
            answer=f"{h.id} showed kindness by keeping a calm voice and offering a snack trail. That gentle idea helped the rat move away without anyone yelling.",
        ),
        QAItem(
            question=f"What did the beacon do during the story?",
            answer=f"The beacon shone like a small star and stayed bright while everyone calmed down. Its steady light made the classroom feel safer.",
        ),
        QAItem(
            question=f"What changed by the end of the classroom story?",
            answer=f"By the end, {c.id}'s dismay was gone and the room felt peaceful again. The rat was safe in a nook, and kindness had turned the scare into a softer ending.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is kindness?",
            answer="Kindness is when someone is gentle, helpful, and careful with feelings. It can make a scary moment feel safer.",
        ),
        QAItem(
            question="What are sound effects in a story?",
            answer="Sound effects are words that help you hear a story in your mind, like squeak, swish, or tap. They can make a scene feel lively.",
        ),
        QAItem(
            question="What is a beacon?",
            answer="A beacon is a bright light that helps people notice where to look. It can shine like a tiny guide in a dark place.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("\n== Story QA ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("\n== World QA ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        lines.append(f"  {e.id}: meters={e.meters} memes={e.memes} attrs={e.attrs}")
    return "\n".join(lines)


ASP_RULES = r"""
valid(S,B,R,K) :- setting(S), beacon(B), rat(R), kindness(K).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for b in BEACONS:
        lines.append(asp.fact("beacon", b))
    for r in RATS:
        lines.append(asp.fact("rat", r))
    for k in KINDNESSES:
        lines.append(asp.fact("kindness", k))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    ok = True
    a = set(asp_valid_combos())
    p = set(valid_combos())
    if a != p:
        ok = False
        print("MISMATCH between ASP and Python valid combos")
        print("only ASP:", sorted(a - p))
        print("only Python:", sorted(p - a))
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(7)))
        assert sample.story
    except Exception as exc:
        ok = False
        print(f"SMOKE TEST FAILED: {exc}")
    if ok:
        print(f"OK: verify passed ({len(p)} combos).")
        return 0
    return 1


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        pass
    if params.beacon not in BEACONS or params.rat not in RATS or params.kindness not in KINDNESSES:
        pass
    world = tell(params)
    return StorySample(params=params, story=world.render(), prompts=generation_prompts(world),
                       story_qa=story_qa(world), world_qa=world_knowledge_qa(world), world=world)


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
    StoryParams(setting="classroom", child="Mina", child_gender="girl", helper="Theo", helper_gender="boy",
                beacon="lamp", rat="rat", kindness="gentle", sound_effect="soft", seed=1),
    StoryParams(setting="classroom", child="Leo", child_gender="boy", helper="Nora", helper_gender="girl",
                beacon="flashlight", rat="rat", kindness="sharing", sound_effect="silly", seed=2),
]


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/4."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        print(f"{len(asp_valid_combos())} combos")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
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
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
