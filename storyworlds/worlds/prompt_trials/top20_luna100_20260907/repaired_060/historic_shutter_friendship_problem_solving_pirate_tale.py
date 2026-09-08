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
place(harbor).
object(historic_shutter).
feature(friendship).
feature(problem_solving).
helper(friend).
safe_plan :- feature(friendship), feature(problem_solving).
shutter_saved :- safe_plan, object(historic_shutter).
happy_ending :- shutter_saved.
#show happy_ending/0.
"""


@dataclass
class StoryParams:
    seed: Optional[int] = None
    name: str = "Luna"
    friend: str = "Pip"
    ship: str = "the Sea Star"
    place: str = "the old harbor"
    object_name: str = "the historic blue shutter"
    treasure: str = "a brass compass"
    weather: str = "a brisk sea wind"


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
        "title": "the shutter in the storm",
        "problem": "a sudden squall tore one hinge loose from the historic blue shutter above the harbor museum",
        "clue": "three old nail holes formed a triangle beside the cracked hinge",
        "turn": "Luna first wanted to climb the slick wall, but Pip pointed to the safer stairs",
        "action": "Luna tied a bright scarf around the loose shutter, fetched the museum keeper, and helped measure a matching wooden brace",
        "dialogue": "'A pirate crew solves trouble together,' Luna said. 'Then we will be a careful crew,' Pip replied",
        "resolution": "the keeper fitted the brace while Luna and Pip held the shutter steady from the dry landing",
        "ending": "the blue shutter rested firmly above the museum door as gulls wheeled over the bright harbor",
        "lesson": "friendship makes problem solving stronger because good friends share clues and choose safe plans",
    },
    {
        "title": "the map behind the shutter",
        "problem": "the historic shutter had swung open and rain was curling a treasured harbor map",
        "clue": "a carved star on the shutter pointed toward a hidden latch beneath the sill",
        "turn": "Luna nearly pulled the map away, then remembered that wet paper could tear",
        "action": "Luna asked Pip to fetch a dry cloth while she held the shutter closed with a boat hook",
        "dialogue": "'You saw the star,' Luna said. 'And you saw how to use it,' Pip answered",
        "resolution": "together they protected the map and showed the keeper the concealed latch",
        "ending": "the restored map dried beside the shutter, its tiny islands shining like crumbs of gold",
        "lesson": "friends solve puzzles best when each person notices a different part",
    },
    {
        "title": "the gull's secret bell",
        "problem": "a bell above the historic shutter rang whenever the wind moved, confusing sailors at the dock",
        "clue": "a length of blue cord was wrapped around the bell rope and caught on the shutter hook",
        "turn": "Luna reached toward the rope, but Pip noticed a stack of crates wobbling below it",
        "action": "they moved the crates away, marked the danger with a red scarf, and called the harbor carpenter",
        "dialogue": "'The bell is a mystery,' Pip said. 'The wobbling crates are the first problem,' Luna replied",
        "resolution": "the carpenter freed the cord and secured the bell without anyone standing beneath it",
        "ending": "one clear bell note floated across the water, followed by the happy flap of a white gull",
        "lesson": "problem solving begins by making the place safe for every friend",
    },
    {
        "title": "the compass in the blue frame",
        "problem": "a brass compass had slipped behind the historic shutter and sailors feared it was lost",
        "clue": "sunlight through a narrow crack made a bright line across the floorboards",
        "turn": "Luna guessed the compass had fallen into the sea, but Pip followed the light instead",
        "action": "they closed the shutter gently, swept only the dry floor, and found the compass beneath a curled rope",
        "dialogue": "'Your light-line found the way,' Luna said. 'Your careful broom saved the compass,' Pip replied",
        "resolution": "the compass was returned to the captain, who used it to check the ship's course",
        "ending": "the brass compass gleamed beside the blue shutter while the Sea Star pointed home",
        "lesson": "friendship turns separate observations into one clever solution",
    },
    {
        "title": "the paintbrush pirate",
        "problem": "salt air had peeled a white crescent from the historic shutter before the harbor festival",
        "clue": "an old paint tin under the sill still held a dry patch of the same blue color",
        "turn": "Luna wanted to paint the crescent quickly, but Pip tested the loose flakes first",
        "action": "they brushed away only the crumbling paint, mixed the old blue with fresh color, and asked the keeper to approve it",
        "dialogue": "'We should not hide a crack with paint,' Pip said. 'We should mend what the paint is telling us,' Luna answered",
        "resolution": "the keeper repaired the wood, and the children painted the finished patch together",
        "ending": "the shutter's blue crescent shone above festival flags and a table of warm sea biscuits",
        "lesson": "friends solve lasting problems by fixing the cause instead of covering it",
    },
    {
        "title": "the tide-clock shutter",
        "problem": "the historic shutter blocked the tide clock, so visitors could not read when the ferry should leave",
        "clue": "a shell wedged in the lower hinge made the shutter stop at the same angle each time",
        "turn": "Luna tried to tug the shutter, but Pip listened to the hinge before it moved",
        "action": "they kept visitors back, placed a wooden marker on the safe path, and asked the dockwright for a narrow tool",
        "dialogue": "'The hinge is speaking,' Pip whispered. 'Then we should listen before we pull,' Luna said",
        "resolution": "the dockwright removed the shell and oiled the hinge without scratching the old wood",
        "ending": "the tide clock became visible again, and the ferry bell answered from the sunny pier",
        "lesson": "careful friends listen to small clues before making a big move",
    },
    {
        "title": "the message under the shutter",
        "problem": "a faded message beneath the historic shutter had become unreadable after years of salt and rain",
        "clue": "the remaining letters matched symbols carved on the harbor's oldest anchor",
        "turn": "Luna wanted to guess the whole message, but Pip suggested copying only the letters they knew",
        "action": "they sketched the symbols, compared them with the anchor, and brought their notes to the town historian",
        "dialogue": "'A guess can sail us in circles,' Luna said. 'A clue can point north,' Pip replied",
        "resolution": "the historian read the message as a welcome to every honest sailor",
        "ending": "new lettering glowed beneath the shutter while children practiced saying welcome to the sea",
        "lesson": "problem solving grows when friends separate what they know from what they only guess",
    },
    {
        "title": "the shutter and the runaway parrot",
        "problem": "a harbor parrot fluttered behind the historic shutter and could not find its way out",
        "clue": "the parrot copied the rhythm of the museum door whenever the shutter opened",
        "turn": "Luna reached for the bird, but Pip warned that a frightened parrot might bite and fly higher",
        "action": "they opened the lower shutter panel, placed fruit on a safe crate, and called the bird's gentle owner",
        "dialogue": "'Let the parrot choose the path,' Pip said. 'We will make the path kind,' Luna replied",
        "resolution": "the parrot hopped onto the crate and returned to its owner without a chase",
        "ending": "green feathers bobbed above the shutter as the parrot called, 'Ahoy, friends!'",
        "lesson": "friendship means patience when a frightened creature needs help",
    },
]


OPENINGS = [
    "At sunrise, Luna and Pip sailed the Sea Star into the old harbor.",
    "The Sea Star rocked beside the old harbor while Luna and Pip shared a breakfast biscuit.",
    "With salt on their cheeks, Luna and Pip stepped onto the old harbor pier.",
    "Luna carried a coil of rope as Pip steered the Sea Star toward the old harbor.",
    "A bright gull swooped over the old harbor when Luna and Pip began their morning adventure.",
]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="A child-facing pirate tale about friendship and problem solving.")
    parser.add_argument("--name")
    parser.add_argument("--friend")
    parser.add_argument("--ship")
    parser.add_argument("--place")
    parser.add_argument("--object-name")
    parser.add_argument("--treasure")
    parser.add_argument("--weather")
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
    place = args.place or "the old harbor"
    if place != "the old harbor":
        raise StoryError("This pirate world is built around the old harbor.")
    return StoryParams(
        seed=None,
        name=args.name or rng.choice(["Luna", "Mara", "Nico", "Tess", "Rafi"]),
        friend=args.friend or rng.choice(["Pip", "Cora", "Finn", "Jo"]),
        ship=args.ship or rng.choice(["the Sea Star", "the Coral Finch", "the Moon Gull"]),
        place=place,
        object_name=args.object_name or "the historic blue shutter",
        treasure=args.treasure or rng.choice(["a brass compass", "a silver spyglass", "a pearl button"]),
        weather=args.weather or rng.choice(["a brisk sea wind", "a warm harbor breeze", "a misty tide"]),
    )


def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            asp.fact("place", "harbor"),
            asp.fact("object", "historic_shutter"),
            asp.fact("feature", "friendship"),
            asp.fact("feature", "problem_solving"),
            asp.fact("helper", "friend"),
        ]
    )


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def python_reasonable_story() -> bool:
    return bool(ASP_RULES and "historic_shutter" in asp_facts() and "friendship" in asp_facts())


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show happy_ending/0."))
    asp_ok = bool(asp.atoms(model, "happy_ending"))
    py_ok = python_reasonable_story()
    if asp_ok != py_ok:
        print(f"MISMATCH: asp={asp_ok} python={py_ok}")
        return 1
    sample = generate(StoryParams(seed=7))
    if not sample.story or not sample.story_qa:
        print("MISMATCH: generated story is incomplete")
        return 1
    print("OK: ASP and Python agree, and the story exercised successfully.")
    return 0


def generate_story(world: World) -> None:
    p = world.params
    seed = p.seed if p.seed is not None else 0
    scenario = SCENARIOS[seed % len(SCENARIOS)]
    opening = OPENINGS[(seed // len(SCENARIOS)) % len(OPENINGS)]

    hero = world.add_character(Character(p.name, "young pirate"))
    friend = world.add_character(Character(p.friend, "trusted deck friend"))
    shutter = world.add_object(ObjectThing(p.object_name, "historic harbor shutter"))
    compass = world.add_object(ObjectThing(p.treasure, "treasure"))

    hero.add_meme("curiosity", 1)
    hero.add_meme("bravery", 0.5)
    friend.add_meme("friendship", 1)
    shutter.add_meter("age", 100)
    compass.add_meter("importance", 1)

    world.say(f"{opening} The {p.weather} fluttered the sails.")
    world.say(
        f"Behind the harbor museum waited {p.object_name}, an old wooden guardian of sailors' stories. "
        f"Beside it rested {p.treasure}, ready for a careful adventure."
    )
    world.say(f"Then they discovered {scenario['title']}: {scenario['problem']}.")
    world.say(f"Their first useful clue was this: {scenario['clue']}.")
    world.say(f"{scenario['turn']}. That changed their plan from a risky guess to a careful search.")
    world.say(f"{scenario['action']}. {scenario['dialogue']}.")
    hero.add_meme("bravery", 1)
    hero.add_meme("problem_solving", 1)
    friend.add_meme("trust", 1)
    shutter.add_meter("stability", 1)
    world.say(f"{scenario['resolution']}. The harbor grew calm, and the friends shared a crunchy biscuit.")
    world.say(
        f"Luna understood that {scenario['lesson']}. "
        f"Friendship was not just sailing side by side; it was listening, sharing work, and caring about the result."
        .replace("Luna", p.name)
    )
    world.say(
        f"The pirate tale ended with {scenario['ending']}. "
        f"{p.name} and {p.friend} climbed aboard {p.ship}, carrying the lesson and leaving the old harbor safer."
    )

    world.facts = {
        "title": scenario["title"],
        "problem": scenario["problem"],
        "clue": scenario["clue"],
        "turn": scenario["turn"],
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
            question=f"What problem did {p.name} and {p.friend} find at the historic shutter?",
            answer=f"They found that {f['problem']}. The trouble mattered because the old harbor shutter protected an important piece of local history.",
        ),
        QAItem(
            question="What clue helped the friends?",
            answer=f"The clue was that {f['clue']}. They used that detail instead of making a hurried guess.",
        ),
        QAItem(
            question=f"How did {p.name} and {p.friend} show friendship?",
            answer=f"They showed friendship when {f['action']}. They listened to each other and shared the work.",
        ),
        QAItem(
            question="How did they solve the problem safely?",
            answer=f"They solved it when {f['resolution']}. Their plan protected both the friends and the historic shutter.",
        ),
        QAItem(
            question="What image proves the story ended happily?",
            answer=f"The ending image is {f['ending']}. It shows the repaired problem and the cheerful harbor afterward.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is friendship?",
            answer="Friendship is caring about someone, listening to them, and helping one another through difficult moments.",
        ),
        QAItem(
            question="What is problem solving?",
            answer="Problem solving means noticing what is wrong, studying useful clues, and choosing a careful action that can improve the situation.",
        ),
        QAItem(
            question="Why should historic objects be treated gently?",
            answer="Historic objects carry memories from earlier times, so gentle care helps people learn from them without causing new damage.",
        ),
    ]


def generation_prompts(world: World) -> list[str]:
    p = world.params
    f = world.facts
    return [
        f"Write a child-facing pirate tale about {p.name} and {p.friend} helping with {f['title']}.",
        f"Use this clue in the plot: {f['clue']}. Show friendship through shared problem solving.",
        f"End with this concrete harbor image: {f['ending']}.",
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
        params = resolve_params(args, random.Random(base_seed))
        params.seed = base_seed
        samples.append(generate(params))
    else:
        seen: set[str] = set()
        for offset in range(max(args.n * 50, 50)):
            if len(samples) >= args.n:
                break
            seed = base_seed + offset
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
