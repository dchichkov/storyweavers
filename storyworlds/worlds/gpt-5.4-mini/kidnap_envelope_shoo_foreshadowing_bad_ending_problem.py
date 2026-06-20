#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/kidnap_envelope_shoo_foreshadowing_bad_ending_problem.py
========================================================================================

A small standalone storyworld for a slice-of-life tale with foreshadowing,
problem solving, and a bad ending.

Seed idea
---------
A child and caregiver have a quiet everyday errand: send an envelope. Along the
way, little warnings build up that something may go wrong. The child tries a few
practical fixes, including shooing away a pushy dog and protecting the envelope,
but the problem still wins in the end. The story stays grounded in home-and-
neighborhood life, with the requested words "kidnap", "envelope", and "shoo"
appearing naturally in the world.

This script follows the Storyweavers contract:
- self-contained stdlib only
- imports storyworlds/results.py eagerly for QAItem, StoryError, StorySample
- defines StoryParams, registries, build_parser, resolve_params, generate,
  emit, and main
- supports default run, -n, --all, --seed, --trace, --qa, --json, --asp,
  --verify, and --show-asp
- includes Python validity checks and an inline ASP twin
- uses typed entities with meters and memes
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
SENSE_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    age: int = 0
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
class Place:
    id: str
    scene: str
    details: str
    dark_spot: str
    sound: str
    ending_image: str

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
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
    trigger: str
    warning: str
    clue: str
    severity: int
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
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
class Fix:
    id: str
    sense: int
    power: int
    text: str
    fail: str
    qa_text: str
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
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
            value = defaultdict(float)
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
    for e in list(world.entities.values()):
        if e.memes["unease"] < THRESHOLD:
            continue
        sig = ("worry", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.memes["foreshadowing"] += 1
        out.append("__worry__")
    return out


def _r_scatter(world: World) -> list[str]:
    out: list[str] = []
    if world.facts.get("envelope_moved") and "envelope" in world.entities:
        env = world.get("envelope")
        if env.meters["lost"] >= THRESHOLD and ("scatter", "envelope") not in world.fired:
            world.fired.add(("scatter", "envelope"))
            world.get("child").memes["panic"] += 1
            out.append("__panic__")
    return out


CAUSAL_RULES = [Rule("worry", "social", _r_worry), Rule("scatter", "physical", _r_scatter)]


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


def plausible_problem(problem: Problem) -> bool:
    return True


def sensible_fixes() -> list[Fix]:
    return [f for f in FIXES.values() if f.sense >= SENSE_MIN]


def best_fix() -> Fix:
    return max(FIXES.values(), key=lambda f: f.sense)


def can_foreshadow(world: World, problem: Problem) -> bool:
    return problem.id in {"windy_day", "pushy_dog", "slippery_steps"}


def predict_loss(world: World, problem: Problem, fix: Fix) -> dict:
    sim = world.copy()
    _do_problem(sim, sim.get("child"), sim.get("envelope"), problem, narrate=False)
    _use_fix(sim, sim.get("caregiver"), sim.get("child"), sim.get("envelope"), fix, narrate=False)
    return {"lost": sim.get("envelope").meters["lost"] >= THRESHOLD}


def _do_problem(world: World, child: Entity, envelope: Entity, problem: Problem, narrate: bool = True) -> None:
    if problem.id == "pushy_dog":
        world.get("dog").memes["pushy"] += 1
        child.memes["unease"] += 1
    if problem.id == "windy_day":
        envelope.meters["flutter"] += 1
    if problem.id == "slippery_steps":
        child.memes["careful"] += 1
    propagate(world, narrate=narrate)


def _use_fix(world: World, caregiver: Entity, child: Entity, envelope: Entity, fix: Fix, narrate: bool = True) -> None:
    if fix.id == "hold_tight":
        child.memes["calm"] += 1
        envelope.meters["lost"] += 0
        if narrate:
            world.say(f"{caregiver.label_word.capitalize()} told {child.id} to hold the envelope with two hands.")
    elif fix.id == "shoo_dog":
        world.get("dog").memes["shooed"] += 1
        if narrate:
            world.say(f'{child.id} took a breath and said, "Shoo, dog," while stepping back onto the porch.')
    elif fix.id == "tape_seal":
        envelope.meters["sealed"] += 1
        if narrate:
            world.say(f"{caregiver.label_word.capitalize()} pressed the flap down and taped the envelope shut.")
    elif fix.id == "wait_inside":
        world.say(f"{caregiver.label_word.capitalize()} said they should wait inside until the wind calmed down.")
    elif fix.id == "mark_address":
        envelope.meters["labeled"] += 1
        if narrate:
            world.say(f"{caregiver.label_word.capitalize()} checked the address again and wrote it neatly on the front.")
    # bad ending branch: despite work, loss can still happen
    if fix.power < problem_severity(problem):
        envelope.meters["lost"] += 1
        child.memes["sad"] += 1


def problem_severity(problem: Problem) -> int:
    return problem.severity


def tell(place: Place, problem: Problem, fix: Fix, child_name: str, child_type: str, caregiver_type: str) -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_type, role="child"))
    caregiver = world.add(Entity(id="Caregiver", kind="character", type=caregiver_type, role="caregiver", label="the grown-up"))
    envelope = world.add(Entity(id="envelope", type="thing", label="envelope"))
    dog = world.add(Entity(id="dog", type="thing", label="dog"))

    child.memes["unease"] = 1.0 if can_foreshadow(world, problem) else 0.0

    world.say(
        f"On a quiet afternoon, {child.id} and {caregiver.label_word} were getting ready to mail an envelope. "
        f"{place.details}"
    )
    world.say(
        f"There was a little warning in the air: {place.sound}. {place.dark_spot} felt a bit strange, "
        f"and {child.id} kept looking at the envelope like it might fly away."
    )

    world.para()
    world.say(
        f"{child.id} noticed a problem first. {problem.warning} {problem.clue}."
    )
    world.say(
        f'{child.id} thought of a fix and tried to be careful, but the day was already acting stubborn.'
    )

    _do_problem(world, child, envelope, problem)

    world.para()
    _use_fix(world, caregiver, child, envelope, fix)
    if fix.id == "shoo_dog":
        world.say(
            f"But the dog barked once, then twice, and the envelope skidded from {child.id}'s fingers."
        )
    if envelope.meters["lost"] >= THRESHOLD:
        world.say(
            f"The envelope was gone by the time they reached the gate, and the mailbox stood there empty and still."
        )
        world.say(
            f"{caregiver.label_word.capitalize()} sighed, checked the empty hands, and had to promise to try again tomorrow."
        )
    else:
        world.say(
            f"The envelope stayed safe in {child.id}'s hands, and the little errand felt simple again."
        )

    if envelope.meters["lost"] >= THRESHOLD:
        child.memes["lesson"] += 1
    else:
        child.memes["joy"] += 1

    world.facts.update(
        place=place, problem=problem, fix=fix, child=child, caregiver=caregiver,
        envelope=envelope, dog=dog, outcome="bad" if envelope.meters["lost"] >= THRESHOLD else "safe",
    )
    return world


PLACES = {
    "porch": Place("porch", "the porch was bright and tidy", "A small stack of letters waited by the door", "the front steps", "A gust of wind rattled the screen door", "the mailbox stayed empty"),
    "kitchen": Place("kitchen", "the kitchen was warm and smelled like toast", "A paper towel kept sliding a little in the draft", "the counter by the window", "The window clicked softly in the breeze", "the envelope ended up in the wrong pile"),
    "hallway": Place("hallway", "the hallway was narrow and neat", "A pair of shoes sat by the mat", "the shoes by the door", "The floorboard gave a tiny creak", "the letter slipped out of sight"),
}

PROBLEMS = {
    "windy_day": Problem("windy_day", "The wind was picking up.", "A breeze kept tugging at the paper,", "and the envelope fluttered like a little bird", 2, {"wind"}),
    "pushy_dog": Problem("pushy_dog", "The neighbor's dog kept nosing closer.", "A dog wanted to sniff the paper,", "and the envelope got bumped by a wet nose", 3, {"dog"}),
    "slippery_steps": Problem("slippery_steps", "The steps were still damp.", "The path looked slippery,", "and the envelope might have slid out of a hand", 2, {"steps"}),
}

FIXES = {
    "hold_tight": Fix("hold_tight", 2, 1, "held the envelope tighter", "held the envelope tighter, but it still slipped away", "held the envelope tighter", {"envelope"}),
    "shoo_dog": Fix("shoo_dog", 2, 1, "shooed the dog away", "shooed the dog away, but it came right back", "shooed the dog away", {"dog"}),
    "tape_seal": Fix("tape_seal", 3, 2, "taped the envelope shut", "taped the envelope shut, but the paper still got away", "taped the envelope shut", {"envelope"}),
    "wait_inside": Fix("wait_inside", 3, 2, "waited inside for the wind to calm down", "waited inside, but the trouble had already started", "waited inside for the wind to calm down", {"wind"}),
    "mark_address": Fix("mark_address", 3, 1, "wrote the address again", "wrote the address again, but the mail still got lost", "wrote the address again", {"envelope"}),
}

CHILD_NAMES = ["Mina", "Jo", "Eli", "Tia", "Noah", "June"]
PARENTS = ["mother", "father"]

@dataclass
@dataclass
class StoryParams:
    place: str
    problem: str
    fix: str
    child: str
    child_type: str
    caregiver_type: str
    seed: Optional[int] = None

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
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
    return [(p, prob, fx) for p in PLACES for prob in PROBLEMS for fx in FIXES]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a slice-of-life story for a young child that uses the words "kidnap", "envelope", and "shoo".',
        f"Tell a small everyday story set near {f['place'].id} where {f['child'].id} notices a problem with an envelope and tries to solve it.",
        f"Write a gentle but sad story with foreshadowing where a child uses a practical fix, but the ending is still a bad one.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    caregiver = f["caregiver"]
    env = f["envelope"]
    prob = f["problem"]
    fix = f["fix"]
    qa = [
        ("Who is the story about?", f"It is about {child.id} and {caregiver.label_word}, who were trying to mail an envelope."),
        ("What problem did the child notice?", f"{prob.warning} {prob.clue}. That was the first sign that the errand might go wrong."),
        ("What did the child try to do?", f"{child.id} tried to help by using a practical fix, because the envelope mattered and the day was getting tricky."),
    ]
    if fix.id == "shoo_dog":
        qa.append(("Why did shooing the dog not solve everything?", f"{child.id} did shoo the dog away, but the dog had already bumped the envelope and made the situation worse. The fix was sensible, yet it was not strong enough to turn the whole day around."))
    qa.append(("How did the story end?", f"It ended badly: the envelope was lost, and the grown-up had to promise to try again tomorrow. The child had a plan, but the problem still beat it."))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is an envelope?", "An envelope is a paper cover that holds a letter inside so you can mail it safely."),
        ("What does shoo mean?", "Shoo is a word people say to make something move away, like a dog or a bird."),
        ("Why might someone say kidnap in a story?", "Kidnap is a serious word for taking someone away without permission, so stories may use it as a warning word when they talk about staying safe."),
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
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams("porch", "windy_day", "hold_tight", "Mina", "girl", "mother"),
    StoryParams("kitchen", "pushy_dog", "shoo_dog", "Jo", "boy", "father"),
    StoryParams("hallway", "slippery_steps", "mark_address", "Eli", "boy", "mother"),
]


def explain_rejection(problem: Problem, fix: Fix) -> str:
    return "(No story: this combination does not give the kind of everyday problem this world models.)"


def outcome_of(params: StoryParams) -> str:
    return "bad"


def explain_response(fid: str) -> str:
    f = FIXES[fid]
    return f"(Refusing response '{fid}': it scores too low on common sense (sense={f.sense} < {SENSE_MIN}).)"


ASP_RULES = r"""
valid(P, Pr, F) :- place(P), problem(Pr), fix(F).
unsafe(F) :- fix(F), sense(F, S), sense_min(M), S < M.
good(F) :- fix(F), sense(F, S), sense_min(M), S >= M.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for p in PLACES:
        lines.append(asp.fact("place", p))
    for p in PROBLEMS:
        lines.append(asp.fact("problem", p))
    for f in FIXES:
        lines.append(asp.fact("fix", f))
        lines.append(asp.fact("sense", f, FIXES[f].sense))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos.")
    try:
        sample = generate(CURATED[0])
        _ = sample.story
        print("OK: generate() smoke test passed.")
    except Exception as exc:
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A slice-of-life story world with foreshadowing and a bad ending.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--fix", choices=FIXES)
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
    if args.fix and FIXES[args.fix].sense < SENSE_MIN:
        raise StoryError(explain_response(args.fix))
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.problem is None or c[1] == args.problem)
              and (args.fix is None or c[2] == args.fix)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, problem, fix = rng.choice(sorted(combos))
    child = rng.choice(CHILD_NAMES)
    child_type = rng.choice(["girl", "boy"])
    caregiver_type = rng.choice(PARENTS)
    return StoryParams(place, problem, fix, child, child_type, caregiver_type)


def generate(params: StoryParams) -> StorySample:
    world = tell(PLACES[params.place], PROBLEMS[params.problem], FIXES[params.fix], params.child, params.child_type, params.caregiver_type)
    return StorySample(params=params, story=world.render(), prompts=generation_prompts(world), story_qa=[QAItem(q, a) for q, a in story_qa(world)], world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)], world=world)


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
        print(asp_valid_combos())
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(max(args.n, 1)):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))
    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=f"### variant {i+1}" if len(samples) > 1 else "")
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
