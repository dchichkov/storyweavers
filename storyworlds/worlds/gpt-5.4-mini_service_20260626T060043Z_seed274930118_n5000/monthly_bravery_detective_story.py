#!/usr/bin/env python3
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


@dataclass
class Place:
    id: str
    name: str
    detail: str
    vibe: str
    clues: list[str] = field(default_factory=list)


@dataclass
class Character:
    id: str
    name: str
    role: str
    brave: float = 0.0
    worry: float = 0.0
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self) -> str:
        return "they"

    def poss(self) -> str:
        return "their"


@dataclass
class Case:
    id: str
    monthly: bool
    mystery: str
    clue_type: str
    culprit_type: str
    resolution: str
    opening_line: str
    turn_line: str
    ending_image: str
    tags: list[str] = field(default_factory=list)


@dataclass
class StoryParams:
    month: str
    place: str
    detective: str
    partner: str
    case: str
    seed: Optional[int] = None


@dataclass
class World:
    month: str
    place: Place
    detective: Character
    partner: Character
    case: Case
    clue_found: bool = False
    suspect_spotted: bool = False
    solved: bool = False
    evidence: list[str] = field(default_factory=list)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        import copy
        return copy.deepcopy(self)


MONTHS = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
]

PLACES = {
    "dock": Place("dock", "the dock", "Salt wind curled around the ropes and boxes.", "quiet", ["rope fiber", "wet footprints", "crate splinters"]),
    "market": Place("market", "the night market", "Lanterns blinked above stacked stalls.", "busy", ["coin dust", "paper scraps", "orange peel"]),
    "library": Place("library", "the library", "Tall shelves made the room feel like a whisper.", "careful", ["bookmark", "pencil shaving", "dust"]),
    "station": Place("station", "the train station", "Echoes bounced off the tile floor.", "hushed", ["ticket stub", "mud print", "metal button"]),
}

CASES = {
    "missing_lantern": Case(
        id="missing_lantern",
        monthly=True,
        mystery="a lantern vanished from a stall",
        clue_type="wax drips",
        culprit_type="street cat",
        resolution="the lantern was found tucked under a bench, nudged there by a curious cat",
        opening_line="Someone at the market had lost a lantern, and the whole row of stalls looked dimmer because of it.",
        turn_line="The detective noticed wax drips on the counter and tiny paw marks near the cloth curtain.",
        ending_image="The lantern glowed again while the cat blinked beside a basket of pears.",
        tags=["market", "lantern", "cat", "monthly", "bravery"],
    ),
    "lost_ticket": Case(
        id="lost_ticket",
        monthly=True,
        mystery="a train ticket disappeared before the last ride",
        clue_type="ticket corner",
        culprit_type="wind",
        resolution="the ticket had blown into a pocket of folded newspapers",
        opening_line="At the station, one last ticket had gone missing, and the clock was already getting sleepy.",
        turn_line="A torn corner of paper stuck out from under a newspaper pile near the bench.",
        ending_image="The ticket was safe at last, and the train whistle sounded like a soft thank-you.",
        tags=["station", "ticket", "wind", "monthly", "bravery"],
    ),
    "library_note": Case(
        id="library_note",
        monthly=True,
        mystery="a secret note was tucked inside the wrong book",
        clue_type="pencil marks",
        culprit_type="helpful child",
        resolution="the note belonged to a child who had hidden it there to keep it safe",
        opening_line="In the library, a note had slipped into the wrong book and started a small, serious mystery.",
        turn_line="The detective found pencil marks under the title page, written in a shaky hand that tried very hard to be brave.",
        ending_image="The book was returned, and the note went home in a careful little envelope.",
        tags=["library", "book", "note", "monthly", "bravery"],
    ),
}


DETECTIVES = [
    ("Mina", "detective"),
    ("Toby", "detective"),
    ("Iris", "detective"),
    ("Jun", "detective"),
]

PARTNERS = [
    ("Pip", "assistant"),
    ("Nell", "assistant"),
    ("Sage", "assistant"),
    ("Rae", "assistant"),
]

MONTHLY_TITLES = {
    "January": "the first cold case of the year",
    "February": "a short month with a long mystery",
    "March": "a windy case with quick steps",
    "April": "a rainy clue trail",
    "May": "a bright case with a brave heart",
    "June": "a warm mystery under a clear sky",
    "July": "a sweaty search that still needed courage",
    "August": "a late-summer puzzle",
    "September": "the kind of case that began with a school-day rumor",
    "October": "a shadowy case with extra courage needed",
    "November": "a quiet case with heavy clouds overhead",
    "December": "a twinkling mystery with a brave ending",
}

BRAVERY_PROMPTS = [
    "Keep going even when the hall feels dark.",
    "Tell the truth about what you noticed.",
    "Ask the next hard question.",
    "Walk closer to the clue instead of backing away.",
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Story world: a monthly detective tale about bravery.")
    ap.add_argument("--month", choices=MONTHS)
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--case", choices=CASES)
    ap.add_argument("--detective")
    ap.add_argument("--partner")
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
    month = args.month or rng.choice(MONTHS)
    place = args.place or rng.choice(list(PLACES))
    case = args.case or rng.choice(list(CASES))
    detective = args.detective or rng.choice([n for n, _ in DETECTIVES])
    partner = args.partner or rng.choice([n for n, _ in PARTNERS])
    if detective == partner:
        partner = rng.choice([n for n, _ in PARTNERS if n != detective])

    if case not in CASES:
        raise StoryError("Unknown case.")
    if place not in PLACES:
        raise StoryError("Unknown place.")
    return StoryParams(month=month, place=place, detective=detective, partner=partner, case=case)


def aspire_case_valid(place: str, case: Case) -> bool:
    return place in case.tags


def valid_combos() -> list[tuple[str, str]]:
    out = []
    for place in PLACES:
        for case_id, case in CASES.items():
            if aspire_case_valid(place, case):
                out.append((place, case_id))
    return out


ASP_RULES = r"""
valid(P,C) :- place(P), case(C), tags(C,P).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for cid, case in CASES.items():
        lines.append(asp.fact("case", cid))
        for tag in case.tags:
            lines.append(asp.fact("tags", cid, tag))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP matches Python ({len(py)} combos).")
        return 0
    print("MISMATCH")
    print("python-only:", sorted(py - cl))
    print("asp-only:", sorted(cl - py))
    return 1


def _make_world(params: StoryParams) -> World:
    place = PLACES[params.place]
    case = CASES[params.case]
    detective = Character(params.detective, params.detective, "detective", brave=1.0, worry=0.2)
    partner = Character(params.partner, params.partner, "partner", brave=0.8, worry=0.1)
    w = World(month=params.month, place=place, detective=detective, partner=partner, case=case)
    w.facts.update(params=params, month=params.month, place=place, case=case, detective=detective, partner=partner)
    return w


def _investigate(world: World) -> None:
    d = world.detective
    p = world.partner
    case = world.case
    place = world.place

    d.meters["steps"] = d.meters.get("steps", 0.0) + 1
    d.memes["bravery"] = d.memes.get("bravery", 0.0) + 1.0
    d.memes["worry"] = d.memes.get("worry", 0.0) + 0.3

    world.say(f"It was {world.month.lower()}, and {MONTHLY_TITLES[world.month]}.")
    world.say(f"At {place.name}, {case.opening_line}")
    world.say(f"{d.name} and {p.name} looked carefully at the scene, because good detectives do not rush the first clue.")

    world.para()
    world.say(f"{case.turn_line}")
    world.say(f"{d.name} felt a small shiver, but {d.name} took {d.poss()} own {BRAVERY_PROMPTS[hash(world.month) % len(BRAVERY_PROMPTS)].lower()}")
    world.say(f"That brave choice helped {d.name} notice {case.clue_type} near the edge of the room.")

    world.clue_found = True
    world.evidence.append(case.clue_type)
    d.memes["bravery"] += 1.0
    p.memes["admiration"] = p.memes.get("admiration", 0.0) + 1.0

    world.para()
    world.say(f"At last, {d.name} followed the clue to the answer.")
    world.say(f"That was how {case.resolution}.")
    world.say(f"{case.ending_image}")
    world.solved = True
    world.facts["solved"] = True


def generate_story(world: World) -> str:
    _investigate(world)
    return world.render()


def generation_prompts(world: World) -> list[str]:
    case = world.case
    return [
        f"Write a short monthly detective story about {case.mystery} that shows bravery.",
        f"Tell a child-friendly mystery set at {world.place.name} in {world.month} where a detective follows {case.clue_type}.",
        f"Create a gentle detective tale in which courage helps solve {case.id}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    case = world.case
    return [
        QAItem(
            question=f"What month was the detective story set in?",
            answer=f"It was set in {world.month}, which made the case feel like {MONTHLY_TITLES[world.month]}.",
        ),
        QAItem(
            question=f"What clue helped {world.detective.name} solve the mystery?",
            answer=f"{world.detective.name} followed {case.clue_type} and used bravery to keep looking until the answer appeared.",
        ),
        QAItem(
            question=f"How did the mystery end?",
            answer=f"It ended when {case.resolution}, and the final image showed {case.ending_image.lower()}",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does bravery mean?",
            answer="Bravery means doing something even when you feel afraid, worried, or unsure.",
        ),
        QAItem(
            question="What does a detective do?",
            answer="A detective looks for clues, asks careful questions, and tries to solve a mystery.",
        ),
        QAItem(
            question="Why do monthly stories feel different?",
            answer="Monthly stories can change with the calendar, so each month brings a different mood, weather, or kind of case.",
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
    lines.append("== (3) World knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    lines.append(f"month={world.month}")
    lines.append(f"place={world.place.name}")
    lines.append(f"case={world.case.id}")
    lines.append(f"detective bravery={world.detective.memes.get('bravery', 0.0)}")
    lines.append(f"detective worry={world.detective.memes.get('worry', 0.0)}")
    lines.append(f"partner admiration={world.partner.memes.get('admiration', 0.0)}")
    lines.append(f"clue_found={world.clue_found}")
    lines.append(f"solved={world.solved}")
    lines.append(f"evidence={world.evidence}")
    return "\n".join(lines)


CURATED = [
    StoryParams(month="January", place="dock", detective="Mina", partner="Pip", case="missing_lantern"),
    StoryParams(month="April", place="station", detective="Iris", partner="Nell", case="lost_ticket"),
    StoryParams(month="October", place="library", detective="Jun", partner="Sage", case="library_note"),
]


def generate(params: StoryParams) -> StorySample:
    world = _make_world(params)
    story = generate_story(world)
    return StorySample(
        params=params,
        story=story,
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} valid place/case combos:\n")
        for place, case in combos:
            print(f"  {place:10} {case}")
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
            rng = random.Random(seed)
            try:
                params = resolve_params(args, rng)
            except StoryError as e:
                print(e)
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
            header = f"### {p.month}: {p.case} at {p.place} ({p.detective} with {p.partner})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
