#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/electrocute_conflict_rhyming_story.py
===============================================================================================================

A small rhyme-forward story world about a child who is tempted by a sparky
thing, meets a conflict, and finds a safer ending.

The seed word is "electrocute", but the story stays child-facing and avoids harm.
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
# Model
# ---------------------------------------------------------------------------
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


@dataclass
class Setting:
    place: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    keyword: str
    danger: str
    rhyme: str
    charge: str
    zone: set[str]


@dataclass
class Guard:
    id: str
    label: str
    covers: set[str]
    stops: set[str]
    prep: str
    tail: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.zone: set[str] = set()

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


THRESHOLD = 1.0


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "workshop": Setting(place="the workshop", affords={"spark", "lamp"}),
    "garage": Setting(place="the garage", affords={"spark"}),
    "porch": Setting(place="the porch", affords={"lamp"}),
}

ACTIVITIES = {
    "spark": Activity(
        id="spark",
        verb="poke the sparking wire",
        gerund="poking sparking wires",
        rush="rush to the wire",
        keyword="spark",
        danger="buzz",
        rhyme="glow",
        charge="electrocute",
        zone={"hands"},
    ),
    "lamp": Activity(
        id="lamp",
        verb="touch the lamp cord",
        gerund="tapping lamp cords",
        rush="dash to the cord",
        keyword="lamp",
        danger="tremble",
        rhyme="glow",
        charge="electrocute",
        zone={"hands"},
    ),
}

GUARDS = [
    Guard(
        id="gloves",
        label="thick rubber gloves",
        covers={"hands"},
        stops={"electrocute"},
        prep="put on the thick rubber gloves first",
        tail="carefully tried again with the gloves on",
    ),
    Guard(
        id="mitts",
        label="puffy oven mitts",
        covers={"hands"},
        stops={"electrocute"},
        prep="wear the puffy oven mitts first",
        tail="smiled and kept the mitts on",
    ),
]

CHILD_NAMES = ["Mila", "Nico", "Tia", "Pip", "Luca", "Rae"]
PARENT_NAMES = ["Mom", "Dad", "Aunt Jo", "Uncle Ben"]


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------
def prize_at_risk(activity: Activity, prize: Entity) -> bool:
    return prize.id in activity.zone


def select_guard(activity: Activity, prize: Entity) -> Optional[Guard]:
    for guard in GUARDS:
        if activity.charge in guard.stops and prize.id in guard.covers:
            return guard
    return None


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            act = ACTIVITIES[act_id]
            for prize_id in ["hands"]:
                prize = Entity(id=prize_id)
                if prize_at_risk(act, prize) and select_guard(act, prize):
                    combos.append((place, act_id, prize_id))
    return combos


def explain_rejection(activity: Activity) -> str:
    return (
        f"(No story: {activity.verb} would not lead to a safe conflict here, "
        f"because no guard in this tiny world solves the problem.)"
    )


# ---------------------------------------------------------------------------
# World building / narration
# ---------------------------------------------------------------------------
def _do_activity(world: World, child: Entity, activity: Activity, narrate: bool = True) -> None:
    world.zone = set(activity.zone)
    child.memes["want"] = child.memes.get("want", 0.0) + 1
    child.meters["spark"] = child.meters.get("spark", 0.0) + 1
    if narrate:
        world.say(f"{child.id} reached for the {activity.keyword}, bright and low.")


def introduce(world: World, child: Entity, parent: Entity, activity: Activity) -> None:
    world.say(
        f"{child.id} was a little child who liked to tinker and to know how things would show."
    )
    world.say(
        f"{child.id} loved {activity.gerund}; it made a tiny {activity.rhyme} in the air."
    )
    world.say(
        f"One day {child.id} and {parent.id} went into {world.setting.place}, neat and slow."
    )


def wants(world: World, child: Entity, activity: Activity) -> None:
    child.memes["desire"] = child.memes.get("desire", 0.0) + 1
    world.say(f"{child.id} wanted to {activity.verb}, though the wire gave a tricky glow.")


def warn(world: World, parent: Entity, child: Entity, activity: Activity) -> None:
    child.memes["fear"] = child.memes.get("fear", 0.0) + 1
    world.say(
        f'"No, no," said {parent.id}. "That spark could {activity.charge}, so please don\'t go."'
    )
    world.say(f"The warning felt stern, and {child.id} frowned at the no-nay show.")


def conflict(world: World, child: Entity, activity: Activity) -> None:
    child.memes["conflict"] = child.memes.get("conflict", 0.0) + 1
    world.say(f"{child.id} tried to {activity.rush}, with a pout and a row.")
    world.say(f"Then {child.id} crossed {child.pronoun('possessive')} arms and let out a little " f"grumble-snow.")


def offer_guard(world: World, parent: Entity, child: Entity, activity: Activity) -> Optional[Guard]:
    guard = select_guard(activity, Entity(id="hands"))
    if guard is None:
        return None
    world.say(
        f'Then {parent.id} said, "We can keep the fun, but first {guard.prep}."'
    )
    return guard


def accept(world: World, child: Entity, parent: Entity, activity: Activity, guard: Guard) -> None:
    child.memes["conflict"] = 0.0
    child.memes["joy"] = child.memes.get("joy", 0.0) + 1
    world.say(f"{child.id}'s face grew bright, like sunrise after snow.")
    world.say(
        f"{child.id} nodded, wore {guard.label}, and {guard.tail}; the danger was set to zero."
    )
    world.say(
        f"So {child.id} could still love the {activity.keyword}, but safely now below."
    )


def tell(setting: Setting, activity: Activity, hero_name: str, parent_name: str) -> World:
    world = World(setting)
    child = world.add(Entity(id=hero_name, kind="character", type="child"))
    parent = world.add(Entity(id=parent_name, kind="character", type="parent"))

    introduce(world, child, parent, activity)
    world.para()
    wants(world, child, activity)
    warn(world, parent, child, activity)
    conflict(world, child, activity)
    guard = offer_guard(world, parent, child, activity)
    if guard:
        world.para()
        accept(world, child, parent, activity, guard)

    world.facts.update(
        child=child,
        parent=parent,
        activity=activity,
        setting=setting,
        guard=guard,
        resolved=guard is not None,
    )
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    parent = f["parent"]
    activity = f["activity"]
    return [
        f'Write a short rhyming story for a young child about "{activity.keyword}" and a gentle conflict.',
        f"Tell a child-facing story where {child.id} wants to {activity.verb} but {parent.id} says no.",
        f"Write a small rhyming tale that includes the word \"electrocute\" in a safe warning.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    parent = f["parent"]
    activity = f["activity"]
    guard = f["guard"]
    qa = [
        QAItem(
            question=f"What did {child.id} want to do in {world.setting.place}?",
            answer=f"{child.id} wanted to {activity.verb} because the spark looked bright and neat.",
        ),
        QAItem(
            question=f"Why did {parent.id} say no at first?",
            answer=(
                f"{parent.id} said no because the wire could {activity.charge}, and that would not be safe."
            ),
        ),
        QAItem(
            question=f"What helped the conflict turn into a safer ending?",
            answer=(
                f"{guard.label} helped because they covered the hands and let {child.id} try again safely."
            ),
        ),
    ]
    if f.get("resolved"):
        qa.append(
            QAItem(
                question=f"How did the story end for {child.id}?",
                answer=f"{child.id} ended happy, with the safer guard on and the spark problem solved.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a spark?",
            answer="A spark is a tiny burst of light or energy that can flash quickly.",
        ),
        QAItem(
            question="What does electrocute mean?",
            answer=(
                "Electrocute means to get badly hurt by electricity, which is why people warn children away from live wires."
            ),
        ),
        QAItem(
            question="Why do gloves help near wires?",
            answer="Thick gloves can help keep hands safer by adding a protective layer.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== Story Q&A ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== World Q&A ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
at_risk(A,P) :- splashes(A,R), worn_on(P,R).
fix(A,P) :- at_risk(A,P), guard(G), covers(G,R), worn_on(P,R), stops(G,M), charge_of(A,M).
valid(Place,A) :- affords(Place,A), at_risk(A,hands), fix(A,hands).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    for pid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        for act in sorted(setting.affords):
            lines.append(asp.fact("affords", pid, act))
    for aid, act in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        lines.append(asp.fact("charge_of", aid, act.charge))
        for r in sorted(act.zone):
            lines.append(asp.fact("splashes", aid, r))
    lines.append(asp.fact("worn_on", "hands", "hands"))
    for guard in GUARDS:
        lines.append(asp.fact("guard", guard.id))
        for c in sorted(guard.covers):
            lines.append(asp.fact("covers", guard.id, c))
        for s in sorted(guard.stops):
            lines.append(asp.fact("stops", guard.id, s))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid/2."))
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


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    activity: str
    name: str
    parent: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Rhyming story world: a conflict near a spark.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
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
    if args.activity is not None and args.place is not None:
        if args.activity not in SETTINGS[args.place].affords:
            raise StoryError("That place does not support that activity.")
    places = [args.place] if args.place else list(SETTINGS)
    place = rng.choice(places)
    acts = [a for a in SETTINGS[place].affords if args.activity is None or a == args.activity]
    if not acts:
        raise StoryError("No valid combination matches the given options.")
    activity = rng.choice(sorted(acts))
    name = args.name or rng.choice(CHILD_NAMES)
    parent = args.parent or rng.choice(PARENT_NAMES)
    return StoryParams(place=place, activity=activity, name=name, parent=parent)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], ACTIVITIES[params.activity], params.name, params.parent)
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
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        parts = []
        if meters:
            parts.append(f"meters={meters}")
        if memes:
            parts.append(f"memes={memes}")
        lines.append(f"  {e.id:8} ({e.kind:8}) {' '.join(parts)}")
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
    StoryParams(place="workshop", activity="spark", name="Mila", parent="Mom"),
    StoryParams(place="garage", activity="spark", name="Nico", parent="Dad"),
    StoryParams(place="porch", activity="lamp", name="Tia", parent="Aunt Jo"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import storyworlds.asp as asp
        print(asp_program("#show valid/2."))
        print("Models:", asp_valid_combos())
        return

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        base_seed = args.seed if args.seed is not None else random.randrange(2**31)
        samples = []
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            try:
                params = resolve_params(args, random.Random(base_seed + i))
            except StoryError as err:
                print(err)
                return
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story in seen:
                i += 1
                continue
            seen.add(sample.story)
            samples.append(sample)
            i += 1

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
