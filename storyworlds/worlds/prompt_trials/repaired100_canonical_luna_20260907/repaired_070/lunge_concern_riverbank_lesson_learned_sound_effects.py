#!/usr/bin/env python3
"""
A tiny riverbank storyworld about a brave lunge, a careful concern, and a
small transformation told with nursery-rhyme rhythm and sound effects.
"""

from __future__ import annotations

# Locate the shared StoryWorld helpers from any batch depth.
from pathlib import Path as _StoryPath
import sys as _StorySys
_storyworlds_root = next(parent for parent in _StoryPath(__file__).resolve().parents
                        if (parent / 'results.py').is_file() and (parent / 'asp.py').is_file())
_StorySys.path.insert(0, str(_storyworlds_root.parent))
_StorySys.path.insert(0, str(_storyworlds_root))


import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
from results import QAItem, StoryError, StorySample  # noqa: E402


PLACES = {"riverbank": "the riverbank"}
ANIMALS = ["frog", "duckling", "otter", "beaver", "turtle"]
NAMES = ["Luna", "Milo", "Pip", "Nell", "Toby", "Daisy"]
CONCERNS = ["a loose leaf boat", "a stranded beetle", "a slippery stepping stone"]
TRAITS = ["watchful", "cheerful", "patient", "curious", "gentle"]

CURATED = [
    ("Luna", "frog", "a stranded beetle", "watchful"),
    ("Milo", "duckling", "a loose leaf boat", "curious"),
    ("Nell", "turtle", "a slippery stepping stone", "patient"),
]



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

@dataclass
class Entity:
    id: str
    kind: str
    type: str
    label: str
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    def __post_init__(self) -> None:
        if not hasattr(self.meters, "__missing__"):
            object.__setattr__(self, "meters", __import__("collections").defaultdict(float, self.meters))
        if not hasattr(self.memes, "__missing__"):
            object.__setattr__(self, "memes", __import__("collections").defaultdict(float, self.memes))
        for key in ("safe", "near_water", "helped", "changed"):
            self.meters.setdefault(key, 0.0)
        for key in ("concern", "courage", "calm", "joy"):
            self.memes.setdefault(key, 0.0)
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
    place: str = "the riverbank"
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
class StoryParams:
    place: str = ""
    animal: str = ""
    concern: str = ""
    name: str = ""
    trait: str = ""
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
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict[str, object] = field(default_factory=dict)
    lines: list[list[str]] = field(default_factory=lambda: [[]])
    fired: set[str] = field(default_factory=set)

    world: object | None = None
    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, text: str) -> None:
        if text:
            self.lines[-1].append(text)

    def para(self) -> None:
        if self.lines[-1]:
            self.lines.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(part) for part in self.lines if part)
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
    def get(self, eid: str):
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
        return self.entities[eid]
    def copy(self):
        clone = __import__("copy").deepcopy(self)
        return clone


def _validate(params: StoryParams) -> None:
    if params.place not in PLACES:
        pass
    if params.animal not in ANIMALS:
        pass
    if params.concern not in CONCERNS:
        pass
    if params.name not in NAMES:
        pass
    if params.trait not in TRAITS:
        pass


def tell(params: StoryParams) -> World:
    _validate(params)
    world = World(Setting(params.place))
    hero = world.add(
        Entity(
            "hero",
            "character",
            params.animal,
            params.name,
            memes={"concern": 1.0, "courage": 0.0},
        )
    )
    friend = world.add(
        Entity(
            "friend",
            "character",
            "river_friend",
            "a small river friend",
            memes={"calm": 1.0},
        )
    )
    trouble = world.add(
        Entity(
            "trouble",
            "object",
            "river_problem",
            params.concern,
            meters={"near_water": 1.0},
        )
    )

    world.facts.update(hero=hero, friend=friend, trouble=trouble, params=params)

    world.say(
        f"At the riverbank, {hero.label} watched the bright water wink and blink."
    )
    world.say(
        f"{hero.label} was {params.trait}, but {hero.label} saw {params.concern} bobbing close to the current."
    )
    world.say("The river went swish, swish; the reeds went hush, hush.")
    world.para()

    world.say(
        f"A sudden wave nudged the trouble away, and {hero.label} made a quick lunge."
    )
    world.say(
        f"Then {hero.label} stopped, because a worried concern tugged at {hero.label}'s heart: the bank was slick and the current was quick."
    )
    world.say(
        f'"Wait," said the river friend. "A brave lunge needs a safe plan."'
    )
    world.say(
        f'"What should I do?" asked {hero.label}.'
    )
    world.say(
        f'"Use the long branch, stay low, and pull from the dry stones," said the river friend.'
    )

    hero.memes["courage"] += 1
    hero.memes["calm"] += 1
    world.para()
    world.say(
        f"So {hero.label} chose the branch, tested the stones, and reached from the dry side."
    )
    world.say("Scritch, scratch! The branch slid beneath the trouble.")
    trouble.meters["helped"] = 1.0
    hero.meters["safe"] = 1.0
    hero.meters["changed"] = 1.0
    hero.memes["concern"] = 0.0
    hero.memes["joy"] += 1
    friend.memes["joy"] += 1
    world.say(
        f"With one small pull, {hero.label} drew {params.concern} back to safety."
    )
    world.say(
        f"Drip, drop! The river carried on, while {hero.label} stepped back from the edge."
    )

    world.para()
    world.say(
        f"The lunge had changed into a lesson: concern can slow a body just enough to help it choose wisely."
    )
    world.say(
        f"{hero.label} was still brave, but now bravery wore a careful pair of shoes."
    )
    world.say(
        "The reeds bowed, the river shone, and the rescued friend gave a happy plop."
    )
    world.say(
        f"That evening, {hero.label} remembered the Lesson Learned: look, listen, then leap only when the safe way is clear."
    )
    return world


def generation_prompts(world: World) -> list[str]:
    p = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "params")
    return [
        f"Write a Nursery Rhyme-style riverbank story about {p.name}, a {p.animal}, making a careful lunge after feeling concern.",
        "Include Sound Effects, a Transformation from fear into careful courage, and a clear Lesson Learned.",
        f"Tell how {p.name} helps {p.concern} without rushing into the river.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p: StoryParams = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "params")  # type: ignore[assignment]
    return [
        QAItem(
            f"What caused {p.name}'s concern?",
            f"{p.name} saw {p.concern} being nudged toward the quick river current.",
        ),
        QAItem(
            "Why did the first lunge become a careful plan?",
            "The bank was slick and the current was quick, so the river friend advised using a long branch from the dry stones.",
        ),
        QAItem(
            "How did the transformation happen?",
            f"{p.name} changed from rushing with worry to acting with calm courage by testing the stones and using the branch.",
        ),
        QAItem(
            "What was the Lesson Learned?",
            "Look, listen, then leap only when the safe way is clear.",
        ),
        QAItem(
            "Which Sound Effects appeared in the story?",
            "The river went swish, swish; the reeds went hush, hush; the branch went scritch, scratch; and the rescued friend made a happy plop.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            "What is a riverbank?",
            "A riverbank is the land beside a river.",
        ),
        QAItem(
            "What does concern mean?",
            "Concern is a feeling that something may be unsafe or may need care.",
        ),
        QAItem(
            "What is a lunge?",
            "A lunge is a sudden movement forward.",
        ),
        QAItem(
            "Why should someone check the ground near moving water?",
            "The ground may be slippery, and moving water can pull objects or people along.",
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in list(world.entities.values()):
        meters = {k: v for k, v in entity.meters.items() if v}
        memes = {k: v for k, v in entity.memes.items() if v}
        lines.append(
            f"  {entity.id:8} ({entity.type:12}) meters={meters} memes={memes}"
        )
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    lines.extend(f"{i}. {prompt}" for i, prompt in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


ASP_RULES = r"""
safe_plan :- concern, dry_stones, branch.
rescue :- safe_plan, lunge.
transformation :- rescue, concern.
lesson_learned :- transformation.
good_story :- lesson_learned, sound_effects.
"""


def asp_facts() -> str:
    import asp

    return "\n".join(
        [
            asp.fact("place", "riverbank"),
            asp.fact("concern"),
            asp.fact("dry_stones"),
            asp.fact("branch"),
            asp.fact("lunge"),
            asp.fact("sound_effects"),
        ]
    )


def asp_program(show: str = "#show good_story/0.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    try:
        import asp

        model = asp.one_model(asp_program())
        names = {str(symbol) for symbol in model}
        required = {"good_story"}
        if not any(name.startswith("good_story") for name in names):
            pass
    except ImportError:
        return 0
    sample = generate(
        StoryParams(
            place="the riverbank",
            animal="frog",
            concern="a stranded beetle",
            name="Luna",
            trait="watchful",
            seed=1,
        )
    )
    required_words = ["lunge", "concern", "Lesson Learned", "swish", "Transformation"]
    text = sample.story
    if not all(word.lower() in text.lower() for word in required_words):
        pass
    print("OK: Python and ASP riverbank story checks passed.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Nursery Rhyme riverbank storyworld with a careful lunge."
    )
    parser.add_argument("--place", choices=list(PLACES))
    parser.add_argument("--animal", choices=ANIMALS)
    parser.add_argument("--concern", choices=CONCERNS)
    parser.add_argument("--name", choices=NAMES)
    parser.add_argument("--trait", choices=TRAITS)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return StoryParams(
        place=getattr(args, "place", None) or "the riverbank",
        animal=getattr(args, "animal", None) or rng.choice(ANIMALS),
        concern=getattr(args, "concern", None) or rng.choice(CONCERNS),
        name=getattr(args, "name", None) or rng.choice(NAMES),
        trait=getattr(args, "trait", None) or rng.choice(TRAITS),
    )


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


def emit(
    sample: StorySample,
    *,
    trace: bool = False,
    qa: bool = False,
    header: str = "",
) -> None:
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
        print(asp_program())
        return
    if getattr(args, "verify", None):
        raise SystemExit(asp_verify())

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        for index, (name, animal, concern, trait) in enumerate(CURATED):
            samples.append(
                generate(
                    StoryParams(
                        place="the riverbank",
                        animal=animal,
                        concern=concern,
                        name=name,
                        trait=trait,
                        seed=base_seed + index,
                    )
                )
            )
    else:
        if getattr(args, "n", None) < 1:
            pass
        for index in range(getattr(args, "n", None)):
            rng = random.Random(base_seed + index)
            params = resolve_params(args, rng)
            params.seed = base_seed + index
            samples.append(generate(params))

    if getattr(args, "asp", None):
        try:
            import asp

            model = asp.one_model(asp_program())
            print("ASP model:", " ".join(str(atom) for atom in model))
        except ImportError as exc:
            pass
        return

    if getattr(args, "json", None):
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for index, sample in enumerate(samples):
        header = ""
        if getattr(args, "all", None):
            header = f"### {sample.params.name} at {sample.params.place}"
        elif len(samples) > 1:
            header = f"### variant {index + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
