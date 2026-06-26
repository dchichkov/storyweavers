#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/zone_geology_ist_ale_dialogue_fairy_tale.py
===============================================================================================================

A standalone storyworld for a tiny fairy-tale domain about a geology-ist,
a travel zone, and a careful bottle of ale.

Seed tale:
---
In a bright little kingdom, a young geology-ist loved to wander the old stone
zone beyond the market road. She listened to pebbles, tapped cliffs, and called
the shiny layers by name. One morning, the baker gave her a small bottle of
ale to carry to the hill feast.

The geology-ist wanted to cross the loose-stone path at once, but her aunt
warned that a bouncing walk might crack the bottle. The geology-ist pouted and
said she did not want to take the long way around. Then her aunt smiled, found
a padded wicker basket, and said they could carry the ale safely and still
reach the feast in time.

The geology-ist agreed, tucked the bottle into the basket, and went on
chatting with the aunt about rocks, ridges, and the old zone.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from collections import defaultdict
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
    carried_by: Optional[str] = None
    region: str = ""
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "aunt", "queen"}
        male = {"boy", "man", "father", "uncle", "king"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Zone:
    id: str
    label: str
    roughness: str
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

    def carried_items(self, actor: Entity) -> list[Entity]:
        return [e for e in self.entities.values() if e.carried_by == actor.id]

    def covered(self, actor: Entity, region: str) -> bool:
        return any(g.protective and region in g.covers for g in self.carried_items(actor))

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
        clone = World(self.zone)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


def _r_spill(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        for mess in ("bumped",):
            if actor.meters[mess] < THRESHOLD:
                continue
            for item in world.carried_items(actor):
                if item.protective or item.region not in actor.memes.get("at_risk_regions", set()):
                    continue
                if world.covered(actor, item.region):
                    continue
                sig = ("spill", actor.id, item.id)
                if sig in world.fired:
                    continue
                world.fired.add(sig)
                item.meters["broken"] += 1
                item.meters["spilled"] += 1
                out.append(f"{actor.pronoun('possessive').capitalize()} {item.label} slipped and spilled.")
    return out


def _r_worry(world: World) -> list[str]:
    out: list[str] = []
    for item in world.entities.values():
        if item.meters["spilled"] < THRESHOLD or not item.caretaker:
            continue
        sig = ("worry", item.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        caretaker = world.get(item.caretaker)
        caretaker.meters["workload"] += 1
        out.append(f"That would mean more work for {caretaker.label}.")
    return out


def _r_conflict(world: World) -> list[str]:
    for actor in world.characters():
        if actor.memes["defiance"] < THRESHOLD or actor.memes["touched_by_warning"] < THRESHOLD:
            continue
        sig = ("conflict", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["conflict"] += 1
        return ["__conflict__"]
    return []


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in (_r_spill, _r_worry, _r_conflict):
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if s != "__conflict__")
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def prize_at_risk(activity: Activity, prize: Prize) -> bool:
    return prize.region in activity.zone


def select_gear(activity: Activity, prize: Prize) -> Optional[Gear]:
    for gear in GEAR:
        if activity.mess in gear.guards and prize.region in gear.covers:
            return gear
    return None


def predict_mess(world: World, actor: Entity, activity: Activity, prize_id: str) -> dict:
    sim = world.copy()
    do_activity(sim, sim.get(actor.id), activity, narrate=False)
    prize = sim.entities.get(prize_id)
    return {
        "spilled": bool(prize and prize.meters["spilled"] >= THRESHOLD),
        "workload": sum(e.meters["workload"] for e in sim.characters()),
    }


def do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    if activity.id not in world.zone.affords:
        raise StoryError(f"(No story: {world.zone.label} does not support {activity.verb}.)")
    actor.meters["bumped"] += 1
    actor.memes["joy"] += 1
    actor.memes["at_risk_regions"] = set(activity.zone)
    propagate(world, narrate=narrate)


def introduce(world: World, hero: Entity) -> None:
    trait = next((t for t in hero.memes.get("traits", []) if t != "little"), "curious")
    world.say(f"{hero.id} was a little {trait} geology-ist who loved the old stories hidden in stone.")


def loves_zone(world: World, hero: Entity, zone: Zone, activity: Activity) -> None:
    hero.memes["love_zone"] += 1
    world.say(f"{hero.pronoun().capitalize()} loved the {zone.label}, and {activity.gerund} there felt like listening to the earth talk.")


def gifts_ale(world: World, giver: Entity, hero: Entity, prize: Entity) -> None:
    prize.carried_by = hero.id
    world.say(f"One morning, {giver.label} gave {hero.id} {hero.pronoun('object')} {prize.phrase} for the feast.")


def wants(world: World, hero: Entity, prize: Entity, activity: Activity) -> None:
    hero.memes["desire"] += 1
    world.say(f"{hero.id} wanted to {activity.verb} at once, but {hero.pronoun('possessive')} hands were full of {prize.label}.")


def warn(world: World, aunt: Entity, hero: Entity, activity: Activity, prize: Entity) -> bool:
    pred = predict_mess(world, hero, activity, prize.id)
    if not pred["spilled"]:
        return False
    world.facts["predicted_workload"] = pred["workload"]
    clause = f"You'll spill your {prize.label}"
    if pred["workload"] >= THRESHOLD:
        clause += ", and then there will be a mess to clean"
    world.say(f'"{clause}," {aunt.label} said. "Let us choose a safer way."')
    return True


def defies(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["defiance"] += 1
    world.say(f"{hero.id} frowned and said, \"But I want to go now!\"")
    world.say(f"Then {hero.pronoun().capitalize()} tried to {activity.rush}.")


def touch_warning(world: World, aunt: Entity, hero: Entity) -> None:
    hero.memes["touched_by_warning"] += 1
    world.say(f"{aunt.label} gently took {hero.pronoun('object')} by the elbow and said, \"Easy now.\"")


def compromise(world: World, aunt: Entity, hero: Entity, activity: Activity, prize: Entity) -> Optional[Gear]:
    gear_def = select_gear(activity, prize)
    if gear_def is None:
        return None
    gear = world.add(Entity(
        id=gear_def.id,
        type="gear",
        label=gear_def.label,
        owner=hero.id,
        caretaker=aunt.id,
        protective=True,
        covers=set(gear_def.covers),
        plural=gear_def.plural,
    ))
    gear.carried_by = hero.id
    if predict_mess(world, hero, activity, prize.id)["spilled"]:
        del world.entities[gear.id]
        return None
    world.say(f"Then {aunt.label} smiled and said, \"How about we {gear_def.prep}?\"")
    return gear_def


def accept(world: World, aunt: Entity, hero: Entity, activity: Activity, prize: Entity, gear_def: Gear) -> None:
    hero.memes["joy"] += 1
    hero.memes["love"] += 1
    hero.memes["conflict"] = 0.0
    world.say(f"{hero.id}'s face brightened. \"Yes, aunt!\" {hero.pronoun()} said, and {hero.pronoun('object')} hugged {aunt.label}.")
    world.say(f"They {gear_def.tail}. Soon {hero.id} was {activity.gerund}, while {prize.label} stayed safe and sound.")


def tell(zone: Zone, activity: Activity, prize_cfg: Prize, hero_name: str = "Mira",
         hero_type: str = "girl", hero_trait: str = "curious", aunt_type: str = "aunt") -> World:
    world = World(zone)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type))
    hero.memes["traits"] = ["little", hero_trait]
    aunt = world.add(Entity(id="Aunt", kind="character", type=aunt_type, label="aunt Elin"))
    prize = world.add(Entity(
        id="prize",
        type=prize_cfg.type,
        label=prize_cfg.label,
        phrase=prize_cfg.phrase,
        owner=hero.id,
        caretaker=aunt.id,
        region=prize_cfg.region,
        plural=prize_cfg.plural,
    ))
    introduce(world, hero)
    loves_zone(world, hero, zone, activity)
    gifts_ale(world, aunt, hero, prize)

    world.para()
    world.say(f"On the way to the hill, the path entered the {zone.label}.")
    wants(world, hero, prize, activity)
    warn(world, aunt, hero, activity, prize)
    defies(world, hero, activity)
    touch_warning(world, aunt, hero)

    world.para()
    gear_def = compromise(world, aunt, hero, activity, prize)
    if gear_def:
        accept(world, aunt, hero, activity, prize, gear_def)

    world.facts.update(
        hero=hero,
        aunt=aunt,
        prize=prize,
        activity=activity,
        zone=zone,
        gear=gear_def,
        conflict=hero.memes["touched_by_warning"] >= THRESHOLD,
        resolved=gear_def is not None,
        trait=hero_trait,
    )
    return world


ZONES = {
    "stone_zone": Zone(id="stone_zone", label="the old stone zone", roughness="bumpy", affords={"carry_ale"}),
    "hill_zone": Zone(id="hill_zone", label="the hill zone", roughness="rocky", affords={"carry_ale"}),
    "cave_zone": Zone(id="cave_zone", label="the cave zone", roughness="slippery", affords={"carry_ale"}),
}

ACTIVITIES = {
    "carry_ale": Activity(
        id="carry_ale",
        verb="carry the ale to the feast",
        gerund="carrying the ale to the feast",
        rush="dash along the stone path",
        mess="bumped",
        soil="spilled",
        zone={"hands"},
        keyword="ale",
        tags={"ale", "zone", "geology"},
    ),
}

PRIZES = {
    "ale": Prize(
        label="ale",
        phrase="a small bottle of ale",
        type="ale",
        region="hands",
    ),
}

GEAR = [
    Gear(
        id="basket",
        label="a padded wicker basket",
        covers={"hands"},
        guards={"bumped"},
        prep="take a padded wicker basket and set the bottle inside",
        tail="walked on with the bottle cushioned safely in the basket",
    ),
    Gear(
        id="cloth_wrap",
        label="a soft cloth wrap",
        covers={"hands"},
        guards={"bumped"},
        prep="wrap the bottle in soft cloth first",
        tail="continued with the bottle wrapped snug and safe",
    ),
]

GIRL_NAMES = ["Mira", "Tessa", "Ayla", "Lena", "Rowan", "Nora"]
BOY_NAMES = ["Galen", "Pip", "Eli", "Bram", "Tobin", "Milo"]
TRAITS = ["curious", "brave", "gentle", "cheerful", "stubborn"]


@dataclass
class StoryParams:
    zone: str
    activity: str
    prize: str
    name: str
    gender: str
    trait: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for zid, zone in ZONES.items():
        for aid in zone.affords:
            act = ACTIVITIES[aid]
            for pid, prize in PRIZES.items():
                if prize_at_risk(act, prize) and select_gear(act, prize):
                    combos.append((zid, aid, pid))
    return combos


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, act, prize = f["hero"], f["activity"], f["prize"]
    return [
        f'Write a fairy tale about a little geology-ist named {hero.id} who must carry {prize.phrase} through {world.zone.label}.',
        f"Tell a short dialogue story where {hero.id} wants to {act.verb} but an aunt worries about the ale.",
        f'Write a child-friendly fairy tale that includes the word "zone" and ends with a safe way to carry ale.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, aunt, prize, act = f["hero"], f["aunt"], f["prize"], f["activity"]
    trait = f["trait"]
    qa = [
        QAItem(
            question=f"Who is the story about?",
            answer=f"It is about {hero.id}, a little {trait} geology-ist, and {aunt.label}.",
        ),
        QAItem(
            question=f"What did {hero.id} want to do in the zone?",
            answer=f"{hero.id} wanted to {act.verb} while carrying {prize.phrase}.",
        ),
        QAItem(
            question=f"Why did {aunt.label} worry?",
            answer=f"{aunt.label} worried that the bumpy path through {world.zone.label} would make the ale spill.",
        ),
    ]
    if f.get("resolved"):
        qa.append(QAItem(
            question="How did they keep the ale safe?",
            answer=f"They put the bottle in {f['gear'].label} so {hero.id} could go on safely.",
        ))
        qa.append(QAItem(
            question=f"How did {hero.id} feel at the end?",
            answer=f"{hero.id} felt happy and went on chatting about rocks while the ale stayed safe.",
        ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is geology?",
            answer="Geology is the study of rocks, stones, soil, and the shapes of the land.",
        ),
        QAItem(
            question="What is a zone?",
            answer="A zone is a part of a place, like one area of a path, cave, or hill.",
        ),
        QAItem(
            question="What is ale?",
            answer="Ale is a brewed drink made from grains, often served in a village hall or feast.",
        ),
    ]


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


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v and k != "traits"}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.protective:
            bits.append(f"covers={sorted(e.covers)}")
        elif e.region:
            bits.append(f"region={e.region}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


CURATED = [
    StoryParams(zone="stone_zone", activity="carry_ale", prize="ale", name="Mira", gender="girl", trait="curious"),
    StoryParams(zone="hill_zone", activity="carry_ale", prize="ale", name="Galen", gender="boy", trait="brave"),
]


def explain_rejection(activity: Activity, prize: Prize) -> str:
    if not prize_at_risk(activity, prize):
        return "(No story: the ale is not actually at risk on that path.)"
    if not select_gear(activity, prize):
        return "(No story: no safe basket or wrap exists for this ale.)"
    return "(No story: the requested options do not make a reasonable fairy-tale conflict.)"


ASP_RULES = r"""
prize_at_risk(A, P) :- bumps(A, R), worn_on(P, R).
protects(G, A, P) :- prize_at_risk(A, P), guards(G, M), mess_of(A, M), covers(G, R), worn_on(P, R).
has_fix(A, P) :- protects(_, A, P).
valid(Z, A, P) :- affords(Z, A), prize_at_risk(A, P), has_fix(A, P).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for zid, z in ZONES.items():
        lines.append(asp.fact("zone", zid))
        for a in sorted(z.affords):
            lines.append(asp.fact("affords", zid, a))
    for aid, a in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        lines.append(asp.fact("mess_of", aid, a.mess))
        for r in sorted(a.zone):
            lines.append(asp.fact("bumps", aid, r))
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A fairy-tale story world about a geology-ist and a safe bottle of ale.")
    ap.add_argument("--zone", choices=ZONES)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
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
    combos = [c for c in valid_combos()
              if (args.zone is None or c[0] == args.zone)
              and (args.activity is None or c[1] == args.activity)
              and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    zone, activity, prize = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(zone=zone, activity=activity, prize=prize, name=name, gender=gender, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(ZONES[params.zone], ACTIVITIES[params.activity], PRIZES[params.prize],
                 hero_name=params.name, hero_type=params.gender, hero_trait=params.trait)
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
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (zone, activity, prize) combos:\n")
        for z, a, p in combos:
            print(f"  {z:12} {a:12} {p}")
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
        header = f"### variant {i + 1}" if len(samples) > 1 and not args.all else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
