#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/pollutant_suspense_humor_problem_solving_fable.py
==============================================================================================================================

A compact fable-style story world about a small village spring, a worrying pollutant,
some nervous investigation, a humorous false alarm, and a cooperative cleanup.

The world is intentionally small and classical:
- a brook feeds a village pond
- an unknown pollutant makes the water look and smell strange
- animals investigate with suspense and a little humor
- they solve the problem with teamwork and a simple tool

The story is generated from world state, not from a frozen paragraph.
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
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"fox", "wolf", "bear", "owl", "hare", "mouse", "toad", "frog"}:
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    id: str
    label: str
    shimmer: str
    odors: list[str] = field(default_factory=list)
    supports: set[str] = field(default_factory=set)


@dataclass
class Pollutant:
    id: str
    label: str
    phrase: str
    kind: str
    smell: str
    color: str
    clue: str
    dangerous: bool = True
    humorous: str = ""


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    cleans: set[str]
    prep: str
    tail: str


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
        import copy as _copy
        w = World(self.place)
        w.entities = _copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        return w


def _polluted_level(world: World) -> float:
    return sum(e.meters.get("pollutant", 0.0) for e in world.entities.values())


def _r_stink(world: World) -> list[str]:
    if _polluted_level(world) < THRESHOLD:
        return []
    sig = ("stink",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    out = []
    for e in world.entities.values():
        if e.kind == "character":
            e.memes["worry"] = e.memes.get("worry", 0.0) + 1
    out.append("A strange smell drifted over the pond, and the little animals grew quiet.")
    return out


def _r_spot_clue(world: World) -> list[str]:
    if _polluted_level(world) < THRESHOLD:
        return []
    sig = ("clue",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    clue = world.facts["pollutant"].clue
    world.facts["clue_seen"] = clue
    return [f"Near the reeds, they spotted {clue}, and the suspense grew deeper."]


def _r_cleanup(world: World) -> list[str]:
    if world.facts.get("cleaned"):
        return []
    if _polluted_level(world) < THRESHOLD:
        return []
    if not world.facts.get("tool_used"):
        return []
    sig = ("cleaned",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    pollutant = world.facts["pollutant"]
    for e in world.entities.values():
        e.meters["pollutant"] = 0.0
    world.facts["cleaned"] = True
    return [f"By sunset, the water was clear again, and the {pollutant.label} was gone."]


CAUSAL_RULES = [_r_stink, _r_spot_clue, _r_cleanup]


def propagate(world: World) -> None:
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                for s in sents:
                    world.say(s)


def predict_clean(world: World, tool: Tool) -> bool:
    sim = world.copy()
    use_tool(sim, tool, narrate=False)
    return bool(sim.facts.get("cleaned"))


def use_tool(world: World, tool: Tool, narrate: bool = True) -> None:
    sig = ("tool", tool.id)
    if sig in world.fired:
        return
    world.fired.add(sig)
    world.facts["tool_used"] = True
    for e in world.entities.values():
        if e.kind == "thing" and e.label in {"spill", "slick film", "dirty foam", "oil sheen"}:
            e.meters["pollutant"] = 0.0
    if narrate:
        world.say(f"They chose {tool.phrase}, and together they began to work.")
    propagate(world)


def introduce(world: World, hero: Entity) -> None:
    world.say(f"In the village by the pond, {hero.label} was known as a careful watcher of small troubles.")


def setup(world: World, hero: Entity, helper: Entity, pollutant: Pollutant) -> None:
    world.say(f"{hero.label} loved the pond because {world.place.shimmer}.")
    world.say(f"One morning, a {pollutant.kind} called {pollutant.label} drifted into the water and made it look {pollutant.color}.")
    world.say(f"It smelled {pollutant.smell}, which made {helper.label} wrinkle {helper.pronoun('possessive')} nose.")
    world.facts["pollutant"] = pollutant


def investigate(world: World, hero: Entity, helper: Entity, pollutant: Pollutant) -> None:
    world.para()
    world.say(f"{hero.label} and {helper.label} went closer, slowly and carefully, because neither knew where the bad smell came from.")
    world.say(f"At first they thought the reeds themselves were guilty, but then {helper.label} sneezed at the wrong moment and startled a fish.")
    world.say(f'"A sneaky fish cannot be the pollutant," {hero.label} said, and {helper.label} let out a sheepish laugh.')
    propagate(world)


def solve(world: World, hero: Entity, helper: Entity, tool: Tool, pollutant: Pollutant) -> None:
    world.para()
    world.say(f"Then {hero.label} noticed the real problem: {pollutant.humorous or pollutant.phrase}.")
    world.say(f"{helper.label} fetched {tool.phrase}, because {tool.prep}.")
    if not predict_clean(world, tool):
        raise StoryError("The chosen tool does not actually solve the pollutant problem.")
    use_tool(world, tool)
    world.say(f"{hero.label} and {helper.label} {tool.tail}, and the pond began to shine again.")


def conclude(world: World, hero: Entity, helper: Entity) -> None:
    world.para()
    world.say(f"By evening, the frogs sang again, the fish swam in peace, and the pond reflected the stars.")
    world.say(f"{hero.label} learned that a small problem can look frightening at first, but patient friends can solve it together.")
    world.say(f"{helper.label} smiled, because the clean water proved that courage, humor, and good sense travel well together.")


PLACE = Place(
    id="pond",
    label="the pond",
    shimmer="the lilies floated like little green boats",
    odors=["fresh grass", "cool water"],
    supports={"worry", "clue", "cleanup"},
)

POLLUTANTS = {
    "oil": Pollutant(
        id="oil",
        label="oil slick",
        phrase="a dark oily spill",
        kind="pollutant",
        smell="sharp and smoky",
        color="rainbow-streaked",
        clue="a shiny trail on the stones",
        humorous="a drop of oil had left a glossy mustache on the water",
    ),
    "sludge": Pollutant(
        id="sludge",
        label="muddy sludge",
        phrase="a blob of muddy sludge",
        kind="pollutant",
        smell="thick and earthy",
        color="brown and cloudy",
        clue="a clump of slime on a broken cart wheel",
        humorous="the sludge looked like chocolate pudding that had forgotten how to be dessert",
    ),
    "soap": Pollutant(
        id="soap",
        label="soap foam",
        phrase="a foamy soap spill",
        kind="pollutant",
        smell="sweet but too strong",
        color="white and fizzy",
        clue="bubbles caught in a bucket handle",
        humorous="the foam wore a frothy crown, as if it were trying to become king of the pond",
    ),
}

TOOLS = {
    "bucket": Tool(
        id="bucket",
        label="bucket",
        phrase="a wide bucket and a long scoop",
        cleans={"oil", "sludge", "soap"},
        prep="it could lift the mess away without making the pond splash everywhere",
        tail="carried the mess to the far bank",
    ),
    "net": Tool(
        id="net",
        label="net",
        phrase="a fine fishing net",
        cleans={"sludge", "soap"},
        prep="it could catch floating bits and bubbles",
        tail="lifted out the clumps and foam",
    ),
    "rags": Tool(
        id="rags",
        label="rags",
        phrase="dry cloths and old rags",
        cleans={"oil", "soap"},
        prep="they could soak up the slickness from the stones",
        tail="wiped the last slippery shine from the edge",
    ),
}

HEROES = ["Milo", "Nina", "Tavi", "Mara", "Pip", "Lena"]
HELPERS = ["Owl", "Turtle", "Fox", "Badger", "Heron", "Hare"]


@dataclass
class StoryParams:
    pollutant: str
    hero: str
    helper: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for pid, pol in POLLUTANTS.items():
        for tid, tool in TOOLS.items():
            if pid in tool.cleans:
                combos.append((PLACE.id, pid, tid))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A fable about a pollutant, suspense, humor, and problem solving.")
    ap.add_argument("--pollutant", choices=POLLUTANTS)
    ap.add_argument("--name")
    ap.add_argument("--helper")
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
    choices = list(POLLUTANTS)
    pollutant = args.pollutant or rng.choice(choices)
    hero = args.name or rng.choice(HEROES)
    helper = args.helper or rng.choice(HELPERS)
    if helper == hero:
        raise StoryError("The hero and helper must be different characters.")
    return StoryParams(pollutant=pollutant, hero=hero, helper=helper, seed=args.seed)


def tell(params: StoryParams) -> World:
    world = World(PLACE)
    hero = world.add(Entity(id="hero", kind="character", type="animal", label=params.hero))
    helper = world.add(Entity(id="helper", kind="character", type="animal", label=params.helper))
    pollutant = POLLUTANTS[params.pollutant]
    world.add(Entity(id="pollution", kind="thing", type="pollutant", label=pollutant.label, phrase=pollutant.phrase, meters={"pollutant": 1.0}))
    intro = hero
    introduce(world, intro)
    setup(world, hero, helper, pollutant)
    investigate(world, hero, helper, pollutant)
    tool = next(t for t in TOOLS.values() if params.pollutant in t.cleans)
    solve(world, hero, helper, tool, pollutant)
    conclude(world, hero, helper)
    world.facts.update(hero=hero, helper=helper, pollutant=pollutant, tool=tool)
    return world


def generation_prompts(world: World) -> list[str]:
    p = world.facts["pollutant"]
    h = world.facts["hero"]
    helper = world.facts["helper"]
    tool = world.facts["tool"]
    return [
        f"Write a short fable about {h.label}, {helper.label}, and a {p.label} near a pond.",
        f"Tell a suspenseful but gentle story in which a pollutant causes worry, then {tool.phrase} solves the problem.",
        f"Create a child-friendly fable with a funny clue, a careful investigation, and a clean ending at the pond.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p = world.facts["pollutant"]
    h = world.facts["hero"]
    helper = world.facts["helper"]
    tool = world.facts["tool"]
    return [
        QAItem(
            question=f"Why did {h.label} and {helper.label} feel worried at the pond?",
            answer=f"They felt worried because a {p.label} polluted the water and made the pond look and smell wrong.",
        ),
        QAItem(
            question=f"What funny detail helped the animals notice the {p.label}?",
            answer=f"They found this clue: {p.humorous}. That helped them see the problem without giving up.",
        ),
        QAItem(
            question=f"How did {h.label} and {helper.label} fix the polluted pond?",
            answer=f"They used {tool.phrase} and worked together until the pollutant was removed and the pond became clear again.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    p = world.facts["pollutant"]
    tool = world.facts["tool"]
    return [
        QAItem(
            question="What is a pollutant?",
            answer="A pollutant is something that should not be in water, air, or soil because it can make the place dirty or unsafe.",
        ),
        QAItem(
            question="Why is clean water important?",
            answer="Clean water helps animals, plants, and people stay healthy, so ponds and streams should be kept clear.",
        ),
        QAItem(
            question=f"What does {tool.label} do in a cleanup?",
            answer=f"{tool.phrase.capitalize()} can help lift or wipe away the mess so the pollutant does not stay in the water.",
        ),
        QAItem(
            question="Why do fables often end with a lesson?",
            answer="Fables often end with a lesson so the listener remembers a wise idea, like staying calm and solving problems together.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
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
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"{e.id}: {e.label} {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
polluted :- pollutant(P), has_pollutant(P), level(P,L), L >= 1.
needs_cleanup(T) :- tool(T), cleans(T,P), has_pollutant(P).
can_solve(P) :- pollutant(P), tool(T), cleans(T,P).
valid_story(P,T) :- pollutant(P), tool(T), cleans(T,P).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid, p in POLLUTANTS.items():
        lines.append(asp.fact("pollutant", pid))
        lines.append(asp.fact("has_pollutant", pid))
        lines.append(asp.fact("level", pid, 1))
    for tid, t in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        for p in sorted(t.cleans):
            lines.append(asp.fact("cleans", tid, p))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    cl = set(asp_valid_combos())
    py = {(p, t) for _, p, t in valid_combos()}
    if cl == py:
        print(f"OK: ASP and Python agree on {len(py)} solvable pollutant/tool pairs.")
        return 0
    print("MISMATCH between ASP and Python:")
    print(" only ASP:", sorted(cl - py))
    print(" only Python:", sorted(py - cl))
    return 1


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
    StoryParams(pollutant="oil", hero="Milo", helper="Turtle"),
    StoryParams(pollutant="sludge", hero="Nina", helper="Fox"),
    StoryParams(pollutant="soap", hero="Tavi", helper="Hare"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.verify:
        sys.exit(asp_verify())
    if args.show_asp:
        print(asp_program("#show valid_story/2."))
        return
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} ASP-solvable pollutant/tool pairs:")
        for p, t in combos:
            print(f"  {p} -> {t}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 20, 20):
            rng = random.Random(base_seed + i)
            i += 1
            try:
                params = resolve_params(args, rng)
            except StoryError as err:
                print(err)
                return
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
