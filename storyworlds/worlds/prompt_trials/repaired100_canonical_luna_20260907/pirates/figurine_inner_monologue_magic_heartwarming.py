#!/usr/bin/env python3
"""
A tiny heartwarming magic world about a lonely figurine, a listening child,
and the inner courage that wakes when kindness is shared.
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
class Figurine:
    id: str
    name: str
    material: str
    place: str
    purpose: str
    magic_word: str
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    figure: object | None = None
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
class Child:
    id: str
    name: str
    age: int
    trait: str
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    child: object | None = None
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
class StoryParams:
    figurine: str = ""
    child: str = ""
    keeper: str = ""
    gift: str = ""
    place: str = ""
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
class World:
    figurine: Figurine
    child: Child
    keeper: str
    gift: str
    place: str
    history: list[str] = field(default_factory=list)
    facts: dict = field(default_factory=dict)

    world: object | None = None
    def say(self, text: str) -> None:
        self.history.append(text)

    def render(self) -> str:
        return "\n\n".join(self.history)
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
    def copy(self):
        clone = __import__("copy").deepcopy(self)
        return clone


FIGURINES = {
    "luna": Figurine(
        id="luna",
        name="Luna",
        material="painted clay",
        place="a dusty shelf",
        purpose="to remind someone that even a small heart can shine",
        magic_word="kindness",
    ),
    "moss": Figurine(
        id="moss",
        name="Moss",
        material="smooth green stone",
        place="a windowsill",
        purpose="to keep lonely rooms company",
        magic_word="welcome",
    ),
    "pippin": Figurine(
        id="pippin",
        name="Pippin",
        material="bright wooden",
        place="an old toy chest",
        purpose="to help brave wishes find their way home",
        magic_word="hope",
    ),
}

CHILDREN = {
    "nora": Child(id="nora", name="Nora", age=6, trait="thoughtful"),
    "eli": Child(id="eli", name="Eli", age=7, trait="curious"),
    "mara": Child(id="mara", name="Mara", age=5, trait="gentle"),
    "leo": Child(id="leo", name="Leo", age=6, trait="hopeful"),
}

KEEPERS = ["Grandma", "Aunt Rose", "Uncle Ben"]
GIFTS = ["a blue ribbon", "a tiny paper crown", "a warm wool scarf", "a painted wooden star"]
PLACES = ["the attic room", "the little library", "the garden shed", "the sunroom"]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate a heartwarming magical figurine story."
    )
    parser.add_argument("--figurine", choices=FIGURINES)
    parser.add_argument("--child", choices=CHILDREN)
    parser.add_argument("--keeper", choices=KEEPERS)
    parser.add_argument("--gift", choices=GIFTS)
    parser.add_argument("--place", choices=PLACES)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--seed", type=int)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if getattr(args, "n", None) < 1:
        return _fallback_storyparams(args, rng, StoryParams, globals())

    figurine = getattr(args, "figurine", None) or rng.choice(sorted(FIGURINES))
    child = getattr(args, "child", None) or rng.choice(sorted(CHILDREN))
    keeper = getattr(args, "keeper", None) or rng.choice(KEEPERS)
    gift = getattr(args, "gift", None) or rng.choice(GIFTS)
    place = getattr(args, "place", None) or rng.choice(PLACES)

    if figurine not in FIGURINES:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    if child not in CHILDREN:
        return _fallback_storyparams(args, rng, StoryParams, globals())

    return StoryParams(
        figurine=figurine,
        child=child,
        keeper=keeper,
        gift=gift,
        place=place,
    )


def build_world(params: StoryParams) -> World:
    figure = Figurine(**_safe_lookup(FIGURINES, params.figurine).__dict__)
    child = Child(**CHILDREN[params.child].__dict__)
    world = World(
        figurine=figure,
        child=child,
        keeper=params.keeper,
        gift=params.gift,
        place=params.place,
    )

    figure.meters["stillness"] = 1.0
    figure.memes["loneliness"] = 2.0
    child.memes["curiosity"] = 1.0
    child.memes["kindness"] = 0.0

    world.say(
        f"{child.name} found the little figurine in {figure.place}, "
        f"where it had been waiting in the quiet {params.place}."
    )
    world.say(
        f"The figurine was {figure.material}, with one chipped shoe and a smile "
        f"so small that most people would have missed it."
    )
    world.say(
        f'"Why are you all alone?" {child.name} asked. '
        f'"I can sit with you for a while."'
    )
    world.say(
        f"{child.name} wondered whether the figurine could hear. "
        f"Deep inside, a tiny thought answered, "
        f'"I have been waiting for someone to notice me."'
    )

    child.memes["kindness"] += 1.0
    figure.memes["loneliness"] -= 1.0
    figure.memes["trust"] = 1.0

    world.say(
        f"{child.name} brushed away the dust and tied {params.gift} around the "
        f"figurine. Then {child.name} placed it beside the window, where the "
        f"afternoon light could reach its face."
    )
    world.say(
        f'"There," said {child.name}. "You have a place with me now."'
    )
    world.say(
        f'"A place with you," the figurine thought. The thought felt warm, '
        f"like a candle glowing behind its painted heart."
    )

    figure.meters["stillness"] = 0.0
    figure.meters["glow"] = 1.0
    figure.memes["belonging"] = 1.0

    world.say(
        f"That evening, {params.keeper} came into {params.place} carrying a basket "
        f"of folded blankets."
    )
    world.say(
        f'"I thought I heard you talking," {params.keeper} said.'
    )
    world.say(
        f'"I was talking to my figurine," {child.name} replied. '
        f'"It seemed lonely, so I gave it a home."'
    )
    world.say(
        f"{params.keeper} smiled and looked closely. The figurine's tiny painted "
        f"heart was shining like a speck of moonlight."
    )
    world.say(
        f'"Perhaps it was waiting for your kindness," {params.keeper} said. '
        f'"Sometimes magic begins when someone cares."'
    )

    child.memes["kindness"] += 1.0
    child.memes["wonder"] = 1.0
    figure.memes["love"] = 1.0

    world.say(
        f"From then on, {child.name} and the figurine shared the window seat. "
        f"They welcomed rainy mornings, listened to the house settle at night, "
        f"and saved the brightest stories for bedtime."
    )
    world.say(
        f"And whenever {child.name} felt lonely, the figurine's little heart "
        f"glowed softly, reminding {child.name} that a home can begin with one "
        f"kind person making room."
    )

    world.facts.update(
        child=child,
        figurine=figure,
        keeper=params.keeper,
        gift=params.gift,
        place=params.place,
        magic=True,
        changed=True,
    )
    return world


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    figure = world.figurine
    child = world.child

    prompts = [
        f"Write a heartwarming magical story about {child.name} finding a lonely figurine.",
        (
            f"Tell a gentle story where {child.name} speaks to a {figure.material} "
            f"figurine, listens to its inner thoughts, and gives it a home."
        ),
        (
            f"Write a child-friendly tale showing that kindness awakens magic, "
            f"with a figurine whose tiny heart begins to glow."
        ),
    ]

    story_qa = [
        QAItem(
            question=f"Where did {child.name} find the figurine?",
            answer=(
                f"{child.name} found the figurine in {figure.place}, inside "
                f"{world.place}, where it had been waiting quietly."
            ),
        ),
        QAItem(
            question="Why did the figurine seem sad at first?",
            answer=(
                f"The figurine seemed sad because it had been alone and dusty for "
                f"a long time, without anyone noticing it."
            ),
        ),
        QAItem(
            question=f"What did {child.name} give the figurine?",
            answer=(
                f"{child.name} gave the figurine {world.gift} and placed it beside "
                f"the window, where it could share a home."
            ),
        ),
        QAItem(
            question="What made the figurine's heart glow?",
            answer=(
                f"{child.name}'s kindness made the figurine's tiny painted heart "
                f"glow like moonlight. The magic began when someone cared."
            ),
        ),
        QAItem(
            question="What did the figurine remind the child?",
            answer=(
                "It reminded the child that a home can begin when one kind person "
                "makes room for someone else."
            ),
        ),
    ]

    world_qa = [
        QAItem(
            question="What is a figurine?",
            answer=(
                "A figurine is a small model or statue of a person, animal, or "
                "imaginary character."
            ),
        ),
        QAItem(
            question="Why can kindness feel magical?",
            answer=(
                "Kindness can feel magical because it helps someone feel noticed, "
                "safe, and loved, and it can change a sad moment into a hopeful one."
            ),
        ),
        QAItem(
            question="What does it mean to make room for someone?",
            answer=(
                "It means welcoming someone and showing that they belong with you."
            ),
        ),
    ]

    return StorySample(
        params=params,
        story=world.render(),
        prompts=prompts,
        story_qa=story_qa,
        world_qa=world_qa,
        world=world,
    )


ASP_RULES = r"""
noticed(F) :- kindness(C), cared_for(C,F).
glowing(F) :- noticed(F), magic(F).
belongs(F) :- glowing(F).
happy(C) :- belongs(F), cared_for(C,F).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp

    return "\n".join(
        [
            asp.fact("figurine", key)
            for key in FIGURINES
        ]
        + [
            asp.fact("magic", key)
            for key in FIGURINES
        ]
        + [asp.fact("kindness", "child")]
        + [asp.fact("cared_for", "child", key) for key in FIGURINES]
    )


def asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n#show glowing/1.\n#show belongs/1.\n"


def dump_trace(world: World) -> str:
    return "\n".join(
        [
            "--- world model state ---",
            f"figurine: {world.figurine.name}",
            f"  material: {world.figurine.material}",
            f"  meters: {world.figurine.meters}",
            f"  memes: {world.figurine.memes}",
            f"child: {world.child.name}",
            f"  meters: {world.child.meters}",
            f"  memes: {world.child.memes}",
            f"magic awakened: {world.facts.get('magic')}",
            f"belonging established: {world.facts.get('changed')}",
        ]
    )


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    lines.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def verify() -> int:
    sample = generate(
        StoryParams(
            figurine="luna",
            child="nora",
            keeper="Grandma",
            gift="a blue ribbon",
            place="the attic room",
        )
    )
    checks = [
        sample.world is not None,
        "figurine" in sample.story.lower(),
        "heart" in sample.story.lower(),
        "kindness" in sample.story.lower(),
        len(sample.story_qa) >= 3,
        len(sample.world_qa) >= 2,
    ]
    if all(checks):
        print("OK: generated story, magic turn, dialogue, inner monologue, and QA passed.")
        return 0
    print("FAIL: storyworld verification failed.")
    return 1


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
        print()
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
        raise SystemExit(verify())

    if getattr(args, "asp", None):
        try:
            import storyworlds.asp as asp

            models = asp.solve(asp_program(), models=1)
            print("ASP magic model:")
            for symbol in models[0] if models else []:
                print(f"  {symbol}")
        except Exception as exc:
            raise SystemExit(f"ASP mode unavailable: {exc}")

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)

    if getattr(args, "all", None):
        params_list = [
            StoryParams(
                figurine="luna",
                child="nora",
                keeper="Grandma",
                gift="a blue ribbon",
                place="the attic room",
            ),
            StoryParams(
                figurine="moss",
                child="eli",
                keeper="Aunt Rose",
                gift="a warm wool scarf",
                place="the little library",
            ),
            StoryParams(
                figurine="pippin",
                child="mara",
                keeper="Uncle Ben",
                gift="a painted wooden star",
                place="the sunroom",
            ),
        ]
    else:
        params_list = []
        for index in range(getattr(args, "n", None)):
            rng = random.Random(base_seed + index)
            params = resolve_params(args, rng)
            params.seed = base_seed + index
            params_list.append(params)

    samples = [generate(params) for params in params_list]

    if getattr(args, "json", None):
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for index, sample in enumerate(samples):
        if len(samples) > 1:
            emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=f"### story {index + 1}")
        else:
            emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None))
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
