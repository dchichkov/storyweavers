#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/jowl_angle_surprise_magic_flashback_folk_tale.py
=============================================================================================================================

A small folk-tale story world about a child, a warning, a surprise, a little
magic, and a remembered path.

The seed image behind this world:
- A child and an elder walk a crooked village road.
- A prized object is in danger if they follow a risky path.
- The elder remembers an old trick from long ago.
- The child discovers a surprising clue near an animal's jowl or at a sharp
  angle in the road.
- A safe magical compromise lets the journey continue.

This script keeps the domain compact and constraint-checked, while still
supporting variation in setting, activity, prize, names, and the folk-tale
instruments: surprise, magic, and flashback.
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

    def __post_init__(self):
        for k in ["dusty", "wet", "torn", "safe", "glow"]:
            self.meters.setdefault(k, 0.0)
        for k in ["joy", "worry", "wonder", "fear", "love", "surprise", "calm", "memory"]:
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "grandmother", "woman"}
        male = {"boy", "father", "grandfather", "man"}
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
    mess: str
    soil: str
    zone: set[str]
    weather: str
    keyword: str = ""
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
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
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


def prize_at_risk(activity: Activity, prize: Prize) -> bool:
    return prize.region in activity.zone


def select_gear(activity: Activity, prize: Prize) -> Optional[Gear]:
    for gear in GEAR:
        if activity.mess in gear.guards and prize.region in gear.covers:
            return gear
    return None


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            act = ACTIVITIES[act_id]
            for prize_id, prize in PRIZES.items():
                if prize_at_risk(act, prize) and select_gear(act, prize):
                    combos.append((place, act_id, prize_id))
    return combos


def _do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    world.zone = set(activity.zone)
    actor.meters[activity.mess] += 1
    actor.memes["joy"] += 1
    for item in world.worn_items(actor):
        if item.protective:
            continue
        if item.region in world.zone and not world.covered(actor, item.region):
            item.meters[activity.mess] += 1
            item.meters["dusty"] += 1
            actor.memes["worry"] += 0.5
            if narrate:
                world.say(f"{actor.pronoun('possessive').capitalize()} {item.label} got messy in the rush.")


def predict_mess(world: World, actor: Entity, activity: Activity, prize_id: str) -> dict:
    sim = World(world.setting)
    sim.entities = {k: Entity(**{**v.__dict__}) for k, v in world.entities.items()}
    sim.zone = set(world.zone)
    _do_activity(sim, sim.get(actor.id), activity, narrate=False)
    prize = sim.entities.get(prize_id)
    return {"soiled": bool(prize and prize.meters["dusty"] >= THRESHOLD)}


def introduce(world: World, hero: Entity) -> None:
    world.say(f"{hero.id} was a little {next((t for t in hero.traits if t != 'little'), hero.type)} {hero.type} who loved old roads and bright tales.")


def setup_love(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["love"] += 1
    world.say(f"{hero.pronoun().capitalize()} loved to {activity.verb} because it felt like stepping into a story.")


def gift(world: World, elder: Entity, hero: Entity, prize: Entity) -> None:
    world.say(f"One day, {elder.pronoun('possessive')} hands gave {hero.id} {prize.phrase}.")


def prize_love(world: World, hero: Entity, prize: Entity) -> None:
    hero.memes["love"] += 1
    prize.worn_by = hero.id
    world.say(f"{hero.id} loved {prize.it()} and wore {prize.it()} proudly.")


def arrive(world: World, hero: Entity, elder: Entity, activity: Activity) -> None:
    day = "One evening,"
    world.say(f"{day} {hero.id} and {elder.pronoun('possessive')} {elder.type} went to {world.setting.place}.")
    if hero.id in {"Mina", "Nori", "Lila"}:
        world.say("The road bent at a sharp angle, like a fishhook in the dust.")
    else:
        world.say("The path curved at a sharp angle, as old village roads often do.")


def wants(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["wonder"] += 1
    world.say(f"{hero.id} wanted to {activity.verb} at once, but there was a careful warning in the air.")


def warn(world: World, elder: Entity, hero: Entity, activity: Activity, prize: Entity) -> bool:
    pred = predict_mess(world, hero, activity, prize.id)
    if not pred["soiled"]:
        return False
    world.say(f"\"If you {activity.verb}, your {prize.label} will get {activity.soil},\" {elder.pronoun('possessive')} {elder.type} said.")
    return True


def flashback(world: World, elder: Entity, activity: Activity) -> None:
    elder.memes["memory"] += 1
    world.say(
        f"Then {elder.id} remembered a time long ago, when a small charm and a steady step saved a whole day."
    )


def surprise_clue(world: World, hero: Entity) -> None:
    hero.memes["surprise"] += 1
    world.say(
        f"At that moment, {hero.id} gave a surprised laugh, for a ribbon with an old sign was tucked near the goat's jowl."
    )


def offer_magic(world: World, elder: Entity, hero: Entity, activity: Activity, prize: Entity) -> Optional[Gear]:
    gear_def = select_gear(activity, prize)
    if gear_def is None:
        return None
    gear = world.add(Entity(
        id=gear_def.id,
        type="gear",
        label=gear_def.label,
        owner=hero.id,
        caretaker=elder.id,
        protective=True,
        covers=set(gear_def.covers),
        plural=gear_def.plural,
    ))
    gear.worn_by = hero.id
    world.say(
        f"{elder.id} smiled and said, \"We can use {gear_def.label} first.\" "
        f"That little magic did not come from a spellbook; it came from knowing the right thing to wear."
    )
    return gear_def


def accept(world: World, hero: Entity, elder: Entity, activity: Activity, prize: Entity, gear_def: Gear) -> None:
    hero.memes["joy"] += 1
    hero.memes["love"] += 1
    hero.memes["calm"] += 1
    world.say(f"{hero.id} agreed, and the worry in {hero.id}'s chest grew small.")
    world.say(
        f"They put on the {gear_def.label}, and then {hero.id} could {activity.verb} while {prize.label} stayed safe. "
        f"The old road felt friendly again."
    )


def tell(setting: Setting, activity: Activity, prize_cfg: Prize, hero_name: str, hero_type: str, parent_type: str, trait: str) -> World:
    world = World(setting)
    world.weather = "" if setting.indoor else activity.weather

    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, traits=["little", trait, "curious"]))
    elder = world.add(Entity(id="Elder", kind="character", type=parent_type, label="the elder"))
    prize = world.add(Entity(
        id="prize",
        type=prize_cfg.type,
        label=prize_cfg.label,
        phrase=prize_cfg.phrase,
        owner=hero.id,
        caretaker=elder.id,
        region=prize_cfg.region,
        plural=prize_cfg.plural,
    ))

    introduce(world, hero)
    setup_love(world, hero, activity)
    gift(world, elder, hero, prize)
    prize_love(world, hero, prize)

    world.para()
    arrive(world, hero, elder, activity)
    wants(world, hero, activity)
    warn(world, elder, hero, activity, prize)
    flashback(world, elder, activity)
    surprise_clue(world, hero)

    world.para()
    gear_def = offer_magic(world, elder, hero, activity, prize)
    if gear_def is not None:
        accept(world, hero, elder, activity, prize, gear_def)

    world.facts.update(
        hero=hero,
        elder=elder,
        prize=prize,
        activity=activity,
        setting=setting,
        gear=gear_def,
        conflict=True,
        resolved=gear_def is not None,
        place=setting.place,
    )
    return world


SETTINGS = {
    "village": Setting(place="the village lane", indoor=False, affords={"bridge", "hill", "well"}),
    "bridge": Setting(place="the old bridge", indoor=False, affords={"bridge", "hill"}),
    "well": Setting(place="the stone well", indoor=False, affords={"well"}),
}

ACTIVITIES = {
    "bridge": Activity(
        id="bridge",
        verb="cross the old bridge",
        gerund="crossing the old bridge",
        rush="dash across the planks",
        mess="wet",
        soil="soaked and cold",
        zone={"feet", "legs", "torso"},
        weather="foggy",
        keyword="bridge",
        tags={"bridge", "wet", "magic"},
    ),
    "hill": Activity(
        id="hill",
        verb="climb the hill",
        gerund="climbing the hill",
        rush="run up the slope",
        mess="dusty",
        soil="dusty and tired",
        zone={"feet", "legs"},
        weather="windy",
        keyword="hill",
        tags={"hill", "dusty", "flashback"},
    ),
    "well": Activity(
        id="well",
        verb="draw water from the well",
        gerund="drawing water from the well",
        rush="lean over the stones",
        mess="wet",
        soil="splashed and damp",
        zone={"torso"},
        weather="calm",
        keyword="well",
        tags={"well", "wet", "surprise"},
    ),
}

PRIZES = {
    "cloak": Prize(label="cloak", phrase="a red wool cloak", type="cloak", region="torso"),
    "boots": Prize(label="boots", phrase="a pair of sturdy boots", type="boots", region="feet", plural=True),
    "satchel": Prize(label="satchel", phrase="a bright satchel", type="satchel", region="torso"),
}

GEAR = [
    Gear(id="raincloak", label="a waxed cloak", covers={"torso"}, guards={"wet"}, prep="wrap up in a waxed cloak", tail="wrapped up in the waxed cloak"),
    Gear(id="hillboots", label="good hill boots", covers={"feet"}, guards={"dusty"}, prep="lace on good hill boots", tail="laced on the good hill boots", plural=True),
    Gear(id="travelsatchel", label="an old travel pouch", covers={"torso"}, guards={"wet", "dusty"}, prep="use an old travel pouch instead", tail="slung the old travel pouch over the shoulder"),
]

NAMES = ["Mina", "Nori", "Lila", "Pavel", "Anik", "Sera"]
TRAITS = ["brave", "gentle", "quick", "curious", "cheerful"]


def explain_rejection(activity: Activity, prize: Prize) -> str:
    if not prize_at_risk(activity, prize):
        return f"(No story: {prize.label} would not be in danger from {activity.gerund}.)"
    return f"(No story: no gear in this world can reasonably keep {prize.label} safe during {activity.gerund}.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small folk-tale story world with surprise, magic, and flashback.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father", "grandmother", "grandfather"])
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
    place, activity, prize_id = rng.choice(sorted(combos))
    prize = PRIZES[prize_id]
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(NAMES)
    parent = args.parent or rng.choice(["mother", "father", "grandmother", "grandfather"])
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, activity=activity, prize=prize_id, name=name, gender=gender, parent=parent, trait=trait)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    act = f["activity"]
    return [
        f'Write a short folk tale for a young child about {f["hero"].id} and a {act.keyword} on an old road.',
        f"Tell a story with surprise, magic, and flashback where a child wants to {act.verb} but an elder worries about a prize.",
        f'Write a gentle village story that includes the words "jowl" and "angle" and ends with a safe, magical choice.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, elder, prize, act = f["hero"], f["elder"], f["prize"], f["activity"]
    return [
        QAItem(
            question=f"What did {hero.id} want to do at the old road?",
            answer=f"{hero.id} wanted to {act.verb}, because the road felt like part of a tale."
        ),
        QAItem(
            question=f"Why did {elder.id} warn {hero.id} about the {prize.label}?",
            answer=f"{elder.id} warned {hero.id} because {prize.label} would have gotten {act.soil} if they had gone on without a safer plan."
        ),
        QAItem(
            question="What made the story feel surprising?",
            answer="The surprise came when a small clue was found near the goat's jowl, just as the path bent at a sharp angle."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a flashback in a story?",
            answer="A flashback is when a story briefly remembers something that happened earlier, so the characters can use that memory now."
        ),
        QAItem(
            question="What does a magic cloak do in a folk tale?",
            answer="A magic cloak can help a character stay dry, hidden, warm, or safe, depending on the tale."
        ),
        QAItem(
            question="Why can a sharp angle in a road matter?",
            answer="A sharp angle can hide a turning point, a clue, or a surprise, because you cannot see what is around it at once."
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== (3) World knowledge questions ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], ACTIVITIES[params.activity], PRIZES[params.prize], params.name, params.gender, params.parent, params.trait)
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
        print("--- world model state ---")
        for e in sample.world.entities.values():
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
            print(f"  {e.id}: ({e.type}) {' '.join(bits)}")
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
    import storyworlds.asp as asp
    lines = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", pid, a))
    for aid, a in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        lines.append(asp.fact("mess_of", aid, a.mess))
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
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    c, p = set(asp_valid_combos()), set(valid_combos())
    if c == p:
        print(f"OK: clingo gate matches valid_combos() ({len(c)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if c - p:
        print("  only in clingo:", sorted(c - p))
    if p - c:
        print("  only in python:", sorted(p - c))
    return 1


CURATED = [
    StoryParams(place="village", activity="hill", prize="boots", name="Mina", gender="girl", parent="grandmother", trait="brave"),
    StoryParams(place="bridge", activity="bridge", prize="cloak", name="Nori", gender="boy", parent="grandfather", trait="curious"),
    StoryParams(place="well", activity="well", prize="satchel", name="Lila", gender="girl", parent="mother", trait="gentle"),
]


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
            header = f"### {p.name}: {p.activity} at {p.place} (prize: {p.prize})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
