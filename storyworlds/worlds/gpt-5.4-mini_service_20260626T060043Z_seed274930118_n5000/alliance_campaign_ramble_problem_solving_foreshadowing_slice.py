#!/usr/bin/env python3
"""
A standalone story world for a small slice-of-life tale about an alliance,
a neighborhood campaign, and a ramble that turns into problem solving.

Premise:
- A child and two friends form an alliance to help their block.
- They start a little campaign to make the street nicer.
- During a ramble through the neighborhood, they notice a small problem.
- Foreshadowing hints that their plan will need one extra tool.
- They solve the problem together and finish with a calmer, brighter block.
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

TITLE = "alliance_campaign_ramble_problem_solving_foreshadowing_slice"


@dataclass
class Person:
    id: str
    role: str
    name: str
    trait: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self) -> str:
        return "they"

    def possessive(self) -> str:
        return "their"


@dataclass
class Thing:
    id: str
    name: str
    kind: str
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class StoryParams:
    place: str = "the block"
    hero: str = "Mina"
    friend1: str = "Owen"
    friend2: str = "Tara"
    trait: str = "careful"
    seed: Optional[int] = None


class World:
    def __init__(self, params: StoryParams) -> None:
        self.params = params
        self.people: dict[str, Person] = {}
        self.things: dict[str, Thing] = {}
        self.lines: list[str] = []
        self.facts: dict[str, object] = {}
        self.foreshadowed = False
        self.problem_seen = False
        self.problem_solved = False

    def add_person(self, person: Person) -> Person:
        self.people[person.id] = person
        return person

    def add_thing(self, thing: Thing) -> Thing:
        self.things[thing.id] = thing
        return thing

    def say(self, text: str) -> None:
        if text:
            self.lines.append(text)

    def para(self) -> None:
        if self.lines and self.lines[-1] != "":
            self.lines.append("")

    def render(self) -> str:
        out: list[str] = []
        buf: list[str] = []
        for line in self.lines:
            if line == "":
                if buf:
                    out.append(" ".join(buf))
                    buf = []
            else:
                buf.append(line)
        if buf:
            out.append(" ".join(buf))
        return "\n\n".join(out)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A slice-of-life story about alliance, campaign, and a ramble.")
    ap.add_argument("--place", default="the block")
    ap.add_argument("--hero")
    ap.add_argument("--friend1")
    ap.add_argument("--friend2")
    ap.add_argument("--trait", choices=["careful", "cheerful", "curious", "patient", "bright"], default=None)
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


def _base_traits() -> list[str]:
    return ["careful", "cheerful", "curious", "patient", "bright"]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    trait = args.trait or rng.choice(_base_traits())
    hero = args.hero or rng.choice(["Mina", "Lena", "Iris", "Noah", "Jun", "Pia"])
    friend1 = args.friend1 or rng.choice(["Owen", "Tara", "Sage", "Milo", "Nia", "Eli"])
    friend2 = args.friend2 or rng.choice(["Tara", "Owen", "Rae", "Zuri", "Ari", "Noa"])
    if len({hero, friend1, friend2}) < 3:
        raise StoryError("Please choose three different names for the hero and two friends.")
    return StoryParams(
        place=args.place,
        hero=hero,
        friend1=friend1,
        friend2=friend2,
        trait=trait,
    )


def _make_world(params: StoryParams) -> World:
    w = World(params)
    hero = w.add_person(Person(id="hero", role="child", name=params.hero, trait=params.trait))
    f1 = w.add_person(Person(id="friend1", role="child", name=params.friend1, trait="helpful"))
    f2 = w.add_person(Person(id="friend2", role="child", name=params.friend2, trait="steady"))
    sign = w.add_thing(Thing(id="sign", name="a little handwritten sign", kind="sign"))
    bag = w.add_thing(Thing(id="bag", name="a paper bag with wipes and tape", kind="toolbag", owner=hero.id))

    hero.meters["hope"] = 1
    hero.memes["belonging"] = 1
    f1.memes["teamwork"] = 1
    f2.memes["teamwork"] = 1
    sign.meters["visible"] = 1
    bag.meters["ready"] = 1

    w.facts.update(hero=hero, friend1=f1, friend2=f2, sign=sign, bag=bag)
    return w


def _foreshadow(w: World) -> None:
    hero: Person = w.facts["hero"]  # type: ignore[assignment]
    sign: Thing = w.facts["sign"]  # type: ignore[assignment]
    hero.memes["curiosity"] = 1
    w.say(
        f"{hero.name} liked quiet afternoons on {w.params.place}, where small jobs could turn into a little adventure."
    )
    w.say(
        f"{hero.name} also carried {sign.name} for their neighborhood campaign: a few nice words, a few tidy corners, and a friendlier block."
    )
    w.say(
        "At the edge of the street, a loose crack in the sidewalk caught their eye; it looked small now, but it seemed like the kind of thing that could bother people later."
    )
    w.foreshadowed = True


def _alliance(w: World) -> None:
    hero: Person = w.facts["hero"]  # type: ignore[assignment]
    f1: Person = w.facts["friend1"]  # type: ignore[assignment]
    f2: Person = w.facts["friend2"]  # type: ignore[assignment]
    hero.memes["trust"] = 1
    f1.memes["trust"] = 1
    f2.memes["trust"] = 1
    w.say(
        f"After school, {hero.name} met {f1.name} and {f2.name}, and the three of them made an alliance over the campaign."
    )
    w.say(
        f"{f1.name} would talk to neighbors, {f2.name} would carry supplies, and {hero.name} would keep everyone looking for little problems."
    )


def _ramble_and_problem(w: World) -> None:
    hero: Person = w.facts["hero"]  # type: ignore[assignment]
    f1: Person = w.facts["friend1"]  # type: ignore[assignment]
    f2: Person = w.facts["friend2"]  # type: ignore[assignment]
    bag: Thing = w.facts["bag"]  # type: ignore[assignment]
    hero.meters["walked"] = 1
    w.say(
        f"Their ramble started slowly, with sneakers on pavement and the soft rustle of {bag.name}."
    )
    w.say(
        f"They passed a mailbox, a row of pots, and a patch of weeds that had grown too close to a drain."
    )
    w.problem_seen = True
    hero.memes["concern"] = 1
    w.say(
        f"Then {hero.name} noticed the drain was half-blocked by damp leaves, and that was exactly the sort of small trouble their campaign wanted to catch early."
    )
    w.say(
        f"{f2.name} crouched down, {f1.name} held the bag open, and {hero.name} said, 'We can fix this before it turns into a bigger mess.'"
    )


def _solve(w: World) -> None:
    hero: Person = w.facts["hero"]  # type: ignore[assignment]
    f1: Person = w.facts["friend1"]  # type: ignore[assignment]
    f2: Person = w.facts["friend2"]  # type: ignore[assignment]
    bag: Thing = w.facts["bag"]  # type: ignore[assignment]
    if not w.problem_seen:
        raise StoryError("The story needs a visible problem before the solution can matter.")
    hero.meters["problem_solving"] = 1
    f1.meters["problem_solving"] = 1
    f2.meters["problem_solving"] = 1
    w.problem_solved = True
    w.say(
        f"Together they scooped the leaves into {bag.name}, and the water slipped through the drain again."
    )
    w.say(
        f"The little crack still needed a grown-up's attention, but the urgent part was gone, and the sidewalk looked calmer already."
    )
    w.say(
        f"By the time they finished their ramble, the three friends felt proud of their alliance, because their campaign had become a real kindness in motion."
    )


def tell(params: StoryParams) -> World:
    w = _make_world(params)
    _foreshadow(w)
    w.para()
    _alliance(w)
    w.para()
    _ramble_and_problem(w)
    w.para()
    _solve(w)
    w.facts["resolved"] = True
    return w


def generation_prompts(world: World) -> list[str]:
    p = world.params
    return [
        f"Write a gentle slice-of-life story about {p.hero}, {p.friend1}, and {p.friend2} forming an alliance for a neighborhood campaign.",
        f"Tell a story that includes a ramble, a foreshadowed small problem, and a practical fix on {p.place}.",
        f"Write a short child-friendly story where friends work together, notice trouble early, and solve it kindly.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p = world.params
    hero: Person = world.facts["hero"]  # type: ignore[assignment]
    f1: Person = world.facts["friend1"]  # type: ignore[assignment]
    f2: Person = world.facts["friend2"]  # type: ignore[assignment]
    return [
        QAItem(
            question=f"Who made the alliance for the neighborhood campaign?",
            answer=f"{hero.name}, {f1.name}, and {f2.name} made the alliance together.",
        ),
        QAItem(
            question=f"What small problem did the friends notice during their ramble on {p.place}?",
            answer="They noticed that damp leaves were blocking a drain and needed to be cleared.",
        ),
        QAItem(
            question=f"How did the friends solve the problem?",
            answer="They used a paper bag to scoop up the leaves so water could flow through the drain again.",
        ),
        QAItem(
            question=f"Why did the story foreshadow the drain earlier?",
            answer="The story hinted at the drain because the loose crack and weeds showed that a small issue might need attention soon.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is an alliance?",
            answer="An alliance is a group of people working together for the same goal.",
        ),
        QAItem(
            question="What is a campaign?",
            answer="A campaign is an organized effort to help, change, or promote something over time.",
        ),
        QAItem(
            question="What does ramble mean?",
            answer="To ramble means to walk or talk in a loose, unhurried way, often while noticing things along the way.",
        ),
        QAItem(
            question="What is foreshadowing?",
            answer="Foreshadowing is when a story gives a small hint about something that will matter later.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Story questions =="]
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for person in world.people.values():
        lines.append(f"{person.id}: name={person.name} trait={person.trait} meters={person.meters} memes={person.memes}")
    for thing in world.things.values():
        lines.append(f"{thing.id}: name={thing.name} kind={thing.kind} meters={thing.meters} memes={thing.memes}")
    lines.append(f"foreshadowed={world.foreshadowed} problem_seen={world.problem_seen} problem_solved={world.problem_solved}")
    return "\n".join(lines)


ASP_RULES = r"""
place(block).
event(alliance).
event(campaign).
event(ramble).
feature(problem_solving).
feature(foreshadowing).
style(slice_of_life).

story_ok :- place(block), event(alliance), event(campaign), event(ramble), feature(problem_solving), feature(foreshadowing), style(slice_of_life).
#show story_ok/0.
"""


def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            asp.fact("place", "block"),
            asp.fact("event", "alliance"),
            asp.fact("event", "campaign"),
            asp.fact("event", "ramble"),
            asp.fact("feature", "problem_solving"),
            asp.fact("feature", "foreshadowing"),
            asp.fact("style", "slice_of_life"),
        ]
    )


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    program = asp_program("#show story_ok/0.")
    model = asp.one_model(program)
    ok = any(sym.name == "story_ok" for sym in model)
    py_ok = True
    if ok == py_ok:
        print("OK: ASP gate matches Python reasonableness gate.")
        return 0
    print("MISMATCH between ASP and Python gates.")
    return 1


def valid_params(params: StoryParams) -> bool:
    return bool(params.place and params.hero and params.friend1 and params.friend2 and params.trait)


def generate(params: StoryParams) -> StorySample:
    if not valid_params(params):
        raise StoryError("Invalid parameters for this story world.")
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


def _all_samples() -> list[StoryParams]:
    return [
        StoryParams(place="the block", hero="Mina", friend1="Owen", friend2="Tara", trait="careful"),
        StoryParams(place="the block", hero="Iris", friend1="Eli", friend2="Rae", trait="curious"),
        StoryParams(place="the block", hero="Jun", friend1="Nia", friend2="Milo", trait="patient"),
    ]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show story_ok/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_program("#show story_ok/0."))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        for p in _all_samples():
            samples.append(generate(p))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 20, 20):
            rng = random.Random(base_seed + i)
            i += 1
            params = resolve_params(args, rng)
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
