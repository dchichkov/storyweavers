#!/usr/bin/env python3
"""
A tiny detective storyworld about an iconic pajama quest, a branch clue,
and a rhyme that helps friends solve a nighttime mystery.
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

_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if not os.path.exists(os.path.join(_root, "results.py")):
    _root = os.path.dirname(_root)
sys.path.insert(0, _root)
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class World:
    setting: str
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict[str, object] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, text: str) -> None:
        self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


@dataclass
class Clue:
    branch: str
    rhyme: str
    place: str
    answer: str
    reveal: str


@dataclass
class StoryParams:
    name: str
    partner: str
    mood: str
    seed: Optional[int] = None


NAMES = ["Luna", "Milo", "Nia", "Pip", "Suri"]
PARTNERS = ["Otis", "Bea", "Tomas", "Kiki", "Juno"]
MOODS = ["curious", "careful", "brave", "cheerful"]

CLUES = [
    Clue(
        branch="a silver branch beside the garden gate",
        rhyme='"By the branch where moonbeams dance, look for the door that gives a chance."',
        place="the little shed",
        answer="the shed door",
        reveal="a red pajama button caught on a wooden latch",
    ),
    Clue(
        branch="a crooked branch tapping the kitchen window",
        rhyme='"When branches knock and shadows play, find the warmest light to save the day."',
        place="the reading nook",
        answer="the reading nook",
        reveal="a pajama sleeve peeking from behind a cushion",
    ),
    Clue(
        branch="a leafy branch bent over the quiet porch",
        rhyme='"Under the branch, beneath the star, follow the stripe that is not far."',
        place="the porch chest",
        answer="the porch chest",
        reveal="a blue pajama pocket tucked under a blanket",
    ),
    Clue(
        branch="a forked branch casting two long shadows",
        rhyme='"Two shadows split, but one clues right: seek the moonlit stripe tonight."',
        place="the hall basket",
        answer="the hall basket",
        reveal="a pajama cuff folded around a toy lantern",
    ),
]

MORALS = [
    "Good detectives look closely, listen kindly, and let clues guide their next step.",
    "A small clue can brighten a big mystery when friends think together.",
    "The best quest is not about being first; it is about noticing what others miss.",
]


def valid_combos() -> list[tuple[str, str]]:
    return [(name, partner) for name in NAMES for partner in PARTNERS]


def build_world(params: StoryParams) -> World:
    if params.name == params.partner:
        raise StoryError("The detective and partner must have different names.")
    if params.mood not in MOODS:
        raise StoryError(f"Unknown mood: {params.mood}")
    rng = random.Random(params.seed)
    clue = rng.choice(CLUES)
    moral = rng.choice(MORALS)

    world = World("a moonlit little house")
    hero = world.add(Entity(params.name, "detective", params.name, {"clues": 0}, {"curiosity": 1}))
    partner = world.add(Entity(params.partner, "partner", params.partner, {"clues": 0}, {"trust": 1}))
    pajama = world.add(Entity("pajama", "lost_item", "an iconic red-and-blue pajama suit", {"found": 0}, {"comfort": 1}))
    branch = world.add(Entity("branch", "clue", clue.branch, {"noticed": 0}, {"mystery": 1}))
    world.facts.update(hero=hero, partner=partner, pajama=pajama, branch=branch, clue=clue, moral=moral)

    world.say(
        f"At bedtime in {world.setting}, {hero.label} became a detective for one important quest: "
        f"to find an iconic pajama suit before the moon climbed high."
    )
    world.say(
        f"{partner.label} joined with a small lantern. The pajama suit was soft, bright, and special "
        f"because its stars and stripes made bedtime feel like an adventure."
    )
    world.say(
        f"Then {hero.label} noticed {clue.branch}. A tiny thread of red cloth hung from it."
    )
    branch.meters["noticed"] = 1
    hero.meters["clues"] = 1
    world.say(f'"That branch is a clue," said {hero.label}. "{partner.label}, what do you see?"')
    world.say(f'"I see a path, not a hiding place," replied {partner.label}. "Let us follow it carefully."')
    world.para()

    hero.memes["curiosity"] = 2
    partner.memes["trust"] = 2
    world.say(f"Beside the branch, they found a card with a neat rhyme: {clue.rhyme}")
    world.say(f"{hero.label} read the rhyme twice, while {partner.label} held the lantern steady.")
    world.say(
        f'"The warm clue must lead to {clue.answer}," said {hero.label}. '
        f'"And we will check together," said {partner.label}.'
    )
    world.say(f"Their shared plan turned the rhyme into a map for the next part of the quest.")
    world.para()

    world.say(f"They searched {clue.place}, looking under cushions, behind books, and beside the old clock.")
    world.say(f"At last, {hero.label} spotted {clue.reveal}.")
    pajama.meters["found"] = 1
    hero.memes["relief"] = 1
    partner.memes["joy"] = 1
    world.say(f'"Case solved!" cried {hero.label}. "{partner.label}, you followed the clue with me."')
    world.say(f'"A good detective listens," said {partner.label}, "and a good friend keeps the lantern bright."')
    world.para()

    world.say(
        f"They carried the {pajama.label} back to bed. Its bright pattern glowed softly in the moonlight, "
        f"so everyone could see what the careful quest had changed."
    )
    world.say(f"{hero.label} wrote the answer in the detective notebook: {clue.answer}.")
    world.say(f"They remembered this lesson: {moral}")
    return world


def generation_prompts(world: World) -> list[str]:
    clue: Clue = world.facts["clue"]  # type: ignore[assignment]
    hero: Entity = world.facts["hero"]  # type: ignore[assignment]
    return [
        'Write a gentle detective story using the words "branch", "iconic", and "pajama".',
        f"Tell a rhyming nighttime Quest in which {hero.label} follows {clue.branch}.",
        "Write a child-friendly mystery where dialogue changes the detectives' plan.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero: Entity = world.facts["hero"]  # type: ignore[assignment]
    partner: Entity = world.facts["partner"]  # type: ignore[assignment]
    pajama: Entity = world.facts["pajama"]  # type: ignore[assignment]
    clue: Clue = world.facts["clue"]  # type: ignore[assignment]
    return [
        QAItem("Who solved the bedtime mystery?", f"{hero.label} and {partner.label} solved it together."),
        QAItem("What did the branch tell them?", f"The branch held a red thread that pointed toward {clue.answer}."),
        QAItem("What helped them choose their next step?", f"A rhyme guided them toward {clue.answer}."),
        QAItem("What were they trying to find?", f"They were trying to find {pajama.label}."),
        QAItem("How did teamwork help?", f"{hero.label} read the clue while {partner.label} held the lantern and checked the path."),
        QAItem("What lesson did they learn?", world.facts["moral"]),  # type: ignore[arg-type]
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem("What is a detective?", "A detective is someone who studies clues to solve a mystery."),
        QAItem("What is a rhyme?", "A rhyme is a group of words with matching or nearly matching sounds."),
        QAItem("What is a branch?", "A branch is a woody part that grows from the trunk of a tree."),
        QAItem("What is a pajama?", "Pajamas are soft clothes worn for sleeping."),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    lines.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
    lines.append("\n== (2) Story questions ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("\n== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        lines.append(
            f"  {entity.id:8} kind={entity.kind:10} meters={entity.meters} memes={entity.memes}"
        )
    return "\n".join(lines)


def asp_facts() -> str:
    import asp
    lines = [asp.fact("setting", "moonlit_house")]
    for name in NAMES:
        lines.append(asp.fact("detective", name))
    for partner in PARTNERS:
        lines.append(asp.fact("partner", partner))
    lines.append(asp.fact("object", "pajama"))
    lines.append(asp.fact("clue", "branch"))
    return "\n".join(lines)


ASP_RULES = r"""
valid_story(N, P) :- detective(N), partner(P), N != P, object(pajama), clue(branch).
#show valid_story/2.
"""


def asp_program(show: str = "#show valid_story/2.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program())
    found = set(asp.atoms(model, "valid_story"))
    expected = set(valid_combos())
    if found == expected:
        print(f"OK: ASP gate contains {len(found)} valid combinations.")
        return 0
    print("ASP/Python mismatch.")
    print("Only ASP:", sorted(found - expected))
    print("Only Python:", sorted(expected - found))
    return 1


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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    name = args.name or rng.choice(NAMES)
    partner = args.partner or rng.choice([p for p in PARTNERS if p != name])
    mood = args.mood or rng.choice(MOODS)
    return StoryParams(name=name, partner=partner, mood=mood, seed=args.seed)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate a rhyming pajama detective quest.")
    parser.add_argument("--name", choices=NAMES)
    parser.add_argument("--partner", choices=PARTNERS)
    parser.add_argument("--mood", choices=MOODS)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--seed", type=int)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


CURATED = [
    StoryParams("Luna", "Otis", "curious"),
    StoryParams("Milo", "Bea", "careful"),
    StoryParams("Nia", "Juno", "brave"),
]


def emit(sample: StorySample, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world:
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
        print(sorted(set(asp.atoms(model, "valid_story"))))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        samples = []
        for i in range(args.n):
            rng = random.Random(base_seed + i)
            params = resolve_params(args, rng)
            params.seed = base_seed + i
            samples.append(generate(params))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=f"### variant {i + 1}" if len(samples) > 1 else "")
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
