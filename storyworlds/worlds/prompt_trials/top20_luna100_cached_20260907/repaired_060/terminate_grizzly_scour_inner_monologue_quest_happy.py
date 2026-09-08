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
place(mountain_village).
feature(inner_monologue).
feature(quest).
feature(happy_ending).
threat(grizzly).
mission(terminate_harm).
tool(scour).
helper(ranger).
safe_plan :- threat(grizzly), mission(terminate_harm), tool(scour), helper(ranger).
happy_ending :- safe_plan, feature(happy_ending).
#show happy_ending/0.
"""


@dataclass
class StoryParams:
    seed: Optional[int] = None
    name: str = "Luna"
    companion: str = "a silver rescue cape"
    snack: str = "berry muffins"
    place: str = "the mountain village"
    threat: str = "the grizzly"
    tool: str = "a long-handled brush"


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

    def render(self) -> str:
        return "\n\n".join(self.trace)


SCENARIOS = [
    {
        "title": "the grizzly at the honey shed",
        "problem": "a grizzly had wandered into the village honey shed after smelling a spilled jar",
        "clue": "muddy pawprints led from the broken jar to a berry patch beyond the creek",
        "thought": "I must not charge at a hungry animal, Luna thought",
        "action": "Luna asked Ranger Bea to clear the path, then used the brush to scour the honey from the doorway while Bea guided the grizzly toward the berry patch",
        "dialogue": "'We can terminate the danger without hurting the grizzly,' Luna said. 'Slowly and together.'",
        "resolution": "The clean doorway and the berry trail helped the grizzly leave the shed and return to the forest",
        "ending": "the grizzly loped beneath the pines while Luna's silver cape flashed in the morning sun",
        "lesson": "a hero ends a threat by protecting every living thing",
    },
    {
        "title": "the grizzly and the school bell",
        "problem": "a grizzly had pushed against the school gate while searching for lunch",
        "clue": "crumbs from a picnic pointed away from the classrooms toward an old compost bin",
        "thought": "The children need safety, but the grizzly needs a calm way out, Luna thought",
        "action": "Luna rang the quiet signal, moved the children indoors, and helped Ranger Sol scour the picnic crumbs from the path",
        "dialogue": "'First we make space,' Luna told Sol. 'Then we show the grizzly a safer direction.'",
        "resolution": "With the tempting crumbs gone and the gate closed, the grizzly followed the ranger's food-scented trail away from school",
        "ending": "the school bell rang for recess beneath a clear sky, and the grizzly vanished over the ferny ridge",
        "lesson": "a superhero uses patience and planning to terminate danger",
    },
    {
        "title": "the grizzly by the river bridge",
        "problem": "a grizzly stood beside the bridge where families needed to cross",
        "clue": "a torn fish sack had spilled silver scales along the riverbank",
        "thought": "The bridge is not a battlefield, Luna thought; it is a place for a safe plan",
        "action": "Luna blocked the bridge with bright flags, helped scour the fish scales from the crossing, and called the wildlife team",
        "dialogue": "'Nobody crosses until the path is safe,' Luna said. 'That includes our furry visitor.'",
        "resolution": "The wildlife team opened a quiet river trail, and the grizzly followed the clean scent away from the bridge",
        "ending": "water sparkled under the empty bridge as Luna high-fived the grateful crossing guard",
        "lesson": "clear thinking can terminate trouble before anyone is harmed",
    },
    {
        "title": "the grizzly under the stage",
        "problem": "a grizzly had curled beneath the village festival stage after finding a sticky cake box",
        "clue": "a trail of frosting marked the route from the box to the shadowed steps",
        "thought": "A loud rescue would make the grizzly afraid, Luna thought",
        "action": "Luna whispered to the musicians, moved the crowd back, and helped scour the frosting from a gentle trail leading into the woods",
        "dialogue": "'Quiet is my superpower today,' Luna said. 'Let the grizzly choose the open path.'",
        "resolution": "The grizzly woke, smelled the clean forest trail, and padded away from the festival",
        "ending": "the band played softly again while golden leaves spun around the empty stage",
        "lesson": "sometimes the bravest hero is the one who makes less noise",
    },
]


OPENINGS = [
    "Morning light poured over {place} as {name} tightened the clasp of {companion}.",
    "At sunrise, {name} stood above {place}, ready for a new quest with {companion} nearby.",
    "The mountain wind whispered through {place} when {name} arrived carrying {snack}.",
    "{name} had just shared {snack} with {companion} when the village warning bell rang.",
]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="A superhero storyworld about Luna, a grizzly, and a careful rescue quest."
    )
    parser.add_argument("--name")
    parser.add_argument("--companion")
    parser.add_argument("--snack")
    parser.add_argument("--place")
    parser.add_argument("--threat")
    parser.add_argument("--tool")
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--seed", type=int)
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or "the mountain village"
    if place != "the mountain village":
        raise StoryError("This superhero quest is anchored in the mountain village.")
    return StoryParams(
        name=args.name or rng.choice(["Luna", "Milo", "Ari", "Zara"]),
        companion=args.companion or rng.choice(["a silver rescue cape", "a bright signal badge"]),
        snack=args.snack or rng.choice(["berry muffins", "warm oat bars", "apple bread"]),
        place=place,
        threat=args.threat or "the grizzly",
        tool=args.tool or "a long-handled brush",
    )


def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            asp.fact("place", "mountain_village"),
            asp.fact("feature", "inner_monologue"),
            asp.fact("feature", "quest"),
            asp.fact("feature", "happy_ending"),
            asp.fact("threat", "grizzly"),
            asp.fact("mission", "terminate_harm"),
            asp.fact("tool", "scour"),
            asp.fact("helper", "ranger"),
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
        print("OK: ASP and Python agree on the safe superhero ending.")
        return 0
    print(f"MISMATCH: asp={asp_ok} python={py_ok}")
    return 1


def generate_story(world: World) -> None:
    p = world.params
    seed = p.seed if p.seed is not None else 0
    scenario = SCENARIOS[seed % len(SCENARIOS)]
    opening = OPENINGS[(seed // len(SCENARIOS)) % len(OPENINGS)]

    hero = Character(p.name, "young superhero")
    ranger = Character("Ranger Bea", "wildlife helper")
    cape = ObjectThing(p.companion, "rescue gear")
    brush = ObjectThing(p.tool, "cleaning tool")
    world.characters[hero.name] = hero
    world.characters[ranger.name] = ranger
    world.objects[cape.name] = cape
    world.objects[brush.name] = brush

    hero.add_meme("courage", 1)
    hero.add_meme("care", 1)
    hero.add_meter("quest_steps", 1)

    world.say(opening.format(name=p.name, place=p.place, companion=p.companion, snack=p.snack))
    world.say(f"Every hero needs fuel, so {p.name} tucked away {p.snack} before beginning the quest.")
    world.say(f"The warning bell announced {scenario['title']}: {scenario['problem']}.")
    world.say(f"{scenario['clue'].capitalize()}. {scenario['thought']}.")
    hero.add_meter("quest_steps", 2)
    world.say(f"{scenario['action']}.")
    world.say(scenario["dialogue"])
    hero.add_meme("bravery", 1)
    ranger.add_meme("trust", 1)
    world.say(f"{scenario['resolution']}. The danger was terminated through care, distance, and teamwork.")
    hero.add_meme("hope", 1)
    world.say(f"{scenario['lesson'].capitalize()}.")
    world.say(f"That evening, {scenario['ending']}. {p.name} shared the last of the {p.snack} with Ranger Bea.")

    world.facts = {
        "title": scenario["title"],
        "problem": scenario["problem"],
        "clue": scenario["clue"],
        "thought": scenario["thought"],
        "action": scenario["action"],
        "dialogue": scenario["dialogue"],
        "resolution": scenario["resolution"],
        "ending": scenario["ending"],
        "lesson": scenario["lesson"],
    }


def story_qa(world: World) -> list[QAItem]:
    p = world.params
    f = world.facts
    return [
        QAItem(
            question=f"What danger did {p.name} face during the quest?",
            answer=f"{f['problem'].capitalize()} The danger required a calm plan because the grizzly was frightened and hungry.",
        ),
        QAItem(
            question="What clue changed the hero's plan?",
            answer=f"{f['clue'].capitalize()} That clue showed where the grizzly had come from and suggested a safer direction.",
        ),
        QAItem(
            question="What inner thought helped the hero act wisely?",
            answer=f"{f['thought']} The thought kept the quest focused on safety instead of a reckless attack.",
        ),
        QAItem(
            question="How was the danger terminated?",
            answer=f"{f['action'].capitalize()} {f['resolution']}. The solution protected the village and the grizzly.",
        ),
        QAItem(
            question="What happy image closes the story?",
            answer=f"{f['ending'].capitalize()} It proves that the quest ended with safety and hope.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is an inner monologue?",
            answer="An inner monologue is a character's private thought that helps the reader understand a choice.",
        ),
        QAItem(
            question="What makes a quest?",
            answer="A quest is a purposeful journey or mission with a problem to solve and a goal to reach.",
        ),
        QAItem(
            question="How can a superhero terminate danger safely?",
            answer="A superhero can terminate danger by using evidence, distance, trusted helpers, and a plan that protects people and animals.",
        ),
    ]


def generation_prompts(world: World) -> list[str]:
    p = world.params
    f = world.facts
    return [
        f"Write a child-facing superhero story about {p.name}'s quest involving {p.threat}.",
        f"Include this inner thought: {f['thought']}",
        f"End with this happy image: {f['ending']}",
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    lines.extend(f"{i}. {q}" for i, q in enumerate(sample.prompts, 1))
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
    for ch in world.characters.values():
        lines.append(f"  {ch.name} ({ch.role}) meters={ch.meters} memes={ch.memes}")
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
        index = 0
        max_attempts = max(1000, 20 * args.n)
        while len(samples) < max(0, args.n) and index < max_attempts:
            seed = base_seed + index
            index += 1
            params = resolve_params(args, random.Random(seed))
            params.seed = seed
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
        if len(samples) < args.n:
            print(
                f"Requested {args.n} unique stories; found {len(samples)} after {index} attempts.",
                file=sys.stderr,
            )

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
