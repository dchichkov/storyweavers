#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/tray_yip_hose_lesson_learned_transformation_magic.py
==============================================================================================================

A small comedy storyworld about a tray, a yippy little dog, and a hose with a
surprising magic trick. The story is state-driven: a careful setup, a noisy
problem, a magical transformation, and a lesson learned at the end.
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
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"wet": 0.0, "shiny": 0.0, "broken": 0.0}
        if not self.memes:
            self.memes = {"joy": 0.0, "worry": 0.0, "pride": 0.0, "lesson": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str
    indoors: bool
    affords: set[str] = field(default_factory=set)


@dataclass
class SceneItem:
    label: str
    phrase: str
    region: str = "hands"
    fragile: bool = False


@dataclass
class Trick:
    id: str
    verb: str
    gerund: str
    mess: str
    weather_word: str
    zone: set[str]
    magic_twist: str


@dataclass
class StoryParams:
    place: str
    trick: str
    prize: str
    name: str
    gender: str
    parent: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}

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
        c = World(self.setting)
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = dict(self.facts)
        return c


SETTINGS = {
    "backyard": Setting("the backyard", False, {"hose"}),
    "garden": Setting("the garden", False, {"hose"}),
    "patio": Setting("the patio", False, {"hose"}),
}

TRICKS = {
    "hose": Trick(
        id="hose",
        verb="spray the hose",
        gerund="spraying the hose",
        mess="wet",
        weather_word="splashy",
        zone={"hands", "feet", "shirt"},
        magic_twist="the hose popped like a magic wand and turned the tray into a tiny floaty stage",
    ),
    "magic": Trick(
        id="magic",
        verb="wave a magic wand",
        gerund="waving a magic wand",
        mess="shiny",
        weather_word="sparkly",
        zone={"hands", "shirt"},
        magic_twist="the wand blinked and turned the tray into a glittery kite tray",
    ),
}

PRIZES = {
    "tray": SceneItem("tray", "a shiny snack tray", "hands", False),
    "cookies": SceneItem("cookies", "warm cookies on a tray", "hands", True),
    "paper": SceneItem("paper", "a paper tray", "hands", True),
}

NAMES = {
    "girl": ["Mia", "Zoe", "Lily", "Ava", "Nina"],
    "boy": ["Leo", "Finn", "Max", "Owen", "Theo"],
}
TRAITS = ["silly", "curious", "cheerful", "bouncy", "goofy"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for trick_id in setting.affords:
            for prize_id, prize in PRIZES.items():
                trick = TRICKS[trick_id]
                if prize.region in trick.zone:
                    combos.append((place, trick_id, prize_id))
    return combos


def explain_rejection(trick: Trick, prize: SceneItem) -> str:
    return (
        f"(No story: {trick.gerund} would not reasonably affect {prize.label}. "
        f"Try a prize that sits in the splash zone.)"
    )


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Comedy world: tray, yip, hose, and a lesson learned.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--trick", choices=TRICKS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name")
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
    if args.trick and args.prize:
        trick, prize = TRICKS[args.trick], PRIZES[args.prize]
        if prize.region not in trick.zone:
            raise StoryError(explain_rejection(trick, prize))
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.trick is None or c[1] == args.trick)
              and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, trick, prize = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(NAMES[gender])
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(place=place, trick=trick, prize=prize, name=name, gender=gender, parent=parent)


def _do_trick(world: World, hero: Entity, trick: Trick) -> None:
    hero.meters[trick.mess] = hero.meters.get(trick.mess, 0.0) + 1.0
    hero.memes["joy"] += 1.0


def _magic_transform(world: World, hero: Entity, tray: Entity, trick: Trick) -> None:
    sig = ("magic", trick.id, tray.id)
    if sig in world.fired:
        return
    world.fired.add(sig)
    tray.meters["shiny"] += 1.0
    tray.memes["pride"] += 1.0
    hero.memes["lesson"] += 1.0
    world.say(f"{trick.magic_twist}.")


def tell(world: World, params: StoryParams) -> World:
    trick = TRICKS[params.trick]
    prize = PRIZES[params.prize]
    hero = world.add(Entity(id=params.name, kind="character", type=params.gender))
    parent = world.add(Entity(id="parent", kind="character", type=params.parent))
    tray = world.add(Entity(id="tray", label="tray", phrase=prize.phrase, owner=hero.id, caretaker=parent.id))

    world.say(
        f"{hero.id} was a {random.choice(TRAITS)} little {hero.type} who loved carrying snacks on a tray."
    )
    world.say(f"{hero.pronoun().capitalize()} also loved the yip-yip sound from a tiny dog under the table.")
    world.say(f"One day, {hero.id}'s {params.parent} gave {hero.pronoun('object')} {prize.phrase}.")
    world.say(f"{hero.id} grinned and balanced {hero.pronoun('possessive')} {prize.label} like it was very important business.")

    world.para()
    world.say(
        f"At {world.setting.place}, {hero.id} wanted to {trick.verb}, but a small dog gave a loud yip and made everyone hop."
    )
    world.say(f"{hero.pronoun().capitalize()} laughed so hard that {hero.pronoun('possessive')} tray wobbled.")
    _do_trick(world, hero, trick)
    if trick.id == "hose":
        world.say(f"Then the hose bumped the tray, and water splashed everywhere.")
    else:
        world.say(f"Then the magic sparkles bounced off the tray like confetti.")

    world.para()
    _magic_transform(world, hero, tray, trick)
    world.say(f"{params.parent.capitalize()} said, 'See? Sometimes a mistake makes room for a clever idea.'")
    world.say(f"{hero.id} nodded and learned that being careful could still be funny.")
    world.say(
        f"In the end, the tray was shiny, the dog had stopped yipping, and {hero.id} was smiling at the silly result."
    )

    world.facts.update(hero=hero, parent=parent, tray=tray, trick=trick, prize=prize, setting=world.setting)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a short comedy story for a child about {f['hero'].id}, a tray, a yip, and a hose.",
        f"Tell a gentle story where a {f['gender'] if 'gender' in f else f['hero'].type} named {f['hero'].id} learns a lesson after a magical hose mishap.",
        f"Write a funny story that includes a tray, a yippy dog, and a transformation caused by magic.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, parent, trick, prize = f["hero"], f["parent"], f["trick"], f["prize"]
    return [
        QAItem(
            question=f"Who is the story about?",
            answer=f"It is about {hero.id}, who was trying to carry {prize.phrase} at {world.setting.place}.",
        ),
        QAItem(
            question=f"What noisy thing caused the trouble?",
            answer=f"A tiny dog gave a big yip, and then {trick.verb} made the tray wobble.",
        ),
        QAItem(
            question=f"What changed at the end?",
            answer=f"The tray became shiny and the mistake turned into a funny magic moment, so {hero.id} learned a lesson.",
        ),
        QAItem(
            question=f"How did the parent help with the problem?",
            answer=f"{parent.type.capitalize()} reminded {hero.id} that careful choices can still lead to funny surprises.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a tray for?",
            answer="A tray is a flat thing you use to carry or hold food, cups, or small objects.",
        ),
        QAItem(
            question="What does yip mean?",
            answer="A yip is a small, sharp bark from a little dog.",
        ),
        QAItem(
            question="What does a hose do?",
            answer="A hose moves water from one place to another, often for watering plants or rinsing things.",
        ),
        QAItem(
            question="What is a lesson learned?",
            answer="A lesson learned is a helpful idea someone remembers after something goes wrong.",
        ),
        QAItem(
            question="What is transformation?",
            answer="A transformation is when something changes into a different form or looks very different.",
        ),
        QAItem(
            question="What is magic in a story?",
            answer="Magic is something surprising or special that seems to happen in a way normal life cannot explain.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story q&a ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world q&a ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        m = {k: v for k, v in e.meters.items() if v}
        n = {k: v for k, v in e.memes.items() if v}
        lines.append(f"{e.id}: kind={e.kind} type={e.type} meters={m} memes={n}")
    lines.append(f"fired={sorted(world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
prize_at_risk(T, P) :- trick(T), prize(P), zone(T, R), region(P, R).
valid(Place, T, P) :- setting(Place), affords(Place, T), prize_at_risk(T, P).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for t in sorted(s.affords):
            lines.append(asp.fact("affords", sid, t))
    for tid, t in TRICKS.items():
        lines.append(asp.fact("trick", tid))
        for r in sorted(t.zone):
            lines.append(asp.fact("zone", tid, r))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("region", pid, p.region))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if py == asp_set:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH:")
    print("python-only:", sorted(py - asp_set))
    print("clingo-only:", sorted(asp_set - py))
    return 1


CURATED = [
    StoryParams("backyard", "hose", "tray", "Mia", "girl", "mother"),
    StoryParams("garden", "magic", "paper", "Leo", "boy", "father"),
    StoryParams("patio", "hose", "cookies", "Zoe", "girl", "mother"),
]


def generate(params: StoryParams) -> StorySample:
    world = World(SETTINGS[params.place])
    tell(world, params)
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
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for c in combos:
            print(c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            seed = base_seed + i
            i += 1
            try:
                p = resolve_params(args, random.Random(seed))
            except StoryError as e:
                print(e)
                return
            p.seed = seed
            s = generate(p)
            if s.story in seen:
                continue
            seen.add(s.story)
            samples.append(s)

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, s in enumerate(samples):
        emit(s, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
