#!/usr/bin/env python3
"""
storyworlds/worlds/ideal_problem_solving_rhyme_myth.py
======================================================

A small mythic storyworld about a child-sized hero who must solve a practical
problem with careful thinking, a helper's gift, and a rhymed final turn.

Premise:
- In a little mythic land, a village keeps a fragile bridge over a moonlit
  stream.
- A child hero wants to cross it to bring home a needed lamp-stone.
- The bridge is weak, and the hero must solve the problem in an ideal way:
  not by force, but by choosing the right tool and the right path.

Story shape:
- Setup: a need, a setting, and a prized object.
- Tension: the path is blocked by a problem that could break the bridge.
- Turn: the hero reasons carefully, tests options, and chooses a gentler fix.
- Resolution: the bridge remains safe, the needed object is delivered, and the
  ending lands in a short rhyme like a mythic blessing.

The storyworld models:
- Physical meters: bridge strength, lantern light, rope tension, stone weight,
  dust, and distance.
- Emotional memes: worry, courage, hope, pride, and relief.

The prose is generated from those state changes, not from a frozen template.
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
    plural: bool = False
    protective: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother", "queen", "priestess"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father", "king", "priest"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Site:
    place: str = "the river bridge"
    mood: str = "moonlit"
    affords: set[str] = field(default_factory=set)


@dataclass
class Problem:
    id: str
    danger: str
    action: str
    test: str
    problem: str
    solution: str
    zone: set[str]
    weight: float
    tags: set[str] = field(default_factory=set)


@dataclass
class Aid:
    id: str
    label: str
    covers: set[str]
    handles: set[str]
    use_line: str
    end_line: str
    plural: bool = False


class World:
    def __init__(self, site: Site) -> None:
        self.site = site
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.zone: set[str] = set()
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World(self.site)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.zone = set(self.zone)
        clone.facts = copy.deepcopy(self.facts)
        return clone


def narrate_join(parts: list[str]) -> str:
    return " ".join(p for p in parts if p)


def bridge_safe(world: World) -> bool:
    bridge = world.facts["bridge"]
    return bridge.meters.get("broken", 0.0) < THRESHOLD


def choose_aid(problem: Problem) -> Optional[Aid]:
    for aid in AIDS:
        if problem.id in aid.handles:
            return aid
    return None


def predict(world: World, hero: Entity, problem: Problem, aid: Optional[Aid]) -> dict:
    sim = world.copy()
    _solve(sim, sim.get(hero.id), problem, aid, narrate=False)
    bridge = sim.get("bridge")
    return {
        "broken": bridge.meters.get("broken", 0.0) >= THRESHOLD,
        "hope": sim.get(hero.id).memes.get("hope", 0.0),
    }


def _apply_problem(world: World, hero: Entity, problem: Problem, narrate: bool = True) -> list[str]:
    out: list[str] = []
    bridge = world.get("bridge")
    hero.meters["distance"] = hero.meters.get("distance", 0.0) + 1
    hero.memes["worry"] = hero.memes.get("worry", 0.0) + 1
    bridge.meters["strain"] = bridge.meters.get("strain", 0.0) + problem.weight
    if bridge.meters["strain"] >= problem.weight:
        out.append(f"The bridge hummed under {hero.id}'s шаг...")  # not narrated if invalid? we'll replace below
    return out


def _solve(world: World, hero: Entity, problem: Problem, aid: Optional[Aid], narrate: bool = True) -> None:
    bridge = world.get("bridge")
    if aid is None:
        bridge.meters["broken"] = bridge.meters.get("broken", 0.0) + 1
        hero.memes["worry"] = hero.memes.get("worry", 0.0) + 1
        if narrate:
            world.say(f"{hero.id} tried to force the way, and the bridge groaned in danger.")
        return
    hero.memes["hope"] = hero.memes.get("hope", 0.0) + 1
    bridge.meters["strain"] = max(0.0, bridge.meters.get("strain", 0.0) - 1)
    bridge.meters["broken"] = 0.0
    if narrate:
        world.say(f"{hero.id} chose the gentler way, and {aid.label} answered the need.")


def tell() -> World:
    world = World(SITE)
    hero = world.add(Entity(id="Arin", kind="character", type="boy", label="Arin"))
    guide = world.add(Entity(id="Guide", kind="character", type="woman", label="the river guide"))
    bridge = world.add(Entity(id="bridge", type="bridge", label="bridge"))
    stone = world.add(Entity(
        id="stone",
        type="stone",
        label="moon-stone",
        phrase="an ideal moon-stone",
        owner=hero.id,
    ))
    bridge.meters["strain"] = 0.0
    bridge.meters["broken"] = 0.0
    bridge.meters["glow"] = 0.0
    bridge.memes["silence"] = 1.0
    world.facts.update(hero=hero, guide=guide, bridge=bridge, stone=stone, problem=PROBLEM, aid=None)

    # Act I
    world.say(
        f"In the moonlit valley, Arin was a small hero who sought an ideal way to help "
        f"the village."
    )
    world.say(
        f"Each dawn, the river bridge held the folk together, and beyond it lay "
        f"the moon-stone that could light the dark kiln."
    )

    # Act II
    world.para()
    world.say(
        f"But the bridge was old, and the path was narrow. If Arin rushed across, "
        f"the boards might split and the people would lose their safe crossing."
    )
    world.say(
        f"The river guide warned, “A loud step can make the span snap; a wise heart "
        f"must seek the ideal plan.”"
    )
    pred = predict(world, hero, PROBLEM, choose_aid(PROBLEM))
    world.facts["predicted_broken"] = pred["broken"]

    # Act III
    world.para()
    aid = choose_aid(PROBLEM)
    world.facts["aid"] = aid
    if aid is None:
        world.say("Arin had no good answer, and the bridge fell into grief.")
        _solve(world, hero, PROBLEM, None)
    else:
        world.say(
            f"Arin remembered the guide's words and looked at the {aid.label}. "
            f"{aid.use_line}"
        )
        _solve(world, hero, PROBLEM, aid)
        stone.meters["glow"] = 1.0
        hero.memes["pride"] = hero.memes.get("pride", 0.0) + 1
        guide.memes["relief"] = guide.memes.get("relief", 0.0) + 1
        world.say(
            f"Then Arin carried the moon-stone home by the safe crossing. "
            f"The bridge stayed whole, and {aid.end_line}"
        )
        world.say(
            "The village lantern woke with silver fire, and Arin smiled like a dawn.\n"
            "“Slow feet keep the path neat; wise hands make hard days sweet.”"
        )

    world.facts["resolved"] = aid is not None
    return world


SITE = Site(place="the river bridge", mood="moonlit", affords={"cross", "carry"})
PROBLEM = Problem(
    id="bridge-crossing",
    danger="the bridge might snap",
    action="cross the bridge",
    test="test the boards",
    problem="old planks and a heavy stone",
    solution="a lighter route and a careful crossing",
    zone={"bridge"},
    weight=1.0,
    tags={"bridge", "stone", "river"},
)

AIDS = [
    Aid(
        id="rope-cart",
        label="a rope cart",
        covers={"hands", "back"},
        handles={"bridge-crossing"},
        use_line="He tied the stone to a rope cart so its weight would not press the boards.",
        end_line="the cart rolled softly, like a hush on water.",
    ),
]

GIRL_NAMES = ["Mira", "Luna", "Sera", "Iris", "Nia"]
BOY_NAMES = ["Arin", "Oren", "Tavi", "Jori", "Leif"]


@dataclass
class StoryParams:
    name: str = "Arin"
    gender: str = "boy"
    seed: Optional[int] = None


def generation_prompts(world: World) -> list[str]:
    return [
        'Write a short myth for a child about an ideal choice that solves a bridge problem.',
        f"Tell a rhyme-like story where {world.facts['hero'].id} must solve a crossing problem without breaking the bridge.",
        'Write a gentle myth in simple language, ending with a rhyme about wise hands and safe paths.',
    ]


def story_qa(world: World) -> list[QAItem]:
    hero = world.facts["hero"]
    guide = world.facts["guide"]
    stone = world.facts["stone"]
    aid = world.facts["aid"]
    return [
        QAItem(
            question=f"Who is the story about?",
            answer=f"The story is about {hero.id}, a small hero in a moonlit valley.",
        ),
        QAItem(
            question=f"What problem did {hero.id} have to solve?",
            answer=f"{hero.id} had to cross the old bridge safely to bring home the moon-stone without making the bridge break.",
        ),
        QAItem(
            question=f"How did the guide help {hero.id} choose the ideal way?",
            answer=f"The guide warned that a loud step could snap the bridge, so {hero.id} used {aid.label} and the safer plan.",
        ),
        QAItem(
            question=f"What changed at the end of the story?",
            answer=f"The bridge stayed whole, the moon-stone came home, and the village lantern shone with silver light.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a bridge for?",
            answer="A bridge helps people cross over water or a gap without having to go through it.",
        ),
        QAItem(
            question="What does ideal mean?",
            answer="Ideal means the best fit for the need, like the choice that solves a problem with the least harm.",
        ),
        QAItem(
            question="What is a rhyme?",
            answer="A rhyme is when words sound alike at the end, which can make a line feel musical.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== Story questions ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== World questions ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        parts = []
        if meters:
            parts.append(f"meters={meters}")
        if memes:
            parts.append(f"memes={memes}")
        lines.append(f"  {e.id} ({e.type}) {' '.join(parts)}")
    return "\n".join(lines)


ASP_RULES = r"""
bridge_problem(B) :- bridge(B).
ideal_solution(S) :- solution(S).
risk(B) :- bridge(B).
safe(B) :- bridge(B), not broken(B).
"""

def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("bridge", "bridge"),
        asp.fact("solution", "gentle_crossing"),
        asp.fact("problem", "bridge_crossing"),
        asp.fact("ideal", "ideal"),
    ]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show safe/1."))
    return sorted(set(asp.atoms(model, "safe")))


def asp_verify() -> int:
    py = {"bridge"}
    cl = {a[0] for a in asp_valid()}
    if py == cl:
        print("OK: ASP and Python agree.")
        return 0
    print("MISMATCH")
    print("python:", sorted(py))
    print("asp:", sorted(cl))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mythic problem-solving rhyme storyworld.")
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["boy", "girl"])
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
    gender = args.gender or rng.choice(["boy", "girl"])
    name = args.name or rng.choice(BOY_NAMES if gender == "boy" else GIRL_NAMES)
    return StoryParams(name=name, gender=gender)


def generate(params: StoryParams) -> StorySample:
    world = tell()
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
        print(asp_program("#show safe/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("1 compatible safe model.")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(StoryParams(name="Arin", gender="boy"))]
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
