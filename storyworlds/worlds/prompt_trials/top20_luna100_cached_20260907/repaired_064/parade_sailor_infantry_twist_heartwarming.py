#!/usr/bin/env python3
"""A heartwarming parade world about a sailor, infantry friends, and a gentle twist."""

from __future__ import annotations

# Locate the shared StoryWorld helpers from any batch depth.
from pathlib import Path as _StoryPath
import sys as _StorySys
_storyworlds_root = next(parent for parent in _StoryPath(__file__).resolve().parents
                        if (parent / 'results.py').is_file() and (parent / 'asp.py').is_file())
_StorySys.path.insert(0, str(_storyworlds_root.parent))
_StorySys.path.insert(0, str(_storyworlds_root))


import argparse
import hashlib
import json
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

ROOT = Path(__file__).resolve().parents[2]
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
class Scene:
    place: str
    weather: str
    mood: str


@dataclass
class StoryParams:
    place: str
    sailor: str
    infantry: str
    child: str
    keepsake: str
    twist: str
    route: str
    seed: Optional[int] = None


@dataclass(frozen=True)
class ParadePlan:
    trouble: str
    worry: str
    discovery: str
    repair: str
    lesson: str
    ending: str


PLACES = {
    "harbor_square": Scene("the harbor square", "a bright sea breeze", "cheerful"),
    "lighthouse_road": Scene("the lighthouse road", "a misty morning", "quiet"),
    "market_lane": Scene("the market lane", "a warm autumn wind", "busy"),
}

SAILORS = {
    "Captain Mira": "captain",
    "Sailor Ben": "sailor",
    "Sailor Nia": "sailor",
    "Chief Arun": "chief sailor",
}

INFANTRY = {
    "Corporal Rose": "infantry scout",
    "Private Eli": "infantry drummer",
    "Sergeant June": "infantry guide",
    "Private Sam": "infantry standard-bearer",
}

CHILDREN = {
    "Lena": "child",
    "Tom": "child",
    "Asha": "child",
    "Noah": "child",
}

KEEPSAKES = {
    "brass compass": "a small brass compass",
    "blue ribbon": "a faded blue ribbon",
    "wooden gull": "a carved wooden gull",
    "silver button": "a bright silver button",
}

TWISTS = {
    "gift": ParadePlan(
        "the sailor's old keepsake disappeared before the parade",
        "a sailor might have misplaced it while helping the infantry line",
        "the keepsake had been hidden inside the parade lantern by a child preparing a surprise",
        "the child returned it and showed a painted memory card made for the sailor",
        "a secret gift can become kinder when it is shared honestly",
        "the sailor carried the painted card beside the keepsake as the parade crossed the square",
    ),
    "memory": ParadePlan(
        "the sailor forgot the parade route and grew embarrassed",
        "the infantry thought the missing turn would spoil the ceremony",
        "the sailor remembered the route by following sounds and scents from an old homecoming day",
        "the infantry changed the plan so the sailor could lead the final turn safely",
        "asking for help can uncover a strong memory instead of a weakness",
        "the sailor and infantry marched together beneath the lighthouse bell",
    ),
    "lantern": ParadePlan(
        "the parade's leading lantern would not shine",
        "everyone feared the evening welcome would be dark",
        "a tiny mirror inside the lantern had turned toward the wall",
        "the sailor polished the mirror while the infantry held the lantern steady",
        "small repairs can brighten a celebration for everyone",
        "the repaired lantern glowed like a little moon above the marching friends",
    ),
    "letter": ParadePlan(
        "a thank-you letter for the sailor blew away",
        "the child who wrote it thought the sailor would never know",
        "the infantry found the letter caught in the flag rope",
        "they dried the page and read it aloud only after asking the child",
        "kind words matter even when they arrive in an unexpected way",
        "the sailor tucked the letter safely beside the flag as drums welcomed the crowd",
    ),
}

ROUTES = ("first_step", "quiet_start", "question_first", "memory_path", "lantern_path")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="A heartwarming parade story about a sailor and infantry friends."
    )
    parser.add_argument("--place", choices=sorted(PLACES))
    parser.add_argument("--sailor", choices=sorted(SAILORS))
    parser.add_argument("--infantry", choices=sorted(INFANTRY))
    parser.add_argument("--child", choices=sorted(CHILDREN))
    parser.add_argument("--keepsake", choices=sorted(KEEPSAKES))
    parser.add_argument("--twist", choices=sorted(TWISTS))
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--seed", type=int)
    for flag in ("all", "trace", "qa", "json", "asp", "verify", "show-asp"):
        parser.add_argument(f"--{flag}", action="store_true")
    return parser


ASP_RULES = """
compatible(P, S, I) :- place(P), sailor(S), infantry(I).
#show compatible/3.
"""


def asp_facts() -> str:
    import asp

    facts = []
    facts.extend(asp.fact("place", value) for value in PLACES)
    facts.extend(asp.fact("sailor", value) for value in SAILORS)
    facts.extend(asp.fact("infantry", value) for value in INFANTRY)
    return "\n".join(facts)


def asp_program(show: str = "#show compatible/3.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_combos() -> list[tuple[str, str, str]]:
    return [
        (place, sailor, infantry)
        for place in sorted(PLACES)
        for sailor in sorted(SAILORS)
        for infantry in sorted(INFANTRY)
    ]


def asp_valid_combos() -> list[tuple]:
    import asp

    symbols = asp.one_model(asp_program())
    return sorted(set(asp.atoms(symbols, "compatible")))


def asp_verify() -> int:
    python_values = set(valid_combos())
    asp_values = set(asp_valid_combos())
    if python_values == asp_values:
        print(f"OK: clingo gate matches valid_combos() ({len(python_values)} combinations).")
        return 0
    print("MISMATCH:")
    print("Python only:", sorted(python_values - asp_values))
    print("ASP only:", sorted(asp_values - python_values))
    return 1


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    choices = [
        combo
        for combo in valid_combos()
        if not args.place or combo[0] == args.place
        if not args.sailor or combo[1] == args.sailor
        if not args.infantry or combo[2] == args.infantry
    ]
    if not choices:
        raise StoryError("No parade can fit those place, sailor, and infantry choices.")

    place, sailor, infantry = rng.choice(choices)
    child = args.child or rng.choice(sorted(CHILDREN))
    keepsake = args.keepsake or rng.choice(sorted(KEEPSAKES))
    twist = args.twist or rng.choice(sorted(TWISTS))
    return StoryParams(
        place=place,
        sailor=sailor,
        infantry=infantry,
        child=child,
        keepsake=keepsake,
        twist=twist,
        route=rng.choice(ROUTES),
    )


def story_rng(params: StoryParams) -> random.Random:
    text = "|".join(
        str(value)
        for value in (
            params.seed,
            params.place,
            params.sailor,
            params.infantry,
            params.child,
            params.keepsake,
            params.twist,
            params.route,
        )
    )
    digest = hashlib.sha256(text.encode("utf-8")).digest()
    return random.Random(int.from_bytes(digest[:8], "big"))


class World:
    def __init__(self, scene: Scene) -> None:
        self.scene = scene
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, text: str) -> None:
        self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(part) for part in self.paragraphs if part)


def tell(params: StoryParams) -> World:
    scene = PLACES[params.place]
    plan = TWISTS[params.twist]
    rng = story_rng(params)
    world = World(scene)

    sailor = world.add(
        Entity(
            id=params.sailor,
            kind="character",
            type=SAILORS[params.sailor],
            memes={"courage": 1.0, "worry": 0.0},
        )
    )
    infantry = world.add(
        Entity(
            id=params.infantry,
            kind="character",
            type=INFANTRY[params.infantry],
            memes={"kindness": 1.0, "readiness": 1.0},
        )
    )
    child = world.add(
        Entity(
            id=params.child,
            kind="character",
            type=CHILDREN[params.child],
            memes={"hope": 1.0, "secret": 1.0},
        )
    )
    keepsake = world.add(
        Entity(
            id=params.keepsake,
            kind="object",
            type="keepsake",
            label=KEEPSAKES[params.keepsake],
            meters={"weight": 0.2, "distance": 0.0},
        )
    )

    openings = {
        "first_step": (
            f"At {scene.place}, the parade was ready to begin beneath {scene.weather}. "
            f"{params.sailor} stood beside the infantry line, carrying {keepsake.label}."
        ),
        "quiet_start": (
            f"The parade began quietly at {scene.place}, where {scene.weather} stirred the flags. "
            f"{params.sailor} checked {keepsake.label} before joining the infantry."
        ),
        "question_first": (
            f'"Is everyone ready?" asked {params.sailor} at {scene.place}. '
            f"The parade waited while the infantry gathered around {keepsake.label}."
        ),
        "memory_path": (
            f"{params.sailor} watched the flags ripple at {scene.place}. "
            f"The sight made the sailor think of home, even as the parade prepared to move."
        ),
        "lantern_path": (
            f"The first parade lantern trembled at {scene.place} under {scene.weather}. "
            f"{params.sailor} held {keepsake.label} close while the infantry formed a careful line."
        ),
    }
    world.say(openings[params.route])
    world.say(
        rng.choice(
            [
                f"{params.infantry} checked the drums and smiled at {params.child}, who held a folded card.",
                f"{params.child} waved from beside the infantry banner while {params.infantry} counted the marching steps.",
                f"The infantry stood proudly, but {params.infantry} noticed that {params.sailor} kept glancing toward the crowd.",
            ]
        )
    )
    world.para()

    world.say(f"Then {plan.trouble.capitalize()}.")
    sailor.memes["worry"] = 1.0
    sailor.meters["confidence"] = 0.6
    world.say(
        rng.choice(
            [
                f'"I do not want to delay the parade," {params.sailor} said softly.',
                f'"Everyone is waiting for us," {params.sailor} whispered, trying to hide the worry.',
                f"{params.sailor} took one careful breath while the crowd began to murmur.",
            ]
        )
    )
    world.say(
        rng.choice(
            [
                f'"We have time to understand what happened," {params.infantry} replied.',
                f'"A parade is made of people, not just steps," said {params.infantry}.',
                f'"Tell us what you need," {params.infantry} said, lowering the banner so the sailor could see clearly.',
            ]
        )
    )
    world.say(plan.worry.capitalize() + ".")
    world.para()

    world.say(
        rng.choice(
            [
                f"{params.child} remembered one small detail and pointed toward the parade lantern.",
                f"{params.infantry} followed a faint blue thread from the marching line to the flag rope.",
                f"{params.sailor} listened past the drums and noticed a familiar bell near the lighthouse road.",
                f"The friends paused instead of rushing, and the missing answer appeared in an unexpected place.",
            ]
        )
    )
    world.say(f"That was the twist: {plan.discovery}.")
    child.memes["secret"] = 0.0
    keepsake.meters["distance"] = 1.0
    sailor.meters["confidence"] = 1.0
    world.say(
        rng.choice(
            [
                f'"You made this for me?" {params.sailor} asked {params.child}.',
                f'"I wanted the parade to say thank you," {params.child} answered.',
                f'{params.infantry} smiled. "Sometimes the smallest clue carries the biggest kindness."',
            ]
        )
    )
    world.para()

    world.say(f"Together, the sailor and infantry {plan.repair}.")
    world.say(
        rng.choice(
            [
                f"{params.sailor} thanked {params.infantry} and knelt so {params.child} could see the keepsake safely.",
                f"The crowd grew quiet, then began to clap in a slow, warm rhythm.",
                f"Even the drummers softened their beat so nobody would miss the tender moment.",
            ]
        )
    )
    sailor.memes["worry"] = 0.0
    sailor.memes["belonging"] = 1.0
    infantry.memes["belonging"] = 1.0
    world.say(f"{params.sailor} shared the lesson: {plan.lesson}.")
    world.say(f"At last, {plan.ending.capitalize()}.")
    world.facts.update(
        sailor=sailor,
        infantry=infantry,
        child=child,
        keepsake=keepsake,
        plan=plan,
        scene=scene,
        twist=params.twist,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    facts = world.facts
    sailor: Entity = facts["sailor"]  # type: ignore[assignment]
    infantry: Entity = facts["infantry"]  # type: ignore[assignment]
    child: Entity = facts["child"]  # type: ignore[assignment]
    plan: ParadePlan = facts["plan"]  # type: ignore[assignment]
    return [
        f"Write a heartwarming parade story about {sailor.id}, a sailor, and {infantry.id}, an infantry friend.",
        f"Include a brief dialogue in which {child.id} changes what the sailor decides to do.",
        f"Use this gentle twist: {plan.discovery}. End with {plan.ending}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    facts = world.facts
    sailor: Entity = facts["sailor"]  # type: ignore[assignment]
    infantry: Entity = facts["infantry"]  # type: ignore[assignment]
    child: Entity = facts["child"]  # type: ignore[assignment]
    keepsake: Entity = facts["keepsake"]  # type: ignore[assignment]
    plan: ParadePlan = facts["plan"]  # type: ignore[assignment]
    scene: Scene = facts["scene"]  # type: ignore[assignment]
    return [
        QAItem(
            question=f"What was {sailor.id} carrying when the parade gathered at {scene.place}?",
            answer=f"{sailor.id} was carrying {keepsake.label} while preparing to march with the infantry.",
        ),
        QAItem(
            question=f"What problem made {sailor.id} worry before the parade began?",
            answer=f"{plan.trouble.capitalize()}, so {sailor.id} worried that the parade would be delayed or spoiled.",
        ),
        QAItem(
            question=f"How did {infantry.id} help {sailor.id}?",
            answer=f"{infantry.id} stayed calm, listened to what {sailor.id} needed, and helped find a kind solution instead of rushing.",
        ),
        QAItem(
            question=f"What did {child.id} reveal in the twist?",
            answer=f"{child.id} revealed that {plan.discovery}. The surprising truth turned the worry into a thoughtful gift or discovery.",
        ),
        QAItem(
            question="What changed by the end of the parade?",
            answer=f"The friends {plan.repair}. {sailor.id} learned that {plan.lesson}, and the parade ended with everyone feeling included.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does a sailor do?",
            answer="A sailor works on or around boats and ships, learning to travel safely on the water and help a crew.",
        ),
        QAItem(
            question="What is infantry?",
            answer="Infantry are soldiers who serve and move mainly on foot. In this gentle story, the infantry friends also help their community.",
        ),
        QAItem(
            question="Why can a parade feel special?",
            answer="A parade brings people together through music, flags, shared memories, and welcoming gestures.",
        ),
        QAItem(
            question="Why is a story twist heartwarming?",
            answer="A heartwarming twist changes a worry into understanding, kindness, or a surprise that helps people feel closer.",
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
    lines.append("")
    lines.append("== world qa ==")
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
    plan: ParadePlan = world.facts["plan"]  # type: ignore[assignment]
    lines.append(f"  twist={world.facts['twist']}")
    lines.append(f"  discovery={plan.discovery}")
    lines.append(f"  ending={plan.ending}")
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
        place="harbor_square",
        sailor="Captain Mira",
        infantry="Corporal Rose",
        child="Lena",
        keepsake="brass compass",
        twist="gift",
        route="first_step",
        seed=101,
    ),
    StoryParams(
        place="lighthouse_road",
        sailor="Sailor Ben",
        infantry="Private Eli",
        child="Asha",
        keepsake="blue ribbon",
        twist="memory",
        route="memory_path",
        seed=202,
    ),
    StoryParams(
        place="market_lane",
        sailor="Sailor Nia",
        infantry="Sergeant June",
        child="Noah",
        keepsake="wooden gull",
        twist="lantern",
        route="lantern_path",
        seed=303,
    ),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return

    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        combinations = asp_valid_combos()
        print(f"{len(combinations)} compatible parade combinations:\n")
        for place, sailor, infantry in combinations:
            print(f"  {place:16} {sailor:16} {infantry}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        samples: list[StorySample] = []
        seen: set[str] = set()
        attempts = 0
        while len(samples) < args.n and attempts < max(args.n * 50, 50):
            current_seed = base_seed + attempts
            attempts += 1
            try:
                params = resolve_params(args, random.Random(current_seed))
            except StoryError as error:
                print(error)
                return
            params.seed = current_seed
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)

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
        if args.all:
            header = "### curated story"
        elif len(samples) > 1:
            header = f"### variant {index + 1}"
        else:
            header = ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
