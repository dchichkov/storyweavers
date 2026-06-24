#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260624T081143Z_seed2038046945_n100/present_bumpity_beggar_happy_ending_conflict_bedtime.py
==============================================================================================================

A small bedtime-story world about a child, a bumpity path, a present, and a beggar.

Seed-tale inspiration:
---
At bedtime, a kind child finds a small present. On a bumpity street, the child wants to
bring it to a beggar who is sitting near the corner. The parent worries that the present
will get damaged or lost on the bumpy way. Together they find a gentle, careful way to
carry it, and the child gives the present away. The story ends happily, with everyone
feeling calmer and kinder.

World model:
- physical meters: bumpiness, damage, warmth, closeness, carried, wrapped
- emotional memes: joy, worry, hope, conflict, gratitude, kindness
- state changes drive the narration; the ending proves the present arrived safely.

Narrative instruments:
- present
- bumpity
- beggar
- Happy Ending
- Conflict
- Bedtime Story
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
    plural: bool = False
    owner: Optional[str] = None
    carried_by: Optional[str] = None
    wrapped: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    beggar: object | None = None
    hero: object | None = None
    parent: object | None = None
    present: object | None = None
    scarf: object | None = None
    def __post_init__(self):
        for k in ["bumpiness", "damage", "warmth", "closeness", "carried", "wrapped"]:
            self.meters.setdefault(k, 0.0)
        for k in ["joy", "worry", "hope", "conflict", "gratitude", "kindness"]:
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "character" and self.type in {"girl", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.kind == "character" and self.type in {"boy", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

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
    place: str = "the bumpity street"
    nighttime: bool = True
    affords: set[str] = field(default_factory=lambda: {"deliver_present"})
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
class StoryParams:
    place: str
    hero_name: str
    hero_type: str
    parent_type: str
    beggar_name: str
    seed: Optional[int] = None
    samples: list = field(default_factory=list)
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


SETTINGS = {
    "street": Setting(place="the bumpity street", nighttime=True, affords={"deliver_present"}),
    "lane": Setting(place="the little lane", nighttime=True, affords={"deliver_present"}),
    "porch": Setting(place="the quiet porch", nighttime=True, affords={"deliver_present"}),
}

HERO_NAMES = ["Mia", "Noah", "Lily", "Theo", "Ava", "Eli", "Nora", "Ben"]
BEGGAR_NAMES = ["Mr. Dove", "Mrs. Pine", "Old Jo", "Sammy", "Mister Finn"]

ASP_RULES = r"""
is_valid(Place) :- setting(Place), bumpity(Place), can_deliver(Place).
safe(Place) :- is_valid(Place), wrapped_present.
happy_ending(Place) :- safe(Place), meets_beggar(Place).
#show is_valid/1.
#show happy_ending/1.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if setting.nighttime:
            lines.append(asp.fact("nighttime", sid))
        if "deliver_present" in setting.affords:
            lines.append(asp.fact("can_deliver", sid))
        if "street" in sid or "lane" in sid:
            lines.append(asp.fact("bumpity", sid))
    lines.append(asp.fact("wrapped_present"))
    lines.append(asp.fact("meets_beggar", "street"))
    lines.append(asp.fact("meets_beggar", "lane"))
    lines.append(asp.fact("meets_beggar", "porch"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


class World:
    def __init__(self, setting: Setting):
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
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


def path_is_bumpity(setting: Setting) -> bool:
    return "bumpity" in setting.place


def can_keep_present_safe(setting: Setting) -> bool:
    return path_is_bumpity(setting)


def tell(params: StoryParams) -> World:
    setting = _safe_lookup(SETTINGS, params.place)
    world = World(setting)
    hero = world.add(Entity(id=params.hero_name, kind="character", type=params.hero_type, label=params.hero_name))
    parent = world.add(Entity(id="parent", kind="character", type=params.parent_type, label=params.parent_type))
    beggar = world.add(Entity(id=params.beggar_name, kind="character", type="beggar", label=params.beggar_name))
    present = world.add(Entity(id="present", type="present", label="present", phrase="a small wrapped present"))
    scarf = world.add(Entity(id="scarf", type="cloth", label="scarf", phrase="a soft scarf"))

    # Act 1
    world.say(f"At bedtime, {hero.id} found {present.phrase} under the lamp.")
    world.say(f"{hero.id} wanted to give the present to {beggar.label}, because kindness felt warm and good.")
    present.owner = hero.id
    hero.memes["kindness"] += 1
    hero.memes["hope"] += 1

    # Act 2
    world.para()
    world.say(f"Outside, {setting.place} was bumpity and dark, and the little stones went tap-tap under their shoes.")
    world.say(f"{parent.label.capitalize()} worried that the present might get damaged on the bumpity way.")
    parent.memes["worry"] += 1
    hero.memes["conflict"] += 1
    world.say(f"{hero.id} felt the conflict in a small knot of feelings, because the gift mattered and so did the warning.")

    # Act 3
    world.para()
    if not can_keep_present_safe(setting):
        pass
    scarf.wrapped = True
    present.wrapped = True
    present.meters["wrapped"] = 1
    present.meters["carried"] = 1
    hero.memes["conflict"] = 0
    hero.memes["joy"] += 1
    parent.memes["worry"] = 0
    parent.memes["hope"] += 1
    world.say(f"Then {parent.label} wrapped the present in the scarf and held it close against the bumps.")
    world.say(f"Together they walked slowly to {beggar.label}, and the little present stayed safe the whole way.")
    world.say(f"{hero.id} gave the present to {beggar.label}, and {beggar.label} smiled with grateful eyes.")
    world.say(f"It was a Happy Ending: the bumpity path did not win, and bedtime ended with quiet, kind hearts.")

    world.facts.update(
        hero=hero,
        parent=parent,
        beggar=beggar,
        present=present,
        scarf=scarf,
        setting=setting,
        resolved=True,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    hero = world.facts["hero"]
    beggar = world.facts["beggar"]
    return [
        'Write a bedtime story for a small child about a present, a bumpity path, and a beggar.',
        f"Tell a gentle story where {hero.id} wants to bring a present to {beggar.label}, but there is a conflict about the bumpity way.",
        "Write a calm bedtime story with a happy ending in which care and kindness help a gift arrive safely.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero = world.facts["hero"]
    parent = world.facts["parent"]
    beggar = world.facts["beggar"]
    present = world.facts["present"]
    return [
        QAItem(
            question=f"Why did {parent.label} worry on the bumpity street?",
            answer=f"{parent.label.capitalize()} worried because the path was bumpity and the present could get damaged before it reached {beggar.label}.",
        ),
        QAItem(
            question=f"What helped keep the present safe?",
            answer="The present was wrapped in a scarf and carried carefully, so the bumps did not hurt it.",
        ),
        QAItem(
            question=f"What was the happy ending?",
            answer=f"{hero.id} gave the present to {beggar.label}, {beggar.label} smiled, and everyone settled down peacefully for bedtime.",
        ),
        QAItem(
            question=f"Who received the present?",
            answer=f"{beggar.label} received the present with a grateful smile.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does bumpity mean?",
            answer="Bumpity means bumpy and uneven, with little ups and downs that can make walking feel shaky.",
        ),
        QAItem(
            question="What is a beggar?",
            answer="A beggar is a person who asks others for help or money, often because they do not have enough.",
        ),
        QAItem(
            question="What is a present?",
            answer="A present is a gift you give to someone else to be kind or to celebrate.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story qa ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    out = ["--- world trace ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        out.append(f"{e.id}: {' '.join(bits)}")
    return "\n".join(out)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Bedtime story world with a bumpity present and a beggar.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--name")
    ap.add_argument("--beggar")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
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
    hero_type = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    hero_name = getattr(args, "name", None) or rng.choice(HERO_NAMES)
    parent_type = getattr(args, "parent", None) or rng.choice(["mother", "father"])
    beggar_name = getattr(args, "beggar", None) or rng.choice(BEGGAR_NAMES)
    if not can_keep_present_safe(_safe_lookup(SETTINGS, place)):
        return _fallback_storyparams(args, rng, StoryParams, globals())
    return StoryParams(place=place, hero_name=hero_name, hero_type=hero_type, parent_type=parent_type, beggar_name=beggar_name)


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


def valid_combos() -> list[tuple[str, str]]:
    return [(k, "present") for k in SETTINGS]


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show is_valid/1."))
    return sorted(set(asp.atoms(model, "is_valid")))


def asp_verify() -> int:
    python_set = set((p,) for p, _ in valid_combos())
    clingo_set = set(asp_valid_combos())
    if python_set == clingo_set:
        print(f"OK: clingo gate matches valid_combos() ({len(python_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos()")
    print("python:", sorted(python_set))
    print("clingo:", sorted(clingo_set))
    return 1


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program("#show happy_ending/1."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples = []
    if getattr(args, "all", None):
        samples = [generate(StoryParams(place=k, hero_name=_safe_lookup(HERO_NAMES, i % len(HERO_NAMES)), hero_type="girl" if i % 2 == 0 else "boy", parent_type="mother", beggar_name=_safe_lookup(BEGGAR_NAMES, i % len(BEGGAR_NAMES)))) for i, k in enumerate(SETTINGS)]
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
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
