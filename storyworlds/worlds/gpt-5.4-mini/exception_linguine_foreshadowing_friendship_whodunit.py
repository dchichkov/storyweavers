#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/exception_linguine_foreshadowing_friendship_whodunit.py
=======================================================================================

A standalone storyworld for a tiny whodunit about friendship, foreshadowing, and
an odd little exception: a bowl of linguine is missing from the table, crumbs and
clues are found, and two friends solve the mystery by noticing what doesn't fit.

This world is intentionally small and classical:
- a child-friendly mystery setup,
- concrete physical state that drives the prose,
- emotional state that shifts as clues are found,
- a final reveal that proves what changed.

The story naturally includes the words "exception" and "linguine", and it leans
into foreshadowing by planting small clues early that make the ending feel earned.
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


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
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
class Setting:
    id: str
    place: str
    afford: set[str] = field(default_factory=set)

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
class CharacterProfile:
    id: str
    type: str
    role: str
    trait: str
    age: int = 0

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
    text: str
    hint: str
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
class Case:
    id: str
    suspicion: int
    reveal: str
    solution: str

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
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.clues_seen: list[str] = []

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in list(self.entities.values()) if e.kind == "character"]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.clues_seen = list(self.clues_seen)
        clone.paragraphs = [[]]
        return clone


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


def _r_suspicion(world: World) -> list[str]:
    out: list[str] = []
    bowl = world.get("bowl")
    if bowl.meters["missing"] < THRESHOLD:
        return out
    sig = ("suspicion", bowl.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    for ch in world.characters():
        ch.memes["curiosity"] += 1
    out.append("__suspicion__")
    return out


def _r_relief(world: World) -> list[str]:
    out: list[str] = []
    if world.get("bowl").meters["found"] < THRESHOLD:
        return out
    sig = ("relief", "bowl")
    if sig in world.fired:
        return out
    world.fired.add(sig)
    for ch in world.characters():
        ch.memes["relief"] += 1
    out.append("__relief__")
    return out


CAUSAL_RULES = [
    Rule("suspicion", "social", _r_suspicion),
    Rule("relief", "social", _r_relief),
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


def _do_hide(world: World, actor: Entity, narrate: bool = True) -> None:
    bowl = world.get("bowl")
    bowl.meters["missing"] += 1
    actor.meters["sauced"] += 1
    if world.get("crumbs").meters["scattered"] < THRESHOLD:
        world.get("crumbs").meters["scattered"] += 1
    propagate(world, narrate=narrate)


def predict_mystery(world: World, actor_id: str) -> dict:
    sim = world.copy()
    _do_hide(sim, sim.get(actor_id), narrate=False)
    return {
        "missing": sim.get("bowl").meters["missing"] >= THRESHOLD,
        "suspicion": sim.get("detective").memes["curiosity"],
    }


def setup(world: World, a: Entity, b: Entity, setting: Setting) -> None:
    a.memes["friendship"] += 1
    b.memes["friendship"] += 1
    world.say(
        f"On a quiet evening, {a.id} and {b.id} sat in {setting.place}. "
        f"A bowl of linguine waited on the table, bright with sauce and steam."
    )
    world.say(
        f'{a.id} smiled. "{b.id}, this feels like the start of an exception," '
        f"{a.pronoun()} said, " "something small and odd."
    )


def foreshadow(world: World, clue: Clue) -> None:
    world.say(clue.text)
    world.clues_seen.append(clue.id)


def missing(world: World, detective: Entity, friend: Entity) -> None:
    detective.memes["curiosity"] += 1
    detective.memes["worry"] += 1
    world.say(
        f"Then {detective.id} blinked. The bowl was gone. "
        f"Only a bright smear and a few noodles remained."
    )
    world.say(
        f'"That is strange," {friend.id} said. "The exception is the bowl, not '
        f"the linguine."
    )


def search(world: World, detective: Entity, friend: Entity) -> None:
    detective.memes["focus"] += 1
    friend.memes["helpfulness"] += 1
    pred = predict_mystery(world, friend.id)
    world.facts["predicted_missing"] = pred["missing"]
    world.say(
        f"{detective.id} looked near the chair, then the doorway, then the sink. "
        f"{friend.id} followed the little trail of sauce."
    )
    world.say(
        f"One clue had been waiting all along: a spoon in the sink and a napkin "
        f"with one corner folded like a flag."
    )


def reveal(world: World, detective: Entity, friend: Entity, culprit: Entity, case: Case) -> None:
    bowl = world.get("bowl")
    bowl.meters["found"] += 1
    culprit.meters["caught"] += 1
    detective.memes["joy"] += 1
    friend.memes["joy"] += 1
    world.say(
        f"{friend.id} gasped. The little chef was the exception. {culprit.id} "
        f"had taken the linguine to the counter to stir in extra cheese."
    )
    world.say(
        f'{detective.id} laughed. "A mystery can be solved by what does not fit," '
        f"{detective.pronoun()} said. The missing bowl was not stolen at all."
    )


def ending(world: World, detective: Entity, friend: Entity, culprit: Entity) -> None:
    world.say(
        f"After that, {culprit.id} set the bowl back on the table, and the three "
        f"friends ate together while the sauce cooled. The odd clue had led them "
        f"to kindness instead of trouble."
    )
    world.say(
        f"By the end, the room was tidy, the linguine was shared, and the friends "
        f"were smiling as if the whole evening had been solved with a wink."
    )


def tell(setting: Setting, clue_pack: list[Clue], case: Case,
         detective_name: str = "Mina", friend_name: str = "Owen",
         culprit_name: str = "Pip") -> World:
    world = World(setting)
    detective = world.add(Entity(id=detective_name, kind="character", type="girl", role="detective"))
    friend = world.add(Entity(id=friend_name, kind="character", type="boy", role="friend"))
    culprit = world.add(Entity(id=culprit_name, kind="character", type="boy", role="culprit"))
    bowl = world.add(Entity(id="bowl", type="thing", label="bowl"))
    crumbs = world.add(Entity(id="crumbs", type="thing", label="crumbs"))
    clue_holder = world.add(Entity(id="note", type="thing", label="note"))

    setup(world, detective, friend, setting)
    world.para()
    foreshadow(world, clue_pack[0])
    foreshadow(world, clue_pack[1])
    _do_hide(world, culprit)
    missing(world, detective, friend)
    world.para()
    search(world, detective, friend)
    world.para()
    reveal(world, detective, friend, culprit, case)
    ending(world, detective, friend, culprit)

    world.facts.update(
        setting=setting, detective=detective, friend=friend, culprit=culprit,
        bowl=bowl, crumbs=crumbs, clue_pack=clue_pack, case=case, clue_holder=clue_holder,
        resolved=True, missing=bowl.meters["missing"] >= THRESHOLD,
    )
    return world


SETTINGS = {
    "kitchen": Setting("kitchen", "the kitchen", afford={"linguine"}),
    "sunroom": Setting("sunroom", "the sunroom", afford={"linguine"}),
    "dining_room": Setting("dining_room", "the dining room", afford={"linguine"}),
}

CLUES = {
    "spoon": Clue("spoon", "A spoon flashed by the sink.", "a tool for stirring", "someone was cooking"),
    "cheese": Clue("cheese", "A little pile of cheese dust clung to the counter.", "extra cheese", "someone wanted more flavor"),
    "napkin": Clue("napkin", "A napkin sat folded like a tiny secret flag.", "a careful wipe", "someone tried to be neat"),
}

CASES = {
    "stirred": Case("stirred", 2, "the linguine was moved for cheese", "the bowl was taken to stir in cheese"),
}

NAMES_GIRL = ["Mina", "Tara", "Ivy", "Lena", "Nora"]
NAMES_BOY = ["Owen", "Pip", "Finn", "Theo", "Noah"]


@dataclass
@dataclass
class StoryParams:
    setting: str
    clue1: str
    clue2: str
    case: str
    detective_name: str
    friend_name: str
    culprit_name: str
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


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid in SETTINGS:
        for c1 in CLUES:
            for c2 in CLUES:
                if c1 != c2:
                    combos.append((sid, c1, c2))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tiny whodunit storyworld with friendship and foreshadowing.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--clue1", choices=CLUES)
    ap.add_argument("--clue2", choices=CLUES)
    ap.add_argument("--case", choices=CASES)
    ap.add_argument("--detective-name")
    ap.add_argument("--friend-name")
    ap.add_argument("--culprit-name")
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
              if (args.setting is None or c[0] == args.setting)]
    if not combos:
        raise StoryError("No valid mystery setting matches the given options.")
    setting, clue1, clue2 = rng.choice(sorted(combos))
    case = args.case or "stirred"
    detective = args.detective_name or rng.choice(NAMES_GIRL)
    friend = args.friend_name or rng.choice(NAMES_BOY)
    culprit = args.culprit_name or rng.choice([n for n in NAMES_BOY if n != friend])
    return StoryParams(setting, clue1, clue2, case, detective, friend, culprit)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], [CLUES[params.clue1], CLUES[params.clue2]], CASES[params.case],
                 params.detective_name or "Mina",
                 params.friend_name or "Owen",
                 params.culprit_name or "Pip")
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a child-friendly whodunit story that includes the words "exception" and "linguine".',
        f"Tell a friendship mystery where {f['detective'].id} and {f['friend'].id} solve a small kitchen puzzle by noticing clues.",
        f"Write a foreshadowing-heavy story where an odd detail about a bowl of linguine points to who moved it.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    d, fr, cu = f["detective"], f["friend"], f["culprit"]
    return [
        ("Who are the main friends in the story?",
         f"The main friends are {d.id} and {fr.id}. They work together and trust each other while solving the mystery."),
        ("What happened to the linguine?",
         "The bowl was missing from the table for a while. In the end, they found that it had been moved to the counter, not stolen."),
        ("What was the exception?",
         "The exception was the bowl itself. Everything else on the table was still there, but the bowl of linguine was the odd thing that had moved."),
        ("Who moved the bowl?",
         f"{cu.id} moved the bowl so the linguine could get more cheese. It turned out to be a helpful choice, not a bad one."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is a clue?",
         "A clue is a small bit of information that helps you solve a mystery. It can be an object, a mark, or something someone said."),
        ("What does foreshadowing do?",
         "Foreshadowing gives little hints early in a story. Those hints help the ending feel fair and surprising at the same time."),
        ("What is friendship?",
         "Friendship is when people care about each other, help each other, and work together kindly."),
        ("What is linguine?",
         "Linguine is a kind of pasta. It is long, flat, and often served with sauce."),
    ]


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
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


ASP_RULES = r"""
clue(C) :- clue_fact(C).
different(C1, C2) :- clue(C1), clue(C2), C1 != C2.
valid(S, C1, C2) :- setting(S), clue(C1), clue(C2), different(C1, C2).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for cid in CLUES:
        lines.append(asp.fact("clue_fact", cid))
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
        print(f"OK: ASP matches valid_combos() ({len(valid_combos())} combos).")
    else:
        rc = 1
        print("Mismatch in valid_combos() parity.")
    try:
        sample = generate(resolve_params(argparse.Namespace(setting=None, clue1=None, clue2=None, case=None,
                                                           detective_name=None, friend_name=None, culprit_name=None),
                                         random.Random(7)))
        _ = sample.story
        print("OK: generate smoke test succeeded.")
    except Exception as exc:
        rc = 1
        print(f"Smoke test failed: {exc}")
    return rc


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
        print(asp_program("", "#show valid/3."))
        return

    rng = random.Random(args.seed if args.seed is not None else random.randrange(2**31))
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(StoryParams(s, c1, c2, "stirred", "Mina", "Owen", "Pip")) for s, c1, c2 in valid_combos()[:5]]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            i += 1
            params = resolve_params(args, random.Random((args.seed or 0) + i))
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)

    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
