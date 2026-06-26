#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T055019Z_seed926384711_n100/playdoh_transformation_inner_monologue_bad_ending_detective.py
================================================================================================

A small detective-style storyworld about a child detective, a lump of playdoh,
an unsettling transformation, and a bad ending that is still fully told.

Seed tale sketch:
---
A young detective notices that a bowl of playdoh has changed overnight. It is
no longer soft and silly. It has dried, cracked, and become a strange little
clue-shaped lump. The detective thinks hard, follows the clues, and realizes too
late what happened. The playdoh cannot be saved, and the mystery ends badly.
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
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    plural: bool = False
    transformed: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    hero: object | None = None
    parent: object | None = None
    playdoh: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
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
    detail: str
    warm: bool = False
    affords: set[str] = field(default_factory=set)
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
    clue: str
    transform_into: str
    bad_end: str
    keyword: str = "playdoh"
    tags: set[str] = field(default_factory=set)
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

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        return None


@dataclass
class StoryParams:
    setting: str
    case: str
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None
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
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
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
        import copy
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


SETTINGS = {
    "classroom": Setting(
        place="the classroom",
        detail="A bright window sat over a low table, and crayons waited in a cup.",
        warm=True,
        affords={"investigate"},
    ),
    "artroom": Setting(
        place="the art room",
        detail="Shelves of paper and glue lined the walls, and one sunny sill ran warm.",
        warm=True,
        affords={"investigate"},
    ),
    "bedroom": Setting(
        place="the bedroom",
        detail="A small desk stood beside a sunny window, where the afternoon light could reach.",
        warm=True,
        affords={"investigate"},
    ),
}

CASES = {
    "suncrack": Case(
        mystery="the playdoh had turned hard and cracked",
        clue="warm sunlight on the windowsill",
        transform_into="a brittle little key-shaped lump",
        bad_end="the soft playdoh was ruined",
        tags={"playdoh", "sun", "crack", "key"},
    ),
    "stalejar": Case(
        mystery="the playdoh smelled old and dry",
        clue="the jar had been left open all afternoon",
        transform_into="a rough little pebble",
        bad_end="the playdoh could not be shaped anymore",
        tags={"playdoh", "dry", "jar"},
    ),
}

GIRL_NAMES = ["Mia", "Nina", "Luna", "Ivy", "Ada", "June", "Lila"]
BOY_NAMES = ["Finn", "Eli", "Noah", "Theo", "Max", "Ben", "Kai"]
TRAITS = ["curious", "quiet", "careful", "sharp-eyed", "brave", "patient"]


def valid_combos() -> list[tuple[str, str]]:
    return [(s, c) for s in SETTINGS for c in CASES]


def explain_rejection(setting: str, case: str) -> str:
    return f"(No story: {setting!r} and {case!r} do not form a valid detective mystery.)"


def explain_gender(gender: str) -> str:
    return f"(No story: unsupported gender {gender!r}.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A detective storyworld about playdoh transformation and a bad ending."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--case", choices=CASES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--parent", choices=["mother", "father"])
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
    if getattr(args, "gender", None) and getattr(args, "gender", None) not in {"girl", "boy"}:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    combos = [c for c in valid_combos()
              if (getattr(args, "setting", None) is None or c[0] == getattr(args, "setting", None))
              and (getattr(args, "case", None) is None or c[1] == getattr(args, "case", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    setting, case = rng.choice(list(combos))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = getattr(args, "parent", None) or rng.choice(["mother", "father"])
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(setting=setting, case=case, name=name, gender=gender, parent=parent, trait=trait)


def introduce(world: World, hero: Entity) -> None:
    world.say(
        f"{hero.id} was a {hero.memes['trait_word']} {hero.type} detective who noticed small things."
    )


def setup(world: World, hero: Entity, parent: Entity, case: Case) -> None:
    world.say(
        f"At {world.setting.place}, {hero.id} sat with a notebook and stared at a bowl of playdoh."
    )
    world.say(f"{hero.pronoun().capitalize()} liked the squishy dough because it could become almost anything.")
    world.say(
        f"That morning, {hero.id} found that {case.mystery}, which made {hero.pronoun('object')} frown."
    )
    world.say(f"{hero.pronoun('possessive').capitalize()} {parent.type} said, \"Please solve it before dinner.\"")


def inner_monologue(world: World, hero: Entity, case: Case) -> None:
    hero.memes["worry"] += 1
    world.say(
        f"{hero.id} looked at the bowl and thought, "
        f"Maybe the answer is hiding in the light, or maybe someone touched the dough when I was away."
    )
    world.say(
        f"{hero.pronoun().capitalize()} tapped the notebook and told {hero.pronoun('object')}, "
        f"Look for the clue, not the loudest story."
    )


def transform(world: World, playdoh: Entity, case: Case) -> None:
    playdoh.transformed = True
    playdoh.meters["hard"] += 1
    playdoh.meters["cracked"] += 1
    playdoh.label = case.transform_into
    playdoh.phrase = case.transform_into
    world.facts["transformed"] = True
    world.say(
        f"Under the window, the playdoh had changed into {case.transform_into}."
    )
    world.say(
        f"The little shape looked like a clue, but it also looked too hard to fix."
    )


def investigate(world: World, hero: Entity, parent: Entity, case: Case, playdoh: Entity) -> None:
    hero.memes["focus"] += 1
    world.say(
        f"{hero.id} walked the room like a tiny detective, checking the sill, the table, and the open air by the window."
    )
    world.say(
        f"In {hero.pronoun('possessive')} head, the thought clicked: warm sunlight had sat on the dough too long."
    )
    world.say(
        f"{hero.id} realized the answer, but the answer arrived late."
    )
    world.facts["clue_found"] = case.clue
    world.facts["too_late"] = True


def bad_ending(world: World, hero: Entity, parent: Entity, case: Case, playdoh: Entity) -> None:
    hero.memes["sadness"] += 1
    playdoh.meters["saved"] = 0
    world.say(
        f"By the time {hero.id} reached for it, the soft playdoh was already ruined."
    )
    world.say(
        f"{hero.id} sighed and wrote the last line in the notebook: {case.bad_end}."
    )
    world.say(
        f"{hero.pronoun('possessive').capitalize()} {parent.type} gave {hero.id} a hug and said the mystery could be remembered, even if the dough could not be fixed."
    )
    world.say(
        f"The detective closed the notebook, and the cracked little lump stayed on the desk like a sad final clue."
    )
    world.facts["bad_end"] = True


def tell(setting: Setting, case: Case, hero_name: str, hero_type: str, parent_type: str, trait: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type))
    hero.memes["trait_word"] = trait
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type))
    playdoh = world.add(Entity(id="playdoh", type="playdoh", label="playdoh", phrase="soft playdoh", owner=hero.id))

    world.facts.update(hero=hero, parent=parent, playdoh=playdoh, case=case, setting=setting)

    introduce(world, hero)
    world.para()
    setup(world, hero, parent, case)
    inner_monologue(world, hero, case)
    transform(world, playdoh, case)
    world.para()
    investigate(world, hero, parent, case, playdoh)
    bad_ending(world, hero, parent, case, playdoh)
    return world


def story_prompts(world: World) -> list[str]:
    f = world.facts
    hero, case = f["hero"], f["case"]
    return [
        'Write a short detective story for a young child about playdoh changing shape.',
        f"Tell a small mystery story where {hero.id}, a {hero.memes['trait_word']} detective, notices playdoh and thinks through the clue.",
        f"Write a gentle detective tale that includes the word \"playdoh\" and ends with a bad ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, parent, case = f["hero"], f["parent"], f["case"]
    return [
        QAItem(
            question=f"Who is the detective in the story?",
            answer=f"The detective is {hero.id}, a {hero.memes['trait_word']} {hero.type} who watches clues closely.",
        ),
        QAItem(
            question=f"What happened to the playdoh?",
            answer=f"The playdoh changed into {case.transform_into}, so it was no longer soft.",
        ),
        QAItem(
            question=f"Why did {hero.id} think the mystery was happening?",
            answer=f"{hero.id} thought warm sunlight or too much air had changed the playdoh, because the clue was {case.clue}.",
        ),
        QAItem(
            question=f"Did the story end happily?",
            answer=f"No. The story ended badly because {case.bad_end}, and the playdoh could not be saved.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is playdoh?",
            answer="Playdoh is a soft modeling dough that children can squish, roll, and shape into different things.",
        ),
        QAItem(
            question="What happens when playdoh gets too dry?",
            answer="When playdoh gets too dry, it can harden and crack, and it becomes hard to shape.",
        ),
        QAItem(
            question="What does a detective do?",
            answer="A detective looks for clues, thinks carefully, and tries to solve a mystery.",
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
    lines.append("== (3) World-knowledge questions ==")
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
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
valid_setting(S) :- setting(S).
valid_case(C) :- case(C).
valid_story(S, C) :- valid_setting(S), valid_case(C).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for c in CASES:
        lines.append(asp.fact("case", c))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    import asp
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


def generate(params: StoryParams) -> StorySample:
    setting = _safe_lookup(SETTINGS, params.setting)
    case = _safe_lookup(CASES, params.case)
    hero_type = params.gender
    world = tell(setting, case, params.name, hero_type, params.parent, params.trait)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=story_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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
    StoryParams(setting="classroom", case="suncrack", name="June", gender="girl", parent="mother", trait="curious"),
    StoryParams(setting="artroom", case="suncrack", name="Finn", gender="boy", parent="father", trait="sharp-eyed"),
    StoryParams(setting="bedroom", case="stalejar", name="Ivy", gender="girl", parent="mother", trait="patient"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible setting/case combos:\n")
        for s, c in combos:
            print(f"  {s:10} {c}")
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
            header = f"### {p.name}: {p.case} in {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
