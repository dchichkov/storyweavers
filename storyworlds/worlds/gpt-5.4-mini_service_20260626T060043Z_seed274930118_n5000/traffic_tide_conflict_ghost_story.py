#!/usr/bin/env python3
"""
A standalone story world for a small ghost-story domain with traffic, tide, and conflict.

Premise:
A child and a ghost stand near a low road by the water. The tide is rising, the traffic is loud,
and a choice must be made before the road becomes unsafe.

The story engine models:
- physical meters: water height, road safety, signal status, noise, and carried objects
- emotional memes: fear, worry, trust, conflict, courage, and relief

The core turn:
The ghost wants to follow the tide's glow across the road, but the child worries about traffic.
A lantern and a careful pause create a compromise that resolves the conflict.

This file is self-contained apart from the shared storyworld result helpers.
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

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    carried_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "ghostgirl"}
        male = {"boy", "father", "man", "ghostboy"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class World:
    place: str
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

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
        import copy

        clone = World(self.place)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


# ---------------------------------------------------------------------------
# Story content
# ---------------------------------------------------------------------------

@dataclass
class Tide:
    label: str
    description: str
    water_rise: float
    safe_road_limit: float
    glow: str


@dataclass
class Traffic:
    label: str
    description: str
    noise: float
    danger: float
    stop_reason: str


@dataclass
class Aid:
    label: str
    phrase: str
    effect: str


@dataclass
class StoryParams:
    place: str
    tide: str
    traffic: str
    aid: str
    child_name: str
    ghost_name: str
    child_type: str
    ghost_type: str
    seed: Optional[int] = None


PLACES = {
    "harbor_road": "the harbor road",
    "breakwater": "the breakwater",
    "salt_lane": "Salt Lane",
}

TIDES = {
    "low": Tide("low tide", "The water stayed back and left shiny stones in the moonlight.", 0.5, 1.5, "a thin silver line"),
    "rising": Tide("rising tide", "The water kept climbing, slow and bright.", 1.2, 1.0, "a pale ribbon of light"),
    "high": Tide("high tide", "The water pressed close to the road and lapped at the edge.", 1.8, 0.7, "a white glow on the waves"),
}

TRAFFIC = {
    "quiet": Traffic("quiet traffic", "Only a few cars rolled by, whispering over the wet road.", 0.4, 0.3, "the road was almost empty"),
    "busy": Traffic("busy traffic", "Cars came and went in a steady stream, and their headlights flickered like eyes.", 1.0, 0.8, "the road was crowded"),
    "rush": Traffic("rush-hour traffic", "Cars hurried past in a long, noisy line, and nobody wanted to slow down.", 1.5, 1.2, "the road was too busy to cross without care"),
}

AIDS = {
    "lantern": Aid("lantern", "a small lantern", "it made the dark edge of the road easy to see"),
    "kite": Aid("kite", "a paper kite", "it gave the ghost something bright to hold while waiting"),
    "bell": Aid("bell", "a little bell", "it let the child warn the cars with a clear ring"),
}

CHILD_NAMES = ["Mira", "Noah", "Lena", "Owen", "Ivy", "Theo", "Nia", "Leo"]
GHOST_NAMES = ["Pale", "Wisp", "Moss", "Murmur", "Luna", "Shade", "Willow", "Drift"]


# ---------------------------------------------------------------------------
# State transitions
# ---------------------------------------------------------------------------

def setup_world(params: StoryParams) -> World:
    world = World(place=PLACES[params.place])
    child = world.add(Entity(
        id=params.child_name,
        kind="character",
        type=params.child_type,
        meters={"courage": 0.2},
        memes={"worry": 0.0, "trust": 0.4, "conflict": 0.0, "relief": 0.0},
    ))
    ghost = world.add(Entity(
        id=params.ghost_name,
        kind="character",
        type=params.ghost_type,
        meters={"glow": 0.8},
        memes={"wonder": 0.6, "conflict": 0.0, "loneliness": 0.3, "relief": 0.0},
    ))
    aid = world.add(Entity(
        id=params.aid,
        type="thing",
        label=AIDS[params.aid].label,
        phrase=AIDS[params.aid].phrase,
        owner=params.child_name,
        carried_by=params.child_name,
        meters={"brightness": 0.7 if params.aid == "lantern" else 0.5},
    ))
    world.facts.update(
        child=child,
        ghost=ghost,
        aid=aid,
        tide=TIDES[params.tide],
        traffic=TRAFFIC[params.traffic],
        place=params.place,
        params=params,
    )
    return world


def predict_crossing(world: World, child: Entity, tide: Tide, traffic: Traffic) -> dict:
    sim = world.copy()
    sim.get(child.id).meters["courage"] += 0.0
    danger = tide.water_rise + traffic.danger
    return {
        "safe": danger <= tide.safe_road_limit + 0.4,
        "danger": danger,
    }


def _rule_conflict(world: World) -> list[str]:
    child = next(e for e in world.characters() if e.kind == "character" and "worry" in e.memes)
    ghost = next(e for e in world.characters() if e.kind == "character" and "wonder" in e.memes)
    tide: Tide = world.facts["tide"]
    traffic: Traffic = world.facts["traffic"]

    if child.memes["worry"] < THRESHOLD or ghost.meters["glow"] < THRESHOLD:
        return []
    danger = tide.water_rise + traffic.danger
    if danger <= tide.safe_road_limit:
        return []
    sig = ("conflict", child.id, ghost.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child.memes["conflict"] += 1
    ghost.memes["conflict"] += 1
    return [
        "The child and the ghost both stopped at the curb, because the tide was close and the traffic was loud."
    ]


def _rule_relief(world: World) -> list[str]:
    child = next(e for e in world.characters() if "worry" in e.memes)
    ghost = next(e for e in world.characters() if "wonder" in e.memes)
    aid: Entity = world.facts["aid"]
    tide: Tide = world.facts["tide"]
    traffic: Traffic = world.facts["traffic"]

    if child.meters.get("courage", 0.0) < THRESHOLD:
        return []
    if child.memes["conflict"] < THRESHOLD:
        return []
    sig = ("relief", child.id, ghost.id)
    if sig in world.fired:
        return []
    danger = tide.water_rise + traffic.danger
    if aid.id == "lantern" and danger <= tide.safe_road_limit + 0.6:
        world.fired.add(sig)
        child.memes["conflict"] = 0.0
        ghost.memes["conflict"] = 0.0
        child.memes["relief"] += 1
        ghost.memes["relief"] += 1
        ghost.meters["glow"] += 0.2
        return [f"The {aid.label} made the edge of the road clear, and the two of them could wait safely."]
    return []


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in (_rule_conflict, _rule_relief):
            sents = rule(world)
            if sents:
                changed = True
                out.extend(sents)
    if narrate:
        for s in out:
            world.say(s)
    return out


def tell(params: StoryParams) -> World:
    world = setup_world(params)
    tide = world.facts["tide"]
    traffic = world.facts["traffic"]
    child = world.get(params.child_name)
    ghost = world.get(params.ghost_name)
    aid = world.get(params.aid)

    world.say(f"At {world.place}, {child.id} met {ghost.id}, a little ghost with a soft glow and a lonely little drift.")
    world.say(f"That night the {tide.label} came in, and the {traffic.label} made the road feel too awake to ignore.")
    world.say(f"{child.id} liked the way {ghost.id} listened to the tide, and {ghost.id} liked the way {child.id} held {aid.it()} carefully.")

    world.para()
    world.say(f"{ghost.id} wanted to follow the {tide.glow}, but the road was not calm enough for a crossing.")
    child.memes["worry"] += 1.0
    child.memes["trust"] += 0.2
    if predict_crossing(world, child, tide, traffic)["safe"]:
        child.meters["courage"] += 0.3
    else:
        world.say(f"{child.id} looked at the cars and frowned, because {traffic.stop_reason}.")

    propagate(world, narrate=True)

    world.para()
    child.meters["courage"] += 0.9
    if aid.id == "bell":
        world.say(f"{child.id} rang the bell once, and the sound gave the traffic a clear warning.")
        traffic_note = "The cars slowed a little."
    elif aid.id == "kite":
        world.say(f"{child.id} lifted the paper kite high, and its bright shape helped {ghost.id} wait at the curb.")
        traffic_note = "The headlights still moved fast, but the waiting felt easier."
    else:
        world.say(f"{child.id} raised the lantern, and the yellow light made a bright circle on the wet curb.")
        traffic_note = "The road edge looked steady and safe."

    world.say(traffic_note)
    if aid.id == "lantern":
        child.memes["trust"] += 0.5
        ghost.memes["wonder"] += 0.2

    propagate(world, narrate=True)

    world.para()
    if child.memes["conflict"] >= THRESHOLD:
        world.say(f"{child.id} took a breath and said they could wait for a better moment.")
    if ghost.memes["conflict"] < THRESHOLD:
        world.say(f"{ghost.id} smiled, and the tide kept shining without asking them to hurry.")
    world.say(f"In the end, the tide moved on, the traffic passed, and the little ghost stayed beside {child.id} under the lantern light.")

    world.facts["resolved"] = child.memes["conflict"] < THRESHOLD
    return world


# ---------------------------------------------------------------------------
# Registries and generation
# ---------------------------------------------------------------------------

@dataclass
class Registry:
    values: dict[str, str]


SETTINGS = {"harbor_road": PLACES, "breakwater": PLACES, "salt_lane": PLACES}

CURATED = [
    StoryParams(place="harbor_road", tide="rising", traffic="busy", aid="lantern", child_name="Mira", ghost_name="Wisp", child_type="girl", ghost_type="ghostboy"),
    StoryParams(place="breakwater", tide="high", traffic="rush", aid="bell", child_name="Theo", ghost_name="Murmur", child_type="boy", ghost_type="ghostgirl"),
    StoryParams(place="salt_lane", tide="rising", traffic="quiet", aid="kite", child_name="Ivy", ghost_name="Drift", child_type="girl", ghost_type="ghost"),
]


def valid_combos() -> list[tuple[str, str, str, str]]:
    out = []
    for place in PLACES:
        for tide_id, tide in TIDES.items():
            for traffic_id, traffic in TRAFFIC.items():
                for aid_id, aid in AIDS.items():
                    if tide.water_rise + traffic.danger > tide.safe_road_limit and aid_id == "bell":
                        out.append((place, tide_id, traffic_id, aid_id))
                    elif tide.water_rise + traffic.danger > tide.safe_road_limit and aid_id == "lantern":
                        out.append((place, tide_id, traffic_id, aid_id))
                    elif tide.water_rise + traffic.danger > tide.safe_road_limit and aid_id == "kite":
                        out.append((place, tide_id, traffic_id, aid_id))
    return out


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    params: StoryParams = f["params"]
    return [
        f'Write a ghost story for a young child that includes the words "{params.tide}" and "{params.traffic}".',
        f"Tell a gentle story where {params.child_name} meets {params.ghost_name} near {world.place} while the tide rises and the traffic feels scary.",
        f"Write a short story with a conflict at the road edge, a bright aid, and a safe ending under lantern light.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child: Entity = f["child"]
    ghost: Entity = f["ghost"]
    tide: Tide = f["tide"]
    traffic: Traffic = f["traffic"]
    aid: Entity = f["aid"]
    params: StoryParams = f["params"]

    return [
        QAItem(
            question=f"Who was the story about at {world.place}?",
            answer=f"It was about {child.id} and {ghost.id}, who met beside {world.place} while the {tide.label} came in.",
        ),
        QAItem(
            question=f"Why did {child.id} worry when {ghost.id} wanted to move near the road?",
            answer=f"{child.id} worried because the {traffic.label} made the road dangerous, and the {tide.label} was rising close to the edge.",
        ),
        QAItem(
            question=f"What helped {child.id} and {ghost.id} wait safely?",
            answer=f"{aid.phrase} helped them. It made the road edge easier to see, so they could pause instead of rushing into the traffic.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a tide?",
            answer="A tide is the regular rising and falling of the sea water near the shore.",
        ),
        QAItem(
            question="What is traffic?",
            answer="Traffic is the movement of cars and other vehicles along a road.",
        ),
        QAItem(
            question="Why can a lantern help at night?",
            answer="A lantern gives off light, so people can see better in the dark.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    lines.extend(sample.prompts)
    lines.append("")
    lines.append("== Story QA ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== World QA ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
place(harbor_road). place(breakwater). place(salt_lane).
tide(low). tide(rising). tide(high).
traffic(quiet). traffic(busy). traffic(rush).
aid(lantern). aid(kite). aid(bell).

safe_limit(low, 1.5).
safe_limit(rising, 1.0).
safe_limit(high, 0.7).

danger(quiet, 0.3).
danger(busy, 0.8).
danger(rush, 1.2).

compatible(P, T, R, A) :-
    place(P), tide(T), traffic(R), aid(A),
    safe_limit(T, L), danger(R, D),
    L < D + 1.0.

#show compatible/4.
"""


def asp_facts() -> str:
    import asp

    lines = []
    for p in PLACES:
        lines.append(asp.fact("place", p))
    for t in TIDES:
        lines.append(asp.fact("tide", t))
    for r in TRAFFIC:
        lines.append(asp.fact("traffic", r))
    for a in AIDS:
        lines.append(asp.fact("aid", a))
    for t, obj in TIDES.items():
        lines.append(asp.fact("safe_limit", t, int(obj.safe_road_limit * 10)))
    for r, obj in TRAFFIC.items():
        lines.append(asp.fact("danger", r, int(obj.danger * 10)))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show compatible/4."))
    return sorted(set(asp.atoms(model, "compatible")))


def asp_verify() -> int:
    py = set((p, t, r, a) for p, t, r, a in valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP gate matches Python reasonableness gate ({len(py)} combos).")
        return 0
    print("MISMATCH between ASP and Python gates:")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in asp:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Ghost story world: traffic, tide, and conflict.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--tide", choices=TIDES)
    ap.add_argument("--traffic", choices=TRAFFIC)
    ap.add_argument("--aid", choices=AIDS)
    ap.add_argument("--name")
    ap.add_argument("--ghost-name")
    ap.add_argument("--gender", choices=["girl", "boy", "ghost"])
    ap.add_argument("--ghost-gender", choices=["ghostgirl", "ghostboy", "ghost"])
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
    combos = valid_combos()
    if not combos:
        raise StoryError("No valid traffic-and-tide story can be built.")

    filtered = [c for c in combos
                if (args.place is None or c[0] == args.place)
                and (args.tide is None or c[1] == args.tide)
                and (args.traffic is None or c[2] == args.traffic)
                and (args.aid is None or c[3] == args.aid)]
    if not filtered:
        raise StoryError("(No valid story matches the given options.)")

    place, tide, traffic, aid = rng.choice(sorted(filtered))
    child_type = args.gender or rng.choice(["girl", "boy"])
    ghost_type = args.ghost_gender or rng.choice(["ghostgirl", "ghostboy", "ghost"])
    child_name = args.name or rng.choice(CHILD_NAMES)
    ghost_name = args.ghost_name or rng.choice(GHOST_NAMES)
    return StoryParams(
        place=place,
        tide=tide,
        traffic=traffic,
        aid=aid,
        child_name=child_name,
        ghost_name=ghost_name,
        child_type=child_type,
        ghost_type=ghost_type,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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
        print("\n--- trace ---")
        for e in sample.world.entities.values():
            meters = {k: v for k, v in e.meters.items() if v}
            memes = {k: v for k, v in e.memes.items() if v}
            bits = []
            if meters:
                bits.append(f"meters={meters}")
            if memes:
                bits.append(f"memes={memes}")
            print(f"{e.id}: {' '.join(bits)}")
    if qa:
        print()
        print(format_qa(sample))


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show compatible/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combinations:")
        for combo in combos:
            print(" ", combo)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            rng = random.Random(base_seed + i)
            i += 1
            try:
                params = resolve_params(args, rng)
            except StoryError as e:
                print(e)
                return
            params.seed = base_seed + i
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
