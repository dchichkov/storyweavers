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
feature(twist).
feature(reconciliation).
ingredient(bacon).
action(remove).
virtue(listening).
heroic(safe_rescue).
can_reconcile :- feature(twist), feature(reconciliation), virtue(listening).
can_remove_bacon :- ingredient(bacon), action(remove), heroic(safe_rescue).
happy_superhero_story :- can_reconcile, can_remove_bacon.
#show happy_superhero_story/0.
"""


@dataclass
class StoryParams:
    seed: Optional[int] = None
    name: str = "Luna"
    companion: str = "Comet"
    snack: str = "bacon biscuits"
    place: str = "Skyline City"
    object_name: str = "the silver signal badge"


@dataclass
class Character:
    name: str
    role: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def add_meter(self, key: str, delta: float) -> None:
        self.meters[key] = self.meters.get(key, 0.0) + delta

    def add_meme(self, key: str, delta: float) -> None:
        self.memes[key] = self.memes.get(key, 0.0) + delta


@dataclass
class Prop:
    name: str
    kind: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def add_meter(self, key: str, delta: float) -> None:
        self.meters[key] = self.meters.get(key, 0.0) + delta


@dataclass
class World:
    params: StoryParams
    characters: dict[str, Character] = field(default_factory=dict)
    props: dict[str, Prop] = field(default_factory=dict)
    trace: list[str] = field(default_factory=list)
    facts: dict[str, str] = field(default_factory=dict)

    def add_character(self, character: Character) -> Character:
        self.characters[character.name] = character
        return character

    def add_prop(self, prop: Prop) -> Prop:
        self.props[prop.name] = prop
        return prop

    def say(self, line: str) -> None:
        self.trace.append(line)

    def render(self) -> str:
        return "\n\n".join(self.trace)


SCENARIOS = [
    {
        "title": "the bacon signal",
        "premise": "a red emergency light blinked above the city breakfast festival",
        "problem": "The signal tower's lunch lift had jammed, leaving a tray of bacon treats stuck between floors while the festival crowd gathered below",
        "clue": "the lift moved a little whenever the old music button was pressed",
        "twist": "The tower was not under attack at all; a shy robot cook had hidden inside to stop a sauce spill",
        "action": "{name} removed the loose bacon tray from the lift's path, then asked the robot cook what had happened",
        "dialogue": "'I thought you caused the trouble,' {name} said. 'I was frightened,' replied the robot. 'Let's fix it together,' said {name}.",
        "resolution": "The robot showed {name} a stuck sauce valve, and together they closed it before the lift moved again",
        "ending": "the robot served warm bacon biscuits to the crowd from a bright, safe lift",
        "lesson": "a true superhero listens for the story behind a problem before choosing whom to blame",
    },
    {
        "title": "the missing bacon banner",
        "premise": "the giant bacon banner vanished from the roof of Hero Hall",
        "problem": "Without it, visiting children could not find the reconciliation picnic where two rival hero teams planned to meet",
        "clue": "tiny silver threads led from the empty pole toward the old clock tower",
        "twist": "The banner had not been stolen; a gust had carried it onto the clock tower, where a nestling bird was tangled in its ribbon",
        "action": "{name} removed the ribbon from the nest only after the bird rescuer arrived, then helped lower the banner carefully",
        "dialogue": "'We can rescue the bird and keep the banner,' said {name}. 'I was ready to accuse someone,' admitted Captain Vale.",
        "resolution": "The rescuers freed the bird, and both hero teams agreed to repair the banner together",
        "ending": "the bacon banner fluttered above a picnic where old rivals passed plates to one another",
        "lesson": "reconciliation begins when people replace quick blame with patient help",
    },
    {
        "title": "the smoky snack signal",
        "premise": "a smoky cloud curled from the superhero canteen during the bacon cook-off",
        "problem": "Everyone thought a villain had sabotaged the ovens, and the two cook teams began shouting",
        "clue": "only the oven marked with a blue star was smoking, while its safety fan stayed still",
        "twist": "The smoke came from a forgotten paper recipe, not a villain's machine",
        "action": "{name} removed the paper with a long kitchen grabber and asked both teams to step back",
        "dialogue": "'I blamed your team too soon,' Chef Bolt said. 'And I blamed yours,' answered Chef Spark. 'Then let us clean this up together,' said {name}.",
        "resolution": "The chefs reconciled, repaired the fan, and restarted the cook-off with fresh bacon",
        "ending": "two chef capes waved from the same counter as the safe ovens warmed the room",
        "lesson": "a twist can turn an argument into a chance to understand one another",
    },
    {
        "title": "the bacon-powered rescue cart",
        "premise": "a tiny rescue cart rolled in circles around the city plaza, carrying a basket of bacon",
        "problem": "Its steering cord had wrapped around a fountain post, and two junior heroes argued about who had made the mistake",
        "clue": "the cart's bell rang three times whenever the cord pulled tight",
        "twist": "The cart had been following a lost puppy's bacon scent, not running away",
        "action": "{name} removed the cord from the post and asked the arguing heroes to hold the basket steady",
        "dialogue": "'We both wanted to help,' said Pip. 'Yes, but we forgot to listen,' said Dot. 'Now listen together,' replied {name}.",
        "resolution": "The heroes guided the cart to the puppy's family and apologized to each other",
        "ending": "the reunited puppy wagged beside the rescue cart while the heroes shared one bacon biscuit",
        "lesson": "reconciliation grows when people admit mistakes and return to the same helpful goal",
    },
]


OPENINGS = [
    "At sunrise, {name}, the neighborhood superhero of {place}, met {companion} beside the bright city gates.",
    "In {place}, every hero knew that {name} could hear a frightened whisper beneath a noisy alarm.",
    "The morning patrol began when {name} tightened the silver signal badge and followed {companion} across {place}.",
    "Above {place}, the clouds shone gold as {name} prepared for a day of rescues, teamwork, and {snack}.",
    "The city bells rang over {place}, and {name} raced out with {companion} to help whoever needed a hero.",
]


TURNS = [
    "That was the twist: the loudest-looking trouble was hiding a smaller, sadder story.",
    "Instead of using super strength first, {name} used the most important heroic power of all: listening.",
    "The clue changed the plan, and the plan changed the hearts of the people nearby.",
    "A real hero can remove danger without removing someone's dignity.",
    "The mystery became easier once everyone stopped shouting long enough to hear the truth.",
]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="A child-facing superhero storyworld about bacon, twists, and reconciliation.")
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
    return StoryParams(
        name=args.name or rng.choice(["Luna", "Nova", "Milo", "Zara", "Theo"]),
        companion=args.companion or rng.choice(["Comet", "a pocket robot", "Captain Whiskers"]),
        snack=args.snack or rng.choice(["bacon biscuits", "bacon sandwiches", "crispy bacon stars"]),
        place=args.place or "Skyline City",
        object_name=args.object_name or rng.choice(["the silver signal badge", "the red rescue cape", "the moon-shaped shield"]),
    )


def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            asp.fact("feature", "twist"),
            asp.fact("feature", "reconciliation"),
            asp.fact("ingredient", "bacon"),
            asp.fact("action", "remove"),
            asp.fact("virtue", "listening"),
            asp.fact("heroic", "safe_rescue"),
        ]
    )


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def python_reasonable_story() -> bool:
    return bool(ASP_RULES and "bacon" in asp_facts() and "remove" in asp_facts() and "twist" in asp_facts() and "reconciliation" in asp_facts())


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show happy_superhero_story/0."))
    asp_ok = bool(asp.atoms(model, "happy_superhero_story"))
    py_ok = python_reasonable_story()
    if asp_ok == py_ok:
        print("OK: ASP and Python agree on the superhero story gate.")
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
        "snack": p.snack,
        "place": p.place,
        "object_name": p.object_name,
    }

    hero = world.add_character(Character(p.name, "superhero"))
    helper = world.add_character(Character(p.companion, "helper"))
    badge = world.add_prop(Prop(p.object_name, "hero gear"))
    bacon = world.add_prop(Prop("bacon", "festival food"))

    hero.add_meme("courage", 1.0)
    hero.add_meme("listening", 0.5)
    helper.add_meme("trust", 0.5)
    badge.add_meter("signal_strength", 1.0)
    bacon.add_meter("warmth", 1.0)

    world.say(opening.format(**values))
    world.say(f"{p.name} carried {p.object_name}, while {p.companion} guarded a basket of {p.snack}.")
    world.say(f"Then came {scenario['title']}: {scenario['premise']}.")
    world.say(f"{scenario['problem']}. {scenario['clue']}.")
    world.say(f"{scenario['twist']}.")
    world.say(turn.format(**values))
    world.say(f"{scenario['action'].format(**values)}.")
    world.say(scenario["dialogue"])
    hero.add_meme("bravery", 1.0)
    hero.add_meme("empathy", 1.0)
    badge.add_meter("usefulness", 1.0)
    world.say(f"{scenario['resolution'].format(**values)}.")
    world.say(f"Everyone shared {p.snack}, because solving trouble was sweeter when nobody was left out.")
    world.say(f"{p.name} understood that {scenario['lesson']}.")
    world.say(f"By evening, {scenario['ending']}. That was the happy ending in {p.place}.")

    world.facts = {
        "title": scenario["title"],
        "problem": scenario["problem"],
        "clue": scenario["clue"],
        "twist": scenario["twist"],
        "action": scenario["action"].format(**values),
        "resolution": scenario["resolution"].format(**values),
        "lesson": scenario["lesson"],
        "ending": scenario["ending"],
    }


def story_qa(world: World) -> list[QAItem]:
    p = world.params
    f = world.facts
    return [
        QAItem(
            question=f"What problem did {p.name} face in {f['title']}?",
            answer=f"{f['problem']}. It needed a careful rescue rather than a hurried guess.",
        ),
        QAItem(
            question="What clue helped reveal the twist?",
            answer=f"{f['clue']}. That detail showed that the first frightening explanation was not the whole truth.",
        ),
        QAItem(
            question="What was the twist?",
            answer=f"{f['twist']}. The twist helped the heroes understand whom to help.",
        ),
        QAItem(
            question="How did the hero use the power to remove danger?",
            answer=f"{f['action']}. The action protected people while also respecting the person or creature involved.",
        ),
        QAItem(
            question="How did reconciliation change the ending?",
            answer=f"{f['resolution']}. The characters repaired both the practical problem and their hurt feelings.",
        ),
        QAItem(
            question="What image proves the story ended happily?",
            answer=f"{f['ending']}. The image shows safety, teamwork, and a shared future.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a twist in a story?",
            answer="A twist is a surprising change in what the characters and reader thought was happening.",
        ),
        QAItem(
            question="What is reconciliation?",
            answer="Reconciliation is the work of making peace after people have argued or hurt one another.",
        ),
        QAItem(
            question="Why should a superhero listen before acting?",
            answer="Listening can reveal the real problem, prevent unfair blame, and help a hero choose a safer rescue.",
        ),
        QAItem(
            question="How can bacon fit into a superhero adventure?",
            answer="Bacon can be a warm, concrete festival food that brings characters together after they solve the trouble.",
        ),
    ]


def generation_prompts(world: World) -> list[str]:
    p = world.params
    f = world.facts
    return [
        f"Write a child-facing superhero story in {p.place} starring {p.name}.",
        f"Include bacon, a safe action to remove danger, and this twist: {f['twist']}.",
        f"Show reconciliation through this resolution: {f['resolution']}.",
        f"End with this concrete happy image: {f['ending']}.",
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
    for prop in world.props.values():
        lines.append(f"  {prop.name} ({prop.kind}) meters={prop.meters} memes={prop.memes}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    if not params.name.strip():
        raise StoryError("The hero needs a name.")
    if not params.place.strip():
        raise StoryError("The superhero story needs a setting.")
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
        print(asp_program("#show happy_superhero_story/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show happy_superhero_story/0."))
        print("happy_superhero_story" if asp.atoms(model, "happy_superhero_story") else "(no happy_superhero_story)")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        params = StoryParams(
            seed=base_seed,
            name=args.name or "Luna",
            companion=args.companion or "Comet",
            snack=args.snack or "bacon biscuits",
            place=args.place or "Skyline City",
            object_name=args.object_name or "the silver signal badge",
        )
        samples.append(generate(params))
    else:
        seen: set[str] = set()
        attempt = 0
        while len(samples) < max(0, args.n) and attempt < max(50, args.n * 50):
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
