#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/smell_problem_solving_transformation_inner_monologue_fable.py
=============================================================================================================================

A small fable-like storyworld about a creature whose smell causes trouble,
who thinks through the problem, solves it, and changes by the end.

Premise seed:
---
A small forest fox named Fern notices that everyone steps back when she
arrives. She realizes her smell has become strong after rolling in a pile of
berries and old leaves. She worries that she will never be welcome at the
meadow supper.

Fern listens to her own thoughts, finds a stream, and asks the wind what
might help. She washes, rolls in mint leaves, and offers to carry water for
the animals who helped her. By the time she returns, her smell is fresh and
the animals see that she has changed in more than one way.

Narrative instruments:
---
- Problem Solving: Fern identifies the cause of the problem and tries a real fix.
- Transformation: Fern's smell and social standing both change by the end.
- Inner Monologue: Fern's private thoughts guide the story beats.
- Fable style: concise, animal-led, and ending with a gentle moral.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Callable, Optional

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
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"fox", "wolf", "lion", "bear", "badger", "rabbit", "mouse"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def name_word(self) -> str:
        return self.label or self.id


@dataclass
class Place:
    name: str
    smell_source: str
    supports: set[str] = field(default_factory=set)


@dataclass
class Problem:
    id: str
    cause: str
    effect: str
    fix_hint: str
    transform: str
    keywords: set[str] = field(default_factory=set)


@dataclass
class Aid:
    id: str
    label: str
    method: str
    guards: set[str] = field(default_factory=set)
    covers: set[str] = field(default_factory=set)


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
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
        clone = World(self.place)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]


def _r_problem(world: World) -> list[str]:
    out: list[str] = []
    fox = world.entities.get("hero")
    if not fox:
        return out
    if fox.meters["smell"] < THRESHOLD:
        return out
    sig = ("problem", fox.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    fox.memes["worry"] += 1
    out.append("The fox felt the problem press in around her.")
    return out


def _r_helped(world: World) -> list[str]:
    out: list[str] = []
    fox = world.entities.get("hero")
    if not fox:
        return out
    if fox.meters["fresh"] < THRESHOLD:
        return out
    sig = ("helped", fox.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    fox.memes["hope"] += 1
    out.append("The fox looked ready for a new beginning.")
    return out


CAUSAL_RULES = [Rule("problem", _r_problem), Rule("helped", _r_helped)]


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


def smell_intensity(problem: Problem) -> str:
    return {
        "berries": "sweet and sticky",
        "mud": "earthy and heavy",
        "fish": "sharp and sour",
        "smoke": "dark and bitter",
    }.get(problem.id, "strong")


def moral() -> str:
    return "Moral: a little thought can turn a trouble into a change."


def predict_result(world: World, actor: Entity, problem: Problem, aid: Aid) -> dict:
    sim = world.copy()
    apply_problem(sim, sim.get(actor.id), problem, narrate=False)
    apply_aid(sim, sim.get(actor.id), aid, narrate=False)
    return {
        "fresh": sim.get(actor.id).meters["fresh"] >= THRESHOLD,
        "problem": sim.get(actor.id).meters["smell"] >= THRESHOLD,
        "worry": sim.get(actor.id).memes["worry"],
    }


def apply_problem(world: World, actor: Entity, problem: Problem, narrate: bool = True) -> None:
    actor.meters["smell"] += 1
    actor.memes["embarrassment"] += 1
    if narrate:
        world.say(
            f"{actor.id} had grown {smell_intensity(problem)} with the smell of {problem.cause}."
        )
    propagate(world, narrate=narrate)


def apply_aid(world: World, actor: Entity, aid: Aid, narrate: bool = True) -> None:
    if aid.id == "wash":
        actor.meters["smell"] = 0
        actor.meters["fresh"] += 1
        actor.memes["relief"] += 1
        if narrate:
            world.say(f"She washed in the stream until the smell was gone.")
    elif aid.id == "mint":
        actor.meters["fresh"] += 1
        actor.meters["smell"] = max(0, actor.meters["smell"] - 1)
        actor.memes["relief"] += 1
        if narrate:
            world.say(f"She rolled in mint leaves, and the air around her softened.")
    elif aid.id == "help_others":
        actor.memes["kindness"] += 1
        actor.meters["status"] += 1
        if narrate:
            world.say(f"She carried water for the others, and they looked at her more kindly.")
    propagate(world, narrate=narrate)


def inner_monologue(world: World, actor: Entity, problem: Problem) -> str:
    if actor.meters["smell"] >= THRESHOLD:
        return (
            f'"I smell so strong," thought {actor.id}. '
            f'"If I keep hiding, I will stay lonely. '
            f'"I should find the cause and fix it."'
        )
    return f'"I feel lighter now," thought {actor.id}. "A clean start makes a brave heart."'


def introduce(world: World, hero: Entity, place: Place) -> None:
    world.say(
        f"Once in the {place.name}, {hero.id} was a small {hero.type} who liked quiet paths."
    )


def trouble(world: World, hero: Entity, problem: Problem) -> None:
    world.say(
        f"One day, {hero.id} rolled through {problem.cause}, and then the smell followed her everywhere."
    )
    world.say(
        f"The animals at the meadow supper stepped back, because her smell was {smell_intensity(problem)}."
    )
    world.say(inner_monologue(world, hero, problem))


def solve(world: World, hero: Entity, problem: Problem, aid: Aid) -> None:
    world.say(
        f"{hero.id} searched for the reason and decided, "
        f"'{problem.fix_hint}.'"
    )
    if aid.id == "wash":
        world.say("She found a clear stream and listened to it as if it were giving advice.")
    elif aid.id == "mint":
        world.say("She found mint near the stream, where its green scent grew strong in the shade.")
    elif aid.id == "help_others":
        world.say("She looked for a way to make amends as well as feel clean.")
    apply_aid(world, hero, aid, narrate=True)


def resolution(world: World, hero: Entity, problem: Problem) -> None:
    world.say(
        f"When {hero.id} returned, the smell had changed, and so had her place among the animals."
    )
    world.say(
        f"They welcomed her to the supper, and {hero.id} sat with a calm smile instead of a worried one."
    )
    world.say(moral())


def tell(place: Place, problem: Problem, aid: Aid, hero_name: str = "Fern") -> World:
    world = World(place)
    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type="fox",
        traits=["small", "thoughtful", "curious"],
    ))
    world.facts["problem"] = problem
    world.facts["aid"] = aid
    world.facts["hero"] = hero

    introduce(world, hero, place)
    world.para()
    trouble(world, hero, problem)
    world.para()
    solve(world, hero, problem, aid)
    world.para()
    resolution(world, hero, problem)
    return world


PLACES = {
    "forest": Place(name="forest", smell_source="berries", supports={"wash", "mint", "help_others"}),
    "riverbank": Place(name="riverbank", smell_source="mud", supports={"wash", "mint", "help_others"}),
    "harbor": Place(name="harbor", smell_source="fish", supports={"wash", "help_others"}),
    "campfire": Place(name="campfire", smell_source="smoke", supports={"wash", "help_others"}),
}

PROBLEMS = {
    "berries": Problem(
        id="berries",
        cause="a pile of berries and old leaves",
        effect="sticky smell",
        fix_hint="I should wash in the stream and find mint leaves",
        transform="fresh and welcome",
        keywords={"smell", "berries", "mint"},
    ),
    "mud": Problem(
        id="mud",
        cause="mud stuck to her fur after the rain",
        effect="earthy smell",
        fix_hint="I should rinse off and roll in clean grass",
        transform="clean and steady",
        keywords={"smell", "mud"},
    ),
    "fish": Problem(
        id="fish",
        cause="fish scales clinging to her paws",
        effect="sharp smell",
        fix_hint="I should wash my paws and carry something useful in return",
        transform="helpful and accepted",
        keywords={"smell", "fish"},
    ),
    "smoke": Problem(
        id="smoke",
        cause="smoke from a fire that caught in her fur",
        effect="bitter smell",
        fix_hint="I should step away, wash, and breathe in the cool air",
        transform="clear and brave",
        keywords={"smell", "smoke"},
    ),
}

AIDS = {
    "wash": Aid(id="wash", label="stream washing", method="wash in the stream", guards={"smell"}, covers={"fur"}),
    "mint": Aid(id="mint", label="mint leaves", method="roll in mint leaves", guards={"smell"}, covers={"fur"}),
    "help_others": Aid(id="help_others", label="helping paws", method="carry water for the others", guards={"worry"}, covers=set()),
}

CURATED = [
    ("forest", "berries", "wash"),
    ("riverbank", "mud", "mint"),
    ("harbor", "fish", "help_others"),
]


@dataclass
class StoryParams:
    place: str
    problem: str
    aid: str
    name: str = "Fern"
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for p, place in PLACES.items():
        for prob in PROBLEMS:
            if PROBLEMS[prob].id == place.smell_source or prob in place.supports:
                for aid in AIDS:
                    if aid in place.supports:
                        combos.append((p, prob, aid))
    return combos


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short fable for children that includes the word "smell" and a fox named {f["hero"].id}.',
        f"Tell a story where {f['hero'].id} notices a smell problem, thinks about it, and finds a useful fix.",
        f"Write a gentle animal fable about being embarrassed by a smell, solving the problem, and coming back changed.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero = world.facts["hero"]
    prob = world.facts["problem"]
    aid = world.facts["aid"]
    return [
        QAItem(
            question=f"What problem did {hero.id} have in the story?",
            answer=f"{hero.id} had a strong smell after getting into {prob.cause}.",
        ),
        QAItem(
            question=f"What did {hero.id} think to herself before fixing the problem?",
            answer="She thought that hiding would keep her lonely, so she decided to find the cause and fix it.",
        ),
        QAItem(
            question=f"What helped {hero.id} change by the end?",
            answer=f"{aid.label} helped her become fresh again, and that changed how the other animals welcomed her.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is smell?",
            answer="Smell is the way something reaches your nose and tells you how it seems, like fresh, sweet, muddy, or smoky.",
        ),
        QAItem(
            question="Why do animals wash when they get dirty or smelly?",
            answer="They wash so the dirt or strong smell does not stay on their fur and bother them anymore.",
        ),
        QAItem(
            question="What can mint smell like?",
            answer="Mint often smells cool, fresh, and a little sharp.",
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"  {e.id:8} ({e.type:7}) meters={meters} memes={memes}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts ==", *[f"- {p}" for p in sample.prompts], ""]
    lines.append("== (2) Story questions ==")
    for qa in sample.story_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    lines.append("")
    lines.append("== (3) World knowledge questions ==")
    for qa in sample.world_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    return "\n".join(lines)


ASP_RULES = r"""
smelly(H) :- smell(H).
needs_fix(H) :- smelly(H), cause(H, C).
fresh(H) :- washed(H).
fresh(H) :- minty(H).
changed(H) :- fresh(H), helped_others(H).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        lines.append(asp.fact("smell_source", pid, p.smell_source))
        for s in sorted(p.supports):
            lines.append(asp.fact("supports", pid, s))
    for pid, pr in PROBLEMS.items():
        lines.append(asp.fact("problem", pid))
        lines.append(asp.fact("cause", pid, pr.cause))
    for aid, a in AIDS.items():
        lines.append(asp.fact("aid", aid))
        lines.append(asp.fact("method", aid, a.method))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show place/1."))
    if model:
        print("OK: ASP rules loaded and solved.")
        return 0
    print("MISMATCH: ASP solver returned no model.")
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small fable world about smell, thinking, and change.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--aid", choices=AIDS)
    ap.add_argument("--name", default="Fern")
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
    combos = valid_combos()
    if args.place:
        combos = [c for c in combos if c[0] == args.place]
    if args.problem:
        combos = [c for c in combos if c[1] == args.problem]
    if args.aid:
        combos = [c for c in combos if c[2] == args.aid]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, problem, aid = rng.choice(sorted(combos))
    return StoryParams(place=place, problem=problem, aid=aid, name=args.name)


def generate(params: StoryParams) -> StorySample:
    world = tell(PLACES[params.place], PROBLEMS[params.problem], AIDS[params.aid], params.name)
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
        print(asp_program("#show place/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show place/1. #show problem/1. #show aid/1."))
        print(model)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(StoryParams(place=p, problem=pr, aid=a, name=args.name)) for p, pr, a in CURATED]
    else:
        seen: set[str] = set()
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
