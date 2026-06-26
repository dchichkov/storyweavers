#!/usr/bin/env python3
"""
storyworlds/worlds/retro_auto_expression_transformation_adventure.py
====================================================================

A standalone story world for a small Adventure-style tale about a retro auto,
a changing expression, and a transformation that turns worry into courage.

Seed premise:
---
A child finds an old retro auto with a sleepy face in a dusty shed. The car
wants to go on an adventure, but it cannot move until someone helps it change:
the battery is flat, the tires are soft, and its grumpy expression scares the
child at first. With a little fixing, polishing, and a brave new smile, the
auto transforms from stuck and sad into ready for the road.

World model:
---
- Entities have physical meters and emotional memes.
- The story turns on a real transformation: a dormant object becomes active.
- A helper must choose the right parts and method before the adventure can start.
- Invalid settings, such as asking for a transformation without enough parts,
  raise StoryError with a clear reason.

This script follows the Storyworld contract:
- build_parser, resolve_params, generate, emit, main
- eager import of results.py containers
- lazy import of asp.py in ASP helpers
- inline ASP_RULES twin plus a Python reasonableness gate
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
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the old garage"
    indoors: bool = True
    affords: set[str] = field(default_factory=set)


@dataclass
class Action:
    id: str
    verb: str
    gerund: str
    rush: str
    mess: str
    soil: str
    needs: set[str]
    keyword: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    label: str
    phrase: str
    type: str
    role: str = "vehicle"
    plural: bool = False
    genders: set[str] = field(default_factory=lambda: {"girl", "boy"})


@dataclass
class Tool:
    id: str
    label: str
    helps: set[str]
    fix: set[str]
    prep: str
    tail: str
    plural: bool = False


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

    def copy(self) -> "World":
        import copy
        c = World(self.setting)
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        return c

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]


def _need_signature(action: Action, prize: Prize) -> bool:
    return prize.role in action.needs


def _select_tool(action: Action, prize: Prize) -> Optional[Tool]:
    for t in TOOLS:
        if action.id in t.fix and prize.role in t.helps:
            return t
    return None


def _do_action(world: World, actor: Entity, action: Action, narrate: bool = True) -> None:
    actor.meters[action.mess] = actor.meters.get(action.mess, 0.0) + 1
    actor.memes["energy"] = actor.memes.get("energy", 0.0) + 1
    if narrate:
        world.say(f"{actor.id} {action.gerund}.")
    if action.id == "restore":
        actor.meters["broken"] = max(0.0, actor.meters.get("broken", 0.0) - 1)
        actor.meters["ready"] = actor.meters.get("ready", 0.0) + 1


def predict(world: World, actor: Entity, action: Action, prize_id: str) -> dict:
    sim = world.copy()
    _do_action(sim, sim.get(actor.id), action, narrate=False)
    prize = sim.entities[prize_id]
    return {
        "ready": prize.meters.get("ready", 0.0) >= THRESHOLD,
        "broken": prize.meters.get("broken", 0.0) > 0.0,
    }


def intro(world: World, child: Entity, prize: Entity) -> None:
    trait = next((t for t in child.traits if t != "little"), "curious")
    world.say(
        f"{child.id} was a little {trait} {child.type} who loved old places and "
        f"things with stories in their wheels."
    )
    world.say(
        f"In the old garage, {child.id} found {prize.phrase}, waiting under a soft coat of dust."
    )


def describe_prize(world: World, child: Entity, prize: Entity) -> None:
    prize.memes["sleepy"] = prize.memes.get("sleepy", 0.0) + 1
    world.say(
        f"{prize.id} had a sleepy little face and a retro shine, like it remembered "
        f"many roads but had forgotten how to smile."
    )
    world.say(
        f"{child.id} liked {prize.it()} right away, even if {prize.pronoun('subject')} looked a bit grumpy."
    )


def worry(world: World, child: Entity, parent: Entity, prize: Entity, action: Action) -> None:
    child.memes["wonder"] = child.memes.get("wonder", 0.0) + 1
    world.say(
        f"{child.id} wanted to take {prize.pronoun('object')} on an adventure, but "
        f"{parent.id} pointed at the flat tire and the dead battery."
    )
    world.say(
        f'"Not yet," {parent.pronoun("subject")} said. "If we try to {action.verb} now, '
        f"{prize.pronoun('subject')} will stay stuck here.""
    )


def grimace(world: World, prize: Entity) -> None:
    prize.memes["grim"] = prize.memes.get("grim", 0.0) + 1
    world.say(
        f"The retro auto's expression stayed stiff and sour, like it was afraid of the road."
    )


def choose_tool(world: World, parent: Entity, prize: Entity, action: Action) -> Optional[Tool]:
    tool = _select_tool(action, prize)
    if tool is None:
        return None
    world.say(
        f"{parent.id} smiled and said, '{tool.prep}.'"
    )
    return tool


def accept_tool(world: World, child: Entity, parent: Entity, prize: Entity, action: Action, tool: Tool) -> None:
    child.memes["hope"] = child.memes.get("hope", 0.0) + 1
    world.say(
        f"{child.id}'s eyes brightened. Together they {tool.tail}, and the old auto began to change."
    )
    world.say(
        f"The battery hummed, the tires grew firm, and {prize.id}'s face softened into a brave new smile."
    )
    world.say(
        f"Soon {prize.id} was {action.gerund}, ready for the lane beyond the garage door."
    )


def tell(setting: Setting, action: Action, prize_cfg: Prize,
         child_name: str = "Nina", child_type: str = "girl",
         parent_type: str = "mother", trait: str = "curious") -> World:
    world = World(setting)
    child = world.add(Entity(id=child_name, kind="character", type=child_type, traits=["little", trait, "brave"]))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type))
    prize = world.add(Entity(
        id="auto", type=prize_cfg.type, label=prize_cfg.label, phrase=prize_cfg.phrase,
        owner=child.id, caretaker=parent.id
    ))
    prize.meters["broken"] = 1.0
    prize.meters["ready"] = 0.0

    intro(world, child, prize)
    describe_prize(world, child, prize)

    world.para()
    worry(world, child, parent, prize, action)
    grimace(world, prize)

    world.para()
    tool = choose_tool(world, parent, prize, action)
    if tool:
        child.memes["joy"] = child.memes.get("joy", 0.0) + 1
        child.memes["trust"] = child.memes.get("trust", 0.0) + 1
        prize.worn_by = child.id
        accept_tool(world, child, parent, prize, action, tool)
        _do_action(world, prize, action, narrate=False)
        world.say(
            f"They rolled out into the morning light, and the auto's retro expression became an eager grin."
        )

    world.facts.update(
        child=child, parent=parent, prize=prize, action=action, tool=tool,
        resolved=tool is not None
    )
    return world


SETTINGS = {
    "garage": Setting(place="the old garage", indoors=True, affords={"restore", "polish", "drive"}),
    "shed": Setting(place="the dusty shed", indoors=True, affords={"restore", "polish"}),
    "roadside": Setting(place="the small roadside yard", indoors=False, affords={"drive", "polish"}),
}

ACTIONS = {
    "restore": Action(
        id="restore",
        verb="restore the old auto",
        gerund="restoring the old auto",
        rush="push the car forward",
        mess="work",
        soil="still broken",
        needs={"vehicle"},
        keyword="restore",
        tags={"transformation", "retro", "auto"},
    ),
    "polish": Action(
        id="polish",
        verb="polish the retro auto",
        gerund="polishing the retro auto",
        rush="rub the shiny hood hard",
        mess="shine",
        soil="dull again",
        needs={"vehicle"},
        keyword="retro",
        tags={"expression", "retro", "auto"},
    ),
    "drive": Action(
        id="drive",
        verb="drive the auto down the lane",
        gerund="driving down the lane",
        rush="race down the lane",
        mess="motion",
        soil="too slow",
        needs={"vehicle"},
        keyword="adventure",
        tags={"adventure", "auto", "transformation"},
    ),
}

PRIZES = {
    "car": Prize(label="car", phrase="a retro little auto", type="car"),
}

TOOLS = [
    Tool(
        id="battery",
        label="a fresh battery",
        helps={"vehicle"},
        fix={"restore"},
        prep="Let's put in a fresh battery first",
        tail="lifted the hood, set in the fresh battery, and tightened the wires",
    ),
    Tool(
        id="pump",
        label="a tire pump",
        helps={"vehicle"},
        fix={"restore"},
        prep="Let's use the tire pump on the soft wheels",
        tail="pumped the tires until they stood proud and round",
    ),
    Tool(
        id="cloth",
        label="a soft cloth",
        helps={"vehicle"},
        fix={"polish"},
        prep="Let's polish the body with a soft cloth",
        tail="wiped the chrome until it gleamed like a little star",
    ),
]


GIRL_NAMES = ["Nina", "Maya", "Lila", "Tara", "Zoe"]
BOY_NAMES = ["Owen", "Finn", "Leo", "Milo", "Theo"]
TRAITS = ["curious", "brave", "cheerful", "careful"]


@dataclass
class StoryParams:
    place: str
    action: str
    prize: str
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for action_id in setting.affords:
            action = ACTIONS[action_id]
            for prize_id, prize in PRIZES.items():
                if _need_signature(action, prize):
                    combos.append((place, action_id, prize_id))
    return combos


def explain_rejection(action: Action, prize: Prize) -> str:
    return (
        f"(No story: {action.gerund} needs a vehicle-like prize, but nothing here fits the transformation "
        f"reasonably. The auto must be a real subject of change, not just a decorative object.)"
    )


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Adventure story world about a retro auto, an expression, and transformation."
    )
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--action", choices=ACTIONS)
    ap.add_argument("--prize", choices=PRIZES)
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
    if args.action and args.prize:
        action = ACTIONS[args.action]
        prize = PRIZES[args.prize]
        if not _need_signature(action, prize):
            raise StoryError(explain_rejection(action, prize))
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.action is None or c[1] == args.action)
              and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, action_id, prize_id = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, action=action_id, prize=prize_id, name=name, gender=gender, parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], ACTIONS[params.action], PRIZES[params.prize],
                 params.name, params.gender, params.parent, params.trait)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    act = f["action"]
    prize = f["prize"]
    return [
        f"Write a gentle adventure story about a retro auto that needs a transformation before it can go out.",
        f"Tell a child-friendly story where {f['child'].id} helps a sleepy car become ready to {act.verb}.",
        f"Write a story with a dusty garage, a grumpy expression, and a happy transformation into motion.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child, parent, prize, action = f["child"], f["parent"], f["prize"], f["action"]
    tool = f["tool"]
    qa = [
        QAItem(
            question=f"What did {child.id} find in the garage?",
            answer=f"{child.id} found {prize.phrase} in the garage. It looked retro, sleepy, and a little grumpy at first.",
        ),
        QAItem(
            question=f"Why did {parent.id} say not to go yet?",
            answer=f"{parent.id} said not to go yet because the auto was still broken, with a flat battery and soft tires. It needed a real fix before it could {action.verb}.",
        ),
    ]
    if f.get("resolved"):
        qa.append(QAItem(
            question=f"What helped the auto change so it could go on the adventure?",
            answer=f"They used {tool.label} and other careful fixing steps, and the old auto transformed from stuck and sad into ready to {action.verb}.",
        ))
        qa.append(QAItem(
            question=f"How did the auto's expression change at the end?",
            answer=f"Its expression changed from a stiff, sour look into a brave new smile. That showed the transformation was complete.",
        ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["action"].tags)
    out = []
    if "retro" in tags:
        out.append(QAItem(
            question="What does retro mean?",
            answer="Retro means old-fashioned in a way that reminds people of another time.",
        ))
    if "transformation" in tags:
        out.append(QAItem(
            question="What is a transformation?",
            answer="A transformation is a big change, when something becomes different from how it was before.",
        ))
    if "auto" in tags:
        out.append(QAItem(
            question="What is an auto?",
            answer="An auto is another word for a car or vehicle that can carry people on roads.",
        ))
    if "expression" in tags:
        out.append(QAItem(
            question="What is an expression on a face?",
            answer="An expression is the look on a face that shows a feeling like happy, sad, or worried.",
        ))
    return out


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
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
prize_at_risk(A, P) :- action(A), prize(P), needs(A, vehicle), worn(P, vehicle).
has_tool(A, P) :- tool(T), fixes(T, A), helps(T, vehicle), prize_at_risk(A, P).
valid_story(S, A, P) :- setting(S), affords(S, A), prize_at_risk(A, P), has_tool(A, P).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for aid, a in ACTIONS.items():
        lines.append(asp.fact("action", aid))
        lines.append(asp.fact("needs", aid, "vehicle"))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("worn", pid, "vehicle"))
    for t in TOOLS:
        lines.append(asp.fact("tool", t.id))
        for x in sorted(t.fix):
            lines.append(asp.fact("fixes", t.id, x))
        for x in sorted(t.helps):
            lines.append(asp.fact("helps", t.id, x))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    if py - cl:
        print("  only in python:", sorted(py - cl))
    return 1


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
    StoryParams(place="garage", action="restore", prize="car", name="Nina", gender="girl", parent="mother", trait="brave"),
    StoryParams(place="garage", action="polish", prize="car", name="Owen", gender="boy", parent="father", trait="curious"),
    StoryParams(place="shed", action="restore", prize="car", name="Maya", gender="girl", parent="mother", trait="careful"),
    StoryParams(place="roadside", action="drive", prize="car", name="Leo", gender="boy", parent="father", trait="cheerful"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        triples = asp_valid_combos()
        print(f"{len(triples)} compatible (setting, action, prize) combos:\n")
        for t in triples:
            print("  ", t)
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.action} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
