#!/usr/bin/env python3
"""
A small storyworld for a space-adventure tale of bravery, suspense, and conflict.

Premise:
- A young astronaut is on a mid-mission repair trip.
- A broken ship part creates suspense and a disagreement about what to do.
- The brave choice is to use a dissimilar spare piece that still fits the job.
- The ending proves the change by showing the ship safe again.

This file is standalone and follows the storyworld contract.
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

# -----------------------------------------------------------------------------
# World constants
# -----------------------------------------------------------------------------
THRESHOLD = 1.0

PLACE_CHOICES = {
    "orbit": "the moon orbit",
    "station": "the small space station",
    "drift": "the drifting cargo lane",
    "crater": "the blue crater base",
}

HERO_NAMES = ["Mira", "Tess", "Kian", "Arlo", "Nia", "Sol", "Rin", "Pip"]
PARTNER_NAMES = ["Juno", "Bex", "Oli", "Zed", "Nova", "Lumi", "Rey"]

TRAITS = ["brave", "careful", "curious", "steady", "bold", "gentle"]

MISSION_TYPES = {
    "beacon": {
        "verb": "fix the beacon",
        "gerund": "fixing the beacon",
        "rush": "dash toward the beacon panel",
        "risk": "it could go dark",
        "keyword": "beacon",
        "tags": {"space", "light"},
    },
    "panel": {
        "verb": "repair the control panel",
        "gerund": "repairing the control panel",
        "rush": "reach for the loose panel",
        "risk": "the ship could lose its guidance",
        "keyword": "panel",
        "tags": {"space", "metal"},
    },
    "glider": {
        "verb": "mend the glider wing",
        "gerund": "mending the glider wing",
        "rush": "run to the broken wing",
        "risk": "their glide could fail",
        "keyword": "wing",
        "tags": {"space", "wing"},
    },
}

TOOLS = {
    "microtool": {
        "label": "a tiny microtool",
        "fits": {"beacon", "panel"},
        "solution": "they used the tiny microtool to tighten the part",
        "ends": "stayed steady",
    },
    "spare_clamp": {
        "label": "a spare clamp",
        "fits": {"panel", "glider"},
        "solution": "they swapped in the spare clamp and locked it in place",
        "ends": "held fast",
    },
    "patch_pin": {
        "label": "a patch pin",
        "fits": {"beacon", "glider"},
        "solution": "they slid in the patch pin and snapped the latch shut",
        "ends": "clicked snugly",
    },
}

BROKEN_PARTS = {
    "bolt": {
        "label": "the silver bolt",
        "kind": "bolt",
        "location": "panel",
        "plural": False,
    },
    "ring": {
        "label": "the green ring",
        "kind": "ring",
        "location": "beacon",
        "plural": False,
    },
    "fin": {
        "label": "the side fin",
        "kind": "fin",
        "location": "glider",
        "plural": False,
    },
}

# -----------------------------------------------------------------------------
# Shared model
# -----------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"   # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman"}
        male = {"boy", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Ship:
    place: str = "orbit"
    mission: str = "beacon"


class World:
    def __init__(self, ship: Ship) -> None:
        self.ship = ship
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
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


# -----------------------------------------------------------------------------
# Reasoning / simulation
# -----------------------------------------------------------------------------
def valid_combo(place: str, mission: str, tool: str) -> bool:
    return mission in TOOLS[tool]["fits"]


def explain_rejection(mission: str, tool: str) -> str:
    return (
        f"(No story: {TOOLS[tool]['label']} is not a believable fix for "
        f"{MISSION_TYPES[mission]['verb']}. The brave choice must still fit the job.)"
    )


def should_use_tool(mission: str, broken_kind: str, tool: str) -> bool:
    return valid_combo(place="orbit", mission=mission, tool=tool) and broken_kind in {"bolt", "ring", "fin"}


def apply_suspense(world: World, hero: Entity, partner: Entity, mission: str, broken: Entity) -> None:
    hero.memes["suspense"] = hero.memes.get("suspense", 0.0) + 1
    partner.memes["suspense"] = partner.memes.get("suspense", 0.0) + 1
    world.say(
        f"Mid-mission, a warning light blinked over the {broken.label}, and the cabin went very still."
    )
    world.say(
        f"It looked as if {MISSION_TYPES[mission]['risk']}, and both astronauts held their breath."
    )


def apply_conflict(world: World, hero: Entity, partner: Entity, mission: str, tool: str) -> None:
    hero.memes["conflict"] = hero.memes.get("conflict", 0.0) + 1
    partner.memes["conflict"] = partner.memes.get("conflict", 0.0) + 1
    world.say(
        f"{partner.id} wanted a perfect match, but {hero.id} noticed a dissimilar spare piece nearby."
    )
    world.say(
        f'"That piece looks odd," {partner.id} said. "{hero.id}, are you sure it can work?"'
    )


def apply_bravery(world: World, hero: Entity, partner: Entity, mission: str, broken: Entity, tool: str) -> None:
    hero.memes["bravery"] = hero.memes.get("bravery", 0.0) + 1
    world.say(
        f"{hero.id} took a deep breath and chose the dissimilar {TOOLS[tool]['label'].replace('a ', '')} anyway."
    )
    world.say(
        f"{hero.pronoun().capitalize()} checked the fit twice, then {TOOLS[tool]['solution']}."
    )
    world.say(
        f"At last, the {broken.label} {TOOLS[tool]['ends']}, and the warning light turned calm and blue again."
    )


def tell(place: str, mission: str, tool: str, broken_kind: str, hero_name: str, hero_type: str,
         partner_name: str, partner_type: str, trait: str) -> World:
    world = World(Ship(place=place, mission=mission))
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, meters={}, memes={}))
    partner = world.add(Entity(id=partner_name, kind="character", type=partner_type, meters={}, memes={}))
    broken_cfg = BROKEN_PARTS[broken_kind]
    broken = world.add(Entity(
        id="broken_part",
        type=broken_cfg["kind"],
        label=broken_cfg["label"],
        phrase=broken_cfg["label"],
        owner="ship",
    ))

    world.say(
        f"{hero.id} was a {trait} young astronaut on {PLACE_CHOICES[place]}. "
        f"{hero.pronoun().capitalize()} liked quiet stars, shiny tools, and solving problems carefully."
    )
    world.say(
        f"{partner.id} was with {hero.id} to {MISSION_TYPES[mission]['verb']}, and their ship carried {broken.label} for the job."
    )
    world.para()

    apply_suspense(world, hero, partner, mission, broken)
    apply_conflict(world, hero, partner, mission, tool)
    world.para()
    apply_bravery(world, hero, partner, mission, broken, tool)

    world.say(
        f"In the end, the ship floated safely on, and the two astronauts smiled at the little repair that saved the day."
    )

    world.facts.update(
        hero=hero,
        partner=partner,
        broken=broken,
        mission=mission,
        tool=tool,
        place=place,
        trait=trait,
        broken_kind=broken_kind,
    )
    return world


# -----------------------------------------------------------------------------
# Registries
# -----------------------------------------------------------------------------
PLACES = sorted(PLACE_CHOICES.keys())
MISSIONS = sorted(MISSION_TYPES.keys())
TOOLS_LIST = sorted(TOOLS.keys())
BROKEN_LIST = sorted(BROKEN_PARTS.keys())
GENDERS = ["girl", "boy"]
PARENTLESS = ["none"]

CURATED = [
    dict(place="orbit", mission="beacon", tool="patch_pin", broken_kind="ring", hero_name="Mira", hero_type="girl",
         partner_name="Juno", partner_type="boy", trait="brave"),
    dict(place="station", mission="panel", tool="microtool", broken_kind="bolt", hero_name="Kian", hero_type="boy",
         partner_name="Nova", partner_type="girl", trait="careful"),
    dict(place="drift", mission="glider", tool="spare_clamp", broken_kind="fin", hero_name="Nia", hero_type="girl",
         partner_name="Rey", partner_type="boy", trait="bold"),
]

# -----------------------------------------------------------------------------
# Parameters
# -----------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    mission: str
    tool: str
    broken_kind: str
    hero_name: str
    hero_type: str
    partner_name: str
    partner_type: str
    trait: str
    seed: Optional[int] = None


# -----------------------------------------------------------------------------
# Q&A
# -----------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short space-adventure story for a young child that includes the word "dissimilar" and a mid-mission problem.',
        f"Tell a gentle story where {f['hero'].id} and {f['partner'].id} face suspense on {PLACE_CHOICES[f['place']]} and solve it with bravery.",
        f"Write a simple story about a brave repair, a risky light, and a conflict that ends in a calm ship.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    partner = f["partner"]
    broken = f["broken"]
    mission = f["mission"]
    tool = f["tool"]
    place = f["place"]
    return [
        QAItem(
            question=f"Who solved the problem on {PLACE_CHOICES[place]}?",
            answer=f"{hero.id} solved it with {partner.id} by choosing the dissimilar {TOOLS[tool]['label']}.",
        ),
        QAItem(
            question=f"What made the middle of the story feel suspenseful?",
            answer=f"The warning light blinked over {broken.label}, and it looked like {MISSION_TYPES[mission]['risk']}.",
        ),
        QAItem(
            question=f"What did {hero.id} do that showed bravery?",
            answer=f"{hero.id} took a deep breath and used the {TOOLS[tool]['label']} even though it looked unusual.",
        ),
        QAItem(
            question=f"What was the conflict in the story?",
            answer=f"{partner.id} worried the odd spare piece would not work, while {hero.id} believed it could fix {broken.label}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does bravery mean?",
            answer="Bravery means doing something scary or uncertain because it is the right thing to do.",
        ),
        QAItem(
            question="What is suspense in a story?",
            answer="Suspense is the feeling of wondering what will happen next, especially when something might go wrong.",
        ),
        QAItem(
            question="What is conflict in a story?",
            answer="Conflict is when characters disagree or face a problem they must work through.",
        ),
        QAItem(
            question="What does dissimilar mean?",
            answer="Dissimilar means not the same or not matching in shape, size, or look.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: type={e.type} kind={e.kind} meters={e.meters} memes={e.memes}")
    return "\n".join(lines)


# -----------------------------------------------------------------------------
# ASP twin
# -----------------------------------------------------------------------------
ASP_RULES = r"""
place(P) :- setting(P).
mission(M) :- task(M).
tool(T) :- implement(T).

compatible(M, T) :- mission(M), tool(T), fits(T, M).
valid_story(P, M, T, B) :- setting(P), task(M), implement(T), broken(B),
                           compatible(M, T), risky(M, B).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for p in PLACES:
        lines.append(asp.fact("setting", p))
    for m in MISSIONS:
        lines.append(asp.fact("task", m))
    for t, cfg in TOOLS.items():
        lines.append(asp.fact("implement", t))
        for m in sorted(cfg["fits"]):
            lines.append(asp.fact("fits", t, m))
    for b in BROKEN_LIST:
        lines.append(asp.fact("broken", b))
    for m, cfg in MISSION_TYPES.items():
        for tag in sorted(cfg["tags"]):
            lines.append(asp.fact("tagged", m, tag))
        for b in BROKEN_LIST:
            lines.append(asp.fact("risky", m, b))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/4."))
    return sorted(set(asp.atoms(model, "valid_story")))


def python_valid_combos() -> list[tuple]:
    out = []
    for p in PLACES:
        for m in MISSIONS:
            for t in TOOLS_LIST:
                for b in BROKEN_LIST:
                    if valid_combo(p, m, t):
                        out.append((p, m, t, b))
    return sorted(set(out))


def asp_verify() -> int:
    a = set(asp_valid_combos())
    p = set(python_valid_combos())
    if a == p:
        print(f"OK: clingo parity matched ({len(a)} combos).")
        return 0
    print("MISMATCH between ASP and Python:")
    if a - p:
        print(" only in ASP:", sorted(a - p))
    if p - a:
        print(" only in Python:", sorted(p - a))
    return 1


# -----------------------------------------------------------------------------
# Generation
# -----------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Space-adventure storyworld with bravery, suspense, and conflict.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--mission", choices=MISSIONS)
    ap.add_argument("--tool", choices=TOOLS_LIST)
    ap.add_argument("--broken-kind", choices=BROKEN_LIST)
    ap.add_argument("--name")
    ap.add_argument("--partner-name")
    ap.add_argument("--gender", choices=GENDERS)
    ap.add_argument("--partner-gender", choices=GENDERS)
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
    if args.mission and args.tool and not valid_combo("orbit", args.mission, args.tool):
        raise StoryError(f"(No story: {TOOLS[args.tool]['label']} cannot fix {MISSION_TYPES[args.mission]['verb']}.)")

    combos = []
    for p in PLACES:
        if args.place and p != args.place:
            continue
        for m in MISSIONS:
            if args.mission and m != args.mission:
                continue
            for t in TOOLS_LIST:
                if args.tool and t != args.tool:
                    continue
                for b in BROKEN_LIST:
                    combos.append((p, m, t, b))
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, mission, tool, broken_kind = rng.choice(combos)
    hero_type = args.gender or rng.choice(GENDERS)
    partner_type = args.partner_gender or ("boy" if hero_type == "girl" else "girl")
    hero_name = args.name or rng.choice(HERO_NAMES)
    partner_name = args.partner_name or rng.choice(PARTNER_NAMES)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(
        place=place,
        mission=mission,
        tool=tool,
        broken_kind=broken_kind,
        hero_name=hero_name,
        hero_type=hero_type,
        partner_name=partner_name,
        partner_type=partner_type,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(
        params.place,
        params.mission,
        params.tool,
        params.broken_kind,
        params.hero_name,
        params.hero_type,
        params.partner_name,
        params.partner_type,
        params.trait,
    )
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
        print(asp_program("#show valid_story/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid_story/4."))
        combos = sorted(set(asp.atoms(model, "valid_story")))
        print(f"{len(combos)} valid story combos:\n")
        for c in combos:
            print(c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for i, row in enumerate(CURATED):
            params = StoryParams(**row, seed=base_seed + i)
            samples.append(generate(params))
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
            header = f"### {p.hero_name}: {p.mission} on {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
