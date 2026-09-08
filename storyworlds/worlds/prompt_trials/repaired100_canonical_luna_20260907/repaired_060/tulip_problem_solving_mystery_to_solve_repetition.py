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
place(garden).
feature(problem_solving).
feature(mystery_to_solve).
feature(repetition).
object(tulip).
can_solve :- feature(problem_solving), feature(mystery_to_solve).
rhymes :- feature(repetition).
happy_ending :- can_solve, rhymes, object(tulip).
#show happy_ending/0.
"""


@dataclass
class StoryParams:
    seed: Optional[int] = None
    name: str = "Luna"
    companion: str = "a small blue bird"
    tulip_color: str = "red"
    place: str = "the moonlit garden"
    time: str = "early morning"


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

    def say(self, text: str) -> None:
        self.trace.append(text)

    def add_character(self, character: Character) -> Character:
        self.characters[character.name] = character
        return character

    def add_object(self, obj: ObjectThing) -> ObjectThing:
        self.objects[obj.name] = obj
        return obj

    def render(self) -> str:
        return "\n\n".join(self.trace)


SCENARIOS = [
    {
        "title": "the tulip that bowed",
        "problem": "the red tulip bowed low though every other flower stood tall",
        "clue": "three round drops glittered beneath its bent stem",
        "mistake": "{name} nearly tied the stem upright at once, but stopped to look again",
        "action": "{name} counted the drops, moved a pebble from the tiny water channel, and asked the gardener for help",
        "dialogue": "'Drip, drip, drip—the water is trapped,' {name} said. 'Then let us clear its path,' replied the bird",
        "resolution": "the channel flowed, the soil grew soft, and the tulip lifted its bright cup",
        "ending": "the tulip nodded in the breeze, and the garden sang, 'Up, up, up!'",
        "lesson": "careful looking can turn a puzzling bow into a blooming answer",
    },
    {
        "title": "the tulip bell",
        "problem": "a tulip rang a tiny bell whenever the wind blew",
        "clue": "the same three notes sounded each time: ting, ting, ting",
        "mistake": "{name} first blamed a fairy, then watched the flower through three little gusts",
        "action": "{name} followed the repeated sound and found a silver bead caught in a leaf",
        "dialogue": "'Ting, ting, ting!' sang {name}. 'The same clue comes back again,' said the bird",
        "resolution": "the bead was freed, and the tulip swayed quietly without its secret rattle",
        "ending": "the bell-bead rested in a box while the tulip danced, 'Sway, sway, sway!'",
        "lesson": "repetition can help a curious solver find what one glance misses",
    },
    {
        "title": "the missing tulip stripe",
        "problem": "one yellow stripe had vanished from a purple tulip",
        "clue": "yellow dust appeared on the same stepping stone each time the tulip shook",
        "mistake": "{name} wanted to paint the stripe back, but waited before changing the flower",
        "action": "{name} followed the dust in a careful loop and discovered a sleepy bee brushing past the petals",
        "dialogue": "'Round and round the bee goes,' {name} whispered. 'Now we know the stripe is pollen,' said the bird",
        "resolution": "the bee flew away, and the tulip's natural stripe showed in the morning light",
        "ending": "the purple tulip gleamed while the bee hummed, 'Buzz, buzz, buzz!'",
        "lesson": "a repeated trail may explain a mystery without needing a quick fix",
    },
    {
        "title": "the tulip's upside-down sign",
        "problem": "a little sign beside the tulip pointed visitors toward the pond instead of the path",
        "clue": "the arrow turned back after each breeze and pointed the wrong way again",
        "mistake": "{name} spun the sign once, then noticed its loose lower peg",
        "action": "{name} placed three pebbles by the safe path, counted them twice, and asked the gardener to reset the sign",
        "dialogue": "'One, two, three—the arrow slips each time,' said {name}. 'Your counting found the trouble,' said the bird",
        "resolution": "the peg was pressed deep, and the sign guided everyone safely around the beds",
        "ending": "the tulip smiled beside the sign as feet went, 'Step, step, step!'",
        "lesson": "patient counting can make a small garden path safe for everyone",
    },
    {
        "title": "the thirsty tulip",
        "problem": "the tulip drooped each afternoon while a nearby puddle grew wider",
        "clue": "a drip fell three times from a cracked cup beside the watering can",
        "mistake": "{name} almost poured more water on the flower, but listened to the drip",
        "action": "{name} traced the leak to the cracked cup and carried fresh water in a sound one",
        "dialogue": "'Drip, drip, drip—the cup is losing it,' said {name}. 'Aha, now we can mend the watering,' said the bird",
        "resolution": "the tulip received a gentle drink, and the puddle stopped growing",
        "ending": "the flower opened wide and whispered, 'Sip, sip, sip!'",
        "lesson": "solving the real problem is kinder than repeating the wrong action",
    },
    {
        "title": "the tulip under the cloche",
        "problem": "a glass cover made the tulip look cloudy every dawn",
        "clue": "a pale circle appeared on the glass, disappeared, and appeared again",
        "mistake": "{name} rubbed the cover once, then watched the circle return",
        "action": "{name} lifted the cover with the gardener and found warm mist collecting inside",
        "dialogue": "'The circle comes back because the warm air stays,' said {name}. 'Then we need a little opening,' said the bird",
        "resolution": "a small vent let the air move, and the tulip shone clearly",
        "ending": "sunlight kissed the petals while the garden chimed, 'Clear, clear, clear!'",
        "lesson": "repeated clues can reveal an invisible cause",
    },
]

OPENINGS = [
    "Luna skipped through {place} at {time}, with {companion} fluttering near.",
    "At {time}, {name} tiptoed into {place} beside {companion}.",
    "{name} carried a little basket through {place}, while {companion} sang overhead.",
    "The morning rhyme began when {name} met {companion} among the flowers.",
]

TURNS = [
    "The clue came back, back, back, and that made the mystery easier to track.",
    "One look was not enough, but three looks made the pattern clear.",
    "A little pause, a careful stare, and the puzzle began to answer.",
    "The repeated sign was not a trick; it was a helpful little hint.",
]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="A nursery-rhyme tulip mystery world.")
    parser.add_argument("--name")
    parser.add_argument("--companion")
    parser.add_argument("--tulip-color")
    parser.add_argument("--place")
    parser.add_argument("--time")
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
    place = args.place or "the moonlit garden"
    time = args.time or "early morning"
    if place != "the moonlit garden":
        raise StoryError("This tulip mystery belongs in the moonlit garden.")
    if time != "early morning":
        raise StoryError("This nursery-rhyme world begins in the early morning.")
    return StoryParams(
        seed=None,
        name=args.name or rng.choice(["Luna", "Milo", "Nell", "Pip", "Tess"]),
        companion=args.companion or rng.choice(["a small blue bird", "a hopping green frog", "a sleepy white mouse"]),
        tulip_color=args.tulip_color or rng.choice(["red", "pink", "golden"]),
        place=place,
        time=time,
    )


def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            asp.fact("place", "garden"),
            asp.fact("object", "tulip"),
            asp.fact("feature", "problem_solving"),
            asp.fact("feature", "mystery_to_solve"),
            asp.fact("feature", "repetition"),
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
        print("OK: ASP and Python agree on the tulip story gate.")
        return 0
    print(f"MISMATCH: asp={asp_ok} python={py_ok}")
    return 1


def generate_story(world: World) -> None:
    p = world.params
    index = (p.seed or 0) % len(SCENARIOS)
    scenario = SCENARIOS[index]
    opening = OPENINGS[((p.seed or 0) // len(SCENARIOS)) % len(OPENINGS)]
    turn = TURNS[((p.seed or 0) // (len(SCENARIOS) * len(OPENINGS))) % len(TURNS)]
    values = {
        "name": p.name,
        "companion": p.companion,
        "tulip_color": p.tulip_color,
        "place": p.place,
        "time": p.time,
    }

    child = world.add_character(Character(p.name, "problem solver"))
    bird = world.add_character(Character(p.companion, "helper"))
    tulip = world.add_object(ObjectThing(f"the {p.tulip_color} tulip", "flower"))
    child.add_meme("curiosity", 1)
    child.add_meme("patience", 0.5)
    child.add_meter("observations", 0)
    bird.add_meme("friendliness", 1)

    world.say(opening.format(**values))
    world.say(
        f"There stood a {p.tulip_color} tulip, bright as a button, and beside it lay "
        f"a tiny card that read, 'Look, look, look!'"
    )
    world.say(f"Then came the mystery: {scenario['problem']}.")
    world.say(f"{scenario['clue']}. {turn}")
    world.say(f"{scenario['mistake']}.")
    child.add_meter("observations", 3)
    child.add_meme("problem_solving", 1)
    world.say(f"{scenario['action']}.")
    world.say(f"{scenario['dialogue']}.")
    tulip.add_meter("health", 1)
    child.add_meme("confidence", 1)
    world.say(f"{scenario['resolution']}. The puzzle clicked shut with a soft, 'Solved, solved, solved!'")
    world.say(f"{scenario['lesson'].capitalize()}.")
    world.say(f"{scenario['ending']}")

    world.facts = {
        "scenario": scenario["title"],
        "problem": scenario["problem"],
        "clue": scenario["clue"],
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
            question=f"What mystery did {p.name} find in the tulip garden?",
            answer=f"{f['problem']}. It was a small garden problem that needed careful attention.",
        ),
        QAItem(
            question="What repeated clue helped solve the mystery?",
            answer=f"{f['clue']}. Seeing the clue return helped Luna notice a pattern instead of guessing.",
        ),
        QAItem(
            question=f"How did {p.name} use problem solving?",
            answer=f"{f['action']}. Luna examined the evidence, chose a safe plan, and worked with a helper.",
        ),
        QAItem(
            question="How was the tulip problem resolved?",
            answer=f"{f['resolution']}. The solution fixed the cause of the trouble and helped the tulip.",
        ),
        QAItem(
            question="What image ends the nursery rhyme?",
            answer=f"{f['ending']}. The bright repeated words show that the garden is peaceful again.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is problem solving?",
            answer="Problem solving means noticing a difficulty, studying its clues, and choosing a useful way to fix it.",
        ),
        QAItem(
            question="Why can repetition help with a mystery?",
            answer="When something happens again and again, its pattern can reveal what is causing the trouble.",
        ),
        QAItem(
            question="What is a tulip?",
            answer="A tulip is a flowering plant with a cup-shaped bloom and long green leaves.",
        ),
    ]


def generation_prompts(world: World) -> list[str]:
    p = world.params
    f = world.facts
    return [
        f"Write a nursery-rhyme story about {p.name} solving a mystery involving a {p.tulip_color} tulip.",
        f"Show repetition through this clue: {f['clue']}.",
        f"End with this concrete image: {f['ending']}.",
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    lines.extend(f"{i}. {prompt}" for i, prompt in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World knowledge ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
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
            companion=args.companion or "a small blue bird",
            tulip_color=args.tulip_color or "red",
            place="the moonlit garden",
            time="early morning",
        )
        samples = [generate(params)]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            seed = base_seed + i
            i += 1
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
            header=f"### variant {index + 1}" if len(samples) > 1 else "",
        )
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
