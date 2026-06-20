#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/confirm_cylindric_fettuccini_mystery_to_solve_bedtime.py
=========================================================================================

A tiny bedtime mystery world: a child hears a small nighttime mystery, follows
clues with a calm grown-up, and learns the harmless cause of the strange sound.

Seed words used in the story world:
- confirm
- cylindric
- fettuccini

The mood is a bedtime story: soft light, quiet rooms, gentle clues, and a
reassuring ending image.
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

    tags: set[str] = field(default_factory=set)

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
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

@dataclass
class Room:
    id: str
    label: str
    quiet: bool = True
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Clue:
    id: str
    label: str
    phrase: str
    shape: str
    kind: str
    reveals: str

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class MysteryObject:
    id: str
    label: str
    phrase: str
    shape: str
    kind: str
    hidden_in: str
    makes_sound: bool = True

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Comfort:
    id: str
    label: str
    phrase: str
    glow: str

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.room = Room(id="room", label="the bedroom")
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
        c = World()
        c.entities = copy.deepcopy(self.entities)
        c.room = copy.deepcopy(self.room)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        return c


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


def _r_worry(world: World) -> list[str]:
    out: list[str] = []
    child = world.entities.get("child")
    if not child:
        return out
    if child.meters["curious"] < THRESHOLD:
        return out
    sig = ("worry", "child")
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["worry"] += 1
    world.room.memes["mystery"] += 1
    out.append("__worry__")
    return out


def _r_confirm(world: World) -> list[str]:
    out: list[str] = []
    child = world.entities.get("child")
    parent = world.entities.get("parent")
    clue = world.entities.get("clue")
    if not (child and parent and clue):
        return out
    if child.memes["worry"] < THRESHOLD:
        return out
    sig = ("confirm", clue.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    parent.memes["calm"] += 1
    child.memes["relief"] += 1
    out.append("__confirm__")
    return out


CAUSAL_RULES = [
    Rule("worry", "social", _r_worry),
    Rule("confirm", "social", _r_confirm),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
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


@dataclass
class Setting:
    id: str
    label: str
    mood: str
    quiet: bool = True

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
@dataclass
class StoryParams:
    setting: str
    child: str
    parent: str
    clue: str
    mystery: str
    comfort: str
    seed: Optional[int] = None

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


SETTINGS = {
    "bedroom": Setting("bedroom", "the bedroom", "soft and sleepy"),
    "hall": Setting("hall", "the hall", "quiet and warm"),
    "kitchen": Setting("kitchen", "the kitchen", "dim and gentle"),
}

CHILDREN = {
    "Mina": "girl",
    "Noah": "boy",
    "Lina": "girl",
    "Owen": "boy",
    "Tess": "girl",
    "Eli": "boy",
}

PARENTS = {
    "Mom": "mother",
    "Dad": "father",
}

MYSTERIES = {
    "spoon": MysteryObject("spoon", "spoon", "a small spoon", "cylindric", "metal", "drawer"),
    "tube": MysteryObject("tube", "tube", "a cylindric tube", "cylindric", "cardboard", "basket"),
    "string": MysteryObject("string", "string", "a curly string", "wavy", "thread", "pillow"),
}

CLUES = {
    "rattle": Clue("rattle", "rattle", "a little rattle sound", "round", "sound", "a spoon in a bowl"),
    "roll": Clue("roll", "roll", "a rolling clue", "cylindric", "motion", "a round thing under the bed"),
    "smell": Clue("smell", "smell", "a warm kitchen smell", "soft", "smell", "fettuccini noodles in a bowl"),
}

COMFORTS = {
    "bear": Comfort("bear", "bear", "a sleepy bear", "glowed softly"),
    "lamp": Comfort("lamp", "lamp", "a tiny lamp", "glowed like a moon"),
    "blanket": Comfort("blanket", "blanket", "a warm blanket", "felt snug and safe"),
}


def valid_combos() -> list[tuple[str, str, str]]:
    return [(s, c, m) for s in SETTINGS for c in CLUES for m in MYSTERIES]


def aspiration_text(clue: Clue, mystery: MysteryObject) -> str:
    return f"{clue.shape} and {mystery.shape}"


def explain_rejection() -> str:
    return "(No story: the mystery would not have enough gentle clues to solve.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Bedtime mystery world with calm clues and a safe ending.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--child")
    ap.add_argument("--parent", choices=PARENTS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--comfort", choices=COMFORTS)
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
              and (args.clue is None or c[1] == args.clue)
              and (args.mystery is None or c[2] == args.mystery)]
    if not combos:
        raise StoryError(explain_rejection())
    setting, clue, mystery = rng.choice(sorted(combos))
    child = args.child or rng.choice(sorted(CHILDREN))
    parent = args.parent or rng.choice(sorted(PARENTS))
    comfort = args.comfort or rng.choice(sorted(COMFORTS))
    return StoryParams(setting, child, parent, clue, mystery, comfort)


def tell(params: StoryParams) -> World:
    w = World()
    child_type = CHILDREN[params.child]
    parent_type = PARENTS[params.parent]
    child = w.add(Entity("child", "character", child_type, params.child, "child", ["sleepy"]))
    parent = w.add(Entity("parent", "character", parent_type, params.parent, "parent", ["calm"]))
    clue = CLUES[params.clue]
    mystery = MYSTERIES[params.mystery]
    comfort = COMFORTS[params.comfort]
    room = w.room

    child.meters["curious"] += 1
    child.memes["love"] += 1
    room.meters["quiet"] += 1

    w.say(f"At bedtime, {child.id} and {parent.id} were in {SETTINGS[params.setting].label}.")
    w.say(f"The room was {SETTINGS[params.setting].mood}, and {child.id} held {comfort.phrase}.")
    w.say(
        f"Then {child.id} heard a small mystery: a soft {clue.label} and a tiny sound like "
        f"{aspiration_text(clue, mystery)}."
    )
    w.para()
    w.say(
        f"{child.id} tiptoed closer and saw {mystery.phrase} near the {mystery.hidden_in}. "
        f"It looked {mystery.shape}, and that made {child.id} curious."
    )
    w.say(f'"Can you confirm what made that sound?" {child.id} asked.')
    child.memes["curious"] += 1
    propagate(w)
    w.say(
        f"{parent.id} knelt beside {child.id} and listened carefully. {parent.id} could confirm "
        f"that the sound came from {clue.reveals}."
    )
    w.say(
        f"It was only a harmless little thing, and the mystery turned into a smile."
    )
    w.para()
    child.memes["relief"] += 1
    child.memes["joy"] += 1
    parent.memes["love"] += 1
    w.say(
        f"{child.id} tucked {comfort.phrase} close again, and the {comfort.label} {comfort.glow}. "
        f"With the mystery solved, the bedroom felt soft and safe, ready for sleep."
    )

    w.facts.update(
        setting=SETTINGS[params.setting],
        child=child,
        parent=parent,
        clue=clue,
        mystery=mystery,
        comfort=comfort,
        solved=True,
        confirm_word=True,
    )
    return w


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a bedtime mystery story that includes the words "confirm", "{f["mystery"].shape}", and "fettuccini".',
        f"Tell a gentle story where {f['child'].id} hears a small mystery, asks {f['parent'].id} to confirm it, and ends with bedtime comfort.",
        f"Write a sleepy story about a {f['mystery'].kind} clue in {f['setting'].label} and a calm grown-up who solves the mystery.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    parent = f["parent"]
    clue = f["clue"]
    mystery = f["mystery"]
    comfort = f["comfort"]
    return [
        QAItem(
            question=f"What mystery did {child.id} hear?",
            answer=f"{child.id} heard a tiny bedtime sound, then found {mystery.phrase} near the {mystery.hidden_in}. The clue made the room feel mysterious until the grown-up looked too.",
        ),
        QAItem(
            question=f"How was the mystery solved?",
            answer=f"{parent.id} listened, looked carefully, and could confirm that the sound came from {clue.reveals}. That turned the scary guess into a calm answer.",
        ),
        QAItem(
            question=f"What helped {child.id} feel safe at the end?",
            answer=f"{child.id} held {comfort.phrase} again while the bedroom grew quiet and warm. The mystery was solved, so bedtime could go on peacefully.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does it mean to confirm something?",
            answer="To confirm something means to check it carefully and make sure it is true. A grown-up can confirm a clue by looking and listening closely.",
        ),
        QAItem(
            question="What does cylindric mean?",
            answer="Cylindric means shaped like a tube or a rolling stick, round and long. A cylindric thing can roll or fit neatly in a small place.",
        ),
        QAItem(
            question="What is fettuccini?",
            answer="Fettuccini is a kind of pasta with long flat noodles. It is soft, tasty, and often served in a bowl.",
        ),
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
    lines.append("== (3) World-knowledge questions ==")
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
        if e.role:
            bits.append(f"role={e.role}")
        if e.traits:
            bits.append(f"traits={e.traits}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  room     (room   ) meters={dict(world.room.meters)} memes={dict(world.room.memes)}")
    return "\n".join(lines)


CURATED = [
    StoryParams("bedroom", "Mina", "Mom", "smell", "spoon", "blanket"),
    StoryParams("hall", "Noah", "Dad", "roll", "tube", "bear"),
    StoryParams("kitchen", "Tess", "Mom", "rattle", "spoon", "lamp"),
]


ASP_RULES = r"""
#show valid/3.
mystery(X) :- mystery_obj(X).
clue(Y) :- clue_obj(Y).
valid(S,C,M) :- setting(S), clue_obj(C), mystery_obj(M).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for c in CLUES:
        lines.append(asp.fact("clue_obj", c))
    for m in MYSTERIES:
        lines.append(asp.fact("mystery_obj", m))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        print("MISMATCH: ASP and Python valid_combos differ.")
        rc = 1
    try:
        generate(CURATED[0])
        print("OK: smoke test story generation succeeded.")
    except Exception as exc:  # noqa: BLE001
        print(f"FAIL: smoke test generation crashed: {exc}")
        rc = 1
    return rc


def build_story(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def generate(params: StoryParams) -> StorySample:
    return build_story(params)


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
        print(asp_program("", "#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos:")
        for s, c, m in asp_valid_combos():
            print(f"  {s:8} {c:8} {m}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as err:
                print(err)
                return
            params.seed = seed
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.child}: {p.mystery} in {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
