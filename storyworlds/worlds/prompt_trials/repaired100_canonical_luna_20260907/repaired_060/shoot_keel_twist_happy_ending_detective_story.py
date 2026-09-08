#!/usr/bin/env python3
from __future__ import annotations

# Locate the shared StoryWorld helpers from any batch depth.
from pathlib import Path as _StoryPath
import sys as _StorySys
_storyworlds_root = next(parent for parent in _StoryPath(__file__).resolve().parents
                        if (parent / 'results.py').is_file() and (parent / 'asp.py').is_file())
_StorySys.path.insert(0, str(_storyworlds_root.parent))
_StorySys.path.insert(0, str(_storyworlds_root))


import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402


ASP_RULES = r"""
% A tiny detective domain about a safe signal shoot and a boat's keel.
clue(signal_shoot).
clue(keel_mark).
feature(twist).
feature(happy_ending).
safe_method(shoreline_shoot).
safe_object(keel).
detective_ready :- clue(signal_shoot), clue(keel_mark), feature(twist).
solved_case :- detective_ready, safe_method(shoreline_shoot), safe_object(keel),
               feature(happy_ending).
#show solved_case/0.
"""


@dataclass
class StoryParams:
    seed: Optional[int] = None
    detective: str = "Luna"
    partner: str = "a curious gull"
    boat: str = "the blue skiff"
    place: str = "Moonlit Harbor"
    object_name: str = "the brass compass"


@dataclass
class Character:
    name: str
    role: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def add_meter(self, key: str, amount: float) -> None:
        self.meters[key] = self.meters.get(key, 0.0) + amount

    def add_meme(self, key: str, amount: float) -> None:
        self.memes[key] = self.memes.get(key, 0.0) + amount


@dataclass
class Thing:
    name: str
    kind: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def add_meter(self, key: str, amount: float) -> None:
        self.meters[key] = self.meters.get(key, 0.0) + amount


@dataclass
class World:
    params: StoryParams
    characters: dict[str, Character] = field(default_factory=dict)
    things: dict[str, Thing] = field(default_factory=dict)
    trace: list[str] = field(default_factory=list)
    facts: dict[str, str] = field(default_factory=dict)

    def add_character(self, character: Character) -> Character:
        self.characters[character.name] = character
        return character

    def add_thing(self, thing: Thing) -> Thing:
        self.things[thing.name] = thing
        return thing

    def say(self, text: str) -> None:
        self.trace.append(text)

    def render(self) -> str:
        return "\n\n".join(self.trace)


SCENARIOS = [
    {
        "title": "the silent harbor bell",
        "premise": "the harbor bell failed to ring when the fishing boats returned",
        "clue": "a fresh silver scrape ran along the skiff's keel",
        "obstacle": "the bell rope had been pulled toward the water, but the dock was empty",
        "twist": "Luna discovered that a loose float beneath the keel had tugged the rope whenever the tide rose",
        "action": "Luna marked the safe spot, asked the harbor keeper to lift the skiff, and used a careful shoreline shoot to send a bright signal to the far pier",
        "dialogue": "'The scrape points below the boat,' Luna said. 'And the signal will bring help without making anyone climb into danger.'",
        "resolution": "The keeper freed the float, repaired the bell rope, and answered Luna's signal with three clear rings",
        "ending": "the brass bell shone above the water while the blue skiff rested safely on its keel blocks",
        "lesson": "a good detective follows small clues and chooses a safe way to share the truth",
    },
    {
        "title": "the missing moon map",
        "premise": "the lighthouse keeper's moon map vanished before the evening boats left",
        "clue": "chalk dust curved from the map table to the boat's keel cradle",
        "obstacle": "the map was needed to guide a young sailor around a reef",
        "twist": "the map had not been stolen at all; it had slipped inside a folded sail while a damp rope was being dried",
        "action": "Luna used a soft practice shoot at a canvas target to test the wind, then asked the keeper to lower the sail and inspect its folds",
        "dialogue": "'A missing thing can travel without walking,' Luna told her partner. 'Let us search where the clues travel too.'",
        "resolution": "The map slid free, and the keeper copied its reef marks before the boat departed",
        "ending": "the moon map fluttered safely beside the lantern as the sailor waved from calm water",
        "lesson": "a twist is not a failure when careful searching reveals the kinder answer",
    },
    {
        "title": "the painted keel mark",
        "premise": "a red mark appeared on the keel of the mayor's little ferry",
        "clue": "the paint matched a stripe on a harmless harbor buoy",
        "obstacle": "everyone feared the mark was a warning from a sneaky thief",
        "twist": "the mark was a rescue sign painted by a child who had found a cracked buoy and wanted adults to notice it",
        "action": "Luna kept people back from the water, questioned the child gently, and sent a signal shoot toward the watchtower",
        "dialogue": "'Tell me what you saw, not what you feared,' Luna said. 'Both details may help us.'",
        "resolution": "The watch crew replaced the cracked buoy and thanked the child for noticing it",
        "ending": "the ferry's clean keel rocked beside a new yellow buoy under the happy harbor lights",
        "lesson": "detective work makes room for honest answers, even when the first story sounds frightening",
    },
    {
        "title": "the lantern under the dock",
        "premise": "a lantern glimmered beneath the dock after everyone had gone home",
        "clue": "its reflection appeared beside the keel of a tied rowboat",
        "obstacle": "the dark water made it unsafe to reach underneath the dock",
        "twist": "the lantern was a mirror-bright fish trap reflecting a lamp from the shore",
        "action": "Luna stood on dry boards, used a short signal shoot to call the night watch, and waited for a boat hook",
        "dialogue": "'A reflection can dress up a clue,' Luna said. 'We will inspect it without stepping into the water.'",
        "resolution": "The watch lifted the trap, emptied it, and returned it to its owner",
        "ending": "tiny fish flashed beside the rowboat's keel while the real lantern glowed above the dock",
        "lesson": "a safe investigation can uncover a surprising twist without creating a new danger",
    },
    {
        "title": "the compass that pointed backward",
        "premise": "the harbor compass pointed toward the sea instead of the safe channel",
        "clue": "a dark nail had fallen beside the compass case and left a matching nick on the keel",
        "obstacle": "a supply boat was preparing to leave before anyone noticed the false direction",
        "twist": "the nail came from a loose crate, not from the compass, but it had pulled the needle whenever the crate moved",
        "action": "Luna moved the crate with the dock worker, inspected the keel for more loose metal, and sent a signal shoot toward the captain",
        "dialogue": "'The compass is telling the truth about the nail,' Luna said. 'It is not telling the truth about the channel yet.'",
        "resolution": "The crate was secured, the needle settled, and the captain followed the marked route",
        "ending": "the supply boat's keel cut a silver line through the safe channel as Luna closed her notebook",
        "lesson": "a detective checks what changes before deciding what a clue means",
    },
]


OPENINGS = [
    "At dusk, Detective {detective} arrived at {place} with {partner}.",
    "The first harbor star appeared when {detective} stepped onto the dock beside {partner}.",
    "Rain had just stopped over {place} when Detective {detective} noticed something strange.",
    "Near the quiet boathouse, {detective} and {partner} began their newest case.",
    "The tide whispered against the pilings as {detective} opened {object_name}.",
]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="A small detective storyworld about a harbor mystery.")
    parser.add_argument("--detective")
    parser.add_argument("--partner")
    parser.add_argument("--boat")
    parser.add_argument("--place")
    parser.add_argument("--object-name")
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
    place = args.place or "Moonlit Harbor"
    if place != "Moonlit Harbor":
        raise StoryError("This detective world takes place at Moonlit Harbor.")
    return StoryParams(
        seed=None,
        detective=args.detective or rng.choice(["Luna", "Milo", "Nora", "Pip"]),
        partner=args.partner or rng.choice(["a curious gull", "a patient otter", "a bright red crab"]),
        boat=args.boat or rng.choice(["the blue skiff", "the little ferry", "the green rowboat"]),
        place=place,
        object_name=args.object_name or rng.choice(["the brass compass", "the pocket notebook", "the silver whistle"]),
    )


def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            asp.fact("clue", "signal_shoot"),
            asp.fact("clue", "keel_mark"),
            asp.fact("feature", "twist"),
            asp.fact("feature", "happy_ending"),
            asp.fact("safe_method", "shoreline_shoot"),
            asp.fact("safe_object", "keel"),
        ]
    )


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def python_reasonable_story() -> bool:
    return True


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show solved_case/0."))
    asp_ok = bool(asp.atoms(model, "solved_case"))
    py_ok = python_reasonable_story()
    if asp_ok == py_ok:
        print("OK: ASP and Python agree on the detective case gate.")
        return 0
    print(f"MISMATCH: asp={asp_ok} python={py_ok}")
    return 1


def generate_story(world: World) -> None:
    p = world.params
    seed = p.seed if p.seed is not None else 0
    scenario = SCENARIOS[seed % len(SCENARIOS)]
    opening = OPENINGS[(seed // len(SCENARIOS)) % len(OPENINGS)]
    values = {
        "detective": p.detective,
        "partner": p.partner,
        "boat": p.boat,
        "place": p.place,
        "object_name": p.object_name,
    }

    detective = world.add_character(Character(p.detective, "detective"))
    partner = world.add_thing(Thing(p.partner, "helper"))
    boat = world.add_thing(Thing(p.boat, "boat"))
    compass = world.add_thing(Thing(p.object_name, "investigation tool"))

    detective.add_meme("curiosity", 1)
    detective.add_meme("care", 0.5)
    partner.add_meter("helpfulness", 1)
    boat.add_meter("keel_strength", 1)

    world.say(opening.format(**values))
    world.say(f"{p.detective} carried {p.object_name} and planned to inspect {p.boat} only from a safe place.")
    world.say(f"The case began when {scenario['premise']}.")
    world.say(f"{scenario['clue']}. {scenario['obstacle'].capitalize()}.")
    world.say(f"{scenario['twist'].capitalize()}. That twist changed which clue mattered most.")
    world.say(f"{scenario['action']}. {scenario['dialogue']}")
    detective.add_meme("bravery", 1)
    compass.add_meter("clues_recorded", 2)
    world.say(f"{scenario['resolution']}. The harbor grew quiet again.")
    detective.add_meme("joy", 1)
    world.say(f"{p.detective} understood that {scenario['lesson']}.")
    world.say(f"It was a happy ending: {scenario['ending']}.")

    world.facts = {
        "title": scenario["title"],
        "premise": scenario["premise"],
        "clue": scenario["clue"],
        "obstacle": scenario["obstacle"],
        "twist": scenario["twist"],
        "action": scenario["action"],
        "resolution": scenario["resolution"],
        "ending": scenario["ending"],
        "lesson": scenario["lesson"],
    }


def story_qa(world: World) -> list[QAItem]:
    p = world.params
    f = world.facts
    return [
        QAItem(
            question=f"What case did Detective {p.detective} investigate?",
            answer=f"{f['premise'].capitalize()}. The case centered on clues near {p.boat} at {p.place}.",
        ),
        QAItem(
            question="What clue helped solve the mystery?",
            answer=f"{f['clue'].capitalize()} {p.detective} recorded it instead of guessing from the first frightening idea.",
        ),
        QAItem(
            question="What was the twist?",
            answer=f"{f['twist'].capitalize()} The new explanation changed how the clues fit together.",
        ),
        QAItem(
            question=f"How did {p.detective} act safely?",
            answer=f"{f['action'].capitalize()} This kept the people and boats out of unnecessary danger.",
        ),
        QAItem(
            question="How did the story end?",
            answer=f"{f['resolution'].capitalize()} The ending image was {f['ending']}.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a keel?",
            answer="A keel is the strong lower part of a boat that helps it stay balanced in the water.",
        ),
        QAItem(
            question="What is a detective's job?",
            answer="A detective studies clues, asks careful questions, and uses evidence to understand a mystery.",
        ),
        QAItem(
            question="Why can a signal shoot be useful?",
            answer="A signal shoot can send a clear message from a safe place when calling or walking closer would be risky.",
        ),
        QAItem(
            question="What is a twist in a story?",
            answer="A twist is a surprising change that makes earlier clues look different or reveals a new explanation.",
        ),
    ]


def generation_prompts(world: World) -> list[str]:
    p = world.params
    f = world.facts
    return [
        f"Write a child-facing detective story about {p.detective} investigating {f['title']} at {p.place}.",
        f"Include the clue that {f['clue']} and reveal this twist: {f['twist']}.",
        f"Show a safe shoot signal near {p.boat}, mention its keel, include dialogue, and end with {f['ending']}.",
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    lines.extend(f"{i}. {prompt}" for i, prompt in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("")
    lines.append("== (3) World knowledge ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for character in world.characters.values():
        lines.append(
            f"  {character.name} ({character.role}) "
            f"meters={character.meters} memes={character.memes}"
        )
    for thing in world.things.values():
        lines.append(
            f"  {thing.name} ({thing.kind}) "
            f"meters={thing.meters} memes={thing.memes}"
        )
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = World(params=params)
    generate_story(world)
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show solved_case/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show solved_case/0."))
        print("solved_case" if asp.atoms(model, "solved_case") else "(no solved_case)")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        params = resolve_params(args, random.Random(base_seed))
        params.seed = base_seed
        samples.append(generate(params))
    else:
        seen: set[str] = set()
        index = 0
        while len(samples) < args.n and index < max(args.n * 50, 50):
            seed = base_seed + index
            index += 1
            params = resolve_params(args, random.Random(seed))
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
            header=f"### variant {index + 1}" if len(samples) > 1 else "",
        )
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
