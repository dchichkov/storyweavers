#!/usr/bin/env python3
"""
A small pirate tale storyworld with suspense, protest, and repeated phrases.

The seed premise:
- A young pirate wants to sail into a dangerous place.
- The crew protests because the plan could get them lost or caught.
- Suspense grows as the captain insists, then a safer choice resolves it.

The world model tracks physical meters and emotional memes so the story is
driven by state, not by swapped nouns in a template.
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
# Registries
# ---------------------------------------------------------------------------

@dataclass
class Place:
    id: str
    label: str
    dark: bool = False
    noisy: bool = False
    hides: bool = False


@dataclass
class Risk:
    id: str
    verb: str
    danger: str
    repeats: str
    place: str
    consequence: str
    keyword: str = "suspense"


@dataclass
class Fix:
    id: str
    label: str
    method: str
    soothes: set[str]
    avoids: set[str]
    tail: str


@dataclass
class StoryParams:
    place: str
    risk: str
    fix: str
    hero: str
    helper: str
    role: str
    seed: Optional[int] = None


PLACES = {
    "reef": Place(id="reef", label="the reef", dark=True, noisy=True, hides=False),
    "cove": Place(id="cove", label="the hidden cove", dark=True, noisy=False, hides=True),
    "harbor": Place(id="harbor", label="the harbor", dark=False, noisy=True, hides=False),
    "island": Place(id="island", label="the little island", dark=False, noisy=False, hides=True),
}

RISKS = {
    "storm": Risk(
        id="storm",
        verb="sail through the storm",
        danger="the waves could smash the boat",
        repeats="again and again",
        place="reef",
        consequence="end up stuck in the dark water",
    ),
    "fog": Risk(
        id="fog",
        verb="sail into the fog",
        danger="the crew could lose the way",
        repeats="over and over",
        place="cove",
        consequence="circle in the same water all night",
    ),
    "drums": Risk(
        id="drums",
        verb="beat the drums too loudly",
        danger="the guards could hear them",
        repeats="bang, bang, bang",
        place="harbor",
        consequence="bring trouble to the deck",
    ),
    "lights": Risk(
        id="lights",
        verb="light a lantern in the dark",
        danger="the light could give them away",
        repeats="one flicker after another",
        place="island",
        consequence="wake every watcher nearby",
    ),
}

FIXES = {
    "map": Fix(
        id="map",
        label="the folded map",
        method="study the map by a dim lantern and choose the safer path",
        soothes={"fear", "conflict"},
        avoids={"storm", "fog", "drums", "lights"},
        tail="They followed the safer line on the paper",
    ),
    "rope": Fix(
        id="rope",
        label="the long rope",
        method="tie the boat to the rocks before moving on",
        soothes={"fear"},
        avoids={"storm", "fog"},
        tail="They tied fast and moved with care",
    ),
    "bell": Fix(
        id="bell",
        label="the ship bell",
        method="wrap the bell so it would not ring",
        soothes={"alarm"},
        avoids={"drums", "lights"},
        tail="They kept the ship as quiet as a mouse",
    ),
    "lantern": Fix(
        id="lantern",
        label="a shuttered lantern",
        method="shut the lantern door and use only a tiny glow",
        soothes={"fear", "suspense"},
        avoids={"lights"},
        tail="They held the light low and small",
    ),
}

HEROES = ["Pip", "Mara", "Jory", "Nell", "Finn", "Bree", "Toma", "Rook"]
HELPERS = ["the first mate", "the cook", "the lookout", "the old sailor"]
ROLES = ["captain", "mate", "swabbie", "deckhand", "young pirate"]


# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------

@dataclass
class Entity:
    id: str
    kind: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    worn: bool = False
    owned_by: Optional[str] = None

    def pronoun(self, case: str = "subject") -> str:
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.history: list[str] = []
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)
            self.history.append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        import copy
        w = World(self.place)
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        return w


# ---------------------------------------------------------------------------
# Causal rules
# ---------------------------------------------------------------------------

THRESHOLD = 1.0


def _r_protest(world: World) -> list[str]:
    out: list[str] = []
    crew = world.get("crew")
    if crew.memes.get("protest", 0.0) < THRESHOLD:
        return out
    sig = ("protest", crew.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    crew.memes["tension"] = crew.memes.get("tension", 0.0) + 1.0
    out.append("The crew spoke up, low and sharp, because they did not like the plan.")
    return out


def _r_suspense(world: World) -> list[str]:
    hero = world.get("hero")
    risk = world.facts.get("risk")
    if hero.memes.get("hesitation", 0.0) < THRESHOLD:
        return []
    sig = ("suspense", hero.id, risk.id if risk else "")
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["suspense"] = hero.memes.get("suspense", 0.0) + 1.0
    return [f"The wind went hush-hush, and everyone waited to see what would happen next."]


def _r_settle(world: World) -> list[str]:
    hero = world.get("hero")
    if hero.memes.get("calm", 0.0) < THRESHOLD:
        return []
    sig = ("settle", hero.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["suspense"] = 0.0
    return [f"The worry eased, and the ship felt steady again."]


CAUSAL_RULES = [
    _r_protest,
    _r_suspense,
    _r_settle,
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                out.extend(sents)
    if narrate:
        for s in out:
            world.say(s)
    return out


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------

def can_fix(risk: Risk, fix: Fix) -> bool:
    return risk.id not in fix.avoids


def reason_invalid(risk: Risk, fix: Fix) -> str:
    return (
        f"(No story: {fix.label} would not safely solve {risk.verb}. "
        f"The fix must fit the danger, not just sound useful.)"
    )


def _predict(world: World, risk: Risk) -> bool:
    sim = world.copy()
    hero = sim.get("hero")
    hero.meters[risk.id] = hero.meters.get(risk.id, 0.0) + 1.0
    hero.memes["hesitation"] = hero.memes.get("hesitation", 0.0) + 1.0
    propagate(sim, narrate=False)
    return hero.memes.get("suspense", 0.0) > 0.0


def tell(place: Place, risk: Risk, fix: Fix, hero_name: str, helper_name: str, role: str) -> World:
    world = World(place)
    hero = world.add(Entity(id="hero", kind="character", label=hero_name))
    helper = world.add(Entity(id="helper", kind="character", label=helper_name))
    crew = world.add(Entity(id="crew", kind="group", label="the crew"))

    world.facts.update(place=place, risk=risk, fix=fix, hero=hero, helper=helper, crew=crew, role=role)

    # Act 1
    world.say(f"{hero_name} was a little {role} on {place.label}.")
    world.say(f"{hero_name} loved the sea and the salt wind, and {hero_name} liked to {risk.verb}.")
    world.say(f"But {helper_name} and the rest of the crew knew the danger: {risk.danger}.")
    world.para()

    # Act 2
    world.say(f"On that night, {place.label} felt dark and close.")
    world.say(f"{hero_name} wanted to {risk.verb}, {risk.repeats}, even though the crew protested.")
    hero.meters[risk.id] = hero.meters.get(risk.id, 0.0) + 1.0
    hero.memes["hesitation"] = hero.memes.get("hesitation", 0.0) + 1.0
    crew.memes["protest"] = crew.memes.get("protest", 0.0) + 1.0
    propagate(world, narrate=True)
    world.say(f"{hero_name} stood at the rail and listened while the water slapped the hull.")
    world.para()

    # Act 3
    if not can_fix(risk, fix):
        raise StoryError(reason_invalid(risk, fix))
    world.say(f"Then {helper_name} held up {fix.label} and said they could {fix.method}.")
    world.say(f"{fix.tail}, and the ship moved without the danger getting worse.")
    hero.memes["calm"] = hero.memes.get("calm", 0.0) + 1.0
    propagate(world, narrate=True)
    world.say(f"In the end, {hero_name} smiled. The crew was quiet, the path was safer, and the little ship slipped on through.")
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"].label
    helper = f["helper"].label
    risk = f["risk"]
    place = f["place"].label
    return [
        f'Write a short pirate tale for a young child about {hero} at {place}, with suspense and protest, and repeat the line "{risk.repeats}".',
        f"Tell a suspenseful pirate story where {hero} wants to {risk.verb} but {helper} protests and the crew finds a safer way.",
        f"Write a gentle pirate adventure that uses repetition and ends with a safer plan than {risk.verb}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"].label
    helper = f["helper"].label
    risk = f["risk"]
    fix = f["fix"]
    place = f["place"].label
    role = f["role"]
    return [
        QAItem(
            question=f"Who was the story about on {place}?",
            answer=f"It was about {hero}, a little {role}, who loved the sea and wanted to {risk.verb}.",
        ),
        QAItem(
            question=f"Why did the crew protest when {hero} wanted to {risk.verb}?",
            answer=f"The crew protested because {risk.danger}. They did not want the ship to fall into that danger.",
        ),
        QAItem(
            question=f"What did {helper} use to help the crew choose a safer plan?",
            answer=f"{helper} used {fix.label} and suggested they could {fix.method}. That gave them a safer way forward.",
        ),
        QAItem(
            question=f"How did the story end after the crew stopped protesting?",
            answer=f"It ended with the ship moving safely, while {hero} felt calmer and the danger did not happen.",
        ),
    ]


WORLD_KNOWLEDGE = {
    "suspense": [
        QAItem(
            question="What is suspense in a story?",
            answer="Suspense is the feeling of waiting and worrying about what will happen next.",
        )
    ],
    "protest": [
        QAItem(
            question="What does it mean to protest?",
            answer="To protest means to speak up and say you do not agree with something.",
        )
    ],
    "reef": [
        QAItem(
            question="What is a reef?",
            answer="A reef is a rocky place under or near the water that can be dangerous for boats.",
        )
    ],
    "fog": [
        QAItem(
            question="Why can fog be tricky for sailors?",
            answer="Fog makes it hard to see, so sailors can lose the way more easily.",
        )
    ],
    "lantern": [
        QAItem(
            question="What is a lantern used for?",
            answer="A lantern gives light, which helps people see in the dark.",
        )
    ],
    "rope": [
        QAItem(
            question="What does a rope do on a ship?",
            answer="A rope can tie things together or help hold a boat in place.",
        )
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    tags = {f["risk"].id, f["fix"].id, "suspense", "protest"}
    out: list[QAItem] = []
    for tag in ["suspense", "protest", "reef", "fog", "lantern", "rope"]:
        if tag in tags and tag in WORLD_KNOWLEDGE:
            out.extend(WORLD_KNOWLEDGE[tag])
    return out


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
    lines.append("== World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        parts = []
        if meters:
            parts.append(f"meters={meters}")
        if memes:
            parts.append(f"memes={memes}")
        lines.append(f"  {e.id}: {e.label} {' '.join(parts)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% A risk is relevant when the place matches the danger's place.
risk_at_place(R, P) :- risk(R), place(P), risk_place(R, P).

% A fix is compatible when it does not directly avoid the risk.
compatible_fix(R, F) :- risk(R), fix(F), not avoids(F, R).

valid_story(P, R, F) :- place(P), risk(R), fix(F), risk_place(R, P), compatible_fix(R, F).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for p in PLACES.values():
        lines.append(asp.fact("place", p.id))
    for r in RISKS.values():
        lines.append(asp.fact("risk", r.id))
        lines.append(asp.fact("risk_place", r.id, r.place))
    for f in FIXES.values():
        lines.append(asp.fact("fix", f.id))
        for bad in sorted(f.avoids):
            lines.append(asp.fact("avoids", f.id, bad))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for p in PLACES.values():
        for r in RISKS.values():
            if r.place != p.id:
                continue
            for f in FIXES.values():
                if can_fix(r, f):
                    out.append((p.id, r.id, f.id))
    return out


def asp_verify() -> int:
    a = set(asp_valid())
    b = set(valid_combos())
    if a == b:
        print(f"OK: clingo gate matches valid_combos() ({len(a)} combos).")
        return 0
    print("MISMATCH between ASP and Python:")
    if a - b:
        print("  only in ASP:", sorted(a - b))
    if b - a:
        print("  only in Python:", sorted(b - a))
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

CURATED = [
    StoryParams(place="reef", risk="storm", fix="map", hero="Pip", helper="the first mate", role="young pirate"),
    StoryParams(place="cove", risk="fog", fix="lantern", hero="Mara", helper="the lookout", role="captain"),
    StoryParams(place="harbor", risk="drums", fix="bell", hero="Jory", helper="the cook", role="deckhand"),
    StoryParams(place="island", risk="lights", fix="rope", hero="Nell", helper="the old sailor", role="mate"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small pirate tale storyworld with suspense and protest.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--risk", choices=RISKS)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--name")
    ap.add_argument("--helper")
    ap.add_argument("--role", choices=ROLES)
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
    if args.risk and args.fix:
        r, f = RISKS[args.risk], FIXES[args.fix]
        if not can_fix(r, f):
            raise StoryError(reason_invalid(r, f))

    combos = [
        (p.id, r.id, f.id)
        for p in PLACES.values()
        for r in RISKS.values()
        for f in FIXES.values()
        if r.place == p.id and can_fix(r, f)
    ]
    combos = [
        c for c in combos
        if (args.place is None or c[0] == args.place)
        and (args.risk is None or c[1] == args.risk)
        and (args.fix is None or c[2] == args.fix)
    ]
    if not combos:
        raise StoryError("(No valid pirate tale matches the given options.)")
    place_id, risk_id, fix_id = rng.choice(sorted(combos))
    name = args.name or rng.choice(HEROES)
    helper = args.helper or rng.choice(HELPERS)
    role = args.role or rng.choice(ROLES)
    return StoryParams(place=place_id, risk=risk_id, fix=fix_id, hero=name, helper=helper, role=role)


def generate(params: StoryParams) -> StorySample:
    place = PLACES[params.place]
    risk = RISKS[params.risk]
    fix = FIXES[params.fix]
    world = tell(place, risk, fix, params.hero, params.helper, params.role)
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid_story/3."))
        combos = sorted(set(asp.atoms(model, "valid_story")))
        print(f"{len(combos)} compatible stories:")
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

    for idx, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero}: {p.risk} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
