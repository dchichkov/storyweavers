#!/usr/bin/env python3
"""
storyworlds/worlds/ivy_google_ellipsis_inner_monologue_suspense_ghost.py
========================================================================

A small story world for a ghost-story mystery with inner monologue and suspense.

Seed inspiration:
- ivy
- google
- ellipsis

Premise:
A child named Ivy hears a soft ghostly presence in an old house. A note with an
ellipsis leaves her uneasy, so she uses Google to search for a way to help. The
search leads her to the attic, where she discovers what the ghost has been
missing.

The simulated world tracks:
- physical meters: chill, dust, glow, found, hidden
- emotional memes: fear, curiosity, suspense, relief, care, loneliness

The prose is driven by the state transitions:
- the note appears with an ellipsis
- Ivy's fear and curiosity rise
- Google gives a clue
- the attic search reduces suspense
- the ghost's loneliness resolves when the lost ribbon is returned
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

    ghost: object | None = None
    ivy: object | None = None
    note: object | None = None
    ribbon: object | None = None
    tablet: object | None = None
    def m(self, key: str) -> float:
        return self.meters.get(key, 0.0)

    def e(self, key: str) -> float:
        return self.memes.get(key, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        if self.type == "girl":
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type == "ghost":
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]
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
    place: str = "the old house"
    detail: str = "The old house was quiet except for a soft creak in the hall."
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
    place: str
    hero: str
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


def build_world(params: StoryParams) -> World:
    world = World(_safe_lookup(SETTINGS, params.place))
    ivy = world.add(Entity(
        id=params.hero,
        kind="character",
        type="girl",
        label="Ivy",
        meters={"chill": 0.0},
        memes={"fear": 0.0, "curiosity": 0.0, "suspense": 0.0, "relief": 0.0, "care": 0.0},
    ))
    ghost = world.add(Entity(
        id="ghost",
        kind="character",
        type="ghost",
        label="the ghost",
        meters={"glow": 0.0},
        memes={"loneliness": 1.0, "suspense": 0.0},
    ))
    note = world.add(Entity(
        id="note",
        type="note",
        label="note",
        phrase="a small note with three dots",
        meters={"hidden": 0.0},
    ))
    tablet = world.add(Entity(
        id="tablet",
        type="tablet",
        label="tablet",
        phrase="a little tablet with Google open",
    ))
    ribbon = world.add(Entity(
        id="ribbon",
        type="ribbon",
        label="blue ribbon",
        phrase="a faded blue ribbon",
        owner="ghost",
        meters={"hidden": 1.0},
    ))

    world.facts.update(ivy=ivy, ghost=ghost, note=note, tablet=tablet, ribbon=ribbon)
    return world


def scene_open(world: World) -> None:
    ivy = world.get("ivy")
    ghost = world.get("ghost")
    note = world.get("note")
    ivy.memes["curiosity"] += 1
    ivy.memes["fear"] += 1
    ghost.memes["suspense"] += 1
    world.say(
        f"Ivy was in {world.setting.place} when she noticed a little note on the stairs: "
        f'"Help me..."'
    )
    world.say(
        "The three dots made the house feel even quieter, and Ivy's thoughts hurried ahead of her. "
        "What if the whisper came back? What if the note meant she should not be there?"
    )
    note.meters["hidden"] = 0.0
    world.para()


def scene_google(world: World) -> None:
    ivy = world.get("ivy")
    ghost = world.get("ghost")
    tablet = world.get("tablet")
    ivy.memes["curiosity"] += 1
    ivy.memes["suspense"] += 1
    world.say(
        "Ivy picked up the tablet and typed her question into Google with careful fingers. "
        "Her heart thumped while the page loaded, and she tried to breathe slowly."
    )
    world.say(
        "The search said that some ghosts stay near a house because they lost something important. "
        "That made Ivy's worry soften into a plan."
    )
    ghost.memes["loneliness"] += 1
    tablet.meters["glow"] = 1.0
    world.para()


def scene_attic(world: World) -> None:
    ivy = world.get("ivy")
    ghost = world.get("ghost")
    ribbon = world.get("ribbon")
    ivy.memes["suspense"] += 1
    world.say(
        "She followed the stairs to the attic, where the air was dusty and still. "
        "Ivy listened to each tiny creak and looked under boxes, behind trunks, and inside a hat basket."
    )
    world.say(
        "At last, under an old blanket, she found a faded blue ribbon. "
        "The ribbon felt small in her hand, but the room seemed to hold its breath around it."
    )
    ribbon.meters["hidden"] = 0.0
    ribbon.owner = "ghost"
    world.para()


def scene_resolution(world: World) -> None:
    ivy = world.get("ivy")
    ghost = world.get("ghost")
    ribbon = world.get("ribbon")
    ivy.memes["fear"] = max(0.0, ivy.memes["fear"] - 1.0)
    ivy.memes["relief"] += 1
    ivy.memes["care"] += 1
    ivy.memes["suspense"] = max(0.0, ivy.memes["suspense"] - 1.0)
    ghost.memes["loneliness"] = 0.0
    ghost.meters["glow"] = 1.0
    world.say(
        "When Ivy held out the ribbon, the ghost looked less shadowy right away. "
        "It was not a scary ghost after all, only a lonely one who had been waiting for a friend."
    )
    world.say(
        '"Thank you," the ghost whispered. Ivy smiled, and the house felt warm again. '
        "By the end, the ribbon was safe, the attic was calm, and the little dots in the note had turned into a happy answer."
    )


def tell(params: StoryParams) -> World:
    world = build_world(params)
    scene_open(world)
    scene_google(world)
    scene_attic(world)
    scene_resolution(world)
    world.facts["resolved"] = True
    return world


SETTINGS = {
    "old_house": Setting(
        place="the old house",
        detail="The old house was quiet except for a soft creak in the hall.",
    ),
}


PRIZES = {
    "ribbon": "blue ribbon",
}


@dataclass
class RegistryRow:
    id: str
    value: str
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


def valid_combos() -> list[tuple[str, str]]:
    return [("old_house", "Ivy")]


def explain_rejection(place: str, hero: str) -> str:
    return "(No story: this world only supports Ivy in the old house.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A ghost-story world about Ivy, Google, and an ellipsis."
    )
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--hero", choices=["Ivy"])
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
    place = getattr(args, "place", None) or "old_house"
    hero = getattr(args, "hero", None) or "Ivy"
    if (place, hero) not in valid_combos():
        return _fallback_storyparams(args, rng, StoryParams, globals())
    return StoryParams(place=place, hero=hero, seed=getattr(args, "seed", None))


def generation_prompts(world: World) -> list[str]:
    return [
        'Write a short ghost story for a young child that includes Ivy, Google, and an ellipsis.',
        'Tell a suspenseful story where Ivy sees a note with three dots, searches on Google, and helps a lonely ghost.',
        'Write a gentle haunted-house story with an inner monologue and a calm ending image.',
    ]


def story_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="Why did Ivy feel nervous at the start?",
            answer="Ivy felt nervous because she found a note that said, \"Help me...\" and the three dots made the old house feel spooky.",
        ),
        QAItem(
            question="Why did Ivy use Google?",
            answer="Ivy used Google because she wanted to understand the ghost's message and find a safe way to help.",
        ),
        QAItem(
            question="What did Ivy find in the attic?",
            answer="Ivy found a faded blue ribbon hidden under an old blanket.",
        ),
        QAItem(
            question="What changed by the end of the story?",
            answer="By the end, the ghost was no longer lonely, Ivy felt relieved, and the old house felt warm instead of spooky.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is an ellipsis?",
            answer="An ellipsis is a row of three dots that can show a pause, an unfinished thought, or words left unsaid.",
        ),
        QAItem(
            question="What does Google do?",
            answer="Google is a search tool that helps people look up information by typing a question or topic.",
        ),
        QAItem(
            question="Why can an old house feel spooky?",
            answer="An old house can feel spooky because it is quiet, dusty, and full of strange noises like creaks and whispers.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for p in sample.prompts:
        lines.append(f"- {p}")
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
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
valid_story(old_house, ivy).

ellipsis_like(note) :- note_message(note).
helpful_search(ivy) :- valid_story(old_house, ivy).
ghost_resolved :- helpful_search(ivy), found_ribbon.
"""


def asp_facts() -> str:
    return "\n".join([
        'place(old_house).',
        'hero(ivy).',
        'note_message(note).',
        'found_ribbon.',
    ])


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    try:
        import asp  # type: ignore
    except Exception as exc:
        print(f"ASP unavailable: {exc}")
        return 1
    program = asp_program("#show valid_story/2.")
    model = asp.one_model(program)
    atoms = set(asp.atoms(model, "valid_story"))
    expected = set(valid_combos())
    if atoms == expected:
        print("OK: ASP matches Python gate.")
        return 0
    print("MISMATCH:")
    print("ASP:", sorted(atoms))
    print("PY :", sorted(expected))
    return 1


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        try:
            import asp  # type: ignore
        except Exception as exc:
            raise SystemExit(f"ASP unavailable: {exc}")
        stories = asp_valid_stories()
        print(f"{len(stories)} compatible stories:")
        for item in stories:
            print(" ", item)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        params = StoryParams(place="old_house", hero="Ivy", seed=base_seed)
        samples = [generate(params)]
    else:
        for i in range(max(1, getattr(args, "n", None))):
            rng = random.Random(base_seed + i)
            params = resolve_params(args, rng)
            params.seed = base_seed + i
            samples.append(generate(params))

    if getattr(args, "json", None):
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
