#!/usr/bin/env python3
"""
Storyworld: expression rhyme bedtime story.

A tiny, self-contained story domain for a child-facing bedtime tale where a
little character learns how an expression can change the mood, and a rhyme can
turn bedtime from bumpy to calm.

The world model tracks:
- physical items like a blanket, a nightlight, and a rhyme card
- emotional state like sleepy, worried, and soothed
- one central tension: a child cannot settle until they find the right bedtime
  expression and a soft rhyme to help a younger sibling or plush friend feel safe

This script supports:
- text and JSON output
- QA prompts
- trace output
- an inline ASP twin for the reasonableness gate
- verification that the Python and ASP gates agree
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
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    held_by: Optional[str] = None
    plural: bool = False
    protective: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "character" and self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.kind == "character" and self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the nursery"
    affords: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    kind: str
    helps: set[str]
    mood_boost: float = 1.0
    phrase: str = ""


@dataclass
class StoryParams:
    place: str
    activity: str
    tool: str
    name: str
    gender: str
    parent: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
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

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def copy(self) -> "World":
        import copy
        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        return w


@dataclass
class Rule:
    name: str
    apply: callable


def _r_worry(world: World) -> list[str]:
    out: list[str] = []
    for e in world.characters():
        if e.memes.get("worry", 0.0) >= THRESHOLD and ("worry", e.id) not in world.fired:
            world.fired.add(("worry", e.id))
            out.append(f"{e.id} frowned, and the room felt heavier for a moment.")
    return out


def _r_soothe(world: World) -> list[str]:
    out: list[str] = []
    for e in world.characters():
        if e.memes.get("soothed", 0.0) >= THRESHOLD and ("soothe", e.id) not in world.fired:
            world.fired.add(("soothe", e.id))
            out.append(f"{e.id} let out a tiny sigh, as if a knot had loosened inside.")
    return out


CAUSAL_RULES = [Rule("worry", _r_worry), Rule("soothe", _r_soothe)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def valid_activity(activity: str) -> bool:
    return activity in ACTIVITIES


def valid_tool(activity: str, tool: str) -> bool:
    return tool in TOOLS and activity in TOOLS[tool].helps


def reasonableness_gate(activity: str, tool: str) -> bool:
    return valid_activity(activity) and valid_tool(activity, tool)


def _act(world: World, child: Entity, activity: str, narrate: bool = True) -> None:
    if activity not in ACTIVITIES:
        raise StoryError(f"Unknown activity: {activity}")
    child.memes[activity] = child.memes.get(activity, 0.0) + 1
    if activity == "tumble":
        child.memes["worry"] = child.memes.get("worry", 0.0) + 1
    if activity == "hum":
        child.memes["soothed"] = child.memes.get("soothed", 0.0) + 1
    propagate(world, narrate=narrate)


def predict_settle(world: World, child: Entity, activity: str, tool: Tool) -> bool:
    sim = world.copy()
    _act(sim, sim.get(child.id), activity, narrate=False)
    sim.get(child.id).memes["soothed"] = sim.get(child.id).memes.get("soothed", 0.0) + tool.mood_boost
    return sim.get(child.id).memes.get("soothed", 0.0) >= THRESHOLD


def intro(world: World, child: Entity) -> None:
    world.say(f"{child.id} was a little {child.type} who loved the soft hush of bedtime.")


def favorite(world: World, child: Entity) -> None:
    world.say(f"{child.pronoun().capitalize()} had a face that could sparkle with a smile or scrunch with a frown.")


def arrive(world: World, child: Entity, parent: Entity) -> None:
    world.say(f"One evening, {child.id} and {child.pronoun('possessive')} {parent.type} went to {world.setting.place}.")
    world.say("The lamp glowed low, and the blanket waited like a warm cloud.")


def want(world: World, child: Entity, activity: str) -> None:
    world.say(f"{child.id} wanted to {activity} before sleep, because {child.pronoun('subject')} was still full of play.")


def worry(world: World, parent: Entity, child: Entity) -> None:
    child.memes["worry"] = child.memes.get("worry", 0.0) + 1
    world.say(f"{parent.pronoun().capitalize()} noticed the tired frown on {child.id}'s face and spoke softly.")


def rhyme_prompt(activity: str) -> str:
    return RHYMES[activity]


def offer_tool(world: World, parent: Entity, child: Entity, activity: str, tool: Tool) -> bool:
    if not predict_settle(world, child, activity, tool):
        return False
    world.say(
        f'"Let us use the {tool.label}," said the {parent.type}, "and we can {activity} with a gentle rhyme."'
    )
    return True


def accept(world: World, child: Entity, parent: Entity, activity: str, tool: Tool) -> None:
    child.memes["soothed"] = child.memes.get("soothed", 0.0) + tool.mood_boost
    child.memes["worry"] = max(0.0, child.memes.get("worry", 0.0) - 1)
    propagate(world, narrate=False)
    world.say(f"{child.id} listened, and {child.pronoun('subject')} tried the little rhyme:")
    world.say(f'"{rhyme_prompt(activity)}"')
    world.say(
        f"The words were small and sweet, and {child.id}'s face changed into a sleepy expression at last."
    )
    world.say(
        f"{child.id} tucked {child.pronoun('possessive')} {tool.label} close and settled down beside {parent.id},"
        f"with the room all calm and dim."
    )


SETTINGS = {
    "nursery": Setting(place="the nursery", affords={"hum", "tumble"}),
    "bedroom": Setting(place="the bedroom", affords={"hum", "tumble"}),
    "windowseat": Setting(place="the window seat", affords={"hum", "tumble"}),
}

ACTIVITIES = {
    "hum": "hum",
    "tumble": "tumble",
}

TOOLS = {
    "nightlight": Tool(
        id="nightlight",
        label="nightlight",
        kind="light",
        helps={"tumble"},
        mood_boost=1.0,
        phrase="a warm little light",
    ),
    "rhyme_card": Tool(
        id="rhyme_card",
        label="rhyme card",
        kind="card",
        helps={"hum", "tumble"},
        mood_boost=1.0,
        phrase="a card with a soft rhyme",
    ),
    "blanket": Tool(
        id="blanket",
        label="blanket",
        kind="cloth",
        helps={"hum"},
        mood_boost=1.0,
        phrase="a warm blanket",
    ),
}

RHYMES = {
    "hum": "Hush now, star, and hush now, tree; sleepy thoughts can come to me.",
    "tumble": "Step by step, the moon will beam; slow soft feet can drift like dream.",
}

GIRL_NAMES = ["Maya", "Lila", "Nina", "Ruby", "Tessa"]
BOY_NAMES = ["Owen", "Eli", "Theo", "Finn", "Milo"]
TRAITS = ["gentle", "curious", "spirited", "shy", "cheerful"]


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place in SETTINGS:
        for activity in ACTIVITIES:
            for tool in TOOLS:
                if reasonableness_gate(activity, tool):
                    out.append((place, activity, tool))
    return out


def explain_rejection(activity: str, tool: str) -> str:
    if activity not in ACTIVITIES:
        return f"(No story: unknown activity {activity!r}.)"
    if tool not in TOOLS:
        return f"(No story: unknown tool {tool!r}.)"
    return f"(No story: the {tool} does not reasonably help with {activity} in this bedtime tale.)"


@dataclass
class StoryWorldFacts:
    child: Entity
    parent: Entity
    tool: Entity
    activity: str
    place: str


def tell(setting: Setting, activity: str, tool_def: Tool, name: str, gender: str, parent_type: str) -> World:
    world = World(setting)
    child = world.add(Entity(id=name, kind="character", type=gender))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type))
    tool = world.add(Entity(id=tool_def.id, type=tool_def.kind, label=tool_def.label, phrase=tool_def.phrase, owner=child.id))

    intro(world, child)
    favorite(world, child)
    world.para()
    arrive(world, child, parent)
    want(world, child, activity)
    worry(world, parent, child)
    _act(world, child, activity)
    world.para()
    if offer_tool(world, parent, child, activity, tool_def):
        accept(world, child, parent, activity, tool_def)

    world.facts["facts"] = StoryWorldFacts(child=child, parent=parent, tool=tool, activity=activity, place=setting.place)
    world.facts["resolved"] = True
    return world


KNOWLEDGE = {
    "expression": [
        (
            "What is an expression?",
            "An expression is the look on someone's face, like a smile, a frown, or wide sleepy eyes.",
        )
    ],
    "rhyme": [
        (
            "What is a rhyme?",
            "A rhyme is a pair of words or lines that sound alike at the end, which can make words feel musical.",
        )
    ],
    "bedtime": [
        (
            "Why do people have bedtime routines?",
            "A bedtime routine helps the body and mind slow down so it is easier to rest.",
        )
    ],
    "nightlight": [
        (
            "What does a nightlight do?",
            "A nightlight gives a small, gentle glow that helps a room feel less dark at night.",
        )
    ],
    "blanket": [
        (
            "Why do blankets feel nice at bedtime?",
            "A blanket feels nice because it is soft and warm, which can help a sleepy person feel safe and cozy.",
        )
    ],
}


def generation_prompts(world: World) -> list[str]:
    f = world.facts["facts"]
    return [
        f'Write a bedtime story for a young child about an expression and a rhyme, using the word "expression".',
        f"Tell a gentle story where {f.child.id} wants to {f.activity} at {f.place}, and a parent offers a soothing rhyme.",
        "Write a soft bedtime tale that begins with worry, then settles into a calm expression.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts["facts"]
    child, parent, tool, activity, place = f.child, f.parent, f.tool, f.activity, f.place
    qa = [
        QAItem(
            question=f"Who is the story about at {place}?",
            answer=f"It is about {child.id}, a little {child.type} who is getting ready for bedtime with {parent.id}.",
        ),
        QAItem(
            question=f"What did {child.id} want to do before sleep?",
            answer=f"{child.id} wanted to {activity} before sleep because the day still felt lively.",
        ),
        QAItem(
            question=f"What helpful thing did the parent offer?",
            answer=f"The parent offered the {tool.label} and a soft rhyme to help {child.id} settle down.",
        ),
        QAItem(
            question=f"How did {child.id}'s face change at the end?",
            answer=f"{child.id}'s face changed into a sleepy, peaceful expression at the end.",
        ),
    ]
    if tool.label == "rhyme card":
        qa.append(
            QAItem(
                question=f"Why was the rhyme card helpful for {child.id}?",
                answer=f"It helped because the rhyme made the moment feel gentle, and that helped {child.id} become calm enough for bed.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    out: list[QAItem] = []
    tags = {"expression", "rhyme", "bedtime"}
    tool = world.facts["facts"].tool
    tags.add(tool.label.replace(" ", "_"))
    for tag in ["expression", "rhyme", "bedtime", "nightlight", "blanket"]:
        if tag in tags and tag in KNOWLEDGE:
            out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE[tag])
    return out


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
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.label:
            bits.append(f"label={e.label}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="nursery", activity="hum", tool="rhyme_card", name="Maya", gender="girl", parent="mother"),
    StoryParams(place="bedroom", activity="tumble", tool="nightlight", name="Owen", gender="boy", parent="father"),
    StoryParams(place="windowseat", activity="hum", tool="blanket", name="Lila", gender="girl", parent="mother"),
]


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("place", pid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", pid, a))
    for aid in ACTIVITIES:
        lines.append(asp.fact("activity", aid))
    for tid, t in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        for a in sorted(t.helps):
            lines.append(asp.fact("helps", tid, a))
    return "\n".join(lines)


ASP_RULES = r"""
valid(Place, Activity, Tool) :- place(Place), activity(Activity), tool(Tool), affords(Place, Activity), helps(Tool, Activity).
#show valid/3.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A bedtime story world about expression and rhyme.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--tool", choices=TOOLS)
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
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.activity is None or c[1] == args.activity)
              and (args.tool is None or c[2] == args.tool)]
    if not combos:
        raise StoryError("No valid bedtime story combination matches the given options.")
    place, activity, tool = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    if args.tool and not valid_tool(activity, args.tool):
        raise StoryError(explain_rejection(activity, args.tool))
    return StoryParams(place=place, activity=activity, tool=tool, name=name, gender=gender, parent=parent)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], params.activity, TOOLS[params.tool], params.name, params.gender, params.parent)
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
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, activity, tool) combos:")
        for c in combos:
            print(" ", c)
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.activity} at {p.place} (tool: {p.tool})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
