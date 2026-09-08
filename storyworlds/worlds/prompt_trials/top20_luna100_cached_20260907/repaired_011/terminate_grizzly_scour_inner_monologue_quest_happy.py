#!/usr/bin/env python3
"""
A small superhero storyworld about a brave child, a grizzly, and a quest to
scour a mountain rescue bell before a storm arrives.
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
    helper: str
    grizzly: str
    mountain: str
    tool: str
    quest: int = 0
    danger: int = 0
    monologue: int = 0
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


HEROES = ["Luna", "Mara", "Pip", "Sol", "Niko", "Tess"]
HELPERS = ["Captain Vale", "Rook", "Beacon", "Aunt Jo", "Moss"]
GRIZZLIES = ["Bruno", "Maple", "Thunder", "Cedar", "Boulder"]
MOUNTAINS = ["Silver Peak", "Moonrock Ridge", "Bluebell Mountain", "Cloudcap Hill"]
TOOLS = ["a bright rescue rope", "a brass bell brush", "a long-handled broom", "a red signal flag"]

QUESTS = [
    {
        "start": "A storm was climbing toward {mountain}, and the old rescue bell at its summit had gone silent.",
        "clue": "A muddy pawprint trail led from the bell path to a cave below the summit.",
        "goal": "If the bell stayed clogged, lost hikers would not hear the warning before nightfall.",
        "cause": "mud and pine needles had packed the bell's clapper tight",
        "action": "{hero} would scour the bell with {tool} while {helper} kept the safe path open.",
        "result": "the clapper swung freely and the rescue bell rang across the valley",
    },
    {
        "start": "The town's emergency map marked one last safe beacon on {mountain}, but its signal had faded.",
        "clue": "A deep growl echoed near the beacon, followed by the scrape of heavy paws.",
        "goal": "The signal had to shine before the storm crossed the trail.",
        "cause": "dust and wet leaves covered the beacon's shining lens",
        "action": "{hero} would scour the lens with {tool} while {helper} watched the clouds.",
        "result": "the clean beacon flashed three brave times through the gray air",
    },
    {
        "start": "At dawn, {hero} discovered that the mountain guardian's warning horn could no longer call the village.",
        "clue": "Near the horn stood {grizzly}, a huge grizzly bear with a thorn caught in its paw.",
        "goal": "The horn had to work, and the frightened bear needed help, before anyone could safely cross the ridge.",
        "cause": "fallen branches and icy grit blocked the horn's mouth",
        "action": "{hero} would scour the horn with {tool}, then offer {grizzly} a calm way back to the forest.",
        "result": "the horn boomed safely, and {grizzly} padded home without fear",
    },
    {
        "start": "The superhero badge in {hero}'s pocket began to glow when the warning beacon on {mountain} stopped blinking.",
        "clue": "The glow pointed toward a grizzly-shaped shadow beside the beacon tower.",
        "goal": "The beacon needed one final repair before the mountain path disappeared in snow.",
        "cause": "snowy grit had jammed the beacon's turning mirror",
        "action": "{hero} would scour the mirror with {tool} while {helper} counted each careful turn.",
        "result": "the mirror turned again and painted a golden path across the snow",
    },
]

DANGERS = [
    {
        "event": "A rumble shook the ridge. Loose stones bounced toward the narrow trail.",
        "response": "{hero} raised {tool} like a shield and guided everyone behind a sturdy rock.",
        "conversation": "\"I hear the mountain moving,\" said {helper}. \"Then we move carefully,\" replied {hero}.",
    },
    {
        "event": "The grizzly stepped from the trees. It looked enormous, but one paw trembled beside the blocked warning device.",
        "response": "{hero} stopped, lowered the tool, and placed a bright trail marker on the ground.",
        "conversation": "\"Should we run?\" whispered {helper}. \"No,\" said {hero}. \"We can give {grizzly} space and solve the real problem.\"",
    },
    {
        "event": "A cold gust swept the ridge and snatched the repair map into a patch of thorny bushes.",
        "response": "{hero} tied the rescue rope around a safe post and pulled the map back without stepping into the thorns.",
        "conversation": "\"The map is stuck!\" cried {helper}. \"A calm knot beats a wild dash,\" said {hero}.",
    },
    {
        "event": "The warning device gave one tiny clank, then a swirl of snow hid the trail home.",
        "response": "{hero} planted the red signal flag where everyone could see it and followed the familiar bell rope.",
        "conversation": "\"We may lose the path,\" said {helper}. \"Not if we leave a bright one behind us,\" answered {hero}.",
    },
]

MONOLOGUES = [
    "\"I do feel small beside a grizzly,\" {hero} thought, \"but being a hero means noticing what needs help and choosing the careful next step.\"",
    "\"My cape cannot push away every storm,\" {hero} thought. \"My listening ears, gentle hands, and brave plan can still make a difference.\"",
    "\"The mountain is loud, and my knees are wobbly,\" {hero} thought. \"I can breathe, think, and protect everyone one safe action at a time.\"",
    "\"A superhero does not have to roar louder than danger,\" {hero} thought. \"A superhero can be quiet enough to understand it.\"",
]

ENDINGS = [
    "When the clouds parted, the rescued hikers followed the ringing signal to town. {hero} received a golden cape pin, while {grizzly} watched from the forest edge.",
    "The village children painted a sign that said, \"Thank you, {hero}!\" At sunset, {grizzly} left a pawprint beside it, and everyone knew the mountain had a new friend.",
    "That evening, warm soup steamed in the rescue station. {helper} hung {tool} beside the door, and {hero} smiled whenever the clear bell sounded above the roofs.",
    "The storm passed without losing a single traveler. Under a bright moon, {hero} heard {grizzly} give one soft, happy huff from the safe forest.",
]

ASP_RULES = r"""
#show valid/3.
#show valid_story/4.

hero(H) :- hero_name(H).
helper(P) :- helper_name(P).
grizzly(G) :- grizzly_name(G).
mountain(M) :- mountain_name(M).
tool(T) :- tool_name(T).
valid(H, G, M) :- hero_name(H), grizzly_name(G), mountain_name(M), grizzly_safe(G).
valid_story(H, G, M, T) :- valid(H, G, M), tool_name(T), tool_safe(T).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for value in HEROES:
        lines.append(asp.fact("hero_name", value))
    for value in HELPERS:
        lines.append(asp.fact("helper_name", value))
    for value in GRIZZLIES:
        lines.append(asp.fact("grizzly_name", value))
    for value in MOUNTAINS:
        lines.append(asp.fact("mountain_name", value))
    for value in TOOLS:
        lines.append(asp.fact("tool_name", value))
    for value in GRIZZLIES:
        lines.append(asp.fact("grizzly_safe", value))
    for value in TOOLS:
        lines.append(asp.fact("tool_safe", value))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_combos() -> list[tuple[str, str, str]]:
    return [(h, g, m) for h in HEROES for g in GRIZZLIES for m in MOUNTAINS]


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(asp.atoms(model, "valid"))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl)[:5])
    if cl - py:
        print("  only in clingo:", sorted(cl - py)[:5])
    return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="A superhero quest with a grizzly and a happy ending.")
    parser.add_argument("--hero", choices=HEROES)
    parser.add_argument("--helper", choices=HELPERS)
    parser.add_argument("--grizzly", choices=GRIZZLIES)
    parser.add_argument("--mountain", choices=MOUNTAINS)
    parser.add_argument("--tool", choices=TOOLS)
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
    return StoryParams(
        hero=args.hero or rng.choice(HEROES),
        helper=args.helper or rng.choice(HELPERS),
        grizzly=args.grizzly or rng.choice(GRIZZLIES),
        mountain=args.mountain or rng.choice(MOUNTAINS),
        tool=args.tool or rng.choice(TOOLS),
        quest=rng.randrange(len(QUESTS)),
        danger=rng.randrange(len(DANGERS)),
        monologue=rng.randrange(len(MONOLOGUES)),
        ending=rng.randrange(len(ENDINGS)),
    )


def apply_seeded_structure(params: StoryParams, seed: int) -> None:
    params.quest = seed % len(QUESTS)
    params.danger = (seed // 3) % len(DANGERS)
    params.monologue = (seed // 5) % len(MONOLOGUES)
    params.ending = (seed // 7) % len(ENDINGS)


def generate(params: StoryParams) -> StorySample:
    values = {
        "hero": params.hero,
        "helper": params.helper,
        "grizzly": params.grizzly,
        "mountain": params.mountain,
        "tool": params.tool,
    }
    quest = QUESTS[params.quest % len(QUESTS)]
    danger = DANGERS[params.danger % len(DANGERS)]

    world = World()
    hero = world.add(Entity(params.hero, "character", params.hero, memes={"courage": 0.2}))
    helper = world.add(Entity(params.helper, "character", params.helper, memes={"trust": 0.5}))
    bear = world.add(Entity(params.grizzly, "animal", params.grizzly, meters={"distance": 8.0}, memes={"fear": 0.7}))
    mountain = world.add(Entity(params.mountain, "place", params.mountain, meters={"storm": 0.2}))
    signal = world.add(Entity("signal", "device", "rescue signal", meters={"clarity": 0.1}, memes={"hope": 0.4}))
    tool = world.add(Entity("tool", "tool", params.tool, meters={"cleaning_power": 0.8}))

    world.say(quest["start"].format(**values))
    world.say(f"{params.hero} wore a blue cape over a warm coat and climbed with {params.helper}.")
    world.say(quest["clue"].format(**values))
    world.say(f"{params.grizzly} was not chasing anyone. The grizzly was guarding the broken signal and needed room to feel safe.")
    world.say(MONOLOGUES[params.monologue % len(MONOLOGUES)].format(**values))

    world.para()
    mountain.meters["storm"] = 0.8
    signal.meters["clarity"] = 0.1
    hero.memes["courage"] = 0.7
    world.say(quest["goal"].format(**values))
    world.say(danger["event"].format(**values))
    world.say(danger["conversation"].format(**values))
    world.say(danger["response"].format(**values))
    world.say(quest["action"].format(**values))

    world.para()
    bear.meters["distance"] = 12.0
    bear.memes["fear"] = 0.2
    signal.meters["clarity"] = 1.0
    mountain.meters["storm"] = 0.4
    hero.memes["courage"] = 1.0
    helper.memes["trust"] = 1.0
    world.say(f"{params.hero} worked slowly, stopping whenever {params.grizzly} shifted its paws. {params.helper} kept watch and spoke in a calm voice.")
    world.say(quest["result"].format(**values))
    world.say(f'"You did not defeat the grizzly," said {params.helper}. "You understood it."')
    world.say(f'"That is a superhero victory," said {params.hero}.')
    world.say(ENDINGS[params.ending % len(ENDINGS)].format(**values))

    world.facts.update(
        hero=params.hero,
        helper=params.helper,
        grizzly=params.grizzly,
        mountain=params.mountain,
        tool=params.tool,
        quest=params.quest % len(QUESTS),
        danger=danger["event"],
        cause=quest["cause"],
        action=quest["action"].format(**values),
        result=quest["result"].format(**values),
        resolved=True,
        happy_ending=True,
    )

    prompts = [
        "Write a child-friendly superhero story about a brave quest involving a grizzly and a rescue signal.",
        f"Tell a superhero adventure in which {params.hero} must scour a mountain signal and safely help {params.grizzly}.",
        f"Write a story with inner monologue, a careful quest, a spoken exchange, and a happy ending for {params.hero}.",
    ]

    story_qa = [
        QAItem(
            question="What quest did the hero undertake?",
            answer=f"{params.hero} climbed {params.mountain} to scour the rescue signal and make it work before the storm arrived.",
        ),
        QAItem(
            question="Why was the grizzly near the mountain signal?",
            answer=f"{params.grizzly} was guarding the broken signal and needed help and space rather than being chased away.",
        ),
        QAItem(
            question="How did the hero handle the danger?",
            answer=f"{params.hero} stayed calm, used {params.tool} carefully, listened to {params.helper}, and kept a safe distance from {params.grizzly}.",
        ),
        QAItem(
            question="How did the quest end?",
            answer=f"The signal worked again, the warning reached the valley, and {params.grizzly} returned safely to the forest.",
        ),
    ]

    world_qa = [
        QAItem(
            question="What is a grizzly?",
            answer="A grizzly is a large brown bear. It is a wild animal that should be given plenty of space and treated carefully.",
        ),
        QAItem(
            question="What does scour mean?",
            answer="To scour means to clean or search something thoroughly, often by rubbing it or looking over every part.",
        ),
        QAItem(
            question="What does terminate mean?",
            answer="To terminate means to bring something to an end, such as ending a storm warning or finishing a quest.",
        ),
        QAItem(
            question="What makes a superhero?",
            answer="A superhero uses courage, kindness, and good judgment to protect others instead of simply showing off strength.",
        ),
        QAItem(
            question="Why is a happy ending useful in a quest story?",
            answer="A happy ending shows that careful choices solved the problem and lets readers see how the characters and their world are safer afterward.",
        ),
    ]

    return StorySample(
        params=params,
        story=world.render(),
        prompts=prompts,
        story_qa=story_qa,
        world_qa=world_qa,
        world=world,
    )


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, prompt in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {prompt}")
    lines.append("")
    lines.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        bits = []
        if entity.meters:
            bits.append(f"meters={entity.meters}")
        if entity.memes:
            bits.append(f"memes={entity.memes}")
        lines.append(f"  {entity.id:12} ({entity.kind:8}) {' '.join(bits)}")
    return "\n".join(lines)


def build_curated() -> list[StoryParams]:
    return [
        StoryParams("Luna", "Captain Vale", "Bruno", "Silver Peak", "a bright rescue rope", 0, 0, 0, 0),
        StoryParams("Mara", "Rook", "Maple", "Moonrock Ridge", "a brass bell brush", 1, 1, 1, 1),
        StoryParams("Pip", "Beacon", "Thunder", "Bluebell Mountain", "a long-handled broom", 2, 2, 2, 2),
        StoryParams("Sol", "Aunt Jo", "Cedar", "Cloudcap Hill", "a red signal flag", 3, 3, 3, 3),
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
        triples = asp_valid_combos()
        print(f"{len(triples)} valid hero, grizzly, and mountain combinations:\n")
        for hero, grizzly, mountain in triples[:20]:
            print(f"  {hero} / {grizzly} / {mountain}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        seen: set[str] = set()
        index = 0
        while len(samples) < args.n and index < max(50, args.n * 50):
            seed = base_seed + index
            index += 1
            params = resolve_params(args, random.Random(seed))
            params.seed = seed
            apply_seeded_structure(params, seed)
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
        header = ""
        if args.all:
            header = f"### {sample.params.hero}: the {sample.params.grizzly} rescue quest"
        elif len(samples) > 1:
            header = f"### variant {index + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
