#!/usr/bin/env python3
"""A nursery-rhyme storyworld about gingham, gentle magic, and a useful surprise."""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

_here = os.path.abspath(__file__)
_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(_here)))))
if not os.path.exists(os.path.join(_root, "results.py")):
    _root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(_here))))
sys.path.insert(0, _root)
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
    child: Item
    friend: Item
    cloth: Item
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


NAMES = ["Mina", "Pip", "Lulu", "Nell", "Toby", "Wren"]
FRIENDS = ["Bram", "Poppy", "Kit", "Moss", "Daisy", "Finn"]
PLACES = ["the little kitchen", "the moonlit garden", "the village lane", "the red attic"]

ASP_RULES = r"""
#show bright/1.
#show helpful/1.
#show shared/1.

bright(X) :- magic_gingham(X).
helpful(X) :- bright(X), kindness_used(X).
shared(X) :- helpful(X), friend_told(X).
"""


def asp_facts() -> str:
    import asp
    return "\n".join([
        asp.fact("magic_gingham", "cloth"),
        asp.fact("kindness_used", "cloth"),
        asp.fact("friend_told", "cloth"),
    ])


def asp_program(show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program())
    got = {(a.name, tuple(x.name if x.type != x.type.Number else x.number for x in a.arguments))
           for a in model}
    expected = {
        ("bright", ("cloth",)),
        ("helpful", ("cloth",)),
        ("shared", ("cloth",)),
    }
    if got == expected:
        print("OK: ASP parity verified.")
        return 0
    print("MISMATCH between ASP and Python expectations.")
    print("ASP:", sorted(got))
    print("PY :", sorted(expected))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A magical gingham nursery rhyme storyworld.")
    ap.add_argument("--name", choices=NAMES)
    ap.add_argument("--friend-name", choices=FRIENDS)
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return StoryParams(
        name=args.name or rng.choice(NAMES),
        friend_name=args.friend_name or rng.choice(FRIENDS),
        place=args.place or rng.choice(PLACES),
    )


def build_world(params: StoryParams) -> World:
    if params.name == params.friend_name:
        raise StoryError("The child and friend must have different names.")
    seed = params.seed if params.seed is not None else sum(
        ord(c) for c in f"{params.name}|{params.friend_name}|{params.place}"
    )
    return World(
        child=Item("child", params.name, "character", memes={"curiosity": 1.0}),
        friend=Item("friend", params.friend_name, "character", memes={"trust": 1.0}),
        cloth=Item(
            "cloth", "gingham", "magical cloth",
            meters={"softness": 1.0, "brightness": 0.8},
            memes={"wonder": 1.0},
        ),
        place=params.place,
        seed=seed,
    )


def _pick(rng: random.Random, values: list[str]) -> str:
    return values[rng.randrange(len(values))]


def _path_lantern(w: World, rng: random.Random) -> str:
    n, f, p = w.child.label, w.friend.label, w.place
    color = _pick(rng, ["blue", "golden", "silver"])
    w.path = "lantern"
    w.facts.update(
        discovery="the gingham could turn a whispered wish into a small floating light",
        trouble=f"the new light drifted away and left {p} dim",
        learned="the cloth answered only a wish spoken kindly for someone else",
        decision=f"{n} asked for a light to guide {f} home instead of asking for a toy",
        resolution=f"the gingham folded itself into a {color} lantern and floated beside {f} all the way home",
        ending=f"the {color} lantern rested on the windowsill while the gingham lay warm and quiet in {n}'s hands",
        object="a floating lantern",
    )
    lines = [
        f"In {p}, {n} found a square of gingham tucked under a wooden bowl.",
        f"When {n} whispered, “Shine a little,” the cloth twinkled and lifted a tiny light into the air.",
        f'"Look!" cried {n}. "{f}, come quickly!"',
        f"{f} hurried in, but the light drifted through the open door and left the room dim.",
        f'"Why did it fly away?" asked {f}.',
        f"{n} held the gingham close and discovered that it had heard the wish but not the need.",
        f'"It may help a friend," said {n}. "I wish for a light to guide you home."',
        f"The gingham warmed, folded into a {color} lantern, and floated beside {f} along the lane.",
        f"At bedtime, {w.facts['ending']}.",
    ]
    return " ".join(lines)


def _path_rain(w: World, rng: random.Random) -> str:
    n, f, p = w.child.label, w.friend.label, w.place
    sound = _pick(rng, ["tap-tap", "plip-plop", "patter-pat"])
    w.path = "rain"
    w.facts.update(
        discovery="the gingham could hold back rain when someone sang a true promise",
        trouble=f"a sudden shower soaked {f}'s paper boat before it reached the village pond",
        learned="the magic listened for a promise that the singer truly meant to keep",
        decision=f"{n} promised to share the boat and keep it safe from the puddled ditch",
        resolution=f"the gingham widened into a bright awning and carried the boat dry to the pond",
        ending=f"the paper boat floated beneath the gingham awning while raindrops chimed on top",
        object="a dry paper boat",
    )
    lines = [
        f"At {p}, {n} and {f} folded a paper boat beside a square of gingham.",
        f"The sky grew gray, and {sound}, the rain began before {f} could launch the boat.",
        f'"My boat will melt!" cried {f}. "Can the gingham help?"',
        f"{n} waved the cloth, but a drop slipped through and landed on the paper sail.",
        f'"Magic likes a promise," said {n}. "But it must be a promise you mean."',
        f"{n} thought carefully, then said, “I promise to share the boat and keep it safe from the ditch.”",
        f"The gingham shivered, grew wide, and made a striped awning over the boat.",
        f"Together the children pushed the boat to the pond while the rain drummed above them.",
        f"At last, {w.facts['ending']}.",
    ]
    return " ".join(lines)


def _path_bells(w: World, rng: random.Random) -> str:
    n, f, p = w.child.label, w.friend.label, w.place
    tune = _pick(rng, ["ding-a-ding", "ting-a-ling", "bell-bell-bright"])
    w.path = "bells"
    w.facts.update(
        discovery="the gingham could make hidden things ring when two friends told the truth together",
        trouble=f"the village lost its welcome bell before the evening gathering",
        learned="the magic grew stronger when both friends added honest words",
        decision=f"{n} and {f} admitted that they had moved the bell rope while playing",
        resolution=f"the gingham rang {tune} and revealed the bell beneath a pile of leaves",
        ending=f"the village bell rang {tune} above the gingham banner, and everyone came smiling",
        object="a found village bell",
    )
    lines = [
        f"Near {p}, {n} and {f} found a checked gingham cloth beside an empty bell post.",
        f"The welcome bell was gone, and the villagers searched every path without finding it.",
        f'"Could the cloth know where it went?" asked {f}.',
        f"{n} touched the gingham, but it stayed still until both children spoke.",
        f'"We must tell the truth," said {n}. "Did we move the bell rope yesterday?"',
        f"{f} looked down. “We did, and then we forgot where we left it.”",
        f"{n} nodded. “I did too. Let us search the place where our game began.”",
        f"The gingham flashed, rang {tune}, and pulled open a leafy mound beside the old rope.",
        f"The children carried the bell back together. At dusk, {w.facts['ending']}.",
    ]
    return " ".join(lines)


PATHS = [_path_lantern, _path_rain, _path_bells]


def generate_story(world: World) -> str:
    rng = random.Random(world.seed ^ 0x51A7)
    return PATHS[world.seed % len(PATHS)](world, rng)


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    n = world.child.label
    return [
        QAItem(f"What did {n} learn about the gingham?", f"{n} learned that {f['learned']}."),
        QAItem("What trouble happened?", f"The trouble was that {f['trouble']}."),
        QAItem(f"What did {n} decide to do?", f"{f['decision'].capitalize()}."),
        QAItem("What showed that the problem was solved?", f"{f['resolution'].capitalize()}."),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            "What is gingham?",
            "Gingham is a woven cloth with a simple checked pattern, often made with two colors.",
        ),
        QAItem(
            "What is magic in a nursery rhyme?",
            "Magic in a nursery rhyme is an imaginative power that makes an ordinary object do something surprising.",
        ),
        QAItem(
            "Why do stories use promises?",
            "Promises help characters show what they value, and keeping one can guide a kind decision.",
        ),
    ]


def generation_prompts(world: World) -> list[str]:
    return [
        "Write a gentle nursery rhyme about gingham and a little bit of magic.",
        f"Tell a child-facing magical story about {world.child.label} and {world.friend.label}.",
        "Use a simple rhyme-like rhythm, a clear problem, and a visible kind resolution.",
    ]


def dump_trace(world: World) -> str:
    out = ["--- world model state ---"]
    for item in (world.child, world.friend, world.cloth):
        out.append(
            f"  {item.id:6} {item.kind:14} label={item.label!r} "
            f"meters={item.meters} memes={item.memes}"
        )
    out.append(f"  place={world.place!r} path={world.path!r}")
    out.append(f"  facts={world.facts}")
    return "\n".join(out)


def format_qa(sample: StorySample) -> str:
    out = ["== Generation prompts =="]
    out.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
    out.append("\n== Story QA ==")
    for q in sample.story_qa:
        out.extend([f"Q: {q.question}", f"A: {q.answer}"])
    out.append("\n== World QA ==")
    for q in sample.world_qa:
        out.extend([f"Q: {q.question}", f"A: {q.answer}"])
    return "\n".join(out)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    story = generate_story(world)
    world.facts["story"] = story
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
        print("\n" + format_qa(sample))


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show bright/1.\n#show helpful/1.\n#show shared/1."))
        return
    if args.verify:
        raise SystemExit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program())
        print(" ".join(str(a) for a in model))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        choices = [
            StoryParams("Mina", "Bram", "the little kitchen", base_seed),
            StoryParams("Pip", "Poppy", "the moonlit garden", base_seed + 1),
            StoryParams("Lulu", "Kit", "the village lane", base_seed + 2),
        ]
        samples = [generate(p) for p in choices]
    else:
        for i in range(args.n):
            rng = random.Random(base_seed + i)
            params = resolve_params(args, rng)
            params.seed = base_seed + i
            samples.append(generate(params))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            header = f"### {sample.params.name} at {sample.params.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i + 1 < len(samples):
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
