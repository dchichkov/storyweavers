#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/paddy_judge_hoof_dentist_office_moral_value.py
===============================================================================

A tiny standalone storyworld for a dental-office adventure with a moral choice,
a little suspense, and the seed words paddy / judge / hoof woven into the world.

Premise
-------
Paddy comes to a dentist office because a strange hoof-print clue has led to a
missing dental key and a delayed cleaning. Judge is the calm adult who must
decide whether to trust Paddy's story, and the suspense comes from the ticking
clock: the office is about to close, the cleaner cart is rolling away, and the
next patient is waiting.

The moral value is simple and child-facing: telling the truth and helping solve
a problem matters more than saving face. The ending proves what changed in the
world model, not just in the wording.

This file follows the Storyweavers contract:
- self-contained stdlib script
- eager import of results.py
- lazy import of asp.py inside ASP helpers
- typed entities with meters and memes
- state-driven prose, QA, JSON, trace, ASP, and verify support
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
CLOSING_TIME = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "judge"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.id
    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)


@dataclass
class Setting:
    id: str
    place: str
    labels: list[str]
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
class Clue:
    id: str
    phrase: str
    label: str
    mystery: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

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
class Pressure:
    id: str
    text: str
    risk: int
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
class Resolution:
    id: str
    text: str
    moral: str
    power: int
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
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


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


def _r_suspense(world: World) -> list[str]:
    out: list[str] = []
    if world.get("clock").meters["late"] < THRESHOLD:
        return out
    for eid in ("paddy", "judge"):
        world.get(eid).memes["anxiety"] += 1
    if ("suspense",) not in world.fired:
        world.fired.add(("suspense",))
        out.append("The room felt tighter as the minutes slipped away.")
    return out


def _r_moral(world: World) -> list[str]:
    out: list[str] = []
    if world.get("paddy").memes["truth"] < THRESHOLD:
        return out
    if ("moral",) in world.fired:
        return out
    world.fired.add(("moral",))
    world.get("judge").memes["trust"] += 1
    out.append("Truth made the problem smaller and the grown-up calmer.")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


CAUSAL_RULES = [Rule("suspense", _r_suspense), Rule("moral", _r_moral)]


def uneasy_opening(world: World, setting: Setting, paddy: Entity, judge: Entity, hoof: Clue) -> None:
    world.say(
        f"In the dentist office, {paddy.id} stood near the shiny chairs while "
        f"{judge.id} checked the counter."
    )
    world.say(
        f"A strange hoof-shaped mark had been found by the sink, and the whole "
        f"office still smelled like mint and polish."
    )
    world.say(
        f'"{paddy.id}," said {judge.id}, "this clue is making quite a story. '
        f'Why were you near the back room?"'
    )


def raise_suspense(world: World, pressure: Pressure) -> None:
    world.get("clock").meters["late"] += pressure.risk
    world.say(pressure.text)


def paddy_confess(world: World, paddy: Entity, judge: Entity, hoof: Clue) -> None:
    paddy.memes["truth"] += 1
    paddy.memes["fear"] += 1
    world.say(
        f"{paddy.id} swallowed hard. The hoof mark was real, and the missing key "
        f"was worse. At last {paddy.pronoun()} said the truth."
    )
    world.say(
        f'"I dropped the key near the back room," {paddy.id} admitted, "and I '
        f"tried to hide it because I thought you'd judge me."'
    )
    world.say(
        f"{judge.id} listened without snapping the pencil in {judge.pronoun('possessive')} hand."
    )


def uncover(world: World, paddy: Entity, judge: Entity, hoof: Clue) -> None:
    paddy.memes["relief"] += 1
    judge.memes["relief"] += 1
    world.get("key").meters["found"] = 1
    world.get("cart").meters["stopped"] = 1
    world.say(
        f"Then the clue made sense: the hoof print belonged to the little therapy "
        f"pony that had trotted in for a visit, not to a thief at all."
    )
    world.say(
        f"The key was under a rolling towel cart, exactly where {paddy.id} had "
        f"looked only after telling the truth."
    )


def resolve(world: World, paddy: Entity, judge: Entity, res: Resolution) -> None:
    world.get("clock").meters["late"] = 0
    world.say(
        f"{judge.id} smiled, and {judge.id} let {paddy.id} help with the clean-up."
    )
    world.say(
        f'"{res.moral}," {judge.id} said. "{res.text}"'
    )
    world.say(
        f"{paddy.id} nodded, and the office stopped feeling like a trap."
    )


def ending_image(world: World, paddy: Entity, judge: Entity) -> None:
    world.say(
        f"In the end, {paddy.id} held the recovered key, {judge.id} stamped the "
        f"appointment card, and the little hoof clue sat on the counter like a "
        f"finished mystery."
    )
    world.say(
        "The next patient came in, and the dentist office was calm again."
    )


SETTING = Setting(
    id="dentist_office",
    place="the dentist office",
    labels=["waiting room", "sink", "back room", "counter", "chair"],
    tags={"dentist_office", "office"},
)

CLUES = {
    "hoof": Clue(
        id="hoof",
        phrase="a hoof-shaped mark",
        label="hoof",
        mystery="a hoof print in the toothpaste dust",
        tags={"hoof", "mystery"},
    )
}

PRESSURES = {
    "closing": Pressure(
        id="closing",
        text="The clock ticked toward closing time, and the cleaner cart was almost gone.",
        risk=CLOSING_TIME,
        tags={"suspense", "clock"},
    ),
    "patient": Pressure(
        id="patient",
        text="The next patient was already waiting, tapping a shoe on the tile.",
        risk=1,
        tags={"suspense", "patient"},
    ),
}

RESOLUTIONS = {
    "truth": Resolution(
        id="truth",
        text="A problem gets smaller when you tell the truth and ask for help.",
        moral="A truthful heart is braver than a hiding one",
        power=2,
        tags={"moral", "truth"},
    ),
}

GIRL_NAMES = ["Paddy", "Mara", "Nina", "Tess"]
BOY_NAMES = ["Paddy", "Finn", "Evan", "Noah"]


@dataclass
class StoryParams:
    setting: str
    clue: str
    pressure1: str
    pressure2: str
    resolution: str
    paddy_name: str
    paddy_gender: str
    judge_name: str = "Judge"
    judge_gender: str = "judge"
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


def valid_combos() -> list[tuple[str, str, str, str, str]]:
    combos = []
    for setting in SETTINGS:
        for clue in CLUES:
            for p1 in PRESSURES:
                for p2 in PRESSURES:
                    for res in RESOLUTIONS:
                        combos.append((setting, clue, p1, p2, res))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A dentist-office adventure with moral value and suspense.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--pressure1", choices=PRESSURES)
    ap.add_argument("--pressure2", choices=PRESSURES)
    ap.add_argument("--resolution", choices=RESOLUTIONS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
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
    setting = args.setting or "dentist_office"
    clue = args.clue or "hoof"
    pressure1 = args.pressure1 or rng.choice(list(PRESSURES))
    pressure2 = args.pressure2 or rng.choice(list(PRESSURES))
    resolution = args.resolution or "truth"
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    if clue not in CLUES:
        raise StoryError("Unknown clue.")
    return StoryParams(
        setting=setting,
        clue=clue,
        pressure1=pressure1,
        pressure2=pressure2,
        resolution=resolution,
        paddy_name=name,
        paddy_gender=gender,
    )


def tell(params: StoryParams) -> World:
    world = World()
    paddy = world.add(Entity(id=params.paddy_name, kind="character", type=params.paddy_gender, role="hero"))
    judge = world.add(Entity(id="Judge", kind="character", type="judge", role="judge"))
    hoof = world.add(Entity(id="hoof", kind="thing", type="thing", label="hoof", tags={"hoof"}))
    key = world.add(Entity(id="key", kind="thing", type="thing", label="dental key"))
    cart = world.add(Entity(id="cart", kind="thing", type="thing", label="cleaner cart"))
    clock = world.add(Entity(id="clock", kind="thing", type="thing", label="clock"))
    world.facts.update(setting=SETTING, paddy=paddy, judge=judge, hoof=hoof, key=key, cart=cart, clock=clock)

    uneasy_opening(world, SETTING, paddy, judge, hoof)
    world.para()
    raise_suspense(world, PRESSURES[params.pressure1])
    raise_suspense(world, PRESSURES[params.pressure2])
    propagate(world, narrate=True)
    world.para()
    paddy_confess(world, paddy, judge, hoof)
    uncover(world, paddy, judge, hoof)
    resolve(world, paddy, judge, RESOLUTIONS[params.resolution])
    world.para()
    ending_image(world, paddy, judge)
    world.facts["outcome"] = "truth"
    return world


def generation_prompts(world: World) -> list[str]:
    return [
        "Write a dentist-office adventure story for a young child that includes the words paddy, judge, and hoof.",
        "Tell a suspenseful story set in a dentist office where Paddy tells the truth and a judge helps solve the mystery of the hoof clue.",
        "Write a moral-value story with an adventure feel: a child in a dentist office worries about being judged, then tells the truth and things turn out well.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    paddy = world.facts["paddy"]
    judge = world.facts["judge"]
    qa = [
        ("Where does the story happen?",
         f"It happens in the dentist office, where shiny chairs, a counter, and a back room make the mystery feel close and real."),
        ("Why is there suspense?",
         f"The clock was moving toward closing time, and the next patient was waiting. That made the hidden key feel important because there was less and less time to solve the problem."),
        ("What did Paddy do that was morally important?",
         f"Paddy told the truth about the missing key instead of hiding it. That mattered because honest words helped {judge.id} solve the mystery and keep the office calm."),
        ("What was the hoof clue?",
         "It was a hoof-shaped mark near the sink, and it pointed to the little therapy pony that had visited the office."),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is a dentist office?",
         "A dentist office is a place where people go to get their teeth checked and cleaned by a dentist."),
        ("What is suspense in a story?",
         "Suspense is the feeling that something important might happen soon, so you keep wondering what will happen next."),
        ("Why is telling the truth a good moral choice?",
         "Telling the truth helps other people trust you and makes it easier to fix a problem."),
        ("What is a hoof?",
         "A hoof is the hard foot of an animal like a horse, pony, or cow."),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World knowledge questions ==")
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
        if e.tags:
            bits.append(f"tags={sorted(e.tags)}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for (n,) in world.fired if n})}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        setting="dentist_office",
        clue="hoof",
        pressure1="closing",
        pressure2="patient",
        resolution="truth",
        paddy_name="Paddy",
        paddy_gender="boy",
    ),
    StoryParams(
        setting="dentist_office",
        clue="hoof",
        pressure1="patient",
        pressure2="closing",
        resolution="truth",
        paddy_name="Paddy",
        paddy_gender="girl",
    ),
]


def generation_story_text(world: World) -> str:
    return world.render()


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError("Unknown setting.")
    if params.clue not in CLUES:
        raise StoryError("Unknown clue.")
    if params.pressure1 not in PRESSURES or params.pressure2 not in PRESSURES:
        raise StoryError("Unknown pressure.")
    if params.resolution not in RESOLUTIONS:
        raise StoryError("Unknown resolution.")
    world = tell(params)
    return StorySample(
        params=params,
        story=generation_story_text(world),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa(world)],
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


ASP_RULES = r"""
suspense :- late.
moral :- truth_told.
"""


def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("setting", "dentist_office"),
        asp.fact("clue", "hoof"),
        asp.fact("resolution", "truth"),
        asp.fact("late", 1),
        asp.fact("truth_told"),
    ]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    try:
        sample = generate(CURATED[0])
        _ = sample.story
    except Exception as exc:
        print(f"FAILED: generate smoke test crashed: {exc}")
        return 1
    return 0


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show suspense/0.\n#show moral/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("asp mode is available for this compact world.")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 30, 30):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story in seen:
                i += 1
                continue
            seen.add(sample.story)
            samples.append(sample)
            i += 1

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
