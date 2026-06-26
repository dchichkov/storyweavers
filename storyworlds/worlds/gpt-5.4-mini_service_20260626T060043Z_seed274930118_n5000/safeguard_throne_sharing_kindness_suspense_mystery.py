#!/usr/bin/env python3
"""
Standalone storyworld: safeguard throne sharing kindness suspense mystery.

A small mystery domain about a child-like keeper, a throne, and a careful act
of sharing that restores kindness while a safeguard keeps the ending safe.
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
class Chamber:
    name: str = "the moonlit chamber"
    mood: str = "quiet"
    has_candlelight: bool = True
    clues: list[str] = field(default_factory=list)


@dataclass
class Character:
    name: str
    role: str
    kind: str = "character"
    meters: dict[str, float] = field(default_factory=lambda: {"distance": 0.0})
    memes: dict[str, float] = field(default_factory=lambda: {"kindness": 0.0, "suspense": 0.0, "trust": 0.0})

    def subj(self) -> str:
        return self.name

    def poss(self) -> str:
        return f"{self.name}'s"


@dataclass
class Object:
    name: str
    label: str
    kind: str = "thing"
    meters: dict[str, float] = field(default_factory=lambda: {"polish": 0.0, "dust": 0.0})
    memes: dict[str, float] = field(default_factory=lambda: {"importance": 0.0})
    held_by: Optional[str] = None
    safeguarded: bool = False


@dataclass
class StoryParams:
    setting: str = "throne room"
    keeper: str = "Mira"
    helper: str = "Noel"
    seed: Optional[int] = None


@dataclass
class World:
    chamber: Chamber
    keeper: Character
    helper: Character
    throne: Object
    safeguard: Object
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


SETTINGS = {
    "throne room": Chamber(name="the throne room", mood="quiet", has_candlelight=True),
    "stone hall": Chamber(name="the stone hall", mood="echoing", has_candlelight=False),
    "amber chamber": Chamber(name="the amber chamber", mood="dim", has_candlelight=True),
}

NAMES = ["Mira", "Noel", "Iris", "Ari", "Lina", "Soren", "Tavi", "Luca"]
HELPERS = ["Noel", "Iris", "Ari", "Lina", "Soren", "Tavi", "Luca", "Mara"]


def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("place", "throne_room"),
        asp.fact("object", "throne"),
        asp.fact("object", "safeguard"),
        asp.fact("theme", "sharing"),
        asp.fact("theme", "kindness"),
        asp.fact("theme", "suspense"),
        asp.fact("style", "mystery"),
        asp.fact("goal", "safeguard"),
    ]
    return "\n".join(lines)


ASP_RULES = r"""
#show compatible/1.
compatible(throne_room) :- place(throne_room), object(throne), goal(safeguard).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def reasonableness_gate(params: StoryParams) -> None:
    if not params.keeper.strip() or not params.helper.strip():
        raise StoryError("The keeper and helper must have names.")
    if params.keeper == params.helper:
        raise StoryError("The keeper and helper must be different people.")
    if "throne" not in params.setting.lower():
        raise StoryError("This world needs a throne room or a throne-like setting.")


def build_world(params: StoryParams) -> World:
    chamber = SETTINGS.get(params.setting, Chamber(name=f"the {params.setting}", mood="quiet"))
    keeper = Character(name=params.keeper, role="keeper")
    helper = Character(name=params.helper, role="helper")
    throne = Object(name="throne", label="throne")
    safeguard = Object(name="safeguard", label="small safeguard")
    return World(chamber=chamber, keeper=keeper, helper=helper, throne=throne, safeguard=safeguard)


def narrate(world: World) -> None:
    k = world.keeper
    h = world.helper
    t = world.throne
    s = world.safeguard
    chamber = world.chamber

    world.say(f"In {chamber.name}, {k.name} watched over a tall throne that everyone kept talking about.")
    world.say(f"The room was quiet enough to make every small footstep feel like a clue.")
    world.say(f"{k.name} noticed that the throne looked lonely, even though it sat in the middle of the chamber like a secret.")

    world.para()
    k.memes["suspense"] += 1
    h.memes["suspense"] += 1
    chamber.clues.append("a ribbon on the throne arm")
    t.meters["dust"] += 1
    world.say(f"Then {h.name} arrived with a careful smile and a ribbon tucked behind {h.name.lower()}'s hand.")
    world.say(f'"I found something strange," {h.name} whispered. "The throne is missing a gentle touch, and the room feels like it is waiting for a decision."')
    world.say(f"{k.name} leaned closer and saw the ribbon, the dust, and a tiny mark on the polished seat.")
    world.say(f"That made the mystery feel even deeper.")

    world.para()
    k.memes["kindness"] += 1
    h.memes["kindness"] += 1
    k.memes["trust"] += 1
    h.memes["trust"] += 1
    s.safeguarded = True
    s.held_by = k.name
    t.held_by = "the room"
    t.meters["dust"] = 0.0
    t.meters["polish"] += 1
    chamber.clues.append("the safeguard was a soft cloth and a shared promise")
    world.say(f"At last, {k.name} understood the answer: the throne did not need guarding from people, only from carelessness.")
    world.say(f"{k.name} and {h.name} shared the small safeguard, wiped the seat clean, and put the ribbon back where it belonged.")
    world.say(f"Because they worked together kindly, the throne shone again, and the mystery ended with a calm, bright room.")
    world.say(f"{k.name} sat beside the throne instead of on it, and {h.name} smiled because sharing had kept everything safe.")

    world.facts.update(
        keeper=k,
        helper=h,
        throne=t,
        safeguard=s,
        chamber=chamber,
        resolved=True,
        clues=list(chamber.clues),
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a child-friendly mystery story about a {f["chamber"].name} with a throne, a safeguard, and a kind sharing choice.',
        f"Tell a suspenseful story where {f['keeper'].name} and {f['helper'].name} solve a small problem with the throne by being kind.",
        f'Write a gentle mystery that includes the words "safeguard", "throne", "sharing", and "kindness".',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    k = f["keeper"].name
    h = f["helper"].name
    chamber = f["chamber"].name
    return [
        QAItem(
            question=f"Where does the mystery happen?",
            answer=f"The mystery happens in {chamber}, where the throne stands in the middle of the room.",
        ),
        QAItem(
            question=f"What did {k} and {h} do to solve the problem?",
            answer=f"They shared the small safeguard, cleaned the throne, and put the ribbon back where it belonged.",
        ),
        QAItem(
            question=f"Why did the room feel suspenseful at first?",
            answer="It felt suspenseful because the throne had a strange mark, a ribbon was out of place, and nobody knew the reason yet.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a safeguard?",
            answer="A safeguard is something that helps keep people or important things safe.",
        ),
        QAItem(
            question="What does sharing mean?",
            answer="Sharing means using something together or giving some of it to someone else so everyone can help.",
        ),
        QAItem(
            question="What is kindness?",
            answer="Kindness means being gentle, helpful, and caring about other people.",
        ),
        QAItem(
            question="What is suspense in a story?",
            answer="Suspense is the feeling of wondering what will happen next when something is not explained yet.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = []
    lines.append("== Generation prompts ==")
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story Q&A ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World Q&A ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    t = world.throne
    s = world.safeguard
    lines = ["--- world trace ---"]
    lines.append(f"chamber={world.chamber.name} mood={world.chamber.mood} candlelight={world.chamber.has_candlelight}")
    lines.append(f"keeper={world.keeper.name} memes={world.keeper.memes}")
    lines.append(f"helper={world.helper.name} memes={world.helper.memes}")
    lines.append(f"throne dust={t.meters['dust']} polish={t.meters['polish']} held_by={t.held_by}")
    lines.append(f"safeguard held_by={s.held_by} safeguarded={s.safeguarded}")
    lines.append(f"clues={world.chamber.clues}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Story world: safeguard, throne, sharing, kindness, suspense, mystery.")
    ap.add_argument("--setting", choices=sorted(SETTINGS), default="throne room")
    ap.add_argument("--keeper")
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    keeper = args.keeper or rng.choice(NAMES)
    helper = args.helper or rng.choice([n for n in HELPERS if n != keeper])
    params = StoryParams(setting=args.setting, keeper=keeper, helper=helper, seed=args.seed)
    reasonableness_gate(params)
    return params


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    narrate(world)
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


def verify() -> int:
    try:
        import asp  # lazy import
    except Exception as e:
        print(f"ASP unavailable: {e}")
        return 1
    program = asp_program("#show compatible/1.")
    model = asp.one_model(program)
    atoms = sorted(set(asp.atoms(model, "compatible")))
    expected = [("throne_room",)]
    if atoms != expected:
        print("MISMATCH between ASP and Python gate:")
        print("  asp:", atoms)
        print("  py :", expected)
        return 1
    sample = generate(StoryParams())
    if not sample.story or "throne" not in sample.story.lower():
        print("Story generation failed.")
        return 1
    print("OK: ASP parity and story generation verified.")
    return 0


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show compatible/1."))
        return
    if args.verify:
        sys.exit(verify())

    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show compatible/1."))
        print(f"{len(asp.atoms(model, 'compatible'))} compatible setting(s):")
        for (setting,) in sorted(set(asp.atoms(model, "compatible"))):
            print(f"  {setting}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    rng = random.Random(base_seed)

    samples: list[StorySample] = []
    if args.all:
        for name1 in ["Mira", "Iris", "Ari"]:
            for name2 in ["Noel", "Luca", "Mara"]:
                if name1 == name2:
                    continue
                samples.append(generate(StoryParams(setting="throne room", keeper=name1, helper=name2, seed=base_seed)))
                if len(samples) >= 5:
                    break
            if len(samples) >= 5:
                break
    else:
        for i in range(args.n):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))

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
