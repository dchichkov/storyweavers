#!/usr/bin/env python3
"""
storyworlds/worlds/orchard_slavery_happy_ending_whodunit.py
===========================================================

A small, standalone storyworld about an orchard mystery with a gentle
whodunit shape and a happy ending.

Premise:
- A child visits an orchard where an old plaque, a missing tag, or a moved
  basket has been disturbed.
- The orchard also holds a careful historical record about slavery, treated
  respectfully as part of the town's memory and a reason to tell the truth.
- A few plausible suspects create a clue-driven mystery.
- The ending resolves in a kind, visible way: the true cause is found, the
  orchard is set right, and the characters leave with a clearer, calmer place.

This script follows the Storyweavers contract:
- stdlib-only prose engine
- typed entities with physical meters and emotional memes
- inline ASP twin plus Python reasonableness gate
- StorySample / QAItem / StoryError from storyworlds.results
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
# Domain registries
# ---------------------------------------------------------------------------

@dataclass
class Setting:
    place: str
    indoor: bool = False
    affords: set[str] = field(default_factory=set)


@dataclass
class Clue:
    id: str
    label: str
    kind: str
    reveals: str
    weight: int = 1


@dataclass
class Suspect:
    id: str
    label: str
    type: str
    motive: str
    alibi: str
    innocent: bool = False


@dataclass
class Case:
    id: str
    mystery: str
    hidden_cause: str
    solution: str
    ending_image: str


SETTINGS = {
    "orchard": Setting(
        place="the orchard",
        indoor=False,
        affords={"lost_tag", "missing_basket", "scratched_sign"},
    ),
    "packing_shed": Setting(
        place="the packing shed",
        indoor=True,
        affords={"lost_tag", "missing_basket"},
    ),
}

CLUES = {
    "apple_skin": Clue(
        id="apple_skin",
        label="a curl of apple skin",
        kind="fruit",
        reveals="Someone had peeled an apple nearby.",
    ),
    "muddy_footprint": Clue(
        id="muddy_footprint",
        label="a muddy footprint",
        kind="ground",
        reveals="The ground had been crossed by boots, not paws.",
    ),
    "ladder_mark": Clue(
        id="ladder_mark",
        label="a ladder mark on the grass",
        kind="tool",
        reveals="A ladder had been moved and leaned there earlier.",
    ),
    "ink_card": Clue(
        id="ink_card",
        label="an ink-stained card",
        kind="paper",
        reveals="A person had handled old records and writing tools.",
    ),
    "windy_leaf": Clue(
        id="wind",
        label="a leaf stuck in a fence slat",
        kind="weather",
        reveals="The wind had blown hard through the rows.",
    ),
}

SUSPECTS = {
    "mara": Suspect(
        id="Mara",
        label="the orchard keeper",
        type="adult",
        motive="She wanted the rows to stay neat for visitors.",
        alibi="She had been at the shed counting crates.",
    ),
    "noah": Suspect(
        id="Noah",
        label="the helper boy",
        type="child",
        motive="He liked moving things to make room for games.",
        alibi="He was carrying apples to the tasting table.",
    ),
    "mrs_lee": Suspect(
        id="Mrs. Lee",
        label="the museum guide",
        type="adult",
        motive="She wanted the old records to stay safe and readable.",
        alibi="She had been showing visitors the history room.",
        innocent=True,
    ),
    "wind": Suspect(
        id="wind",
        label="the wind",
        type="weather",
        motive="It could shake branches and nudge light objects around.",
        alibi="It had been rattling the fence all morning.",
        innocent=True,
    ),
}

CASES = {
    "tag": Case(
        id="tag",
        mystery="a missing red tag from the orchard history board",
        hidden_cause="the museum guide moved it while cleaning a dusty display",
        solution="Mrs. Lee had taken the tag down only to wipe the board, then put it back in the right spot",
        ending_image="the red tag was back on the board, shining beside the apple trees",
    ),
    "basket": Case(
        id="basket",
        mystery="a missing basket from under the apple table",
        hidden_cause="the helper boy borrowed it to carry windfalls to the press",
        solution="Noah had simply carried the basket to the press table and forgotten to say so",
        ending_image="the basket sat by the press, full of apples and no longer missing",
    ),
    "sign": Case(
        id="sign",
        mystery="a scratched sign near the oldest tree",
        hidden_cause="a loose branch had scraped it during a windy swing",
        solution="the wind had nudged the branch, and Mara trimmed it before it could scratch again",
        ending_image="the sign stood straight again, with the old tree calm behind it",
    ),
}


# ---------------------------------------------------------------------------
# Shared entity model
# ---------------------------------------------------------------------------

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
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
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

    def copy(self) -> "World":
        import copy
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.facts = dict(self.facts)
        clone.paragraphs = [[]]
        return clone


# ---------------------------------------------------------------------------
# ASP twin / reasonableness gate
# ---------------------------------------------------------------------------

ASP_RULES = r"""
case_valid(S) :- setting(S), affords(S, A), clue_set(A), has_solution(A).
has_solution(tag).
has_solution(basket).
has_solution(sign).

clue_set(tag) :- clue(apple_skin); clue(ink_card).
clue_set(basket) :- clue(muddy_footprint); clue(apple_skin).
clue_set(sign) :- clue(windy_leaf); clue(apple_skin).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if setting.indoor:
            lines.append(asp.fact("indoor", sid))
        for a in sorted(setting.affords):
            lines.append(asp.fact("affords", sid, a))
    for cid, clue in CLUES.items():
        lines.append(asp.fact("clue", cid))
        lines.append(asp.fact("clue_kind", cid, clue.kind))
    for sid, case in CASES.items():
        lines.append(asp.fact("case", sid))
        lines.append(asp.fact("case_type", sid, case.id))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_settings() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show case_valid/1."))
    return sorted(set(asp.atoms(model, "case_valid")))


def asp_verify() -> int:
    py = sorted((s,) for s in valid_setting_ids())
    cl = asp_valid_settings()
    if py == cl:
        print(f"OK: clingo gate matches Python gate ({len(py)} settings).")
        return 0
    print("MISMATCH between clingo and Python gate:")
    print("python:", py)
    print("clingo:", cl)
    return 1


def valid_setting_ids() -> list[str]:
    return [sid for sid, setting in SETTINGS.items() if setting.affords]


# ---------------------------------------------------------------------------
# World logic
# ---------------------------------------------------------------------------

THRESHOLD = 1.0


def reason_gate(case: Case) -> bool:
    return case.id in CASES


def choose_case(rng: random.Random, setting: Setting) -> Case:
    options = [c for c in CASES.values() if c.id in setting.affords]
    if not options:
        raise StoryError("This setting cannot support a clear orchard mystery.")
    return rng.choice(options)


def choose_suspects(rng: random.Random, case: Case) -> list[Suspect]:
    pool = list(SUSPECTS.values())
    rng.shuffle(pool)
    suspects = [pool[0], pool[1], pool[2]]
    if case.id == "sign":
        suspects = [SUSPECTS["mara"], SUSPECTS["noah"], SUSPECTS["wind"]]
    elif case.id == "tag":
        suspects = [SUSPECTS["mrs_lee"], SUSPECTS["noah"], SUSPECTS["wind"]]
    elif case.id == "basket":
        suspects = [SUSPECTS["noah"], SUSPECTS["mara"], SUSPECTS["mrs_lee"]]
    return suspects


def build_world(params: "StoryParams") -> World:
    setting = SETTINGS[params.place]
    case = CASES[params.case]
    world = World(setting)

    child = world.add(Entity(id=params.name, kind="character", type=params.gender, label=params.name))
    adult = world.add(Entity(id="Guide", kind="character", type="woman" if params.parent == "mother" else "man", label="the guide"))
    orchard = world.add(Entity(id="Orchard", kind="place", type="place", label="the orchard"))

    suspects = choose_suspects(random.Random(params.seed or 0), case)
    for s in suspects:
        world.add(Entity(id=s.id, kind="character", type=s.type, label=s.label))

    world.facts.update(
        child=child,
        adult=adult,
        orchard=orchard,
        case=case,
        suspects=suspects,
        true_suspect=suspects[0],
        clue_ids=params.clues,
    )

    child.memes["curious"] = 1
    child.memes["wonder"] = 1
    adult.memes["calm"] = 1

    world.say(
        f"{params.name} came to {setting.place} with the guide and looked at the neat rows of apple trees."
    )
    world.say(
        "Near the oldest tree, the orchard kept a little history board about the people who worked there long ago, so the town would remember the truth about slavery and about the families who later cared for the land."
    )
    world.para()
    world.say(
        f"Then something was wrong: {case.mystery}."
    )
    world.say(
        f"{params.name} felt curious right away. The guide smiled and said they could solve it by looking carefully."
    )

    # Clue trail
    world.para()
    clues = [CLUES[cid] for cid in params.clues]
    for clue in clues:
        world.say(f"They found {clue.label}. {clue.reveals}")
    return world


# ---------------------------------------------------------------------------
# Story parameters / QA
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    place: str
    case: str
    name: str
    gender: str
    parent: str
    seed: Optional[int] = None
    clues: list[str] = field(default_factory=list)


NAMES = ["Mina", "Eli", "Nora", "Theo", "Lila", "Sam"]
GENDERS = ["girl", "boy"]
PARENTS = ["mother", "father"]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or "orchard"
    if place not in SETTINGS:
        raise StoryError("Unknown setting.")
    setting = SETTINGS[place]

    case = args.case or choose_case(rng, setting).id
    if case not in CASES:
        raise StoryError("Unknown mystery case.")

    if args.clue:
        clues = list(args.clue)
    else:
        if case == "tag":
            clues = ["apple_skin", "ink_card"]
        elif case == "basket":
            clues = ["muddy_footprint", "apple_skin"]
        else:
            clues = ["windy_leaf", "ladder_mark"]

    name = args.name or rng.choice(NAMES)
    gender = args.gender or rng.choice(GENDERS)
    parent = args.parent or rng.choice(PARENTS)

    return StoryParams(
        place=place,
        case=case,
        name=name,
        gender=gender,
        parent=parent,
        clues=clues,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    case: Case = f["case"]
    child: Entity = f["child"]
    return [
        f"Write a gentle whodunit in {world.setting.place} where {child.id} solves {case.mystery}.",
        "Tell a short orchard mystery with clues, a careful reveal, and a happy ending.",
        "Write a child-friendly story that mentions the orchard's history and ends with the truth restored.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    case: Case = f["case"]
    child: Entity = f["child"]
    adult: Entity = f["adult"]
    suspects: list[Suspect] = f["suspects"]
    true_suspect = suspects[0]

    return [
        QAItem(
            question=f"What mystery did {child.id} notice in the orchard?",
            answer=f"{child.id} noticed {case.mystery}. It made the little group stop and look carefully around the trees.",
        ),
        QAItem(
            question=f"Who helped {child.id} look for clues?",
            answer=f"The guide helped {child.id} look for clues and stay calm while they searched the orchard together.",
        ),
        QAItem(
            question=f"Who turned out to be the most likely cause of the mystery?",
            answer=f"The clues pointed most strongly to {true_suspect.label}. The story keeps the answer gentle and fair, so the true cause can be understood without blame where it does not belong.",
        ),
        QAItem(
            question="Why did the story mention slavery?",
            answer=(
                "It mentioned slavery because the orchard kept a careful history board, and the story wanted to show that remembering the truth matters. "
                "The board helped the town honor the people who suffered and the people who later cared for the land."
            ),
        ),
        QAItem(
            question="How did the mystery end?",
            answer=f"It ended with a happy fix: {case.solution}. In the last image, {case.ending_image}.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is an orchard?",
            answer="An orchard is a place where fruit trees grow together, like apple trees or pear trees.",
        ),
        QAItem(
            question="What is a whodunit?",
            answer="A whodunit is a mystery story where the characters look for clues to find out who caused the problem.",
        ),
        QAItem(
            question="Why is it important to remember hard history?",
            answer="It is important to remember hard history so people can tell the truth, be kind, and make better choices in the future.",
        ),
        QAItem(
            question="What does slavery mean?",
            answer=(
                "Slavery was an unfair system where people were forced to work and were not treated as free human beings. "
                "It is part of history, and people remember it so they can honor those who suffered and work for fairness now."
            ),
        ),
    ]


# ---------------------------------------------------------------------------
# Rendering and CLI
# ---------------------------------------------------------------------------

def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts ==",]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for qa in sample.story_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for qa in sample.world_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
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
        lines.append(f"  {e.id:10} ({e.kind:7}) {' '.join(bits)}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Orchard whodunit storyworld with a happy ending.")
    ap.add_argument("--place", choices=sorted(SETTINGS))
    ap.add_argument("--case", choices=sorted(CASES))
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=GENDERS)
    ap.add_argument("--parent", choices=PARENTS)
    ap.add_argument("--clue", action="append", choices=sorted(CLUES))
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


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    case: Case = world.facts["case"]
    child: Entity = world.facts["child"]
    adult: Entity = world.facts["adult"]

    world.para()
    world.say(
        f"{child.id} studied the clues like tiny puzzle pieces. {adult.label.capitalize()} pointed to the marks on the ground, the leaves, and the old board."
    )
    world.say(
        f"At last, {child.id} understood that the most likely answer was not a scary stranger but an ordinary, honest reason."
    )
    world.para()
    world.say(
        f"The mystery was solved: {case.solution}."
    )
    world.say(
        f"The orchard felt peaceful again, and {child.id} could see {case.ending_image}."
    )
    world.say(
        "The guide thanked everyone for looking carefully, because truth makes a place feel safer and kinder."
    )

    story = world.render()
    return StorySample(
        params=params,
        story=story,
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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


def asp_verify_gate() -> int:
    import asp
    model = asp.one_model(asp_program("#show case_valid/1."))
    asp_set = set(asp.atoms(model, "case_valid"))
    py_set = {(sid,) for sid in valid_setting_ids()}
    if asp_set == py_set:
        print(f"OK: ASP gate matches Python gate ({len(py_set)} settings).")
        return 0
    print("MISMATCH between ASP and Python gate.")
    print("ASP:", sorted(asp_set))
    print("PY :", sorted(py_set))
    return 1


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show case_valid/1."))
        return
    if args.verify:
        sys.exit(asp_verify_gate())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show case_valid/1."))
        vals = sorted(set(asp.atoms(model, "case_valid")))
        print(f"{len(vals)} valid settings:")
        for (sid,) in vals:
            print(f"  {sid}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for sid in sorted(CASES):
            p = StoryParams(
                place="orchard",
                case=sid,
                name=random.choice(NAMES),
                gender=random.choice(GENDERS),
                parent=random.choice(PARENTS),
                seed=base_seed,
                clues=["apple_skin", "ink_card"] if sid == "tag" else (
                    ["muddy_footprint", "apple_skin"] if sid == "basket" else ["windy_leaf", "ladder_mark"]
                ),
            )
            samples.append(generate(p))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
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
        header = ""
        if len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
