#!/usr/bin/env python3
"""
storyworlds/worlds/lavender_reed_enchant_teamwork_dialogue_slice_of.py
======================================================================

A small slice-of-life storyworld about a gentle shared task with lavender,
reed, and a little bit of enchantment.

Seed tale sketch:
---
A child and a grown-up are tidying a small table in a sunny room. They sort
lavender sprigs, trim reed stems, and wrap a simple gift. The child wants the
little bundle to feel magical. The grown-up says that a kind voice and steady
hands can make ordinary things feel enchanted. They work together, talk it
through, and finish the bundle just in time.

World shape:
---
- Physical meters: freshness, tidiness, neatness, sparkle, warmth, fatigue.
- Emotional memes: delight, worry, patience, pride, calm, closeness.

Narrative instruments:
---
- Teamwork: two people divide the work, compare notes, and help each other.
- Dialogue: the story advances through short, grounded spoken lines.
- Slice of life: no grand adventure, just a warm, small, complete moment.

The story is intentionally modest and grounded: the turn is a practical snag,
and the ending proves that the shared method changed the world state.
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
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    adult: object | None = None
    bundle: object | None = None
    child: object | None = None
    lavender: object | None = None
    reed: object | None = None
    def __post_init__(self) -> None:
        for k in ["freshness", "tidiness", "neatness", "sparkle", "warmth", "fatigue"]:
            self.meters.setdefault(k, 0.0)
        for k in ["delight", "worry", "patience", "pride", "calm", "closeness"]:
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "grandmother", "grandma"}
        male = {"boy", "father", "dad", "man", "grandfather", "grandpa"}
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
    place: str = "the sunroom"
    indoors: bool = True
    affordances: set[str] = field(default_factory=set)
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
class Task:
    id: str
    verb: str
    gerund: str
    snag: str
    repair: str
    item: str
    keyword: str
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
class Tool:
    id: str
    label: str
    purpose: str
    helps: set[str]
    avoids: set[str]
    plural: bool = False
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


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


def normalize(name: str) -> str:
    return name.strip().lower().replace(" ", "_")


def dialogue(a: Entity, b: Entity, line_a: str, line_b: str) -> str:
    return f'"{line_a}" {a.id} said. "{line_b}" {b.id} replied.'


def story_detail(setting: Setting) -> str:
    if setting.indoors:
        return "The room was bright and still, with afternoon light on the table."
    return f"{setting.place.capitalize()} felt quiet, with a soft breeze moving through the air."


def predict_snag(world: World, task: Task, item: Entity) -> bool:
    sim = world_copy(world)
    perform_task(sim, sim.get("Child"), task, narrate=False)
    return sim.get(item.id).meters["tidiness"] < THRESHOLD


def world_copy(world: World) -> World:
    import copy
    clone = World(world.setting)
    clone.entities = copy.deepcopy(world.entities)
    clone.fired = set(world.fired)
    clone.paragraphs = [[]]
    clone.facts = dict(world.facts)
    return clone


def perform_task(world: World, actor: Entity, task: Task, narrate: bool = True) -> None:
    if task.id not in world.setting.affordances:
        pass
    actor.meters["fatigue"] += 1
    actor.memes["patience"] += 0.5
    if task.id == "bundle":
        for ent in list(world.entities.values()):
            if ent.type in {"lavender", "reed"}:
                ent.meters["tidiness"] += 0.5
                ent.meters["freshness"] += 0.5
        world.get("Bundle").meters["neatness"] += 1
        world.get("Bundle").meters["sparkle"] += 1
    elif task.id == "trim":
        world.get("Reed").meters["tidiness"] += 1
        world.get("Reed").meters["freshness"] += 0.5
    elif task.id == "arrange":
        world.get("Lavender").meters["freshness"] += 1
        world.get("Lavender").meters["sparkle"] += 1
    if narrate:
        world.say(f"They kept going with {task.gerund}.")


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for task_id in setting.affordances:
            task = _safe_lookup(TASKS, task_id)
            for item_id, item in ITEMS.items():
                if task.id == "bundle" and item_id in {"Lavender", "Reed"}:
                    combos.append((place, task_id, item_id))
                elif task.id in {"trim", "arrange"} and item_id == "Lavender":
                    combos.append((place, task_id, item_id))
    return combos


def generate_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short slice-of-life story for a child that includes the words "{f["task"].keyword}", "{f["item"].label}", and "teamwork".',
        f"Tell a gentle story where {f['child'].id} and {f['adult'].id} work together to {f['task'].verb} without losing the calm feeling in {f['setting'].place}.",
        f'Write a simple dialogue-filled story about lavender and reed being prepared by two people side by side.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child: Entity = _safe_fact(world, f, "child")
    adult: Entity = _safe_fact(world, f, "adult")
    task: Task = _safe_fact(world, f, "task")
    item: Entity = _safe_fact(world, f, "item")
    setting: Setting = _safe_fact(world, f, "setting")
    return [
        QAItem(
            question=f"What were {child.id} and {adult.id} doing in {setting.place}?",
            answer=(
                f"They were working together to {task.verb}. "
                f"Their teamwork made the small job feel steady and kind."
            ),
        ),
        QAItem(
            question=f"Why did {child.id} want help with the {item.label}?",
            answer=(
                f"{child.id} wanted the {item.label} to look neat and a little magical, "
                f"but doing it alone felt too hard. Working together made it easier."
            ),
        ),
        QAItem(
            question=f"What changed after they talked and kept going?",
            answer=(
                f"The {item.label} became neat and ready, and both of them felt proud. "
                f"By the end, the ordinary table had turned into something that felt gently enchanted."
            ),
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is lavender?",
            answer="Lavender is a fragrant purple plant often used in bundles, tea, or little decorations.",
        ),
        QAItem(
            question="What is reed?",
            answer="A reed is a thin, straight plant stem that can be trimmed, woven, or tied into simple shapes.",
        ),
        QAItem(
            question="What does enchant mean?",
            answer="To enchant something is to make it feel magical, charming, or special.",
        ),
        QAItem(
            question="What is teamwork?",
            answer="Teamwork means people help each other and share the work so a task gets done together.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: round(v, 2) for k, v in e.meters.items() if v}
        memes = {k: round(v, 2) for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:8} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


def build_world(params: "StoryParams") -> World:
    setting = _safe_lookup(SETTINGS, params.place)
    world = World(setting)
    child = world.add(Entity(id=params.child_name, kind="character", type=params.child_type))
    adult = world.add(Entity(id=params.adult_name, kind="character", type=params.adult_type))
    lavender = world.add(Entity(id="Lavender", type="lavender", label="lavender", phrase="a small bunch of lavender", owner=child.id))
    reed = world.add(Entity(id="Reed", type="reed", label="reed", phrase="a few reed stems", owner=adult.id))
    bundle = world.add(Entity(id="Bundle", type="bundle", label="bundle", phrase="a little bundle of lavender and reed"))
    child.memes["delight"] += 1
    adult.memes["calm"] += 1
    world.say(f"{child.id} and {adult.id} were in {setting.place}.")
    world.say(story_detail(setting))
    world.say(f"{child.id} touched the lavender and smiled. {adult.id} set the reed stems beside the ribbon.")
    world.para()
    world.say(dialogue(child, adult, f"Can we make it feel a little enchanted?", f"We can, if we work together."))
    world.say(f"{child.id} wanted the table to look tidy, and the lavender to stay bright.")
    world.say(f"{adult.id} nodded and lifted the reed stems into a neat stack.")
    if predict_snag(world, TASKS["bundle"], bundle):
        world.say(dialogue(adult, child, "It looks like the bundle needs two sets of hands.", "I can hold the ribbon while you tie it."))
    world.para()
    perform_task(world, child, TASKS["arrange"])
    world.say(f"{child.id} arranged the lavender in a small fan.")
    perform_task(world, adult, TASKS["trim"])
    world.say(f"{adult.id} trimmed the reed so the ends would sit even.")
    world.say(dialogue(child, adult, "That looks better already.", "It does. Now let's finish it together."))
    perform_task(world, child, TASKS["bundle"])
    child.memes["pride"] += 1
    adult.memes["closeness"] += 1
    world.say(f"At last, they tied the ribbon around the bundle.")
    world.say(f"The lavender smelled sweet, the reed stood straight, and the little gift looked gently enchanted.")
    world.facts.update(child=child, adult=adult, task=_safe_lookup(TASKS, params.task), item=world.get("Bundle"), setting=setting)
    return world


@dataclass
class StoryParams:
    place: str
    task: str
    child_name: str
    child_type: str
    adult_name: str
    adult_type: str
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


SETTINGS = {
    "sunroom": Setting(place="the sunroom", indoors=True, affordances={"arrange", "trim", "bundle"}),
    "kitchen_table": Setting(place="the kitchen table", indoors=True, affordances={"arrange", "trim", "bundle"}),
    "porch": Setting(place="the porch", indoors=False, affordances={"arrange", "trim", "bundle"}),
}

TASKS = {
    "arrange": Task(
        id="arrange",
        verb="arrange the lavender",
        gerund="arranging the lavender",
        snag="the stems are uneven",
        repair="make the lavender look tidy",
        item="lavender",
        keyword="lavender",
        tags={"lavender", "scent"},
    ),
    "trim": Task(
        id="trim",
        verb="trim the reed",
        gerund="trimming the reed",
        snag="the reed ends are rough",
        repair="make the reed sit evenly",
        item="reed",
        keyword="reed",
        tags={"reed", "plants"},
    ),
    "bundle": Task(
        id="bundle",
        verb="bundle the lavender and reed",
        gerund="bundling lavender and reed",
        snag="the ribbon is hard to hold",
        repair="tie everything into one neat gift",
        item="bundle",
        keyword="enchant",
        tags={"lavender", "reed", "enchant"},
    ),
}

ITEMS = {
    "Lavender": Entity(id="Lavender", type="lavender", label="lavender"),
    "Reed": Entity(id="Reed", type="reed", label="reed"),
    "Bundle": Entity(id="Bundle", type="bundle", label="bundle"),
}

GIRL_NAMES = ["Mina", "June", "Lila", "Nora", "Ivy", "Ada"]
BOY_NAMES = ["Theo", "Ezra", "Finn", "Owen", "Miles", "Leo"]
ADULT_NAMES = ["Mom", "Dad", "Aunt Rae", "Uncle Ben", "Grandma", "Grandpa"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Slice-of-life storyworld with lavender, reed, enchant, teamwork, and dialogue.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--task", choices=TASKS)
    ap.add_argument("--name")
    ap.add_argument("--adult-name")
    ap.add_argument("--child-type", choices=["girl", "boy"], default=None)
    ap.add_argument("--adult-type", choices=["mother", "father", "woman", "man", "grandmother", "grandfather"], default=None)
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
    place = getattr(args, "place", None) or rng.choice(list(SETTINGS))
    task = getattr(args, "task", None) or rng.choice(list(TASKS))
    child_type = getattr(args, "child_type", None) or rng.choice(["girl", "boy"])
    adult_type = getattr(args, "adult_type", None) or rng.choice(["mother", "father", "grandmother", "grandfather"])
    child_name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if child_type == "girl" else BOY_NAMES)
    adult_name = getattr(args, "adult_name", None) or rng.choice(ADULT_NAMES)
    if child_name == adult_name:
        adult_name = adult_name + " "
    return StoryParams(place=place, task=task, child_name=child_name, child_type=child_type, adult_name=adult_name, adult_type=adult_type)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generate_prompts(world),
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


ASP_RULES = r"""
place(sunroom). place(kitchen_table). place(porch).
task(arrange). task(trim). task(bundle).
supports(sunroom, arrange). supports(sunroom, trim). supports(sunroom, bundle).
supports(kitchen_table, arrange). supports(kitchen_table, trim). supports(kitchen_table, bundle).
supports(porch, arrange). supports(porch, trim). supports(porch, bundle).

can_story(P,T) :- supports(P,T).
#show can_story/2.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for p in SETTINGS:
        lines.append(asp.fact("place", p))
    for t in TASKS:
        lines.append(asp.fact("task", t))
    for p, s in SETTINGS.items():
        for t in s.affordances:
            lines.append(asp.fact("supports", p, t))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show can_story/2."))
    return sorted(set(asp.atoms(model, "can_story")))


def asp_verify() -> int:
    asp_set = set(asp_valid_combos())
    py_set = set((p, t) for p, t, _ in valid_combos())
    if asp_set == py_set:
        print(f"OK: clingo gate matches valid_combos() ({len(py_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print(" only in asp:", sorted(asp_set - py_set))
    print(" only in py:", sorted(py_set - asp_set))
    return 1


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program("#show can_story/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, task) combos:")
        for p, t in combos:
            print(f"  {p:14} {t}")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        for place in SETTINGS:
            for task in TASKS:
                params = StoryParams(place=place, task=task, child_name="Mina", child_type="girl", adult_name="Mom", adult_type="mother")
                samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(getattr(args, "n", None) * 50, 50):
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
