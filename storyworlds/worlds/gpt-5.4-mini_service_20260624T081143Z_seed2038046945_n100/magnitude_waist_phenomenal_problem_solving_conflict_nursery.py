#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260624T081143Z_seed2038046945_n100/magnitude_waist_phenomenal_problem_solving_conflict_nursery.py
==========================================================================================

A small nursery-rhyme story world about a child, a tricky waist fit, and a
problem-solving turn that resolves a little conflict.

Seed prompt image:
- A tiny child wants to move and dance.
- Something around the waist does not fit right.
- A grownup and child feel a little conflict.
- They solve it with a simple, physical fix.
- The ending should feel cheerful and a bit rhyming.

Required seed words:
- magnitude
- waist
- phenomenal

Style:
- Nursery rhyme cadence, simple and child-facing.
- Clear beginning, conflict, turn, and ending image.
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
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    region: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str
    indoors: bool = False
    affords: set[str] = field(default_factory=set)


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    mess: str
    zone: set[str]
    keyword: str
    rhyme: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    label: str
    phrase: str
    type: str
    region: str


@dataclass
class Fix:
    id: str
    label: str
    prep: str
    tail: str
    covers: set[str]
    guards: set[str]


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.lines: list[str] = []
        self.facts: dict[str, object] = {}
        self.fired: set[tuple] = set()

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.lines.append(text)

    def render(self) -> str:
        return " ".join(self.lines)


SETTINGS = {
    "nursery": Setting("the nursery", indoors=True, affords={"dance", "hop", "tuck"}),
    "garden": Setting("the garden", indoors=False, affords={"dance", "hop"}),
    "playroom": Setting("the playroom", indoors=True, affords={"dance", "tuck"}),
}

ACTIVITIES = {
    "dance": Activity(
        id="dance",
        verb="dance",
        gerund="dancing",
        rush="spin and prance",
        mess="tangled",
        zone={"waist"},
        keyword="dance",
        rhyme="tall and grand",
        tags={"conflict", "problem solving"},
    ),
    "hop": Activity(
        id="hop",
        verb="hop",
        gerund="hopping",
        rush="bounce along",
        mess="bumped",
        zone={"waist"},
        keyword="hop",
        rhyme="up and down",
        tags={"conflict"},
    ),
    "tuck": Activity(
        id="tuck",
        verb="tuck toys away",
        gerund="tucking toys",
        rush="hurry and reach",
        mess="bent",
        zone={"waist"},
        keyword="tuck",
        rhyme="nice and neat",
        tags={"problem solving"},
    ),
}

PRIZES = {
    "sash": Prize("sash", "a shiny sash", "sash", "waist"),
    "belt": Prize("belt", "a bright little belt", "belt", "waist"),
}

FIXES = [
    Fix("loosen", "a looser knot", "make a looser knot", "the sash sat smooth", {"waist"}, {"tangled", "bumped", "bent"}),
    Fix("swap", "a softer ribbon", "swap to a softer ribbon", "the ribbon felt light", {"waist"}, {"tangled", "bumped", "bent"}),
]


@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    name: str
    parent: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            act = ACTIVITIES[act_id]
            for prize_id, prize in PRIZES.items():
                if prize.region in act.zone:
                    combos.append((place, act_id, prize_id))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Nursery rhyme storyworld about waist trouble and a kind fix.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--name")
    ap.add_argument("--parent", choices=["mother", "father"])
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
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.activity is None or c[1] == args.activity)
              and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError("(No valid nursery-rhyme combination matches the given options.)")
    place, activity, prize = rng.choice(sorted(combos))
    name = args.name or rng.choice(["Maya", "Nina", "Toby", "Milo", "Luna"])
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(place=place, activity=activity, prize=prize, name=name, parent=parent)


def reason_gate() -> list[tuple[str, str, str]]:
    return sorted(valid_combos())


ASP_RULES = r"""
place(nursery). place(garden). place(playroom).
affords(nursery,dance). affords(nursery,hop). affords(nursery,tuck).
affords(garden,dance). affords(garden,hop).
affords(playroom,dance). affords(playroom,tuck).

activity(dance). activity(hop). activity(tuck).

prize(sash). prize(belt).
worn_on(sash,waist). worn_on(belt,waist).

splashes(dance,waist). splashes(hop,waist). splashes(tuck,waist).

valid(P,A,R) :- affords(P,A), splashes(A,Region), worn_on(R,Region), place(P), activity(A), prize(R).
#show valid/3.
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for p in SETTINGS:
        lines.append(asp.fact("place", p))
        for a in SETTINGS[p].affords:
            lines.append(asp.fact("affords", p, a))
    for a in ACTIVITIES:
        lines.append(asp.fact("activity", a))
        for r in ACTIVITIES[a].zone:
            lines.append(asp.fact("splashes", a, r))
    for p in PRIZES:
        lines.append(asp.fact("prize", p))
        lines.append(asp.fact("worn_on", p, PRIZES[p].region))
    return "\n".join(lines)


def asp_program(show: str = "#show valid/3.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and python:")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


def opening(world: World, hero: Entity, parent: Entity, prize: Entity, act: Activity) -> None:
    world.say(
        f"In the {world.setting.place.removeprefix('the ')}, little {hero.id} had a phenomenal day, "
        f"and the tune went ping and play."
    )
    world.say(
        f"{hero.pronoun().capitalize()} loved to {act.verb}, with {prize.phrase} snug at {hero.pronoun('possessive')} waist."
    )
    world.say(
        f"{hero.pronoun('possessive').capitalize()} {parent.label} had tied it just right, at a gentle magnitude, neat as lace."
    )


def conflict(world: World, hero: Entity, parent: Entity, prize: Entity, act: Activity) -> None:
    hero.memes["desire"] = hero.memes.get("desire", 0) + 1
    hero.memes["conflict"] = hero.memes.get("conflict", 0) + 1
    world.say(
        f"But when {hero.id} tried to {act.rush}, the {prize.label} pinched at the waist and would not stay in place."
    )
    world.say(
        f"{hero.pronoun().capitalize()} frowned, and {hero.pronoun('possessive')} {parent.label} said, "
        f'"Let us stop and think, and solve this little case."'
    )


def choose_fix(act: Activity, prize: Prize) -> Fix:
    for fx in FIXES:
        if prize.region in fx.covers and act.mess in fx.guards:
            return fx
    raise StoryError("No reasonable fix fits this nursery problem.")


def resolution(world: World, hero: Entity, parent: Entity, prize: Entity, act: Activity) -> Fix:
    fx = choose_fix(act, prize)
    world.say(
        f"They chose {fx.prep}, and {hero.id} stood still with a tiny grin."
    )
    world.say(
        f"At once, {fx.tail}, and {hero.id} could {act.gerund} again with a happy spin."
    )
    hero.memes["conflict"] = 0
    hero.memes["joy"] = hero.memes.get("joy", 0) + 1
    return fx


def tell(params: StoryParams) -> World:
    world = World(SETTINGS[params.place])
    hero = world.add(Entity(id=params.name, kind="character", type="girl"))
    parent = world.add(Entity(id="parent", kind="character", type=params.parent, label=f"{params.parent}"))
    prize = world.add(Entity(id="prize", type=PRIZES[params.prize].type, label=PRIZES[params.prize].label, phrase=PRIZES[params.prize].phrase, owner=hero.id, caretaker=parent.id, region=PRIZES[params.prize].region))
    act = ACTIVITIES[params.activity]
    opening(world, hero, parent, prize, act)
    world.say("")
    conflict(world, hero, parent, prize, act)
    world.say("")
    fx = resolution(world, hero, parent, prize, act)
    world.facts.update(hero=hero, parent=parent, prize=prize, activity=act, fix=fx, setting=world.setting)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    act = f["activity"]
    prize = f["prize"]
    return [
        f"Write a nursery rhyme story about {hero.id}, a waist problem, and a kind solution.",
        f"Tell a tiny rhyme where a child wants to {act.verb} but {prize.phrase} makes trouble at the waist.",
        f"Use the words magnitude, waist, and phenomenal in a child-friendly story with a conflict and fix.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    prize = f["prize"]
    act = f["activity"]
    fx = f["fix"]
    return [
        QAItem(
            question=f"What was happening to {hero.id}'s {prize.label} at the waist?",
            answer=f"It was pinching and making a little conflict, because {prize.phrase} did not sit comfortably while {hero.id} wanted to {act.verb}.",
        ),
        QAItem(
            question=f"How did the grownup help solve the problem for {hero.id}?",
            answer=f"They chose {fx.label} and made the tie looser, so the waist felt better and {hero.id} could keep going.",
        ),
        QAItem(
            question="What made the ending feel good again?",
            answer=f"The problem was solved, the conflict stopped, and {hero.id} could {act.gerund} with a smile.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is the waist?",
            answer="The waist is the middle part of your body, a little above your hips and below your ribs.",
        ),
        QAItem(
            question="What does it mean when something is phenomenal?",
            answer="Phenomenal means very, very wonderful or extra special.",
        ),
        QAItem(
            question="What is the magnitude of something?",
            answer="Magnitude means how big or strong something is.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    out.extend(sample.prompts)
    out.append("")
    out.append("== story qa ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== world qa ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        bits = []
        if e.region:
            bits.append(f"region={e.region}")
        if e.memes:
            bits.append(f"memes={dict(e.memes)}")
        lines.append(f"{e.id}: {e.type} {' '.join(bits)}")
    return "\n".join(lines)


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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
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
        for place, act, prize in valid_combos():
            p = StoryParams(place=place, activity=act, prize=prize, name="Maya", parent="mother")
            samples.append(generate(p))
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            i += 1
            rng = random.Random(base_seed + i)
            try:
                params = resolve_params(args, rng)
            except StoryError as e:
                print(e)
                return
            params.seed = base_seed + i
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
        header = f"### variant {i+1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
