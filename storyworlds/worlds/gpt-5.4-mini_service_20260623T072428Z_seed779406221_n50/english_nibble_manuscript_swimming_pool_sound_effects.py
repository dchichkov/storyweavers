#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260623T072428Z_seed779406221_n50/english_nibble_manuscript_swimming_pool_sound_effects.py
================================================================================================

A small standalone storyworld for a bedtime-story-like poolside mishap: a child
brings an english manuscript to a swimming pool, a nibble of snack tempts them
to lean too close, sound effects splash through the scene, and a careful grown-up
guides them toward a safe, repeatable routine.

Seed words: english, nibble, manuscript
Setting: swimming pool
Features: Sound Effects, Cautionary, Repetition
Style: Bedtime Story
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


THRESHOLD = 1.0



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
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    attrs: dict[str, str] = field(default_factory=dict)

    child: object | None = None
    manuscript: object | None = None
    parent: object | None = None
    treat: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)
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
        if not hasattr(self, "_tags"):
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
    place: str = "the swimming pool"
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


@dataclass
class Item:
    id: str
    label: str
    phrase: str
    vulnerable: str
    splash_zones: set[str]
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

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
class Treat:
    id: str
    label: str
    phrase: str
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

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
class Helper:
    id: str
    label: str
    phrase: str
    warning: str
    routine: str
    sound: str
    helper: object | None = None
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

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
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.weather = "bright"
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
        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        w.weather = self.weather
        w.facts = dict(self.facts)
        return w


def _sound(text: str) -> str:
    return text


def _r_wet(world: World) -> list[str]:
    out = []
    child = world.entities.get("child")
    manuscript = world.entities.get("manuscript")
    if not child or not manuscript:
        return out
    if child.meters.get("wet", 0) < THRESHOLD:
        return out
    sig = ("wet",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    manuscript.meters["wet"] = manuscript.meters.get("wet", 0) + 1
    manuscript.meters["wrinkled"] = manuscript.meters.get("wrinkled", 0) + 1
    out.append("The manuscript got wet and wrinkled.")
    return out


def _r_sad(world: World) -> list[str]:
    child = world.entities.get("child")
    if not child or child.meters.get("wet", 0) < THRESHOLD:
        return []
    sig = ("sad",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child.memes["worry"] = child.memes.get("worry", 0) + 1
    return []


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in (_r_wet, _r_sad):
            s = rule(world)
            if s:
                changed = True
                out.extend(s)
    if narrate:
        for s in out:
            world.say(s)
    return out


def predict_wetness(world: World) -> bool:
    sim = world.copy()
    child = sim.get("child")
    child.meters["wet"] = child.meters.get("wet", 0) + 1
    propagate(sim, narrate=False)
    return sim.get("manuscript").meters.get("wet", 0) >= THRESHOLD


def tell_intro(world: World, child: Entity, parent: Entity, manuscript: Entity, treat: Entity) -> None:
    world.say(f"On a soft afternoon, {child.id} sat beside {world.setting.place} with {manuscript.phrase}.")
    world.say(f"{child.pronoun().capitalize()} loved the english words on the pages and read them aloud again and again.")
    world.say(f"Near {child.pronoun('possessive')} lap, {treat.phrase} rested in a tiny bowl. Nibble, nibble, nibble, went the snack.")


def tell_warning(world: World, parent: Entity, child: Entity, manuscript: Entity) -> None:
    parent.memes["care"] = parent.memes.get("care", 0) + 1
    if predict_wetness(world):
        world.say(f'"Careful," {parent.id} said. "Keep {manuscript.label} away from the water, away from the splash, away from the edge."')
    else:
        world.say(f'"Careful," {parent.id} said, "and hold your pages with dry hands."')


def tell_splash(world: World, child: Entity) -> None:
    child.meters["wet"] = child.meters.get("wet", 0) + 1
    child.memes["surprise"] = child.memes.get("surprise", 0) + 1
    world.say(f"{child.id} leaned too close. Splash! Plip! The pool answered with a bright little sound.")
    propagate(world)


def tell_repetition(world: World, child: Entity, parent: Entity, manuscript: Entity) -> None:
    world.say(f'"No splash with the manuscript," {parent.id} said. "Dry hands, dry pages, dry feet."')
    world.say(f'{child.id} nodded. "Dry hands, dry pages, dry feet," {child.id} repeated.')
    world.say(f"Again and again, the rule stayed the same: no water on the english manuscript.")


def tell_resolution(world: World, child: Entity, parent: Entity, helper: Helper, manuscript: Entity, treat: Treat) -> None:
    child.memes["calm"] = child.memes.get("calm", 0) + 1
    world.say(f'{helper.label.capitalize()} came with a calm smile and said, "{helper.warning}"')
    world.say(f"Then came the good routine: {helper.routine}.")
    world.say(f"{helper.sound} went the little poolside table as the manuscript was moved to a dry basket.")
    world.say(f"{child.id} kept {treat.phrase} on a napkin, read one page, and breathed out slowly.")
    world.say(f"In the end, {manuscript.label} stayed safe, and the pool sparkled like a bedtime dream.")


def tell(setting: Setting, name: str = "Mia", gender: str = "girl", parent_type: str = "mother") -> World:
    world = World(setting)
    child = world.add(Entity(id=name, kind="character", type=gender, role="child"))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, role="parent"))
    manuscript = world.add(Entity(id="manuscript", type="manuscript", label="manuscript", phrase="an english manuscript"))
    treat = world.add(Entity(id="treat", type="treat", label="nibble", phrase="a nibble of crackers"))
    helper = Helper(
        id="helper",
        label="the lifeguard",
        phrase="the lifeguard",
        warning="Pool water and paper do not mix, little one.",
        routine="step back, dry your hands, and read from the bench",
        sound="thump-thump",
    )
    world.facts.update(child=child, parent=parent, manuscript=manuscript, treat=treat, helper=helper)

    tell_intro(world, child, parent, manuscript, treat)
    world.para()
    tell_warning(world, parent, child, manuscript)
    tell_splash(world, child)
    world.para()
    tell_repetition(world, child, parent, manuscript)
    world.para()
    tell_resolution(world, child, parent, helper, manuscript, treat)
    world.facts["manuscript_wet"] = manuscript.meters.get("wet", 0) >= THRESHOLD
    return world


SETTINGS = {
    "pool": Setting(place="the swimming pool"),
}

NAMES = ["Mia", "Leo", "Nora", "Ben", "Lily", "Sam"]
GENDERS = ["girl", "boy"]
PARENTS = ["mother", "father"]


@dataclass
class StoryParams:
    place: str
    name: str
    gender: str
    parent: str
    seed: Optional[int] = None
    samples: list = field(default_factory=list)
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

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
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


def valid_combos() -> list[tuple[str]]:
    return [("pool",)]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Bedtime pool story with sound effects, caution, and repetition.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=GENDERS)
    ap.add_argument("--parent", choices=PARENTS)
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
    place = getattr(args, "place", None) or "pool"
    gender = getattr(args, "gender", None) or rng.choice(GENDERS)
    name = getattr(args, "name", None) or rng.choice(NAMES)
    parent = getattr(args, "parent", None) or rng.choice(PARENTS)
    return StoryParams(place=place, name=name, gender=gender, parent=parent)


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.place), params.name, params.gender, params.parent)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    c = world.facts["child"]
    return [
        f'Write a bedtime story for a small child where {c.id} sits by a swimming pool with an english manuscript and a nibble of snacks.',
        "Tell a gentle cautionary story with repeated words, soft sound effects, and a safe ending by the pool.",
        'Write a simple bedtime story that repeats "dry hands, dry pages, dry feet" and ends with the manuscript staying safe.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    c, p, m, t = f["child"], f["parent"], f["manuscript"], f["treat"]
    qa = [
        QAItem(
            question=f"What was {c.id} holding beside the swimming pool?",
            answer=f"{c.id} was holding an english manuscript and a nibble of crackers by the pool.",
        ),
        QAItem(
            question=f"Why did {p.id} warn {c.id} to be careful?",
            answer=f"{p.id} warned {c.id} because pool water could splash onto the manuscript and ruin the dry pages.",
        ),
        QAItem(
            question=f"What sound did the pool make when {c.id} leaned too close?",
            answer=f"The pool said splash and plip, and the sound reminded everyone to stay careful.",
        ),
        QAItem(
            question=f"How did the story end for the manuscript?",
            answer="The manuscript stayed safe in a dry basket, and the child kept reading beside the pool.",
        ),
    ]
    if f["manuscript_wet"]:
        qa.append(QAItem(
            question=f"What happened to the manuscript after the splash?",
            answer="It got wet and wrinkled, which is why the child had to move it to a dry place.",
        ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="Why should paper stay away from pool water?",
            answer="Paper can get soggy and ruined when it gets wet, so it is better to keep it dry near water.",
        ),
        QAItem(
            question="What does nibble mean?",
            answer="A nibble is a tiny bite of food, just enough to taste a little snack.",
        ),
        QAItem(
            question="What is a manuscript?",
            answer="A manuscript is a piece of writing, often a story or book text before it is printed.",
        ),
        QAItem(
            question="What is a swimming pool for?",
            answer="A swimming pool is for safe swimming and splashing, with grown-up rules to help everyone stay safe.",
        ),
    ]


ASP_RULES = r"""
pool(P) :- setting(P).
paper(M) :- manuscript(M).
food(T) :- treat(T).
risk(M) :- paper(M), wet(M).
wet(M) :- splash(_, M).
safe_end :- not wet(manuscript).
"""

def asp_facts() -> str:
    import asp
    return "\n".join([
        asp.fact("setting", "pool"),
        asp.fact("manuscript", "manuscript"),
        asp.fact("treat", "treat"),
        asp.fact("splash", "child", "manuscript"),
    ])


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    try:
        import asp
    except Exception:
        print("ASP unavailable")
        return 1
    model = asp.one_model(asp_program("#show safe_end/0."))
    return 0 if asp.atoms(model, "safe_end") else 1


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story QA ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== World QA ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
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
        lines.append(f"  {e.id:10} ({e.type:9}) {' '.join(bits)}")
    return "\n".join(lines)


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program("#show safe_end/0."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        print(asp_program("#show safe_end/0."))
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(StoryParams(place="pool", name=n, gender=g, parent=p)) for n, g, p in [("Mia", "girl", "mother")]]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(getattr(args, "n", None) * 20, 20):
            i += 1
            params = resolve_params(args, random.Random(base_seed + i))
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
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=f"### variant {i+1}" if len(samples) > 1 else "")
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
