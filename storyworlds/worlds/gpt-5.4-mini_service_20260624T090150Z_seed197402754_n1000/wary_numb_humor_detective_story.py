#!/usr/bin/env python3
"""
A small detective-style story world about a wary investigator, a numb clue,
and a humorous case that can be solved with the right evidence.
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


# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------

@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.meters.setdefault("lost", 0.0)
        self.meters.setdefault("found", 0.0)
        self.meters.setdefault("numb", 0.0)
        self.meters.setdefault("order", 0.0)
        self.memes.setdefault("wary", 0.0)
        self.memes.setdefault("humor", 0.0)
        self.memes.setdefault("relief", 0.0)
        self.memes.setdefault("curiosity", 0.0)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother"}
        male = {"boy", "man", "father"}
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
    indoors: bool = True
    atmosphere: str = "quiet"
    can_hide: bool = True


@dataclass
class Clue:
    id: str
    label: str
    phrase: str
    kind: str
    location: str
    weirdness: str
    helps: str


@dataclass
class Case:
    title: str
    suspect: str
    motive: str
    clue: str
    fix: str


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.fired: set[tuple] = set()

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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

    def copy(self) -> "World":
        import copy as _copy

        w = World(self.place)
        w.entities = _copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        w.fired = set(self.fired)
        return w


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

PLACES = {
    "office": Place(name="the office", indoors=True, atmosphere="bright", can_hide=True),
    "library": Place(name="the library", indoors=True, atmosphere="hushed", can_hide=True),
    "station": Place(name="the station", indoors=True, atmosphere="bustling", can_hide=False),
}

DETECTIVES = {
    "casey": ("Casey", "girl"),
    "milo": ("Milo", "boy"),
    "jun": ("Jun", "character"),
}

CLUES = {
    "cold_coin": Clue(
        id="cold_coin",
        label="cold coin",
        phrase="a cold coin with a tiny scratch",
        kind="coin",
        location="desk",
        weirdness="oddly numb",
        helps="points to a hurried pocket",
    ),
    "comic_note": Clue(
        id="comic_note",
        label="comic note",
        phrase="a folded note with a silly doodle",
        kind="note",
        location="lamp",
        weirdness="funny",
        helps="shows who tried to hide the joke",
    ),
    "glove": Clue(
        id="glove",
        label="glove",
        phrase="one lonely glove",
        kind="glove",
        location="chair",
        weirdness="worn inside out",
        helps="reveals a dropped trail",
    ),
}

CASES = {
    "missing_key": Case(
        title="The Missing Key",
        suspect="the janitor",
        motive="wanted the spare key for the locked cabinet",
        clue="cold_coin",
        fix="unlock the cabinet and find the key tag",
    ),
    "lost_laugh": Case(
        title="The Lost Laugh",
        suspect="the prankster",
        motive="hid a joke note for attention",
        clue="comic_note",
        fix="follow the doodle to the hiding place",
    ),
    "vanished_glove": Case(
        title="The Vanished Glove",
        suspect="the courier",
        motive="dropped the glove while rushing by",
        clue="glove",
        fix="check the path and return the glove",
    ),
}

NAMES_BY_TYPE = {
    "girl": ["Casey", "Mina", "Ivy", "Nora"],
    "boy": ["Milo", "Theo", "Finn", "Owen"],
    "character": ["Jun", "Ari", "Sam", "Rue"],
}


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% A case is reasonable when its clue is present in the selected place and the
% clue has the right kind of oddity to attract a detective's attention.
reason(Place, Case, Clue) :- place(Place), case(Case), clue(Clue),
                            in_place(Clue, Place), helps_case(Clue, Case).

% A full story is valid when a detective can be wary, notice a numb clue,
% and still solve the case with a humorous turn.
valid_story(Place, Case, Clue) :- reason(Place, Case, Clue),
                                  has_trait(detective, wary),
                                  clue_trait(Clue, numb),
                                  clue_trait(Clue, humor).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp

    lines: list[str] = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for cid in CASES:
        lines.append(asp.fact("case", cid))
    for clid, clue in CLUES.items():
        lines.append(asp.fact("clue", clid))
        lines.append(asp.fact("in_place", clid, clue.location))
        lines.append(asp.fact("helps_case", clid, clue.id if clid in CASES else clid))
        if "numb" in clue.weirdness:
            lines.append(asp.fact("clue_trait", clid, "numb"))
        if "funny" in clue.weirdness:
            lines.append(asp.fact("clue_trait", clid, "humor"))
    lines.append(asp.fact("has_trait", "detective", "wary"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import storyworlds.asp as asp

    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_stories())
    if py == cl:
        print(f"OK: clingo gate matches Python gate ({len(py)} stories).")
        return 0
    print("MISMATCH between clingo and Python gate:")
    if py - cl:
        print("  only in Python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# Core logic
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    place: str
    case: str
    detective: str
    gender: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, p in PLACES.items():
        for case_id, case in CASES.items():
            clue = CLUES[case.clue]
            if clue.location and p.can_hide:
                combos.append((place, case_id, case.clue))
    return combos


def build_world(params: StoryParams) -> World:
    place = PLACES[params.place]
    case = CASES[params.case]
    clue = CLUES[case.clue]

    world = World(place)
    detective_name, detective_type = DETECTIVES[params.detective]
    detective = world.add(Entity(
        id=detective_name,
        kind="character",
        type=detective_type,
        label="the detective",
        meters={"lost": 0.0, "found": 0.0, "numb": 0.0, "order": 0.0},
        memes={"wary": 1.0, "humor": 1.0, "relief": 0.0, "curiosity": 1.0},
    ))
    clue_ent = world.add(Entity(
        id=clue.id,
        kind="thing",
        type=clue.kind,
        label=clue.label,
        phrase=clue.phrase,
        owner=case.suspect,
        meters={"lost": 1.0, "found": 0.0, "numb": 1.0, "order": 0.0},
        memes={"wary": 0.0, "humor": 1.0},
    ))
    world.facts.update(
        detective=detective,
        clue=clue_ent,
        case=case,
        place=place,
        suspect=case.suspect,
    )
    return world


def _search(world: World, detective: Entity, clue: Entity) -> None:
    detective.memes["wary"] += 0.5
    detective.memes["curiosity"] += 0.5
    world.say(
        f"{detective.id} walked into {world.place.name} with a wary eye and a calm hat."
    )
    world.say(
        f"The room was {world.place.atmosphere}, but the case felt stranger than it looked."
    )
    world.para()
    world.say(
        f"On the desk sat {clue.phrase}. It looked numb, almost as if it had stopped"
        f" caring about being lost."
    )
    clue.meters["found"] += 1.0
    detective.meters["found"] += 1.0


def _deduce(world: World, detective: Entity, case: Case, clue: Entity) -> None:
    world.say(
        f"{detective.id} studied the clue and gave a small laugh. "
        f"Even a serious mystery can have a funny face when a coin turns cold or a note wears a doodle."
    )
    detective.memes["humor"] += 0.5
    detective.meters["numb"] += clue.meters["numb"]
    world.say(
        f"The clue pointed at {case.suspect}, who {case.motive}. "
        f"That was the kind of odd trail {detective.id} liked: neat, simple, and a little silly."
    )


def _resolve(world: World, detective: Entity, case: Case, clue: Entity) -> None:
    detective.meters["order"] += 1.0
    detective.memes["relief"] += 1.0
    world.para()
    world.say(
        f"{detective.id} followed the clue and chose to {case.fix}."
    )
    world.say(
        f"In the end, the missing piece was found, the suspect was understood, and "
        f"the whole room felt less jittery and more bright."
    )
    world.say(
        f"{detective.id} smiled, still wary enough to notice details, but no longer numb to the joke in the case."
    )


def tell(params: StoryParams) -> World:
    world = build_world(params)
    detective = world.get(world.facts["detective"].id)
    clue = world.get(world.facts["clue"].id)
    case: Case = world.facts["case"]  # type: ignore[assignment]

    _search(world, detective, clue)
    _deduce(world, detective, case, clue)
    _resolve(world, detective, case, clue)
    return world


def generation_prompts(world: World) -> list[str]:
    case: Case = world.facts["case"]  # type: ignore[assignment]
    clue: Entity = world.facts["clue"]  # type: ignore[assignment]
    detective: Entity = world.facts["detective"]  # type: ignore[assignment]
    return [
        f"Write a short detective story for children about {detective.id} and a {clue.label} that feels numb and funny.",
        f"Tell a humorous mystery where a wary detective solves {case.title} by following {clue.phrase}.",
        f"Write a small detective tale in which a clue looks numb at first, but the case still gets solved.",
    ]


def story_qa(world: World) -> list[QAItem]:
    case: Case = world.facts["case"]  # type: ignore[assignment]
    clue: Entity = world.facts["clue"]  # type: ignore[assignment]
    detective: Entity = world.facts["detective"]  # type: ignore[assignment]
    return [
        QAItem(
            question=f"Who was the detective in the story?",
            answer=f"The detective was {detective.id}, and {detective.id} was wary, curious, and ready to notice details.",
        ),
        QAItem(
            question=f"What clue helped solve {case.title}?",
            answer=f"{clue.phrase} helped solve the case because it looked numb and odd, but it pointed to the answer.",
        ),
        QAItem(
            question="How did the story end?",
            answer=f"It ended with the case solved, the clue understood, and {detective.id} smiling at the funny little mystery.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does wary mean?",
            answer="Wary means careful and watchful, like someone who is paying close attention because they do not want to miss a clue.",
        ),
        QAItem(
            question="What does numb mean?",
            answer="Numb means you cannot feel something very well, or it seems strangely dull or quiet.",
        ),
        QAItem(
            question="Why can a mystery be funny?",
            answer="A mystery can be funny when the clues are surprising or silly, but the detective still treats the case seriously.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== Story QA ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World QA ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in world.entities.values():
        lines.append(
            f"{e.id}: kind={e.kind} type={e.type} meters={dict(e.meters)} memes={dict(e.memes)}"
        )
    return "\n".join(lines)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_combos()
    if args.place:
        combos = [c for c in combos if c[0] == args.place]
    if args.case:
        combos = [c for c in combos if c[1] == args.case]
    if not combos:
        raise StoryError("No valid detective story matches the given options.")

    place, case, _ = rng.choice(sorted(combos))
    detective = args.detective or rng.choice(sorted(DETECTIVES))
    gender = args.gender or "character"
    return StoryParams(place=place, case=case, detective=detective, gender=gender)


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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small humorous detective story world.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--case", choices=CASES)
    ap.add_argument("--detective", choices=DETECTIVES)
    ap.add_argument("--gender", choices=["girl", "boy", "character"])
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def asp_program_text(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program_text("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import storyworlds.asp as asp

        model = asp.one_model(asp_program_text("#show valid_story/3."))
        print(sorted(set(asp.atoms(model, "valid_story"))))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams(place="office", case="missing_key", detective="casey", gender="girl"),
            StoryParams(place="library", case="lost_laugh", detective="milo", gender="boy"),
            StoryParams(place="station", case="vanished_glove", detective="jun", gender="character"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 25):
            try:
                params = resolve_params(args, random.Random(base_seed + i))
            except StoryError as err:
                print(err)
                return
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story in seen:
                i += 1
                continue
            seen.add(sample.story)
            samples.append(sample)
            i += 1

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for idx, sample in enumerate(samples):
        if len(samples) > 1:
            print(f"### variant {idx + 1}")
        emit(sample, trace=args.trace, qa=args.qa)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
