#!/usr/bin/env python3
"""A heartwarming parade world about a sailor, an infantry drummer, and a kind twist."""

from __future__ import annotations

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
    instrument: str
    twist: str
    route: str
    seed: Optional[int] = None


@dataclass(frozen=True)
class ParadePlan:
    missing: str
    worry: str
    first_plan: str
    setback: str
    hidden_truth: str
    repair: str
    lesson: str
    ending: str


@dataclass
class World:
    scene: Scene
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict[str, object] = field(default_factory=dict)

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


PLACES = {
    "harbor_square": Scene("the harbor square", "a soft sea breeze", "bright and busy"),
    "town_green": Scene("the town green", "a warm golden wind", "green and cheerful"),
    "lighthouse_road": Scene("the road beneath the lighthouse", "a cool salt breeze", "white and shining"),
}

SAILORS = {
    "Captain Mira": "captain",
    "Sailor Ben": "sailor",
    "Sailor Rosa": "sailor",
    "Sailor Eli": "sailor",
}

INFANTRY = {
    "Corporal June": "infantry drummer",
    "Private Arun": "infantry marcher",
    "Sergeant Mae": "infantry guide",
    "Private Tomas": "infantry marcher",
}

CHILDREN = {
    "Luna": "girl",
    "Pip": "boy",
    "Nia": "girl",
    "Sam": "boy",
}

INSTRUMENTS = {
    "drum": "a bright parade drum",
    "bell": "a silver handbell",
    "trumpet": "a small brass trumpet",
    "whistle": "a wooden boatswain's whistle",
}

TWISTS = {
    "lost_banner": ParadePlan(
        "the blue harbor banner",
        "the sailor's banner vanished just before the parade began",
        "searched the supply cart and the flagpoles",
        "the cart was empty, and the wind kept turning everyone toward the wrong street",
        "the banner had been folded inside the quiet drum case to protect it from a sudden shower",
        "opened the case, dried the banner, and invited the youngest marchers to carry it",
        "a hidden kindness can look like a problem until someone asks why",
        "the blue banner floated above the parade while the drummer walked beside the child who had saved it",
    ),
    "silent_drum",
    ParadePlan(
        "the drum's clear parade beat",
        "the infantry drummer could not make the drum speak",
        "checked the drumskin, the sticks, and the marching route",
        "every part looked ready, but the drum stayed silent whenever the crowd watched",
        "the drummer was saving the first beat for a homesick sailor who had never heard a town parade",
        "let the sailor give the opening tap and marched at a gentle pace",
        "sharing the important moment can make courage return",
        "one brave tap became a warm rolling rhythm all the way to the harbor",
    ),
    "crooked_route",
    ParadePlan(
        "the parade route to the sailors' welcome table",
        "the map sent the marchers toward a locked gate",
        "followed the chalk arrows and asked the harbor keeper for help",
        "the arrows had been washed into crooked loops by the morning rain",
        "a child had redrawn the route so a tired sailor could pass the shortest, smoothest way",
        "moved the welcome table beside the lighthouse and thanked the careful mapmaker",
        "a small change can make a welcome easier for someone else",
        "the sailors rested beneath the lighthouse while the infantry led a shorter, happier parade",
    ),
    "missing_ribbon",
    ParadePlan(
        "the red ribbon for the oldest sailor",
        "the ribbon disappeared from the welcome basket",
        "looked beneath the chairs and along the marching line",
        "they found red leaves and red flags, but no ribbon",
        "the ribbon had been tied around a shy sailor's hand so he would know he belonged",
        "wove a larger ribbon circle and welcomed every new marcher into it",
        "belonging is something people can make together",
        "the ribbon circle stretched from the sailor to the infantry and around the smiling crowd",
    ),
    "rainy_finish",
    ParadePlan(
        "the parade's final song",
        "rain clouds gathered before the last song could be played",
        "waited beneath the covered market and practiced softly",
        "the wind scattered the song cards across the wet stones",
        "the sailor knew the melody by heart because it was the song his family sang at sea",
        "followed the sailor's humming and turned the final song into a gentle chorus",
        "a remembered song can carry everyone when plans are blown away",
        "rain drummed on the roof while the whole parade sang together",
    ),
    "empty_chair",
    ParadePlan(
        "a chair reserved for a sailor's little brother",
        "one chair stood empty at the front of the parade",
        "asked the harbor families whether anyone knew where he was",
        "the crowd searched the square, but the child was not lost",
        "he had been helping an elderly infantry veteran reach the parade safely",
        "made room for both of them and placed the chair beside the band",
        "helping someone arrive can be the finest part of a celebration",
        "the empty chair became two seats filled with applause and shining eyes",
    ),
}

ROUTES = ("banner_first", "music_first", "map_first", "kindness_first", "weather_first", "quiet_first")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="A heartwarming parade world with a sailor and infantry.")
    parser.add_argument("--place", choices=sorted(PLACES))
    parser.add_argument("--sailor", choices=sorted(SAILORS))
    parser.add_argument("--infantry", choices=sorted(INFANTRY))
    parser.add_argument("--child", choices=sorted(CHILDREN))
    parser.add_argument("--instrument", choices=sorted(INSTRUMENTS))
    parser.add_argument("--twist", choices=sorted(TWISTS))
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--seed", type=int)
    for flag in ("all", "trace", "qa", "json", "asp", "verify", "show-asp"):
        parser.add_argument(f"--{flag}", action="store_true")
    return parser


def valid_combos() -> list[tuple[str, str, str]]:
    return [
        (place, instrument, twist)
        for place in sorted(PLACES)
        for instrument in sorted(INSTRUMENTS)
        for twist in sorted(TWISTS)
    ]


ASP_RULES = """
valid(Place, Instrument, Twist) :-
    place(Place),
    instrument(Instrument),
    twist(Twist).
"""


def asp_facts() -> str:
    import asp

    return "\n".join(
        [
            *(asp.fact("place", value) for value in PLACES),
            *(asp.fact("instrument", value) for value in INSTRUMENTS),
            *(asp.fact("twist", value) for value in TWISTS),
        ]
    )


def asp_program(show: str = "#show valid/3.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    symbols = asp.one_model(asp_program())
    return sorted(set(asp.atoms(symbols, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combinations).")
        return 0
    print("MISMATCH:")
    print("Python only:", sorted(py - cl))
    print("ASP only:", sorted(cl - py))
    return 1


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    choices = [
        combo
        for combo in valid_combos()
        if not args.place or combo[0] == args.place
        if not args.instrument or combo[1] == args.instrument
        if not args.twist or combo[2] == args.twist
    ]
    if not choices:
        raise StoryError("No valid parade story fits those options.")

    place, instrument, twist = rng.choice(choices)
    sailor = args.sailor or rng.choice(sorted(SAILORS))
    infantry = args.infantry or rng.choice(sorted(INFANTRY))
    child = args.child or rng.choice(sorted(CHILDREN))
    return StoryParams(
        place=place,
        sailor=sailor,
        infantry=infantry,
        child=child,
        instrument=instrument,
        twist=twist,
        route=rng.choice(ROUTES),
    )


def story_rng(params: StoryParams) -> random.Random:
    key = "|".join(
        str(value)
        for value in (
            params.seed,
            params.place,
            params.sailor,
            params.infantry,
            params.child,
            params.instrument,
            params.twist,
            params.route,
        )
    )
    digest = hashlib.sha256(key.encode("utf-8")).digest()
    return random.Random(int.from_bytes(digest[:8], "big"))


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
            memes={"homesick": 1.0, "hope": 0.0},
        )
    )
    infantry = world.add(
        Entity(
            id=params.infantry,
            kind="character",
            type=INFANTRY[params.infantry],
            meters={"marching_strength": 1.0},
            memes={"patience": 1.0},
        )
    )
    child = world.add(
        Entity(
            id=params.child,
            kind="character",
            type=CHILDREN[params.child],
            memes={"curiosity": 1.0, "kindness": 1.0},
        )
    )
    instrument = world.add(
        Entity(
            id=params.instrument,
            kind="object",
            type="instrument",
            label=INSTRUMENTS[params.instrument],
            meters={"readiness": 1.0},
        )
    )

    openings = {
        "banner_first": (
            f"At {scene.place}, {child.id} arrived before the parade and saw {scene.weather} "
            f"lifting every flag. The {plan.missing} was already causing a worried murmur."
        ),
        "music_first": (
            f"The first sound at {scene.place} was supposed to be {instrument.label}, "
            f"but the parade had not yet found its opening note. Then {child.id} heard that {plan.missing}."
        ),
        "map_first": (
            f"{child.id} held the parade map at {scene.place}, where the day felt {scene.mood}. "
            f"One mark on the map led to a problem: {plan.missing}."
        ),
        "kindness_first": (
            f"Before the parade began at {scene.place}, {child.id} noticed {sailor.id} standing quietly apart. "
            f"Nearby, {plan.missing}."
        ),
        "weather_first": (
            f"{scene.weather.capitalize()} moved through {scene.place} as the parade gathered. "
            f"Everyone hurried when they learned that {plan.missing}."
        ),
        "quiet_first": (
            f"For one quiet moment, {scene.place} seemed ready for a parade. Then {child.id} noticed "
            f"that {plan.missing}."
        ),
    }
    world.say(openings[params.route])
    world.say(
        rng.choice(
            [
                f"{infantry.id}, the infantry guide, checked the marching line while {sailor.id} held the welcome flag.",
                f"{sailor.id} smiled bravely, and {infantry.id} counted the careful steps of the infantry.",
                f"{child.id} carried a little ribbon and promised to help wherever the parade needed help.",
                f"The sailor and the infantry stood together, but both waited for someone to explain the trouble.",
            ]
        )
    )
    world.para()

    world.say(
        rng.choice(
            [
                f'"We must hurry," said {infantry.id}. "{plan.worry.capitalize()}"',
                f'"What shall we do?" asked {child.id}. {sailor.id} pointed toward the silent parade line.',
                f'"The parade cannot begin like this," whispered {sailor.id}. {infantry.id} looked at the waiting families.',
                f'{child.id} asked, "Who needs our help first?" The question made everyone stop and listen.',
            ]
        )
    )
    world.say(f"{plan.first_plan.capitalize()}.")
    child.meters["steps_taken"] = 1.0
    infantry.meters["searches_completed"] = 1.0
    world.say(
        rng.choice(
            [
                f"They searched carefully, but {plan.setback}.",
                f"That plan seemed sensible until {plan.setback}.",
                f"The sailor, the infantry, and {child.id} tried together. Still, {plan.setback}.",
            ]
        )
    )
    world.say(
        rng.choice(
            [
                f'"Let us ask what happened before we guess," {child.id} said.',
                f'"A parade is made of people, not only marching," {sailor.id} replied gently.',
                f'"Look for the reason, not just the missing thing," said {infantry.id}.',
                f'{child.id} took a breath. "Someone may have been helping in a way we cannot see yet."',
            ]
        )
    )
    world.para()

    world.say(f"That kind question revealed the twist: {plan.hidden_truth.capitalize()}.")
    world.say(
        rng.choice(
            [
                f"The sailor's worried face softened, and the infantry lowered its hurried pace.",
                f"Everyone understood that the problem had been hiding a good intention.",
                f"{child.id} smiled because the strange clue now made sense.",
                f"The parade changed shape as soon as the truth was known.",
            ]
        )
    )
    sailor.memes["homesick"] = 0.0
    sailor.memes["hope"] = 1.0
    child.memes["kindness"] = 2.0
    world.say(f"Together, they {plan.repair}.")
    infantry.meters["marching_strength"] = 2.0
    instrument.meters["readiness"] = 2.0
    world.para()

    world.say(
        rng.choice(
            [
                f'{sailor.id} said, "Thank you for seeing the person inside the problem."',
                f'"Now this feels like a real welcome," {infantry.id} said.',
                f'{child.id} answered, "Everyone should have a place in the parade."',
                f'The sailor laughed softly. "Your kindness gave us the best marching order."',
            ]
        )
    )
    world.say(f"{child.id} remembered the lesson: {plan.lesson}.")
    world.say(
        rng.choice(
            [
                f"At last, {plan.ending.capitalize()}.",
                f"When the parade moved on, {plan.ending.capitalize()}.",
                f"The final picture was simple and bright: {plan.ending}.",
                f"By sunset, {plan.ending.capitalize()}.",
            ]
        )
    )

    world.facts.update(
        sailor=sailor,
        infantry=infantry,
        child=child,
        instrument=instrument,
        plan=plan,
        scene=scene,
        twist=params.twist,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    facts = world.facts
    plan: ParadePlan = facts["plan"]  # type: ignore[assignment]
    sailor: Entity = facts["sailor"]  # type: ignore[assignment]
    infantry: Entity = facts["infantry"]  # type: ignore[assignment]
    child: Entity = facts["child"]  # type: ignore[assignment]
    return [
        f"Write a heartwarming parade story about {child.id}, {sailor.id}, and {infantry.id}.",
        f"Include {facts['instrument'].label}, a problem involving {plan.missing}, and a kind twist revealing that {plan.hidden_truth}.",
        f"End with a joyful parade image that proves {child.id} helped {sailor.id} feel welcome.",
    ]


def story_qa(world: World) -> list[QAItem]:
    facts = world.facts
    plan: ParadePlan = facts["plan"]  # type: ignore[assignment]
    sailor: Entity = facts["sailor"]  # type: ignore[assignment]
    infantry: Entity = facts["infantry"]  # type: ignore[assignment]
    child: Entity = facts["child"]  # type: ignore[assignment]
    scene: Scene = facts["scene"]  # type: ignore[assignment]
    return [
        QAItem(
            question=f"What problem interrupted the parade at {scene.place}?",
            answer=f"The problem was that {plan.missing}. This made the sailor, the infantry, and {child.id} worry before the parade could begin.",
        ),
        QAItem(
            question=f"How did {child.id} change the search with a question?",
            answer=f"{child.id} asked what had happened before anyone guessed. That encouraged the group to look for a helpful reason instead of blaming someone.",
        ),
        QAItem(
            question=f"What twist did {sailor.id} and {infantry.id} discover?",
            answer=f"They discovered that {plan.hidden_truth}. The missing item or changed plan was connected to kindness rather than carelessness.",
        ),
        QAItem(
            question=f"How did the group repair the parade?",
            answer=f"Together, they {plan.repair}. This let the parade continue while making the welcome more thoughtful.",
        ),
        QAItem(
            question=f"What lesson did {child.id} remember at the end?",
            answer=f"{child.id} remembered that {plan.lesson}. The ending showed this lesson through a warm parade shared by the sailor, the infantry, and the children.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a parade?",
            answer="A parade is an organized procession in which people move together, often with music, flags, uniforms, or decorations.",
        ),
        QAItem(
            question="What does a sailor do?",
            answer="A sailor works or travels on a ship and helps care for the vessel, its route, and the people aboard it.",
        ),
        QAItem(
            question="What is infantry?",
            answer="Infantry are soldiers who move and work on foot. In a peaceful parade story, they can march together with careful steps and music.",
        ),
        QAItem(
            question="Why can a twist make a story heartwarming?",
            answer="A twist can reveal that a confusing action came from care or generosity. The new understanding helps characters forgive one another and share joy.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    lines.extend(f"{index}. {prompt}" for index, prompt in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== story qa ==")
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
    lines.append(f"  hidden_truth={plan.hidden_truth}")
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
        sailor="Sailor Ben",
        infantry="Corporal June",
        child="Luna",
        instrument="drum",
        twist="lost_banner",
        route="banner_first",
        seed=101,
    ),
    StoryParams(
        place="town_green",
        sailor="Captain Mira",
        infantry="Private Arun",
        child="Pip",
        instrument="bell",
        twist="silent_drum",
        route="music_first",
        seed=202,
    ),
    StoryParams(
        place="lighthouse_road",
        sailor="Sailor Rosa",
        infantry="Sergeant Mae",
        child="Nia",
        instrument="trumpet",
        twist="empty_chair",
        route="kindness_first",
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
        print(f"{len(combinations)} compatible combinations:\n")
        for place, instrument, twist in combinations:
            print(f"  {place:16} {instrument:10} {twist}")
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
        emit(
            sample,
            trace=args.trace,
            qa=args.qa,
            header=(
                "### curated story"
                if args.all
                else f"### variant {index + 1}" if len(samples) > 1 else ""
            ),
        )
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
