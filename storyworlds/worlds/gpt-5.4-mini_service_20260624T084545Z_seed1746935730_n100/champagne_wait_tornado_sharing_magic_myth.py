#!/usr/bin/env python3
"""
A small mythic storyworld about sharing champagne, waiting out a tornado, and
using magic to turn one feast into many cups for everyone.

Seed image:
- In a bright old story place, a child and a keeper bring out champagne for a
  festival.
- A tornado begins to whirl nearby, and the keeper says to wait.
- The child uses a little magic and a spirit of sharing so the drink can be
  offered safely to all after the storm passes.
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
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    hero: object | None = None
    keeper: object | None = None
    prize: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
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
    place: str
    windbreak: bool
    affords_wait: bool = True
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
class ObjectCfg:
    label: str
    phrase: str
    type: str
    plural: bool = False
    shared_by: int = 1
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
class StoryParams:
    place: str
    object: str
    hero_name: str
    hero_type: str
    keeper_type: str
    seed: Optional[int] = None
    params: object | None = None
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


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
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
    "village_square": Setting(place="the village square", windbreak=False),
    "stone_circle": Setting(place="the stone circle", windbreak=True),
    "harbor_hall": Setting(place="the harbor hall", windbreak=True),
}

OBJECTS = {
    "champagne": ObjectCfg(
        label="champagne",
        phrase="a cool bottle of champagne for the feast",
        type="bottle",
        plural=False,
        shared_by=8,
    ),
    "cups": ObjectCfg(
        label="cups",
        phrase="a silver tray of small cups for sharing",
        type="cups",
        plural=True,
        shared_by=12,
    ),
}

HERO_NAMES = ["Ari", "Mina", "Sora", "Lio", "Nia", "Tala", "Orin", "Eda"]
TRAITS = ["brave", "gentle", "curious", "bright", "kind"]
TITLES = {
    "girl": "maiden",
    "boy": "boy",
    "mother": "mother",
    "father": "father",
}

THRESHOLD = 1.0


def reasonableness_gate(setting: Setting, obj: ObjectCfg) -> bool:
    return True


ASP_RULES = r"""
selected_place(P) :- place(P).
selected_object(O) :- object(O).
valid_story(P,O) :- place(P), object(O).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("place", pid))
        if s.windbreak:
            lines.append(asp.fact("windbreak", pid))
    for oid in OBJECTS:
        lines.append(asp.fact("object", oid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def tell(setting: Setting, obj_cfg: ObjectCfg, hero_name: str, hero_type: str, keeper_type: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type))
    keeper = world.add(Entity(id="Keeper", kind="character", type=keeper_type, label="the keeper"))
    prize = world.add(Entity(
        id="champagne",
        type=obj_cfg.type,
        label=obj_cfg.label,
        phrase=obj_cfg.phrase,
        owner=hero.id,
        caretaker=keeper.id,
        plural=obj_cfg.plural,
    ))

    # setup
    hero.memes["wonder"] += 1
    world.say(f"In {setting.place}, {hero.id} was a little {_safe_lookup(TITLES, hero_type)} who loved festival light.")
    world.say(f"{hero.pronoun().capitalize()} had {prize.phrase}, and {hero.id} hoped to share {prize.it()} with everyone.")
    world.say(f"The keeper smiled because sharing was one of the oldest blessings in that place.")

    # rising storm
    world.para()
    hero.memes["desire"] += 1
    world.say(f"Then a tornado began to curl over the fields, dark as a spinning rope.")
    hero.meters["fear"] += 1
    keeper.memes["worry"] += 1
    world.say(f"{hero.id} wanted to open the champagne at once, but the keeper raised a hand and said, \"Wait.\"")
    world.say(f'"We must wait until the wind has passed, or the feast will fly apart."')

    # tension
    world.para()
    hero.memes["impatience"] += 1
    world.say(f"{hero.id} waited beside the stone steps and listened to the tornado thrum in the distance.")
    world.say(f"To keep the joy from slipping away, {hero.id} held the bottle close and thought of a kinder spell.")

    # resolution
    world.para()
    hero.memes["sharing"] += 1
    hero.memes["magic"] += 1
    if setting.windbreak:
        world.say(f"When the tornado drifted past the hills, the air grew still behind the old stones.")
    else:
        world.say(f"When the tornado spun on, it missed the sheltered square and moved away at last.")
    world.say(f"{hero.id} whispered a magic word, and the single bottle became many bright cups for sharing.")
    world.say(f"The keeper laughed, and together they poured the champagne for the children, the singers, and the tired old folk.")
    world.say(f"At the end, the feast was calm, the cups were full, and the story of waiting had become a story of sharing.")

    world.facts.update(hero=hero, keeper=keeper, prize=prize, setting=setting, obj_cfg=obj_cfg)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    return [
        "Write a tiny myth about champagne, waiting, and a tornado, with a magic turn that ends in sharing.",
        f"Tell a child-friendly story where {hero.id} wants to share champagne, but a tornado makes everyone wait.",
        "Write a gentle legend in which magic helps one feast become enough for many people after the storm.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, keeper, prize, setting = f["hero"], f["keeper"], f["prize"], f["setting"]
    return [
        QAItem(
            question=f"Who wanted to share the champagne in {setting.place}?",
            answer=f"{hero.id} wanted to share the champagne, and the keeper helped keep everyone safe.",
        ),
        QAItem(
            question="Why did they have to wait?",
            answer="They had to wait because a tornado was spinning nearby, and the keeper did not want the feast to fly apart.",
        ),
        QAItem(
            question="What changed at the end of the story?",
            answer="At the end, the tornado had passed, magic turned one bottle into many cups, and the champagne was shared with everyone.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is champagne?",
            answer="Champagne is a sparkling drink with bubbles. People often pour it for celebrations and special moments.",
        ),
        QAItem(
            question="What does it mean to wait?",
            answer="To wait means to pause and stay still for a while until it is safe or the right time to do something.",
        ),
        QAItem(
            question="What is a tornado?",
            answer="A tornado is a very strong spinning wind that can move across the ground and blow things around.",
        ),
        QAItem(
            question="What is sharing?",
            answer="Sharing means letting other people use, enjoy, or have part of something too.",
        ),
        QAItem(
            question="What is magic in stories?",
            answer="Magic is a story power that can do amazing things that do not happen in everyday life.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story questions ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== World knowledge questions ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    out = ["--- world trace ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        out.append(f"{e.id}: {e.type} {' '.join(bits)}")
    return "\n".join(out)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A mythic storyworld about champagne, waiting, tornadoes, sharing, and magic.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--object", dest="object", choices=OBJECTS)
    ap.add_argument("--name", choices=HERO_NAMES)
    ap.add_argument("--hero-type", choices=["girl", "boy"])
    ap.add_argument("--keeper-type", choices=["mother", "father"])
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
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
    obj = getattr(args, "object", None) or rng.choice(list(OBJECTS))
    hero_type = getattr(args, "hero_type", None) or rng.choice(["girl", "boy"])
    keeper_type = getattr(args, "keeper_type", None) or rng.choice(["mother", "father"])
    name = getattr(args, "name", None) or rng.choice(HERO_NAMES)
    if not reasonableness_gate(_safe_lookup(SETTINGS, place), _safe_lookup(OBJECTS, obj)):
        return _fallback_storyparams(args, rng, StoryParams, globals())
    return StoryParams(place=place, object=obj, hero_name=name, hero_type=hero_type, keeper_type=keeper_type)


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.place), _safe_lookup(OBJECTS, params.object), params.hero_name, params.hero_type, params.keeper_type)
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


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = {(p, o) for p in SETTINGS for o in OBJECTS if reasonableness_gate(_safe_lookup(SETTINGS, p), _safe_lookup(OBJECTS, o))}
    cl = set(asp_valid())
    if py == cl:
        print(f"OK: clingo gate matches Python ({len(py)} combos).")
        return 0
    print("MISMATCH:")
    print("python-only:", sorted(py - cl))
    print("clingo-only:", sorted(cl - py))
    return 1


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        print(f"{len(asp_valid())} valid stories:")
        for p, o in asp_valid():
            print(f"  {p} {o}")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        for place in SETTINGS:
            for obj in OBJECTS:
                params = StoryParams(place=place, object=obj, hero_name="Ari", hero_type="girl", keeper_type="mother")
                params.seed = base_seed
                samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 20):
            rng = random.Random(base_seed + i)
            i += 1
            try:
                params = resolve_params(args, rng)
            except StoryError:
                continue
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
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
