#!/usr/bin/env python3
"""
storyworlds/worlds/pivot_mask_foreshadowing_lesson_learned_slice_of.py
======================================================================

A small slice-of-life story world about a child, a mask, and a gentle pivot
from one plan to a better one.

Premise:
- A child loves a special mask.
- A short outing or playtime could send that mask flying, bending, or tearing.
- A parent notices the warning signs early and suggests a simple fix.
- The child learns that a good pivot can save the day.

This world is intentionally compact and state-driven: the story is built from
typed entities, physical meters, and emotional memes, with a light foreshadowing
beat and a lesson-learned resolution.
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
        for k in ["wear", "risk", "fray", "dirty", "workload"]:
            self.meters.setdefault(k, 0.0)
        for k in ["joy", "worry", "desire", "relief", "confidence", "lesson"]:
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
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
    indoor: bool = False
    affords: set[str] = field(default_factory=set)


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    risk: str
    zone: set[str]
    weather: str
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
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.zone: set[str] = set()
        self.weather: str = ""
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
        return any(g.protective and region in g.covers for g in self.worn_items(actor))

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
        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.zone = set(self.zone)
        clone.weather = self.weather
        clone.paragraphs = [[]]
        return clone


def prize_at_risk(activity: Activity, prize: Prize) -> bool:
    return prize.region in activity.zone


def select_gear(activity: Activity, prize: Prize) -> Optional[Gear]:
    for gear in GEAR:
        if prize.region in gear.covers and activity.risk in gear.guards:
            return gear
    return None


def _do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    if activity.id not in world.setting.affords:
        raise StoryError(f"Activity {activity.id} does not fit setting {world.setting.place}.")
    world.zone = set(activity.zone)
    actor.meters["risk"] += 1
    actor.memes["joy"] += 1
    if narrate:
        world.say(f"{actor.id} did {activity.gerund}.")
    propagate(world, narrate=narrate)


def _r_risk(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters["risk"] < THRESHOLD:
            continue
        for item in world.worn_items(actor):
            if item.protective or item.region not in world.zone:
                continue
            if world.covered(actor, item.region):
                continue
            sig = ("risk", actor.id, item.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            item.meters["fray"] += 1
            item.meters["dirty"] += 1
            out.append(f"{actor.pronoun('possessive').capitalize()} {item.label} began to fray.")
    return out


def _r_worry(world: World) -> list[str]:
    out: list[str] = []
    for item in world.entities.values():
        if item.meters["dirty"] < THRESHOLD or not item.caretaker:
            continue
        sig = ("worry", item.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        carer = world.get(item.caretaker)
        carer.memes["worry"] += 1
        carer.meters["workload"] += 1
        out.append(f"That would mean more work for {carer.label}.")
    return out


CAUSAL_RULES = [
    _r_risk,
    _r_worry,
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
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def predict_mess(world: World, actor: Entity, activity: Activity, prize_id: str) -> dict:
    sim = world.copy()
    _do_activity(sim, sim.get(actor.id), activity, narrate=False)
    prize = sim.entities.get(prize_id)
    return {
        "ruined": bool(prize and prize.meters["dirty"] >= THRESHOLD),
        "workload": sum(e.meters["workload"] for e in sim.characters()),
    }


def introduce(world: World, hero: Entity) -> None:
    trait = next((t for t in hero.traits if t != "little"), "curious")
    world.say(f"{hero.id} was a little {trait} {hero.type} who loved quiet, ordinary days.")


def loves_mask(world: World, hero: Entity, mask: Entity) -> None:
    hero.memes["desire"] += 1
    mask.worn_by = hero.id
    world.say(
        f"{hero.id} loved {hero.pronoun('possessive')} {mask.label} and wore {mask.it()} with care."
    )


def foreshadow(world: World, hero: Entity, mask: Entity, activity: Activity) -> None:
    world.say(
        f"Before they left, {hero.pronoun('possessive')} {mask.label} string looked a little loose, "
        f"and {hero.id} noticed it but did not think much of it."
    )
    if activity.weather:
        world.say(
            f"The air was {activity.weather}, which made the loose string flutter now and then."
        )


def arrive(world: World, hero: Entity, parent: Entity, activity: Activity) -> None:
    day = {"breezy": "One breezy day, ", "sunny": "One sunny day, ", "gray": "One gray day, "}.get(
        activity.weather, "One day, "
    )
    world.say(
        f"{day}{hero.id} and {hero.pronoun('possessive')} {parent.pronoun('possessive')} parent went to {world.setting.place}."
    )
    world.say(
        f"{world.setting.place.capitalize()} felt calm, but the {activity.keyword} breeze kept tugging at small things."
    )


def wants(world: World, hero: Entity, parent: Entity, activity: Activity) -> None:
    world.say(
        f"{hero.id} wanted to {activity.verb}, and {hero.pronoun('possessive')} feet kept pivoting with excitement."
    )


def warn(world: World, parent: Entity, hero: Entity, activity: Activity, prize: Entity) -> bool:
    pred = predict_mess(world, hero, activity, prize.id)
    if not pred["ruined"]:
        return False
    world.facts["predicted_workload"] = pred["workload"]
    world.facts["warning"] = True
    world.say(
        f'"If you {activity.verb}, your {prize.label} could slip out of place," {parent.label or parent.type} said.'
    )
    return True


def pivot(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["confidence"] += 1
    world.say(
        f"{hero.id} paused, took a little pivot, and looked at the plan from another side."
    )


def offer_fix(world: World, parent: Entity, hero: Entity, activity: Activity, prize: Entity) -> Optional[Gear]:
    gear_def = select_gear(activity, prize)
    if gear_def is None:
        return None
    gear = world.add(Entity(
        id=gear_def.id,
        type="gear",
        label=gear_def.label,
        owner=hero.id,
        caretaker=parent.id,
        protective=True,
        covers=set(gear_def.covers),
        plural=gear_def.plural,
    ))
    gear.worn_by = hero.id
    if predict_mess(world, hero, activity, prize.id)["ruined"]:
        gear.worn_by = None
        del world.entities[gear.id]
        return None
    world.say(
        f'{parent.label or parent.type} smiled. "How about we {gear_def.prep}?"'
    )
    return gear


def accept(world: World, parent: Entity, hero: Entity, activity: Activity, prize: Entity, gear_def: Gear) -> None:
    hero.memes["joy"] += 1
    hero.memes["relief"] += 1
    hero.memes["lesson"] += 1
    world.say(
        f"{hero.id} nodded, slipped on {gear_def.label}, and felt the worry leave {hero.pronoun('possessive')} shoulders."
    )
    world.say(
        f"Then {hero.id} went back to {activity.gerund}, and {prize.label} stayed neat the whole time."
    )
    world.say(
        f"That was the lesson learned: sometimes a small pivot makes the day work better."
    )


def tell(
    setting: Setting,
    activity: Activity,
    prize_cfg: Prize,
    hero_name: str = "Mina",
    hero_type: str = "girl",
    hero_traits: Optional[list[str]] = None,
    parent_type: str = "mother",
) -> World:
    world = World(setting)
    world.weather = activity.weather

    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type=hero_type,
        traits=["little"] + (hero_traits or ["careful", "bright"]),
    ))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label="mom" if parent_type == "mother" else "dad"))
    prize = world.add(Entity(
        id="mask",
        type=prize_cfg.type,
        label=prize_cfg.label,
        phrase=prize_cfg.phrase,
        owner=hero.id,
        caretaker=parent.id,
        region=prize_cfg.region,
        plural=prize_cfg.plural,
    ))

    introduce(world, hero)
    loves_mask(world, hero, prize)
    foreshadow(world, hero, prize, activity)

    world.para()
    arrive(world, hero, parent, activity)
    wants(world, hero, parent, activity)
    warn(world, parent, hero, activity, prize)
    pivot(world, hero, activity)

    world.para()
    gear_def = offer_fix(world, parent, hero, activity, prize)
    if gear_def:
        accept(world, parent, hero, activity, prize, gear_def)

    world.facts.update(
        hero=hero,
        parent=parent,
        prize=prize,
        prize_cfg=prize_cfg,
        activity=activity,
        setting=setting,
        gear=gear_def,
        resolved=gear_def is not None,
    )
    return world


SETTINGS = {
    "front_yard": Setting(place="the front yard", indoor=False, affords={"kite_walk", "scooter"}),
    "sidewalk": Setting(place="the sidewalk", indoor=False, affords={"kite_walk", "scooter"}),
    "porch": Setting(place="the porch", indoor=True, affords={"craft"}),
}

ACTIVITIES = {
    "kite_walk": Activity(
        id="kite_walk",
        verb="walk with a kite",
        gerund="walking with a kite",
        rush="dash after the kite",
        risk="wind",
        zone={"head"},
        weather="breezy",
        keyword="wind",
        tags={"wind", "breezy"},
    ),
    "scooter": Activity(
        id="scooter",
        verb="ride the scooter",
        gerund="riding the scooter",
        rush="push fast down the sidewalk",
        risk="breeze",
        zone={"head"},
        weather="breezy",
        keyword="breeze",
        tags={"wind", "motion"},
    ),
    "craft": Activity(
        id="craft",
        verb="make a little sign",
        gerund="making a little sign",
        rush="grab the markers",
        risk="glue",
        zone={"head"},
        weather="gray",
        keyword="glue",
        tags={"quiet", "craft"},
    ),
}

PRIZES = {
    "mask": Prize(
        label="mask",
        phrase="a bright paper mask with a blue ribbon",
        type="mask",
        region="head",
    ),
    "cap": Prize(
        label="cap",
        phrase="a favorite soft cap",
        type="cap",
        region="head",
    ),
}

GEAR = [
    Gear(
        id="mask_clip",
        label="a snug mask clip",
        covers={"head"},
        guards={"wind", "breeze"},
        prep="clip the ribbon tighter",
        tail="kept the mask snug",
    ),
    Gear(
        id="hair_band",
        label="a stretchy hair band",
        covers={"head"},
        guards={"wind", "breeze"},
        prep="use a stretchy hair band under the ribbon",
        tail="held the mask steady",
    ),
    Gear(
        id="visor",
        label="a clear visor",
        covers={"head"},
        guards={"glue"},
        prep="wear the clear visor over the craft table",
        tail="kept the craft neat",
    ),
]

GIRL_NAMES = ["Mina", "June", "Lena", "Ivy", "Nora", "Sia", "Ruby", "Tess"]
BOY_NAMES = ["Owen", "Nico", "Theo", "Jules", "Milo", "Ben", "Ezra", "Ari"]
TRAITS = ["careful", "curious", "bright", "gentle", "quiet", "playful"]


@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            act = ACTIVITIES[act_id]
            for prize_id, prize in PRIZES.items():
                if prize_at_risk(act, prize) and select_gear(act, prize):
                    combos.append((place, act_id, prize_id))
    return combos


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, parent, act, prize = f["hero"], f["parent"], f["activity"], f["prize_cfg"]
    return [
        f'Write a short slice-of-life story for a child named {hero.id} about a mask and a small pivot.',
        f"Tell a gentle story where {hero.id} wants to {act.verb} but {parent.label} worries about {prize.phrase}.",
        f'Write a simple story that includes the words "pivot" and "mask" and ends with a lesson learned.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, parent, prize, act = f["hero"], f["parent"], f["prize"], f["activity"]
    qa = [
        QAItem(
            question=f"What did {hero.id} want to do at {world.setting.place}?",
            answer=f"{hero.id} wanted to {act.verb} at {world.setting.place}.",
        ),
        QAItem(
            question=f"Why did {parent.label} worry about the mask?",
            answer=f"{parent.label} worried because the breeze could make the {prize.label} slip or fray.",
        ),
        QAItem(
            question=f"What changed after the pivot?",
            answer=f"After the pivot, they used a better plan so the {prize.label} stayed safe.",
        ),
    ]
    if f.get("resolved"):
        gear = f["gear"]
        qa.append(
            QAItem(
                question=f"How did {gear.label} help?",
                answer=f"{gear.label} helped keep the {prize.label} snug while {hero.id} kept playing.",
            )
        )
        qa.append(
            QAItem(
                question=f"What lesson did {hero.id} learn?",
                answer="The lesson learned was that a small pivot can turn a problem into a good plan.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a mask?",
            answer="A mask is something you wear on your face or head for play, costume, or protection.",
        ),
        QAItem(
            question="What does pivot mean?",
            answer="To pivot means to turn or change direction, often to make a better choice.",
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
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams("front_yard", "kite_walk", "mask", "Mina", "girl", "mother", "careful"),
    StoryParams("sidewalk", "scooter", "mask", "Owen", "boy", "father", "playful"),
    StoryParams("porch", "craft", "mask", "Lena", "girl", "mother", "gentle"),
]


def explain_rejection(activity: Activity, prize: Prize) -> str:
    if not prize_at_risk(activity, prize):
        return f"(No story: {prize.label} is not actually at risk during {activity.gerund}.)"
    return f"(No story: there is no reasonable gear that keeps the {prize.label} safe during {activity.gerund}.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Slice-of-life story world about a mask, a pivot, and a lesson learned.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
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
    if args.activity and args.prize:
        act, pr = ACTIVITIES[args.activity], PRIZES[args.prize]
        if not (prize_at_risk(act, pr) and select_gear(act, pr)):
            raise StoryError(explain_rejection(act, pr))
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.activity is None or c[1] == args.activity)
              and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, activity, prize = rng.choice(sorted(combos))
    pr = PRIZES[prize]
    gender = args.gender or rng.choice(sorted(pr.genders))
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, activity=activity, prize=prize, name=name, gender=gender, parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], ACTIVITIES[params.activity], PRIZES[params.prize],
                 params.name, params.gender, [params.trait, "steady"], params.parent)
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


ASP_RULES = r"""
prize_at_risk(A,P) :- splashes(A,R), worn_on(P,R).
protects(G,A,P) :- prize_at_risk(A,P), mess_of(A,M), guards(G,M), covers(G,R), worn_on(P,R).
has_fix(A,P) :- protects(_,A,P).
valid(Place,A,P) :- affords(Place,A), prize_at_risk(A,P), has_fix(A,P).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        if s.indoor:
            lines.append(asp.fact("indoor", pid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", pid, a))
    for aid, a in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        lines.append(asp.fact("mess_of", aid, a.risk))
        for r in sorted(a.zone):
            lines.append(asp.fact("splashes", aid, r))
    for pid, pr in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("worn_on", pid, pr.region))
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
    if args.verify:
        sys.exit(asp_verify())
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
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
