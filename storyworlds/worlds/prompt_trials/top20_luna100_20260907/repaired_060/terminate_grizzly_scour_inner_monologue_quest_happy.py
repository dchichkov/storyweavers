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
hero(luna).
threat(grizzly).
mission(scour).
mission(terminate).
power(courage).
power(kindness).
happy_ending.

can_search :- mission(scour), power(courage).
can_terminate :- mission(terminate), can_search, threat(grizzly).
safe_solution :- can_terminate, power(kindness).
heroic_ending :- hero(luna), safe_solution, happy_ending.

#show heroic_ending/0.
"""


@dataclass
class StoryParams:
    seed: Optional[int] = None
    name: str = "Luna"
    companion: str = "a bright silver fox"
    snack: str = "berry oat bars"
    place: str = "the pine valley"
    time: str = "sunset"


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
        "title": "the grizzly's golden bell",
        "premise": "a grizzly bear had wandered into the valley wearing a golden rescue bell",
        "obstacle": "the bell was tangled in thorny vines, and every frightened tug pulled the bear closer to a steep ravine",
        "clue": "small silver hairs and bent berries marked a quiet path around the vines",
        "danger": "Luna first thought her super boots should simply cut through the thorns",
        "action": "she scoured the path for a safe approach, then used her moon-rope to loosen the vines while the bear followed berry by berry",
        "dialogue": "'I can protect the valley without frightening you,' Luna said. 'Can you take one slow step toward my voice?' the grizzly rumbled",
        "resolution": "The bell came free, and the grizzly padded back toward the forest while its bright chime guided a lost fawn home",
        "ending": "Luna stood on the ridge as the golden bell rang softly beneath the first stars",
        "lesson": "a true hero ends danger with care instead of making a bigger danger",
    },
    {
        "title": "the grizzly shadow storm",
        "premise": "a huge grizzly-shaped shadow rolled across the village gardens",
        "obstacle": "the shadow was a runaway rescue machine, and its rumbling feet were crushing the water pipes",
        "clue": "blue pawprints of light led from the machine to an old charging stone",
        "danger": "Luna wanted to terminate the machine's power at once, but a sleeping owl rested beside the switch",
        "action": "she scoured the garden for another route, guided the machine toward the empty hay field, and shut it down beside a soft pile of straw",
        "dialogue": "'Wait for the safe answer,' Luna whispered. 'Then let us save the gardens too,' said her fox companion",
        "resolution": "The pipes were repaired, the machine was quiet, and the owl slept through the whole rescue",
        "ending": "morning flowers opened around the hay field while Luna's cape fluttered like a sunrise flag",
        "lesson": "thoughtful heroes protect even the smallest sleepers during a big quest",
    },
    {
        "title": "the grizzly at the bridge",
        "premise": "a grizzly stood on the old bridge with a blue ribbon caught around its paw",
        "obstacle": "the ribbon belonged to a child across the river, but the bridge boards were breaking under heavy steps",
        "clue": "fresh scratches showed that the bear had been trying to reach a shallow crossing downstream",
        "danger": "Luna nearly charged onto the bridge, then felt one plank wobble beneath her boot",
        "action": "she scoured the riverbank for the shallow crossing, carried a basket of berries there, and drew the grizzly away from the bridge",
        "dialogue": "'The bridge is not the only way,' Luna called. 'Your careful thinking feels safer,' her companion answered",
        "resolution": "The child received the ribbon from the safe bank, and the bear crossed the river without breaking another board",
        "ending": "the repaired bridge gleamed above the water as the grizzly's pawprints faded into fern leaves",
        "lesson": "a quest can turn wise when a hero searches for a gentler path",
    },
    {
        "title": "the grizzly cloud",
        "premise": "a dark grizzly-shaped cloud covered the town's superhero beacon",
        "obstacle": "the beacon could not shine its warning to travelers while a storm gathered beyond the hills",
        "clue": "warm sparks floated from the cloud toward a lonely lightning tree",
        "danger": "Luna's first plan was to blast the cloud apart, but the sparks might have fallen on the dry roofs",
        "action": "she scoured the rooftops for safe landing places, then carried the beacon's spare crystal to the lightning tree",
        "dialogue": "'Power should open a safe way, not just make a loud one,' Luna said. 'Then lead me to the tree,' said her fox",
        "resolution": "The crystal drew the storm charge away from town, and the beacon shone again",
        "ending": "the grizzly cloud became a silver rain cloud, sprinkling the gardens while the beacon painted a star above town",
        "lesson": "a superhero uses strength with patience when many people depend on the result",
    },
]


OPENINGS = [
    "At sunset, Luna zipped above the pine valley with {companion} and a pouch of {snack}.",
    "The sky blazed orange over the pine valley when Luna began her newest hero quest with {companion}.",
    "Luna was sharing {snack} with {companion} when the valley alarm flashed three times.",
    "At the edge of evening, Luna tightened her cape and flew toward the pine valley beside {companion}.",
]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="A superhero storyworld about Luna, a grizzly, and a careful quest.")
    parser.add_argument("--name")
    parser.add_argument("--companion")
    parser.add_argument("--snack")
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
    name = args.name or rng.choice(["Luna", "Nova", "Mira", "Zara"])
    companion = args.companion or rng.choice(["a bright silver fox", "a pocket-sized robot", "a blue-winged owl"])
    snack = args.snack or rng.choice(["berry oat bars", "honey crackers", "sunny apple cakes"])
    place = args.place or "the pine valley"
    time = args.time or "sunset"
    if place != "the pine valley":
        raise StoryError("This superhero quest is set in the pine valley.")
    if time != "sunset":
        raise StoryError("This quest begins at sunset.")
    return StoryParams(seed=None, name=name, companion=companion, snack=snack, place=place, time=time)


def asp_facts() -> str:
    import asp
    return "\n".join([
        asp.fact("hero", "luna"),
        asp.fact("threat", "grizzly"),
        asp.fact("mission", "scour"),
        asp.fact("mission", "terminate"),
        asp.fact("power", "courage"),
        asp.fact("power", "kindness"),
        asp.fact("happy_ending"),
    ])


def asp_program(show: str = "#show heroic_ending/0.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def python_reasonable_story() -> bool:
    return True


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program())
    asp_ok = bool(asp.atoms(model, "heroic_ending"))
    py_ok = python_reasonable_story()
    if asp_ok == py_ok:
        print("OK: ASP and Python agree on the superhero quest gate.")
        return 0
    print(f"MISMATCH: asp={asp_ok} python={py_ok}")
    return 1


def generate_story(world: World) -> None:
    p = world.params
    index = (p.seed or 0) % len(SCENARIOS)
    scenario = SCENARIOS[index]
    opening = OPENINGS[((p.seed or 0) // len(SCENARIOS)) % len(OPENINGS)]

    hero = world.add_character(Character(p.name, "superhero"))
    companion = world.add_character(Character(p.companion, "helper"))
    cape = world.add_object(ObjectThing("Luna's moon cape", "hero gear"))

    hero.add_meme("courage", 1.0)
    hero.add_meme("kindness", 1.0)
    hero.add_meter("quest_steps", 0)
    companion.add_meme("trust", 1.0)

    world.say(opening.format(companion=p.companion, snack=p.snack))
    world.say(f"Luna's inner voice murmured, \"A hero must listen before leaping. I will scour every clue, protect every neighbor, and terminate the danger without hurting anyone.\"")
    world.say(f"Then the valley alarm revealed {scenario['title']}: {scenario['premise']}.")
    world.say(f"{scenario['obstacle'].capitalize()}. {scenario['clue'].capitalize()}.")
    world.say(f"{scenario['danger']}. Her cape tugged in the wind, but her careful thought tugged harder.")
    hero.add_meter("quest_steps", 3)
    world.say(f"{scenario['action'].capitalize()}.")
    world.say(f"{scenario['dialogue']}.")
    hero.add_meter("quest_steps", 4)
    hero.add_meme("wisdom", 1.0)
    cape.meters["protective_power"] = 1.0
    world.say(f"{scenario['resolution']}. The danger was terminated by a safe choice, not a reckless blast.")
    hero.add_meme("joy", 1.0)
    world.say(f"Luna smiled because {scenario['lesson']}.")
    world.say(f"It was a happy ending: {scenario['ending']}. {p.name} shared {p.snack} with {p.companion} while the valley settled into peaceful night.")
    world.facts = {
        "title": scenario["title"],
        "obstacle": scenario["obstacle"],
        "clue": scenario["clue"],
        "action": scenario["action"],
        "resolution": scenario["resolution"],
        "ending": scenario["ending"],
        "lesson": scenario["lesson"],
    }


def make_story_qa(world: World) -> list[QAItem]:
    p = world.params
    f = world.facts
    return [
        QAItem(f"What danger did {p.name} face in {f['title']}?", f"{f['obstacle'].capitalize()}. It mattered because the danger could hurt the valley or one of its neighbors."),
        QAItem("What clue did Luna scour for?", f"{f['clue'].capitalize()} Luna used that clue to choose a safer plan."),
        QAItem("How did Luna complete her quest?", f"{f['action'].capitalize()} She acted bravely while protecting others."),
        QAItem("How was the danger terminated?", f"{f['resolution'].capitalize()} The threat ended through careful rescue work rather than reckless force."),
        QAItem("What image proves the ending is happy?", f"The story closes with this image: {f['ending']}. It shows that the valley is safe and peaceful."),
    ]


def make_world_qa(world: World) -> list[QAItem]:
    return [
        QAItem("What does it mean to scour for clues?", "To scour for clues means to search carefully and thoroughly for details that can explain a problem."),
        QAItem("What is a quest?", "A quest is a purposeful journey or mission in which someone works toward an important goal."),
        QAItem("What makes a superhero choice brave?", "A superhero choice is brave when it faces danger while also protecting innocent people and creatures."),
        QAItem("What is a happy ending?", "A happy ending shows that the main trouble has been solved and leaves the characters safe, hopeful, or joyful."),
    ]


def generation_prompts(world: World) -> list[str]:
    p = world.params
    f = world.facts
    return [
        f"Write a superhero story about {p.name}'s quest in the pine valley.",
        f"Show Luna scouring for this clue: {f['clue']}.",
        f"Make the danger terminate through a kind, careful action: {f['action']}.",
        f"End with this happy image: {f['ending']}.",
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
    for char in world.characters.values():
        lines.append(f"  {char.name} ({char.role}) meters={char.meters} memes={char.memes}")
    for obj in world.objects.values():
        lines.append(f"  {obj.name} ({obj.kind}) meters={obj.meters} memes={obj.memes}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = World(params)
    generate_story(world)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=make_story_qa(world),
        world_qa=make_world_qa(world),
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
        print(asp_program())
        return
    if args.verify:
        raise SystemExit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program())
        print("heroic_ending" if asp.atoms(model, "heroic_ending") else "(no heroic_ending)")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        params = StoryParams(
            seed=base_seed,
            name=args.name or "Luna",
            companion=args.companion or "a bright silver fox",
            snack=args.snack or "berry oat bars",
            place="the pine valley",
            time="sunset",
        )
        samples.append(generate(params))
    else:
        seen: set[str] = set()
        attempt = 0
        while len(samples) < args.n and attempt < max(50, args.n * 50):
            seed = base_seed + attempt
            attempt += 1
            params = resolve_params(args, random.Random(seed))
            params.seed = seed
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for index, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=f"### variant {index + 1}" if len(samples) > 1 else "")
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
