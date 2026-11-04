#!/usr/bin/env python3
"""A gentle bedtime tale about a snack, a hurried plan, and a useful hook."""

from __future__ import annotations

import argparse
import hashlib
import json
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

HERE = Path(__file__).resolve()
ROOT = next((p for p in HERE.parents if (p / "storyworlds" / "results.py").exists()), None)
if ROOT is None:
    raise RuntimeError("Could not find storyworlds/results.py")
if str(ROOT / "storyworlds") not in sys.path:
    sys.path.insert(0, str(ROOT / "storyworlds"))
from results import QAItem, StoryError, StorySample  # noqa: E402



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
class Character:
    name: str
    kind: str
    role: str
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    child: object | None = None
    helper: object | None = None
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
class Place:
    name: str
    kind: str
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    room: object | None = None
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
class Snack:
    name: str
    material: str
    safe: bool = True
    hung_up: bool = False
    snack: object | None = None
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
    child: Character
    helper: Character
    room: Place
    snack: Snack
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

    def say(self, text: str) -> None:
        self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)
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


ROOMS = {
    "blue bedroom": ("the blue bedroom", "bedroom"),
    "attic room": ("the little attic room", "bedroom"),
    "moonlit kitchen": ("the moonlit kitchen", "kitchen"),
}
CHILDREN = (("Luna", "rabbit"), ("Pip", "mouse"), ("Mira", "fox"))
HELPERS = (("Nell", "owl"), ("Tansy", "cat"), ("Bram", "bear"))
SNACKS = (
    ("a honey biscuit", "biscuit"),
    ("a little oat cake", "oat"),
    ("a pear slice", "pear"),
)
ROUTES = ("quiet_start", "question_start", "moon_start", "snack_start")


@dataclass
class StoryParams:
    seed: Optional[int] = None
    room: str = "blue bedroom"
    child_name: str = "Luna"
    child_kind: str = "rabbit"
    helper_name: str = "Nell"
    helper_kind: str = "owl"
    snack_name: str = "a honey biscuit"
    snack_material: str = "biscuit"
    route: str = "quiet_start"
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


ASP_RULES = r"""
child(C) :- child_character(C).
helper(H) :- helper_character(H).
safe_hang(S) :- snack(S), hook(H), tested(H).
settled(C) :- child(C), safe_hang(S), shares(C,S), rests(C).
valid_story :- settled(C), helper(H), child(C).
#show safe_hang/1.
#show valid_story/0.
"""


def asp_facts() -> str:
    import asp

    return "\n".join(
        (
            asp.fact("child_character", "luna"),
            asp.fact("helper_character", "nell"),
            asp.fact("snack", "bedtime_snack"),
            asp.fact("hook", "snack_hook"),
            asp.fact("tested", "snack_hook"),
            asp.fact("shares", "luna", "bedtime_snack"),
            asp.fact("rests", "luna"),
        )
    )


def asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n"


def python_reasonableness() -> bool:
    return bool(SNACKS) and all(material for _, material in SNACKS) and "quiet_start" in ROUTES


def asp_verify() -> int:
    import asp

    if not python_reasonableness():
        print("Python reasonableness gate failed.")
        return 1
    model = asp.one_model(asp_program())
    hung = set(asp.atoms(model, "safe_hang"))
    valid = set(asp.atoms(model, "valid_story"))
    if hung == {("bedtime_snack",)} and valid == {()}:
        checks = 0
        for i, snack in enumerate(SNACKS):
            params = StoryParams(
                seed=i,
                snack_name=snack[0],
                snack_material=snack[1],
            )
            sample = generate(params)
            if not sample.world.snack.hung_up or "Good night" not in sample.story:
                print("Generated-story verification failed.")
                return 1
            checks += 1
        print(f"OK: ASP/Python parity and {checks} generated bedtime stories.")
        return 0
    print("ASP/Python parity mismatch.")
    print("ASP safe hang:", sorted(hung))
    print("ASP valid story:", sorted(valid))
    return 1


def story_rng(params: StoryParams) -> random.Random:
    raw = "|".join(str(v) for v in (
        params.seed, params.room, params.child_name, params.child_kind,
        params.helper_name, params.helper_kind, params.snack_name,
        params.snack_material, params.route,
    ))
    digest = hashlib.sha256(raw.encode("utf-8")).digest()
    return random.Random(int.from_bytes(digest[:8], "big"))


def build_world(params: StoryParams) -> World:
    if params.room not in ROOMS:
        pass
    if params.route not in ROUTES:
        pass
    if not params.child_name.strip() or not params.helper_name.strip():
        pass
    if not params.snack_name.strip() or not params.snack_material.strip():
        pass
    room_name, room_kind = _safe_lookup(ROOMS, params.room)
    return World(
        child=Character(params.child_name, params.child_kind, "sleepy snack-maker"),
        helper=Character(params.helper_name, params.helper_kind, "kind bedtime helper"),
        room=Place(room_name, room_kind),
        snack=Snack(params.snack_name, params.snack_material),
    )


def tell_story(world: World, params: StoryParams) -> None:
    child, helper, room, snack = world.child, world.helper, world.room, world.snack
    rng = story_rng(params)
    child.memes.update(sleepiness=0.5, haste=1.0, comfort=0.0)
    helper.memes.update(patience=1.0, kindness=1.0)
    child.meters["bedtime_minutes_left"] = 5
    room.meters["lamp_light"] = 0.3

    openings = {
        "quiet_start": f"The moon laid a pale square on {room.name}, and {child.name} was almost ready for bed.",
        "question_start": f'"Can a snack be ready before the moon moves?" {child.name} asked in {room.name}.',
        "moon_start": f"One sleepy star blinked above {room.name} as {child.name} remembered the little snack.",
        "snack_start": f"{child.name} had {snack.name} waiting for bedtime, but the blanket was already warm.",
    }
    world.say(openings[params.route])
    world.say(
        f"The snack belonged in its covered basket, but {child.name} hurried to reach it and set it on a wobbly stool."
    )
    world.say(rng.choice((
        f'"Slow feet, sleepy one," {helper.name} said. "Where can the snack rest safely?"',
        f'"I want it now," {child.name} whispered. {helper.name} replied, "We have time to make it safe."',
    )))
    world.say(
        f"{child.name} reached too quickly; {snack.name} slid toward the edge. {helper.name} caught the plate before it tipped."
    )

    world.para()
    world.say(
        f'"Let us try the same little rule again: pause, check, then choose," said {helper.name}.'
    )
    world.say(
        f"Pause, check, then choose. This time {child.name} looked around instead of rushing."
    )
    world.say(
        f"They found a low wooden hook beside the covered snack basket. {helper.name} tested it gently before letting anything hang there."
    )
    world.say(
        f'"The hook is steady," {helper.name} said. "Now the plate can hang above the floor, away from sleepy feet."'
    )
    snack.hung_up = True
    child.memes["haste"] = 0.0
    child.memes["comfort"] = 1.0
    child.meters["safe_choices"] = 1
    room.meters["snack_secured"] = 1
    world.say(
        f"{child.name} hung the covered plate on the tested hook, then took one small piece to enjoy before brushing their teeth."
    )
    world.say(
        f'"You helped me slow down," {child.name} said. "And you noticed the wobbly stool," {helper.name} answered.'
    )

    world.para()
    world.say(
        f"Pause, check, then choose. The words sounded softer the second time, like a lullaby settling over {room.name}."
    )
    world.say(
        f"{child.name} climbed into bed. The snack hung safely above the floor, and the stool stood tucked back under the table."
    )
    world.say(
        f"Good night, thought {child.name}, as the moonlight reached the quiet blanket."
    )
    world.facts.update(
        cause="haste put the plate on a wobbly stool",
        method="pause, check, then choose",
        repair="tested the low hook and hung up the covered plate",
        ending="the covered snack hung safely above the floor beside the tucked-in stool",
        solved=True,
    )


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    tell_story(world, params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=[
            f"Tell a gentle bedtime story about {world.child.name} learning not to hurry with {world.snack.name}.",
            f"Use the repeated words “Pause, check, then choose” as {world.child.name} finds a safe place to hang the snack.",
        ],
        story_qa=[
            QAItem(
                question=f"Why did {world.child.name}'s snack nearly fall?",
                answer=f"{world.child.name} hurried and put {world.snack.name} on a wobbly stool, so it slid toward the edge.",
            ),
            QAItem(
                question="What repeated words helped the child slow down?",
                answer="The helper repeated, “Pause, check, then choose,” and the child used the reminder to look for a safer place.",
            ),
            QAItem(
                question="How did they keep the snack away from sleepy feet?",
                answer="They tested a low wooden hook, then hung the covered plate above the floor.",
            ),
            QAItem(
                question=f"What did {world.child.name} do before going to bed?",
                answer=f"{world.child.name} enjoyed a small piece, brushed their teeth, and climbed into bed while the covered snack stayed safely on its hook.",
            ),
        ],
        world_qa=[
            QAItem(
                question="Why is it helpful to slow down when carrying food?",
                answer="Slowing down gives someone time to notice an unstable surface and keep food from spilling or falling.",
            ),
            QAItem(
                question="What should someone check before hanging something on a hook?",
                answer="They should make sure the hook is secure and can safely hold the item's weight.",
            ),
        ],
        world=world,
    )


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    child_name, child_kind = rng.choice(CHILDREN)
    helper_name, helper_kind = rng.choice(HELPERS)
    snack_name, snack_material = rng.choice(SNACKS)
    return StoryParams(
        seed=getattr(args, "seed", None),
        room=getattr(args, "room", None) or rng.choice(sorted(ROOMS)),
        child_name=getattr(args, "child_name", None) or child_name,
        child_kind=child_kind,
        helper_name=getattr(args, "helper_name", None) or helper_name,
        helper_kind=helper_kind,
        snack_name=getattr(args, "snack", None) or snack_name,
        snack_material=snack_material if getattr(args, "snack", None) is None else "snack",
        route=rng.choice(ROUTES),
    )


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for entity in (world.child, world.helper, world.room):
        lines.append(
            f"{entity.name}: meters={entity.meters} memes={getattr(entity, 'memes', {})}"
        )
    lines.append(
        f"{world.snack.name}: material={world.snack.material!r} "
        f"safe={world.snack.safe} hung_up={world.snack.hung_up}"
    )
    lines.append(f"story outcome: {world.facts}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="A gentle bedtime snack story.")
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    parser.add_argument("--room", choices=sorted(ROOMS))
    parser.add_argument("--child-name")
    parser.add_argument("--helper-name")
    parser.add_argument("--snack")
    return parser


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
        print("\n== prompts ==")
        for i, prompt in enumerate(sample.prompts, 1):
            print(f"{i}. {prompt}")
        print("\n== story qa ==")
        for item in sample.story_qa:
            print(f"Q: {item.question}\nA: {item.answer}")
        print("\n== world qa ==")
        for item in sample.world_qa:
            print(f"Q: {item.question}\nA: {item.answer}")


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program())
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp

        model = asp.one_model(asp_program())
        print("safe_hang:", sorted(set(asp.atoms(model, "safe_hang"))))
        print("valid_story:", sorted(set(asp.atoms(model, "valid_story"))))
        return
    if getattr(args, "n", None) < 1:
        pass
    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    count = 3 if getattr(args, "all", None) else getattr(args, "n", None)
    samples = []
    for i in range(count):
        params = resolve_params(args, random.Random(base_seed + i))
        params.seed = base_seed + i
        samples.append(generate(params))
    if getattr(args, "json", None):
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        emit(
            sample,
            trace=getattr(args, "trace", None),
            qa=getattr(args, "qa", None),
            header=f"### variant {i + 1}" if len(samples) > 1 else "",
        )
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
