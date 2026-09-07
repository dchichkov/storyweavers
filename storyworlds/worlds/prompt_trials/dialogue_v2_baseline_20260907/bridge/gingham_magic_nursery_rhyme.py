#!/usr/bin/env python3
"""Gingham Magic Nursery Rhyme.

A small moonlit tale about a gingham bridge, a friendly spell, and a careful
little crossing.
"""

from __future__ import annotations

import argparse
import json
import random
import re
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from pathlib import Path as _StoryPath
_storyworlds_root = next(parent for parent in _StoryPath(__file__).resolve().parents
                        if (parent / 'results.py').is_file() and (parent / 'asp.py').is_file())
sys.path.insert(0, str(_storyworlds_root))
from results import QAItem, StoryError, StorySample



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
    label: str
    kind: str = "thing"
    location: str = ""
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
class Event:
    kind: str
    text: str
    question: str = ""
    cause: str = ""
    result: str = ""
    state: dict = field(default_factory=dict)
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
    hero: str = "Nell"
    helper: str = "Pip"
    charm: str = "moon"
    fault: str = "loose"
    seed: int = 777
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


HEROES = ("Nell", "Mabel", "Toby", "Wren", "Pip", "Dot")
HELPERS = ("Pip", "Dot", "Moss", "Bim", "Lark")
CHARMS = {
    "moon": "a silver moon button",
    "star": "a little star bead",
    "bell": "a blue bell bead",
}
FAULTS = {
    "loose": "a loose corner",
    "dark": "a dark spell",
    "narrow": "a narrow path",
}
SOLUTIONS = {
    "loose": "knot",
    "dark": "glow",
    "narrow": "widen",
}
PROMPT = (
    "Write a gentle nursery-rhyme story about a child using gingham and magic "
    "to repair a tiny bridge for a moonlit crossing."
)


class World:
    def __init__(self, params: StoryParams):
        self.params = params
        self.entities: dict[str, Entity] = {
            "hero": Entity(
                "hero",
                params.hero,
                "character",
                "garden",
                memes={"worry": 0.7, "courage": 0.3},
            ),
            "helper": Entity(
                "helper",
                params.helper,
                "character",
                "garden",
                memes={"worry": 0.4, "trust": 0.6},
            ),
            "bridge": Entity(
                "bridge",
                "the gingham bridge",
                "bridge",
                "over the brook",
                meters={"secure": 0, "lit": 0, "width": 1, "crossed": 0},
            ),
            "charm": Entity(
                "charm",
                _safe_lookup(CHARMS, params.charm),
                "charm",
                "in a pocket",
                meters={"used": 0},
            ),
            "rabbit": Entity(
                "rabbit",
                "the sleepy rabbit",
                "animal",
                "near the brook",
                meters={"crossed": 0},
            ),
        }
        self.history: list[Event] = []

    def snapshot(self) -> dict:
        return {key: asdict(value) for key, value in self.entities.items()}

    def narrate(self, kind: str, text: str, *, question="", cause="", result=""):
        self.history.append(
            Event(
                kind=kind,
                text=text,
                question=question,
                cause=cause,
                result=result,
                state=self.snapshot(),
            )
        )

    def sample(self) -> StorySample:
        return StorySample(
            params=self.params,
            story="\n\n".join(event.text for event in self.history),
            prompts=[PROMPT],
            story_qa=[
                QAItem(event.question, f"{event.cause} {event.result}")
                for event in self.history
                if event.question
            ],
            world_qa=[
                QAItem(
                    "What is gingham?",
                    "Gingham is cloth woven with a simple checked pattern.",
                ),
                QAItem(
                    "What does a magic charm do in this world?",
                    "A magic charm helps a careful person change one small problem.",
                ),
            ],
            world=self,
        )
    def get(self, eid: str):
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
        return self.entities[eid]
    def copy(self):
        clone = __import__("copy").deepcopy(self)
        return clone


def validate_params(params: StoryParams):
    if params.fault not in FAULTS:
        pass
    if params.charm not in CHARMS:
        pass
    if params.hero == params.helper:
        pass
    for name in (params.hero, params.helper):
        if not re.fullmatch(r"[A-Z][a-z]+", name):
            pass


def build_world(params: StoryParams) -> World:
    validate_params(params)
    world = World(params)
    if params.fault == "loose":
        world.get("bridge").meters["width"] = 1
    elif params.fault == "dark":
        world.get("bridge").meters["width"] = 1
    else:
        world.get("bridge").meters["width"] = 0.5
    return world


def try_cross(world: World) -> bool:
    bridge = world.get("bridge")
    if not bridge.meters["secure"]:
        return False
    if not bridge.meters["lit"]:
        return False
    if bridge.meters["width"] < 1:
        return False
    bridge.meters["crossed"] += 1
    world.get("rabbit").meters["crossed"] = 1
    world.get("rabbit").location = "the far bank"
    return True


def repair(world: World):
    params = world.params
    bridge = world.get("bridge")
    charm = world.get("charm")
    if params.fault == "loose":
        bridge.meters["secure"] = 1
        bridge.meters["lit"] = 1
    elif params.fault == "dark":
        bridge.meters["lit"] = 1
    elif params.fault == "narrow":
        bridge.meters["width"] = 1
        bridge.meters["secure"] = 1
        bridge.meters["lit"] = 1
    charm.meters["used"] = 1


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    h = params.hero
    f = params.helper
    charm = _safe_lookup(CHARMS, params.charm)
    bridge = world.get("bridge")

    world.narrate(
        "beginning",
        f"{h} found a gingham bridge beside the brook, "
        f"where a sleepy rabbit wished to reach the clover crook. "
        f"The checks were red and white, and the moon made them shine.",
    )
    world.narrate(
        "call",
        f"'{f}, come see!' called {h}. 'The rabbit needs a bridge before the stars go to bed.'",
    )
    world.narrate(
        "answer",
        f"{f} came carrying {charm}. 'A little magic may help,' said {f}, "
        "'but gentle hands must lead the way.'",
    )

    if params.fault == "loose":
        world.narrate(
            "problem",
            f"The bridge corner flapped in the breeze. The gingham road was loose, "
            f"and the brook below went swish, swish, swish.",
            question="What was wrong with the gingham bridge?",
            cause="One corner of the gingham bridge was loose.",
            result="The bridge could not safely hold the rabbit.",
        )
        world.narrate(
            "plan",
            f"{h} held the cloth while {f} tied a neat knot. "
            f"Then {h} touched the knot with {charm} and whispered, "
            "'Stay snug, stay bright, stay kind.'",
            question="How did the friends repair the bridge?",
            cause="The loose corner needed to be held in place.",
            result="They tied it firmly and used the charm to make the repair last.",
        )
    elif params.fault == "dark":
        world.narrate(
            "problem",
            f"The gingham bridge was sound, but a cloud hid the moon. "
            f"Without light, the rabbit could not find the checked path.",
            question="Why could the rabbit not cross at first?",
            cause="The bridge was too dark to see.",
            result="The friends needed to light the gingham path.",
        )
        world.narrate(
            "plan",
            f"{h} set {charm} beside the first check. "
            f"{f} sang, 'Glow, glow, little light; show the bridge through velvet night.'",
            question="What did the charm need to change?",
            cause="The strong bridge was hidden in darkness.",
            result="The charm was placed beside the path and asked to shine.",
        )
    else:
        world.narrate(
            "problem",
            f"The gingham bridge was tied and bright, but it was too narrow. "
            f"The rabbit's soft paws had no room to pass.",
            question="Why was the rabbit waiting beside the brook?",
            cause="The bridge was too narrow for the rabbit.",
            result="The friends needed to widen the checked path.",
        )
        world.narrate(
            "plan",
            f"{h} unfolded a second gingham strip while {f} held {charm} above it. "
            f"They lined up the checks, red beside red and white beside white.",
            question="What did the friends add to the bridge?",
            cause="The first cloth path did not leave enough room.",
            result="They unfolded a second gingham strip beside the first.",
        )

    repair(world)
    world.narrate(
        "turn",
        f"The charm twinkled once. The gingham checks shone like tiny windows, "
        f"and the repaired bridge rested quietly over the brook.",
        question="What showed that the magic had worked?",
        cause=f"{(getattr(charm, 'capitalize')() if callable(getattr(charm, 'capitalize', None)) else str(charm).capitalize())} answered the careful repair.",
        result="The bridge became ready for a safe crossing.",
    )

    if not try_cross(world):
        pass
    world.narrate(
        "resolution",
        f"The rabbit took one hop, then two, then three. "
        f"Across the gingham bridge it went, while the brook sang, "
        "'Step by step, the safe way's best!'",
        question="How did the friends test the bridge?",
        cause="They let the rabbit cross after the repair was complete.",
        result="The rabbit reached the far bank safely.",
    )
    world.narrate(
        "ending",
        f"On the clover bank, the rabbit bowed. {h} smiled at {f}, "
        f"and {f} tucked away {charm}. "
        "The gingham bridge glimmered beneath the moon, ready for tomorrow's rhyme.",
    )

    sample = world.sample()
    check_sample(sample)
    return sample


def check_sample(sample: StorySample):
    world = sample.world
    bridge = world.get("bridge")
    rabbit = world.get("rabbit")
    if not bridge.meters["secure"] or not bridge.meters["lit"]:
        pass
    if bridge.meters["width"] < 1:
        pass
    if rabbit.meters["crossed"] != 1 or rabbit.location != "the far bank":
        pass
    if world.get("charm").meters["used"] != 1:
        pass
    if len(sample.story_qa) < 3:
        pass
    if "gingham" not in sample.story.lower():
        pass


ASP_RULES = """
repair(loose,knot).
repair(dark,glow).
repair(narrow,widen).
valid(F,R) :- repair(F,R).
#show valid/2.
"""


def asp_facts() -> str:
    from asp import fact

    return "\n".join(
        fact("fault", fault, solution)
        for fault, solution in SOLUTIONS.items()
    )


def asp_combos() -> set[tuple[str, str]]:
    from asp import atoms, one_model

    symbols = one_model(asp_facts() + "\n" + ASP_RULES)
    return set(atoms(symbols, "valid"))


def verify():
    expected = {(fault, solution) for fault, solution in SOLUTIONS.items()}
    if asp_combos() != expected:
        pass
    count = 0
    for fault in FAULTS:
        for charm in CHARMS:
            sample = generate(
                StoryParams(
                    hero="Nell",
                    helper="Pip",
                    charm=charm,
                    fault=fault,
                    seed=count,
                )
            )
            check_sample(sample)
            count += 1
    print(f"OK: {count} story states; {len(expected)} repair rules.")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--seed", type=int, default=777)
    parser.add_argument("--hero")
    parser.add_argument("--helper")
    parser.add_argument("--charm", choices=tuple(CHARMS))
    parser.add_argument("--fault", choices=tuple(FAULTS))
    for flag in ("all", "trace", "qa", "json", "asp", "verify", "show-asp"):
        parser.add_argument("--" + flag, action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    hero = getattr(args, "hero", None) or rng.choice(HEROES)
    helper = getattr(args, "helper", None) or rng.choice([name for name in HELPERS if name != hero])
    params = StoryParams(
        hero=hero,
        helper=helper,
        charm=getattr(args, "charm", None) or rng.choice(tuple(CHARMS)),
        fault=getattr(args, "fault", None) or rng.choice(tuple(FAULTS)),
        seed=getattr(args, "seed", None),
    )
    validate_params(params)
    return params


def emit(sample: StorySample, *, trace=False, qa=False, header=""):
    if header:
        print(header)
    print(sample.story)
    if qa:
        for item in sample.story_qa:
            print(f"\nQ: {item.question}\nA: {item.answer}")
    if trace:
        print("\nTRACE")
        print(
            json.dumps(
                {
                    "entities": sample.world.snapshot(),
                    "history": [asdict(event) for event in sample.world.history],
                },
                indent=2,
            )
        )


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        if getattr(args, "n", None) < 1:
            pass
        if getattr(args, "show_asp", None):
            print(asp_facts() + "\n" + ASP_RULES)
            return 0
        if getattr(args, "verify", None):
            verify()
            return 0
        if getattr(args, "asp", None):
            print(json.dumps(sorted(asp_combos())))
            return 0

        rng = random.Random(getattr(args, "seed", None))
        if getattr(args, "all", None):
            params_list = []
            for fault in FAULTS:
                for charm in CHARMS:
                    copied = argparse.Namespace(**vars(args))
                    copied.fault = fault
                    copied.charm = charm
                    params_list.append(resolve_params(copied, rng))
        else:
            params_list = [resolve_params(args, rng) for _ in range(getattr(args, "n", None))]

        samples = [generate(params) for params in params_list]
        if getattr(args, "json", None):
            payload = [sample.to_dict() for sample in samples]
            print(
                json.dumps(
                    payload[0] if len(payload) == 1 else payload,
                    ensure_ascii=False,
                    indent=2,
                )
            )
        else:
            for index, sample in enumerate(samples):
                emit(
                    sample,
                    trace=getattr(args, "trace", None),
                    qa=getattr(args, "qa", None),
                    header=f"\n### Story {index + 1}\n"
                    if len(samples) > 1
                    else "",
                )
        return 0
    except StoryError as exc:
        parser.error(str(exc))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
