#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/avatar_foreshadowing_quest_teamwork_pirate_tale.py
===================================================================================

A tiny pirate-tale storyworld with foreshadowing, a quest, and teamwork.

Premise:
A small pirate crew follows a clue about a hidden island treasure. An avatar
carved on a map foreshadows the route, the crew works together through trouble,
and the ending proves the quest changed what they found and how they felt.

This file is self-contained and uses only the standard library plus the shared
storyworld result containers. Clingo / ASP support is imported lazily when asked
for, so normal story generation runs without it.
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
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class Crew:
    id: str
    name: str
    pronoun_type: str
    role: str
    trait: str
    age: int = 0


@dataclass
class Quest:
    id: str
    map_place: str
    route: str
    goal: str
    obstacle: str
    clue: str
    avatar_hint: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    help_text: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    crew_a: str
    crew_b: str
    captain: str
    companion: str
    quest: str
    tool: str
    seed: Optional[int] = None
    # Optional background knobs
    weather: str = "calm"
    relation: str = "mates"


class World:
    def __init__(self) -> None:
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
        c = World()
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = dict(self.facts)
        return c


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            out = rule.apply(world)
            if out:
                changed = True
                produced.extend(out)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def _r_encourage(world: World) -> list[str]:
    out: list[str] = []
    if world.get("crew_a").memes["hope"] >= THRESHOLD and world.get("crew_b").memes["hope"] >= THRESHOLD:
        sig = ("encourage",)
        if sig not in world.fired:
            world.fired.add(sig)
            world.get("ship").meters["readiness"] += 1
            out.append("The deck felt ready for the journey.")
    return out


def _r_teamwork(world: World) -> list[str]:
    out: list[str] = []
    a = world.get("crew_a")
    b = world.get("crew_b")
    if a.memes["trust"] >= THRESHOLD and b.memes["trust"] >= THRESHOLD:
        sig = ("teamwork",)
        if sig not in world.fired:
            world.fired.add(sig)
            world.get("ship").meters["teamwork"] += 1
            out.append("Together, they found a way forward.")
    return out


CAUSAL_RULES = [Rule("encourage", _r_encourage), Rule("teamwork", _r_teamwork)]


def reasonableness_ok(quest: Quest, tool: Tool) -> bool:
    return "avatar" in quest.tags and "map" in tool.tags


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for qid, q in QUESTS.items():
        for tid, t in TOOLS.items():
            if reasonableness_ok(q, t):
                combos.append((qid, tid))
    return combos


def avatar_foreshadowing(world: World, quest: Quest) -> None:
    world.say(
        f"At the start, the crew found a weathered map with an avatar carved in the corner. "
        f"The little figure pointed toward {quest.map_place}, as if it was warning them where the path would bend."
    )
    world.say(
        f'"That avatar keeps staring at the same spot," said {world.get("crew_b").id}. '
        f'"Maybe the treasure is hiding near {quest.obstacle}."'
    )
    world.get("crew_a").memes["hope"] += 1
    world.get("crew_b").memes["hope"] += 1


def set_sail(world: World, captain: Entity, companion: Entity, quest: Quest, tool: Tool) -> None:
    captain.memes["hope"] += 1
    companion.memes["hope"] += 1
    world.say(
        f"{captain.id} and {companion.id} climbed aboard their little pirate ship and set sail for {quest.map_place}. "
        f"They brought {tool.label} because the map said the clue would only make sense in the dark."
    )


def trouble(world: World, quest: Quest) -> None:
    world.para()
    world.say(
        f"By noon, a rough fog wrapped the water. The crew could not see the rocks, and the sea tossed them toward {quest.obstacle}."
    )
    world.get("ship").meters["trouble"] += 1
    world.get("crew_a").memes["worry"] += 1
    world.get("crew_b").memes["worry"] += 1


def teamwork_solution(world: World, captain: Entity, companion: Entity, quest: Quest, tool: Tool) -> None:
    captain.memes["trust"] += 1
    companion.memes["trust"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{captain.id} held the {tool.label} high, and {companion.id} steadied the map. "
        f"One read the clue, the other steered, and together they found the narrow turn the avatar had hinted at."
    )
    world.say(
        f"They reached {quest.goal} just beyond {quest.obstacle}, where the chest waited under a pile of shells."
    )


def ending(world: World, captain: Entity, companion: Entity, quest: Quest) -> None:
    captain.memes["joy"] += 1
    companion.memes["joy"] += 1
    world.say(
        f"When the chest opened, it held a bright compass and a note that read, 'Good crews listen to clues and to each other.'"
    )
    world.say(
        f"{captain.id} grinned at {companion.id}. The avatar on the map had not been a decoration at all; it had been a promise. "
        f"The two pirates sailed home with the treasure, the compass, and a new way of working as one team."
    )


def tell(params: StoryParams) -> World:
    world = World()
    captain = world.add(Entity(id="crew_a", kind="character", type="boy", role="captain", traits=["bold"]))
    companion = world.add(Entity(id="crew_b", kind="character", type="girl", role="mate", traits=["sharp"]))
    ship = world.add(Entity(id="ship", kind="thing", type="ship", label="their little ship"))
    quest = QUESTS[params.quest]
    tool = TOOLS[params.tool]

    captain.id = params.captain
    companion.id = params.companion

    world.entities = {captain.id: captain, companion.id: companion, ship.id: ship}

    captain.memes["hope"] = 1
    companion.memes["hope"] = 1
    captain.memes["trust"] = 1
    companion.memes["trust"] = 1

    world.say(
        f"On a bright morning, {captain.id} and {companion.id} found an old map in the captain's bag."
    )
    avatar_foreshadowing(world, quest)
    world.para()
    set_sail(world, captain, companion, quest, tool)
    trouble(world, quest)
    teamwork_solution(world, captain, companion, quest, tool)
    world.para()
    ending(world, captain, companion, quest)

    world.facts.update(
        captain=captain,
        companion=companion,
        ship=ship,
        quest=quest,
        tool=tool,
        outcome="found",
    )
    return world


QUESTS = {
    "island": Quest(
        id="island",
        map_place="a hidden island",
        route="the moonlit reef",
        goal="the coral cove",
        obstacle="a ring of jagged rocks",
        clue="follow the star that has three points",
        avatar_hint="an avatar pointing seaward",
        tags={"avatar", "quest", "foreshadowing"},
    ),
    "cave": Quest(
        id="cave",
        map_place="a cliff cave",
        route="the narrow inlet",
        goal="the shell room",
        obstacle="a dark waterfall",
        clue="listen where the water sounds hollow",
        avatar_hint="an avatar with a lantern",
        tags={"avatar", "quest", "foreshadowing"},
    ),
    "lagoon": Quest(
        id="lagoon",
        map_place="a silver lagoon",
        route="the windy channel",
        goal="the sandbar chest",
        obstacle="a drifting patch of weeds",
        clue="turn when the gulls circle twice",
        avatar_hint="an avatar with a tiny oar",
        tags={"avatar", "quest", "foreshadowing"},
    ),
}

TOOLS = {
    "lantern": Tool(id="lantern", label="a lantern", help_text="a warm light for reading maps", tags={"map", "light"}),
    "spyglass": Tool(id="spyglass", label="a spyglass", help_text="a tool for seeing far away", tags={"map", "see"}),
    "rope": Tool(id="rope", label="a coil of rope", help_text="a tool for climbing and tying off", tags={"help", "map"}),
    "chart": Tool(id="chart", label="a spare chart", help_text="an extra copy of the route", tags={"map"}),
}


def generation_prompts(world: World) -> list[str]:
    q: Quest = world.facts["quest"]
    t: Tool = world.facts["tool"]
    c: Entity = world.facts["captain"]
    b: Entity = world.facts["companion"]
    return [
        f'Write a pirate tale for a young child that includes the word "avatar" and a quest with a helpful clue.',
        f"Tell a story where {c.id} and {b.id} follow a map, notice an avatar foreshadowing danger, and work together to find treasure.",
        f"Write a short teamwork adventure in which {t.label} helps a pirate crew reach {q.goal} after the map's avatar hints at the right path.",
    ]


def story_qa(world: World) -> list[QAItem]:
    q: Quest = world.facts["quest"]
    t: Tool = world.facts["tool"]
    c: Entity = world.facts["captain"]
    b: Entity = world.facts["companion"]
    return [
        QAItem(
            question="What did the avatar on the map do?",
            answer=(
                f"It foreshadowed the route by pointing toward {q.map_place} and hinting that the crew would need to watch the path carefully. "
                f"That clue helped them stay alert when the fog and rocks appeared."
            ),
        ),
        QAItem(
            question="How did the crew solve the problem on the quest?",
            answer=(
                f"{c.id} held up {t.label}, while {b.id} steadied the map and read the clue. "
                f"They worked together, which let them find the safe turn and reach {q.goal}."
            ),
        ),
        QAItem(
            question="What changed by the end of the story?",
            answer=(
                f"They began as pirates following a mystery, and they ended as a better team with treasure in hand. "
                f"The quest gave them a compass, and the avatar clue taught them to trust one another."
            ),
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is an avatar in a story picture?",
            answer=(
                "An avatar is a pictured figure that stands for someone or something in the story. "
                "Writers can use it to hint at danger, guide a quest, or show a character's role."
            ),
        ),
        QAItem(
            question="What is teamwork?",
            answer=(
                "Teamwork means people help each other and share the job. "
                "When a crew uses teamwork, the work gets easier and the group can solve harder problems."
            ),
        ),
        QAItem(
            question="What is foreshadowing?",
            answer=(
                "Foreshadowing is a clue that hints about something important that will happen later. "
                "It makes the story feel like the ending was waiting patiently from the beginning."
            ),
        ),
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
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.traits:
            bits.append(f"traits={e.traits}")
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


def explain_rejection() -> str:
    return "(No story: this world needs an avatar-linked quest plus a map-like tool so the foreshadowing and teamwork can actually matter.)"


def valid_params(p: StoryParams) -> bool:
    return p.quest in QUESTS and p.tool in TOOLS and reasonableness_ok(QUESTS[p.quest], TOOLS[p.tool])


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.quest and args.quest not in QUESTS:
        raise StoryError("(Unknown quest.)")
    if args.tool and args.tool not in TOOLS:
        raise StoryError("(Unknown tool.)")
    if args.quest and args.tool and not reasonableness_ok(QUESTS[args.quest], TOOLS[args.tool]):
        raise StoryError(explain_rejection())
    combos = [c for c in valid_combos()
              if (args.quest is None or c[0] == args.quest)
              and (args.tool is None or c[1] == args.tool)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    quest, tool = rng.choice(sorted(combos))
    captain = args.captain or rng.choice(["Bluefin", "Rook", "Marlin", "Coral", "Nettie"])
    companion = args.companion or rng.choice(["Pip", "Mina", "Jory", "Luna", "Sailor"])
    if companion == captain:
        companion += "a"
    weather = rng.choice(["calm", "windy", "misty"])
    relation = rng.choice(["mates", "siblings", "friends"])
    return StoryParams(
        crew_a=captain,
        crew_b=companion,
        captain=captain,
        companion=companion,
        quest=quest,
        tool=tool,
        weather=weather,
        relation=relation,
    )


def generate(params: StoryParams) -> StorySample:
    if params.quest not in QUESTS or params.tool not in TOOLS:
        raise StoryError("(Invalid params.)")
    if not valid_params(params):
        raise StoryError(explain_rejection())
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


ASP_RULES = r"""
quest(Q) :- quest_fact(Q).
tool(T) :- tool_fact(T).
valid(Q,T) :- quest(Q), tool(T), has_avatar(Q), map_like(T).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for qid, q in QUESTS.items():
        lines.append(asp.fact("quest_fact", qid))
        lines.append(asp.fact("has_avatar", qid))
    for tid, t in TOOLS.items():
        lines.append(asp.fact("tool_fact", tid))
        if "map" in t.tags:
            lines.append(asp.fact("map_like", tid))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import io
    import contextlib

    rc = 0
    a = set(asp_valid_combos())
    p = set(valid_combos())
    if a == p:
        print(f"OK: gate matches valid_combos() ({len(a)} combos).")
    else:
        rc = 1
        print("MISMATCH in gate:")
        print("  only in asp:", sorted(a - p))
        print("  only in python:", sorted(p - a))
    try:
        sample = generate(resolve_params(argparse.Namespace(quest=None, tool=None, captain=None, companion=None), random.Random(777)))
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            emit(sample, trace=True, qa=True)
    except Exception as err:
        print(f"SMOKE TEST FAILED: {err}")
        return 1
    print("OK: generate/emit smoke test passed.")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Pirate tale storyworld with avatar foreshadowing, a quest, and teamwork.")
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--captain")
    ap.add_argument("--companion")
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


CURATED = [
    StoryParams(crew_a="Bluefin", crew_b="Pip", captain="Bluefin", companion="Pip", quest="island", tool="lantern"),
    StoryParams(crew_a="Rook", crew_b="Mina", captain="Rook", companion="Mina", quest="cave", tool="chart"),
    StoryParams(crew_a="Coral", crew_b="Jory", captain="Coral", companion="Jory", quest="lagoon", tool="spyglass"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible quest/tool combos:")
        for q, t in combos:
            print(f"  {q:8} {t}")
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
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
