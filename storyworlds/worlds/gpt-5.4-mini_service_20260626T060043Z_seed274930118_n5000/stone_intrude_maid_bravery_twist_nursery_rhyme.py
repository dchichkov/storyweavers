#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/stone_intrude_maid_bravery_twist_nursery_rhyme.py
=============================================================================================================

A small nursery-rhyme story world about a maid, an intruding stone, bravery,
and a little twist at the end.

Seed-tale premise:
---
A tidy maid tends a nursery by the garden gate. One day a stone intrudes,
rolling in where it does not belong. The maid is uneasy at first, but she
bravely carries the stone away. The twist is that the stone was hiding a tiny
toy mouse underneath, and the nursery ends in laughter.

This world models:
- a maid with bravery and worry as emotional memes,
- a stone with size, weight, and a hidden thing beneath it,
- a setting where the stone can intrude,
- a gentle twist that changes the ending image.

The prose aims to feel like a nursery rhyme: short, musical, concrete, and
child-facing, while still being state-driven.
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

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    location: str = ""
    hidden: Optional[str] = None
    wearable: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type == "maid":
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.kind == "character":
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str
    image: str
    has_window: bool = False
    stone_can_intrude: bool = True


@dataclass
class Stone:
    label: str
    phrase: str
    size: str
    weight: str
    hidden: str
    can_glow: bool = False


@dataclass
class StoryParams:
    place: str
    stone: str
    maid_name: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting):
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()

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
        import copy
        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        w.fired = set(self.fired)
        return w


def _n(word: str) -> str:
    return "an" if word[:1].lower() in "aeiou" else "a"


SETTINGS = {
    "nursery": Setting(place="the nursery", image="soft quilts and a painted moon"),
    "kitchen": Setting(place="the kitchen", image="a warm pie-scented sill"),
    "garden_gate": Setting(place="the garden gate", image="a little gate with curling vines"),
    "playroom": Setting(place="the playroom", image="bright blocks and a rocking lamb"),
}

STONES = {
    "pebble": Stone(
        label="pebble",
        phrase="a small pebble",
        size="small",
        weight="light",
        hidden="a tiny toy mouse",
        can_glow=False,
    ),
    "gray_stone": Stone(
        label="stone",
        phrase="a round gray stone",
        size="round",
        weight="heavy",
        hidden="a tiny toy mouse",
        can_glow=False,
    ),
    "moonstone": Stone(
        label="moonstone",
        phrase="a pale moonstone",
        size="smooth",
        weight="heavy",
        hidden="a silver ribbon",
        can_glow=True,
    ),
}

MAID_NAMES = ["May", "Mina", "Lily", "Nell", "Wren", "Rose", "Ivy", "Poppy"]


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        if not setting.stone_can_intrude:
            continue
        for stone_id in STONES:
            combos.append((place, stone_id))
    return combos


def reasonableness_gate(place: str, stone_id: str) -> None:
    if place not in SETTINGS:
        raise StoryError(f"Unknown setting: {place}")
    if stone_id not in STONES:
        raise StoryError(f"Unknown stone: {stone_id}")
    if (place, stone_id) not in valid_combos():
        raise StoryError("This setting and stone do not make a sensible nursery-rhyme story.")


def build_world(params: StoryParams) -> World:
    setting = SETTINGS[params.place]
    stone = STONES[params.stone]
    world = World(setting)

    maid = world.add(Entity(
        id=params.maid_name,
        kind="character",
        type="maid",
        label="maid",
        phrase=f"little maid {params.maid_name}",
        location=setting.place,
        meters={"tidy": 1.0},
        memes={"worry": 0.0, "bravery": 0.0, "joy": 0.0},
    ))

    rock = world.add(Entity(
        id="stone",
        kind="thing",
        type=stone.label,
        label=stone.label,
        phrase=stone.phrase,
        location="outside",
        hidden=stone.hidden,
        meters={"weight": 2.0 if stone.weight == "heavy" else 1.0, "stillness": 1.0},
        memes={"mystery": 1.0},
    ))

    world.facts.update(maid=maid, stone=rock, setting=setting, stone_cfg=stone)
    return world


def intrude(world: World) -> None:
    maid: Entity = world.facts["maid"]
    stone: Entity = world.facts["stone"]
    setting: Setting = world.facts["setting"]
    stone.location = setting.place
    maid.memes["worry"] += 1.0
    world.say(
        f"In {setting.place}, by moonlight's gleam, "
        f"{maid.label.capitalize()} kept things neat and sweet."
    )
    world.say(
        f"Then in came {stone.phrase}, all cool and gray, "
        f"and intruded where it should not stay."
    )


def brave(world: World) -> None:
    maid: Entity = world.facts["maid"]
    stone: Entity = world.facts["stone"]
    maid.memes["bravery"] += 1.0
    maid.memes["worry"] = max(0.0, maid.memes["worry"] - 0.5)
    world.say(
        f"{maid.id} drew a breath, both deep and true, "
        f"and said, 'I know what I will do.'"
    )
    world.say(
        f"With steady hands and a gentle grin, "
        f"she tucked her sleeves and lifted in."
    )
    stone.location = "in her hands"


def twist(world: World) -> None:
    maid: Entity = world.facts["maid"]
    stone: Entity = world.facts["stone"]
    stone_cfg: Stone = world.facts["stone_cfg"]
    maid.memes["joy"] += 1.0
    world.say(
        f"But under the stone, as plain as day, "
        f"there hid a tiny toy mouse astray."
    )
    world.say(
        f"{maid.id} laughed, and the mouse peeped too, "
        f"for the stone had held a secret view."
    )
    if stone_cfg.can_glow:
        world.say(
            f"And when the lamp swung soft and slow, "
            f"the moonstone gave a milky glow."
        )
    world.say(
        f"She set the stone back safe and sound, "
        f"and the little mouse danced round and round."
    )
    stone.location = "on the sill"
    maid.memes["worry"] = 0.0


def tell(params: StoryParams) -> World:
    world = build_world(params)
    intrude(world)
    world.para()
    brave(world)
    world.para()
    twist(world)
    world.facts["resolved"] = True
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    maid = f["maid"]
    stone = f["stone_cfg"]
    setting = f["setting"]
    return [
        f'Write a short nursery-rhyme story about {maid.id}, a {stone.label}, and a surprise at {setting.place}.',
        f'Tell a gentle rhyme where a maid is brave enough to move {stone.phrase} after it intrudes into the room.',
        f'Create a child-friendly story with the words "stone", "intrude", and "maid", ending with a twist.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    maid: Entity = f["maid"]
    stone: Entity = f["stone"]
    setting: Setting = f["setting"]
    stone_cfg: Stone = f["stone_cfg"]
    return [
        QAItem(
            question=f"Who kept the {setting.place} neat at the start?",
            answer=f"The little maid {maid.id} kept {setting.place} neat and tidy.",
        ),
        QAItem(
            question=f"What intruded into {setting.place}?",
            answer=f"{stone_cfg.phrase.capitalize()} intruded into {setting.place}.",
        ),
        QAItem(
            question=f"What did {maid.id} do when the stone came in?",
            answer=f"{maid.id} was brave and carried the stone away with gentle hands.",
        ),
        QAItem(
            question=f"What was the twist at the end?",
            answer=f"There was a tiny toy mouse hiding under the stone.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a maid in an old story?",
            answer="A maid is a person who helps keep a place clean and tidy in a story.",
        ),
        QAItem(
            question="What is a stone?",
            answer="A stone is a hard piece of rock.",
        ),
        QAItem(
            question="What does brave mean?",
            answer="Brave means you do something even when you feel a little scared.",
        ),
        QAItem(
            question="What is a twist in a story?",
            answer="A twist is a surprise that changes what you expected to happen.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.location:
            bits.append(f"location={e.location}")
        if e.hidden:
            bits.append(f"hidden={e.hidden}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        lines.append(asp.fact("scene_image", sid, s.image))
    for tid, t in STONES.items():
        lines.append(asp.fact("stone", tid))
        lines.append(asp.fact("size", tid, t.size))
        lines.append(asp.fact("weight", tid, t.weight))
    lines.append(asp.fact("role", "maid"))
    return "\n".join(lines)


ASP_RULES = r"""
% A stone intrudes when it moves into the setting.
intrudes(S, P) :- stone(S), setting(P).

% Bravery is reasonable if the maid faces an intruding stone.
brave_story(P, S) :- intrudes(S, P), role(maid).

% A twist is part of the story when the stone hides something.
twist(S) :- stone(S).

#show intrudes/2.
#show brave_story/2.
#show twist/1.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show intrudes/2.\n#show brave_story/2.\n#show twist/1."))
    syms = set(str(a) for a in model)
    python_expected = set()
    for p in SETTINGS:
        for s in STONES:
            python_expected.add(f"intrudes({s},{p})")
            python_expected.add(f"brave_story({p},{s})")
            python_expected.add(f"twist({s})")
    if syms == python_expected:
        print(f"OK: ASP parity matched ({len(syms)} atoms).")
        return 0
    print("MISMATCH between ASP and Python expectations.")
    print("ASP:", sorted(syms))
    print("PY :", sorted(python_expected))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Nursery-rhyme storyworld: a maid, an intruding stone, bravery, and a twist."
    )
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--stone", choices=STONES)
    ap.add_argument("--maid-name", choices=MAID_NAMES)
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
    combos = valid_combos()
    if args.place:
        combos = [c for c in combos if c[0] == args.place]
    if args.stone:
        combos = [c for c in combos if c[1] == args.stone]
    if not combos:
        raise StoryError("No valid story combination matches those choices.")
    place, stone = rng.choice(combos)
    maid_name = args.maid_name or rng.choice(MAID_NAMES)
    return StoryParams(place=place, stone=stone, maid_name=maid_name)


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
    StoryParams(place="nursery", stone="gray_stone", maid_name="May"),
    StoryParams(place="playroom", stone="pebble", maid_name="Nell"),
    StoryParams(place="garden_gate", stone="moonstone", maid_name="Wren"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show intrudes/2.\n#show brave_story/2.\n#show twist/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import storyworlds.asp as asp
        model = asp.one_model(asp_program("#show intrudes/2.\n#show brave_story/2.\n#show twist/1."))
        for atom in model:
            print(atom)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for p in CURATED:
            samples.append(generate(p))
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.maid_name}: {p.stone} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
