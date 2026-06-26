#!/usr/bin/env python3
"""
storyworlds/worlds/firm_humor_conflict_comedy.py
================================================

A compact story world about a small firm, a silly mistake, and a comedy-flavored
compromise.

Seed premise:
- A child visits a friendly little firm.
- The child loves a funny office toy or task.
- The toy/task can make a mess or cause a comic problem.
- A parent or caretaker warns them, tension builds, and then a practical,
  reasonable fix lets the story end happily.

This world is designed to be child-facing, grounded in a simple simulated state,
and easy to verify with both Python and an inline ASP twin.
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
            self.meters = {"mess": 0.0, "dirty": 0.0, "workload": 0.0, "wobble": 0.0}
        if not self.memes:
            self.memes = {"joy": 0.0, "love": 0.0, "worry": 0.0, "conflict": 0.0,
                          "desire": 0.0, "amusement": 0.0, "relief": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "aunt"}
        male = {"boy", "father", "dad", "man", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the little firm"
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
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.zone: set[str] = set()
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
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    apply: callable


def _r_mess(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters["mess"] < THRESHOLD:
            continue
        for item in world.worn_items(actor):
            if item.protective or item.region not in world.zone or world.covered(actor, item.region):
                continue
            sig = ("mess", actor.id, item.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            item.meters["dirty"] += 1
            out.append(f"{actor.id}'s {item.label} got dirty.")
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
        out.append(f"That would make extra work for {carer.label}.")
    return out


CAUSAL_RULES = [Rule("mess", _r_mess), Rule("worry", _r_worry)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            bits = rule.apply(world)
            if bits:
                changed = True
                produced.extend(bits)
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
    return {"soiled": bool(prize and prize.meters["dirty"] >= THRESHOLD)}


def _do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    if activity.id not in world.setting.affords:
        return
    world.zone = set(activity.zone)
    actor.meters[activity.mess] += 1
    actor.memes["joy"] += 1
    actor.memes["amusement"] += 1
    propagate(world, narrate=narrate)


def intro(world: World, hero: Entity) -> None:
    world.say(f"{hero.id} was a little {hero.type} who loved the busy, friendly firm.")


def loves_activity(world: World, hero: Entity, activity: Activity) -> None:
    world.say(
        f"{hero.pronoun().capitalize()} loved {activity.gerund} because the whole thing felt like a joke that had learned to walk."
    )


def buys(world: World, parent: Entity, hero: Entity, prize: Entity) -> None:
    world.say(f"One morning, {hero.pronoun('possessive')} {parent.label} brought {hero.pronoun('object')} {prize.phrase} for the day at the firm.")


def loves_prize(world: World, hero: Entity, prize: Entity) -> None:
    hero.memes["love"] += 1
    prize.worn_by = hero.id
    world.say(f"{hero.id} loved {hero.pronoun('possessive')} {prize.label} and wore {prize.it()} proudly.")


def arrive(world: World, hero: Entity, parent: Entity, activity: Activity) -> None:
    world.say(f"At the little firm, the desks were neat, the papers were stacked high, and everything looked almost too serious for {activity.keyword}.")
    world.say(f"Still, {hero.id} wanted to {activity.verb} right away.")


def warn(world: World, parent: Entity, hero: Entity, activity: Activity, prize: Entity) -> bool:
    pred = predict_mess(world, hero, activity, prize.id)
    if not pred["soiled"]:
        return False
    world.say(f'"If you {activity.verb}, your {prize.label} will get {activity.soil}," {parent.label} said. "And then we will all have a frown at the firm."')
    return True


def defies(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["desire"] += 1
    hero.memes["conflict"] += 1
    world.say(f"{hero.id} tried to {activity.rush}, but the wish to play was bigger than {hero.pronoun('possessive')} careful thoughts.")


def joke_turn(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["amusement"] += 1
    world.say(f"Then {hero.id} giggled, because even the serious papers seemed to listen to the silly little boing of {activity.keyword}.")


def compromise(world: World, parent: Entity, hero: Entity, activity: Activity, prize: Entity) -> Optional[Gear]:
    gear = select_gear(activity, prize)
    if gear is None:
        return None
    inst = world.add(Entity(
        id=gear.id,
        type="gear",
        label=gear.label,
        owner=hero.id,
        caretaker=parent.id,
        protective=True,
        covers=set(gear.covers),
        plural=gear.plural,
    ))
    inst.worn_by = hero.id
    if predict_mess(world, hero, activity, prize.id)["soiled"]:
        inst.worn_by = None
        del world.entities[inst.id]
        return None
    world.say(f'"How about we {gear.prep} first?" {parent.label} asked. "Then you can {activity.verb} without making the firm look like a joke went off in the copier."')
    return gear


def accept(world: World, parent: Entity, hero: Entity, activity: Activity, prize: Entity, gear: Gear) -> None:
    hero.memes["joy"] += 1
    hero.memes["love"] += 1
    hero.memes["conflict"] = 0.0
    hero.memes["relief"] += 1
    world.say(f"{hero.id} smiled, hugged {hero.pronoun('possessive')} {parent.label}, and agreed to the plan.")
    world.say(f"Soon {hero.id} was {activity.gerund}, {prize.label} stayed clean, and the firm was full of happy laughter instead of worry.")


def tell(setting: Setting, activity: Activity, prize_cfg: Prize, hero_name: str = "Mina", hero_type: str = "girl",
         parent_type: str = "mother") -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label="mom"))
    prize = world.add(Entity(
        id="prize",
        type=prize_cfg.type,
        label=prize_cfg.label,
        phrase=prize_cfg.phrase,
        owner=hero.id,
        caretaker=parent.id,
        region=prize_cfg.region,
        plural=prize_cfg.plural,
    ))

    intro(world, hero)
    loves_activity(world, hero, activity)
    buys(world, parent, hero, prize)
    loves_prize(world, hero, prize)
    world.para()
    arrive(world, hero, parent, activity)
    warn(world, parent, hero, activity, prize)
    defies(world, hero, activity)
    joke_turn(world, hero, activity)
    world.para()
    gear = compromise(world, parent, hero, activity, prize)
    if gear:
        accept(world, parent, hero, activity, prize, gear)

    world.facts.update(hero=hero, parent=parent, prize=prize, activity=activity, gear=gear)
    return world


SETTINGS = {
    "firm": Setting(place="the little firm", affords={"stamp"}),
    "office": Setting(place="the office", affords={"stamp", "bounce"}),
    "studio": Setting(place="the studio firm", affords={"paint"}),
}

ACTIVITIES = {
    "stamp": Activity(
        id="stamp",
        verb="stamp the funny label",
        gerund="stamping funny labels",
        rush="dash to the stamp pad",
        mess="inky",
        soil="spotty with ink",
        zone={"torso", "hands"},
        keyword="stamp",
        tags={"humor", "ink"},
    ),
    "bounce": Activity(
        id="bounce",
        verb="bounce the rubber ball",
        gerund="bouncing the rubber ball",
        rush="race after the ball",
        mess="scattered",
        soil="scattered everywhere",
        zone={"floor"},
        keyword="ball",
        tags={"humor", "bounce"},
    ),
    "paint": Activity(
        id="paint",
        verb="paint a silly sign",
        gerund="painting silly signs",
        rush="grab the paint brush",
        mess="painted",
        soil="splashed with paint",
        zone={"torso", "hands"},
        keyword="paint",
        tags={"humor", "paint"},
    ),
}

PRIZES = {
    "shirt": Prize(label="shirt", phrase="a crisp white shirt", type="shirt", region="torso"),
    "tie": Prize(label="tie", phrase="a neat red tie", type="tie", region="torso"),
    "papers": Prize(label="papers", phrase="a stack of important papers", type="papers", region="hands", plural=True),
}

GEAR = [
    Gear(id="apron", label="an apron", covers={"torso", "hands"}, guards={"inky", "painted"}, prep="put on an apron", tail="put on the apron", plural=False),
    Gear(id="paperweight", label="a heavy paperweight", covers={"hands"}, guards={"scattered"}, prep="set out the paperweight", tail="set out the paperweight", plural=False),
    Gear(id="smock", label="an old smock", covers={"torso", "hands"}, guards={"painted", "inky"}, prep="pull on the old smock", tail="pulled on the old smock", plural=False),
]

GIRL_NAMES = ["Mina", "Pia", "Lena", "Nora", "Zia"]
BOY_NAMES = ["Leo", "Finn", "Omar", "Ben", "Theo"]
TRAITS = ["playful", "curious", "cheerful", "silly"]


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


def valid_combos() -> list[tuple[str, str, str]]:
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
    hero, parent, act, prize = f["hero"], f["parent"], f["activity"], f["prize"]
    return [
        f'Write a short comedy about a child named {hero.id} at a small firm who wants to {act.verb} but must keep {prize.label} clean.',
        f"Tell a funny but gentle story where {hero.id} and {parent.label} solve a little office problem without ruining the {prize.label}.",
        f'Write a child-friendly story that includes the word "firm" and ends with laughter after a careful compromise.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, parent, act, prize = f["hero"], f["parent"], f["activity"], f["prize"]
    gear = f.get("gear")
    qa = [
        QAItem(
            question=f"Who wanted to {act.verb} at the firm?",
            answer=f"{hero.id} wanted to {act.verb} at the firm, even though the day was supposed to stay neat and orderly.",
        ),
        QAItem(
            question=f"Why did {parent.label} worry about {prize.label}?",
            answer=f"{parent.label} worried because if {hero.id} did {act.verb}, {prize.label} would get {act.soil}.",
        ),
        QAItem(
            question="What made the story funny?",
            answer=f"The story was funny because the serious little firm got mixed up with {act.keyword}, silly giggles, and a problem that needed a careful fix.",
        ),
    ]
    if gear is not None:
        qa.append(QAItem(
            question=f"How did {gear.label} help?",
            answer=f"{gear.label.capitalize()} helped by covering the right parts so {hero.id} could {act.verb} without ruining the {prize.label}.",
        ))
        qa.append(QAItem(
            question=f"How did {hero.id} feel at the end?",
            answer=f"{hero.id} felt happy and relieved at the end, because the family found a funny, safe way to keep playing at the firm.",
        ))
    return qa


KNOWLEDGE = {
    "firm": [("What is a firm?", "A firm is a business or company where people work together to do a job.")],
    "apron": [("What is an apron for?", "An apron helps protect clothes from spills, paint, or ink while you work.")],
    "paperweight": [("What does a paperweight do?", "A paperweight is a heavy object that keeps papers from blowing or sliding away.")],
    "ink": [("Why can ink be messy?", "Ink can be messy because it can leave dark spots on clothes, hands, and paper.")],
    "paint": [("Why do people use a smock when painting?", "A smock helps keep paint off your clothes so they stay clean.")],
    "bounce": [("Why do balls bounce?", "Balls bounce because they are springy and push back after they hit the ground.")],
    "humor": [("What makes a joke funny?", "A joke can be funny when it surprises you in a silly, harmless way.")],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["activity"].tags)
    tags.add("firm")
    if world.facts.get("gear"):
        tags.add(world.facts["gear"].id)
    out: list[QAItem] = []
    for tag, items in KNOWLEDGE.items():
        if tag in tags:
            out.extend(QAItem(question=q, answer=a) for q, a in items)
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
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
        if e.region:
            bits.append(f"region={e.region}")
        lines.append(f"{e.id}: {e.type} {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="firm", activity="stamp", prize="shirt", name="Mina", gender="girl", parent="mother", trait="playful"),
    StoryParams(place="office", activity="bounce", prize="papers", name="Leo", gender="boy", parent="father", trait="silly"),
    StoryParams(place="studio", activity="paint", prize="tie", name="Nora", gender="girl", parent="mother", trait="curious"),
]


def explain_rejection(activity: Activity, prize: Prize) -> str:
    if not prize_at_risk(activity, prize):
        return f"(No story: {activity.gerund} would not really touch the {prize.label}, so there is no honest conflict.)"
    return f"(No story: nothing in the gear list safely fixes {activity.gerund} and keeps the {prize.label} clean.)"


def explain_gender(prize_id: str, gender: str) -> str:
    ok = " / ".join(sorted(PRIZES[prize_id].genders))
    return f"(No story: that prize does not fit the requested {gender} child here; try {ok}.)"


ASP_RULES = r"""
prize_at_risk(A,P) :- splashes(A,R), worn_on(P,R).
protects(G,A,P) :- prize_at_risk(A,P), mess_of(A,M), guards(G,M), covers(G,R), worn_on(P,R).
has_fix(A,P) :- protects(_,A,P).
valid(Place,A,P) :- affords(Place,A), prize_at_risk(A,P), has_fix(A,P).
valid_story(Place,A,P,G) :- valid(Place,A,P), wears(G,P).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
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
    a = set(asp_valid_combos())
    b = set(valid_combos())
    if a == b:
        print(f"OK: clingo gate matches valid_combos() ({len(a)} combos).")
        return 0
    print("MISMATCH:")
    if a - b:
        print("  only in clingo:", sorted(a - b))
    if b - a:
        print("  only in python:", sorted(b - a))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Comedy story world about a tiny firm, a silly mishap, and a safe compromise.")
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
    if args.gender and args.prize and args.gender not in PRIZES[args.prize].genders:
        raise StoryError(explain_gender(args.prize, args.gender))
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.activity is None or c[1] == args.activity)
              and (args.prize is None or c[2] == args.prize)]
    if args.gender:
        combos = [c for c in combos if args.gender in PRIZES[c[2]].genders]
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
    world = tell(SETTINGS[params.place], ACTIVITIES[params.activity], PRIZES[params.prize], params.name, params.gender, params.parent)
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
        print(f"{len(triples)} compatible combos ({len(stories)} with gender):\n")
        for place, act, prize in triples:
            genders = sorted(g for (pl, a, pr, g) in stories if (pl, a, pr) == (place, act, prize))
            print(f"  {place:8} {act:8} {prize:8}  [{', '.join(genders)}]")
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
