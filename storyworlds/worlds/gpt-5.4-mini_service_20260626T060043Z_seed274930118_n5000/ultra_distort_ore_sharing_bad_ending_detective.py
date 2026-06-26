#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/ultra_distort_ore_sharing_bad_ending_detective.py
=============================================================================================================

A small detective-story world about a shared ore sample, an ultra-fussy clue, and
the ways a false story can distort what really happened.

Seed tale sketch:
---
Detective June came to a quiet mining town after a shiny ore sample went missing.
The foreman wanted to share the sample with the town, but someone had already
swapped the label and distorted the report. June followed the tiny clues: a
powdery boot print, a broken lantern, and a scrap of ribbon. In the end, the
truth came out, but the ending was still bad: the ore was ruined, the share
box was empty, and the town had to face the loss.

Simulation model:
---
- Typed entities have physical meters and emotional memes.
- The ore can be shared, hidden, cracked, and mislabeled.
- Distortion raises confusion and makes witness reports unreliable.
- If the truth is not protected in time, the ending resolves as a bad ending:
  the ore is lost to the town even after the detective learns what happened.

The world is deliberately small and constraint-checked, with a reasonableness
gate and an ASP twin for the same registry facts.
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
    held_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        male = {"man", "boy", "detective", "foreman", "miner"}
        female = {"woman", "girl", "detective"}
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    name: str
    indoors: bool = False
    can_share: bool = True
    can_hide: bool = True


@dataclass
class Clue:
    id: str
    label: str
    reveals: str
    kind: str


@dataclass
class Solution:
    id: str
    label: str
    required_clue: str
    ending: str


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.facts: dict = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.trace: list[str] = []

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)
            self.trace.append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        import copy

        w = World(self.place)
        w.entities = copy.deepcopy(self.entities)
        w.facts = dict(self.facts)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        return w


@dataclass
class StoryParams:
    place: str
    culprit: str
    clue: str
    solution: str
    seed: Optional[int] = None


PLACES = {
    "mine": Place(name="the old mine", indoors=False, can_share=True, can_hide=True),
    "office": Place(name="the detective office", indoors=True, can_share=False, can_hide=False),
    "station": Place(name="the train station", indoors=True, can_share=True, can_hide=True),
}

ENTITIES = {
    "detective": Entity(id="June", kind="character", type="detective", label="Detective June"),
    "foreman": Entity(id="Miller", kind="character", type="foreman", label="Foreman Miller"),
    "miner": Entity(id="Poe", kind="character", type="miner", label="Miner Poe"),
    "ultra_ore": Entity(
        id="ultra_ore",
        type="ore",
        label="ultra ore",
        phrase="a heavy chunk of ultra ore",
        owner="town",
        caretaker="Miller",
    ),
    "display_box": Entity(id="display_box", type="box", label="share box", phrase="the town's share box"),
    "ribbon": Entity(id="ribbon", type="clue", label="blue ribbon", phrase="a scrap of blue ribbon"),
    "boot_print": Entity(id="boot_print", type="clue", label="powdery boot print", phrase="a powdery boot print"),
    "smudged_report": Entity(id="report", type="paper", label="smudged report", phrase="a smudged report"),
}

CLUES = {
    "ribbon": Clue(id="ribbon", label="blue ribbon", reveals="the miner passed the lamp room", kind="trace"),
    "boot_print": Clue(id="boot_print", label="powdery boot print", reveals="someone walked through the ore dust", kind="trace"),
    "smudged_report": Clue(id="report", label="smudged report", reveals="someone tried to distort the written record", kind="paper"),
}

SOLUTIONS = {
    "share_late": Solution(id="share_late", label="late sharing", required_clue="boot_print", ending="bad ending"),
    "hide_it": Solution(id="hide_it", label="hide the ore", required_clue="smudged_report", ending="bad ending"),
    "tell_truth": Solution(id="tell_truth", label="tell the truth", required_clue="ribbon", ending="bad ending"),
}

NAMES = ["June", "Iris", "Noah", "Mina", "Theo", "Ava"]
TRAITS = ["careful", "ultra-serious", "patient", "sharp"]


def reasonableness_gate(place: Place, culprit: str, clue: str, solution: str) -> None:
    if clue not in CLUES:
        raise StoryError(f"Unknown clue: {clue}")
    if solution not in SOLUTIONS:
        raise StoryError(f"Unknown solution: {solution}")
    if culprit not in ENTITIES:
        raise StoryError(f"Unknown culprit choice: {culprit}")
    if not place.can_share and solution == "share_late":
        raise StoryError("This place cannot support the shared-ore setup.")
    if clue == "ribbon" and culprit != "miner":
        raise StoryError("The ribbon clue only makes sense with the miner at the mine.")
    if clue == "smudged_report" and place.indoors is False:
        raise StoryError("A smudged report belongs in an indoor paper trail.")
    if solution == "hide_it" and place.name != "the old mine":
        raise StoryError("Hiding the ore only works at the mine in this storyworld.")


def build_world(params: StoryParams) -> World:
    world = World(PLACES[params.place])
    detective = world.add(ENTITY["detective"])
    foreman = world.add(ENTITY["foreman"])
    miner = world.add(ENTITY[params.culprit])
    ore = world.add(ENTITY["ultra_ore"])
    box = world.add(ENTITY["display_box"])
    clue = world.add(ENTITY[params.clue])
    report = world.add(ENTITY["smudged_report"])
    world.facts.update(
        detective=detective, foreman=foreman, miner=miner, ore=ore, box=box,
        clue=clue, report=report, solution=SOLUTIONS[params.solution],
        place=world.place, culprit=params.culprit, clue_id=params.clue,
        solution_id=params.solution,
    )
    return world


def _distort_report(world: World) -> None:
    report = world.get("report")
    if ("distort", "report") in world.fired:
        return
    world.fired.add(("distort", "report"))
    report.meters["distorted"] = 1
    report.memes["confusion"] = 1
    world.say("The report had been distorted, and the facts looked slippery.")


def _share_ore(world: World) -> None:
    ore = world.get("ultra_ore")
    box = world.get("display_box")
    if ("share", ore.id) in world.fired:
        return
    world.fired.add(("share", ore.id))
    ore.held_by = box.id
    ore.meters["shared"] = 1
    world.say("The town lined up to share the ultra ore, but the box felt too light.")


def _discover_clue(world: World) -> None:
    clue = world.facts["clue"]
    detective = world.get("June")
    if ("discover", clue.id) in world.fired:
        return
    world.fired.add(("discover", clue.id))
    detective.memes["focus"] = detective.memes.get("focus", 0) + 1
    if clue.id == "boot_print":
        world.say("Detective June found a powdery boot print near the lamp room.")
    elif clue.id == "ribbon":
        world.say("A tiny blue ribbon hung on a nail, like someone had rushed past.")
    else:
        world.say("A smudged report sat on the desk, warning June that the story had been distorted.")


def _bad_ending(world: World) -> None:
    ore = world.get("ultra_ore")
    detective = world.get("June")
    if ("ending", "bad") in world.fired:
        return
    world.fired.add(("ending", "bad"))
    ore.meters["lost"] = 1
    ore.memes["worry"] = 1
    detective.memes["regret"] = detective.memes.get("regret", 0) + 1
    world.say("In the end, the ore was gone from the share box, and the town had to face a bad ending.")


def simulate(world: World) -> None:
    _share_ore(world)
    _distort_report(world)
    _discover_clue(world)
    _bad_ending(world)


def tell(params: StoryParams) -> World:
    world = build_world(params)
    detective = world.get("June")
    foreman = world.get("Miller")
    miner = world.get(params.culprit)
    ore = world.get("ultra_ore")
    clue = world.facts["clue"]
    solution = world.facts["solution"]

    world.say(f"Detective June arrived at {world.place.name} after the ultra ore vanished.")
    world.say(f"Foreman Miller wanted to share the ore with everyone, but something felt off.")
    world.say(f"Someone had tried to distort the records, and the clue was hiding in plain sight.")
    world.para()
    world.say(f"June watched {miner.label.lower()} and {foreman.label.lower()} from the shadow of the cart track.")
    world.say(f"The little clue was {clue.label}, and it pointed toward the truth.")
    simulate(world)
    world.para()
    if solution.id == "tell_truth":
        world.say("June told the truth out loud, but it arrived too late to save the ore.")
    elif solution.id == "share_late":
        world.say("The town tried to share the ore again, yet the box was already empty.")
    else:
        world.say("June looked for the hidden ore, but the mine had already swallowed the chance.")
    world.say("That was how the detective solved the case and still had to live with the bad ending.")
    world.facts["ending"] = "bad ending"
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        'Write a short detective story for a young child that includes ultra ore, sharing, and a bad ending.',
        f"Tell a mystery about {f['detective'].label} who follows a clue and learns how the ore was distorted.",
        "Write a gentle detective tale where a shared treasure is lost and the ending is sad, but clear.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    detective = f["detective"].label
    foreman = f["foreman"].label
    clue = f["clue"].label
    place = f["place"].name
    return [
        QAItem(
            question=f"Who was the detective in the story at {place}?",
            answer=f"The detective was {detective}. {detective} followed tiny clues and tried to understand what happened to the ultra ore.",
        ),
        QAItem(
            question="What clue helped June think about the missing ore?",
            answer=f"The clue was {clue}. It gave June a small, careful sign about who had been near the ore and how the story had been distorted.",
        ),
        QAItem(
            question="Why was the ending bad even after the case was solved?",
            answer=f"The ending was bad because the ultra ore was still lost from the share box. June learned the truth, but the town did not get its treasure back.",
        ),
        QAItem(
            question=f"What did {foreman} want to do with the ore?",
            answer=f"{foreman} wanted to share the ultra ore with the town, but the distortion and the loss made that plan fail.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a clue in a detective story?",
            answer="A clue is a small piece of evidence that can help a detective understand what happened.",
        ),
        QAItem(
            question="What does it mean to distort something?",
            answer="To distort something means to twist it so it does not show the truth clearly anymore.",
        ),
        QAItem(
            question="What is ore?",
            answer="Ore is rock or stone that has valuable metal or minerals inside it.",
        ),
        QAItem(
            question="What does sharing mean?",
            answer="Sharing means letting other people use or enjoy something together instead of keeping it all for yourself.",
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
    for e in world.entities.values():
        bits = []
        if any(v for v in e.meters.values()):
            bits.append(f"meters={e.meters}")
        if any(v for v in e.memes.values()):
            bits.append(f"memes={e.memes}")
        if e.held_by:
            bits.append(f"held_by={e.held_by}")
        lines.append(f"  {e.id:12} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="mine", culprit="miner", clue="ribbon", solution="tell_truth"),
    StoryParams(place="mine", culprit="miner", clue="boot_print", solution="share_late"),
    StoryParams(place="office", culprit="foreman", clue="smudged_report", solution="tell_truth"),
]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place_id, place in PLACES.items():
        for culprit in ("miner", "foreman"):
            for clue_id in CLUES:
                for sol_id in SOLUTIONS:
                    try:
                        reasonableness_gate(place, culprit, clue_id, sol_id)
                    except StoryError:
                        continue
                    combos.append((place_id, culprit, clue_id))
    return combos


def explain_rejection(place: Place, culprit: str, clue: str, solution: str) -> str:
    return (
        f"(No story: the combination place={place.name}, culprit={culprit}, "
        f"clue={clue}, solution={solution} does not make a coherent detective case.)"
    )


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Detective-story world: ultra ore, distort, sharing, bad ending.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--culprit", choices=["miner", "foreman"])
    ap.add_argument("--clue", choices=list(CLUES))
    ap.add_argument("--solution", choices=list(SOLUTIONS))
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
    place = args.place or rng.choice(list(PLACES))
    culprit = args.culprit or rng.choice(["miner", "foreman"])
    clue = args.clue or rng.choice(list(CLUES))
    solution = args.solution or rng.choice(list(SOLUTIONS))
    reasonableness_gate(PLACES[place], culprit, clue, solution)
    return StoryParams(place=place, culprit=culprit, clue=clue, solution=solution)


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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


ASP_RULES = r"""
place(mine). place(office). place(station).
culprit(miner). culprit(foreman).
clue(ribbon). clue(boot_print). clue(smudged_report).
solution(tell_truth). solution(share_late). solution(hide_it).

valid(P,C,Cl) :- place(P), culprit(C), clue(Cl).
shared_case(P,C,Cl) :- valid(P,C,Cl), P = mine.
bad_ending(P,C,Cl) :- valid(P,C,Cl), shared_case(P,C,Cl).
#show valid/3.
#show bad_ending/3.
"""


def asp_facts() -> str:
    import asp
    return "\n".join([
        asp.fact("place", "mine"),
        asp.fact("place", "office"),
        asp.fact("place", "station"),
        asp.fact("culprit", "miner"),
        asp.fact("culprit", "foreman"),
        asp.fact("clue", "ribbon"),
        asp.fact("clue", "boot_print"),
        asp.fact("clue", "smudged_report"),
        asp.fact("solution", "tell_truth"),
        asp.fact("solution", "share_late"),
        asp.fact("solution", "hide_it"),
    ])


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    atoms = set(asp.atoms(model, "valid"))
    py = set(valid_combos())
    if atoms == py:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and python gates.")
    print("clingo-only:", sorted(atoms - py))
    print("python-only:", sorted(py - atoms))
    return 1


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_valid_bad_endings() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show bad_ending/3."))
    return sorted(set(asp.atoms(model, "bad_ending")))


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3.\n#show bad_ending/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        valid = asp_valid_combos()
        bad = asp_valid_bad_endings()
        print(f"{len(valid)} compatible cases, {len(bad)} bad-ending cases:\n")
        for p, c, cl in valid:
            mark = "BAD" if (p, c, cl) in bad else ""
            print(f"  {p:8} {c:9} {cl:14} {mark}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        i = 0
        seen: set[str] = set()
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
        header = f"### variant {i + 1}" if len(samples) > 1 and not args.all else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
