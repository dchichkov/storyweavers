#!/usr/bin/env python3
"""
storyworlds/worlds/cuban_suspense_problem_solving_humor_bedtime_story.py
========================================================================

A small bedtime-story world with Cuban flavor, gentle suspense, problem solving,
and a touch of humor.

Premise:
A child is ready for bed in a cozy Cuban home, but a beloved bedtime item goes
missing. The family follows clues around the house, fixes a small snag, and ends
the night with warmth, laughter, and sleep.

The world is intentionally compact: a few settings, a few bedtime problems, and
a few believable resolutions. The prose is generated from world state rather
than from a frozen template.
"""

from __future__ import annotations

import argparse
import copy
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
    worn_by: Optional[str] = None
    plural: bool = False
    protective: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "grandmother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "grandfather", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    name: str
    indoors: bool = True
    cozy: bool = True
    affords: set[str] = field(default_factory=set)


@dataclass
class Problem:
    id: str
    verb: str
    search_verb: str
    clue: str
    risk: str
    resolution: str
    setting_hint: str
    tags: set[str] = field(default_factory=set)


@dataclass
class BedtimePrize:
    label: str
    phrase: str
    region: str
    plural: bool = False
    genders: set[str] = field(default_factory=lambda: {"girl", "boy"})


@dataclass
class HelpItem:
    id: str
    label: str
    phrase: str
    helps: set[str]
    covers: set[str]
    risk_free: bool = True


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.lines: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.trace: list[str] = []

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.lines[-1].append(text)

    def para(self) -> None:
        if self.lines[-1]:
            self.lines.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.lines if p)

    def copy(self) -> "World":
        clone = World(self.place)
        clone.entities = copy.deepcopy(self.entities)
        clone.lines = [[]]
        clone.facts = copy.deepcopy(self.facts)
        clone.fired = set(self.fired)
        return clone


@dataclass
class StoryParams:
    place: str
    problem: str
    prize: str
    name: str
    gender: str
    helper: str
    seed: Optional[int] = None


PLACES = {
    "cozy_apartment": Place(
        name="a cozy apartment",
        indoors=True,
        cozy=True,
        affords={"find", "fix", "listen"},
    ),
    "cuban_patio": Place(
        name="a small Cuban patio",
        indoors=False,
        cozy=True,
        affords={"find", "fix", "listen"},
    ),
    "sleepy_kitchen": Place(
        name="the sleepy kitchen",
        indoors=True,
        cozy=True,
        affords={"find", "fix", "listen"},
    ),
}

PROBLEMS = {
    "missing_blanket": Problem(
        id="missing_blanket",
        verb="look for the missing blanket",
        search_verb="search under the chairs",
        clue="a soft corner peeking from behind the sofa",
        risk="the bed felt too cool and too empty",
        resolution="the blanket was found under a stack of folded towels",
        setting_hint="The room was quiet, except for a tiny tick-tick from the fan.",
        tags={"search", "blanket", "cozy"},
    ),
    "stuck_music_box": Problem(
        id="stuck_music_box",
        verb="fix the music box",
        search_verb="open the little lid carefully",
        clue="a ribbon jammed under the winding key",
        risk="the bedtime song had gone silent",
        resolution="the ribbon came free, and the tune chimed again",
        setting_hint="A Cuban lullaby waited on the air, patient and soft.",
        tags={"music", "song", "cozy"},
    ),
    "sleepy_fan": Problem(
        id="sleepy_fan",
        verb="quiet the squeaky fan",
        search_verb="peek at the fan blades",
        clue="a paper star stuck to one corner",
        risk="the squeak kept hopping through the room like a tiny mouse",
        resolution="the paper star was removed, and the fan purred softly",
        setting_hint="The night felt warm, and everyone wanted a calmer breeze.",
        tags={"sound", "fan", "humor"},
    ),
}

PRIZES = {
    "blanket": BedtimePrize(
        label="blanket",
        phrase="a blue blanket with little clouds",
        region="torso",
    ),
    "music_box": BedtimePrize(
        label="music box",
        phrase="a small music box that played a Cuban lullaby",
        region="hands",
    ),
    "pillow": BedtimePrize(
        label="pillow",
        phrase="a pillow with a moon on it",
        region="head",
    ),
}

HELPERS = {
    "abuela": HelpItem(
        id="abuela",
        label="Abuela",
        phrase="a patient abuela with clever hands",
        helps={"find", "fix", "listen"},
        covers={"torso", "hands", "head"},
    ),
    "mother": HelpItem(
        id="mother",
        label="Mamá",
        phrase="a gentle mamá with a warm smile",
        helps={"find", "fix", "listen"},
        covers={"torso", "hands", "head"},
    ),
    "father": HelpItem(
        id="father",
        label="Papá",
        phrase="a careful papá who liked to solve little puzzles",
        helps={"find", "fix", "listen"},
        covers={"torso", "hands", "head"},
    ),
}

GIRL_NAMES = ["Luna", "Mila", "Sofia", "Ana", "Elena", "Celia", "Nina"]
BOY_NAMES = ["Mateo", "Leo", "Rafa", "Tomas", "Enzo", "Nico", "Pablo"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for place in PLACES:
        for problem in PROBLEMS:
            for prize in PRIZES:
                if problem == "stuck_music_box" and prize == "blanket":
                    continue
                combos.append((place, problem, prize))
    return combos


def _prize_valid(problem: Problem, prize: BedtimePrize) -> bool:
    if problem.id == "stuck_music_box" and prize.label == "blanket":
        return False
    return True


def _select_helper(problem: Problem) -> HelpItem:
    if problem.id == "sleepy_fan":
        return HELPERS["father"]
    if problem.id == "missing_blanket":
        return HELPERS["mother"]
    return HELPERS["abuela"]


def tell(place: Place, problem: Problem, prize: BedtimePrize, hero_name: str, hero_gender: str) -> World:
    world = World(place)
    child = world.add(Entity(id=hero_name, kind="character", type=hero_gender, label=hero_name))
    helper_def = _select_helper(problem)
    helper = world.add(Entity(id=helper_def.id, kind="character", type="grandmother" if helper_def.id == "abuela" else "mother" if helper_def.id == "mother" else "father", label=helper_def.label))
    prize_ent = world.add(Entity(
        id="prize",
        kind="thing",
        type=prize.label,
        label=prize.label,
        phrase=prize.phrase,
        owner=child.id,
        caretaker=helper.id,
        region=prize.region,
        plural=prize.plural,
    ))
    fan = world.add(Entity(id="fan", kind="thing", type="fan", label="fan"))
    ribbon = world.add(Entity(id="ribbon", kind="thing", type="ribbon", label="ribbon"))
    star = world.add(Entity(id="star", kind="thing", type="star", label="paper star"))
    child.memes["sleepy"] = 1
    child.memes["worry"] = 0

    world.say(f"{hero_name} was a little {hero_gender} in {place.name}, ready for bed but not quite ready to sleep.")
    world.say(f"{problem.setting_hint}")
    world.say(f"{hero_name} loved {prize.phrase}, because bedtime felt safer when {prize.it()} was near.")
    world.para()

    child.memes["worry"] += 1
    world.say(f"But tonight, {problem.verb} was the only thing {hero_name} could think about.")
    world.say(f"{problem.risk.capitalize()}.")
    world.say(f"So {hero_name} and {helper.label} began to {problem.search_verb}.")
    world.say(f"First they looked near the bed, then under a pillow, then behind a chair.")
    world.para()

    if problem.id == "missing_blanket":
        child.memes["worry"] += 1
        world.say(f"At last, they found {problem.clue}.")
        world.say(f"Under the folded towels, the blanket was tucked in so tightly that it looked like it was hiding on purpose.")
        world.say(f"{helper.label} laughed and said, 'Even blankets need a little bedtime game sometimes.'")
        world.say(f"They pulled it free, and {problem.resolution}.")
    elif problem.id == "stuck_music_box":
        child.memes["worry"] += 1
        world.say(f"At last, they found {problem.clue}.")
        world.say(f"{helper.label} opened the lid with a tiny twist, and the ribbon popped out like a surprised snake.")
        world.say(f"{hero_name} giggled, because the music box had been fussy in the silliest possible way.")
        world.say(f"Then {problem.resolution}.")
    else:
        child.memes["worry"] += 1
        world.say(f"At last, they found {problem.clue}.")
        world.say(f"Papá lifted the fan guard very gently, and the paper star fluttered out like a sleepy snowflake.")
        world.say(f"{hero_name} snorted a laugh. 'The fan was wearing a sticker crown,' {hero_name} said.")
        world.say(f"Then {problem.resolution}.")
    world.para()

    child.memes["worry"] = 0
    child.memes["joy"] = 1
    helper.memes["relief"] = 1
    world.say(f"With the problem solved, {hero_name} tucked back in under the blanket and listened.")
    if problem.id == "stuck_music_box":
        world.say(f"The Cuban lullaby drifted softly across the room, and the music box sounded like it was smiling.")
    elif problem.id == "sleepy_fan":
        world.say(f"The fan hummed like a sleepy kitten, and everyone smiled at the silly little breeze.")
    else:
        world.say(f"The room felt warm again, and even the moon outside seemed to settle down for sleep.")
    world.say(f"{helper.label} kissed {hero_name}'s forehead, and the night became quiet and kind.")

    world.facts.update(
        child=child,
        helper=helper,
        prize=prize_ent,
        problem=problem,
        place=place,
        helper_def=helper_def,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    problem = f["problem"]
    prize = f["prize"]
    return [
        f'Write a short bedtime story for a child named {child.id} that includes the word "cuban" and a gentle surprise.',
        f"Tell a cozy story where {child.id} and {helper.label} solve a small problem involving {prize.phrase}.",
        f"Write a bedtime story with suspense, problem solving, and humor about {problem.verb} in a Cuban home.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    prize = f["prize"]
    problem = f["problem"]
    place = f["place"]
    return [
        QAItem(
            question=f"Who helped {child.id} when the bedtime problem started in {place.name}?",
            answer=f"{helper.label} helped {child.id}. {helper.label} stayed calm and looked for clues until the problem was solved.",
        ),
        QAItem(
            question=f"What was missing or broken when {child.id} was getting ready for bed?",
            answer=f"The trouble was about {prize.phrase}. The story was about {problem.verb}, which made bedtime feel uncertain for a little while.",
        ),
        QAItem(
            question=f"Why did {child.id} feel worried before the problem was solved?",
            answer=f"{child.id} felt worried because {problem.risk}. That made bedtime feel suspenseful until the family found a fix.",
        ),
        QAItem(
            question=f"What changed at the end of the story?",
            answer=f"By the end, the problem was solved, {child.id} felt cozy again, and the room was quiet enough for sleep.",
        ),
    ]


KNOWLEDGE = {
    "cuban": [
        (
            "What does Cuban mean?",
            "Cuban usually means something from Cuba, an island country in the Caribbean. People can use it for food, music, families, and places connected to Cuba.",
        ),
    ],
    "bedtime": [
        (
            "Why do people have bedtime routines?",
            "Bedtime routines help the body and mind slow down, so it gets easier to rest and fall asleep.",
        ),
    ],
    "music": [
        (
            "Why can gentle music help at bedtime?",
            "Gentle music can feel calming, which helps make a room feel safe, soft, and ready for sleep.",
        ),
    ],
    "fan": [
        (
            "Why might a fan make noise?",
            "A fan can make noise when something small touches the blades or guard, or when the moving air makes the parts vibrate.",
        ),
    ],
    "blanket": [
        (
            "What does a blanket do?",
            "A blanket helps keep a person warm and cozy when they are resting or sleeping.",
        ),
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["problem"].tags)
    tags.add("bedtime")
    if world.facts["problem"].id == "stuck_music_box":
        tags.add("music")
        tags.add("cuban")
    if world.facts["problem"].id == "sleepy_fan":
        tags.add("fan")
    if world.facts["problem"].id == "missing_blanket":
        tags.add("blanket")
    out: list[QAItem] = []
    for tag in ["cuban", "bedtime", "music", "fan", "blanket"]:
        if tag in tags:
            out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE[tag])
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
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.region:
            bits.append(f"region={e.region}")
        lines.append(f"  {e.id:10} ({e.type:10}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="cozy_apartment", problem="missing_blanket", prize="blanket", name="Luna", gender="girl"),
    StoryParams(place="sleepy_kitchen", problem="stuck_music_box", prize="music_box", name="Mateo", gender="boy"),
    StoryParams(place="cuban_patio", problem="sleepy_fan", prize="pillow", name="Ana", gender="girl"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A Cuban-flavored bedtime story world with suspense, humor, and gentle problem solving.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
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


def explain_rejection(problem: Problem, prize: BedtimePrize) -> str:
    return f"(No story: {problem.verb} does not fit with {prize.label} in this tiny bedtime world.)"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.problem and args.prize:
        if not _prize_valid(PROBLEMS[args.problem], PRIZES[args.prize]):
            raise StoryError(explain_rejection(PROBLEMS[args.problem], PRIZES[args.prize]))
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.problem is None or c[1] == args.problem)
              and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, problem, prize = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    return StoryParams(place=place, problem=problem, prize=prize, name=name, gender=gender)


def generate(params: StoryParams) -> StorySample:
    world = tell(PLACES[params.place], PROBLEMS[params.problem], PRIZES[params.prize], params.name, params.gender)
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
place(P) :- setting(P).
problem(X) :- problem_kind(X).
prize(Y) :- prize_kind(Y).

valid(P, X, Y) :- setting(P), problem_kind(X), prize_kind(Y), not invalid(P, X, Y).
invalid(P, X, Y) :- problem_kind(X), prize_kind(Y), X = stuck_music_box, Y = blanket.

#show valid/3.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid in PLACES:
        lines.append(asp.fact("setting", pid))
    for pid in PROBLEMS:
        lines.append(asp.fact("problem_kind", pid))
    for pid in PRIZES:
        lines.append(asp.fact("prize_kind", pid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        triples = asp_valid_combos()
        print(f"{len(triples)} compatible combos:")
        for p, x, y in triples:
            print(f"  {p:15} {x:18} {y}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
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
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.problem} at {p.place} (prize: {p.prize})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
