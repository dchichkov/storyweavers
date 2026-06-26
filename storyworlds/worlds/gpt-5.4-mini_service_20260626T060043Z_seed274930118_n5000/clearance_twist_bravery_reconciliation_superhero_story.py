#!/usr/bin/env python3
"""
storyworlds/worlds/clearance_twist_bravery_reconciliation_superhero_story.py
============================================================================

A small superhero story world about a brave hero, a tense twist, a hard choice,
and a reconciliation that earns clearance for a final act of rescue.

The seed tale behind this world is simple:
- A young hero wants to join a city rescue drill.
- The hero needs clearance to enter the rooftop launcher and suit bay.
- A sudden twist makes the hero look suspicious.
- Bravery reveals the truth.
- Reconciliation repairs trust and opens the gate.

This script models a tiny, classical simulation with:
- physical meters: clearance, damage, distance, readiness, trust, etc.
- emotional memes: fear, bravery, hurt, relief, pride, apology, forgiveness.

The story is state-driven: the same simulated events produce the prose, QA, and
trace output.
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
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.type in {"scissors", "goggles"} else "it"


@dataclass
class Setting:
    place: str
    afford: set[str] = field(default_factory=set)


@dataclass
class Mission:
    id: str
    verb: str
    gerund: str
    twist: str
    risk: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class ClearanceItem:
    id: str
    label: str
    phrase: str
    covers: set[str]
    helps: set[str]
    prep: str
    tail: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
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

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]


GIRL_NAMES = ["Nova", "Mira", "Luna", "Ivy", "Zara", "Ruby"]
BOY_NAMES = ["Ray", "Tate", "Leo", "Finn", "Jace", "Kai"]
TRAITS = ["brave", "curious", "steady", "kind", "bold", "quick"]


SETTINGS = {
    "city_gate": Setting(place="the city gate", afford={"patrol", "rescue"}),
    "rooftop": Setting(place="the rooftop launch pad", afford={"rescue", "scan"}),
    "tower_hall": Setting(place="the tower hall", afford={"briefing", "repair"}),
}

MISSIONS = {
    "rescue": Mission(
        id="rescue",
        verb="join the rescue drill",
        gerund="joining the rescue drill",
        twist="a false alarm made the team think someone had broken the rules",
        risk="the gate guard might deny clearance",
        keyword="clearance",
        tags={"clearance", "rescue", "hero"},
    ),
    "patrol": Mission(
        id="patrol",
        verb="go on patrol",
        gerund="patrolling the street",
        twist="a broken beacon made the path look unsafe",
        risk="the team might think the hero was too small to help",
        keyword="clearance",
        tags={"patrol", "hero"},
    ),
    "repair": Mission(
        id="repair",
        verb="fix the broken lift",
        gerund="repairing the lift",
        twist="a snapped wire had hidden the real problem behind a panel",
        risk="the workshop might lock the tool room",
        keyword="clearance",
        tags={"repair", "trust"},
    ),
    "scan": Mission(
        id="scan",
        verb="scan the skyline",
        gerund="scanning the skyline",
        twist="a cloud of sparks hid the signal tower",
        risk="the launch pad might stay closed",
        keyword="clearance",
        tags={"scan", "clearance"},
    ),
    "briefing": Mission(
        id="briefing",
        verb="help at the briefing",
        gerund="helping at the briefing",
        twist="a mix-up in the schedule made the room tense",
        risk="the captain might send the hero away",
        keyword="clearance",
        tags={"briefing", "trust"},
    ),
}

CLEARANCES = {
    "badge": ClearanceItem(
        id="badge",
        label="silver badge",
        phrase="a silver badge with a blue star",
        covers={"door"},
        helps={"clearance"},
        prep="present the silver badge to the guard",
        tail="slid the silver badge across the scanner",
    ),
    "visor": ClearanceItem(
        id="visor",
        label="clear visor",
        phrase="a clear visor with a bright stripe",
        covers={"face"},
        helps={"scan"},
        prep="put on the clear visor first",
        tail="lowered the clear visor over their eyes",
    ),
    "passcard": ClearanceItem(
        id="passcard",
        label="pass card",
        phrase="a pass card with a red stamp",
        covers={"door"},
        helps={"repair", "briefing"},
        prep="show the pass card at the door",
        tail="held the pass card up to the latch",
    ),
}

KNOWLEDGE = {
    "clearance": [("What is clearance?",
                  "Clearance is permission to enter a place, use a tool, or start a job.")],
    "hero": [("What is a superhero?",
              "A superhero is a helper who uses courage and special gear to keep people safe.")],
    "trust": [("What is trust?",
               "Trust is when you believe someone will do the right thing and keep a promise.")],
    "rescue": [("What is a rescue?",
                "A rescue is when someone helps another person get to safety.")],
    "badge": [("What is a badge?",
               "A badge is a small sign or pin that can show who you are or where you belong.")],
    "visor": [("What does a visor do?",
               "A visor can protect your eyes and help you see more clearly.")],
}

KNOWLEDGE_ORDER = ["clearance", "hero", "trust", "rescue", "badge", "visor"]


def story_tone(mission: Mission) -> str:
    return {
        "rescue": "The city hummed like a drum before a big save.",
        "patrol": "The streetlights blinked like watchful eyes.",
        "repair": "The workshop smelled like metal and courage.",
        "scan": "The rooftop wind tugged at every cape and ribbon.",
        "briefing": "The tower hall felt serious and still.",
    }[mission.id]


def select_clearance(mission: Mission) -> ClearanceItem:
    for item in CLEARANCES.values():
        if mission.id in item.helps or "clearance" in item.helps:
            return item
    raise StoryError("No reasonable clearance item fits this mission.")


def reasonableness_gate(mission: Mission, item: ClearanceItem) -> None:
    if mission.id not in item.helps and "clearance" not in item.helps:
        raise StoryError("The chosen clearance item does not fit the mission.")


def build_world(setting: Setting, mission: Mission, hero_name: str, hero_type: str,
                parent_type: str, trait: str) -> World:
    world = World(setting)
    hero = world.add(Entity(
        id=hero_name, kind="character", type=hero_type, label=hero_name,
        memes={"bravery": 0.0, "fear": 0.0, "hurt": 0.0, "pride": 0.0, "relief": 0.0,
               "apology": 0.0, "forgiveness": 0.0, "trust": 0.0},
        meters={"clearance": 0.0},
    ))
    mentor = world.add(Entity(
        id="Mentor", kind="character", type=parent_type, label="the mentor",
        memes={"trust": 0.0, "worry": 0.0, "hurt": 0.0, "forgiveness": 0.0},
    ))
    gate = world.add(Entity(
        id="Gate", kind="thing", type="gate", label="the gate",
        meters={"open": 0.0},
    ))
    item = select_clearance(mission)
    gear = world.add(Entity(
        id=item.id, kind="thing", type="gear", label=item.label, phrase=item.phrase,
        owner=hero.id, caretaker=mentor.id, meters={"ready": 1.0},
    ))
    gear.worn_by = hero.id

    world.facts.update(hero=hero, mentor=mentor, gate=gate, gear=gear, mission=mission,
                       setting=setting, trait=trait)
    return world


def narrate_setup(world: World) -> None:
    f = world.facts
    hero: Entity = f["hero"]
    mentor: Entity = f["mentor"]
    mission: Mission = f["mission"]
    world.say(f"{hero.id} was a little {f['trait']} {hero.type} who wanted to help when the city needed it most.")
    world.say(f"{hero.pronoun().capitalize()} loved {mission.gerund}, because it made {hero.pronoun('object')} feel like a real superhero.")
    world.say(f"At home, {mentor.label} had given {hero.id} {hero.pronoun('object')} {f['gear'].phrase}.")
    world.say(story_tone(mission))


def narrate_twist(world: World) -> None:
    f = world.facts
    hero: Entity = f["hero"]
    mentor: Entity = f["mentor"]
    mission: Mission = f["mission"]
    gear: Entity = f["gear"]
    world.para()
    hero.memes["fear"] += 1.0
    mentor.memes["worry"] += 1.0
    world.say(f"One day, {hero.id} and {mentor.label} hurried to {world.setting.place}.")
    world.say(f"{hero.id} wanted to {mission.verb}, but {mission.twist} and {mission.risk}.")
    world.say(f"The guard frowned and asked for clearance, even while {hero.id} held up {gear.label}.")
    hero.meters["clearance"] = 0.0
    mentor.memes["hurt"] += 1.0


def narrate_bravery(world: World) -> None:
    f = world.facts
    hero: Entity = f["hero"]
    mentor: Entity = f["mentor"]
    mission: Mission = f["mission"]
    gear: Entity = f["gear"]
    world.para()
    hero.memes["bravery"] += 1.0
    hero.meters["clearance"] += 1.0
    world.say(f"Then {hero.id} took a deep breath and stepped forward anyway.")
    world.say(f"{hero.pronoun().capitalize()} showed {gear.label} was real clearance gear and explained the mix-up.")
    world.say(f"{hero.id} did not shout; {hero.pronoun()} spoke clearly, which made the guard listen.")
    mentor.memes["trust"] += 1.0
    hero.memes["pride"] += 1.0


def narrate_reconciliation(world: World) -> None:
    f = world.facts
    hero: Entity = f["hero"]
    mentor: Entity = f["mentor"]
    gate: Entity = f["gate"]
    world.para()
    mentor.memes["forgiveness"] += 1.0
    hero.memes["apology"] += 1.0
    hero.memes["relief"] += 1.0
    gate.meters["open"] = 1.0
    world.say(f"The guard saw the truth, and the mistake melted away.")
    world.say(f"{hero.id} apologized for the confusion, and {mentor.label} forgave {hero.pronoun('object')} right away.")
    world.say(f"That was the twist turning into reconciliation: the gate opened, and the city had its helper back.")
    world.say(f"{hero.id} went through with {hero.meters['clearance']:.0f} clear in {hero.pronoun('possessive')} heart, brave and smiling.")


def tell(setting: Setting, mission: Mission, hero_name: str, hero_type: str,
         parent_type: str, trait: str) -> World:
    world = build_world(setting, mission, hero_name, hero_type, parent_type, trait)
    narrate_setup(world)
    narrate_twist(world)
    narrate_bravery(world)
    narrate_reconciliation(world)
    return world


@dataclass
class StoryParams:
    place: str
    mission: str
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str]]:
    return [(place, mission) for place, s in SETTINGS.items() for mission in s.afford if mission in MISSIONS]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = f["hero"]
    mission: Mission = f["mission"]
    return [
        f'Write a short superhero story for a child about "{mission.keyword}" and a brave act of clearance.',
        f"Tell a story where {hero.id} tries to {mission.verb} but must earn clearance after a surprising twist.",
        f"Write a simple superhero story with bravery, reconciliation, and a gate that opens at the end.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    mentor: Entity = f["mentor"]
    mission: Mission = f["mission"]
    return [
        QAItem(
            question=f"What did {hero.id} want to do at {world.setting.place}?",
            answer=f"{hero.id} wanted to {mission.verb}, because {hero.pronoun()} wanted to help like a superhero.",
        ),
        QAItem(
            question=f"Why did the guard ask for clearance?",
            answer=f"The guard asked for clearance because the twist made the scene look risky and the city needed proof that the gear and hero belonged there.",
        ),
        QAItem(
            question=f"How did {hero.id} show bravery?",
            answer=f"{hero.id} showed bravery by stepping forward, speaking clearly, and explaining the mix-up instead of running away.",
        ),
        QAItem(
            question=f"What changed after reconciliation?",
            answer=f"After reconciliation, the mistake was forgiven, the gate opened, and {hero.id} could help again.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    out: list[QAItem] = []
    tags = set(world.facts["mission"].tags)
    tags.update({"clearance"})
    for tag in KNOWLEDGE_ORDER:
        if tag in tags and tag in KNOWLEDGE:
            q, a = KNOWLEDGE[tag][0]
            out.append(QAItem(question=q, answer=a))
    return out


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


def explain_rejection(place: str, mission: str) -> str:
    return f"(No story: {mission} is not possible at {place} in this world.)"


ASP_RULES = r"""
place(P) :- setting(P).
mission(M) :- activity(M).
gear(G) :- item(G).

can_enter(P,M) :- afford(P,M).
needs_clearance(M) :- mission(M).

brave(H) :- hero(H).
reconciles(H) :- apology(H), forgiveness(H).

valid_story(P,M) :- can_enter(P,M), needs_clearance(M).
valid_story(P,M) :- can_enter(P,M), brave(hero), reconciles(hero).
#show valid_story/2.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        for m in sorted(setting.afford):
            lines.append(asp.fact("afford", pid, m))
    for mid, mission in MISSIONS.items():
        lines.append(asp.fact("activity", mid))
    for gid, gear in CLEARANCES.items():
        lines.append(asp.fact("item", gid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if py == asp_set:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - asp_set:
        print("  only in python:", sorted(py - asp_set))
    if asp_set - py:
        print("  only in clingo:", sorted(asp_set - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Superhero story world with clearance, bravery, twist, and reconciliation.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--mission", choices=MISSIONS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name")
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
    combos = valid_combos()
    if args.place:
        combos = [c for c in combos if c[0] == args.place]
    if args.mission:
        combos = [c for c in combos if c[1] == args.mission]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, mission = rng.choice(sorted(combos))
    name = args.name or rng.choice(GIRL_NAMES if (args.gender or "girl") == "girl" else BOY_NAMES)
    gender = args.gender or ("girl" if name in GIRL_NAMES else "boy")
    parent = args.parent or rng.choice(["mother", "father"])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, mission=mission, name=name, gender=gender, parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], MISSIONS[params.mission], params.name,
                 "girl" if params.gender == "girl" else "boy", params.parent, params.trait)
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
    StoryParams(place="city_gate", mission="rescue", name="Nova", gender="girl", parent="mother", trait="brave"),
    StoryParams(place="rooftop", mission="scan", name="Ray", gender="boy", parent="father", trait="steady"),
    StoryParams(place="tower_hall", mission="briefing", name="Mira", gender="girl", parent="mother", trait="kind"),
    StoryParams(place="city_gate", mission="patrol", name="Kai", gender="boy", parent="father", trait="bold"),
    StoryParams(place="tower_hall", mission="repair", name="Ivy", gender="girl", parent="mother", trait="curious"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid_story/2."))
        print(sorted(set(asp.atoms(model, "valid_story"))))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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
            header = f"### {p.name}: {p.mission} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
