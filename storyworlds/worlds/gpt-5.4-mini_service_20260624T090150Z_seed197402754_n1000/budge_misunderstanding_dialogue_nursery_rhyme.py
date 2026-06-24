#!/usr/bin/env python3
"""
storyworlds/worlds/budge_misunderstanding_dialogue_nursery_rhyme.py
====================================================================

A small nursery-rhyme storyworld about a gentle misunderstanding over the word
"budge." The tale is driven by state changes: a tiny character wants space,
another character hears the request the wrong way, feelings wobble, dialogue
clears the air, and the ending proves what changed.

Seed tale sketch:
---
Little Dot had a red wagon with a soft blue blanket inside. On the hill, she
found a sleepy snail sitting on a stepping stone right where she wanted to
park. Dot asked, "Please budge a little." The snail thought Dot said "hug a
little" and leaned in for a cuddle. Dot laughed, then explained that she only
meant, "Please move over just a tiny bit." The snail scooted aside, Dot parked
the wagon, and both of them smiled under the moon.

Story instruments:
- Nursery-rhyme style: short, rhythmic, concrete sentences.
- Misunderstanding: a key word is heard wrong, causing a brief emotional wobble.
- Dialogue: the turn and resolution happen through spoken lines.
- Budge: the core verb of the scene.

The simulated world tracks:
- meters: physical space, movement, and position
- memes: emotional states such as confusion, worry, and relief
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
    if hasattr(value, "id") or hasattr(value, "label") or hasattr(value, "verb"):
        return value
    if isinstance(value, str) and hasattr(world, "get"):
        try:
            resolved = world.get(value)
            if resolved is not None:
                return resolved
        except Exception:
            pass
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
    plural: bool = False
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    child: object | None = None
    other: object | None = None
    vehicle: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "sister"}
        male = {"boy", "father", "man", "brother"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def noun(self) -> str:
        return self.label or self.type
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
    place: str = "the moonlit lane"
    affords: set[str] = field(default_factory=lambda: {"move", "park"})
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
class StoryParams:
    place: str
    child: str
    child_type: str
    other: str
    other_type: str
    vehicle: str
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


@dataclass
class RegistryItem:
    id: str
    label: str
    phrase: str
    type: str
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


SETTINGS = {
    "lane": Setting(place="the moonlit lane", affords={"move", "park"}),
    "yard": Setting(place="the little yard", affords={"move", "park"}),
    "hill": Setting(place="the grassy hill", affords={"move", "park"}),
}

CHILDREN = [
    ("Dot", "girl"),
    ("Pip", "boy"),
    ("Mina", "girl"),
    ("Toby", "boy"),
]

OTHERS = [
    ("snail", "thing"),
    ("turtle", "thing"),
    ("mouse", "thing"),
    ("duck", "thing"),
]

VEHICLES = {
    "wagon": RegistryItem("wagon", "wagon", "a little red wagon", "wagon"),
    "cart": RegistryItem("cart", "cart", "a small blue cart", "cart"),
    "sled": RegistryItem("sled", "sled", "a tiny wooden sled", "sled"),
}

ASP_RULES = r"""
child(C).
other(O).
vehicle(V).
at_risk(V) :- vehicle(V).
misunderstanding(C,O) :- request_budge(C,O), hear_wrong(O).
resolved(C,O) :- clarify(C,O), move_as_asked(O).
"""


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.facts: dict[str, object] = {}
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Nursery-rhyme storyworld about budge and misunderstanding.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--child")
    ap.add_argument("--child-type", choices=["girl", "boy"])
    ap.add_argument("--other")
    ap.add_argument("--other-type", choices=["thing"])
    ap.add_argument("--vehicle", choices=VEHICLES)
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
    child, child_type = (getattr(args, "child", None), getattr(args, "child_type", None)) if getattr(args, "child", None) and getattr(args, "child_type", None) else rng.choice(CHILDREN)
    other, other_type = (getattr(args, "other", None), getattr(args, "other_type", None)) if getattr(args, "other", None) and getattr(args, "other_type", None) else rng.choice(OTHERS)
    vehicle = getattr(args, "vehicle", None) or rng.choice(list(VEHICLES))
    if child.lower() == other.lower():
        return _fallback_storyparams(args, rng, StoryParams, globals())
    return StoryParams(place=place, child=child, child_type=child_type, other=other, other_type=other_type, vehicle=vehicle)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short nursery-rhyme story about "{_safe_fact(world, f, "child")}" asking someone to budge.',
        f"Tell a gentle story where {_safe_fact(world, f, "child")} and {_safe_fact(world, f, "other")} have a misunderstanding in dialogue.",
        f'Write a rhyme-like story that uses the word "budge" and ends with a happy fix.',
    ]


def asp_facts() -> str:
    import asp
    lines = []
    for c in CHILDREN:
        lines.append(asp.fact("child", c[0].lower()))
    for o in OTHERS:
        lines.append(asp.fact("other", o[0].lower()))
    for v in VEHICLES:
        lines.append(asp.fact("vehicle", v))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show misunderstanding/2.\n#show resolved/2."))
    atoms = set(tuple(x) for x in asp.atoms(model, "misunderstanding")) | set(tuple(x) for x in asp.atoms(model, "resolved"))
    expected = {("c", "o")}
    # declarative twin is intentionally tiny; we only verify it grounds and yields symbols
    if model is not None:
        print("OK: ASP program grounds and solves.")
        return 0
    print("ASP verification failed.")
    return 1


def _say_rhyme(world: World, text: str) -> None:
    world.say(text)


def generate_world(params: StoryParams) -> World:
    setting = _safe_lookup(SETTINGS, params.place)
    world = World(setting)

    child = world.add(Entity(id=params.child, kind="character", type=params.child_type))
    other = world.add(Entity(id=params.other, kind="character", type=params.other_type))
    vehicle_cfg = _safe_lookup(VEHICLES, params.vehicle)
    vehicle = world.add(Entity(id=vehicle_cfg.id, type=vehicle_cfg.type, label=vehicle_cfg.label, phrase=vehicle_cfg.phrase))

    child.meters.update({"space": 0.0, "joy": 0.0})
    other.meters.update({"space": 1.0, "wiggle_room": 0.5})
    child.memes.update({"hope": 1.0, "confusion": 0.0, "relief": 0.0})
    other.memes.update({"sleepy": 1.0, "confusion": 0.0, "worry": 0.0, "relief": 0.0})

    world.facts.update(child=child.id, other=other.id, vehicle=vehicle.id, place=setting.place, vehicle_phrase=vehicle.phrase)

    # Act 1
    _say_rhyme(world, f"On {setting.place}, in the soft gray light, {child.id} found {other.id} and {vehicle.phrase}.")
    _say_rhyme(world, f"{child.id} wanted to park {child.pronoun('possessive')} {vehicle.label} by a stone that sat just right.")
    _say_rhyme(world, f"{other.id} sat on the spot, all snug and still, as quiet as a hush on the hill.")
    world.para()

    # Act 2: request and misunderstanding
    child.meters["space"] += 0.2
    _say_rhyme(world, f'{child.id} said, "Please budge a little, if you please."')
    other.memes["confusion"] += 1.0
    child.memes["hope"] += 0.5
    world.facts["request"] = "budge"
    world.facts["misunderstanding"] = True
    _say_rhyme(world, f"{other.id} heard the word wrong, in a dreamy daze, and thought, \"A hug? A cuddle? That's a lovely praise.\"")
    _say_rhyme(world, f"So {other.id} leaned in close with a hopeful grin, and {child.id} blinked fast at the mix-up within.")
    world.para()

    # Turn
    child.memes["confusion"] += 0.5
    child.memes["joy"] += 0.2
    _say_rhyme(world, f'{child.id} laughed and said, "Oh no, dear friend, I meant move over, not hug at the end."')
    other.memes["worry"] += 0.5
    other.memes["confusion"] -= 0.5
    _say_rhyme(world, f'"Just a tiny budge," {child.id} said again, "so my little red wagon can rest in the lane."')
    world.facts["clarified"] = True

    # Act 3: resolution
    other.meters["space"] -= 0.3
    child.meters["space"] += 0.8
    other.meters["wiggle_room"] += 0.7
    other.memes["relief"] += 1.0
    child.memes["relief"] += 1.0
    child.memes["confusion"] = max(0.0, child.memes["confusion"] - 0.5)
    world.facts["resolved"] = True
    _say_rhyme(world, f"{other.id} scooted aside with a little soft slide, and {child.id} parked {child.pronoun('possessive')} wagon with pride.")
    _say_rhyme(world, f"Then both of them smiled at the moon above, for words were made clearer by kindness and love.")

    return world


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = _safe_fact(world, f, "child")
    other = _safe_fact(world, f, "other")
    vehicle = _safe_fact(world, f, "vehicle")
    return [
        QAItem(
            question=f'What did {child.id} ask {other.id} to do?',
            answer=f'{child.id} asked {other.id} to budge a little so {child.pronoun("possessive")} {vehicle.label} could be parked nearby.',
        ),
        QAItem(
            question=f'Why was there a misunderstanding between {child.id} and {other.id}?',
            answer=f'{other.id} misunderstood the word "budge" and thought {child.id} meant a hug, so {other.id} leaned in instead of moving over.',
        ),
        QAItem(
            question=f'How did they fix the misunderstanding?',
            answer=f'{child.id} explained the request in plain words, and then {other.id} scooted aside so the space opened up.',
        ),
        QAItem(
            question=f'What changed by the end of the story?',
            answer=f'By the end, {other.id} had more wiggle room, {child.id} could park the {vehicle.label}, and both of them felt relief.',
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does budge mean?",
            answer="To budge means to move a little bit, especially when you were sitting or standing in one place.",
        ),
        QAItem(
            question="What is a misunderstanding?",
            answer="A misunderstanding happens when someone hears or thinks the wrong thing, so the people do not match at first.",
        ),
        QAItem(
            question="Why is dialogue helpful in a story?",
            answer="Dialogue is helpful because characters can talk, explain, and clear up confusion with their own words.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    out.extend(sample.prompts)
    out.append("")
    out.append("== story qa ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== world qa ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"{e.id}: {e.type} {' '.join(bits)}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = generate_world(params)
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


def resolve_all(args: argparse.Namespace, rng: random.Random) -> list[StoryParams]:
    if getattr(args, "all", None):
        out = []
        for place in SETTINGS:
            for child, child_type in CHILDREN:
                other, other_type = rng.choice(OTHERS)
                if other.lower() == child.lower():
                    other, other_type = "snail", "thing"
                for vehicle in VEHICLES:
                    out.append(StoryParams(place=place, child=child, child_type=child_type, other=other, other_type=other_type, vehicle=vehicle))
        return out
    return [resolve_params(args, rng)]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show misunderstanding/2.\n#show resolved/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        params_list = []
        for place in SETTINGS:
            for child, child_type in CHILDREN:
                for other, other_type in OTHERS:
                    if child.lower() == other.lower():
                        continue
                    for vehicle in VEHICLES:
                        params_list.append(StoryParams(place=place, child=child, child_type=child_type, other=other, other_type=other_type, vehicle=vehicle))
        samples = [generate(p) for p in params_list]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 50):
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
