#!/usr/bin/env python3
"""A child-facing mystery about a curious mechanism, friendship, and a careful twist."""

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
    mood: str
    weather: str


@dataclass
class StoryParams:
    place: str
    mechanism: str
    name: str
    friend: str
    suspect: str
    mystery: str = ""
    route: str = ""
    seed: Optional[int] = None


@dataclass(frozen=True)
class MysteryCase:
    missing: str
    suspicion: str
    test: str
    failed: str
    clue: str
    truth: str
    repair: str
    lesson: str
    ending: str


class World:
    def __init__(self, scene: Scene) -> None:
        self.scene = scene
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
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


PLACES = {
    "clocktower": Scene("the old clocktower", "echoing", "a cool morning wind"),
    "workshop": Scene("the neighborhood workshop", "sawdusty", "bright afternoon sun"),
    "greenhouse": Scene("the glass greenhouse", "dewy", "soft rain on the roof"),
    "riverbank": Scene("the riverbank shed", "quiet", "a warm breeze"),
}

MECHANISMS = {
    "wind_latch": "a small wind-powered latch",
    "marble_lift": "a wooden marble lift",
    "bell_winder": "a brass bell-winding machine",
    "sun_tracker": "a box of turning mirrors",
    "seed_sorter": "a hand-cranked seed sorter",
}

FRIENDS = {"Luna": "girl", "Milo": "boy", "Pia": "girl", "Sam": "boy"}
SUSPECTS = {"magpie": "bird", "fox": "fox", "goat": "goat", "raccoon": "raccoon"}

CASES = {
    "missing_key": MysteryCase(
        "the silver key that opened the clock cabinet",
        "the magpie had been seen near the open window",
        "measured the keyhole and compared it with the magpie's shiny feathers",
        "the keyhole was too narrow for feathers to touch the latch",
        "a bright scratch curved from the latch to a loose floorboard",
        "the wind had turned the mechanism, and the key had slipped under the board",
        "lifted the board with an adult, retrieved the key, and added a safety stop",
        "a nearby friend or animal is not proof of blame",
        "the clock ticked again while the key rested safely in its little blue dish",
    ),
    "spinning_sign": MysteryCase(
        "the workshop sign that pointed visitors toward the door",
        "the fox had walked past just before the sign spun away",
        "tied a ribbon to the sign and watched its movement in still air",
        "the ribbon turned even when the fox was far away",
        "a bent spring inside the sign caught on a splinter",
        "the mechanism was springing back too hard and twisting the sign by itself",
        "straightened the spring with help and covered the sharp splinter",
        "a warning should be tested before it becomes an accusation",
        "the sign pointed steadily to the workshop as friends entered together",
    ),
    "vanishing_seeds": MysteryCase(
        "a tray of moonflower seeds",
        "the goat had nibbled near the empty tray",
        "counted the hoofprints and checked whether the tray could slide",
        "the prints stopped before the tray's hidden path began",
        "a brass gear tooth was caught in a strip of blue cloth",
        "the seed sorter had pulled the tray beneath its turning wheel",
        "stopped the machine, gathered every seed, and placed a guard over the gear",
        "curiosity needs a safe pause before anyone reaches into a machine",
        "moonflower seeds filled neat rows while the covered sorter rested",
    ),
    "dark_greenhouse": MysteryCase(
        "the greenhouse's warm lamp",
        "the raccoon had left muddy marks beside the lamp stand",
        "turned the mirror box one notch at a time to follow the light",
        "the light moved even when nobody touched the box",
        "a loose cord trembled against the mirror's wooden arm",
        "a fan had been pulling the cord into the mechanism and changing the mirror's angle",
        "switched off the fan, tied the cord away, and marked the safe path",
        "a strange result can have a plain cause hidden nearby",
        "the repaired mirrors warmed one bright patch where seedlings lifted their leaves",
    ),
    "silent_bell": MysteryCase(
        "the bell that called friends to the river cleanup",
        "the raccoon had bumped the shed door before the bell went silent",
        "pulled the winding handle gently and listened for the first click",
        "the handle moved without touching the bell's inner wheel",
        "a tiny wooden pin lay beneath the winding gear",
        "the pin had fallen out, so the handle could not transfer motion to the bell",
        "replaced the pin, tested the bell from a safe distance, and tied a warning card nearby",
        "understanding how a mechanism works is safer than forcing it",
        "one clear bell note floated over the river while friends held the repaired handle",
    ),
}

ROUTES = (
    "clue_first",
    "dialogue_first",
    "test_first",
    "friend_first",
    "map_first",
    "quiet_first",
    "two_theories",
)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A friendship mystery about a curious mechanism.")
    ap.add_argument("--place", choices=sorted(PLACES))
    ap.add_argument("--mechanism", choices=sorted(MECHANISMS))
    ap.add_argument("--name")
    ap.add_argument("--friend", choices=sorted(FRIENDS))
    ap.add_argument("--suspect", choices=sorted(SUSPECTS))
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--seed", type=int)
    for flag in ("all", "trace", "qa", "json", "asp", "verify", "show-asp"):
        ap.add_argument(f"--{flag}", action="store_true")
    return ap


def valid_combos() -> list[tuple[str, str]]:
    return [(place, mechanism) for place in sorted(PLACES) for mechanism in sorted(MECHANISMS)]


ASP_RULES = """
valid(Place, Mechanism) :- place(Place), mechanism(Mechanism).
safe(Place, Mechanism) :- valid(Place, Mechanism).
"""


def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            *(asp.fact("place", place) for place in PLACES),
            *(asp.fact("mechanism", mechanism) for mechanism in MECHANISMS),
        ]
    )


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combinations).")
        return 0
    print("MISMATCH:", sorted(py - cl), sorted(cl - py))
    return 1


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [
        combo
        for combo in valid_combos()
        if not args.place or combo[0] == args.place
        if not args.mechanism or combo[1] == args.mechanism
    ]
    if not combos:
        raise StoryError("No safe mechanism mystery fits those options.")
    place, mechanism = rng.choice(combos)
    name = args.name or "Luna"
    friend_choices = [friend for friend in sorted(FRIENDS) if friend != name] or sorted(FRIENDS)
    return StoryParams(
        place=place,
        mechanism=mechanism,
        name=name,
        friend=args.friend or rng.choice(friend_choices),
        suspect=args.suspect or rng.choice(sorted(SUSPECTS)),
        mystery=rng.choice(sorted(CASES)),
        route=rng.choice(ROUTES),
    )


def story_rng(params: StoryParams) -> random.Random:
    text = "|".join(
        str(value)
        for value in (
            params.seed,
            params.place,
            params.mechanism,
            params.name,
            params.friend,
            params.suspect,
            params.mystery,
            params.route,
        )
    )
    return random.Random(int.from_bytes(hashlib.sha256(text.encode()).digest()[:8], "big"))


def tell(params: StoryParams) -> World:
    scene = PLACES[params.place]
    mechanism = MECHANISMS[params.mechanism]
    case = CASES[params.mystery]
    rng = story_rng(params)
    world = World(scene)

    hero = world.add(
        Entity(
            id=params.name,
            kind="character",
            type=FRIENDS.get(params.name, "child"),
            memes={"curiosity": 1.0, "care": 1.0},
        )
    )
    friend = world.add(
        Entity(
            id=params.friend,
            kind="character",
            type=FRIENDS[params.friend],
            memes={"friendship": 1.0},
        )
    )
    suspect = world.add(
        Entity(
            id=params.suspect,
            kind="character",
            type=SUSPECTS[params.suspect],
            label=params.suspect,
        )
    )
    machine = world.add(
        Entity(
            id="mechanism",
            kind="machine",
            type=params.mechanism,
            label=mechanism,
            meters={"motion": 0.0, "risk": 0.0},
            memes={"mystery": 1.0},
        )
    )

    openings = {
        "clue_first": (
            f"{params.name} first noticed a strange scrape beside {scene.place}. "
            f"Then the children discovered that {case.missing} had vanished from the place where {mechanism} stood."
        ),
        "dialogue_first": (
            f'"Wait," {params.name} said at {scene.place}. "We should look before we blame anyone." '
            f"{case.missing.capitalize()} had vanished, and {mechanism} sat silent nearby."
        ),
        "test_first": (
            f"At {scene.place}, {params.name} and {params.friend} were learning how {mechanism} worked "
            f"when they found that {case.missing} had disappeared."
        ),
        "friend_first": (
            f"{params.friend} called for {params.name} at {scene.place}. "
            f"{case.missing.capitalize()} was gone, and {mechanism} had stopped in an odd position."
        ),
        "map_first": (
            f"{params.name} drew a map of {scene.place}, marking the door, the machine, and a loose board. "
            f"In the middle, the child wrote that {case.missing} was missing."
        ),
        "quiet_first": (
            f"The quiet at {scene.place} felt unusual. "
            f"{mechanism.capitalize()} was still, {case.missing} was gone, and a faint scratch crossed the floor."
        ),
        "two_theories": (
            f"Two ideas competed at {scene.place}: an animal had taken {case.missing}, "
            f"or {mechanism} had moved it. {params.name} asked everyone to wait for evidence."
        ),
    }
    world.say(openings[params.route])
    world.say(
        rng.choice(
            [
                f"{params.name} and {params.friend} promised to stay together and keep their hands away from moving parts.",
                f"{params.friend} opened a notebook while {params.name} watched the machine from a safe distance.",
                f"The friends agreed that a mystery was easier when they shared questions instead of hiding worries.",
                f"{params.name} checked that {params.friend} was comfortable before they began looking around.",
            ]
        )
    )
    world.para()

    world.say(
        rng.choice(
            [
                f"Suspicion fell on the {suspect.label} because {case.suspicion}.",
                f'"The {suspect.label} must have done it," someone said, pointing out that {case.suspicion}.',
                f"A worried voice blamed the {suspect.label} as soon as people noticed that {case.suspicion}.',
                f"Because {case.suspicion}, the group nearly sent the {suspect.label} away without checking the machine.",
            ]
        )
    )
    suspect.memes["blamed"] = 1.0
    hero.memes["fairness"] = 1.0
    world.say(
        rng.choice(
            [
                f'"Being nearby is not the same as being guilty," {params.name} said. "Let us test the mechanism safely."',
                f'{params.friend} stood beside the {suspect.label}. "Friends do not let guesses hurt someone," {params.friend} said.',
                f'"We can be cautious and kind at the same time," {params.name} told the group.',
                f'{params.name} took a breath. "No one reaches inside until we understand what moves."',
            ]
        )
    )
    world.para()

    machine.meters["risk"] = 1.0
    world.say(f"First, {params.name} {case.test}. But {case.failed}.")
    world.say(
        rng.choice(
            [
                f"{params.friend} helped {params.name} record the failed test instead of pretending it had worked.",
                f'"That result is useful," {params.friend} said. "It tells us which idea to release."',
                f"The friends stepped back from the machine, because curiosity without care could make the mystery worse.",
                f"{params.name} closed the notebook. The first answer had failed, so the children changed their question.",
            ]
        )
    )
    world.say(f"Then they found the important clue: {case.clue}.")
    world.say(
        rng.choice(
            [
                f"{params.name} traced the clue without touching anything and asked {params.friend} what motion could have made it.",
                f"{params.friend} noticed that the clue matched the machine's turning path, not the {suspect.label}'s tracks.",
                "Together, the children drew arrows showing how one small movement could cause the next.",
                f"The clue made the twist clear: the machine, not the nearby {suspect.label}, had started the chain of events.",
            ]
        )
    )
    world.para()

    machine.meters["motion"] = 1.0
    machine.meters["risk"] = 0.0
    hero.meters["tests_completed"] = 2.0
    friend.memes["trust"] = 1.0
    world.say(f"The truth was that {case.truth}. The {suspect.label} had not caused the trouble.")
    suspect.memes["blamed"] = 0.0
    world.say(
        rng.choice(
            [
                f"The group apologized to the {suspect.label}, and then {params.name} and {params.friend} {case.repair}.",
                f'"We were too quick," {params.name} admitted. After the apology, the friends {case.repair}.',
                f"Friendship turned the argument into careful work. Everyone stepped back while {params.name} and {params.friend} {case.repair}.",
                f"Once the blame was gone, the children worked together: they {case.repair}.",
            ]
        )
    )
    world.say(f"{params.name} wrote the caution in the notebook: {case.lesson}.")
    world.say(
        rng.choice(
            [
                f"At the end of the day, {case.ending}.",
                f"When the last question was answered, {case.ending}.",
                f"Peace returned in a picture everyone could see: {case.ending}.",
                f"Before leaving, the friends looked back. {case.ending.capitalize()}.",
            ]
        )
    )
    world.facts.update(
        hero=hero,
        friend=friend,
        suspect=suspect,
        machine=machine,
        scene=scene,
        mechanism=mechanism,
        case=case,
        truth=case.truth,
        repair=case.repair,
        lesson=case.lesson,
        ending=case.ending,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    facts = world.facts
    case = facts["case"]
    return [
        f"Write a short mystery for a young child about {facts['hero'].id}, a mechanism, and {case.missing}.",
        f"Tell a friendship story in which {facts['hero'].id} and {facts['friend'].id} protect the {facts['suspect'].label} from an unfair accusation.",
        f"Write a cautionary mystery revealing that {facts['truth']}, and end with {facts['ending']}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    facts = world.facts
    case = facts["case"]
    return [
        QAItem(
            question=f"What disappeared from {facts['scene'].place}?",
            answer=f"{case.missing.capitalize()} disappeared from {facts['scene'].place} while {facts['mechanism']} was nearby.",
        ),
        QAItem(
            question=f"Why was the {facts['suspect'].label} blamed at first?",
            answer=f"The {facts['suspect'].label} was blamed because {case.suspicion}. That circumstance did not prove who caused the trouble.",
        ),
        QAItem(
            question=f"What did {facts['hero'].id} and {facts['friend'].id} learn from their first test?",
            answer=f"They {case.test}, but {case.failed}. The failed test helped them abandon their first explanation.",
        ),
        QAItem(
            question=f"What clue revealed the mechanism's part in the mystery?",
            answer=f"They found that {case.clue}. This showed that {case.truth}.",
        ),
        QAItem(
            question=f"How did the friends repair the problem and make the ending safer?",
            answer=f"They apologized to the {facts['suspect'].label}, then {case.repair}. They remembered that {case.lesson}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a mechanism?",
            answer="A mechanism is a set of parts that work together to make or control movement, such as gears, springs, levers, or wheels.",
        ),
        QAItem(
            question="Why should children be cautious around a mechanism?",
            answer="Moving parts can pinch, cut, or start unexpectedly, so children should stop the machine, keep hands away, and ask a trusted adult for help.",
        ),
        QAItem(
            question="How can friendship help during a mystery?",
            answer="Friends can share observations, listen calmly, protect one another from unfair blame, and make safer decisions together.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts ==", *(f"{i}. {prompt}" for i, prompt in enumerate(sample.prompts, 1)), "", "== story qa =="]
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
    lines.append(f"  truth={world.facts['truth']}")
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
    if trace and sample.world:
        print(dump_trace(sample.world))
    if qa:
        print("\n" + format_qa(sample))


CURATED = [
    StoryParams(
        place="clocktower",
        mechanism="wind_latch",
        name="Luna",
        friend="Milo",
        suspect="magpie",
        mystery="missing_key",
        route="clue_first",
        seed=11,
    ),
    StoryParams(
        place="workshop",
        mechanism="spinning_sign",
        name="Luna",
        friend="Pia",
        suspect="fox",
        mystery="spinning_sign",
        route="dialogue_first",
        seed=22,
    ),
    StoryParams(
        place="greenhouse",
        mechanism="sun_tracker",
        name="Luna",
        friend="Sam",
        suspect="raccoon",
        mystery="dark_greenhouse",
        route="test_first",
        seed=33,
    ),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/2."))
        return

    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        combinations = asp_valid_combos()
        print(f"{len(combinations)} compatible combinations:\n")
        for place, mechanism in combinations:
            print(f"  {place:12} {mechanism}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        samples: list[StorySample] = []
        seen: set[str] = set()
        attempts = 0
        while len(samples) < args.n and attempts < max(args.n * 50, 50):
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

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
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
