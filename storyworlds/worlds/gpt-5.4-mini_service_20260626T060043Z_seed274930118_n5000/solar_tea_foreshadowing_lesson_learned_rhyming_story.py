#!/usr/bin/env python3
"""
A tiny storyworld for a rhyming lesson about solar tea.

Premise:
A child wants to make tea using sunlight, but the sky may not stay bright
long enough. The story uses foreshadowing: small hints about clouds, warmth,
and patience point toward the lesson learned at the end.

Theme words:
- solar
- tea

Narrative instruments:
- Foreshadowing
- Lesson Learned

Style:
- Rhyming Story
"""

from __future__ import annotations

import argparse
import json
import os
import random
import re
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class Place:
    id: str
    label: str
    indoor: bool
    sunny: bool
    affords: set[str] = field(default_factory=set)


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    result: str
    requires_sun: bool
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    helps: set[str] = field(default_factory=set)
    requires: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    place: str
    activity: str
    tool: str
    name: str
    parent: str
    seed: Optional[int] = None


PLACES = {
    "backyard": Place("backyard", "the backyard", indoor=False, sunny=True, affords={"solar_tea", "tea"}),
    "garden": Place("garden", "the garden", indoor=False, sunny=True, affords={"solar_tea", "tea"}),
    "porch": Place("porch", "the porch", indoor=False, sunny=True, affords={"solar_tea", "tea"}),
    "kitchen": Place("kitchen", "the kitchen", indoor=True, sunny=False, affords={"tea"}),
}

ACTIVITIES = {
    "solar_tea": Activity(
        id="solar_tea",
        verb="brew solar tea",
        gerund="brewing solar tea",
        result="the tea turned warm and bright",
        requires_sun=True,
        tags={"solar", "tea", "sun", "warmth", "patience"},
    ),
    "tea": Activity(
        id="tea",
        verb="make tea",
        gerund="making tea",
        result="the tea steamed softly in a cup",
        requires_sun=False,
        tags={"tea", "warmth"},
    ),
}

TOOLS = {
    "jar": Tool(
        id="jar",
        label="a clear jar",
        phrase="a clear jar with a lid",
        helps={"solar_tea"},
        requires={"sun"},
    ),
    "kettle": Tool(
        id="kettle",
        label="a little kettle",
        phrase="a little kettle with a shiny handle",
        helps={"tea"},
        requires=set(),
    ),
}


GIRL_NAMES = ["Mia", "Luna", "Nora", "Ivy", "Zoe", "Ruby"]
BOY_NAMES = ["Leo", "Milo", "Finn", "Theo", "Eli", "Noah"]
PARENT_NAMES = ["mom", "dad", "grandma", "grandpa"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place_id, place in PLACES.items():
        for act_id, act in ACTIVITIES.items():
            if act_id not in place.affords:
                continue
            for tool_id, tool in TOOLS.items():
                if act_id in tool.helps:
                    combos.append((place_id, act_id, tool_id))
    return combos


def reason_gate(place: Place, activity: Activity, tool: Tool) -> bool:
    return activity.id in place.affords and activity.id in tool.helps


def explain_rejection(place: Place, activity: Activity, tool: Tool) -> str:
    if activity.id not in place.affords:
        return f"(No story: {place.label} does not fit {activity.gerund}.)"
    return f"(No story: {tool.label} is not the right tool for {activity.gerund}.)"


def rhyme_pair(a: str, b: str) -> str:
    return f"{a} {b}"


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.facts: dict = {}
        self.trace: list[str] = []

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, line: str) -> None:
        self.trace.append(line)

    def render(self) -> str:
        return " ".join(self.trace)


def foreshadow(world: World, child: Entity, activity: Activity) -> None:
    if world.place.indoor:
        world.say(
            f"In the kitchen, the window gave a dim little gleam, "
            f"and the clouds outside looked like a sleepy dream."
        )
    else:
        world.say(
            f"The sun was high, and the air felt nice; "
            f"but one thin cloud drifted by twice."
        )
    world.say(
        f"{child.id} saw the light and gave a cheer, "
        f"yet a drifting cloud made the sky not clear."
    )


def begin(world: World, child: Entity, parent: Entity, activity: Activity, tool: Tool) -> None:
    world.say(
        f"{child.id} wanted to {activity.verb} with {tool.label} in sight, "
        f"while {parent.label} smiled and said, 'Pick the day just right.'"
    )
    world.say(
        f"{child.id} loved the plan, so neat and true, "
        f"for solar tea felt special when the sun shone through."
    )


def tension(world: World, child: Entity, activity: Activity, tool: Tool) -> None:
    world.say(
        f"{child.id} set the jar by the wall, then waited near the gate, "
        f"but the cloud rolled closer and did not seem to wait."
    )
    if activity.requires_sun:
        world.say(
            f"The jar needed sun to warm the tea, "
            f"and shade would make the brew stay plain as plain could be."
        )


def turn(world: World, child: Entity, parent: Entity, activity: Activity, tool: Tool) -> None:
    world.say(
        f"{parent.label} said, 'Patience is a helping tune; "
        f"the sun will peek again this afternoon.'"
    )
    world.say(
        f"{child.id} moved the jar to a brighter stone, "
        f"then watched for sunbeams all alone."
    )
    world.say(
        f"At last the clouds drifted out of the way, "
        f"and sunlight came back to save the day."
    )
    world.say(
        f"The tea grew warm with a golden glow, "
        f"and {child.id} learned to let slow good things grow."
    )


def ending(world: World, child: Entity, activity: Activity, tool: Tool) -> None:
    world.say(
        f"So {child.id} sipped the tea and grinned with glee; "
        f"the lesson learned was plain to see."
    )
    world.say(
        f"If you want solar tea to taste just right, "
        f"wait for the sun and keep hope bright."
    )
    world.facts["done"] = True


def tell(place: Place, activity: Activity, tool: Tool, name: str, parent_name: str) -> World:
    world = World(place)
    child = world.add(Entity(id=name, kind="character", type="child", label=name))
    parent = world.add(Entity(id=parent_name, kind="character", type="parent", label=parent_name))
    world.add(Entity(id=tool.id, kind="thing", type="tool", label=tool.label, phrase=tool.phrase, owner=child.id))

    world.facts.update(
        child=child,
        parent=parent,
        activity=activity,
        tool=tool,
        place=place,
    )

    begin(world, child, parent, activity, tool)
    world.say("")
    foreshadow(world, child, activity)
    tension(world, child, activity, tool)
    world.say("")
    turn(world, child, parent, activity, tool)
    world.say("")
    ending(world, child, activity, tool)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    parent = f["parent"]
    activity = f["activity"]
    tool = f["tool"]
    place = f["place"]
    return [
        f"Write a rhyming story about {child.id} making {activity.id.replace('_', ' ')} at {place.label}.",
        f"Tell a gentle foreshadowing story where {child.id} wants to {activity.verb} with {tool.label}.",
        f"Write a lesson-learned rhyming story about sunshine, patience, and {activity.id.replace('_', ' ')}.",
        f"Make a child-friendly rhyme about {child.id}, {parent.label}, and a sunny plan that needs waiting.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    parent = f["parent"]
    activity = f["activity"]
    tool = f["tool"]
    place = f["place"]
    return [
        QAItem(
            question=f"What did {child.id} want to do at {place.label}?",
            answer=f"{child.id} wanted to {activity.verb} with {tool.label}.",
        ),
        QAItem(
            question=f"What small hint showed that {child.id} might need to wait?",
            answer="A drifting cloud passed by, which hinted that the sunlight might not stay bright enough right away.",
        ),
        QAItem(
            question=f"What did {parent.label} tell {child.id} to remember?",
            answer="The parent told the child to be patient, because good things can take a little time.",
        ),
        QAItem(
            question=f"What happened at the end?",
            answer=f"The sun came back, the tea warmed up, and {child.id} learned that waiting can help a solar treat turn out well.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is solar energy?",
            answer="Solar energy is light and warmth that come from the sun.",
        ),
        QAItem(
            question="Why do people wait for sunshine when they use solar power?",
            answer="They wait because sunlight is what helps solar things work, so clouds can make them slower or weaker.",
        ),
        QAItem(
            question="What does tea usually need?",
            answer="Tea usually needs hot water or warmth so it can steep and taste cozy.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    lines.extend(sample.prompts)
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
        lines.append(f"{e.id}: {e.type}, label={e.label}")
    return "\n".join(lines)


ASP_RULES = r"""
place(backyard). place(garden). place(porch). place(kitchen).
indoor(kitchen).

activity(solar_tea). activity(tea).
affords(backyard,solar_tea). affords(garden,solar_tea). affords(porch,solar_tea). affords(kitchen,tea).
affords(backyard,tea). affords(garden,tea). affords(porch,tea).

tool(jar). tool(kettle).
helps(jar,solar_tea).
helps(kettle,tea).

valid(Place,Act,Tool) :- affords(Place,Act), helps(Tool,Act).
#show valid/3.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        if p.indoor:
            lines.append(asp.fact("indoor", pid))
        if p.sunny:
            lines.append(asp.fact("sunny", pid))
        for act in sorted(p.affords):
            lines.append(asp.fact("affords", pid, act))
    for aid in ACTIVITIES:
        lines.append(asp.fact("activity", aid))
    for tid, t in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        for act in sorted(t.helps):
            lines.append(asp.fact("helps", tid, act))
    return "\n".join(lines)


def asp_program() -> str:
    return asp_facts() + "\n" + ASP_RULES


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP matches Python ({len(py)} combos).")
        return 0
    print("MISMATCH:")
    print("Python only:", sorted(py - cl))
    print("ASP only:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A rhyming solar-tea storyworld.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--name")
    ap.add_argument("--parent")
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
    if args.activity:
        combos = [c for c in combos if c[1] == args.activity]
    if args.tool:
        combos = [c for c in combos if c[2] == args.tool]
    if not combos:
        raise StoryError("No valid solar-tea story matches those choices.")
    place, activity, tool = rng.choice(sorted(combos))
    name = args.name or rng.choice(GIRL_NAMES + BOY_NAMES)
    parent = args.parent or rng.choice(PARENT_NAMES)
    return StoryParams(place=place, activity=activity, tool=tool, name=name, parent=parent)


def generate(params: StoryParams) -> StorySample:
    world = tell(PLACES[params.place], ACTIVITIES[params.activity], TOOLS[params.tool], params.name, params.parent)
    return StorySample(
        params=params,
        story=world.render().strip(),
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
    StoryParams(place="garden", activity="solar_tea", tool="jar", name="Mia", parent="mom"),
    StoryParams(place="porch", activity="solar_tea", tool="jar", name="Leo", parent="dad"),
    StoryParams(place="backyard", activity="solar_tea", tool="jar", name="Nora", parent="grandma"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} valid combos:")
        for c in combos:
            print("  ", c)
        return

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        base_seed = args.seed if args.seed is not None else random.randrange(2**31)
        samples: list[StorySample] = []
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 40):
            i += 1
            seed = base_seed + i
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as e:
                print(e)
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
