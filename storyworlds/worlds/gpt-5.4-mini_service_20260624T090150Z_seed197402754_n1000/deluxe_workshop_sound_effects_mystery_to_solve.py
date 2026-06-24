#!/usr/bin/env python3
"""
A small Storyweavers world: a deluxe workshop bedtime mystery with gentle sound
effects and repetition.

Premise:
- A child and a grown-up are in a workshop at bedtime.
- A quiet mystery: something keeps making a soft sound.
- The child wants to solve it before sleep.

World logic:
- Soundy tools and objects can be placed, nudged, and covered.
- One hidden source can be revealed by careful checking.
- Repetition is used in narration as a bedtime-story rhythm.
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


# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------


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
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    placed_in: Optional[str] = None
    hidden_in: Optional[str] = None
    openable: bool = False
    open: bool = False
    deluxe: bool = False
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    child: object | None = None
    grownup: object | None = None
    hidden: object | None = None
    mystery: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
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
class Workshop:
    place: str = "the workshop"
    bedtime: bool = True
    setting: object | None = None
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
class Clue:
    label: str
    sound: str
    source: str
    reveal: str
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


@dataclass
class StoryParams:
    clue: str
    name: str
    gender: str
    grownup: str
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


class World:
    def __init__(self, setting: Workshop) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[str] = set()

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
        import copy
        c = World(self.setting)
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.facts = dict(self.facts)
        c.paragraphs = [[]]
        return c


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

CLUES = {
    "tiny bell": Clue(
        label="tiny bell",
        sound="ting-ting",
        source="a ribbon tied to a drawer knob",
        reveal="the ribbon had been brushing the knob when the door moved",
    ),
    "loose gear": Clue(
        label="loose gear",
        sound="click-clack",
        source="a small gear in a music box",
        reveal="the gear was bumping softly inside the music box",
    ),
    "wind-up toy": Clue(
        label="wind-up toy",
        sound="whirr-whirr",
        source="a toy hidden under a cloth",
        reveal="the toy was winding down under the cloth",
    ),
}

GIRL_NAMES = ["Mina", "Lily", "Nora", "Ivy", "Maya"]
BOY_NAMES = ["Leo", "Owen", "Finn", "Theo", "Max"]
GROWNUPS = {"mother": "mom", "father": "dad"}


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% A clue is solvable when its source can be revealed by opening or moving one thing.
solvable(C) :- clue(C), has_source(C), revealable(C).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for cid, clue in CLUES.items():
        lines.append(asp.fact("clue", cid))
        lines.append(asp.fact("sound", cid, clue.sound))
        lines.append(asp.fact("has_source", cid))
        lines.append(asp.fact("revealable", cid))
    return "\n".join(lines)

def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"

def asp_valid_clues() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show solvable/1."))
    return sorted(set(asp.atoms(model, "solvable")))


# ---------------------------------------------------------------------------
# Story helpers
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Bedtime workshop mystery with sound effects and repetition."
    )
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--grownup", choices=["mother", "father"])
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
    clue = getattr(args, "clue", None) or rng.choice(sorted(CLUES))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    if getattr(args, "name", None):
        name = getattr(args, "name", None)
    else:
        name = rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    grownup = getattr(args, "grownup", None) or rng.choice(["mother", "father"])
    return StoryParams(clue=clue, name=name, gender=gender, grownup=grownup)


def syllable_sound(clue: Clue) -> str:
    return clue.sound


def generate_story(world: World) -> None:
    child = world.get("child")
    grownup = world.get("grownup")
    clue = _safe_lookup(CLUES, world.facts.get("clue"))

    world.say(f"At bedtime in the deluxe workshop, {child.id} listened very, very carefully.")
    world.say(f"Tick-tick. {syllable_sound(clue)}. Tick-tick. The sound came again, soft as a whisper.")
    world.say(f'"What is that sound?" {child.id} asked. "What is that sound?"')

    world.para()
    world.say(f"{grownup.label.capitalize()} smiled and held a finger to {grownup.pronoun('possessive')} lips.")
    world.say(f'"Let us look and look," {grownup.pronoun()} said. "Slowly, slowly."')
    world.say(f"{child.id} opened a drawer, then another drawer, but the sound was still there: {syllable_sound(clue)}.")

    world.para()
    world.say(f"{child.id} followed the little sound to a shiny corner of the workshop.")
    world.say(f"There sat a deluxe little box, and inside it was the mystery.")
    world.say(f"{clue.reveal}. {syllable_sound(clue)} went the last tiny tap, then stopped.")

    world.para()
    world.say(f'"Oh!" {child.id} said. "It was hiding in the {clue.label}!"')
    world.say(f"{grownup.label.capitalize()} laughed softly. " + f'"We found it, we found it," {grownup.pronoun()} said.')
    world.say(f"The workshop grew quiet and warm. Quiet and warm. And {child.id} was ready for sleep.")


def story_qa(world: World) -> list[QAItem]:
    child = world.get("child")
    grownup = world.get("grownup")
    clue = _safe_lookup(CLUES, world.facts.get("clue"))
    return [
        QAItem(
            question=f"What kind of place was the story set in?",
            answer="It was set in a workshop, and it was a bedtime story with a gentle mystery."
        ),
        QAItem(
            question=f"What sound kept coming back while {child.id} looked for the mystery?",
            answer=f'The sound kept coming back like {clue.sound}. The story repeats it so it feels soft and secret.'
        ),
        QAItem(
            question=f"How did {child.id} and {grownup.label} solve the mystery?",
            answer=f"They looked slowly and carefully, then found that the sound came from {clue.source}."
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    clue = _safe_lookup(CLUES, world.facts.get("clue"))
    return [
        QAItem(
            question="What does deluxe mean?",
            answer="Deluxe means fancy, special, and made to feel extra nice."
        ),
        QAItem(
            question="What is a workshop?",
            answer="A workshop is a room where people build, fix, or make things."
        ),
        QAItem(
            question="Why do stories repeat words sometimes?",
            answer="Stories repeat words to make them feel musical, soothing, and easy to remember."
        ),
        QAItem(
            question="What is a mystery?",
            answer="A mystery is something puzzling that people try to figure out."
        ),
        QAItem(
            question=f"What made the clue sound special?",
            answer=f"It was a tiny sound, {clue.sound}, which sounded gentle and helped point to the hidden source."
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.kind:
            bits.append(f"kind={e.kind}")
        if e.type:
            bits.append(f"type={e.type}")
        if e.placed_in:
            bits.append(f"placed_in={e.placed_in}")
        if e.hidden_in:
            bits.append(f"hidden_in={e.hidden_in}")
        if e.deluxe:
            bits.append("deluxe=True")
        lines.append(f"  {e.id}: " + ", ".join(bits))
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    out = ["== Story questions =="]
    for qa in sample.story_qa:
        out.append(f"Q: {qa.question}")
        out.append(f"A: {qa.answer}")
    out.append("")
    out.append("== World knowledge questions ==")
    for qa in sample.world_qa:
        out.append(f"Q: {qa.question}")
        out.append(f"A: {qa.answer}")
    return "\n".join(out)


def generate(params: StoryParams) -> StorySample:
    setting = Workshop()
    world = World(setting)

    child = world.add(Entity(id=params.name, kind="character", type=params.gender, deluxe=True))
    grownup = world.add(Entity(
        id=_safe_lookup(GROWNUPS, params.grownup),
        kind="character",
        type=params.grownup,
        label=_safe_lookup(GROWNUPS, params.grownup),
    ))
    mystery = world.add(Entity(
        id="mystery_box",
        kind="thing",
        type="box",
        label="deluxe little box",
        phrase="a deluxe little box",
        openable=True,
        open=False,
        deluxe=True,
    ))
    hidden = world.add(Entity(
        id="hidden_clue",
        kind="thing",
        type=params.clue,
        label=_safe_lookup(CLUES, params.clue).label,
        hidden_in=mystery.id,
    ))

    world.facts = {"clue": params.clue, "child": child.id, "grownup": grownup.id}

    # Simulate the story beats.
    generate_story(world)

    return StorySample(
        params=params,
        story=world.render(),
        prompts=[
            f'Write a bedtime story in a deluxe workshop where a child hears "{_safe_lookup(CLUES, params.clue).sound}" and solves a mystery.',
            f"Tell a gentle repeat-after-me story about {child.id} and {grownup.label} finding the source of a mysterious sound.",
            f'Write a small story with the words "deluxe", "workshop", and "{_safe_lookup(CLUES, params.clue).label}".',
        ],
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


# ---------------------------------------------------------------------------
# ASP verification / selection
# ---------------------------------------------------------------------------

def asp_verify() -> int:
    import asp
    py = set((k,) for k in CLUES)
    cl = set(asp_valid_clues())
    if py == cl:
        print(f"OK: clingo gate matches Python registry ({len(py)} clues).")
        return 0
    print("MISMATCH between clingo and Python registries:")
    print("  only in python:", sorted(py - cl))
    print("  only in clingo:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

CURATED = [
    StoryParams(clue="tiny bell", name="Mina", gender="girl", grownup="mother"),
    StoryParams(clue="loose gear", name="Leo", gender="boy", grownup="father"),
    StoryParams(clue="wind-up toy", name="Nora", gender="girl", grownup="mother"),
]


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
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
        print(asp_program("#show solvable/1."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        print(asp_valid_clues())
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 50):
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
        header = ""
        if getattr(args, "all", None):
            p = sample.params
            header = f"### {p.name}: {p.clue} in the workshop"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
