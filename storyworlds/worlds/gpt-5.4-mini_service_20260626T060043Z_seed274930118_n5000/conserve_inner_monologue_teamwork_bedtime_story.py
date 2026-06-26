#!/usr/bin/env python3
"""
storyworlds/worlds/conserve_inner_monologue_teamwork_bedtime_story.py
======================================================================

A small bedtime-story world about a child, a cozy night, and learning to
conserve something important with gentle teamwork and an inner monologue.

Seed premise:
- At bedtime, a child wants one more round of cozy activity.
- A parent or sibling worries about wasting a shared resource.
- The child thinks quietly to themself, then everyone finds a kinder way.
- The ending image proves the resource was conserved and the room stayed cozy.

This world emphasizes:
- Inner monologue as a story instrument.
- Teamwork as the resolution.
- Bedtime-story tone: soft, concrete, child-facing, calm.
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
# World model
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "sister"}
        male = {"boy", "father", "dad", "man", "brother"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    mood: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    resource: str
    waste: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Resource:
    label: str
    phrase: str
    type: str
    conserve_kind: str  # "light" | "water" | "heat" | "paper"
    vulnerable: str
    genders: set[str] = field(default_factory=lambda: {"girl", "boy"})


@dataclass
class Tool:
    id: str
    label: str
    prep: str
    tail: str
    protects: set[str] = field(default_factory=set)
    saves: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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

        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        return clone

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "bedroom": Setting(place="the bedroom", mood="soft", affords={"book", "lamp", "water"}),
    "nursery": Setting(place="the nursery", mood="gentle", affords={"book", "lamp"}),
    "hall": Setting(place="the hallway by the bedrooms", mood="quiet", affords={"lamp"}),
}

ACTIVITIES = {
    "book": Activity(
        id="book",
        verb="read one more story",
        gerund="reading one more story",
        rush="reach for another page",
        resource="light",
        waste="electricity",
        keyword="bedtime",
        tags={"book", "light"},
    ),
    "lamp": Activity(
        id="lamp",
        verb="keep the lamp on all night",
        gerund="keeping the lamp on",
        rush="leave the lamp glowing",
        resource="light",
        waste="electricity",
        keyword="lamp",
        tags={"lamp", "light"},
    ),
    "water": Activity(
        id="water",
        verb="let the bathwater keep running",
        gerund="watching the warm water run",
        rush="leave the faucet open",
        resource="water",
        waste="water",
        keyword="water",
        tags={"water"},
    ),
    "wash": Activity(
        id="wash",
        verb="wash one more stuffed animal",
        gerund="washing one more stuffed animal",
        rush="use extra water",
        resource="water",
        waste="water",
        keyword="wash",
        tags={"water", "toy"},
    ),
}

RESOURCES = {
    "light": Resource(
        label="lamp light",
        phrase="a warm little lamp",
        type="lamp",
        conserve_kind="light",
        vulnerable="electricity",
    ),
    "water": Resource(
        label="bathwater",
        phrase="a tub of warm bathwater",
        type="water",
        conserve_kind="water",
        vulnerable="water",
    ),
    "blanket": Resource(
        label="blanket warmth",
        phrase="a soft blanket",
        type="blanket",
        conserve_kind="heat",
        vulnerable="heat",
    ),
}

TOOLS = [
    Tool(
        id="booklight",
        label="one shared bedside lamp",
        prep="share one bedside lamp and read together",
        tail="used only one lamp instead of two",
        protects={"light"},
        saves={"electricity"},
    ),
    Tool(
        id="towel",
        label="a warm towel",
        prep="wrap the toy up in a warm towel and stop at one bath",
        tail="turned the faucet off together",
        protects={"water"},
        saves={"water"},
    ),
    Tool(
        id="blanket",
        label="one big blanket",
        prep="pull one big blanket over both of them",
        tail="kept the room cozy without turning up the heater",
        protects={"heat"},
        saves={"heat"},
    ),
]

CHILD_NAMES = ["Maya", "Eli", "Nora", "Leo", "Zoe", "Ivy", "Noah", "Luna"]
PARENT_TYPES = ["mother", "father"]
SIBLING_TYPES = ["sister", "brother"]
TRAITS = ["sleepy", "curious", "gentle", "cozy", "careful", "sensitive"]


# ---------------------------------------------------------------------------
# Story parameters
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    activity: str
    resource: str
    name: str
    parent: str
    helper: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------
def resource_at_risk(activity: Activity, resource: Resource) -> bool:
    return activity.resource == resource.conserve_kind


def select_tool(activity: Activity, resource: Resource) -> Optional[Tool]:
    for tool in TOOLS:
        if activity.resource in tool.protects and resource.vulnerable in tool.saves:
            return tool
    return None


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            act = ACTIVITIES[act_id]
            for res_id, res in RESOURCES.items():
                if resource_at_risk(act, res) and select_tool(act, res):
                    combos.append((place, act_id, res_id))
    return combos


def explain_rejection(activity: Activity, resource: Resource) -> str:
    if not resource_at_risk(activity, resource):
        return (
            f"(No story: {activity.gerund} would not really waste {resource.label}, "
            f"so there is no honest worry to solve.)"
        )
    return (
        f"(No story: there is no compatible bedtime tool that both fits {activity.gerund} "
        f"and helps conserve {resource.label}.)"
    )


# ---------------------------------------------------------------------------
# World simulation
# ---------------------------------------------------------------------------
def predict_waste(world: World, activity: Activity, resource_id: str) -> bool:
    sim = world.copy()
    sim.facts["wasting"] = True
    tool = select_tool(activity, RESOURCES[resource_id])
    if tool is None:
        return True
    return False


def _do_activity(world: World, child: Entity, activity: Activity) -> None:
    child.memes["desire"] = child.memes.get("desire", 0.0) + 1.0
    world.facts["activity_started"] = activity.id


def tell(
    setting: Setting,
    activity: Activity,
    resource_cfg: Resource,
    hero_name: str = "Maya",
    hero_type: str = "girl",
    parent_type: str = "mother",
    helper_type: str = "sister",
    trait: str = "sleepy",
) -> World:
    world = World(setting)

    child = world.add(Entity(id=hero_name, kind="character", type=hero_type, traits=["little", trait]))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label="mom" if parent_type == "mother" else "dad"))
    helper = world.add(Entity(id="Helper", kind="character", type=helper_type, label="big sister" if helper_type == "sister" else "big brother"))
    resource = world.add(Entity(id="Resource", type=resource_cfg.type, label=resource_cfg.label, phrase=resource_cfg.phrase, owner=child.id))

    world.say(f"It was bedtime in {setting.place}, and the room was soft and quiet.")
    world.say(f"{child.id} was a little {trait} {hero_type} who loved the calm of night.")
    world.say(f"{child.id} loved {activity.gerund} because it felt cozy and safe.")

    world.para()
    world.say(
        f"At first, {child.id} wanted to {activity.verb}, even though {parent.pronoun('subject').capitalize()} "
        f"was watching {resource.label} carefully."
    )
    if activity.id == "book":
        world.say(f"{child.id} held the book close and felt one more page tugging at {heredoc(child)}.")
    elif activity.id == "lamp":
        world.say(f"The little lamp glowed like a tiny moon, and {child.id} did not want it to go dark.")
    elif activity.id == "water":
        world.say(f"The warm bathwater steamed a little, and {child.id} thought the splashy fun should keep going.")
    else:
        world.say(f"The stuffed animal was still wet, and {child.id} wanted just one more wash.")

    world.say(f"In {child.id}'s quiet little mind, a thought whispered: 'Maybe I can have my wish and still conserve.'")

    world.para()
    world.say(
        f"{parent.pronoun('subject').capitalize()} smiled gently and said that bedtime was already full enough, "
        f"and that they should help the room stay calm and save {resource.label}."
    )
    world.say(
        f"{helper.pronoun('subject').capitalize()} stepped in too, because teamwork makes bedtime easier."
    )

    tool = select_tool(activity, resource_cfg)
    if tool is None:
        raise StoryError(explain_rejection(activity, resource_cfg))

    world.say(
        f"Together they chose {tool.label}; {tool.prep}, and {child.id} nodded because it sounded kind."
    )
    world.say(
        f"{child.id} thought, 'If we do this together, we can still feel cozy and not waste anything.'"
    )
    world.say(
        f"So they {tool.tail}, and the room stayed soft instead of bright and busy."
    )

    world.para()
    world.say(
        f"At the end, {child.id} curled up with {helper.pronoun('possessive')} help, {parent.pronoun('subject')} tucked the blanket neatly, "
        f"and the little {resource.label} was saved for tomorrow."
    )
    world.say(
        f"{child.id} fell asleep feeling proud, because teamwork had turned a want into a gentle plan."
    )

    world.facts.update(
        child=child,
        parent=parent,
        helper=helper,
        resource=resource,
        activity=activity,
        tool=tool,
        setting=setting,
    )
    return world


def heredoc(child: Entity) -> str:
    return child.pronoun("object")


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    activity = f["activity"]
    resource = f["resource"]
    return [
        f'Write a bedtime story for a child named {child.id} who wants to {activity.verb} but learns to conserve {resource.label}.',
        f"Tell a cozy story where {child.id} has an inner monologue and the family uses teamwork to save {resource.label}.",
        f"Write a gentle bedtime story about choosing a careful plan instead of wasting {resource.label} at night.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    parent = f["parent"]
    helper = f["helper"]
    activity = f["activity"]
    resource = f["resource"]
    tool = f["tool"]
    return [
        QAItem(
            question=f"What did {child.id} want to do at bedtime?",
            answer=f"{child.id} wanted to {activity.verb}, but then everyone worked together to make a gentler plan.",
        ),
        QAItem(
            question=f"Why did {parent.label} worry?",
            answer=f"{parent.label} worried because {activity.gerund} would waste {resource.label}.",
        ),
        QAItem(
            question=f"How did the family solve the problem?",
            answer=f"They used {tool.label}, so {child.id} could keep the cozy feeling while conserving {resource.label}.",
        ),
        QAItem(
            question=f"Who helped {child.id} besides {parent.label}?",
            answer=f"{helper.label} helped too, and that teamwork made the bedtime plan feel easy.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does it mean to conserve something?",
            answer="To conserve something means to use less of it so some is left for later.",
        ),
        QAItem(
            question="Why is bedtime often calm?",
            answer="Bedtime is often calm because people are getting ready to rest, so they use softer voices and gentler actions.",
        ),
        QAItem(
            question="What is teamwork?",
            answer="Teamwork is when people help each other and do a job together.",
        ),
        QAItem(
            question="What is an inner monologue?",
            answer="An inner monologue is the quiet voice a person thinks in their own mind.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
resource_at_risk(A, R) :- activity(A), resource(R), activity_resource(A, K), resource_kind(R, K).
compatible(A, R) :- resource_at_risk(A, R), tool(T), tool_handles(T, K), activity_resource(A, K), tool_saves(T, V), resource_vulnerable(R, V).
valid_story(P, A, R) :- setting(P), affords(P, A), resource_at_risk(A, R), compatible(A, R).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", pid, a))
    for aid, a in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        lines.append(asp.fact("activity_resource", aid, a.resource))
    for rid, r in RESOURCES.items():
        lines.append(asp.fact("resource", rid))
        lines.append(asp.fact("resource_kind", rid, r.conserve_kind))
        lines.append(asp.fact("resource_vulnerable", rid, r.vulnerable))
    for t in TOOLS:
        lines.append(asp.fact("tool", t.id))
        for p in sorted(t.protects):
            lines.append(asp.fact("tool_handles", t.id, p))
        for s in sorted(t.saves):
            lines.append(asp.fact("tool_saves", t.id, s))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    python_set = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if python_set == asp_set:
        print(f"OK: ASP matches Python gate ({len(python_set)} combos).")
        return 0
    print("MISMATCH between ASP and Python gates:")
    if asp_set - python_set:
        print("  only in ASP:", sorted(asp_set - python_set))
    if python_set - asp_set:
        print("  only in Python:", sorted(python_set - asp_set))
    return 1


# ---------------------------------------------------------------------------
# Storyworld interface
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A cozy bedtime story world about conserving something with teamwork.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--resource", choices=RESOURCES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=PARENT_TYPES)
    ap.add_argument("--helper", choices=SIBLING_TYPES)
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
    if args.activity and args.resource:
        act, res = ACTIVITIES[args.activity], RESOURCES[args.resource]
        if not resource_at_risk(act, res) or not select_tool(act, res):
            raise StoryError(explain_rejection(act, res))

    combos = [
        c for c in valid_combos()
        if (args.place is None or c[0] == args.place)
        and (args.activity is None or c[1] == args.activity)
        and (args.resource is None or c[2] == args.resource)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place, activity, resource = rng.choice(sorted(combos))
    name = args.name or rng.choice(CHILD_NAMES)
    gender = args.gender or rng.choice(["girl", "boy"])
    parent = args.parent or rng.choice(PARENT_TYPES)
    helper = args.helper or rng.choice(SIBLING_TYPES)
    trait = rng.choice(TRAITS)

    return StoryParams(
        place=place,
        activity=activity,
        resource=resource,
        name=name,
        parent=parent,
        helper=helper,
        trait=trait,
        seed=args.seed,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.place],
        ACTIVITIES[params.activity],
        RESOURCES[params.resource],
        hero_name=params.name,
        hero_type="girl" if params.seed is not None and params.seed % 2 == 0 else "boy" if params.seed is not None and params.seed % 3 == 0 else ("girl" if params.name in {"Maya", "Nora", "Ivy", "Luna", "Zoe"} else "boy"),
        parent_type=params.parent,
        helper_type=params.helper,
        trait=params.trait,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.traits:
            bits.append(f"traits={e.traits}")
        if e.label:
            bits.append(f"label={e.label}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


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
    StoryParams(place="bedroom", activity="book", resource="light", name="Maya", parent="mother", helper="sister", trait="curious"),
    StoryParams(place="nursery", activity="lamp", resource="light", name="Leo", parent="father", helper="brother", trait="sleepy"),
    StoryParams(place="bedroom", activity="water", resource="water", name="Nora", parent="mother", helper="sister", trait="gentle"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible bedtime combos:\n")
        for p, a, r in combos:
            print(f"  {p:10} {a:10} {r:10}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
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
