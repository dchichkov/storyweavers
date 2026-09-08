#!/usr/bin/env python3
"""A child-facing mystery world about a disturbance, fair conflict, and repair."""

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
    mood: str
    weather: str


@dataclass
class StoryParams:
    place: str
    disturbance: str
    name: str
    friend: str
    suspect: str
    case: str = ""
    route: str = ""
    seed: Optional[int] = None


@dataclass(frozen=True)
class MysteryCase:
    missing: str
    accusation: str
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
    "garden": Scene("the garden", "leafy", "a mild breeze"),
    "pond": Scene("the pond", "glassy", "a silver drizzle"),
    "shed": Scene("the shed", "hushed", "warm afternoon light"),
}

DISTURBANCES = {
    "rattle": "a sudden rattling sound",
    "swirl": "a swirl of loose papers",
    "shadow": "a quick shadow across the wall",
    "splash": "an unexpected splash",
}

FRIENDS = {"Mina": "girl", "Theo": "boy", "Iris": "girl", "Ned": "boy"}
SUSPECTS = {"duck": "duck", "cat": "cat", "raccoon": "raccoon", "frog": "frog"}

CASES = {
    "seed_packets": MysteryCase(
        "three packets of moonflower seeds",
        "a torn packet lay beside the animal's tracks",
        "matched the tracks against a sketch in the club notebook",
        "the sizes did not match, so the easy answer fell apart",
        "a loose green cord looped around the watering-can handle",
        "a gust had lifted the packets into a shade net",
        "lowered the net together and sorted every seed into a labeled jar",
        "a nearby track is not proof of blame",
        "moonflower seeds rested in neat jars while the empty net fluttered overhead",
    ),
    "bell_rope": MysteryCase(
        "the little brass bell from the gate",
        "someone heard a clink just after the animal passed",
        "followed the sound with pauses so echoes would not fool them",
        "the loudest clink came from an empty bucket, not the bell",
        "a frayed knot showed where the bell rope had snagged",
        "the bell had rolled through a drain channel and lodged beneath a grate",
        "lifted it safely with a hooked stick and braided a stronger rope",
        "sounds can point the wrong way unless clues agree",
        "the rehung bell gave one clear note above a grate swept clean",
    ),
    "painted_sign": MysteryCase(
        "the newly painted welcome sign",
        "a tail-shaped smear seemed to point toward the animal",
        "measured the smear with string and compared its height",
        "it was too straight and high to be a tail mark",
        "a green cord mark curved across the still-tacky blue paint",
        "the sign had swung against a windbreak screen during the disturbance",
        "peeled it free with an adult's help and built a stable drying rack",
        "a familiar shape is not proof of what made it",
        "the blue sign shone on its rack with one small cord mark as a reminder",
    ),
    "paper_boats": MysteryCase(
        "the children's fleet of folded paper boats",
        "wet prints circled the launch shelf after the animal visited",
        "placed one test boat on the shelf and watched the moving air",
        "the boat stayed still, so the breeze alone was not enough",
        "a ripple led beneath a gap in the rain barrel",
        "drips had filled a groove and floated the boats under the footbridge",
        "corked the leak and rescued the boats with a long net",
        "a fair test changes one thing at a time",
        "the rescued boats dried in a bright row above the newly corked barrel",
    ),
    "music_pages": MysteryCase(
        "the pages of a song written for pond night",
        "a croak or purr interrupted rehearsal when the pages vanished",
        "replayed the tune and watched where each loose scrap moved",
        "the scraps moved toward the wall, not toward the sound",
        "a shadow appeared behind a vent whenever the fan turned",
        "the fan had drawn the pages against the vent in their original order",
        "switched off the fan, recovered the song, and clipped its pages",
        "two events together do not prove one caused the other",
        "the complete song rested under a star-shaped clip as rehearsal began",
    ),
    "story_tokens": MysteryCase(
        "the carved tokens used to choose the evening story",
        "the animal was beside the empty token bowl",
        "asked everyone when they had last seen the bowl full",
        "their memories disagreed, and arguing made nothing clearer",
        "a curved scratch circled the base of the rotating book display",
        "the display's mesh base scooped up the tokens when it turned",
        "rotated it back, collected the tokens, and fitted a smooth base cover",
        "listening to every witness works better than shouting a guess",
        "one moon token gleamed in the bowl as everyone settled for the story",
    ),
}

ROUTES = (
    "clue_first",
    "dialogue_first",
    "test_first",
    "memory_first",
    "map_first",
    "quiet_first",
    "race_clock",
    "two_theories",
)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A mystery world about a disturbance and a fair conflict."
    )
    ap.add_argument("--place", choices=sorted(PLACES))
    ap.add_argument("--disturbance", choices=sorted(DISTURBANCES))
    ap.add_argument("--name")
    ap.add_argument("--friend", choices=sorted(FRIENDS))
    ap.add_argument("--suspect", choices=sorted(SUSPECTS))
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--seed", type=int)
    for flag in ("all", "trace", "qa", "json", "asp", "verify", "show-asp"):
        ap.add_argument(f"--{flag}", action="store_true")
    return ap


def valid_combos() -> list[tuple[str, str]]:
    return [(place, disturbance) for place in sorted(PLACES) for disturbance in sorted(DISTURBANCES)]


ASP_RULES = """
valid(Place, Disturbance) :- place(Place), disturbance(Disturbance).
"""


def asp_facts() -> str:
    import asp

    return "\n".join(
        [
            *(asp.fact("place", place) for place in PLACES),
            *(asp.fact("disturbance", disturbance) for disturbance in DISTURBANCES),
        ]
    )


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    symbols = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(symbols, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH:", sorted(py - cl), sorted(cl - py))
    return 1


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [
        combo
        for combo in valid_combos()
        if not args.place or combo[0] == args.place
        if not args.disturbance or combo[1] == args.disturbance
    ]
    if not combos:
        raise StoryError("No valid mystery fits those options.")
    place, disturbance = rng.choice(combos)
    name = args.name or "Luna"
    friends = [friend for friend in sorted(FRIENDS) if friend != name] or sorted(FRIENDS)
    return StoryParams(
        place=place,
        disturbance=disturbance,
        name=name,
        friend=args.friend or rng.choice(friends),
        suspect=args.suspect or rng.choice(sorted(SUSPECTS)),
        case=rng.choice(sorted(CASES)),
        route=rng.choice(ROUTES),
    )


def story_rng(params: StoryParams) -> random.Random:
    text = "|".join(
        str(value)
        for value in (
            params.seed,
            params.place,
            params.disturbance,
            params.name,
            params.friend,
            params.suspect,
            params.case,
            params.route,
        )
    )
    return random.Random(int.from_bytes(hashlib.sha256(text.encode()).digest()[:8], "big"))


def tell(params: StoryParams) -> World:
    scene = PLACES[params.place]
    case = CASES[params.case]
    disturbance = DISTURBANCES[params.disturbance]
    rng = story_rng(params)
    world = World(scene)

    hero = world.add(
        Entity(
            id=params.name,
            kind="character",
            type="girl" if params.name in {"Luna", "Mina", "Iris"} else "boy",
        )
    )
    friend = world.add(
        Entity(id=params.friend, kind="character", type=FRIENDS[params.friend])
    )
    suspect = world.add(
        Entity(
            id=params.suspect,
            kind="character",
            type=SUSPECTS[params.suspect],
            label=params.suspect,
        )
    )

    openings = {
        "clue_first": (
            f"The first thing {hero.id} noticed was {disturbance} near {scene.place}. "
            f"Only then did the young detective learn that {case.missing} had vanished."
        ),
        "dialogue_first": (
            f'"Please do not decide yet," {hero.id} said as voices rose at {scene.place}. '
            f"{case.missing.capitalize()} had vanished, and {disturbance} was the only quiet witness."
        ),
        "test_first": (
            f"At {hero.id}'s Mystery Club, every disturbance began with a test. "
            f"This one began when {case.missing} disappeared from {scene.place} under {scene.weather}."
        ),
        "memory_first": (
            f"Later, {friend.id} would remember the {scene.mood} hush of {scene.place}. "
            f"Everyone was searching for {case.missing}, and {hero.id} had heard {disturbance}."
        ),
        "map_first": (
            f"{hero.id} drew a map of {scene.place}: the doorway, the shelves, and the spot where "
            f"{disturbance} began. In the center the young detective wrote what was missing: {case.missing}."
        ),
        "quiet_first": (
            f"Nothing seemed wrong at {scene.place} until {friend.id} noticed an empty space. "
            f"{case.missing.capitalize()} was gone, and nearby was {disturbance}."
        ),
        "race_clock": (
            f"There was little time before visitors arrived at {scene.place}. "
            f"{case.missing.capitalize()} had disappeared, while {disturbance} waited where it should not be."
        ),
        "two_theories": (
            f"Two explanations competed at {scene.place}: an animal had taken {case.missing}, "
            f"or the disturbance had moved it. {hero.id} found {disturbance} between the theories."
        ),
    }

    world.say(openings[params.route])
    world.say(
        rng.choice(
            [
                f"{friend.id} stayed beside {hero.id}, writing facts instead of rumors.",
                f"{hero.id} opened the club notebook while {friend.id} kept everyone clear of the disturbed area.",
                f"Together, {hero.id} and {friend.id} agreed that every claim needed more than a guess.",
                f"The disturbance made {friend.id} uneasy, but {hero.id} promised they would check each detail.",
            ]
        )
    )
    world.para()

    world.say(
        rng.choice(
            [
                f"Suspicion settled on the {suspect.label} because {case.accusation}.",
                f'"The {suspect.label} did it," someone declared, pointing out that {case.accusation}.',
                f"A sharp disagreement began when people noticed that {case.accusation} and blamed the {suspect.label}.",
                f"Because {case.accusation}, a worried neighbor tried to send the {suspect.label} away.",
            ]
        )
    )
    world.say(
        "The unfair accusation turned the disturbance into a conflict between worried neighbors."
    )
    suspect.memes["blamed"] = 1
    hero.memes["fairness"] = 1

    world.say(
        rng.choice(
            [
                f'"Being close is not the same as being guilty," {hero.id} replied. '
                f'"Let us find a clue that explains how."',
                f'{hero.id} raised one hand. "That may be a lead, but it is not a fair answer yet."',
                f'"We can disagree without frightening anyone," {friend.id} said, protecting the {suspect.label}.',
                f'{hero.id} felt the conflict tighten. "{hero.id} said, "We need evidence that fits every part."',
            ]
        )
    )
    world.para()

    world.say(f"First, {hero.id} {case.test}. But {case.failed}.")
    world.say(
        rng.choice(
            [
                f"Instead of hiding the failed test, {hero.id} crossed out the theory and invited {friend.id} to look again.",
                f"The mistake showed which idea to release. {friend.id} turned the notebook to a clean page.",
                f'"Wrong ideas can teach good detectives," {friend.id} whispered, and the search changed direction.',
                "That result quieted the argument. Even the loudest accuser leaned closer to see the evidence.",
            ]
        )
    )
    world.say(f"Then they found the decisive clue: {case.clue}.")
    world.say(
        rng.choice(
            [
                f"{hero.id} traced its direction without touching it and saw the hidden chain of events.",
                "Working backward from that clue, the children reconstructed each small movement.",
                "They compared the clue with the map, the weather, and the empty space; all three agreed.",
                "The clue did more than point at a place. It explained why the disturbance had misled them.",
            ]
        )
    )
    world.para()

    world.say(
        f"The truth was that {case.truth}. The {suspect.label} had not caused the loss at all."
    )
    suspect.memes["blamed"] = 0
    hero.meters["tests_completed"] = 2
    world.say(
        rng.choice(
            [
                f"The accusers apologized to the {suspect.label}, then {hero.id} and {friend.id} {case.repair}.",
                f'"We were too quick," the neighbors admitted. After making peace with the {suspect.label}, everyone {case.repair}.',
                f"The conflict ended with an apology, not a victory. Side by side, the group {case.repair}.",
                f"Once the {suspect.label} was welcomed back, blame became useful work: they {case.repair}.",
            ]
        )
    )
    world.say(f"{hero.id} wrote the lesson in the mystery book: {case.lesson}.")
    world.say(
        rng.choice(
            [
                f"At sunset, {case.ending}.",
                f"When the last question was answered, {case.ending}.",
                f"Peace returned in a picture everyone could see: {case.ending}.",
                f"Before leaving, they looked back. {case.ending.capitalize()}.",
            ]
        )
    )

    world.facts.update(
        hero=hero,
        friend=friend,
        suspect=suspect,
        scene=scene,
        disturbance=disturbance,
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
        f"Write a short mystery for a young child about {facts['hero'].id}, {facts['disturbance']}, and the disappearance of {case.missing}.",
        f"Tell a gentle conflict mystery in which {facts['hero'].id} tests evidence before deciding whether the {facts['suspect'].label} is responsible.",
        f"Write a detective story set at {facts['scene'].place}; reveal that {facts['truth']}, and end with {facts['ending']}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    facts = world.facts
    case = facts["case"]
    return [
        QAItem(
            question=f"What disturbance did {facts['hero'].id} notice before something went missing at {facts['scene'].place}?",
            answer=f"{facts['hero'].id} noticed {facts['disturbance']} before {case.missing} went missing at {facts['scene'].place}.",
        ),
        QAItem(
            question=f"Why did the neighbors accuse the {facts['suspect'].label}?",
            answer=f"They accused the {facts['suspect'].label} because {case.accusation}. That detail suggested a possibility but did not prove who caused the loss.",
        ),
        QAItem(
            question=f"How did {facts['hero'].id}'s first test change the investigation?",
            answer=f"{facts['hero'].id} {case.test}, but {case.failed}. The friends released their first theory and searched for better evidence.",
        ),
        QAItem(
            question=f"Which clue revealed what really caused the disturbance?",
            answer=f"The decisive clue was that {case.clue}. It helped the children discover that {case.truth}.",
        ),
        QAItem(
            question=f"How did the group repair the problem and end the conflict?",
            answer=f"After apologizing to the {facts['suspect'].label}, the group worked together: they {case.repair}. They remembered that {case.lesson}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What should a child do when a disturbance makes people blame someone?",
            answer="A child should pause, keep everyone safe, ask calm questions, and test more than one explanation before deciding who is responsible.",
        ),
        QAItem(
            question="Why can a nearby clue be misleading?",
            answer="A nearby clue may show where something ended up rather than who moved it. Other evidence is needed to explain the whole chain of events.",
        ),
        QAItem(
            question="How can people repair a conflict after an unfair accusation?",
            answer="They can listen, explain what the evidence shows, apologize clearly, and work together to fix the original problem.",
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
    lines.append(f"  disturbance={world.facts['disturbance']}")
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
        place="garden",
        disturbance="rattle",
        name="Luna",
        friend="Mina",
        suspect="duck",
        case="seed_packets",
        route="clue_first",
        seed=11,
    ),
    StoryParams(
        place="pond",
        disturbance="splash",
        name="Luna",
        friend="Theo",
        suspect="frog",
        case="paper_boats",
        route="test_first",
        seed=22,
    ),
    StoryParams(
        place="shed",
        disturbance="swirl",
        name="Luna",
        friend="Iris",
        suspect="cat",
        case="bell_rope",
        route="dialogue_first",
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
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:\n")
        for place, disturbance in combos:
            print(f"  {place:8} {disturbance}")
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
