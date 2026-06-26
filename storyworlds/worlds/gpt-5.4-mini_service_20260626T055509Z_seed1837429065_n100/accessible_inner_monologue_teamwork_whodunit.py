#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T055509Z_seed1837429065_n100/accessible_inner_monologue_teamwork_whodunit.py
==============================================================================================================

A small, standalone storyworld in the "accessible inner monologue teamwork whodunit" style.

Premise:
- A child detective visits an accessible place with a helper.
- Something important goes missing.
- The detective uses quiet inner monologue, teamwork, and concrete clues to solve the mystery.
- The culprit is not evil; the story ends with a calm, helpful reveal.

This world is intentionally small and constraint-checked:
- physical meters: distance moved, clue strength, readiness, mess, etc.
- emotional memes: worry, curiosity, trust, relief, pride, teamwork
- a reasonableness gate prevents weak or impossible mystery setups
- inline ASP rules mirror the Python gate for parity checks

The generated stories are child-facing, concrete, and mystery-shaped:
beginning -> clues -> inference -> reveal -> resolution image.
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


# ---------------------------------------------------------------------------
# Core world entities
# ---------------------------------------------------------------------------

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    location: str = ""
    movable: bool = True
    accessible: bool = True
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for k in ["distance", "clue", "worry", "trust", "relief", "pride", "teamwork", "mess", "hidden"]:
            self.meters.setdefault(k, 0.0)
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Location:
    id: str
    label: str
    accessible: bool
    clues: set[str] = field(default_factory=set)
    allows: set[str] = field(default_factory=set)


@dataclass
class Mystery:
    id: str
    missing_label: str
    missing_phrase: str
    clue_kind: str
    clue_phrase: str
    culprit_kind: str
    culprit_label: str
    culprit_phrase: str
    hiding_place: str
    reveal_reason: str
    inner_thought: str


@dataclass
class Companion:
    id: str
    name: str
    type: str
    trait: str


class World:
    def __init__(self, location: Location) -> None:
        self.location = location
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.mentioned_clues: list[str] = []

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

    def copy(self) -> "World":
        c = World(self.location)
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = copy.deepcopy(self.facts)
        c.mentioned_clues = list(self.mentioned_clues)
        return c


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

LOCATIONS = {
    "library": Location(
        id="library",
        label="the community library",
        accessible=True,
        clues={"ramp", "books", "dust", "wheels"},
        allows={"book", "marker", "bell"},
    ),
    "museum": Location(
        id="museum",
        label="the small museum",
        accessible=True,
        clues={"ramp", "rope", "dust", "shoeprints"},
        allows={"badge", "key", "mask"},
    ),
    "cafe": Location(
        id="cafe",
        label="the corner cafe",
        accessible=True,
        clues={"tray", "crumbs", "smell", "footprints"},
        allows={"spoon", "napkin", "jar"},
    ),
}

MYSTERIES = {
    "book": Mystery(
        id="book",
        missing_label="book",
        missing_phrase="the blue storybook",
        clue_kind="dust",
        clue_phrase="a dusty line on the low shelf",
        culprit_kind="helper",
        culprit_label="the librarian",
        culprit_phrase="the librarian",
        hiding_place="the accessible reading cart",
        reveal_reason="It had been moved there to keep the path clear.",
        inner_thought="If the shelf is dusty but the cart has the book, then someone moved it on purpose, not by mistake.",
    ),
    "marker": Mystery(
        id="marker",
        missing_label="marker",
        missing_phrase="the red marker",
        clue_kind="wheels",
        clue_phrase="small wheel marks on the floor",
        culprit_kind="helper",
        culprit_label="the teacher",
        culprit_phrase="the teacher",
        hiding_place="the art table drawer",
        reveal_reason="It was borrowed for a class sign and put back in a safe place.",
        inner_thought="Wheel marks plus a tidy table mean the marker did not vanish; it traveled with help.",
    ),
    "bell": Mystery(
        id="bell",
        missing_label="bell",
        missing_phrase="the silver bell",
        clue_kind="ramp",
        clue_phrase="a tiny glitter line near the ramp",
        culprit_kind="animal",
        culprit_label="the puppy",
        culprit_phrase="the puppy",
        hiding_place="under the soft mat by the ramp",
        reveal_reason="It rolled there after a playful bump and got tucked away by paws.",
        inner_thought="A glitter trail near the ramp means the bell rolled low, where small paws could reach it.",
    ),
}


@dataclass
class StoryParams:
    location: str
    mystery: str
    detective_name: str
    detective_type: str
    detective_trait: str
    companion_name: str
    companion_type: str
    companion_trait: str
    seed: Optional[int] = None


NAMES = {
    "girl": ["Mina", "Lila", "Nora", "Ivy", "Zara", "Pia"],
    "boy": ["Theo", "Max", "Ravi", "Noah", "Eli", "Owen"],
    "helper": ["June", "Sam", "Ari", "Lee", "Tess", "Jo"],
}

TRAITS = ["curious", "careful", "bright", "patient", "kind", "brave"]


# ---------------------------------------------------------------------------
# World model / story engine
# ---------------------------------------------------------------------------

def _bump(ent: Entity, key: str, amount: float = 1.0) -> None:
    ent.meters[key] = ent.meters.get(key, 0.0) + amount
    ent.memes[key] = ent.memes.get(key, 0.0) + amount


def _say_inner(world: World, detective: Entity, text: str) -> None:
    world.say(f"{detective.pronoun().capitalize()} thought, “{text}”")


def _clue_visible(world: World, mystery: Mystery) -> bool:
    return mystery.clue_kind in world.location.clues


def _predict_reveal(world: World, detective: Entity, companion: Entity, mystery: Mystery) -> bool:
    sim = world.copy()
    _search(sim, sim.get(detective.id), sim.get(companion.id), mystery, narrate=False)
    return bool(sim.facts.get("solved"))


def _search(world: World, detective: Entity, companion: Entity, mystery: Mystery, narrate: bool = True) -> None:
    if ("search", mystery.id) in world.fired:
        return
    world.fired.add(("search", mystery.id))
    _bump(detective, "curiosity")
    _bump(companion, "trust")
    _bump(companion, "teamwork")
    _bump(detective, "teamwork")
    _bump(detective, "clue", 1.0)
    if narrate:
        world.say(
            f"{detective.id} and {companion.id} searched together, "
            f"moving slowly so the accessible path stayed clear."
        )


def _notice_clue(world: World, detective: Entity, mystery: Mystery) -> None:
    if ("clue", mystery.id) in world.fired:
        return
    world.fired.add(("clue", mystery.id))
    _bump(detective, "clue")
    _bump(detective, "pride", 0.5)
    world.mentioned_clues.append(mystery.clue_phrase)
    world.say(f"{detective.id} spotted {mystery.clue_phrase}.")


def _inner_monologue(world: World, detective: Entity, mystery: Mystery) -> None:
    _bump(detective, "worry", 0.5)
    _say_inner(world, detective, mystery.inner_thought)


def _ask_team(world: World, detective: Entity, companion: Entity) -> None:
    _bump(companion, "trust")
    _bump(detective, "teamwork")
    _bump(companion, "teamwork")
    world.say(
        f"{detective.id} whispered the clue to {companion.id}, and they nodded like a tiny team of detectives."
    )


def _compare_clues(world: World, detective: Entity, mystery: Mystery) -> None:
    if ("compare", mystery.id) in world.fired:
        return
    world.fired.add(("compare", mystery.id))
    world.say(
        f"{detective.id} looked again at {mystery.clue_phrase} and the neat path near the ramp."
    )
    _bump(detective, "curiosity")
    _bump(detective, "clue")


def _solve(world: World, detective: Entity, companion: Entity, mystery: Mystery) -> None:
    if ("solve", mystery.id) in world.fired:
        return
    world.fired.add(("solve", mystery.id))
    _bump(detective, "relief", 1.5)
    _bump(companion, "relief", 1.0)
    _bump(detective, "pride", 1.0)
    world.facts["solved"] = True
    world.facts["revealed_hiding_place"] = mystery.hiding_place
    world.say(
        f"Then {detective.id} smiled. “I know where it is,” {detective.pronoun()} said. "
        f"“The clue points to {mystery.hiding_place}.”"
    )
    world.say(
        f"Together, {detective.id} and {companion.id} found {mystery.missing_phrase} right where it had been kept."
    )
    world.say(mystery.reveal_reason)


def tell(location: Location, mystery: Mystery, detective_name: str, detective_type: str,
         detective_trait: str, companion_name: str, companion_type: str,
         companion_trait: str) -> World:
    world = World(location)

    detective = world.add(Entity(
        id=detective_name,
        kind="character",
        type=detective_type,
        traits=[detective_trait, "detective"],
    ))
    companion = world.add(Entity(
        id=companion_name,
        kind="character",
        type=companion_type,
        traits=[companion_trait, "helper"],
    ))
    missing = world.add(Entity(
        id="missing",
        type=mystery.missing_label,
        label=mystery.missing_label,
        phrase=mystery.missing_phrase,
        owner=detective.id,
        location="hidden",
        movable=True,
        accessible=True,
    ))

    world.say(
        f"{detective.id} arrived at {location.label}, where the doorway had a wide accessible ramp and the floor was smooth and bright."
    )
    world.say(
        f"{detective.id} was a {detective_trait} little {detective_type} who liked solving whodunits."
    )
    world.say(
        f"That morning, {mystery.missing_phrase} was gone."
    )
    world.say(
        f"{companion.id} stayed close, ready to help."
    )

    world.para()
    _inner_monologue(world, detective, mystery)
    _notice_clue(world, detective, mystery)
    _ask_team(world, detective, companion)

    world.para()
    _search(world, detective, companion, mystery)
    _compare_clues(world, detective, mystery)
    if _predict_reveal(world, detective, companion, mystery):
        _solve(world, detective, companion, mystery)

    world.para()
    if world.facts.get("solved"):
        world.say(
            f"By the end, the path was clear again, {mystery.missing_phrase} was back in place, and {detective.id} felt proud of the teamwork."
        )
    else:
        world.say(
            f"The mystery stayed quiet for one more moment, but the team was still looking with careful eyes."
        )

    world.facts.update(
        detective=detective,
        companion=companion,
        missing=missing,
        mystery=mystery,
        location=location,
    )
    return world


# ---------------------------------------------------------------------------
# Narrative registries
# ---------------------------------------------------------------------------

@dataclass
class WorldProfile:
    place: str
    mystery: str
    label: str


def valid_combos() -> list[tuple[str, str]]:
    out = []
    for loc_id, loc in LOCATIONS.items():
        if not loc.accessible:
            continue
        for m_id, m in MYSTERIES.items():
            if m.clue_kind in loc.clues and m.missing_label in loc.allows:
                out.append((loc_id, m_id))
    return out


def explain_rejection(location: Location, mystery: Mystery) -> str:
    return (
        f"(No story: {mystery.missing_phrase} does not fit the clue pattern of {location.label}. "
        f"The setup needs a visible clue and a believable hiding place, so this combination is rejected.)"
    )


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    detective = f["detective"]
    companion = f["companion"]
    mystery = f["mystery"]
    return [
        f'Write a child-friendly whodunit about {detective.id} and {companion.id} at {world.location.label} with an accessible ramp.',
        f"Tell a story where {detective.id} notices a clue, thinks quietly, and works with {companion.id} to find {mystery.missing_phrase}.",
        f'Write a short mystery that uses the word "accessible" and ends with teamwork solving the puzzle.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    detective: Entity = f["detective"]
    companion: Entity = f["companion"]
    mystery: Mystery = f["mystery"]
    location: Location = f["location"]
    return [
        QAItem(
            question=f"What problem did {detective.id} notice at {location.label}?",
            answer=f"{detective.id} noticed that {mystery.missing_phrase} was gone when the day began.",
        ),
        QAItem(
            question=f"What clue helped {detective.id} think about where the missing thing was?",
            answer=f"The clue was {mystery.clue_phrase}, which made {detective.id} pause and think.",
        ),
        QAItem(
            question=f"How did {detective.id} and {companion.id} solve the mystery together?",
            answer=(
                f"They used teamwork: {detective.id} noticed the clue, whispered it to {companion.id}, "
                f"and then they searched carefully until they found {mystery.missing_phrase} in {mystery.hiding_place}."
            ),
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    loc = world.location
    return [
        QAItem(
            question="What does accessible mean?",
            answer="Accessible means something is made so more people can use it easily, like a doorway with a ramp instead of only stairs.",
        ),
        QAItem(
            question="Why do detectives think about clues before they guess?",
            answer="Detectives think about clues first so they can make a good guess instead of a wild one.",
        ),
        QAItem(
            question="What is teamwork?",
            answer="Teamwork is when people help each other and work together to do something better than they could alone.",
        ),
        QAItem(
            question=f"Why is a ramp helpful at {loc.label}?",
            answer="A ramp is helpful because it lets people roll, walk, or carry things more easily into the building.",
        ),
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


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
accessible(L) :- location(L), ramp(L).
clueful(L,M) :- location(L), mystery(M), clue_in_location(M,L).
valid_story(L,M) :- accessible(L), clueful(L,M), usable_hiding_place(L,M).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for lid, loc in LOCATIONS.items():
        lines.append(asp.fact("location", lid))
        if loc.accessible:
            lines.append(asp.fact("accessible", lid))
        for c in sorted(loc.clues):
            lines.append(asp.fact("clue_at", lid, c))
        for a in sorted(loc.allows):
            lines.append(asp.fact("allows", lid, a))
        if "ramp" in loc.clues:
            lines.append(asp.fact("ramp", lid))
    for mid, m in MYSTERIES.items():
        lines.append(asp.fact("mystery", mid))
        lines.append(asp.fact("missing_label", mid, m.missing_label))
        lines.append(asp.fact("clue_in_location", mid, m.clue_kind))
        lines.append(asp.fact("usable_hiding_place", loc_id_for_allow(m.missing_label), mid))
    return "\n".join(lines)


def loc_id_for_allow(label: str) -> str:
    for lid, loc in LOCATIONS.items():
        if label in loc.allows:
            return lid
    return "library"


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if py == asp_set:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - asp_set:
        print("  only in python:", sorted(py - asp_set))
    if asp_set - py:
        print("  only in clingo:", sorted(asp_set - py))
    return 1


# ---------------------------------------------------------------------------
# Sampling / generation
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Accessible inner-monologue teamwork whodunit.")
    ap.add_argument("--place", choices=LOCATIONS)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--name")
    ap.add_argument("--companion")
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
    combos = valid_combos()
    if args.place or args.mystery:
        combos = [
            (p, m) for (p, m) in combos
            if (args.place is None or p == args.place)
            and (args.mystery is None or m == args.mystery)
        ]
    if not combos:
        raise StoryError("(No valid accessible mystery combination matches the given options.)")
    place, mystery = rng.choice(sorted(combos))
    det_type = rng.choice(["girl", "boy"])
    comp_type = rng.choice(["girl", "boy", "helper"])
    det_name = args.name or rng.choice(NAMES[det_type])
    comp_name = args.companion or rng.choice(NAMES.get(comp_type, ["Kai"]))
    trait = rng.choice(TRAITS)
    comp_trait = rng.choice(TRAITS)
    return StoryParams(
        location=place,
        mystery=mystery,
        detective_name=det_name,
        detective_type=det_type,
        detective_trait=trait,
        companion_name=comp_name,
        companion_type=comp_type,
        companion_trait=comp_trait,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(
        LOCATIONS[params.location],
        MYSTERIES[params.mystery],
        params.detective_name,
        params.detective_type,
        params.detective_trait,
        params.companion_name,
        params.companion_type,
        params.companion_trait,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: round(v, 2) for k, v in e.meters.items() if v}
        memes = {k: round(v, 2) for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:10} ({e.type:9}) {' '.join(bits)}")
    lines.append(f"  location: {world.location.label}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


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
    StoryParams("library", "book", "Mina", "girl", "curious", "Sam", "helper", "patient"),
    StoryParams("museum", "marker", "Theo", "boy", "careful", "Lee", "helper", "kind"),
    StoryParams("cafe", "bell", "Nora", "girl", "bright", "Ari", "helper", "brave"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid_story/2."))
        print(f"{len(asp.atoms(model, 'valid_story'))} accessible compatible combinations")
        for item in sorted(set(asp.atoms(model, "valid_story"))):
            print(" ", item)
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
            header = f"### {p.detective_name}: {p.mystery} at {p.location}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
