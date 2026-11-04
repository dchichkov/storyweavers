#!/usr/bin/env python3
"""A child-facing superhero storyworld about germs, carbon dioxide, and care."""

from __future__ import annotations

import argparse
import hashlib
import json
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

ROOT = Path(__file__).resolve().parents[4]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass(frozen=True)
class Place:
    description: str
    detail: str


@dataclass
class StoryParams:
    place: str
    challenge: str
    hero: str
    friend: str
    route: str = "sunrise"
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, text: str) -> None:
        self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(paragraph) for paragraph in self.paragraphs if paragraph)


PLACES = {
    "greenhouse": Place(
        "the school greenhouse",
        "sunlight made bright squares on the seedling shelves",
    ),
    "classroom": Place(
        "the bright science classroom",
        "paper planets wobbled above the reading corner",
    ),
    "courtyard": Place(
        "the school courtyard",
        "a row of marigolds nodded beside the garden table",
    ),
}

CHALLENGES = {
    "cap": {
        "label": "the loose jar lid",
        "question": "Should the fizzy jar be closed?",
        "qa_detail": (
            "Pip picked up the lid, but Luna explained that a tight lid could trap "
            "carbon dioxide pressure and pop off."
        ),
    },
    "sneeze": {
        "label": "a sneeze near the shared marker",
        "question": "How should they keep the shared tools clean?",
        "qa_detail": (
            "Pip sneezed into a hand near the shared marker. Luna paused the activity "
            "so Pip could use a tissue and wash with soap before touching the tools."
        ),
    },
    "spill": {
        "label": "a small spill beside the table",
        "question": "What should they do about the slippery drops?",
        "qa_detail": (
            "A few drops slid beside the table. Luna asked everyone to step back while "
            "Ms. Rowan helped wipe them up."
        ),
    },
}

# Python gate and ASP facts use the same deliberately small compatibility registry.
ALLOWED = {
    ("greenhouse", "cap"),
    ("greenhouse", "sneeze"),
    ("greenhouse", "spill"),
    ("classroom", "cap"),
    ("classroom", "sneeze"),
    ("courtyard", "sneeze"),
    ("courtyard", "spill"),
}

HEROES = {
    "Luna": "Captain Comet",
    "Kai": "Captain Kite",
    "Zuri": "Captain Zing",
}
FRIENDS = {"Pip", "Bea", "Tavi"}
ROUTES = ("sunrise", "bell", "checklist")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="A superhero storyworld about a careful science-club demonstration."
    )
    parser.add_argument("--place")
    parser.add_argument("--challenge")
    parser.add_argument("--hero")
    parser.add_argument("--friend")
    parser.add_argument("--route")
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--seed", type=int)
    for flag in ("all", "trace", "qa", "json", "asp", "verify", "show-asp"):
        parser.add_argument(f"--{flag}", action="store_true")
    return parser


def valid_combos() -> list[tuple[str, str]]:
    return sorted(ALLOWED)


ASP_RULES = """
valid(Place, Challenge) :-
    place(Place),
    challenge(Challenge),
    fits(Place, Challenge).
"""


def asp_facts() -> str:
    import asp

    lines = [
        *(asp.fact("place", place) for place in sorted(PLACES)),
        *(asp.fact("challenge", challenge) for challenge in sorted(CHALLENGES)),
        *(asp.fact("fits", place, challenge) for place, challenge in valid_combos()),
    ]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    symbols = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(symbols, "valid")))


def asp_verify() -> int:
    python_combos = set(valid_combos())
    clingo_combos = set(asp_valid_combos())
    if python_combos != clingo_combos:
        print("MISMATCH:", sorted(python_combos - clingo_combos), sorted(clingo_combos - python_combos))
        return 1

    checked = 0
    for index, (place, challenge) in enumerate(valid_combos()):
        hero = sorted(HEROES)[index % len(HEROES)]
        friends = sorted(FRIENDS)
        friend = friends[index % len(friends)]
        params = StoryParams(
            place=place,
            challenge=challenge,
            hero=hero,
            friend=friend,
            route=ROUTES[index % len(ROUTES)],
            seed=1000 + index,
        )
        sample = generate(params)
        story = sample.story.lower()
        if (
            "germ" not in story
            or "carbon dioxide" not in story
            or "?" not in story
            or "captain" not in story
            or not sample.story_qa
            or sample.story.strip()[-1:] not in ".!?"
        ):
            print(f"Generated-story check failed for {place}/{challenge}.")
            return 1
        checked += 1

    print(
        f"OK: clingo gate matches valid_combos() ({len(python_combos)} combos); "
        f"checked {checked} generated stories."
    )
    return 0


def _check_choice(field_name: str, value: Optional[str], choices: set[str]) -> None:
    if value is not None and value not in choices:
        readable = ", ".join(sorted(choices))
        raise StoryError(f"Invalid {field_name} {value!r}; choose one of: {readable}.")


def validate_params(params: StoryParams) -> None:
    _check_choice("place", params.place, set(PLACES))
    _check_choice("challenge", params.challenge, set(CHALLENGES))
    _check_choice("hero", params.hero, set(HEROES))
    _check_choice("friend", params.friend, FRIENDS)
    _check_choice("route", params.route, set(ROUTES))
    if (params.place, params.challenge) not in ALLOWED:
        raise StoryError(
            f"The {params.challenge!r} challenge does not fit the {params.place!r} setting."
        )


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    _check_choice("place", args.place, set(PLACES))
    _check_choice("challenge", args.challenge, set(CHALLENGES))
    _check_choice("hero", args.hero, set(HEROES))
    _check_choice("friend", args.friend, FRIENDS)
    _check_choice("route", args.route, set(ROUTES))

    combos = [
        combo
        for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.challenge is None or combo[1] == args.challenge)
    ]
    if not combos:
        if args.place and args.challenge:
            raise StoryError(
                f"The {args.challenge!r} challenge does not fit the {args.place!r} setting."
            )
        raise StoryError("No safe science-club story fits those options.")

    place, challenge = rng.choice(combos)
    hero = args.hero or rng.choice(sorted(HEROES))
    available_friends = sorted(FRIENDS - {hero})
    friend = args.friend or rng.choice(available_friends)
    if friend == hero:
        raise StoryError("The hero and friend must be different characters.")

    params = StoryParams(
        place=place,
        challenge=challenge,
        hero=hero,
        friend=friend,
        route=args.route or rng.choice(ROUTES),
    )
    validate_params(params)
    return params


def story_rng(params: StoryParams) -> random.Random:
    text = "|".join(
        str(value)
        for value in (
            params.seed,
            params.place,
            params.challenge,
            params.hero,
            params.friend,
            params.route,
        )
    )
    digest = hashlib.sha256(text.encode("utf-8")).digest()
    return random.Random(int.from_bytes(digest[:8], "big"))


def tell(params: StoryParams) -> World:
    validate_params(params)
    place = PLACES[params.place]
    challenge = CHALLENGES[params.challenge]
    rng = story_rng(params)
    world = World(place)

    hero = world.add(
        Entity(
            id=params.hero,
            kind="character",
            type="child_superhero",
            label=params.hero,
            meters={"care": 0.55, "safety_checks": 0.0},
            memes={"confidence": 0.55, "kindness": 0.8},
        )
    )
    friend = world.add(
        Entity(
            id=params.friend,
            kind="character",
            type="child_science_helper",
            label=params.friend,
            meters={"care": 0.5, "clean_hands": 1.0},
            memes={"confidence": 0.5, "caution": 0.4},
        )
    )
    teacher = world.add(
        Entity(
            id="Ms. Rowan",
            kind="character",
            type="teacher",
            label="Ms. Rowan",
            meters={"supervision": 1.0},
            memes={"patience": 0.9},
        )
    )
    jar = world.add(
        Entity(
            id="open_fizz_jar",
            kind="object",
            type="demonstration_jar",
            label="the open demonstration jar",
            meters={"open": 1.0, "bubbling": 0.6, "sealed": 0.0},
            memes={"safe_setup": 0.8},
        )
    )
    germ_risk = world.add(
        Entity(
            id="germ_transfer_risk",
            kind="hazard",
            type="conceptual_hygiene_risk",
            label="germ-transfer risk",
            meters={"relative_risk": 0.35},
            memes={"awareness": 0.4},
        )
    )
    table = world.add(
        Entity(
            id="science_table",
            kind="object",
            type="work_surface",
            label="the science table",
            meters={"dry": 1.0, "tools_clean": 1.0},
            memes={"order": 0.7},
        )
    )

    openings = {
        "sunrise": (
            f"Morning light reached {place.description} as the science club gathered; "
            f"{place.detail}."
        ),
        "bell": (
            f"The science-club bell gave a cheerful ding in {place.description}. "
            f"{place.detail}, and {params.friend}'s goggles slid down to the tip of a nose."
        ),
        "checklist": (
            f"At {place.description}, {params.hero} checked the safety list before "
            f"the club began. Nearby, {place.detail}."
        ),
    }
    world.say(openings[params.route])
    world.say(
        f"{hero.id}, known as {HEROES[params.hero]}, clipped a bright cape safely to "
        f"the back of a chair. Superheroes kept capes away from science tables. "
        f"With {teacher.label} beside them, {hero.id} and {friend.id} put on goggles "
        f"and washed their hands before watching a small baking-soda-and-vinegar "
        f"demonstration in {jar.label}. The fizz made carbon dioxide bubbles."
    )
    world.say(
        f'{hero.id} tapped a rhyme on the safety card: "Wash hands before the show; '
        f'tiny germs can travel where we go." Many germs are harmless, but some can '
        f"make people sick, so the children kept their hands clean and their tools to themselves."
    )
    world.para()

    if params.challenge == "cap":
        world.say(
            f"As the bubbles danced, {friend.id} picked up the loose lid. "
            f'"Should I screw it on and keep every bubble?"'
        )
        world.say(
            f'"Hold on," {hero.id} replied. "Carbon dioxide needs room to escape. '
            f"A tight lid could trap pressure and pop off.\" "
            f'{friend.id} set the lid on a far shelf. "No flying lids on my watch!"'
        )
        jar.meters["open"] = 1.0
        jar.meters["sealed"] = 0.0
        jar.memes["safe_setup"] = 1.0
        friend.memes["caution"] = 0.9
        hero.meters["safety_checks"] += 1.0
        turn = "the lid stayed on the shelf, well away from the open jar"
        consequence = (
            f"The lid rested on the far shelf while the open jar fizzed gently on its tray."
        )
        question = "Why did Luna ask Pip to leave the jar lid off?"
        answer = (
            "Luna kept the jar open because carbon dioxide bubbles need a way out. "
            "A tight lid could trap pressure and pop off, so Pip put the lid on a far shelf."
        )
    elif params.challenge == "sneeze":
        world.say(
            f"Just then, {friend.id} sneezed into a hand while reaching toward the shared marker. "
            f'"Oh! Could a germ ride from my hand to the marker?"'
        )
        world.say(
            f'"Let us pause, not panic," {hero.id} said. "Use a tissue, then wash with soap '
            f"before touching shared tools.\" "
            f'{friend.id} used a tissue and washed carefully. "Marker mission: clean hands first!"'
        )
        friend.meters["clean_hands"] = 1.0
        friend.memes["caution"] = 0.9
        germ_risk.meters["relative_risk"] = 0.08
        germ_risk.memes["awareness"] = 1.0
        table.meters["tools_clean"] = 1.0
        hero.meters["safety_checks"] += 1.0
        turn = "the children paused so Pip could clean up before sharing the marker"
        consequence = (
            f"The marker was ready to share again, and {friend.id}'s clean hands "
            f"returned to the activity."
        )
        question = "What did Pip do after sneezing near the shared marker?"
        answer = (
            f"{friend.id} used a tissue and washed with soap before touching the shared "
            f"marker. {hero.id} explained that germs can travel on hands, so the group paused "
            f"rather than panicking."
        )
    else:
        world.say(
            f"A few drops slipped beside the table, making a shiny patch near the walkway. "
            f'"The floor might get slippery," {friend.id} warned.'
        )
        world.say(
            f'"Good spotting," {hero.id} answered. "Everyone step back while Ms. Rowan '
            f"helps us wipe it up.\" "
            f'{friend.id} moved the picture cards away. "My cape is brave, but it is not a mop!"'
        )
        table.meters["dry"] = 0.0
        hero.meters["safety_checks"] += 1.0
        table.meters["dry"] = 1.0
        friend.memes["caution"] = 0.9
        turn = "everyone stepped back while the teacher helped clear the slippery drops"
        consequence = (
            "Ms. Rowan dried the table and floor before anyone carried the picture cards back."
        )
        question = "How did Luna and Pip handle the drops near the walkway?"
        answer = (
            f"{friend.id} warned that the drops could make the walkway slippery. "
            f"{hero.id} asked everyone to step back, and Ms. Rowan helped wipe the area dry."
        )

    world.para()
    world.say(
        f"That small pause changed the whole demonstration: {turn}. "
        f"{teacher.label} checked the setup, and the children watched the carbon dioxide "
        f"bubble out of the jar instead of trying to trap it."
    )
    world.say(
        f'{hero.id} read the second rhyme aloud: "Keep the jar open; let bubbles rise; '
        f"trap gas in a lid, and it may surprise!\" "
        f'{friend.id} grinned. "A superhero rhyme with a safety sign—very powerful punctuation."'
    )
    world.say(
        f"{consequence} The group finished with clean hands, goggles on, and the jar open "
        f"under {teacher.label}'s watch."
    )
    world.say(
        f"When the club ended, {HEROES[params.hero]}'s cape hung neatly on its chair, "
        f"the safety card stood beside the fizzing jar, and {params.friend} could explain "
        f"why the bubbles were welcome but a sealed lid was not."
    )

    hero.meters["care"] = 1.0
    hero.meters["safety_checks"] = max(1.0, hero.meters["safety_checks"])
    hero.memes["confidence"] = 0.9
    friend.memes["confidence"] = 0.85
    friend.memes["caution"] = 1.0
    world.facts.update(
        hero=hero,
        friend=friend,
        teacher=teacher,
        jar=jar,
        germ_risk=germ_risk,
        table=table,
        place=place,
        challenge=challenge,
        challenge_key=params.challenge,
        turn=turn,
        consequence=consequence,
        question=question,
        answer=answer,
        alias=HEROES[params.hero],
        rhyme="Keep the jar open; let bubbles rise; trap gas in a lid, and it may surprise!",
        rng=rng,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    facts = world.facts
    return [
        f"Write a superhero story for a young child about {facts['hero'].id}, "
        f"{facts['friend'].id}, and a safe carbon dioxide demonstration in "
        f"{facts['place'].description}.",
        f"Tell a cautionary, humorous story in which {facts['hero'].id} responds to "
        f"{facts['challenge']['label']} with care for germs and safety.",
        f"Include a spoken exchange, a memorable rhyme, and an ending that shows how "
        f"the science club changed its actions: {facts['consequence']}",
    ]


def story_qa(world: World) -> list[QAItem]:
    facts = world.facts
    hero = facts["hero"].id
    friend = facts["friend"].id
    teacher = facts["teacher"].label
    place = facts["place"].description
    return [
        QAItem(
            question=f"What science activity were {hero} and {friend} watching at {place}?",
            answer=(
                f"With {teacher} supervising, they watched a small baking-soda-and-vinegar "
                f"demonstration in an open jar. The fizz made carbon dioxide bubbles."
            ),
        ),
        QAItem(
            question=f"What problem did {hero} and {friend} notice during the demonstration?",
            answer=(
                f"They noticed {facts['challenge']['label']}. {facts['answer']}"
            ),
        ),
        QAItem(
            question=f"How did {hero} and {friend} change what they were doing?",
            answer=(
                f"They paused and followed the safer plan: {facts['answer']} "
                f"{facts['consequence']}"
            ),
        ),
        QAItem(
            question="What did the rhyme teach the children about the bubbling jar?",
            answer=(
                "The rhyme reminded them to keep the jar open so carbon dioxide could escape. "
                "A tight lid could trap pressure and pop off."
            ),
        ),
        QAItem(
            question=f"Why did {hero} remind the club to wash its hands?",
            answer=(
                f"{hero} explained that germs are too tiny to see and can sometimes travel "
                f"on hands or shared tools. The children washed with soap and kept the "
                f"shared equipment clean."
            ),
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    del world
    return [
        QAItem(
            question="Why should a bubbling demonstration jar not be tightly sealed?",
            answer=(
                "Gas can build pressure inside a sealed container and may force the lid off. "
                "Children should only do science activities with a responsible adult and "
                "follow the activity's safety directions."
            ),
        ),
        QAItem(
            question="How can people help limit the spread of some germs?",
            answer=(
                "People can wash their hands with soap, cover coughs and sneezes with a tissue "
                "or elbow, and clean shared tools when needed. Germs are too small to see."
            ),
        ),
        QAItem(
            question="What is carbon dioxide?",
            answer=(
                "Carbon dioxide is a gas found in the air. Some safe, adult-supervised "
                "demonstrations make visible bubbles of it."
            ),
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = [
        "== prompts ==",
        *(f"{index}. {prompt}" for index, prompt in enumerate(sample.prompts, 1)),
        "",
        "== story qa ==",
    ]
    for item in sample.story_qa:
        lines.extend((f"Q: {item.question}", f"A: {item.answer}"))
    lines.extend(("", "== world qa =="))
    for item in sample.world_qa:
        lines.extend((f"Q: {item.question}", f"A: {item.answer}"))
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        lines.append(
            f"  {entity.id} ({entity.kind}/{entity.type}) "
            f"meters={entity.meters} memes={entity.memes}"
        )
    lines.append(f"  outcome={world.facts['turn']}")
    return "\n".join(lines)


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
        print("\n" + format_qa(sample))


CURATED = [
    StoryParams(
        place="greenhouse",
        challenge="cap",
        hero="Luna",
        friend="Pip",
        route="sunrise",
        seed=11,
    ),
    StoryParams(
        place="classroom",
        challenge="sneeze",
        hero="Kai",
        friend="Bea",
        route="bell",
        seed=22,
    ),
    StoryParams(
        place="courtyard",
        challenge="spill",
        hero="Zuri",
        friend="Tavi",
        route="checklist",
        seed=33,
    ),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        try:
            sys.exit(asp_verify())
        except ImportError as error:
            print(f"ASP verification needs clingo: {error}", file=sys.stderr)
            sys.exit(2)
    if args.asp:
        try:
            combos = asp_valid_combos()
        except ImportError as error:
            print(f"ASP mode needs clingo: {error}", file=sys.stderr)
            sys.exit(2)
        print(f"{len(combos)} compatible place/challenge pairs:\n")
        for place, challenge in combos:
            print(f"  {place:12} {challenge}")
        return

    if args.n < 1:
        print("StoryError: -n must be at least 1.", file=sys.stderr)
        return

    try:
        if args.all:
            # Validate any supplied filters even though --all uses the curated set.
            _check_choice("place", args.place, set(PLACES))
            _check_choice("challenge", args.challenge, set(CHALLENGES))
            _check_choice("hero", args.hero, set(HEROES))
            _check_choice("friend", args.friend, FRIENDS)
            _check_choice("route", args.route, set(ROUTES))
            samples = [generate(params) for params in CURATED]
        else:
            base_seed = args.seed if args.seed is not None else random.randrange(2**31)
            samples = []
            seen: set[str] = set()
            attempts = 0
            while len(samples) < args.n and attempts < max(args.n * 60, 60):
                seed = base_seed + attempts
                attempts += 1
                params = resolve_params(args, random.Random(seed))
                params.seed = seed
                sample = generate(params)
                if sample.story in seen:
                    continue
                seen.add(sample.story)
                samples.append(sample)
    except StoryError as error:
        print(f"StoryError: {error}", file=sys.stderr)
        return

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
        header = (
            "### curated story"
            if args.all
            else (f"### variant {index + 1}" if len(samples) > 1 else "")
        )
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
