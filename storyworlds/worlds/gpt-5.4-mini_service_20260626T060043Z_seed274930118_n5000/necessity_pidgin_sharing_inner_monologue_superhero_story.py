#!/usr/bin/env python3
"""
A standalone storyworld script for a tiny superhero tale about necessity, pidgin,
sharing, and inner monologue.

The premise:
- A small hero hears a distressed neighbor in pidgin and realizes the city has a
  simple need.
- The hero cannot solve the problem alone, so the turning point is sharing
  power, tools, or attention.
- The ending proves the need was met and the city feels safer.

This world is intentionally small and constraint-driven: a story is generated
only when the hero's action, the problem, and the available shareable aid fit
together.
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
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    helper: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def item_pronoun(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Hero:
    name: str
    type: str
    trait: str
    power: str


@dataclass
class Problem:
    id: str
    need: str
    pidgin: str
    inner_monologue: str
    risk: str
    location: str


@dataclass
class Shareable:
    id: str
    label: str
    phrase: str
    helps: set[str]
    action: str
    result: str
    plural: bool = False


class World:
    def __init__(self, city: str) -> None:
        self.city = city
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}

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
        c = World(self.city)
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = dict(self.facts)
        return c


CITY = {
    "harbor": "the harbor",
    "midtown": "Midtown",
    "skyline": "Skyline Avenue",
    "market": "the market square",
}

HEROES = [
    Hero("Nova", "girl", "brave", "spark shield"),
    Hero("Bolt", "boy", "quick", "wind dash"),
    Hero("Mica", "girl", "kind", "light step"),
    Hero("Flux", "boy", "careful", "glow thread"),
]

PROBLEMS = {
    "bridge_lamp": Problem(
        id="bridge_lamp",
        need="light",
        pidgin="Dis wan lamp gone dark, please help.",
        inner_monologue="Nova thought, Someone is waiting in the dark, and that is a real need, not a small fuss.",
        risk="the bridge is too dark for safe footsteps",
        location="under the bridge",
    ),
    "rising_water": Problem(
        id="rising_water",
        need="rope",
        pidgin="Water dey rise, and we need rope quick!",
        inner_monologue="Bolt thought, If nobody shares rope now, the whole walkway can get cut off.",
        risk="the path may close before people cross",
        location="at the river stairs",
    ),
    "stuck_bus": Problem(
        id="stuck_bus",
        need="power",
        pidgin="Bus no move, but everybody need go home.",
        inner_monologue="Mica thought, This is the kind of moment when one helper is not enough.",
        risk="families could be stranded after sunset",
        location="by the bus stop",
    ),
}

SHARERS = [
    Shareable(
        id="lantern",
        label="lantern light",
        phrase="a bright lantern from the rescue shed",
        helps={"light"},
        action="share the lantern light",
        result="the dark path became easy to see",
    ),
    Shareable(
        id="rope",
        label="strong rope",
        phrase="the city's strong rope coil",
        helps={"rope"},
        action="share the strong rope",
        result="the crossing could be tied down safely",
    ),
    Shareable(
        id="charge_pack",
        label="battery pack",
        phrase="a charged battery pack from the hero belt",
        helps={"power"},
        action="share the battery pack",
        result="the bus lights hummed back on",
    ),
]

CURATED = [
    ("harbor", "bridge_lamp", 0),
    ("midtown", "stuck_bus", 1),
    ("skyline", "rising_water", 2),
]


@dataclass
class StoryParams:
    city: str
    problem: str
    hero: str
    seed: Optional[int] = None


ASP_RULES = r"""
city(C) :- city_name(C).
need(P,N) :- problem(P), problem_need(P,N).
shareable(S,N) :- share_item(S), helps_need(S,N).
compatible(C,P,S) :- city(C), problem(P), need(P,N), shareable(S,N).
valid_story(C,P,S) :- compatible(C,P,S).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for cid in CITY:
        lines.append(asp.fact("city_name", cid))
    for pid, prob in PROBLEMS.items():
        lines.append(asp.fact("problem", pid))
        lines.append(asp.fact("problem_need", pid, prob.need))
    for s in SHARERS:
        lines.append(asp.fact("share_item", s.id))
        for need in sorted(s.helps):
            lines.append(asp.fact("helps_need", s.id, need))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for city in CITY:
        for pid, prob in PROBLEMS.items():
            for s in SHARERS:
                if prob.need in s.helps:
                    out.append((city, pid, s.id))
    return out


def tell(city_key: str, problem_key: str, hero: Hero) -> World:
    world = World(CITY[city_key])
    hero_ent = world.add(Entity(id=hero.name, kind="character", type=hero.type))
    prob = PROBLEMS[problem_key]
    share = next(s for s in SHARERS if prob.need in s.helps)

    world.say(
        f"In {world.city}, {hero_ent.id} was a {hero.trait} little hero with a {hero.power}."
    )
    world.say(
        f"One afternoon, a voice called out, \"{prob.pidgin}\""
    )
    world.say(prob.inner_monologue)
    world.say(
        f"{hero_ent.id} looked at the problem and knew the need was plain: {prob.need}."
    )

    world.para()
    world.say(
        f"{hero_ent.id} flew to {prob.location}, where the danger was real: {prob.risk}."
    )
    world.say(
        f"Instead of trying to do everything alone, {hero_ent.id} chose to {share.action}."
    )
    world.say(
        f"{hero_ent.id} shared {share.phrase} with the people who needed it."
    )

    world.para()
    world.say(
        f"That simple choice changed the whole block. {share.result}."
    )
    world.say(
        f"The voices in the street softened, and {hero_ent.id} thought that sharing was not small at all; it was exactly what the city needed."
    )

    world.facts.update(
        hero=hero_ent,
        problem=prob,
        share=share,
        city=city_key,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    prob = f["problem"]
    return [
        f'Write a short superhero story for a child where {hero.id} hears pidgin and meets a real necessity.',
        f'Create a gentle action story in which a hero named {hero.id} notices "{prob.pidgin}" and solves the problem by sharing.',
        f'Write a tiny superhero tale with an inner monologue, a street problem, and a shared helper that makes the city safer.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    prob = f["problem"]
    share = f["share"]
    return [
        QAItem(
            question=f"What did {hero.id} hear in the city?",
            answer=f"{hero.id} heard a plea in pidgin: \"{prob.pidgin}\"",
        ),
        QAItem(
            question=f"What need did {hero.id} understand from the problem?",
            answer=f"{hero.id} understood that the real necessity was {prob.need}.",
        ),
        QAItem(
            question=f"How did {hero.id} solve the problem?",
            answer=f"{hero.id} solved it by choosing to {share.action} instead of trying to act alone.",
        ),
        QAItem(
            question=f"What did {hero.id} think to themself before acting?",
            answer=f"{hero.id}'s inner monologue showed that the danger was serious and that sharing would help.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does necessity mean?",
            answer="Necessity means something that is needed right away, not something extra.",
        ),
        QAItem(
            question="What is pidgin?",
            answer="Pidgin is a simple way of speaking that helps people from different language backgrounds understand each other.",
        ),
        QAItem(
            question="Why do superheroes share in a team story?",
            answer="They share because some jobs are too big for one hero, and sharing makes the rescue work better and safer.",
        ),
        QAItem(
            question="What is an inner monologue?",
            answer="An inner monologue is the quiet thinking a character does inside their own head before acting.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story Q&A ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== World Q&A ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: type={e.type}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Superhero storyworld: necessity, pidgin, sharing, inner monologue.")
    ap.add_argument("--city", choices=CITY)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--hero")
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
    if args.city and args.problem:
        if (args.city, args.problem, next(s.id for s in SHARERS if PROBLEMS[args.problem].need in s.helps)) not in combos:
            raise StoryError("No valid story matches those explicit choices.")
    valid = [(c, p) for c, p, _ in combos if (args.city is None or c == args.city) and (args.problem is None or p == args.problem)]
    if not valid:
        raise StoryError("No valid combination matches the given options.")
    city, problem = rng.choice(valid)
    hero = args.hero or rng.choice([h.name for h in HEROES])
    return StoryParams(city=city, problem=problem, hero=hero)


def generate(params: StoryParams) -> StorySample:
    hero = next(h for h in HEROES if h.name == params.hero)
    world = tell(params.city, params.problem, hero)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    import asp
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP matches Python ({len(py)} combos).")
        return 0
    print("MISMATCH:")
    print("only python:", sorted(py - cl))
    print("only asp:", sorted(cl - py))
    return 1


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} valid combos:")
        for c in combos:
            print(c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for city, problem, hero_idx in CURATED:
            params = StoryParams(city=city, problem=problem, hero=HEROES[hero_idx].name, seed=base_seed)
            samples.append(generate(params))
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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
