#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/pain_wuss_magic_space_adventure.py
==============================================================================================================

A small space-adventure storyworld with a magical helper, a worried child, and
a safe compromise that turns fear of pain into brave curiosity.

The seed-inspired premise is simple:
- a child wants to do a daring space activity,
- the child is worried about pain and about seeming like a wuss,
- a trusted adult notices the risk,
- magic gear makes the adventure safe,
- the ending image proves the child changed.

The world is constrained and simulation-driven:
physical state uses meters, emotional state uses memes, and the narration is
assembled from the world model rather than from a frozen template.
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
        for k in ["pain", "danger", "work", "dust"]:
            self.meters.setdefault(k, 0.0)
        for k in ["joy", "fear", "worry", "resolve", "shame", "confidence", "love"]:
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "captain"}
        male = {"boy", "father", "dad", "man", "pilot"}
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
    indoors: bool = False
    affords: set[str] = field(default_factory=set)


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    hazard: str
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


def _r_pain(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters["danger"] < THRESHOLD:
            continue
        for item in world.worn_items(actor):
            if item.protective or item.region not in world.zone or world.covered(actor, item.region):
                continue
            sig = ("pain", item.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            item.meters["dust"] += 1
            actor.memes["fear"] += 1
            out.append(f"{actor.id} felt a sharp pain through {item.label}.")
    return out


def _r_work(world: World) -> list[str]:
    out: list[str] = []
    for item in world.entities.values():
        if item.meters["dust"] < THRESHOLD or not item.caretaker:
            continue
        sig = ("work", item.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        caretaker = world.get(item.caretaker)
        caretaker.meters["work"] += 1
        out.append(f"That would mean more work for {caretaker.id}.")
    return out


CAUSAL_RULES = [_r_pain, _r_work]


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


def prize_at_risk(activity: Activity, prize: Prize) -> bool:
    return prize.region in activity.zone


def select_gear(activity: Activity, prize: Prize) -> Optional[Gear]:
    for gear in GEAR:
        if activity.hazard in gear.guards and prize.region in gear.covers:
            return gear
    return None


def predict_hurt(world: World, actor: Entity, activity: Activity, prize_id: str) -> dict:
    sim = world.copy()
    _do_activity(sim, sim.get(actor.id), activity, narrate=False)
    prize = sim.entities.get(prize_id)
    return {"hurt": bool(prize and prize.meters["dust"] >= THRESHOLD), "work": sum(e.meters["work"] for e in sim.characters())}


def _do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    if activity.id not in world.setting.affords:
        raise StoryError("The chosen place cannot host that space activity.")
    world.zone = set(activity.zone)
    actor.meters["danger"] += 1
    actor.memes["resolve"] += 1
    propagate(world, narrate=narrate)


def intro(world: World, hero: Entity) -> None:
    world.say(f"{hero.id} was a little {hero.type} who loved the shiny edge of space.")


def love_activity(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["joy"] += 1
    world.say(f"{hero.pronoun().capitalize()} loved {activity.gerund}, because it made the whole ship feel like an adventure.")


def buy_prize(world: World, parent: Entity, hero: Entity, prize: Entity) -> None:
    world.say(f"One day, {hero.pronoun('possessive')} {parent.id} brought home {hero.pronoun('object')} {prize.phrase}.")


def love_prize(world: World, hero: Entity, prize: Entity) -> None:
    hero.memes["love"] += 1
    prize.worn_by = hero.id
    world.say(f"{hero.id} loved {hero.pronoun('possessive')} {prize.label} and wore {prize.it()} everywhere.")


def arrive(world: World, hero: Entity, parent: Entity, activity: Activity) -> None:
    world.say(f"One day, {hero.id} and {hero.pronoun('possessive')} {parent.id} went to {world.setting.place}.")
    world.say(f"The place was full of {activity.keyword} lights and a few blinking panels.")


def wants(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["worry"] += 1
    world.say(f"{hero.id} wanted to {activity.verb}, but {hero.pronoun('subject')} worried about pain and about seeming like a wuss.")


def warn(world: World, parent: Entity, hero: Entity, activity: Activity, prize: Entity) -> None:
    pred = predict_hurt(world, hero, activity, prize.id)
    if pred["hurt"]:
        world.facts["predicted_hurt"] = True
        world.facts["predicted_work"] = pred["work"]
        world.say(f'"If you rush in now, your {prize.label} could get hurt," {parent.id} said. "Let\'s find the magic way."')


def hesitate(world: World, hero: Entity) -> None:
    hero.memes["shame"] += 1
    world.say(f"{hero.id} bit {hero.pronoun('possessive')} lip. {hero.pronoun().capitalize()} did not want anyone to think {hero.pronoun('subject')} was a wuss.")


def offer_magic(world: World, parent: Entity, hero: Entity, activity: Activity, prize: Entity) -> Optional[Gear]:
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
    if predict_hurt(world, hero, activity, prize.id)["hurt"]:
        gear.worn_by = None
        del world.entities[gear.id]
        return None
    world.say(f"{parent.id} smiled and lifted the magic {gear_def.label}.")
    world.say(f'"How about we {gear_def.prep}?" {parent.id} asked.')
    return gear_def


def accept(world: World, parent: Entity, hero: Entity, activity: Activity, prize: Entity, gear_def: Gear) -> None:
    hero.memes["fear"] = 0.0
    hero.memes["shame"] = 0.0
    hero.memes["confidence"] += 1
    hero.memes["joy"] += 1
    world.say(f"{hero.id}'s eyes got bright. {hero.id} hugged {hero.pronoun('possessive')} {parent.id}.")
    world.say(f'"Okay," {hero.id} said. "I can be careful without being a wuss."')
    world.say(f"They {gear_def.tail}. Soon {hero.id} was {activity.gerund}, and {prize.label} stayed clean and safe.")


def tell(setting: Setting, activity: Activity, prize_cfg: Prize, hero_name: str = "Mira", hero_type: str = "girl",
         parent_type: str = "mother", trait: str = "brave") -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, traits=["little", trait, "curious"]))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type))
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
    love_activity(world, hero, activity)
    buy_prize(world, parent, hero, prize)
    love_prize(world, hero, prize)

    world.para()
    arrive(world, hero, parent, activity)
    wants(world, hero, activity)
    warn(world, parent, hero, activity, prize)
    hesitate(world, hero)

    world.para()
    gear_def = offer_magic(world, parent, hero, activity, prize)
    if gear_def is not None:
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
    "starship": Setting(place="the starship", indoors=True, affords={"cometrun", "asteroid", "moonhop"}),
    "moonbase": Setting(place="the moonbase bay", indoors=True, affords={"cometrun", "asteroid"}),
    "dock": Setting(place="the sky dock", indoors=False, affords={"asteroid", "moonhop"}),
}

ACTIVITIES = {
    "cometrun": Activity(
        id="cometrun",
        verb="run beside the comet trail",
        gerund="running beside comet trails",
        rush="dash toward the comet trail",
        hazard="sparks",
        soil="scuffed and sore",
        zone={"hands", "knees"},
        keyword="comet",
        tags={"space", "comet", "spark"},
    ),
    "asteroid": Activity(
        id="asteroid",
        verb="hop across the asteroid deck",
        gerund="hopping across asteroid decks",
        rush="jump onto the asteroid deck",
        hazard="rocks",
        soil="bumped and dusty",
        zone={"feet", "knees"},
        keyword="asteroid",
        tags={"space", "asteroid", "rock"},
    ),
    "moonhop": Activity(
        id="moonhop",
        verb="jump through the moon tunnel",
        gerund="jumping through moon tunnels",
        rush="leap into the moon tunnel",
        hazard="cold",
        soil="shivery",
        zone={"torso"},
        keyword="moon",
        tags={"space", "moon", "cold"},
    ),
}

PRIZES = {
    "boots": Prize(label="boots", phrase="a pair of bright space boots", type="boots", region="feet", plural=True),
    "pads": Prize(label="pads", phrase="shiny knee pads", type="pads", region="knees", plural=True),
    "cloak": Prize(label="cloak", phrase="a moon cloak", type="cloak", region="torso"),
}

GEAR = [
    Gear(id="magicboots", label="magic boots", covers={"feet"}, guards={"rocks", "cold"}, prep="put on the magic boots first", tail="walked along in the magic boots", plural=True),
    Gear(id="sparkpads", label="spark pads", covers={"hands", "knees"}, guards={"sparks"}, prep="slip on the magic spark pads first", tail="stepped out in the magic spark pads", plural=True),
    Gear(id="mooncloak", label="moon cloak", covers={"torso"}, guards={"cold"}, prep="wrap the moon cloak around you first", tail="glided ahead in the moon cloak"),
]

GIRL_NAMES = ["Mira", "Luna", "Nia", "Zara", "Tess"]
BOY_NAMES = ["Kai", "Leo", "Finn", "Oren", "Max"]
TRAITS = ["brave", "curious", "bold", "gentle", "spirited"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
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
        f'Write a short space adventure story for a young child about "{act.keyword}", magic, and a worried child.',
        f"Tell a gentle story where {hero.id} wants to {act.verb} but worries about pain and about seeming like a wuss.",
        f"Write a child-friendly story set on {world.setting.place} where a parent offers magic gear to keep {prize.label} safe.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, parent, prize, act = f["hero"], f["parent"], f["prize"], f["activity"]
    gear = f.get("gear")
    qa = [
        QAItem(question=f"Who was the story about?", answer=f"It was about {hero.id}, a little {hero.type} who loved space adventures."),
        QAItem(question=f"What did {hero.id} want to do?", answer=f"{hero.id} wanted to {act.verb}, even though {hero.pronoun('subject')} was worried about pain."),
        QAItem(question=f"What did the parent worry about?", answer=f"{parent.id} worried that {hero.pronoun('possessive')} {prize.label} could get hurt if {hero.id} rushed in too fast."),
    ]
    if gear:
        qa.append(QAItem(question=f"What magic thing helped?", answer=f"The magic {gear.label} helped {hero.id} play safely while keeping {prize.label} safe."))
        qa.append(QAItem(question=f"How did the child feel at the end?", answer=f"{hero.id} felt happy and more confident, and did not need to act like a wuss to be safe."))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    act = f["activity"]
    gear = f.get("gear")
    out = [
        QAItem(question="What is a spaceship?", answer="A spaceship is a vehicle made for traveling through space."),
        QAItem(question="What does magic mean in stories?", answer="Magic is a special kind of pretend power that can do amazing things."),
    ]
    if "space" in act.tags:
        out.append(QAItem(question="Why wear gear in space?", answer="Space gear helps protect people from cold, sharp bits, and other dangers."))
    if gear and gear.id == "magicboots":
        out.append(QAItem(question="What are boots for?", answer="Boots cover your feet and help keep them safe when the ground is rough or cold."))
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
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="starship", activity="cometrun", prize="pads", name="Mira", gender="girl", parent="mother", trait="brave"),
    StoryParams(place="moonbase", activity="asteroid", prize="boots", name="Kai", gender="boy", parent="father", trait="curious"),
    StoryParams(place="dock", activity="moonhop", prize="cloak", name="Luna", gender="girl", parent="mother", trait="gentle"),
]


def explain_rejection(activity: Activity, prize: Prize) -> str:
    if not prize_at_risk(activity, prize):
        return f"(No story: {activity.gerund} does not put {prize.label} in danger.)"
    return f"(No story: the magic gear catalog cannot safely protect {prize.label} from {activity.gerund}.)"


def explain_gender(prize_id: str, gender: str) -> str:
    ok = " / ".join(sorted(PRIZES[prize_id].genders))
    return f"(No story: that {PRIZES[prize_id].label} story does not fit a {gender}; try {ok}.)"


ASP_RULES = r"""
prize_at_risk(A,P) :- splashes(A,R), worn_on(P,R).
protects(G,A,P) :- gear(G), prize_at_risk(A,P), mess_of(A,M), guards(G,M), covers(G,R), worn_on(P,R).
has_fix(A,P) :- protects(_,A,P).
valid(Place,A,P) :- affords(Place,A), prize_at_risk(A,P), has_fix(A,P).
valid_story(Place,A,P,Gender) :- valid(Place,A,P), wears(Gender,P).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        if s.indoors:
            lines.append(asp.fact("indoors", pid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", pid, a))
    for aid, a in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        lines.append(asp.fact("mess_of", aid, a.hazard))
        for r in sorted(a.zone):
            lines.append(asp.fact("splashes", aid, r))
    for pid, pr in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("worn_on", pid, pr.region))
        if pr.plural:
            lines.append(asp.fact("prize_plural", pid))
        for g in sorted(pr.genders):
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
    a, p = set(asp_valid_combos()), set(valid_combos())
    if a == p:
        print(f"OK: clingo gate matches valid_combos() ({len(a)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if a - p:
        print("  only in clingo:", sorted(a - p))
    if p - a:
        print("  only in python:", sorted(p - a))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Space adventure storyworld with magic, pain, and a safe compromise.")
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
              and (args.prize is None or c[2] == args.prize)
              and (args.gender is None or args.gender in PRIZES[c[2]].genders)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, activity, prize_id = rng.choice(sorted(combos))
    prize = PRIZES[prize_id]
    gender = args.gender or rng.choice(sorted(prize.genders))
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, activity=activity, prize=prize_id, name=name, gender=gender, parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], ACTIVITIES[params.activity], PRIZES[params.prize],
                 params.name, params.gender, params.parent, params.trait)
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
            print(f"  {place:9} {act:10} {prize:8}  [{', '.join(genders)}]")
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
