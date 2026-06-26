#!/usr/bin/env python3
"""
Small storyworld: mould, ratatouille, teamwork, and a little magic in an everyday kitchen.

This world tells a gentle slice-of-life tale where a shared cooking plan starts
with a spoiled ingredient, turns on cooperation, and ends with a comforting meal
saved by practical teamwork and a small bit of magic.
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
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    magical: bool = False
    helper: object | None = None
    ingredient: object | None = None
    knife: object | None = None
    lamp: object | None = None
    main: object | None = None
    def __post_init__(self) -> None:
        self.meters = __import__('collections').defaultdict(float, self.meters)
        self.memes = __import__('collections').defaultdict(float, self.memes)

    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "character":
            if self.type in {"girl", "woman", "mother", "mom"}:
                return {"subject": "she", "object": "her", "possessive": "her"}[case]
            if self.type in {"boy", "man", "father", "dad"}:
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
class Kitchen:
    place: str = "the apartment kitchen"
    window_light: bool = True
    affords: set[str] = field(default_factory=lambda: {"ratatouille", "cleaning", "tea", "magic"})
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
class Ingredient:
    id: str
    label: str
    phrase: str
    freshness: str
    spoilage_risk: str
    flavor: str
    tags: set[str] = field(default_factory=set)
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
    phrase: str
    function: str
    magical: bool = False
    helps: set[str] = field(default_factory=set)
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
    kitchen: str
    ingredient: str
    helper1: str
    helper2: str
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


class World:
    def __init__(self, kitchen: Kitchen) -> None:
        self.kitchen = kitchen
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

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


INGREDIENTS = {
    "mouldy_tomato": Ingredient(
        id="mouldy_tomato",
        label="tomatoes",
        phrase="a basket of tomatoes with a fuzzy mould spot",
        freshness="fresh enough to inspect",
        spoilage_risk="fuzzy and mouldy",
        flavor="bright and sweet",
        tags={"mould", "tomato", "food"},
    ),
    "mouldy_eggplant": Ingredient(
        id="mouldy_eggplant",
        label="eggplants",
        phrase="two eggplants with a little mould at the stem",
        freshness="still useful after trimming",
        spoilage_risk="soft and mould-streaked",
        flavor="deep and savory",
        tags={"mould", "eggplant", "food"},
    ),
    "mouldy_zucchini": Ingredient(
        id="mouldy_zucchini",
        label="zucchini",
        phrase="zucchini that had gone a bit mouldy in the crisper",
        freshness="not ruined yet",
        spoilage_risk="mould-spotted",
        flavor="mild and green",
        tags={"mould", "zucchini", "food"},
    ),
}

TOOLS = {
    "knife": Tool(
        id="knife",
        label="knife",
        phrase="a sharp kitchen knife",
        function="trim away the bad parts",
        helps={"cleaning", "ratatouille"},
    ),
    "pan": Tool(
        id="pan",
        label="pan",
        phrase="a wide, warm pan",
        function="cook vegetables evenly",
        helps={"ratatouille"},
    ),
    "spoon": Tool(
        id="spoon",
        label="spoon",
        phrase="a wooden spoon",
        function="stir the vegetables gently",
        helps={"ratatouille"},
    ),
    "lamp": Tool(
        id="lamp",
        label="lamp",
        phrase="a tiny lamp with a blue glass shade",
        function="make the kitchen glow with a little magic",
        magical=True,
        helps={"magic", "teamwork"},
    ),
}

CHARACTERS = {
    "Mina": {"type": "girl", "traits": ["calm", "careful", "kind"]},
    "Jon": {"type": "boy", "traits": ["patient", "helpful", "quiet"]},
    "Aunt Nia": {"type": "woman", "traits": ["warm", "practical", "cheerful"]},
    "Omar": {"type": "boy", "traits": ["bright", "eager", "gentle"]},
}

KITCHENS = {
    "apartment": Kitchen(place="the apartment kitchen", window_light=True, affords={"ratatouille", "cleaning", "tea", "magic"}),
    "cottage": Kitchen(place="the cottage kitchen", window_light=True, affords={"ratatouille", "cleaning", "tea", "magic"}),
    "studio": Kitchen(place="the little studio kitchen", window_light=False, affords={"ratatouille", "cleaning", "tea", "magic"}),
}


def _is_spoiled(ingredient: Ingredient) -> bool:
    return "mould" in ingredient.tags


def _can_save(ingredient: Ingredient) -> bool:
    return _is_spoiled(ingredient)


def _do_teamwork(world: World, cook1: Entity, cook2: Entity, ingredient: Entity) -> None:
    cook1.memes["teamwork"] = cook1.memes.get("teamwork", 0.0) + 1
    cook2.memes["teamwork"] = cook2.memes.get("teamwork", 0.0) + 1
    ingredient.meters["prepared"] = ingredient.meters.get("prepared", 0.0) + 1
    world.say(
        f"{cook1.id} and {cook2.id} split the work. One trimmed the mould, and the other set out the pan and spoon."
    )


def _do_magic(world: World, helper: Entity, ingredient: Entity) -> None:
    helper.memes["wonder"] = helper.memes.get("wonder", 0.0) + 1
    ingredient.meters["saved"] = ingredient.meters.get("saved", 0.0) + 1
    world.say(
        f"{helper.id} lifted the blue lamp, and the kitchen shone softly. "
        f"The glow did not erase the mould, but it made everyone steady and careful."
    )


def _cook_ratatouille(world: World, cook1: Entity, cook2: Entity, ingredient: Entity) -> None:
    cook1.memes["pride"] = cook1.memes.get("pride", 0.0) + 1
    cook2.memes["pride"] = cook2.memes.get("pride", 0.0) + 1
    ingredient.meters["cooked"] = ingredient.meters.get("cooked", 0.0) + 1
    world.say(
        f"Then they cooked a cozy ratatouille together, and the little kitchen filled with the smell of warm vegetables."
    )


def build_world(params: StoryParams) -> World:
    kitchen = _safe_lookup(KITCHENS, params.kitchen)
    world = World(kitchen)

    main = world.add(Entity(
        id=params.helper1,
        kind="character",
        type=_safe_lookup(CHARACTERS, params.helper1)["type"],
        traits=list(_safe_lookup(CHARACTERS, params.helper1)["traits"]),
    ))
    helper = world.add(Entity(
        id=params.helper2,
        kind="character",
        type=_safe_lookup(CHARACTERS, params.helper2)["type"],
        traits=list(_safe_lookup(CHARACTERS, params.helper2)["traits"]),
    ))
    ingredient_cfg = _safe_lookup(INGREDIENTS, params.ingredient)
    ingredient = world.add(Entity(
        id="ingredient",
        kind="thing",
        type="ingredient",
        label=ingredient_cfg.label,
        phrase=ingredient_cfg.phrase,
        owner=main.id,
        caretaker=main.id,
        meters={"mould": 1.0 if _is_spoiled(ingredient_cfg) else 0.0},
        memes={"worry": 1.0 if _is_spoiled(ingredient_cfg) else 0.0},
    ))
    knife = world.add(Entity(id="knife", kind="thing", type="tool", label="knife", phrase=TOOLS["knife"].phrase, owner=main.id))
    lamp = world.add(Entity(id="lamp", kind="thing", type="tool", label="lamp", phrase=TOOLS["lamp"].phrase, owner=helper.id, magical=True))

    world.facts.update(
        main=main,
        helper=helper,
        ingredient=ingredient,
        ingredient_cfg=ingredient_cfg,
        knife=knife,
        lamp=lamp,
        kitchen=kitchen,
    )

    world.say(
        f"{main.id} was in {kitchen.place} with {helper.id}, and the afternoon felt unhurried and ordinary."
    )
    world.say(
        f"On the counter sat {ingredient_cfg.phrase}, and {main.id} frowned because the mould made it look nearly forgotten."
    )
    world.para()
    world.say(
        f"{main.id} said they could still make ratatouille if they worked carefully."
    )
    _do_teamwork(world, main, helper, ingredient)
    _do_magic(world, helper, ingredient)
    _cook_ratatouille(world, main, helper, ingredient)
    world.say(
        f"In the end, the bowl of ratatouille came out fragrant and warm, and the kitchen felt like a small safe place again."
    )
    world.facts["resolved"] = True
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        'Write a small slice-of-life story about mouldy vegetables, teamwork, and a little magic in a kitchen.',
        f"Tell a gentle story where {f['main'].id} and {f['helper'].id} find a way to save {f['ingredient_cfg'].phrase} and make ratatouille.",
        'Write an everyday kitchen story that includes the words "mould" and "ratatouille" and ends with a warm meal shared by two helpers.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    main: Entity = _safe_fact(world, f, "main")
    helper: Entity = _safe_fact(world, f, "helper")
    ingredient: Entity = _safe_fact(world, f, "ingredient")
    cfg: Ingredient = _safe_fact(world, f, "ingredient_cfg")
    qa = [
        QAItem(
            question=f"What problem did {main.id} notice in the kitchen?",
            answer=f"{main.id} noticed that {cfg.phrase} had mould on it, so they could not just ignore it and cook right away.",
        ),
        QAItem(
            question=f"Who helped {main.id} fix the ingredients?",
            answer=f"{helper.id} helped {main.id}. They worked side by side, which is why the saving plan felt like teamwork.",
        ),
        QAItem(
            question=f"What did they make after trimming the mould away?",
            answer="They made ratatouille, a warm vegetable dish that fit the cozy kitchen mood.",
        ),
        QAItem(
            question=f"Why was the lamp important in the story?",
            answer=f"The little lamp gave a soft magical glow that helped everyone stay calm and careful while they cooked.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended with a bowl of ratatouille on the table and the kitchen feeling safe, warm, and ordinary again.",
        ),
    ]
    if ingredient.meters.get("mould", 0.0) >= THRESHOLD:
        qa.append(QAItem(
            question=f"Why did they not throw away the food right away?",
            answer="They did not throw it away right away because the mould was only on part of it, so careful trimming and teamwork could save the rest.",
        ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is mould?",
            answer="Mould is a fuzzy kind of growth that can appear on food when it sits too long or gets too damp.",
        ),
        QAItem(
            question="What is ratatouille?",
            answer="Ratatouille is a cooked vegetable dish, often made with tomatoes, zucchini, eggplant, and herbs.",
        ),
        QAItem(
            question="What is teamwork?",
            answer="Teamwork is when people help each other and split a job so it becomes easier.",
        ),
        QAItem(
            question="What is magic in a story?",
            answer="Magic is a special story idea that can make a scene feel a little wondrous or impossible, even in an everyday place.",
        ),
    ]


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


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:10} ({e.kind:8}) {' '.join(bits)}")
    return "\n".join(lines)


def select_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    kitchen = getattr(args, "kitchen", None) or rng.choice(list(KITCHENS))
    ingredient = getattr(args, "ingredient", None) or rng.choice(list(INGREDIENTS))
    helper1 = getattr(args, "helper1", None) or rng.choice(list(CHARACTERS))
    helper2 = getattr(args, "helper2", None) or rng.choice([k for k in CHARACTERS if k != helper1])
    if helper1 == helper2:
        pass
    if not _can_save(_safe_lookup(INGREDIENTS, ingredient)):
        pass
    return StoryParams(kitchen=kitchen, ingredient=ingredient, helper1=helper1, helper2=helper2)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Slice-of-life storyworld: mould, ratatouille, teamwork, and magic.")
    ap.add_argument("--kitchen", choices=KITCHENS.keys())
    ap.add_argument("--ingredient", choices=INGREDIENTS.keys())
    ap.add_argument("--helper1", choices=CHARACTERS.keys())
    ap.add_argument("--helper2", choices=CHARACTERS.keys())
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return select_params(args, rng)


ASP_RULES = r"""
character(X) :- hero(X).
character(Y) :- helper(Y).
ingredient(I) :- item(I).
mouldy(I) :- has_mould(I).
can_save(I) :- mouldy(I).

teamwork(H1,H2,I) :- character(H1), character(H2), H1 != H2, ingredient(I), can_save(I).
magic(H,I) :- character(H), ingredient(I), can_save(I).
resolved(I) :- teamwork(_,_,I), magic(_,I).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for name in CHARACTERS:
        lines.append(asp.fact("hero", name))
        lines.append(asp.fact("helper", name))
    for iid, ing in INGREDIENTS.items():
        lines.append(asp.fact("item", iid))
        if "mould" in ing.tags:
            lines.append(asp.fact("has_mould", iid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show resolved/1. #show teamwork/3. #show magic/2."))
    atoms = set(asp.atoms(model, "resolved"))
    expected = {(iid,) for iid in INGREDIENTS if "mould" in _safe_lookup(INGREDIENTS, iid).tags}
    if atoms == expected:
        print(f"OK: ASP parity matches Python for {len(expected)} mouldy ingredient(s).")
        return 0
    print("MISMATCH between ASP and Python.")
    print("ASP:", sorted(atoms))
    print("PY :", sorted(expected))
    return 1


def asp_resolved() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show resolved/1."))
    return sorted(set(asp.atoms(model, "resolved")))


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show resolved/1. #show teamwork/3. #show magic/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        print("ASP-compatible stories:")
        for iid, in asp_resolved():
            print(f"  {iid}")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        for kitchen in KITCHENS:
            for ingredient in INGREDIENTS:
                for h1 in CHARACTERS:
                    for h2 in CHARACTERS:
                        if h1 == h2:
                            continue
                        params = StoryParams(kitchen=kitchen, ingredient=ingredient, helper1=h1, helper2=h2, seed=base_seed)
                        samples.append(generate(params))
    else:
        for i in range(getattr(args, "n", None)):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))

    if getattr(args, "json", None):
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        if len(samples) > 1:
            print(f"### variant {i + 1}")
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
