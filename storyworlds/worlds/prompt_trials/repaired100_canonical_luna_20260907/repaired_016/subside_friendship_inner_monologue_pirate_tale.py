#!/usr/bin/env python3
"""
A small pirate story world about fear beginning to subside when friendship gives
a young sailor courage to repair a storm-tossed lantern.
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

HERE = Path(__file__).resolve()
STORYWORLDS_ROOT = next(parent for parent in HERE.parents if (parent / "results.py").is_file())
sys.path.insert(0, str(STORYWORLDS_ROOT))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Character:
    id: str
    name: str
    role: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class Location:
    name: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class StoryParams:
    captain_name: str
    friend_name: str
    island_name: str
    seed: Optional[int] = None


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Character] = {}
        self.location = Location("the Moonwake Sea")
        self.facts: dict[str, object] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.dialogue_turns: list[tuple[str, str]] = []

    def add(self, entity: Character) -> Character:
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


@dataclass(frozen=True)
class Voyage:
    island: str
    weather: str
    trouble: str
    danger: str
    clue: str
    captain_action: str
    friend_action: str
    repair: str
    result: str
    lesson: str
    ending: str


VOYAGES = [
    Voyage(
        island="Whispering Key",
        weather="a silver storm rolled over the sea",
        trouble="the mast lantern cracked and its flame began to fade",
        danger="without the lantern, the ship could miss the reef in the dark",
        clue="a loose copper wire was tapping against the lantern frame",
        captain_action="held the lantern steady with both hands",
        friend_action="climbed halfway up the mast and tied a safety rope",
        repair="bent the copper wire away from the wick and fitted a spare glass pane",
        result="the lantern shone steadily before the ship reached the reef",
        lesson="fear can subside when friends turn a large danger into small, careful jobs",
        ending="the repaired lantern made a golden path across the black water",
    ),
    Voyage(
        island="Blue Parrot Isle",
        weather="warm rain drummed on the deck",
        trouble="a wave washed the treasure map toward the rail",
        danger="the map could vanish beneath the hungry waves",
        clue="a red wax mark had caught on a splinter near the wheel",
        captain_action="crawled low across the wet deck",
        friend_action="looped a line around the map case",
        repair="pressed the map flat inside its dry oilskin cover",
        result="the route to the island remained clear and safe",
        lesson="a friend's calm voice can help worry subside enough to notice a useful clue",
        ending="the map opened under the lantern, with the red wax mark glowing like a tiny sunset",
    ),
    Voyage(
        island="Crescent Cove",
        weather="thick fog curled around the ship",
        trouble="the lookout bell broke loose from its hook",
        danger="the crew might not hear the warning if rocks appeared",
        clue="the bell rope was frayed only where it rubbed the hook",
        captain_action="stood beside the rail and listened for hidden rocks",
        friend_action="wrapped the rope in a strip of sailcloth",
        repair="secured the bell with a fresh knot and a spare hook",
        result="the warning bell rang clearly through the fog",
        lesson="friendship helps a frightened sailor pause, listen, and choose wisely",
        ending="the bell chimed through the mist while two friends shared the warmest cup of cocoa aboard",
    ),
    Voyage(
        island="Starfish Shoal",
        weather="a hard wind shoved the ship sideways",
        trouble="the small rowboat broke loose from its ropes",
        danger="it could strike the hull or drift away with the food supplies",
        clue="one rope end was smooth from rubbing against a sharp cleat",
        captain_action="kept the ship pointed into the waves",
        friend_action="crawled along the deck with a thick replacement rope",
        repair="covered the sharp cleat and tied the boat with two strong knots",
        result="the rowboat rested safely beside the ship again",
        lesson="when friends share the work, a storm feels smaller",
        ending="the rowboat bobbed beside the ship like a faithful little duck",
    ),
    Voyage(
        island="Candlefish Rock",
        weather="the sea heaved beneath a moonless sky",
        trouble="the compass needle spun in circles",
        danger="the ship could sail toward the jagged rocks",
        clue="a metal buckle had fallen beside the compass box",
        captain_action="kept one hand on the wheel and breathed slowly",
        friend_action="lifted the buckle away from the compass",
        repair="placed the compass on a wooden board and marked the safe heading",
        result="the needle pointed north once more",
        lesson="a steady friend can help a worried mind subside long enough to solve a mystery",
        ending="the compass settled on north while the moon slipped from behind a cloud",
    ),
]


NAMES = ["Mara", "Pip", "Nell", "Tavi", "Jun", "Cora"]
FRIENDS = ["Finn", "Bram", "Lio", "Sable", "Kit", "Rook"]
ISLANDS = [v.island for v in VOYAGES]

OPENINGS = [
    "At dusk, the little pirate ship Sea Finch sailed across the Moonwake Sea.",
    "The Sea Finch had almost reached land when the sky turned purple and wild.",
    "Captain Mara and her best friend stood watch as the last sunlight slipped away.",
    "A salty wind swept over the deck while the Sea Finch searched for a safe harbor.",
]


ASP_RULES = r"""
#show danger/1.
#show friendship/1.
#show safe/1.
danger(lantern) :- broken(lantern), night.
friendship(captain, friend) :- works_together(captain, friend).
safe(ship) :- danger(lantern), friendship(captain, friend), repaired(lantern).
"""


def asp_facts() -> str:
    import asp

    return "\n".join(
        [
            asp.fact("broken", "lantern"),
            asp.fact("night"),
            asp.fact("captain", "captain"),
            asp.fact("friend", "friend"),
            asp.fact("works_together", "captain", "friend"),
            asp.fact("repaired", "lantern"),
        ]
    )


def asp_program(show: str = "#show danger/1.\n#show friendship/1.\n#show safe/1.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Pirate friendship story world.")
    parser.add_argument("--captain-name", choices=NAMES)
    parser.add_argument("--friend-name", choices=FRIENDS)
    parser.add_argument("--island-name", choices=ISLANDS)
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
    captain = args.captain_name or rng.choice(NAMES)
    friend = args.friend_name or rng.choice([name for name in FRIENDS if name != captain])
    island = args.island_name or rng.choice(ISLANDS)
    return StoryParams(captain_name=captain, friend_name=friend, island_name=island)


def setup_world(params: StoryParams) -> World:
    world = World()
    captain = world.add(Character("captain", params.captain_name, "captain"))
    friend = world.add(Character("friend", params.friend_name, "friend"))
    world.facts.update(captain=captain, friend=friend)
    world.location.memes["friendship"] = 1.0
    world.location.meters["fear"] = 0.8
    return world


def choose_voyage(params: StoryParams) -> Voyage:
    key = params.seed if params.seed is not None else sum(ord(c) for c in params.captain_name + params.friend_name)
    if params.island_name:
        matches = [voyage for voyage in VOYAGES if voyage.island == params.island_name]
        if not matches:
            raise StoryError(f"Unknown island: {params.island_name}")
        return matches[key % len(matches)]
    return VOYAGES[key % len(VOYAGES)]


def speak(world: World, person: Character, words: str) -> None:
    world.dialogue_turns.append((person.name, words))
    world.say(f'{person.name} said, "{words}"')


def generate_story(world: World, params: StoryParams) -> None:
    captain: Character = world.facts["captain"]
    friend: Character = world.facts["friend"]
    voyage = choose_voyage(params)

    if captain.name == friend.name:
        raise StoryError("The captain and friend must have different names.")

    world.facts.update(
        voyage=voyage,
        opening=OPENINGS[(params.seed or 0) % len(OPENINGS)],
        resolved=False,
    )

    world.say(world.facts["opening"])
    world.say(
        f"Captain {captain.name} held the wheel, while {friend.name}, the ship's youngest sailor "
        f"and closest friend, watched the horizon near {voyage.island}."
    )
    world.say(f"Then {voyage.weather}. {voyage.trouble.capitalize()} {voyage.danger.capitalize()}.")

    world.para()
    world.say(
        f"{captain.name} felt a heavy knot in the stomach. 'What if I steer us wrong?' "
        "the captain thought. The fear did not vanish, but it began to subside when "
        f"{friend.name} stepped close."
    )
    speak(world, friend, "We are together. Tell me what you notice.")
    speak(world, captain, f"I notice that {voyage.clue}.")
    world.say(
        f"The thought became clearer: {voyage.lesson.capitalize()}. "
        f"{captain.name} pointed to the clue instead of pointing at the fear."
    )

    world.para()
    speak(world, captain, "You take the safe side, and I will hold the problem steady.")
    speak(world, friend, "Aye, captain. One small job at a time.")
    world.say(f"First, {captain.name} {voyage.captain_action}.")
    world.say(f"Next, {friend.name} {voyage.friend_action}.")
    world.say(f"Together they {voyage.repair}.")
    world.location.meters["fear"] = 0.2
    world.location.meters["lantern_light"] = 1.0
    world.say(f"{voyage.result.capitalize()}.")
    speak(world, friend, "See? The dark did not win.")
    speak(world, captain, "Nor did fear. Thank you, my friend.")
    world.say(
        f"By the time the danger had passed, {captain.name}'s fear had begun to subside completely. "
        f"{voyage.ending.capitalize()}."
    )
    world.facts["resolved"] = True


def story_qa(world: World) -> list[QAItem]:
    captain: Character = world.facts["captain"]
    friend: Character = world.facts["friend"]
    voyage: Voyage = world.facts["voyage"]
    return [
        QAItem(
            question=f"Who was Captain {captain.name} sailing with?",
            answer=f"Captain {captain.name} was sailing with {friend.name}, the captain's close friend.",
        ),
        QAItem(
            question=f"What danger faced the ship near {voyage.island}?",
            answer=f"{voyage.danger.capitalize()}",
        ),
        QAItem(
            question=f"What clue did {captain.name} notice?",
            answer=f"{captain.name} noticed that {voyage.clue}.",
        ),
        QAItem(
            question=f"How did friendship help {captain.name}?",
            answer=(
                f"{friend.name} stayed close, listened to the captain, and shared the work. "
                f"That helped the captain's fear subside while they repaired the problem together."
            ),
        ),
        QAItem(
            question="What showed that the story's problem was solved?",
            answer=f"{voyage.ending.capitalize()}",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does it mean for fear to subside?",
            answer="It means the fear becomes weaker or calmer, even if the problem has not vanished yet.",
        ),
        QAItem(
            question="Why are friends useful during a difficult task?",
            answer="Friends can listen, share the work, notice clues, and help one another make safer choices.",
        ),
        QAItem(
            question="What is a pirate ship's lantern used for?",
            answer="A ship's lantern gives light so sailors can see hazards and find their way in darkness.",
        ),
        QAItem(
            question="Why should sailors repair a danger before continuing?",
            answer="They should repair it so the ship and everyone aboard can travel more safely.",
        ),
    ]


def generation_prompts(world: World) -> list[str]:
    captain: Character = world.facts["captain"]
    friend: Character = world.facts["friend"]
    voyage: Voyage = world.facts["voyage"]
    return [
        (
            f"Write a child-friendly pirate tale about Captain {captain.name} and {friend.name} "
            f"working together near {voyage.island} after {voyage.trouble}."
        ),
        (
            f"Include an inner monologue in which {captain.name}'s fear begins to subside when "
            f"{friend.name} offers friendship and asks about this clue: {voyage.clue}."
        ),
        f"End the pirate story with this concrete image: {voyage.ending}.",
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        lines.append(
            f"  {entity.id}: name={entity.name} role={entity.role} "
            f"meters={entity.meters} memes={entity.memes}"
        )
    lines.append(f"  location: {world.location.name}")
    lines.append(f"  location meters={world.location.meters}")
    lines.append(f"  location memes={world.location.memes}")
    lines.append(f"  dialogue turns: {len(world.dialogue_turns)}")
    lines.append(f"  resolved: {world.facts.get('resolved')}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    sections = ["== generation prompts =="]
    sections.extend(f"- {prompt}" for prompt in sample.prompts)
    sections.append("")
    sections.append("== story questions ==")
    for item in sample.story_qa:
        sections.append(f"Q: {item.question}")
        sections.append(f"A: {item.answer}")
    sections.append("")
    sections.append("== world questions ==")
    for item in sample.world_qa:
        sections.append(f"Q: {item.question}")
        sections.append(f"A: {item.answer}")
    return "\n".join(sections)


def generate(params: StoryParams) -> StorySample:
    world = setup_world(params)
    generate_story(world, params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


CURATED = [
    StoryParams("Mara", "Finn", "Whispering Key"),
    StoryParams("Pip", "Sable", "Crescent Cove"),
    StoryParams("Nell", "Rook", "Candlefish Rock"),
]


def asp_verify() -> int:
    import asp

    model = asp.one_model(asp_program())
    dangers = asp.atoms(model, "danger")
    friendships = asp.atoms(model, "friendship")
    safe = asp.atoms(model, "safe")
    if ("lantern",) not in dangers:
        print("MISMATCH: ASP did not detect the lantern danger.")
        return 1
    if ("captain", "friend") not in friendships:
        print("MISMATCH: ASP did not detect friendship.")
        return 1
    if ("ship",) not in safe:
        print("MISMATCH: ASP did not detect the repaired safe ship.")
        return 1

    for params in CURATED:
        sample = generate(params)
        if "subside" not in sample.story.lower():
            print("MISMATCH: generated story does not include subside.")
            return 1
        if len(sample.world.dialogue_turns) < 4:
            print("MISMATCH: generated story lacks dialogue.")
            return 1
        if not sample.world.facts["resolved"]:
            print("MISMATCH: generated story did not resolve.")
            return 1

    print("OK: ASP and Python story checks agree.")
    return 0


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return

    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    if args.asp:
        import asp

        model = asp.one_model(asp_program())
        print("danger:", asp.atoms(model, "danger"))
        print("friendship:", asp.atoms(model, "friendship"))
        print("safe:", asp.atoms(model, "safe"))
        return

    if args.n < 1:
        raise StoryError("-n must be at least 1.")

    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        samples = []
        seen: set[str] = set()
        for index in range(args.n):
            rng = random.Random(base_seed + index)
            params = resolve_params(args, rng)
            params.seed = base_seed + index
            sample = generate(params)
            if sample.story in seen:
                params.seed += 1000003
                sample = generate(params)
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
            header=f"### variant {index + 1}" if len(samples) > 1 else "",
        )
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
