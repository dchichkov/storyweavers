#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/contour_cautionary_superhero_story.py
===============================================================================================

A small cautionary superhero storyworld built from the seed word "contour".

Premise:
- A young superhero wants to dash, dive, or soar near a risky contour in the city.
- A mentor foresees a problem: a cape, mask, or rescue kit could be ruined.
- The story turns on a warning, a moment of defiance, and a safer heroic compromise.

The simulated world tracks both physical state ("meters") and emotional state
("memes") so the prose is driven by actual causal changes rather than a frozen
template.
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
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    region: str = ""
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for k in ["wind", "rain", "dust", "damage", "workload"]:
            self.meters.setdefault(k, 0.0)
        for k in ["joy", "love", "worry", "defiance", "conflict", "caution", "bravery"]:
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "aunt"}
        male = {"boy", "man", "father", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Zone:
    place: str = "the city"
    outdoors: bool = True
    affords: set[str] = field(default_factory=set)


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    mess: str
    soil: str
    zone: set[str]
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    label: str
    phrase: str
    type: str
    region: str
    plural: bool = False
    genders: set[str] = field(default_factory=lambda: {"girl", "boy"})


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
    def __init__(self, zone: Zone) -> None:
        self.zone = zone
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

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
        return any(e.protective and region in e.covers for e in self.worn_items(actor))

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        import copy as _copy
        clone = World(self.zone)
        clone.entities = _copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


def _r_blowback(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters["wind"] < THRESHOLD:
            continue
        for item in world.worn_items(actor):
            if item.protective or item.region not in world.zone.affords:
                continue
            if world.covered(actor, item.region):
                continue
            sig = ("blowback", actor.id, item.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            item.meters["damage"] += 1
            actor.memes["worry"] += 1
            out.append(f"The wind tugged at {actor.pronoun('possessive')} {item.label}.")
    return out


def _r_workload(world: World) -> list[str]:
    out: list[str] = []
    for item in world.entities.values():
        if item.meters["damage"] < THRESHOLD or not item.caretaker:
            continue
        sig = ("workload", item.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        carer = world.get(item.caretaker)
        carer.meters["workload"] += 1
        out.append(f"That would mean more work for {carer.label}.")
    return out


def _r_conflict(world: World) -> list[str]:
    for actor in world.characters():
        if actor.memes["defiance"] < THRESHOLD or actor.memes["worry"] < THRESHOLD:
            continue
        sig = ("conflict", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["conflict"] += 1
        return ["__conflict__"]
    return []


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in (_r_blowback, _r_workload, _r_conflict):
            sents = rule(world)
            if sents:
                changed = True
                out.extend(s for s in sents if s != "__conflict__")
    if narrate:
        for s in out:
            world.say(s)
    return out


def activity_at_risk(activity: Activity, prize: Prize) -> bool:
    return prize.region in activity.zone


def select_gear(activity: Activity, prize: Prize) -> Optional[Gear]:
    for gear in GEAR:
        if activity.mess in gear.guards and prize.region in gear.covers:
            return gear
    return None


def predict_mess(world: World, actor: Entity, activity: Activity, prize_id: str) -> dict:
    sim = world.copy()
    _do_activity(sim, sim.get(actor.id), activity, narrate=False)
    prize = sim.entities[prize_id]
    return {"damaged": prize.meters["damage"] >= THRESHOLD,
            "workload": sum(e.meters["workload"] for e in sim.characters())}


def _do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    if activity.id not in world.zone.affords:
        raise StoryError("The chosen setting cannot support that heroic move.")
    actor.meters[activity.mess] += 1
    actor.memes["bravery"] += 1
    world.say(f"{actor.id} {activity.gerund}.")
    propagate(world, narrate=narrate)


def introduce(world: World, hero: Entity) -> None:
    trait = next((t for t in hero.traits if t != "young"), "brave")
    world.say(f"{hero.id} was a young, {trait} superhero who watched every rooftop and street corner.")


def love(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["love"] += 1
    world.say(f"{hero.pronoun().capitalize()} loved to {activity.verb}, because the city felt like a map of secrets.")


def acquire(world: World, mentor: Entity, hero: Entity, prize: Entity) -> None:
    world.say(f"One bright day, {hero.id}'s {mentor.label} gave {hero.pronoun('object')} {prize.phrase}.")
    prize.worn_by = hero.id


def cherish(world: World, hero: Entity, prize: Entity) -> None:
    hero.memes["joy"] += 1
    world.say(f"{hero.id} loved {hero.pronoun('possessive')} {prize.label} and wore {prize.it()} like a badge.")


def arrive(world: World, hero: Entity, mentor: Entity, activity: Activity) -> None:
    world.say(f"One breezy afternoon, {hero.id} and {hero.pronoun('possessive')} {mentor.label} went to {world.zone.place}.")
    world.say(f"Along the far contour of the city, the clouds looked restless.")


def wants(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["caution"] += 1
    world.say(f"{hero.id} wanted to {activity.verb} right away, even though the contour looked risky.")


def warn(world: World, mentor: Entity, hero: Entity, activity: Activity, prize: Entity) -> bool:
    pred = predict_mess(world, hero, activity, prize.id)
    if not pred["damaged"]:
        return False
    clause = f"You'll damage your {prize.label}"
    if pred["workload"] >= THRESHOLD:
        clause += ", and then I'll have to fix it"
    world.say(f'"{clause}," {mentor.label} said. "That contour is not for careless flying."')
    world.facts["predicted_damage"] = activity.soil
    return True


def defies(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["defiance"] += 1
    world.say(f"{hero.id} still felt the pull of adventure and tried to {activity.rush}.")


def grab_and_conflict(world: World, mentor: Entity, hero: Entity) -> None:
    hero.memes["worry"] += 1
    propagate(world, narrate=False)
    world.say(f"But {hero.pronoun('possessive')} {mentor.label} caught {hero.pronoun('possessive')} sleeve and held on.")
    world.say(f'"We can be brave without being reckless," {mentor.label} said.')


def compromise(world: World, mentor: Entity, hero: Entity, activity: Activity, prize: Entity) -> Optional[Gear]:
    gear_def = select_gear(activity, prize)
    if gear_def is None:
        return None
    gear = world.add(Entity(
        id=gear_def.id,
        type="gear",
        label=gear_def.label,
        owner=hero.id,
        caretaker=mentor.id,
        protective=True,
        covers=set(gear_def.covers),
        plural=gear_def.plural,
    ))
    gear.worn_by = hero.id
    if predict_mess(world, hero, activity, prize.id)["damaged"]:
        gear.worn_by = None
        del world.entities[gear.id]
        return None
    world.say(f'{hero.id} nodded. "{gear_def.prep}," {mentor.label} said, and the plan sounded wise.')
    return gear_def


def resolve(world: World, hero: Entity, mentor: Entity, activity: Activity, prize: Entity, gear_def: Gear) -> None:
    hero.memes["joy"] += 1
    hero.memes["love"] += 1
    hero.memes["conflict"] = 0.0
    world.say(f"{hero.id} smiled, hugged {hero.pronoun('possessive')} {mentor.label}, and promised to be careful.")
    world.say(f"Together they {gear_def.tail}. Soon {hero.id} was {activity.gerund}, while {prize.label} stayed safe.")


def tell(zone: Zone, activity: Activity, prize_cfg: Prize, hero_name: str, hero_type: str,
         hero_traits: Optional[list[str]] = None, mentor_type: str = "woman") -> World:
    world = World(zone)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, traits=["young"] + (hero_traits or ["bold", "kind"])))
    mentor = world.add(Entity(id="Mentor", kind="character", type=mentor_type, label="the mentor"))
    prize = world.add(Entity(id="prize", type=prize_cfg.type, label=prize_cfg.label, phrase=prize_cfg.phrase,
                             owner=hero.id, caretaker=mentor.id, region=prize_cfg.region, plural=prize_cfg.plural))

    introduce(world, hero)
    love(world, hero, activity)
    acquire(world, mentor, hero, prize)
    cherish(world, hero, prize)

    world.para()
    arrive(world, hero, mentor, activity)
    wants(world, hero, activity)
    warn(world, mentor, hero, activity, prize)
    defies(world, hero, activity)
    grab_and_conflict(world, mentor, hero)

    world.para()
    gear_def = compromise(world, mentor, hero, activity, prize)
    if gear_def:
        resolve(world, hero, mentor, activity, prize, gear_def)

    world.facts.update(hero=hero, mentor=mentor, prize=prize, activity=activity, zone=zone, gear=gear_def,
                       conflict=hero.memes["worry"] >= THRESHOLD, resolved=gear_def is not None)
    return world


SETTINGS = {
    "rooftops": Zone(place="the rooftops", outdoors=True, affords={"windline", "stormedge"}),
    "bridge": Zone(place="the bridge", outdoors=True, affords={"windline"}),
    "harbor": Zone(place="the harbor", outdoors=True, affords={"stormedge"}),
}

ACTIVITIES = {
    "windline": Activity(
        id="windline",
        verb="fly along the contour line",
        gerund="gliding along the contour line",
        rush="zip too close to the edge",
        mess="wind",
        soil="ruffled and scuffed",
        zone={"torso"},
        keyword="contour",
        tags={"contour", "wind"},
    ),
    "stormedge": Activity(
        id="stormedge",
        verb="dash toward the storm contour",
        gerund="darting near the storm contour",
        rush="race toward the thundercloud edge",
        mess="rain",
        soil="soaked and storm-tossed",
        zone={"torso"},
        keyword="contour",
        tags={"contour", "storm", "rain"},
    ),
}

PRIZES = {
    "cape": Prize(
        label="cape",
        phrase="a bright red cape",
        type="cape",
        region="torso",
    ),
    "mask": Prize(
        label="mask",
        phrase="a shiny blue mask",
        type="mask",
        region="face",
    ),
    "utilitybelt": Prize(
        label="utility belt",
        phrase="a useful utility belt",
        type="belt",
        region="torso",
    ),
}

GEAR = [
    Gear(
        id="harness",
        label="a safety harness",
        covers={"torso"},
        guards={"wind", "rain"},
        prep="put on a safety harness first",
        tail="flew back along the contour with the harness snug and secure",
    ),
    Gear(
        id="goggles",
        label="wind goggles",
        covers={"face"},
        guards={"wind", "rain"},
        prep="pull on wind goggles first",
        tail="came home with the wind goggles still clean and tight",
    ),
    Gear(
        id="rainhood",
        label="a rain hood",
        covers={"face", "torso"},
        guards={"rain"},
        prep="wear a rain hood before going out",
        tail="moved through the storm edge with the rain hood keeping the trouble away",
    ),
]

HERO_NAMES = ["Nova", "Piper", "Sky", "Juno", "Milo", "Aria", "Zane", "Mina"]
TRAITS = ["bright", "curious", "steady", "bold", "quick", "careful"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, zone in SETTINGS.items():
        for act_id in zone.affords:
            act = ACTIVITIES[act_id]
            for prize_id, prize in PRIZES.items():
                if activity_at_risk(act, prize) and select_gear(act, prize):
                    combos.append((place, act_id, prize_id))
    return combos


@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    name: str
    gender: str
    mentor: str
    trait: str
    seed: Optional[int] = None


KNOWLEDGE = {
    "contour": [("What is a contour?", "A contour is a line that shows the shape or edge of something, like a hill or a map."),],
    "wind": [("What does wind do?", "Wind is moving air. It can push leaves, hats, and capes around."),],
    "rain": [("Where does rain come from?", "Rain falls from clouds when tiny water drops get heavy enough."),],
    "cape": [("What is a cape for?", "A cape is a superhero cloth that can flap behind someone, so it is fun but can get in the way."),],
    "mask": [("Why do superheroes wear masks?", "A mask can help hide a superhero's face and give them a secret identity."),],
    "harness": [("What does a safety harness do?", "A safety harness helps keep someone secure when they are climbing or flying."),],
}


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, mentor, act, prize = f["hero"], f["mentor"], f["activity"], f["prize"]
    return [
        f'Write a short cautionary superhero story for a child that includes the word "{act.keyword}" and a safe choice.',
        f"Tell a superhero story where {hero.id} wants to {act.verb} but {hero.pronoun('possessive')} {mentor.label} worries about {hero.pronoun('possessive')} {prize.label}.",
        f"Make a gentle superhero adventure about a risky contour, a warning, and a smarter way to help.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, mentor, prize, act = f["hero"], f["mentor"], f["prize"], f["activity"]
    qa = [
        QAItem(
            question=f"Who is the story about when {hero.id} goes near the contour?",
            answer=f"It is about {hero.id}, a young superhero, and {hero.pronoun('possessive')} {mentor.label}.",
        ),
        QAItem(
            question=f"What did {hero.id} want to do at {world.zone.place}?",
            answer=f"{hero.id} wanted to {act.verb}, even though the contour looked risky.",
        ),
        QAItem(
            question=f"Why did {mentor.label} worry about {hero.pronoun('possessive')} {prize.label}?",
            answer=f"{mentor.label} worried because the wind and rain could damage {hero.pronoun('possessive')} {prize.label}.",
        ),
    ]
    if f.get("resolved"):
        gear = f["gear"]
        qa.append(QAItem(
            question=f"How did {gear.label} help {hero.id} stay safe?",
            answer=f"{gear.label} helped by protecting the right part of {hero.pronoun('possessive')} costume, so {hero.id} could still help without getting hurt.",
        ))
        qa.append(QAItem(
            question=f"How did {hero.id} feel at the end?",
            answer=f"{hero.id} felt happy and calm after choosing the safer plan with {hero.pronoun('possessive')} {mentor.label}.",
        ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["activity"].tags)
    if world.facts.get("gear"):
        tags.add(world.facts["gear"].id)
    out: list[QAItem] = []
    for tag, pairs in KNOWLEDGE.items():
        if tag in tags:
            out.extend(QAItem(question=q, answer=a) for q, a in pairs)
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
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.protective:
            bits.append(f"covers={sorted(e.covers)}")
        elif e.region:
            bits.append(f"region={e.region}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


def explain_rejection(activity: Activity, prize: Prize) -> str:
    if not activity_at_risk(activity, prize):
        return f"(No story: {activity.gerund} does not endanger a {prize.label} here.)"
    return f"(No story: nothing in the gear set safely covers a {prize.label} for {activity.verb}.)"


CURATED = [
    StoryParams(place="rooftops", activity="windline", prize="cape", name="Nova", gender="girl", mentor="woman", trait="careful"),
    StoryParams(place="rooftops", activity="stormedge", prize="utilitybelt", name="Piper", gender="girl", mentor="woman", trait="bold"),
    StoryParams(place="bridge", activity="windline", prize="mask", name="Zane", gender="boy", mentor="man", trait="steady"),
]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.activity and args.prize:
        act, pr = ACTIVITIES[args.activity], PRIZES[args.prize]
        if not (activity_at_risk(act, pr) and select_gear(act, pr)):
            raise StoryError(explain_rejection(act, pr))
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.activity is None or c[1] == args.activity)
              and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, activity, prize = rng.choice(sorted(combos))
    return StoryParams(
        place=place,
        activity=activity,
        prize=prize,
        name=args.name or rng.choice(HERO_NAMES),
        gender=args.gender or rng.choice(["girl", "boy"]),
        mentor=args.mentor or rng.choice(["woman", "man"]),
        trait=args.trait or rng.choice(TRAITS),
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], ACTIVITIES[params.activity], PRIZES[params.prize],
                 params.name, params.gender, [params.trait, "young"], params.mentor)
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A cautionary superhero storyworld with contour-shaped danger and a safer heroic turn.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--mentor", choices=["woman", "man"])
    ap.add_argument("--name")
    ap.add_argument("--trait")
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


ASP_RULES = r"""
prize_at_risk(A,P) :- splashes(A,R), worn_on(P,R).
protects(G,A,P) :- prize_at_risk(A,P), mess_of(A,M), guards(G,M), covers(G,R), worn_on(P,R).
has_fix(A,P) :- protects(_,A,P).
valid(Place,A,P) :- affords(Place,A), prize_at_risk(A,P), has_fix(A,P).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, z in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        if z.outdoors:
            lines.append(asp.fact("outdoors", pid))
        for a in sorted(z.affords):
            lines.append(asp.fact("affords", pid, a))
    for aid, a in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        lines.append(asp.fact("mess_of", aid, a.mess))
        for r in sorted(a.zone):
            lines.append(asp.fact("splashes", aid, r))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("worn_on", pid, p.region))
    for g in GEAR:
        lines.append(asp.fact("gear", g.id))
        for m in sorted(g.guards):
            lines.append(asp.fact("guards", g.id, m))
        for r in sorted(g.covers):
            lines.append(asp.fact("covers", g.id, r))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    clingo_set, python_set = set(asp_valid_combos()), set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())

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
            header = f"### {p.name}: {p.activity} at {p.place} (prize: {p.prize})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
