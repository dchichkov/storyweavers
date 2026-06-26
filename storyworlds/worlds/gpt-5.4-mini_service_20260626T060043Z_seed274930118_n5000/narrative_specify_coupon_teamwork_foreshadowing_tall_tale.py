#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/narrative_specify_coupon_teamwork_foreshadowing_tall_tale.py
================================================================================

A small tall-tale storyworld about a crew finding a coupon, teaming up, and
using a careful clue from the start to solve a big, harmless problem.

The source tale this world grows from:

A tall fellow named Gus found an extra-big coupon tucked in a cereal box.
The coupon promised a free kite, but only if Gus could bring three things to
the corner shop: a spool, a ribbon, and a smile from someone willing to help.
Gus could not carry everything alone. He asked his sister Dot and their friend
Milo to help.

First they nearly forgot the ribbon, then a shop sign pointed them back to it.
That little sign was the foreshadowing clue: the ribbon had to be tied just
right, or the kite would wobble like a spoon in a thunderstorm. Together they
specify the needed parts, work as a team, and trade the coupon for the kite.
By sunset, the whole block could see the kite riding the wind like a tiny ship.

This script models:
- a coupon with a condition list
- a crew that can split the labor
- a foreshadowed clue that points to the missing item
- a tall-tale ending image proving the change
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

FORESHADOW_THRESHOLD = 1.0
TEAM_THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    carrier: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "sister"}
        male = {"boy", "father", "dad", "man", "brother"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    name: str
    outdoor: bool = True
    affords: set[str] = field(default_factory=set)


@dataclass
class Task:
    id: str
    verb: str
    gerund: str
    needed: list[str]
    clue: str
    tall_image: str


@dataclass
class Coupon:
    id: str
    label: str
    phrase: str
    requires: list[str]
    prize: str
    redeem_at: str
    valid_if: str


@dataclass
class StoryParams:
    place: str
    task: str
    coupon: str
    name: str
    helper1: str
    helper2: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
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
        w = World(self.place)
        w.entities = copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.fired = set(self.fired)
        w.facts = copy.deepcopy(self.facts)
        return w

    def crew(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]


def _r_teamwork(world: World) -> list[str]:
    out: list[str] = []
    crew = world.crew()
    leader = world.facts.get("hero")
    if not leader:
        return out
    helpers = [c for c in crew if c.id != leader.id]
    if len(helpers) < 2:
        return out
    if any(c.memes.get("helping", 0) < TEAM_THRESHOLD for c in helpers):
        return out
    sig = ("teamwork",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero = world.get(leader.id)
    hero.memes["confidence"] = hero.memes.get("confidence", 0) + 1
    out.append("The crew moved like a pair of geese in a fair wind, each one pulling the load just so.")
    return out


def _r_coupon_ready(world: World) -> list[str]:
    out: list[str] = []
    coupon: Entity = world.facts.get("coupon")
    task: Task = world.facts.get("task")
    hero: Entity = world.facts.get("hero")
    if not coupon or not task or not hero:
        return out
    if coupon.meters.get("complete", 0) < 1:
        return out
    sig = ("coupon_ready", coupon.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    out.append(f"{hero.id} held the coupon up high, ready to trade it for the prize.")
    return out


def _r_foreshadow(world: World) -> list[str]:
    out: list[str] = []
    clue = world.facts.get("clue_seen", False)
    ribbon = world.entities.get("ribbon")
    if not clue or not ribbon:
        return out
    sig = ("foreshadow",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    ribbon.memes["noticed"] = ribbon.memes.get("noticed", 0) + 1
    out.append("That little sign had been a hint all along, pointing the crew back to the ribbon.")
    return out


RULES = [_r_teamwork, _r_coupon_ready, _r_foreshadow]


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in RULES:
            sents = rule(world)
            if sents:
                changed = True
                out.extend(sents)
    if narrate:
        for s in out:
            world.say(s)
    return out


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Tall-tale storyworld about a coupon, teamwork, and a foreshadowed clue."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--task", choices=TASKS)
    ap.add_argument("--coupon", choices=COUPONS)
    ap.add_argument("--name")
    ap.add_argument("--helper1")
    ap.add_argument("--helper2")
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


PLACES = {
    "corner_shop": Place("the corner shop", outdoor=False, affords={"kite"}),
    "county_fair": Place("the county fair", outdoor=True, affords={"kite"}),
    "boardwalk": Place("the boardwalk", outdoor=True, affords={"kite"}),
}

TASKS = {
    "kite": Task(
        id="kite",
        verb="trade the coupon for a kite",
        gerund="trading the coupon for a kite",
        needed=["spool", "ribbon", "smile"],
        clue="a sign pointed to the ribbon bin",
        tall_image="the kite rose so high it could have tickled the moon",
    ),
    "jam": Task(
        id="jam",
        verb="trade the coupon for jam",
        gerund="trading the coupon for jam",
        needed=["jar", "lid", "smile"],
        clue="the jar shelf groaned like an old porch",
        tall_image="the jam shone red as a sunset in a rain barrel",
    ),
}

COUPONS = {
    "kite_coupon": Coupon(
        id="kite_coupon",
        label="kite coupon",
        phrase="a coupon for one free kite",
        requires=["spool", "ribbon", "smile"],
        prize="kite",
        redeem_at="the corner shop",
        valid_if="the helpers bring every needed thing",
    ),
    "jam_coupon": Coupon(
        id="jam_coupon",
        label="jam coupon",
        phrase="a coupon for one free jar of berry jam",
        requires=["jar", "lid", "smile"],
        prize="jam",
        redeem_at="the boardwalk stand",
        valid_if="the helpers bring every needed thing",
    ),
}

NAMES = ["Gus", "Dot", "Milo", "Nell", "Ivy", "Mabel", "Bert", "Walt"]
HELPERS = ["Dot", "Milo", "Nell", "Ivy", "Bert", "Walt", "Pip", "June"]


def valid_combos() -> list[tuple[str, str, str]]:
    return [(p, t, c) for p, place in PLACES.items() for t, task in TASKS.items() for c, coupon in COUPONS.items() if t == "kite" and coupon.prize == "kite" and task.id in place.affords]


ASP_RULES = r"""
task(T) :- task_name(T).
coupon(C) :- coupon_name(C).

needs(C, R) :- coupon_item(C, R).
needed(T, R) :- task_item(T, R).

compatible(P, T, C) :- place(P), task(T), coupon(C),
                       affords(P, T),
                       same_prize(T, C),
                       all_needed(T, C).

same_prize(T, C) :- task_prize(T, X), coupon_prize(C, X).
all_needed(T, C) :- needed(T, R), needs(C, R).
valid_story(P, T, C) :- compatible(P, T, C).

#show valid_story/3.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, place in PLACES.items():
        lines.append(asp.fact("place", pid))
        if place.outdoor:
            lines.append(asp.fact("outdoor", pid))
        for a in sorted(place.affords):
            lines.append(asp.fact("affords", pid, a))
    for tid, task in TASKS.items():
        lines.append(asp.fact("task_name", tid))
        lines.append(asp.fact("task_prize", tid, tid))
        for r in task.needed:
            lines.append(asp.fact("task_item", tid, r))
    for cid, c in COUPONS.items():
        lines.append(asp.fact("coupon_name", cid))
        lines.append(asp.fact("coupon_prize", cid, c.prize))
        for r in c.requires:
            lines.append(asp.fact("coupon_item", cid, r))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    import asp
    py = set(valid_combos())
    cl = set(asp_valid_stories())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and python:")
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    if py - cl:
        print("  only in python:", sorted(py - cl))
    return 1


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.task is None or c[1] == args.task)
              and (args.coupon is None or c[2] == args.coupon)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, task, coupon = rng.choice(sorted(combos))
    name = args.name or rng.choice(NAMES)
    helper1 = args.helper1 or rng.choice([n for n in HELPERS if n != name])
    helper2 = args.helper2 or rng.choice([n for n in HELPERS if n not in {name, helper1}])
    return StoryParams(place=place, task=task, coupon=coupon, name=name, helper1=helper1, helper2=helper2)


def tell(params: StoryParams) -> World:
    place = PLACES[params.place]
    task = TASKS[params.task]
    coupon = COUPONS[params.coupon]
    world = World(place)
    hero = world.add(Entity(id=params.name, kind="character", type="boy", label=params.name))
    h1 = world.add(Entity(id=params.helper1, kind="character", type="girl", label=params.helper1))
    h2 = world.add(Entity(id=params.helper2, kind="character", type="boy", label=params.helper2))
    cp = world.add(Entity(id="coupon", type="coupon", label=coupon.label, phrase=coupon.phrase, owner=hero.id))
    ribbon = world.add(Entity(id="ribbon", type="thing", label="ribbon"))
    spool = world.add(Entity(id="spool", type="thing", label="spool"))
    smile = world.add(Entity(id="smile", type="thing", label="smile"))

    world.facts.update(hero=hero, helpers=[h1, h2], coupon=cp, task=task, clue_seen=True)

    # Beginning
    world.say(f"{hero.id} was a tall-tale fellow with a hat like a wagon wheel and a pocket full of wonder.")
    world.say(f"One bright day, {hero.id} found {coupon.phrase} tucked away like a pearl in a cornstalk.")
    world.say(f"The coupon said it would work if three things came along: {', '.join(coupon.requires[:-1])}, and {coupon.requires[-1]}.")

    # Middle
    world.para()
    world.say(f"{hero.id} wanted to {task.verb}, but {hero.pronoun('possessive')} arms were not long enough for the load.")
    h1.memes["helping"] = 1
    h2.memes["helping"] = 1
    world.say(f"So {hero.id} called on {h1.id} and {h2.id}, and the three of them went off like a row of cheerful bluebirds.")
    world.say(f"At first they nearly missed the ribbon, until {task.clue}.")
    propagate(world, narrate=True)

    # Resolution
    world.para()
    if all(req in {"spool", "ribbon", "smile"} for req in coupon.requires):
        cp.meters["complete"] = 1
    world.say(f"Together they carried {spool.label}, {ribbon.label}, and {smile.label} to {coupon.redeem_at}.")
    propagate(world, narrate=True)
    world.say(f"The clerk took the coupon, winked, and handed over the prize.")
    world.say(f"By the end, {task.tall_image}.")

    world.facts["resolved"] = True
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = f["hero"]
    task: Task = f["task"]
    coupon: Entity = f["coupon"]
    return [
        'Write a short tall-tale story for a child about a coupon, teamwork, and a clue that was foreshadowed.',
        f"Tell a story where {hero.id} and two helpers work together to {task.verb} using {coupon.label}.",
        f"Write a narrative that specifies the needed items, uses the word 'coupon', and ends with a big sky-high image.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    task: Task = f["task"]
    coupon: Entity = f["coupon"]
    helpers = f["helpers"]
    return [
        QAItem(
            question=f"What did {hero.id} find at the start of the story?",
            answer=f"{hero.id} found {coupon.phrase}, which promised a prize if the needed things were brought in.",
        ),
        QAItem(
            question=f"Who helped {hero.id} get everything ready?",
            answer=f"{helpers[0].id} and {helpers[1].id} helped, and the three of them worked as a team.",
        ),
        QAItem(
            question=f"What clue foreshadowed the missing item?",
            answer=f"The clue was that {TASKS[f['task'].id].clue if isinstance(f['task'], Task) else 'a sign pointed them back'}; it led them back to the ribbon before the final trade.",
        ),
        QAItem(
            question=f"What happened at the end after they used the coupon?",
            answer=f"They traded the coupon and got the prize, and the story ended with {task.tall_image}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What is a coupon?", answer="A coupon is a paper or card that can be traded for a deal, discount, or prize."),
        QAItem(question="What does teamwork mean?", answer="Teamwork means people help each other do a job together."),
        QAItem(question="What is foreshadowing?", answer="Foreshadowing is a hint that gives you a small clue about what will matter later."),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(x[0] for x in world.fired if x))}")
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
    StoryParams(place="corner_shop", task="kite", coupon="kite_coupon", name="Gus", helper1="Dot", helper2="Milo"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        stories = asp_valid_stories()
        print(f"{len(stories)} compatible stories:")
        for s in stories:
            print(" ", s)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            i += 1
            try:
                params = resolve_params(args, random.Random(base_seed + i))
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
        header = ""
        if len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
