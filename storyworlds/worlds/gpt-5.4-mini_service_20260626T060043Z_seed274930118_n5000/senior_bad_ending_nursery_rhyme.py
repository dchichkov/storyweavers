#!/usr/bin/env python3
"""
A small storyworld for a nursery-rhyme-style senior tale with a gentle but
bad ending.

Seed premise:
- A senior wants a simple evening delight.
- A small helper or object could make it safer.
- The ending does not fully resolve; the wanted thing is lost or ruined.

The world is kept tiny on purpose: one character, one fragile prize, one risky
setting, and one missed chance that leads to a sad final image.
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


# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    region: str = ""
    plural: bool = False
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for k in ("wet", "cold", "tired", "lost", "dirty", "broken"):
            self.meters.setdefault(k, 0.0)
        for k in ("hope", "joy", "worry", "lonely", "regret"):
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"man", "father", "grandfather", "senior"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in {"woman", "mother", "grandmother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    weather: str
    risk: str
    afford: str


@dataclass
class Prize:
    label: str
    phrase: str
    type: str
    region: str
    plural: bool = False


@dataclass
class StoryParams:
    setting: str
    prize: str
    name: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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

        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.facts = dict(self.facts)
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "hill": Setting(place="the hill", weather="windy", risk="wind", afford="sing"),
    "porch": Setting(place="the porch", weather="rainy", risk="rain", afford="rock"),
    "garden": Setting(place="the garden", weather="breezy", risk="mud", afford="stroll"),
}

PRIZES = {
    "tea": Prize(label="tea", phrase="a warm cup of tea", type="cup", region="hands"),
    "hat": Prize(label="hat", phrase="a neat little hat", type="hat", region="head"),
    "cake": Prize(label="cake", phrase="a tiny jam cake", type="cake", region="hands"),
}

NAMES = ["Mr. Finn", "Old Ben", "Nora", "Mabel", "Eli", "June"]


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------

def prize_at_risk(setting: Setting, prize: Prize) -> bool:
    return setting.risk in {"wind", "rain", "mud"} and prize.region in {"hands", "head"}


def select_fix(setting: Setting, prize: Prize) -> Optional[str]:
    if setting.risk == "wind" and prize.region == "head":
        return "a ribbon"
    if setting.risk == "rain" and prize.region == "hands":
        return "a dry tray"
    return None


def explain_rejection(setting: Setting, prize: Prize) -> str:
    return (
        f"(No story: the chosen setting and prize do not make a fair little problem. "
        f"The {setting.place} risk is {setting.risk}, but the {prize.label} does not need that kind of care.)"
    )


# ---------------------------------------------------------------------------
# Narration helpers
# ---------------------------------------------------------------------------

def intro(world: World, senior: Entity, prize: Entity) -> None:
    world.say(
        f"On a little wind-kissed day, {senior.id} was a senior with a soft smile and a slow, steady tread."
    )
    world.say(
        f"{senior.pronoun('possessive').capitalize()} heart was bright, and {senior.id} loved {prize.phrase} more than a sleepy tune."
    )


def setup(world: World, senior: Entity, prize: Entity) -> None:
    world.say(
        f"{senior.id} set out for {world.setting.place}, where the {world.setting.risk} could tug at small things."
    )
    prize.worn_by = senior.id
    world.say(
        f"With {prize.it()} in hand, {senior.id} hummed a tiny rhyme and went along."
    )


def turn(world: World, senior: Entity, prize: Entity) -> None:
    if world.setting.weather == "windy" and prize.region == "head":
        senior.memes["worry"] += 1
        prize.meters["lost"] += 1
        world.say(
            f"Then came a gusty twirl! Off flew {senior.pronoun('possessive')} {prize.label}, so light and fast."
        )
    elif world.setting.weather == "rainy" and prize.region == "hands":
        senior.memes["worry"] += 1
        prize.meters["wet"] += 1
        world.say(
            f"Then came the rain-a-brain, and {senior.pronoun('possessive')} {prize.label} grew soggy and plain."
        )
    else:
        senior.memes["worry"] += 1
        world.say(
            f"A little trouble came, as it often does in a nursery rhyme, and {senior.id} could not keep up with it."
        )


def bad_ending(world: World, senior: Entity, prize: Entity) -> None:
    senior.memes["hope"] = 0
    senior.memes["regret"] += 1
    senior.memes["lonely"] += 1
    if prize.meters["lost"] >= THRESHOLD:
        world.say(
            f"{senior.id} searched and searched, but the {prize.label} never came back."
        )
        world.say(
            f"So {senior.id} went home with empty hands, and the evening felt very quiet indeed."
        )
    elif prize.meters["wet"] >= THRESHOLD:
        world.say(
            f"{senior.id} tried to dry {prize.it()}, but it stayed wet and sad."
        )
        world.say(
            f"The little treat was no treat at all, and {senior.id} sat alone beside the dimmest lamp."
        )
    else:
        world.say(
            f"Nothing was mended in the end, and the small joy slipped away like a pebble in the grass."
        )


# ---------------------------------------------------------------------------
# Story assembly
# ---------------------------------------------------------------------------

def tell(setting: Setting, prize_cfg: Prize, name: str) -> World:
    world = World(setting)
    senior = world.add(Entity(id=name, kind="character", type="senior"))
    prize = world.add(
        Entity(
            id="prize",
            type=prize_cfg.type,
            label=prize_cfg.label,
            phrase=prize_cfg.phrase,
            owner=senior.id,
            region=prize_cfg.region,
        )
    )

    intro(world, senior, prize)
    world.para()
    setup(world, senior, prize)
    world.para()
    turn(world, senior, prize)
    world.para()
    bad_ending(world, senior, prize)

    world.facts.update(
        senior=senior,
        prize=prize,
        setting=setting,
        bad_end=True,
    )
    return world


# ---------------------------------------------------------------------------
# QA and prompts
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    senior = f["senior"]
    prize = f["prize"]
    setting = f["setting"]
    return [
        f'Write a short nursery-rhyme story about a senior named {senior.id} at {setting.place} with {prize.phrase}.',
        f"Tell a gentle rhyme where {senior.id} wants {prize.phrase}, but the {setting.risk} spoils the plan.",
        f'Write a small story for a child that includes "{senior.id}" and ends sadly when {prize.label} is lost or ruined.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    senior = f["senior"]
    prize = f["prize"]
    setting = f["setting"]
    return [
        QAItem(
            question=f"Who is the story about?",
            answer=f"It is about {senior.id}, a senior with a gentle heart.",
        ),
        QAItem(
            question=f"What did {senior.id} want to carry at {setting.place}?",
            answer=f"{senior.id} wanted to carry {prize.phrase}.",
        ),
        QAItem(
            question=f"What went wrong in the end?",
            answer=f"The {setting.risk} made the plan go badly, and the {prize.label} was lost or ruined.",
        ),
        QAItem(
            question=f"Did the story end happily?",
            answer="No. It ended sadly, with the little joy not being fixed.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    setting = f["setting"]
    if setting.risk == "wind":
        return [
            QAItem(
                question="What can wind do to a light hat?",
                answer="Wind can lift a light hat off a person's head and blow it away.",
            )
        ]
    if setting.risk == "rain":
        return [
            QAItem(
                question="What can rain do to something held in your hands?",
                answer="Rain can make a thing wet and soggy if it is not protected.",
            )
        ]
    return [
        QAItem(
            question="What can mud do to careful shoes?",
            answer="Mud can stick to things and make them messy.",
        )
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for p in sample.prompts:
        lines.append(f"- {p}")
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


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
setting_risky(S) :- setting(S), risk(S, wind).
setting_risky(S) :- setting(S), risk(S, rain).
setting_risky(S) :- setting(S), risk(S, mud).

prize_at_risk(S, P) :- setting_risky(S), prize(P), risk_region(S, R), worn_on(P, R).

bad_outcome(S, P) :- prize_at_risk(S, P), no_fix(S, P).
bad_outcome(S, P) :- setting(S), prize(P), lost_possible(S, P).

valid_story(S, P) :- setting(S), prize(P), prize_at_risk(S, P), bad_outcome(S, P).
"""

def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        lines.append(asp.fact("risk", sid, s.risk))
        lines.append(asp.fact("risk_region", sid, "head" if s.risk == "wind" else "hands" if s.risk == "rain" else "hands"))
        lines.append(asp.fact("lost_possible", sid, "prize"))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("worn_on", pid, p.region))
        lines.append(asp.fact("no_fix", "dummy", pid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp

    program = asp_program("#show valid_story/2.")
    model = asp.one_model(program)
    asp_set = set(asp.atoms(model, "valid_story"))
    py_set = set()
    for sid, s in SETTINGS.items():
        for pid, p in PRIZES.items():
            if prize_at_risk(s, p) and select_fix(s, p) is None:
                py_set.add((sid, pid))
    if asp_set == py_set:
        print(f"OK: clingo gate matches Python gate ({len(py_set)} combos).")
        return 0
    print("MISMATCH between ASP and Python gates.")
    if asp_set - py_set:
        print("only in ASP:", sorted(asp_set - py_set))
    if py_set - asp_set:
        print("only in Python:", sorted(py_set - asp_set))
    return 1


# ---------------------------------------------------------------------------
# Params and generation
# ---------------------------------------------------------------------------

def valid_combos() -> list[tuple[str, str]]:
    out = []
    for sid, s in SETTINGS.items():
        for pid, p in PRIZES.items():
            if prize_at_risk(s, p) and select_fix(s, p) is None:
                out.append((sid, pid))
    return out


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny nursery-rhyme storyworld about a senior and a bad ending.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--name", choices=NAMES)
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
    if args.setting and args.prize:
        if not prize_at_risk(SETTINGS[args.setting], PRIZES[args.prize]):
            raise StoryError(explain_rejection(SETTINGS[args.setting], PRIZES[args.prize]))
        if select_fix(SETTINGS[args.setting], PRIZES[args.prize]) is None:
            raise StoryError(explain_rejection(SETTINGS[args.setting], PRIZES[args.prize]))
    combos = [
        (sid, pid) for sid, pid in valid_combos()
        if (args.setting is None or sid == args.setting)
        and (args.prize is None or pid == args.prize)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, prize = rng.choice(sorted(combos))
    name = args.name or rng.choice(NAMES)
    return StoryParams(setting=setting, prize=prize, name=name)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], PRIZES[params.prize], params.name)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
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


CURATED = [
    StoryParams(setting="hill", prize="hat", name="Old Ben"),
    StoryParams(setting="porch", prize="tea", name="Nora"),
    StoryParams(setting="garden", prize="cake", name="Mabel"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid_story/2."))
        print(sorted(set(asp.atoms(model, "valid_story"))))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
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
