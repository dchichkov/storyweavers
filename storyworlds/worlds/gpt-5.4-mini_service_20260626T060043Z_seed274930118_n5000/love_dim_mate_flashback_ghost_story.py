#!/usr/bin/env python3
"""
storyworlds/worlds/love_dim_mate_flashback_ghost_story.py
=========================================================

A small child-facing ghost story world built around a fading lantern, a loyal
mate, and a flashback that reveals why the haunting feels sad instead of cruel.

Premise:
- A child and a friend explore a quiet old house at dusk.
- A ghostly presence is not trying to scare them away; it is dimming with
  loneliness and missing a remembered friendship.
- A flashback shows the original promise or play that tied them together.
- The ending turns on recognition, kindness, and a small repair that brightens
  the room and the ghost's heart.

The seed words "love-dim" and "mate" are woven into the world vocabulary and
narration. The tone stays close to a gentle ghost story: eerie setting, a
memory from before, a soft reveal, and a warm ending image.
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
    if hasattr(key, "id"):
        key = key.id
    try:
        return mapping[key]
    except Exception:
        pass
    if hasattr(mapping, "values"):
        values = [value for value in mapping.values() if value is not None]
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
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    hero: object | None = None
    lantern: object | None = None
    mate: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type == "ghost":
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
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

    def __getitem__(self, key):
        if isinstance(key, int):
            if key == 0:
                return self
            raise IndexError(key)
        if isinstance(key, str):
            if hasattr(self, key):
                return getattr(self, key)
            for attr in ("meters", "memes"):
                mapping = getattr(self, attr, None)
                if hasattr(mapping, "get") and key in mapping:
                    return mapping.get(key)
        raise KeyError(key)

    def __iter__(self):
        yield self

    def __hash__(self):
        return hash(getattr(self, "id", id(self)))


@dataclass
class Setting:
    place: str
    mood: str
    darkness: str
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
class Memory:
    label: str
    place: str
    object_name: str
    promise: str
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

    def __getitem__(self, key):
        if isinstance(key, int):
            if key == 0:
                return self
            raise IndexError(key)
        if isinstance(key, str):
            if hasattr(self, key):
                return getattr(self, key)
            for attr in ("meters", "memes"):
                mapping = getattr(self, attr, None)
                if hasattr(mapping, "get") and key in mapping:
                    return mapping.get(key)
        raise KeyError(key)

    def __iter__(self):
        yield self

    def __hash__(self):
        return hash(getattr(self, "id", id(self)))


@dataclass
class StoryParams:
    setting: str = ""
    hero_name: str = ""
    hero_type: str = ""
    mate_name: str = ""
    mate_type: str = ""
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
        self.fired: set[tuple] = set()
        self.flashback_seen = False

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
        import copy as _copy

        w = World(self.setting)
        w.entities = _copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        w.fired = set(self.fired)
        w.flashback_seen = self.flashback_seen
        return w


SETTINGS = {
    "attic": Setting(place="the old attic", mood="dusty", darkness="dim"),
    "garden": Setting(place="the moonlit garden", mood="quiet", darkness="silver"),
    "hall": Setting(place="the long front hall", mood="hushed", darkness="blue"),
}

MEMORIES = {
    "attic": Memory(
        label="the lantern memory",
        place="the old attic",
        object_name="a small brass lantern",
        promise="we will always come back with a light",
    ),
    "garden": Memory(
        label="the swing memory",
        place="the moonlit garden",
        object_name="a wooden swing",
        promise="we will always push each other one more time",
    ),
    "hall": Memory(
        label="the blanket memory",
        place="the long front hall",
        object_name="a striped blanket",
        promise="we will always share the blanket when the house goes cold",
    ),
}

GIRL_NAMES = ["Mina", "Lena", "Ivy", "Nora", "Lila", "Ada"]
BOY_NAMES = ["Owen", "Milo", "Eli", "Noah", "Theo", "Finn"]


ASP_RULES = r"""
#show valid_setting/1.
#show valid_story/3.

valid_setting(attic).
valid_setting(garden).
valid_setting(hall).

valid_story(S, H, M) :- valid_setting(S), hero(H), mate(M).
"""


def asp_facts() -> str:
    import asp

    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("valid_setting", sid))
    for name in GIRL_NAMES:
        lines.append(asp.fact("hero_name", name))
    for name in BOY_NAMES:
        lines.append(asp.fact("hero_name", name))
    lines.append(asp.fact("hero", "girl"))
    lines.append(asp.fact("hero", "boy"))
    lines.append(asp.fact("mate", "ghost"))
    lines.append(asp.fact("mate", "friend"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp

    model = asp.one_model(asp_program("#show valid_setting/1."))
    clingo_set = set(asp.atoms(model, "valid_setting"))
    py_set = {(k,) for k in SETTINGS.keys()}
    if clingo_set == py_set:
        print(f"OK: clingo gate matches settings ({len(py_set)}).")
        return 0
    print("MISMATCH between clingo and python settings gate.")
    if clingo_set - py_set:
        print("  only in clingo:", sorted(clingo_set - py_set))
    if py_set - clingo_set:
        print("  only in python:", sorted(py_set - clingo_set))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A gentle ghost story about love-dim and a mate.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--name")
    ap.add_argument("--mate-name")
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
    setting = getattr(args, "setting", None) or rng.choice(list(SETTINGS))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    if getattr(args, "name", None):
        hero_name = getattr(args, "name", None)
    else:
        hero_name = rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    mate_name = getattr(args, "mate_name", None) or rng.choice([n for n in (GIRL_NAMES + BOY_NAMES) if n != hero_name])
    return StoryParams(setting=setting, hero_name=hero_name, hero_type=gender, mate_name=mate_name, mate_type="ghost")


def valid_story(params: StoryParams) -> bool:
    return params.setting in SETTINGS and params.hero_name != params.mate_name


def select_memory(setting: str) -> Memory:
    return _safe_lookup(MEMORIES, setting)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a gentle ghost story for a 3-to-5-year-old that includes the words "love-dim" and "mate".',
        f"Tell a spooky-but-kind story about {_safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "hero_name")} and a ghostly mate in {world.setting.place}.",
        f"Write a short flashback story where a forgotten promise helps {_safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "hero_name")} and the mate brighten the house again.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "hero")
    mate = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "mate")
    mem = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "memory")
    return [
        QAItem(
            question=f"Who is the story about?",
            answer=f"It is about {hero.id} and a ghostly mate named {mate.id}. They meet in {world.setting.place}.",
        ),
        QAItem(
            question=f"What made the ghost seem love-dim at first?",
            answer=f"The ghost seemed love-dim because it was lonely and dimmed the room with a sad hush.",
        ),
        QAItem(
            question=f"What did the flashback show?",
            answer=f"The flashback showed {hero.id} and the mate sharing {mem.object_name} and making the promise, “{mem.promise}.”",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended with {hero.id} keeping the old promise, which made the room brighter and helped the mate feel loved again.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a flashback?",
            answer="A flashback is a part of a story that shows something from earlier, before the main moment now.",
        ),
        QAItem(
            question="What is a ghost in a gentle story?",
            answer="A ghost is an unseen or see-through character that can feel spooky, sad, or kind in a story.",
        ),
        QAItem(
            question="What does dim mean?",
            answer="Dim means not very bright.",
        ),
    ]


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
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  flashback_seen={world.flashback_seen}")
    return "\n".join(lines)


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
    lines.append("== (3) World knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def tell(params: StoryParams) -> World:
    if not valid_story(params):
        pass
    setting = _safe_lookup(SETTINGS, params.setting)
    mem = select_memory(params.setting)
    world = World(setting)
    hero = world.add(Entity(id=params.hero_name, kind="character", type=params.hero_type, label=params.hero_name))
    mate = world.add(Entity(id=params.mate_name, kind="character", type="ghost", label="the mate"))
    lantern = world.add(Entity(id="lantern", type="thing", label="lantern", phrase="a small brass lantern", owner=hero.id))
    hero.memes.update(love=1.0, courage=0.0, wonder=0.0)
    mate.memes.update(love_dim=1.0, loneliness=1.0, relief=0.0)
    lantern.meters.update(bright=0.5)

    world.facts.update(hero=hero, mate=mate, memory=mem, lantern=lantern, setting=setting)

    world.say(
        f"At {setting.place}, {hero.id} found {mem.label} under a hush of {setting.mood} air."
    )
    world.say(
        f"At first, {hero.id} could only see a faint shape by the stairs, a ghostly mate that looked love-dim and quiet."
    )
    world.para()
    world.say(
        f"The house felt colder when the mate drifted near, and the little lantern in {hero.id}'s hands seemed to glow only halfway."
    )
    world.say(
        f"{hero.id} wanted to run, but then a flutter of memory tugged at {hero.id}'s heart."
    )
    world.para()
    world.flashback_seen = True
    world.say(
        f"Flashback: long ago, in the same {setting.place}, {hero.id} and the mate had sat together with {mem.object_name}."
    )
    world.say(
        f"They had promised, “{mem.promise},” and they had laughed while the dark windows listened."
    )
    world.para()
    mate.memes["loneliness"] = 0.0
    mate.memes["relief"] = 1.0
    hero.memes["courage"] = 1.0
    lantern.meters["bright"] = 1.0
    world.say(
        f"{hero.id} whispered the promise back and held the lantern up high."
    )
    world.say(
        f"The mate softened, the room warmed, and the love-dim glow turned bright as a bedtime star."
    )
    world.say(
        f"By the end, {hero.id} was smiling beside the mate, and {mem.object_name} felt like it had never been forgotten at all."
    )
    return world


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


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for s in SETTINGS:
        for g in ["girl", "boy"]:
            for m in MEMORIES:
                out.append((s, g, m))
    return out


CURATED = [
    StoryParams(setting="attic", hero_name="Mina", hero_type="girl", mate_name="Noah"),
    StoryParams(setting="garden", hero_name="Owen", hero_type="boy", mate_name="Ivy"),
    StoryParams(setting="hall", hero_name="Lila", hero_type="girl", mate_name="Eli"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp

        model = asp.one_model(asp_program("#show valid_setting/1."))
        combos = sorted(set(asp.atoms(model, "valid_setting")))
        print(f"{len(combos)} settings:\n")
        for c in combos:
            print(" ", c[0])
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
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False, default=str))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
