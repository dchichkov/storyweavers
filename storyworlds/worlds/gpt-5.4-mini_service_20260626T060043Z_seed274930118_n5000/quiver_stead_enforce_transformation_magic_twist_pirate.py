#!/usr/bin/env python3
"""
storyworlds/worlds/quiver_stead_enforce_transformation_magic_twist_pirate.py
============================================================================

A small pirate-tale story world with a magical twist: a captain enforces a rule,
a treasured quiver is at risk, and a spell transforms the situation into a safer
path.

The world is constraint-checked. The captain only offers a fix that genuinely
handles the risky change, and the story is built from simulated state rather
than a frozen paragraph.
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

    def __post_init__(self) -> None:
        self.meters = dict(self.meters)
        self.memes = dict(self.memes)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"captain", "man", "boy"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in {"woman", "girl"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Harbor:
    place: str = "the bay"
    affords: set[str] = field(default_factory=set)
    magical: bool = False


@dataclass
class Incident:
    id: str
    verb: str
    noun: str
    effect: str
    risk_region: str
    magic_keyword: str
    twist_keyword: str


@dataclass
class Fix:
    id: str
    label: str
    phrase: str
    covers: set[str]
    guards: set[str]
    prep: str
    tail: str


class World:
    def __init__(self, harbor: Harbor) -> None:
        self.harbor = harbor
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.trace_notes: list[str] = []

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
        clone = World(self.harbor)
        clone.entities = {k: Entity(**{
            "id": v.id, "kind": v.kind, "type": v.type, "label": v.label,
            "phrase": v.phrase, "owner": v.owner, "caretaker": v.caretaker,
            "worn_by": v.worn_by, "region": v.region, "plural": v.plural,
            "meters": dict(v.meters), "memes": dict(v.memes),
        }) for k, v in self.entities.items()}
        clone.fired = set(self.fired)
        return clone

    def worn_items(self, actor: Entity) -> list[Entity]:
        return [e for e in self.entities.values() if e.worn_by == actor.id]


@dataclass
class StoryParams:
    place: str
    incident: str
    fix: str
    name: str
    seed: Optional[int] = None


HARBORS = {
    "bay": Harbor(place="the bay", affords={"quiver", "stead"}, magical=True),
    "dock": Harbor(place="the dock", affords={"quiver", "stead"}, magical=True),
    "isle": Harbor(place="the isle", affords={"quiver"}, magical=True),
}

INCIDENTS = {
    "quiver": Incident(
        id="quiver",
        verb="shoot the quiver full of sparks",
        noun="quiver",
        effect="sparked and warm",
        risk_region="back",
        magic_keyword="Magic",
        twist_keyword="Twist",
    ),
    "stead": Incident(
        id="stead",
        verb="gallop the stead through the spray",
        noun="stead",
        effect="splashed and skittish",
        risk_region="legs",
        magic_keyword="Transformation",
        twist_keyword="Twist",
    ),
}

FIXES = [
    Fix(
        id="cloak",
        label="a saltcloak",
        phrase="a saltcloak with a silver clasp",
        covers={"back"},
        guards={"sparks"},
        prep="put on the saltcloak first",
        tail="pulled the saltcloak tight and rode on",
    ),
    Fix(
        id="bridle",
        label="a calm bridle",
        phrase="a calm bridle braided with blue thread",
        covers={"legs"},
        guards={"spray"},
        prep="fit the calm bridle first",
        tail="took the calm bridle and kept the stead steady",
    ),
]

NAMES = ["Mara", "Finn", "Jory", "Nell", "Kip", "Tamsin"]
TRAITS = ["bold", "quick", "cheery", "stubborn", "bright"]


def risky(incident: Incident) -> bool:
    return incident.id in INCIDENTS


def select_fix(incident: Incident) -> Optional[Fix]:
    guard = "sparks" if incident.id == "quiver" else "spray"
    region = incident.risk_region
    for fix in FIXES:
        if guard in fix.guards and region in fix.covers:
            return fix
    return None


def explain_rejection(incident: Incident) -> str:
    return (
        f"(No story: there is no honest fix for {incident.id} in this tiny pirate world.)"
    )


def asp_facts() -> str:
    import asp
    lines = []
    for hid, h in HARBORS.items():
        lines.append(asp.fact("harbor", hid))
        if h.magical:
            lines.append(asp.fact("magical_harbor", hid))
        for a in sorted(h.affords):
            lines.append(asp.fact("affords", hid, a))
    for iid, i in INCIDENTS.items():
        lines.append(asp.fact("incident", iid))
        lines.append(asp.fact("risk_region", iid, i.risk_region))
    for fx in FIXES:
        lines.append(asp.fact("fix", fx.id))
        for c in sorted(fx.covers):
            lines.append(asp.fact("covers", fx.id, c))
        for g in sorted(fx.guards):
            lines.append(asp.fact("guards", fx.id, g))
    return "\n".join(lines)


ASP_RULES = r"""
risky(I) :- incident(I).
compatible(F,I) :- risky(I), risk_region(I,R), covers(F,R), incident(I), guards(F,G), needed_guard(I,G).
has_fix(I) :- compatible(_,I).
valid(H,I,F) :- affords(H,I), has_fix(I).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    ax = set(asp_valid())
    if py == ax:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and python:")
    print("only in python:", sorted(py - ax))
    print("only in clingo:", sorted(ax - py))
    return 1


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for hid, h in HARBORS.items():
        for iid in h.affords:
            inc = INCIDENTS[iid]
            if select_fix(inc) is not None:
                combos.append((hid, iid, select_fix(inc).id))
    return combos


def build_story(world: World, params: StoryParams) -> None:
    captain = world.add(Entity(id=params.name, kind="character", type="captain", label="captain"))
    mate = world.add(Entity(id="Mate", kind="character", type="crew", label="mate"))
    incident = INCIDENTS[params.incident]
    fix = select_fix(incident)
    if fix is None:
        raise StoryError(explain_rejection(incident))

    world.facts.update(captain=captain, mate=mate, incident=incident, fix=fix)

    world.say(f"{captain.id} was a {random.choice(TRAITS)} pirate captain who loved a bright trick and a brave song.")
    world.say(f"{captain.id} kept a quiver by the deck rail and a steady steed by the pier, because every pirate ship had room for one odd treasure.")
    world.say(f"{captain.id} and the mate sailed into {world.harbor.place}, where the air smelled of salt and old wood.")

    world.para()
    if params.incident == "quiver":
        world.say(
            f"{captain.id} wanted to {incident.verb}, but the mate warned that the quiver would get {incident.effect}."
        )
    else:
        world.say(
            f"{captain.id} wanted to {incident.verb}, but the mate warned that the stead would get {incident.effect}."
        )

    world.say(
        f'The captain said, "I will enforce one rule: no risky play without a safe plan."'
    )
    world.say(
        f"Then a magic gust rolled over the harbor, and the wind made a small twist in the ropes and sails."
    )

    captain.memes["resolve"] = captain.memes.get("resolve", 0) + 1
    captain.memes["worry"] = captain.memes.get("worry", 0) + 1

    world.para()
    world.say(
        f"{captain.id} looked at {fix.label} and smiled. {captain.pronoun('possessive').capitalize()} plan was to {fix.prep}."
    )
    world.say(
        f"That way, the {incident.noun} could stay safe from the magic twist."
    )
    world.say(
        f"{captain.id} did not need to stop the adventure; {captain.pronoun()} only needed to transform the way it began."
    )
    world.say(
        f"Soon {captain.id} {fix.tail}, and the little pirate crew cheered as the harbor glittered in the last light."
    )
    captain.memes["joy"] = captain.memes.get("joy", 0) + 1
    captain.memes["worry"] = 0


def tell(params: StoryParams) -> World:
    harbor = HARBORS[params.place]
    world = World(harbor)
    build_story(world, params)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    inc: Incident = f["incident"]
    return [
        f'Write a short pirate tale with a {inc.noun}, a Magic breeze, and a Twist that changes the plan.',
        f"Tell a child-friendly pirate story where {f['captain'].id} enforces a rule and finds a safe fix.",
        f"Write a small story about a captain, {inc.noun}, and a transformation that keeps the adventure going.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    cap: Entity = f["captain"]
    inc: Incident = f["incident"]
    fix: Fix = f["fix"]
    return [
        QAItem(
            question=f"What did {cap.id} want to do at first?",
            answer=f"{cap.id} wanted to {inc.verb}.",
        ),
        QAItem(
            question=f"What rule did {cap.id} enforce?",
            answer="The captain enforced a rule that risky play needed a safe plan first.",
        ),
        QAItem(
            question=f"What helped keep the {inc.noun} safe?",
            answer=f"{fix.label} helped keep the {inc.noun} safe during the magic twist.",
        ),
        QAItem(
            question=f"What changed the pirate plan in the end?",
            answer="A magic twist changed the plan, and the captain used a transformation-style fix instead of stopping the fun.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    inc: Incident = f["incident"]
    if inc.id == "quiver":
        return [
            QAItem(
                question="What is a quiver?",
                answer="A quiver is a holder for arrows, often carried on the back or slung over a shoulder.",
            ),
            QAItem(
                question="What does magic mean in a story?",
                answer="Magic means something impossible or surprising happens in a special way.",
            ),
        ]
    return [
        QAItem(
            question="What is a stead in old pirate stories?",
            answer="A stead is a horse or riding animal that carries a rider.",
        ),
        QAItem(
            question="What is a transformation?",
            answer="A transformation is a change from one state or form into another.",
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
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Pirate tale story world with magic twist.")
    ap.add_argument("--place", choices=HARBORS)
    ap.add_argument("--incident", choices=INCIDENTS)
    ap.add_argument("--fix", choices=[f.id for f in FIXES])
    ap.add_argument("--name", choices=NAMES)
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
    if args.incident and args.fix:
        inc = INCIDENTS[args.incident]
        fx = next(f for f in FIXES if f.id == args.fix)
        if not (inc.risk_region in fx.covers and any(g in fx.guards for g in ("sparks", "spray"))):
            raise StoryError("(No valid combination matches the given options.)")
    combos = valid_combos()
    if args.place:
        combos = [c for c in combos if c[0] == args.place]
    if args.incident:
        combos = [c for c in combos if c[1] == args.incident]
    if args.fix:
        combos = [c for c in combos if c[2] == args.fix]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, incident, fix = rng.choice(sorted(combos))
    name = args.name or rng.choice(NAMES)
    return StoryParams(place=place, incident=incident, fix=fix, name=name)


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
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


CURATED = [
    StoryParams(place="bay", incident="quiver", fix="cloak", name="Mara"),
    StoryParams(place="dock", incident="stead", fix="bridle", name="Finn"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        triples = asp_valid()
        print(f"{len(triples)} compatible combos:\n")
        for place, incident, fix in triples:
            print(f"  {place:8} {incident:8} {fix:8}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            seed = base_seed + i
            i += 1
            params = resolve_params(args, random.Random(seed))
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
            header = f"### {p.name}: {p.incident} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
