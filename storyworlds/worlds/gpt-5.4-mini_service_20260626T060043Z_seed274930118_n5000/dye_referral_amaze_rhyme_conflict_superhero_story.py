#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/dye_referral_amaze_rhyme_conflict_superhero_story.py
==============================================================================================================

A small superhero-style storyworld about a hero, a dye mishap, a referral,
and a surprising rhyme that cools a conflict.

Seed tale:
---
A young superhero named Nova loved helping people in Bright City. Nova wore a
plain white cape that needed to be dyed the perfect blue before the city parade.
On the way to the dye shop, the capesmith got called away. The shopkeeper gave
Nova a referral to a famous cloth helper across town.

But when Nova reached the helper's studio, the dye splashed on the wrong cloth
and the hero and helper argued. Nova took a breath and spoke in rhyme, turning
the conflict into a joke. The helper laughed, fixed the cape, and Nova left
amazed at how a few kind words could save the day.

World model:
- Physical meters track dye stains, distance walked, and finished work.
- Emotional memes track awe, conflict, trust, and calm.
- The story turns on a mistaken dye job, a referral, and a rhyme-based truce.
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
    kind: str = "thing"  # "hero" | "helper" | "thing"
    label: str = ""
    phrase: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "hero":
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    name: str
    affords: set[str] = field(default_factory=set)


@dataclass
class DyeJob:
    color: str
    mess: str
    rhyme_hint: str
    risk_word: str
    place: str
    referral_kind: str = "tailor"


@dataclass
class StoryParams:
    place: str
    job: str
    hero: str
    helper: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place, job: DyeJob) -> None:
        self.place = place
        self.job = job
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
        import copy as _copy
        w = World(self.place, self.job)
        w.entities = _copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        w.fired = set(self.fired)
        return w


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Superhero storyworld about dye, referral, amaze, rhyme, and conflict.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--job", choices=JOBS)
    ap.add_argument("--hero")
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


PLACES = {
    "bright_city": Place("Bright City", affords={"dye"}),
    "harbor_lane": Place("Harbor Lane", affords={"dye"}),
}

JOBS = {
    "blue_cape": DyeJob(color="blue", mess="dyed", rhyme_hint="shine", risk_word="stain", place="bright_city"),
    "red_mask": DyeJob(color="red", mess="spilled", rhyme_hint="glow", risk_word="smudge", place="harbor_lane"),
}

HEROES = ["Nova", "Comet", "Starling", "Pulse"]
HELPERS = ["Mira", "Tess", "Ari", "Juno"]
ADJECTIVES = ["brave", "kind", "swift", "bright"]


def reasonableness_gate(place: Place, job: DyeJob) -> bool:
    return "dye" in place.affords and job.color in {"blue", "red"}


def explain_rejection(place: Place, job: DyeJob) -> str:
    return f"(No story: {place.name} does not support the dye scene for the {job.color} cape.)"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.job:
        if not reasonableness_gate(PLACES[args.place], JOBS[args.job]):
            raise StoryError(explain_rejection(PLACES[args.place], JOBS[args.job]))
    combos = [
        (p, j)
        for p in PLACES
        for j in JOBS
        if (args.place is None or args.place == p) and (args.job is None or args.job == j)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, job = rng.choice(sorted(combos))
    hero = args.hero or rng.choice(HEROES)
    helper = args.helper or rng.choice(HELPERS)
    return StoryParams(place=place, job=job, hero=hero, helper=helper)


def setup_world(params: StoryParams) -> World:
    place = PLACES[params.place]
    job = JOBS[params.job]
    w = World(place, job)
    hero = w.add(Entity(id=params.hero, kind="hero", label=params.hero, meters={"distance": 0.0}, memes={"awe": 0.0, "conflict": 0.0, "calm": 0.0}))
    helper = w.add(Entity(id=params.helper, kind="helper", label=params.helper, meters={"work": 0.0}, memes={"trust": 0.0}))
    cape = w.add(Entity(id="cape", label=f"{job.color} cape", phrase=f"a white cape waiting to be dyed {job.color}", meters={"dye": 0.0}, memes={"value": 1.0}))
    referral = w.add(Entity(id="referral", label="referral card", phrase=f"a card with a referral to a {job.referral_kind}", meters={"distance": 0.0}))
    w.facts.update(hero=hero, helper=helper, cape=cape, referral=referral, place=place, job=job)
    return w


def intro(world: World) -> None:
    hero = world.get(world.facts["hero"].id)
    job = world.facts["job"]
    world.say(f"{hero.id} was a {random.choice(ADJECTIVES)} superhero who loved helping people in {world.place.name}.")
    world.say(f"{hero.id} needed {job.color} dye for a cape, because {hero.pronoun('possessive')} plain white cape was ready for a change.")
    hero.memes["awe"] += 1


def seek_referral(world: World) -> None:
    hero = world.facts["hero"]
    referral = world.facts["referral"]
    world.say(f"At the dye shop, the capesmith had to rush away, but left {hero.id} a referral card.")
    world.say(f"The card pointed to a helper across town, so {hero.id} tucked it into {hero.pronoun('possessive')} belt and hurried on.")
    hero.meters["distance"] += 2
    referral.meters["distance"] += 2


def dye_conflict(world: World) -> None:
    hero = world.facts["hero"]
    helper = world.facts["helper"]
    cape = world.facts["cape"]
    job = world.facts["job"]
    hero.meters["distance"] += 1
    cape.meters["dye"] += 1
    cape.memes["value"] += 0.5
    helper.memes["trust"] += 0.5
    world.say(f"At the studio, the dye splashed onto the wrong cloth, and {hero.id} and {helper.id} both frowned.")
    world.say(f"{hero.id} wanted a perfect {job.color} cape, but the wet {job.mess} made a messy blot instead.")
    hero.memes["conflict"] += 1
    helper.memes["conflict"] = helper.memes.get("conflict", 0.0) + 1
    world.facts["conflict"] = True


def rhyme_turn(world: World) -> None:
    hero = world.facts["hero"]
    helper = world.facts["helper"]
    job = world.facts["job"]
    world.say(f"{hero.id} took a breath and said, “No more gloom, let's make it bloom; we can fix this in the same small room.”")
    world.say(f"The rhyme made the helper blink, then smile, because the angry feeling broke apart like a bubble.")
    hero.memes["conflict"] = 0.0
    helper.memes["conflict"] = 0.0
    hero.memes["calm"] += 1
    helper.memes["trust"] += 1
    world.facts["rhyme_used"] = True
    world.say(f"Together they rinsed the cloth, checked the shade, and dyed the cape the right {job.color} at last.")


def ending(world: World) -> None:
    hero = world.facts["hero"]
    helper = world.facts["helper"]
    cape = world.facts["cape"]
    job = world.facts["job"]
    cape.meters["dye"] = 2.0
    hero.memes["awe"] += 1
    world.say(f"When {hero.id} wore the finished cape, the city lights caught the color and made {hero.pronoun('object')} look amazing.")
    world.say(f"{helper.id} laughed, {hero.id} smiled, and the referral had turned a mistake into a rescue.")
    world.say(f"By nightfall, {hero.id} flew home amazed that a referral, a rhyme, and a little patience could save the day.")


def tell(params: StoryParams) -> World:
    world = setup_world(params)
    intro(world)
    world.para()
    seek_referral(world)
    dye_conflict(world)
    world.para()
    rhyme_turn(world)
    ending(world)
    return world


def valid_combos() -> list[tuple[str, str]]:
    return [(p, j) for p in PLACES for j in JOBS if reasonableness_gate(PLACES[p], JOBS[j])]


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for p in PLACES:
        lines.append(asp.fact("place", p))
        for a in sorted(PLACES[p].affords):
            lines.append(asp.fact("affords", p, a))
    for j, job in JOBS.items():
        lines.append(asp.fact("job", j))
        lines.append(asp.fact("color", j, job.color))
        lines.append(asp.fact("referral_kind", j, job.referral_kind))
    return "\n".join(lines)


ASP_RULES = r"""
valid(P,J) :- place(P), job(J), affords(P,dye), color(J,C), C = blue.
valid(P,J) :- place(P), job(J), affords(P,dye), color(J,C), C = red.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"].id
    helper = f["helper"].id
    job = f["job"]
    return [
        f"Write a short superhero story where {hero} needs {job.color} dye, gets a referral, and fixes a conflict with rhyme.",
        f"Tell a child-friendly adventure set in {world.place.name} where a cape mishap becomes amazing by the end.",
        f"Write a story about {hero} and {helper} that starts with a dye problem and ends with a calm, happy rescue.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    job = f["job"]
    cape = f["cape"]
    return [
        QAItem(
            question=f"Why did {hero.id} go looking for help in the first place?",
            answer=f"{hero.id} needed {job.color} dye for the cape, so {hero.id} followed a referral to find someone who could help.",
        ),
        QAItem(
            question=f"What went wrong when {hero.id} reached {helper.id}'s studio?",
            answer=f"The dye splashed onto the wrong cloth, and the mess turned the job into a conflict before it was fixed.",
        ),
        QAItem(
            question=f"What did {hero.id} say that helped calm everyone down?",
            answer=f"{hero.id} spoke in rhyme: “No more gloom, let's make it bloom; we can fix this in the same small room.”",
        ),
        QAItem(
            question=f"What was the ending image after the problem was solved?",
            answer=f"{hero.id} wore the finished {cape.label} home and felt amazed that a referral and a rhyme had saved the day.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What is dye used for?", answer="Dye is used to change the color of cloth, paper, or other materials."),
        QAItem(question="What is a referral?", answer="A referral is a helpful recommendation that points someone to the right person or place."),
        QAItem(question="What is a rhyme?", answer="A rhyme is when words sound alike at the end, like cat and hat."),
        QAItem(question="What is conflict?", answer="Conflict is a problem or disagreement that makes people upset until it gets solved."),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={{{', '.join(f'{k}: {v}' for k, v in e.meters.items() if v)}}}")
        if e.memes:
            bits.append(f"memes={{{', '.join(f'{k}: {v}' for k, v in e.memes.items() if v)}}}")
        lines.append(f"  {e.id:8} ({e.kind:6}) {' '.join(bits)}")
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


CURATED = [
    StoryParams(place="bright_city", job="blue_cape", hero="Nova", helper="Mira"),
    StoryParams(place="harbor_lane", job="red_mask", hero="Comet", helper="Tess"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for p, j in combos:
            print(f"  {p:12} {j}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            rng = random.Random(base_seed + i)
            i += 1
            try:
                params = resolve_params(args, rng)
            except StoryError as err:
                print(err)
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
        header = f"### variant {i + 1}" if len(samples) > 1 and not args.all else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
