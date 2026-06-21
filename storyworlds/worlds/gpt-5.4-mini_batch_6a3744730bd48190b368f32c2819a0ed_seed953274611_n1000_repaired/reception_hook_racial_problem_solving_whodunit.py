#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/reception_hook_racial_problem_solving_whodunit.py
==================================================================================

A small whodunit storyworld about a community reception, a missing hook, and a
child detective who solves the mystery by noticing clues, asking careful
questions, and fixing the problem without blame.

The seed words are worked into the world as:
- reception: a welcoming event in the town hall
- hook: a small metal hook that goes missing from the cloak display
- racial: the reception celebrates racial harmony and shared community stories

The domain stays child-facing and concrete. The mystery is not about race as an
issue; rather, "racial" appears in the event name and the story respects every
person at the reception.

Run it
------
    python storyworlds/worlds/gpt-5.4-mini/reception_hook_racial_problem_solving_whodunit.py
    python storyworlds/worlds/gpt-5.4-mini/reception_hook_racial_problem_solving_whodunit.py --qa --json
    python storyworlds/worlds/gpt-5.4-mini/reception_hook_racial_problem_solving_whodunit.py --all
    python storyworlds/worlds/gpt-5.4-mini/reception_hook_racial_problem_solving_whodunit.py --verify
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
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man"}
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

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Place:
    id: str
    label: str
    hooks: int
    decor: str
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
    label: str
    found_in: str
    meaning: str
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
class Fix:
    id: str
    label: str
    method: str
    success: str
    failure: str
    sense: int
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
        c = World()
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        return c


@dataclass
class Rule:
    name: str
    tag: str
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


def _r_search(world: World) -> list[str]:
    out = []
    if world.facts.get("searching") and not world.facts.get("hook_found"):
        sig = ("search",)
        if sig not in world.fired:
            world.fired.add(sig)
            clue = world.facts.get("clue")
            if clue:
                out.append(f"__found__")
    return out


def _r_relief(world: World) -> list[str]:
    out = []
    if world.facts.get("hook_found") and not world.facts.get("relief_done"):
        sig = ("relief",)
        if sig not in world.fired:
            world.fired.add(sig)
            for eid in ("detective", "host"):
                if eid in world.entities:
                    world.get(eid).memes["relief"] += 1
            out.append("__relief__")
    return out


CAUSAL_RULES = [Rule("search", "mystery", _r_search), Rule("relief", "social", _r_relief)]


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


def reasonable_combo(place: Place, clue: Clue, fix: Fix) -> bool:
    return place.hooks > 0 and fix.sense >= 2 and fix.power >= 1 and clue.found_in == place.id


def sensible_fixes() -> list[Fix]:
    return [f for f in FIXES.values() if f.sense >= 2]


def solveable(place: Place, fix: Fix) -> bool:
    return fix.power >= place.hooks


def predict_loss(world: World, place_id: str) -> dict:
    sim = world.copy()
    sim.get(place_id).meters["missing_hook"] += 1
    return {"missing": sim.get(place_id).meters["missing_hook"] >= THRESHOLD}


def open_scene(world: World, child: Entity, host: Entity, place: Place) -> None:
    child.memes["curiosity"] += 1
    world.say(
        f"At the {place.label}, the reception was bright with music, paper stars, "
        f"and warm cookies. {host.id} welcomed everyone to a racial harmony reception, "
        f"where families shared songs and stories."
    )
    world.say(
        f"{child.id} noticed the cloak corner right away. A little brass hook was missing, "
        f"and one coat hung crooked beside the empty spot."
    )


def inspect(world: World, child: Entity, host: Entity, clue: Clue, place: Place) -> None:
    child.memes["attention"] += 1
    world.facts["searching"] = True
    world.say(
        f'"Something is off," {child.id} said softly. {child.pronoun().capitalize()} '
        f'looked at the floor and saw a {clue.label} {clue.found_in}.'
    )
    world.say(
        f'"That clue means the hook did not disappear," {child.id} said. '
        f'It was pulled away during the busy reception, not stolen forever.'
    )


def question(world: World, child: Entity, host: Entity, clue: Clue) -> None:
    world.say(
        f"{child.id} asked a few careful questions: who used the cloak corner, "
        f"when the coats were moved, and whether anyone had bumped the display."
    )
    world.say(
        f"{host.id} thought, then pointed toward the refreshment table. "
        f"The answer had to fit the clue, not just the worry."
    )


def reveal(world: World, fix: Fix, place: Place, host: Entity) -> None:
    world.facts["hook_found"] = True
    if fix.sense >= 2:
        world.say(
            f"{child_name(world)} noticed a tiny metal shine near the ribbon box. "
            f"The hook had slipped behind a stack of programs when a chair was nudged."
        )
        world.say(
            f'{host.id} smiled. "{fix.success}," {host.pronoun()} said, and the cloak corner '
            f"was ready again."
        )


def child_name(world: World) -> str:
    return world.facts["detective"].id


def fix_problem(world: World, fix: Fix, place: Place, host: Entity, child: Entity) -> None:
    if solveable(place, fix):
        world.say(
            f"With {fix.method}, {child.id} put the small hook back where it belonged. "
            f"The crooked coat hung straight again."
        )
        world.say(
            f"{host.id} thanked {child.id} for being calm, curious, and fair."
        )
    else:
        world.say(
            f"{fix.failure}. The crooked coat still leaned sideways, so the mystery was not solved."
        )


def end_scene(world: World, child: Entity, host: Entity, place: Place) -> None:
    child.memes["pride"] += 1
    world.say(
        f"By the end of the reception, the music was still playing, the coats were straight, "
        f"and the guests kept talking and laughing under the paper stars."
    )
    world.say(
        f"{child.id} had solved the little mystery by looking closely and asking kind questions."
    )


def tell(place: Place, clue: Clue, fix: Fix, child_name: str, child_type: str, host_type: str) -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_type, role="detective"))
    host = world.add(Entity(id="Host", kind="character", type=host_type, role="host", label="the host"))
    world.add(Entity(id="hook", label="hook"))
    world.facts.update(detective=child, host=host, place=place, clue=clue, fix=fix)
    open_scene(world, child, host, place)
    world.para()
    inspect(world, child, host, clue, place)
    question(world, child, host, clue)
    world.para()
    reveal(world, fix, place, host)
    fix_problem(world, fix, place, host, child)
    end_scene(world, child, host, place)
    world.facts["solved"] = True
    return world


PLACES = {
    "town_hall": Place(
        id="town_hall",
        label="town hall",
        hooks=3,
        decor="paper stars",
        tags={"reception", "hook", "racial"},
    ),
    "library_room": Place(
        id="library_room",
        label="library room",
        hooks=2,
        decor="lanterns",
        tags={"reception", "hook"},
    ),
    "school_gym": Place(
        id="school_gym",
        label="school gym",
        hooks=4,
        decor="bright banners",
        tags={"reception", "hook", "racial"},
    ),
}

CLUES = {
    "scratch": Clue(
        id="scratch",
        label="silver scratch",
        found_in="by the coat stand",
        meaning="the hook had scraped the floor",
        tags={"hook"},
    ),
    "ribbon": Clue(
        id="ribbon",
        label="blue ribbon",
        found_in="near the ribbon box",
        meaning="the hook got moved with the decorations",
        tags={"hook", "reception"},
    ),
    "thread": Clue(
        id="thread",
        label="red thread",
        found_in="under the welcome table",
        meaning="the hook was carried under papers",
        tags={"hook", "racial"},
    ),
}

FIXES = {
    "search_under_table": Fix(
        id="search_under_table",
        label="look under the table",
        method="a flashlight and a careful look under the welcome table",
        success="That was the missing hook",
        failure="They looked under the table, but the hook was not there",
        sense=2,
        power=1,
        tags={"problem_solving"},
    ),
    "check_ribbon_box": Fix(
        id="check_ribbon_box",
        label="check the ribbon box",
        method="checking the ribbon box and the pile of programs",
        success="The hook had slipped behind the programs",
        failure="The ribbon box was empty, so that clue did not help",
        sense=3,
        power=2,
        tags={"problem_solving"},
    ),
    "move_coats": Fix(
        id="move_coats",
        label="move the coats",
        method="lifting the coats aside one by one and following the shiny clue",
        success="The hook was hiding exactly where the shiny clue pointed",
        failure="The coats were too heavy to help, and the mystery stayed stuck",
        sense=4,
        power=3,
        tags={"problem_solving"},
    ),
}

@dataclass
class StoryParams:
    place: str
    clue: str
    fix: str
    child_name: str
    child_type: str
    host_type: str
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


CURATED = [
    StoryParams(place="town_hall", clue="thread", fix="check_ribbon_box",
                child_name="Maya", child_type="girl", host_type="woman", seed=1),
    StoryParams(place="school_gym", clue="scratch", fix="move_coats",
                child_name="Eli", child_type="boy", host_type="man", seed=2),
    StoryParams(place="library_room", clue="ribbon", fix="search_under_table",
                child_name="Nora", child_type="girl", host_type="woman", seed=3),
]


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for pid, place in PLACES.items():
        for cid, clue in CLUES.items():
            for fid, fix in FIXES.items():
                if reasonable_combo(place, clue, fix):
                    out.append((pid, cid, fid))
    return out


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a child-friendly whodunit set at a {f["place"].label} reception and include the words "reception", "hook", and "racial".',
        f"Tell a small mystery where {f['detective'].id} notices a missing hook during a community reception and solves it by following a clue.",
        f"Write a problem-solving story where a careful child asks kind questions at a racial harmony reception and finds the missing hook.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["detective"]
    host = f["host"]
    place = f["place"]
    clue = f["clue"]
    fix = f["fix"]
    return [
        ("What kind of event was happening?",
         f"It was a reception, and the room was decorated for a racial harmony reception with music, cookies, and paper stars."),
        ("What was missing?",
         "A small brass hook was missing from the cloak corner."),
        ("How did the detective solve the mystery?",
         f"{child.id} looked for clues, asked careful questions, and then used {fix.method} to find the hook."),
        ("What did the host think of the solution?",
         f"{host.id} was pleased because the answer fit the clue and fixed the problem without blaming anyone."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is a reception?",
         "A reception is a welcoming event where people gather, talk, and often eat snacks."),
        ("What is a hook?",
         "A hook is a small curved piece that can hold a coat, a bag, or a sign."),
        ("What does it mean to solve a problem?",
         "To solve a problem means to find out what is wrong and choose a good way to fix it."),
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
        bits = []
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
solved :- place(P), clue(C), fix(F), valid(P,C,F).
valid(P,C,F) :- hooks(P,H), H > 0, clue_at(C,P), fix_sense(F,S), S >= 2.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        lines.append(asp.fact("hooks", pid, p.hooks))
    for cid, c in CLUES.items():
        lines.append(asp.fact("clue", cid))
        lines.append(asp.fact("clue_at", cid, c.found_in.replace(" ", "_")))
    for fid, f in FIXES.items():
        lines.append(asp.fact("fix", fid))
        lines.append(asp.fact("fix_sense", fid, f.sense))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        print("MISMATCH: ASP and Python valid_combos differ.")
        rc = 1
    try:
        sample = generate(resolve_params(argparse.Namespace(place=None, clue=None, fix=None,
                                                            child_name=None, child_type=None,
                                                            host_type=None, seed=None),
                                          random.Random(7)))
        _ = sample.story
        print("OK: story generation smoke test passed.")
    except Exception as exc:  # noqa: BLE001
        print(f"FAILED smoke test: {exc}")
        rc = 1
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Whodunit storyworld about a reception and a missing hook.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--name", dest="child_name")
    ap.add_argument("--child-type", choices=["girl", "boy"], dest="child_type")
    ap.add_argument("--host-type", choices=["woman", "man"], dest="host_type")
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
              if (args.place is None or c[0] == args.place)
              and (args.clue is None or c[1] == args.clue)
              and (args.fix is None or c[2] == args.fix)]
    if not combos:
        curated = globals().get("CURATED", [])
        explicit = [
            v for k, v in vars(args).items()
            if k not in {"n", "seed", "all", "trace", "qa", "json", "asp", "verify", "show_asp"}
            and v is not None
            and v is not False
        ]
        if curated and not explicit:
            choice = rng.choice(curated)
            return choice if isinstance(choice, StoryParams) else StoryParams(*choice)
        raise StoryError("(No valid combination matches the given options.)")
    place, clue, fix = rng.choice(sorted(combos))
    child_type = args.child_type or rng.choice(["girl", "boy"])
    child_name = args.child_name or rng.choice(["Maya", "Eli", "Nora", "Owen", "Iris", "Noah"])
    host_type = args.host_type or rng.choice(["woman", "man"])
    return StoryParams(place=place, clue=clue, fix=fix, child_name=child_name,
                       child_type=child_type, host_type=host_type)


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES or params.clue not in CLUES or params.fix not in FIXES:
        raise StoryError("Invalid story params.")
    place = PLACES[params.place]
    clue = CLUES[params.clue]
    fix = FIXES[params.fix]
    if not reasonable_combo(place, clue, fix):
        raise StoryError("This combination does not form a reasonable mystery.")
    world = tell(place, clue, fix, params.child_name, params.child_type, params.host_type)
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
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos:")
        for triple in asp_valid_combos():
            print(" ", triple)
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(args.n):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))
    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i + 1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
