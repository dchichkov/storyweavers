#!/usr/bin/env python3
"""
A standalone storyworld about a fairy-tale beach day, a picky dress code, and a
humorous happy ending centered on a bikini.

The seed premise:
- A princess or fairy-tale child wants to play by the water.
- A treasured bikini is involved.
- A fussy guardian worries the bikini is not the right gear for a game or a
  royal errand.
- The world turns on choosing the right place and the right garment so the
  story can end happily and with a little laughter.

This script models a small causal simulation with physical meters and emotional
memes, plus an inline ASP twin for the reasonableness gate.
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
        if not self.meters:
            self.meters = {}
        if not self.memes:
            self.memes = {}

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "queen", "princess", "fairy"}
        male = {"boy", "father", "king", "prince"}
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
        import copy
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.zone = set(self.zone)
        clone.weather = self.weather
        clone.paragraphs = [[]]
        return clone


def _r_soak(world: World) -> list[str]:
    out = []
    for actor in world.characters():
        if actor.meters.get("wet", 0.0) < THRESHOLD:
            continue
        for item in world.worn_items(actor):
            if item.protective or item.region not in world.zone:
                continue
            if world.covered(actor, item.region):
                continue
            sig = ("soak", item.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            item.meters["wet"] = item.meters.get("wet", 0.0) + 1
            item.meters["dirty"] = item.meters.get("dirty", 0.0) + 1
            out.append(f"{actor.pronoun('possessive').capitalize()} {item.label} got wet and a bit silly.")
    return out


def _r_workload(world: World) -> list[str]:
    out = []
    for item in list(world.entities.values()):
        if item.meters.get("dirty", 0.0) < THRESHOLD or not item.caretaker:
            continue
        sig = ("work", item.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        carer = world.get(item.caretaker)
        carer.meters["workload"] = carer.meters.get("workload", 0.0) + 1
        out.append(f"That would mean more washing for {carer.label}.")
    return out


def _r_conflict(world: World) -> list[str]:
    for actor in world.characters():
        if actor.memes.get("defiance", 0.0) < THRESHOLD or actor.memes.get("stopped", 0.0) < THRESHOLD:
            continue
        sig = ("conflict", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["conflict"] = actor.memes.get("conflict", 0.0) + 1
        return ["__conflict__"]
    return []


CAUSAL_RULES = [
    ("soak", _r_soak),
    ("workload", _r_workload),
    ("conflict", _r_conflict),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced = []
    changed = True
    while changed:
        changed = False
        for _, rule in CAUSAL_RULES:
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
    _do_activity(sim, sim.get(actor.id), activity, narrate=False)
    prize = sim.entities.get(prize_id)
    return {
        "soiled": bool(prize and prize.meters.get("dirty", 0.0) >= THRESHOLD),
        "workload": sum(e.meters.get("workload", 0.0) for e in sim.characters()),
    }


def _do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    if activity.id not in world.setting.affords:
        raise StoryError(f"{world.setting.place} does not afford {activity.id}.")
    world.zone = set(activity.zone)
    actor.meters[activity.mess] = actor.meters.get(activity.mess, 0.0) + 1
    actor.memes["joy"] = actor.memes.get("joy", 0.0) + 1
    propagate(world, narrate=narrate)


def tell(setting: Setting, activity: Activity, prize_cfg: Prize, hero_name: str = "Luna",
         hero_type: str = "princess", hero_traits: Optional[list[str]] = None,
         parent_type: str = "queen") -> World:
    world = World(setting)
    world.weather = "" if setting.indoor else activity.weather

    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type,
                            meters={}, memes={}, ))
    hero.meters.setdefault("joy", 0.0)
    hero.memes.setdefault("love", 0.0)

    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label="the queen"))
    prize = world.add(Entity(
        id="prize", type=prize_cfg.type, label=prize_cfg.label, phrase=prize_cfg.phrase,
        owner=hero.id, caretaker=parent.id, region=prize_cfg.region, plural=prize_cfg.plural,
    ))

    hero.memes["love"] = hero.memes.get("love", 0.0) + 1
    world.say(f"{hero.id} was a little {hero_type} who loved {activity.gerund} and bright sea air.")
    world.say(f"One day, {parent.label} bought {hero.pronoun('object')} {prize.phrase}.")
    prize.worn_by = hero.id
    world.say(f"{hero.id} loved {hero.pronoun('possessive')} {prize.label} and wore {prize.it()} with royal pride.")

    world.para()
    where = "inside" if setting.indoor else "outside"
    world.say(f"One sunny day, {hero.id} and {hero.pronoun('possessive')} {parent.label} went to {setting.place}.")
    world.say(f"{hero.id} wanted to {activity.verb} {where}, but {hero.pronoun('possessive')} {parent.label} lifted a careful eyebrow.")
    pred = predict_mess(world, hero, activity, prize.id)
    if pred["soiled"]:
        world.facts["predicted_soil"] = activity.soil
        world.facts["predicted_workload"] = pred["workload"]
        world.say(f'"You\'ll get your {prize.label} {activity.soil}," {hero.pronoun("possessive")} {parent.label} said.')
        hero.memes["defiance"] = hero.memes.get("defiance", 0.0) + 1
        world.say(f"{hero.id} puffed up like a tiny royal cloud and tried to {activity.rush}.")
        hero.memes["stopped"] = hero.memes.get("stopped", 0.0) + 1

    world.para()
    gear_def = select_gear(activity, prize)
    if gear_def is None:
        raise StoryError("No compatible gear exists for this story.")
    gear = world.add(Entity(id=gear_def.id, type="gear", label=gear_def.label,
                            owner=hero.id, caretaker=parent.id, protective=True,
                            covers=set(gear_def.covers), plural=gear_def.plural))
    gear.worn_by = hero.id
    if predict_mess(world, hero, activity, prize.id)["soiled"]:
        gear.worn_by = None
        del world.entities[gear.id]
        raise StoryError("The proposed gear did not actually prevent the mess.")

    world.say(f"Then {parent.label} smiled and said, 'How about we {gear_def.prep}?'")
    hero.memes["joy"] = hero.memes.get("joy", 0.0) + 1
    hero.memes["love"] = hero.memes.get("love", 0.0) + 1
    hero.memes["conflict"] = 0.0
    world.say(f"{hero.id}'s face brightened. '{'Yay, let's do it!'}' {hero.id} laughed.")
    world.say(f"They {gear_def.tail}. Soon {hero.id} was {activity.gerund}, {prize.label} stayed clean, and everyone laughed at the splashy little wiggle of the waves.")

    world.facts.update(hero=hero, parent=parent, prize=prize, prize_cfg=prize_cfg,
                       activity=activity, setting=setting, gear=gear_def,
                       resolved=True, conflict=True)
    return world


SETTINGS = {
    "seashore": Setting(place="the seashore", indoor=False, affords={"swim", "splash"}),
    "lilypad_pond": Setting(place="the lily pond", indoor=False, affords={"splash"}),
    "castle_pool": Setting(place="the castle pool", indoor=False, affords={"swim"}),
}

ACTIVITIES = {
    "swim": Activity(
        id="swim", verb="swim in the waves", gerund="swimming in the waves", rush="dash into the waves",
        mess="wet", soil="soaking wet", zone={"torso", "legs"}, weather="sunny",
        keyword="bikini", tags={"water", "wet", "bikini"},
    ),
    "splash": Activity(
        id="splash", verb="splash in the water", gerund="splashing in the water", rush="skip into the pond",
        mess="wet", soil="splashed and wet", zone={"legs"}, weather="sunny",
        keyword="bikini", tags={"water", "wet", "bikini"},
    ),
}

PRIZES = {
    "bikini": Prize(
        label="bikini", phrase="a sparkling little bikini", type="bikini", region="torso",
        plural=False, genders={"girl"},
    ),
    "cape": Prize(
        label="cape", phrase="a glittering cape", type="cape", region="torso",
        plural=False, genders={"girl", "boy"},
    ),
}

GEAR = [
    Gear(
        id="sunhat", label="a sunhat", covers={"head"}, guards={"wet"},
        prep="put on a sunhat first", tail="walked back to the water with a sunhat and a grin",
    ),
    Gear(
        id="swim_wrap", label="a swim wrap", covers={"torso", "legs"}, guards={"wet"},
        prep="put on a swim wrap over your bikini", tail="went back dressed for splashing",
    ),
    Gear(
        id="royal_towel", label="a royal towel cloak", covers={"torso"}, guards={"wet"},
        prep="wear a royal towel cloak for the walk", tail="strolled back like the funniest little queen at the shore",
    ),
]

GIRL_NAMES = ["Luna", "Mira", "Sofia", "Nina", "Iris"]
TRAITS = ["brave", "curious", "cheerful", "sparkly"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            act = ACTIVITIES[act_id]
            for prize_id, prize in PRIZES.items():
                if prize_at_risk(act, prize) and select_gear(act, prize):
                    combos.append((place, act_id, prize_id))
    return combos


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


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, parent, act, prize = f["hero"], f["parent"], f["activity"], f["prize_cfg"]
    return [
        f'Write a short fairy tale for a little child about a {hero.type} named {hero.id}, a {prize.label}, and a funny water-side compromise.',
        f"Tell a gentle story where {hero.id} wants to {act.verb} at {world.setting.place} but {parent.label} worries about the {prize.label}.",
        f'Write a humorous happy-ending story that includes the word "{prize.label}" and ends with a safe splashy choice.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, parent, prize, act = f["hero"], f["parent"], f["prize"], f["activity"]
    qa = [
        QAItem(
            question=f"Who wanted to {act.verb} at {world.setting.place}?",
            answer=f"{hero.id} wanted to {act.verb}, and {parent.label} was watching carefully.",
        ),
        QAItem(
            question=f"What pretty item did {parent.label} buy for {hero.id}?",
            answer=f"{parent.label} bought {hero.pronoun('object')} {prize.phrase}.",
        ),
        QAItem(
            question=f"Why did the story need a safer plan?",
            answer=f"The plan was needed because {hero.id} could have ended up {act.soil}, which would have made extra washing for {parent.label}.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended happily, with {hero.id} {act.gerund} while {prize.label} stayed clean and everyone laughed.",
        ),
    ]
    if f.get("resolved"):
        gear = f["gear"]
        qa.append(QAItem(
            question=f"What helped {hero.id} play without ruining the {prize.label}?",
            answer=f"{gear.label} helped, because it let {hero.id} play safely while the {prize.label} stayed dry.",
        ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a bikini?",
            answer="A bikini is a two-piece swimsuit that people wear for swimming or playing in water.",
        ),
        QAItem(
            question="Why can water make clothes slippery?",
            answer="Water can make fabric wet and slippery, so clothes may feel heavy and drip.",
        ),
        QAItem(
            question="Why do people wear swim clothes near the sea?",
            answer="People wear swim clothes near the sea so they can play in the water more comfortably.",
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
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.protective:
            bits.append(f"covers={sorted(e.covers)}")
        elif e.region:
            bits.append(f"region={e.region}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="seashore", activity="swim", prize="bikini", name="Luna", gender="girl", parent="queen", trait="brave"),
    StoryParams(place="lilypad_pond", activity="splash", prize="bikini", name="Mira", gender="girl", parent="queen", trait="curious"),
]


def explain_rejection(activity: Activity, prize: Prize) -> str:
    if not prize_at_risk(activity, prize):
        return f"(No story: {activity.gerund} would not truly threaten the {prize.label}.)"
    return f"(No story: the catalog has no fair fix for a {prize.label} in this setup.)"


def explain_gender(prize_id: str, gender: str) -> str:
    ok = " / ".join(sorted(PRIZES[prize_id].genders))
    return f"(No story: a {PRIZES[prize_id].label} is not a typical {gender}'s item here; try --gender {ok}.)"


ASP_RULES = r"""
prize_at_risk(A,P) :- splashes(A,R), worn_on(P,R).
protects(G,A,P) :- gear(G), prize_at_risk(A,P), mess_of(A,M), guards(G,M), covers(G,R), worn_on(P,R).
has_fix(A,P) :- protects(_,A,P).
valid(Place,A,P) :- affords(Place,A), prize_at_risk(A,P), has_fix(A,P).
valid_story(Place,A,P,Gender) :- valid(Place,A,P), wears(Gender,P).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for aid, a in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        lines.append(asp.fact("mess_of", aid, a.mess))
        for r in sorted(a.zone):
            lines.append(asp.fact("splashes", aid, r))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("worn_on", pid, p.region))
        for g in sorted(p.genders):
            lines.append(asp.fact("wears", g, pid))
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


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/4."))
    return sorted(set(asp.atoms(model, "valid_story")))


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
    ap = argparse.ArgumentParser(description="A fairy-tale story world about a bikini, humor, and a happy ending.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["queen", "king"])
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
    if args.gender and args.prize and args.gender not in PRIZES[args.prize].genders:
        raise StoryError(explain_gender(args.prize, args.gender))
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.activity is None or c[1] == args.activity)
              and (args.prize is None or c[2] == args.prize)
              and (args.gender is None or args.gender in PRIZES[c[2]].genders)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, activity, prize_id = rng.choice(sorted(combos))
    prize = PRIZES[prize_id]
    gender = args.gender or rng.choice(sorted(prize.genders))
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else ["Finn", "Theo"])
    parent = args.parent or rng.choice(["queen", "king"])
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, activity=activity, prize=prize_id, name=name, gender=gender, parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], ACTIVITIES[params.activity], PRIZES[params.prize],
                 params.name, "princess" if params.gender == "girl" else "prince",
                 [params.trait], params.parent)
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
        triples, stories = asp_valid_combos(), asp_valid_stories()
        print(f"{len(triples)} compatible (place, activity, prize) combos ({len(stories)} with gender):\n")
        for place, act, prize in triples:
            genders = sorted(g for (pl, a, pr, g) in stories if (pl, a, pr) == (place, act, prize))
            print(f"  {place:12} {act:8} {prize:8}  [{', '.join(genders)}]")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
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
