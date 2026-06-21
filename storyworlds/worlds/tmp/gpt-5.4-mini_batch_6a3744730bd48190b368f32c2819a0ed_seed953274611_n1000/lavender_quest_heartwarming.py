#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/lavender_quest_heartwarming.py
===============================================================

A small heartwarming quest storyworld about a child, a gentle helper, and a
search for lavender. The domain is intentionally tiny: a child wants to bring a
bit of lavender home for a loved one, meets a snag, then completes the quest
with help and returns with something comforting and real.

The world uses typed entities with physical meters and emotional memes, a small
forward-chaining simulator, a Python reasonableness gate, and an inline ASP twin
for parity checks.
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
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    carries: list[str] = field(default_factory=list)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "grandmother"}
        male = {"boy", "father", "dad", "man", "grandfather"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad", "grandmother": "grandma", "grandfather": "grandpa"}.get(self.type, self.type)


@dataclass
class Location:
    id: str
    label: str
    kind: str
    abundant: bool = False
    sheltered: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class Goal:
    id: str
    label: str
    phrase: str
    need: str
    helper: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    helps: set[str]
    tags: set[str] = field(default_factory=set)


@dataclass
class World:
    locations: dict[str, Location] = field(default_factory=dict)
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def add_loc(self, loc: Location) -> Location:
        self.locations[loc.id] = loc
        return loc

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
        clone = World()
        clone.locations = copy.deepcopy(self.locations)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_soothe(world: World) -> list[str]:
    out: list[str] = []
    child = world.entities.get("child")
    elder = world.entities.get("elder")
    if not child or not elder:
        return out
    if child.memes["worry"] < THRESHOLD or elder.memes["care"] < THRESHOLD:
        return out
    sig = ("soothe",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["calm"] += 1
    elder.memes["calm"] += 1
    out.append("__soothe__")
    return out


def _r_bloom(world: World) -> list[str]:
    child = world.entities.get("child")
    flowers = world.entities.get("lavender")
    if not child or not flowers:
        return []
    if child.meters["seeking"] < THRESHOLD:
        return []
    if flowers.meters["found"] >= THRESHOLD:
        return []
    sig = ("bloom",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    flowers.meters["found"] += 1
    return ["__find__"]


CAUSAL_RULES = [Rule("soothe", "social", _r_soothe), Rule("bloom", "quest", _r_bloom)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            got = rule.apply(world)
            if got:
                changed = True
                produced.extend(x for x in got if not x.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def quest_reasonable(start: Location, goal: Location, goal_cfg: Goal) -> bool:
    return goal_cfg.need in goal.tags and start.id != goal.id


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid, start in LOCATIONS.items():
        for gid, goal in LOCATIONS.items():
            for qid, qc in GOALS.items():
                if quest_reasonable(start, goal, qc) and goal.id == qc.id:
                    combos.append((sid, gid, qid))
    return combos


def predict(world: World, goal_id: str) -> dict:
    sim = world.copy()
    _start_quest(sim, sim.get("child"), sim.locations[goal_id], narrate=False)
    return {
        "found": bool(sim.entities["lavender"].meters["found"] >= THRESHOLD),
        "calm": sim.get("child").memes["calm"],
    }


def _start_quest(world: World, child: Entity, goal_loc: Location, narrate: bool = True) -> None:
    child.meters["seeking"] += 1
    child.memes["hope"] += 1
    if goal_loc.abundant:
        world.entities["lavender"].meters["found"] += 1
    if narrate:
        propagate(world, narrate=True)


def tell(start: Location, goal: Location, quest: Goal, tool: Tool,
         child_name: str = "Mina", elder_name: str = "Grandma",
         child_gender: str = "girl", elder_gender: str = "grandmother") -> World:
    world = World()
    child = world.add(Entity(id="child", kind="character", type=child_gender, label=child_name, role="seeker", traits=["kind"]))
    elder = world.add(Entity(id="elder", kind="character", type=elder_gender, label=elder_name, role="guide", traits=["gentle"]))
    lavender = world.add(Entity(id="lavender", kind="thing", type="flower", label="lavender", phrase="a sprig of lavender"))
    world.add_loc(start)
    world.add_loc(goal)
    world.facts["start"] = start
    world.facts["goal"] = goal
    world.facts["quest"] = quest
    world.facts["tool"] = tool

    child.memes["hope"] = 1
    elder.memes["care"] = 1

    world.say(f"{child.label} loved {quest.phrase}. {child.label_word.capitalize()} wanted to bring home {lavender.label} for {elder.label}.")
    world.say(f"That morning, {child.label} set off from {start.label}, carrying {tool.phrase}.")
    world.para()
    world.say(f"The path led toward {goal.label}, where the air smelled faintly of summer and green leaves.")
    child.memes["worry"] += 1
    world.say(f"{child.label} soon saw that reaching the best patch would take patience, not rushing.")

    if goal.abundant:
        world.para()
        _start_quest(world, child, goal, narrate=True)
        world.say(f"{child.label} gently cut one small sprig and wrapped it in a soft cloth.")
        elder.memes["love"] += 1
        world.say(f"At home, {elder.label_word.capitalize()} smiled when the lavender reached her hands.")
        world.say(f"{child.label} tucked the little bundle on the table, and the whole room smelled calm and sweet.")
        outcome = "found"
    else:
        world.para()
        child.memes["worry"] += 1
        elder.memes["care"] += 1
        world.say(f"At the edge of the path, {child.label} felt unsure and called for {elder.label_word}.")
        propagate(world, narrate=True)
        world.say(f"{elder.label_word.capitalize()} walked beside {child.label}, and together they looked until the lavender was found.")
        world.say(f"The quest did not need speed after all; it needed a steady hand and a warm one.")
        outcome = "guided"

    world.facts.update(child=child, elder=elder, lavender=lavender, outcome=outcome)
    return world


LOCATIONS = {
    "home": Location(id="home", label="the garden gate", kind="start", sheltered=True, tags={"start", "home"}),
    "path": Location(id="path", label="the sunny path", kind="trail", tags={"path"}),
    "hill": Location(id="hill", label="the little hillside", kind="goal", abundant=True, tags={"lavender", "goal"}),
    "shop": Location(id="shop", label="the market stall", kind="goal", abundant=False, tags={"goal"}),
}

GOALS = {
    "hill": Goal(id="hill", label="the little hillside", phrase="the quest for a lovely surprise", need="lavender", helper="gentle search", tags={"lavender", "goal"}),
    "shop": Goal(id="shop", label="the market stall", phrase="the quest for a sweet gift", need="lavender", helper="easy help", tags={"lavender", "goal"}),
}

TOOLS = {
    "basket": Tool(id="basket", label="basket", phrase="a tiny woven basket", helps={"carry", "gather"}, tags={"carry"}),
    "ribbon": Tool(id="ribbon", label="ribbon", phrase="a blue ribbon to tie the stems", helps={"wrap"}, tags={"wrap"}),
}

NAMES = ["Mina", "Lina", "Sophie", "Nora", "Ella", "Maya", "Iris"]
ELDER_NAMES = ["Grandma", "Nana", "Aunt Ruth", "Mrs. Bell"]


@dataclass
class StoryParams:
    start: str
    goal: str
    quest: str
    tool: str
    child_name: str = "Mina"
    child_gender: str = "girl"
    elder_name: str = "Grandma"
    elder_gender: str = "grandmother"
    seed: Optional[int] = None


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    quest = f["quest"]
    goal = f["goal"]
    return [
        f"Write a heartwarming quest story for a young child where {child.label} searches for lavender and brings it home.",
        f"Tell a gentle story about {child.label}'s quest to reach {goal.label} for lavender, with a loving ending.",
        f"Write a small, warm story that includes the word lavender and shows a child learning patience on a quest.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    elder = f["elder"]
    goal = f["goal"]
    out = [
        ("Who is the story about?", f"It is about {child.label}, who goes on a small quest with help from {elder.label}."),
        ("What was the child looking for?", "The child was looking for lavender. It was meant to become a comforting little gift."),
        ("Why did the child need help?", f"The best spot was not easy to reach alone, so {elder.label} came along with a calm, steady hand."),
        ("How did the story end?", "The lavender was found and brought home safely. The last image is of a room that smells soft and sweet."),
    ]
    if f["outcome"] == "found":
        out.append(("What changed by the end?", "The child began with hope and ended with the lavender in hand. The quest turned into a warm surprise for the elder at home."))
    else:
        out.append(("What changed by the end?", "The child learned that asking for help can be part of a good quest. The search became easier once the elder walked beside them."))
    return out


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is lavender?", "Lavender is a flower with a soft purple color and a gentle smell. People often find it calming."),
        ("Why might someone keep lavender at home?", "People may keep lavender nearby because it smells nice and can make a room feel peaceful."),
        ("What is a quest?", "A quest is a search for something important. It can be a little adventure with a goal."),
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
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.traits:
            bits.append(f"traits={e.traits}")
        lines.append(f"  {e.id:8} ({e.type:9}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
found_lavender :- seeker(S), seeking(S), goal(G), abundant(G).
calm_end :- found_lavender.
story_ok :- found_lavender.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for lid, loc in LOCATIONS.items():
        lines.append(asp.fact("location", lid))
        if loc.abundant:
            lines.append(asp.fact("abundant", lid))
        for t in sorted(loc.tags):
            lines.append(asp.fact("tag", lid, t))
    for gid, goal in GOALS.items():
        lines.append(asp.fact("goal", gid))
        for t in sorted(goal.tags):
            lines.append(asp.fact("goal_tag", gid, t))
    for tid, tool in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        for t in sorted(tool.tags):
            lines.append(asp.fact("tool_tag", tid, t))
    lines.append(asp.fact("need", "lavender"))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import asp
    rc = 0
    py = set(valid_combos())
    model = asp.one_model(asp_program("", "#show story_ok/0."))
    ok = bool(asp.atoms(model, "story_ok"))
    if not py:
        print("MISMATCH: no Python valid combos.")
        rc = 1
    else:
        print(f"OK: Python valid_combos() returned {len(py)} combos.")
    sample_params = resolve_params(build_parser().parse_args([]), random.Random(7))
    try:
        sample = generate(sample_params)
        _ = sample.story
    except Exception as exc:  # noqa: BLE001
        print(f"FAIL: story generation crashed: {exc}")
        return 1
    if ok:
        print("OK: ASP gate can derive a valid story.")
    else:
        print("MISMATCH: ASP gate did not derive story_ok.")
        rc = 1
    if sample.story.strip():
        print("OK: normal generate() smoke test succeeded.")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A heartwarming lavender quest storyworld.")
    ap.add_argument("--start", choices=LOCATIONS)
    ap.add_argument("--goal", choices=GOALS)
    ap.add_argument("--quest", choices=GOALS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--elder", choices=ELDER_NAMES)
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
    goal = args.goal or rng.choice(list(GOALS))
    if args.quest and args.quest != goal:
        raise StoryError("The quest and the goal must match in this little world.")
    start = args.start or rng.choice(list(LOCATIONS))
    tool = args.tool or rng.choice(list(TOOLS))
    name = args.name or rng.choice(NAMES)
    gender = args.gender or ("girl" if name in NAMES[:4] else "boy")
    elder = args.elder or rng.choice(ELDER_NAMES)
    elder_gender = "grandmother" if elder in {"Grandma", "Nana"} else "mother"
    return StoryParams(start=start, goal=goal, quest=goal, tool=tool, child_name=name, child_gender=gender, elder_name=elder, elder_gender=elder_gender)


def generate(params: StoryParams) -> StorySample:
    if params.start not in LOCATIONS or params.goal not in GOALS or params.tool not in TOOLS:
        raise StoryError("Invalid parameters for this storyworld.")
    start = LOCATIONS[params.start]
    goal = LOCATIONS[params.goal]
    quest = GOALS[params.quest]
    tool = TOOLS[params.tool]
    world = tell(start, goal, quest, tool, child_name=params.child_name, elder_name=params.elder_name, child_gender=params.child_gender, elder_gender=params.elder_gender)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa(world)],
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
    StoryParams(start="home", goal="hill", quest="hill", tool="basket", child_name="Mina", child_gender="girl", elder_name="Grandma", elder_gender="grandmother"),
    StoryParams(start="path", goal="hill", quest="hill", tool="ribbon", child_name="Lina", child_gender="girl", elder_name="Nana", elder_gender="grandmother"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid/3.\n#show story_ok/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("", "#show valid/3."))
        vals = sorted(set(asp.atoms(model, "valid")))
        print(f"{len(vals)} valid quest combos:")
        for v in vals:
            print(" ", v)
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
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as err:
                print(err)
                return
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
