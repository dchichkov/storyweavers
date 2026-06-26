#!/usr/bin/env python3
"""
storyworlds/worlds/cheap_enchilada_mystery_to_solve_problem_solving.py
======================================================================

A tiny mythic storyworld about a cheap enchilada mystery, where a child and a
helper notice a problem, follow clues, and solve it with careful thinking.

The seed image:
---
A small village festival needs one last meal. A clever child discovers that the
cheap enchilada everyone expected to serve is missing from the stone table.
Something has gone wrong: the shell is cracked, the sauce is gone, or the tray
was set in the wrong place. The child and a helper follow clues, solve the
mystery, and make the meal whole again.

The simulated domain:
---
- The village has a plaza, a kitchen, a market, and a hearth.
- A cheap enchilada is a humble food with a fragile shell and bright sauce.
- A mystery can hide in a clue trail: crumbs, sauce smears, a breeze, a cat,
  or a mistaken swap.
- Problem solving means asking who moved what, what broke, what is missing,
  and what can be repaired.
- The ending proves a change in state: the meal is found, fixed, or replaced,
  and the feast can begin.
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
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother", "queen"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father", "king"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    id: str
    label: str
    kind: str
    clues: set[str] = field(default_factory=set)
    affords: set[str] = field(default_factory=set)


@dataclass
class Mystery:
    id: str
    label: str
    phrase: str
    clue_markers: set[str] = field(default_factory=set)
    fix_markers: set[str] = field(default_factory=set)
    spoiled_by: str = "none"
    risk_place: str = ""
    solved_by: str = ""
    requires: set[str] = field(default_factory=set)


@dataclass
class Helper:
    id: str
    label: str
    kind: str
    skill: str
    gaze: str
    action: str
    result: str


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.trace_log: list[str] = []

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)
            self.trace_log.append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        import copy
        w = World(self.place)
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.trace_log = list(self.trace_log)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        return w


@dataclass
class StoryParams:
    place: str
    mystery: str
    helper: str
    hero_name: str
    hero_type: str
    seed: Optional[int] = None


PLACES = {
    "plaza": Place(
        id="plaza",
        label="the sunlit plaza",
        kind="public",
        clues={"crumbs", "sauce", "dust", "shadow"},
        affords={"search", "gather"},
    ),
    "kitchen": Place(
        id="kitchen",
        label="the village kitchen",
        kind="indoor",
        clues={"crumbs", "sauce", "steam", "lid"},
        affords={"search", "cook"},
    ),
    "market": Place(
        id="market",
        label="the busy market",
        kind="public",
        clues={"cloth", "wheelmark", "coin", "basket"},
        affords={"search", "trade"},
    ),
    "hearth": Place(
        id="hearth",
        label="the warm hearth room",
        kind="indoor",
        clues={"ash", "crumbs", "glow", "bowl"},
        affords={"search", "warm"},
    ),
}

MYSTERIES = {
    "missing_enchilada": Mystery(
        id="missing_enchilada",
        label="the cheap enchilada",
        phrase="a cheap enchilada with bright red sauce and a soft corn shell",
        clue_markers={"crumbs", "sauce", "lid", "wheelmark", "basket"},
        fix_markers={"reassembled", "replaced", "served"},
        spoiled_by="cold wind",
        risk_place="plaza",
        solved_by="found_and_repaired",
        requires={"search", "problem_solving"},
    ),
    "split_shell": Mystery(
        id="split_shell",
        label="the cheap enchilada",
        phrase="a cheap enchilada with a cracked shell and a spill of sauce",
        clue_markers={"crumbs", "sauce", "ash"},
        fix_markers={"patched", "served"},
        spoiled_by="rough carry",
        risk_place="kitchen",
        solved_by="patched_and_served",
        requires={"search", "problem_solving"},
    ),
}

HELPERS = {
    "owl": Helper(
        id="owl",
        label="an old owl",
        kind="animal",
        skill="patient seeing",
        gaze="wise eyes",
        action="tilts its head and looks for tiny signs",
        result="notices where the trail bends",
    ),
    "grandmother": Helper(
        id="grandmother",
        label="the grandmother",
        kind="person",
        skill="careful hands",
        gaze="kind eyes",
        action="touches the bowl and follows the clues",
        result="remembers how the tray was moved",
    ),
    "fox": Helper(
        id="fox",
        label="a small fox",
        kind="animal",
        skill="quick sniffing",
        gaze="sharp nose",
        action="sniffs the air and darts along the edge of the path",
        result="finds the hidden basket",
    ),
}


GIRL_NAMES = ["Mira", "Lina", "Nia", "Tala", "Ira", "Sela"]
BOY_NAMES = ["Kian", "Ravi", "Oren", "Timo", "Niko", "Eli"]
TRAITS = ["curious", "brave", "thoughtful", "gentle", "steady", "bright"]


def choose_helper(helper_id: str) -> Helper:
    if helper_id not in HELPERS:
        raise StoryError(f"Unknown helper '{helper_id}'.")
    return HELPERS[helper_id]


def choose_mystery(mystery_id: str) -> Mystery:
    if mystery_id not in MYSTERIES:
        raise StoryError(f"Unknown mystery '{mystery_id}'.")
    return MYSTERIES[mystery_id]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place_id, place in PLACES.items():
        for mystery_id, mystery in MYSTERIES.items():
            if mystery.risk_place and mystery.risk_place != place_id:
                continue
            for helper_id in HELPERS:
                combos.append((place_id, mystery_id, helper_id))
    return combos


ASP_RULES = r"""
place(plaza). place(kitchen). place(market). place(hearth).
affords(plaza,search). affords(plaza,gather).
affords(kitchen,search). affords(kitchen,cook).
affords(market,search). affords(market,trade).
affords(hearth,search). affords(hearth,warm).

mystery(missing_enchilada). mystery(split_shell).
risk_place(missing_enchilada,plaza).
risk_place(split_shell,kitchen).

helper(owl). helper(grandmother). helper(fox).

valid(P,M,H) :- place(P), mystery(M), helper(H), affords(P,search),
                not blocked(P,M).
blocked(P,M) :- risk_place(M,R), P != R, risk_place(M,R).

#show valid/3.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for p in PLACES.values():
        lines.append(asp.fact("place", p.id))
        lines.append(asp.fact("place_kind", p.id, p.kind))
        for c in sorted(p.clues):
            lines.append(asp.fact("clue", p.id, c))
        for a in sorted(p.affords):
            lines.append(asp.fact("affords", p.id, a))
    for m in MYSTERIES.values():
        lines.append(asp.fact("mystery", m.id))
        lines.append(asp.fact("spoiled_by", m.id, m.spoiled_by))
        if m.risk_place:
            lines.append(asp.fact("risk_place", m.id, m.risk_place))
        for c in sorted(m.clue_markers):
            lines.append(asp.fact("mystery_clue", m.id, c))
        for f in sorted(m.fix_markers):
            lines.append(asp.fact("fix_marker", m.id, f))
    for h in HELPERS.values():
        lines.append(asp.fact("helper", h.id))
        lines.append(asp.fact("skill", h.id, h.skill))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


@dataclass
class StepLog:
    clue: str
    meaning: str


def seed_story(world: World, hero: Entity, helper: Helper, mystery: Mystery) -> None:
    world.say(
        f"Long ago, when the bells were young, {hero.id} kept watch over {mystery.label}."
    )
    world.say(
        f"It was not a rich feast, only a cheap enchilada, yet everyone honored it "
        f"because small things can feed a whole village."
    )
    world.say(
        f"Then, at the edge of {world.place.label}, the food was gone or broken, and "
        f"{hero.id} felt a hush of worry."
    )
    world.say(
        f"That was when {helper.label} came near; {helper.action}."
    )


def inspect_clue(world: World, hero: Entity, helper: Helper, mystery: Mystery) -> list[StepLog]:
    logs: list[StepLog] = []
    place = world.place
    if "crumbs" in place.clues or "crumbs" in mystery.clue_markers:
        logs.append(StepLog("crumbs", "someone carried the meal in a hurry"))
    if "sauce" in place.clues or "sauce" in mystery.clue_markers:
        logs.append(StepLog("sauce", "the enchilada had been moved, not stolen by magic"))
    if "wheelmark" in place.clues or "basket" in place.clues:
        logs.append(StepLog("basket", "a basket or cart had passed by the stone table"))
    if "shadow" in place.clues:
        logs.append(StepLog("shadow", "a shape had lingered near the doorway"))
    if "lid" in place.clues:
        logs.append(StepLog("lid", "something had been covered and set aside"))
    return logs


def solve_mystery(world: World, hero: Entity, helper: Helper, mystery: Mystery) -> None:
    logs = inspect_clue(world, hero, helper, mystery)
    world.facts["logs"] = logs
    if logs:
        world.say(
            f"{hero.id} looked at the small signs one by one, and {helper.label} "
            f"helped by {helper.skill}."
        )
    for log in logs:
        world.say(f"The clue of {log.clue} meant that {log.meaning}.")
    if mystery.id == "missing_enchilada":
        world.say(
            f"At last they found the cheap enchilada in a basket by the market gate, "
            f"where the wind could not touch it."
        )
        world.say(
            f"The shell was still whole, and the sauce had only slipped to one side."
        )
    else:
        world.say(
            f"At last they found the cheap enchilada beside the hearth, where the heat "
            f"had cracked its shell."
        )
        world.say(
            f"{helper.label} suggested a careful repair, and {hero.id} listened."
        )


def repair_and_finish(world: World, hero: Entity, mystery: Mystery, helper: Helper) -> None:
    if mystery.id == "missing_enchilada":
        world.facts["solved"] = True
        world.say(
            f"They set the cheap enchilada back on the stone table, warmed the sauce, "
            f"and carried it to the feast."
        )
        world.say(
            f"The village ate with relief, for the meal had been found and the mystery "
            f"was no longer a shadow."
        )
    else:
        world.facts["solved"] = True
        world.say(
            f"They patched the cracked shell with fresh corn and spooned the sauce back "
            f"into place."
        )
        world.say(
            f"When the plate was lifted, the cheap enchilada looked humble again, but now "
            f"it was whole."
        )


def tell(place: Place, mystery: Mystery, helper: Helper, hero_name: str, hero_type: str) -> World:
    world = World(place)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type))
    companion = world.add(Entity(id=helper.id, kind="character", type="helper", label=helper.label))
    ench = world.add(Entity(
        id="enchilada",
        type="enchilada",
        label="cheap enchilada",
        phrase=mystery.phrase,
        owner=hero.id,
    ))

    world.facts.update(hero=hero, companion=companion, mystery=mystery, helper=helper, ench=ench)

    seed_story(world, hero, helper, mystery)
    world.para()
    world.say(
        f"{hero.id} said the first rule of the day: when something is missing, do not panic; "
        f"look for the clue."
    )
    world.say(
        f"So {hero.id} and {helper.label} began to search {place.label}, moving slowly as if "
        f"the ground itself might whisper."
    )
    solve_mystery(world, hero, helper, mystery)
    world.para()
    repair_and_finish(world, hero, mystery, helper)
    world.say(
        f"In the end, {hero.id} stood beside the table while the village tasted the meal, "
        f"and the little cheap enchilada became part of the story the elders told."
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    mystery = f["mystery"]
    helper = f["helper"]
    return [
        "Write a myth-like story for young children about a cheap enchilada and a mystery that must be solved.",
        f"Tell a gentle tale where {hero.id} notices that {mystery.label} is in trouble and {helper.label} helps solve the problem.",
        f"Write a short mythic problem-solving story with clues, careful thinking, and the words cheap and enchilada.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    mystery = f["mystery"]
    helper = f["helper"]
    place = world.place.label
    qa = [
        QAItem(
            question=f"What was the mystery in {place}?",
            answer=f"The mystery was what happened to the cheap enchilada, a humble meal that the village expected to serve.",
        ),
        QAItem(
            question=f"Who helped {hero.id} solve the problem?",
            answer=f"{helper.label} helped by looking carefully at the clues and guiding {hero.id} through the search.",
        ),
        QAItem(
            question="How did they solve it?",
            answer=(
                f"They followed the clues, found the cheap enchilada, and then repaired or carried it "
                f"back so the feast could continue."
            ),
        ),
    ]
    if mystery.id == "missing_enchilada":
        qa.append(QAItem(
            question="Where was the cheap enchilada found?",
            answer="It was found in a basket near the market gate, safe from the wind.",
        ))
    else:
        qa.append(QAItem(
            question="What was wrong with the cheap enchilada?",
            answer="Its shell had cracked near the hearth, so it needed a careful repair.",
        ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is an enchilada?",
            answer="An enchilada is a tortilla rolled or folded around filling, usually with sauce on top.",
        ),
        QAItem(
            question="Why can a cheap meal still matter?",
            answer="A cheap meal can still matter because it can feed people, and caring for food shows respect and gratitude.",
        ),
        QAItem(
            question="What is a clue?",
            answer="A clue is a small sign that helps someone figure out what happened.",
        ),
        QAItem(
            question="What does it mean to solve a problem?",
            answer="To solve a problem means to think carefully, find a way through the trouble, and make things work again.",
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
    lines.append("== (3) World knowledge ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    lines.append(f"place: {world.place.label}")
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id} ({e.type}) {' '.join(bits)}")
    if world.facts.get("logs"):
        lines.append("  clues:")
        for log in world.facts["logs"]:
            lines.append(f"    - {log.clue}: {log.meaning}")
    return "\n".join(lines)


def explain_rejection(place: str, mystery: str) -> str:
    return f"(No story: the chosen combination at {place} does not fit the {mystery} mystery.)"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_combos()
    if args.place and args.place not in PLACES:
        raise StoryError(f"Unknown place '{args.place}'.")
    if args.mystery and args.mystery not in MYSTERIES:
        raise StoryError(f"Unknown mystery '{args.mystery}'.")
    if args.helper and args.helper not in HELPERS:
        raise StoryError(f"Unknown helper '{args.helper}'.")

    filtered = [
        c for c in combos
        if (args.place is None or c[0] == args.place)
        and (args.mystery is None or c[1] == args.mystery)
        and (args.helper is None or c[2] == args.helper)
    ]
    if not filtered:
        raise StoryError("(No valid combination matches the given options.)")
    place, mystery_id, helper_id = rng.choice(sorted(filtered))
    mystery = MYSTERIES[mystery_id]
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    hero_type = gender
    return StoryParams(
        place=place,
        mystery=mystery_id,
        helper=helper_id,
        hero_name=name,
        hero_type=hero_type,
        seed=None,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(PLACES[params.place], MYSTERIES[params.mystery], HELPERS[params.helper], params.hero_name, params.hero_type)
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
    ap = argparse.ArgumentParser(
        description="Mythic storyworld: a cheap enchilada mystery solved by careful problem solving."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--helper", choices=HELPERS)
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


def asp_verify() -> int:
    import asp
    py = set(valid_combos())
    ac = set(asp_valid_combos())
    if py == ac:
        print(f"OK: ASP matches Python valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between ASP and Python:")
    print("only python:", sorted(py - ac))
    print("only asp:", sorted(ac - py))
    return 1


CURATED = [
    StoryParams(place="plaza", mystery="missing_enchilada", helper="owl", hero_name="Mira", hero_type="girl"),
    StoryParams(place="kitchen", mystery="split_shell", helper="grandmother", hero_name="Kian", hero_type="boy"),
    StoryParams(place="plaza", mystery="missing_enchilada", helper="fox", hero_name="Tala", hero_type="girl"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for c in combos:
            print(" ", c)
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
            rng = random.Random(seed)
            i += 1
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
        if args.all:
            p = sample.params
            header = f"### {p.hero_name}: {p.mystery} at {p.place} with {p.helper}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
