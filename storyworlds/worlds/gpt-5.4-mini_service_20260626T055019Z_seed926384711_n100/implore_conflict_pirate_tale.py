#!/usr/bin/env python3
"""
storyworlds/worlds/implore_conflict_pirate_tale.py
===================================================

A small pirate-tale story world with a single tension shape:
a childlike crew member wants to act bravely, a treasured object is at risk,
and the captain must implore them toward a safer compromise.

The world is modeled as entities with physical meters and emotional memes.
A short forward simulation determines whether the treasured item would be
ruined, which then drives the warning, conflict, and resolution.

Seed premise:
- A young sailor loves a pirate activity.
- The captain foresees a mess that would damage a prized item.
- The sailor resists, the captain implores, and the crew finds the right gear.
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
        for k in ["wet", "muddy", "salted", "dirty", "workload"]:
            self.meters.setdefault(k, 0.0)
        for k in ["joy", "love", "desire", "defiance", "conflict", "implore"]:
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "captain"}
        male = {"boy", "father", "dad", "man", "sailor", "pirate", "boy pirate"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

    @property
    def label_word(self) -> str:
        return self.label or self.type


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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.zone = set(self.zone)
        clone.weather = self.weather
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_soak(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        for mess in ["wet", "salted"]:
            if actor.meters[mess] < THRESHOLD:
                continue
            for item in world.worn_items(actor):
                if item.protective or item.region not in world.zone:
                    continue
                if world.covered(actor, item.region):
                    continue
                sig = ("soak", actor.id, item.id, mess)
                if sig in world.fired:
                    continue
                world.fired.add(sig)
                item.meters[mess] += 1
                item.meters["dirty"] += 1
                out.append(f"{actor.pronoun('possessive').capitalize()} {item.label} got {mess} and dirty.")
    return out


def _r_conflict(world: World) -> list[str]:
    for actor in world.characters():
        if actor.memes["defiance"] < THRESHOLD or actor.memes["implore"] < THRESHOLD:
            continue
        sig = ("conflict", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["conflict"] += 1
        return ["__conflict__"]
    return []


def _r_workload(world: World) -> list[str]:
    out: list[str] = []
    for item in world.entities.values():
        if item.meters["dirty"] < THRESHOLD or not item.caretaker:
            continue
        sig = ("work", item.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        carer = world.get(item.caretaker)
        carer.meters["workload"] += 1
        out.append(f"That would mean more work for {carer.label_word}.")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule("soak", "physical", _r_soak),
    Rule("workload", "physical", _r_workload),
    Rule("conflict", "social", _r_conflict),
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
        "soiled": bool(prize and prize.meters["dirty"] >= THRESHOLD),
        "workload": sum(e.meters["workload"] for e in sim.characters()),
    }


def _do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    if activity.id not in world.setting.affords:
        return
    world.zone = set(activity.zone)
    actor.meters[activity.mess] += 1
    actor.memes["joy"] += 1
    propagate(world, narrate=narrate)


def setting_detail(setting: Setting, activity: Activity) -> str:
    if setting.indoor:
        return f"The {setting.place} was calm, and lantern light shone on the boards."
    if activity.weather == "stormy":
        return f"The wind snapped the sails, and {setting.place} smelled of salt and rain."
    return f"{setting.place.capitalize()} looked wide and bright, with gulls wheeling overhead."


def introduce(world: World, hero: Entity) -> None:
    trait = next((t for t in hero.traits if t != "little"), "")
    world.say(f"{hero.id} was a little {trait} {hero.type} who loved the sea and every creak of a pirate ship.")


def loves_activity(world: World, hero: Entity, activity: Activity) -> None:
    world.say(f"{hero.pronoun().capitalize()} loved {activity.gerund}, because {activity.keyword} made the whole voyage feel bold.")


def treasure_story(world: World, parent: Entity, hero: Entity, prize: Entity) -> None:
    world.say(f"One sunset, {hero.id}'s {parent.label_word} showed {hero.pronoun('object')} a {prize.phrase}.")
    prize.worn_by = hero.id
    hero.memes["love"] += 1
    world.say(f"{hero.id} loved {hero.pronoun('possessive')} {prize.label} and kept {prize.it()} close like a lucky charm.")


def arrive(world: World, hero: Entity, parent: Entity, activity: Activity) -> None:
    day = {"stormy": "One stormy day, ", "sunny": "One sunny day, "}.get(world.weather, "One day, ")
    go = "set out for" if world.setting.indoor else "went to"
    world.say(f"{day}{hero.id} and {hero.pronoun('possessive')} {parent.label_word} {go} {world.setting.place}.")
    world.say(setting_detail(world.setting, activity))


def wants(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["desire"] += 1
    world.say(f"{hero.id} wanted to {activity.verb} right away, but the tide and the wind were both growing rough.")


def warn(world: World, parent: Entity, hero: Entity, activity: Activity, prize: Entity) -> bool:
    pred = predict_mess(world, hero, activity, prize.id)
    if not pred["soiled"]:
        return False
    world.facts["predicted_soil"] = activity.soil
    world.facts["predicted_workload"] = pred["workload"]
    clause = f"If you go now, your {prize.label} will get {activity.soil}"
    if pred["workload"] >= THRESHOLD:
        clause += f", and then I'll have to clean {prize.it()}"
    world.say(f'"{clause}," {parent.label_word} said. "Please think on it, matey."')
    return True


def implore(world: World, parent: Entity, hero: Entity, activity: Activity, prize: Entity) -> None:
    parent.memes["implore"] += 1
    hero.memes["defiance"] += 1
    world.say(
        f"{parent.label_word} drew closer and implored {hero.id}, "
        f"asking them to choose the safer way before the {prize.label} was spoiled."
    )
    world.say(f"{hero.id} heard the plea, but {hero.pronoun('possessive')} jaw stayed set like a little ship's prow.")


def grab_conflict(world: World, parent: Entity, hero: Entity, activity: Activity) -> None:
    hero.memes["conflict"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Then {parent.label_word} took {hero.pronoun('possessive')} hand and said, "
        f'"You may still want to {activity.verb}, but we must do it the smart way."'
    )


def pout(world: World, hero: Entity, activity: Activity) -> None:
    if hero.memes["conflict"] >= THRESHOLD:
        world.say(f"{hero.id} pouted and stamped {hero.pronoun('possessive')} foot. "
                  f'"But I want to {activity.verb}!" {hero.pronoun().capitalize()} cried.')


def compromise(world: World, parent: Entity, hero: Entity, activity: Activity, prize: Entity) -> Optional[Gear]:
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
    world.say(
        f"{parent.label_word} pointed to the gear and smiled. "
        f'"How about we {gear_def.prep} and then {activity.verb}?"'
    )
    return gear_def


def accept(world: World, parent: Entity, hero: Entity, activity: Activity, prize: Entity, gear_def: Gear) -> None:
    hero.memes["joy"] += 1
    hero.memes["love"] += 1
    hero.memes["conflict"] = 0.0
    world.say(f"{hero.id}'s face brightened at once, and {hero.id} hugged {hero.pronoun('possessive')} {parent.label_word}.")
    world.say(
        f'"Aye, that will do!" {hero.pronoun().capitalize()} said. '
        f"They {gear_def.tail}. Soon {hero.id} was {activity.gerund}, "
        f"{hero.pronoun('possessive')} {prize.label} stayed clean, and the ship felt cheerful again."
    )


def tell(setting: Setting, activity: Activity, prize_cfg: Prize, hero_name: str = "Nico", hero_type: str = "boy",
         hero_traits: Optional[list[str]] = None, parent_type: str = "captain") -> World:
    world = World(setting)
    world.weather = "" if setting.indoor else activity.weather

    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type=hero_type,
        traits=["little"] + (hero_traits or ["bold", "stubborn"]),
    ))
    parent = world.add(Entity(id="Captain", kind="character", type=parent_type, label="the captain"))
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
    loves_activity(world, hero, activity)
    treasure_story(world, parent, hero, prize)

    world.para()
    arrive(world, hero, parent, activity)
    wants(world, hero, activity)
    warn(world, parent, hero, activity, prize)
    implore(world, parent, hero, activity, prize)
    grab_conflict(world, parent, hero, activity)

    world.para()
    pout(world, hero, activity)
    gear_def = compromise(world, parent, hero, activity, prize)
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
        conflict=hero.memes["conflict"] >= THRESHOLD,
        resolved=gear_def is not None,
    )
    return world


SETTINGS = {
    "ship": Setting(place="the pirate ship", indoor=False, affords={"storm,deck", "lookout", "sail"}),
    "dock": Setting(place="the dock", indoor=False, affords={"load", "sail"}),
    "island": Setting(place="the island shore", indoor=False, affords={"dig", "sail"}),
}

ACTIVITIES = {
    "storm": Activity(
        id="storm",
        verb="dash along the deck",
        gerund="racing along the deck",
        rush="run to the wet rails",
        mess="wet",
        soil="soaking wet",
        zone={"torso", "legs"},
        weather="stormy",
        keyword="storm",
        tags={"storm", "wet"},
    ),
    "sail": Activity(
        id="sail",
        verb="hoist the sail",
        gerund="hauling on the sail ropes",
        rush="climb up the rigging",
        mess="salted",
        soil="salt-streaked",
        zone={"torso", "arms"},
        weather="stormy",
        keyword="sail",
        tags={"sea", "salt"},
    ),
    "lookout": Activity(
        id="lookout",
        verb="climb the lookout",
        gerund="watching from the crow's nest",
        rush="climb higher and higher",
        mess="wet",
        soil="sprayed wet",
        zone={"torso", "arms"},
        weather="stormy",
        keyword="lookout",
        tags={"sea", "wet"},
    ),
    "dig": Activity(
        id="dig",
        verb="dig for buried treasure",
        gerund="digging in the sand",
        rush="run to the dunes",
        mess="dirty",
        soil="covered in sand",
        zone={"legs", "feet"},
        weather="sunny",
        keyword="treasure",
        tags={"sand", "treasure"},
    ),
}

PRIZES = {
    "map": Prize("map", "a folded treasure map with a red X", "map", "torso"),
    "hat": Prize("hat", "a feathered pirate hat", "hat", "torso"),
    "boots": Prize("boots", "shiny ship boots", "boots", "feet", plural=True),
}

GEAR = [
    Gear("oilskin", "an oilskin coat", {"torso"}, {"wet", "salted"}, "put on the oilskin coat first", "went to get the oilskin coat"),
    Gear("stormboots", "storm boots", {"feet"}, {"wet", "salted"}, "pull on storm boots first", "pulled on the storm boots first", plural=True),
    Gear("patch", "a patched cloak", {"torso"}, {"wet"}, "wear a patched cloak over your shirt", "took the patched cloak", plural=False),
]

BOY_NAMES = ["Nico", "Finn", "Jett", "Oren", "Toby", "Pip"]
GIRL_NAMES = ["Mara", "Nia", "Tessa", "Luna", "Rhea", "Pearl"]
TRAITS = ["bold", "curious", "cheerful", "stubborn", "brave"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            if act_id not in ACTIVITIES:
                continue
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
    "storm": [("What is a storm?", "A storm is when wind and rain get strong and the sea gets wild.")],
    "wet": [("Why do clothes get wet?", "Clothes get wet when water soaks into the fabric.")],
    "salt": [("Why does sea spray feel salty?", "Sea spray feels salty because it comes from seawater.")],
    "map": [("What is a treasure map?", "A treasure map is a drawing that shows where someone thinks treasure is hidden.")],
    "oilskin": [("What is an oilskin coat for?", "An oilskin coat helps keep a sailor dry in rain and sea spray.")],
}


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, parent, act, prize = f["hero"], f["parent"], f["activity"], f["prize_cfg"]
    return [
        f'Write a short pirate tale for a small child about "{f["activity"].keyword}" and a treasure map.',
        f"Tell a story where {hero.id} wants to {act.verb} but {hero.pronoun('possessive')} {parent.label_word} must implore {hero.pronoun('object')} to be careful with {prize.phrase}.",
        f"Make a gentle sea story with a conflict, a promise, and a safer way to {act.verb}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, parent, prize, act = f["hero"], f["parent"], f["prize"], f["activity"]
    gear = f.get("gear")
    qa = [
        QAItem(
            question=f"Who wanted to {act.verb} in the story?",
            answer=f"{hero.id}, a little {next(t for t in hero.traits if t != 'little')} {hero.type}, wanted to {act.verb}.",
        ),
        QAItem(
            question=f"Why did {parent.label_word} worry about {hero.pronoun('possessive')} {prize.label}?",
            answer=f"{parent.label_word} worried because the {prize.label} would get {f.get('predicted_soil', act.soil)} if {hero.id} went out without the right gear.",
        ),
        QAItem(
            question=f"What did the captain do when the conflict grew?",
            answer=f"The captain implored {hero.id} to choose the safer way, then held {hero.pronoun('possessive')} hand until they found a better plan.",
        ),
    ]
    if gear:
        qa.append(
            QAItem(
                question=f"How did the {gear.label} help?",
                answer=f"The {gear.label} kept the at-risk part dry, so {hero.id} could {act.verb} without ruining the {prize.label}.",
            )
        )
        qa.append(
            QAItem(
                question=f"How did {hero.id} feel at the end?",
                answer=f"{hero.id} felt happy again once the plan worked, and the ship was calm enough for {act.gerund}.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["activity"].tags)
    gear = world.facts.get("gear")
    if gear:
        tags.add(gear.id)
    out: list[QAItem] = []
    for key, items in KNOWLEDGE.items():
        if key in tags:
            out.extend(QAItem(question=q, answer=a) for q, a in items)
    return out


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
    lines.append("== (3) World knowledge ==")
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
        lines.append(f"  {e.id:10} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams("ship", "storm", "map", "Nico", "boy", "captain", "bold"),
    StoryParams("dock", "sail", "hat", "Mara", "girl", "captain", "curious"),
    StoryParams("island", "dig", "boots", "Pip", "boy", "captain", "cheerful"),
]


def explain_rejection(activity: Activity, prize: Prize) -> str:
    if not prize_at_risk(activity, prize):
        return f"(No story: {activity.gerund} does not reach the {prize.region}, so the prize would stay safe and the conflict would be weak.)"
    return f"(No story: nothing in the gear set both covers the {prize.region} and guards against {activity.mess}. Try a different prize.)"


def explain_gender(prize_id: str, gender: str) -> str:
    ok = " / ".join(sorted(PRIZES[prize_id].genders))
    return f"(No story: that prize does not fit the requested gender in this world; try --gender {ok}.)"


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
    ap = argparse.ArgumentParser(description="Pirate tale story world with implore, conflict, and a safer sea compromise.")
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
    return StoryParams(place, activity, prize_id, name, gender, "captain", rng.choice(TRAITS))


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
        triples, stories = asp_valid_combos(), asp_valid_stories()
        print(f"{len(triples)} compatible (place, activity, prize) combos ({len(stories)} with gender):\n")
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
