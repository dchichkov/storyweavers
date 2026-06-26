#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/flag_beard_repetition_problem_solving_conflict_comedy.py
===============================================================================================================

A small standalone storyworld about a repeated flag mishap, a very noticeable beard,
and a comedy-style conflict that gets solved with practical thinking.

Premise:
- A child-like character takes pride in a flag they keep displaying.
- Another character has a beard that keeps getting tangled in the same flagpole/rope setup.
- The story repeats a comic problem twice before a clever fix is found.

The world model tracks:
- physical meters: flag height, rope tension, beard tangles, wind, wobble, distance
- emotional memes: pride, annoyance, patience, embarrassment, laughter, relief

The narrative is generated from state transitions, not from a frozen paragraph.
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
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    owner: Optional[str] = None

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class StoryParams:
    place: str
    name: str
    helper: str
    seed: Optional[int] = None


@dataclass
class World:
    place: str
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)

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


@dataclass
class Rule:
    name: str
    apply: callable


def _r_tangle(world: World) -> list[str]:
    out = []
    flag = world.get("flag")
    beard = world.get("beard")
    if flag.meters.get("flutter", 0) < THRESHOLD:
        return out
    if world.facts.get("beard_near_flag", 0) < THRESHOLD:
        return out
    sig = ("tangle", world.facts.get("tangle_count", 0))
    if sig in world.fired:
        return out
    world.fired.add(sig)
    beard.meters["tangle"] = beard.meters.get("tangle", 0) + 1
    beard.memes["annoyance"] = beard.memes.get("annoyance", 0) + 1
    out.append("The beard caught on the flag again.")
    return out


def _r_solution(world: World) -> list[str]:
    out = []
    helper = world.get("helper")
    flag = world.get("flag")
    beard = world.get("beard")
    if world.facts.get("fix_done"):
        return out
    if helper.memes.get("problem_solving", 0) < THRESHOLD:
        return out
    if beard.meters.get("tangle", 0) < THRESHOLD:
        return out
    sig = ("fix",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.facts["fix_done"] = True
    flag.meters["flutter"] = 0
    flag.meters["held_back"] = 1
    beard.meters["tangle"] = 0
    helper.memes["relief"] = helper.memes.get("relief", 0) + 1
    out.append("They moved the flag a little farther away and used a smooth clip.")
    return out


CAUSAL_RULES = [
    Rule("tangle", _r_tangle),
    Rule("solution", _r_solution),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def build_world(params: StoryParams) -> World:
    world = World(place=params.place)
    child = world.add(Entity(id=params.name, kind="character", type="boy", label=params.name))
    helper = world.add(Entity(id="helper", kind="character", type=params.helper, label=f"the {params.helper}"))
    flag = world.add(Entity(id="flag", type="flag", label="flag", phrase="a bright little flag"))
    beard = world.add(Entity(id="beard", type="beard", label="beard", phrase="a big curly beard"))

    child.memes["pride"] = 1
    helper.memes["patience"] = 1
    helper.memes["problem_solving"] = 1

    world.say(f"{child.id} loved the bright flag in {world.place}.")
    world.say(f"{helper.label} also had a very proud beard that seemed to notice everything.")
    world.say(f"Every time {child.id} straightened the flag, the beard got close and started another silly problem.")

    world.para()
    world.say(f"One breezy day, {child.id} raised the flag high, and the cloth fluttered like it had jokes to tell.")
    flag.meters["flutter"] = 1
    world.facts["beard_near_flag"] = 1
    world.facts["tangle_count"] = 1
    propagate(world)

    world.para()
    world.say(f"{child.id} tried again, because sometimes people hope the same move will work better the second time.")
    flag.meters["flutter"] = 1
    world.facts["tangle_count"] = 2
    world.say("But the beard snagged again, which was somehow even funnier than before.")
    beard.meters["tangle"] = beard.meters.get("tangle", 0) + 1
    beard.memes["annoyance"] = beard.memes.get("annoyance", 0) + 1
    world.say(f"{helper.label} frowned, then laughed, because the beard was acting like it wanted a turn with the flag.")
    propagate(world)

    world.para()
    if world.facts.get("fix_done"):
        world.say(f"{helper.label} moved the pole, clipped the rope neatly, and the beard finally stayed out of the way.")
        world.say(f"After that, {child.id} waved the flag once, then again, and the whole thing worked like a tiny parade.")
        world.say(f"{helper.label} smiled under {helper.pronoun('possessive')} beard, and everybody laughed at the happy ending.")
    else:
        # In practice the causal rule should have fixed it, but keep a sensible ending.
        world.say(f"{helper.label} found a calmer spot for the flag, and the beard stopped getting tangled.")
        world.say(f"That left {child.id} free to enjoy the flag without another unexpected beard adventure.")

    world.facts.update(child=child, helper=helper, flag=flag, beard=beard)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    return [
        f"Write a funny short story about {child.id}, a flag, and a beard that keeps causing the same problem.",
        f"Tell a comedy story where {helper.label} solves a repeated flag-and-beard mishap with a clever fix.",
        f"Write a child-friendly story about a flag that gets in the way of a beard, then gets moved to solve the problem.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    return [
        QAItem(
            question=f"Who wanted to enjoy the flag in {world.place}?",
            answer=f"{child.id} wanted to enjoy the flag in {world.place}, and {helper.label} was there too."
        ),
        QAItem(
            question="What kept happening to the beard before the problem was solved?",
            answer="The beard kept getting caught on the flag, so the same silly problem happened again."
        ),
        QAItem(
            question="How was the problem fixed?",
            answer="They solved it by moving the flag a little farther away and using a smooth clip so the beard would not snag again."
        ),
        QAItem(
            question="Why did the story feel funny?",
            answer="It felt funny because the same beard-and-flag problem happened more than once before anyone found the clever fix."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a flag?",
            answer="A flag is a piece of cloth that can hang from a pole and flap in the wind."
        ),
        QAItem(
            question="What is a beard?",
            answer="A beard is the hair that grows on some people's chins and cheeks."
        ),
        QAItem(
            question="Why can repeated problems be helpful in stories?",
            answer="Repeated problems give characters a chance to notice what is wrong and try a better plan."
        ),
        QAItem(
            question="What does problem solving mean?",
            answer="Problem solving means thinking carefully about what is causing trouble and choosing a way to fix it."
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"  {e.id:8} ({e.type:7}) meters={meters} memes={memes}")
    lines.append(f"  facts={world.facts}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== story questions ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== world questions ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


def asp_facts() -> str:
    import storyworlds.asp as asp
    return "\n".join([
        asp.fact("entity", "flag"),
        asp.fact("entity", "beard"),
        asp.fact("entity", "helper"),
        asp.fact("problem", "flag_beard_tangle"),
        asp.fact("can_solve", "move_flag"),
        asp.fact("can_solve", "clip_rope"),
    ])


ASP_RULES = r"""
entity(flag).
entity(beard).
entity(helper).
problem(flag_beard_tangle).
can_solve(move_flag).
can_solve(clip_rope).

repeated_problem(P) :- problem(P), problem(P).
solved(P) :- problem(P), can_solve(move_flag), can_solve(clip_rope).
story_ok :- entity(flag), entity(beard), repeated_problem(flag_beard_tangle), solved(flag_beard_tangle).

#show story_ok/0.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show story_ok/0."))
    ok = any(sym.name == "story_ok" for sym in model)
    if ok:
        print("OK: ASP model supports the flag-beard problem-solving story.")
        return 0
    print("MISMATCH: ASP model did not produce story_ok.")
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Comedy storyworld about a flag, a beard, repetition, and problem solving.")
    ap.add_argument("--place", choices=["yard", "court", "garden"], default=None)
    ap.add_argument("--name", default=None)
    ap.add_argument("--helper", choices=["mother", "father", "uncle", "aunt"], default=None)
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
    place = args.place or rng.choice(["yard", "court", "garden"])
    name = args.name or rng.choice(["Milo", "Nina", "Pip", "Theo", "Lena"])
    helper = args.helper or rng.choice(["mother", "father", "uncle", "aunt"])
    return StoryParams(place=place, name=name, helper=helper)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
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
    StoryParams(place="yard", name="Milo", helper="father"),
    StoryParams(place="garden", name="Nina", helper="mother"),
    StoryParams(place="court", name="Theo", helper="uncle"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show story_ok/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import storyworlds.asp as asp
        model = asp.one_model(asp_program("#show story_ok/0."))
        print("ASP model:")
        for sym in model:
            print(sym)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 20, 20):
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
            header = f"### {p.name} in {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
