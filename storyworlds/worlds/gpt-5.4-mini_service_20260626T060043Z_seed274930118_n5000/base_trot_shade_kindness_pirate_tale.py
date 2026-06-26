#!/usr/bin/env python3
"""
storyworlds/worlds/base_trot_shade_kindness_pirate_tale.py
===========================================================

A small pirate-tale storyworld about a youngster at the base, a hot trot in the
sun, and the kindness of finding shade to help everyone keep going.

Premise:
- A little pirate loves to trot around the base by the sea.
- The midday sun can make the journey harsh and can fade a prized hat.

Tension:
- The hero wants to go right away, but the captain worries about the heat.
- If they dash into the open, the hat gets dusty and uncomfortable.

Turn:
- The crew spots a shady sail awning by the base and chooses the cooler path.

Resolution:
- The hero reaches the place with the prize intact and shows kindness by
  sharing the shade with a tired matey.

The storyworld keeps a live model with physical meters and emotional memes so
the prose is state-driven rather than a frozen paragraph with swapped names.
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
    traits: list[str] = field(default_factory=list)

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
    place: str = "the base"
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
        import copy as _copy
        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.zone = set(self.zone)
        clone.weather = self.weather
        clone.paragraphs = [[]]
        return clone


def _default_meters() -> dict[str, float]:
    return {"dusty": 0.0, "hot": 0.0, "dry": 0.0, "dirty": 0.0}


def _default_memes() -> dict[str, float]:
    return {"joy": 0.0, "worry": 0.0, "kindness": 0.0, "conflict": 0.0, "desire": 0.0}


@dataclass
class Rule:
    name: str
    tag: str
    apply: callable


def _r_hot(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters.get("hot", 0.0) < THRESHOLD:
            continue
        for item in world.worn_items(actor):
            if item.protective or item.region not in world.zone:
                continue
            if world.covered(actor, item.region):
                continue
            sig = ("hot", item.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            item.meters["dusty"] = item.meters.get("dusty", 0.0) + 1
            item.meters["dry"] = item.meters.get("dry", 0.0) + 1
            out.append(f"{actor.pronoun('possessive').capitalize()} {item.label} grew dusty in the hot sun.")
    return out


def _r_worry(world: World) -> list[str]:
    out: list[str] = []
    for item in world.entities.values():
        if item.meters.get("dusty", 0.0) < THRESHOLD or not item.caretaker:
            continue
        sig = ("worry", item.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        caregiver = world.get(item.caretaker)
        caregiver.memes["worry"] = caregiver.memes.get("worry", 0.0) + 1
        out.append(f"That made {caregiver.label} worry.")
    return out


def _r_kindness(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.memes.get("kindness", 0.0) < THRESHOLD:
            continue
        sig = ("kindness", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        out.append(f"{actor.id} shared the cool shade with a tired matey.")
    return out


CAUSAL_RULES = [
    Rule("hot", "physical", _r_hot),
    Rule("worry", "social", _r_worry),
    Rule("kindness", "social", _r_kindness),
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
    return {"soiled": bool(prize and prize.meters.get("dirty", 0.0) >= THRESHOLD)}


def _do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    if activity.id not in world.setting.affords:
        return
    world.zone = set(activity.zone)
    actor.meters[activity.mess] = actor.meters.get(activity.mess, 0.0) + 1
    actor.meters["hot"] = actor.meters.get("hot", 0.0) + 1
    actor.memes["joy"] = actor.memes.get("joy", 0.0) + 1
    propagate(world, narrate=narrate)


def introduce(world: World, hero: Entity) -> None:
    trait = next((t for t in hero.traits if t != "little"), "cheery")
    world.say(f"{hero.id} was a little {trait} pirate who loved the base by the sea.")


def loves_activity(world: World, hero: Entity, activity: Activity) -> None:
    world.say(f"{hero.pronoun().capitalize()} loved to {activity.gerund}; {activity.keyword} made every day feel like a voyage.")


def buys(world: World, parent: Entity, hero: Entity, prize: Entity) -> None:
    world.say(f"That morning, {hero.id}'s {parent.label} gave {hero.pronoun('object')} {prize.phrase}.")


def loves_prize(world: World, hero: Entity, prize: Entity) -> None:
    hero.memes["joy"] = hero.memes.get("joy", 0.0) + 1
    prize.worn_by = hero.id
    world.say(f"{hero.id} loved {hero.pronoun('possessive')} {prize.label} and wore {prize.it()} proudly.")


def arrive(world: World, hero: Entity, parent: Entity, activity: Activity) -> None:
    day = "One sunny day, "
    world.say(f"{day}{hero.id} and {hero.pronoun('possessive')} {parent.label} went to {world.setting.place}.")
    world.say("The bright sun sat high, and the deck at the base felt warm underfoot.")


def wants(world: World, hero: Entity, parent: Entity, activity: Activity) -> None:
    hero.memes["desire"] = hero.memes.get("desire", 0.0) + 1
    world.say(f"{hero.id} wanted to {activity.verb} right away, but {hero.pronoun('possessive')} {parent.label} lifted a warning hand.")


def warn(world: World, parent: Entity, hero: Entity, activity: Activity, prize: Entity) -> bool:
    pred = predict_mess(world, hero, activity, prize.id)
    if not pred["soiled"]:
        return False
    world.facts["predicted_soil"] = activity.soil
    world.say(f"\"You'll get your {prize.label} {activity.soil},\" {hero.pronoun('possessive')} {parent.label} said.")
    return True


def defies(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["conflict"] = hero.memes.get("conflict", 0.0) + 1
    world.say(f"{hero.id} huffed, then tried to {activity.rush}.")


def grab_hand(world: World, parent: Entity, hero: Entity, activity: Activity) -> None:
    hero.memes["worry"] = hero.memes.get("worry", 0.0) + 1
    world.say(f"Then {hero.pronoun('possessive')} {parent.label} took {hero.pronoun('possessive')} hand and guided {hero.pronoun('object')} toward the shade.")


def compromise(world: World, parent: Entity, hero: Entity, activity: Activity, prize: Entity) -> Optional[Gear]:
    gear_def = select_gear(activity, prize)
    if gear_def is None:
        return None
    gear = world.add(Entity(
        id=gear_def.id, type="gear", label=gear_def.label, owner=hero.id,
        caretaker=parent.id, protective=True, covers=set(gear_def.covers), plural=gear_def.plural
    ))
    gear.worn_by = hero.id
    if predict_mess(world, hero, activity, prize.id)["soiled"]:
        gear.worn_by = None
        del world.entities[gear.id]
        return None
    world.say(f"{parent.label.capitalize()} smiled. \"How about we {gear_def.prep} and take the shady way?\"")
    return gear_def


def accept(world: World, parent: Entity, hero: Entity, activity: Activity, prize: Entity, gear_def: Gear) -> None:
    hero.memes["joy"] = hero.memes.get("joy", 0.0) + 1
    hero.memes["kindness"] = hero.memes.get("kindness", 0.0) + 1
    hero.memes["conflict"] = 0.0
    world.say(f"{hero.id}'s face lit up. \"Aye!\" {hero.pronoun()} said, and gave the shady spot to a tired matey as well.")
    world.say(f"Soon {hero.id} was {activity.gerund}, {prize.label} stayed clean, and the base looked merry under the sail shade.")


def tell(setting: Setting, activity: Activity, prize_cfg: Prize, hero_name: str = "Pip", hero_type: str = "boy", parent_type: str = "captain") -> World:
    world = World(setting)
    world.weather = activity.weather

    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, traits=["little", "brave", "kind"], meters=_default_meters(), memes=_default_memes()))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label="captain", meters=_default_meters(), memes=_default_memes()))
    prize = world.add(Entity(
        id="prize", type=prize_cfg.type, label=prize_cfg.label, phrase=prize_cfg.phrase,
        owner=hero.id, caretaker=parent.id, region=prize_cfg.region, plural=prize_cfg.plural,
        meters=_default_meters(), memes=_default_memes()
    ))

    introduce(world, hero)
    loves_activity(world, hero, activity)
    buys(world, parent, hero, prize)
    loves_prize(world, hero, prize)

    world.para()
    arrive(world, hero, parent, activity)
    wants(world, hero, parent, activity)
    warn(world, parent, hero, activity, prize)
    defies(world, hero, activity)
    grab_hand(world, parent, hero, activity)

    world.para()
    gear_def = compromise(world, parent, hero, activity, prize)
    if gear_def:
        accept(world, parent, hero, activity, prize, gear_def)

    world.facts.update(hero=hero, parent=parent, prize=prize, prize_cfg=prize_cfg, activity=activity, setting=setting, gear=gear_def, conflict=True, resolved=gear_def is not None)
    return world


SETTINGS = {
    "base": Setting(place="the base", indoor=False, affords={"trot", "shade"}),
    "cove": Setting(place="the cove base", indoor=False, affords={"trot", "shade"}),
}

ACTIVITIES = {
    "trot": Activity(
        id="trot",
        verb="trot to the shady sail",
        gerund="trotting around the base",
        rush="dash to the open deck",
        mess="hot",
        soil="too hot and dusty",
        zone={"torso"},
        weather="sunny",
        keyword="trot",
        tags={"sun", "base", "pirate"},
    ),
    "shade": Activity(
        id="shade",
        verb="rest in the shade",
        gerund="resting in the shade",
        rush="run into the hot sun",
        mess="dry",
        soil="dry and weary",
        zone={"torso"},
        weather="sunny",
        keyword="shade",
        tags={"shade", "sun", "kindness"},
    ),
}

GEAR = [
    Gear(
        id="sailshade",
        label="a canvas sail shade",
        covers={"torso"},
        guards={"hot", "dry"},
        prep="raise the canvas sail shade",
        tail="walked beneath the sail shade",
    ),
    Gear(
        id="sunhat",
        label="a broad sunhat",
        covers={"torso"},
        guards={"hot"},
        prep="put on the broad sunhat first",
        tail="went out under the sunhat",
    ),
]

PRIZES = {
    "hat": Prize(label="hat", phrase="a bright blue pirate hat", type="hat", region="torso"),
    "cloak": Prize(label="cloak", phrase="a red pirate cloak", type="cloak", region="torso"),
}

GIRL_NAMES = ["Mira", "Nina", "Tess", "Rae"]
BOY_NAMES = ["Pip", "Jory", "Finn", "Tate"]
TRAITS = ["brave", "cheery", "spry", "kind"]


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
    "pirate": [("What is a pirate?", "A pirate is a sailor who travels the sea, looking for adventure and treasure.")],
    "shade": [("What is shade?", "Shade is a cool, darker place made when something blocks the sun.")],
    "sun": [("Why does shade feel nice on a hot day?", "Shade feels nice because it helps block the sun and makes the air feel cooler.")],
    "kindness": [("What is kindness?", "Kindness means being gentle, helpful, and thoughtful toward others.")],
    "base": [("What is a base?", "A base is a place where people or a crew keep supplies, rest, and start their trips.")],
}
KNOWLEDGE_ORDER = ["pirate", "base", "sun", "shade", "kindness"]


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
    hero, parent, act, prize = f["hero"], f["parent"], f["activity"], f["prize_cfg"]
    return [
        f'Write a short pirate tale for a child that includes the words "base", "trot", and "shade".',
        f"Tell a gentle story where {hero.id} wants to {act.verb} at {world.setting.place} but the captain worries about {prize.phrase}.",
        f"Write a story about kindness on a sunny day at the base, ending with a cool shady place for a tired matey.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, parent, prize, act = f["hero"], f["parent"], f["prize"], f["activity"]
    qa = [
        QAItem(
            question=f"Who is the story about when {hero.id} visits {world.setting.place} to {act.verb} in {hero.pronoun('possessive')} {prize.label}?",
            answer=f"It is about a little pirate named {hero.id} and {hero.pronoun('possessive')} captain. They go to {world.setting.place} on a sunny day, and {hero.id} is wearing {hero.pronoun('possessive')} {prize.label}.",
        ),
        QAItem(
            question=f"What did {hero.id} want to do at the base before the captain worried about the {prize.label}?",
            answer=f"{hero.id} wanted to {act.verb}. That was tricky because the hot sun could make the {prize.label} dusty.",
        ),
        QAItem(
            question=f"Why did the captain worry about the {prize.label}?",
            answer=f"The captain worried because the sun would make the {prize.label} {act.soil}, and nobody wanted that on such a proud pirate day.",
        ),
    ]
    if f.get("resolved"):
        gear = f["gear"]
        qa.append(QAItem(
            question=f"How did the {gear.label} help {hero.id}?",
            answer=f"They used {gear.label} to make a cool shady path, so {hero.id} could {act.verb} without ruining the {prize.label}.",
        ))
        qa.append(QAItem(
            question=f"How did {hero.id} feel at the end?",
            answer=f"{hero.id} felt happy and kind after the captain agreed to the shade plan. The base ended the day cool and merry.",
        ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["activity"].tags)
    if world.facts.get("gear"):
        tags.add("kindness")
    out: list[QAItem] = []
    for tag in KNOWLEDGE_ORDER:
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
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="base", activity="trot", prize="hat", name="Pip", gender="boy", parent="captain", trait="kind"),
    StoryParams(place="cove", activity="trot", prize="cloak", name="Mira", gender="girl", parent="captain", trait="cheery"),
]


def explain_rejection(activity: Activity, prize: Prize) -> str:
    noun = prize.label if prize.plural else f"a {prize.label}"
    if not prize_at_risk(activity, prize):
        return f"(No story: {activity.gerund} would not trouble {noun}, so the captain would have no honest warning.)"
    return f"(No story: nothing in the gear catalog truly keeps {noun} safe from {activity.gerund}.)"


def explain_gender(prize_id: str, gender: str) -> str:
    ok = " / ".join(sorted(PRIZES[prize_id].genders))
    return f"(No story: a {PRIZES[prize_id].label} isn't a typical {gender}'s item here; try --gender {ok}.)"


ASP_RULES = r"""
prize_at_risk(A, P) :- splashes(A, R), worn_on(P, R).
protects(G, A, P) :- gear(G), prize_at_risk(A, P),
                     mess_of(A, M), guards(G, M),
                     covers(G, R), worn_on(P, R).
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
    ap = argparse.ArgumentParser(description="Pirate tale story world: base, trot, shade, and kindness.")
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
    world = tell(SETTINGS[params.place], ACTIVITIES[params.activity], PRIZES[params.prize], params.name, params.gender, params.parent)
    return StorySample(params=params, story=world.render(), prompts=generation_prompts(world), story_qa=story_qa(world), world_qa=world_knowledge_qa(world), world=world)


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
            print(f"  {place:8} {act:8} {prize:8}  [{', '.join(genders)}]")
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
