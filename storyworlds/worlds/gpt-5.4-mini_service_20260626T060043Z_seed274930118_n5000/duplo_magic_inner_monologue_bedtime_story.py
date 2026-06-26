#!/usr/bin/env python3
"""
storyworlds/worlds/duplo_magic_inner_monologue_bedtime_story.py
===============================================================

A small bedtime-story world about a child, a set of duplo blocks, and a little
spark of magic that can either make bedtime cozy or make a small mess of the
room. The story is driven by simulated state: the child's feelings, the toy
pieces, the glowing charm, and the quiet turn from restless play to calm
cleanup.

The world premise:
- A child wants to keep building with duplo at bedtime.
- A magical piece can help, but only in a gentle, reasonable way.
- The child thinks quietly to themself before choosing what to do.
- The ending proves what changed in the room and in the child's heart.

The inline ASP rules mirror the Python reasonableness gate:
- A magic choice is valid only if it can actually help with the duplo situation.
- The story is valid only when the bedtime turn can resolve the tension.

This script is self-contained and uses only the Python standard library at
runtime; clingo is imported lazily only for ASP modes.
"""

from __future__ import annotations

import argparse
import dataclasses
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


# ---------------------------------------------------------------------------
# Core world model
# ---------------------------------------------------------------------------

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    carried_by: Optional[str] = None
    worn_by: Optional[str] = None
    is_magic: bool = False
    helps_tidy: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    traits: list[str] = field(default_factory=list)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Room:
    place: str = "the bedroom"
    bedtime: bool = True
    cozy: bool = True


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    mess: str
    sparkle: str
    risk: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class MagicThing:
    id: str
    label: str
    phrase: str
    tidies: set[str]
    glows_for: str
    safe_with_bedtime: bool = True


class World:
    def __init__(self, room: Room) -> None:
        self.room = room
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.fired: set[tuple] = set()
        self.trace_lines: list[str] = []

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

    def copy(self) -> "World":
        clone = World(dataclasses.replace(self.room))
        clone.entities = dataclasses.asdict  # sentinel overwritten below
        import copy as _copy
        clone.entities = _copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

ACTIVITIES = {
    "build": Activity(
        id="build",
        verb="build one more tower",
        gerund="building towers",
        mess="scattered",
        sparkle="glimmer",
        risk="the blocks would stay out too late",
        keyword="duplo",
        tags={"duplo", "bedtime"},
    ),
    "stack": Activity(
        id="stack",
        verb="stack the duplo higher",
        gerund="stacking duplo blocks",
        mess="scattered",
        sparkle="shine",
        risk="the blocks would tumble across the rug",
        keyword="duplo",
        tags={"duplo", "bedtime"},
    ),
    "sleepy_castle": Activity(
        id="sleepy_castle",
        verb="make a sleepy castle",
        gerund="making sleepy castles",
        mess="scattered",
        sparkle="twinkle",
        risk="the castle would take up the whole blanket",
        keyword="duplo",
        tags={"duplo", "bedtime"},
    ),
}

MAGIC = {
    "lantern": MagicThing(
        id="lantern",
        label="a tiny moon lantern",
        phrase="a tiny moon lantern that glowed softly",
        tidies={"scattered"},
        glows_for="calm",
    ),
    "blanket_spell": MagicThing(
        id="blanket_spell",
        label="a blanket spell",
        phrase="a blanket spell that gathered the blocks into a neat nest",
        tidies={"scattered"},
        glows_for="tidy",
    ),
    "sleep_spark": MagicThing(
        id="sleep_spark",
        label="a sleep spark",
        phrase="a sleep spark that made everything feel drowsy and gentle",
        tidies={"scattered"},
        glows_for="sleep",
    ),
}

CHILDREN = {
    "Mia": ("girl", ["curious", "gentle"]),
    "Noah": ("boy", ["thoughtful", "restless"]),
    "Luna": ("girl", ["quiet", "dreamy"]),
    "Theo": ("boy", ["softhearted", "slow"]),
    "Ivy": ("girl", ["bright", "tender"]),
}

CURATED = [
    ("Mia", "build", "lantern"),
    ("Noah", "stack", "blanket_spell"),
    ("Luna", "sleepy_castle", "sleep_spark"),
]


@dataclass
class StoryParams:
    child_name: str
    activity: str
    magic: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
activity_valid(A) :- activity(A).
magic_valid(M) :- magic(M).

compatible(A,M) :- activity_valid(A), magic_valid(M),
                   needs(A, N), tidies(M, N),
                   bedtime_safe(M).

valid_story(A,M) :- compatible(A,M).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for aid, act in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        lines.append(asp.fact("needs", aid, act.mess))
        lines.append(asp.fact("sparkle", aid, act.sparkle))
    for mid, mag in MAGIC.items():
        lines.append(asp.fact("magic", mid))
        for n in sorted(mag.tidies):
            lines.append(asp.fact("tidies", mid, n))
        if mag.safe_with_bedtime:
            lines.append(asp.fact("bedtime_safe", mid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_pairs() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


# ---------------------------------------------------------------------------
# Logic helpers
# ---------------------------------------------------------------------------

def valid_pairs() -> list[tuple[str, str]]:
    pairs = []
    for aid in ACTIVITIES:
        for mid in MAGIC:
            act = ACTIVITIES[aid]
            mag = MAGIC[mid]
            if act.mess in mag.tidies and mag.safe_with_bedtime:
                pairs.append((aid, mid))
    return pairs


def reasonableness_gate(activity: Activity, magic: MagicThing) -> bool:
    return activity.mess in magic.tidies and magic.safe_with_bedtime


def explain_rejection(activity: Activity, magic: MagicThing) -> str:
    return (
        f"(No story: {magic.label} cannot reasonably solve {activity.gerund}. "
        f"The magic must tidy the same kind of bedtime mess the child makes.)"
    )


# ---------------------------------------------------------------------------
# Story simulation
# ---------------------------------------------------------------------------

def predict(world: World, child: Entity, activity: Activity, magic: MagicThing) -> dict:
    sim = world.copy()
    _do_activity(sim, sim.get(child.id), activity, narrate=False)
    _use_magic(sim, sim.get("magic"), magic, narrate=False)
    return {
        "tidy": sim.get("blocks").meters.get("tidy", 0.0) >= THRESHOLD,
        "sleepy": sim.get(child.id).memes.get("sleepy", 0.0) >= THRESHOLD,
        "calm": sim.get(child.id).memes.get("calm", 0.0) >= THRESHOLD,
    }


def _do_activity(world: World, child: Entity, activity: Activity, narrate: bool = True) -> None:
    child.meters[activity.mess] = child.meters.get(activity.mess, 0.0) + 1.0
    child.memes["want"] = child.memes.get("want", 0.0) + 1.0
    world.get("blocks").meters[activity.mess] = world.get("blocks").meters.get(activity.mess, 0.0) + 1.0
    world.facts["mess"] = activity.mess
    if narrate:
        world.say(f"{child.pronoun().capitalize()} wanted to {activity.verb} one more time.")


def _use_magic(world: World, magic_item: Entity, magic: MagicThing, narrate: bool = True) -> None:
    blocks = world.get("blocks")
    if blocks.meters.get("scattered", 0.0) >= THRESHOLD and "scattered" in magic.tidies:
        blocks.meters["tidy"] = blocks.meters.get("tidy", 0.0) + 1.0
        blocks.meters["scattered"] = max(0.0, blocks.meters.get("scattered", 0.0) - 1.0)
        if narrate:
            world.say(f"The {magic.label} gave the duplo a soft glow and helped them settle into a neat pile.")


def introduce(world: World, child: Entity) -> None:
    trait = child.traits[0] if child.traits else "gentle"
    world.say(f"{child.id} was a {trait} little child who loved quiet evenings and neat little toys.")


def bedtime_setup(world: World, child: Entity) -> None:
    world.say("At bedtime, the room was warm and still, and the lamp made a little pool of gold on the floor.")
    world.say(f"{child.id} kept a pile of duplo nearby, because building with them felt cozy in the hush of night.")


def inner_monologue(world: World, child: Entity, activity: Activity) -> None:
    world.say(
        f'Inside {child.pronoun("possessive")} own head, {child.id} thought, '
        f'"Just one more {activity.keyword} shape..."'
    )
    child.memes["inner_monologue"] = child.memes.get("inner_monologue", 0.0) + 1.0


def worry(world: World, child: Entity, activity: Activity) -> None:
    world.say(
        f"Then {child.id} noticed the blocks were getting {activity.risk}, "
        f"and the room was asking for sleep, not more noise."
    )
    child.memes["worry"] = child.memes.get("worry", 0.0) + 1.0


def choose_magic(world: World, child: Entity, magic: MagicThing) -> None:
    world.say(
        f"{child.id} looked at {magic.phrase} and wondered if it could help without waking the night."
    )


def resolve(world: World, child: Entity, activity: Activity, magic: MagicThing) -> None:
    _do_activity(world, child, activity, narrate=True)
    _use_magic(world, world.get("magic"), magic, narrate=True)
    child.memes["calm"] = child.memes.get("calm", 0.0) + 1.0
    child.memes["sleepy"] = child.memes.get("sleepy", 0.0) + 1.0
    world.say(
        f"{child.id} took one deep breath, tucked the last block into the glowing nest, "
        f"and felt {child.pronoun('possessive')} eyelids grow heavy."
    )
    world.say(
        f"At the end, the duplo were tidy, the magic was quiet, and {child.id} was ready for dreams."
    )


def tell(child_name: str, activity_id: str, magic_id: str) -> World:
    room = Room()
    world = World(room)
    child_type, traits = CHILDREN[child_name]
    child = world.add(Entity(id=child_name, kind="character", type=child_type, traits=traits))
    blocks = world.add(Entity(id="blocks", type="duplo", label="duplo blocks", phrase="a pile of duplo blocks"))
    magic_item = world.add(Entity(id="magic", type="magic", label=MAGIC[magic_id].label, phrase=MAGIC[magic_id].phrase, is_magic=True))
    world.facts.update(child=child, blocks=blocks, magic=magic_item, activity=ACTIVITIES[activity_id], magic_def=MAGIC[magic_id])

    introduce(world, child)
    bedtime_setup(world, child)
    world.para()
    inner_monologue(world, child, ACTIVITIES[activity_id])
    worry(world, child, ACTIVITIES[activity_id])
    choose_magic(world, child, MAGIC[magic_id])
    world.para()
    resolve(world, child, ACTIVITIES[activity_id], MAGIC[magic_id])
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    act = f["activity"]
    mag = f["magic_def"]
    return [
        f'Write a bedtime story for a young child named {child.id} who wants to {act.verb} and uses {mag.label} gently.',
        f'Tell a quiet story about duplo, a sleepy room, and a little magical helper that makes the child feel calm.',
        f'Write a simple bedtime story where inner monologue helps a child decide whether to keep building with duplo or settle down.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child: Entity = f["child"]
    act: Activity = f["activity"]
    mag: MagicThing = f["magic_def"]
    return [
        QAItem(
            question=f"What did {child.id} want to do at bedtime?",
            answer=f"{child.id} wanted to {act.verb}.",
        ),
        QAItem(
            question=f"What did {child.id} think quietly to themself?",
            answer=f"{child.id} thought, 'Just one more {act.keyword} shape...' before deciding what to do.",
        ),
        QAItem(
            question=f"How did {mag.label} help in the story?",
            answer=f"{mag.label} helped the duplo settle into a neat pile so the room could get ready for sleep.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended with the duplo tidy, the room quiet, and {child.id} feeling sleepy and calm.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What are duplo blocks?",
            answer="Duplo blocks are big building blocks for little hands. They click together to make towers, houses, and castles.",
        ),
        QAItem(
            question="What does bedtime mean?",
            answer="Bedtime is the time to get ready for sleep, with quiet voices, soft lights, and calm routines.",
        ),
        QAItem(
            question="Why can a magic glow feel comforting?",
            answer="A gentle glow can feel comforting because it makes a room seem safe, warm, and peaceful.",
        ),
        QAItem(
            question="What is an inner monologue?",
            answer="An inner monologue is the quiet voice inside your head that helps you think before you act.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== (3) World knowledge questions ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


# ---------------------------------------------------------------------------
# Serialization helpers
# ---------------------------------------------------------------------------

def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        parts = []
        if meters:
            parts.append(f"meters={meters}")
        if memes:
            parts.append(f"memes={memes}")
        lines.append(f"  {e.id} ({e.type}): " + (" ".join(parts) if parts else "quiet"))
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Parameter resolution and generation
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A bedtime story world about duplo, magic, and quiet inner thoughts.")
    ap.add_argument("--child", choices=sorted(CHILDREN))
    ap.add_argument("--activity", choices=sorted(ACTIVITIES))
    ap.add_argument("--magic", choices=sorted(MAGIC))
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.activity and args.magic:
        act = ACTIVITIES[args.activity]
        mag = MAGIC[args.magic]
        if not reasonableness_gate(act, mag):
            raise StoryError(explain_rejection(act, mag))

    pairs = [p for p in valid_pairs()
             if (args.activity is None or p[0] == args.activity)
             and (args.magic is None or p[1] == args.magic)]

    if not pairs:
        raise StoryError("(No valid bedtime story matches the given options.)")

    activity, magic = rng.choice(sorted(pairs))
    child = args.child or rng.choice(sorted(CHILDREN))
    return StoryParams(child_name=child, activity=activity, magic=magic)


def generate(params: StoryParams) -> StorySample:
    world = tell(params.child_name, params.activity, params.magic)
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


# ---------------------------------------------------------------------------
# ASP verification
# ---------------------------------------------------------------------------

def asp_verify() -> int:
    import asp
    py = set(valid_pairs())
    cl = set(asp_valid_pairs())
    if py == cl:
        print(f"OK: clingo gate matches valid_pairs() ({len(py)} pairs).")
        return 0
    print("MISMATCH between clingo and valid_pairs():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


def asp_show_program() -> str:
    return asp_program("#show valid_story/2.")


# ---------------------------------------------------------------------------
# CLI main
# ---------------------------------------------------------------------------

def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_show_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid_story/2."))
        pairs = sorted(set(asp.atoms(model, "valid_story")))
        print(f"{len(pairs)} compatible bedtime pairs:\n")
        for a, m in pairs:
            print(f"  {a:14} {m}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    curated = [StoryParams(child_name=c, activity=a, magic=m) for c, a, m in CURATED]
    if args.all:
        samples = [generate(p) for p in curated]
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
            header = f"### {p.child_name}: {p.activity} + {p.magic}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
