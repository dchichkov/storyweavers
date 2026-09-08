#!/usr/bin/env python3
"""
A small fairy-tale world about Gray and abcdefghijklm, where a shared problem
is solved by sharing clues, tools, and courage.
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

for _parent in Path(__file__).resolve().parents:
    if (_parent / "storyworlds" / "results.py").is_file():
        sys.path.insert(0, str(_parent / "storyworlds"))
        break
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str
    type: str
    label: str
    region: str = ""
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for key in ("blocked", "clue", "shared", "repaired", "safe"):
            self.meters.setdefault(key, 0.0)
        for key in ("worry", "hope", "pride", "trust", "relief", "kindness"):
            self.memes.setdefault(key, 0.0)


@dataclass(frozen=True)
class Tale:
    problem: str
    warning: str
    clue: str
    selfish_choice: str
    consequence: str
    sharing_turn: str
    solution: str
    result: str
    lesson: str
    ending: str


@dataclass
class StoryParams:
    seed: Optional[int] = None
    hero: str = "gray"
    companion: str = "abcdef ghijklm"
    place: str = "the Moonlit Orchard"
    feature: str = "Problem Solving and Sharing"
    style: str = "Fairy Tale"


HEROES = ["gray", "silver", "Mira", "Pip", "Nell"]
COMPANIONS = ["abcdefghijklm", "the little fox", "the bell keeper", "the willow sprite"]
PLACES = ["the Moonlit Orchard", "the Whispering Castle", "the Lantern Village", "the Bluebell Wood"]

TALES = [
    Tale(
        problem="the moon bridge cracked just before the village children needed to cross it",
        warning="A bridge made of moonlight must be mended with more than one bright thought",
        clue="three loose stars were caught in the reeds below the broken arch",
        selfish_choice="hide the stars and try to repair the bridge alone",
        consequence="the first patch shimmered brightly, but it bent and left a dark gap in the middle",
        sharing_turn="Gray showed the loose stars to abcdefghijklm and asked what the reeds had taught them",
        solution="placed one star at each end while abcdefghijklm sang the bridge's old counting song",
        result="the moon bridge grew wide and strong enough for every child to cross",
        lesson="A hard problem becomes clearer when people share both what they know and what they have",
        ending="By dawn, the last star rested above the bridge, shining over two friends who had solved the trouble together",
    ),
    Tale(
        problem="the royal garden fountain stopped singing on the morning of the Queen's feast",
        warning="A silent fountain may be hiding a small blockage and a large secret",
        clue="a blue seed was wedged beneath the fountain's silver wheel",
        selfish_choice="keep the seed and twist the wheel without asking for help",
        consequence="the wheel groaned, and a thin stream splashed across the garden path",
        sharing_turn="Gray gave the blue seed to abcdefghijklm and listened while the companion studied its markings",
        solution="used the seed as a key while Gray turned the wheel slowly",
        result="the fountain sang again, and its water filled every waiting cup",
        lesson="Sharing a useful object can unlock an answer that one pair of hands cannot find",
        ending="The feast began beside a singing fountain, and every guest raised a cup to the helpers",
    ),
    Tale(
        problem="a warm golden wind carried the village's harvest baskets into the Thorny Meadow",
        warning="No basket returns safely when a rescuer rushes into thorns without a plan",
        clue="the baskets had left a trail of red ribbons along the safest path",
        selfish_choice="race after the nearest basket and keep the ribbons tucked in a pocket",
        consequence="the thorns caught Gray's cloak, and the baskets rolled farther toward the hill",
        sharing_turn="Gray shared the ribbons with abcdefghijklm and let the companion choose the path",
        solution="tied ribbons between the thorns while Gray gathered the baskets one by one",
        result="the harvest came home without a torn basket or a scratched hand",
        lesson="A shared plan can turn a tangled path into a trail that everyone can follow",
        ending="That evening, the village bread rose high, and a red ribbon fluttered from every doorway",
    ),
    Tale(
        problem="the castle clock lost its golden minute before the king's birthday",
        warning="Time will not return to a clock unless every missing piece is named",
        clue="a tiny golden gear was hiding inside a sleepy dragon's teacup",
        selfish_choice="take the gear quietly and pretend the clock had been fixed by magic",
        consequence="the clock ticked once, then stopped with its hands pointing in opposite directions",
        sharing_turn="Gray told abcdefghijklm the whole truth and shared the broken clock's picture",
        solution="matched the gear to the picture while abcdefghijklm woke the dragon with a gentle rhyme",
        result="the dragon returned the gear, and the clock chimed at the right moment",
        lesson="Honest sharing gives helpers the information they need to solve a puzzle",
        ending="At noon, the birthday bells rang, and even the dragon smiled from its teacup",
    ),
]

OPENINGS = [
    "Once upon a gentle evening,",
    "Long ago, beneath a patient moon,",
    "In a kingdom where small acts could wake great magic,",
    "At the edge of an old enchanted road,",
]

DIALOGUES = [
    '"I have a clue," said {hero}. "And I have a question," answered {companion}.',
    '"Should we try alone?" asked {hero}. "No," said {companion}. "Let us share what we see."',
    '"This is difficult," whispered {hero}. "Then we will make it smaller together," said {companion}.',
    '"What do you know?" asked {companion}. "{clue}," replied {hero}. "Now we can begin."',
]


class World:
    def __init__(self, params: StoryParams) -> None:
        self.params = params
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[str] = set()
        self.facts: dict[str, object] = {}

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def get(self, entity_id: str) -> Entity:
        return self.entities[entity_id]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(part) for part in self.paragraphs if part)


def make_world(params: StoryParams) -> World:
    world = World(params)
    hero = world.add(Entity("hero", "character", "child", params.hero, region=params.place))
    companion = world.add(Entity("companion", "character", "helper", params.companion, region=params.place))
    tool = world.add(Entity("shared_clue", "thing", "clue", "the shared clue", region=params.place))
    hero.memes["hope"] = 1.0
    hero.memes["pride"] = 1.0
    companion.memes["trust"] = 1.0
    tool.meters["clue"] = 1.0
    return world


def tell(params: StoryParams) -> World:
    world = make_world(params)
    hero = world.get("hero")
    companion = world.get("companion")
    tale = TALES[(params.seed or 0) % len(TALES)]
    dialogue = DIALOGUES[((params.seed or 0) // len(TALES)) % len(DIALOGUES)].format(
        hero=hero.label, companion=companion.label, clue=tale.clue
    )
    opening = OPENINGS[((params.seed or 0) // 7) % len(OPENINGS)]

    world.say(f"{opening} {hero.label} lived near {params.place} with a thoughtful companion named {companion.label}.")
    world.say(f"They cared about one another, but that day {tale.problem}.")
    world.para()
    world.say(f"An old fairy warning whispered, \"{tale.warning}.\"")
    world.say(f"Gray wanted the trouble gone at once and chose to {tale.selfish_choice}.")
    hero.memes["pride"] += 1.0
    hero.memes["worry"] += 1.0
    hero.meters["blocked"] = 1.0
    world.say(f"That choice made matters harder: {tale.consequence}.")
    world.say(f"Then {hero.label} noticed that {tale.clue}.")
    world.say(dialogue)
    world.say(f"{tale.sharing_turn}.")
    hero.memes["kindness"] += 1.0
    companion.memes["trust"] += 1.0
    world.get("shared_clue").meters["shared"] = 1.0
    world.para()
    world.say(f"Together, they {tale.solution}.")
    hero.meters["blocked"] = 0.0
    hero.meters["repaired"] = 1.0
    world.get("shared_clue").meters["repaired"] = 1.0
    hero.memes["relief"] += 1.0
    companion.memes["relief"] += 1.0
    world.say(f"Because they shared their clues and effort, {tale.result}.")
    world.say(f"{hero.label} learned that {tale.lesson}.")
    world.say(tale.ending)

    world.facts.update(
        hero=hero,
        companion=companion,
        tale=tale,
        params=params,
        resolved=True,
        sharing=True,
    )
    return world


def story_qa(world: World) -> list[QAItem]:
    hero = world.facts["hero"]
    companion = world.facts["companion"]
    tale = world.facts["tale"]
    params = world.facts["params"]
    return [
        QAItem(
            f"Who solved the problem in {params.place}?",
            f"{hero.label} and {companion.label} solved it together by sharing clues, ideas, and work.",
        ),
        QAItem(
            f"What problem appeared in {params.place}?",
            f"The problem was that {tale.problem}.",
        ),
        QAItem(
            f"What did {hero.label} first do wrong?",
            f"{hero.label} tried to {tale.selfish_choice}, which made the trouble worse because the plan was not shared.",
        ),
        QAItem(
            f"What clue helped {hero.label} and {companion.label}?",
            f"They discovered that {tale.clue}. That clue showed them where to begin.",
        ),
        QAItem(
            f"How did sharing change the solution?",
            f"{hero.label} and {companion.label} shared what they knew and then {tale.solution}. This teamwork led to the result that {tale.result}.",
        ),
        QAItem(
            "What lesson does the fairy tale teach?",
            f"It teaches that {tale.lesson}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem("What is problem solving?", "Problem solving means noticing a difficulty, finding useful clues, and trying a sensible way to improve the situation."),
        QAItem("Why is sharing helpful?", "Sharing is helpful because people can combine their knowledge, tools, and effort instead of struggling alone."),
        QAItem("What is a fairy tale?", "A fairy tale is a story with wonder, magical events, and a lesson about how characters choose to act."),
        QAItem("What is a clue?", "A clue is a small piece of information that helps someone understand a problem or find an answer."),
    ]


def generation_prompts(world: World) -> list[str]:
    params = world.facts["params"]
    tale = world.facts["tale"]
    return [
        f"Write a {params.style.lower()} about {params.hero} and {params.companion} solving a problem through sharing.",
        f"Tell a story in {params.place} where {params.hero} uses the clue that {tale.clue}.",
        f"Create a child-friendly tale showing why {params.feature.lower()} matter.",
    ]


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
        meters = {key: value for key, value in entity.meters.items() if value}
        memes = {key: value for key, value in entity.memes.items() if value}
        lines.append(f"  {entity.id}: meters={meters} memes={memes}")
    lines.append(f"  resolved={world.facts.get('resolved')} sharing={world.facts.get('sharing')}")
    return "\n".join(lines)


ASP_RULES = r"""
problem(hero) :- blocked(hero).
shares(hero, companion) :- problem(hero), clue(shared_clue), trusts(companion).
solved(hero) :- shares(hero, companion), repaired(shared_clue).
#show problem/1.
#show shares/2.
#show solved/1.
"""


def asp_facts() -> str:
    import asp
    return "\n".join([
        asp.fact("blocked", "hero"),
        asp.fact("clue", "shared_clue"),
        asp.fact("trusts", "companion"),
        asp.fact("repaired", "shared_clue"),
    ])


def asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program())
    found = {f"{symbol.name}/{len(symbol.arguments)}" for symbol in model}
    expected = {"problem/1", "shares/2", "solved/1"}
    if found == expected:
        for seed in range(5):
            sample = generate(StoryParams(seed=seed))
            if "together" not in sample.story or "sharing" not in sample.story.lower():
                print("MISMATCH: generated story lacks a shared solution")
                return 1
        print("OK: ASP twin and generated stories agree.")
        return 0
    print("MISMATCH:", sorted(found), "expected", sorted(expected))
    return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="A problem-solving and sharing fairy tale world.")
    parser.add_argument("--hero", choices=HEROES)
    parser.add_argument("--companion", choices=COMPANIONS)
    parser.add_argument("--place", choices=PLACES)
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return StoryParams(
        seed=args.seed,
        hero=args.hero or rng.choice(HEROES),
        companion=args.companion or rng.choice(COMPANIONS),
        place=args.place or rng.choice(PLACES),
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
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


CURATED = [
    StoryParams(seed=0, hero="gray", companion="abcdefghijklm", place="the Moonlit Orchard"),
    StoryParams(seed=1, hero="Mira", companion="the little fox", place="the Whispering Castle"),
    StoryParams(seed=2, hero="Pip", companion="the willow sprite", place="the Bluebell Wood"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        raise SystemExit(asp_verify())
    if args.asp:
        import asp
        print(" ".join(str(symbol) for symbol in asp.one_model(asp_program())))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        samples = []
        for index in range(args.n):
            seed = base_seed + index
            params = resolve_params(args, random.Random(seed))
            params.seed = seed
            samples.append(generate(params))

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
