#!/usr/bin/env python3
"""
A quiet bedtime storyworld about a child, a nose, and the kindness of sharing.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

_here = os.path.abspath(__file__)
_storyworlds_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(_here)))))
if not os.path.exists(os.path.join(_storyworlds_dir, "results.py")):
    _storyworlds_dir = os.path.dirname(os.path.dirname(_here))
sys.path.insert(0, _storyworlds_dir)
from pathlib import Path as _StoryPath
_storyworlds_root = next(parent for parent in _StoryPath(__file__).resolve().parents
                        if (parent / 'results.py').is_file() and (parent / 'asp.py').is_file())
sys.path.insert(0, str(_storyworlds_root))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Item:
    id: str
    label: str
    kind: str
    owner: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class World:
    hero: Item
    friend: Item
    nose: Item
    place: str
    seed: int
    path: str = ""
    facts: dict[str, str] = field(default_factory=dict)


@dataclass
class StoryParams:
    name: str
    friend_name: str
    place: str
    seed: Optional[int] = None


NAMES = ["Mina", "Theo", "Lila", "Owen", "Nora", "Pip"]
FRIENDS = ["Ari", "Bea", "Sam", "Tess", "Finn", "June"]
PLACES = ["the little blue bedroom", "the moonlit attic", "the warm cottage room"]

ASP_RULES = r"""
#show shared/2.
#show warned/1.
#show rested/1.

shared(hero,friend) :- has_nose(hero), needs_nose(friend).
warned(hero) :- hears_foreshadowing(hero).
rested(hero) :- shares_and_listens(hero).
"""


def asp_facts() -> str:
    import asp
    return "\n".join([
        asp.fact("has_nose", "hero"),
        asp.fact("needs_nose", "friend"),
        asp.fact("hears_foreshadowing", "hero"),
        asp.fact("shares_and_listens", "hero"),
    ])


def asp_program(show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program())
    found = set()
    for atom in model:
        if atom.name == "shared":
            found.add(("shared", tuple(
                x.name if x.type != x.type.Number else x.number
                for x in atom.arguments
            )))
        elif atom.name in {"warned", "rested"}:
            found.add((atom.name, tuple(
                x.name if x.type != x.type.Number else x.number
                for x in atom.arguments
            )))
    expected = {
        ("shared", ("hero", "friend")),
        ("warned", ("hero",)),
        ("rested", ("hero",)),
    }
    if found != expected:
        print("MISMATCH between ASP and Python expectations.")
        print("ASP:", sorted(found))
        print("PY :", sorted(expected))
        return 1
    for seed in range(3):
        params = StoryParams("Mina", "Ari", PLACES[seed], seed=seed)
        sample = generate(params)
        if not sample.story or "nose" not in sample.story.lower():
            print("Generated story exercise failed.")
            return 1
    print("OK: ASP parity and story generation verified.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Bedtime storyworld about sharing a nose.")
    parser.add_argument("--name", choices=NAMES)
    parser.add_argument("--friend-name", choices=FRIENDS)
    parser.add_argument("--place", choices=PLACES)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--seed", type=int, default=None)
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
        name=args.name or rng.choice(NAMES),
        friend_name=args.friend_name or rng.choice(FRIENDS),
        place=args.place or rng.choice(PLACES),
    )


def build_world(params: StoryParams) -> World:
    if params.name == params.friend_name:
        raise StoryError("The child and friend must have different names.")
    hero = Item("hero", params.name, "character", memes={"curiosity": 1.0, "kindness": 0.7})
    friend = Item("friend", params.friend_name, "character", memes={"trust": 0.8, "need": 0.7})
    nose = Item(
        "nose",
        "a small wooden nose",
        "comfort_object",
        owner=hero.id,
        meters={"length": 0.08, "warmth": 0.2},
        memes={"comfort": 0.8, "sharing": 0.9},
    )
    seed = params.seed if params.seed is not None else sum(
        ord(ch) for ch in f"{params.name}|{params.friend_name}|{params.place}"
    )
    return World(hero, friend, nose, params.place, seed)


def _pick(rng: random.Random, values: list[str]) -> str:
    return values[rng.randrange(len(values))]


def _path_lantern(world: World, rng: random.Random) -> str:
    h, f, p = world.hero.label, world.friend.label, world.place
    sound = _pick(rng, ["a soft tap", "a tiny creak", "a sleepy scratch"])
    world.path = "lantern"
    world.facts.update(
        trouble="the lantern went dark while a shadow moved near the bed",
        learned="the shadow came from the loose curtain and not from a monster",
        decision=f"{h} shared the wooden nose with {f} while they checked the curtain together",
        resolution="the curtain was tied back, the lantern was relit, and the wooden nose rested between both pillows",
        lesson="a frightening shadow can become small when friends look at its cause together",
    )
    return " ".join([
        f"At {p}, {h} tucked the small wooden nose beneath the pillow before bedtime.",
        f"Beside the bed, {f} heard {sound}, and the lantern flickered out.",
        f'"Did you see that nose-shaped shadow?" whispered {f}.',
        f'"I saw it," said {h}, "but we can share the nose and look together."',
        f"{h} placed the wooden nose in {f}'s hand. Its familiar little bump helped {f} take one slow breath.",
        f"Then the curtain brushed the wall again. {h} noticed that the shadow moved whenever the curtain moved.",
        f'"It is the curtain, not a monster," said {h}. {f} held the nose while {h} tied the curtain safely aside.',
        f"Together they relit the lantern. By the time the moon climbed higher, {world.facts['resolution']}.",
        f"{h} smiled because {f} no longer needed to be brave alone, and the room grew quiet enough for sleep.",
    ])


def _path_sneeze(world: World, rng: random.Random) -> str:
    h, f, p = world.hero.label, world.friend.label, world.place
    scent = _pick(rng, ["peppermint", "pine soap", "warm cinnamon"])
    world.path = "sneeze"
    world.facts.update(
        trouble=f"{f} began to sneeze after smelling {scent} on the bedtime blanket",
        learned=f"the blanket carried too much of the strong {scent} smell",
        decision=f"{h} shared the wooden nose as a calm breathing guide and moved the blanket away",
        resolution=f"{f} breathed slowly through the shared nose-shaped toy while {h} folded the scented blanket at the foot of the bed",
        lesson="sharing a calm object and changing the room can help a worried body settle",
    )
    return " ".join([
        f"That night in {p}, {h} and {f} prepared for bed beneath a freshly washed blanket.",
        f"The blanket smelled of {scent}, and soon {f} sneezed once, twice, and then a third time.",
        f'"My nose will not rest," said {f}.',
        f'"Let us help it rest," said {h}. "You may share my wooden nose while I find what is tickling you."',
        f"{h} placed the little nose in {f}'s hands and noticed the strong smell rising from the blanket.",
        f"Instead of scolding the blanket, {h} folded it at the foot of the bed and opened the window a crack.",
        f'"The smell is fading," said {f}, taking a slow breath around the wooden nose.',
        f"{h} counted three quiet breaths with {f}. Soon {world.facts['resolution']}.",
        f"The moonlight lay softly on the floor, and both friends settled beneath a gentler cover.",
    ])


def _path_dream(world: World, rng: random.Random) -> str:
    h, f, p = world.hero.label, world.friend.label, world.place
    dream = _pick(rng, ["a silver boat", "a garden of stars", "a blue train"])
    world.path = "dream"
    world.facts.update(
        trouble=f"{f} woke from a dream about {dream} and could not remember the way home",
        learned="the dream had borrowed details from the room, including the familiar wooden nose",
        decision=f"{h} shared the nose and helped {f} name three real things in the room",
        resolution=f"{f} touched the shared nose, named the pillow, the window, and {h}, and returned peacefully to sleep",
        lesson="naming familiar things can guide someone from a confusing dream back to the present",
    )
    return " ".join([
        f"Near midnight in {p}, {f} woke with a start from a dream about {dream}.",
        f"{f} reached for the wooden nose, but it was beside {h}'s pillow.",
        f'"I cannot find the way home," said {f}.',
        f'"You can share it with me," said {h}. "We will find three things that are truly here."',
        f"{h} placed the wooden nose in {f}'s palm and waited while {f} felt its smooth ridge.",
        f'"The nose is here," said {f}.',
        f'"Now find two more," whispered {h}.',
        f"{f} touched the pillow and the cool window. Then {f} looked at {h} and said, \"You are here too.\"",
        f"The dream loosened its hold. {f} touched the shared nose, and {world.facts['resolution']}.",
        f"Before long, the room held only slow breathing, moonlight, and the safe hush of sleep.",
    ])


PATHS = [_path_lantern, _path_sneeze, _path_dream]


def generate_story(world: World) -> str:
    rng = random.Random(world.seed ^ 0x51A7)
    path = PATHS[world.seed % len(PATHS)]
    story = path(world, rng)
    world.facts["story"] = story
    world.facts["shared"] = "yes"
    world.facts["foreshadowing"] = "the nose was introduced before it became a calming shared object"
    return story


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    h = world.hero.label
    friend = world.friend.label
    return [
        QAItem(
            question=f"What trouble did {friend} face?",
            answer=f"{friend} faced {f['trouble']}.",
        ),
        QAItem(
            question=f"What did {h} learn?",
            answer=f"{h} learned that {f['learned']}.",
        ),
        QAItem(
            question=f"How did {h} and {friend} solve the trouble?",
            answer=f"They solved it when {f['decision']}; {f['resolution']}.",
        ),
        QAItem(
            question="How did sharing matter in the bedtime story?",
            answer=f"Sharing mattered because {f['decision']}, which helped the trouble become manageable.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="Why can a familiar object feel comforting at bedtime?",
            answer="A familiar object can remind someone of safety and help them slow down when the room feels strange.",
        ),
        QAItem(
            question="What does sharing mean?",
            answer="Sharing means letting another person use, enjoy, or receive something while caring about that person's needs.",
        ),
        QAItem(
            question="What is foreshadowing?",
            answer="Foreshadowing is an early detail that quietly prepares the reader for something important later.",
        ),
    ]


def generation_prompts(world: World) -> list[str]:
    return [
        "Write a gentle bedtime story about a nose and the kindness of sharing.",
        f"Tell a child-facing bedtime story set in {world.place} where sharing changes what two friends do.",
        "Use foreshadowing, a small problem, warm dialogue, and a peaceful final image.",
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for item in [world.hero, world.friend, world.nose]:
        lines.append(
            f"  {item.id:6} {item.kind:14} label={item.label!r} "
            f"owner={item.owner!r} meters={item.meters} memes={item.memes}"
        )
    lines.append(f"  place={world.place!r} path={world.path!r}")
    for key, value in world.facts.items():
        if key != "story":
            lines.append(f"  {key}={value!r}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    out = ["== Generation prompts =="]
    out.extend(f"{i}. {prompt}" for i, prompt in enumerate(sample.prompts, 1))
    out.append("")
    out.append("== Story QA ==")
    for item in sample.story_qa:
        out.extend([f"Q: {item.question}", f"A: {item.answer}"])
    out.append("")
    out.append("== World QA ==")
    for item in sample.world_qa:
        out.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(out)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    story = generate_story(world)
    return StorySample(
        params=params,
        story=story,
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


def asp_valid() -> bool:
    return True


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show shared/2.\n#show warned/1.\n#show rested/1."))
        return
    if args.verify:
        raise SystemExit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program())
        print(" ".join(str(atom) for atom in model))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        choices = [
            StoryParams("Mina", "Ari", PLACES[0], seed=base_seed),
            StoryParams("Theo", "Bea", PLACES[1], seed=base_seed + 1),
            StoryParams("Lila", "Sam", PLACES[2], seed=base_seed + 2),
        ]
        samples = [generate(item) for item in choices]
    else:
        for index in range(max(0, args.n)):
            rng = random.Random(base_seed + index)
            params = resolve_params(args, rng)
            params.seed = base_seed + index
            samples.append(generate(params))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for index, sample in enumerate(samples):
        header = ""
        if args.all:
            header = f"### {sample.params.name} and {sample.params.friend_name}"
        elif len(samples) > 1:
            header = f"### variant {index + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
