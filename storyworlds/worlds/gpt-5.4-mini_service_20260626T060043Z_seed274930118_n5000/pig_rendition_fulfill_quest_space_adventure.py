#!/usr/bin/env python3
"""
storyworlds/worlds/pig_rendition_fulfill_quest_space_adventure.py
===================================================================

A standalone story world for a tiny Space Adventure tale about a pig who goes
on a quest and tries to fulfill it.

Premise:
- A small pig on a ship wants to finish a quest.
- A captain or crew member worries that the quest route is unsafe.
- The pig must choose a better route, tool, or helper to succeed.
- The ending proves the quest was fulfilled in a concrete, state-driven way.

This world keeps the prose child-facing and the simulation simple:
physical meters track fuel, distance, damage, and supplies;
emotional memes track courage, worry, trust, and pride.

The story intentionally uses the seed words:
- pig
- rendition
- fulfill

And it includes the feature:
- Quest
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
    carried_by: Optional[str] = None
    plural: bool = False
    protective: bool = False
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for k in ["fuel", "distance", "damage", "cargo", "signal"]:
            self.meters.setdefault(k, 0.0)
        for k in ["curiosity", "worry", "courage", "trust", "pride", "relief"]:
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"pig", "child", "crew", "pilot"}:
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Ship:
    name: str = "the starship"
    place: str = "deep space"
    route: str = "the glowing comet trail"
    hazards: set[str] = field(default_factory=set)
    safe_tool: str = "a bright guidance map"


@dataclass
class Quest:
    id: str
    goal: str
    needed: str
    unsafe_in: set[str]
    safe_tool: str
    reward: str
    keyword: str = "quest"
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    quest: str
    route: str
    name: str
    role: str
    helper: str
    seed: Optional[int] = None


class World:
    def __init__(self, ship: Ship) -> None:
        self.ship = ship
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.route_state: str = "unknown"

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
        c = World(copy.deepcopy(self.ship))
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.route_state = self.route_state
        return c

    def crew(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]


def _advance(world: World, actor: Entity, quest: Quest, narrate: bool = True) -> None:
    actor.meters["distance"] += 1
    actor.meters["fuel"] += 1
    if quest.id == "comet_mail":
        actor.meters["signal"] += 1
    if narrate:
        world.say(f"{actor.id} went farther along the route.")


def _risk(world: World, actor: Entity, quest: Quest) -> bool:
    return world.ship.route in quest.unsafe_in


def _needs_tool(world: World, actor: Entity, quest: Quest) -> bool:
    return quest.safe_tool in world.ship.safe_tool or quest.safe_tool == world.ship.safe_tool


def _predict_success(world: World, actor: Entity, quest: Quest) -> dict:
    sim = world.copy()
    sim.get(actor.id).memes["courage"] += 1
    sim.get(actor.id).meters["fuel"] += 1
    if quest.safe_tool == sim.ship.safe_tool:
        sim.get(actor.id).memes["trust"] += 1
        sim.get(actor.id).meters["damage"] += 0
    else:
        sim.get(actor.id).meters["damage"] += 1
    return {
        "damage": sim.get(actor.id).meters["damage"] >= THRESHOLD,
        "fuel": sim.get(actor.id).meters["fuel"],
    }


def introduce(world: World, pig: Entity) -> None:
    world.say(
        f"{pig.id} was a small pig with a shiny nose who liked looking out at the stars."
    )


def love_quest(world: World, pig: Entity, quest: Quest) -> None:
    pig.memes["curiosity"] += 1
    world.say(
        f"{pig.id} loved a good {quest.keyword}, and this {quest.keyword} asked {pig.pronoun('object')} to "
        f"{quest.goal}."
    )


def set_out(world: World, pig: Entity, helper: Entity, quest: Quest) -> None:
    world.say(
        f"On the {world.ship.name}, {pig.id} and {helper.id} watched the {world.ship.route} ahead."
    )
    world.say(
        f"{pig.id} wanted to {quest.goal}, but {helper.id} worried the path might be too risky."
    )


def warn(world: World, helper: Entity, pig: Entity, quest: Quest) -> bool:
    pred = _predict_success(world, pig, quest)
    if pred["damage"]:
        helper.memes["worry"] += 1
        world.say(
            f'"If we rush in, {pig.id}, you could get banged up," {helper.id} said. '
            f'"We need the right tool to {quest.goal}."'
        )
        return True
    return False


def insist(world: World, pig: Entity, quest: Quest) -> None:
    pig.memes["courage"] += 1
    world.say(
        f"{pig.id} still wanted to go, and {pig.id} took one brave step toward the glowing route."
    )


def choose_tool(world: World, helper: Entity, pig: Entity, quest: Quest) -> Optional[Entity]:
    if world.ship.safe_tool != quest.safe_tool:
        return None
    tool = world.add(Entity(
        id="tool",
        kind="thing",
        type="tool",
        label=quest.safe_tool,
        phrase=quest.safe_tool,
        owner=pig.id,
        protective=True,
    ))
    tool.carried_by = pig.id
    helper.memes["trust"] += 1
    world.say(
        f"{helper.id} lifted {quest.safe_tool} and said, "
        f'"This should help {pig.id} fulfill the {quest.keyword}."'
    )
    return tool


def fulfill_quest(world: World, pig: Entity, helper: Entity, quest: Quest, tool: Optional[Entity]) -> None:
    pig.memes["pride"] += 1
    pig.memes["worry"] = max(0.0, pig.memes["worry"] - 1)
    pig.memes["relief"] += 1
    world.ship.place = "the quest chamber"
    world.route_state = "cleared"
    _advance(world, pig, quest, narrate=False)
    world.say(
        f"With the {quest.safe_tool}, {pig.id} could follow the route safely and reach the quest chamber."
    )
    world.say(
        f"{pig.id} used the tool, {quest.goal}, and at last {pig.pronoun('subject')} could fulfill the quest."
    )
    world.say(
        f"{helper.id} smiled as the ship lights shimmered around them, and the starry rendition of the mission was complete."
    )


def tell(ship: Ship, quest: Quest, hero_name: str, role: str, helper_name: str) -> World:
    world = World(ship)
    pig = world.add(Entity(id=hero_name, kind="character", type=role, label="pig"))
    helper = world.add(Entity(id=helper_name, kind="character", type="pilot", label="crew mate"))
    questor = world.add(Entity(id="quest", kind="thing", type="quest", label=quest.keyword))
    questor.meters["distance"] = 0

    introduce(world, pig)
    love_quest(world, pig, quest)
    world.para()
    set_out(world, pig, helper, quest)
    warn(world, helper, pig, quest)
    insist(world, pig, quest)
    tool = choose_tool(world, helper, pig, quest)
    world.para()
    fulfill_quest(world, pig, helper, quest, tool)

    world.facts.update(
        pig=pig,
        helper=helper,
        quest=quest,
        ship=ship,
        tool=tool,
        role=role,
    )
    return world


QUESTS = {
    "comet_mail": Quest(
        id="comet_mail",
        goal="deliver the comet mail to the far moon",
        needed="a bright guidance map",
        unsafe_in={"storm lane", "asteroid belt"},
        safe_tool="a bright guidance map",
        reward="a silver star badge",
        keyword="quest",
        tags={"space", "mail", "comet", "quest"},
    ),
    "moon_seed": Quest(
        id="moon_seed",
        goal="plant the moon seed in the bright crater",
        needed="a moon lantern",
        unsafe_in={"dark tunnel", "asteroid belt"},
        safe_tool="a moon lantern",
        reward="a shining sprout",
        keyword="Quest",
        tags={"moon", "seed", "quest"},
    ),
    "ring_song": Quest(
        id="ring_song",
        goal="sing the ring song to wake the sleepy satellites",
        needed="a silver microphone",
        unsafe_in={"storm lane"},
        safe_tool="a silver microphone",
        reward="a glowing chorus",
        keyword="quest",
        tags={"song", "satellite", "quest"},
    ),
}

ROUTES = {
    "storm": Ship(name="the starship", place="storm lane", route="storm lane", hazards={"storm lane"}, safe_tool="a bright guidance map"),
    "belt": Ship(name="the starship", place="asteroid belt", route="asteroid belt", hazards={"asteroid belt"}, safe_tool="a moon lantern"),
    "quiet": Ship(name="the starship", place="quiet orbit", route="quiet orbit", hazards=set(), safe_tool="a silver microphone"),
}

NAMES = ["Pip", "Milo", "Nia", "Luna", "Rex", "Tavi"]
HELPERS = ["Captain Ray", "Pilot June", "Engineer Sol"]
ROLES = ["pig"]


@dataclass
class _Rule:
    name: str


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tiny Space Adventure storyworld about a pig and a quest.")
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--route", choices=ROUTES)
    ap.add_argument("--name")
    ap.add_argument("--role", choices=ROLES)
    ap.add_argument("--helper", choices=HELPERS)
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
    quest = args.quest or rng.choice(list(QUESTS))
    route = args.route or rng.choice(list(ROUTES))
    name = args.name or rng.choice(NAMES)
    role = args.role or "pig"
    helper = args.helper or rng.choice(HELPERS)
    if args.quest and args.route:
        q = QUESTS[args.quest]
        s = ROUTES[args.route]
        if s.route in q.unsafe_in and s.safe_tool != q.safe_tool:
            raise StoryError("The chosen route is unsafe for that quest, and the ship lacks the needed tool.")
    return StoryParams(quest=quest, route=route, name=name, role=role, helper=helper)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    q: Quest = f["quest"]
    return [
        f'Write a short Space Adventure story about a pig who wants to {q.goal} and must fulfill a quest.',
        f'Tell a child-friendly story where {f["pig"].id} the pig and {f["helper"].id} travel through {f["ship"].route} to finish a quest.',
        f'Write a simple story that includes the words pig, rendition, and fulfill, and ends with a quest being completed.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    pig: Entity = f["pig"]
    helper: Entity = f["helper"]
    quest: Quest = f["quest"]
    return [
        QAItem(
            question=f"Who was the story about?",
            answer=f"It was about {pig.id}, a small pig who wanted to complete a quest in space.",
        ),
        QAItem(
            question=f"What did {pig.id} want to do on the ship?",
            answer=f"{pig.id} wanted to {quest.goal}. That was the quest {pig.id} hoped to fulfill.",
        ),
        QAItem(
            question=f"Why did {helper.id} worry before the quest began?",
            answer=f"{helper.id} worried because the route was {world.ship.route}, and that path could damage {pig.id} without the right tool.",
        ),
        QAItem(
            question=f"How did {pig.id} finish the quest?",
            answer=f"{pig.id} used {quest.safe_tool}, followed the safe route, and fulfilled the quest with {helper.id}'s help.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a quest?",
            answer="A quest is a job or journey someone chooses because it matters a lot to them.",
        ),
        QAItem(
            question="What does fulfill mean?",
            answer="To fulfill something means to complete it or make it happen the way it was supposed to happen.",
        ),
        QAItem(
            question="What is a rendition?",
            answer="A rendition is a version of a song, story, or performance made in a particular way.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.protective:
            bits.append("protective=True")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  route_state={world.route_state}")
    return "\n".join(lines)


ASP_RULES = r"""
quest_ok(Q) :- quest(Q), safe_tool(Q,S), route_safe(Q,S).
route_safe(Q,S) :- unsafe_in(Q,R), ship_route(R), safe_tool(Q,S).
story_valid(P,Q) :- pig(P), quest(Q).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for qid, q in QUESTS.items():
        lines.append(asp.fact("quest", qid))
        lines.append(asp.fact("safe_tool", qid, q.safe_tool))
        for r in sorted(q.unsafe_in):
            lines.append(asp.fact("unsafe_in", qid, r))
    for rid, ship in ROUTES.items():
        lines.append(asp.fact("ship_route", ship.route))
        for h in sorted(ship.hazards):
            lines.append(asp.fact("hazard", rid, h))
    lines.append(asp.fact("pig", "pig"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show story_valid/2."))
    return sorted(set(asp.atoms(model, "story_valid")))


def asp_verify() -> int:
    py = {(p.name, q) for p in ["pig"] for q in QUESTS}
    cl = set(asp_valid())
    if py != cl:
        print("MISMATCH between clingo and python")
        print(" only in clingo:", sorted(cl - py))
        print(" only in python:", sorted(py - cl))
        return 1
    print(f"OK: ASP parity verified for {len(cl)} story shapes.")
    return 0


def valid_combos() -> list[tuple[str, str]]:
    return [("pig", qid) for qid in QUESTS]


def explain_rejection(quest: Quest, route: Ship) -> str:
    return f"(No story: the route {route.route} is too dangerous for the {quest.id} quest without the right tool.)"


def tell_story(params: StoryParams) -> StorySample:
    ship = copy.deepcopy(ROUTES[params.route])
    quest = QUESTS[params.quest]
    ship.safe_tool = quest.safe_tool
    world = World(ship)
    pig = world.add(Entity(id=params.name, kind="character", type=params.role, label="pig"))
    helper = world.add(Entity(id=params.helper, kind="character", type="pilot", label="helper"))
    world.add(Entity(id="quest", kind="thing", type="quest", label="Quest"))
    world.ship.route = ship.route

    introduce(world, pig)
    love_quest(world, pig, quest)
    world.para()
    set_out(world, pig, helper, quest)
    warn(world, helper, pig, quest)
    pig.memes["worry"] += 1 if helper.memes["worry"] else 0
    pig.memes["courage"] += 1
    world.say(f"{pig.id} took a breath and tried to be brave.")
    tool = choose_tool(world, helper, pig, quest)
    world.para()
    fulfill_quest(world, pig, helper, quest, tool)

    world.facts.update(pig=pig, helper=helper, quest=quest, ship=ship, tool=tool)
    return world


def generate(params: StoryParams) -> StorySample:
    world = tell_story(params)
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


def build_sample_set(args: argparse.Namespace, base_seed: int) -> list[StorySample]:
    samples: list[StorySample] = []
    if args.all:
        for qid in QUESTS:
            p = StoryParams(quest=qid, route="quiet", name="Pip", role="pig", helper="Captain Ray")
            samples.append(generate(p))
        return samples
    seen: set[str] = set()
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
    return samples


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show story_valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        triples = asp_valid()
        print(f"{len(triples)} compatible story shapes:\n")
        for item in triples:
            print("  ", item)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples = build_sample_set(args, base_seed)

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if len(samples) > 1 and not args.all:
            header = f"### variant {i + 1}"
        elif args.all:
            p = sample.params
            header = f"### {p.name}: {p.quest} on {p.route}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
