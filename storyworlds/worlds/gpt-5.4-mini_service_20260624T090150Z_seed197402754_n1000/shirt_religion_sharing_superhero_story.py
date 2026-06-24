#!/usr/bin/env python3
"""
storyworlds/worlds/shirt_religion_sharing_superhero_story.py
============================================================

A small story world about a young superhero who shares a special shirt for a
religious celebration, then learns that sharing can help everyone feel included.

The story premise:
- A child loves a bright superhero shirt.
- A religion-related gathering is coming up.
- Someone else needs the shirt for the shared event.
- The hero feels a tug of possessiveness, then chooses sharing.
- The ending shows the shirt worn and the mood changed.

This world keeps the prose concrete and state-driven:
- physical meters: shirt.clean, shirt.worn, shirt.shared, shirt.mended
- emotional memes: pride, worry, generosity, relief, belonging

The story is intentionally small and classical: setup, tension, turn, resolution.
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

    helper: object | None = None
    hero: object | None = None
    shirt: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def noun(self) -> str:
        return self.label or self.type

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
    place: str = "the little chapel hall"
    indoors: bool = True
    affords: set[str] = field(default_factory=lambda: {"sharing"})
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
class ShirtCfg:
    label: str = "superhero shirt"
    phrase: str = "a bright superhero shirt with a bold star on the chest"
    color: str = "bright blue"
    symbol: str = "star"
    kind: str = "shirt"
    SHIRT: object | None = None
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
    shirt: str
    hero_name: str
    hero_gender: str
    helper_name: str
    helper_gender: str
    faith_word: str
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


def make_defaults() -> Setting:
    return Setting()


SETTING = make_defaults()
SHIRT = ShirtCfg()

HERO_NAMES = ["Maya", "Noah", "Lina", "Eli", "Nora", "Tess", "Kai", "Zoe"]
HELPER_NAMES = ["Ari", "Mila", "Jonah", "Rosa", "Finn", "Leah"]
FAITH_WORDS = ["church", "temple", "mosque", "synagogue", "prayer", "service", "festival"]


def hero_pronoun_word(gender: str, case: str = "subject") -> str:
    if gender == "girl":
        return {"subject": "she", "object": "her", "possessive": "her"}[case]
    if gender == "boy":
        return {"subject": "he", "object": "him", "possessive": "his"}[case]
    return {"subject": "they", "object": "them", "possessive": "their"}[case]


def valid_story(params: StoryParams) -> bool:
    return bool(params.place and params.shirt and params.hero_name and params.helper_name)


ASP_RULES = r"""
% A shirt can be shared when two kids want it for one event.
shared_story(P) :- place(P), shirt(S), event(E), shareable(S,E).

% A story is reasonable if the shirt is actually the thing being shared.
shareable(S,E) :- shirt(S), uses_for_event(S,E).

% The hero's worry is justified when the helper also needs the shirt.
needs_shirt(H) :- helper(H), wants_to_wear(H,S), shirt(S).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    lines.append(asp.fact("place", "chapel_hall"))
    lines.append(asp.fact("shirt", "superhero_shirt"))
    lines.append(asp.fact("event", "faith_day"))
    lines.append(asp.fact("uses_for_event", "superhero_shirt", "faith_day"))
    lines.append(asp.fact("helper", "helper_child"))
    lines.append(asp.fact("wants_to_wear", "helper_child", "superhero_shirt"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def _hero(world: World) -> Entity:
    return world.get("hero")


def _helper(world: World) -> Entity:
    return world.get("helper")


def _shirt(world: World) -> Entity:
    return world.get("shirt")


def start_story(world: World) -> None:
    hero = _hero(world)
    helper = _helper(world)
    shirt = _shirt(world)
    world.say(
        f"{hero.id} was a little superhero who loved {shirt.phrase}. "
        f"It looked strong and shiny, like it could help {hero.pronoun('object')} do anything."
    )
    world.say(
        f"At the same time, {helper.id} was getting ready for a special {world.facts['faith_word']} day at "
        f"{world.setting.place}."
    )


def conflict(world: World) -> None:
    hero = _hero(world)
    helper = _helper(world)
    shirt = _shirt(world)
    hero.memes["pride"] += 1
    hero.memes["worry"] += 1
    shirt.meters["worn"] = 1
    world.say(
        f"{hero.id} wanted to keep the {shirt.label} all to {hero.pronoun('object')}self, "
        f"because {hero.pronoun('subject')} felt extra brave in it."
    )
    world.say(
        f"But {helper.id} softly asked to borrow it for the {world.facts['faith_word']} gathering, "
        f"because the shirt matched the event and made {helper.pronoun('object')} feel ready."
    )
    world.say(
        f"{hero.id} looked down at the shirt and felt a little tight inside. "
        f"That was the hard part of sharing."
    )


def turn_to_sharing(world: World) -> None:
    hero = _hero(world)
    helper = _helper(world)
    shirt = _shirt(world)
    hero.memes["generosity"] += 1
    hero.memes["worry"] = 0
    helper.memes["belonging"] += 1
    shirt.meters["shared"] += 1
    shirt.meters["clean"] += 1
    world.say(
        f"Then {hero.id} took a breath and smiled. "
        f'"You can wear it first," {hero.pronoun("subject")} said. "Sharing makes it even better."'
    )
    world.say(
        f"{helper.id} hugged the shirt carefully and promised to return it neat and folded."
    )


def ending(world: World) -> None:
    hero = _hero(world)
    helper = _helper(world)
    shirt = _shirt(world)
    hero.memes["relief"] += 1
    hero.memes["belonging"] += 1
    helper.memes["relief"] += 1
    shirt.meters["mended"] += 1
    world.say(
        f"At the {world.facts['faith_word']} gathering, {helper.id} wore the {shirt.label} with a proud grin, "
        f"and {hero.id} stood beside {helper.pronoun('object')} like a tiny sidekick."
    )
    world.say(
        f"The shirt still looked bright and strong, and now it carried two happy stories instead of one."
    )


def tell_story(params: StoryParams) -> World:
    world = World(SETTING)
    hero = world.add(Entity(
        id=params.hero_name,
        kind="character",
        type=params.hero_gender,
        meters={"clean": 0.0},
        memes={"pride": 0.0, "worry": 0.0, "generosity": 0.0, "relief": 0.0, "belonging": 0.0},
    ))
    helper = world.add(Entity(
        id=params.helper_name,
        kind="character",
        type=params.helper_gender,
        meters={"clean": 0.0},
        memes={"belonging": 0.0, "relief": 0.0},
    ))
    shirt = world.add(Entity(
        id="shirt",
        kind="thing",
        type="shirt",
        label=SHIRT.label,
        phrase=SHIRT.phrase,
        owner=hero.id,
        caretaker=hero.id,
        meters={"clean": 1.0, "worn": 0.0, "shared": 0.0, "mended": 0.0},
    ))
    world.facts.update(
        hero=hero,
        helper=helper,
        shirt=shirt,
        faith_word=params.faith_word,
        place=params.place,
    )
    start_story(world)
    world.para()
    conflict(world)
    world.para()
    turn_to_sharing(world)
    ending(world)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    helper = _safe_fact(world, f, "helper")
    shirt = _safe_fact(world, f, "shirt")
    return [
        f"Write a child-friendly superhero story about {hero.id} and a {shirt.label} that gets shared.",
        f"Tell a gentle story where {helper.id} needs a {shirt.label} for a {f['faith_word']} event and {hero.id} learns to share.",
        "Write a short superhero story with a bright shirt, a respectful religion setting, and a happy sharing ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    helper = _safe_fact(world, f, "helper")
    shirt = _safe_fact(world, f, "shirt")
    faith = _safe_fact(world, f, "faith_word")
    return [
        QAItem(
            question=f"Who wanted to wear the {shirt.label} at first?",
            answer=f"{hero.id} wanted to keep the {shirt.label} because it made {hero.pronoun('subject')} feel brave.",
        ),
        QAItem(
            question=f"Why did {helper.id} ask for the shirt?",
            answer=f"{helper.id} needed it for the special {faith} gathering at {f['place']}.",
        ),
        QAItem(
            question=f"What changed when the two children chose sharing?",
            answer=f"The shirt became shared, and both children ended the story feeling calmer and happier.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"{helper.id} wore the {shirt.label} to the event, and {hero.id} stood nearby feeling proud and relieved.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is sharing?",
            answer="Sharing means letting someone else use or enjoy something too, instead of keeping it all for yourself.",
        ),
        QAItem(
            question="What is a shirt?",
            answer="A shirt is a piece of clothing that covers the upper body.",
        ),
        QAItem(
            question="What is a religion gathering?",
            answer="A religion gathering is a time when people come together for prayer, worship, or another special event in their faith.",
        ),
        QAItem(
            question="Why can sharing feel kind?",
            answer="Sharing can feel kind because it helps another person, and it shows that you care about them.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story QA ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World QA ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"  {e.id:8} ({e.type:9}) meters={meters} memes={memes}")
    return "\n".join(lines)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if getattr(args, "shirt", None) and getattr(args, "shirt", None) != "superhero":
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place = getattr(args, "place", None) or "the little chapel hall"
    hero_gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    helper_gender = "boy" if hero_gender == "girl" else "girl"
    hero_name = getattr(args, "name", None) or rng.choice(HERO_NAMES)
    helper_name = getattr(args, "helper", None) or rng.choice([n for n in HELPER_NAMES if n != hero_name])
    faith_word = getattr(args, "faith", None) or rng.choice(FAITH_WORDS)
    return StoryParams(
        place=place,
        shirt="superhero",
        hero_name=hero_name,
        hero_gender=hero_gender,
        helper_name=helper_name,
        helper_gender=helper_gender,
        faith_word=faith_word,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell_story(params)
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A superhero storyworld about sharing a special shirt.")
    ap.add_argument("--place")
    ap.add_argument("--shirt")
    ap.add_argument("--name")
    ap.add_argument("--helper")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--faith")
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


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid/1."))
    atoms = asp.atoms(model, "valid")
    expected = [("shirt_religion_sharing_superhero_story",)]
    return 0 if atoms == expected else 1


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/1."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        params = StoryParams(
            place="the little chapel hall",
            shirt="superhero",
            hero_name="Maya",
            hero_gender="girl",
            helper_name="Ari",
            helper_gender="boy",
            faith_word="service",
        )
        samples = [generate(params)]
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
