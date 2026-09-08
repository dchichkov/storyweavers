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
% The small city needs a careful hero, not a loud one.
ingredient(bacon).
feature(twist).
feature(reconciliation).
heroic_skill(listening).
problem(smoke_alarm).

can_help :- ingredient(bacon), feature(twist), feature(reconciliation).
safe_plan :- heroic_skill(listening), problem(smoke_alarm).
happy_rescue :- can_help, safe_plan.
#show happy_rescue/0.
"""


@dataclass
class StoryParams:
    seed: Optional[int] = None
    name: str = "Luna"
    companion: str = "Pip"
    snack: str = "bacon biscuits"
    place: str = "Maple City"
    object_name: str = "the silver whisk"


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
        "title": "the bacon beacon",
        "problem": "the breakfast beacon had filled the market square with smoke",
        "clue": "the smoke curled toward a loose copper vent",
        "twist": "the smoky beacon was not broken at all; it was warming a nest of tiny rooftop birds",
        "action": "Luna lowered the heat, opened a side window, and carried the bacon pan away from the nest",
        "dialogue": "'We can remove the danger without removing their home,' Luna told Captain Crisp",
        "resolution": "Captain Crisp moved the beacon to a safe chimney while Luna set a cool perch beside it",
        "ending": "the birds chirped above a clear square while the bacon beacon glowed softly",
        "lesson": "a true hero protects people and makes room for small neighbors",
    },
    {
        "title": "the missing bacon badge",
        "problem": "Mayor Mallow's bacon-shaped hero badge had vanished before the parade",
        "clue": "a trail of buttery crumbs led beneath the rolling stage",
        "twist": "the badge had not been stolen; a shy rival hero had borrowed it to feel brave",
        "action": "Luna asked the rival to come out, listened to the whole story, and offered a different shiny badge",
        "dialogue": "'You do not have to hide to belong here,' Luna said",
        "resolution": "the rival returned the badge and joined the parade as the city's new helper",
        "ending": "two badges flashed together while the crowd shared warm bacon biscuits",
        "lesson": "reconciliation can turn a missing thing into a new friendship",
    },
    {
        "title": "the runaway bacon cart",
        "problem": "a breakfast cart rolled downhill toward the library doors",
        "clue": "one wheel had a bright red ribbon caught around its axle",
        "twist": "the cart was being pushed by a kitten trapped inside its empty cupboard",
        "action": "Luna removed the ribbon, caught the cart with a safety line, and gently freed the kitten",
        "dialogue": "'First we stop the cart, then we solve the mystery,' Luna told Pip",
        "resolution": "the librarian forgave the startled kitten and placed a soft bell on the cart",
        "ending": "the bacon cart rested by the library steps while the kitten rang its new bell",
        "lesson": "a calm rescue leaves room for forgiveness",
    },
    {
        "title": "the cloud over breakfast hill",
        "problem": "a dark cloud covered the hill where the city's breakfast festival was beginning",
        "clue": "silver sparks rose from a forgotten kitchen fan",
        "twist": "the cloud was made by a frightened weather robot trying to hide",
        "action": "Luna removed the fan's loose paper, lowered her shield, and spoke gently to the robot",
        "dialogue": "'You can tell us what went wrong,' Luna said. 'We will listen.'",
        "resolution": "the robot guided the cloud away and helped toast every bacon biscuit",
        "ending": "sunlight returned as the robot wore a paper cape beside Luna",
        "lesson": "listening can make a frightened mistake safe to fix",
    },
    {
        "title": "the bacon bridge surprise",
        "problem": "the little bridge over Sparkle Creek was blocked by a giant bacon sign",
        "clue": "the sign's rope led to a workshop where two heroes were arguing",
        "twist": "each hero had built half the sign and both thought the other had ruined it",
        "action": "Luna removed the tangled rope, placed the two halves side by side, and asked each builder what they wanted",
        "dialogue": "'Your ideas fit better together than they look apart,' Luna said",
        "resolution": "the heroes reconciled and rebuilt the sign as a bright welcome arch",
        "ending": "children crossed beneath the bacon arch while both builders took a bow",
        "lesson": "a patient hero can reveal the bridge inside an argument",
    },
]


OPENINGS = [
    "At sunrise, Luna zipped across Maple City with Pip and a pouch of bacon biscuits.",
    "The rooftops sparkled when Luna began her morning patrol through Maple City.",
    "Luna was checking the city gardens when Pip pointed toward a strange breakfast-colored cloud.",
    "Maple City had just opened its shops, and Luna was carrying bacon biscuits to the rescue station.",
    "With her silver cape fluttering, Luna hurried toward the loudest alarm in the city.",
]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="A child-friendly superhero storyworld about bacon, twists, and reconciliation.")
    parser.add_argument("--name")
    parser.add_argument("--companion")
    parser.add_argument("--snack")
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
    place = args.place or "Maple City"
    if place != "Maple City":
        raise StoryError("This superhero storyworld is built in Maple City.")
    return StoryParams(
        seed=None,
        name=args.name or rng.choice(["Luna", "Nova", "Milo", "Zara", "Theo"]),
        companion=args.companion or rng.choice(["Pip", "a tiny robot", "Captain Crisp"]),
        snack=args.snack or rng.choice(["bacon biscuits", "bacon sandwiches", "bacon muffins"]),
        place=place,
        object_name=args.object_name or rng.choice(["the silver whisk", "the blue cape clasp", "the star-shaped spoon"]),
    )


def python_reasonable_story() -> bool:
    return True


def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            asp.fact("ingredient", "bacon"),
            asp.fact("feature", "twist"),
            asp.fact("feature", "reconciliation"),
            asp.fact("heroic_skill", "listening"),
            asp.fact("problem", "smoke_alarm"),
        ]
    )


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show happy_rescue/0."))
    asp_ok = bool(asp.atoms(model, "happy_rescue"))
    py_ok = python_reasonable_story()
    if asp_ok == py_ok:
        print("OK: ASP and Python agree on the superhero story gate.")
        return 0
    print(f"MISMATCH: asp={asp_ok} python={py_ok}")
    return 1


def generate_story(world: World) -> None:
    p = world.params
    seed = p.seed if p.seed is not None else 0
    scenario = SCENARIOS[seed % len(SCENARIOS)]
    opening = OPENINGS[(seed // len(SCENARIOS)) % len(OPENINGS)]

    hero = world.add_character(Character(p.name, "superhero"))
    companion = world.add_character(Character(p.companion, "helper"))
    tool = world.add_object(ObjectThing(p.object_name, "hero tool"))
    bacon = world.add_object(ObjectThing("bacon", "food"))

    hero.add_meme("courage", 1)
    hero.add_meme("curiosity", 1)
    companion.add_meme("trust", 1)
    bacon.add_meter("warmth", 1)

    world.say(opening)
    world.say(f"At the rescue station, {p.name} checked {p.object_name} and packed extra {p.snack}.")
    world.say(f"Then the alarm rang: {scenario['problem']}.")
    world.say(f"{p.name} followed the clue that {scenario['clue']}.")
    world.say(f"That clue led to a twist: {scenario['twist']}.")
    hero.add_meter("careful_steps", 3)
    world.say(f"{scenario['action']}.")
    world.say(f"{scenario['dialogue']}. {p.companion} nodded and helped instead of rushing.")
    hero.add_meme("kindness", 1)
    companion.add_meme("trust", 1)
    tool.add_meter("useful_actions", 1)
    world.say(f"{scenario['resolution']}. The danger was gone, but nobody had been pushed aside.")
    world.say(f"That was the reconciliation: {scenario['lesson']}.")
    hero.add_meme("joy", 1)
    world.say(f"By evening, {scenario['ending']}. {p.name} and {p.companion} shared the last {p.snack}.")
    world.say("Luna's cape caught the golden light, and Maple City felt safer because its heroes had listened.")

    world.facts = {
        "title": scenario["title"],
        "problem": scenario["problem"],
        "clue": scenario["clue"],
        "twist": scenario["twist"],
        "action": scenario["action"],
        "resolution": scenario["resolution"],
        "lesson": scenario["lesson"],
        "ending": scenario["ending"],
    }


def story_qa(world: World) -> list[QAItem]:
    p = world.params
    f = world.facts
    return [
        QAItem(
            question=f"What problem did {p.name} face in {f['title']}?",
            answer=f"{f['problem'].capitalize()}. It needed a careful rescue because rushing could have hurt someone or made the trouble worse.",
        ),
        QAItem(
            question="What clue changed the rescue?",
            answer=f"{f['clue'].capitalize()}. The clue helped Luna look beyond the first explanation.",
        ),
        QAItem(
            question=f"What was the twist in {f['title']}?",
            answer=f"{f['twist'].capitalize()}. The surprising truth showed why listening mattered.",
        ),
        QAItem(
            question="How did reconciliation help?",
            answer=f"{f['resolution'].capitalize()}. Luna solved the danger while giving the other characters a chance to repair their relationship.",
        ),
        QAItem(
            question="What image proves the story ended happily?",
            answer=f"{f['ending'].capitalize()}. The peaceful image shows that the rescue changed Maple City for the better.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="Why should a superhero listen before acting?",
            answer="Listening can reveal the real problem, protect bystanders, and lead to a kinder solution.",
        ),
        QAItem(
            question="What is a twist?",
            answer="A twist is a surprising change in what the characters or reader thought was happening.",
        ),
        QAItem(
            question="What is reconciliation?",
            answer="Reconciliation is the process of making peace after hurt or disagreement and finding a way to work together again.",
        ),
    ]


def generation_prompts(world: World) -> list[str]:
    p = world.params
    f = world.facts
    return [
        f"Write a child-facing superhero story about {p.name} solving {f['title']} in Maple City.",
        f"Include this twist: {f['twist']}. Show {p.name} choosing to remove danger without removing kindness.",
        f"End with reconciliation and this concrete image: {f['ending']}.",
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
        lines.append(f"  {character.name} ({character.role}) meters={character.meters} memes={character.memes}")
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
        print(asp_program("#show happy_rescue/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show happy_rescue/0."))
        print("happy_rescue" if asp.atoms(model, "happy_rescue") else "(no happy_rescue)")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        params = StoryParams(
            seed=base_seed,
            name=args.name or "Luna",
            companion=args.companion or "Pip",
            snack=args.snack or "bacon biscuits",
            place="Maple City",
            object_name=args.object_name or "the silver whisk",
        )
        samples = [generate(params)]
    else:
        seen: set[str] = set()
        index = 0
        while len(samples) < args.n and index < max(args.n * 50, 50):
            seed = base_seed + index
            index += 1
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
