#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/reel_garrison_manger_campground_teamwork_superhero_story.py
================================================================================================

A standalone story world for a tiny superhero tale at a campground.

Seed premise:
- A young superhero wants to use a reel for a rescue at a campground.
- A teammate and a trusted adult worry about the hero's cape getting snagged.
- They solve the problem with teamwork, using the right gear and a careful plan.
- The story should naturally include the words reel, garrison, and manger.

The world is deliberately small and constraint-checked: there is one main
activity, one prize at risk, and a compatible teamwork-based fix.
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
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.meters = dict(self.meters)
        self.memes = dict(self.memes)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the campground"
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
        self.zone: set[str] = set()
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
        clone.zone = set(self.zone)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


def prize_at_risk(activity: Activity, prize: Prize) -> bool:
    return prize.region in activity.zone


def select_gear(activity: Activity, prize: Prize) -> Optional[Gear]:
    for gear in GEAR:
        if activity.mess in gear.guards and prize.region in gear.covers:
            return gear
    return None


def explain_rejection(activity: Activity, prize: Prize) -> str:
    noun = prize.label if prize.plural else f"a {prize.label}"
    return (
        f"(No story: {activity.gerund} does not put {noun} at real risk, "
        f"so there is no honest superhero problem to solve.)"
    )


def valid_combos() -> list[tuple[str, str]]:
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
    actor.meters[activity.mess] = actor.meters.get(activity.mess, 0.0) + 1.0
    actor.memes["joy"] = actor.memes.get("joy", 0.0) + 1.0
    for item in world.worn_items(actor):
        if item.protective:
            continue
        if item.region not in world.zone:
            continue
        if world.covered(actor, item.region):
            continue
        if item.meters.get(activity.mess, 0.0) >= THRESHOLD:
            continue
        item.meters[activity.mess] = item.meters.get(activity.mess, 0.0) + 1.0
        item.meters["dirty"] = item.meters.get("dirty", 0.0) + 1.0
        if narrate:
            world.say(f"{actor.pronoun('possessive').capitalize()} {item.label} got messy.")
        if item.caretaker:
            carer = world.get(item.caretaker)
            carer.meters["workload"] = carer.meters.get("workload", 0.0) + 1.0


def predict_mess(world: World, actor: Entity, activity: Activity, prize_id: str) -> dict:
    sim = world.copy()
    _do_activity(sim, sim.get(actor.id), activity, narrate=False)
    prize = sim.entities.get(prize_id)
    return {"soiled": bool(prize and prize.meters.get("dirty", 0.0) >= THRESHOLD)}


def introduce(world: World, hero: Entity) -> None:
    world.say(
        f"{hero.id} was a little {hero.type} hero with a bright cape and a big heart."
    )


def teamwork_theme(world: World, hero: Entity, teammate: Entity) -> None:
    hero.memes["teamwork"] = hero.memes.get("teamwork", 0.0) + 1.0
    teammate.memes["teamwork"] = teammate.memes.get("teamwork", 0.0) + 1.0
    world.say(
        f"{hero.id} and {teammate.id} loved teamwork, because together they could do more than either one alone."
    )


def setup_scene(world: World, hero: Entity, teammate: Entity) -> None:
    world.say(
        f"At the campground, they passed the little garrison by the trail and the old manger by the pony pen."
    )
    world.say(
        f"{hero.id} liked how the reel in {teammate.id}'s hands could pull a line straight and strong."
    )


def wants_action(world: World, hero: Entity, activity: Activity, prize: Entity) -> None:
    hero.memes["desire"] = hero.memes.get("desire", 0.0) + 1.0
    world.say(
        f"{hero.id} wanted to {activity.verb}, but {hero.pronoun('possessive')} {prize.label} was in the way."
    )


def warn(world: World, mentor: Entity, hero: Entity, activity: Activity, prize: Entity) -> bool:
    pred = predict_mess(world, hero, activity, prize.id)
    if not pred["soiled"]:
        return False
    world.facts["predicted_soil"] = activity.soil
    world.say(
        f'"If you {activity.verb}, your {prize.label} will get {activity.soil}," {mentor.id} said.'
    )
    return True


def fix_with_teamwork(world: World, mentor: Entity, hero: Entity, teammate: Entity, activity: Activity, prize: Entity) -> Optional[Gear]:
    gear_def = select_gear(activity, prize)
    if gear_def is None:
        return None
    gear = world.add(
        Entity(
            id=gear_def.id,
            kind="thing",
            type="gear",
            label=gear_def.label,
            protective=True,
            covers=set(gear_def.covers),
            plural=gear_def.plural,
            owner=hero.id,
            caretaker=mentor.id,
        )
    )
    gear.worn_by = hero.id
    if not predict_mess(world, hero, activity, prize.id)["soiled"]:
        world.say(
            f"{mentor.id} smiled and said, 'Teamwork first: we will use {gear_def.label} and work together.'"
        )
        world.say(f"{teammate.id} held the line, and {hero.id} steadied the reel.")
        return gear_def
    gear.worn_by = None
    del world.entities[gear.id]
    return None


def resolve(world: World, hero: Entity, mentor: Entity, teammate: Entity, activity: Activity, prize: Entity, gear_def: Gear) -> None:
    hero.memes["joy"] = hero.memes.get("joy", 0.0) + 1.0
    hero.memes["conflict"] = 0.0
    world.say(
        f"{hero.id} nodded, and the three of them worked as a team."
    )
    world.say(
        f"With {gear_def.label} on, {hero.id} could {activity.verb} safely at the campground."
    )
    world.say(
        f"The reel turned clean and sure, {prize.label} stayed safe, and the campground looked ready for a hero's next rescue."
    )


def tell(setting: Setting, activity: Activity, prize_cfg: Prize, hero_name: str, hero_type: str, teammate_name: str, mentor_name: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type))
    teammate = world.add(Entity(id=teammate_name, kind="character", type="boy"))
    mentor = world.add(Entity(id=mentor_name, kind="character", type="mother", label="the mentor"))
    prize = world.add(
        Entity(
            id="prize",
            kind="thing",
            type=prize_cfg.type,
            label=prize_cfg.label,
            phrase=prize_cfg.phrase,
            region=prize_cfg.region,
            plural=prize_cfg.plural,
            owner=hero.id,
            caretaker=mentor.id,
        )
    )
    prize.worn_by = hero.id

    introduce(world, hero)
    teamwork_theme(world, hero, teammate)
    setup_scene(world, hero, teammate)
    world.para()
    wants_action(world, hero, activity, prize)
    warn(world, mentor, hero, activity, prize)
    world.say(f"{teammate.id} grabbed the reel so it would not slip.")
    gear_def = fix_with_teamwork(world, mentor, hero, teammate, activity, prize)
    world.para()
    if gear_def:
        resolve(world, hero, mentor, teammate, activity, prize, gear_def)

    world.facts.update(
        hero=hero,
        teammate=teammate,
        mentor=mentor,
        prize=prize,
        activity=activity,
        gear=gear_def,
        resolved=gear_def is not None,
    )
    return world


SETTINGS = {
    "campground": Setting(place="the campground", affords={"reel"}),
}

ACTIVITIES = {
    "reel": Activity(
        id="reel",
        verb="reel in the rescue line",
        gerund="reeling in the rescue line",
        rush="pull the reel too fast",
        mess="tangled",
        soil="all tangled",
        zone={"torso"},
        keyword="reel",
        tags={"reel", "teamwork", "campground"},
    ),
}

PRIZES = {
    "cape": Prize(
        label="cape",
        phrase="a bright superhero cape",
        type="cape",
        region="torso",
    ),
}

GEAR = [
    Gear(
        id="team_gloves",
        label="team gloves",
        covers={"torso"},
        guards={"tangled"},
        prep="put on team gloves first",
        tail="used team gloves to keep the line steady",
    ),
    Gear(
        id="safety_clasp",
        label="a safety clasp",
        covers={"torso"},
        guards={"tangled"},
        prep="clip on a safety clasp first",
        tail="clipped on a safety clasp and worked together",
    ),
]

HERO_NAMES = ["Nova", "Jay", "Mira", "Ace", "Zed", "Ruby"]
TEAMMATE_NAMES = ["Bolt", "Pip", "Rae", "Toby"]
MENTOR_NAMES = ["Captain Lane", "Scout Mina"]

CURATED = [
    {
        "place": "campground",
        "activity": "reel",
        "prize": "cape",
        "name": "Nova",
        "gender": "girl",
        "teammate": "Bolt",
        "mentor": "Captain Lane",
    }
]


@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    name: str
    gender: str
    teammate: str
    mentor: str
    seed: Optional[int] = None


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    act = f["activity"]
    prize = f["prize"]
    return [
        f'Write a short superhero story for a young child set at a campground, with teamwork and the word "{act.keyword}".',
        f"Tell a gentle rescue story where {hero.id} wants to {act.verb} but must protect a {prize.label}.",
        f"Write a campground superhero story that includes the words reel, garrison, and manger, and ends with teamwork saving the day.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    teammate = f["teammate"]
    mentor = f["mentor"]
    prize = f["prize"]
    act = f["activity"]
    return [
        QAItem(
            question=f"Where did {hero.id} and {teammate.id} work on the rescue line?",
            answer="They worked at the campground, near the little garrison and the manger by the pony pen.",
        ),
        QAItem(
            question=f"Why did {mentor.id} warn {hero.id} about the plan?",
            answer=f"{mentor.id} warned {hero.id} because {act.verb} would have made the {prize.label} all {act.soil}.",
        ),
        QAItem(
            question=f"How did teamwork help {hero.id} in the end?",
            answer=f"Teamwork helped because {teammate.id} held the reel steady and {mentor.id} brought {f['gear'].label}, so {hero.id} could {act.verb} safely.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a reel?",
            answer="A reel is a tool that winds up a line so it can be pulled in neatly.",
        ),
        QAItem(
            question="What is a garrison?",
            answer="A garrison is a place where guards stay or where a small group protects a location.",
        ),
        QAItem(
            question="What is a manger?",
            answer="A manger is a trough that holds food for animals.",
        ),
        QAItem(
            question="What does teamwork mean?",
            answer="Teamwork means people help each other and do a job together.",
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
            bits.append(f"covers={sorted(e.covers)}")
        elif e.region:
            bits.append(f"region={e.region}")
        lines.append(f"  {e.id:12} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


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
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("worn_on", pid, p.region))
    for g in GEAR:
        lines.append(asp.fact("gear", g.id))
        for c in sorted(g.covers):
            lines.append(asp.fact("covers", g.id, c))
        for m in sorted(g.guards):
            lines.append(asp.fact("guards", g.id, m))
    return "\n".join(lines)


ASP_RULES = r"""
prize_at_risk(A,P) :- splashes(A,R), worn_on(P,R).
protects(G,A,P) :- gear(G), prize_at_risk(A,P), mess_of(A,M), guards(G,M), covers(G,R), worn_on(P,R).
valid(Place,A,P) :- affords(Place,A), prize_at_risk(A,P), protects(_,A,P).
#show valid/3.
"""


def asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp

    model = asp.one_model(asp_program())
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
    ap = argparse.ArgumentParser(
        description="A campground superhero storyworld about reel, garrison, manger, and teamwork."
    )
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--teammate")
    ap.add_argument("--mentor")
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
    place, activity, prize = rng.choice(combos)
    return StoryParams(
        place=place,
        activity=activity,
        prize=prize,
        name=args.name or rng.choice(HERO_NAMES),
        gender=args.gender or rng.choice(["girl", "boy"]),
        teammate=args.teammate or rng.choice(TEAMMATE_NAMES),
        mentor=args.mentor or rng.choice(MENTOR_NAMES),
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.place],
        ACTIVITIES[params.activity],
        PRIZES[params.prize],
        params.name,
        params.gender,
        params.teammate,
        params.mentor,
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
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, activity, prize) combos:\n")
        for c in combos:
            print("  ", c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for p in CURATED:
            params = StoryParams(**p)
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 20, 20):
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
