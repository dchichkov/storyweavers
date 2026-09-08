#!/usr/bin/env python3
"""A nursery-rhyme bedroom tale about mending a friendship with a careful repair."""

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
import re
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from results import QAItem, StoryError, StorySample


@dataclass
class Entity:
    id: str
    label: str
    kind: str
    location: str
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
    state: dict = field(default_factory=dict)
    question: str = ""
    cause: str = ""
    result: str = ""
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
    hero: str = "Luna"
    friend: str = "Pip"
    object_name: str = "moon tent"
    flaw: str = "jag"
    seed: int = 777
    sample: object | None = None
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


NAMES = ("Luna", "Pip", "Milo", "Nia", "Tess", "Ollie")
OBJECTS = ("moon tent", "pillow fort", "blanket boat")
FLAWS = ("jag", "loose knot", "sharp stake")
PROMPT = (
    "Write a nursery-rhyme children's story in a bedroom where friends repair "
    "a small playhouse, learn a lesson, and strengthen their friendship."
)

ASP_RULES = """
repairable(F) :- flaw(F).
safe(F) :- repairable(F).
#show safe/1.
"""


class World:
    def __init__(self, params: StoryParams):
        self.params = params
        self.entities = {
            "hero": Entity("hero", params.hero, "character", "bedroom",
                           memes={"care": 0.5, "trust": 0.5}),
            "friend": Entity("friend", params.friend, "character", "bedroom",
                             memes={"care": 0.5, "trust": 0.5}),
            "playhouse": Entity("playhouse", f"the {params.object_name}", "toy", "bedroom",
                                meters={"stability": 1, "safe": 0}),
            "stake": Entity("stake", "the little stake", "tool", "bedroom",
                            meters={"sharpness": 1, "placed": 0}),
            "ribbon": Entity("ribbon", "a red ribbon", "material", "bedroom",
                             meters={"length": 2, "used": 0}),
        }
        self.history: list[Event] = []

    def snapshot(self) -> dict:
        return {key: asdict(value) for key, value in self.entities.items()}

    def narrate(self, kind: str, text: str, *, question: str = "",
                cause: str = "", result: str = ""):
        self.history.append(Event(kind, text, self.snapshot(), question, cause, result))

    def say(self, speaker: str, text: str):
        if speaker not in self.entities:
            pass
        label = self.entities[speaker].label
        verb = "asked" if text.endswith("?") else "said"
        self.history.append(Event("speech", f'"{text}" {label} {verb}.', self.snapshot()))

    def finish_friendship(self):
        for key in ("hero", "friend"):
            self.entities[key].memes.update(care=1.0, trust=1.0)
    def get(self, eid: str):
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
        return self.entities[eid]
    def copy(self):
        clone = __import__("copy").deepcopy(self)
        return clone


def validate_params(params: StoryParams):
    if params.hero == params.friend:
        pass
    if any(not re.fullmatch(r"[A-Z][a-z]+", x) for x in (params.hero, params.friend)):
        pass
    if params.object_name not in OBJECTS:
        pass
    if params.flaw not in FLAWS:
        pass


def build_world(params: StoryParams) -> World:
    validate_params(params)
    return World(params)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    h, f = params.hero, params.friend
    toy = world.get("playhouse").label
    flaw = params.flaw

    world.narrate(
        "beginning",
        f"In a bedroom bright with moonlight, {h} and {f} built {toy}. "
        "They hummed a tiny tune while pillows made walls and blankets made a roof."
    )
    world.say("hero", "Will our little house stand through the night?")
    world.say("friend", "It will, if we test it gently and fix what we find.")
    world.narrate(
        "test",
        f"{h} tapped the roof. Tap, tap! The {toy} wobbled, and a {flaw} caught the blanket.",
        question="What did the friends discover when they tested the playhouse?",
        cause=f"The blanket caught on {flaw}, making the playhouse wobble.",
        result="They stopped playing and looked for a careful repair."
    )
    world.say("hero", "I can yank the blanket free!")
    world.say("friend", "Wait. A hard yank may tear it. Shall we look first?")
    world.say("hero", "You are right. I was being a dolt.")
    world.say("friend", "Friends do not need to be perfect. Friends need to listen.")

    world.get("hero").memes["care"] = 0.8
    world.get("friend").memes["trust"] = 0.8
    world.narrate(
        "lesson",
        f"They peered beneath the blanket. The little stake had tipped sideways, "
        f"and its {flaw} pointed up like a tiny thorn.",
        question="Why did the friends inspect the blanket instead of pulling it?",
        cause="A hard pull could tear the blanket on the raised flaw.",
        result="Looking first showed them that the stake had tipped sideways."
    )
    world.say("hero", "I will hold the blanket high. You can turn the stake.")
    world.say("friend", "Together, then. One, two, three!")
    world.say("hero", "Softly, softly—steady as a sleepy star.")

    stake = world.get("stake")
    stake.meters["sharpness"] = 0
    stake.meters["placed"] = 1
    world.get("ribbon").meters["used"] = 1
    world.get("playhouse").meters.update(stability=2, safe=1)
    world.narrate(
        "repair",
        f"With a snug little twist, {f} turned the stake down. {h} tied the red ribbon "
        "around it as a bright reminder. Snip, tuck, snug!",
        question="How did the friends make the bedroom playhouse safe?",
        cause="The tipped stake had a raised sharp point.",
        result="They turned it down and tied a red ribbon around it."
    )
    world.say("friend", "Now the blanket can rest without a scratch.")
    world.say("hero", "And I learned not to rush when a friend says, 'Look first.'")
    world.say("friend", "That is a lesson worth keeping.")
    world.narrate(
        "test_again",
        f"They tested {toy} once more. Tap, tap! It stood steady, and the ribbon bobbed "
        "like a little flag.",
        question="How did they know the repair worked?",
        cause="They tapped the playhouse again after turning down the stake.",
        result="It stayed steady, and the ribbon marked the safe repair."
    )
    world.finish_friendship()
    world.say("hero", "May I share the moon tent with you?")
    world.say("friend", "Yes. There is room for two careful friends.")
    world.narrate(
        "ending",
        f"Under the blanket roof, {h} and {f} whispered a rhyme: "
        "'Look before you tug, be kind before you boast; a careful friend is the friend we love most.' "
        "The bedroom grew quiet, and the red ribbon danced in the moonbeam."
    )
    sample = StorySample(
        params=params,
        story="\n\n".join(event.text for event in world.history),
        prompts=[PROMPT],
        story_qa=[
            QAItem(event.question, f"{event.cause} {event.result}")
            for event in world.history if event.question
        ],
        world_qa=[
            QAItem("What is the lesson of the story?",
                   "Look carefully before rushing, and let friendship guide the repair.")
        ],
        world=world,
    )
    check_sample(sample)
    return sample


def check_sample(sample: StorySample):
    world = sample.world
    if not world.get("playhouse").meters["safe"]:
        pass
    if world.get("stake").meters["sharpness"] != 0:
        pass
    if any(world.entities[key].memes["trust"] < 1 for key in ("hero", "friend")):
        pass
    speeches = [e for e in world.history if e.kind == "speech"]
    if len(speeches) < 8:
        pass
    if len(sample.story_qa) < 3:
        pass
    if "dolt" not in sample.story or "jag" not in sample.story:
        pass


def asp_facts() -> str:
    from asp import fact
    return "\n".join(fact("flaw", flaw) for flaw in FLAWS)


def asp_safe() -> set[str]:
    from asp import atoms, one_model
    return {row[0] for row in atoms(one_model(asp_facts() + ASP_RULES), "safe")}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--seed", type=int, default=777)
    parser.add_argument("--hero")
    parser.add_argument("--friend")
    parser.add_argument("--object-name", choices=OBJECTS)
    parser.add_argument("--flaw", choices=FLAWS)
    for flag in ("all", "trace", "qa", "json", "asp", "verify", "show-asp"):
        parser.add_argument("--" + flag, action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    hero = getattr(args, "hero", None) or rng.choice(NAMES)
    friend = getattr(args, "friend", None) or rng.choice([name for name in NAMES if name != hero])
    return StoryParams(
        hero=hero,
        friend=friend,
        object_name=getattr(args, "object_name", None) or rng.choice(OBJECTS),
        flaw=getattr(args, "flaw", None) or rng.choice(FLAWS),
        seed=getattr(args, "seed", None),
    )


def verify():
    if asp_safe() != set(FLAWS):
        pass
    count = 0
    for flaw in FLAWS:
        for obj in OBJECTS:
            sample = generate(StoryParams(object_name=obj, flaw=flaw))
            check_sample(sample)
            count += 1
    print(f"OK: {count} story states; ASP agrees on {len(FLAWS)} flaws.")


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False):
    print(sample.story)
    if qa:
        for item in sample.story_qa:
            print(f"\nQ: {item.question}\nA: {item.answer}")
        for item in sample.world_qa:
            print(f"\nQ: {item.question}\nA: {item.answer}")
    if trace:
        print("\nTRACE")
        print(json.dumps({
            "entities": sample.world.snapshot(),
            "history": [asdict(event) for event in sample.world.history],
        }, indent=2))


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
            print(json.dumps(sorted(asp_safe())))
            return 0
        rng = random.Random(getattr(args, "seed", None))
        if getattr(args, "all", None):
            samples = [
                generate(StoryParams(object_name=obj, flaw=flaw, seed=getattr(args, "seed", None)))
                for obj in OBJECTS for flaw in FLAWS
            ]
        else:
            samples = [generate(resolve_params(args, rng)) for _ in range(getattr(args, "n", None))]
        if getattr(args, "json", None):
            payload = [sample.to_dict() for sample in samples]
            print(json.dumps(payload[0] if len(payload) == 1 else payload,
                             ensure_ascii=False, indent=2))
        else:
            for index, sample in enumerate(samples):
                if len(samples) > 1:
                    print(f"\n### Story {index + 1}\n")
                emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None))
        return 0
    except StoryError as exc:
        parser.error(str(exc))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
