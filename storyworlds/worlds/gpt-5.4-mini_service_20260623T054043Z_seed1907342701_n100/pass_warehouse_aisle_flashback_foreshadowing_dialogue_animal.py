#!/usr/bin/env python3
"""
storyworlds/worlds/pass_warehouse_aisle_flashback_foreshadowing_dialogue_animal.py
=================================================================================

A small animal-story world set in a warehouse aisle.

Premise:
- An animal character is trying to pass through a warehouse aisle with a small
  item that matters to them.
- The aisle has a simple obstacle or worry.
- A flashback reveals why the item or route matters.
- Foreshadowing hints that a helpful choice is coming.
- Dialogue carries the turn.
- The ending proves what changed in the aisle.

The domain is intentionally tiny: a few places, a few items, a few helpers, and
one central verb, "pass", which can mean either move through a space or hand
something along.
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
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    plural: bool = False

    def pronoun(self, case: str = "subject") -> str:
        male = {"boy", "father", "dad", "man"}
        female = {"girl", "mother", "mom", "woman"}
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    id: str
    label: str
    clutter: str
    afford: set[str] = field(default_factory=set)


@dataclass
class Problem:
    id: str
    label: str
    clue: str
    block: str
    meter: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    helps: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Keep:
    id: str
    label: str
    phrase: str
    value: str
    carried_by: str = ""
    plural: bool = False
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.flashback_done = False
        self.foreshadow_done = False
        self.route_open = False

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
        clone = World(self.place)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.facts = copy.deepcopy(self.facts)
        clone.flashback_done = self.flashback_done
        clone.foreshadow_done = self.foreshadow_done
        clone.route_open = self.route_open
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_clear_route(world: World) -> list[str]:
    out = []
    if not world.facts.get("route_passable"):
        return out
    if world.route_open:
        return out
    sig = ("route_open", world.place.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.route_open = True
    out.append("__route_open__")
    return out


CAUSAL_RULES = [Rule("route_open", "physical", _r_clear_route)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            got = rule.apply(world)
            if got:
                changed = True
                produced.extend(g for g in got if not g.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def route_at_risk(problem: Problem, place: Place) -> bool:
    return problem.id in place.afford


def helper_fits(problem: Problem, tool: Tool, keep: Keep) -> bool:
    return problem.id == tool.helps and keep.value == "important"


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for place_id, place in PLACES.items():
        for prob_id, prob in PROBLEMS.items():
            if not route_at_risk(prob, place):
                continue
            for tool_id, tool in TOOLS.items():
                for keep_id, keep in KEEPS.items():
                    if helper_fits(prob, tool, keep):
                        combos.append((place_id, prob_id, tool_id, keep_id))
    return combos


def choose_name(rng: random.Random, animal: str) -> str:
    if animal == "mouse":
        return rng.choice(["Milo", "Mina", "Pip", "Nia", "Toby", "Luna"])
    if animal == "cat":
        return rng.choice(["Mittens", "Clover", "Poppy", "Roo", "Tessa"])
    return rng.choice(["Hugo", "Daisy", "Wren", "Sunny", "Bea"])


def build_flashback(hero: Entity, keep: Entity) -> str:
    return (
        f"{hero.id} remembered a small day when {hero.pronoun('possessive')} "
        f"{keep.label} had slipped from a shelf and rolled under a box. "
        f"That was when {hero.id} learned to keep it close."
    )


def build_foreshadow(problem: Problem, tool: Tool) -> str:
    return (
        f"Something in the aisle gave a little warning: the stacked boxes leaned "
        f"toward {problem.label}, and the {tool.label} waited nearby like it knew "
        f"someone would need it."
    )


def setup(world: World, hero: Entity, helper: Entity, keep: Entity, problem: Problem) -> None:
    hero.memes["care"] += 1
    hero.memes["worry"] += 1
    helper.memes["patience"] += 1
    keep.carried_by = hero.id
    world.say(
        f"{hero.id} padded into the {world.place.label}, where the {world.place.clutter} made the aisle feel narrow."
    )
    world.say(
        f"{hero.id} had {hero.pronoun('possessive')} {keep.label} and wanted to pass through without dropping it."
    )
    world.say(build_flashback(hero, keep))
    world.para()
    world.say(build_foreshadow(problem, world.facts["tool"]))
    world.say(
        f"At the far end, {helper.id} looked up and said, "
        f"\"If the boxes slide, we can pass together.\""
    )


def tension(world: World, hero: Entity, helper: Entity, problem: Problem) -> None:
    hero.memes["stuck"] += 1
    world.say(
        f"But the {problem.label} blocked the way, and {hero.id} stopped with a little sigh."
    )
    world.say(
        f"\"I can't pass,\" {hero.id} said. \"The {problem.label} is in the way.\""
    )
    world.say(
        f"\"You can,\" {helper.id} said. \"We just have to do it carefully.\""
    )


def solve(world: World, hero: Entity, helper: Entity, keep: Keep, tool: Tool, problem: Problem) -> None:
    world.facts["route_passable"] = True
    propagate(world, narrate=False)
    world.say(
        f"{helper.id} nudged the small boxes aside and passed {tool.phrase} to {hero.id}."
    )
    world.say(
        f"{hero.id} used the {tool.label} to steady the stack, then passed the {keep.label} to {helper.id} for a moment."
    )
    hero.memes["relief"] += 1
    helper.memes["relief"] += 1
    world.say(
        f"\"There,\" {helper.id} said. \"Now we can pass.\""
    )
    world.say(
        f"Together they walked down the aisle, and the {problem.label} was no longer blocking the way."
    )


def tell(place: Place, problem: Problem, tool: Tool, keep: Keep,
         hero_name: str = "Milo", animal: str = "mouse",
         helper_name: str = "Clover", helper_animal: str = "cat") -> World:
    world = World(place)
    hero = world.add(Entity(id=hero_name, kind="character", type=animal, role="hero"))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_animal, role="helper"))
    keep_ent = world.add(Entity(id="keep", kind="thing", type="package", label=keep.label, phrase=keep.phrase, plural=keep.plural))
    route = world.add(Entity(id="route", kind="thing", type="route", label="the aisle", phrase="the aisle"))
    obstacle = world.add(Entity(id="obstacle", kind="thing", type=problem.id, label=problem.label))
    toolbox = world.add(Entity(id="tool", kind="thing", type=tool.id, label=tool.label))
    world.facts.update(
        hero=hero,
        helper=helper,
        keep=keep_ent,
        route=route,
        obstacle=obstacle,
        tool=toolbox,
        problem=problem,
        place=place,
        route_passable=False,
    )

    setup(world, hero, helper, keep_ent, problem)
    world.para()
    tension(world, hero, helper, problem)
    world.para()
    solve(world, hero, helper, keep_ent, tool, problem)
    world.facts["resolved"] = True
    return world


SETTINGS = {
    "aisle_a": Place(id="aisle_a", label="warehouse aisle", clutter="tall shelves and shiny boxes", afford={"spill", "cart", "rope"}),
    "aisle_b": Place(id="aisle_b", label="warehouse aisle", clutter="labels, pallets, and stacked crates", afford={"spill", "cart", "rope"}),
    "aisle_c": Place(id="aisle_c", label="warehouse aisle", clutter="boxes and low pallets", afford={"spill", "cart"}),
    "aisle_d": Place(id="aisle_d", label="warehouse aisle", clutter="forklifts sleeping by the wall", afford={"cart", "rope"}),
}

PLACES = SETTINGS

PROBLEMS = {
    "spill": Problem(id="spill", label="a spilled crate of apples", clue="a wet red shine", block="makes the floor slippery", meter="slip", tags={"spill", "fruit"}),
    "cart": Problem(id="cart", label="a tipped cart", clue="one wheel pointing up", block="blocks the center of the aisle", meter="block", tags={"cart"}),
    "rope": Problem(id="rope", label="a loose rope coil", clue="a loop on the floor", block="can trip small feet", meter="trip", tags={"rope"}),
}

TOOLS = {
    "hook": Tool(id="hook", label="a hook stick", phrase="the hook stick", helps="spill", tags={"hook"}),
    "handle": Tool(id="handle", label="a cart handle", phrase="the cart handle", helps="cart", tags={"handle"}),
    "broom": Tool(id="broom", label="a broom", phrase="the broom", helps="rope", tags={"broom"}),
}

KEEPS = {
    "seedbag": Keep(id="seedbag", label="seed bag", phrase="a tiny seed bag", value="important", plural=False, tags={"seed"}),
    "note": Keep(id="note", label="note", phrase="a folded note", value="important", plural=False, tags={"note"}),
    "snack": Keep(id="snack", label="snack pouch", phrase="a snack pouch", value="important", plural=False, tags={"snack"}),
}

ANIMALS = ["mouse", "cat", "rabbit"]


@dataclass
class StoryParams:
    place: str
    problem: str
    tool: str
    keep: str
    hero_name: str = "Milo"
    hero_animal: str = "mouse"
    helper_name: str = "Clover"
    helper_animal: str = "cat"
    seed: Optional[int] = None


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    problem = f["problem"]
    tool = f["tool"]
    keep = f["keep"]
    return [
        f'Write an animal story set in a warehouse aisle where {hero.id} needs to pass through while carrying {keep.label}.',
        f"Tell a gentle story where {hero.id} and {helper.id} talk in dialogue about how to pass a blocked warehouse aisle.",
        f'Write a short story that includes the word "pass" and ends with {keep.label} safely moving through the warehouse aisle.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    problem = f["problem"]
    tool = f["tool"]
    keep = f["keep"]
    place = f["place"].label
    return [
        QAItem(
            question=f"Why did {hero.id} need help passing through the {place}?",
            answer=f"{problem.label.capitalize()} blocked the aisle, so {hero.id} could not pass easily while carrying {keep.label}. {helper.id} helped by making a safe path and handing over {tool.label}.",
        ),
        QAItem(
            question=f"What did {hero.id} remember before trying to pass the shelves?",
            answer=f"{hero.id} remembered a time when {keep.label} slipped from a shelf. That flashback made {hero.id} careful about keeping it close.",
        ),
        QAItem(
            question=f"What did {helper.id} say that hinted the problem could be fixed?",
            answer=f"{helper.id} said, \"If the boxes slide, we can pass together.\" That was foreshadowing, because it hinted that a careful move would open the way.",
        ),
        QAItem(
            question=f"How did {hero.id} and {helper.id} end the trip through the aisle?",
            answer=f"They passed slowly together, and the {problem.label} was no longer blocking the way. In the end, {keep.label} made it through safely.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does it mean to pass through a place?",
            answer="To pass through a place means to move along it and go from one end to the other. In a narrow aisle, that can mean walking carefully past shelves and boxes.",
        ),
        QAItem(
            question="What is foreshadowing in a story?",
            answer="Foreshadowing is a clue that hints something will matter later. It helps the reader expect what may happen next.",
        ),
        QAItem(
            question="What is a flashback in a story?",
            answer="A flashback is a short look back at something that happened earlier. It helps explain why a character feels careful or worried now.",
        ),
        QAItem(
            question="Why do animals in stories talk so much?",
            answer="Animal stories often give animals human speech so they can share feelings, plans, and mistakes in a simple way children can follow.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    parts = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        parts.append(f"{i}. {p}")
    parts.append("")
    parts.append("== (2) Story questions ==")
    for q in sample.story_qa:
        parts.append(f"Q: {q.question}")
        parts.append(f"A: {q.answer}")
    parts.append("")
    parts.append("== (3) World-knowledge questions ==")
    for q in sample.world_qa:
        parts.append(f"Q: {q.question}")
        parts.append(f"A: {q.answer}")
    return "\n".join(parts)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if any(v for v in e.meters.values()):
            bits.append(f"meters={dict((k, v) for k, v in e.meters.items() if v)}")
        if any(v for v in e.memes.values()):
            bits.append(f"memes={dict((k, v) for k, v in e.memes.items() if v)}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  route_open={world.route_open}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="aisle_a", problem="spill", tool="hook", keep="seedbag", hero_name="Milo", hero_animal="mouse", helper_name="Clover", helper_animal="cat"),
    StoryParams(place="aisle_b", problem="cart", tool="handle", keep="note", hero_name="Nia", hero_animal="rabbit", helper_name="Poppy", helper_animal="cat"),
    StoryParams(place="aisle_c", problem="spill", tool="hook", keep="snack", hero_name="Toby", hero_animal="mouse", helper_name="Daisy", helper_animal="rabbit"),
    StoryParams(place="aisle_d", problem="rope", tool="broom", keep="seedbag", hero_name="Luna", hero_animal="cat", helper_name="Moss", helper_animal="rabbit"),
]


def explain_rejection(problem: Problem, place: Place) -> str:
    return f"(No story: {problem.label} does not make sense for {place.label}.)"


def asp_facts() -> str:
    import asp
    lines = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        for a in sorted(p.afford):
            lines.append(asp.fact("affords", pid, a))
    for pid, p in PROBLEMS.items():
        lines.append(asp.fact("problem", pid))
        lines.append(asp.fact("blocks", pid, p.meter))
    for tid, t in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        lines.append(asp.fact("helps", tid, t.helps))
    for kid, k in KEEPS.items():
        lines.append(asp.fact("keep", kid))
        lines.append(asp.fact("important_keep", kid))
    return "\n".join(lines)


ASP_RULES = r"""
valid(P, R, T, K) :- place(P), problem(R), tool(T), keep(K), affords(P, R), helps(T, R), important_keep(K).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    ok = py == cl
    if ok:
        print(f"OK: ASP matches valid_combos() ({len(py)} combos).")
    else:
        print("MISMATCH between ASP and Python.")
        print("only python:", sorted(py - cl))
        print("only asp:", sorted(cl - py))
    try:
        sample = generate(CURATED[0])
        _ = sample.story
        print("OK: generate() smoke test passed.")
    except Exception as exc:
        print(f"FAILED smoke test: {exc}")
        ok = False
    return 0 if ok else 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal story world in a warehouse aisle.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--keep", choices=KEEPS)
    ap.add_argument("--hero-name")
    ap.add_argument("--hero-animal", choices=ANIMALS)
    ap.add_argument("--helper-name")
    ap.add_argument("--helper-animal", choices=ANIMALS)
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
              and (args.problem is None or c[1] == args.problem)
              and (args.tool is None or c[2] == args.tool)
              and (args.keep is None or c[3] == args.keep)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, problem, tool, keep = rng.choice(sorted(combos))
    hero_animal = args.hero_animal or rng.choice(ANIMALS)
    helper_animal = args.helper_animal or rng.choice([a for a in ANIMALS if a != hero_animal])
    return StoryParams(
        place=place, problem=problem, tool=tool, keep=keep,
        hero_name=args.hero_name or choose_name(rng, hero_animal),
        hero_animal=hero_animal,
        helper_name=args.helper_name or choose_name(rng, helper_animal),
        helper_animal=helper_animal,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES or params.problem not in PROBLEMS or params.tool not in TOOLS or params.keep not in KEEPS:
        raise StoryError("Invalid StoryParams.")
    place = PLACES[params.place]
    problem = PROBLEMS[params.problem]
    tool = TOOLS[params.tool]
    keep = KEEPS[params.keep]
    if not route_at_risk(problem, place) or not helper_fits(problem, tool, keep):
        raise StoryError(explain_rejection(problem, place))
    world = tell(place, problem, tool, keep, params.hero_name, params.hero_animal, params.helper_name, params.helper_animal)
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
        print(asp_program("#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} valid combos:")
        for row in combos:
            print("  ", row)
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
                sample = generate(params)
            except StoryError as err:
                print(err)
                return
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
