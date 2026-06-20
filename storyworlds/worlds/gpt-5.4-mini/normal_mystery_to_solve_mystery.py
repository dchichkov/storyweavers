#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/normal_mystery_to_solve_mystery.py
===================================================================

A standalone story world for a small, child-facing mystery:
a child notices that something normal has gone missing,
follows clues through a few ordinary places, and solves the mystery
with a calm helper and a sensible ending.

The domain is intentionally tiny:
- a child has a favorite normal object
- that object disappears from its usual place
- clues in the world point to a hidden spot
- a helper explains the answer
- the object is found and the world returns to normal

The story is built from simulated state, not from a frozen paragraph.
It supports the shared Storyweavers contract, plus an inline ASP twin
for the reasonableness gate and outcome parity checks.
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
        female = {"girl", "mother", "mom", "woman", "aunt"}
        male = {"boy", "father", "dad", "man", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type



    @property
    def phrase(self) -> str:
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

@dataclass
class Clue:
    id: str
    label: str
    hint: str
    location: str
    reveals: str
    truthful: bool = True

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
class HiddenThing:
    id: str
    label: str
    phrase: str
    usual_spot: str
    hidden_spot: str
    normalness: str
    portable: bool = True
    tags: set[str] = field(default_factory=set)

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
class Helper:
    id: str
    label: str
    phrase: str
    calm: str
    method: str
    answer: str
    tags: set[str] = field(default_factory=set)

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


def _r_worry(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    if child.meters["mystery"] >= THRESHOLD and ("worry", "child") not in world.fired:
        world.fired.add(("worry", "child"))
        child.memes["worry"] += 1
        out.append("__worry__")
    return out


def _r_clue(world: World) -> list[str]:
    out: list[str] = []
    if world.facts.get("got_clue") and ("clue", world.facts.get("clue_id")) not in world.fired:
        world.fired.add(("clue", world.facts.get("clue_id")))
        helper = world.get("helper")
        helper.memes["helpful"] += 1
        out.append("__clue__")
    return out


CAUSAL_RULES = [Rule("worry", "social", _r_worry), Rule("clue", "social", _r_clue)]


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


def normal_storyable(missing: HiddenThing, clue: Clue) -> bool:
    return missing.portable and clue.truthful


def predict_solution(world: World, clue: Clue, hidden: HiddenThing) -> bool:
    sim = world.copy()
    sim.facts["got_clue"] = True
    sim.facts["clue_id"] = clue.id
    sim.get("child").meters["mystery"] += 1
    return clue.reveals == hidden.hidden_spot


def setup(world: World, child: Entity, helper: Entity, hidden: HiddenThing) -> None:
    child.memes["curiosity"] += 1
    child.memes["love"] += 1
    world.say(
        f"{child.id} had a normal morning and a normal plan: find {hidden.phrase}."
    )
    world.say(
        f"It always stayed in {hidden.usual_spot}, and that was where {child.id} "
        f"expected to see it."
    )


def notice_missing(world: World, child: Entity, hidden: HiddenThing) -> None:
    child.meters["mystery"] += 1
    child.memes["surprise"] += 1
    world.say(
        f"But when {child.id} looked, {hidden.phrase} was gone. "
        f"The spot looked normal, yet something was not right."
    )
    world.say(f'{child.id} frowned. "That is strange," {child.pronoun()} said.')


def search_clue(world: World, child: Entity, clue: Clue) -> None:
    child.memes["determination"] += 1
    world.say(
        f"{child.id} checked {clue.location} and found {clue.hint}. "
        f"It felt like a small clue in a bigger mystery."
    )


def ask_helper(world: World, child: Entity, helper: Entity, clue: Clue) -> None:
    world.facts["got_clue"] = True
    world.facts["clue_id"] = clue.id
    propagate(world, narrate=False)
    world.say(
        f"Then {child.id} asked {helper.id}, who stayed calm and listened. "
        f'{helper.id} pointed at {clue.reveals} and said, "{helper.answer}"'
    )


def solve(world: World, child: Entity, hidden: HiddenThing, helper: Entity) -> None:
    child.memes["relief"] += 1
    child.memes["joy"] += 1
    world.get("child").meters["mystery"] = 0.0
    world.say(
        f"At last, {hidden.phrase} was found in {hidden.hidden_spot}. "
        f"It had simply been put there for safekeeping."
    )
    world.say(
        f'{child.id} laughed and said, "Oh! So that is the normal answer." '
        f"{helper.id} smiled, and the room felt normal again."
    )


def tell(hidden: HiddenThing, clue: Clue, helper_def: Helper,
         child_name: str = "Milo", child_gender: str = "boy",
         helper_name: str = "Aunt June", helper_gender: str = "woman") -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="child"))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_gender, role="helper"))
    world.add(Entity(id="home", kind="place", type="room", label="the house"))
    world.add(Entity(id="usual", kind="place", type="place", label=hidden.usual_spot))
    world.add(Entity(id="hidden", kind="place", type="place", label=hidden.hidden_spot))

    setup(world, child, helper, hidden)
    world.para()
    notice_missing(world, child, hidden)
    search_clue(world, child, clue)
    world.para()
    ask_helper(world, child, helper, clue)
    solve(world, child, hidden, helper)

    world.facts.update(
        child=child,
        helper=helper,
        hidden=hidden,
        clue=clue,
        solved=True,
        clue_found=True,
        normal=hidden.normalness,
    )
    return world


HIDDEN_THINGS = {
    "glasses": HiddenThing(
        "glasses", "glasses", "the glasses", "the table", "the bedside shelf",
        "very normal", tags={"normal", "find", "glasses"}
    ),
    "key": HiddenThing(
        "key", "key", "the small key", "the bowl by the door", "the cookie jar",
        "very normal", tags={"normal", "find", "key"}
    ),
    "toy": HiddenThing(
        "toy", "toy", "the tiny toy car", "the toy box", "the laundry basket",
        "very normal", tags={"normal", "find", "toy"}
    ),
}

CLUES = {
    "crumbs": Clue("crumbs", "crumbs", "a few crumbs on the floor", "the kitchen",
                   "the kitchen", truthful=True),
    "blanket": Clue("blanket", "blanket", "a blanket folded a little too neatly",
                    "the couch", "the couch", truthful=True),
    "smile": Clue("smile", "smile", "a helpful smile from the helper",
                  "the hallway", "the hallway", truthful=True),
}

HELPERS = {
    "aunt": Helper("aunt", "aunt", "Aunt June", "calm", "look carefully", "It was put away in a safe place.", tags={"helper"}),
    "uncle": Helper("uncle", "uncle", "Uncle Ben", "calm", "think slowly", "Try the place where normal things are kept.", tags={"helper"}),
}

GIRL_NAMES = ["Mia", "Nora", "Lily", "Ava", "Zoe"]
BOY_NAMES = ["Milo", "Noah", "Eli", "Theo", "Finn"]


@dataclass
@dataclass
class StoryParams:
    hidden: str
    clue: str
    helper: str
    child: str
    child_gender: str
    helper_name: str
    helper_gender: str
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
    for hid in HIDDEN_THINGS:
        for clue in CLUES:
            for helper in HELPERS:
                if normal_storyable(HIDDEN_THINGS[hid], CLUES[clue]):
                    combos.append((hid, clue, helper))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small mystery story world about finding something normal.")
    ap.add_argument("--hidden", choices=HIDDEN_THINGS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--child")
    ap.add_argument("--child-gender", choices=["boy", "girl"])
    ap.add_argument("--helper-name")
    ap.add_argument("--helper-gender", choices=["man", "woman"])
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
              if (args.hidden is None or c[0] == args.hidden)
              and (args.clue is None or c[1] == args.clue)
              and (args.helper is None or c[2] == args.helper)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    hidden, clue, helper = rng.choice(sorted(combos))
    hg = args.helper_gender or rng.choice(["man", "woman"])
    cg = args.child_gender or rng.choice(["boy", "girl"])
    child = args.child or rng.choice(BOY_NAMES if cg == "boy" else GIRL_NAMES)
    helper_name = args.helper_name or HELPERS[helper].phrase
    return StoryParams(hidden, clue, helper, child, cg, helper_name, hg)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a child-friendly mystery story that includes the word "normal" and ends with a solved clue.',
        f"Tell a calm mystery where {f['child'].id} notices {f['hidden'].phrase} is missing and asks for help.",
        f"Write a short story about a normal thing that was hidden, a clue, and a helper who solves the mystery.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child, helper, hidden, clue = f["child"], f["helper"], f["hidden"], f["clue"]
    return [
        ("What was missing?",
         f"{hidden.phrase} was missing from {hidden.usual_spot}, which made the morning feel odd."),
        ("What was the clue?",
         f"The clue was {clue.hint}. It helped point the search toward {clue.reveals}."),
        ("Who helped solve the mystery?",
         f"{helper.id} helped solve it by staying calm and explaining where to look next."),
        ("How did the mystery end?",
         f"It ended with {hidden.phrase} found in {hidden.hidden_spot}, so everything felt normal again."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What does normal mean?",
         "Normal means usual or expected. It is what something is like when nothing strange is happening."),
        ("What is a clue?",
         "A clue is a small piece of information that helps solve a mystery."),
        ("What should you do when you cannot find something?",
         "Look carefully, stay calm, and ask a grown-up or helper for help."),
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
        if e.label:
            bits.append(f"label={e.label}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams("glasses", "crumbs", "aunt", "Milo", "boy", "Aunt June", "woman"),
    StoryParams("key", "smile", "uncle", "Nora", "girl", "Uncle Ben", "man"),
    StoryParams("toy", "blanket", "aunt", "Eli", "boy", "Aunt June", "woman"),
]


def explain_rejection() -> str:
    return "(No story: the requested choices do not make a solvable mystery.)"


def asp_facts() -> str:
    import asp
    lines = []
    for hid in HIDDEN_THINGS:
        lines.append(asp.fact("hidden", hid))
    for cid in CLUES:
        lines.append(asp.fact("clue", cid))
    for hid, h in HIDDEN_THINGS.items():
        lines.append(asp.fact("portable", hid))
        lines.append(asp.fact("normal", hid))
        lines.append(asp.fact("usual_spot", hid, h.usual_spot))
        lines.append(asp.fact("hidden_spot", hid, h.hidden_spot))
    for cid, c in CLUES.items():
        lines.append(asp.fact("truthful", cid))
        lines.append(asp.fact("reveals", cid, c.reveals))
    return "\n".join(lines)


ASP_RULES = r"""
solvable(H, C) :- hidden(H), clue(C), portable(H), truthful(C), hidden_spot(H, S), reveals(C, S).
solution(H) :- solvable(H, _).
"""


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show solvable/2."))
    return sorted(set(asp.atoms(model, "solvable")))


def asp_verify() -> int:
    import io
    import contextlib

    rc = 0
    if set(asp_valid_combos()) != set((h, c) for h, c, _ in [(a, b, c) for a, b, c in valid_combos()]):
        rc = 1
        print("MISMATCH in ASP validity.")
    try:
        sample = generate(resolve_params(argparse.Namespace(hidden=None, clue=None, helper=None,
                                                            child=None, child_gender=None,
                                                            helper_name=None, helper_gender=None),
                                         random.Random(777)))
        _ = sample.story
        print("OK: story generation smoke test passed.")
    except Exception as e:
        print(f"SMOKE TEST FAILED: {e}")
        return 1
    return rc


def generate(params: StoryParams) -> StorySample:
    world = tell(HIDDEN_THINGS[params.hidden], CLUES[params.clue], HELPERS[params.helper],
                 params.child, params.child_gender, params.helper_name, params.helper_gender)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
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
        print(asp_program("", "#show solvable/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_program("", "#show solvable/2."))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
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
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")
if __name__ == "__main__":
    main()
