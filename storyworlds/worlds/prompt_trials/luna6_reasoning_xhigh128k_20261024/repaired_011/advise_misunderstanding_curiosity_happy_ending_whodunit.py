#!/usr/bin/env python3
"""
A small, stand-alone whodunit storyworld about curiosity, mistaken clues, and kind advice.

A child and a friend are preparing for a special event when an important object
goes missing. A clue points toward the wrong person, but a careful question and
a second clue reveal who moved it—and why.
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class StoryParams:
    kid: str
    friend: str
    suspect: str
    mentor: str
    case_id: str
    seed: Optional[int] = None


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    label: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "character":
            return {
                "subject": "they",
                "object": "them",
                "possessive": "their",
            }[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


KIDS = ["Mina", "Theo", "Lila", "Jun", "Ari", "Zoe"]
FRIENDS = ["Pip", "Max", "Bea", "Omar", "Tess", "Ravi"]
SUSPECTS = ["Nora", "Eli", "Uma", "Cal", "Rosa", "Finn"]
MENTORS = ["Gran Jo", "Aunt May", "Mr. Sol", "Coach Imani"]

CASES = [
    {
        "id": "moon_key",
        "title": "The Missing Moon Key",
        "place": "the Willow Library puppet room",
        "event": "the moon puppet show",
        "item": "brass moon key",
        "opening": (
            "At {place}, {kid} and {friend} were setting up for {event}. "
            "The {item} was needed to unlock the little trunk where the puppets "
            "waited, but its hook beside the trunk was empty."
        ),
        "misleading": "A blue thread clung to the empty hook.",
        "comparison": "It was the same shade as {suspect}'s scarf.",
        "accusation": (
            "That thread looks like your scarf, {suspect}. Did you move the key?"
        ),
        "suspect_activity": "holding the blue curtain open",
        "source": (
            "The frayed end matched a loose tassel on the curtain, not "
            "{suspect}'s scarf."
        ),
        "true_clue": (
            "When {kid} lifted the dragon puppet, its pocket sagged, and "
            "something inside gave a tiny metallic clink."
        ),
        "discovery": (
            "The brass moon key was tucked inside the dragon puppet's pocket."
        ),
        "friend_action": (
            "slipped the key into the dragon puppet's pocket"
        ),
        "friend_reason": (
            "the hook was wobbling and I was afraid the key would fall"
        ),
        "found_at": "inside the dragon puppet's pocket",
        "recovery": (
            "Together, they took the brass moon key from the dragon puppet's "
            "pocket and hung it on a steady hook."
        ),
        "ending": (
            "The key turned in the trunk's little lock. When the curtain opened, "
            "the dragon puppet bowed as if it had solved the mystery, too."
        ),
        "reason_qa": "the hook was wobbling, and the key might have fallen",
        "mislead_qa": "a blue thread that looked like the scarf {suspect} wore",
        "source_qa": "a loose tassel on the curtain",
        "true_qa": "the dragon puppet's pocket sagged and made a little metallic clink",
        "resolution_qa": (
            "The key was safe in the dragon puppet's pocket, where {friend} had "
            "put it because the hook was wobbling."
        ),
    },
    {
        "id": "garden_bell",
        "title": "The Picnic Bell Mystery",
        "place": "the Lantern Garden picnic lawn",
        "event": "a story picnic",
        "item": "silver story bell",
        "opening": (
            "On the Lantern Garden lawn, {kid} and {friend} were arranging a "
            "blanket for {event}. The {item} was supposed to ring when everyone "
            "was ready for the first tale, but its place by the blanket was empty."
        ),
        "misleading": "Four damp marks crossed the grass beside the blanket.",
        "comparison": "They looked like tracks from {suspect}'s muddy boots.",
        "accusation": (
            "Those marks look like your boots, {suspect}. Did you move the bell?"
        ),
        "suspect_activity": "watering the marigolds beyond the blanket",
        "source": (
            "Each mark had four soft toe pads and no boot heel; Puddle, the "
            "garden cat, had crossed the grass."
        ),
        "true_clue": (
            "A breeze lifted the picnic basket's cloth handle, and a faint "
            "silver chime sounded from underneath it."
        ),
        "discovery": (
            "The silver story bell was tucked beneath the basket's folded liner."
        ),
        "friend_action": "put the bell in the picnic basket",
        "friend_reason": (
            "the blanket was sliding toward the hill and I wanted the bell to "
            "stay safe"
        ),
        "found_at": "beneath the picnic basket's folded liner",
        "recovery": (
            "They lifted the basket and found the silver story bell beneath its "
            "folded liner."
        ),
        "ending": (
            "The bell rang out over the garden, and the first story began while "
            "Puddle curled up in a sunny patch beside the blanket."
        ),
        "reason_qa": (
            "the blanket was sliding toward the hill, and the bell needed to "
            "stay safe"
        ),
        "mislead_qa": "damp marks that looked like muddy boot tracks",
        "source_qa": "Puddle the garden cat's paw prints",
        "true_qa": "a faint silver chime came from beneath the picnic basket's handle",
        "resolution_qa": (
            "The bell was beneath the picnic basket's liner. {friend} had put it "
            "there to keep it safe when the blanket began sliding."
        ),
    },
    {
        "id": "paper_crown",
        "title": "The Crown in the Folder",
        "place": "the Maple School art room",
        "event": "a puppet parade",
        "item": "gold paper crown",
        "opening": (
            "In the Maple School art room, {kid} and {friend} were preparing "
            "for {event}. The {item} was meant to crown the paper king at the "
            "parade's start, but the dry table beside the paint pots was bare."
        ),
        "misleading": "Bright silver glitter sparkled around the empty spot.",
        "comparison": "Matching glitter clung to {suspect}'s sleeves.",
        "accusation": (
            "Your sleeves have the same glitter, {suspect}. Did you take the crown?"
        ),
        "suspect_activity": "cutting silver stars from scraps of parade paper",
        "source": (
            "The glitter was scattered across the star-paper scraps in the art "
            "tray, just like the glitter on {suspect}'s sleeves."
        ),
        "true_clue": (
            "A crisp golden point peeked from between the pages of a green "
            "folder, safely away from the wet paint."
        ),
        "discovery": "The gold paper crown lay flat inside the green folder.",
        "friend_action": "slid the crown into the green folder",
        "friend_reason": (
            "a splash of blue paint was about to reach it and I wanted to keep "
            "it dry"
        ),
        "found_at": "inside the green folder",
        "recovery": (
            "They opened the green folder and lifted out the gold paper crown, "
            "still perfectly dry."
        ),
        "ending": (
            "The paper king wore the crown in the parade, where every silver "
            "star glittered in the sunshine."
        ),
        "reason_qa": (
            "a splash of blue paint was about to reach the crown, and "
            "{friend} wanted to keep it dry"
        ),
        "mislead_qa": "silver glitter that also appeared on {suspect}'s sleeves",
        "source_qa": "the silver star-paper scraps in the art tray",
        "true_qa": "a golden point peeking from inside the green folder",
        "resolution_qa": (
            "The crown was safe inside the green folder. {friend} had put it "
            "there to protect it from a splash of blue paint."
        ),
    },
    {
        "id": "wooden_duck",
        "title": "The Duck on the Drying Shelf",
        "place": "the Cedar Shed garden club",
        "event": "a pond-side treasure game",
        "item": "carved wooden duck token",
        "opening": (
            "At the Cedar Shed garden club, {kid} and {friend} were laying out "
            "{event}. The {item} marked the first turn on the treasure map, "
            "but it had vanished from the map's upper corner."
        ),
        "misleading": "Pale sawdust dusted the ground beside the map.",
        "comparison": "It seemed to match the sawdust on {suspect}'s shirt.",
        "accusation": (
            "The sawdust on your shirt matches this, {suspect}. Did you move "
            "the duck?"
        ),
        "suspect_activity": "carrying wooden signboards to the shed",
        "source": (
            "The sawdust was fresh from the signboards {suspect} had carried; "
            "it was not a trail from the missing token."
        ),
        "true_clue": (
            "A curly wood shaving and a tiny dot of glue led toward the sunny "
            "drying shelf."
        ),
        "discovery": (
            "The carved wooden duck rested on the sunny shelf with its little "
            "beak freshly mended."
        ),
        "friend_action": "carried the duck to the sunny drying shelf",
        "friend_reason": (
            "its beak was chipped, so I glued it and set it out to dry"
        ),
        "found_at": "on the sunny drying shelf",
        "recovery": (
            "They brought the carved wooden duck back from the sunny drying "
            "shelf, taking care not to touch its fresh repair."
        ),
        "ending": (
            "When the glue dried, the duck pointed its beak down the first "
            "dotted trail, and the treasure game began."
        ),
        "reason_qa": (
            "the duck's beak was chipped, and {friend} had glued it so it could "
            "dry safely"
        ),
        "mislead_qa": "sawdust that seemed to match the dust on {suspect}'s shirt",
        "source_qa": "the wooden signboards {suspect} had carried",
        "true_qa": "a curly wood shaving and a dot of glue leading to the drying shelf",
        "resolution_qa": (
            "The duck was on the sunny drying shelf. {friend} had taken it there "
            "to mend its chipped beak and let the glue dry."
        ),
    },
]

CASE_BY_ID = {case["id"]: case for case in CASES}

ASP_RULES = r"""
role_name(N) :- kid_name(N).
role_name(N) :- friend_name(N).
role_name(N) :- suspect_name(N).

valid(K, F, S, C) :-
    kid_name(K),
    friend_name(F),
    suspect_name(S),
    case_record(C),
    K != F,
    K != S,
    F != S.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for name in KIDS:
        lines.append(asp.fact("kid_name", name))
    for name in FRIENDS:
        lines.append(asp.fact("friend_name", name))
    for name in SUSPECTS:
        lines.append(asp.fact("suspect_name", name))
    for case in CASES:
        case_id = case["id"]
        lines.append(asp.fact("case_record", case_id))
        lines.append(asp.fact("case_item", case_id, case["item"]))
        lines.append(asp.fact("case_place", case_id, case["place"]))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for kid in KIDS:
        for friend in FRIENDS:
            for suspect in SUSPECTS:
                if len({kid, friend, suspect}) != 3:
                    continue
                for case in CASES:
                    combos.append((kid, friend, suspect, case["id"]))
    return combos


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def validate_params(params: StoryParams) -> None:
    if params.kid not in KIDS:
        raise StoryError(f"Unknown child investigator: {params.kid!r}.")
    if params.friend not in FRIENDS:
        raise StoryError(f"Unknown friend: {params.friend!r}.")
    if params.suspect not in SUSPECTS:
        raise StoryError(f"Unknown suspect: {params.suspect!r}.")
    if params.mentor not in MENTORS:
        raise StoryError(f"Unknown adviser: {params.mentor!r}.")
    if params.case_id not in CASE_BY_ID:
        raise StoryError(f"Unknown mystery case: {params.case_id!r}.")
    if len({params.kid, params.friend, params.suspect}) != 3:
        raise StoryError(
            "The investigator, friend, and initially suspected person must be "
            "three different characters."
        )


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    params = StoryParams(
        kid=args.kid or rng.choice(KIDS),
        friend=args.friend or rng.choice(FRIENDS),
        suspect=args.suspect or rng.choice(SUSPECTS),
        mentor=args.mentor or rng.choice(MENTORS),
        case_id=args.case or rng.choice(CASES)["id"],
        seed=args.seed,
    )
    validate_params(params)
    return params


def apply_seeded_structure(
    params: StoryParams, seed: int, *, fixed_case: bool = False
) -> None:
    if not fixed_case:
        params.case_id = CASES[seed % len(CASES)]["id"]


def generate(params: StoryParams) -> StorySample:
    validate_params(params)
    case = CASE_BY_ID[params.case_id]
    values = {
        "kid": params.kid,
        "friend": params.friend,
        "suspect": params.suspect,
        "mentor": params.mentor,
        "place": case["place"],
        "event": case["event"],
        "item": case["item"],
    }

    world = World()
    kid = world.add(
        Entity(
            id="kid",
            kind="character",
            label=params.kid,
            meters={"attention": 0.35, "confidence": 0.35},
            memes={"curiosity": 0.45, "worry": 0.55},
        )
    )
    friend = world.add(
        Entity(
            id="friend",
            kind="character",
            label=params.friend,
            meters={"distance_from_clue": 0.4},
            memes={"helpfulness": 0.8, "worry": 0.25},
        )
    )
    suspect = world.add(
        Entity(
            id="suspect",
            kind="character",
            label=params.suspect,
            meters={"distance_from_false_clue": 0.2},
            memes={"unfair_suspicion": 0.8, "trust": 0.6},
        )
    )
    mentor = world.add(
        Entity(
            id="mentor",
            kind="character",
            label=params.mentor,
            meters={"distance_from_group": 0.1},
            memes={"patience": 0.9, "kindness": 0.9},
        )
    )
    item = world.add(
        Entity(
            id="missing_item",
            kind="object",
            label=case["item"],
            meters={"at_station": 1.0, "recovered": 0.0},
            memes={"importance": 0.8, "mystery": 0.7},
        )
    )
    place = world.add(
        Entity(
            id="setting",
            kind="place",
            label=case["place"],
            meters={"event_ready": 0.6},
            memes={"coziness": 0.8, "tension": 0.0},
        )
    )
    false_clue = world.add(
        Entity(
            id="misleading_clue",
            kind="clue",
            label=case["misleading"],
            meters={"reliability": 0.25},
            memes={"suspicion": 0.75},
        )
    )
    true_clue = world.add(
        Entity(
            id="helpful_clue",
            kind="clue",
            label=case["true_clue"],
            meters={"reliability": 0.0},
            memes={"curiosity": 0.0},
        )
    )

    world.say(case["opening"].format(**values))
    world.say(
        f"{case['misleading'].format(**values)} "
        f"{case['comparison'].format(**values)}"
    )

    world.para()
    place.memes["tension"] = 0.75
    suspect.memes["unfair_suspicion"] = 1.0
    kid.memes["curiosity"] = 0.65
    kid.memes["worry"] = 0.8
    false_clue.meters["noticed"] = 1.0

    accusation = case["accusation"].format(**values)
    world.say(f"{params.kid} leaned closer. “{accusation}”")
    world.say(
        f"{params.suspect} shook their head. “I didn't move it. "
        f"I was {case['suspect_activity']}; let's check before we decide.”"
    )
    world.say(
        f"{params.mentor} spoke gently. “I advise you to test the clue and "
        f"ask kindly before you accuse anyone.”"
    )
    world.say(
        f"{params.kid} nodded. “You're right. {params.suspect}, may I check "
        f"where it came from?”"
    )
    world.say(f"{params.suspect} answered, “Of course. Look closely.”")
    world.say(case["source"].format(**values))

    false_clue.meters["reliability"] = 0.0
    false_clue.memes["suspicion"] = 0.0
    suspect.memes["unfair_suspicion"] = 0.0
    kid.meters["attention"] = 0.9
    kid.memes["curiosity"] = 0.9
    kid.memes["worry"] = 0.45
    world.say(
        f"{params.kid} let out a breath. “That clue wasn't proof. "
        f"Let's keep looking.”"
    )

    world.para()
    true_clue.meters["reliability"] = 0.9
    true_clue.memes["curiosity"] = 0.9
    world.say(case["true_clue"].format(**values))
    world.say(case["discovery"].format(**values))
    world.say(
        f"{params.kid} turned to {params.friend}. “Did you move the "
        f"{case['item']}?”"
    )
    world.say(
        f"{params.friend} nodded. “Yes. I {case['friend_action']}, because "
        f"{case['friend_reason']}. I meant to tell you, but I forgot.”"
    )
    world.say(
        f"{params.kid} smiled. “Thanks for telling us. Let's put it back "
        f"before everyone arrives.”"
    )
    world.say(case["recovery"].format(**values))
    world.say(case["ending"].format(**values))

    item.meters["at_station"] = 0.0
    item.meters["recovered"] = 1.0
    item.memes["mystery"] = 0.0
    friend.memes["worry"] = 0.0
    friend.memes["helpfulness"] = 1.0
    suspect.memes["trust"] = 0.9
    kid.meters["confidence"] = 0.9
    kid.memes["worry"] = 0.0
    place.meters["event_ready"] = 1.0
    place.memes["tension"] = 0.0

    world.facts.update(
        kid=params.kid,
        friend=params.friend,
        initially_suspected=params.suspect,
        mentor=params.mentor,
        case_id=params.case_id,
        item=case["item"],
        setting=case["place"],
        false_lead=case["misleading"],
        false_lead_source=case["source"],
        true_clue=case["true_clue"],
        mover=params.friend,
        method=case["friend_action"],
        reason=case["reason_qa"],
        found_at=case["found_at"],
        resolved=True,
    )

    prompts = [
        (
            "Write a cozy child-friendly whodunit in which a curious child follows "
            "clues, receives kind advice, and solves a small misunderstanding."
        ),
        (
            f"Tell a complete mystery about {params.kid} and {params.friend} "
            f"preparing for {case['event']} when the {case['item']} goes missing."
        ),
        (
            f"Include a misleading clue about {params.suspect}, a spoken piece of "
            f"advice, a fair investigation, and a happy ending."
        ),
    ]

    story_qa = [
        QAItem(
            question="What was missing?",
            answer=(
                f"The {case['item']} was missing just before {case['event']}. "
                f"It mattered because it was needed {case['purpose']}."
            ),
        ),
        QAItem(
            question=f"Why did {params.kid} first suspect {params.suspect}?",
            answer=(
                f"At first, {params.kid} suspected {params.suspect} because "
                f"{case['mislead_qa'].format(**values)}. A closer look showed "
                f"that the clue came from {case['source_qa']}, not from "
                f"{params.suspect}."
            ),
        ),
        QAItem(
            question=f"What did {params.mentor} advise {params.kid} to do?",
            answer=(
                f"{params.mentor} advised {params.kid} to test the clue and ask "
                "kindly before accusing anyone. That helped everyone check the "
                "evidence without blaming the wrong person."
            ),
        ),
        QAItem(
            question="What clue helped solve the mystery?",
            answer=(
                f"The useful clue was that {case['true_qa']}. It led the friends "
                f"to look in the right place."
            ),
        ),
        QAItem(
            question="Who moved the missing object, and why?",
            answer=(
                f"{params.friend} had moved the {case['item']}. "
                f"{case['resolution_qa'].format(**values)}"
            ),
        ),
    ]

    world_qa = [
        QAItem(
            question="What is a whodunit?",
            answer=(
                "A whodunit is a mystery story where someone follows clues to "
                "figure out who did something and what happened."
            ),
        ),
        QAItem(
            question="Why should a person check a clue before blaming someone?",
            answer=(
                "A clue can have more than one explanation, so checking it can "
                "prevent an unfair accusation."
            ),
        ),
        QAItem(
            question="What does curiosity help a detective do?",
            answer=(
                "Curiosity helps a detective notice details, ask questions, and "
                "look for evidence that explains what happened."
            ),
        ),
        QAItem(
            question="What is a misunderstanding?",
            answer=(
                "A misunderstanding happens when someone gets the wrong idea "
                "about a person or an event."
            ),
        ),
        QAItem(
            question="How can advice help during a mystery?",
            answer=(
                "Helpful advice can remind someone to stay calm, ask kindly, and "
                "check the facts before deciding what happened."
            ),
        ),
    ]

    return StorySample(
        params=params,
        story=world.render(),
        prompts=prompts,
        story_qa=story_qa,
        world_qa=world_qa,
        world=world,
    )


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, prompt in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {prompt}")
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
    for entity in world.entities.values():
        details = []
        if entity.meters:
            details.append(f"meters={entity.meters}")
        if entity.memes:
            details.append(f"memes={entity.memes}")
        lines.append(
            f"  {entity.id:18} ({entity.kind:10}) "
            f"{entity.label}: {' '.join(details)}"
        )
    if world.facts:
        lines.append(f"  facts: {world.facts}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "A cozy whodunit storyworld about advice, curiosity, and a "
            "misunderstanding."
        )
    )
    parser.add_argument("--kid", choices=KIDS)
    parser.add_argument("--friend", choices=FRIENDS)
    parser.add_argument("--suspect", choices=SUSPECTS)
    parser.add_argument("--mentor", choices=MENTORS)
    parser.add_argument("--case", choices=[case["id"] for case in CASES])
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def asp_verify() -> int:
    try:
        python_combos = set(valid_combos())
        clingo_combos = set(asp_valid_combos())
    except Exception as exc:
        print(f"Could not verify the ASP twin: {exc}")
        return 1

    if python_combos != clingo_combos:
        print("MISMATCH between the Python reasonableness gate and clingo:")
        if python_combos - clingo_combos:
            print("  only in Python:", sorted(python_combos - clingo_combos))
        if clingo_combos - python_combos:
            print("  only in clingo:", sorted(clingo_combos - python_combos))
        return 1

    for params in build_curated():
        sample = generate(params)
        if not sample.world or not sample.world.facts.get("resolved"):
            print(f"Generated story did not resolve: {params.case_id}")
            return 1
        if sample.story.count("“") < 6:
            print(f"Generated story is missing spoken dialogue: {params.case_id}")
            return 1
        if "advise" not in sample.story.lower():
            print(f"Generated story is missing the advice turn: {params.case_id}")
            return 1
        if not sample.story.endswith(CASE_BY_ID[params.case_id]["ending"].format(
            kid=params.kid,
            friend=params.friend,
            suspect=params.suspect,
            mentor=params.mentor,
            place=CASE_BY_ID[params.case_id]["place"],
            event=CASE_BY_ID[params.case_id]["event"],
            item=CASE_BY_ID[params.case_id]["item"],
        )):
            print(f"Generated story is missing its ending: {params.case_id}")
            return 1

    print(
        "OK: clingo matches the Python gate "
        f"({len(python_combos)} valid role-and-case combinations), "
        "and all curated stories include dialogue, advice, and a resolution."
    )
    return 0


def build_curated() -> list[StoryParams]:
    return [
        StoryParams(
            kid="Mina",
            friend="Pip",
            suspect="Eli",
            mentor="Gran Jo",
            case_id="moon_key",
        ),
        StoryParams(
            kid="Theo",
            friend="Bea",
            suspect="Nora",
            mentor="Aunt May",
            case_id="garden_bell",
        ),
        StoryParams(
            kid="Lila",
            friend="Max",
            suspect="Cal",
            mentor="Mr. Sol",
            case_id="paper_crown",
        ),
        StoryParams(
            kid="Jun",
            friend="Ravi",
            suspect="Uma",
            mentor="Coach Imani",
            case_id="wooden_duck",
        ),
    ]


CURATED = build_curated()


def emit(
    sample: StorySample,
    *,
    trace: bool = False,
    qa: bool = False,
    header: str = "",
) -> None:
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
        print(asp_program("#show valid/4."))
        return
    if args.verify:
        raise SystemExit(asp_verify())
    if args.asp:
        try:
            combos = asp_valid_combos()
        except Exception as exc:
            print(f"Could not solve the ASP twin: {exc}", file=sys.stderr)
            raise SystemExit(1)
        print(
            f"{len(combos)} reasonable (child, friend, suspect, case) "
            "combinations."
        )
        print("Mysteries:")
        for case in CASES:
            print(f"  {case['title']}: {case['item']} at {case['place']}")
        return
    if args.n < 1 and not args.all:
        print("No story: -n must be at least 1.", file=sys.stderr)
        raise SystemExit(2)

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    try:
        if args.all:
            samples = [generate(params) for params in CURATED]
        else:
            for offset in range(args.n):
                seed = base_seed + offset
                params = resolve_params(args, random.Random(seed))
                params.seed = seed
                apply_seeded_structure(
                    params,
                    seed,
                    fixed_case=args.case is not None,
                )
                samples.append(generate(params))
    except StoryError as exc:
        print(f"No story: {exc}", file=sys.stderr)
        raise SystemExit(2)

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(
                json.dumps(
                    [sample.to_dict() for sample in samples],
                    indent=2,
                    ensure_ascii=False,
                )
            )
        return

    for index, sample in enumerate(samples):
        header = ""
        if args.all:
            case = CASE_BY_ID[sample.params.case_id]
            header = f"### {case['title']}"
        elif len(samples) > 1:
            header = f"### variant {index + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
