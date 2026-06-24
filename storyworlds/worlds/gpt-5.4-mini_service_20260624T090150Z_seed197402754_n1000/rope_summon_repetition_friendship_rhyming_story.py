#!/usr/bin/env python3
"""
A tiny story world about a rope, a summon, and a friendship rhyme.

A child and a friend try to summon a paper kite with a bell-rope at the park.
When the rope tangles, they pause, help each other, and find a playful rhythm:
pull, call, laugh, and try again. The story is built from state changes:
the rope can be coiled, tangled, straightened, and used; the friends can feel
hope, worry, and joy; the kite can answer the summon by lifting into the air.
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

RHYME_ENDINGS = {
    "park": ("spark", "arc", "dark"),
    "yard": ("card", "yard", "hard"),
    "meadow": ("glow", "show", "slow"),
}

NAMES = ["Mina", "Nico", "Tia", "Bram", "Lina", "Owen", "Sage", "Pip"]
FRIEND_NAMES = ["Milo", "Rae", "June", "Toby", "Pia", "Finn", "Noa", "Bea"]


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    held_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self):
        for k in ("tangle", "pull", "lift", "joy", "worry", "friendship"):
            self.meters.setdefault(k, 0.0)
            self.memes.setdefault(k, 0.0)


@dataclass
class StoryParams:
    place: str
    hero: str
    friend: str
    seed: Optional[int] = None


@dataclass
class World:
    place: str
    hero: Entity
    friend: Entity
    rope: Entity
    kite: Entity
    bell: Entity
    facts: dict = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small rhyming story world about rope and friendship.")
    ap.add_argument("--place", choices=["park", "yard", "meadow"])
    ap.add_argument("--name")
    ap.add_argument("--friend")
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
    place = args.place or rng.choice(["park", "yard", "meadow"])
    hero = args.name or rng.choice(NAMES)
    friend = args.friend or rng.choice(FRIEND_NAMES)
    if hero == friend:
        raise StoryError("The hero and friend must be different names.")
    return StoryParams(place=place, hero=hero, friend=friend)


def _rhymes(place: str) -> tuple[str, str, str]:
    return RHYME_ENDINGS.get(place, ("light", "night", "bright"))


def _make_world(params: StoryParams) -> World:
    hero = Entity(id=params.hero, kind="character", label=params.hero)
    friend = Entity(id=params.friend, kind="character", label=params.friend)
    rope = Entity(id="rope", label="rope", phrase="a soft red rope", owner=hero.id)
    kite = Entity(id="kite", label="kite", phrase="a paper kite with a painted tail")
    bell = Entity(id="bell", label="bell", phrase="a tiny silver bell", owner=friend.id)
    return World(place=params.place, hero=hero, friend=friend, rope=rope, kite=kite, bell=bell)


def _pull_rope(world: World, by: Entity, amount: float = 1.0) -> None:
    world.rope.meters["pull"] += amount
    if world.rope.meters["tangle"] > 0:
        world.rope.memes["worry"] += 0.5
    else:
        world.rope.meters["lift"] += amount


def _tangle_rope(world: World) -> None:
    world.rope.meters["tangle"] += 1.0
    world.hero.memes["worry"] += 1.0
    world.friend.memes["worry"] += 1.0


def _untangle_rope(world: World) -> None:
    if world.rope.meters["tangle"] <= 0:
        return
    world.rope.meters["tangle"] = max(0.0, world.rope.meters["tangle"] - 1.0)
    world.hero.memes["joy"] += 0.5
    world.friend.memes["joy"] += 0.5
    world.hero.memes["friendship"] += 1.0
    world.friend.memes["friendship"] += 1.0


def _summon_kite(world: World) -> bool:
    if world.rope.meters["tangle"] > 0:
        return False
    if world.rope.meters["pull"] < 2.0:
        return False
    world.kite.meters["lift"] += 1.0
    world.kite.held_by = None
    return True


def tell(params: StoryParams) -> World:
    world = _make_world(params)
    rhyme1, rhyme2, rhyme3 = _rhymes(params.place)
    world.facts["rhymes"] = (rhyme1, rhyme2, rhyme3)

    world.say(
        f"In the {params.place}, where the grass could {rhyme1}, "
        f"{world.hero.id} found a rope and gave a grin."
    )
    world.say(
        f'"Let us summon the kite," said {world.friend.id} with cheer, '
        f"and the little bell rang bright and clear."
    )
    world.para()

    world.say(
        f"{world.hero.id} held the rope. {world.friend.id} held the bell. "
        f"They sang, 'Pull and call, and watch it swell!'"
    )
    _pull_rope(world, world.hero, 1.0)
    _pull_rope(world, world.friend, 1.0)
    _summon_kite(world)
    world.say(
        f"The kite twitched once, then gave a tiny sway, "
        f"but a twist in the rope still blocked the way."
    )
    _tangle_rope(world)
    world.say(
        f"The rope made a knot, all curly and tight. "
        f"The friends stopped fast; that did not feel right."
    )
    world.para()

    world.say(
        f'"No fret," said {world.friend.id}. "We can fix this as pals." '
        f'"Yes," said {world.hero.id}, "with careful hands and calms."'
    )
    _untangle_rope(world)
    world.say(
        f"They worked side by side in a soft, slow swing, "
        f"and the knot came loose like a ribbon in spring."
    )
    world.say(
        f"Then the bell went ding, the rope went straight, "
        f"and the kite rose high like it knew it was late."
    )
    _pull_rope(world, world.hero, 1.0)
    _pull_rope(world, world.friend, 1.0)
    _summon_kite(world)
    world.say(
        f"Up, up went the kite in the {params.place} air, "
        f"with {world.hero.id} and {world.friend.id} laughing there."
    )
    world.say(
        f"They called once more, then called once again, "
        f"and the rope kept time like a happy refrain."
    )

    world.facts.update(
        params=params,
        place=params.place,
        hero=world.hero,
        friend=world.friend,
        rope=world.rope,
        kite=world.kite,
        bell=world.bell,
        summoned=world.kite.meters["lift"] > 0,
        tangled_at_turn=True,
        resolved=world.rope.meters["tangle"] == 0,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    p = world.facts["params"]
    return [
        f'Write a short rhyming story for a young child about a rope that can summon a kite in the {p.place}.',
        f"Tell a gentle friendship story where {p.hero} and {p.friend} use a rope, make a knot, and then fix it together.",
        f'Write a simple rhyme that repeats "pull" and "call" and ends with friends smiling at a flying kite.',
    ]


def story_qa(world: World) -> list[QAItem]:
    p = world.facts["params"]
    return [
        QAItem(
            question=f"Who wanted to summon the kite in the {p.place}?",
            answer=f"{world.hero.id} and {world.friend.id} both wanted to summon the kite together.",
        ),
        QAItem(
            question="What problem happened to the rope?",
            answer="The rope got tangled into a tight knot before the kite could rise well.",
        ),
        QAItem(
            question="How did the friends fix the problem?",
            answer="They worked side by side, untangled the rope, and then pulled again together.",
        ),
        QAItem(
            question="What changed at the end of the story?",
            answer="The kite lifted into the air, and the friends felt happy and proud.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a rope for?",
            answer="A rope is a long, strong cord you can pull, tie, or use to help move things.",
        ),
        QAItem(
            question="What does summon mean?",
            answer="To summon something means to call it or bring it near in a special way.",
        ),
        QAItem(
            question="What is friendship?",
            answer="Friendship is the caring bond between people who help, listen, and have fun together.",
        ),
        QAItem(
            question="Why do people repeat words in a rhyme?",
            answer="People repeat words in a rhyme to make it catchy, playful, and easy to remember.",
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in [world.hero, world.friend, world.rope, world.bell, world.kite]:
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:8} ({e.kind:9}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
rope_used :- pull_count(N), N >= 2.
kite_lifts :- rope_used, not tangled.
tangled :- knot.
friendship_grows :- untie, help.
"""


def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            asp.fact("place", "park"),
            asp.fact("place", "yard"),
            asp.fact("place", "meadow"),
            asp.fact("keyword", "rope"),
            asp.fact("keyword", "summon"),
            asp.fact("feature", "repetition"),
            asp.fact("feature", "friendship"),
        ]
    )


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    return 0


CURATED = [
    StoryParams(place="park", hero="Mina", friend="Milo"),
    StoryParams(place="yard", hero="Tia", friend="Rae"),
    StoryParams(place="meadow", hero="Nico", friend="June"),
]


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


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


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
        print(asp_program("#show kite_lifts/0."))
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 40):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            i += 1
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
            header = f"### {p.hero} and {p.friend} in the {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
