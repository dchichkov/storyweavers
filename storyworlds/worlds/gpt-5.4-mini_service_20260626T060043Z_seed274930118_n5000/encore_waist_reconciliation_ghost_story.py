#!/usr/bin/env python3
"""
storyworlds/worlds/encore_waist_reconciliation_ghost_story.py
==============================================================

A small story world about a shy ghost, a torn costume sash at the waist, and
an encore that only becomes possible after reconciliation.

Premise:
- A child performer meets a ghost in an old theater.
- The ghost loves one last encore but feels ashamed of a frayed sash tied at
  the waist.
- A disagreement arises when the stage manager wants to hide the ghost away.
- Reconciliation comes through listening, a careful repair, and a final encore
  that proves the ghost can be seen without fear.

This script is standalone and uses only the stdlib unless --asp or --verify is
requested, in which case it lazily imports the shared clingo helpers.
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
    region: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Action:
    id: str
    verb: str
    gerund: str
    risk: str
    zone: set[str]
    keyword: str


@dataclass
class Prize:
    label: str
    phrase: str
    region: str


@dataclass
class Gear:
    id: str
    label: str
    covers: set[str]
    repair: str
    helps: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.zone: set[str] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()

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
        clone.zone = set(self.zone)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        return clone

    def worn_items(self, actor: Entity) -> list[Entity]:
        return [e for e in self.entities.values() if e.worn_by == actor.id]


def _r_shame(world: World) -> list[str]:
    out: list[str] = []
    for e in world.entities.values():
        if e.kind != "character":
            continue
        if e.memes.get("shame", 0.0) < THRESHOLD:
            continue
        if ("shame", e.id) in world.fired:
            continue
        world.fired.add(("shame", e.id))
        out.append(f"{e.id} looked smaller in the dim light.")
    return out


def _r_fray(world: World) -> list[str]:
    out: list[str] = []
    ghost = world.entities.get("Ghost")
    sash = world.entities.get("sash")
    if not ghost or not sash:
        return out
    if ghost.meters.get("tug", 0.0) < THRESHOLD:
        return out
    if ("fray", "sash") in world.fired:
        return out
    world.fired.add(("fray", "sash"))
    sash.meters["frayed"] = sash.meters.get("frayed", 0.0) + 1
    out.append("The sash at the ghost's waist split a little more.")
    return out


def _r_reconcile(world: World) -> list[str]:
    out: list[str] = []
    ghost = world.entities.get("Ghost")
    child = world.entities.get("Child")
    manager = world.entities.get("Manager")
    if not ghost or not child or not manager:
        return out
    if ghost.memes.get("heard", 0.0) < THRESHOLD or child.memes.get("kindness", 0.0) < THRESHOLD:
        return out
    if ("reconcile", ghost.id) in world.fired:
        return out
    world.fired.add(("reconcile", ghost.id))
    ghost.memes["fear"] = 0.0
    ghost.memes["peace"] = ghost.memes.get("peace", 0.0) + 1
    manager.memes["softness"] = manager.memes.get("softness", 0.0) + 1
    out.append("The room grew gentler, and the old worry loosened.")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in (_r_shame, _r_fray, _r_reconcile):
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def predict(world: World, actor: Entity, action: Action) -> dict:
    sim = world.copy()
    do_action(sim, sim.get(actor.id), action, narrate=False)
    return {
        "risk": bool(sim.entities["sash"].meters.get("frayed", 0.0) >= THRESHOLD),
        "peace": sim.entities["Ghost"].memes.get("peace", 0.0),
    }


def do_action(world: World, actor: Entity, action: Action, narrate: bool = True) -> None:
    if action.id not in world.setting.affords:
        return
    world.zone = set(action.zone)
    actor.meters[action.keyword] = actor.meters.get(action.keyword, 0.0) + 1
    actor.memes["joy"] = actor.memes.get("joy", 0.0) + 1
    propagate(world, narrate=narrate)


def build_scene(world: World) -> None:
    child = world.add(Entity(id="Child", kind="character", type="girl"))
    ghost = world.add(Entity(id="Ghost", kind="character", type="ghost"))
    manager = world.add(Entity(id="Manager", kind="character", type="woman", label="stage manager"))
    sash = world.add(Entity(id="sash", type="sash", label="silver sash", phrase="a silver sash", owner="Ghost", region="waist"))
    sash.worn_by = "Ghost"

    child.memes["curiosity"] = 1
    child.memes["kindness"] = 1
    ghost.memes["shame"] = 1
    ghost.memes["fear"] = 1
    ghost.memes["heard"] = 0
    manager.memes["worry"] = 1

    world.say("In the old theater, a little girl heard a soft rustle behind the curtain.")
    world.say("A pale ghost stood there, wearing a silver sash tied at the waist.")
    world.say("The ghost loved one more encore, but the torn sash made the night feel heavy.")
    world.para()
    world.say("The child did not run away. She stepped closer and smiled at the shy ghost.")
    world.say("The stage manager frowned and whispered that ghosts should stay hidden.")
    world.say("But the child listened, and the ghost listened too.")
    ghost.memes["heard"] = 1
    ghost.memes["tension"] = 1
    manager.memes["tension"] = 1
    world.para()
    world.say("Together, they mended the sash and agreed the ghost could stay for the final song.")
    ghost.memes["peace"] = 1
    manager.memes["softness"] = 1
    world.say("When the curtain rose again, the ghost bowed for an encore with a brave, bright heart.")
    world.say("The silver sash stayed snug at the waist, and the theater was full of gentle applause.")

    world.facts.update(
        child=child,
        ghost=ghost,
        manager=manager,
        sash=sash,
        setting=world.setting,
    )


SETTINGS = {
    "the old theater": Setting(place="the old theater", affords={"encore", "repair"}),
}

ACTIONS = {
    "encore": Action(
        id="encore",
        verb="sing an encore",
        gerund="singing an encore",
        risk="fray the sash at the waist",
        zone={"waist"},
        keyword="song",
    ),
    "repair": Action(
        id="repair",
        verb="mend the sash",
        gerund="mending the sash",
        risk="nothing",
        zone=set(),
        keyword="care",
    ),
}

PRIZES = {
    "sash": Prize(
        label="sash",
        phrase="a silver sash",
        region="waist",
    ),
}

GEAR = [
    Gear(
        id="needle",
        label="a needle and thread",
        covers={"waist"},
        repair="mended",
        helps="stitch the sash before the encore",
    )
]

NAMES = ["Mira", "Lena", "Ivy", "June", "Nora"]


@dataclass
class StoryParams:
    place: str
    action: str
    prize: str
    name: str = "Mira"
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A ghost story about an encore and reconciliation.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--action", choices=ACTIONS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--name")
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            for prize_id in PRIZES:
                if act_id == "encore" and prize_id == "sash":
                    combos.append((place, act_id, prize_id))
    return combos


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.action is None or c[1] == args.action)
              and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, action, prize = rng.choice(combos)
    return StoryParams(place=place, action=action, prize=prize, name=args.name or rng.choice(NAMES))


def tell(params: StoryParams) -> World:
    world = World(SETTINGS[params.place])
    build_scene(world)
    return world


def generation_prompts(world: World) -> list[str]:
    return [
        'Write a short ghost story for a young child that includes the word "encore".',
        'Tell a gentle story about a ghost at the waist of a silver sash who needs reconciliation.',
        'Write a spooky-but-kind theater story where an encore ends in reconciliation.',
    ]


def story_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="Why did the ghost feel shy before the encore?",
            answer="The ghost felt shy because the silver sash at the waist was torn, and the room felt like it might stare.",
        ),
        QAItem(
            question="How did the child help the ghost?",
            answer="The child listened kindly, stayed close, and helped mend the sash so the ghost could return for the encore.",
        ),
        QAItem(
            question="What changed at the end of the story?",
            answer="By the end, the ghost felt peaceful, the stage manager softened, and the encore could happen without fear.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is an encore?",
            answer="An encore is an extra performance that happens after the first song or scene is already over.",
        ),
        QAItem(
            question="What is a waist?",
            answer="The waist is the middle part of the body, usually above the hips and below the ribs.",
        ),
        QAItem(
            question="What does reconciliation mean?",
            answer="Reconciliation means making peace after a disagreement so people can understand one another again.",
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
        if e.region:
            bits.append(f"region={e.region}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
prize_at_risk(A, P) :- action(A), prize(P), splashes(A, R), worn_on(P, R).
repair_possible(P) :- prize(P), worn_on(P, waist), tool(needle).
reconciliation(A) :- action(A), has_gentleness, repair_possible(sash).
valid_story(Place, A, P) :- setting(Place), affords(Place, A), prize_at_risk(A, P), reconciliation(A).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", pid, a))
    for aid, a in ACTIONS.items():
        lines.append(asp.fact("action", aid))
        for r in sorted(a.zone):
            lines.append(asp.fact("splashes", aid, r))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("worn_on", pid, p.region))
    lines.append(asp.fact("tool", "needle"))
    lines.append(asp.fact("has_gentleness"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    import asp
    py = set(valid_combos())
    cl = set(asp_valid())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        print(asp_program("#show valid_story/3."))
        model = asp.one_model(asp_program("#show valid_story/3."))
        print(sorted(set(asp.atoms(model, "valid_story"))))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(StoryParams(place=p, action=a, prize=pr, name="Mira"))
                   for p, a, pr in valid_combos()]
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
        if len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
