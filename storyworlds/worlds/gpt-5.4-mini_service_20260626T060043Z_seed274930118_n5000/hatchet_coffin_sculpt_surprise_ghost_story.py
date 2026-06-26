#!/usr/bin/env python3
"""
storyworlds/worlds/hatchet_coffin_sculpt_surprise_ghost_story.py
=================================================================

A small, child-facing ghost-story world with a gentle spooky mood:
a hatchet, a coffin, a sculpting task, and a surprise that changes the end
image.

Seed tale used to build the simulation:
---
On a windy night, a child and a kind grandparent worked in a tiny workshop
beside an old graveyard. They wanted to sculpt a little wooden coffin for the
next lantern parade. The child picked up a hatchet, but the grandparent worried
the rough tool would split the wood. Then a soft knock came from the rafters:
it was a friendly ghost with a surprise idea. Together, they changed the plan,
made the coffin smooth and special, and the ghost's surprise turned the dark
night into a happy one.
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
    touched_by: Optional[str] = None
    protective: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "grandmother", "aunt"}
        male = {"boy", "father", "dad", "man", "grandfather", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str = "the workshop"
    atmosphere: str = "moonlit"
    affords: set[str] = field(default_factory=set)


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    mess: str
    soil: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    label: str
    phrase: str
    type: str
    fragile: bool = True


@dataclass
class Tool:
    id: str
    label: str
    careful: bool
    good_for: set[str]
    bad_for: set[str]


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.tool_in_hand: Optional[str] = None

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


def _sawdust(world: World) -> list[str]:
    out: list[str] = []
    actor = world.get("child")
    prize = world.get("coffin")
    if actor.meters.get("force", 0) >= THRESHOLD and world.tool_in_hand == "hatchet":
        sig = ("sawdust",)
        if sig not in world.fired:
            world.fired.add(sig)
            prize.meters["chips"] = prize.meters.get("chips", 0) + 1
            prize.meters["rough"] = prize.meters.get("rough", 0) + 1
            out.append("Little chips jumped from the wood.")
    return out


def _split_risk(world: World) -> list[str]:
    out: list[str] = []
    actor = world.get("child")
    prize = world.get("coffin")
    if actor.meters.get("force", 0) < THRESHOLD:
        return out
    if world.tool_in_hand != "hatchet":
        return out
    if prize.meters.get("rough", 0) < THRESHOLD:
        return out
    if ("split",) in world.fired:
        return out
    world.fired.add(("split",))
    actor.memes["worry"] = actor.memes.get("worry", 0) + 1
    out.append("The grandparent worried the rough hatchet might split the small coffin.")
    return out


def _ghost_surprise(world: World) -> list[str]:
    out: list[str] = []
    ghost = world.get("ghost")
    if ghost.memes.get("shy", 0) >= THRESHOLD and ghost.memes.get("helpful", 0) >= THRESHOLD:
        if ("surprise",) not in world.fired:
            world.fired.add(("surprise",))
            out.append("__surprise__")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for fn in (_sawdust, _split_risk, _ghost_surprise):
            sents = fn(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if s != "__surprise__")
    if narrate:
        for s in produced:
            world.say(s)
    return produced


SETTINGS = {
    "workshop": Setting(place="the workshop", atmosphere="moonlit", affords={"sculpt"}),
}

ACTIVITIES = {
    "sculpt": Activity(
        id="sculpt",
        verb="sculpt a little coffin",
        gerund="sculpting a little coffin",
        rush="carve too fast",
        mess="chips",
        soil="rough and splintery",
        keyword="sculpt",
        tags={"ghost", "coffin", "hatchet", "surprise"},
    ),
}

PRIZES = {
    "coffin": Prize(
        label="coffin",
        phrase="a small wooden coffin",
        type="coffin",
        fragile=True,
    ),
}

TOOLS = {
    "hatchet": Tool(
        id="hatchet",
        label="a hatchet",
        careful=False,
        good_for={"rough"},
        bad_for={"fine"},
    ),
    "file": Tool(
        id="file",
        label="a smooth file",
        careful=True,
        good_for={"fine"},
        bad_for=set(),
    ),
}

GHOST_NAMES = ["Misty", "Puff", "Wisp", "Mallow", "Moonbeam"]
CHILD_NAMES = ["Nina", "Theo", "Mina", "Owen", "Luca"]


@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    tool: str
    child_name: str
    seed: Optional[int] = None


def reasonableness_gate(place: str, activity: str, prize: str, tool: str) -> None:
    if place not in SETTINGS:
        raise StoryError("The setting does not fit this small ghost story.")
    if activity != "sculpt" or prize != "coffin":
        raise StoryError("This world only tells the coffin-sculpting ghost story.")
    if tool not in TOOLS:
        raise StoryError("Unknown tool for this story.")
    if tool == "hatchet":
        return
    raise StoryError("The story needs the rough hatchet to begin the problem.")


ASP_RULES = r"""
% A valid ghost-story exists when the workshop supports sculpting,
% the prize is a coffin, and the rough hatchet is the tool in play.
valid_story(Place, Activity, Prize, Tool) :-
    setting(Place), affords(Place, Activity),
    prize(Prize), tool(Tool),
    Activity = sculpt, Prize = coffin, Tool = hatchet.

% The hatchet is a risky tool for fine coffin work.
risky(Tool, Activity) :- tool(Tool), activity(Activity), Tool = hatchet, Activity = sculpt.

% The surprise arrives once the ghost is shy and helpful.
surprise :- ghost, shy, helpful.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for aid in ACTIVITIES:
        lines.append(asp.fact("activity", aid))
    for pid in PRIZES:
        lines.append(asp.fact("prize", pid))
    for tid in TOOLS:
        lines.append(asp.fact("tool", tid))
    lines.append(asp.fact("ghost"))
    lines.append(asp.fact("shy"))
    lines.append(asp.fact("helpful"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/4."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    python_set = {("workshop", "sculpt", "coffin", "hatchet")}
    clingo_set = set(asp_valid())
    if python_set == clingo_set:
        print("OK: clingo gate matches the Python gate (1 valid story).")
        return 0
    print("MISMATCH between clingo and Python gates.")
    print("python:", sorted(python_set))
    print("clingo:", sorted(clingo_set))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A gentle ghost story about a hatchet, a coffin, sculpting, and a surprise."
    )
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--tool", choices=TOOLS)
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
    place = args.place or "workshop"
    activity = args.activity or "sculpt"
    prize = args.prize or "coffin"
    tool = args.tool or "hatchet"
    reasonableness_gate(place, activity, prize, tool)
    name = args.name or rng.choice(CHILD_NAMES)
    return StoryParams(place=place, activity=activity, prize=prize, tool=tool, child_name=name)


def _build_world(params: StoryParams) -> World:
    world = World(SETTINGS[params.place])
    child = world.add(Entity(id="child", kind="character", type="boy", label=params.child_name))
    grandparent = world.add(Entity(id="grandparent", kind="character", type="grandfather", label="Grandpa"))
    coffin = world.add(Entity(id="coffin", type="coffin", label="coffin", phrase="a small wooden coffin", caretaker=grandparent.id))
    ghost = world.add(Entity(id="ghost", kind="character", type="ghost", label="the ghost"))
    hatchet = world.add(Entity(id="hatchet", type="tool", label="hatchet", phrase="a hatchet"))
    filetool = world.add(Entity(id="file", type="tool", label="file", phrase="a smooth file"))
    world.tool_in_hand = params.tool

    ghost.memes["shy"] = 1.0
    ghost.memes["helpful"] = 1.0

    world.say(f"{params.child_name} was a curious child who loved the moonlit workshop.")
    world.say(f"{params.child_name} wanted to {ACTIVITIES[params.activity].verb} with {TOOLs if False else ''}".replace(" with ", " "))
    world.say(f"The worktable held {coffin.phrase}, and {params.child_name} picked up {TOOLS[params.tool].label}.")
    world.say(f"Grandpa looked over and frowned a little. He knew a hatchet could make fine work rough.")
    world.para()
    child.meters["force"] = 1.0
    child.memes["joy"] = 1.0
    child.memes["want"] = 1.0
    propagate(world, narrate=False)
    world.say(f"{params.child_name} started to {ACTIVITIES[params.activity].verb}, and tiny wood chips sprang up like pale snow.")
    if world.tool_in_hand == "hatchet":
        world.say("The hatchet could shape the wood, but it was not the gentlest tool.")
    world.say("Then there came a soft knock from the rafters.")
    world.say("It was a friendly ghost with a surprise idea.")
    world.para()
    if world.tool_in_hand == "hatchet":
        world.say(f'“Let us begin with the hatchet, then finish with the file,” the ghost whispered. “Surprise!”')
        world.tool_in_hand = "file"
        world.say("Together, they switched to the smooth file and turned the rough shape into a neat little coffin.")
    world.say("By the end, the coffin looked smooth and careful, and the ghost floated happily above it like a candle flame.")
    world.say(f"{params.child_name} smiled, because the surprise had changed the scary night into a warm one.")
    world.facts.update(child=child, grandparent=grandparent, coffin=coffin, ghost=ghost, params=params)
    return world


def generation_prompts(world: World) -> list[str]:
    p = world.facts["params"]
    return [
        'Write a gentle ghost story for a young child that includes a hatchet, a coffin, and a surprise.',
        f"Tell a moonlit story where {p.child_name} wants to sculpt a coffin but a friendly ghost changes the plan.",
        "Write a child-facing spooky story where rough tools become a softer idea by the end.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p = world.facts["params"]
    return [
        QAItem(
            question=f"What did {p.child_name} want to do in the workshop?",
            answer=f"{p.child_name} wanted to sculpt a little coffin in the moonlit workshop.",
        ),
        QAItem(
            question=f"Why did Grandpa worry about the hatchet?",
            answer="Grandpa worried because the hatchet was rough and could make the small coffin splinter.",
        ),
        QAItem(
            question="What surprise changed the story?",
            answer="A friendly ghost knocked from the rafters and suggested using a smoother tool to finish the coffin.",
        ),
        QAItem(
            question="How did the story end?",
            answer="The coffin ended up smooth and careful, and the night felt warm instead of scary.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a hatchet?",
            answer="A hatchet is a small axe with a short handle. People use it for rough cutting or splitting.",
        ),
        QAItem(
            question="What is a coffin?",
            answer="A coffin is a box used for a person or creature that has died. In stories, it can also be a spooky object.",
        ),
        QAItem(
            question="What does sculpting mean?",
            answer="Sculpting means shaping a material like wood, clay, or stone into a form.",
        ),
        QAItem(
            question="What is a surprise?",
            answer="A surprise is something unexpected that makes you pause and look closely.",
        ),
        QAItem(
            question="What makes a ghost story spooky instead of mean?",
            answer="A gentle ghost story uses shadows, quiet sounds, and surprise, but it stays kind and safe.",
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
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:10} ({e.type:9}) {' '.join(bits)}")
    lines.append(f"  tool_in_hand={world.tool_in_hand}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = _build_world(params)
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
    StoryParams(place="workshop", activity="sculpt", prize="coffin", tool="hatchet", child_name="Nina"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        triples = asp_valid()
        print(f"{len(triples)} compatible story tuple(s):")
        for t in triples:
            print(" ", t)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 20, 20):
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
