#!/usr/bin/env python3
"""
A tiny story world about an ant colony trying to assign a parcel-delivery task.

Seed tale:
A little ant found a parcel near the hill. The ants needed to assign who would
carry it home before the night rain came. They tried to solve the problem with
teams, maps, and careful routes, but the parcel slipped away in the dark, and
the colony went to sleep sad and worried.

This world keeps the state small and classical:
- ants have stamina, worry, pride, and tiredness
- parcels have weight, fragility, and location
- assignment tries to match a parcel to a carrier
- problem solving may reduce risk, but this world intentionally allows a bad ending
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
@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    plural: bool = False
    owner: Optional[str] = None
    location: str = ""
    assigned_to: Optional[str] = None
    carried_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "character":
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the hill"
    weather: str = "evening"
    hazards: set[str] = field(default_factory=set)


@dataclass
class AntSpec:
    name: str
    role: str
    size: str
    stamina: int
    traits: list[str] = field(default_factory=list)


@dataclass
class ParcelSpec:
    label: str
    phrase: str
    weight: int
    fragile: bool
    origin: str
    destination: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.trace: list[str] = []

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


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "hill": Setting(place="the hill", weather="evening", hazards={"wind"}),
    "path": Setting(place="the lantern path", weather="night", hazards={"dark"}),
    "leafy": Setting(place="the leafy tunnel", weather="evening", hazards={"rain"}),
}

ANTS = {
    "mina": AntSpec(name="Mina", role="scout", size="small", stamina=4, traits=["careful", "gentle"]),
    "taro": AntSpec(name="Taro", role="carrier", size="strong", stamina=6, traits=["steady", "patient"]),
    "lulu": AntSpec(name="Lulu", role="planner", size="small", stamina=5, traits=["smart", "calm"]),
    "nib": AntSpec(name="Nib", role="helper", size="tiny", stamina=3, traits=["quick", "eager"]),
}

PARCELS = {
    "crumbs": ParcelSpec(label="parcel of crumbs", phrase="a parcel of sweet crumbs", weight=2, fragile=False, origin="the kitchen step", destination="the nursery hall"),
    "berry": ParcelSpec(label="parcel of berries", phrase="a parcel of ripe berries", weight=3, fragile=True, origin="the garden gate", destination="the baby room"),
    "seed": ParcelSpec(label="parcel of seeds", phrase="a parcel of shining seeds", weight=1, fragile=False, origin="the old log", destination="the warm pantry"),
}

ASSIGNMENTS = {
    "single": "assign one ant",
    "team": "assign a team",
    "relay": "assign a relay line",
}

# ---------------------------------------------------------------------------
# Parameters
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    setting: str
    parcel: str
    assignment: str
    lead_ant: str
    helper_ant: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A parcel is assignable when there is enough ant skill to carry it.
can_carry(A, P) :- ant(A), parcel(P), ant_stamina(A, S), parcel_weight(P, W), S >= W.

% A plan is reasonable when a chosen carrier can carry the parcel.
plan(S, P, A) :- setting(S), parcel(P), can_carry(A, P).

% A relay is possible if two ants together can carry the parcel.
relay_plan(S, P, A1, A2) :- setting(S), parcel(P), ant(A1), ant(A2), A1 != A2,
                           ant_stamina(A1, S1), ant_stamina(A2, S2),
                           parcel_weight(P, W), S1 + S2 >= W.

% The world is valid if at least one plan exists.
valid_story(S, P) :- plan(S, P, _).
valid_story(S, P) :- relay_plan(S, P, _, _).

#show valid_story/2.
#show plan/3.
#show relay_plan/4.
"""

def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for aid, a in ANTS.items():
        lines.append(asp.fact("ant", aid))
        lines.append(asp.fact("ant_role", aid, a.role))
        lines.append(asp.fact("ant_stamina", aid, a.stamina))
    for pid, p in PARCELS.items():
        lines.append(asp.fact("parcel", pid))
        lines.append(asp.fact("parcel_weight", pid, p.weight))
        if p.fragile:
            lines.append(asp.fact("fragile", pid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_stories())
    asp_set = set(asp_valid_stories())
    if py == asp_set:
        print(f"OK: clingo gate matches valid_stories() ({len(py)} cases).")
        return 0
    print("MISMATCH between clingo and python:")
    if py - asp_set:
        print("  only in python:", sorted(py - asp_set))
    if asp_set - py:
        print("  only in clingo:", sorted(asp_set - py))
    return 1


# ---------------------------------------------------------------------------
# Reasonable gate
# ---------------------------------------------------------------------------
def valid_stories() -> list[tuple[str, str]]:
    out = []
    for sid in SETTINGS:
        for pid, p in PARCELS.items():
            for aid, a in ANTS.items():
                if a.stamina >= p.weight:
                    out.append((sid, pid))
                    break
    return sorted(set(out))


def explain_rejection(parcel: ParcelSpec, ant: AntSpec) -> str:
    return (
        f"(No story: {ant.name} is too tired to carry {parcel.phrase}. "
        f"Try a stronger ant or a lighter parcel.)"
    )


# ---------------------------------------------------------------------------
# World simulation
# ---------------------------------------------------------------------------
def build_world(params: StoryParams) -> World:
    setting = SETTINGS[params.setting]
    world = World(setting)

    lead_spec = ANTS[params.lead_ant]
    helper_spec = ANTS[params.helper_ant]
    parcel_spec = PARCELS[params.parcel]

    lead = world.add(Entity(
        id=lead_spec.name, kind="character", type="ant", label=lead_spec.name,
        phrase=f"a little {lead_spec.role} ant", meters={"stamina": float(lead_spec.stamina)}, memes={}
    ))
    helper = world.add(Entity(
        id=helper_spec.name, kind="character", type="ant", label=helper_spec.name,
        phrase=f"a little {helper_spec.role} ant", meters={"stamina": float(helper_spec.stamina)}, memes={}
    ))
    parcel = world.add(Entity(
        id="parcel", kind="thing", type="parcel", label=parcel_spec.label,
        phrase=parcel_spec.phrase, location=setting.place, meters={"weight": float(parcel_spec.weight)},
    ))

    # Act 1: bedtime-story setup
    world.say(
        f"At {setting.place}, little {lead.label} found {parcel.phrase} resting beside a pebble."
    )
    world.say(
        f"{lead.label} called softly for {helper.label}, because the ants needed to assign the parcel before night got deeper."
    )
    world.para()

    # Act 2: problem solving
    lead.memes["worry"] = 1.0
    helper.memes["worry"] = 1.0
    world.say(
        f"The colony gathered under a leaf and thought very hard. "
        f"They looked at the parcel's weight, the dark path, and the long way home."
    )

    if params.assignment == "single":
        parcel.assigned_to = lead.id
        parcel.carried_by = lead.id
        world.say(
            f"They decided to assign {lead.label} alone, because {lead.label} was quick and brave."
        )
    elif params.assignment == "team":
        parcel.assigned_to = lead.id
        parcel.carried_by = helper.id
        world.say(
            f"They decided to assign a team, with {lead.label} pointing the way and {helper.label} carrying the front end."
        )
    else:
        parcel.assigned_to = lead.id
        parcel.carried_by = helper.id
        world.say(
            f"They made a relay line, so the parcel could pass from ant to ant like a tiny bedtime lantern."
        )

    # Bad ending: a plausible failure in the dark
    world.para()
    if setting.hazards & {"dark", "wind", "rain"}:
        lead.memes["fear"] = 1.0
        helper.memes["fear"] = 1.0
        parcel.meters["slip_risk"] = 1.0

    if params.parcel == "berry" and params.setting == "leafy":
        world.say(
            f"But the leaf tunnel shook with a small rain tap, and the berries got slippery."
        )
        world.say(
            f"The ants tried to brace the load, yet the parcel slid from the path and rolled into the grass."
        )
    else:
        world.say(
            f"Then a gust nudged the parcel, and the line of ants lost their careful rhythm."
        )
        world.say(
            f"The parcel tipped into a crack by the root, too far for the smallest feet to reach."
        )

    parcel.location = "lost in the grass"
    parcel.meters["lost"] = 1.0
    lead.memes["sad"] = 1.0
    helper.memes["sad"] = 1.0
    world.say(
        f"The ants searched with their antennae low, but the night kept the parcel hidden."
    )
    world.say(
        f"At last the colony went home quiet and sleepy, with no parcel delivered and no warm cheer at the door."
    )

    world.facts = {
        "setting": setting,
        "parcel_spec": parcel_spec,
        "lead": lead_spec,
        "helper": helper_spec,
        "assignment": params.assignment,
        "bad_ending": True,
    }
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    p = f["parcel_spec"]
    lead = f["lead"]
    return [
        "Write a bedtime story about ants trying to solve a delivery problem, but ending sadly.",
        f"Tell a gentle story where {lead.name} must assign {p.phrase} before night gets too dark.",
        f"Write a small bedtime story about a parcel, an ant colony, and a plan that does not work out.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    lead = f["lead"]
    helper = f["helper"]
    p = f["parcel_spec"]
    setting = f["setting"]
    return [
        QAItem(
            question=f"Who found the parcel at {setting.place}?",
            answer=f"{lead.name} found {p.phrase} near a pebble at {setting.place}."
        ),
        QAItem(
            question="What were the ants trying to do before the night got deeper?",
            answer="They were trying to assign who would carry the parcel home."
        ),
        QAItem(
            question=f"Why did {lead.name} and {helper.name} feel worried?",
            answer=f"They were worried because the parcel was heavy enough to need careful planning, and the dark made the trip risky."
        ),
        QAItem(
            question="How did the story end?",
            answer="It ended badly: the parcel slipped away, the ants could not recover it, and they went home sad and sleepy."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is an ant?",
            answer="An ant is a tiny insect that often lives with many other ants in a colony."
        ),
        QAItem(
            question="What is a parcel?",
            answer="A parcel is a wrapped package or bundle that can be carried from one place to another."
        ),
        QAItem(
            question="What does assign mean?",
            answer="To assign means to choose who will do a job or take a task."
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        bits = []
        if e.location:
            bits.append(f"location={e.location}")
        if e.assigned_to:
            bits.append(f"assigned_to={e.assigned_to}")
        if e.carried_by:
            bits.append(f"carried_by={e.carried_by}")
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:8} ({e.type}) {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Parameters, generation, emit
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    setting: str
    parcel: str
    assignment: str
    lead_ant: str
    helper_ant: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Bedtime story world about ants, parcels, and assignment.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--parcel", choices=PARCELS)
    ap.add_argument("--assignment", choices=ASSIGNMENTS)
    ap.add_argument("--lead-ant", choices=ANTS)
    ap.add_argument("--helper-ant", choices=ANTS)
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
    if args.lead_ant and args.helper_ant and args.lead_ant == args.helper_ant:
        raise StoryError("Lead ant and helper ant must be different.")
    if args.assignment == "single" and args.helper_ant is not None:
        raise StoryError("Single-ant assignment cannot have a helper ant pinned.")
    setting = args.setting or rng.choice(list(SETTINGS))
    parcel = args.parcel or rng.choice(list(PARCELS))
    assignment = args.assignment or rng.choice(list(ASSIGNMENTS))
    lead = args.lead_ant or rng.choice(list(ANTS))
    helper = args.helper_ant or rng.choice([k for k in ANTS if k != lead])
    spec = PARCELS[parcel]
    if ANTS[lead].stamina < spec.weight and assignment == "single":
        raise StoryError(explain_rejection(spec, ANTS[lead]))
    return StoryParams(setting=setting, parcel=parcel, assignment=assignment, lead_ant=lead, helper_ant=helper)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
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
# ASP helpers
# ---------------------------------------------------------------------------
def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid_story/2.\n#show plan/3.\n#show relay_plan/4."))
    out = []
    out.extend(asp.atoms(model, "valid_story"))
    return sorted(set(out))


def asp_verify_gate() -> int:
    py = set(valid_stories())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_stories() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and python:")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
CURATED = [
    StoryParams(setting="hill", parcel="crumbs", assignment="single", lead_ant="taro", helper_ant="mina"),
    StoryParams(setting="path", parcel="berry", assignment="team", lead_ant="lulu", helper_ant="taro"),
    StoryParams(setting="leafy", parcel="seed", assignment="relay", lead_ant="mina", helper_ant="nib"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/2.\n#show plan/3.\n#show relay_plan/4."))
        return
    if args.verify:
        sys.exit(asp_verify_gate())

    if args.asp:
        triples = asp_valid_combos()
        print(f"{len(triples)} valid story cases:\n")
        for item in triples:
            print(item)
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
        if len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
