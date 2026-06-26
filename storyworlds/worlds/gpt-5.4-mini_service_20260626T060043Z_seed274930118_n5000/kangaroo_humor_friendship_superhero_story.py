#!/usr/bin/env python3
"""
storyworlds/worlds/kangaroo_humor_friendship_superhero_story.py
==============================================================

A standalone story world about a small superhero, a cheerful kangaroo friend,
and a funny problem that can be solved with a safe, shared plan.

Seed idea:
---
A young superhero loves helping around the city. Their kangaroo friend loves
hopping beside them and making everyone laugh. But when the hero wears a new
cape on a bouncy mission, the cape can snag or tangle. The mentor worries,
the hero grumbles, and the friend turns the tense moment into a joke. Then they
find a clever fix that keeps the cape safe and lets the team keep going.

World model:
---
- typed entities with physical meters and emotional memes
- the hero's action can tug on the cape or mask
- the kangaroo friend adds humor and friendship pressure/support
- a reasonable fix must actually protect the risky item
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

    def m(self, key: str) -> float:
        return self.meters.get(key, 0.0)

    def e(self, key: str) -> float:
        return self.memes.get(key, 0.0)

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
class Setting:
    place: str
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
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.zone: set[str] = set()
        self.fired: set[tuple] = set()
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
        return any(item.protective and region in item.covers for item in self.worn_items(actor))

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


SETTINGS = {
    "city": Setting(place="the city square", affords={"bounce", "race", "stunt"}),
    "rooftop": Setting(place="the rooftop garden", affords={"bounce", "stunt"}),
    "park": Setting(place="the park", affords={"bounce", "race"}),
}

ACTIVITIES = {
    "bounce": Activity(
        id="bounce",
        verb="bounce across the walkway",
        gerund="bouncing across walkways",
        rush="hop down the steps in a big hurry",
        mess="snagged",
        soil="snagged and crooked",
        zone={"torso", "back"},
        keyword="bounce",
        tags={"kangaroo", "humor", "friendship"},
    ),
    "stunt": Activity(
        id="stunt",
        verb="do a big hero stunt",
        gerund="doing big hero stunts",
        rush="dash into the stunt ring",
        mess="snagged",
        soil="caught and twisted",
        zone={"torso"},
        keyword="stunt",
        tags={"superhero", "humor"},
    ),
    "race": Activity(
        id="race",
        verb="race the wind",
        gerund="racing the wind",
        rush="sprint down the lane",
        mess="snagged",
        soil="tugged loose",
        zone={"back", "torso"},
        keyword="race",
        tags={"friendship", "superhero"},
    ),
}

PRIZES = {
    "cape": Prize("cape", "a new red cape", "cape", "back"),
    "mask": Prize("mask", "a shiny blue mask", "mask", "face"),
    "belt": Prize("belt", "a utility belt with pockets", "belt", "waist"),
}

GEAR = [
    Gear("capeclip", "a cape clip", {"back"}, {"snagged"}, "clip the cape short", "clipped the cape short"),
    Gear("softmask", "a soft mask strap", {"face"}, {"snagged"}, "use a soft mask strap", "used the soft mask strap"),
    Gear("beltloop", "a belt loop tie", {"waist"}, {"snagged"}, "tie the belt snugly", "tied the belt snugly"),
]

HERO_NAMES = ["Nova", "Zed", "Pip", "Mira", "Toby", "Luna"]
KANGAROO_NAMES = ["Roo", "Juno", "Bop", "Skippy", "Mallow"]
MENTOR_NAMES = ["Captain Stern", "Aunt Comet", "Chief Spark"]
TRAITS = ["brave", "silly", "cheery", "restless", "curious"]


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


def _do_activity(world: World, actor: Entity, activity: Activity) -> None:
    world.zone = set(activity.zone)
    actor.meters[activity.mess] = actor.meters.get(activity.mess, 0.0) + 1
    actor.memes["joy"] = actor.memes.get("joy", 0.0) + 1
    for item in world.worn_items(actor):
        if item.protective or item.region not in world.zone:
            continue
        if world.covered(actor, item.region):
            continue
        item.meters[activity.mess] = item.meters.get(activity.mess, 0.0) + 1
        item.meters["dirty"] = item.meters.get("dirty", 0.0) + 1


def predict_mess(world: World, actor: Entity, activity: Activity, prize_id: str) -> dict:
    sim = World(world.setting)
    sim.entities = {k: Entity(**{**e.__dict__, "meters": dict(e.meters), "memes": dict(e.memes), "covers": set(e.covers)}) for k, e in world.entities.items()}
    sim.zone = set(world.zone)
    _do_activity(sim, sim.get(actor.id), activity)
    prize = sim.entities[prize_id]
    return {"soiled": prize.meters.get("dirty", 0.0) >= THRESHOLD}


def tell(setting: Setting, activity: Activity, prize_cfg: Prize, hero_name: str, hero_type: str, hero_trait: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, meters={}, memes={"joy": 0.0, "love": 0.0}))
    kangaroo = world.add(Entity(id="Kangaroo", kind="character", type="kangaroo", label="the kangaroo", meters={}, memes={"humor": 0.0, "friendship": 0.0}))
    mentor = world.add(Entity(id="Mentor", kind="character", type="woman", label="the mentor", meters={}, memes={"worry": 0.0}))
    prize = world.add(Entity(id="Prize", type=prize_cfg.type, label=prize_cfg.label, phrase=prize_cfg.phrase, owner=hero.id, caretaker=mentor.id, region=prize_cfg.region, plural=prize_cfg.plural))

    hero.memes["heroic"] = 1.0
    hero.memes["friendship"] = 1.0
    kangaroo.memes["friendship"] = 1.0

    world.say(f"{hero_name} was a {hero_trait} little superhero who liked helping people in {setting.place}.")
    world.say(f"{hero_name} also had a kangaroo friend who could hop so fast that even the pigeons blinked.")
    world.say(f"One day, {hero_name} wore {prize_cfg.phrase} and felt ready for a cheerful rescue.")

    world.para()
    world.say(f"At {setting.place}, {hero_name} wanted to {activity.verb}, and the kangaroo bounced nearby, making a funny little boing-boing sound.")
    world.say(f"{hero_name} laughed, but the mentor frowned and looked at {prize_cfg.phrase}.")
    if predict_mess(world, hero, activity, prize.id)["soiled"]:
        world.say(f'"If you rush into that {activity.keyword}, your {prize.label} will get {activity.soil}," the mentor said.')
        hero.memes["worry"] = hero.memes.get("worry", 0.0) + 1
        hero.memes["defiance"] = hero.memes.get("defiance", 0.0) + 1
        world.say(f"{hero_name} puffed up and tried to {activity.rush}, but the kangaroo hopped in front and made a silly face like a tiny fuzzy traffic sign.")
        kangaroo.memes["humor"] = kangaroo.memes.get("humor", 0.0) + 1
        hero.memes["grabbed_by"] = 1.0
        world.say(f"{hero_name} snorted, and the grumpy feeling broke a little when the kangaroo did a wobbly superhero pose.")
        gear = select_gear(activity, prize)
        if gear is None:
            raise StoryError("No reasonable gear exists for this story.")
        fix = world.add(Entity(id=gear.id, type="gear", label=gear.label, owner=hero.id, caretaker=mentor.id, protective=True, covers=set(gear.covers)))
        fix.worn_by = hero.id
        world.say(f'The mentor smiled. "How about we {gear.prep} first?"')
        hero.memes["joy"] = hero.memes.get("joy", 0.0) + 1
        hero.memes["friendship"] = hero.memes.get("friendship", 0.0) + 1
        kangaroo.memes["friendship"] = kangaroo.memes.get("friendship", 0.0) + 1
        world.say(f"{hero_name} nodded, and soon they {gear.tail}.")
        world.say(f"Then {hero_name} was {activity.gerund}, {prize_cfg.phrase} stayed clean, and the kangaroo bounced beside them like a happy drumbeat.")
    else:
        world.say(f"The mentor saw no real risk, so the team laughed and went on with the day.")

    world.facts.update(hero=hero, kangaroo=kangaroo, mentor=mentor, prize=prize, prize_cfg=prize_cfg, activity=activity, setting=setting)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    act = f["activity"]
    prize = f["prize_cfg"]
    return [
        f'Write a short superhero story for a small child that includes a kangaroo and the word "{act.keyword}".',
        f"Tell a funny friendship story where {hero.id} wants to {act.verb} but needs to protect {prize.phrase}.",
        f"Write a gentle superhero tale about a kangaroo friend, a silly problem, and a safe solution.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, kangaroo, mentor, prize, act = f["hero"], f["kangaroo"], f["mentor"], f["prize"], f["activity"]
    return [
        QAItem(
            question=f"Who was the superhero in the story?",
            answer=f"The superhero was {hero.id}, a {hero.type} who wanted to help and have fun."
        ),
        QAItem(
            question=f"What animal friend helped make the story funny?",
            answer=f"The funny friend was the kangaroo, who hopped around and made silly faces."
        ),
        QAItem(
            question=f"Why did the mentor worry about {prize.label}?",
            answer=f"The mentor worried because if {hero.id} went ahead with {act.verb}, {prize.phrase} could get {act.soil}."
        ),
        QAItem(
            question=f"What solved the problem in the end?",
            answer=f"They used {select_gear(act, prize).label} first, so {hero.id} could keep going and {prize.phrase} stayed safe."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a kangaroo?",
            answer="A kangaroo is a hopping animal from Australia. It uses strong back legs and often carries a baby in a pouch."
        ),
        QAItem(
            question="Why is friendship important?",
            answer="Friendship helps people share ideas, feel brave, and solve problems together."
        ),
        QAItem(
            question="What does a superhero do?",
            answer="A superhero tries to help others, protect people, and do brave things."
        ),
        QAItem(
            question="Why can a cape be useful for a superhero?",
            answer="A cape can be part of a superhero costume and can make the hero look bold and ready to help."
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== Story QA ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World QA ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    out = ["--- world model state ---"]
    for e in world.entities.values():
        out.append(f"{e.id}: type={e.type} meters={e.meters} memes={e.memes} worn_by={e.worn_by} covers={sorted(e.covers)}")
    return "\n".join(out)


@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    name: str
    gender: str
    trait: str
    seed: Optional[int] = None


ASP_RULES = r"""
prize_at_risk(A,P) :- splashes(A,R), worn_on(P,R).
protects(G,A,P) :- prize_at_risk(A,P), mess_of(A,M), guards(G,M), covers(G,R), worn_on(P,R).
has_fix(A,P) :- protects(_,A,P).
valid(Place,A,P) :- affords(Place,A), prize_at_risk(A,P), has_fix(A,P).
"""


def asp_facts() -> str:
    import asp
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
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH:")
    if py - cl:
        print(" only in python:", sorted(py - cl))
    if cl - py:
        print(" only in clingo:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A superhero story world with a kangaroo friend, humor, and friendship.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--parent", choices=["mentor"], default="mentor")
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
    if args.activity and args.prize:
        act, pr = ACTIVITIES[args.activity], PRIZES[args.prize]
        if not (prize_at_risk(act, pr) and select_gear(act, pr)):
            raise StoryError("That activity and prize do not make a reasonable superhero problem.")
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.activity is None or c[1] == args.activity)
              and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError("No valid combination matches the given options.")
    place, activity, prize = rng.choice(sorted(combos))
    return StoryParams(
        place=place,
        activity=activity,
        prize=prize,
        name=args.name or rng.choice(HERO_NAMES),
        gender=args.gender or rng.choice(["girl", "boy"]),
        trait=args.trait or rng.choice(TRAITS),
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], ACTIVITIES[params.activity], PRIZES[params.prize], params.name, params.gender, params.trait)
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
    StoryParams(place="city", activity="bounce", prize="cape", name="Nova", gender="girl", trait="silly"),
    StoryParams(place="rooftop", activity="stunt", prize="mask", name="Pip", gender="boy", trait="brave"),
    StoryParams(place="park", activity="race", prize="belt", name="Mira", gender="girl", trait="cheery"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid/3."))
        print(sorted(set(asp.atoms(model, "valid"))))
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

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
