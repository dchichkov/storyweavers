#!/usr/bin/env python3
"""A superhero storyworld about germs, carbon dioxide, and careful choices."""

from __future__ import annotations

import argparse
import hashlib
import json
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

for _parent in Path(__file__).resolve().parents:
    if (_parent / "results.py").is_file():
        sys.path.insert(0, str(_parent))
        break

from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str
    type: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass(frozen=True)
class Mission:
    key: str
    setting: str
    activity: str
    shared_item: str
    germ_path: str
    source_code: str
    cleaning_code: str
    cleaning_action: str
    vent: str
    air_code: str
    closure_reason: str
    teacher: str
    plant: str
    ending_image: str


@dataclass
class StoryParams:
    mission: str
    hero: str
    partner: str
    power: str
    route: str
    seed: Optional[int] = None


class World:
    """Small live state model: observations lead to separate, sensible actions."""

    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.events: list[str] = []

    def add(self, entity: Entity) -> Entity:
        if entity.id in self.entities:
            raise StoryError(f"Duplicate world entity: {entity.id}")
        self.entities[entity.id] = entity
        return entity

    def say(self, text: str) -> None:
        self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def record(self, event: str) -> None:
        self.events.append(event)

    def render(self) -> str:
        return "\n\n".join(" ".join(part) for part in self.paragraphs if part)


MISSIONS = {
    "greenhouse": Mission(
        key="greenhouse",
        setting="the school greenhouse",
        activity="planting bean seeds for the spring fair",
        shared_item="the watering-can handle",
        germ_path=(
            "A soil-smudged glove had touched the watering-can handle before "
            "the children passed the can around."
        ),
        source_code="soil_glove",
        cleaning_code="care_instructions",
        cleaning_action="cleaned the watering-can handle according to its care instructions",
        vent="roof vent",
        air_code="screened_roof_vent",
        closure_reason="to keep a gust from scattering the seed labels",
        teacher="Ms. Vale",
        plant="bean seedlings",
        ending_image=(
            "bean seedlings stood by the clean watering can, their seed labels "
            "held steady with smooth stones"
        ),
    ),
    "maker_room": Mission(
        key="maker_room",
        setting="the school maker room",
        activity="making paper pinwheels beside a pot of basil",
        shared_item="the shared ruler",
        germ_path=(
            "After handling sticky glue, several children had passed the same "
            "ruler from hand to hand."
        ),
        source_code="gluey_hands",
        cleaning_code="care_instructions",
        cleaning_action="cleaned the shared ruler according to its care instructions",
        vent="high window",
        air_code="screened_high_window",
        closure_reason="to stop a draft from flipping the paper pinwheels",
        teacher="Mr. Moss",
        plant="basil",
        ending_image=(
            "the clean ruler lay beside a row of paper pinwheels, and the basil "
            "leaves nodded"
        ),
    ),
    "garden_classroom": Mission(
        key="garden_classroom",
        setting="the community garden classroom",
        activity="painting markers for the sunflower beds",
        shared_item="the marker tub",
        germ_path=(
            "The marker tub had passed among children returning from the garden "
            "before anyone stopped at the sink."
        ),
        source_code="garden_hands",
        cleaning_code="care_instructions",
        cleaning_action="cleaned the marker tub according to its care instructions",
        vent="side vent",
        air_code="screened_side_vent",
        closure_reason="to keep drizzle from reaching the fair displays",
        teacher="Ms. Jun",
        plant="sunflower seedlings",
        ending_image=(
            "sunflower seedlings leaned toward the light while the clean marker "
            "tub waited beside bright new signs"
        ),
    ),
}

HEROES = ("Ari", "Luna", "Milo", "Nia", "Theo", "Zuri")
POWERS = {
    "star_badge": "their star badge flashed a bright pause signal",
    "steady_shield": "their clear shield held the loose fair labels in place",
    "super_hearing": "their super-hearing caught the paper streamer tapping gently",
    "moonbeam_signal": "a soft moonbeam signal gathered everyone's attention",
}
ROUTES = ("germ_first", "air_first", "cape_first", "question_first")

ASP_RULES = """
valid(Mission, Source, Cleaning, AirPlan) :-
    mission(Mission),
    source(Mission, Source),
    clean(Mission, Cleaning),
    vent(Mission, AirPlan).
"""


@dataclass(frozen=True)
class SceneChoice:
    arrival: str
    joke: str
    hero_reply: str
    ending_lead: str


def valid_combinations() -> list[tuple[str, str, str, str]]:
    """The Python reasonableness gate for a mission's complete safe plan."""
    return sorted(
        (
            mission.key,
            mission.source_code,
            mission.cleaning_code,
            mission.air_code,
        )
        for mission in MISSIONS.values()
    )


def validate_params(params: StoryParams) -> None:
    if params.mission not in MISSIONS:
        raise StoryError(f"Unknown mission: {params.mission!r}.")
    if params.hero not in HEROES:
        raise StoryError(f"Unknown superhero name: {params.hero!r}.")
    if params.partner not in HEROES:
        raise StoryError(f"Unknown partner name: {params.partner!r}.")
    if params.hero == params.partner:
        raise StoryError("The superhero and partner must be different people.")
    if params.power not in POWERS:
        raise StoryError(f"Unknown superhero power: {params.power!r}.")
    if params.route not in ROUTES:
        raise StoryError(f"Unknown story route: {params.route!r}.")
    combination = next(
        (
            combo
            for combo in valid_combinations()
            if combo[0] == params.mission
        ),
        None,
    )
    if combination is None:
        raise StoryError("No reasonable safety plan fits that mission.")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="A superhero story about germs, carbon dioxide, and fresh air."
    )
    parser.add_argument("--mission", choices=sorted(MISSIONS))
    parser.add_argument("--hero", choices=HEROES)
    parser.add_argument("--partner", choices=HEROES)
    parser.add_argument("--power", choices=sorted(POWERS))
    parser.add_argument("--route", choices=ROUTES)
    parser.add_argument("-n", type=int, default=1, help="number of stories")
    parser.add_argument("--seed", type=int)
    for flag in ("all", "trace", "qa", "json", "asp", "verify", "show-asp"):
        parser.add_argument(f"--{flag}", action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_combinations()
    if args.mission:
        combos = [combo for combo in combos if combo[0] == args.mission]
    if not combos:
        raise StoryError("No reasonable safety plan fits those options.")

    mission = rng.choice(combos)[0]
    hero = args.hero or rng.choice(HEROES)
    if args.partner:
        partner = args.partner
    else:
        choices = [name for name in HEROES if name != hero]
        partner = rng.choice(choices)

    if hero == partner:
        raise StoryError("The superhero and partner must be different people.")

    return StoryParams(
        mission=mission,
        hero=hero,
        partner=partner,
        power=args.power or rng.choice(sorted(POWERS)),
        route=args.route or rng.choice(ROUTES),
    )


def story_rng(params: StoryParams) -> random.Random:
    text = "|".join(
        str(value)
        for value in (
            params.seed,
            params.mission,
            params.hero,
            params.partner,
            params.power,
            params.route,
        )
    )
    digest = hashlib.sha256(text.encode("utf-8")).digest()
    return random.Random(int.from_bytes(digest[:8], "big"))


def scene_choice(rng: random.Random) -> SceneChoice:
    return SceneChoice(
        arrival=rng.choice(
            (
                "A bright fair banner waved above the tables.",
                "The fair bell waited on its hook, ready to ring.",
                "A paper star marked the team's table.",
            )
        ),
        joke=rng.choice(
            (
                "Captain {hero}'s cape puffed up like a lopsided tent. "
                "{partner} said, “Your cape is ready for camping, not crime-fighting!”",
                "A fair label stuck to Captain {hero}'s cape like a medal. "
                "{partner} grinned: “It says BEANS, not BEST HERO!”",
                "Captain {hero}'s cape curled around one elbow. "
                "{partner} said, “Your cape has captured its own superhero!”",
                "A streamer tickled Captain {hero}'s shoulder. "
                "{partner} whispered, “The breeze is trying to give you a high-five.”",
            )
        ),
        hero_reply=rng.choice(
            (
                "“A careful pause is part of the mission. Let's check both clues.”",
                "“We can save the fair and make a smart plan. First, let's ask.”",
                "“No guessing when a kind question can help us choose.”",
            )
        ),
        ending_lead=rng.choice(
            (
                "When the fair bell rang,",
                "Soon the visitors arrived, and",
                "At last, the team opened the fair with",
                "The next breeze brought the first fair visitors, who saw",
            )
        ),
    )


def simulate(params: StoryParams) -> World:
    validate_params(params)
    mission = MISSIONS[params.mission]
    rng = story_rng(params)
    choice = scene_choice(rng)
    world = World()

    hero = world.add(
        Entity(
            id=params.hero,
            kind="character",
            type="superhero",
            label=params.hero,
            meters={"clue_checks": 0.0, "helpfulness": 0.5},
            memes={"curiosity": 0.7, "confidence": 0.4, "worry": 0.3},
        )
    )
    partner = world.add(
        Entity(
            id=params.partner,
            kind="character",
            type="child",
            label=params.partner,
            meters={"hands_washed": 0.0},
            memes={"curiosity": 0.8, "worry": 0.4, "trust": 0.6},
        )
    )
    teacher = world.add(
        Entity(
            id=mission.teacher,
            kind="character",
            type="teacher",
            label=mission.teacher,
            meters={"vent_checked": 0.0, "tool_cleaned": 0.0},
            memes={"patience": 0.9},
        )
    )
    shared_item = world.add(
        Entity(
            id=mission.shared_item,
            kind="object",
            type="shared_tool",
            label=mission.shared_item,
            meters={"needs_cleaning": 1.0, "transfer_concern": 0.75},
            memes={"care_needed": 1.0},
        )
    )
    vent = world.add(
        Entity(
            id=mission.vent,
            kind="object",
            type="screened_vent",
            label=mission.vent,
            meters={"open": 0.0, "air_movement": 0.05},
            memes={},
        )
    )
    room = world.add(
        Entity(
            id=mission.setting,
            kind="place",
            type="indoor_room",
            label=mission.setting,
            meters={"air_exchange": 0.05, "people_breathing": 1.0},
            memes={"calm": 0.5},
        )
    )
    poster = world.add(
        Entity(
            id="safety poster",
            kind="object",
            type="cartoon",
            label="cartoon Germ Gremlin",
            meters={},
            memes={"warning": 1.0},
        )
    )
    plant = world.add(
        Entity(
            id=mission.plant,
            kind="living_thing",
            type="plant",
            label=mission.plant,
            meters={"sunlight": 0.7},
            memes={},
        )
    )

    world.facts.update(
        mission=mission,
        hero=hero,
        partner=partner,
        teacher=teacher,
        shared_item=shared_item,
        vent=vent,
        room=room,
        poster=poster,
        plant=plant,
        params=params,
    )

    world.say(
        f"{choice.arrival} At {mission.setting}, Captain {hero.id} and "
        f"{partner.id} were {mission.activity}. The screened {mission.vent} "
        f"was closed {mission.closure_reason}, so the room had little breeze."
    )
    world.record("The team arrived while the screened vent was closed.")

    if params.route == "germ_first":
        world.say(
            f"A faint smudge on {mission.shared_item} caught "
            f"{partner.id}'s attention."
        )
    elif params.route == "air_first":
        world.say(
            f"A paper streamer above the screened {mission.vent} barely stirred."
        )
    elif params.route == "cape_first":
        world.say(
            f"Captain {hero.id}'s cape caught briefly on a fair label; "
            f"the superhero carefully freed it."
        )
    else:
        world.say(
            f"“Should we wash before the snack?” {partner.id} asked, "
            f"eyeing the apple slices."
        )

    germ_observation = (
        f"{mission.germ_path} Germs are too small to see, so this was a reason "
        "to pause and clean, not proof that a harmful germ was present."
    )
    air_observation = (
        f"The streamer above the screened {mission.vent} hardly moved. It "
        "showed little air movement there; it could not detect germs or "
        "carbon dioxide."
    )
    if params.route in ("air_first", "question_first"):
        world.say(air_observation)
        world.say(germ_observation)
    else:
        world.say(germ_observation)
        world.say(air_observation)

    hero.meters["clue_checks"] += 2.0
    world.record("The team noticed a shared-tool concern and still air.")
    world.para()

    world.say(
        f"The fair bell was close, and the apple slices were ready. "
        f"{partner.id} worried that stopping would delay the visitors."
    )
    world.say(
        f"“Does carbon dioxide mean there is a germ in the air?” "
        f"{partner.id} asked."
    )
    world.say(
        f"“I don't know yet,” Captain {hero.id} replied. "
        f"“A real hero checks instead of guessing. {mission.teacher}, can you help?”"
    )
    world.say(
        f"“They are different things,” {teacher.id} explained. “People breathe "
        "out carbon dioxide, and plants use it with sunlight to make food. "
        "The streamer shows that little air is moving; it is not a gas test. "
        "Opening this screened vent brings in fresh air, but it will not clean "
        "a shared tool.”"
    )
    world.say(
        f"“Then let's pause the snack, clean {mission.shared_item}, and wash "
        f"our hands,” Captain {hero.id} said. “Could you open the vent a little?”"
    )
    world.say(
        f"“I can do that, and I will clean the tool by its care instructions,” "
        f"{teacher.id} answered. “You two can wash up.”"
    )
    world.record("The team learned that carbon dioxide and germs are different.")
    world.para()

    world.say(
        f"Captain {hero.id} used {POWERS[params.power]}. A cartoon Germ "
        f"Gremlin grinned from the safety poster, but the drawing was only a "
        "reminder—not a germ anyone could see."
    )
    world.say(choice.joke.format(hero=hero.id, partner=partner.id))
    world.say(
        f"Captain {hero.id} called out, “Before you eat, wash hands—don't delay; "
        "soap, rinse, dry, then save the day! Clean shared tools with grown-up "
        "care; for fresh air, ask an adult there.”"
    )
    world.say(
        f"{partner.id} smiled. “I'll keep the apple slices covered while we "
        "wash, and help hold the fair labels!”"
    )
    world.para()

    world.say(
        f"At the sink, {hero.id} and {partner.id} washed their hands with soap "
        "and water, rinsed, and dried them. "
        f"{teacher.id} {mission.cleaning_action}."
    )
    partner.meters["hands_washed"] = 1.0
    shared_item.meters["needs_cleaning"] = 0.0
    shared_item.meters["transfer_concern"] = 0.12
    shared_item.memes["care_needed"] = 0.0
    teacher.meters["tool_cleaned"] = 1.0
    world.record("The children washed; the adult cleaned the shared tool.")

    world.say(
        f"{teacher.id} opened the screened {mission.vent} a little. The "
        "streamer lifted and fluttered, showing that air was moving again."
    )
    vent.meters["open"] = 1.0
    vent.meters["air_movement"] = 0.75
    room.meters["air_exchange"] = 0.72
    teacher.meters["vent_checked"] = 1.0
    hero.memes["confidence"] = 0.85
    partner.memes["worry"] = 0.1
    partner.memes["trust"] = 0.9
    room.memes["calm"] = 0.85
    world.record("The adult opened the screened vent for fresh air.")

    if shared_item.meters["needs_cleaning"] == 0.0 and room.meters["air_exchange"] > 0.5:
        world.say(
            "Fresh air and a clean shared tool came from two different helpful "
            "steps; neither step pretended to do the other's job."
        )
    world.say(
        f"{choice.ending_lead} {mission.ending_image}. The cartoon Germ "
        f"Gremlin stayed on its poster, while Captain {hero.id} and "
        f"{partner.id} shared the snack only after washing their hands."
    )
    world.record("The fair opened with clean hands, a cleaned tool, and moving air.")
    return world


def generation_prompts(world: World) -> list[str]:
    mission: Mission = world.facts["mission"]  # type: ignore[assignment]
    hero: Entity = world.facts["hero"]  # type: ignore[assignment]
    partner: Entity = world.facts["partner"]  # type: ignore[assignment]
    return [
        f"Write a child-friendly superhero story about Captain {hero.id} and "
        f"{partner.id} solving a careful germ-and-air puzzle at {mission.setting}.",
        f"Include a cautionary rhyme that helps the children choose handwashing, "
        f"cleaning a shared tool, and asking an adult about fresh air.",
        "Explain that carbon dioxide is different from a germ, add a gentle joke, "
        "and end with a concrete image showing what changed.",
    ]


def story_qa(world: World) -> list[QAItem]:
    mission: Mission = world.facts["mission"]  # type: ignore[assignment]
    hero: Entity = world.facts["hero"]  # type: ignore[assignment]
    partner: Entity = world.facts["partner"]  # type: ignore[assignment]
    teacher: Entity = world.facts["teacher"]  # type: ignore[assignment]
    return [
        QAItem(
            question=f"What made {hero.id} and {partner.id} pause before the snack?",
            answer=(
                f"{mission.germ_path} That did not prove a harmful germ was "
                "there, but it was a sensible reason to clean a shared tool and "
                "wash hands before eating."
            ),
        ),
        QAItem(
            question=f"What did the streamer near the vent tell {partner.id}?",
            answer=(
                f"The streamer above the screened {mission.vent} barely moved, "
                "so it showed little air movement in that spot. It could not "
                "measure carbon dioxide or detect a germ."
            ),
        ),
        QAItem(
            question=f"How did {teacher.id} explain carbon dioxide?",
            answer=(
                f"{teacher.id} explained that people breathe out carbon dioxide "
                "and plants use it with sunlight to make food. Carbon dioxide "
                "is a gas, not a germ."
            ),
        ),
        QAItem(
            question=f"What did {hero.id}, {partner.id}, and the adult do to help?",
            answer=(
                f"{hero.id} and {partner.id} washed their hands with soap and "
                f"water, while {teacher.id} {mission.cleaning_action} and "
                f"opened the screened {mission.vent} for fresh air. The separate "
                "steps addressed separate concerns."
            ),
        ),
        QAItem(
            question="What showed that the team's plan had worked?",
            answer=(
                f"After the tool was cleaned and the screened vent was open, "
                f"{mission.ending_image}. The streamer fluttered in the moving air."
            ),
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="Can a paper streamer tell you how much carbon dioxide is in a room?",
            answer=(
                "No. A streamer can show that air is moving in one place, but it "
                "does not measure carbon dioxide. A suitable monitor is needed "
                "to measure the gas."
            ),
        ),
        QAItem(
            question="How can children help reduce the spread of germs from hands?",
            answer=(
                "Children can wash their hands with soap and water, especially "
                "before eating, and ask an adult to clean shared objects in a "
                "way that fits the object's care instructions."
            ),
        ),
        QAItem(
            question="What is one difference between a germ and carbon dioxide?",
            answer=(
                "A germ is a tiny organism; carbon dioxide is a gas that people "
                "breathe out and plants use with sunlight to make food. They are "
                "different things."
            ),
        ),
    ]


def generate(params: StoryParams) -> StorySample:
    world = simulate(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def format_qa(sample: StorySample) -> str:
    lines = [
        "== prompts ==",
        *(f"{i}. {prompt}" for i, prompt in enumerate(sample.prompts, 1)),
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
            f"  {entity.label} ({entity.kind}/{entity.type}) "
            f"meters={entity.meters} memes={entity.memes}"
        )
    lines.append("  events:")
    lines.extend(f"    - {event}" for event in world.events)
    return "\n".join(lines)


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


def asp_facts() -> str:
    import asp

    facts: list[str] = []
    for mission in MISSIONS.values():
        facts.extend(
            (
                asp.fact("mission", mission.key),
                asp.fact("source", mission.key, mission.source_code),
                asp.fact("clean", mission.key, mission.cleaning_code),
                asp.fact("vent", mission.key, mission.air_code),
            )
        )
    return "\n".join(facts)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combinations() -> list[tuple]:
    import asp

    symbols = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(symbols, "valid")))


def asp_verify() -> int:
    try:
        python_combos = set(valid_combinations())
        clingo_combos = set(asp_valid_combinations())
    except Exception as error:
        print(f"ASP verification could not run: {error}")
        return 2

    if python_combos != clingo_combos:
        print(
            "MISMATCH:",
            sorted(python_combos - clingo_combos),
            sorted(clingo_combos - python_combos),
        )
        return 1

    try:
        for index, mission_key in enumerate(sorted(MISSIONS)):
            params = StoryParams(
                mission=mission_key,
                hero="Luna",
                partner="Ari",
                power="steady_shield",
                route=ROUTES[index % len(ROUTES)],
                seed=300 + index,
            )
            sample = generate(params)
            if (
                len(sample.story) < 350
                or "carbon dioxide" not in sample.story
                or "germ" not in sample.story
                or "“" not in sample.story
                or "save the day" not in sample.story
                or len(sample.story_qa) < 4
            ):
                raise StoryError(f"The generated {mission_key} story failed a quality check.")
            if sample.world is None:
                raise StoryError("A generated story did not retain its world model.")
            item = sample.world.entities[MISSIONS[mission_key].shared_item]
            room = sample.world.entities[MISSIONS[mission_key].setting]
            if item.meters.get("needs_cleaning") != 0.0:
                raise StoryError(f"The {mission_key} tool was not cleaned in the simulation.")
            if room.meters.get("air_exchange", 0.0) < 0.5:
                raise StoryError(f"The {mission_key} vent did not change the simulated air state.")
    except (StoryError, KeyError) as error:
        print(f"Generated-story verification failed: {error}")
        return 1

    print(
        f"OK: ASP matches the Python gate ({len(python_combos)} plans); "
        f"generated stories passed state, dialogue, and QA checks."
    )
    return 0


CURATED = [
    StoryParams(
        mission="greenhouse",
        hero="Luna",
        partner="Ari",
        power="steady_shield",
        route="germ_first",
        seed=11,
    ),
    StoryParams(
        mission="maker_room",
        hero="Milo",
        partner="Zuri",
        power="super_hearing",
        route="air_first",
        seed=22,
    ),
    StoryParams(
        mission="garden_classroom",
        hero="Nia",
        partner="Theo",
        power="moonbeam_signal",
        route="question_first",
        seed=33,
    ),
]


def main() -> int:
    args = build_parser().parse_args()

    if args.show_asp:
        try:
            print(asp_program("#show valid/4."))
        except Exception as error:
            print(f"Could not build ASP program: {error}", file=sys.stderr)
            return 2
        return 0

    if args.verify:
        return asp_verify()

    if args.asp:
        try:
            combos = asp_valid_combinations()
        except Exception as error:
            print(f"ASP solving could not run: {error}", file=sys.stderr)
            return 2
        print(f"{len(combos)} compatible safety plans:\n")
        for mission, source, cleaning, air_plan in combos:
            print(f"  {mission:18} source={source:12} clean={cleaning:18} air={air_plan}")
        return 0

    if not args.all and args.n < 1:
        print("The number of stories must be at least one.", file=sys.stderr)
        return 2

    try:
        if args.all:
            samples = [generate(params) for params in CURATED]
        else:
            base_seed = args.seed if args.seed is not None else random.randrange(2**31)
            samples = []
            seen: set[str] = set()
            attempts = 0
            limit = max(args.n * 80, 80)
            while len(samples) < args.n and attempts < limit:
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
        print(error, file=sys.stderr)
        return 2

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
        return 0

    for index, sample in enumerate(samples):
        header = (
            "### curated story"
            if args.all
            else (f"### variant {index + 1}" if len(samples) > 1 else "")
        )
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
