#!/usr/bin/env python3
"""
A small storyworld about a toy library, a kid superhero, funny mishaps,
and a brave turn toward sharing and teamwork.

Seed premise:
- Christian visits a toy library.
- He wants to play heroically with a favorite toy, but the library has
  a rule about keeping toys organized and quiet.
- Sound effects and humor appear as part of the action.
- The story ends with a clever, kind superhero-style solution.

This script follows the Storyweavers world contract and includes a Python
reasonableness gate plus an inline ASP twin.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Toy:
    name: str
    kind: str
    sound: str
    humor: str
    hero_pose: str
    small: bool = True


@dataclass
class Setting:
    place: str = "the toy library"
    features: set[str] = field(default_factory=lambda: {"sound_effects", "humor"})
    quiet: bool = True


@dataclass
class StoryParams:
    toy: str
    sidekick: str
    villain: str
    seed: Optional[int] = None


@dataclass
class Entity:
    id: str
    kind: str = "character"
    type: str = "person"
    label: str = ""
    phrase: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.facts: dict = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[str] = set()
        self.trace_bits: list[str] = []

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World(self.setting)
        clone.entities = {k: Entity(**{
            "id": v.id, "kind": v.kind, "type": v.type, "label": v.label, "phrase": v.phrase,
            "meters": dict(v.meters), "memes": dict(v.memes)
        }) for k, v in self.entities.items()}
        clone.fired = set(self.fired)
        return clone


TOYS = {
    "rocket": Toy("rocket", "space toy", "whoosh", "the rocket's nose tickled like a banana", "arms up"),
    "robot": Toy("robot", "toy robot", "beep-boop", "the robot bowed so hard it nearly toppled", "one fist up"),
    "cape": Toy("cape", "hero cape", "fwip", "the cape flapped like a sneaky curtain", "cape spread wide"),
    "drum": Toy("drum", "bam-bam", "the drum said hello with two tiny booms", "puffing cheeks"),
    "bubble_wand": Toy("bubble wand", "bubble toy", "pop-pop", "the bubbles looked like floating blueberry moons", "tip held high"),
}

SIDEKICKS = ["Milo", "June", "Nina", "Theo", "Ruby", "Eli"]
VILLAINS = ["Captain Clatter", "Professor Muddle", "The Sneaky Sock", "Count Grumble"]


def reasonableness_gate(toy: Toy, sidekick: str, villain: str) -> None:
    if toy.kind not in {"space toy", "toy robot", "hero cape", "bubble toy", "drum"}:
        raise StoryError("This toy does not fit the superhero toy-library story.")
    if sidekick == villain:
        raise StoryError("The sidekick and villain must be different characters.")


def predict_disorder(world: World, toy: Toy) -> bool:
    sim = world.copy()
    hero = sim.get("Christian")
    hero.memes["excitement"] = hero.memes.get("excitement", 0.0) + 1.0
    hero.meters["noise"] = hero.meters.get("noise", 0.0) + 1.0
    return toy.kind in {"drum", "bubble toy"} or hero.meters["noise"] > 0.5


def intro(world: World, hero: Entity) -> None:
    world.say(
        f"Christian was a little superhero fan who loved the toy library, where every shelf "
        f"held a pretend adventure waiting to begin."
    )


def setup_story(world: World, hero: Entity, sidekick: Entity, villain: Entity, toy: Toy) -> None:
    world.say(
        f'Christian spotted the {toy.name}, and it looked ready for a grand rescue mission. '
        f'His friend {sidekick.id} grinned, and somewhere between the shelves, '
        f'{villain.id} seemed to be the kind of trouble that liked noisy surprises.'
    )
    world.say(
        f'"{toy.sound}!" Christian whispered, because even whispering can sound heroic in a toy library.'
    )
    hero.memes["joy"] = hero.memes.get("joy", 0.0) + 1.0
    hero.memes["curiosity"] = hero.memes.get("curiosity", 0.0) + 1.0


def conflict(world: World, hero: Entity, sidekick: Entity, villain: Entity, toy: Toy) -> None:
    noisy = predict_disorder(world, toy)
    if noisy:
        hero.memes["trouble"] = hero.memes.get("trouble", 0.0) + 1.0
        world.say(
            f"Christian lifted the {toy.name} for a big dramatic pose. "
            f'“{toy.sound}!” went the toy, and {sidekick.id} giggled so hard they snorted. '
            f"Even the nearest book looked surprised."
        )
        world.say(
            f"Then {villain.id} popped out with a silly cackle: “I shall scatter the toys and make this place a jumble!”"
        )
        world.say(
            f"Christian gasped. A superhero mission was needed right away."
        )
    else:
        world.say(
            f"Christian held the {toy.name} carefully, and the room stayed calm enough for a clever plan."
        )


def turn(world: World, hero: Entity, sidekick: Entity, villain: Entity, toy: Toy) -> None:
    hero.memes["bravery"] = hero.memes.get("bravery", 0.0) + 1.0
    sidekick.memes["helpful"] = sidekick.memes.get("helpful", 0.0) + 1.0
    world.say(
        f"Christian pointed to the toy bins and whispered, “Teamwork time!” "
        f'{sidekick.id} nodded, and together they made a funny plan:'
    )
    world.say(
        f'Christian used the {toy.name} like a pretend megaphone and shouted, '
        f'"To the neat shelf!" {toy.sound}! {toy.hero_pose}! '
        f'The shout was big, but the joke was bigger, and even {villain.id} blinked.'
    )
    world.say(
        f'{sidekick.id} rolled a tiny cart in circles. “I am the fastest library helper in the universe,” they said, '
        f'which made Christian laugh so hard he had to hold his cape.'
    )


def resolution(world: World, hero: Entity, sidekick: Entity, villain: Entity, toy: Toy) -> None:
    hero.memes["kindness"] = hero.memes.get("kindness", 0.0) + 1.0
    hero.memes["trouble"] = 0.0
    world.say(
        f"Christian finally made the best superhero move of all: he invited {villain.id} to help put the toys back in order."
    )
    world.say(
        f'{villain.id} muttered, “I guess I do like a neat shelf,” and shoved a block into the bin with a tiny, embarrassed '
        f'"plop." Christian laughed, not at {villain.id}, but with them.'
    )
    world.say(
        f'By the end, the {toy.name} was back on its shelf, {sidekick.id} was smiling, and Christian stood tall, '
        f"listening to the quiet little sounds of a library that felt safe again."
    )


def build_world(params: StoryParams) -> World:
    setting = Setting()
    world = World(setting)
    hero = world.add(Entity(id="Christian", kind="character", type="boy", label="Christian"))
    sidekick = world.add(Entity(id=params.sidekick, kind="character", type="child", label=params.sidekick))
    villain = world.add(Entity(id=params.villain, kind="character", type="villain", label=params.villain))
    toy = TOYS[params.toy]

    world.facts.update(hero=hero, sidekick=sidekick, villain=villain, toy=toy, setting=setting)
    intro(world, hero)
    world.para()
    setup_story(world, hero, sidekick, villain, toy)
    world.para()
    conflict(world, hero, sidekick, villain, toy)
    world.para()
    turn(world, hero, sidekick, villain, toy)
    resolution(world, hero, sidekick, villain, toy)
    return world


SETTINGS = {"toy_library": Setting()}
DEFAULT_TOY = "rocket"


def asp_facts() -> str:
    import asp
    lines = []
    lines.append(asp.fact("setting", "toy_library"))
    lines.append(asp.fact("feature", "toy_library", "sound_effects"))
    lines.append(asp.fact("feature", "toy_library", "humor"))
    for tid, toy in TOYS.items():
        lines.append(asp.fact("toy", tid))
        lines.append(asp.fact("toy_kind", tid, toy.kind))
    lines.append(asp.fact("character", "christian"))
    return "\n".join(lines)


ASP_RULES = r"""
good_story(T) :- toy(T), toy_kind(T, K), K != "bad".
compatible(toy_library, T) :- setting(toy_library), good_story(T).
#show compatible/2.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show compatible/2."))
    return sorted(set(asp.atoms(model, "compatible")))


def asp_verify() -> int:
    py = {( "toy_library", t) for t in TOYS.keys()}
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches python gate ({len(py)} toys).")
        return 0
    print("MISMATCH between clingo and python gates.")
    print(" only python:", sorted(py - cl))
    print(" only clingo:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Toy library superhero storyworld.")
    ap.add_argument("--toy", choices=sorted(TOYS))
    ap.add_argument("--sidekick", choices=SIDEKICKS)
    ap.add_argument("--villain", choices=VILLAINS)
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    toy = args.toy or rng.choice(sorted(TOYS))
    sidekick = args.sidekick or rng.choice(SIDEKICKS)
    villain = args.villain or rng.choice(VILLAINS)
    reasonableness_gate(TOYS[toy], sidekick, villain)
    if sidekick == villain:
        raise StoryError("The sidekick and villain cannot be the same character.")
    return StoryParams(toy=toy, sidekick=sidekick, villain=villain)


def generation_prompts(world: World) -> list[str]:
    toy = world.facts["toy"]
    return [
        "Write a short superhero story for a child set in a toy library.",
        f"Tell a funny story about Christian, the {toy.name}, and a problem that needs teamwork.",
        f"Write a gentle adventure with sound effects like {toy.sound} and a neat ending in the toy library.",
    ]


def story_qa(world: World) -> list[QAItem]:
    toy: Toy = world.facts["toy"]
    sidekick: Entity = world.facts["sidekick"]
    villain: Entity = world.facts["villain"]
    return [
        QAItem(
            question="Who is the story about?",
            answer="It is about Christian, a little superhero fan who visits the toy library.",
        ),
        QAItem(
            question=f"What sound did the {toy.name} make in the story?",
            answer=f'The {toy.name} went "{toy.sound}!" and helped make the scene feel silly and exciting.',
        ),
        QAItem(
            question=f"How did Christian fix the problem with {villain.id}?",
            answer=(
                f"Christian used teamwork, made a funny plan with {sidekick.id}, and invited "
                f"{villain.id} to help put the toys back in order."
            ),
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a toy library?",
            answer="A toy library is a place where children can find, borrow, and share toys, much like a book library shares books.",
        ),
        QAItem(
            question="Why do sound effects make stories fun?",
            answer="Sound effects make stories fun because they help readers hear the action in their imaginations, like booms, pops, and whooshes.",
        ),
        QAItem(
            question="Why is humor good in a superhero story?",
            answer="Humor can make a superhero story feel light and friendly, so even big problems can be solved with kindness and a smile.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== Story questions ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== World knowledge questions ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: kind={e.kind} type={e.type} meters={e.meters} memes={e.memes}")
    lines.append(f"setting={world.setting.place}")
    return "\n".join(lines)


CURATED = [
    StoryParams(toy="rocket", sidekick="Milo", villain="Captain Clatter"),
    StoryParams(toy="robot", sidekick="June", villain="Professor Muddle"),
    StoryParams(toy="cape", sidekick="Ruby", villain="The Sneaky Sock"),
    StoryParams(toy="drum", sidekick="Theo", villain="Count Grumble"),
    StoryParams(toy="bubble_wand", sidekick="Nina", villain="Captain Clatter"),
]


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
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


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show compatible/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible toy choices:\n")
        for _, toy in combos:
            print(f"  toy_library  {toy}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 40, 40):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as e:
                print(e)
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
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
