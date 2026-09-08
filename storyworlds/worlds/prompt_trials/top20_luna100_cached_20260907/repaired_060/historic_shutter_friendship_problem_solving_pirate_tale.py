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
% A tiny pirate world with a historic shutter, friendship, and problem solving.
place(old_lighthouse).
object(historic_shutter).
feature(friendship).
feature(problem_solving).
helper(parrot).
safe_plan :- historic_shutter, problem_solving, friendship.
happy_ending :- safe_plan, helper(parrot).
#show happy_ending/0.
"""


@dataclass
class StoryParams:
    seed: Optional[int] = None
    name: str = "Luna"
    friend: str = "Pip"
    parrot: str = "Captain Peep"
    ship: str = "the Moonbeam"
    place: str = "the old lighthouse"
    treasure: str = "a brass compass"


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
class ObjectThing:
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
    objects: dict[str, ObjectThing] = field(default_factory=dict)
    trace: list[str] = field(default_factory=list)
    facts: dict[str, str] = field(default_factory=dict)

    def add_character(self, character: Character) -> Character:
        self.characters[character.name] = character
        return character

    def add_object(self, obj: ObjectThing) -> ObjectThing:
        self.objects[obj.name] = obj
        return obj

    def say(self, text: str) -> None:
        self.trace.append(text)

    def render(self) -> str:
        return "\n\n".join(self.trace)


SCENARIOS = [
    {
        "title": "the shutter at stormwatch tower",
        "premise": "the lighthouse's historic wooden shutter slammed in the wind and blocked its bright warning lamp",
        "clue": "a loose rope had wrapped around the brass latch, while three old scrape marks showed how the shutter usually opened",
        "obstacle": "Sailors beyond the reef could not see the harbor's safe channel before the storm arrived",
        "mistake": "Luna reached for the shutter at once, but a hard gust made the tower door shudder",
        "action": "Luna and Pip tied a line to the lower hinge, used the old scrape marks as a guide, and asked Captain Peep to call when the rope went slack",
        "dialogue": "'We can solve this together,' Luna said. 'You watch the rope, and I will watch the hinge.'",
        "resolution": "The friends freed the rope, eased the shutter open, and revealed the steady lamp",
        "ending": "the historic shutter rested safely against the stone wall while a golden beam swept across the dark water",
        "lesson": "friendship turns a frightening problem into a plan that careful hands can finish",
    },
    {
        "title": "the painted harbor clue",
        "premise": "the historic shutter wore a faded blue fish, but one hinge had slipped and covered half the picture",
        "clue": "the missing fish eye was painted on the stone beside the hinge, showing where the old shutter had once rested",
        "obstacle": "Without the picture, visiting sailors could not tell which window marked the harbor office",
        "mistake": "Pip wanted to yank the shutter upward, but Luna noticed the brittle paint cracking near his fingers",
        "action": "The friends placed a plank beneath the shutter, copied the stone mark, and lifted only after checking the weight together",
        "dialogue": "'Slow hands protect old things,' Pip said. Luna nodded, 'And good friends remind us when to slow down.'",
        "resolution": "They reset the hinge without harming the paint, and the blue fish pointed clearly toward the harbor office",
        "ending": "moonlight glimmered on the fish's restored eye as the two friends welcomed the sailors ashore",
        "lesson": "problem solving means listening, observing, and caring for what belongs to everyone",
    },
    {
        "title": "the parrot behind the shutter",
        "premise": "Captain Peep vanished behind a historic shutter that had stuck halfway open",
        "clue": "his red feather bobbed beside a narrow gap, and a trail of crumbs led beneath the sill",
        "obstacle": "The parrot was safe but could not find his way back through the jammed opening",
        "mistake": "Luna nearly pulled the shutter wider, then heard the old wood creak like a tired ship",
        "action": "Luna kept the shutter still, while Pip slid a lantern through the gap and followed the crumb trail from the other side",
        "dialogue": "'Peep, stay where you are,' Luna called. 'We know where you are now,' Pip answered.",
        "resolution": "Pip found a fallen brass cup blocking the track, and the friends removed it before opening the shutter gently",
        "ending": "Captain Peep perched on the historic frame and shouted a proud, 'Pieces of eight!'",
        "lesson": "friends solve problems best when they share clues instead of rushing alone",
    },
    {
        "title": "the tide-table shutter",
        "premise": "a historic shutter covered the lighthouse's tide table just as the tide began to rise",
        "clue": "a chalk arrow on the floor pointed to a second viewing slot beside the shutter",
        "obstacle": "The crew needed the tide table to guide the Moonbeam through a shallow channel",
        "mistake": "Pip guessed the tide from the waves, but Luna saw the rocks appearing and disappearing at different times",
        "action": "Luna read the chalk arrow, Pip held the lantern, and Captain Peep repeated the numbers from the old table",
        "dialogue": "'The sea gives clues, but the table gives a safer answer,' Luna said. 'Then let us use both,' Pip replied.",
        "resolution": "They found the viewing slot, read the tide correctly, and steered the Moonbeam around the shallow rocks",
        "ending": "the ship glided into calm water while the historic shutter clicked softly in the evening breeze",
        "lesson": "problem solving grows stronger when friends compare what each one notices",
    },
]


OPENINGS = [
    "At moonrise, Luna sailed the Moonbeam toward the old lighthouse with Pip and Captain Peep.",
    "The sea was dark as ink when Luna and Pip climbed from the Moonbeam to the old lighthouse.",
    "A silver moon followed Luna, Pip, and Captain Peep toward the old lighthouse after supper.",
    "The Moonbeam rocked gently below the old lighthouse while Luna and Pip carried a lantern ashore.",
    "On a breezy pirate night, Luna checked the Moonbeam's rope and climbed toward the old lighthouse with Pip.",
]


TURNS = [
    "That small clue changed the problem from a frightening mystery into a puzzle with pieces.",
    "Instead of tugging harder, Luna let the old marks show them where to begin.",
    "The friends stopped, listened, and made a plan that gave every hand a job.",
    "A careful look proved more useful than a strong pull.",
    "The next step became clear when Luna and Pip put their clues together.",
]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="A child-facing pirate tale about a historic shutter, friendship, and problem solving."
    )
    parser.add_argument("--name")
    parser.add_argument("--friend")
    parser.add_argument("--parrot")
    parser.add_argument("--ship")
    parser.add_argument("--place")
    parser.add_argument("--treasure")
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
    place = args.place or "the old lighthouse"
    if place != "the old lighthouse":
        raise StoryError("This pirate tale takes place at the old lighthouse.")
    return StoryParams(
        seed=None,
        name=args.name or rng.choice(["Luna", "Mara", "Nico", "Tavi", "Rafi"]),
        friend=args.friend or rng.choice(["Pip", "Jory", "Milo", "Bess"]),
        parrot=args.parrot or rng.choice(["Captain Peep", "Redbeak", "Polly"]),
        ship=args.ship or rng.choice(["the Moonbeam", "the Sea Star", "the Little Kraken"]),
        place=place,
        treasure=args.treasure or rng.choice(["a brass compass", "a pearl spyglass", "a silver key"]),
    )


def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            asp.fact("place", "old_lighthouse"),
            asp.fact("object", "historic_shutter"),
            asp.fact("feature", "friendship"),
            asp.fact("feature", "problem_solving"),
            asp.fact("helper", "parrot"),
        ]
    )


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def python_reasonable_story() -> bool:
    return True


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show happy_ending/0."))
    asp_ok = bool(asp.atoms(model, "happy_ending"))
    py_ok = python_reasonable_story()
    if asp_ok == py_ok:
        print("OK: ASP and Python agree on the pirate-story gate.")
        return 0
    print(f"MISMATCH: asp={asp_ok} python={py_ok}")
    return 1


def generate_story(world: World) -> None:
    p = world.params
    index = p.seed if p.seed is not None else 0
    scenario = SCENARIOS[index % len(SCENARIOS)]
    opening = OPENINGS[(index // len(SCENARIOS)) % len(OPENINGS)]
    turn = TURNS[(index // (len(SCENARIOS) * len(OPENINGS))) % len(TURNS)]
    values = {
        "name": p.name,
        "friend": p.friend,
        "parrot": p.parrot,
        "ship": p.ship,
        "place": p.place,
        "treasure": p.treasure,
    }

    def text(key: str) -> str:
        return scenario[key].format(**values)

    luna = world.add_character(Character(p.name, "young pirate"))
    friend = world.add_character(Character(p.friend, "friend"))
    parrot = world.add_character(Character(p.parrot, "parrot"))
    shutter = world.add_object(ObjectThing("the historic shutter", "historic wooden shutter"))
    compass = world.add_object(ObjectThing(p.treasure, "navigation treasure"))

    luna.add_meme("curiosity", 1)
    luna.add_meme("bravery", 0.5)
    friend.add_meme("friendship", 1)
    parrot.add_meter("watchfulness", 1)
    shutter.add_meter("age", 100)
    compass.add_meter("usefulness", 1)

    world.say(opening)
    world.say(f"Luna carried {p.treasure}, but tonight's greatest treasure was a safe way home.")
    world.say(f"At the tower, they found {text('premise')}.")
    world.say(f"{text('obstacle')}. {text('clue')}.")
    world.say(f"{text('mistake')}. {turn}")
    world.say(f"{text('action')}. {text('dialogue')}")
    luna.add_meme("bravery", 1)
    friend.add_meme("trust", 1)
    shutter.add_meter("safe_position", 1)
    world.say(f"{text('resolution')}. The crew cheered from the Moonbeam.")
    world.say(f"Everyone agreed that {text('lesson')}.")
    world.say(f"It was a happy pirate ending: {text('ending')}.")
    world.facts = {
        "scenario": scenario["title"],
        "obstacle": text("obstacle"),
        "clue": text("clue"),
        "action": text("action"),
        "resolution": text("resolution"),
        "lesson": text("lesson"),
        "ending": text("ending"),
    }


def story_qa(world: World) -> list[QAItem]:
    p = world.params
    f = world.facts
    return [
        QAItem(
            question=f"What problem did {p.name} and {p.friend} face?",
            answer=f"They faced this problem: {f['obstacle']}. The historic shutter made the trouble urgent because others needed the lighthouse's help.",
        ),
        QAItem(
            question="What clue helped the friends?",
            answer=f"The important clue was this: {f['clue']}. They used it instead of pulling at the old shutter blindly.",
        ),
        QAItem(
            question="How did friendship help solve the problem?",
            answer=f"{f['action']}. Each friend had a useful job, so they could act carefully and support one another.",
        ),
        QAItem(
            question="How was the problem resolved?",
            answer=f"{f['resolution']}. Their solution protected the old shutter and helped the people at sea.",
        ),
        QAItem(
            question="What image closes the pirate tale?",
            answer=f"The story ends with {f['ending']}. That image shows that the lighthouse and its friends are safe.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is friendship?",
            answer="Friendship is caring about another person, listening to them, and helping them through a difficult moment.",
        ),
        QAItem(
            question="What is problem solving?",
            answer="Problem solving means noticing the facts, making a careful plan, trying it safely, and changing the plan when new clues appear.",
        ),
        QAItem(
            question="Why should a historic shutter be handled gently?",
            answer="A historic shutter is an old part of a place's story, so gentle handling can protect its wood, paint, and useful memories.",
        ),
    ]


def generation_prompts(world: World) -> list[str]:
    p = world.params
    f = world.facts
    return [
        f"Write a child-facing pirate tale about {p.name} and {p.friend} at {p.place}.",
        f"Show friendship and problem solving through this clue: {f['clue']}.",
        f"End with this concrete lighthouse image: {f['ending']}.",
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
    for obj in world.objects.values():
        lines.append(f"  {obj.name} ({obj.kind}) meters={obj.meters} memes={obj.memes}")
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

    if args.show_asp:
        print(asp_program("#show happy_ending/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show happy_ending/0."))
        print("happy_ending" if asp.atoms(model, "happy_ending") else "(no happy_ending)")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        params = StoryParams(
            seed=base_seed,
            name=args.name or "Luna",
            friend=args.friend or "Pip",
            parrot=args.parrot or "Captain Peep",
            ship=args.ship or "the Moonbeam",
            place="the old lighthouse",
            treasure=args.treasure or "a brass compass",
        )
        samples.append(generate(params))
    else:
        seen: set[str] = set()
        attempt = 0
        while len(samples) < args.n and attempt < max(args.n * 50, 50):
            seed = base_seed + attempt
            attempt += 1
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
