#!/usr/bin/env python3
"""
A standalone story world for a small Space Adventure tale about physics and
reconciliation.

Premise:
- A curious child crew member wants to use a physics gadget on a tiny ship.
- The gadget causes a drifting problem.
- A partner gets upset, then the two reconcile by using careful physics and
  sharing the fix.

The world is intentionally small, deterministic when pinned, and constraint-checked.
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
# Tiny physical/emotional model
# ---------------------------------------------------------------------------

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
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {}
        if not self.memes:
            self.memes = {}

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "captain"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Ship:
    name: str
    place: str
    gravity: float = 0.0
    drift: float = 0.0
    route: str = "steady"
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    fired: set[str] = field(default_factory=set)

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

    def copy(self) -> "Ship":
        clone = Ship(self.name, self.place, self.gravity, self.drift, self.route)
        clone.entities = json.loads(json.dumps({k: {
            "id": v.id, "kind": v.kind, "type": v.type, "label": v.label,
            "phrase": v.phrase, "owner": v.owner, "caretaker": v.caretaker,
            "worn_by": v.worn_by, "meters": v.meters, "memes": v.memes
        } for k, v in self.entities.items()}))
        restored = {}
        for k, v in clone.entities.items():
            restored[k] = Entity(**v)
        clone.entities = restored
        clone.fired = set(self.fired)
        clone.facts = dict(self.facts)
        clone.paragraphs = [[]]
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

@dataclass
class Place:
    id: str
    label: str
    detail: str
    gravity: float
    afford: set[str] = field(default_factory=set)


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    mishap: str
    consequence: str
    physics: str
    force: float
    drift: float
    tag: str


@dataclass
class ReconciliationTool:
    id: str
    label: str
    method: str
    fix: str
    stabilizes: float


SETTINGS = {
    "orbital_station": Place(
        id="orbital_station",
        label="the orbital station",
        detail="The station hummed softly, and stars blinked outside the round window.",
        gravity=0.2,
        afford={"magnet_lab", "balancing_game", "bubble_walk"},
    ),
    "lunar_hangar": Place(
        id="lunar_hangar",
        label="the lunar hangar",
        detail="Dusty moonlight lay on the floor, and the big launch doors shone silver.",
        gravity=0.16,
        afford={"magnet_lab", "balancing_game"},
    ),
    "small_ship": Place(
        id="small_ship",
        label="the little ship",
        detail="The little ship was cozy, with a control panel that glowed blue and green.",
        gravity=0.9,
        afford={"magnet_lab", "balancing_game", "bubble_walk"},
    ),
}

ACTIVITIES = {
    "magnet_lab": Activity(
        id="magnet_lab",
        verb="play with the magnet lab",
        gerund="testing magnets",
        mishap="the tools pulled together too hard",
        consequence="the loose parts skittered across the floor",
        physics="magnets can pull metal without touching it",
        force=1.2,
        drift=0.7,
        tag="physics",
    ),
    "balancing_game": Activity(
        id="balancing_game",
        verb="try the balancing game",
        gerund="balancing rings and blocks",
        mishap="one side tipped too fast",
        consequence="the tower wobbled and clattered down",
        physics="balance changes when weight spreads unevenly",
        force=0.8,
        drift=0.4,
        tag="physics",
    ),
    "bubble_walk": Activity(
        id="bubble_walk",
        verb="practice the bubble walk",
        gerund="floating carefully with bubbles",
        mishap="the bubble popped at the wrong time",
        consequence="the toy rolled under a console",
        physics="small pushes can move things in zeroish gravity",
        force=0.6,
        drift=0.5,
        tag="physics",
    ),
}

TOOLS = {
    "soft_gloves": ReconciliationTool(
        id="soft_gloves",
        label="soft gloves",
        method="slow the hands down",
        fix="careful hands",
        stabilizes=0.7,
    ),
    "tether_cord": ReconciliationTool(
        id="tether_cord",
        label="a tether cord",
        method="hold the two of them steady",
        fix="steady teamwork",
        stabilizes=0.9,
    ),
    "gravity_chart": ReconciliationTool(
        id="gravity_chart",
        label="a gravity chart",
        method="show where the pull was stronger",
        fix="shared understanding",
        stabilizes=0.5,
    ),
}

NAMES = ["Nova", "Milo", "Zuri", "Pip", "Luna", "Arin", "Ivy", "Kai"]
PARTNERS = ["friend", "crewmate", "sibling", "co-pilot"]
GENDERS = ["girl", "boy"]


# ---------------------------------------------------------------------------
# Parameters
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    place: str
    activity: str
    tool: str
    name: str
    gender: str
    partner: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# World logic
# ---------------------------------------------------------------------------

def _is_valid_combo(place: Place, activity: Activity, tool: ReconciliationTool) -> bool:
    if activity.id not in place.afford:
        return False
    if activity.id == "magnet_lab" and tool.id not in {"soft_gloves", "tether_cord", "gravity_chart"}:
        return False
    return True


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for pid, place in SETTINGS.items():
        for aid, act in ACTIVITIES.items():
            for tid, tool in TOOLS.items():
                if _is_valid_combo(place, act, tool):
                    out.append((pid, aid, tid))
    return out


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.activity is None or c[1] == args.activity)
              and (args.tool is None or c[2] == args.tool)]
    if not combos:
        raise StoryError("No valid story matches those choices.")

    if args.activity == "magnet_lab" and args.tool == "gravity_chart":
        # still valid, but if explicitly pinned to a mismatched story we prevent nonsense later
        pass

    place, activity, tool = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(GENDERS)
    name = args.name or rng.choice(NAMES)
    partner = args.partner or rng.choice(PARTNERS)
    return StoryParams(
        place=place,
        activity=activity,
        tool=tool,
        name=name,
        gender=gender,
        partner=partner,
    )


def build_world(params: StoryParams) -> Ship:
    place = SETTINGS[params.place]
    activity = ACTIVITIES[params.activity]
    tool = TOOLS[params.tool]

    ship = Ship(name="Comet Bell", place=place.label, gravity=place.gravity)
    ship.facts.update(place=place, activity=activity, tool=tool, params=params)

    hero = ship.add(Entity(
        id=params.name,
        kind="character",
        type=params.gender,
        label=params.name,
        meters={"joy": 0.0, "drift": 0.0},
        memes={"joy": 0.0, "curiosity": 0.0, "worry": 0.0, "hurt": 0.0, "love": 0.0, "peace": 0.0},
    ))
    partner = ship.add(Entity(
        id="partner",
        kind="character",
        type="girl" if params.gender == "boy" else "boy",
        label=params.partner,
        meters={"joy": 0.0},
        memes={"worry": 0.0, "hurt": 0.0, "love": 0.0, "peace": 0.0, "angry": 0.0},
    ))
    gadget = ship.add(Entity(
        id="gadget",
        kind="thing",
        type="tool",
        label=tool.label,
        phrase=tool.label,
        owner=hero.id,
        meters={"loose": 1.0, "drift": 0.0},
    ))
    return ship


def predict_mishap(ship: Ship, params: StoryParams) -> dict[str, bool]:
    sim = ship.copy()
    act = ACTIVITIES[params.activity]
    sim.gravity += act.drift
    sim.drift += act.drift
    if act.force >= 0.6:
        sim.facts["moved"] = True
    return {
        "mishap": True,
        "needs_reconciliation": True,
    }


def apply_activity(ship: Ship, hero: Entity, partner: Entity, activity: Activity) -> None:
    hero.meters["drift"] = hero.meters.get("drift", 0.0) + activity.drift
    hero.memes["curiosity"] = hero.memes.get("curiosity", 0.0) + 1.0
    ship.gravity += activity.drift
    ship.drift += activity.drift
    if ship.drift >= THRESHOLD:
        partner.memes["worry"] = partner.memes.get("worry", 0.0) + 1.0


def cause_conflict(ship: Ship, hero: Entity, partner: Entity, activity: Activity) -> None:
    hero.memes["hurt"] = hero.memes.get("hurt", 0.0) + 1.0
    partner.memes["angry"] = partner.memes.get("angry", 0.0) + 1.0
    ship.say(f"{hero.id} wanted to {activity.verb}, but the little ship gave a sudden wobble.")
    ship.say(f"{activity.consequence.capitalize()}, and {partner.label} frowned at the mess.")

    ship.para()


def reconcile(ship: Ship, hero: Entity, partner: Entity, tool: ReconciliationTool, activity: Activity) -> None:
    hero.memes["hurt"] = 0.0
    partner.memes["angry"] = 0.0
    hero.memes["love"] = hero.memes.get("love", 0.0) + 1.0
    partner.memes["love"] = partner.memes.get("love", 0.0) + 1.0
    hero.memes["peace"] = hero.memes.get("peace", 0.0) + 1.0
    partner.memes["peace"] = partner.memes.get("peace", 0.0) + 1.0
    ship.drift = max(0.0, ship.drift - tool.stabilizes)
    ship.gravity = max(0.0, ship.gravity - tool.stabilizes / 2)

    ship.say(f"Then they used {tool.label} to {tool.method}.")
    ship.say(f"That brought {tool.fix}, and soon the two of them were smiling again.")
    ship.say(f"Together they tried to {activity.verb} in a calmer way, and the ship stayed steady.")


def tell(params: StoryParams) -> Ship:
    ship = build_world(params)
    hero = ship.get(params.name)
    partner = ship.get("partner")
    activity = ACTIVITIES[params.activity]
    tool = TOOLS[params.tool]
    place = SETTINGS[params.place]

    ship.say(f"{hero.id} loved the stars and the hum of {place.label}.")
    ship.say(f"{hero.id} was a curious little {hero.type} who knew that {activity.physics}.")
    ship.say(f"One day, {hero.id} and {partner.label} went to {place.label}.")
    ship.say(f"{hero.id} wanted to {activity.verb}, because {activity.gerund} felt exciting.")

    ship.para()
    apply_activity(ship, hero, partner, activity)
    ship.say(f"At first, everything felt fun, but then {activity.mishap}.")
    cause_conflict(ship, hero, partner, activity)

    ship.say(f"{partner.label} said they needed a smarter plan.")
    ship.say(f"{hero.id} listened, and the two of them thought about physics instead of rushing.")

    ship.para()
    reconcile(ship, hero, partner, tool, activity)

    ship.say(f"In the end, {hero.id} and {partner.label} were friends again.")
    ship.say(f"The little ship drifted less, and the stars outside looked extra bright.")
    ship.facts.update(hero=hero, partner=partner)
    return ship


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------

def generation_prompts(ship: Ship) -> list[str]:
    f = ship.facts
    p = f["params"]
    act = f["activity"]
    tool = f["tool"]
    return [
        f"Write a short space adventure story for a young child about {p.name}, {act.tag}, and reconciliation.",
        f"Tell a gentle story where {p.name} wants to {act.verb} on {ship.place} and later uses {tool.label} to make peace.",
        f"Write a tiny spaceship story that includes the word \"physics\" and ends with the crew smiling again.",
    ]


def story_qa(ship: Ship) -> list[QAItem]:
    f = ship.facts
    params: StoryParams = f["params"]
    act: Activity = f["activity"]
    tool: ReconciliationTool = f["tool"]
    hero: Entity = f["hero"]
    partner: Entity = f["partner"]

    return [
        QAItem(
            question=f"Who wanted to {act.verb} in the story?",
            answer=f"{params.name} wanted to {act.verb} while exploring {SETTINGS[params.place].label}.",
        ),
        QAItem(
            question="What problem happened after they started?",
            answer=f"{act.mishap.capitalize()}, and that made the little ship wobble and the mood turn tense.",
        ),
        QAItem(
            question="How did they reconcile?",
            answer=f"They used {tool.label} to {tool.method}, which helped them calm down and work together again.",
        ),
        QAItem(
            question="What was the ending like?",
            answer=f"At the end, {params.name} and {params.partner} were smiling, and the ship stayed steady.",
        ),
    ]


WORLD_KNOWLEDGE = {
    "physics": [
        (
            "What is physics?",
            "Physics is the study of how things move, push, pull, bounce, and balance in the world.",
        ),
        (
            "Why do things drift in space?",
            "Things drift in space because there is very little air or friction to slow them down, so they keep moving until something stops them.",
        ),
    ],
    "reconciliation": [
        (
            "What does reconciliation mean?",
            "Reconciliation means people stop being upset with each other and make peace again.",
        )
    ],
    "magnets": [
        (
            "What do magnets do?",
            "Magnets can pull on some metal objects from far away without touching them.",
        )
    ],
    "gravity": [
        (
            "What is gravity?",
            "Gravity is the pull that makes things fall down or stay on the ground instead of floating away.",
        )
    ],
}


def world_knowledge_qa(ship: Ship) -> list[QAItem]:
    out: list[QAItem] = []
    out.extend(QAItem(question=q, answer=a) for q, a in WORLD_KNOWLEDGE["physics"])
    out.extend(QAItem(question=q, answer=a) for q, a in WORLD_KNOWLEDGE["reconciliation"])
    if ship.facts["activity"].id == "magnet_lab":
        out.extend(QAItem(question=q, answer=a) for q, a in WORLD_KNOWLEDGE["magnets"])
    out.extend(QAItem(question=q, answer=a) for q, a in WORLD_KNOWLEDGE["gravity"])
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


def dump_trace(ship: Ship) -> str:
    lines = ["--- world model state ---"]
    for e in ship.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:10} ({e.kind:9}) {' '.join(bits)}")
    lines.append(f"  drift={ship.drift:.2f} gravity={ship.gravity:.2f}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
place(P) :- setting(P).
activity(A) :- move(A).
tool(T) :- recon_tool(T).

valid(P, A, T) :- place(P), activity(A), tool(T), affords(P, A).

needs_reconciliation(A) :- activity(A).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, p in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        lines.append(asp.fact("gravity", pid, int(p.gravity * 100)))
        for a in sorted(p.afford):
            lines.append(asp.fact("affords", pid, a))
    for aid, a in ACTIVITIES.items():
        lines.append(asp.fact("move", aid))
    for tid, t in TOOLS.items():
        lines.append(asp.fact("recon_tool", tid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    clingo_set = set(asp_valid_combos())
    py_set = set(valid_combos())
    if clingo_set == py_set:
        print(f"OK: clingo gate matches valid_combos() ({len(py_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print("  only in clingo:", sorted(clingo_set - py_set))
    print("  only in python:", sorted(py_set - clingo_set))
    return 1


# ---------------------------------------------------------------------------
# Sample generation
# ---------------------------------------------------------------------------

CURATED = [
    StoryParams(place="orbital_station", activity="magnet_lab", tool="soft_gloves", name="Nova", gender="girl", partner="friend"),
    StoryParams(place="lunar_hangar", activity="balancing_game", tool="gravity_chart", name="Milo", gender="boy", partner="sibling"),
    StoryParams(place="small_ship", activity="bubble_walk", tool="tether_cord", name="Zuri", gender="girl", partner="co-pilot"),
]


def generate(params: StoryParams) -> StorySample:
    ship = tell(params)
    return StorySample(
        params=params,
        story=ship.render(),
        prompts=generation_prompts(ship),
        story_qa=story_qa(ship),
        world_qa=world_knowledge_qa(ship),
        world=ship,
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
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Space adventure story world with physics and reconciliation.")
    ap.add_argument("--place", choices=SETTINGS.keys())
    ap.add_argument("--activity", choices=ACTIVITIES.keys())
    ap.add_argument("--tool", choices=TOOLS.keys())
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=GENDERS)
    ap.add_argument("--partner", choices=PARTNERS)
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        triples = asp_valid_combos()
        print(f"{len(triples)} compatible combos:")
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
        while len(samples) < args.n and i < max(50, args.n * 50):
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
            header = f"### {p.name}: {p.activity} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
