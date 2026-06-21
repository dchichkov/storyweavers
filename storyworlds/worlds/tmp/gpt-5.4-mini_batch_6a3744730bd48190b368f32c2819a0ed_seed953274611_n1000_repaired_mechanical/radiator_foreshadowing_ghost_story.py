#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/radiator_foreshadowing_ghost_story.py
======================================================================

A small standalone storyworld about a child, a chilly old house, a radiator,
and a gentle ghost-story mood with foreshadowing. The premise is simple:
something in the house seems eerie, clues pile up, and the end reveals that the
"ghost" was a harmless cause with a warm resolution.

The world is intentionally tiny and child-facing:
- a child hears strange sounds
- a caregiver notices clues and predicts a cause
- a hidden, ordinary source explains the haunting
- the ending image proves the change from fear to relief

The script supports the standard storyworld CLI and includes an ASP twin for
reasonableness and parity checks.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)
    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Setting:
    id: str
    place: str
    room: str
    mood: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


@dataclass
class Noise:
    id: str
    label: str
    sound: str
    clue: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


@dataclass
class Cause:
    id: str
    label: str
    explanation: str
    safe: bool = True
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


@dataclass
class StoryParams:
    setting: str
    noise: str
    cause: str
    child_name: str
    child_gender: str
    parent_gender: str
    seed: Optional[int] = None
    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


SETTINGS = {
    "old_house": Setting(
        id="old_house",
        place="an old house",
        room="the upstairs hallway",
        mood="drafty and dim",
        tags={"ghost", "house", "old"},
    ),
    "quiet_flat": Setting(
        id="quiet_flat",
        place="a quiet apartment",
        room="the narrow back hall",
        mood="dim and creaky",
        tags={"ghost", "house", "quiet"},
    ),
}

NOISES = {
    "rattle": Noise(
        id="rattle",
        label="rattling",
        sound="a soft clatter-clack",
        clue="the pipes in the wall had been waking up",
        tags={"sound", "pipes"},
    ),
    "tap": Noise(
        id="tap",
        label="tapping",
        sound="tap-tap-tap",
        clue="something metal was cooling and ticking",
        tags={"sound", "metal"},
    ),
    "hush": Noise(
        id="hush",
        label="whispering",
        sound="a hushy whisper",
        clue="warm air was sliding through a loose vent",
        tags={"sound", "air"},
    ),
}

CAUSES = {
    "radiator": Cause(
        id="radiator",
        label="the radiator",
        explanation="the old radiator had turned on and begun to ping and hiss as it warmed up",
        safe=True,
        tags={"radiator", "heat"},
    ),
    "pipe": Cause(
        id="pipe",
        label="a pipe",
        explanation="a pipe in the wall was knocking as it expanded with the heat",
        safe=True,
        tags={"pipe", "heat"},
    ),
    "window": Cause(
        id="window",
        label="a loose window latch",
        explanation="a loose window latch was tapping in the night wind",
        safe=True,
        tags={"window", "wind"},
    ),
}


GIRL_NAMES = ["Maya", "Lila", "Nora", "Rose", "Ivy", "June"]
BOY_NAMES = ["Theo", "Finn", "Eli", "Noah", "Leo", "Milo"]


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
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

    def copy(self) -> "World":
        w = World()
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        return w


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


def _r_cold(world: World) -> list[str]:
    out: list[str] = []
    house = world.get("house")
    if house.meters["cold"] >= THRESHOLD and ("cold",) not in world.fired:
        world.fired.add(("cold",))
        for kid in ("child",):
            world.get(kid).memes["unease"] += 1
        out.append("__cold__")
    return out


def _r_guess(world: World) -> list[str]:
    out: list[str] = []
    if world.get("child").memes["unease"] >= THRESHOLD and ("guess",) not in world.fired:
        world.fired.add(("guess",))
        world.get("parent").memes["focus"] += 1
        out.append("__guess__")
    return out


def _r_relief(world: World) -> list[str]:
    out: list[str] = []
    if world.get("cause").meters["revealed"] >= THRESHOLD and ("relief",) not in world.fired:
        world.fired.add(("relief",))
        world.get("child").memes["relief"] += 1
        world.get("house").meters["cold"] = 0.0
        out.append("__relief__")
    return out


CAUSAL_RULES = [Rule("cold", _r_cold), Rule("guess", _r_guess), Rule("relief", _r_relief)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def plausible_combo(setting: Setting, noise: Noise, cause: Cause) -> bool:
    return "ghost" in setting.tags and noise.safe and cause.safe


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid, s in SETTINGS.items():
        for nid, n in NOISES.items():
            for cid, c in CAUSES.items():
                if plausible_combo(s, n, c):
                    combos.append((sid, nid, cid))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Ghost-story world with radiator foreshadowing.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--noise", choices=NOISES)
    ap.add_argument("--cause", choices=CAUSES)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
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
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.noise is None or c[1] == args.noise)
              and (args.cause is None or c[2] == args.cause)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, noise, cause = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(setting=setting, noise=noise, cause=cause, child_name=name, child_gender=gender, parent_gender=parent)


def tell(setting: Setting, noise: Noise, cause: Cause, child_name: str, child_gender: str, parent_gender: str) -> World:
    w = World()
    child = w.add(Entity(id=child_name, kind="character", type=child_gender, role="child"))
    parent = w.add(Entity(id="parent", kind="character", type=parent_gender, label="the parent", role="parent"))
    house = w.add(Entity(id="house", kind="place", type="house", label=setting.place))
    radiator = w.add(Entity(id="radiator", kind="thing", type="radiator", label="the radiator"))
    w.add(Entity(id="cause", kind="thing", type="cause", label=cause.label))
    w.say(
        f"It was late in {setting.place}, and the house felt {setting.mood}. "
        f"{child_name} stood in {setting.room} and heard {noise.sound}."
    )
    w.say(
        f'From somewhere nearby came {noise.label} sounds, and that made {child_name} look up fast. '
        f'It almost felt like a ghost was walking the halls.'
    )
    w.para()
    child.meters["curious"] += 1
    house.meters["cold"] += 1
    propagate(w, narrate=False)
    w.say(
        f'{child_name} whispered, "Did you hear that?" and the parent listened too. '
        f'{noise.clue.capitalize()}.'
    )
    w.say(
        f'The parent said, "Let me guess. It sounds spooky, but I think it is {cause.explanation}."'
    )
    w.para()
    parent.memes["calm"] += 1
    cause.meters["revealed"] += 1
    propagate(w, narrate=False)
    w.say(
        f'Then they walked closer, and sure enough, it was just {cause.label}. '
        f'The {radiator.label_word if hasattr(radiator, "label_word") else radiator.label} hummed softly, warm and old.'
    )
    w.say(
        f'{child_name} smiled with relief. The hallway was no longer creepy, just cozy and a little warm.'
    )
    w.say(
        f'By the end, the strange sound had a simple answer, and the house felt safe again.'
    )
    w.facts.update(setting=setting, noise=noise, cause=cause, child=child, parent=parent, house=house)
    return w


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a child-friendly ghost story that includes the word "radiator" and uses foreshadowing.',
        f"Tell a spooky-but-safe story where {f['child'].id} hears {f['noise'].label} sounds in {f['setting'].place} and a grown-up explains the clue.",
        f"Write a short ghost story that builds suspense with a warm household object and ends in relief.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    setting = f["setting"]
    cause = f["cause"]
    return [
        QAItem(
            question="Why did the story feel spooky at first?",
            answer=f"The house was dim and {child.id} heard strange sounds in the hallway. That made the place feel haunted before anyone knew the real cause."
        ),
        QAItem(
            question="What clue foreshadowed the ending?",
            answer=f"The story kept mentioning the cold house, the strange noises, and the old radiator. Those clues pointed toward a normal household sound instead of a real ghost."
        ),
        QAItem(
            question=f"What was the strange sound really caused by?",
            answer=f"It was really caused by {cause.explanation}. Once that was discovered, the scary feeling went away."
        ),
        QAItem(
            question="How did the child feel at the end?",
            answer=f"{child.id} felt relieved and calm. The hallway turned from creepy to cozy once the answer was found."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a radiator?",
            answer="A radiator is a heater that warms a room, often by making little pinging or hissing noises as it gets hot."
        ),
        QAItem(
            question="What is foreshadowing in a story?",
            answer="Foreshadowing is when a story gives small clues early on about what will happen later. It helps the ending feel like it was being prepared all along."
        ),
        QAItem(
            question="Why do old houses sometimes creak?",
            answer="Old houses can creak because wood and pipes shift as the temperature changes. Those sounds can seem spooky, even when nothing magical is happening."
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions -- child level, no story needed ==")
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
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


CURATED = [
    StoryParams(setting="old_house", noise="rattle", cause="radiator", child_name="Maya", child_gender="girl", parent_gender="mother"),
    StoryParams(setting="quiet_flat", noise="tap", cause="pipe", child_name="Theo", child_gender="boy", parent_gender="father"),
    StoryParams(setting="old_house", noise="hush", cause="window", child_name="Nora", child_gender="girl", parent_gender="mother"),
]


ASP_RULES = r"""
ghosty(S) :- setting(S), tag(S, ghost).
plausible(S,N,C) :- setting(S), noise(N), cause(C), ghosty(S).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for tag in sorted(s.tags):
            lines.append(asp.fact("tag", sid, tag))
    for nid in NOISES:
        lines.append(asp.fact("noise", nid))
    for cid in CAUSES:
        lines.append(asp.fact("cause", cid))
    return "\n".join(lines)


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show plausible/3."))
    return sorted(set(asp.atoms(model, "plausible")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: ASP matches valid_combos() ({len(valid_combos())} combos).")
    else:
        rc = 1
        print("MISMATCH between ASP and Python gate.")
    try:
        sample = generate(resolve_params(argparse.Namespace(setting=None, noise=None, cause=None, name=None, gender=None, parent=None), random.Random(7)))
        if not sample.story.strip():
            raise RuntimeError("empty story")
        print("OK: smoke test generation succeeded.")
    except Exception as e:
        rc = 1
        print(f"SMOKE TEST FAILED: {e}")
    return rc


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS or params.noise not in NOISES or params.cause not in CAUSES:
        raise StoryError("(Invalid params.)")
    if not plausible_combo(SETTINGS[params.setting], NOISES[params.noise], CAUSES[params.cause]):
        raise StoryError("(No valid combination matches the given options.)")
    world = tell(
        SETTINGS[params.setting],
        NOISES[params.noise],
        CAUSES[params.cause],
        params.child_name,
        params.child_gender,
        params.parent_gender,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
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
    if args.show_asp:
        print(asp_program(show="#show plausible/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        for s, n, c in asp_valid_combos():
            print(s, n, c)
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(args.n):
            p = resolve_params(args, random.Random(base_seed + i))
            p.seed = base_seed + i
            samples.append(generate(p))
    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, s in enumerate(samples):
        emit(s, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
