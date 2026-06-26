#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/thaw_sharing_rhyme_inner_monologue_bedtime_story.py
==============================================================================================================

A small bedtime-story world about thawing, sharing, rhyme, and a child's
inner monologue.

Seed-shaped premise:
A sleepy child wants to thaw a frozen bedtime treat. The child worries about
whether to keep it all, then hears a gentle rhyme and learns to share it.
The story should feel cozy, concrete, and causally grounded: cold things thaw,
sharing creates a second place-setting, and the inner monologue carries the
turn from wanting to keeping to giving.

World model notes:
- entities have physical meters and emotional memes
- thawing changes temperature and softness over time
- sharing splits one treat into two servings
- rhyme and inner monologue are narrated as part of the child's bedtime rhythm
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
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    child: object | None = None
    parent: object | None = None
    sibling_ent: object | None = None
    treat: object | None = None
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
    warm_source: str
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
class Treat:
    id: str
    label: str
    phrase: str
    flavor: str
    can_share: bool = True
    frozen_start: bool = True
    split_label: str = "pieces"
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
    place: str
    treat: str
    name: str
    gender: str
    parent: str
    sibling: str
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


SETTINGS = {
    "kitchen": Setting(place="the kitchen", warm_source="the oven light"),
    "bedroom": Setting(place="the bedroom", warm_source="the night-light"),
    "window_seat": Setting(place="the window seat", warm_source="the sleepy lamp"),
}

TREATS = {
    "berry_bun": Treat(
        id="berry_bun",
        label="berry bun",
        phrase="a frozen berry bun",
        flavor="berry-sweet",
        can_share=True,
        split_label="halves",
    ),
    "moon_cookie": Treat(
        id="moon_cookie",
        label="moon cookie",
        phrase="a frozen moon cookie",
        flavor="vanilla-soft",
        can_share=True,
        split_label="shares",
    ),
    "sleepy_tart": Treat(
        id="sleepy_tart",
        label="sleepy tart",
        phrase="a frozen sleepy tart",
        flavor="sweet and soft",
        can_share=True,
        split_label="slices",
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Nora"]
BOY_NAMES = ["Leo", "Ben", "Sam", "Finn", "Noah", "Theo"]
SIBLINGS = ["little brother", "little sister", "older brother", "older sister"]
PARENTS = ["mother", "father"]

CURATED = [
    StoryParams(place="kitchen", treat="berry_bun", name="Lily", gender="girl", parent="mother", sibling="little brother"),
    StoryParams(place="bedroom", treat="moon_cookie", name="Leo", gender="boy", parent="father", sibling="little sister"),
    StoryParams(place="window_seat", treat="sleepy_tart", name="Mia", gender="girl", parent="mother", sibling="older brother"),
]

ASP_RULES = r"""
place(P) :- setting(P).
treat(T) :- dessert(T).
shareable(T) :- dessert(T), can_share(T).
valid(P,T) :- place(P), treat(T), shareable(T).
#show valid/2.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for tid, tr in TREATS.items():
        lines.append(asp.fact("dessert", tid))
        if tr.can_share:
            lines.append(asp.fact("can_share", tid))
        if tr.frozen_start:
            lines.append(asp.fact("frozen_start", tid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple[str, str]]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def is_reasonable(place: str, treat: str) -> bool:
    return place in SETTINGS and treat in TREATS and _safe_lookup(TREATS, treat).can_share


def valid_combos() -> list[tuple[str, str]]:
    return [(p, t) for p in SETTINGS for t in TREATS if is_reasonable(p, t)]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A cozy bedtime story about thawing and sharing.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--treat", choices=TREATS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--parent", choices=PARENTS)
    ap.add_argument("--sibling", choices=SIBLINGS)
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
    combos = [c for c in valid_combos()
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "treat", None) is None or c[1] == getattr(args, "treat", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, treat = rng.choice(list(combos))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = getattr(args, "parent", None) or rng.choice(PARENTS)
    sibling = getattr(args, "sibling", None) or rng.choice(SIBLINGS)
    return StoryParams(place=place, treat=treat, name=name, gender=gender, parent=parent, sibling=sibling)


def _warmup_steps(world: World, child: Entity, treat: Entity) -> None:
    treat.meters["temperature"] = 0.0
    treat.meters["softness"] = 0.0
    child.memes["want"] = 1.0
    child.memes["bedtime"] = 1.0
    world.say(
        f"{child.id} found {child.pronoun('possessive')} {treat.label} waiting cold on a little plate."
    )
    world.say(
        f"{child.pronoun().capitalize()} wanted to taste {treat.pronoun('object')} right away, but it was still icy."
    )


def _inner_monologue(world: World, child: Entity, treat: Entity) -> None:
    world.say(
        f"Inside {child.id}'s head, a sleepy thought whispered, "
        f'"If I wait, the {treat.label} will soften and feel nicer."'
    )


def _rhyme(world: World, parent: Entity, child: Entity, treat: Entity) -> None:
    child.memes["calm"] = child.memes.get("calm", 0.0) + 1.0
    world.say(
        f'{parent.pronoun("possessive").capitalize()} {parent.type} smiled and sang, '
        f'"Warm it slow, let kindness show; share the sweet, then heads will glow."'
    )


def _thaw(world: World, child: Entity, treat: Entity) -> None:
    treat.meters["temperature"] = 1.0
    treat.meters["softness"] = 1.0
    world.say(
        f"They set the {treat.label} beside {world.setting.warm_source}, where it could thaw slowly."
    )


def _share(world: World, child: Entity, sibling: Entity, treat: Entity) -> tuple[str, str]:
    child.memes["generous"] = child.memes.get("generous", 0.0) + 1.0
    child.memes["joy"] = child.memes.get("joy", 0.0) + 1.0
    part = "halves" if _safe_lookup(TREATS, treat.id).split_label == "halves" else _safe_lookup(TREATS, treat.id).split_label
    world.say(
        f"{child.id} broke the {treat.label} into two {part} and gave one to {sibling.label}."
    )
    return part, sibling.label


def tell(setting: Setting, treat_cfg: Treat, name: str, gender: str, parent_type: str, sibling: str) -> World:
    world = World(setting)
    child = world.add(Entity(id=name, kind="character", type=gender))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label=f"the {parent_type}"))
    sibling_ent = world.add(Entity(id="Sibling", kind="character", type="child", label=sibling))
    treat = world.add(Entity(id="Treat", type="food", label=treat_cfg.label, phrase=treat_cfg.phrase, owner=name))
    treat.meters["frozen"] = 1.0

    world.say(
        f"At bedtime, {child.id} and {parent.label} sat in {setting.place}, where the light was soft and the room was quiet."
    )
    world.say(
        f"{child.id} had {treat.phrase}, and {child.pronoun('possessive')} tummy gave a tiny, hopeful rumble."
    )
    world.para()
    _warmup_steps(world, child, treat)
    _inner_monologue(world, child, treat)
    _rhyme(world, parent, child, treat)
    _thaw(world, child, treat)
    world.para()
    world.say(
        f"After a little while, the {treat.label} grew warm enough to bend when touched."
    )
    part, _ = _share(world, child, sibling_ent, treat)
    world.say(
        f"{child.id} and {sibling_ent.label} each took a {part == 'halves' and 'half' or 'piece'}, "
        f"and both smiled the same sleepy smile."
    )
    world.say(
        f"That night, {child.id} felt proud, because sharing made the snack taste even sweeter."
    )

    world.facts.update(
        child=child,
        parent=parent,
        sibling=sibling_ent,
        treat=treat,
        setting=setting,
        treat_cfg=treat_cfg,
        shared=True,
        thawed=True,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = _safe_fact(world, f, "child")
    treat_cfg = _safe_fact(world, f, "treat_cfg")
    return [
        f'Write a cozy bedtime story about {child.id} thawing {treat_cfg.phrase} and sharing it kindly.',
        f"Tell a gentle story for a young child where a sleepy snack is thawed, a rhyme is sung, and two people share it.",
        f'Write a bedtime story that includes a quiet inner monologue, a soft rhyme, and the word "thaw".',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = _safe_fact(world, f, "child")
    parent = _safe_fact(world, f, "parent")
    sibling = _safe_fact(world, f, "sibling")
    treat = _safe_fact(world, f, "treat")
    return [
        QAItem(
            question=f"What did {child.id} want to do with the {treat.label} at bedtime?",
            answer=f"{child.id} wanted to thaw the {treat.label} and eat it as a sleepy snack.",
        ),
        QAItem(
            question=f"Who helped {child.id} make the snack feel safe and kind?",
            answer=f"{parent.label} helped by singing a gentle rhyme and suggesting they wait for the {treat.label} to thaw slowly.",
        ),
        QAItem(
            question=f"What changed when {child.id} shared the treat with {sibling.label}?",
            answer=f"The one frozen treat became two warm shares, and {child.id} felt proud and happy instead of grabby.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does thawing mean?",
            answer="Thawing means a cold frozen thing gets warmer and softer instead of staying icy.",
        ),
        QAItem(
            question="Why do people share bedtime snacks?",
            answer="People share bedtime snacks so everyone can have a little taste and feel cared for.",
        ),
        QAItem(
            question="What is a rhyme?",
            answer="A rhyme is a little song or verse with words that sound alike, which can feel calm and playful.",
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
        if e.label:
            bits.append(f"label={e.label}")
        lines.append(f"  {e.id:8} ({e.kind:7}) {' '.join(bits)}")
    return "\n".join(lines)


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


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.place), _safe_lookup(TREATS, params.treat), params.name, params.gender, params.parent, params.sibling)
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
        print(asp_program("#show valid/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show valid/2."))
        combos = sorted(set(asp.atoms(model, "valid")))
        print(f"{len(combos)} compatible bedtime-story combos:\n")
        for place, treat in combos:
            print(f"  {place:12} {treat}")
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
            header = f"### {p.name}: {p.treat} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
