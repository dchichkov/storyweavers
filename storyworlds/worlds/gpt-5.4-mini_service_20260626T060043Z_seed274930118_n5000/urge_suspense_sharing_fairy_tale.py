#!/usr/bin/env python3
"""
storyworlds/worlds/urge_suspense_sharing_fairy_tale.py
=======================================================

A small fairy-tale storyworld about an urgent temptation, a suspenseful pause,
and a shared ending that changes the world state.

Seed tale, used to build the world:
---
Once in a moonlit forest, a little girl named Mira found a warm honey cake on a
stone bench. She felt a strong urge to keep it for herself, because she was
hungry and the cake smelled sweet.

As she walked home, she heard a tiny voice in the dark asking for help. A
small owl had lost her way and was shivering near the path. Mira looked at the
cake again and felt the urge tugging at her heart. The forest felt quiet and
worrisome, and she did not know whether to share.

At last Mira broke the cake in two and shared it with the owl. The owl led her
safely through the trees, and the forest seemed brighter afterward.

This script turns that premise into a tiny simulation with meters and memes:
- hunger and sweetness can drive the urge to keep the treat
- darkness and loneliness create suspense
- sharing reduces hunger and raises trust, which can change the ending
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
    caregiver: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    half: object | None = None
    helper: object | None = None
    hero: object | None = None
    snack: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "queen", "princess"}
        male = {"boy", "man", "father", "king", "prince"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.plural:
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
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
    twilight: str
    woods: bool = True
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
class Treat:
    id: str
    label: str
    phrase: str
    sweetness: str
    shareable: bool = True
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
    setting: str
    treat: str
    child_name: str
    child_type: str
    helper_name: str
    helper_type: str
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
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


SETTINGS = {
    "moonlit_forest": Setting(place="the moonlit forest", twilight="moonlit"),
    "stone_bridge": Setting(place="the stone bridge", twilight="misty"),
    "hedge_cottage": Setting(place="the hedge cottage", twilight="golden"),
}

TREATS = {
    "honey_cake": Treat(
        id="honey_cake",
        label="honey cake",
        phrase="a warm honey cake with sugar on top",
        sweetness="sweet and golden",
    ),
    "berry_tart": Treat(
        id="berry_tart",
        label="berry tart",
        phrase="a little berry tart with red juice shining on it",
        sweetness="bright and sweet",
    ),
    "apple_turnover": Treat(
        id="apple_turnover",
        label="apple turnover",
        phrase="a flaky apple turnover that smelled like cinnamon",
        sweetness="warm and cozy",
    ),
}

CHILDREN = ["Mira", "Lena", "Iris", "Nora", "Elsa", "Pippa"]
HELPERS = ["owl", "mouse", "fox", "rabbit", "sparrow", "deer"]
TRAITS = ["little", "curious", "gentle", "brave", "bright"]


def valid_combos() -> list[tuple[str, str]]:
    return [(s, t) for s in SETTINGS for t in TREATS]


def urge_reasonable(treat: Treat) -> bool:
    return treat.shareable


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A fairy-tale storyworld about urge, suspense, and sharing.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--treat", choices=TREATS)
    ap.add_argument("--name")
    ap.add_argument("--helper")
    ap.add_argument("--child-type", choices=["girl", "boy"])
    ap.add_argument("--helper-type", choices=["owl", "mouse", "fox", "rabbit", "sparrow", "deer"])
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


def explain_rejection(treat: Treat) -> str:
    return f"(No story: {treat.label} is not a shareable treat in this world.)"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    setting = getattr(args, "setting", None) or rng.choice(list(SETTINGS))
    treat = getattr(args, "treat", None) or rng.choice(list(TREATS))
    if not urge_reasonable(_safe_lookup(TREATS, treat)):
        return _fallback_storyparams(args, rng, StoryParams, globals())
    child_type = getattr(args, "child_type", None) or rng.choice(["girl", "boy"])
    child_name = getattr(args, "name", None) or rng.choice(CHILDREN)
    helper_type = getattr(args, "helper_type", None) or rng.choice(HELPERS)
    helper_name = getattr(args, "helper", None) or rng.choice(HELPERS)
    return StoryParams(
        setting=setting,
        treat=treat,
        child_name=child_name,
        child_type=child_type,
        helper_name=helper_name,
        helper_type=helper_type,
    )


def _resolve_article(label: str) -> str:
    return "an" if label[:1].lower() in "aeiou" else "a"


def tell(setting: Setting, treat: Treat, child_name: str, child_type: str, helper_name: str, helper_type: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=child_name, kind="character", type=child_type, label=child_name))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_type, label=helper_type))
    snack = world.add(Entity(
        id=treat.id,
        type="thing",
        label=treat.label,
        phrase=treat.phrase,
        owner=hero.id,
        caregiver=helper.id,
    ))
    hero.meters["hunger"] = 2.0
    hero.memes["urge"] = 2.0
    hero.memes["hope"] = 1.0
    helper.memes["lonely"] = 1.0
    helper.meters["distance"] = 1.0
    world.facts.update(hero=hero, helper=helper, snack=snack, treat=treat)

    world.say(
        f"Once upon a time, {child_name} was a {hero.pronoun('possessive')} little {child_type} in {setting.place}."
        f" {hero.pronoun().capitalize()} carried {(_resolve_article(treat.label))} {treat.label} that looked {treat.sweetness}."
    )
    world.say(
        f"{child_name} felt a strong urge to keep {snack.it()} all by {hero.pronoun('possessive')}self, because the cake smelled too good to share."
        f" But the forest was quiet, and quiet can make a heart listen closely."
    )

    world.para()
    hero.memes["suspense"] = 1.0
    world.say(
        f"As {child_name} stepped deeper into {setting.place}, the moon climbed higher and the path grew dim."
        f" Then a small voice drifted from the dark: '{child_name}, can you help me?'"
    )
    world.say(
        f"It was {helper_name}, a lost {helper_type}, shivering near the roots."
        f" The little helper was hungry too, and the silence made the moment feel very long."
    )

    world.para()
    hero.memes["conflict"] = 1.0
    if hero.memes["urge"] >= THRESHOLD and hero.memes["hunger"] >= THRESHOLD:
        world.say(
            f"{child_name} looked at the {treat.label} again and felt the urge tug harder."
            f" For one suspenseful breath, {hero.pronoun()} did not know whether to keep it or share it."
        )
    if helper.memes["lonely"] >= THRESHOLD:
        world.say(
            f"Then {child_name} saw how lonely {helper_name} looked in the dark, and {hero.pronoun('possessive')} heart softened."
        )

    shared = False
    if treat.shareable:
        shared = True
        half = world.add(Entity(id=f"{treat.id}_half", type="thing", label=f"half of the {treat.label}", owner=helper.id))
        hero.meters["hunger"] -= 1.0
        helper.meters["hunger"] = 0.0
        hero.memes["urge"] = 0.0
        hero.memes["kindness"] = 1.0
        helper.memes["trust"] = 2.0
        helper.memes["hope"] = 2.0
        world.say(
            f"At last {child_name} broke the treat in two and shared {half.it()} with {helper_name}."
            f" The first bite was small, but it made the dark feel less sharp."
        )
        world.say(
            f"{helper_name} smiled, and in return {helper_name} showed the safe path through the trees."
            f" Together they walked home while the moon looked like a silver lantern above them."
        )
    else:
        world.say(
            f"{child_name} could not share the treat, so the night stayed tense until a helper found another way to guide the way."
        )

    world.para()
    if shared:
        world.say(
            f"By the end, the {treat.label} was smaller, but the forest felt friendlier."
            f" {child_name} was no longer alone in the dark, and the little path home seemed bright as a ribbon."
        )
    else:
        world.say(
            f"By the end, {child_name} still held the treat, but the night had taught a cautious lesson about asking for help."
        )

    world.facts.update(shared=shared)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    helper = _safe_fact(world, f, "helper")
    snack = _safe_fact(world, f, "snack")
    return [
        f'Write a short fairy tale for a child who feels an urge to keep {snack.label} instead of sharing.',
        f"Tell a suspenseful but gentle story where {hero.id} meets a lost {helper.type} in {world.setting.place}.",
        f"Write a story about sharing a {snack.label} that ends with the characters finding the way home together.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    helper = _safe_fact(world, f, "helper")
    snack = _safe_fact(world, f, "snack")
    treat = _safe_fact(world, f, "treat")
    qa = [
        QAItem(
            question=f"What did {hero.id} feel when {hero.pronoun()} found the {snack.label}?",
            answer=f"{hero.id} felt a strong urge to keep the {snack.label} because it smelled {treat.sweetness}.",
        ),
        QAItem(
            question=f"Why did the moment become suspenseful in {world.setting.place}?",
            answer=f"It became suspenseful because the path grew dark and {helper.id} was lost and asking for help in the forest.",
        ),
        QAItem(
            question=f"What did {hero.id} do at the end of the story?",
            answer=f"{hero.id} shared the {snack.label} with {helper.id}, and that helped them find the safe path home.",
        ),
    ]
    if f.get("shared"):
        qa.append(
            QAItem(
                question=f"How did sharing change what happened to {hero.id} and {helper.id}?",
                answer=f"Sharing made {hero.id} feel kinder and helped {helper.id} feel trust and hope, so they could walk home together.",
            )
        )
    return qa


KNOWLEDGE = {
    "urge": [
        QAItem(
            question="What is an urge?",
            answer="An urge is a strong feeling that makes you want to do something right away.",
        )
    ],
    "sharing": [
        QAItem(
            question="Why do people share food?",
            answer="People share food so everyone can have some, and sharing can make others feel cared for.",
        )
    ],
    "suspense": [
        QAItem(
            question="What makes a story suspenseful?",
            answer="A story feels suspenseful when you are waiting to see what will happen next and you do not know the answer yet.",
        )
    ],
    "fairy_tale": [
        QAItem(
            question="What is a fairy tale?",
            answer="A fairy tale is a magical story with brave choices, strange helpers, and a clear ending.",
        )
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    out = []
    out.extend(KNOWLEDGE["urge"])
    out.extend(KNOWLEDGE["sharing"])
    out.extend(KNOWLEDGE["suspense"])
    out.extend(KNOWLEDGE["fairy_tale"])
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== Story questions =="]
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World knowledge ==")
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
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
shareable(treat).
valid_story(S,T) :- setting(S), treat(T), shareable(T).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for t in TREATS:
        lines.append(asp.fact("treat", t))
        lines.append(asp.fact("shareable", t))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if py == asp_set:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and python gates:")
    print("only in python:", sorted(py - asp_set))
    print("only in clingo:", sorted(asp_set - py))
    return 1


CURATED = [
    StoryParams(setting="moonlit_forest", treat="honey_cake", child_name="Mira", child_type="girl", helper_name="Owl", helper_type="owl"),
    StoryParams(setting="stone_bridge", treat="berry_tart", child_name="Lena", child_type="girl", helper_name="Fox", helper_type="fox"),
    StoryParams(setting="hedge_cottage", treat="apple_turnover", child_name="Iris", child_type="girl", helper_name="Rabbit", helper_type="rabbit"),
]


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.setting), _safe_lookup(TREATS, params.treat), params.child_name, params.child_type, params.helper_name, params.helper_type)
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
        print(asp_program("#show valid_story/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show valid_story/2."))
        print(sorted(set(asp.atoms(model, "valid_story"))))
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
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

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
