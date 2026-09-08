#!/usr/bin/env python3
"""
A small superhero storyworld about a brave search, a grizzly guardian, and a happy ending.

Seed premise:
A young hero must scour a mountain trail and terminate a runaway danger before it reaches the village.
The grizzly is not the villain; careful listening reveals how to help it, and the quest ends safely.
"""

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


@dataclass
class StoryParams:
    hero: str
    grizzly: str
    helper: str
    place: str
    object_name: str
    problem: int = 0
    monologue: int = 0
    quest: int = 0
    ending: int = 0
    seed: Optional[int] = None


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    label: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict[str, object] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

    def add(self, entity: Entity) -> Entity:
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


HEROES = ["Luna", "Milo", "Nova", "Pax", "Skye", "Robin"]
GRIZZLIES = ["Bruno", "Honey", "Moss", "Tundra", "Berry"]
HELPERS = ["Ari", "Jules", "Tess", "Kai", "Mina"]
PLACES = ["Whispering Ridge", "Pinecone Pass", "Silverfoot Mountain", "Cloudberry Trail"]
OBJECTS = ["the village bell", "the rescue beacon", "the golden compass", "the storm lantern"]

PROBLEMS = [
    {
        "lead": "{hero} was patrolling {place} when {object_name} rolled from a supply cart and began clattering downhill.",
        "cause": "the loose object was racing toward the village bridge",
        "risk": "If it struck the bridge, the frightened villagers might rush into the storm.",
        "action": "{hero} followed the tracks while {helper} used a bright signal to guide the runaway object toward a flat meadow.",
        "talk": "\"Do not chase me,\" called {hero}. \"Tell me what you need!\" {grizzly} growled, \"A thorn is caught in my paw.\"",
        "fix": "{hero} stopped, used a soft cloth to remove the thorn, and then placed {object_name} safely beside the meadow post.",
        "result": "the grizzly could walk comfortably again and the runaway object stopped before reaching the bridge",
        "image": "{grizzly} waved one broad paw as {object_name} shone safely beside the meadow post",
    },
    {
        "lead": "At {place}, {hero} saw {grizzly} tugging at a rope that held {object_name} above a narrow ravine.",
        "cause": "the rope had tangled around the grizzly's branch shelter",
        "risk": "A hard pull could send the object tumbling into the ravine.",
        "action": "{hero} asked {helper} to keep everyone back, then scoured the trail for a safe knot-cutting tool.",
        "talk": "\"Why are you pulling?\" asked {hero}. {grizzly} pointed at the rope and rumbled, \"My cub is on the other side.\"",
        "fix": "{hero} used a rescue hook to loosen the rope, made a bridge from sturdy logs, and guided the cub around the tangle.",
        "result": "the cub crossed safely and the rope no longer threatened the ravine",
        "image": "the grizzly and cub rested beneath the branch shelter while {object_name} swung gently in the clear air",
    },
    {
        "lead": "{hero} reached {place} after hearing a deep rumble beneath the trail. {object_name} was buried under fresh snow.",
        "cause": "a small avalanche had covered the useful object and startled {grizzly}",
        "risk": "More snow could slide if anyone dug in the wrong place.",
        "action": "{hero} scoured the slope for quiet footholds while {helper} listened for safe digging spots.",
        "talk": "\"I will not rush,\" thought {hero}. Then {hero} said, \"Can you hear the beacon?\" {grizzly} answered with a low rumble from the safest side.",
        "fix": "{hero} followed the grizzly's sound, cleared the snow in small careful scoops, and ended the search when the object was found.",
        "result": "the avalanche danger was over and the buried object could guide rescuers again",
        "image": "a blue signal blinked across the snow as {grizzly} watched calmly from the firm ground",
    },
    {
        "lead": "A gust at {place} lifted {object_name} into a curtain of pine branches, and {grizzly} lumbered after it.",
        "cause": "the wind had carried the object toward a nest hidden high in the trees",
        "risk": "Climbing too quickly could shake the nest and scare the young birds.",
        "action": "{hero} scoured the forest floor and found a long fallen branch, while {helper} whispered directions.",
        "talk": "\"Easy does it,\" said {hero}. {grizzly} looked up and rumbled, \"The little birds are sleeping.\"",
        "fix": "{hero} used the branch to lower the object without touching the nest, then helped {grizzly} guide it into a sheltered hollow.",
        "result": "the birds stayed safe and the wind could no longer carry the object away",
        "image": "the young birds chirped above them while {object_name} rested in the sheltered hollow",
    },
]

MONOLOGUES = [
    "Inside, {hero} thought, \"A true superhero does not just stop trouble; a true superhero notices who might be hurt.\"",
    "{hero}'s thoughts raced: \"I can be brave and careful at the same time. First listen, then act.\"",
    "For one quiet moment, {hero} told themself, \"The strongest power is a calm choice made for someone else.\"",
    "{hero} wondered, \"Is {grizzly} causing trouble, or is {grizzly} asking for help? I must learn the answer before I leap.\"",
]

QUESTS = [
    "The quest was not a race. It was a promise to scour every safe path, protect the mountain, and terminate the danger without making a new one.",
    "{helper} cheered, \"Quest team, move together!\" {hero} answered, \"Together, we can finish this safely.\"",
    "Step by step, the heroes followed clues, checked the ground, and turned a frightening chase into a rescue.",
    "When the final clue appeared, {hero} raised a fist and said, \"We know what to do now.\" Even {grizzly} gave an approving huff.",
]

ENDINGS = [
    "That evening, the village thanked {hero} with warm berry pies. {grizzly} received a basket of apples, and the mountain trail glowed peacefully under the stars.",
    "The next morning, {object_name} hung safely at the village hall. {hero}, {helper}, and {grizzly} stood beneath it as the first bell rang.",
    "At sunset, {grizzly} led {hero} to a sunny rock above {place}. They watched the village lights sparkle, proud that courage had made room for kindness.",
    "The villagers painted a small golden paw beside {hero}'s superhero symbol. It meant that the best heroes protect every neighbor, even a grizzly.",
]

ASP_RULES = r"""
#show valid/3.
#show valid_story/4.

hero(H) :- hero_name(H).
grizzly(G) :- grizzly_name(G).
helper(A) :- helper_name(A).
place(P) :- place_name(P).
object(O) :- object_name(O).

valid(H, G, P) :- hero_name(H), grizzly_name(G), place_name(P).
valid_story(H, G, P, O) :- valid(H, G, P), object_name(O).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for value in HEROES:
        lines.append(asp.fact("hero_name", value))
    for value in GRIZZLIES:
        lines.append(asp.fact("grizzly_name", value))
    for value in HELPERS:
        lines.append(asp.fact("helper_name", value))
    for value in PLACES:
        lines.append(asp.fact("place_name", value))
    for value in OBJECTS:
        lines.append(asp.fact("object_name", value))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="A superhero quest with a grizzly guardian.")
    parser.add_argument("--hero", choices=HEROES)
    parser.add_argument("--grizzly", choices=GRIZZLIES)
    parser.add_argument("--helper", choices=HELPERS)
    parser.add_argument("--place", choices=PLACES)
    parser.add_argument("--object-name", dest="object_name", choices=OBJECTS)
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


def asp_valid_combos() -> set[tuple[str, str, str]]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return {(h, g, p) for h, g, p in asp.atoms(model, "valid")}


def asp_verify() -> int:
    expected = {(h, g, p) for h in HEROES for g in GRIZZLIES for p in PLACES}
    actual = asp_valid_combos()
    if expected != actual:
        print("MISMATCH between Python and ASP valid combinations.")
        print("Only in Python:", sorted(expected - actual))
        print("Only in ASP:", sorted(actual - expected))
        return 1
    for params in build_curated():
        sample = generate(params)
        if not sample.story or "grizzly" not in sample.story.lower():
            print("Generated-story verification failed.")
            return 1
    print(f"OK: ASP matches Python ({len(expected)} combinations), and generated stories pass.")
    return 0


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return StoryParams(
        hero=args.hero or rng.choice(HEROES),
        grizzly=args.grizzly or rng.choice(GRIZZLIES),
        helper=args.helper or rng.choice(HELPERS),
        place=args.place or rng.choice(PLACES),
        object_name=args.object_name or rng.choice(OBJECTS),
        problem=rng.randrange(len(PROBLEMS)),
        monologue=rng.randrange(len(MONOLOGUES)),
        quest=rng.randrange(len(QUESTS)),
        ending=rng.randrange(len(ENDINGS)),
    )


def generate(params: StoryParams) -> StorySample:
    values = {
        "hero": params.hero,
        "grizzly": params.grizzly,
        "helper": params.helper,
        "place": params.place,
        "object_name": params.object_name,
    }
    event = PROBLEMS[params.problem % len(PROBLEMS)]
    world = World()
    hero = world.add(Entity(params.hero, "character", params.hero, memes={"courage": 0.0}))
    bear = world.add(Entity(params.grizzly, "animal", params.grizzly, memes={"trust": 0.0}))
    helper = world.add(Entity(params.helper, "character", params.helper, memes={"helpfulness": 0.0}))
    object_entity = world.add(Entity("quest_object", "object", params.object_name, meters={"danger": 0.0}))
    mountain = world.add(Entity("mountain", "place", params.place, meters={"stability": 1.0}))

    world.say(f"{params.hero} wore a blue cape and watched over {params.place}, where {params.grizzly} the grizzly lived among the pines.")
    world.say(event["lead"].format(**values))
    world.say(MONOLOGUES[params.monologue % len(MONOLOGUES)].format(**values))

    world.para()
    object_entity.meters["danger"] = 1.0
    bear.memes["worry"] = 1.0
    world.say(f"The trouble grew because {event['cause']}.")
    world.say(event["risk"].format(**values))
    world.say(f"{params.helper} hurried to {params.hero}'s side. \"We can help without hurting anyone,\" said {params.helper}.")
    world.say(event["talk"].format(**values))
    world.say(event["action"].format(**values))
    world.say(QUESTS[params.quest % len(QUESTS)].format(**values))

    world.para()
    world.say(event["fix"].format(**values))
    object_entity.meters["danger"] = 0.0
    bear.memes["worry"] = 0.0
    bear.memes["trust"] = 1.0
    hero.memes["courage"] = 1.0
    helper.memes["helpfulness"] = 1.0
    world.say(f"The danger was terminated because {event['result']}.")
    world.say(ENDINGS[params.ending % len(ENDINGS)].format(**values))
    world.facts.update(
        hero=params.hero,
        grizzly=params.grizzly,
        helper=params.helper,
        place=params.place,
        object_name=params.object_name,
        cause=event["cause"],
        action=event["action"].format(**values),
        result=event["result"],
        danger_terminated=True,
        quest_complete=True,
        happy_ending=True,
    )

    prompts = [
        "Write a child-friendly superhero quest in which a hero scours a mountain trail, helps a grizzly, and terminates a danger with kindness.",
        f"Tell a superhero story about {params.hero}, {params.grizzly} the grizzly, and a quest at {params.place}.",
        f"Write a happy-ending adventure where {params.hero} listens before acting and safely protects {params.object_name}.",
    ]
    story_qa = [
        QAItem("Who was the superhero in the story?", f"{params.hero} was the superhero who protected {params.place}."),
        QAItem("Why did the situation become dangerous?", f"It became dangerous because {event['cause']}."),
        QAItem(f"What did {params.hero} do?", f"{params.hero} {event['action'].format(**values).lower()}"),
        QAItem("How did the quest end?", f"The danger was terminated because {event['result']}, and everyone reached a happy ending."),
    ]
    world_qa = [
        QAItem("What is a quest?", "A quest is a journey with a goal, clues, challenges, and a reason to keep going."),
        QAItem("What is a grizzly?", "A grizzly is a large brown bear that lives in parts of North America."),
        QAItem("What does terminate mean?", "Terminate means to bring something to an end."),
        QAItem("Why should a hero listen before acting?", "Listening helps a hero understand the real problem and choose a safer, kinder solution."),
        QAItem("What makes an ending happy?", "A happy ending shows that the danger is over and the characters are safe, wiser, or together."),
    ]
    return StorySample(params=params, story=world.render(), prompts=prompts, story_qa=story_qa, world_qa=world_qa, world=world)


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    lines.extend(f"{i}. {prompt}" for i, prompt in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        lines.append(
            f"  {entity.id}: kind={entity.kind}, meters={entity.meters}, memes={entity.memes}"
        )
    lines.append(f"  facts={world.facts}")
    return "\n".join(lines)


def build_curated() -> list[StoryParams]:
    return [
        StoryParams("Luna", "Bruno", "Ari", "Whispering Ridge", "the village bell", 0, 0, 0, 0),
        StoryParams("Milo", "Honey", "Jules", "Pinecone Pass", "the rescue beacon", 1, 1, 1, 1),
        StoryParams("Nova", "Moss", "Tess", "Silverfoot Mountain", "the golden compass", 2, 2, 2, 2),
        StoryParams("Pax", "Tundra", "Kai", "Cloudberry Trail", "the storm lantern", 3, 3, 3, 3),
    ]


CURATED = build_curated()


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
        print(asp_program("#show valid_story/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = sorted(asp_valid_combos())
        print(f"{len(combos)} valid hero, grizzly, and place combinations:")
        for hero, grizzly, place in combos[:20]:
            print(f"  {hero} with {grizzly} at {place}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        samples = []
        seen: set[str] = set()
        for i in range(max(1, args.n)):
            seed = base_seed + i
            params = resolve_params(args, random.Random(seed))
            params.seed = seed
            params.problem = seed % len(PROBLEMS)
            params.monologue = (seed // 3) % len(MONOLOGUES)
            params.quest = (seed // 5) % len(QUESTS)
            params.ending = (seed // 7) % len(ENDINGS)
            sample = generate(params)
            if sample.story not in seen:
                samples.append(sample)
                seen.add(sample.story)

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for index, sample in enumerate(samples):
        header = ""
        if args.all:
            header = f"### {sample.params.hero}: quest at {sample.params.place}"
        elif len(samples) > 1:
            header = f"### variant {index + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
