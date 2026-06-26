#!/usr/bin/env python3
"""
A standalone storyworld for a small Space Adventure domain.

Premise:
- A tall launch tower or tall observation ladder matters physically.
- A child astronaut wants to go on a space walk or fix a satellite.
- A flashback to an earlier setback creates conflict.
- Bravery turns the conflict into action and a safe resolution.

This script follows the Storyweavers storyworld contract:
- self-contained stdlib script
- StoryParams and CLI
- generate / emit / main
- Python reasonableness gate plus inline ASP twin
- story-grounded QA and world-knowledge QA
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
    protective: bool = False
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "captain", "pilot"}
        male = {"boy", "father", "man", "engineer", "captain"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    description: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Mission:
    id: str
    verb: str
    gerund: str
    rush: str
    risk: str
    zone: set[str]
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Gear:
    id: str
    label: str
    covers: set[str]
    guards: set[str]
    prep: str
    tail: str
    plural: bool = False


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.zone: set[str] = set()

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def worn_items(self, actor: Entity) -> list[Entity]:
        return [e for e in self.entities.values() if e.worn_by == actor.id]

    def covered(self, actor: Entity, region: str) -> bool:
        return any(e.protective and region in getattr(e, "covers", set()) for e in self.worn_items(actor))

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
        clone.fired = set(self.fired)
        clone.zone = set(self.zone)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


def prize_at_risk(mission: Mission, object_id: str) -> bool:
    obj = OBJECTS[object_id]
    return obj.region in mission.zone


def select_gear(mission: Mission, obj: "Prize") -> Optional[Gear]:
    for gear in GEAR:
        if obj.region in gear.covers and mission.risk in gear.guards:
            return gear
    return None


@dataclass
class Prize:
    label: str
    phrase: str
    type: str
    region: str
    plural: bool = False
    genders: set[str] = field(default_factory=lambda: {"girl", "boy"})


def predict_mess(world: World, hero: Entity, mission: Mission, prize_id: str) -> dict:
    sim = world.copy()
    _do_mission(sim, sim.get(hero.id), mission, narrate=False)
    prize = sim.entities.get(prize_id)
    return {"soiled": bool(prize and prize.meters.get("dust", 0) >= THRESHOLD)}


def _do_mission(world: World, actor: Entity, mission: Mission, narrate: bool = True) -> None:
    world.zone = set(mission.zone)
    actor.meters[mission.risk] = actor.meters.get(mission.risk, 0) + 1
    actor.memes["bravery"] = actor.memes.get("bravery", 0) + 1
    propagate(world, narrate=narrate)


def _r_dust(world: World) -> list[str]:
    out = []
    for actor in world.characters():
        if actor.meters.get("dust", 0) < THRESHOLD:
            continue
        for item in world.worn_items(actor):
            if item.protective:
                continue
            if item.id in world.fired:
                continue
            sig = ("dust", actor.id, item.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            item.meters["dust"] = item.meters.get("dust", 0) + 1
            out.append(f"{actor.pronoun('possessive').capitalize()} {item.label} picked up a thin layer of dust.")
    return out


def _r_conflict(world: World) -> list[str]:
    out = []
    for actor in world.characters():
        if actor.memes.get("flashback", 0) < THRESHOLD or actor.memes.get("worry", 0) < THRESHOLD:
            continue
        sig = ("conflict", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["conflict"] = actor.memes.get("conflict", 0) + 1
        out.append("__conflict__")
    return out


CAUSAL_RULES = [
    _r_dust,
    _r_conflict,
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if s != "__conflict__")
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def add_flashback(world: World, hero: Entity, mission: Mission) -> None:
    hero.memes["flashback"] = hero.memes.get("flashback", 0) + 1
    hero.memes["worry"] = hero.memes.get("worry", 0) + 1
    world.say(
        f"{hero.id} stared at the tall tower and suddenly remembered a different launch day, "
        f"when {hero.pronoun('subject')} had frozen with fear and missed the first climb."
    )
    world.say(
        f"That memory made the next step feel huge, because the tower rose so tall above the pad."
    )


def offer_bravery(world: World, mentor: Entity, hero: Entity) -> None:
    hero.memes["courage"] = hero.memes.get("courage", 0) + 1
    world.say(
        f"{mentor.label.capitalize()} touched {hero.pronoun('possessive')} shoulder and said, "
        f'"You can feel scared and still be brave. We will take it one rung at a time."'
    )


def accept_solution(world: World, hero: Entity, gear: Gear, mission: Mission, prize: Prize) -> None:
    hero.memes["conflict"] = 0
    hero.memes["calm"] = hero.memes.get("calm", 0) + 1
    world.say(
        f"{hero.id} took a breath, put on {gear.label}, and climbed with careful hands."
    )
    world.say(
        f"They {gear.tail}. At the top, {hero.id} finished {mission.gerund}, and {prize.label} stayed safe and clean."
    )


def resolve_story(world: World, hero: Entity, mentor: Entity, mission: Mission, prize: Prize, gear: Gear) -> None:
    world.para()
    world.say(
        f"{hero.id} wanted to {mission.verb}, but {hero.pronoun('possessive')} chest felt tight from the flashback."
    )
    world.say(
        f"When {hero.id} tried to {mission.rush}, {hero.pronoun('subject')} hesitated at the tall ladder."
    )
    world.say(
        f"{mentor.label.capitalize()} noticed the pause and stayed close."
    )
    offer_bravery(world, mentor, hero)
    accept_solution(world, hero, gear, mission, prize)


def tell(setting: Setting, mission: Mission, prize_cfg: Prize, hero_name: str = "Nova",
         hero_type: str = "girl", mentor_type: str = "captain", trait: str = "curious") -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, meters={}, memes={"bravery": 0.0}))
    mentor = world.add(Entity(id="Mentor", kind="character", type=mentor_type, label="the captain"))
    prize = world.add(Entity(id="prize", type=prize_cfg.type, label=prize_cfg.label, phrase=prize_cfg.phrase,
                             owner=hero.id, caretaker=mentor.id))
    prize.region = prize_cfg.region  # type: ignore[attr-defined]

    world.say(
        f"{hero.id} was a {trait} space kid who loved tall things: tall rockets, tall towers, and tall dreams."
    )
    world.say(
        f"At the launch base, {hero.id} wore {prize.phrase} and kept looking up at the {setting.place}."
    )
    world.say(
        f"{mentor.label.capitalize()} said the mission was to {mission.verb}, because the ship needed one small fix."
    )

    world.para()
    world.say(setting.description)
    add_flashback(world, hero, mission)
    world.say(
        f"{hero.id} wanted to be useful, but {hero.pronoun('possessive')} old flashback made the job feel bigger than the sky."
    )

    gear = select_gear(mission, prize_cfg)
    if gear is None:
        raise StoryError("No reasonable gear can protect this prize on this mission.")

    if predict_mess(world, hero, mission, prize.id)["soiled"]:
        resolve_story(world, hero, mentor, mission, prize_cfg, gear)

    world.facts.update(hero=hero, mentor=mentor, prize=prize, mission=mission, setting=setting, gear=gear)
    return world


SETTINGS = {
    "launchpad": Setting(
        place="launch tower",
        description="The launch tower was tall enough to make even brave kids swallow hard.",
        affords={"repair"},
    ),
    "station": Setting(
        place="space station",
        description="The station hummed softly, with windows that looked out into black glittering space.",
        affords={"repair", "collect"},
    ),
    "moonbase": Setting(
        place="moon ladder",
        description="The moon ladder stood tall in the low gravity, stretching up beside the silver habitat.",
        affords={"repair"},
    ),
}

MISSIONS = {
    "repair": Mission(
        id="repair",
        verb="fix the blinking antenna",
        gerund="fixing the blinking antenna",
        rush="climb to the antenna",
        risk="dust",
        zone={"torso", "hands"},
        keyword="antenna",
        tags={"space", "repair"},
    ),
    "collect": Mission(
        id="collect",
        verb="collect the floating bolts",
        gerund="gathering the floating bolts",
        rush="reach for the bolts",
        risk="dust",
        zone={"hands"},
        keyword="bolts",
        tags={"space", "collect"},
    ),
}

OBJECTS = {
    "helmet": Prize(
        label="helmet",
        phrase="a shiny helmet",
        type="helmet",
        region="torso",
    ),
    "suit": Prize(
        label="spacesuit",
        phrase="a thick spacesuit",
        type="suit",
        region="torso",
    ),
    "gloves": Prize(
        label="gloves",
        phrase="clean gloves",
        type="gloves",
        region="hands",
        plural=True,
    ),
}

GEAR = [
    Gear(
        id="magboots",
        label="magnetic boots",
        covers={"feet"},
        guards={"dust"},
        prep="snap on magnetic boots first",
        tail="went back across the hatch in magnetic boots",
        plural=True,
    ),
    Gear(
        id="glove_liner",
        label="a glove liner",
        covers={"hands"},
        guards={"dust"},
        prep="put on a glove liner first",
        tail="climbed back up with the glove liner on",
    ),
    Gear(
        id="visor",
        label="a clear visor",
        covers={"torso"},
        guards={"dust"},
        prep="lower a clear visor first",
        tail="finished the climb with the visor lowered",
    ),
]

HERO_NAMES = ["Nova", "Pip", "Mika", "Rin", "Luna", "Kai", "Orion", "Zia"]
TRAITS = ["brave", "curious", "quick", "gentle", "steady"]


@dataclass
class StoryParams:
    place: str
    mission: str
    prize: str
    name: str
    gender: str
    mentor: str
    trait: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for mission_id in setting.affords:
            mission = MISSIONS[mission_id]
            for prize_id, prize in OBJECTS.items():
                if prize_at_risk(mission, prize_id) and select_gear(mission, prize):
                    combos.append((place, mission_id, prize_id))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Space adventure story world with flashback, bravery, and conflict.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--mission", choices=MISSIONS)
    ap.add_argument("--prize", choices=OBJECTS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--mentor", choices=["captain", "engineer"])
    ap.add_argument("--name")
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
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.mission is None or c[1] == args.mission)
              and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, mission, prize = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    mentor = args.mentor or rng.choice(["captain", "engineer"])
    name = args.name or rng.choice(HERO_NAMES)
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, mission=mission, prize=prize, name=name, gender=gender, mentor=mentor, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], MISSIONS[params.mission], OBJECTS[params.prize],
                 hero_name=params.name, hero_type=params.gender, mentor_type=params.mentor, trait=params.trait)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    mission = f["mission"]
    prize = f["prize"]
    return [
        f'Write a short Space Adventure story about a child named {hero.id} who feels a flashback before {mission.verb}.',
        f"Tell a gentle story where {hero.id} finds bravery after a scary memory and still completes the mission.",
        f'Write a child-friendly space story that includes a tall tower, a conflict, and a brave ending with {prize.label}.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    mentor = f["mentor"]
    mission = f["mission"]
    prize = f["prize"]
    return [
        QAItem(
            question=f"Why did {hero.id} feel worried before {hero.pronoun('subject')} tried to {mission.verb}?",
            answer=f"{hero.id} had a flashback to an older launch day and remembered freezing with fear. That memory made the tall tower and the mission feel harder.",
        ),
        QAItem(
            question=f"How did {mentor.label} help {hero.id} after the flashback?",
            answer=f"{mentor.label.capitalize()} stayed close, spoke gently, and reminded {hero.id} that bravery means doing the hard thing even while feeling scared.",
        ),
        QAItem(
            question=f"What stayed safe while {hero.id} finished {mission.gerund}?",
            answer=f"{prize.label} stayed safe and clean because the right gear was used for the mission.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a launch tower?",
            answer="A launch tower is a tall structure beside a rocket that helps people and machines reach the ship safely.",
        ),
        QAItem(
            question="What does bravery mean?",
            answer="Bravery means doing something hard or scary even when your heart feels nervous.",
        ),
        QAItem(
            question="What is a flashback?",
            answer="A flashback is when a memory from earlier suddenly comes back into your mind.",
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
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.protective:
            bits.append("protective=True")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
prize_at_risk(M, P) :- mission(M), splashes(M, R), prize_region(P, R).
protects(G, M, P) :- gear(G), prize_at_risk(M, P), mission_risk(M, Risk), guards(G, Risk), prize_region(P, R), covers(G, R).
has_fix(M, P) :- protects(_, M, P).
valid(Place, M, P) :- affords(Place, M), prize_at_risk(M, P), has_fix(M, P).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        for m in sorted(s.affords):
            lines.append(asp.fact("affords", pid, m))
    for mid, m in MISSIONS.items():
        lines.append(asp.fact("mission", mid))
        lines.append(asp.fact("mission_risk", mid, m.risk))
        for z in sorted(m.zone):
            lines.append(asp.fact("splashes", mid, z))
    for oid, p in OBJECTS.items():
        lines.append(asp.fact("prize", oid))
        lines.append(asp.fact("prize_region", oid, p.region))
        for g in sorted(p.genders):
            lines.append(asp.fact("wears", g, oid))
    for g in GEAR:
        lines.append(asp.fact("gear", g.id))
        for c in sorted(g.covers):
            lines.append(asp.fact("covers", g.id, c))
        for k in sorted(g.guards):
            lines.append(asp.fact("guards", g.id, k))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


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
    StoryParams(place="launchpad", mission="repair", prize="helmet", name="Nova", gender="girl", mentor="captain", trait="brave"),
    StoryParams(place="station", mission="collect", prize="gloves", name="Kai", gender="boy", mentor="engineer", trait="curious"),
    StoryParams(place="moonbase", mission="repair", prize="suit", name="Zia", gender="girl", mentor="captain", trait="steady"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, mission, prize) combos:\n")
        for c in combos:
            print(" ", c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            params = resolve_params(args, random.Random(base_seed + i))
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
