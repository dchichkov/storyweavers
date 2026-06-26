#!/usr/bin/env python3
"""
storyworlds/worlds/allow_pork_bravery_repetition_conflict_detective_story.py
=============================================================================

A small detective-story world built from the seed words "allow" and "pork",
with narrative features centered on bravery, repetition, and conflict.

The source tale imagined here:
---
A young detective notices that the community hall has a stern sign:
"No pork allowed." But every night, someone keeps leaving a warm pork roll
outside the kitchen door. The hall cook is upset, the caretaker is strict,
and the detective wants to find out who is sneaking in and why. The clue
is repeated again and again: a tiny muddy paw print, a soft tap-tap at the
same window, and the same neat ribbon tied around each roll.

The detective follows the repeated clues into a dark yard, faces a nervous
stray piglet, and learns the piglet is not stealing the pork at all. It is
bringing it from the butcher cart because it is trying to help. The detective
shows bravery, calms the conflict, and helps the cook and caretaker agree on
a safer plan.

World model:
---
Entities have physical meters and emotional memes. Physical clues can build up,
and emotional conflict can rise or settle through actions. Repetition matters
because the same clue appearing more than once strengthens the case. Bravery
matters because the detective can push into a risky place to test a theory.
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
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in {"piglet", "pig"}:
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str = "the community hall"
    after_dark: bool = True


@dataclass
class Clue:
    id: str
    label: str
    repeatable: bool
    kind: str  # "sound" | "print" | "object"
    detail: str


@dataclass
class CaseFile:
    suspect: str
    truth: str
    conflict_reason: str
    allow_plan: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.clues_seen: dict[str, int] = {}
        self.darkness: float = 1.0

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

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        clone.clues_seen = dict(self.clues_seen)
        clone.darkness = self.darkness
        return clone


@dataclass
class StoryParams:
    detective: str
    detective_type: str
    helper: str
    helper_type: str
    place: str
    suspect: str
    seed: Optional[int] = None


DETECTIVE_NAMES = ["Mina", "Toby", "Iris", "Jules", "Nico", "Pip"]
HELPER_NAMES = ["Nell", "June", "Otis", "Bram", "Lena", "Rufus"]


SETTINGS = {
    "hall": Setting(place="the community hall", after_dark=True),
    "market": Setting(place="the night market", after_dark=True),
    "kitchen": Setting(place="the kitchen corridor", after_dark=False),
}

CLUES = {
    "paw": Clue(
        id="paw",
        label="muddy paw print",
        repeatable=True,
        kind="print",
        detail="a tiny muddy paw print near the back step",
    ),
    "tap": Clue(
        id="tap",
        label="tap-tap at the window",
        repeatable=True,
        kind="sound",
        detail="a soft tap-tap that came again and again from the same window",
    ),
    "ribbon": Clue(
        id="ribbon",
        label="blue ribbon",
        repeatable=False,
        kind="object",
        detail="a blue ribbon tied neatly around the warm pork roll",
    ),
}

CASE_FILE = CaseFile(
    suspect="piglet",
    truth="a lonely piglet was carrying the pork roll to help the cook",
    conflict_reason="the hall caretaker thought someone was breaking the no-pork rule",
    allow_plan="the cook agreed to allow the pork rolls only for the late meal, with a signed note and a covered tray",
)


ASP_RULES = r"""
% A clue is strong when it repeats or when multiple clue kinds point to the same case.
strong_clue(C) :- clue(C), repeated(C).
strong_clue(C) :- clue(C), clue_kind(C, object).
strong_case :- strong_clue(paw), strong_clue(tap), clue_kind(ribbon, object).

% Bravery helps the detective enter a risky place and see the truth.
brave(D) :- detective(D), enters_dark_place(D), resolves_case(D).

% Conflict is real when the rule says "no pork allowed" and someone has a pork reason.
conflict :- no_pork_allowed, pork_present, needs_exception.

% An acceptable resolution exists if the helper and caretaker agree to allow it.
resolution :- allow_plan.
#show strong_case/0.
#show brave/1.
#show conflict/0.
#show resolution/0.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for cid, clue in CLUES.items():
        lines.append(asp.fact("clue", cid))
        lines.append(asp.fact("clue_kind", cid, clue.kind))
        if clue.repeatable:
            lines.append(asp.fact("repeated", cid))
    lines.append(asp.fact("detective", "detective"))
    lines.append(asp.fact("detective", "helper"))
    lines.append(asp.fact("no_pork_allowed"))
    lines.append(asp.fact("pork_present"))
    lines.append(asp.fact("needs_exception"))
    lines.append(asp.fact("allow_plan"))
    lines.append(asp.fact("enters_dark_place", "detective"))
    lines.append(asp.fact("resolves_case", "detective"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_results() -> list[tuple[str, ...]]:
    import asp
    model = asp.one_model(asp_program("#show strong_case/0. #show brave/1. #show conflict/0. #show resolution/0."))
    atoms = []
    for sym in model:
        if sym.name == "strong_case":
            atoms.append(("strong_case",))
        elif sym.name == "brave":
            atoms.append(("brave", sym.arguments[0].name))
        elif sym.name == "conflict":
            atoms.append(("conflict",))
        elif sym.name == "resolution":
            atoms.append(("resolution",))
    return atoms


def valid_story_combo(place: str, suspect: str) -> bool:
    return place in SETTINGS and suspect == "piglet"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A detective story world about allow, pork, bravery, repetition, and conflict."
    )
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--detective")
    ap.add_argument("--helper")
    ap.add_argument("--suspect", choices=["piglet"])
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or rng.choice(list(SETTINGS))
    detective = args.detective or rng.choice(DETECTIVE_NAMES)
    helper = args.helper or rng.choice(HELPER_NAMES)
    suspect = args.suspect or "piglet"
    if not valid_story_combo(place, suspect):
        raise StoryError("This detective case only works with the piglet suspect in one of the known settings.")
    return StoryParams(
        detective=detective,
        detective_type="girl" if detective in {"Mina", "Iris", "Lena"} else "boy",
        helper=helper,
        helper_type="girl" if helper in {"Nell", "June", "Lena"} else "boy",
        place=place,
        suspect=suspect,
    )


def _narrate_clue(world: World, clue_id: str) -> None:
    clue = CLUES[clue_id]
    count = world.clues_seen.get(clue_id, 0) + 1
    world.clues_seen[clue_id] = count
    if clue_id == "paw":
        if count == 1:
            world.say("Near the back step, the detective found a tiny muddy paw print.")
        else:
            world.say("The same muddy paw print appeared again by the side door.")
    elif clue_id == "tap":
        if count == 1:
            world.say("Then came a soft tap-tap at the window.")
        else:
            world.say("The tap-tap came again from the same window, just like before.")
    elif clue_id == "ribbon":
        world.say("Tied around the warm pork roll was a neat blue ribbon.")


def tell(setting: Setting, detective_name: str, helper_name: str, suspect: str) -> World:
    world = World(setting)
    det = world.add(Entity(id=detective_name, kind="character", type="boy" if detective_name not in {"Mina", "Iris", "Lena"} else "girl"))
    helpr = world.add(Entity(id=helper_name, kind="character", type="boy" if helper_name not in {"Nell", "June", "Lena"} else "girl"))
    piglet = world.add(Entity(id="piglet", kind="character", type="piglet", label="a small piglet"))
    pork_roll = world.add(Entity(id="pork_roll", type="thing", label="pork roll", phrase="a warm pork roll", owner="cook"))
    sign = world.add(Entity(id="sign", type="thing", label="sign", phrase='the sign that said "No pork allowed"'))
    cook = world.add(Entity(id="cook", kind="character", type="woman", label="the cook"))
    caretaker = world.add(Entity(id="caretaker", kind="character", type="man", label="the caretaker"))

    world.say(f"{detector_name(det)} was a young detective who loved hard questions and neat clues.")
    world.say(f"{det.pronoun('subject').capitalize()} worked beside {helper_name} at {world.setting.place}.")
    world.say(f"Everyone could read the sign that said, \"No pork allowed,\" and that made the kitchen uneasy.")
    world.say(f"Still, the cook kept finding {pork_roll.phrase} outside the door.")

    world.para()
    world.say("The case began with a strange pattern.")
    _narrate_clue(world, "paw")
    _narrate_clue(world, "tap")
    _narrate_clue(world, "paw")
    _narrate_clue(world, "tap")
    _narrate_clue(world, "ribbon")

    det.memes["curiosity"] = 1.0
    det.memes["bravery"] = 1.0
    helper.memes["worry"] = 1.0
    caretaker.memes["conflict"] = 1.0
    cook.memes["conflict"] = 1.0

    world.para()
    world.say(f"The caretaker said the rule must stay, because {CASE_FILE.conflict_reason}.")
    world.say(f"The cook frowned, because someone still had to bring dinner to the hall.")
    world.say(f"{det.pronoun('subject').capitalize()} knew this was the part that needed bravery.")
    world.say(f"So {det.pronoun('subject')} followed the repeated clues into the dark yard behind the hall.")

    world.darkness = 2.0
    det.meters["risk"] = 1.0
    det.memes["bravery"] += 1.0
    piglet.memes["fear"] = 1.0

    world.para()
    world.say("Behind the shed, the detective found the truth.")
    world.say("The piglet was not stealing the pork roll at all.")
    world.say("It had been nudging the cart because it wanted to help carry dinner to the kitchen door.")
    world.say("The blue ribbon had marked the roll so the cook would know it was meant for the late meal.")

    helper.memes["understanding"] = 1.0
    cook.memes["relief"] = 1.0
    caretaker.memes["conflict"] = 0.0
    cook.memes["conflict"] = 0.0
    det.memes["confidence"] = 1.0

    world.para()
    world.say(f"{det.pronoun('subject').capitalize()} explained the clues one by one, and the room grew quiet.")
    world.say(f"At last, the cook agreed to allow the pork rolls only for the late meal, with a covered tray and a signed note.")
    world.say(f"The caretaker nodded, because the new plan still respected the rule while making room for kindness.")
    world.say(f"That night, the same hall felt calmer, and the little piglet walked proudly beside the detective instead of hiding in the dark.")

    world.facts.update(
        detective=det,
        helper=helpr,
        piglet=piglet,
        pork_roll=pork_roll,
        sign=sign,
        cook=cook,
        caretaker=caretaker,
        case=CASE_FILE,
        setting=setting,
    )
    return world


def detector_name(det: Entity) -> str:
    return det.id


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    det: Entity = f["detective"]
    return [
        "Write a short detective story for a child about a rule, a repeated clue, and a brave investigation.",
        f"Tell a mystery about {det.id} where the words 'allow' and 'pork' matter to the case.",
        "Write a gentle detective tale where the same clue appears more than once and the conflict ends with a fair plan.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    det: Entity = f["detective"]
    helper: Entity = f["helper"]
    return [
        QAItem(
            question=f"Who was the detective in the story?",
            answer=f"The detective was {det.id}, a curious young sleuth who kept following the same clues.",
        ),
        QAItem(
            question=f"Why was there conflict about the pork?",
            answer=(
                "There was conflict because the hall had a rule that pork was not allowed, "
                "but the cook still needed to understand who was bringing the pork rolls and why."
            ),
        ),
        QAItem(
            question="Which clue was repeated more than once?",
            answer="The muddy paw print and the tap-tap at the window both showed up again and again, which helped make the case clear.",
        ),
        QAItem(
            question=f"How did {det.id} show bravery?",
            answer=(
                f"{det.id} showed bravery by going into the dark yard after the repeated clues, "
                "instead of stopping when things felt spooky."
            ),
        ),
        QAItem(
            question=f"How did the story end for {helper.id} and the caretaker?",
            answer="They agreed on a safer plan that still respected the rule and allowed the pork rolls for the late meal.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does it mean to allow something?",
            answer="To allow something means to let it happen or to say yes to it.",
        ),
        QAItem(
            question="What is pork?",
            answer="Pork is meat that comes from a pig.",
        ),
        QAItem(
            question="Why can repetition help in a mystery?",
            answer="Repetition can help because when the same clue appears again, it can show that the clue is important.",
        ),
        QAItem(
            question="What is bravery?",
            answer="Bravery is being willing to do something hard or scary when it matters.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        m = {k: v for k, v in e.meters.items() if v}
        n = {k: v for k, v in e.memes.items() if v}
        lines.append(f"{e.id}: kind={e.kind} type={e.type} meters={m} memes={n}")
    lines.append(f"clues_seen={world.clues_seen}")
    return "\n".join(lines)


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show strong_case/0. #show brave/1. #show conflict/0. #show resolution/0."))
    shown = set()
    for sym in model:
        if sym.name == "strong_case":
            shown.add(("strong_case",))
        elif sym.name == "brave":
            shown.add(("brave", sym.arguments[0].name))
        elif sym.name == "conflict":
            shown.add(("conflict",))
        elif sym.name == "resolution":
            shown.add(("resolution",))
    expected = {("strong_case",), ("brave", "detective"), ("conflict",), ("resolution",)}
    if shown != expected:
        print("MISMATCH between ASP and Python expectations:")
        print("  ASP:", sorted(shown))
        print("  PY :", sorted(expected))
        return 1
    print("OK: ASP parity verified.")
    return 0


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], params.detective, params.helper, params.suspect)
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
    StoryParams(detective="Mina", detective_type="girl", helper="Nell", helper_type="girl", place="hall", suspect="piglet"),
    StoryParams(detective="Toby", detective_type="boy", helper="Bram", helper_type="boy", place="market", suspect="piglet"),
    StoryParams(detective="Iris", detective_type="girl", helper="Otis", helper_type="boy", place="kitchen", suspect="piglet"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show strong_case/0. #show brave/1. #show conflict/0. #show resolution/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show strong_case/0. #show brave/1. #show conflict/0. #show resolution/0."))
        print("ASP model:")
        for sym in model:
            print(sym)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            params = resolve_params(args, random.Random(base_seed + i))
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

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
