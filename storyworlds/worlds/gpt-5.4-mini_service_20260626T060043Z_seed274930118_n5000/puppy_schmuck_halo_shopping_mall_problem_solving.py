#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/puppy_schmuck_halo_shopping_mall_problem_solving.py
=============================================================================================================

A small, self-contained storyworld for a bedtime-style tale in a shopping mall.

Core seed image:
- A puppy in a shopping mall
- A misunderstood "schmuck" object or name
- A halo that needs careful handling

Narrative instruments:
- Problem Solving
- Misunderstanding
- Friendship

The world simulates a child-friendly mall errand where a puppy finds a shiny halo
and mistakes about "schmuck" cause a small wobble in the plan. The friend helps
untangle the confusion, and the ending proves the problem changed the world.
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
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    friend: object | None = None
    halo: object | None = None
    hero: object | None = None
    schmuck: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
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
class MallSetting:
    place: str = "the shopping mall"
    shops: tuple[str, ...] = ("toy shop", "cafe", "hat shop", "information desk")
    world: object | None = None
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
class ObjectChoice:
    id: str
    label: str
    phrase: str
    type: str
    risk: str
    reason: str
    location: str
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
class StoryParams:
    item: str
    hero_name: str
    hero_type: str
    friend_name: str
    friend_type: str
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
    def __init__(self, setting: MallSetting) -> None:
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

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


def bedtime_opening(hero: Entity, friend: Entity, setting: MallSetting) -> str:
    return f"One quiet evening, {hero.id} the puppy and {friend.id} went to {setting.place} with soft paws and sleepy smiles."


def item_intro(item: ObjectChoice) -> str:
    return {
        "halo": "It was a little golden halo, light as a feather and bright as moonlight.",
        "schmuck": "It was a tiny shiny schmuck, a silly sparkling thing that was easy to misread.",
        "button": "It was a round pearly button that glittered like a small star.",
    }.get(item.id, f"It was {item.phrase}.")


def _r_misunderstanding(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    friend = world.get("friend")
    if hero.memes.get("confused", 0) < THRESHOLD:
        return out
    sig = ("misunderstanding")
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.memes["worry"] = hero.memes.get("worry", 0) + 1
    friend.memes["worry"] = friend.memes.get("worry", 0) + 1
    out.append("The little mix-up made both friends pause and think.")
    return out


def _r_friendship(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    friend = world.get("friend")
    if hero.memes.get("kindness", 0) < THRESHOLD or friend.memes.get("kindness", 0) < THRESHOLD:
        return out
    sig = ("friendship")
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.memes["calm"] = hero.memes.get("calm", 0) + 1
    friend.memes["calm"] = friend.memes.get("calm", 0) + 1
    out.append("Their friendship made the air feel warm and safe again.")
    return out


CAUSAL_RULES = [_r_misunderstanding, _r_friendship]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def tell_story(params: StoryParams) -> World:
    world = World(MallSetting())
    item = _safe_lookup(ITEMS, params.item)

    hero = world.add(Entity(id=params.hero_name, kind="character", type=params.hero_type))
    friend = world.add(Entity(id=params.friend_name, kind="character", type=params.friend_type))
    halo = world.add(Entity(id="halo", type=item.type, label=item.label, phrase=item.phrase, owner=hero.id))
    schmuck = world.add(Entity(id="schmuck", type="toy", label="schmuck", phrase="a tiny shiny schmuck", owner=friend.id))

    world.say(bedtime_opening(hero, friend, world.setting))
    world.say("Near the toy shop window, the puppy spotted something glowing on the floor.")
    world.say(item_intro(item))

    world.para()
    hero.memes["curious"] = 1
    if item.id == "halo":
        world.say(f"{hero.id} thought the halo was a lost crown ring and gently nosed it toward {friend.id}.")
    else:
        world.say(f"{hero.id} thought the schmuck was a lost lucky charm and nudged it closer to the bench.")

    world.say(f"But {friend.id} blinked and said it was not for keeping. It belonged back where it came from.")
    hero.memes["confused"] = 1
    propagate(world, narrate=True)

    world.para()
    world.say(f"Then {friend.id} looked closer and noticed the name tag tucked under the shine.")
    world.say(f"It was only a small misunderstanding, and the best fix was to ask the information desk for help.")
    hero.memes["kindness"] = 1
    friend.memes["kindness"] = 1
    propagate(world, narrate=True)

    world.para()
    world.say(f"Together they carried the little treasure to the right shop, and {friend.id} held the door while {hero.id} stood still.")
    world.say(f"The clerk smiled, thanked them for being careful, and put the halo back where it could be found again.")
    world.say(f"{hero.id} wagged his tail, and {friend.id} gave {hero.id} a happy pat. The mall felt calm and cozy, like a nightlight for the heart.")

    world.facts.update(
        hero=hero,
        friend=friend,
        item=item,
        halo=halo,
        schmuck=schmuck,
        setting=world.setting,
        resolved=True,
        misunderstanding=True,
    )
    return world


def generate_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = _safe_fact(world, f, "hero")
    friend: Entity = _safe_fact(world, f, "friend")
    item: ObjectChoice = _safe_fact(world, f, "item")
    return [
        f'Write a bedtime-style story about a puppy and a friend at {world.setting.place} where a {item.id} causes a small misunderstanding.',
        f"Tell a gentle story in which {hero.id} the puppy and {friend.id} solve a problem together and return a {item.label} to the right place.",
        f'Write a short warm story that includes the words "{hero.id.lower()}", "{friend.id.lower()}", and "{item.id}" in a shopping mall setting.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = _safe_fact(world, f, "hero")
    friend: Entity = _safe_fact(world, f, "friend")
    item: ObjectChoice = _safe_fact(world, f, "item")

    return [
        QAItem(
            question=f"Who went to the shopping mall in this story?",
            answer=f"{hero.id} the puppy and {friend.id} went to the shopping mall together.",
        ),
        QAItem(
            question=f"What did {hero.id} first think about the {item.id}?",
            answer=f"{hero.id} first thought it was a lost treasure and wanted to bring it closer to {friend.id}.",
        ),
        QAItem(
            question="What kind of trouble happened in the middle?",
            answer="A small misunderstanding happened, so both friends stopped and looked more carefully.",
        ),
        QAItem(
            question="How was the problem solved?",
            answer="They asked the information desk for help and returned the shiny thing to the right shop.",
        ),
        QAItem(
            question="How did the story end?",
            answer=f"It ended with {hero.id} and {friend.id} feeling calm, happy, and close as friends.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a shopping mall?",
            answer="A shopping mall is a big indoor place with many shops, walking paths, and places to visit.",
        ),
        QAItem(
            question="What is a misunderstanding?",
            answer="A misunderstanding happens when someone thinks something means one thing, but it really means something else.",
        ),
        QAItem(
            question="What does friendship help people do?",
            answer="Friendship helps people listen, be gentle, and solve problems together.",
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
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


SETTINGS = {
    "mall": MallSetting(),
}

ITEMS = {
    "halo": ObjectChoice(
        id="halo",
        label="halo",
        phrase="a tiny golden halo",
        type="toy",
        risk="could be misplaced",
        reason="it belongs back with the costume display",
        location="the costume shop",
        tags={"halo", "problem_solving"},
    ),
    "schmuck": ObjectChoice(
        id="schmuck",
        label="schmuck",
        phrase="a tiny shiny schmuck",
        type="toy",
        risk="could be mistaken for a keepsake",
        reason="it belongs back at the gift counter",
        location="the gift counter",
        tags={"schmuck", "misunderstanding"},
    ),
    "button": ObjectChoice(
        id="button",
        label="button",
        phrase="a pearly button",
        type="thing",
        risk="could be lost",
        reason="it belongs on a display pillow",
        location="the craft shop",
        tags={"problem_solving"},
    ),
}

NAMES = ["Pip", "Milo", "Nina", "Toby", "Luna", "Benny", "Daisy", "Mimi"]
FRIEND_NAMES = ["June", "Ollie", "Mina", "Rae", "Cora", "Theo", "Ari", "Nell"]


def valid_combos() -> list[tuple[str, str]]:
    return [("mall", item_id) for item_id in ITEMS]


@dataclass
class ASPCache:
    pass
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


ASP_RULES = r"""
valid(Place, Item) :- setting(Place), item(Item), at(Place, Item), has_fix(Item).
friendly(Place, Item) :- valid(Place, Item), friendship(Item), misunderstanding(Item).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    for pid in SETTINGS:
        lines.append(asp.fact("setting", pid))
        lines.append(asp.fact("at", pid, "halo"))
        lines.append(asp.fact("at", pid, "schmuck"))
        lines.append(asp.fact("at", pid, "button"))
    for iid, item in ITEMS.items():
        lines.append(asp.fact("item", iid))
        lines.append(asp.fact("has_fix", iid))
        if "misunderstanding" in item.tags:
            lines.append(asp.fact("misunderstanding", iid))
        if "problem_solving" in item.tags:
            lines.append(asp.fact("friendship", iid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Bedtime story world: puppy, schmuck, halo, and a mall-sized misunderstanding.")
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--name")
    ap.add_argument("--friend")
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
    if getattr(args, "item", None) is not None and getattr(args, "item", None) not in ITEMS:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    item = getattr(args, "item", None) or rng.choice(list(ITEMS))
    hero_name = getattr(args, "name", None) or rng.choice(NAMES)
    friend_name = getattr(args, "friend", None) or rng.choice(FRIEND_NAMES)
    return StoryParams(
        item=item,
        hero_name=hero_name,
        hero_type="puppy",
        friend_name=friend_name,
        friend_type="child",
    )


def generate(params: StoryParams) -> StorySample:
    world = tell_story(params)
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


CURATED = [
    StoryParams(item="halo", hero_name="Pip", hero_type="puppy", friend_name="June", friend_type="child"),
    StoryParams(item="schmuck", hero_name="Milo", hero_type="puppy", friend_name="Mina", friend_type="child"),
    StoryParams(item="button", hero_name="Luna", hero_type="puppy", friend_name="Ollie", friend_type="child"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible story combos:\n")
        for place, item in combos:
            print(f"  {place:10} {item}")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(getattr(args, "n", None) * 20, 20):
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
            header = f"### {p.hero_name} and {p.friend_name} with {p.item}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
