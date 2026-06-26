#!/usr/bin/env python3
"""
storyworlds/worlds/interpret_oma_transformation_suspense_nursery_rhyme.py
========================================================================

A small story world in a nursery-rhyme voice about an interpreter child and
Oma, with a gentle transformation and a little suspense.

Premise:
- A child named Pip can interpret for Oma.
- Oma has a beloved old toy / object that is about to change.
- A tiny worry grows when the object vanishes or seems broken.

Turn:
- Pip interprets a clue and realizes the change is not a loss.
- The object transforms into something useful or beautiful.

Resolution:
- Oma and Pip feel relieved; the transformed thing proves safe and happy.
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
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    child: object | None = None
    item: object | None = None
    oma: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "character" and self.type in {"girl", "woman", "mother", "grandmother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.kind == "character" and self.type in {"boy", "man", "father", "grandfather"}:
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
    place: str = "the little house"
    indoors: bool = True
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
class Item:
    id: str
    label: str
    phrase: str
    type: str
    transforms_into: str
    trigger: str
    reveal: str
    gentle: bool = True
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
    item: str
    name: str
    gender: str
    setting: str
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
        self.facts: dict = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()

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


SETTINGS = {
    "house": Setting(place="the little house", indoors=True),
    "kitchen": Setting(place="the warm kitchen", indoors=True),
    "attic": Setting(place="the dusty attic", indoors=True),
    "garden": Setting(place="the moonlit garden", indoors=False),
}

ITEMS = {
    "egg": Item(
        id="egg",
        label="egg",
        phrase="a pale blue egg",
        type="egg",
        transforms_into="bird",
        trigger="cracked softly in the moonlight",
        reveal="a tiny songbird",
    ),
    "seed": Item(
        id="seed",
        label="seed",
        phrase="a small brown seed",
        type="seed",
        transforms_into="flower",
        trigger="warmed in Oma's hands",
        reveal="a bright little flower",
    ),
    "stone": Item(
        id="stone",
        label="stone",
        phrase="a smooth gray stone",
        type="stone",
        transforms_into="star",
        trigger="shined beside the window",
        reveal="a little glowing star",
    ),
}

GIRL_NAMES = ["Mia", "Nina", "Lily", "Ada", "Rose", "Ivy"]
BOY_NAMES = ["Pip", "Finn", "Theo", "Ben", "Max", "Noah"]


def nursery_voice(item: Item) -> str:
    return {
        "egg": "Hush-a-bye, hush-a-lay, the moon can tuck a shell away.",
        "seed": "Tip-tap, tip-toe, a tiny seed knows how to grow.",
        "stone": "Blink-a-bright, blink-a-blue, a stone can hide a spark or two.",
    }[item.id]


def world_detail(setting: Setting) -> str:
    if setting.indoors:
        return f"{setting.place.capitalize()} was still and small, with soft light on the floor."
    return "Outside the night was silver, and the leaves went whisper-wee."


def transform_item(world: World, child: Entity, oma: Entity, item: Entity, item_def: Item) -> None:
    if ("transform", item.id) in world.fired:
        return
    world.fired.add(("transform", item.id))
    item.type = item_def.transforms_into
    item.label = item_def.reveal
    item.phrase = item_def.reveal
    item.meters["changed"] = 1.0
    child.memes["wonder"] += 1.0
    oma.memes["relief"] += 1.0
    world.say(
        f"Then {item.phrase} was there instead, as gentle as a bell. "
        f"It had not gone away; it had changed its dress."
    )


def tell(setting: Setting, item_def: Item, hero_name: str, hero_gender: str) -> World:
    world = World(setting)
    child = world.add(Entity(id=hero_name, kind="character", type=hero_gender, label=hero_name))
    oma = world.add(Entity(id="Oma", kind="character", type="grandmother", label="Oma"))
    item = world.add(Entity(
        id=item_def.id,
        kind="thing",
        type=item_def.type,
        label=item_def.label,
        phrase=item_def.phrase,
        owner=oma.id,
        caretaker=oma.id,
    ))

    child.memes["love"] = 1.0
    child.memes["curiosity"] = 1.0
    oma.memes["love"] = 1.0
    oma.memes["worry"] = 1.0

    world.say(f"{hero_name} could interpret for Oma when words were in a tangle.")
    world.say(f"Oma smiled at {hero_name}, and {hero_name} smiled right back.")
    world.say(f"{world_detail(setting)} {nursery_voice(item_def)}")
    world.say(f"Oma kept {item.phrase} on a shelf, and {hero_name} watched it every day.")

    world.para()
    world.say(
        f"One small night, the {item.label} {item_def.trigger}, "
        f"and Oma gasped so light and thin."
    )
    world.say(f"{hero_name} held still and listened for the meaning under the din.")
    child.memes["suspense"] = 1.0
    oma.memes["suspense"] = 1.0

    world.para()
    world.say(
        f"{hero_name} interpreted the hush and heard a tiny clue: "
        f"the change was not a loss, but something new."
    )
    world.say(
        f"So {hero_name} opened the window, and the moon came walking in to see "
        f"what the little secret would begin."
    )
    transform_item(world, child, oma, item, item_def)

    world.para()
    world.say(
        f"Oma laughed, then hugged {hero_name} tight. "
        f"The new little {item.type} twinkled in the night."
    )
    world.say(
        f"And {hero_name} said, in a sing-song way, "
        f"'{item_def.reveal} stays with us today!'"
    )

    world.facts.update(
        child=child,
        oma=oma,
        item=item,
        item_def=item_def,
        setting=setting,
        transformed=True,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = _safe_fact(world, f, "child")
    item = _safe_fact(world, f, "item_def")
    return [
        f"Write a nursery-rhyme story about {child.id} who can interpret for Oma and helps a {item.label} transform.",
        f"Tell a gentle suspense story where Oma fears a {item.label} is lost, but the child notices a clue and the thing changes into {item.reveal}.",
        f"Write a short rhyming tale with the words interpret and Oma, ending in a happy transformation.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = _safe_fact(world, f, "child")
    oma = _safe_fact(world, f, "oma")
    item = _safe_fact(world, f, "item")
    item_def = _safe_fact(world, f, "item_def")
    return [
        QAItem(
            question=f"Who could interpret for Oma in the story?",
            answer=f"{child.id} could interpret for Oma when the words got tangled.",
        ),
        QAItem(
            question=f"What happened to the {item_def.label} after the suspenseful moment?",
            answer=f"The {item_def.label} transformed into {item_def.reveal}.",
        ),
        QAItem(
            question=f"Why did Oma worry before the ending?",
            answer=f"Oma worried because the {item_def.label} seemed to disappear or break, but it was only changing into something new.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    item_def = _safe_fact(world, f, "item_def")
    return [
        QAItem(
            question="What does it mean to interpret?",
            answer="To interpret means to explain words or meaning from one person to another, often across different languages.",
        ),
        QAItem(
            question="Who is an Oma?",
            answer="Oma is a word some families use for grandmother.",
        ),
        QAItem(
            question=f"What is a {item_def.label} in simple words?",
            answer=f"A {item_def.label} is a small thing that can hold life or surprise, depending on the story.",
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
        bits = []
        if e.meters:
            bits.append(f"meters={dict(e.meters)}")
        if e.memes:
            bits.append(f"memes={dict(e.memes)}")
        if e.phrase:
            bits.append(f"phrase={e.phrase!r}")
        lines.append(f"  {e.id:8} ({e.kind:7}/{e.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({name for name, *_ in world.fired})}")
    return "\n".join(lines)


ASP_RULES = r"""
#show valid/3.
#show valid_story/4.

valid(Item, Setting, Name) :- item(Item), setting(Setting), name(Name).
valid_story(Item, Setting, Name, Gender) :- valid(Item, Setting, Name), gender(Gender).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for iid in ITEMS:
        lines.append(asp.fact("item", iid))
    for name in GIRL_NAMES:
        lines.append(asp.fact("name", name))
        lines.append(asp.fact("gender", "girl"))
    for name in BOY_NAMES:
        lines.append(asp.fact("name", name))
        lines.append(asp.fact("gender", "boy"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/4."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    clingo_set = set(asp_valid_combos())
    python_set = set((iid, sid, name) for sid in SETTINGS for iid in ITEMS for name in (GIRL_NAMES + BOY_NAMES))
    if clingo_set == python_set:
        print(f"OK: clingo gate matches python combos ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and python combos:")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A nursery-rhyme story world about interpret, Oma, suspense, and transformation.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
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
    item_id = getattr(args, "item", None) or rng.choice(list(ITEMS))
    setting_id = getattr(args, "setting", None) or rng.choice(list(SETTINGS))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    if gender == "girl":
        name = getattr(args, "name", None) or rng.choice(GIRL_NAMES)
    else:
        name = getattr(args, "name", None) or rng.choice(BOY_NAMES)
    return StoryParams(item=item_id, name=name, gender=gender, setting=setting_id)


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.setting), _safe_lookup(ITEMS, params.item), params.name, params.gender)
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
    StoryParams(item="egg", name="Pip", gender="boy", setting="garden"),
    StoryParams(item="seed", name="Mia", gender="girl", setting="house"),
    StoryParams(item="stone", name="Finn", gender="boy", setting="attic"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/4."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        combos = asp_valid_combos()
        stories = asp_valid_stories()
        print(f"{len(combos)} compatible combos ({len(stories)} with gender):")
        for item, setting, name in combos:
            print(f"  {item:5} {setting:8} {name}")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 20):
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
        header = ""
        if getattr(args, "all", None):
            p = sample.params
            header = f"### {p.name}: {p.item} in {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
