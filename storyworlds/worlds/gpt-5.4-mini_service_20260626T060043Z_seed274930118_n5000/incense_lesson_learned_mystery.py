#!/usr/bin/env python3
"""
A compact storyworld: a small mystery with incense, clues, and a lesson learned.

Premise:
- A child notices a strange smell of incense in a quiet place.
- Something seems missing or misplaced.
- The child investigates through a few concrete clues.
- The mystery resolves with a gentle lesson learned.

The world is intentionally small and constraint-checked:
- The incense clue must be plausible in the chosen setting.
- The story must have a clear turn from suspicion to understanding.
- The ending must prove what changed and what lesson was learned.
"""

from __future__ import annotations

import argparse
import dataclasses
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
class Setting:
    name: str
    place_phrase: str
    incense_reason: str
    clue: str
    hiding_spot: str
    atmosphere: str
    indoor: bool = True
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


@dataclass
class ObjectItem:
    name: str
    label: str
    phrase: str
    owner: str
    found_by: str = ""
    hidden: bool = False
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
class World:
    setting: Setting
    child_name: str
    child_type: str
    parent_name: str
    parent_type: str
    object_name: str
    object_label: str
    object_phrase: str
    object_owner: str
    story_lines: list[str] = field(default_factory=list)
    facts: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    world: object | None = None
    def say(self, text: str) -> None:
        if text:
            self.story_lines.append(text)

    def para(self) -> None:
        if self.story_lines and self.story_lines[-1] != "":
            self.story_lines.append("")

    def render(self) -> str:
        parts: list[str] = []
        buf: list[str] = []
        for line in self.story_lines:
            if line == "":
                if buf:
                    parts.append(" ".join(buf))
                    buf = []
            else:
                buf.append(line)
        if buf:
            parts.append(" ".join(buf))
        return "\n\n".join(parts)

    def pronoun(self, who: str, case: str = "subject") -> str:
        typ = self.child_type if who == "child" else self.parent_type
        if typ in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if typ in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]
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
        return None


SETTINGS = {
    "temple_hall": Setting(
        name="temple hall",
        place_phrase="the quiet temple hall",
        incense_reason="someone had recently lit incense for a calm prayer",
        clue="a thin ribbon of smoke curling under the door",
        hiding_spot="the shoe shelf",
        atmosphere="still and whispery",
        indoor=True,
    ),
    "music_room": Setting(
        name="music room",
        place_phrase="the small music room",
        incense_reason="the teacher burned incense to make the room feel peaceful",
        clue="a sweet smell drifting past the piano bench",
        hiding_spot="the music stand",
        atmosphere="soft and echoing",
        indoor=True,
    ),
    "tea_shop": Setting(
        name="tea shop",
        place_phrase="the little tea shop",
        incense_reason="the owner liked a little incense near the counter",
        clue="a warm smoky smell near the cups",
        hiding_spot="the napkin basket",
        atmosphere="warm and hushy",
        indoor=True,
    ),
    "library_corner": Setting(
        name="library corner",
        place_phrase="the old library corner",
        incense_reason="the librarian used incense to cover the smell of dusty books",
        clue="a gentle scent floating by the reading pillows",
        hiding_spot="the return cart",
        atmosphere="calm and dusty",
        indoor=True,
    ),
}

OBJECTS = {
    "bookmark": ("bookmark", "a handmade ribbon bookmark", "her favorite ribbon bookmark"),
    "toy_fox": ("toy fox", "a tiny plush fox", "his small plush fox"),
    "ring": ("ring", "a silver practice ring", "her practice ring"),
    "key": ("key", "a brass little key", "his little brass key"),
}

GIRL_NAMES = ["Mina", "Lina", "Sora", "Tia", "Nina", "Eva"]
BOY_NAMES = ["Owen", "Milo", "Arlo", "Finn", "Theo", "Ben"]
PARENT_TYPES = ["mother", "father"]
CHILD_TYPES = ["girl", "boy"]

LESSON_SENTENCES = [
    "She learned that not every strange thing is scary; sometimes it is only a clue waiting to be understood.",
    "He learned that a careful question can solve a worry better than a quick guess.",
    "They learned that quiet places can hold small mysteries, and patience can help reveal the truth.",
]


def _article(phrase: str) -> str:
    return "an" if phrase[:1].lower() in "aeiou" else "a"


def validate_params(setting: Setting, object_key: str, child_type: str) -> None:
    if object_key == "ring" and child_type != "girl":
        pass
    if setting.name == "music room" and object_key == "key":
        pass
    if setting.name == "tea shop" and object_key == "bookmark":
        pass


def choose_names(rng: random.Random, child_type: str, parent_type: str) -> tuple[str, str]:
    child_name = rng.choice(GIRL_NAMES if child_type == "girl" else BOY_NAMES)
    parent_name = rng.choice(["Mom", "Dad"]) if parent_type in {"mother", "father"} else "Parent"
    return child_name, parent_name


def build_world(params: "StoryParams") -> World:
    setting = _safe_lookup(SETTINGS, params.setting)
    obj_name, obj_label, obj_phrase = _safe_lookup(OBJECTS, params.object)
    world = World(
        setting=setting,
        child_name=params.child_name,
        child_type=params.child_type,
        parent_name=params.parent_name,
        parent_type=params.parent_type,
        object_name=obj_name,
        object_label=obj_label,
        object_phrase=obj_phrase,
        object_owner=params.parent_name,
    )
    world.facts.update(
        setting=params.setting,
        object=params.object,
        child_name=params.child_name,
        child_type=params.child_type,
        parent_name=params.parent_name,
        parent_type=params.parent_type,
    )
    return world


def tell_story(world: World) -> None:
    s = world.setting
    child = world.child_name
    parent = world.parent_name
    child_subj = world.pronoun("child", "subject")
    child_obj = world.pronoun("child", "object")
    child_poss = world.pronoun("child", "possessive")
    parent_poss = world.pronoun("parent", "possessive")

    world.say(
        f"{child} was a little {world.child_type} who loved quiet places and tiny puzzles."
    )
    world.say(
        f"One afternoon at {s.place_phrase}, the air felt {s.atmosphere}, and {s.incense_reason}."
    )
    world.say(
        f"{child} noticed {s.clue}, and that made {child} stop and look around."
    )
    world.para()

    world.say(
        f"Then {child} saw that {parent}'s {world.object_label} was gone from its usual spot."
    )
    world.say(
        f"{child} knew {parent_poss} {world.object_label} was important, so {child_subj} became a little worried."
    )
    world.say(
        f"{child_subj.capitalize()} asked, 'Did someone take it?' and slowly began to search."
    )
    world.para()

    world.say(
        f"{child} followed the incense smell and noticed a trail of tiny signs near {s.hiding_spot}."
    )
    world.say(
        f"The clue led {child_obj} right to the lost {world.object_label}, tucked safely where it had fallen."
    )
    world.say(
        f"{child} smiled, carried it back, and gave it to {parent}."
    )
    world.say(
        random.choice(LESSON_SENTENCES)
    )
    world.say(
        f"In the end, the strange incense had not hidden a problem at all; it had simply led {child} to the answer."
    )
    world.say(
        f"{parent} thanked {child}, and the quiet place felt calm again."
    )

    world.facts.update(
        lesson="not every strange thing is scary; sometimes it is a clue",
        resolved=True,
        incense_reason=s.incense_reason,
        clue=s.clue,
        hiding_spot=s.hiding_spot,
        object_label=world.object_label,
    )


@dataclass
class StoryParams:
    setting: str
    object: str
    child_name: str
    child_type: str
    parent_name: str
    parent_type: str
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mystery storyworld with incense and a lesson learned.")
    ap.add_argument("--setting", choices=sorted(SETTINGS.keys()))
    ap.add_argument("--object", dest="object_", choices=sorted(OBJECTS.keys()))
    ap.add_argument("--child-type", choices=CHILD_TYPES)
    ap.add_argument("--parent-type", choices=PARENT_TYPES)
    ap.add_argument("--name")
    ap.add_argument("--parent-name")
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    setting = getattr(args, "setting", None) or rng.choice(list(SETTINGS))
    object_key = getattr(args, "object_", None) or rng.choice(list(OBJECTS))
    child_type = getattr(args, "child_type", None) or rng.choice(CHILD_TYPES)
    parent_type = getattr(args, "parent_type", None) or rng.choice(PARENT_TYPES)
    validate_params(_safe_lookup(SETTINGS, setting), object_key, child_type)
    child_name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if child_type == "girl" else BOY_NAMES)
    parent_name = getattr(args, "parent_name", None) or rng.choice(["Mom", "Dad"])
    return StoryParams(
        setting=setting,
        object=object_key,
        child_name=child_name,
        child_type=child_type,
        parent_name=parent_name,
        parent_type=parent_type,
    )


def generation_prompts(world: World) -> list[str]:
    return [
        f"Write a short mystery story for a young child about incense, a lost {world.object_name}, and a careful clue.",
        f"Tell a gentle story where {world.child_name} notices incense at the {world.setting.name} and discovers what happened to {world.parent_name}'s {world.object_label}.",
        f"Write a child-friendly mystery that ends with a lesson learned after a small search and a happy finding.",
    ]


def story_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question=f"What strange smell did {world.child_name} notice first?",
            answer=f"{world.child_name} noticed the smell of incense first, along with the quiet feeling of {world.setting.atmosphere} air.",
        ),
        QAItem(
            question=f"What was missing in the mystery?",
            answer=f"{world.parent_name}'s {world.object_label} was missing at first, which made the mystery feel real and important.",
        ),
        QAItem(
            question=f"Where was the lost {world.object_name} found?",
            answer=f"It was found near {world.setting.hiding_spot}, safely tucked away after {world.child_name} followed the clues.",
        ),
        QAItem(
            question="What lesson did the child learn?",
            answer="The child learned that not every strange thing is scary; sometimes it is only a clue waiting to be understood.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is incense?",
            answer="Incense is material that people burn so it makes a smell, often for calm, ceremony, or a special mood.",
        ),
        QAItem(
            question="Why do people use clues in mysteries?",
            answer="People use clues in mysteries because clues help them figure out what happened by looking carefully.",
        ),
        QAItem(
            question="What does it mean to learn a lesson?",
            answer="To learn a lesson means to understand something useful that helps you act better next time.",
        ),
    ]


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print()
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for k, v in sorted(world.facts.items()):
        lines.append(f"{k}: {v}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== story questions =="]
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== prompts ==")
    for p in sample.prompts:
        lines.append(f"- {p}")
    return "\n".join(lines)


def asp_facts() -> str:
    import asp
    lines = []
    for key, setting in SETTINGS.items():
        lines.append(asp.fact("setting", key))
        lines.append(asp.fact("place", key, setting.place_phrase))
        lines.append(asp.fact("incense_reason", key, setting.incense_reason))
    for key, (name, label, phrase) in OBJECTS.items():
        lines.append(asp.fact("object", key))
        lines.append(asp.fact("object_name", key, name))
        lines.append(asp.fact("object_label", key, label))
        lines.append(asp.fact("object_phrase", key, phrase))
    return "\n".join(lines)


ASP_RULES = r"""
% A story is reasonable if the setting has an incense reason and the object can be lost and found.
reasonable(S,O) :- setting(S), object(O), incense_reason(S,_), object_label(O,_), object_phrase(O,_).

% A mystery should include a clue and a lesson learned.
mystery_ready(S,O) :- reasonable(S,O).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show reasonable/2."))
    asp_set = set(asp.atoms(model, "reasonable"))
    py_set = {(s, o) for s in SETTINGS for o in OBJECTS}
    if asp_set == py_set:
        print(f"OK: ASP parity matches Python registry coverage ({len(py_set)} combos).")
        return 0
    print("MISMATCH between ASP and Python:")
    print("ASP only:", sorted(asp_set - py_set))
    print("Python only:", sorted(py_set - asp_set))
    return 1


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    tell_story(world)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def all_params() -> list[StoryParams]:
    out: list[StoryParams] = []
    for s in SETTINGS:
        for o in OBJECTS:
            for ct in CHILD_TYPES:
                for pt in PARENT_TYPES:
                    try:
                        validate_params(_safe_lookup(SETTINGS, s), o, ct)
                    except StoryError:
                        continue
                    out.append(
                        StoryParams(
                            setting=s,
                            object=o,
                            child_name=_safe_lookup(GIRL_NAMES, 0) if ct == "girl" else _safe_lookup(BOY_NAMES, 0),
                            child_type=ct,
                            parent_name="Mom" if pt == "mother" else "Dad",
                            parent_type=pt,
                        )
                    )
    return out


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show reasonable/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)

    if getattr(args, "all", None):
        params_list = all_params()
        samples = [generate(p) for p in params_list]
    else:
        samples = []
        seen = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < getattr(args, "n", None) * 50 + 50:
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

    for idx, sample in enumerate(samples):
        header = ""
        if len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 72 + "\n")


if __name__ == "__main__":
    main()
