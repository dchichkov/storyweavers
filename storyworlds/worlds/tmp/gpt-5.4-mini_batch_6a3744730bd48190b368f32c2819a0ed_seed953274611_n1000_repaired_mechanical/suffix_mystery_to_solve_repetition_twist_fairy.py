#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/suffix_mystery_to_solve_repetition_twist_fairy.py
==================================================================================

A standalone fairy-tale story world about a small mystery, a repeated clue, and a
twist ending: a village keeps finding the same odd suffix on three things, a child
solves the puzzle by following the repetition, and the surprising culprit turns out
to be a helpful creature rather than a thief.

The story engine is tiny but state-driven:
- characters and objects carry physical meters and emotional memes
- clue-finding changes world state
- a mystery is solved through repeated clues
- the twist is grounded in the simulation, not in a frozen paragraph

Run it
------
    python storyworlds/worlds/gpt-5.4-mini/suffix_mystery_to_solve_repetition_twist_fairy.py
    python storyworlds/worlds/gpt-5.4-mini/suffix_mystery_to_solve_repetition_twist_fairy.py --all
    python storyworlds/worlds/gpt-5.4-mini/suffix_mystery_to_solve_repetition_twist_fairy.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4-mini/suffix_mystery_to_solve_repetition_twist_fairy.py --json
    python storyworlds/worlds/gpt-5.4-mini/suffix_mystery_to_solve_repetition_twist_fairy.py --verify
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
SENSE_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "queen", "woman", "princess"}
        male = {"boy", "king", "man", "prince"}
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
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)


@dataclass
class Setting:
    id: str
    place: str
    detail: str
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


@dataclass
class Clue:
    id: str
    text: str
    repeat: str
    meaning: str
    twist_hint: str
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
class Suspect:
    id: str
    label: str
    species: str
    clue_kind: str
    cause_text: str
    truth_text: str
    helps: bool = False
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
    clue: str
    suspect: str
    solver_name: str
    solver_type: str
    helper_name: str
    helper_type: str
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


def _meter(ent: Entity, key: str) -> float:
    return ent.meters.get(key, 0.0)


def _add_meter(ent: Entity, key: str, amt: float = 1.0) -> None:
    ent.meters[key] = ent.meters.get(key, 0.0) + amt


def _add_meme(ent: Entity, key: str, amt: float = 1.0) -> None:
    ent.memes[key] = ent.memes.get(key, 0.0) + amt


def _r_repeat(world: World) -> list[str]:
    out: list[str] = []
    solver = world.get("solver")
    clue = world.get("clue")
    if solver.memes.get("noticed", 0.0) < THRESHOLD:
        return out
    sig = ("repeat", clue.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    clue.meters["seen"] = clue.meters.get("seen", 0.0) + 1
    _add_meme(solver, "certainty", 1.0)
    out.append("The same clue showed up again, and now the child knew it was not an accident.")
    return out


def _r_solve(world: World) -> list[str]:
    out: list[str] = []
    solver = world.get("solver")
    suspect = world.get("suspect")
    clue = world.get("clue")
    if clue.meters.get("seen", 0.0) < 2 or solver.memes.get("certainty", 0.0) < THRESHOLD:
        return out
    sig = ("solve", clue.id, suspect.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    suspect.meters["revealed"] = suspect.meters.get("revealed", 0.0) + 1
    _add_meme(solver, "relief", 1.0)
    out.append("The pattern meant something, and the mystery loosened its knot.")
    return out


CAUSAL_RULES: list[Callable[[World], list[str]]] = [_r_repeat, _r_solve]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def clue_repeats(clue: Clue) -> bool:
    return bool(clue.repeat)


def suspect_cause_matches(clue: Clue, suspect: Suspect) -> bool:
    return clue.id == suspect.clue_kind


def valid_story(setting: Setting, clue: Clue, suspect: Suspect) -> bool:
    return clue_repeats(clue) and suspect_cause_matches(clue, suspect)


def wise_solve_possible(clue: Clue) -> bool:
    return clue.meaning in {"suffix", "pattern", "trail"}


def explain_rejection(setting: Setting, clue: Clue, suspect: Suspect) -> str:
    if not clue_repeats(clue):
        return "(No story: the clue does not repeat, so the mystery would not have a true pattern to solve.)"
    if not suspect_cause_matches(clue, suspect):
        return "(No story: that suspect does not fit the clue, so the mystery would not have an honest twist.)"
    return "(No story: this combination is not suitable for a small mystery story.)"


SETTINGS = {
    "cottage": Setting(id="cottage", place="a warm cottage", detail="The windows shone gold, and the hearth ticked softly."),
    "market": Setting(id="market", place="a sleepy village market", detail="The stalls were quiet, and apple crates made little towers of shadow."),
    "wood": Setting(id="wood", place="the moonlit wood", detail="The trees leaned close, and silver moss made the ground look like a spell."),
}

CLUES = {
    "suffix": Clue(id="suffix", text="suffix", repeat="the same ending", meaning="suffix",
                   twist_hint="what seemed like a mark was really part of a name",
                   tags={"pattern", "word", "suffix"}),
    "bell": Clue(id="bell", text="bell", repeat="the same soft ring", meaning="pattern",
                 twist_hint="the sound came from something living, not magic",
                 tags={"pattern", "sound"}),
    "footprint": Clue(id="footprint", text="footprint", repeat="the same tiny print", meaning="trail",
                      twist_hint="the tracks led to a kind helper",
                      tags={"pattern", "trail"}),
}

SUSPECTS = {
    "fox": Suspect(id="fox", label="a red fox", species="fox", clue_kind="suffix",
                   cause_text="had brushed bright petals into the ribbons",
                   truth_text="was only carrying the ribbons to the well", helps=True,
                   tags={"animal", "twist"}),
    "raven": Suspect(id="raven", label="a black raven", species="bird", clue_kind="bell",
                     cause_text="had stolen shiny things from the porch",
                     truth_text="was only ringing the little bell to call the cat", helps=True,
                     tags={"animal", "twist"}),
    "mouse": Suspect(id="mouse", label="a tiny mouse", species="mouse", clue_kind="footprint",
                     cause_text="had left tiny tracks in flour",
                     truth_text="was only taking crumbs to its nest", helps=True,
                     tags={"animal", "twist"}),
}

GIRL_NAMES = ["Ava", "Mina", "Lina", "Rose", "Elsa", "Nora"]
BOY_NAMES = ["Eli", "Finn", "Noah", "Theo", "Owen", "Milo"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid, setting in SETTINGS.items():
        for cid, clue in CLUES.items():
            for xid, suspect in SUSPECTS.items():
                if valid_story(setting, clue, suspect):
                    combos.append((sid, cid, xid))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Fairy-tale mystery world with repetition and a twist.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--suspect", choices=SUSPECTS)
    ap.add_argument("--name")
    ap.add_argument("--helper")
    ap.add_argument("--helper-type", choices=["girl", "boy", "queen", "king", "fox", "raven"], dest="helper_type")
    ap.add_argument("--solver-type", choices=["girl", "boy"], dest="solver_type")
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
              and (args.suspect is None or c[2] == args.suspect)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, clue, suspect = rng.choice(sorted(combos))
    solver_type = args.solver_type or rng.choice(["girl", "boy"])
    solver_name = args.name or rng.choice(GIRL_NAMES if solver_type == "girl" else BOY_NAMES)
    helper_type = args.helper_type or rng.choice(["fox", "raven", "girl", "boy"])
    helper_name = args.helper or rng.choice(GIRL_NAMES + BOY_NAMES)
    return StoryParams(setting=setting, clue=clue, suspect=suspect,
                       solver_name=solver_name, solver_type=solver_type,
                       helper_name=helper_name, helper_type=helper_type)


def tell(params: StoryParams) -> World:
    world = World()
    setting = SETTINGS[params.setting]
    clue = CLUES[params.clue]
    suspect = SUSPECTS[params.suspect]

    solver = world.add(Entity(id="solver", kind="character", type=params.solver_type, label=params.solver_name, role="solver"))
    helper = world.add(Entity(id="helper", kind="character", type=params.helper_type, label=params.helper_name, role="helper"))
    clue_ent = world.add(Entity(id="clue", kind="thing", type="clue", label=clue.text))
    suspect_ent = world.add(Entity(id="suspect", kind="thing", type="suspect", label=suspect.label))

    _add_meme(solver, "curious", 1.0)
    _add_meme(helper, "gentle", 1.0)

    world.say(f"Once in {setting.place}, {solver.label_word} loved looking for odd things.")
    world.say(f"{setting.detail} One evening, {solver.label_word} found a mystery: {clue.text}.")
    world.say(f"{solver.label_word} whispered it twice, then once more: “{clue.repeat}, {clue.repeat}, {clue.repeat}.”")
    world.para()

    _add_meme(solver, "noticed", 1.0)
    world.say(f'"I hear a pattern," {solver.label_word} said. "{clue.text} keeps coming back."')
    world.say(f"{helper.label_word.capitalize()} looked too, and they searched beside the gate and under the fern.")
    propagate(world)
    world.say(f"At the third place, the clue returned again, exactly like before.")
    world.para()

    world.say(f"That was when {solver.label_word} solved the mystery.")
    if suspect.helps:
        world.say(f"The answer was a twist: {suspect.label} was not stealing the clue at all.")
        world.say(f"{suspect.label_word if hasattr(suspect, 'label_word') else suspect.label} had {suspect.truth_text}.")
    else:
        world.say(f"The answer was a twist: {suspect.label} had been hiding in plain sight.")
        world.say(suspect.truth_text)

    world.say(f"The strange ending made sense at last: {clue.twist_hint}.")
    world.say(f"{solver.label_word} smiled, and the village felt small and safe again.")
    world.facts.update(setting=setting, clue=clue, suspect=suspect, solver=solver, helper=helper,
                       solved=solver.memes.get("relief", 0.0) >= THRESHOLD)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    clue: Clue = f["clue"]
    return [
        f'Write a fairy-tale mystery story that includes the word "{clue.text}".',
        f"Tell a short story with repetition, a small mystery, and a twist ending where the clue {clue.repeat} keeps appearing.",
        f"Write a gentle village mystery for a child where someone notices a pattern and solves it with kindness.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    clue: Clue = f["clue"]
    suspect: Suspect = f["suspect"]
    solver: Entity = f["solver"]
    helper: Entity = f["helper"]
    return [
        ("What kind of story is this?",
         "It is a fairy-tale mystery with repetition and a twist. The repeated clue helps the child solve the puzzle."),
        (f"What clue kept coming back?",
         f"The clue was {clue.text}. It appeared again and again, so {solver.label_word} could tell it was part of a pattern."),
        (f"Who helped look for the answer?",
         f"{helper.label_word.capitalize()} helped {solver.label_word} search. Together they followed the repeated clue until the mystery opened up."),
        (f"What was the twist?",
         f"The twist was that {suspect.label} was not a bad actor at all. The surprising answer made the strange clue make sense."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    clue: Clue = world.facts["clue"]
    return [
        ("What is a suffix?",
         "A suffix is a little part added to the end of a word. It can change how the word sounds or what it means."),
        ("What does repetition do in a story?",
         "Repetition means something happens or is said again and again. It helps listeners notice an important pattern."),
        ("What is a twist in a story?",
         "A twist is a surprising turn that changes how you understand the story. It makes the ending feel clever and new."),
    ] if clue.id == "suffix" else [
        ("What does repetition do in a story?",
         "Repetition means something happens or is said again and again. It helps listeners notice an important pattern."),
        ("What is a twist in a story?",
         "A twist is a surprising turn that changes how you understand the story. It makes the ending feel clever and new."),
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
        if e.role:
            bits.append(f"role={e.role}")
        if e.meters:
            bits.append(f"meters={dict(e.meters)}")
        if e.memes:
            bits.append(f"memes={dict(e.memes)}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(setting="cottage", clue="suffix", suspect="fox", solver_name="Lina", solver_type="girl", helper_name="Milo", helper_type="boy"),
    StoryParams(setting="market", clue="bell", suspect="raven", solver_name="Eli", solver_type="boy", helper_name="Ava", helper_type="girl"),
    StoryParams(setting="wood", clue="footprint", suspect="mouse", solver_name="Nora", solver_type="girl", helper_name="Theo", helper_type="boy"),
]


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for cid, clue in CLUES.items():
        lines.append(asp.fact("clue", cid))
        if clue.repeat:
            lines.append(asp.fact("repeats", cid))
        lines.append(asp.fact("meaning", cid, clue.meaning))
    for xid, suspect in SUSPECTS.items():
        lines.append(asp.fact("suspect", xid))
        lines.append(asp.fact("clue_kind", xid, suspect.clue_kind))
    return "\n".join(lines)


ASP_RULES = r"""
valid(S, C, X) :- setting(S), clue(C), suspect(X), repeats(C), clue_kind(X, C).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        rc = 1
        print("MISMATCH: ASP valid combos differ from Python valid_combos().")
    else:
        print(f"OK: ASP matches valid_combos() ({len(valid_combos())} combos).")
    try:
        sample = generate(resolve_params(argparse.Namespace(setting=None, clue=None, suspect=None, name=None, helper=None, helper_type=None, solver_type=None), random.Random(0)))
        _ = sample.story
        print("OK: normal generate() smoke test passed.")
    except Exception as e:
        rc = 1
        print(f"MISMATCH: generate() smoke test failed: {e}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    return argparse.ArgumentParser(description="Fairy-tale mystery world with repetition and a twist.")


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_combos()
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    sid, cid, xid = rng.choice(sorted(combos))
    solver_type = rng.choice(["girl", "boy"])
    helper_type = rng.choice(["girl", "boy"])
    solver_name = rng.choice(GIRL_NAMES if solver_type == "girl" else BOY_NAMES)
    helper_name = rng.choice(GIRL_NAMES if helper_type == "girl" else BOY_NAMES)
    return StoryParams(setting=sid, clue=cid, suspect=xid, solver_name=solver_name, solver_type=solver_type,
                       helper_name=helper_name, helper_type=helper_type)


GIRL_NAMES = ["Ava", "Mina", "Lina", "Rose", "Elsa", "Nora", "Ivy"]
BOY_NAMES = ["Eli", "Finn", "Noah", "Theo", "Owen", "Milo", "Jasper"]


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS or params.clue not in CLUES or params.suspect not in SUSPECTS:
        raise StoryError("Invalid params.")
    world = tell(params)
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
        for combo in asp_valid_combos():
            print(combo)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
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
