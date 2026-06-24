#!/usr/bin/env python3
"""
storyworlds/worlds/hearth_twist_ghost_story.py
==============================================

A small, child-facing ghost story world about a hearth, a chill room, and a
twist that turns the scary-feeling thing into a friendly helper.

Seed tale, imagined and then modeled:
---
On a cold evening, a child sat beside the hearth and tried to be brave.
The fire was low, the room felt drafty, and every little creak sounded spooky.
Then a small ghost drifted out of the shadows. The child froze at first, but
the ghost was not there to frighten anyone. It wanted to help.

The ghost nudged a stuck bellows handle, brought back a lost ember from behind
the hearth, and made the fire glow warm again. The room stopped feeling cold,
and the child learned that sometimes a twist in a ghost story is a kind surprise.
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
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"warmth": 0.0, "soot": 0.0, "draft": 0.0, "glow": 0.0}
        if not self.memes:
            self.memes = {"brave": 0.0, "fear": 0.0, "wonder": 0.0, "comfort": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the cottage room"
    affords: set[str] = field(default_factory=set)


@dataclass
class Scenario:
    id: str
    keyword: str
    scare: str
    fix: str
    ending: str
    zone: set[str]
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    guards: set[str]
    covers: set[str]
    tail: str
    plural: bool = False


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.zone: set[str] = set()
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
        import copy
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.zone = set(self.zone)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def worn_items(self, actor: Entity) -> list[Entity]:
        return [e for e in self.entities.values() if e.worn_by == actor.id]

    def covered(self, actor: Entity, region: str) -> bool:
        return any(g.protective and region in g.covers for g in self.worn_items(actor))


SCENARIOS = {
    "hearth": Scenario(
        id="hearth",
        keyword="hearth",
        scare="the hearth looked like a mouth of coals in the dark",
        fix="the room felt chilly and the fire was too low",
        ending="the hearth glowed like a sleepy gold moon",
        zone={"torso", "hands"},
        tags={"fire", "warmth", "ghost"},
    ),
    "draft": Scenario(
        id="draft",
        keyword="draft",
        scare="a cold draft slipped through the room and lifted the curtains",
        fix="the child felt shivery near the old stones",
        ending="the draft tucked itself away and the room felt snug",
        zone={"torso"},
        tags={"cold", "ghost", "wind"},
    ),
}

TOOLS = [
    Tool(
        id="blanket",
        label="blanket",
        phrase="a thick blanket",
        guards={"draft"},
        covers={"torso"},
        tail="pulled the blanket tight over the child's shoulders",
    ),
    Tool(
        id="bellows",
        label="bellows",
        phrase="an old bellows",
        guards={"low_fire"},
        covers={"hands"},
        tail="squeezed the bellows until the embers woke up",
    ),
    Tool(
        id="lantern",
        label="lantern",
        phrase="a small lantern",
        guards={"dark"},
        covers={"hands"},
        tail="set the lantern on the floor so the shadows looked smaller",
    ),
]

SETTINGS = {
    "cottage": Setting(place="the cottage room", affords={"hearth", "draft"}),
    "hall": Setting(place="the old hall", affords={"draft"}),
}

GHOST_NAMES = ["Moss", "Pip", "Nell", "Wisp", "Ivy"]
CHILD_NAMES = ["Mina", "Owen", "Lia", "Noah", "Tess"]
TRAITS = ["brave", "quiet", "curious", "careful"]


def hearth_at_risk(scenario: Scenario) -> bool:
    return True


def select_tool(scenario: Scenario) -> Optional[Tool]:
    if scenario.id == "hearth":
        return next((t for t in TOOLS if t.id == "bellows"), None)
    if scenario.id == "draft":
        return next((t for t in TOOLS if t.id == "blanket"), None)
    return None


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for sid, sc in SCENARIOS.items():
        lines.append(asp.fact("scenario", sid))
        for t in sorted(sc.tags):
            lines.append(asp.fact("tag", sid, t))
    for tool in TOOLS:
        lines.append(asp.fact("tool", tool.id))
        for g in sorted(tool.guards):
            lines.append(asp.fact("guards", tool.id, g))
        for c in sorted(tool.covers):
            lines.append(asp.fact("covers", tool.id, c))
    return "\n".join(lines)


ASP_RULES = r"""
needs_fix(S) :- scenario(S), tag(S, warmth).
needs_fix(S) :- scenario(S), tag(S, cold).
has_tool(S,T) :- needs_fix(S), guards(T, warm_fire), tool(T).
has_tool(S,T) :- needs_fix(S), guards(T, draft), tool(T).
valid_story(P,S) :- affords(P,S), scenario(S), needs_fix(S), has_tool(S,_).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def valid_combos() -> list[tuple[str, str]]:
    out = []
    for place, setting in SETTINGS.items():
        for sid in setting.affords:
            if hearth_at_risk(SCENARIOS[sid]) and select_tool(SCENARIOS[sid]):
                out.append((place, sid))
    return out


@dataclass
class StoryParams:
    place: str
    scenario: str
    name: str
    gender: str
    ghost: str
    trait: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny hearth-and-ghost story world.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--scenario", choices=SCENARIOS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--ghost")
    ap.add_argument("--trait", choices=TRAITS)
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
              and (args.scenario is None or c[1] == args.scenario)]
    if not combos:
        raise StoryError("No valid hearth story matches the given options.")
    place, scenario = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(CHILD_NAMES)
    ghost = args.ghost or rng.choice(GHOST_NAMES)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, scenario=scenario, name=name, gender=gender, ghost=ghost, trait=trait)


def _setup(world: World, child: Entity, ghost: Entity, hearth: Entity, scenario: Scenario) -> None:
    world.say(f"{child.id} was a {child.meters and child.meters is not None and '' or ''}{child.pronoun().capitalize()} sat close to the hearth in {world.setting.place}.")
    world.say(f"The room felt quiet, but {scenario.scare}.")
    child.memes["brave"] += 1
    hearth.meters["glow"] += 1
    hearth.meters["warmth"] += 1


def _twist(world: World, child: Entity, ghost: Entity, scenario: Scenario) -> None:
    child.memes["fear"] += 1
    world.say(f"Then {ghost.id} drifted out of the dark, all pale and soft like mist on glass.")
    world.say(f"{child.id} froze at first, because a ghost in the house sounded spooky.")
    ghost.memes["wonder"] += 1
    world.say(f"But {ghost.id} did not howl or boo. {ghost.id} pointed at the hearth and made a tiny worried face.")


def _fix(world: World, child: Entity, ghost: Entity, tool: Tool, hearth: Entity, scenario: Scenario) -> None:
    world.say(f"{ghost.id} found {tool.phrase} behind the hearth and nudged it to {child.id}.")
    world.say(f"Together they {tool.tail}.")
    if tool.id == "bellows":
        hearth.meters["glow"] += 2
        hearth.meters["warmth"] += 2
        world.say("An ember blinked awake, and the fire grew round and bright again.")
    if tool.id == "blanket":
        child.meters["warmth"] += 2
        world.say("The blanket trapped the cold outside the child's shoulders.")
    child.memes["fear"] = 0.0
    child.memes["comfort"] += 2
    child.memes["wonder"] += 1
    ghost.memes["comfort"] += 1
    world.say(f"That was the twist: the ghost was not there to frighten anyone; {ghost.id} had come to help.")


def tell(setting: Setting, scenario: Scenario, child_name: str, gender: str, ghost_name: str, trait: str) -> World:
    world = World(setting)
    child = world.add(Entity(id=child_name, kind="character", type=gender))
    ghost = world.add(Entity(id=ghost_name, kind="character", type="ghost"))
    hearth = world.add(Entity(id="hearth", type="hearth", label="hearth"))
    tool = world.add(Entity(id="tool", type="tool", label="tool"))

    world.facts.update(child=child, ghost=ghost, hearth=hearth, scenario=scenario, tool=tool)

    world.say(f"{child.id} was a {trait} {gender} who liked sitting near the hearth.")
    world.say(f"{child.id} loved the little glow because it made the room feel safe.")
    world.para()
    _setup(world, child, ghost, hearth, scenario)
    world.para()
    _twist(world, child, ghost, scenario)
    chosen = select_tool(scenario)
    if chosen is None:
        raise StoryError("No reasonable fix exists for this ghost story.")
    world.facts["chosen_tool"] = chosen
    _fix(world, child, ghost, chosen, hearth, scenario)
    world.say(f"In the end, {scenario.ending}.")
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    sc = f["scenario"]
    return [
        f'Write a gentle ghost story for a young child named {child.id} with a {sc.keyword} by the hearth.',
        f"Tell a short story where a ghost seems spooky at first, but the twist is that {f['ghost'].id} helps fix the hearth.",
        f"Write a cozy story about the hearth, a small ghost, and a surprising kind ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    ghost = f["ghost"]
    sc = f["scenario"]
    tool = f["chosen_tool"]
    return [
        QAItem(
            question=f"Where was {child.id} sitting when the ghost story began?",
            answer=f"{child.id} was sitting close to the hearth in {world.setting.place}.",
        ),
        QAItem(
            question=f"Why did {child.id} feel scared when {ghost.id} appeared?",
            answer=f"{child.id} felt scared because a ghost drifting out of the dark sounded spooky at first.",
        ),
        QAItem(
            question=f"What was the twist in the story?",
            answer=f"The twist was that {ghost.id} was friendly and came to help with the {sc.keyword} problem near the hearth.",
        ),
        QAItem(
            question=f"How did {ghost.id} help the room feel better?",
            answer=f"{ghost.id} helped by bringing {tool.phrase} and fixing the hearth so the room could feel warm again.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a hearth?",
            answer="A hearth is the part of a fireplace where the fire burns and where people often sit to feel warm.",
        ),
        QAItem(
            question="Why can a room feel spooky in the dark?",
            answer="A room can feel spooky in the dark because shadows hide familiar shapes and little sounds seem bigger.",
        ),
        QAItem(
            question="What does a blanket do?",
            answer="A blanket covers someone to help them stay warm and cozy.",
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
        meters = {k: round(v, 2) for k, v in e.meters.items() if v}
        memes = {k: round(v, 2) for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="cottage", scenario="hearth", name="Mina", gender="girl", ghost="Wisp", trait="curious"),
    StoryParams(place="hall", scenario="draft", name="Owen", gender="boy", ghost="Moss", trait="careful"),
]


def asp_verify() -> int:
    import asp
    clingo_set = set(asp.atoms(asp.one_model(asp_program("#show valid_story/2.")), "valid_story"))
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print("  only in clingo:", sorted(clingo_set - python_set))
    print("  only in python:", sorted(python_set - clingo_set))
    return 1


def asp_valid_combos() -> list[tuple]:
    import asp
    return sorted(set(asp.atoms(asp.one_model(asp_program("#show valid_story/2.")), "valid_story")))


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], SCENARIOS[params.scenario], params.name, params.gender, params.ghost, params.trait)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible story combos:\n")
        for place, scenario in combos:
            print(f"  {place:8} {scenario}")
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
