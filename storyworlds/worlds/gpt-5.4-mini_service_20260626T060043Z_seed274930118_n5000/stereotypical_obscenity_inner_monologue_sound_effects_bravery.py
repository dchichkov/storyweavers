#!/usr/bin/env python3
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
class Character:
    name: str
    role: str
    brave: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class Prop:
    name: str
    kind: str
    meters: dict[str, float] = field(default_factory=dict)


@dataclass
class StoryParams:
    place: str
    hero_name: str
    sidekick_name: str
    problem: str
    sound: str
    seed: Optional[int] = None


PLACES = {
    "prairie": "the wide prairie",
    "canyon": "the red canyon",
    "town": "the dusty little town",
    "barn": "the old hay barn",
}

HERO_NAMES = ["Dusty", "Mae", "Hank", "Nell", "Jasper", "Ruby", "Bo", "June"]
SIDEKICK_NAMES = ["Pepper", "Tiny", "Midge", "Wren", "Toby", "Lulu"]

PROBLEMS = {
    "stuck_gate": {
        "label": "a stubborn gate",
        "noise": "KRRR-EEEK!",
        "line": "the gate would not budge",
        "resolution": "gave it one brave heave",
    },
    "storm_drums": {
        "label": "a rolling thunderhead",
        "noise": "BOOM-BOOM-BRAAAM!",
        "line": "the sky was rumbling like a giant drum",
        "resolution": "stood steady until the clouds rolled on",
    },
    "bullfrog_choir": {
        "label": "a chorus of bullfrogs",
        "noise": "RIBBIT-RIBBIT-RRROOOAARR!",
        "line": "the marsh sounded like a whole choir of frogs",
        "resolution": "laughed and listened without running away",
    },
}

SOUNDS = ["WHAM!", "KRRR-EEEK!", "BOOM!", "ZIP-ZAP!", "RIBBIT!", "THUMP!", "HOO-EE!"]

ASP_RULES = r"""
problem(P) :- problem_kind(P).
sound_effect(S) :- sound_kind(S).
brave_story(P, S) :- problem(P), sound_effect(S).
"""


class World:
    def __init__(self, params: StoryParams) -> None:
        self.params = params
        self.characters: dict[str, Character] = {}
        self.props: dict[str, Prop] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.fired: set[str] = set()

    def add_character(self, c: Character) -> Character:
        self.characters[c.name] = c
        return c

    def add_prop(self, p: Prop) -> Prop:
        self.props[p.name] = p
        return p

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall-tale story world with bravery and sound effects.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--hero-name", choices=HERO_NAMES)
    ap.add_argument("--sidekick-name", choices=SIDEKICK_NAMES)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--sound", choices=SOUNDS)
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
    place = args.place or rng.choice(sorted(PLACES))
    problem = args.problem or rng.choice(sorted(PROBLEMS))
    sound = args.sound or rng.choice(SOUNDS)
    hero_name = args.hero_name or rng.choice(HERO_NAMES)
    sidekick_name = args.sidekick_name or rng.choice([n for n in SIDEKICK_NAMES if n != hero_name])
    if args.problem and args.sound and args.sound not in SOUNDS:
        raise StoryError("That sound does not belong in this tall tale.")
    return StoryParams(
        place=place,
        hero_name=hero_name,
        sidekick_name=sidekick_name,
        problem=problem,
        sound=sound,
    )


def setup_world(params: StoryParams) -> World:
    world = World(params)
    hero = world.add_character(Character(name=params.hero_name, role="hero"))
    sidekick = world.add_character(Character(name=params.sidekick_name, role="sidekick"))
    world.add_prop(Prop(name=PROBLEMS[params.problem]["label"], kind="problem"))
    hero.memes["bravery"] = 0.0
    sidekick.memes["worry"] = 1.0
    world.facts.update(
        place=params.place,
        hero=hero,
        sidekick=sidekick,
        problem=params.problem,
        sound=params.sound,
    )
    return world


def tell_story(world: World) -> None:
    p = world.params
    hero = world.characters[p.hero_name]
    sidekick = world.characters[p.sidekick_name]
    place = PLACES[p.place]
    prob = PROBLEMS[p.problem]
    sound = p.sound

    world.say(
        f"Once, on {place}, {hero.name} was a small person with a big hat and an even bigger heart."
    )
    world.say(
        f"{hero.name} and {sidekick.name} were out where the wind could sing, and the day was so wide "
        f"it seemed to have a mile of blue in every pocket."
    )
    world.say(
        f"Then {prob['line']}, and from somewhere came {sound}."
    )
    world.para()
    world.say(
        f"{hero.name} swallowed hard and thought, I can be scared and still be brave."
    )
    world.say(
        f"{sidekick.name} whispered, \"Maybe we should run.\""
    )
    world.say(
        f"But {hero.name} squared {hero.name.lower()} shoulders like a fence post in a windstorm and marched closer."
    )
    hero.memes["bravery"] += 1.0
    sidekick.memes["worry"] += 1.0
    world.say(
        f"With one tall-tale tug of courage, {hero.name} {prob['resolution']}."
    )
    world.say(
        f"That went {sound} and then, as quiet as a kitten in a flour sack, the trouble gave way."
    )
    world.para()
    world.say(
        f"{sidekick.name} stared, grinned, and said, \"Well, hush my boots, you really did it!\""
    )
    world.say(
        f"{hero.name} tipped the hat and smiled, because bravery is not never being afraid; bravery is facing the noise anyway."
    )
    world.facts["resolved"] = True
    world.facts["bravery"] = hero.memes["bravery"]


def generation_prompts(world: World) -> list[str]:
    p = world.params
    return [
        f'Write a tall-tale style story for a young child set on {PLACES[p.place]} with a brave hero.',
        f"Tell a short story where {p.hero_name} hears {p.sound} and chooses bravery instead of running away.",
        f"Write a child-friendly adventure with inner monologue, sound effects, and a bold ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p = world.params
    prob = PROBLEMS[p.problem]
    return [
        QAItem(
            question=f"Where did {p.hero_name} and {p.sidekick_name} go in the story?",
            answer=f"They went to {PLACES[p.place]}, where the day was wide and windy.",
        ),
        QAItem(
            question=f"What problem scared {p.hero_name} first?",
            answer=f"{prob['line'].capitalize()}, and that made the moment feel bigger than a barn roof.",
        ),
        QAItem(
            question=f"What did {p.hero_name} think before getting brave?",
            answer="The hero thought, I can be scared and still be brave.",
        ),
        QAItem(
            question=f"How did the problem end?",
            answer=f"{p.hero_name} {prob['resolution']}, and the trouble finally went quiet.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is bravery?",
            answer="Bravery is doing the right thing or facing a hard moment even when you feel scared.",
        ),
        QAItem(
            question="What are sound effects in a story?",
            answer="Sound effects are written sounds, like BOOM or KRRR-EEEK, that help the reader imagine the noise.",
        ),
        QAItem(
            question="What is an inner monologue?",
            answer="An inner monologue is the private voice in a character's head, like a little thought whispering inside.",
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for c in world.characters.values():
        bits = []
        if c.memes:
            bits.append(f"memes={c.memes}")
        if c.meters:
            bits.append(f"meters={c.meters}")
        lines.append(f"  {c.name:10} ({c.role}) {' '.join(bits)}")
    lines.append(f"  facts: {world.facts}")
    return "\n".join(lines)


def asp_facts() -> str:
    import asp
    lines = []
    for p in PROBLEMS:
        lines.append(asp.fact("problem_kind", p))
    for s in SOUNDS:
        lines.append(asp.fact("sound_kind", s))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_check() -> bool:
    import asp
    model = asp.one_model(asp_program("#show brave_story/2."))
    atoms = set(asp.atoms(model, "brave_story"))
    expected = {(p, s) for p in PROBLEMS for s in SOUNDS}
    return atoms == expected


def build_story_text(world: World) -> StorySample:
    tell_story(world)
    return StorySample(
        params=world.params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def generate(params: StoryParams) -> StorySample:
    return build_story_text(setup_world(params))


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print("== (1) Generation prompts ==")
        for i, p in enumerate(sample.prompts, 1):
            print(f"{i}. {p}")
        print("\n== (2) Story questions ==")
        for item in sample.story_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")
        print("\n== (3) World-knowledge questions ==")
        for item in sample.world_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")


def verify() -> int:
    try:
        ok = asp_check()
    except Exception as e:
        print(f"ASP verification failed: {e}")
        return 1
    if not ok:
        print("ASP mismatch.")
        return 1
    print("OK: ASP parity check passed.")
    return 0


def curated() -> list[StoryParams]:
    return [
        StoryParams(place="prairie", hero_name="Dusty", sidekick_name="Pepper", problem="stuck_gate", sound="KRRR-EEEK!"),
        StoryParams(place="canyon", hero_name="Mae", sidekick_name="Tiny", problem="storm_drums", sound="BOOM!"),
        StoryParams(place="barn", hero_name="Hank", sidekick_name="Wren", problem="bullfrog_choir", sound="RIBBIT!"),
    ]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show brave_story/2."))
        return
    if args.verify:
        sys.exit(verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show brave_story/2."))
        atoms = sorted(set(asp.atoms(model, "brave_story")))
        for a in atoms:
            print(a)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in curated()]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            seed = base_seed + i
            i += 1
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
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 and not args.all else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
