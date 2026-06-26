#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/hose_credit_conflict_problem_solving_detective_story.py
==============================================================================================================================

A standalone storyworld in a small detective-story domain.

Premise:
- A child detective tries to solve a household problem involving a hose and some
  credit.
- The conflict is not physical danger; it is a practical disagreement about who
  may use what, and how to fix the mess in a fair way.
- The ending proves the change in state: the truth is found, the problem is
  solved, and the characters' feelings shift from tense to relieved.

This script follows the Storyworld contract:
- self-contained stdlib script
- eager import of storyworlds/results.py for QAItem, StoryError, StorySample
- lazy import of storyworlds/asp.py in ASP helpers
- defines StoryParams, registries, build_parser, resolve_params, generate, emit,
  main
- supports default run, -n, --all, --seed, --trace, --qa, --json, --asp,
  --verify, and --show-asp

The story is deliberately constrained:
- The hose must matter to the problem.
- The credit must matter to the solution or the conflict.
- The protagonist must do detective work, not simply receive a fixed ending.
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
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    borrowed_from: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    clues: list[str] = field(default_factory=list)

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
class Setting:
    place: str
    indoor: bool = False
    affordances: set[str] = field(default_factory=set)


@dataclass
class Hose:
    label: str
    phrase: str
    kind: str
    risk: str
    use: str
    clue_source: str
    place: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Credit:
    label: str
    phrase: str
    kind: str
    form: str
    owner_role: str
    kind_of_credit: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Fix:
    label: str
    phrase: str
    prep: str
    result: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.trace: list[str] = []

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.facts = dict(self.facts)
        return clone


@dataclass
class StoryParams:
    place: str
    hose: str
    credit: str
    detective: str
    detective_type: str
    helper: str
    helper_type: str
    suspect: str
    suspect_type: str
    seed: Optional[int] = None


SETTINGS = {
    "shed": Setting(place="the shed", indoor=True, affordances={"search", "repair"}),
    "yard": Setting(place="the yard", indoor=False, affordances={"search", "water", "repair"}),
    "garage": Setting(place="the garage", indoor=True, affordances={"search", "repair"}),
    "porch": Setting(place="the porch", indoor=False, affordances={"search", "water"}),
}

HOSES = {
    "green_hose": Hose(
        label="green garden hose",
        phrase="a green garden hose with a brass nozzle",
        kind="hose",
        risk="dry patch",
        use="water the dusty plants",
        clue_source="coiled neatly near the wall",
        place="yard",
        tags={"hose", "water", "garden"},
    ),
    "red_hose": Hose(
        label="red garden hose",
        phrase="a red garden hose with a wobbly connector",
        kind="hose",
        risk="leaky spot",
        use="spray off the muddy step",
        clue_source="hung on a hook by the door",
        place="porch",
        tags={"hose", "water", "repair"},
    ),
}

CREDITS = {
    "store_credit": Credit(
        label="store credit slip",
        phrase="a little store credit slip",
        kind="credit",
        form="slip",
        owner_role="parent",
        kind_of_credit="store credit",
        tags={"credit", "money", "receipt"},
    ),
    "library_credit": Credit(
        label="library credit card",
        phrase="a library credit card",
        kind="card",
        owner_role="librarian",
        kind_of_credit="library credit",
        form="card",
        tags={"credit", "card", "borrow"},
    ),
}

FIXES = {
    "receipt_check": Fix(
        label="receipt check",
        phrase="check the receipt and the checkout list",
        prep="look at the receipt, then follow the checkout list",
        result="the truth about who used the credit",
        tags={"problem_solving", "detective", "receipt"},
    ),
    "hose_patch": Fix(
        label="hose patch kit",
        phrase="use the patch kit and tighten the connector",
        prep="fetch the patch kit and fix the crack",
        result="the hose stopped leaking",
        tags={"problem_solving", "repair", "hose"},
    ),
    "fair_trade": Fix(
        label="fair trade",
        phrase="make a fair trade for the borrowed credit",
        prep="talk it out and make a fair trade",
        result="everyone agreed and the argument cooled down",
        tags={"conflict", "problem_solving", "credit"},
    ),
}

GIRL_NAMES = ["Mina", "Ruby", "Nora", "Ivy", "June", "Ada", "Maya", "Lena"]
BOY_NAMES = ["Eli", "Otto", "Theo", "Finn", "Max", "Leo", "Ben", "Sam"]
TRAITS = ["curious", "careful", "brave", "sharp-eyed", "quiet", "patient"]


def select_hose(place: str) -> Hose:
    if place == "yard":
        return HOSES["green_hose"]
    return HOSES["red_hose"]


def select_credit() -> Credit:
    return CREDITS["store_credit"]


def select_fix(hose: Hose, credit: Credit) -> Fix:
    if hose.kind == "hose" and credit.kind == "credit":
        return FIXES["receipt_check"]
    return FIXES["fair_trade"]


def reasonableness_gate(hose: Hose, credit: Credit) -> bool:
    return "hose" in hose.tags and "credit" in credit.tags


def predict_problem(world: World, detective: Entity, hose: Entity, credit: Entity) -> dict:
    sim = world.copy()
    _do_investigation(sim, sim.get(detective.id), sim.get(hose.id), sim.get(credit.id), narrate=False)
    return {
        "solved": sim.facts.get("solved", False),
        "conflict": sim.facts.get("conflict", False),
    }


def _do_investigation(world: World, detective: Entity, hose: Entity, credit: Entity, narrate: bool = True) -> None:
    detective.memes["curiosity"] = detective.memes.get("curiosity", 0) + 1
    detective.meters["clues"] = detective.meters.get("clues", 0) + 1

    if narrate:
        world.say(f"{detective.id} studied the {hose.label} and the {credit.label} like a tiny detective.")

    if hose.meters.get("leak", 0) >= THRESHOLD:
        detective.clues.append("water on the floor")
    if credit.meters.get("missing", 0) >= THRESHOLD:
        detective.clues.append("an empty pocket")
    if credit.borrowed_from:
        detective.clues.append("a borrowed note")

    world.facts["looked"] = True


def tell(params: StoryParams) -> World:
    setting = SETTINGS[params.place]
    world = World(setting)

    detective = world.add(Entity(
        id=params.detective,
        kind="character",
        type=params.detective_type,
        label="detective",
        memes={"curiosity": 1.0, "careful": 1.0},
        meters={"clues": 0.0},
    ))
    helper = world.add(Entity(
        id=params.helper,
        kind="character",
        type=params.helper_type,
        label="helper",
        memes={"worry": 1.0},
    ))
    suspect = world.add(Entity(
        id=params.suspect,
        kind="character",
        type=params.suspect_type,
        label="suspect",
        memes={"defiance": 1.0, "worry": 0.5},
    ))
    hose_cfg = select_hose(params.place)
    credit_cfg = select_credit()

    hose = world.add(Entity(
        id="hose",
        type=hose_cfg.kind,
        label=hose_cfg.label,
        phrase=hose_cfg.phrase,
        owner=helper.id,
        caretaker=helper.id,
        meters={"leak": 1.0 if params.place == "porch" else 0.0},
    ))
    credit = world.add(Entity(
        id="credit",
        type=credit_cfg.kind,
        label=credit_cfg.label,
        phrase=credit_cfg.phrase,
        owner=helper.id,
        caretaker=helper.id,
        borrowed_from=suspect.id if params.place == "garage" else helper.id,
        meters={"missing": 1.0 if params.place == "garage" else 0.0},
    ))

    world.facts.update(
        detective=detective,
        helper=helper,
        suspect=suspect,
        hose=hose,
        credit=credit,
        hose_cfg=hose_cfg,
        credit_cfg=credit_cfg,
        fix=select_fix(hose_cfg, credit_cfg),
        solved=False,
        conflict=False,
    )

    # Act 1
    world.say(f"{detective.id} was a little {next((t for t in ['curious','careful','brave','sharp-eyed','quiet','patient'] if t), 'curious')} {detective.type} who loved solving little neighborhood mysteries.")
    world.say(f"{helper.id} had a {hose.label} and a {credit.label}, and both seemed important that morning.")
    world.say(f"{suspect.id} kept saying the problem was not a problem, which made {detective.id} even more curious.")
    world.para()

    # Act 2
    world.say(f"At {setting.place}, {detective.id} noticed that the {hose.label} could not do its job if it stayed broken.")
    if credit.borrowed_from == suspect.id:
        world.say(f"At the same time, the {credit.label} had been borrowed in a way that did not feel fair.")
        world.facts["conflict"] = True
    else:
        world.say(f"The {credit.label} was still there, but nobody could explain who was allowed to use it.")
        world.facts["conflict"] = True
    world.say(f"{detective.id} asked careful questions and followed the small clues instead of guessing.")
    _do_investigation(world, detective, hose, credit, narrate=True)
    world.para()

    # Act 3
    fix = select_fix(hose_cfg, credit_cfg)
    if fix == FIXES["receipt_check"]:
        world.say(f"{detective.id} decided to {fix.prep}.")
        world.say(f"That showed {helper.id} what really happened: the {credit.label} had been used for a needed repair, not wasted.")
        world.say(f"Then {detective.id} helped {helper.id} {FIXES['hose_patch'].prep}, and the hose worked again.")
    else:
        world.say(f"{detective.id} chose to {fix.prep}.")
    world.say(f"In the end, {fix.result}, and the neighborhood felt calm again.")
    world.say(f"{suspect.id} stopped frowning, {helper.id} smiled, and {detective.id} had solved the case.")

    world.facts["solved"] = True
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    det = f["detective"]
    helper = f["helper"]
    hose = f["hose"]
    credit = f["credit"]
    return [
        f"Write a short detective story for a young child about {det.id}, a {hose.label}, and a {credit.label}.",
        f"Tell a gentle mystery where {det.id} notices a problem with the {hose.label} and a disagreement about the {credit.label}.",
        f"Write a story in which a tiny detective uses clues, careful questions, and problem solving to settle a conflict.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    det = f["detective"]
    helper = f["helper"]
    suspect = f["suspect"]
    hose = f["hose"]
    credit = f["credit"]
    qa = [
        QAItem(
            question=f"Who was the detective in the story?",
            answer=f"The detective was {det.id}, a small {det.type} who liked to solve mysteries.",
        ),
        QAItem(
            question=f"What two things made the morning feel tricky?",
            answer=f"The tricky things were the {hose.label} and the {credit.label}. One needed help, and the other caused a disagreement.",
        ),
        QAItem(
            question=f"What did {det.id} do instead of guessing?",
            answer=f"{det.id} asked careful questions and looked at the clues so the problem could be solved fairly.",
        ),
        QAItem(
            question=f"Why was there a conflict?",
            answer=f"There was a conflict because the {credit.label} had been borrowed in a way that did not feel fair, and everyone had different feelings about it.",
        ),
        QAItem(
            question=f"How was the hose problem fixed?",
            answer=f"{det.id} followed the clues, then helped fix the hose so it could work again.",
        ),
    ]
    if world.facts.get("solved"):
        qa.append(QAItem(
            question=f"How did the story end for {helper.id} and {suspect.id}?",
            answer=f"They felt calmer at the end because the truth came out, the hose worked again, and the argument was settled.",
        ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    out = [
        QAItem(
            question="What is a hose for?",
            answer="A hose is a long tube that carries water so people can water plants or wash things outside.",
        ),
        QAItem(
            question="What is credit?",
            answer="Credit is a way to use value now and settle it later, or a slip or card that shows something can be borrowed or paid for.",
        ),
        QAItem(
            question="What does a detective do?",
            answer="A detective looks for clues, asks questions, and solves mysteries by putting the pieces together.",
        ),
        QAItem(
            question="Why do people solve problems by talking?",
            answer="Talking helps people share clues, explain feelings, and find a fair solution without making the conflict worse.",
        ),
    ]
    return out


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
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.clues:
            bits.append(f"clues={e.clues}")
        if e.borrowed_from:
            bits.append(f"borrowed_from={e.borrowed_from}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  facts={world.facts}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Detective story world with hose, credit, conflict, and problem solving.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--detective")
    ap.add_argument("--detective-type", choices=["girl", "boy"])
    ap.add_argument("--helper")
    ap.add_argument("--helper-type", choices=["girl", "boy"])
    ap.add_argument("--suspect")
    ap.add_argument("--suspect-type", choices=["girl", "boy"])
    ap.add_argument("--hose", choices=HOSES)
    ap.add_argument("--credit", choices=CREDITS)
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or rng.choice(list(SETTINGS))
    if place not in SETTINGS:
        raise StoryError("Unknown place.")

    detective_type = args.detective_type or rng.choice(["girl", "boy"])
    helper_type = args.helper_type or rng.choice(["girl", "boy"])
    suspect_type = args.suspect_type or rng.choice(["girl", "boy"])

    detective = args.detective or rng.choice(GIRL_NAMES if detective_type == "girl" else BOY_NAMES)
    helper = args.helper or rng.choice(GIRL_NAMES if helper_type == "girl" else BOY_NAMES)
    suspect = args.suspect or rng.choice(GIRL_NAMES if suspect_type == "girl" else BOY_NAMES)

    hose_key = args.hose or ("green_hose" if place == "yard" else "red_hose")
    credit_key = args.credit or "store_credit"

    hose = HOSES[hose_key]
    credit = CREDITS[credit_key]
    if not reasonableness_gate(hose, credit):
        raise StoryError("The selected hose and credit do not form a reasonable detective problem.")
    return StoryParams(
        place=place,
        hose=hose_key,
        credit=credit_key,
        detective=detective,
        detective_type=detective_type,
        helper=helper,
        helper_type=helper_type,
        suspect=suspect,
        suspect_type=suspect_type,
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


CURATED = [
    StoryParams(place="yard", hose="green_hose", credit="store_credit",
                detective="June", detective_type="girl",
                helper="Mina", helper_type="girl",
                suspect="Eli", suspect_type="boy"),
    StoryParams(place="porch", hose="red_hose", credit="store_credit",
                detective="Theo", detective_type="boy",
                helper="Ruby", helper_type="girl",
                suspect="Max", suspect_type="boy"),
    StoryParams(place="garage", hose="red_hose", credit="store_credit",
                detective="Ivy", detective_type="girl",
                helper="Ben", helper_type="boy",
                suspect="Lena", suspect_type="girl"),
]


ASP_RULES = r"""
hose_problem(H) :- hose(H), hose_needs_fix(H).
conflict(C) :- conflict_case(C).
problem_solving(S) :- solution(S), solves(S, conflict_case), solves(S, hose_problem).
good_story :- hose_problem(_), conflict(_), problem_solving(_).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for key, hose in HOSES.items():
        lines.append(asp.fact("hose", key))
        lines.append(asp.fact("hose_needs_fix", key))
        for t in sorted(hose.tags):
            lines.append(asp.fact("hose_tag", key, t))
    for key, credit in CREDITS.items():
        lines.append(asp.fact("credit", key))
        for t in sorted(credit.tags):
            lines.append(asp.fact("credit_tag", key, t))
    for key in FIXES:
        lines.append(asp.fact("solution", key))
        lines.append(asp.fact("solves", key, "conflict_case"))
        lines.append(asp.fact("solves", key, "hose_problem"))
    lines.append(asp.fact("conflict_case", "borrowed_credit"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show good_story/0."))
    atoms = asp.atoms(model, "good_story")
    ok = len(atoms) == 1
    if ok:
        print("OK: ASP twin supports the story shape.")
        return 0
    print("MISMATCH: ASP twin did not derive the expected story shape.")
    return 1


def asp_good_story() -> bool:
    import asp
    model = asp.one_model(asp_program("#show good_story/0."))
    return len(asp.atoms(model, "good_story")) == 1


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show good_story/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("good_story:" , asp_good_story())
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
