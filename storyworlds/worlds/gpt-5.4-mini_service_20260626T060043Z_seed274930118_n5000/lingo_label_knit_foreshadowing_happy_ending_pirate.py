#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/lingo_label_knit_foreshadowing_happy_ending_pirate.py
===========================================================================================================

A standalone story world for a tiny Pirate Tale domain with foreshadowing and a
happy ending.

Seed-tale inspiration:
---
A little pirate loves the sea, the pirate lingo, and a shiny label on a prize
bag. Before a stormy trip, a grown-up notices the wind and warns that a knitted
shawl will get soaked. The child wants to go anyway, but a better plan appears:
put on weatherproof gear, keep the lingo, keep the courage, and sail safely.
In the end, the crew reaches the cove, rescues the prize, and celebrates.

This world models:
- physical meters: wetness, roughness, tornness, treasure, windiness
- emotional memes: joy, worry, bravado, relief, love, conflict
- causal foreshadowing: cloud and wind signs predict trouble
- a happy ending: compatible gear prevents the loss and the crew sails on
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0

REGIONS = {"head", "torso", "feet", "hands", "neck"}


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
        for k in ["wet", "rough", "torn", "treasure", "wind"]:
            self.meters.setdefault(k, 0.0)
        for k in ["joy", "worry", "bravado", "relief", "love", "conflict"]:
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "captain"}
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
        self.wind_signs: int = 0
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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.wind_signs = self.wind_signs
        clone.paragraphs = [[]]
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


MESS_KINDS = {"wet", "torn", "rough"}


def _r_soak(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters["wet"] < THRESHOLD:
            continue
        for item in world.worn_items(actor):
            if item.protective:
                continue
            if item.region not in {"head", "torso", "hands", "neck"}:
                continue
            if world.covered(actor, item.region):
                continue
            sig = ("soak", actor.id, item.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            item.meters["wet"] += 1
            item.meters["rough"] += 1
            out.append(f"{actor.id}'s {item.label} got soaked by the sea spray.")
    return out


def _r_tear(world: World) -> list[str]:
    out: list[str] = []
    for item in list(world.entities.values()):
        if item.meters["wet"] < THRESHOLD:
            continue
        if item.label != "knitted shawl":
            continue
        sig = ("tear", item.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        item.meters["torn"] += 1
        out.append("The knitted shawl sagged and looked close to ruined.")
    return out


def _r_worry(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters["wind"] < THRESHOLD or actor.memes["worry"] >= THRESHOLD:
            continue
        sig = ("worry", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["worry"] += 1
        out.append("The wind signs made the captain worry.")
    return out


CAUSAL_RULES = [
    Rule("soak", "physical", _r_soak),
    Rule("tear", "physical", _r_tear),
    Rule("worry", "social", _r_worry),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
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
        if activity.mess in gear.guards and prize.region in gear.covers:
            return gear
    return None


def predict_mess(world: World, actor: Entity, activity: Activity, prize_id: str) -> dict:
    sim = world.copy()
    _do_activity(sim, sim.get(actor.id), activity, narrate=False)
    prize = sim.entities.get(prize_id)
    return {
        "soiled": bool(prize and prize.meters["torn"] >= THRESHOLD or prize and prize.meters["wet"] >= THRESHOLD),
        "worry": sum(e.memes["worry"] for e in sim.characters()),
    }


def activity_delight(activity: Activity) -> str:
    return {
        "sail": "the mast creaked like a sea song",
        "storm": "the gray clouds looked like a grumpy old whale",
        "dock": "the ropes and planks felt ready for an adventure",
    }.get(activity.id, "the whole day felt full of sea breeze")


def setting_detail(setting: Setting, activity: Activity) -> str:
    if setting.place == "the cove":
        return "The cove gleamed under a strip of bright water."
    if setting.place == "the dock":
        return "The dock bobbed gently, and gulls cried overhead."
    return f"{setting.place.capitalize()} looked busy and salty."


def _do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    if activity.id not in world.setting.affords:
        raise StoryError(f"The setting {world.setting.place} cannot host {activity.id}.")
    actor.meters[activity.mess] += 1
    actor.meters["wind"] += 1
    actor.memes["bravado"] += 1
    world.wind_signs += 1
    propagate(world, narrate=narrate)


def introduce(world: World, hero: Entity) -> None:
    trait = next((t for t in hero.traits if t != "little"), "")
    world.say(f"{hero.id} was a little {trait} pirate who loved every salty word and shiny label on deck.")


def loves_lingo(world: World, hero: Entity) -> None:
    hero.memes["love"] += 1
    world.say(f'{hero.pronoun().capitalize()} loved pirate lingo and shouted "Ahoy!" whenever the breeze felt brave.')


def buys(world: World, parent: Entity, hero: Entity, prize: Entity) -> None:
    world.say(f"One morning, {hero.pronoun('possessive')} {parent.type} bought {hero.pronoun('object')} {prize.phrase}.")


def loves_prize(world: World, hero: Entity, prize: Entity) -> None:
    hero.memes["love"] += 1
    prize.worn_by = hero.id
    world.say(f"{hero.id} loved {hero.pronoun('possessive')} {prize.label} and wore {prize.it()} like a lucky flag.")


def arrive(world: World, hero: Entity, parent: Entity, activity: Activity) -> None:
    world.say(f"One windy day, {hero.id} and {hero.pronoun('possessive')} {parent.type} went to {world.setting.place}.")
    world.say(setting_detail(world.setting, activity))


def foreshadow(world: World, parent: Entity, hero: Entity, activity: Activity, prize: Entity) -> bool:
    pred = predict_mess(world, hero, activity, prize.id)
    if not pred["soiled"]:
        return False
    world.facts["predicted_loss"] = True
    world.say(f'"Those clouds mean trouble," {parent.pronoun()} said. "Your {prize.label} could get ruined out there."')
    return True


def defies(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["conflict"] += 1
    world.say(f"{hero.id} still wanted to {activity.verb}, and {hero.pronoun()} stomped a small boot in the sand.")


def offer_gear(world: World, parent: Entity, hero: Entity, activity: Activity, prize: Entity) -> Optional[Gear]:
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
    if predict_mess(world, hero, activity, prize.id)["soiled"]:
        gear.worn_by = None
        del world.entities[gear.id]
        return None
    world.say(f'{parent.pronoun("possessive").capitalize()} {parent.type} smiled and said, "{gear_def.prep}."')
    return gear


def accept(world: World, parent: Entity, hero: Entity, activity: Activity, prize: Entity, gear_def: Gear) -> None:
    hero.memes["joy"] += 1
    hero.memes["love"] += 1
    hero.memes["conflict"] = 0.0
    hero.memes["relief"] += 1
    world.say(f"{hero.id} grinned, nodded, and hugged {hero.pronoun('possessive')} {parent.type}.")
    world.say(
        f'They {gear_def.tail}. Soon {hero.id} was {activity.gerund}, '
        f'{prize.label} safe and clean, and the crew was cheering, "Yo-ho-ho!"'
    )


def tell(setting: Setting, activity: Activity, prize_cfg: Prize,
         hero_name: str = "Nell", hero_type: str = "girl",
         hero_traits: Optional[list[str]] = None, parent_type: str = "captain") -> World:
    world = World(setting)
    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type=hero_type,
        traits=["little"] + (hero_traits or ["brave", "curious"]),
    ))
    parent = world.add(Entity(id="Captain", kind="character", type=parent_type))
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

    introduce(world, hero)
    loves_lingo(world, hero)
    buys(world, parent, hero, prize)
    loves_prize(world, hero, prize)

    world.para()
    arrive(world, hero, parent, activity)
    foreshadow(world, parent, hero, activity, prize)
    defies(world, hero, activity)
    _do_activity(world, hero, activity, narrate=True)

    world.para()
    gear_def = offer_gear(world, parent, hero, activity, prize)
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
    "dock": Setting(place="the dock", affords={"sail", "storm"}),
    "cove": Setting(place="the cove", affords={"sail", "storm"}),
    "ship": Setting(place="the ship", affords={"sail", "storm"}),
}

ACTIVITIES = {
    "sail": Activity(
        id="sail",
        verb="sail out to the cove",
        gerund="sailing out to the cove",
        rush="dash to the rigging",
        mess="wet",
        soil="soaked",
        zone={"head", "torso", "hands"},
        weather="windy",
        keyword="ahoy",
        tags={"sea", "wet", "pirate"},
    ),
    "storm": Activity(
        id="storm",
        verb="race through the storm",
        gerund="racing through the storm",
        rush="charge toward the waves",
        mess="wet",
        soil="ruined by spray",
        zone={"head", "torso", "hands", "feet"},
        weather="stormy",
        keyword="storm",
        tags={"sea", "wet", "pirate", "wind"},
    ),
}

PRIZES = {
    "shawl": Prize(
        label="shawl",
        phrase="a knitted shawl with a bright blue label",
        type="shawl",
        region="torso",
    ),
    "map": Prize(
        label="map",
        phrase="a folded treasure map with a red label",
        type="map",
        region="hands",
        plural=False,
    ),
}

GEAR = [
    Gear(
        id="oilskin",
        label="an oilskin coat",
        covers={"torso"},
        guards={"wet"},
        prep="put on an oilskin coat first",
        tail="sailed back out with the oilskin coat on",
    ),
    Gear(
        id="gloves",
        label="seafarer gloves",
        covers={"hands"},
        guards={"wet"},
        prep="pull on the seafarer gloves first",
        tail="headed off with the seafarer gloves on",
        plural=True,
    ),
    Gear(
        id="hood",
        label="a hooded sea cloak",
        covers={"head", "torso"},
        guards={"wet"},
        prep="tie on a hooded sea cloak first",
        tail="went back out in the hooded sea cloak",
    ),
]

GIRL_NAMES = ["Nell", "Mira", "Ruby", "Tess", "Ivy", "Poppy"]
BOY_NAMES = ["Finn", "Jett", "Rory", "Kai", "Pax", "Beau"]
TRAITS = ["brave", "curious", "cheerful", "spirited", "merry"]


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


KNOWLEDGE = {
    "sea": [("What is the sea?", "The sea is a huge body of salt water that waves and wind can move.")],
    "wind": [("What does wind do on a ship?", "Wind can fill the sails and help a ship move across the water.")],
    "pirate": [("What is pirate lingo?", "Pirate lingo is the funny talking style pirates use, like 'ahoy' and 'yo-ho-ho'.")],
    "wet": [("Why do wet clothes feel heavy?", "Wet clothes feel heavy because they soak up water and hold it inside the fabric.")],
    "map": [("What is a map?", "A map is a picture that shows where places are and how to get there.")],
    "shawl": [("What is a shawl?", "A shawl is a cloth you wrap around your shoulders to help keep warm.")],
    "knit": [("What does it mean to knit?", "To knit means to make cloth by looping yarn together with needles or by handwork.")],
    "label": [("What is a label?", "A label is a small tag or mark that names what something is or who it belongs to.")],
}


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, parent, act, prize = f["hero"], f["parent"], f["activity"], f["prize_cfg"]
    return [
        f'Write a short pirate story for a young child that includes the words "lingo", "label", and "knit".',
        f"Tell a sea-faring story where {hero.id} wants to {act.verb} but {hero.pronoun('possessive')} {parent.type} warns about {prize.phrase}.",
        f"Write a happy-ending pirate tale with a foreshadowing warning, a safer plan, and a cheerful final voyage.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, parent, prize, act = f["hero"], f["parent"], f["prize"], f["activity"]
    qa = [
        QAItem(
            question=f"Who is the pirate story about?",
            answer=f"It is about {hero.id}, a little {hero.type} pirate, and {hero.pronoun('possessive')} {parent.type}.",
        ),
        QAItem(
            question=f"What did {hero.id} want to do at {world.setting.place}?",
            answer=f"{hero.id} wanted to {act.verb} and hear the sea sing under the wind.",
        ),
        QAItem(
            question=f"Why did {parent.type} warn {hero.id} about {prize.label}?",
            answer=f"{parent.pronoun().capitalize()} warned because {prize.label} could get wet and ruined in the spray.",
        ),
    ]
    if f.get("resolved"):
        gear = f["gear"]
        qa.append(QAItem(
            question=f"How did the crew keep {prize.label} safe?",
            answer=f"They used {gear.label} first, so {hero.id} could {act.verb} without ruining {hero.pronoun('possessive')} {prize.label}.",
        ))
        qa.append(QAItem(
            question=f"How did the story end?",
            answer=f"It ended happily, with {hero.id} {act.gerund} and everyone cheering in pirate lingo.",
        ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["activity"].tags)
    tags.update({"pirate", "label", "knit"})
    out: list[QAItem] = []
    for tag in ["pirate", "sea", "wind", "wet", "map", "shawl", "knit", "label"]:
        if tag in tags:
            out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE[tag])
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
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.protective:
            bits.append(f"covers={sorted(e.covers)}")
        elif e.region:
            bits.append(f"region={e.region}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  wind signs: {world.wind_signs}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="dock", activity="sail", prize="shawl", name="Nell", gender="girl", parent="captain", trait="brave"),
    StoryParams(place="cove", activity="storm", prize="map", name="Finn", gender="boy", parent="captain", trait="curious"),
]


def explain_rejection(activity: Activity, prize: Prize) -> str:
    if not prize_at_risk(activity, prize):
        return f"(No story: {activity.gerund} would not endanger {prize.label}, so the foreshadowing would have no honest warning.)"
    return f"(No story: there is no gear here that both fits the danger and keeps {prize.label} safe.)"


def explain_gender(prize_id: str, gender: str) -> str:
    ok = " / ".join(sorted(PRIZES[prize_id].genders))
    return f"(No story: a {PRIZES[prize_id].label} isn't set up for {gender} here; try --gender {ok}.)"


ASP_RULES = r"""
prize_at_risk(A, P) :- splashes(A, R), worn_on(P, R).
protects(G, A, P) :- gear(G), prize_at_risk(A, P), mess_of(A, M), guards(G, M), covers(G, R), worn_on(P, R).
has_fix(A, P) :- protects(_, A, P).
valid(Place, A, P) :- affords(Place, A), prize_at_risk(A, P), has_fix(A, P).
valid_story(Place, A, P, Gender) :- valid(Place, A, P), wears(Gender, P).
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
        lines.append(asp.fact("mess_of", aid, a.mess))
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
    ap = argparse.ArgumentParser(description="Pirate tale story world with foreshadowing and a happy ending.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["captain"])
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
    parent = args.parent or "captain"
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, activity=activity, prize=prize_id, name=name, gender=gender, parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], ACTIVITIES[params.activity], PRIZES[params.prize],
                 params.name, params.gender, [params.trait, "stubborn"], params.parent)
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
        import asp
        triples, stories = asp_valid_combos(), asp_valid_stories()
        print(f"{len(triples)} compatible (place, activity, prize) combos ({len(stories)} with gender):\n")
        for place, act, prize in triples:
            genders = sorted(g for (pl, a, pr, g) in stories if (pl, a, pr) == (place, act, prize))
            print(f"  {place:9} {act:8} {prize:8}  [{', '.join(genders)}]")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
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
