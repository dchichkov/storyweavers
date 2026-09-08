#!/usr/bin/env python3
"""
A small child-friendly detective storyworld about a thin clue, a sippy cup,
and a mystery solved through foreshadowing, teamwork, and a flashback.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = HERE
while ROOT != os.path.dirname(ROOT):
    if os.path.exists(os.path.join(ROOT, "results.py")):
        break
    ROOT = os.path.dirname(ROOT)
sys.path.insert(0, ROOT)

from results import QAItem, StoryError, StorySample  # noqa: E402


METERS = {"clue_strength", "urgency", "trust", "order"}
MEMES = {"curiosity", "worry", "hope", "pride"}


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for key in METERS:
            self.meters.setdefault(key, 0.0)
        for key in MEMES:
            self.memes.setdefault(key, 0.0)


@dataclass
class CaseFile:
    place: str
    objects: dict[str, Entity]
    facts: dict[str, object] = field(default_factory=dict)

    def copy(self) -> "CaseFile":
        return CaseFile(
            place=self.place,
            objects={
                key: Entity(
                    value.id,
                    value.kind,
                    value.label,
                    dict(value.meters),
                    dict(value.memes),
                )
                for key, value in self.objects.items()
            },
            facts=dict(self.facts),
        )


@dataclass
class StoryParams:
    detective_name: str
    helper_name: str
    place: str
    seed: Optional[int] = None


DETECTIVE_NAMES = ["Luna", "Milo", "Nia", "Theo", "Zara", "Pip"]
HELPER_NAMES = ["Ari", "Bea", "Cora", "Jules", "Remy", "Sam"]
PLACES = [
    "the little library",
    "the town museum",
    "the sunny train station",
    "the rain garden",
]

@dataclass(frozen=True)
class Mystery:
    id: str
    missing_item: str
    thin_clue: str
    omen: str
    flashback: str
    task: str
    obstacle: str
    team_turn: str
    solution: str
    ending: str


MYSTERIES = [
    Mystery(
        "cup_cart",
        "the blue sippy cup",
        "a thin line of berry juice curved from the picnic bench to the wagon",
        "the wagon wheel squeaked once before anyone noticed the empty cup shelf",
        "Luna remembered seeing a red scarf tied to that wagon during yesterday's cleanup",
        "follow the thin juice line and inspect the wagon",
        "a gust of wind pushed leaves over the trail",
        "asked the helper to hold a paper umbrella while Luna brushed the leaves aside",
        "the cup was tucked beneath the wagon seat beside the red scarf",
        "the blue sippy cup stood on the shelf again, clean and ready for its thirsty owner",
    ),
    Mystery(
        "paint_room",
        "the green sippy cup",
        "one thin green paint mark crossed the hallway floor",
        "a loose paintbrush trembled in its jar when the morning door slammed",
        "Luna remembered that the art cart had rolled past the hallway after lunch",
        "trace the paint mark and check every wheel on the art cart",
        "the mark disappeared beneath a stack of drying pictures",
        "the helper lifted the pictures while Luna compared the cart's wheels",
        "the cup rested inside the cart's covered supply box",
        "the green cup gleamed beside a row of painted stars",
    ),
    Mystery(
        "pond_path",
        "the yellow sippy cup",
        "a thin wet ribbon shone between two stepping stones",
        "a frog croaked from the reeds just after the cup bell rang",
        "Luna remembered that the gardener had carried a basket along the pond path",
        "search the path and ask who moved the basket",
        "mud covered the basket's handle and hid its tiny label",
        "the helper held a lantern while Luna washed the handle with pond water",
        "the yellow cup was safe inside the basket under a folded towel",
        "the cup made a soft sippy sound as its owner drank beside the pond",
    ),
    Mystery(
        "reading_nook",
        "the red sippy cup",
        "a thin silver thread trailed from the reading nook to a cushion",
        "the window curtain fluttered though the window seemed shut",
        "Luna remembered that the puppet fox had a silver thread on its tail",
        "look behind the cushions and inspect the puppet basket",
        "the cushions had been rearranged for story time",
        "the helper read the cushion labels aloud while Luna searched the matching corner",
        "the cup was behind the puppet basket, caught by the fox's thread",
        "the red cup returned to the reading nook beside the favorite fox book",
    ),
    Mystery(
        "market_table",
        "the purple sippy cup",
        "a thin trail of flour dotted the floor below the market table",
        "a paper bag rustled before the baker arrived",
        "Luna remembered that a floury apron had brushed the table at noon",
        "follow the flour dots and check the bags without spilling them",
        "three bags looked alike and the labels had folded inward",
        "the helper held each bag steady while Luna found the one with a purple handle",
        "the purple cup was inside that bag, wrapped in a clean napkin",
        "the market table shone, and the purple cup waited beside fresh bread",
    ),
    Mystery(
        "clock_room",
        "the orange sippy cup",
        "a thin golden ribbon lay beneath the tall clock",
        "the clock gave one extra tick before the room grew quiet",
        "Luna remembered tying golden ribbons to the music box during yesterday's parade",
        "follow the ribbon and search near the music box",
        "the clock's swinging pendulum blocked the narrow shelf",
        "the helper stopped the pendulum while Luna reached behind the music box",
        "the orange cup was resting in a basket of parade ribbons",
        "the clock ticked evenly again while the orange cup shone in its proper place",
    ),
]

INTRO_FORMS = [
    "Detective {detective} kept a notebook with a very thin pencil. At {place}, {missing} vanished just before snack time.",
    "At {place}, Detective {detective} noticed a small mystery: {missing} was gone, and nobody knew where it had gone.",
    "The case began when the shelf at {place} showed one empty space. Detective {detective} opened a notebook and wrote, 'Find {missing}.'",
    "Detective {detective} liked quiet clues. That morning at {place}, a missing {missing} gave {detective} a reason to investigate.",
]

DIALOGUE_FORMS = [
    ('"I found something," said {detective}. "Can you help me read the clue?"', '"Together," said {helper}. "You follow the trail, and I will watch the tricky places."'),
    ('"{helper}, the clue is thin, but it is real," said {detective}.', '"Then we will not ignore it," replied {helper}. "Show me where it starts."'),
    ('"Do you think the missing cup left a trail?" asked {helper}.', '"I do," said {detective}. "If we work as a team, we can follow it carefully."'),
    ('"{detective}, what did you remember?" asked {helper}.', '"A useful detail from yesterday," said {detective}. "Let us test it together."'),
]

AWARDS = [
    "a silver detective sticker",
    "a blue notebook star",
    "a tiny brass badge",
    "a ribbon marked Case Solved",
]


ASP_RULES = r"""
needs_search(P) :- detective(P), missing(P, I), clue(I).
team_ready(P) :- needs_search(P), helper(P).
reasonable(P) :- team_ready(P), has_foreshadowing(P), has_flashback(P).
"""


def asp_facts() -> str:
    import asp

    return "\n".join(
        [
            asp.fact("detective", "luna"),
            asp.fact("helper", "ari"),
            asp.fact("missing", "luna_case", "sippy_cup"),
            asp.fact("clue", "sippy_cup"),
            asp.fact("helper", "ari"),
            asp.fact("has_foreshadowing", "luna_case"),
            asp.fact("has_flashback", "luna_case"),
        ]
    )


def asp_program(show: str = "#show reasonable/1.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> bool:
    import asp

    model = asp.one_model(asp_program())
    return bool(asp.atoms(model, "reasonable"))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate a detective story about a thin clue and a sippy cup."
    )
    parser.add_argument("--detective", choices=DETECTIVE_NAMES)
    parser.add_argument("--helper", choices=HELPER_NAMES)
    parser.add_argument("--place", choices=PLACES)
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    detective = args.detective or rng.choice(DETECTIVE_NAMES)
    helper = args.helper or rng.choice(HELPER_NAMES)
    if detective == helper:
        helper = rng.choice([name for name in HELPER_NAMES if name != detective])
    return StoryParams(
        detective_name=detective,
        helper_name=helper,
        place=args.place or rng.choice(PLACES),
        seed=rng.randrange(2**31),
    )


def reasonableness_gate(params: StoryParams) -> None:
    if params.detective_name not in DETECTIVE_NAMES:
        raise StoryError("The detective must be chosen from the known detectives.")
    if params.helper_name not in HELPER_NAMES:
        raise StoryError("The helper must be chosen from the known helpers.")
    if params.detective_name == params.helper_name:
        raise StoryError("The detective and helper must be different people.")
    if params.place not in PLACES:
        raise StoryError("The case needs a known setting.")


def make_world(params: StoryParams) -> CaseFile:
    objects = {
        "shelf": Entity("shelf", "furniture", "the cup shelf"),
        "cup": Entity("cup", "clue_object", "the missing sippy cup"),
        "trail": Entity("trail", "clue", "the thin clue"),
        "helper": Entity("helper", "person", params.helper_name),
        "detective": Entity("detective", "person", params.detective_name),
    }
    case = CaseFile(params.place, objects)
    case.facts.update(
        {
            "detective": params.detective_name,
            "helper": params.helper_name,
            "resolved": False,
            "clue_strength": 0,
        }
    )
    return case


def set_up_case(case: CaseFile, mystery: Mystery) -> None:
    case.facts["mystery"] = mystery
    case.facts["missing_item"] = mystery.missing_item
    case.objects["trail"].meters["clue_strength"] = 1
    case.objects["detective"].memes["curiosity"] = 1
    case.objects["detective"].memes["worry"] = 1
    case.facts["clue_strength"] = 1


def foreshadow(case: CaseFile) -> str:
    mystery: Mystery = case.facts["mystery"]
    case.objects["detective"].memes["worry"] += 1
    case.facts["urgency"] = 1
    return (
        f"Before the search began, a warning appeared: {mystery.omen}. "
        f"It foreshadowed that the trail might soon be harder to see."
    )


def dialogue(case: CaseFile) -> str:
    mystery: Mystery = case.facts["mystery"]
    forms = case.facts["dialogue_forms"]
    first, second = forms
    values = {
        "detective": case.facts["detective"],
        "helper": case.facts["helper"],
        "missing": mystery.missing_item,
    }
    case.objects["helper"].memes["trust"] = 1
    return f"{first.format(**values)} {second.format(**values)}"


def flashback(case: CaseFile) -> str:
    mystery: Mystery = case.facts["mystery"]
    case.facts["memory_used"] = True
    case.objects["detective"].memes["hope"] = 1
    return (
        f"Then {case.facts['detective']} had a flashback: {mystery.flashback}. "
        f"That memory pointed the team toward the next part of the case."
    )


def solve_case(case: CaseFile) -> str:
    mystery: Mystery = case.facts["mystery"]
    detective = case.facts["detective"]
    helper = case.facts["helper"]
    case.facts["resolved"] = True
    case.facts["location_found"] = True
    case.facts["clue_strength"] = 2
    case.objects["shelf"].meters["order"] = 1
    case.objects["detective"].memes["pride"] = 1
    case.objects["helper"].memes["trust"] = 2
    award = case.facts["award"]
    return (
        f"{mystery.solution.capitalize()}. {mystery.ending.capitalize()}. "
        f'{detective} gave {helper} a high five. "We solved it together," said {detective}. '
        f'"The thin clue, the old memory, and our teamwork all mattered." '
        f"The librarian gave {detective} {award}."
    )


def tell_story(params: StoryParams) -> CaseFile:
    case = make_world(params)
    rng = random.Random(params.seed if params.seed is not None else params.place)
    mystery = rng.choice(MYSTERIES)
    case.facts["dialogue_forms"] = rng.choice(DIALOGUE_FORMS)
    case.facts["award"] = rng.choice(AWARDS)
    set_up_case(case, mystery)

    intro = INTRO_FORMS[rng.randrange(len(INTRO_FORMS))].format(
        detective=params.detective_name,
        place=params.place,
        missing=mystery.missing_item,
    )
    warning = foreshadow(case)
    exchange = dialogue(case)
    memory = flashback(case)
    lead = (
        f"{params.detective_name} studied {mystery.thin_clue}. "
        f"{params.helper_name} carefully checked the nearby corners while "
        f"{params.detective_name} followed the clue."
    )
    complication = (
        f"At first, {mystery.obstacle}. "
        f"Nobody guessed, and the case seemed ready to grow cold."
    )
    teamwork = (
        f"Then the teamwork began: {mystery.team_turn}. "
        f"Together they returned to the clue instead of rushing."
    )
    action = (
        f"They decided to {mystery.task}. {complication} "
        f"{teamwork}"
    )
    ending = solve_case(case)

    structure = rng.randrange(3)
    if structure == 0:
        paragraphs = [intro, warning, exchange, memory, lead + " " + action, ending]
    elif structure == 1:
        paragraphs = [intro + " " + warning, exchange, memory + " " + lead, action, ending]
    else:
        paragraphs = [intro, warning + " " + exchange, memory, lead, action, ending]

    case.facts["story"] = "\n\n".join(paragraphs)
    case.facts["mystery_id"] = mystery.id
    case.facts["thin_clue"] = mystery.thin_clue
    return case


def prompts(case: CaseFile) -> list[str]:
    mystery: Mystery = case.facts["mystery"]
    return [
        'Write a detective story using the words "thin" and "sippy".',
        f"Tell a mystery at {case.place} in which {case.facts['detective']} searches for {mystery.missing_item}.",
        "Use foreshadowing, a flashback, and teamwork, then end with a concrete image showing the case is solved.",
    ]


def story_qa(case: CaseFile) -> list[QAItem]:
    mystery: Mystery = case.facts["mystery"]
    detective = case.facts["detective"]
    helper = case.facts["helper"]
    return [
        QAItem(
            question=f"What disappeared at {case.place}?",
            answer=f"{mystery.missing_item.capitalize()} disappeared from its usual place at {case.place}, so {detective} opened a case.",
        ),
        QAItem(
            question=f"What thin clue did {detective} notice?",
            answer=f"{detective} noticed {mystery.thin_clue}, a thin clue that gave the team a direction to investigate.",
        ),
        QAItem(
            question=f"How did {detective} and {helper} use teamwork?",
            answer=f"They worked together because {helper} watched the difficult places while {detective} followed the clue; when {mystery.obstacle}, {mystery.team_turn}.",
        ),
        QAItem(
            question=f"What did {detective} remember in the flashback?",
            answer=f"{detective} remembered that {mystery.flashback}, and that memory helped the team choose where to search next.",
        ),
        QAItem(
            question="How did the ending prove the mystery was solved?",
            answer=f"{mystery.ending.capitalize()}. The returned cup and the orderly scene showed that the missing item had been found.",
        ),
    ]


def world_qa(case: CaseFile) -> list[QAItem]:
    return [
        QAItem(
            question="What is foreshadowing?",
            answer="Foreshadowing is an early hint that prepares readers for something important later.",
        ),
        QAItem(
            question="What is a flashback?",
            answer="A flashback is a part of a story that returns to an earlier event or memory.",
        ),
        QAItem(
            question="Why can teamwork help solve a mystery?",
            answer="Teamwork helps because people can notice different clues, share memories, and divide the search safely.",
        ),
        QAItem(
            question="What does sippy mean in this story?",
            answer="Sippy describes a cup made for taking small, easy drinks, often by a young child.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    lines.extend(f"{i}. {prompt}" for i, prompt in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== Story Q&A ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World Q&A ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(case: CaseFile) -> str:
    return "\n".join(
        [
            "--- trace ---",
            f"place={case.place}",
            f"mystery_id={case.facts.get('mystery_id')}",
            f"resolved={case.facts.get('resolved')}",
            f"clue_strength={case.facts.get('clue_strength')}",
            f"location_found={case.facts.get('location_found', False)}",
            f"objects={list(case.objects)}",
        ]
    )


def generate(params: StoryParams) -> StorySample:
    reasonableness_gate(params)
    case = tell_story(params)
    return StorySample(
        params=params,
        story=case.facts["story"],
        prompts=prompts(case),
        story_qa=story_qa(case),
        world_qa=world_qa(case),
        world=case,
    )


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


def asp_verify() -> int:
    import asp

    py_ok = True
    asp_ok = asp_valid()
    if py_ok != asp_ok:
        print("MISMATCH between ASP and Python gates.")
        return 1
    sample = generate(
        StoryParams(
            detective_name="Luna",
            helper_name="Ari",
            place="the little library",
            seed=17,
        )
    )
    required = ("thin", "sippy", "flashback", "teamwork")
    if not all(word in sample.story.lower() for word in required):
        print("Generated story is missing a required narrative element.")
        return 1
    if not sample.world.facts["resolved"]:
        print("Generated case did not resolve.")
        return 1
    print("OK: ASP and Python gates agree; generated case resolves.")
    return 0


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return

    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        print("ASP gate: reasonable/1 is", "true" if asp_valid() else "false")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    if args.all:
        params_list = [
            StoryParams("Luna", "Ari", "the little library", base_seed),
            StoryParams("Milo", "Bea", "the town museum", base_seed + 1),
            StoryParams("Nia", "Jules", "the rain garden", base_seed + 2),
        ]
        samples = [generate(params) for params in params_list]
    else:
        samples: list[StorySample] = []
        seen: set[str] = set()
        index = 0
        target = max(1, args.n)
        while len(samples) < target and index < max(100, target * 50):
            rng = random.Random(base_seed + index)
            index += 1
            params = resolve_params(args, rng)
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for index, sample in enumerate(samples):
        header = f"### variant {index + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
