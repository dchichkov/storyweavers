#!/usr/bin/env python3
"""
A tiny superhero storyworld about a hero's quest, an inner monologue, a grizzly threat, and a happy ending.

Seed premise:
A brave hero hears about a grizzly problem, scours the city for clues, and learns that the real victory comes from thinking carefully before acting. The story should include inner monologue, a quest, and a happy ending in a superhero style.
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
    sidekick: str
    city: str
    target: str
    clue: str
    tool: str
    quest_variant: int = 0
    turn_variant: int = 0
    ending_variant: int = 0
    seed: Optional[int] = None


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    label: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "character":
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


HEROES = ["Nova", "Blaze", "Comet", "Vector", "Aurora", "Pulse", "Spark", "Mara"]
SIDEKICKS = ["Zip", "Milo", "June", "Tess", "Echo", "Pip"]
CITIES = ["Maple City", "Bright Harbor", "Riverglass", "Sunbeam Square", "Skyline Bay"]
TARGETS = [
    "the grizzly statue in the museum",
    "the grizzly-shaped shadow near the park",
    "the grizzly alarm hidden in the tower",
    "the grizzly track marks by the river",
]
CLUES = [
    "a muddy paw print",
    "a torn ticket stub",
    "a silver button",
    "a streak of pine needles",
    "a chalk arrow",
]
TOOLS = [
    "a flashlight",
    "a grappling line",
    "a magnifier",
    "a whisper-radio",
    "a signal map",
]

QUESTS = [
    "{hero} decided to scour {city} for clues before the problem got bigger. {sidekick} said, 'We need a quest, not a guess.'",
    "When the report came in, {hero} put on the cape and told {sidekick}, 'Time to scour the city and find the truth.'",
    "{city} buzzed with worry, so {hero} and {sidekick} began a careful quest under the bright streetlights.",
    "{hero} heard the word grizzly and thought, 'This might look huge, but I can handle it if I search wisely.' {sidekick} nodded and followed.",
]

TURN_LINES = [
    "At the center of the search, the clue led to {target}. {hero} looked closer and realized the danger was not wild at all—it was a false alarm made by a broken robot bear.",
    "The trail ended beside {target}. Then {hero}'s inner monologue whispered, 'Terminate the panic, not the problem.' That thought changed everything.",
    "The last clue pointed to {target}. {sidekick} gasped, but {hero} noticed the marks were from paint, not claws.",
    "Under the moonlight, the search reached {target}. {hero} thought, 'If I rush, I could scare everyone. If I listen, I can help everyone.'",
]

DIALOGUE_BITS = [
    "{sidekick} asked, 'What if the grizzly is real?' {hero} answered, 'Then we stay calm, stay kind, and keep scouting.'",
    "{sidekick} whispered, 'Do we have to terminate the search?' {hero} said, 'No, just the fear. The quest is almost done.'",
    "'I found a clue,' said {sidekick}. 'Good,' replied {hero}, 'then we are one step closer to a happy ending.'",
    "'Will this be messy?' asked {sidekick}. 'Only if we let it be,' said {hero}. 'Let's use our heads.'",
]

HAPPY_ENDINGS = [
    "In the end, {hero} used {tool} to show the crowd the truth. The grizzly scare vanished, the city cheered, and {sidekick} grinned beside a safe, quiet {target}.",
    "After the final check, {hero} gently shut down the broken robot with a careful tap. The town called it a happy ending, because nobody got hurt and everyone learned to look twice.",
    "{hero} and {sidekick} returned home as heroes. {city} glowed behind them, calm at last, while the last clue sat in {hero}'s hand like a trophy.",
    "The crowd thanked {hero}, and {sidekick} said, 'That was a real quest.' {hero} smiled, because the best victory was the one that kept everyone safe.",
]

ASP_RULES = r"""
#show valid/3.
#show valid_story/4.

hero_name(N) :- hero(N).
sidekick_name(S) :- sidekick(S).
city_name(C) :- city(C).
target_name(T) :- target(T).
clue_name(C) :- clue(C).
tool_name(T) :- tool(T).

valid(H, C, T) :- hero(H), city(C), target(T).
valid_story(H, C, T, K) :- valid(H, C, T), clue(K).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for h in HEROES:
        lines.append(asp.fact("hero", h))
    for s in SIDEKICKS:
        lines.append(asp.fact("sidekick", s))
    for c in CITIES:
        lines.append(asp.fact("city", c))
    for t in TARGETS:
        lines.append(asp.fact("target", t))
    for c in CLUES:
        lines.append(asp.fact("clue", c))
    for t in TOOLS:
        lines.append(asp.fact("tool", t))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A superhero storyworld with a quest, inner monologue, and happy ending.")
    ap.add_argument("--hero", choices=HEROES)
    ap.add_argument("--sidekick", choices=SIDEKICKS)
    ap.add_argument("--city", choices=CITIES)
    ap.add_argument("--target", choices=TARGETS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def valid_combos() -> list[tuple[str, str, str]]:
    return [
        ("Nova", "Bright Harbor", "the grizzly statue in the museum"),
        ("Blaze", "Maple City", "the grizzly-shaped shadow near the park"),
        ("Comet", "Riverglass", "the grizzly alarm hidden in the tower"),
        ("Aurora", "Sunbeam Square", "the grizzly track marks by the river"),
    ]


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted({(hero, city, target) for _, hero, city, target in asp.atoms(model, "valid")})


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_combos()
    if args.hero and args.city and args.target:
        if (args.hero, args.city, args.target) not in combos:
            raise StoryError("No story: that hero, city, and target do not make a believable quest.")
    if args.hero:
        combos = [c for c in combos if c[0] == args.hero]
    if args.city:
        combos = [c for c in combos if c[1] == args.city]
    if args.target:
        combos = [c for c in combos if c[2] == args.target]
    if not combos:
        raise StoryError("No valid combo matches the given options.")
    hero, city, target = rng.choice(sorted(combos))
    return StoryParams(
        hero=hero,
        sidekick=args.sidekick or rng.choice(SIDEKICKS),
        city=city,
        target=target,
        clue=args.clue or rng.choice(CLUES),
        tool=args.tool or rng.choice(TOOLS),
        quest_variant=rng.randrange(len(QUESTS)),
        turn_variant=rng.randrange(len(TURN_LINES)),
        ending_variant=rng.randrange(len(HAPPY_ENDINGS)),
    )


def apply_seeded_structure(params: StoryParams, seed: int) -> None:
    params.quest_variant = seed % len(QUESTS)
    params.turn_variant = (seed // len(QUESTS)) % len(TURN_LINES)
    params.ending_variant = (seed // 5) % len(HAPPY_ENDINGS)


def generate(params: StoryParams) -> StorySample:
    values = {
        "hero": params.hero,
        "sidekick": params.sidekick,
        "city": params.city,
        "target": params.target,
        "clue": params.clue,
        "tool": params.tool,
    }

    w = World()
    hero = w.add(Entity(id=params.hero, kind="character", label=params.hero, meters={"distance": 0.0}, memes={"resolve": 1.0}))
    sidekick = w.add(Entity(id=params.sidekick, kind="character", label=params.sidekick, meters={"distance": 0.0}, memes={"worry": 0.4}))
    city = w.add(Entity(id=params.city, label=params.city, meters={"lights": 1.0}, memes={"anxiety": 0.2}))
    target = w.add(Entity(id="target", label=params.target, meters={"mystery": 1.0}, memes={"danger": 0.6}))
    clue = w.add(Entity(id="clue", label=params.clue, meters={"found": 0.0}, memes={"importance": 0.7}))
    tool = w.add(Entity(id="tool", label=params.tool, meters={"ready": 1.0}, memes={"helpfulness": 1.0}))

    w.say(QUESTS[params.quest_variant % len(QUESTS)].format(**values))
    w.say(f"The night wind moved over {city.label}, and {hero.label} held {tool.label} like a promise.")
    w.say(f"{hero.label} thought, 'I can scour every rooftop until I find the clue.'")
    w.say(DIALOGUE_BITS[params.turn_variant % len(DIALOGUE_BITS)].format(**values))

    w.para()
    hero.meters["distance"] = 3.0
    sidekick.meters["distance"] = 3.0
    clue.meters["found"] = 1.0
    target.meters["mystery"] = 0.5
    target.memes["danger"] = 0.1
    w.say(f"Together they scoured {city.label} until they found {params.clue} near {params.target}.")
    w.say(TURN_LINES[params.turn_variant % len(TURN_LINES)].format(**values))
    w.say(f"{hero.label} paused and listened to the inner monologue in their own head: 'Stay calm. Scan carefully. Terminate the panic, not the people.'")

    w.para()
    hero.memes["relief"] = 1.0
    sidekick.memes["joy"] = 1.0
    city.memes["anxiety"] = 0.0
    target.meters["mystery"] = 0.0
    target.memes["danger"] = 0.0
    w.say(f"{hero.label} used {tool.label} to reveal that the grizzly threat was only a broken machine and some stage paint.")
    w.say(f"{sidekick.label} said, 'So the grizzly was not a monster at all!' {hero.label} replied, 'Right. We solved the quest by thinking first.'")
    w.say(HAPPY_ENDINGS[params.ending_variant % len(HAPPY_ENDINGS)].format(**values))

    w.facts.update(
        hero=hero.id,
        sidekick=sidekick.id,
        city=city.id,
        target=target.label,
        clue=clue.label,
        tool=tool.label,
        quest_variant=params.quest_variant % len(QUESTS),
        turn_variant=params.turn_variant % len(TURN_LINES),
        ending_variant=params.ending_variant % len(HAPPY_ENDINGS),
        contains_inner_monologue=True,
        contains_quest=True,
        happy_ending=True,
    )

    prompts = [
        "Write a superhero story about a quest to investigate a grizzly problem, with inner monologue and a happy ending.",
        f"Tell a child-friendly superhero tale where {params.hero} and {params.sidekick} scour {params.city} for clues and discover the truth.",
        f"Write a story in which the words terminate, grizzly, and scour appear, and the hero wins with calm thinking.",
    ]

    story_qa = [
        QAItem(
            question="Who was the hero of the story?",
            answer=f"{params.hero} was the hero who led the quest with {params.sidekick}.",
        ),
        QAItem(
            question="What did the hero scour the city for?",
            answer=f"{params.hero} scoured {params.city} for {params.clue} and signs of the grizzly problem.",
        ),
        QAItem(
            question="What was the real danger?",
            answer="The real danger was not a real monster; it was a broken machine and a false alarm that made people worry.",
        ),
        QAItem(
            question="How did the story end?",
            answer="It ended happily, because the hero solved the problem, calmed the crowd, and kept everyone safe.",
        ),
    ]

    world_qa = [
        QAItem(
            question="What is a quest?",
            answer="A quest is a mission or journey to find something, solve a problem, or help someone.",
        ),
        QAItem(
            question="What is inner monologue?",
            answer="Inner monologue is the private thinking a character does in their own mind.",
        ),
        QAItem(
            question="What does terminate mean?",
            answer="Terminate means to stop something or bring it to an end.",
        ),
        QAItem(
            question="What does grizzly mean?",
            answer="Grizzly can mean bear-like or scary in a rough, wild way.",
        ),
        QAItem(
            question="What does scour mean?",
            answer="Scour means to search carefully and thoroughly.",
        ),
    ]

    return StorySample(params=params, story=w.render(), prompts=prompts, story_qa=story_qa, world_qa=world_qa, world=w)


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story ==",]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
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
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:10} ({e.kind:9}) {' '.join(bits)}")
    return "\n".join(lines)


def build_curated() -> list[StoryParams]:
    return [
        StoryParams(hero="Nova", sidekick="Zip", city="Bright Harbor", target="the grizzly statue in the museum", clue="a muddy paw print", tool="a flashlight", quest_variant=0, turn_variant=1, ending_variant=0),
        StoryParams(hero="Blaze", sidekick="June", city="Maple City", target="the grizzly-shaped shadow near the park", clue="a torn ticket stub", tool="a magnifier", quest_variant=1, turn_variant=0, ending_variant=1),
        StoryParams(hero="Comet", sidekick="Tess", city="Riverglass", target="the grizzly alarm hidden in the tower", clue="a silver button", tool="a signal map", quest_variant=2, turn_variant=2, ending_variant=2),
        StoryParams(hero="Aurora", sidekick="Pip", city="Sunbeam Square", target="the grizzly track marks by the river", clue="a chalk arrow", tool="a whisper-radio", quest_variant=3, turn_variant=3, ending_variant=3),
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
        print(f"{len(triples)} compatible (hero, city, target) combos:\n")
        for hero, city, target in triples:
            print(f"  {hero:10} in {city:16} -> {target}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as err:
                print(err)
                return
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
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero}: quest in {p.city}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
