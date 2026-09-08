#!/usr/bin/env python3
"""
A tiny detective-story world about an expiring phosphorus glow, a mistaken
accusation, and a reconciliation with a happy ending.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    role: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class Place:
    id: str
    label: str
    tags: set[str] = field(default_factory=set)


@dataclass
class World:
    place: Place
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict[str, object] = field(default_factory=dict)
    clues: list[str] = field(default_factory=list)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, text: str) -> None:
        self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


@dataclass(frozen=True)
class Case:
    key: str
    object_name: str
    clue: str
    mistake: str
    method: str
    reveal: str
    ending: str


CASES = (
    Case(
        "greenhouse_lantern",
        "the greenhouse lantern",
        "a faint green smear on the brass latch",
        "Mara thought Ivo had taken the lantern",
        "the lantern had been moved beside the warm seed tray, where its phosphorus mark would fade fastest",
        "Ivo had carried it there to keep rain from reaching the wick, but he had forgotten to tell Mara",
        "the lantern glowed once more while both friends watched the new seedlings shine",
    ),
    Case(
        "museum_compass",
        "the museum compass",
        "a phosphorus fleck beneath the display table",
        "Nell thought Tomas had hidden the compass",
        "the compass had slipped behind a velvet box when the evening guard dusted the case",
        "Tomas had found the box but feared Nell would blame him for the broken clasp",
        "they repaired the clasp together and placed the compass under a clear, safe bell",
    ),
    Case(
        "river_boat_lamp",
        "the river boat lamp",
        "wet footprints ending beside a coil of blue rope",
        "Pia thought Rowan had taken the lamp without asking",
        "the lamp had been moved under the boat seat before the storm, and its phosphorus paint was beginning to expire",
        "Rowan had saved it from the rain but had stayed silent after Pia shouted",
        "the lamp shone from the bow as the two friends rowed home beneath the stars",
    ),
    Case(
        "clocktower_badge",
        "the clocktower badge",
        "a tiny green reflection on the lowest stair",
        "Eli thought June had pocketed the badge",
        "the badge had fallen through the stair rail and rested near an old phosphorus sign",
        "June had seen it first but waited because she wanted to solve the mystery alone",
        "June handed over the badge, and Eli thanked her before they rang the noon bell",
    ),
)


@dataclass
class StoryParams:
    place: str
    detective_name: str
    friend_name: str
    detective_gender: str = "girl"
    friend_gender: str = "boy"
    seed: Optional[int] = None


PLACES = {
    "greenhouse": Place("greenhouse", "the moonlit greenhouse", {"glass", "plants"}),
    "museum": Place("museum", "the quiet little museum", {"indoor", "display"}),
    "boathouse": Place("boathouse", "the old river boathouse", {"river", "wood"}),
    "clocktower": Place("clocktower", "the town clocktower", {"stone", "stairs"}),
}

NAMES = {
    "girl": ["Luna", "Mara", "Nell", "Pia", "June"],
    "boy": ["Ivo", "Tomas", "Rowan", "Eli", "Finn"],
}


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    detective_gender = args.detective_gender or "girl"
    friend_gender = args.friend_gender or "boy"
    detective = args.detective or rng.choice(NAMES[detective_gender])
    friend = args.friend or rng.choice([n for n in NAMES[friend_gender] if n != detective])
    return StoryParams(
        place=args.place or rng.choice(list(PLACES)),
        detective_name=detective,
        friend_name=friend,
        detective_gender=detective_gender,
        friend_gender=friend_gender,
    )


def valid_params(params: StoryParams) -> None:
    if params.place not in PLACES:
        raise StoryError(f"Unknown place: {params.place}.")
    if params.detective_gender not in NAMES or params.friend_gender not in NAMES:
        raise StoryError("Each character must have a supported gender.")
    if not params.detective_name.strip() or not params.friend_name.strip():
        raise StoryError("Both character names are required.")
    if params.detective_name.casefold() == params.friend_name.casefold():
        raise StoryError("The detective and friend need different names.")


def investigate(params: StoryParams) -> World:
    valid_params(params)
    rng = random.Random(params.seed if params.seed is not None else sum(map(ord, params.place)))
    case = CASES[rng.randrange(len(CASES))]
    place = PLACES[params.place]
    world = World(place)
    detective = world.add(Entity("detective", "character", params.detective_name, "detective"))
    friend = world.add(Entity("friend", "character", params.friend_name, "friend"))
    evidence = world.add(Entity("evidence", "object", case.object_name, "missing_object"))
    vial = world.add(Entity("phosphorus", "material", "a small phosphorus vial", "glowing_material"))

    detective.memes["curiosity"] = 1
    friend.memes["worry"] = 1
    vial.meters["remaining_glow"] = 1
    vial.meters["expires_soon"] = 1

    world.say(f"In {place.label}, Detective {detective.label} arrived when {evidence.label} vanished.")
    world.say(f"The room was locked, but a thin phosphorus glow still trembled near the window.")
    world.para()

    world.clues.extend([case.clue, "the phosphorus glow was growing dim", "the door showed no fresh scratch"])
    world.say(f"Detective {detective.label} knelt down. The first clue was {case.clue}.")
    world.say("Then the detective noticed that the phosphorus would expire before sunrise.")
    world.say(f'"You took it!" {detective.label} said to {friend.label}. "The glow is fading because of you."')
    world.say(f'"I did not steal it," {friend.label} replied. "But I know I moved something nearby."')
    world.para()

    detective.memes["anger"] = 0
    detective.memes["curiosity"] = 2
    world.say(f"Instead of shouting again, Detective {detective.label} followed the glow and checked the floor, the latch, and the nearest hiding place.")
    world.say(f"The clues showed that {case.mistake.lower()}; the truth was simpler: {case.method}.")
    world.say(f'"I was wrong to accuse you," {detective.label} said. "Will you help me finish the case?"')
    world.say(f'"Yes," said {friend.label}. "I should have told you where I put it."')
    world.para()

    world.facts.update(
        case=case,
        detective=detective,
        friend=friend,
        evidence=evidence,
        phosphorus=vial,
        place=place,
        solved=True,
        reconciled=True,
        happy=True,
        answer=case.reveal,
    )
    detective.memes["trust"] = 1
    friend.memes["relief"] = 1
    vial.meters["remaining_glow"] = 0
    vial.meters["expired"] = 1

    world.say(f"Together they found the answer: {case.reveal}.")
    world.say(f"The phosphorus did expire, but the evidence was safe. {case.ending}.")
    world.say(f"Detective {detective.label} wrote one final note: “A good detective follows clues, and a good friend tells the truth.”")
    return world


def generate(params: StoryParams) -> StorySample:
    world = investigate(params)
    case: Case = world.facts["case"]
    detective: Entity = world.facts["detective"]
    friend: Entity = world.facts["friend"]
    return StorySample(
        params=params,
        story=world.render(),
        prompts=[
            "Write a child-friendly detective story using the words expire and phosphorus.",
            f"Tell a reconciliation story in which Detective {detective.label} solves a mystery with {friend.label}.",
            f"Write a happy ending at {world.facts['place'].label} where a fading phosphorus clue helps reveal the truth.",
        ],
        story_qa=[
            QAItem(
                "What happened to the phosphorus?",
                "The phosphorus glow was growing dim and expired before sunrise, so the detective had to follow its fading clue quickly.",
            ),
            QAItem(
                "Why did the detective apologize?",
                f"Detective {detective.label} apologized because the clues showed that {case.mistake.lower()}, not that {friend.label} had stolen anything.",
            ),
            QAItem(
                "How did the friends reconcile?",
                f"{detective.label} admitted the accusation was wrong, and {friend.label} admitted that the moved object should have been explained. Then they solved the case together.",
            ),
            QAItem(
                "How did the story end happily?",
                f"The missing object was safe, the friends trusted each other again, and {case.ending}.",
            ),
        ],
        world_qa=[
            QAItem(
                "What does expire mean?",
                "Expire means to come to an end or stop being usable. In this story, the phosphorus glow expired as its light faded away.",
            ),
            QAItem(
                "What is phosphorus?",
                "Phosphorus is a chemical element. Some phosphorus materials can glow, so the story uses a small glow as a clue.",
            ),
            QAItem(
                "What does reconciliation mean?",
                "Reconciliation means making peace after a disagreement by admitting mistakes, listening, and restoring trust.",
            ),
        ],
        world=world,
    )


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    lines.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
    lines.append("\n== Story questions ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("\n== World-knowledge questions ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        meters = {k: v for k, v in entity.meters.items() if v}
        memes = {k: v for k, v in entity.memes.items() if v}
        lines.append(f"{entity.id}: kind={entity.kind}, meters={meters}, memes={memes}")
    lines.append(f"clues={world.clues}")
    lines.append(f"solved={world.facts.get('solved')}, reconciled={world.facts.get('reconciled')}, happy={world.facts.get('happy')}")
    return "\n".join(lines)


ASP_RULES = r"""
glow(phosphorus) :- phosphorus(phosphorus), remaining(phosphorus, 1).
fading(phosphorus) :- phosphorus(phosphorus), expires_soon(phosphorus).
clue(fading_glow) :- fading(phosphorus).
solved(case) :- clue(fading_glow), no_forced_entry(case).
reconciled(friends) :- solved(case), apology(detective), truth(friend).
happy(ending) :- reconciled(friends), safe(evidence).
#show solved/1.
#show reconciled/1.
#show happy/1.
"""


def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            asp.fact("phosphorus", "phosphorus"),
            asp.fact("remaining", "phosphorus", 1),
            asp.fact("expires_soon", "phosphorus"),
            asp.fact("no_forced_entry", "case"),
            asp.fact("apology", "detective"),
            asp.fact("truth", "friend"),
            asp.fact("safe", "evidence"),
        ]
    )


def asp_program(show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    try:
        import asp
        model = asp.one_model(asp_program())
        names = {symbol.name for symbol in model}
        required = {"solved", "reconciled", "happy"}
        if not required.issubset(names):
            print("ASP parity check failed.")
            return 1
        sample = generate(StoryParams("greenhouse", "Luna", "Ivo", seed=3))
        if not sample.story or "expire" not in sample.story or "phosphorus" not in sample.story:
            print("Story smoke test failed.")
            return 1
    except Exception as exc:
        print(f"Verification failed: {exc}")
        return 1
    print("OK: smoke tests passed.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="A phosphorus detective story with reconciliation.")
    parser.add_argument("--place", choices=sorted(PLACES))
    parser.add_argument("--detective")
    parser.add_argument("--friend")
    parser.add_argument("--detective-gender", choices=sorted(NAMES))
    parser.add_argument("--friend-gender", choices=sorted(NAMES))
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--seed", type=int)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def curated() -> list[StoryParams]:
    return [
        StoryParams("greenhouse", "Luna", "Ivo", seed=1),
        StoryParams("museum", "Mara", "Tomas", seed=2),
        StoryParams("boathouse", "Pia", "Rowan", seed=3),
        StoryParams("clocktower", "June", "Eli", seed=4),
    ]


def emit(sample: StorySample, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show solved/1."))
        return
    if args.verify:
        raise SystemExit(asp_verify())
    if args.asp:
        try:
            import asp
            print(asp.one_model(asp_program("#show solved/1.\n#show reconciled/1.\n#show happy/1.")))
        except Exception as exc:
            raise SystemExit(f"ASP unavailable: {exc}")
        return

    if args.all:
        samples = [generate(p) for p in curated()]
    else:
        base_seed = args.seed if args.seed is not None else random.randrange(2**31)
        samples = []
        for index in range(max(0, args.n)):
            rng = random.Random(base_seed + index)
            params = resolve_params(args, rng)
            params.seed = base_seed + index
            samples.append(generate(params))

    if args.json:
        payload = samples[0].to_json() if len(samples) == 1 else json.dumps(
            [sample.to_dict() for sample in samples], indent=2, ensure_ascii=False
        )
        print(payload)
        return

    for index, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=f"### variant {index + 1}" if len(samples) > 1 else "")
        if index + 1 < len(samples):
            print("\n" + "=" * 68 + "\n")


if __name__ == "__main__":
    main()
