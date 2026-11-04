#!/usr/bin/env python3
"""
A small whodunit storyworld about curiosity, careful advice, and a happy ending.

A child notices that a treasured object has gone missing and suspects the wrong
person. A trusted adviser encourages them to follow a real clue, ask kindly,
and discover what happened.
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

_REPO_ROOT = next(
    (parent for parent in Path(__file__).resolve().parents if (parent / "storyworlds" / "results.py").is_file()),
    Path(__file__).resolve().parents[5],
)
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from storyworlds.results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class StoryParams:
    case: str
    child: str
    adviser: str
    seed: Optional[int] = None


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


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
        return "\n\n".join(" ".join(part) for part in self.paragraphs if part)


CHILDREN = ["Mina", "Eli", "Noor", "Theo", "Luz", "Ari"]
ADVISERS = ["Aunt Sol", "Mr. Vale", "Grandma June", "Coach Ren"]
SUSPECTS = ["Bea", "Niko", "Tavi"]

CASES = {
    "bell": {
        "item": "brass handbell",
        "place": "the little theater",
        "event": "the handbell was gone from its hook before the puppet show",
        "clue": "a short strand of blue thread",
        "clue_detail": (
            "A blue thread clung to the empty hook. The same bright thread was "
            "sticking from the theater curtain, whose hem had caught on the hook."
        ),
        "wrong_suspect": "Niko",
        "culprit": "Tavi",
        "culprit_role": "the puppet-show drummer",
        "reveal": (
            "Behind the curtain, Tavi held up the bell. The loose hem had caught "
            "it, and Tavi had taken it down so it would not fall during the show."
        ),
        "confession": (
            "“I heard it tap against the curtain,” Tavi said. “I put it in my "
            "music basket so it would stay safe until the show.”"
        ),
        "ending": (
            "Soon the bell rang for the puppet show, and its clear note made "
            "the curtain's blue hem shimmer."
        ),
        "result": "Tavi had safely moved the bell after its hook caught the curtain",
        "place_image": "the blue curtain",
    },
    "cookie_tin": {
        "item": "star-shaped cookie tin",
        "place": "the community kitchen",
        "event": "the cookie tin had vanished from the sunny windowsill",
        "clue": "a trail of cinnamon crumbs",
        "clue_detail": (
            "Cinnamon crumbs crossed the counter and stopped beside the cool "
            "pantry shelf. They were not scattered near the garden door at all."
        ),
        "wrong_suspect": "Bea",
        "culprit": "Niko",
        "culprit_role": "the garden helper",
        "reveal": (
            "On the pantry shelf, Niko was checking the tin. The sunny sill had "
            "grown too warm, so Niko had carried it away before the cookies softened."
        ),
        "confession": (
            "“I moved it to the cool shelf,” Niko explained. “A few crumbs fell "
            "when I carried it, and I meant to tell everyone.”"
        ),
        "ending": (
            "The neighbors shared the cookies at the long table, and the empty "
            "starry tin caught a warm square of afternoon light."
        ),
        "result": "Niko had moved the tin to keep the cookies cool",
        "place_image": "the pantry shelf",
    },
    "spoon": {
        "item": "silver serving spoon",
        "place": "the school garden shed",
        "event": "the serving spoon was missing just before the seed-swap picnic",
        "clue": "a little curl of green ribbon",
        "clue_detail": (
            "A curl of green ribbon lay by the potting bench. A matching ribbon "
            "was tied around the seed packets, not the picnic basket."
        ),
        "wrong_suspect": "Tavi",
        "culprit": "Bea",
        "culprit_role": "the seed-swap organizer",
        "reveal": (
            "Bea opened a seed box and found the spoon tucked beside the packets. "
            "Bea had moved it from the wobbly picnic table before it could slide off."
        ),
        "confession": (
            "“I set it here while I steadied the table,” Bea said. “Then I got "
            "busy sorting seeds and forgot to put it back.”"
        ),
        "ending": (
            "At the picnic, the spoon rested safely beside a bowl of berries, "
            "while green ribbons fluttered above the seed table."
        ),
        "result": "Bea had set the spoon aside while steadying the picnic table",
        "place_image": "the seed box",
    },
    "kite_spool": {
        "item": "red kite spool",
        "place": "the windy hill",
        "event": "the kite spool was missing when the breeze finally returned",
        "clue": "a yellow wool fiber",
        "clue_detail": (
            "A yellow fiber snagged on the fence. Beyond it, the kite's red "
            "string led toward the low gate, where a wool scarf had caught."
        ),
        "wrong_suspect": "Niko",
        "culprit": "Tavi",
        "culprit_role": "the hill's kite-flying helper",
        "reveal": (
            "At the gate, Tavi showed the spool. Tavi had wound in the loose "
            "string before it could tangle around the scarf and the fence."
        ),
        "confession": (
            "“The string was pulling the scarf tight,” Tavi said. “I reeled it "
            "in to keep the kite and the scarf from getting tangled.”"
        ),
        "ending": (
            "With the scarf free, the red kite lifted over the hill, and its "
            "tail flicked like a bright little flag."
        ),
        "result": "Tavi had wound in the string to keep it from tangling on the fence",
        "place_image": "the low gate",
    },
}

ASP_RULES = r"""
#show valid_case/1.

case_id(C) :- case(C).
has_clue(C) :- clue_available(C).
kind_resolution(C) :- kind_resolution_possible(C).
valid_case(C) :- case_id(C), has_clue(C), kind_resolution(C).
"""


def valid_case_ids() -> list[str]:
    """Python reasonableness gate for cases with a clue and a kind resolution."""
    return sorted(
        case_id
        for case_id, case in CASES.items()
        if case.get("clue") and case.get("result") and case.get("ending")
    )


def asp_facts() -> str:
    import storyworlds.asp as asp

    lines: list[str] = []
    for case_id in sorted(CASES):
        lines.append(asp.fact("case", case_id))
        case = CASES[case_id]
        if case.get("clue"):
            lines.append(asp.fact("clue_available", case_id))
        if case.get("result") and case.get("ending"):
            lines.append(asp.fact("kind_resolution_possible", case_id))
    return "\n".join(lines)


def asp_program(show: str = "#show valid_case/1.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_case_ids() -> list[str]:
    import storyworlds.asp as asp

    model = asp.one_model(asp_program())
    return sorted({case_id for (case_id,) in asp.atoms(model, "valid_case")})


def asp_verify() -> int:
    python_cases = set(valid_case_ids())
    clingo_cases = set(asp_valid_case_ids())
    if python_cases != clingo_cases:
        print("MISMATCH between the Python gate and the ASP gate:")
        if python_cases - clingo_cases:
            print("  only in Python:", sorted(python_cases - clingo_cases))
        if clingo_cases - python_cases:
            print("  only in clingo:", sorted(clingo_cases - python_cases))
        return 1

    print(f"OK: clingo gate matches the Python gate ({len(python_cases)} cases).")
    for case_id in sorted(python_cases):
        sample = generate(StoryParams(case=case_id, child="Mina", adviser="Aunt Sol"))
        if not sample.story.strip() or "“" not in sample.story or "?”" not in sample.story:
            print(f"FAIL: {case_id} did not produce a complete story with spoken dialogue.")
            return 1
        if not CASES[case_id]["ending"].split(",")[0] in sample.story:
            print(f"FAIL: {case_id} is missing its changed ending image.")
            return 1
        if not sample.story_qa or not sample.world_qa:
            print(f"FAIL: {case_id} is missing a QA set.")
            return 1
    print(f"OK: exercised {len(python_cases)} generated stories, dialogue, endings, and QA.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="A curious, child-friendly whodunit storyworld."
    )
    parser.add_argument("--case", choices=sorted(CASES))
    parser.add_argument("--child", choices=CHILDREN)
    parser.add_argument("--adviser", choices=ADVISERS)
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    available = valid_case_ids()
    if args.case:
        if args.case not in available:
            raise StoryError(f"No story: the case {args.case!r} has no reasonable solution.")
        case_id = args.case
    else:
        if not available:
            raise StoryError("No story: there are no cases with a clue and a kind solution.")
        case_id = rng.choice(available)

    child = args.child or rng.choice(CHILDREN)
    adviser = args.adviser or rng.choice(ADVISERS)
    return StoryParams(case=case_id, child=child, adviser=adviser)


def generate(params: StoryParams) -> StorySample:
    if params.case not in valid_case_ids():
        raise StoryError(f"No story: {params.case!r} is not a solvable case.")
    if params.child not in CHILDREN:
        raise StoryError(f"No story: {params.child!r} is not a registered child character.")
    if params.adviser not in ADVISERS:
        raise StoryError(f"No story: {params.adviser!r} is not a registered adviser.")

    case = CASES[params.case]
    w = World()
    child = w.add(
        Entity(
            id="child",
            kind="character",
            label=params.child,
            memes={"curiosity": 0.4, "confidence": 0.5},
        )
    )
    adviser = w.add(
        Entity(
            id="adviser",
            kind="character",
            label=params.adviser,
            memes={"patience": 0.9, "kindness": 0.9},
        )
    )
    w.add(Entity(id="suspect_bea", kind="character", label="Bea"))
    w.add(Entity(id="suspect_niko", kind="character", label="Niko"))
    w.add(Entity(id="suspect_tavi", kind="character", label="Tavi"))
    missing_object = w.add(
        Entity(
            id="mystery_object",
            kind="object",
            label=case["item"],
            meters={"at_display": 0.0, "found": 0.0},
            memes={"mystery": 1.0},
        )
    )
    clue = w.add(
        Entity(
            id="physical_clue",
            kind="clue",
            label=case["clue"],
            meters={"noticed": 0.0, "followed": 0.0},
            memes={"meaning": 0.0},
        )
    )
    place = w.add(
        Entity(
            id="setting",
            kind="place",
            label=case["place"],
            meters={"searched": 0.0},
            memes={"suspense": 0.0},
        )
    )

    w.say(
        f"At {place.label}, {params.child} noticed that the {case['item']} had "
        f"gone missing: {case['event']}."
    )
    w.say(
        f"Bea, Niko, and Tavi had all been helping nearby, so the little gathering "
        f"became a very quiet whodunit."
    )

    place.memes["suspense"] = 1.0
    child.memes["curiosity"] = 0.8
    w.para()
    w.say(
        f"“I think {case['wrong_suspect']} took the {case['item']}!” said {params.child}. "
        f"“{case['wrong_suspect']} was close by.”"
    )
    w.say(
        f"“Maybe,” said {params.adviser}, “but being nearby is not proof. Let’s "
        f"follow the {case['clue']} and ask everyone kindly before we decide.”"
    )
    child.memes["confidence"] = 0.7
    child.memes["curiosity"] = 1.0
    clue.meters["noticed"] = 1.0
    clue.meters["followed"] = 1.0
    place.meters["searched"] = 1.0
    w.say(case["clue_detail"])

    w.para()
    w.say(
        f"{params.child} spoke to {case['culprit']} instead of making an accusation. "
        f"“Did you see what happened to the {case['item']}?”"
    )
    w.say(case["confession"])
    w.say(case["reveal"])

    missing_object.meters["found"] = 1.0
    missing_object.meters["at_display"] = 1.0
    missing_object.memes["mystery"] = 0.0
    clue.memes["meaning"] = 1.0
    child.memes["relief"] = 1.0
    child.memes["kindness"] = 1.0
    adviser.memes["pride"] = 1.0
    place.memes["suspense"] = 0.0
    w.say(
        f"{params.child} smiled at {case['wrong_suspect']}. “I’m glad we checked "
        f"the clue before guessing.” {case['ending']}"
    )

    w.facts.update(
        case=params.case,
        child=params.child,
        adviser=params.adviser,
        item=case["item"],
        location=case["place"],
        clue=case["clue"],
        mistaken_suspect=case["wrong_suspect"],
        helper_who_moved_item=case["culprit"],
        resolution=case["result"],
        clue_followed=True,
        accusation_avoided=True,
        mystery_resolved=True,
    )

    prompts = [
        "Write a gentle whodunit in which a curious child follows a clue instead of blaming someone.",
        (
            f"Tell a child-friendly mystery about {params.child} at {case['place']}, "
            f"where {case['item']} goes missing and kind advice changes what the child does."
        ),
        (
            f"Write a complete story with a misunderstanding, a useful clue, "
            f"a spoken exchange, and a happy ending."
        ),
    ]
    story_qa = [
        QAItem(
            question=f"What went missing at {case['place']}?",
            answer=f"The {case['item']} went missing at {case['place']}.",
        ),
        QAItem(
            question=f"What clue did {params.child} follow?",
            answer=(
                f"{params.child} followed {case['clue']}. It helped show that "
                f"{case['wrong_suspect']} had not simply taken the missing object."
            ),
        ),
        QAItem(
            question=f"Why did {params.child} first suspect {case['wrong_suspect']}?",
            answer=(
                f"{params.child} thought {case['wrong_suspect']} might be responsible "
                f"because they had been nearby, but the adviser explained that being "
                f"nearby was not proof."
            ),
        ),
        QAItem(
            question="What had really happened to the missing object?",
            answer=(
                f"{case['result']}. Once the clue was understood, everyone could "
                f"solve the mystery without blaming anyone unfairly."
            ),
        ),
        QAItem(
            question=f"What advice helped {params.child} solve the mystery?",
            answer=(
                f"{params.adviser} advised {params.child} to follow the clue and ask "
                f"everyone kindly before deciding who was responsible."
            ),
        ),
    ]
    world_qa = [
        QAItem(
            question="What is a clue in a mystery?",
            answer=(
                "A clue is a detail that helps people figure out what happened, "
                "such as a mark, a sound, or an object left behind."
            ),
        ),
        QAItem(
            question="Why should a detective check a clue before blaming someone?",
            answer=(
                "Checking a clue helps a detective learn what really happened and "
                "keeps an innocent person from being blamed by mistake."
            ),
        ),
        QAItem(
            question="What does curiosity help someone do?",
            answer=(
                "Curiosity helps someone ask questions, notice details, and keep "
                "looking for a good explanation."
            ),
        ),
        QAItem(
            question="What is a whodunit?",
            answer=(
                "A whodunit is a mystery story in which characters gather clues "
                "to find out who did something or what happened."
            ),
        ),
    ]

    return StorySample(
        params=params,
        story=w.render(),
        prompts=prompts,
        story_qa=story_qa,
        world_qa=world_qa,
        world=w,
    )


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    lines.extend(f"{index}. {prompt}" for index, prompt in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.extend((f"Q: {item.question}", f"A: {item.answer}"))
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.extend((f"Q: {item.question}", f"A: {item.answer}"))
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        details = []
        if entity.meters:
            details.append(f"meters={entity.meters}")
        if entity.memes:
            details.append(f"memes={entity.memes}")
        lines.append(f"  {entity.label:24} ({entity.kind:10}) {' '.join(details)}")
    lines.append(f"  facts={world.facts}")
    return "\n".join(lines)


def build_curated() -> list[StoryParams]:
    return [
        StoryParams(case="bell", child="Mina", adviser="Aunt Sol"),
        StoryParams(case="cookie_tin", child="Theo", adviser="Grandma June"),
        StoryParams(case="spoon", child="Noor", adviser="Mr. Vale"),
        StoryParams(case="kite_spool", child="Ari", adviser="Coach Ren"),
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

    if args.n < 1 and not args.all:
        raise StoryError("-n must be at least 1.")

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        case_ids = asp_valid_case_ids()
        print(f"{len(case_ids)} solvable whodunit cases:\n")
        for case_id in case_ids:
            case = CASES[case_id]
            print(f"  {case_id:12} -> {case['item']} ({case['place']})")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        seen: set[str] = set()
        attempts = 0
        while len(samples) < args.n and attempts < max(50, args.n * 50):
            seed = base_seed + attempts
            attempts += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as error:
                print(error)
                return
            params.seed = seed
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)

    if len(samples) < args.n and not args.all:
        print("Could not generate enough distinct stories from the selected options.")
        return

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for index, sample in enumerate(samples):
        header = ""
        if args.all:
            header = f"### {sample.params.case.replace('_', ' ').title()}"
        elif len(samples) > 1:
            header = f"### variant {index + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    try:
        main()
    except StoryError as error:
        print(error, file=sys.stderr)
        sys.exit(2)
