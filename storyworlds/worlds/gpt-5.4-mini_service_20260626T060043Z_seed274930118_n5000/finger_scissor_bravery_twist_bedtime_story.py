#!/usr/bin/env python3
"""
A tiny bedtime-style story world about a brave child, a careful scissor, and a
small twist that turns worry into a gentle fix.

Seed imagery:
- finger
- scissor
- Bravery
- Twist
- Bedtime Story

The domain is intentionally small and constraint-checked: a child wants to make
a paper star before bed, but the scissors feel scary because fingers can get too
close. The turn is a small, kind twist: the child slows down, asks for help, and
finds bravery in careful hands.
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

# ---------------------------------------------------------------------------
# Story model
# ---------------------------------------------------------------------------

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
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.type.endswith("s") else "it"


@dataclass
class Setting:
    place: str = "the bedroom"
    affords: set[str] = field(default_factory=set)


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    risk: str
    twist: str
    zone: set[str]
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    guards: set[str]
    covers: set[str]
    prep: str
    tail: str


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

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
class StoryParams:
    place: str
    activity: str
    tool: str
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


SETTINGS = {
    "bedroom": Setting(place="the bedroom", affords={"craft"}),
    "table": Setting(place="the little table", affords={"craft"}),
}

ACTIVITIES = {
    "craft": Activity(
        id="craft",
        verb="cut out a paper star",
        gerund="cutting out paper stars",
        rush="reach for the paper too fast",
        risk="sharp scissors might nick a finger",
        twist="slow down and ask for help",
        zone={"fingers"},
        keyword="star",
        tags={"paper", "scissor", "finger", "bravery", "twist"},
    )
}

TOOLS = {
    "scissor": Tool(
        id="scissor",
        label="scissors",
        phrase="small silver scissors",
        guards={"paper"},
        covers={"fingers"},
        prep="hold the scissors together with a grown-up hand nearby",
        tail="worked slowly, one careful snip at a time",
    ),
    "safe_scissor": Tool(
        id="safe_scissor",
        label="rounded scissors",
        phrase="rounded safety scissors",
        guards={"paper"},
        covers={"fingers"},
        prep="use the rounded safety scissors with a grown-up nearby",
        tail="made gentle little snips without any hurry",
    ),
}

NAMES = ["Mia", "Lena", "Nora", "Ivy", "Ava", "Theo", "Ben", "Leo"]
TRAITS = ["brave", "gentle", "sleepy", "curious", "careful", "quiet"]


class RuleWorld(World):
    pass


def can_use_tool(activity: Activity, tool: Tool) -> bool:
    return "fingers" in tool.covers and "paper" in tool.guards


def predict_risk(world: World, actor: Entity, activity: Activity, tool: Tool) -> dict:
    sim = World(world.setting)
    sim.entities = {k: Entity(**{**vars(v), "meters": dict(v.meters), "memes": dict(v.memes)})
                    for k, v in world.entities.items()}
    sim.fired = set(world.fired)
    simulate_action(sim, sim.get(actor.id), activity, tool, narrate=False)
    finger = sim.entities.get("finger")
    return {
        "hurt": bool(finger and finger.meters.get("hurt", 0.0) >= THRESHOLD),
        "worry": sim.entities[actor.id].memes.get("worry", 0.0),
    }


def simulate_action(world: World, actor: Entity, activity: Activity, tool: Tool, narrate: bool = True) -> None:
    if world.setting.place not in {world.setting.place}:
        return
    if tool.id not in world.entities:
        world.add(Entity(id=tool.id, type="tool", label=tool.label, phrase=tool.phrase, owner=actor.id))
    actor.meters["focus"] = actor.meters.get("focus", 0.0) + 1.0
    actor.memes["determination"] = actor.memes.get("determination", 0.0) + 1.0
    if tool.label == "scissors" and "fingers" in activity.zone:
        finger = world.get("finger")
        if actor.memes.get("rush", 0.0) >= THRESHOLD:
            finger.meters["hurt"] = finger.meters.get("hurt", 0.0) + 1.0
            actor.memes["worry"] = actor.memes.get("worry", 0.0) + 1.0
            if narrate:
                world.say("The scissors slipped too close, and the finger felt a sharp little sting.")
    else:
        if narrate:
            world.say("The scissors stayed steady, and the paper began to turn into a star.")


def tell(setting: Setting, activity: Activity, tool: Tool, hero_name: str, hero_type: str,
         hero_trait: str, parent_type: str) -> World:
    world = World(setting)
    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type=hero_type,
        meters={"focus": 0.0},
        memes={"bravery": 0.0, "worry": 0.0, "determination": 0.0},
    ))
    parent = world.add(Entity(
        id="Parent",
        kind="character",
        type=parent_type,
        label="the parent",
        meters={"calm": 0.0},
        memes={"care": 1.0},
    ))
    finger = world.add(Entity(id="finger", kind="body", type="finger", label="finger", owner=hero.id))
    world.add(Entity(id=tool.id, kind="tool", type="tool", label=tool.label, phrase=tool.phrase, owner=hero.id))

    world.say(
        f"{hero_name} was a {hero_trait} little {hero_type} who loved quiet bedtime crafts."
    )
    world.say(
        f"{hero.pronoun().capitalize()} wanted to {activity.verb} before sleep and make the room feel cozy."
    )
    world.para()
    world.say(
        f"On the little table, {hero_name} found {tool.phrase}, and the paper waited like a tiny moon."
    )

    world.say(
        f"{hero_name} tried to {activity.rush}, but {tool.label} looked sharp enough to make a finger worry."
    )
    world.say(
        f"{parent.label.capitalize()} noticed the rush and held up a gentle hand."
    )
    hero.memes["rush"] = 1.0
    pred = predict_risk(world, hero, activity, tool)
    if pred["hurt"]:
        world.say(
            f'"If you hurry," {parent.pronoun("possessive")} {parent.type} said, '
            f'"the {finger.label} could get nicked."'
        )
    world.say(
        f"{hero_name} paused, took a small breath, and found the bravery to {activity.twist}."
    )
    hero.memes["bravery"] += 1.0
    hero.memes["rush"] = 0.0
    world.para()
    world.say(
        f"{hero_name} held the {tool.label} the careful way {tool.prep}, and the paper made a soft rustle."
    )
    world.say(
        f"One neat cut after another, {hero_name} {tool.tail}, and the star came out bright and tidy."
    )
    world.say(
        f"In the end, the {finger.label} stayed safe, the brave feeling stayed warm, and bedtime felt peaceful."
    )

    world.facts.update(
        hero=hero,
        parent=parent,
        finger=finger,
        activity=activity,
        tool=tool,
        setting=setting,
        resolved=True,
        hurt=bool(finger.meters.get("hurt", 0.0) >= THRESHOLD),
    )
    return world


SETTINGS_BY_KEY = SETTINGS
ACTIVITY_BY_KEY = ACTIVITIES
TOOLS_BY_KEY = TOOLS


KNOWLEDGE = {
    "finger": [
        QAItem(
            question="What is a finger?",
            answer="A finger is one of the small parts at the end of your hand that helps you hold and touch things.",
        )
    ],
    "scissor": [
        QAItem(
            question="What are scissors for?",
            answer="Scissors are used to cut paper, string, or other thin things with a careful snip.",
        )
    ],
    "bravery": [
        QAItem(
            question="What does bravery mean?",
            answer="Bravery means doing something hard or scary while you stay calm and keep going.",
        )
    ],
    "twist": [
        QAItem(
            question="What is a twist in a story?",
            answer="A twist is a change that surprises you and sends the story in a new direction.",
        )
    ],
    "bedtime": [
        QAItem(
            question="Why do some children do quiet things before bedtime?",
            answer="Quiet things help the body and mind slow down so it is easier to rest and sleep.",
        )
    ],
}


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    act = f["activity"]
    tool = f["tool"]
    return [
        f'Write a bedtime story for a small child about {hero.id} and a pair of {tool.label}.',
        f'Create a gentle story with the words "{act.keyword}", "bravery", and "twist".',
        f"Tell a calming story where {hero.id} wants to {act.verb} but learns to be careful with a finger and scissors.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    parent = f["parent"]
    activity = f["activity"]
    tool = f["tool"]
    place = f["setting"].place
    qa = [
        QAItem(
            question=f"What did {hero.id} want to do at {place} before bedtime?",
            answer=f"{hero.id} wanted to {activity.verb} and make a tiny paper star.",
        ),
        QAItem(
            question=f"Why did {parent.label} worry about the scissors?",
            answer=f"{parent.label.capitalize()} worried because {tool.label} were sharp and a finger could get nicked if {hero.id} hurried.",
        ),
        QAItem(
            question=f"What changed when {hero.id} found bravery?",
            answer=f"{hero.id} slowed down, used the {tool.label} carefully, and the little twist helped the story end peacefully.",
        ),
    ]
    if f.get("resolved"):
        qa.append(
            QAItem(
                question=f"How did the story end?",
                answer=f"It ended with the finger safe, the paper star finished, and bedtime feeling calm and cozy.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["activity"].tags)
    out: list[QAItem] = []
    for tag in ["bedtime", "bravery", "twist", "finger", "scissor"]:
        if tag in tags or tag in KNOWLEDGE:
            out.extend(KNOWLEDGE.get(tag, []))
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for p in sample.prompts:
        lines.append(f"- {p}")
    lines.append("")
    lines.append("== Story QA ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World QA ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"{e.id} ({e.type}): {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="bedroom", activity="craft", tool="scissor", name="Mia", gender="girl", parent="mother", trait="brave"),
    StoryParams(place="table", activity="craft", tool="scissor", name="Theo", gender="boy", parent="father", trait="careful"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Bedtime story world about bravery, a finger, and scissors.")
    ap.add_argument("--place", choices=SETTINGS_BY_KEY)
    ap.add_argument("--activity", choices=ACTIVITY_BY_KEY)
    ap.add_argument("--tool", choices=TOOLS_BY_KEY)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name")
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
    if args.activity and args.tool:
        act = ACTIVITY_BY_KEY[args.activity]
        tool = TOOLS_BY_KEY[args.tool]
        if not can_use_tool(act, tool):
            raise StoryError("That tool does not make sense for this careful story.")
    place = args.place or rng.choice(list(SETTINGS_BY_KEY))
    activity = args.activity or rng.choice(list(ACTIVITY_BY_KEY))
    tool = args.tool or rng.choice(list(TOOLS_BY_KEY))
    gender = args.gender or rng.choice(["girl", "boy"])
    parent = args.parent or rng.choice(["mother", "father"])
    name = args.name or rng.choice(NAMES)
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, activity=activity, tool=tool, name=name, gender=gender, parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS_BY_KEY[params.place],
        ACTIVITY_BY_KEY[params.activity],
        TOOLS_BY_KEY[params.tool],
        params.name,
        params.gender,
        params.trait,
        params.parent,
    )
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
tool_ok(T) :- tool(T), guards(T,paper), covers(T,fingers).
at_risk(A) :- activity(A), splashes(A,fingers).
safe_story(P,A,T) :- setting(P), activity(A), tool(T), at_risk(A), tool_ok(T).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid in SETTINGS_BY_KEY:
        lines.append(asp.fact("setting", pid))
    for aid, a in ACTIVITY_BY_KEY.items():
        lines.append(asp.fact("activity", aid))
        for tag in sorted(a.tags):
            lines.append(asp.fact("tag", aid, tag))
        for z in sorted(a.zone):
            lines.append(asp.fact("splashes", aid, z))
    for tid, t in TOOLS_BY_KEY.items():
        lines.append(asp.fact("tool", tid))
        for g in sorted(t.guards):
            lines.append(asp.fact("guards", tid, g))
        for c in sorted(t.covers):
            lines.append(asp.fact("covers", tid, c))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for p in SETTINGS_BY_KEY:
        for a, act in ACTIVITY_BY_KEY.items():
            for t, tool in TOOLS_BY_KEY.items():
                if can_use_tool(act, tool):
                    out.append((p, a, t))
    return out


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show safe_story/3."))
    return sorted(set(asp.atoms(model, "safe_story")))


def asp_verify() -> int:
    python_set = set(valid_combos())
    clingo_set = set(asp_valid_combos())
    if python_set == clingo_set:
        print(f"OK: clingo gate matches valid_combos() ({len(python_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if clingo_set - python_set:
        print(" only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print(" only in python:", sorted(python_set - clingo_set))
    return 1


def explain_rejection(activity: Activity, tool: Tool) -> str:
    return f"(No story: {tool.label} do not fit this careful bedtime craft.)"


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show safe_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_program("#show safe_story/3."))
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
