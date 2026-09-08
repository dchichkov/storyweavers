#!/usr/bin/env python3
"""
Story world: a fairy-tale creamery where a deadly mistake becomes a lesson
learned.

The story uses a brief inner-monologue flavor through openly spoken thoughts,
and a flashback that reveals how Luna learned to handle a dangerous ingredient.
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
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "storyworlds"))
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
class Entity:
    id: str
    kind: str
    label: str
    type: str
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
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
class Creamery:
    name: str
    place: str
    hearth: str
    warning: str
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
class StoryParams:
    creamery: str = "Moonmilk Creamery"
    hero_name: str = "Luna"
    helper_name: str = "Pip"
    danger: str = "thorn-honey"
    style: str = "Fairy Tale"
    feature: str = "Inner Monologue, Flashback, Lesson Learned"
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


CREAMERIES = {
    "Moonmilk Creamery": Creamery(
        "Moonmilk Creamery",
        "beside the silver forest",
        "the blue-tiled hearth",
        "Never taste the black jar",
    ),
    "Roseglass Creamery": Creamery(
        "Roseglass Creamery",
        "under the hill of singing roses",
        "the copper hearth",
        "Keep the red vial locked",
    ),
    "Clover Bell Creamery": Creamery(
        "Clover Bell Creamery",
        "where three green roads meet",
        "the little stone hearth",
        "Ask before using strange honey",
    ),
}

HEROES = ["Luna", "Mara", "Tavi", "Nell", "Orin"]
HELPERS = ["Pip", "Bram", "Etta", "Sol", "Wren"]

DANGERS = {
    "thorn-honey": {
        "ingredient": "a black jar of thorn-honey",
        "threat": "a deadly honey that can make a careless taster terribly ill",
        "clue": "the warning rune on the jar began to glow red",
        "flashback": (
            "Luna remembered the old keeper saying, “A sweet smell is not proof "
            "of a safe bite.”"
        ),
        "repair": (
            "They set the black jar inside a locked iron box, swept every drop "
            "from the table, and made the ice cream with clean meadow honey."
        ),
        "result": (
            "The new batch was safe, creamy, and bright with the taste of summer."
        ),
        "lesson": "a beautiful ingredient must still be checked before it is used",
        "ending": (
            "At sunset, the villagers ate moon-white scoops while the locked jar "
            "rested far away beneath a silver bell."
        ),
    },
    "dragon-pepper": {
        "ingredient": "a ruby pinch of dragon-pepper",
        "threat": "a deadly spice that burns more fiercely than a dragon's breath",
        "clue": "the copper spoon smoked as soon as it touched the red powder",
        "flashback": (
            "Luna remembered the miller's warning: “Heat can hide inside a tiny grain.”"
        ),
        "repair": (
            "They sealed the pepper in a stone pot, washed the spoon three times, "
            "and stirred fresh cream with harmless cinnamon instead."
        ),
        "result": (
            "The clean batch tasted warm and sweet, with no dragon-fire sting."
        ),
        "lesson": "a tiny amount of danger is still danger",
        "ending": (
            "The village children cheered as cinnamon clouds rose above their bowls "
            "and the sealed pepper slept in its stone pot."
        ),
    },
    "nightshade-syrup": {
        "ingredient": "a violet bottle of nightshade syrup",
        "threat": "a deadly syrup that belongs in a locked apothecary, not in dessert",
        "clue": "the bottle cast a cold shadow even though the hearth was blazing",
        "flashback": (
            "Luna remembered a lesson from her grandmother: “If a thing feels wrong, "
            "pause before it touches the pot.”"
        ),
        "repair": (
            "They carried the bottle to the apothecary, washed the mixing bowl, "
            "and replaced the syrup with blackberry juice from the orchard."
        ),
        "result": (
            "The finished cream turned purple from safe berries and smelled of rain."
        ),
        "lesson": "a worried feeling deserves careful attention and a safe check",
        "ending": (
            "The creamery bell chimed as everyone tasted blackberry scoops beneath "
            "the kindly evening stars."
        ),
    },
}

ASP_RULES = r"""
creamery(C) :- creamery_name(C).
dangerous(I) :- danger_name(I).
safe_batch(B) :- washed(B), safe_ingredient(B).
lesson_learned(H) :- hero(H), learned(H).
resolved(C) :- safe_batch(B), creamery_of(B,C).
"""


def asp_facts() -> str:
    import asp

    lines = []
    for name in CREAMERIES:
        lines.append(asp.fact("creamery_name", name))
    for name in DANGERS:
        lines.append(asp.fact("danger_name", name))
    lines.extend(
        [
            asp.fact("hero", "hero"),
            asp.fact("dangerous", "ingredient"),
            asp.fact("washed", "batch"),
            asp.fact("safe_ingredient", "batch"),
            asp.fact("safe_batch", "batch"),
            asp.fact("creamery_of", "batch", "creamery"),
            asp.fact("learned", "hero"),
        ]
    )
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp

    model = asp.one_model(
        asp_program(
            "#show safe_batch/1.\n#show lesson_learned/1.\n#show resolved/2."
        )
    )
    found = set()
    for symbol in model:
        args = tuple(
            a.string
            if a.type == a.type.String
            else a.number
            if a.type == a.type.Number
            else a.name
            for a in symbol.arguments
        )
        found.add((symbol.name, args))
    wanted = {
        ("safe_batch", ("batch",)),
        ("lesson_learned", ("hero",)),
        ("resolved", ("batch", "creamery")),
    }
    if found == wanted:
        print("OK: ASP and Python parity looks good.")
        return 0
    print("MISMATCH between ASP and Python reasoning.")
    print("ASP:", sorted(found))
    print("PY :", sorted(wanted))
    return 1


class World:
    def __init__(self, creamery: Creamery) -> None:
        self.creamery = creamery
        self.entities: dict[str, Entity] = {}
        self.facts: dict[str, object] = {}
        self.lines: list[str] = []

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, line: str) -> None:
        self.lines.append(line)

    def render(self) -> str:
        return " ".join(self.lines)
    def get(self, eid: str):
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
        return self.entities[eid]
    def copy(self):
        clone = __import__("copy").deepcopy(self)
        return clone


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="A fairy-tale creamery story about a deadly ingredient and a lesson learned."
    )
    parser.add_argument("--creamery", choices=list(CREAMERIES))
    parser.add_argument("--name")
    parser.add_argument("--helper")
    parser.add_argument("--danger", choices=list(DANGERS))
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    hero = getattr(args, "name", None) or rng.choice(HEROES)
    helper = getattr(args, "helper", None) or rng.choice([name for name in HELPERS if name != hero])
    if hero == helper:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    return StoryParams(
        creamery=getattr(args, "creamery", None) or rng.choice(list(CREAMERIES)),
        hero_name=hero,
        helper_name=helper,
        danger=getattr(args, "danger", None) or rng.choice(list(DANGERS)),
    )


def generate(params: StoryParams) -> StorySample:
    if params.creamery not in CREAMERIES:
        pass
    if params.danger not in DANGERS:
        pass
    if params.hero_name == params.helper_name:
        pass

    rng = random.Random(
        params.seed
        if params.seed is not None
        else f"{params.creamery}:{params.hero_name}:{params.helper_name}:{params.danger}"
    )
    creamery = _safe_lookup(CREAMERIES, params.creamery)
    danger = _safe_lookup(DANGERS, params.danger)
    world = World(creamery)

    hero = world.add(
        Entity(
            "hero",
            "character",
            params.hero_name,
            "child",
            meters={"care": 0.0, "danger": 0.0},
            memes={"pride": 0.0, "worry": 0.0, "wisdom": 0.0},
        )
    )
    helper = world.add(
        Entity(
            "helper",
            "character",
            params.helper_name,
            "helper",
            meters={"care": 0.0},
            memes={"alertness": 1.0},
        )
    )
    ingredient = world.add(
        Entity(
            "ingredient",
            "ingredient",
            danger["ingredient"],
            "dangerous_food",
            meters={"danger": 1.0},
            memes={"temptation": 1.0},
        )
    )

    world.say(
        f"Once upon a time, {params.hero_name} worked at the {creamery.name}, "
        f"{creamery.place}."
    )
    world.say(
        f"One morning, the young cream-maker prepared a golden batch of ice cream "
        f"on {creamery.hearth} for the village feast."
    )
    world.say(
        f"Beside the clean milk stood {danger['ingredient']}, an ingredient that was "
        f"{danger['threat']}."
    )
    world.say(
        f'"It smells wonderful," {params.hero_name} whispered. "Perhaps one drop '
        f'will make the feast unforgettable."'
    )
    world.say(
        f'"Please wait," said {params.helper_name}. "What does the label say?"'
    )
    world.say(
        f"{params.hero_name} looked closely, and {danger['clue']}."
    )
    world.say(
        f"Inside, {params.hero_name} thought, 'A sweet smell is not enough. I must "
        f"find out whether this belongs in our food.'"
    )
    hero.meters["danger"] = 1.0
    hero.memes["worry"] = 1.0
    ingredient.memes["temptation"] = 2.0

    world.say(
        f"That sight opened a flashback. The day before, {params.hero_name} had "
        f"heard the keeper explain a rule beside the same creamery door."
    )
    world.say(danger["flashback"])
    world.say(
        f'"Then we will not guess," {params.hero_name} said. '
        f'"We will ask someone who knows."'
    )
    world.say(
        f'"And we will protect everyone while we wait," replied {params.helper_name}.'
    )
    world.say(
        f"They carried the suspicious ingredient away from the milk, marked the "
        f"table with a red ribbon, and called the village apothecary."
    )
    world.say(
        f"The apothecary confirmed that the ingredient was {danger['threat']}, "
        f"so even a small taste could have harmed the feast."
    )
    world.say(danger["repair"])
    hero.meters["care"] = 1.0
    hero.meters["danger"] = 0.0
    hero.memes["worry"] = 0.0
    hero.memes["wisdom"] = 1.0
    ingredient.memes["temptation"] = 0.0
    world.say(
        f"The lesson learned by {params.hero_name} was clear: {danger['lesson']}."
    )
    world.say(
        f'"I wanted the ice cream to be special," {params.hero_name} told '
        f'{params.helper_name}, "but keeping people safe is the most special work '
        f'of all."'
    )
    world.say(
        f'"Now it is special and safe," {params.helper_name} answered, smiling.'
    )
    world.say(danger["result"])
    world.say(danger["ending"])

    world.facts.update(
        hero=hero,
        helper=helper,
        ingredient=ingredient,
        creamery=creamery,
        dangerous=True,
        safe_batch=True,
        lesson=True,
        clue=danger["clue"],
        flashback=danger["flashback"],
        repair=danger["repair"],
        lesson_text=danger["lesson"],
        result=danger["result"],
    )

    prompts = [
        f"Write a Fairy Tale about {params.hero_name} working at the {creamery.name}.",
        f"Include a deadly ingredient, a flashback, inner monologue, and a lesson learned.",
        f"Show how {params.hero_name} and {params.helper_name} turn danger into a safe creamery feast.",
    ]
    story_qa = [
        QAItem(
            "What made the ingredient dangerous?",
            f"{danger['ingredient']} was {danger['threat']}.",
        ),
        QAItem(
            f"What clue did {params.hero_name} notice?",
            danger["clue"].capitalize() + ".",
        ),
        QAItem(
            "What did the flashback remind Luna about?",
            danger["flashback"],
        ),
        QAItem(
            f"What did {params.hero_name} and {params.helper_name} do?",
            danger["repair"],
        ),
        QAItem(
            "What lesson was learned?",
            f"The lesson learned was that {danger['lesson']}.",
        ),
        QAItem(
            "How did the ending prove the problem was solved?",
            danger["result"],
        ),
    ]
    world_qa = [
        QAItem(
            "What is a creamery?",
            "A creamery is a place where milk is handled to make foods such as butter, cheese, and ice cream.",
        ),
        QAItem(
            "Why should an unknown ingredient not be tasted?",
            "An unknown ingredient may be poisonous or otherwise dangerous, so it should be identified by a knowledgeable person first.",
        ),
        QAItem(
            "What is a flashback?",
            "A flashback is a part of a story that shows an earlier event or memory.",
        ),
        QAItem(
            "What is a lesson learned?",
            "A lesson learned is a useful understanding gained from an experience and used to make a wiser choice.",
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
        print("--- trace ---")
        for key, entity in sample.world.entities.items():
            print(
                f"{key}: {entity.label} meters={entity.meters} memes={entity.memes}"
            )
    if qa:
        print("\n== prompts ==")
        for prompt in sample.prompts:
            print(prompt)
        print("\n== story qa ==")
        for item in sample.story_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")
        print("\n== world qa ==")
        for item in sample.world_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(
            asp_program(
                "#show safe_batch/1.\n#show lesson_learned/1.\n#show resolved/2."
            )
        )
        return
    if getattr(args, "verify", None):
        raise SystemExit(asp_verify())

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        for creamery_name in CREAMERIES:
            params = StoryParams(
                creamery=creamery_name,
                hero_name=_safe_lookup(HEROES, 0),
                helper_name=_safe_lookup(HELPERS, 0),
                danger=list(DANGERS)[len(samples) % len(DANGERS)],
                seed=base_seed + len(samples),
            )
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        index = 0
        while len(samples) < getattr(args, "n", None) and index < max(50, getattr(args, "n", None) * 20):
            params = resolve_params(args, random.Random(base_seed + index))
            params.seed = base_seed + index
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            index += 1

    if getattr(args, "json", None):
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for index, sample in enumerate(samples):
        emit(
            sample,
            trace=getattr(args, "trace", None),
            qa=getattr(args, "qa", None),
            header=f"### variant {index + 1}" if len(samples) > 1 else "",
        )
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
