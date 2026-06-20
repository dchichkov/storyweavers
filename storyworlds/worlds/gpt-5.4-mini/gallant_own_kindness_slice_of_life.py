#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/gallant_own_kindness_slice_of_life.py
======================================================================

A standalone storyworld for a small slice-of-life kindness story built from the
seed words *gallant* and *own*.

Premise
-------
A child notices someone having a small, ordinary problem in daily life, offers a
gallant act of kindness, and ends up making the day warmer for everyone. The
domain stays grounded in a simple neighborhood / school-day setting and keeps
the state model visible: a lost or awkward item, a helpful action, feelings
changing, and a gentle ending image that proves what improved.

This world is intentionally narrow: it prefers a few plausible, well-shaped
stories over many weak ones. It includes a Python reasonableness gate plus an
inline ASP twin, and supports the shared Storyweavers interface.
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
EMPATHY_MIN = 1.0


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
        female = {"girl", "mother", "mom", "woman", "sister", "aunt"}
        male = {"boy", "father", "dad", "man", "brother", "uncle"}
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
    light: str
    mood: str
    affords: set[str] = field(default_factory=set)

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
class Problem:
    id: str
    name: str
    item: str
    trouble: str
    need: str
    location: str
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
class KindAct:
    id: str
    name: str
    verb: str
    object: str
    help_text: str
    result_text: str
    power: int
    sense: int
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
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
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
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
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


def _r_soften(world: World) -> list[str]:
    out: list[str] = []
    for ent in list(world.entities.values()):
        if ent.meters["trouble"] < THRESHOLD:
            continue
        sig = ("soften", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        ent.meters["soften"] += 1
        out.append("__soften__")
    return out


CAUSAL_RULES: list[Rule] = [Rule("soften", "social", _r_soften)]


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


def is_reasonable(problem: Problem, act: KindAct, setting: Setting) -> bool:
    return problem.id in setting.affords and act.power >= EMPATHY_MIN and act.sense >= 2


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid, setting in SETTINGS.items():
        for pid, problem in PROBLEMS.items():
            if pid not in setting.affords:
                continue
            for aid, act in KIND_ACTS.items():
                if is_reasonable(problem, act, setting):
                    combos.append((sid, pid, aid))
    return combos


def predict(world: World, problem_id: str) -> dict:
    sim = world.copy()
    _do_kindness(sim, sim.get("helper"), sim.get(problem_id), KIND_ACTS[sim.facts["act"].id], narrate=False)
    return {
        "fixed": sim.get(problem_id).meters["trouble"] < THRESHOLD,
        "warmth": sim.get("helper").memes["warmth"],
    }


def _do_kindness(world: World, helper: Entity, problem: Entity, act: KindAct, narrate: bool = True) -> None:
    problem.meters["trouble"] = 0.0
    helper.memes["warmth"] += 1
    helper.memes["pride"] += 1
    propagate(world, narrate=narrate)


def setup(world: World, helper: Entity, other: Entity, setting: Setting) -> None:
    helper.memes["joy"] += 1
    other.memes["joy"] += 1
    world.say(
        f"On an ordinary afternoon, {helper.id} and {other.id} were at {setting.place}. "
        f"The day felt {setting.mood}, with {setting.light} coming through the windows."
    )


def introduce_problem(world: World, other: Entity, problem: Problem) -> None:
    other.meters["trouble"] += 1
    other.memes["embarrassed"] += 1
    world.say(
        f"Then {problem.name} had a small problem: {problem.item} was {problem.trouble} "
        f"{problem.location}, and that made {other.id} look worried."
    )
    world.say(f"{other.id} wished someone would help with {problem.need}.")


def notice(world: World, helper: Entity, other: Entity, problem: Problem) -> None:
    helper.memes["kindness"] += 1
    world.say(
        f"{helper.id} noticed right away. {helper.id} gave {other.id} a gallant smile and said, "
        f'"Don’t worry. I can help with your own {problem.item}."'
    )


def act(world: World, helper: Entity, other: Entity, problem: Problem, act: KindAct) -> None:
    world.say(
        f"{helper.id} {act.verb} {act.object} and {act.help_text}. "
        f"{act.result_text}."
    )
    _do_kindness(world, helper, world.get(problem.id), act)


def ending(world: World, helper: Entity, other: Entity, problem: Problem) -> None:
    world.say(
        f"After that, {other.id} smiled again and held {other.pronoun('possessive')} {problem.item} close. "
        f"{helper.id} felt gallant in the quiet way that makes a normal day brighter."
    )
    if problem.id == "lunch":
        world.say(f"At lunch, the table was calm, and the little worry was gone.")
    elif problem.id == "drawing":
        world.say(f"By the end, the drawing looked finished and neat instead of messy.")
    elif problem.id == "raincoat":
        world.say(f"Later, the raincoat hung neatly by the door, ready for the next walk.")
    elif problem.id == "book":
        world.say(f"The book was dry and safe again, waiting for the next page.")


def tell(setting: Setting, problem: Problem, act: KindAct,
         helper_name: str = "Mia", helper_gender: str = "girl",
         other_name: str = "Noah", other_gender: str = "boy",
         adult_name: str = "Parent", adult_gender: str = "mother") -> World:
    world = World(setting)
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_gender, role="helper"))
    other = world.add(Entity(id=other_name, kind="character", type=other_gender, role="other"))
    adult = world.add(Entity(id=adult_name, kind="character", type=adult_gender, role="adult", label="the adult"))
    prob = world.add(Entity(id=problem.id, kind="thing", type="thing", label=problem.item))
    world.facts.update(setting=setting, problem=problem, act=act, helper=helper, other=other, adult=adult, prob=prob)

    setup(world, helper, other, setting)
    world.para()
    introduce_problem(world, other, problem)
    notice(world, helper, other, problem)
    world.para()
    act(world, helper, other, problem, act)
    ending(world, helper, other, problem)

    world.facts["fixed"] = prob.meters["trouble"] < THRESHOLD
    return world


SETTINGS = {
    "kitchen": Setting("kitchen", "the kitchen", "sunlight", "soft and busy", {"lunch", "napkin"}),
    "classroom": Setting("classroom", "the classroom", "lamp light", "bright and calm", {"drawing", "book"}),
    "porch": Setting("porch", "the porch", "late-afternoon light", "quiet and warm", {"raincoat"}),
    "library": Setting("library", "the library corner", "soft lamp light", "still and gentle", {"book"}),
}

PROBLEMS = {
    "lunch": Problem("lunch", "Tina's lunch", "sandwich", "sliding off the plate", "a napkin", "the table", {"lunch"}),
    "drawing": Problem("drawing", "Aria's drawing", "paper", "smudged with paint", "a fresh sheet", "the desk", {"drawing"}),
    "raincoat": Problem("raincoat", "Ben's raincoat", "zipper", "stuck halfway up", "a careful tug", "the hook by the door", {"raincoat"}),
    "book": Problem("book", "Lina's book", "page", "curling from a splash", "a dry cloth", "the windowsill", {"book"}),
}

KIND_ACTS = {
    "napkin": KindAct("napkin", "offer a napkin", "offered", "a clean napkin", "tucked it under the plate", "The sandwich stayed in place", 2, 3, {"lunch"}),
    "fresh_sheet": KindAct("fresh_sheet", "bring fresh paper", "brought", "a fresh sheet of paper", "slid it under the painty page", "The drawing had a clean place to rest", 2, 3, {"drawing"}),
    "careful_tug": KindAct("careful_tug", "help with the zipper", "gave", "the zipper a careful tug", "pulled slowly and steady", "The zipper went up all the way", 3, 3, {"raincoat"}),
    "dry_cloth": KindAct("dry_cloth", "dry the page", "used", "a dry cloth", "blotted the wet edge gently", "The page was safe again", 2, 3, {"book"}),
}


GALLANT = ["Mia", "Ella", "Noah", "Liam", "Nina", "Owen"]
GENDERS = {"Mia": "girl", "Ella": "girl", "Nina": "girl", "Noah": "boy", "Liam": "boy", "Owen": "boy"}


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a slice-of-life kindness story that includes the words "gallant" and "own".',
        f"Tell a gentle story where {f['helper'].id} helps {f['other'].id} with {f['problem'].item} in a normal everyday place.",
        f'Write a short story about kindness, where a child notices someone else\'s own {f["problem"].item} is in trouble and helps in a gallant way.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    helper, other, problem, act = f["helper"], f["other"], f["problem"], f["act"]
    qa = [
        ("Who is the story about?", f"It is about {helper.id} and {other.id}. They are just having an ordinary day when a small problem appears."),
        ("What was the problem?", f"{other.id}'s {problem.item} was {problem.trouble} {problem.location}. That was enough to make the day feel a little awkward."),
        ("What did {0} do?".format(helper.id), f"{helper.id} noticed, spoke kindly, and helped with {act.name}. {helper.id}'s gallant kindness made the problem go away."),
    ]
    if f.get("fixed"):
        qa.append(("How did it end?", f"It ended well. The trouble was gone, and {other.id} could keep using {problem.item} while {helper.id} felt proud and kind."))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = set(world.facts["problem"].tags) | set(world.facts["act"].tags)
    out: list[tuple[str, str]] = []
    if "lunch" in tags:
        out.append(("Why do people use a napkin at lunch?", "A napkin helps catch crumbs and spills, so the table and clothes stay cleaner."))
    if "drawing" in tags:
        out.append(("Why is fresh paper helpful for drawing?", "Fresh paper gives you a clean surface to draw on when a page gets messy."))
    if "raincoat" in tags:
        out.append(("What does a zipper do?", "A zipper closes clothing together, and if it gets stuck, someone can help it move carefully."))
    if "book" in tags:
        out.append(("Why keep a book dry?", "Books can get damaged by water, so it is kinder to dry them off quickly."))
    out.append(("What does gallant mean?", "Gallant means brave and kind in a polite, helpful way."))
    out.append(("What is kindness?", "Kindness is when you notice someone needs help and you choose to help gently."))
    return out


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
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
reasonable(S, P, A) :- setting(S), problem(P), act(A), affords(S, P), power(A, Pow), Pow >= 1.
fixed(P) :- chosen_problem(P), chosen_act(A), power(A, Pow), trouble(P, T), Pow >= 1, T > 0.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for pid in sorted(s.affords):
            lines.append(asp.fact("affords", sid, pid))
    for pid, p in PROBLEMS.items():
        lines.append(asp.fact("problem", pid))
        for t in sorted(p.tags):
            lines.append(asp.fact("problem_tag", pid, t))
    for aid, a in KIND_ACTS.items():
        lines.append(asp.fact("act", aid))
        lines.append(asp.fact("power", aid, a.power))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show reasonable/3."))
    return sorted(set(asp.atoms(model, "reasonable")))


def asp_verify() -> int:
    python_set = set(valid_combos())
    clingo_set = set(asp_valid_combos())
    if python_set == clingo_set:
        print(f"OK: gate matches valid_combos() ({len(python_set)} combos).")
        return 0
    print("MISMATCH in gate:")
    print(" only python:", sorted(python_set - clingo_set))
    print(" only clingo:", sorted(clingo_set - python_set))
    return 1


@dataclass
class StoryParams:
    setting: str
    problem: str
    act: str
    helper: str
    helper_gender: str
    other: str
    other_gender: str
    adult_gender: str
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

CURATED = [
    dataclass(type("P", (), {}))
]



def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Slice-of-life kindness storyworld.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--act", choices=KIND_ACTS)
    ap.add_argument("--helper")
    ap.add_argument("--other")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [
        c for c in valid_combos()
        if (args.setting is None or c[0] == args.setting)
        and (args.problem is None or c[1] == args.problem)
        and (args.act is None or c[2] == args.act)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, problem, act = rng.choice(sorted(combos))
    helper = args.helper or rng.choice(GALLANT)
    other_pool = [n for n in GALLANT if n != helper]
    other = args.other or rng.choice(other_pool)
    return StoryParams(setting, problem, act, helper, GENDERS[helper], other, GENDERS[other], "mother")


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], PROBLEMS[params.problem], KIND_ACTS[params.act],
                 params.helper, params.helper_gender, params.other, params.other_gender, "mother")
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
        print(asp_program("", "#show reasonable/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos:")
        for t in asp_valid_combos():
            print(" ", t)
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        curated = [
            StoryParams("kitchen", "lunch", "napkin", "Mia", "girl", "Noah", "boy", "mother"),
            StoryParams("classroom", "drawing", "fresh_sheet", "Ella", "girl", "Liam", "boy", "mother"),
            StoryParams("porch", "raincoat", "careful_tug", "Noah", "boy", "Mia", "girl", "mother"),
            StoryParams("library", "book", "dry_cloth", "Nina", "girl", "Owen", "boy", "mother"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            seed = base_seed + i
            i += 1
            params = resolve_params(args, random.Random(seed))
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
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
