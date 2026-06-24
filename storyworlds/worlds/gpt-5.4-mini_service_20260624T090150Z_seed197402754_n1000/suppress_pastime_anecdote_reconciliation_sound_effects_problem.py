#!/usr/bin/env python3
"""
A small folk-tale storyworld about a hush-hush pastime, a troublesome sound,
and a reconciliation that solves the problem.

Seed image:
- A child loves an evening pastime.
- The pastime makes a lively sound that disturbs someone nearby.
- A problem grows from the noise.
- The characters reconcile by finding a clever, gentle solution.

This world keeps the prose state-driven: the story changes based on entities,
their meters, and their memes.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "queen", "sister"}
        male = {"boy", "father", "man", "king", "brother"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    name: str
    kind: str
    silence_needed: bool
    sound_carries: bool = True
    season: str = ""


@dataclass
class Pastime:
    id: str
    verb: str
    gerund: str
    tool: str
    sound: str
    gentle_fix: str
    noise_meter: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Problem:
    id: str
    symptom: str
    consequence: str
    resolved_by: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


@dataclass
class StoryParams:
    place: str
    pastime: str
    problem: str
    name: str
    gender: str
    elder: str
    trait: str
    seed: Optional[int] = None


PLACES = {
    "village_green": Place(name="the village green", kind="outdoor", silence_needed=False, sound_carries=True, season="spring"),
    "cottage_yard": Place(name="the cottage yard", kind="outdoor", silence_needed=False, sound_carries=True, season="summer"),
    "hearth_room": Place(name="the hearth room", kind="indoor", silence_needed=True, sound_carries=False, season="winter"),
    "market_lane": Place(name="the market lane", kind="outdoor", silence_needed=True, sound_carries=True, season="autumn"),
}

PASTIMES = {
    "drumming": Pastime(
        id="drumming",
        verb="beat the little drum",
        gerund="beating the little drum",
        tool="little drum",
        sound="rat-a-tat",
        gentle_fix="wrap the drum with a soft cloth and tap more lightly",
        noise_meter="loudness",
        tags={"sound_effects", "pastime", "suppress"},
    ),
    "whistling": Pastime(
        id="whistling",
        verb="whistle a tune",
        gerund="whistling a tune",
        tool="reed whistle",
        sound="fwee-fwee",
        gentle_fix="step to a quiet place and whistle softly",
        noise_meter="loudness",
        tags={"sound_effects", "pastime", "suppress"},
    ),
    "clapping_game": Pastime(
        id="clapping_game",
        verb="play the clapping game",
        gerund="playing the clapping game",
        tool="pair of hands",
        sound="clap-clap",
        gentle_fix="slow the rhythm and clap with smaller pats",
        noise_meter="loudness",
        tags={"sound_effects", "pastime"},
    ),
    "bean_counting": Pastime(
        id="bean_counting",
        verb="sort beans in a bowl",
        gerund="sorting beans in a bowl",
        tool="wooden bowl",
        sound="click-click",
        gentle_fix="move the bowl closer and count in whispers",
        noise_meter="rattle",
        tags={"problem_solving", "pastime"},
    ),
    "storytelling": Pastime(
        id="storytelling",
        verb="tell an anecdote",
        gerund="telling an anecdote",
        tool="lamp-lit bench",
        sound="murmur-murmur",
        gentle_fix="lean close and speak in turn",
        noise_meter="murmur",
        tags={"anecdote", "reconciliation"},
    ),
}

PROBLEMS = {
    "sleeping_baby": Problem(
        id="sleeping_baby",
        symptom="the baby in the next room could not sleep",
        consequence="the house grew fussy and tired",
        resolved_by="soften the sound",
        tags={"reconciliation", "problem_solving"},
    ),
    "skittish_goose": Problem(
        id="skittish_goose",
        symptom="the old goose flapped and honked",
        consequence="the yard turned into a noisy scramble",
        resolved_by="calm the goose",
        tags={"sound_effects", "problem_solving"},
    ),
    "cross_grandmother": Problem(
        id="cross_grandmother",
        symptom="grandmother frowned at the clatter",
        consequence="the mood went sour and small",
        resolved_by="make peace",
        tags={"reconciliation"},
    ),
}

GIRL_NAMES = ["Mara", "Tess", "Nina", "Elsa", "Lina", "Anya"]
BOY_NAMES = ["Owen", "Pip", "Evan", "Milo", "Rory", "Jasper"]
TRAITS = ["bright", "gentle", "curious", "cheerful", "stubborn", "wise"]
ELDERS = ["grandmother", "grandfather", "aunt", "uncle", "old neighbor"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for pid, place in PLACES.items():
        for past_id in PASTIMES:
            for prob_id in PROBLEMS:
                if place.silence_needed or PASTIMES[past_id].noise_meter in {"loudness", "rattle"}:
                    combos.append((pid, past_id, prob_id))
    return combos


def explain_rejection(place: Place, pastime: Pastime) -> str:
    return (
        f"(No story: {pastime.gerund} does not fit well at {place.name}. "
        f"Choose a place and pastime that can plausibly stir a problem.)"
    )


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Folk-tale storyworld about pastime, sound effects, and reconciliation.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--pastime", choices=PASTIMES)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--elder", choices=ELDERS)
    ap.add_argument("--trait", choices=TRAITS)
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
    combos = [
        c for c in valid_combos()
        if (args.place is None or c[0] == args.place)
        and (args.pastime is None or c[1] == args.pastime)
        and (args.problem is None or c[2] == args.problem)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, pastime, problem = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    elder = args.elder or rng.choice(ELDERS)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, pastime=pastime, problem=problem, name=name, gender=gender, elder=elder, trait=trait)


def _gain(ent: Entity, key: str, amt: float = 1.0) -> None:
    ent.meters[key] = ent.meters.get(key, 0.0) + amt


def tell(place: Place, pastime: Pastime, problem: Problem, name: str, gender: str, elder: str, trait: str) -> World:
    world = World(place)
    child = world.add(Entity(id=name, kind="character", type=gender, label=name, meters={}, memes={}))
    old = world.add(Entity(id="Elder", kind="character", type="woman" if elder in {"grandmother", "aunt"} else "man", label=elder, meters={}, memes={}))

    tool = world.add(Entity(id="Tool", type="thing", label=pastime.tool, phrase=pastime.tool))
    tool.owner = child.id

    world.say(f"Once, in {place.name}, there lived a {trait} child named {child.id}.")
    world.say(f"{child.id} loved {pastime.gerund}, and the little {pastime.tool} went {pastime.sound} with every try.")
    world.say(f"The sound had a folk-tale way of wandering far in the air.")

    world.para()
    world.say(f"One day, {child.id} went near {place.name} to play {pastime.id}.")
    _gain(child, pastime.noise_meter, 1.0)
    _gain(child, "delight", 1.0)
    _gain(old, "unease", 1.0)
    world.say(f"{child.id} tried to {pastime.verb}, and the air answered {pastime.sound}.")
    world.say(f"That made {problem.symptom}.")

    if place.sound_carries:
        _gain(old, "frustration", 1.0)
    if place.silence_needed:
        _gain(old, "frustration", 1.0)
    _gain(child, "shame", 1.0)

    world.para()
    world.say(f"{old.id if old.id != 'Elder' else elder.capitalize()} called the child close and spoke kindly.")
    world.say(f'"This is a small {problem.id}," {elder} said, "but it can grow if we do not solve it."')
    world.say(f"{child.id} lowered {child.pronoun('possessive')} head, then listened.")

    world.para()
    _gain(child, "resolve", 1.0)
    _gain(old, "compassion", 1.0)
    world.say(f"Together they chose to {pastime.gentle_fix}.")
    world.say(f"Then the {pastime.sound} grew soft, and {problem.consequence} faded away.")
    world.say(f"{child.id} and {elder} made peace, and the pastime became gentle again.")
    world.say(f"At the end, the little {pastime.tool} still existed, but it no longer bothered the house or yard.")

    world.facts.update(child=child, elder=old, pastime=pastime, problem=problem, place=place)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    pastime = f["pastime"]
    problem = f["problem"]
    place = f["place"]
    return [
        f'Write a short folk tale about a child named {child.id} and the word "{pastime.id}".',
        f"Tell a gentle story where {child.id} loves {pastime.gerund} at {place.name}, but the sound causes a problem.",
        f'Write a simple reconciliation story that includes "{problem.symptom}" and ends with a quiet solution.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    elder = f["elder"]
    pastime = f["pastime"]
    problem = f["problem"]
    place = f["place"]
    return [
        QAItem(
            question=f"What did {child.id} love to do in {place.name}?",
            answer=f"{child.id} loved {pastime.gerund}. The pastime made a lively little sound in the air.",
        ),
        QAItem(
            question=f"What problem grew when {child.id} tried to play {pastime.id}?",
            answer=f"{problem.symptom.capitalize()}. The noise made the trouble worse until the elder stepped in.",
        ),
        QAItem(
            question=f"How did {child.id} and {elder.id} solve the problem?",
            answer=f"They chose to {pastime.gentle_fix}. That softened the sound and helped them reconcile.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    pastime = f["pastime"]
    return [
        QAItem(
            question="What is an anecdote?",
            answer="An anecdote is a short true or story-like tale told to share a memory or a small lesson.",
        ),
        QAItem(
            question="What does reconciliation mean?",
            answer="Reconciliation means making peace again after a disagreement or a worry.",
        ),
        QAItem(
            question="Why do sound effects matter in a story?",
            answer="Sound effects help readers hear the action in their minds, like a drum going rat-a-tat or a whistle going fwee-fwee.",
        ),
        QAItem(
            question="What is problem solving?",
            answer="Problem solving means noticing what is wrong and choosing a careful way to fix it.",
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
    out = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        out.append(f"  {e.id}: {e.type} {' '.join(bits)}")
    return "\n".join(out)


ASP_RULES = r"""
place(P) :- setting(P).
pastime(T) :- tool(T).
problem(X) :- issue(X).

valid_story(P, T, X) :- setting(P), pastime(T), problem(X).
"""

def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for pid in PLACES:
        lines.append(asp.fact("setting", pid))
    for tid in PASTIMES:
        lines.append(asp.fact("pastime", tid))
    for xid in PROBLEMS:
        lines.append(asp.fact("issue", xid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    clingo_set = set(asp.atoms(model, "valid_story"))
    py_set = set(valid_combos())
    if clingo_set == py_set:
        print(f"OK: clingo gate matches valid_combos() ({len(py_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print("  only in clingo:", sorted(clingo_set - py_set))
    print("  only in python:", sorted(py_set - clingo_set))
    return 1


def select_name(gender: str, rng: random.Random) -> str:
    return rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        PLACES[params.place],
        PASTIMES[params.pastime],
        PROBLEMS[params.problem],
        params.name,
        params.gender,
        params.elder,
        params.trait,
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


CURATED = [
    StoryParams(place="village_green", pastime="drumming", problem="sleeping_baby", name="Mara", gender="girl", elder="grandmother", trait="bright"),
    StoryParams(place="cottage_yard", pastime="whistling", problem="skittish_goose", name="Owen", gender="boy", elder="grandfather", trait="curious"),
    StoryParams(place="hearth_room", pastime="storytelling", problem="cross_grandmother", name="Nina", gender="girl", elder="grandmother", trait="gentle"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import storyworlds.asp as asp
        model = asp.one_model(asp_program("#show valid_story/3."))
        print(sorted(set(asp.atoms(model, "valid_story"))))
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
            rng = random.Random(seed)
            try:
                params = resolve_params(args, rng)
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
        header = f"### variant {i + 1}" if len(samples) > 1 and not args.all else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
