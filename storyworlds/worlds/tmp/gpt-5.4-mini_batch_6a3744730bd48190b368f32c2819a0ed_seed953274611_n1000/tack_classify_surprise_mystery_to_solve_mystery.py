#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/tack_classify_surprise_mystery_to_solve_mystery.py
==================================================================================

A tiny mystery storyworld: children discover a surprising clue, classify
scraps and objects, and solve a small missing-item mystery with a tackboard.

The domain is intentionally small and classical:
- a room with a noticeboard
- a handful of clue objects
- a missing item
- a surprise that changes the suspects' emotions
- a calm solution that proves what changed

The story uses the seed words "tack" and "classify", and keeps a mystery style.
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
SUSPECT_MIN = 0
CLUE_SCORE_GOOD = 2


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
    taken: bool = False
    pinned: bool = False
    classified: bool = False

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
        return self.label or self.type


@dataclass
class Place:
    id: str
    name: str
    mood: str
    hiding_spot: str
    surface: str
    surprising_sound: str
    quiet: bool = True


@dataclass
class Clue:
    id: str
    label: str
    kind: str
    reveals: str
    can_tack: bool = False
    clue_score: int = 1
    tags: set[str] = field(default_factory=set)


@dataclass
class Mystery:
    id: str
    missing: str
    owner: str
    lost_place: str
    solved_by: str
    surprise: str
    ending_image: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    place: str
    mystery: str
    clue: str
    helper: str
    helper_gender: str
    child: str
    child_gender: str
    adult: str
    seed: Optional[int] = None
    clue2: str = "classify"


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


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]


def _r_surprise(world: World) -> list[str]:
    out: list[str] = []
    if world.facts.get("surprise_shown"):
        return out
    if world.facts.get("surprise_ready") and world.facts.get("clue_pinned"):
        world.facts["surprise_shown"] = True
        for eid in ("child", "helper"):
            world.get(eid).memes["surprise"] += 1
        out.append("__surprise__")
    return out


def _r_classified(world: World) -> list[str]:
    out: list[str] = []
    if world.facts.get("classified_done"):
        return out
    if world.facts.get("all_classified"):
        world.facts["classified_done"] = True
        world.get("helper").memes["pride"] += 1
        out.append("__classify__")
    return out


CAUSAL_RULES = [Rule("surprise", _r_surprise), Rule("classified", _r_classified)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            parts = rule.apply(world)
            if parts:
                changed = True
                produced.extend(p for p in parts if not p.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def classify_item(item: Entity, clue: Clue) -> str:
    if clue.kind in item.traits or clue.kind in item.attrs.get("tags", []):
        item.classified = True
        return f"{item.id} belonged in the same group as the clue."
    return f"{item.id} did not match the clue."


def tack_clue(world: World, clue_ent: Entity, board: Entity, clue: Clue) -> None:
    clue_ent.pinned = True
    board.meters["notes"] += 1
    world.facts["clue_pinned"] = True
    world.say(f"{clue_ent.label} was held on the board with a tack.")


def inspect(world: World, child: Entity, place: Place, mystery: Mystery) -> None:
    child.memes["curiosity"] += 1
    world.say(
        f"{child.id} stood in {place.name}, where {place.surprising_sound} came from "
        f"{place.hiding_spot}."
    )
    world.say(
        f"The room felt {place.mood}, like it knew a secret about {mystery.missing}."
    )


def notice_surprise(world: World, helper: Entity, child: Entity, surprise: str) -> None:
    helper.memes["alarm"] += 1
    world.facts["surprise_ready"] = True
    world.say(f"Then a surprise waited in plain sight: {surprise}.")
    world.say(f"{helper.id} blinked and asked {child.id} to look again, more carefully this time.")


def sort_clues(world: World, helper: Entity, items: list[Entity], clue: Clue) -> None:
    world.say(
        f"{helper.id} began to classify the scraps, line by line, until the room made sense."
    )
    for item in items:
        if item.id == clue.id:
            item.classified = True
            world.say(f"{item.label} matched the clue.")
        else:
            world.say(f"{item.label} stayed on the wrong side of the list.")
    world.facts["all_classified"] = all(i.classified for i in items)


def solve(world: World, child: Entity, helper: Entity, mystery: Mystery, place: Place) -> None:
    world.say(
        f"At last, {child.id} pointed to the right place and solved the mystery of {mystery.missing}."
    )
    world.say(
        f"It had been hidden near {place.hiding_spot}, just where the clue said it would be."
    )
    world.say(mystery.ending_image)
    child.memes["relief"] += 1
    helper.memes["relief"] += 1


def tell(place: Place, mystery: Mystery, clue: Clue, helper_name: str, helper_gender: str,
         child_name: str, child_gender: str, adult_name: str) -> World:
    world = World()
    board = world.add(Entity(id="board", kind="thing", type="board", label="the tackboard"))
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="child"))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_gender, role="helper"))
    adult = world.add(Entity(id=adult_name, kind="character", type="adult", role="adult"))
    missing = world.add(Entity(id="missing", kind="thing", type="thing", label=mystery.missing))
    clue_ent = world.add(Entity(id="clue", kind="thing", type="clue", label=clue.label, traits=[clue.kind]))

    world.facts["surprise_ready"] = False
    world.facts["clue_pinned"] = False
    world.facts["all_classified"] = False

    inspect(world, child, place, mystery)
    world.para()
    world.say(
        f"{child.id} and {helper.id} found {clue.label} and decided to classify the clues."
    )
    if clue.can_tack:
        tack_clue(world, clue_ent, board, clue)
    world.say(
        f"{adult.id} watched quietly, ready to help if the trail went cold."
    )
    notice_surprise(world, helper, child, mystery.surprise)
    world.para()
    items = [
        world.add(Entity(id="button", kind="thing", type="clue", label="a button", traits=["round"])),
        world.add(Entity(id="thread", kind="thing", type="clue", label="a bit of thread", traits=["soft"])),
        world.add(Entity(id="stamp", kind="thing", type="clue", label="a stamped envelope", traits=["paper"])),
        clue_ent,
    ]
    sort_clues(world, helper, items, clue)
    propagate(world, narrate=False)
    world.say(
        f"{adult.id} nodded when the list finally fit together."
    )
    solve(world, child, helper, mystery, place)
    world.facts.update(
        child=child, helper=helper, adult=adult, place=place, mystery=mystery,
        clue=clue, clue_ent=clue_ent, board=board, items=items, missing=missing
    )
    return world


PLACES = {
    "museum_room": Place(
        id="museum_room",
        name="the museum room",
        mood="still and curious",
        hiding_spot="the shadow behind the display case",
        surface="glass floor",
        surprising_sound="a tiny clink",
    ),
    "school_hall": Place(
        id="school_hall",
        name="the school hall",
        mood="quiet and bright",
        hiding_spot="the coat hooks",
        surface="polished floor",
        surprising_sound="a soft tap",
    ),
    "attic": Place(
        id="attic",
        name="the attic",
        mood="dusty and secret",
        hiding_spot="the old trunk",
        surface="wood boards",
        surprising_sound="a thump in the rafters",
    ),
}

CLUES = {
    "blue_tack": Clue(
        id="blue_tack",
        label="a blue tack",
        kind="round",
        reveals="a round mark on the board",
        can_tack=True,
        clue_score=2,
        tags={"tack", "classify"},
    ),
    "feather": Clue(
        id="feather",
        label="a white feather",
        kind="soft",
        reveals="a soft bend in the dust",
        can_tack=False,
        clue_score=1,
        tags={"mystery"},
    ),
    "stamp": Clue(
        id="stamp",
        label="a stamped envelope",
        kind="paper",
        reveals="a paper trail",
        can_tack=False,
        clue_score=3,
        tags={"classify"},
    ),
}

MYSTERIES = {
    "missing_key": Mystery(
        id="missing_key",
        missing="the library key",
        owner="the librarian",
        lost_place="the museum room",
        solved_by="the clue board",
        surprise="the missing key was tucked into the back of a picture frame",
        ending_image="The key gleamed on the desk, safe at last.",
        tags={"key", "mystery"},
    ),
    "missing_note": Mystery(
        id="missing_note",
        missing="the secret note",
        owner="the teacher",
        lost_place="the school hall",
        solved_by="the clue board",
        surprise="the secret note had been pinned behind the class poster",
        ending_image="The note lay flat and tidy beside the chalk tray.",
        tags={"note", "mystery"},
    ),
    "missing_map": Mystery(
        id="missing_map",
        missing="the treasure map",
        owner="the old guide",
        lost_place="the attic",
        solved_by="the clue board",
        surprise="the treasure map was folded inside the old trunk lid",
        ending_image="The map rested open under the lamp, full of neat lines.",
        tags={"map", "mystery"},
    ),
}

HELPER_NAMES = ["Mina", "Theo", "Iris", "Owen", "Nora", "Finn"]
CHILD_NAMES = ["Lily", "Milo", "Ava", "Ben", "Zoe", "Cal"]
ADULT_NAMES = ["Mrs. Lane", "Mr. Finch", "Ms. Vale"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for pid in PLACES:
        for mid in MYSTERIES:
            for cid in CLUES:
                if CLUES[cid].can_tack and CLUES[cid].clue_score >= CLUE_SCORE_GOOD:
                    combos.append((pid, mid, cid))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Tiny mystery storyworld: a tackboard, a surprise, and a clue classification solve."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--helper")
    ap.add_argument("--helper-gender", choices=["girl", "boy", "woman", "man"], default="girl")
    ap.add_argument("--child")
    ap.add_argument("--child-gender", choices=["girl", "boy"], default="girl")
    ap.add_argument("--adult")
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
    if args.clue and CLUES[args.clue].clue_score < CLUE_SCORE_GOOD:
        raise StoryError("That clue is too weak to make a satisfying mystery.")
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.mystery is None or c[1] == args.mystery)
              and (args.clue is None or c[2] == args.clue)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, mystery, clue = rng.choice(sorted(combos))
    helper = args.helper or rng.choice(HELPER_NAMES)
    child = args.child or rng.choice(CHILD_NAMES)
    adult = args.adult or rng.choice(ADULT_NAMES)
    return StoryParams(
        place=place,
        mystery=mystery,
        clue=clue,
        helper=helper,
        helper_gender=args.helper_gender,
        child=child,
        child_gender=args.child_gender,
        adult=adult,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError("Unknown place.")
    if params.mystery not in MYSTERIES:
        raise StoryError("Unknown mystery.")
    if params.clue not in CLUES:
        raise StoryError("Unknown clue.")
    place = PLACES[params.place]
    mystery = MYSTERIES[params.mystery]
    clue = CLUES[params.clue]
    world = tell(
        place=place,
        mystery=mystery,
        clue=clue,
        helper_name=params.helper,
        helper_gender=params.helper_gender,
        child_name=params.child,
        child_gender=params.child_gender,
        adult_name=params.adult,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    m: Mystery = f["mystery"]
    c: Clue = f["clue"]
    return [
        f'Write a child-friendly mystery story that includes the words "tack" and "classify".',
        f"Tell a short mystery where {f['child'].id} and {f['helper'].id} use a tackboard to classify clues and solve {m.missing}.",
        f"Write a surprise-filled story with a quiet clue hunt, a tack on the board, and a solved mystery.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child: Entity = f["child"]
    helper: Entity = f["helper"]
    adult: Entity = f["adult"]
    mystery: Mystery = f["mystery"]
    clue: Clue = f["clue"]
    place: Place = f["place"]
    return [
        ("What kind of story is this?",
         "It is a mystery story. The children gather clues, notice a surprise, and solve the missing-item puzzle."),
        (f"What did {child.id} and {helper.id} do with the clue?",
         f"They pinned it with a tack and used it to classify the clues. That helped them decide which scraps belonged together and which ones did not."),
        (f"What was the surprise?",
         f"The surprise was that {mystery.surprise}. That sudden discovery changed the clues from confusing to useful."),
        (f"How was the mystery solved?",
         f"They followed the clue board and found {mystery.missing} near {place.hiding_spot}. The last clue fit the others, so the hidden item made sense."),
        (f"How did the story end?",
         f"It ended with {mystery.ending_image} The room felt calm again because the missing thing was found."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What does a tack do?",
         "A tack is a small sharp pin used to hold paper or clues onto a board. It keeps the paper in place so people can study it."),
        ("What does it mean to classify things?",
         "To classify things means to sort them into groups that belong together. People do this when they want to make patterns and answers easier to see."),
        ("Why can a surprise help a mystery?",
         "A surprise can show a clue that nobody noticed before. That new clue can make the answer much easier to find."),
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
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.taken:
            bits.append("taken=True")
        if e.pinned:
            bits.append("pinned=True")
        if e.classified:
            bits.append("classified=True")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, _ in world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
surprise_shown :- clue_pinned, surprise_ready.
all_classified :- classified(clue), classified(button), classified(thread), classified(stamp).
solved :- surprise_shown, all_classified.
"""


def asp_facts() -> str:
    import asp
    parts = []
    for pid in PLACES:
        parts.append(asp.fact("place", pid))
    for mid, m in MYSTERIES.items():
        parts.append(asp.fact("mystery", mid))
    for cid, c in CLUES.items():
        parts.append(asp.fact("clue", cid))
        if c.can_tack:
            parts.append(asp.fact("can_tack", cid))
    return "\n".join(parts)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show can_tack/1."))
    return sorted(set(asp.atoms(model, "can_tack")))


def asp_verify() -> int:
    rc = 0
    try:
        import asp
        combos = asp_valid_combos()
        py = sorted((cid,) for cid, c in CLUES.items() if c.can_tack and c.clue_score >= CLUE_SCORE_GOOD)
        if set(combos) == set(py):
            print("OK: ASP gate matches Python gate.")
        else:
            print("MISMATCH: ASP and Python gates differ.")
            rc = 1
        sample = generate(resolve_params(argparse.Namespace(
            place=None, mystery=None, clue=None, helper=None, helper_gender="girl",
            child=None, child_gender="girl", adult=None
        ), random.Random(777)))
        print("OK: generate() smoke test succeeded.")
        _ = sample.story
    except Exception as exc:
        print(f"VERIFY FAILED: {exc}")
        return 1
    return rc


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
    StoryParams(place="museum_room", mystery="missing_key", clue="blue_tack", helper="Mina", helper_gender="girl", child="Lily", child_gender="girl", adult="Mrs. Lane"),
    StoryParams(place="school_hall", mystery="missing_note", clue="blue_tack", helper="Theo", helper_gender="boy", child="Ben", child_gender="boy", adult="Mr. Finch"),
    StoryParams(place="attic", mystery="missing_map", clue="blue_tack", helper="Iris", helper_gender="girl", child="Ava", child_gender="girl", adult="Ms. Vale"),
]


def build_sample_from_params(params: StoryParams) -> StorySample:
    return generate(params)


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show can_tack/1.\n#show solved/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("tack-ready clues:")
        for (cid,) in asp_valid_combos():
            print(f"  {cid}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [build_sample_from_params(p) for p in CURATED]
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
            header = f"### {p.place} / {p.mystery} / {p.clue}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
