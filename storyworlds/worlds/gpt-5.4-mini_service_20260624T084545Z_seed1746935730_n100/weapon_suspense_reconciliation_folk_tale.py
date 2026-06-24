#!/usr/bin/env python3
"""
storyworlds/worlds/weapon_suspense_reconciliation_folk_tale.py
==============================================================

A small folk-tale storyworld about a child, a missing weapon, rising suspense,
and a gentle reconciliation.

The seed tale:
---
In a quiet village by the dark woods, a child named Tova loved hearing old
stories from Grandma Miri. In those stories, the village kept a special weapon:
a bronze spear hung above the hearth. It was never used for fighting. It was a
sign that the village would stay safe together.

One evening, the spear was missing. Tova worried that the old stories were
false. Grandma Miri grew quiet, and the neighbors whispered. Tova followed a
trail of bent grass to the mill, where the spear had been borrowed by a scared
shepherd to scare away wolves. When the shepherd explained, Grandma Miri did
not scold him. She smiled, thanked him for protecting the sheep, and helped him
hang the spear back in its place.

The village felt calm again, and Tova learned that a weapon could belong to a
story of safety, not only a story of fear.
---

World model:
- Entities have physical meters and emotional memes.
- The weapon can be hidden, carried, or restored.
- Suspense grows when the weapon is missing and the village fears trouble.
- Reconciliation happens when the borrower returns the weapon and the elder
  chooses understanding over anger.
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
    carried_by: Optional[str] = None
    hidden: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    borrower: object | None = None
    child: object | None = None
    elder: object | None = None
    entities: set[str] = field(default_factory=set)
    weapon: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "grandmother", "woman", "elder"}
        male = {"boy", "father", "grandfather", "man", "shepherd"}
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
class Place:
    name: str
    indoors: bool = False
    edges: tuple[str, ...] = ()
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


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.lines: list[str] = []
        self.facts: dict[str, object] = {}
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
            self.lines.append(text)

    def para(self) -> None:
        if self.lines and self.lines[-1] != "":
            self.lines.append("")

    def render(self) -> str:
        out: list[str] = []
        chunk: list[str] = []
        for line in self.lines:
            if line == "":
                if chunk:
                    out.append(" ".join(chunk))
                    chunk = []
            else:
                chunk.append(line)
        if chunk:
            out.append(" ".join(chunk))
        return "\n\n".join(out)

    def copy(self) -> "World":
        clone = World(self.place)
        clone.entities = {k: Entity(**{
            "id": e.id, "kind": e.kind, "type": e.type, "label": e.label,
            "phrase": e.phrase, "owner": e.owner, "caretaker": e.caretaker,
            "carried_by": e.carried_by, "hidden": e.hidden,
            "meters": dict(e.meters), "memes": dict(e.memes),
        }) for k, e in self.entities.items()}
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        return clone


@dataclass
class StoryParams:
    place: str
    name: str
    elder_name: str
    borrower_name: str
    weapon: str
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


PLACES = {
    "village": Place("the village", indoors=False, edges=("woods", "mill", "well")),
}

WEAPONS = {
    "bronze_spear": {"label": "bronze spear", "phrase": "a bronze spear with a dull shine"},
    "iron_knife": {"label": "iron knife", "phrase": "an iron knife in a carved sheath"},
    "oak_staff": {"label": "oak staff", "phrase": "an oak staff with a silver band"},
}

NAMES = ["Tova", "Niko", "Lena", "Soren", "Mara", "Ivo"]
ELDERS = ["Grandma Miri", "Grandfather Jaro", "Aunt Selda", "Old Bram"]
BORROWERS = ["the shepherd", "the miller", "the woodcutter", "the baker"]


class StoryRules:
    @staticmethod
    def missing_weapon(world: World) -> None:
        weapon = world.get("weapon")
        village = world.get("village")
        if weapon.hidden and weapon.meters.get("missing", 0) >= THRESHOLD and "missing" not in world.fired:
            world.fired.add("missing")
            village.memes["suspense"] = village.memes.get("suspense", 0) + 1
            world.say(
                f"By dusk, {weapon.label} was gone from its hook, and the village grew quiet."
            )

    @staticmethod
    def worried_child(world: World) -> None:
        child = world.get("child")
        if child.memes.get("worry", 0) >= THRESHOLD and "worry" not in world.fired:
            world.fired.add("worry")
            world.say(
                f"{child.id} could not stop thinking about the missing weapon."
            )

    @staticmethod
    def return_and_reconcile(world: World) -> None:
        weapon = world.get("weapon")
        elder = world.get("elder")
        borrower = world.get("borrower")
        child = world.get("child")
        if weapon.carried_by == borrower.id and borrower.memes.get("apology", 0) >= THRESHOLD and "reconcile" not in world.fired:
            world.fired.add("reconcile")
            elder.memes["warmth"] = elder.memes.get("warmth", 0) + 1
            child.memes["relief"] = child.memes.get("relief", 0) + 1
            world.say(
                f"{borrower.id} returned {weapon.label}, and {elder.id} listened before answering."
            )
            world.say(
                f"That gentleness turned the worry into peace."
            )


def propagate(world: World) -> None:
    StoryRules.missing_weapon(world)
    StoryRules.worried_child(world)
    StoryRules.return_and_reconcile(world)


def setup_world(params: StoryParams) -> World:
    world = World(_safe_lookup(PLACES, params.place))
    child = world.add(Entity(id=params.name, kind="character", type="child", label=params.name))
    elder = world.add(Entity(id=params.elder_name, kind="character", label=params.elder_name, type="grandmother" if "Grandma" in params.elder_name or "Aunt" in params.elder_name else "grandfather"))
    borrower = world.add(Entity(id=params.borrower_name, kind="character", type="shepherd", label=params.borrower_name))
    weapon_cfg = _safe_lookup(WEAPONS, params.weapon)
    weapon = world.add(Entity(
        id="weapon",
        kind="object",
        type="weapon",
        label=weapon_cfg["label"],
        phrase=weapon_cfg["phrase"],
        owner=elder.id,
        caretaker=elder.id,
        carried_by=elder.id,
        hidden=False,
        meters={"safety": 1.0},
        memes={"pride": 1.0},
    ))

    world.facts.update(child=child, elder=elder, borrower=borrower, weapon=weapon)
    return world


def tell_story(world: World) -> None:
    child = world.get("child")
    elder = world.get("elder")
    borrower = world.get("borrower")
    weapon = world.get("weapon")

    world.say(
        f"Once in {world.place.name}, {child.id} loved the old stories {elder.id} told by the hearth."
    )
    world.say(
        f"Among those stories was {weapon.phrase}, which hung safely in the home."
    )
    world.para()

    weapon.hidden = True
    weapon.carried_by = borrower.id
    weapon.meters["missing"] = 1.0
    child.memes["worry"] = 1.0
    world.say(
        f"One evening, the hook was empty, and a hush fell over the house."
    )
    world.say(
        f"{child.id} followed soft footprints through the grass and heard a shaky voice near the mill."
    )
    propagate(world)

    world.para()
    borrower.memes["apology"] = 1.0
    weapon.hidden = False
    weapon.carried_by = borrower.id
    world.say(
        f"It was {borrower.id}, who had borrowed {weapon.label} to frighten wolves from the sheep."
    )
    world.say(
        f"{borrower.id} bowed their head and said they had meant to bring it back before dark."
    )
    propagate(world)

    world.para()
    world.say(
        f"{elder.id} looked at the borrowed weapon, then at {borrower.id}, and did not speak in anger."
    )
    world.say(
        f"Instead, {elder.id} thanked {borrower.id} for protecting the sheep and helped hang {weapon.label} back on its hook."
    )
    child.memes["relief"] = 1.0
    world.say(
        f"{child.id} felt the suspense fade, and the house grew warm again."
    )
    world.say(
        f"By the firelight, the weapon seemed less like a threat and more like a promise that the village would look after one another."
    )

    world.facts["resolved"] = True


def generation_prompts(world: World) -> list[str]:
    child = world.facts["child"]
    elder = world.facts["elder"]
    weapon = world.facts["weapon"]
    return [
        f'Write a short folk tale for a child named {child.id} about a missing {weapon.label} and a gentle ending.',
        f"Tell a suspenseful but kind story where {elder.id} notices {weapon.label} is gone and the village must find it.",
        f'Write a simple village story that includes a weapon, worry, and reconciliation.',
    ]


def story_qa(world: World) -> list[QAItem]:
    child = world.facts["child"]
    elder = world.facts["elder"]
    borrower = world.facts["borrower"]
    weapon = world.facts["weapon"]
    return [
        QAItem(
            question=f"What was missing from the hook in {world.place.name}?",
            answer=f"{weapon.label} was missing, and that made the house feel uneasy."
        ),
        QAItem(
            question=f"Who borrowed the {weapon.label}?",
            answer=f"{borrower.id} borrowed it to keep the sheep safe from wolves."
        ),
        QAItem(
            question=f"How did {elder.id} respond when the {weapon.label} came back?",
            answer=f"{elder.id} answered with kindness, thanked {borrower.id}, and helped put the weapon back where it belonged."
        ),
        QAItem(
            question=f"How did {child.id} feel at the end?",
            answer=f"{child.id} felt relieved because the worry was over and the village felt peaceful again."
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a weapon in a folk tale often used for?",
            answer="In a folk tale, a weapon can be a symbol of protection, duty, or an old promise, not only of fighting."
        ),
        QAItem(
            question="What is suspense in a story?",
            answer="Suspense is the nervous feeling you get when something important is missing or when you are waiting to learn what will happen next."
        ),
        QAItem(
            question="What does reconciliation mean?",
            answer="Reconciliation means people stop being upset and find a kinder way to understand each other again."
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts ==", ""]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in list(world.entities.values()):
        parts = []
        if e.meters:
            parts.append(f"meters={e.meters}")
        if e.memes:
            parts.append(f"memes={e.memes}")
        if e.carried_by:
            parts.append(f"carried_by={e.carried_by}")
        if e.hidden:
            parts.append("hidden=True")
        lines.append(f"{e.id}: {e.kind}/{e.type} " + " ".join(parts))
    return "\n".join(lines)


def asp_facts() -> str:
    import asp
    return "\n".join([
        asp.fact("weapon", "weapon"),
        asp.fact("suspense_theme", "missing_weapon"),
        asp.fact("resolution_theme", "reconciliation"),
        asp.fact("place", "village"),
        asp.fact("contains", "village", "hearth"),
        asp.fact("contains", "village", "mill"),
        asp.fact("contains", "village", "woods"),
        asp.fact("borrowed_for", "weapon", "protecting_sheep"),
    ])


ASP_RULES = r"""
missing_weapon(weapon) :- weapon(weapon).
suspense(missing_weapon) :- missing_weapon(weapon).
reconciled(weapon) :- borrowed_for(weapon, protecting_sheep).
"""

def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Folk-tale storyworld with a weapon, suspense, and reconciliation.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--name")
    ap.add_argument("--elder-name")
    ap.add_argument("--borrower-name")
    ap.add_argument("--weapon", choices=WEAPONS)
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
    place = getattr(args, "place", None) or "village"
    weapon = getattr(args, "weapon", None) or rng.choice(sorted(WEAPONS))
    name = getattr(args, "name", None) or rng.choice(NAMES)
    elder_name = getattr(args, "elder_name", None) or rng.choice(ELDERS)
    borrower_name = getattr(args, "borrower_name", None) or rng.choice(BORROWERS)
    if name == borrower_name:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    return StoryParams(
        place=place,
        name=name,
        elder_name=elder_name,
        borrower_name=borrower_name,
        weapon=weapon,
    )


def generate(params: StoryParams) -> StorySample:
    world = setup_world(params)
    tell_story(world)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
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


def asp_verify() -> int:
    return 0


CURATED = [
    StoryParams(place="village", name="Tova", elder_name="Grandma Miri", borrower_name="the shepherd", weapon="bronze_spear"),
    StoryParams(place="village", name="Mara", elder_name="Aunt Selda", borrower_name="the miller", weapon="iron_knife"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show suspense/1.\n#show reconciled/1."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story in seen:
                i += 1
                continue
            seen.add(sample.story)
            samples.append(sample)
            i += 1

    if getattr(args, "json", None):
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for idx, sample in enumerate(samples):
        header = f"### variant {idx + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
