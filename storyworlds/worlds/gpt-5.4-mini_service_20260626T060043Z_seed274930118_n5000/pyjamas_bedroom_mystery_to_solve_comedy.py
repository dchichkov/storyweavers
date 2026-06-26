#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/pyjamas_bedroom_mystery_to_solve_comedy.py
==============================================================================================================

A small, self-contained story world about a bedtime mystery in a bedroom:
someone's pyjamas have gone missing, the search turns into a comic detective
case, and the ending proves where the pyjamas were all along.

The world is constraint-checked and supports a Python reasonableness gate plus
an inline ASP twin for parity verification.
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
# Core domain data
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    hidden_in: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str = "the bedroom"
    afford: str = "bedtime"


@dataclass
class Culprit:
    id: str
    label: str
    type: str
    comic_nudge: str
    hide_spot: str
    clue: str
    can_solve: bool = True


@dataclass
class StoryParams:
    name: str
    gender: str
    parent: str
    culprit: str
    hide_spot: str
    trait: str
    seed: Optional[int] = None


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

        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTING = Setting()

CULPRITS = {
    "cat": Culprit(
        id="cat",
        label="curious cat",
        type="cat",
        comic_nudge="pounced on the dangling cuff like it was a ribbon",
        hide_spot="under the pillow",
        clue="a tiny paw print on the blanket",
    ),
    "teddy": Culprit(
        id="teddy",
        label="bouncy teddy bear",
        type="toy",
        comic_nudge="rolled around during pretend play and somehow became a detective suspect",
        hide_spot="inside the toy box",
        clue="a stuffed paw peeking out of the lid",
    ),
    "robot": Culprit(
        id="robot",
        label="little robot toy",
        type="toy",
        comic_nudge="trundled off with serious beep-beep confidence",
        hide_spot="behind the curtain",
        clue="a shiny wheel track on the carpet",
    ),
    "sibling": Culprit(
        id="sibling",
        label="silly older sibling",
        type="child",
        comic_nudge="borrowed the pyjamas for a secret giggle and forgot to put them back",
        hide_spot="in the laundry basket",
        clue="a folded blanket with the wrong socks on top",
    ),
}

TRAITS = ["sleepy", "curious", "cheerful", "silly", "brave", "bouncy"]
GIRL_NAMES = ["Mia", "Lily", "Zoe", "Ava", "Ella", "Nora", "Ruby"]
BOY_NAMES = ["Leo", "Finn", "Noah", "Ben", "Theo", "Max", "Eli"]

PYJAMAS_PHRASES = [
    "striped pyjamas",
    "soft blue pyjamas",
    "cozy starry pyjamas",
    "red rocket pyjamas",
]
PYJAMAS_LABELS = ["pyjamas", "pajamas"]


# ---------------------------------------------------------------------------
# World model and rules
# ---------------------------------------------------------------------------
def valid_combos() -> list[tuple[str, str]]:
    return sorted((c.id, c.hide_spot) for c in CULPRITS.values())


def valid_story_combo(culprit_id: str, hide_spot: str) -> bool:
    culprit = CULPRITS[culprit_id]
    return culprit.hide_spot == hide_spot and culprit.can_solve


def _mystery_proven(world: World) -> bool:
    pyj = world.entities.get("pyjamas")
    culprit = world.facts["culprit_ent"]
    return bool(pyj and pyj.hidden_in == culprit.hide_spot and pyj.owner == world.facts["hero"].id)


def tell(params: StoryParams) -> World:
    world = World(SETTING)

    hero = world.add(Entity(
        id=params.name,
        kind="character",
        type=params.gender,
        meters={"sleepiness": 0.0, "curiosity": 0.0},
        memes={"worry": 0.0, "relief": 0.0, "amusement": 0.0},
    ))
    parent = world.add(Entity(
        id="parent",
        kind="character",
        type=params.parent,
        label=f"the {params.parent}",
        meters={"patience": 1.0},
        memes={"calm": 1.0},
    ))
    pyj = world.add(Entity(
        id="pyjamas",
        type="thing",
        label="pyjamas",
        phrase=random.choice(PYJAMAS_PHRASES),
        owner=hero.id,
        caretaker=parent.id,
    ))
    culprit = CULPRITS[params.culprit]
    culprit_ent = world.add(Entity(
        id=culprit.id,
        kind="character" if culprit.type == "child" else "thing",
        type=culprit.type,
        label=culprit.label,
        meters={"mischief": 1.0},
        memes={"guilt": 0.0, "glee": 1.0},
    ))

    world.facts.update(hero=hero, parent=parent, pyj=pyj, culprit=culprit_ent, culprit_def=culprit)

    world.say(
        f"{hero.id} was a {params.trait} little {hero.type} who liked bedtime, "
        f"especially when {hero.pronoun('possessive')} {pyj.label} were ready and waiting."
    )
    world.say(
        f"One night, the room was tidy, the lamp was low, and {hero.id} wanted to wear "
        f"{hero.pronoun('possessive')} {pyj.phrase} straight away."
    )
    world.say(
        f"Then came the puzzle: the {pyj.label} were nowhere to be seen."
    )
    hero.meters["curiosity"] += 1.0
    hero.memes["worry"] += 1.0

    world.para()
    world.say(
        f"{hero.id} looked under the blanket, beside the bed, and behind the laundry chair."
    )
    world.say(
        f"{culprit.label.capitalize()} had {culprit.comic_nudge}."
    )
    world.say(
        f"That gave {hero.id} one strange clue: {culprit.clue}."
    )
    hero.meters["curiosity"] += 1.0

    world.para()
    world.say(
        f"The {params.parent} came in and squinted at the clue like a tiny bedtime detective."
    )
    world.say(
        f"\"Hmm,\" {parent.pronoun()} said, \"this looks like a bedroom mystery, but probably not a scary one.\""
    )
    world.say(
        f"{hero.id} and {parent.pronoun('object')} followed the clue with serious faces and very silly toes."
    )
    hero.memes["amusement"] += 1.0

    pyj.hidden_in = culprit.hide_spot
    culprit_ent.hidden_in = culprit.hide_spot
    world.para()
    world.say(
        f"At last, they checked {culprit.hide_spot}."
    )
    world.say(
        f"There were the {pyj.label} all along, tucked away where nobody had looked first."
    )
    world.say(
        f"{culprit.label} had simply wandered off with them during the fuss and made the whole thing look like a grand case."
    )

    hero.memes["worry"] = 0.0
    hero.memes["relief"] += 1.0
    hero.memes["amusement"] += 1.0

    if culprit.id == "cat":
        world.say(
            f"The cat blinked as if to say the pyjamas had been chosen for their excellent whisker appeal."
        )
    elif culprit.id == "teddy":
        world.say(
            f"The teddy looked especially proud, as if hiding pyjamas was a very important toy job."
        )
    elif culprit.id == "robot":
        world.say(
            f"The robot gave one last beep, which somehow sounded like an apology and a giggle at the same time."
        )
    else:
        world.say(
            f"The sibling grinned, returned the pyjamas, and admitted the prank had been funny right up until bedtime."
        )

    world.para()
    world.say(
        f"{hero.id} laughed, pulled on {hero.pronoun('possessive')} {pyj.label}, and climbed into bed."
    )
    world.say(
        f"The mystery was solved, the room felt cozy again, and the bedtime detective case ended with a smile."
    )
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    cul = f["culprit_def"]
    return [
        f"Write a short comedy mystery for a young child set in a bedroom where {hero.id} cannot find {hero.pronoun('possessive')} pyjamas.",
        f"Tell a gentle bedtime story about {hero.id} searching the bedroom for missing pyjamas and discovering that {cul.label} caused the mix-up.",
        "Write a funny, cozy mystery that ends with the pyjamas found and bedtime saved.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    parent = f["parent"]
    cul = f["culprit_def"]
    pyj = f["pyj"]

    return [
        QAItem(
            question=f"What was missing from {hero.id}'s bedroom at bedtime?",
            answer=f"{hero.id}'s pyjamas were missing, so bedtime turned into a small mystery.",
        ),
        QAItem(
            question=f"Who helped {hero.id} search for the missing pyjamas?",
            answer=f"The {parent.type} helped {hero.id} search the bedroom and follow the clue.",
        ),
        QAItem(
            question=f"Where were the pyjamas found in the end?",
            answer=f"They were found {cul.hide_spot}, which solved the mystery and made everyone laugh.",
        ),
        QAItem(
            question=f"What kind of feeling did {hero.id} have when the pyjamas were gone?",
            answer=f"{hero.id} felt worried at first, then curious, and finally relieved and amused when the pyjamas turned up.",
        ),
        QAItem(
            question=f"Why did the bedroom mystery feel funny instead of scary?",
            answer=f"It felt funny because {cul.label} caused a harmless mix-up, the clue was a little silly, and the ending was cozy and calm.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What are pyjamas for?",
            answer="Pyjamas are clothes people wear for sleeping or for getting ready for bed.",
        ),
        QAItem(
            question="What is a mystery?",
            answer="A mystery is a puzzling situation where you do not know something yet and need clues to solve it.",
        ),
        QAItem(
            question="Why do people look for clues?",
            answer="People look for clues because clues can help them figure out what happened.",
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


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.hidden_in:
            bits.append(f"hidden_in={e.hidden_in}")
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
culprit(C) :- culprit_fact(C,_).
hide_spot(C,S) :- culprit_fact(C,S).
valid_story(C,S) :- culprit(C), hide_spot(C,S).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for cid, c in CULPRITS.items():
        lines.append(asp.fact("culprit_fact", cid, c.hide_spot))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    clingo_set, python_set = set(asp_valid_combos()), set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


# ---------------------------------------------------------------------------
# Storyworld API
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A comedic bedroom mystery about missing pyjamas."
    )
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--culprit", choices=sorted(CULPRITS))
    ap.add_argument("--hide-spot", choices=sorted({c.hide_spot for c in CULPRITS.values()}))
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
    culprit_id = args.culprit or rng.choice(sorted(CULPRITS))
    culprit = CULPRITS[culprit_id]
    hide_spot = args.hide_spot or culprit.hide_spot

    if args.culprit and args.hide_spot and not valid_story_combo(args.culprit, args.hide_spot):
        raise StoryError(f"(No story: {args.culprit} does not plausibly hide pyjamas {args.hide_spot}.)")
    if args.hide_spot and args.hide_spot != culprit.hide_spot:
        raise StoryError(f"(No story: {culprit.label} does not fit the hide spot {args.hide_spot}.)")

    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(
        name=name,
        gender=gender,
        parent=parent,
        culprit=culprit_id,
        hide_spot=hide_spot,
        trait=trait,
    )


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
        combos = sorted(set(asp.atoms(model, "valid_story")))
        print(f"{len(combos)} valid bedroom mystery combos:\n")
        for c, s in combos:
            print(f"  {c:10} {s}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for cid, c in CULPRITS.items():
            params = StoryParams(
                name="Mia" if c.type != "boy" else "Leo",
                gender="girl" if c.type != "boy" else "boy",
                parent="mother",
                culprit=cid,
                hide_spot=c.hide_spot,
                trait="curious",
                seed=base_seed,
            )
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
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
        if len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
