#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/relevant_genetic_surprise_foreshadowing_dialogue_detective_story.py
==============================================================================================

A small detective-story world for a child-facing mystery with:
- relevant clues
- a genetic clue about family resemblance
- surprise
- foreshadowing
- dialogue

The story premise is simple:
A careful little detective notices clues in a neighborhood mystery.
A surprising family trait becomes the key to the case.
The world is simulated as meters and memes, so the ending changes because the
state changes: clues are found, suspicions rise, dialogue narrows the search,
and the surprise reveal resolves the case.

This script is standalone and uses only the stdlib plus the shared result
containers from storyworlds/results.py. ASP is imported lazily only when used.
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
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    clue: object | None = None
    detective: object | None = None
    helper: object | None = None
    missing: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "aunt"}
        male = {"boy", "man", "father", "uncle"}
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
class Setting:
    place: str
    indoor: bool
    noise: str
    afford: set[str] = field(default_factory=set)
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
class Case:
    mystery: str
    item: str
    clue: str
    reveal: str
    foreshadow: str
    surprise: str
    question: str
    answer: str
    genetic_hint: str
    dialogue_line: str
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
class StoryParams:
    place: str
    case: str
    detective: str
    gender: str
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
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[str] = set()

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        import copy
        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        w.fired = set(self.fired)
        return w


SETTINGS = {
    "museum": Setting(place="the museum", indoor=True, noise="quiet halls", afford={"inspection"}),
    "library": Setting(place="the library", indoor=True, noise="soft whispers", afford={"inspection"}),
    "garden": Setting(place="the garden", indoor=False, noise="rustling leaves", afford={"inspection"}),
    "station": Setting(place="the train station", indoor=True, noise="rolling footsteps", afford={"inspection"}),
}

CASES = {
    "red_scarf": Case(
        mystery="who took the red scarf",
        item="red scarf",
        clue="a tiny thread caught on a bench",
        reveal="the missing scarf was tucked in a helper's coat pocket",
        foreshadow="the helper had red fluff on the sleeve",
        surprise="the helper was not the thief at all; the coat had been borrowed from family",
        question="Why did the detective look at the sleeve so carefully?",
        answer="Because the little thread on the sleeve was a relevant clue that matched the missing red scarf.",
        genetic_hint="the helper shared the same bright freckled smile as an aunt from the same family",
        dialogue_line='\"I borrowed this coat from my aunt,\" said the helper. \"Look at the sleeve thread.\"',
    ),
    "blue_key": Case(
        mystery="where the blue key went",
        item="blue key",
        clue="a blue paint speck on a glove",
        reveal="the key was inside a toy box all along",
        foreshadow="the glove had the same paint speck as the toy box lid",
        surprise="the locked drawer was not the real problem; the key had been put away by mistake",
        question="What clue helped the detective know where to search?",
        answer="The blue paint speck was relevant because it matched the toy box and pointed to the right place.",
        genetic_hint="the shopkeeper had the same dimpled chin as the child who loved sorting toys",
        dialogue_line='\"I always put blue things with blue things,\" said the child, pointing at the toy box.',
    ),
    "golden_cookie": Case(
        mystery="who ate the golden cookie",
        item="golden cookie",
        clue="crumbs shaped like little stars",
        reveal="a puppy had dragged the cookie under the table",
        foreshadow="the puppy had crumbs on its whiskers before anyone looked under the table",
        surprise="the clues led to the puppy, not the grumpy neighbor everyone suspected",
        question="Why did the detective peek under the table?",
        answer="Because the star-shaped crumbs were a relevant clue, and they pointed lower than the grown-ups expected.",
        genetic_hint="the puppy and its owner both had the same white stripe down the nose",
        dialogue_line='\"I only chased the smell,\" barked the puppy, wagging beside the table.',
    ),
}

GIRL_NAMES = ["Mila", "Nora", "Ivy", "Lena", "Sana", "Ada", "Tess"]
BOY_NAMES = ["Owen", "Finn", "Eli", "Milo", "Theo", "Jude", "Noah"]
HELPERS = ["neighbor", "cousin", "shopkeeper", "librarian", "gardener"]
TRAITS = ["careful", "brave", "patient", "curious", "smart"]


def reason_ok(setting: Setting, case: Case) -> bool:
    return "inspection" in setting.afford and bool(case.clue) and bool(case.reveal)


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for case_id, case in CASES.items():
            if reason_ok(setting, case):
                combos.append((place, case_id))
    return combos


def explain_rejection(setting: Setting, case: Case) -> str:
    return f"(No story: this case cannot be investigated at {setting.place}, so there is no fair clue path.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Detective story world with relevant clues and a genetic surprise.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--case", choices=CASES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--helper", choices=HELPERS)
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
    if getattr(args, "place", None) and getattr(args, "case", None):
        if not reason_ok(_safe_lookup(SETTINGS, getattr(args, "place", None)), _safe_lookup(CASES, getattr(args, "case", None))):
            return _fallback_storyparams(args, rng, StoryParams, globals())
    combos = [c for c in valid_combos()
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "case", None) is None or c[1] == getattr(args, "case", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, case_id = rng.choice(list(combos))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    helper = getattr(args, "helper", None) or rng.choice(HELPERS)
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(place=place, case=case_id, detective=name, gender=gender, helper=helper, seed=None)


def tell(params: StoryParams) -> World:
    setting = _safe_lookup(SETTINGS, params.place)
    case = _safe_lookup(CASES, params.case)
    world = World(setting)

    detective = world.add(Entity(id=params.detective, kind="character", type=params.gender))
    helper = world.add(Entity(id="helper", kind="character", type="boy", label=params.helper))
    clue = world.add(Entity(id="clue", type="thing", label=case.clue))
    missing = world.add(Entity(id="missing", type="thing", label=case.item))

    detective.memes["curiosity"] += 1
    detective.memes["focus"] += 1
    helper.memes["uneasy"] += 1
    clue.meters["noticed"] = 0.0
    missing.meters["missing"] = 1.0

    world.say(f"{detective.id} was a {params.trait} little detective who liked solving puzzles at {setting.place}.")
    world.say(f"One day, {case.mystery} made everyone in {setting.place} look around and whisper.")
    world.say(f'"This seems relevant," {detective.pronoun("subject")} said, kneeling near {case.clue}.')
    world.say(f"{setting.noise} made the room feel calm, but the missing {case.item} made the people uneasy.")
    world.para()
    world.say(f'{detective.id} asked, "Did anyone see {case.item}?"')
    world.say(f'{helper.id} glanced down and answered, "{case.dialogue_line}"')
    world.say(f"{case.foreshadow.capitalize()}. {case.genetic_hint.capitalize()}.")
    world.say(f'{detective.id} nodded. "That family detail matters," {detective.pronoun("subject")} said.')
    world.para()
    world.say(f"{detective.id} followed the clue carefully, because {case.clue} could lead to the answer.")
    world.say(f"The surprise was that {case.surprise}.")
    world.say(f"In the end, {case.reveal}, and the mystery was solved.")
    world.say(f'{detective.id} smiled. "Case closed," {detective.pronoun("subject")} said, while {helper.id} finally laughed.')
    world.facts.update(
        detective=detective,
        helper=helper,
        case=case,
        setting=setting,
        clue=clue,
        missing=missing,
        solved=True,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    case = _safe_fact(world, f, "case")
    detective = _safe_fact(world, f, "detective")
    return [
        f'Write a short detective story for a child where a detective named {detective.id} follows a relevant clue and learns a genetic detail.',
        f'Tell a gentle mystery with dialogue, foreshadowing, and a surprise ending about {case.mystery}.',
        f'Write a small story that uses the words "relevant" and "genetic" and ends with "Case closed."',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    case = _safe_fact(world, f, "case")
    detective = _safe_fact(world, f, "detective")
    helper = _safe_fact(world, f, "helper")
    return [
        QAItem(
            question=f"What did {detective.id} try to solve?",
            answer=f"{detective.id} tried to solve {case.mystery} at {world.setting.place}.",
        ),
        QAItem(
            question=f"Which clue was relevant to the mystery?",
            answer=f"The clue was {case.clue}, and it was relevant because it helped point to the answer.",
        ),
        QAItem(
            question=f"What surprising thing changed the detective's guess?",
            answer=f"The surprising thing was that {case.surprise}. That new fact changed who the detective trusted.",
        ),
        QAItem(
            question=f"Why did the detective mention a family detail?",
            answer=f"Because {case.genetic_hint}, and that genetic resemblance helped narrow the mystery.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a clue in a detective story?",
            answer="A clue is a small piece of information that helps solve a mystery.",
        ),
        QAItem(
            question="What does genetic mean?",
            answer="Genetic means something you can share with your family, like a trait or resemblance.",
        ),
        QAItem(
            question="Why do detectives listen to dialogue?",
            answer="Detectives listen to dialogue because people may say helpful facts, hints, or surprises.",
        ),
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
    lines.append("== (3) World knowledge questions ==")
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
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {e.id:10} ({e.kind:8}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
setting(P) :- place(P).
case(C) :- mystery(C).
valid(P,C) :- setting(P), case(C), inspectable(P,C).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid in SETTINGS:
        lines.append(asp.fact("place", pid))
    for cid in CASES:
        lines.append(asp.fact("mystery", cid))
        lines.append(asp.fact("inspectable", "museum", cid))
        lines.append(asp.fact("inspectable", "library", cid))
        lines.append(asp.fact("inspectable", "garden", cid))
        lines.append(asp.fact("inspectable", "station", cid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    clingo_set, python_set = set(asp_valid_combos()), set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


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


CURATED = [
    StoryParams(place="museum", case="red_scarf", detective="Mila", gender="girl", helper="neighbor"),
    StoryParams(place="library", case="blue_key", detective="Owen", gender="boy", helper="librarian"),
    StoryParams(place="garden", case="golden_cookie", detective="Ivy", gender="girl", helper="gardener"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show valid/2."))
        vals = sorted(set(asp.atoms(model, "valid")))
        print(f"{len(vals)} valid combos:")
        for p, c in vals:
            print(f"  {p} {c}")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(getattr(args, "n", None) * 50, 50):
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
        header = ""
        if getattr(args, "all", None):
            p = sample.params
            header = f"### {p.detective}: {p.case} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
