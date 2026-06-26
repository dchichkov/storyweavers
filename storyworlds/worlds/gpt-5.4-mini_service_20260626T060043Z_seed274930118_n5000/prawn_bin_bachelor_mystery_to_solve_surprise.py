#!/usr/bin/env python3
"""
A small heartwarming storyworld about a bachelor, a prawn, and a bin mystery.

The seed tale:
---
A bachelor named Owen lived alone in a tidy little flat. One evening, he opened
the kitchen bin to throw away a peel and found a cooked prawn wrapped in a paper
napkin. He wondered who had left it there. He checked the note on the fridge and
looked around the hallway, trying to solve the mystery.

Then his neighbor, a little girl named Pip, knocked on the door with a grin.
She had left the prawn as a surprise from the building potluck, because she knew
Owen had missed dinner after a long day. Owen laughed, thanked her, and warmed
the prawn into a small supper. The mystery turned into a kind surprise, and the
flat felt less lonely after that.

World model:
---
- Physical meters track things like smell, warmth, tidiness, and fullness.
- Emotional memes track things like curiosity, loneliness, relief, and gratitude.
- A found prawn in the bin raises curiosity; a note, knock, and reveal resolve it.
- A surprise gift can brighten the bachelor's evening and soften loneliness.

This world is intentionally small, concrete, and plausible, so every sample reads
like a complete miniature story with a turn and a warm ending.
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
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class Setting:
    place: str = "a small flat"
    city: str = "Riverton"
    indoors: bool = True


@dataclass
class Mystery:
    label: str
    clue_item: str
    clue_place: str
    reveal_source: str
    solved_by: str
    surprise_kind: str


@dataclass
class StoryParams:
    setting: str
    mystery: str
    hero_name: str
    helper_name: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.lines: list[str] = []
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.lines.append(text)

    def render(self) -> str:
        return " ".join(self.lines)


SETTINGS = {
    "flat": Setting(place="a small flat", city="Riverton", indoors=True),
    "house": Setting(place="a little house", city="Riverton", indoors=True),
    "apartment": Setting(place="a tidy apartment", city="Brindle", indoors=True),
}

MYSTERIES = {
    "prawn_bin": Mystery(
        label="the prawn in the bin",
        clue_item="prawn",
        clue_place="bin",
        reveal_source="neighbor surprise",
        solved_by="a knock at the door",
        surprise_kind="a kind surprise",
    ),
    "note_missing": Mystery(
        label="the missing note",
        clue_item="note",
        clue_place="fridge",
        reveal_source="a sticky note",
        solved_by="a warm message",
        surprise_kind="a helpful surprise",
    ),
}

HEROES = ["Owen", "Miles", "Noah", "Eli", "Caleb"]
HELPERS = ["Pip", "Mina", "June", "Luna", "Ruby"]


@dataclass
class WorldState:
    hero: Entity
    helper: Entity
    setting: Setting
    mystery: Mystery
    bin_entity: Entity
    prawn: Entity
    memo: Entity
    solved: bool = False
    surprise_delivered: bool = False
    curiosity_spike: bool = False


def build_world(params: StoryParams) -> WorldState:
    setting = SETTINGS[params.setting]
    mystery = MYSTERIES[params.mystery]
    world = World(setting)

    hero = world.add(Entity(
        id=params.hero_name,
        kind="character",
        type="bachelor",
        label="the bachelor",
        meters={"hunger": 0.2, "tidiness": 0.8, "warmth": 0.4},
        memes={"loneliness": 0.7, "curiosity": 0.2, "gratitude": 0.0, "relief": 0.0},
    ))
    helper = world.add(Entity(
        id=params.helper_name,
        kind="character",
        type="neighbor",
        label="the neighbor",
        meters={"cheer": 0.8},
        memes={"kindness": 0.8, "joy": 0.7},
    ))
    bin_entity = world.add(Entity(
        id="bin",
        kind="thing",
        type="bin",
        label="the kitchen bin",
        meters={"smell": 0.1, "mess": 0.2},
    ))
    prawn = world.add(Entity(
        id="prawn",
        kind="thing",
        type="prawn",
        label="a cooked prawn",
        owner=params.helper_name,
        meters={"warmth": 0.3, "freshness": 0.7},
    ))
    memo = world.add(Entity(
        id="memo",
        kind="thing",
        type="note",
        label="a folded paper napkin",
        owner=params.helper_name,
    ))

    return WorldState(hero, helper, setting, mystery, bin_entity, prawn, memo)


def line_intro(state: WorldState, world: World) -> None:
    world.say(
        f"{state.hero.id} was a bachelor living in {state.setting.place}, and he kept the place neat because it made the evenings feel calm."
    )
    world.say(
        f"He was a little lonely sometimes, but he liked quiet meals, clean counters, and the warm hum of his kettle."
    )


def line_inciting(state: WorldState, world: World) -> None:
    state.hero.memes["curiosity"] += 0.8
    state.hero.meters["hunger"] += 0.2
    state.bin_entity.meters["mess"] += 0.1
    world.say(
        f"One evening, he opened {state.mystery.clue_place} to toss away a peel and found {state.prawn.label} tucked inside."
    )
    world.say(
        f"That was odd enough to make him pause, and soon he was asking who would leave a prawn in the bin."
    )


def line_investigate(state: WorldState, world: World) -> None:
    world.say(
        f"He checked the hallway, peeked at the fridge, and even looked for a note, hoping the mystery would solve itself."
    )
    state.hero.memes["curiosity"] += 0.5
    if state.hero.memes["curiosity"] >= THRESHOLD:
        state.curiosity_spike = True
        world.say(
            f"The more he looked, the more the little puzzle tugged at him, because the prawn seemed too thoughtful to be an accident."
        )


def line_surprise(state: WorldState, world: World) -> None:
    state.surprise_delivered = True
    state.solved = True
    state.hero.memes["relief"] += 0.9
    state.hero.memes["gratitude"] += 0.8
    state.hero.memes["loneliness"] -= 0.3
    state.helper.memes["kindness"] += 0.1
    world.say(
        f"Then there was a knock at the door, and {state.helper.id} stood there smiling with a tiny grin, holding the missing note."
    )
    world.say(
        f"She explained that she had left {state.prawn.label} as {state.mystery.surprise_kind} from the building potluck, because she knew he had missed dinner after a long day."
    )


def line_resolution(state: WorldState, world: World) -> None:
    state.prawn.meters["warmth"] += 0.6
    state.hero.meters["hunger"] = 0.0
    world.say(
        f"{state.hero.id} laughed, thanked her, and warmed {state.prawn.label} into a small supper."
    )
    world.say(
        f"What had started as a bin mystery became a gentle little evening, and the flat felt bright and friendly by the time he sat down to eat."
    )


def tell(params: StoryParams) -> WorldState:
    world = World(SETTINGS[params.setting])
    state = build_world(params)
    line_intro(state, world)
    world.say("")
    line_inciting(state, world)
    line_investigate(state, world)
    line_surprise(state, world)
    line_resolution(state, world)

    world.facts.update(
        hero=state.hero,
        helper=state.helper,
        setting=state.setting,
        mystery=state.mystery,
        solved=state.solved,
        surprise=state.surprise_delivered,
    )
    return state, world


def generation_prompts(state: WorldState) -> list[str]:
    return [
        "Write a heartwarming story about a bachelor who finds a prawn in the bin and wonders who left it there.",
        f"Tell a short mystery story where {state.hero.id} solves the puzzle of {state.mystery.label} with a surprise from {state.helper.id}.",
        "Write a gentle, child-friendly story that begins with a puzzling prawn and ends with a warm dinner and a happy surprise.",
    ]


def story_qa(state: WorldState) -> list[QAItem]:
    return [
        QAItem(
            question=f"Why did {state.hero.id} feel curious when he found the prawn in the bin?",
            answer=f"He felt curious because a cooked prawn in the bin was unusual, so he wanted to know who had left it there and why.",
        ),
        QAItem(
            question=f"Who solved the mystery for {state.hero.id}?",
            answer=f"{state.helper.id} solved it by coming to the door and explaining that the prawn was a surprise from the building potluck.",
        ),
        QAItem(
            question=f"What changed after the surprise was explained?",
            answer=f"{state.hero.id} felt relieved and grateful, and the lonely evening turned into a warm supper in a friendlier flat.",
        ),
    ]


def world_qa(state: WorldState) -> list[QAItem]:
    return [
        QAItem(
            question="What is a prawn?",
            answer="A prawn is a small shellfish that people can cook and eat.",
        ),
        QAItem(
            question="What is a bin used for?",
            answer="A bin is used for throwing away rubbish so a room stays tidy.",
        ),
        QAItem(
            question="What does a surprise do in a story?",
            answer="A surprise can change what the characters think is happening and make the story feel warmer or more exciting.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== story questions ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== world questions ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def dump_trace(state: WorldState) -> str:
    lines = ["--- world trace ---"]
    for ent in [state.hero, state.helper, state.bin_entity, state.prawn, state.memo]:
        meters = {k: round(v, 3) for k, v in ent.meters.items() if v}
        memes = {k: round(v, 3) for k, v in ent.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {ent.id} ({ent.type}) " + " ".join(bits))
    lines.append(f"  solved={state.solved} surprise={state.surprise_delivered}")
    return "\n".join(lines)


def valid_combos() -> list[tuple[str, str]]:
    return [(setting, mystery) for setting in SETTINGS for mystery in MYSTERIES]


@dataclass
class StoryConfig:
    setting: str
    mystery: str
    hero_name: str
    helper_name: str
    seed: Optional[int] = None


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if s.indoors:
            lines.append(asp.fact("indoors", sid))
    for mid, m in MYSTERIES.items():
        lines.append(asp.fact("mystery", mid))
        lines.append(asp.fact("clue_item", mid, m.clue_item))
        lines.append(asp.fact("clue_place", mid, m.clue_place))
        lines.append(asp.fact("surprise_kind", mid, m.surprise_kind))
    return "\n".join(lines)


ASP_RULES = r"""
valid(S, M) :- setting(S), mystery(M).
#show valid/2.
"""


def asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if py == asp_set:
        print(f"OK: ASP matches Python ({len(py)} combos).")
        return 0
    print("MISMATCH:")
    if py - asp_set:
        print(" only python:", sorted(py - asp_set))
    if asp_set - py:
        print(" only asp:", sorted(asp_set - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Heartwarming mystery storyworld about a bachelor, a prawn, and a bin.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--name")
    ap.add_argument("--helper")
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryConfig:
    combos = valid_combos()
    if args.setting and args.mystery:
        if (args.setting, args.mystery) not in combos:
            raise StoryError("That setting and mystery do not fit this small world.")
    setting, mystery = args.setting or rng.choice(sorted(SETTINGS)), args.mystery or rng.choice(sorted(MYSTERIES))
    hero = args.name or rng.choice(HEROES)
    helper = args.helper or rng.choice([h for h in HELPERS if h != hero])
    return StoryConfig(setting=setting, mystery=mystery, hero_name=hero, helper_name=helper)


def generate(params: StoryConfig) -> StorySample:
    state, world = tell(StoryParams(**params.__dict__))
    return StorySample(
        params=StoryParams(**params.__dict__),
        story=world.render(),
        prompts=generation_prompts(state),
        story_qa=story_qa(state),
        world_qa=world_qa(state),
        world=state,
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
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} valid combos:")
        for c in combos:
            print(c)
        return

    if args.all:
        samples = [
            generate(StoryConfig(setting=s, mystery=m, hero_name="Owen", helper_name="Pip"))
            for s, m in valid_combos()
        ]
    else:
        base_seed = args.seed if args.seed is not None else random.randrange(2**31)
        samples = []
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            cfg = resolve_params(args, random.Random(base_seed + i))
            i += 1
            key = (cfg.setting, cfg.mystery, cfg.hero_name, cfg.helper_name)
            if key in seen:
                continue
            seen.add(key)
            samples.append(generate(cfg))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for idx, sample in enumerate(samples):
        if len(samples) > 1:
            print(f"### variant {idx + 1}")
        emit(sample, trace=args.trace, qa=args.qa)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
