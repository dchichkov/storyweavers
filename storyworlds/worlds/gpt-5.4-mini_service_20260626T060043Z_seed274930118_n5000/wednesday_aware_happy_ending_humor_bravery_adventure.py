#!/usr/bin/env python3
"""
storyworlds/worlds/wednesday_aware_happy_ending_humor_bravery_adventure.py
=========================================================================

A small adventure storyworld for a brave, aware child on Wednesday.

Premise:
- A child wants to go on a little adventure anyway.
- The path may get wet or muddy.
- A parent notices the risk, warns them, and offers a safer fix.
- The child is brave, a little funny, and the ending is happy.

This world is intentionally compact: a few settings, a few activities, and a
few compatible gear-based compromises that genuinely solve the problem.
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

MESS_KINDS = {"wet", "muddy", "dirty"}

REGIONS = {"feet", "legs", "torso"}


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
        for k in ["wet", "muddy", "dirty", "workload"]:
            self.meters.setdefault(k, 0.0)
        for k in ["joy", "love", "worry", "bravery", "curiosity", "humor", "aware", "defiance", "conflict", "grabbed_by"]:
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

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Setting:
    place: str
    outdoor: bool
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
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_soak(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        for mess in MESS_KINDS:
            if actor.meters[mess] < THRESHOLD:
                continue
            for item in world.worn_items(actor):
                if item.protective or item.region not in world.zone:
                    continue
                if world.covered(actor, item.region):
                    continue
                sig = ("soak", item.id, mess)
                if sig in world.fired:
                    continue
                world.fired.add(sig)
                item.meters[mess] += 1
                item.meters["dirty"] += 1
                out.append(f"{actor.pronoun('possessive').capitalize()} {item.label} got {mess} and dirty.")
    return out


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
        out.append(f"That would mean more work for {carer.label}.")
    return out


def _r_conflict(world: World) -> list[str]:
    for actor in world.characters():
        if actor.memes["grabbed_by"] < THRESHOLD or actor.memes["defiance"] < THRESHOLD:
            continue
        sig = ("conflict", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["conflict"] += 1
        return ["__conflict__"]
    return []


CAUSAL_RULES = [
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
    actor.memes["aware"] += 1
    propagate(world, narrate=narrate)


def intro(world: World, hero: Entity) -> None:
    trait = next((t for t in hero.traits if t != "little"), "curious")
    world.say(f"{hero.id} was a little {trait} {hero.type} who liked brave little adventures.")


def loves(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["humor"] += 1
    world.say(f"{hero.pronoun().capitalize()} loved {activity.gerund}; it made even a plain path feel like a quest.")


def wed(world: World, hero: Entity) -> None:
    world.say(f"It was Wednesday, and {hero.id} felt especially aware of every puddle, pebble, and signpost.")


def arrive(world: World, hero: Entity, parent: Entity, setting: Setting, activity: Activity) -> None:
    world.say(f"{hero.id} and {hero.pronoun('possessive')} {parent.label_word} went to {setting.place}.")
    world.say(f"The path looked ready for {activity.gerund}.")


def wants(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["curiosity"] += 1
    world.say(f"{hero.id} wanted to {activity.verb} right away.")


def warn(world: World, parent: Entity, hero: Entity, activity: Activity, prize: Entity) -> bool:
    pred = predict_mess(world, hero, activity, prize.id)
    if not pred["soiled"]:
        return False
    world.facts["predicted_soil"] = activity.soil
    world.facts["predicted_workload"] = pred["workload"]
    world.say(
        f'"If you go now, your {prize.label} will get {activity.soil}," '
        f"{hero.pronoun('possessive')} {parent.label_word} said. "
        f'"Let’s be clever about it."'
    )
    return True


def humor(world: World, hero: Entity, helper: Entity, activity: Activity) -> None:
    hero.memes["humor"] += 1
    world.say(f"A silly goat nearby sneezed, and {hero.id} laughed even while staying brave.")
    world.say(f'"If the trail wants a joke, I can bring one," {helper.id} bleated, and everyone smiled.')


def defy(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["defiance"] += 1
    world.say(f"{hero.id} was tempted to charge ahead anyway and tried to {activity.rush}.")


def grab(world: World, parent: Entity, hero: Entity) -> None:
    hero.memes["grabbed_by"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Then {hero.pronoun('possessive')} {parent.label_word} held {hero.pronoun('possessive')} hand and said, "
        f'"We can still go, but we should do it safely."'
    )


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
        f'{hero.pronoun("possessive").capitalize()} {parent.label_word} pointed at {gear_def.label} and smiled. '
        f'"How about we {gear_def.prep} and go together?"'
    )
    return gear_def


def accept(world: World, parent: Entity, hero: Entity, activity: Activity, prize: Entity, gear_def: Gear) -> None:
    hero.memes["joy"] += 1
    hero.memes["love"] += 1
    hero.memes["bravery"] += 1
    hero.memes["conflict"] = 0.0
    world.say(
        f"{hero.id} grinned, hugged {hero.pronoun('possessive')} {parent.label_word}, and said, "
        f'"I can do brave *and* sensible!"'
    )
    world.say(
        f"They {gear_def.tail}. Soon {hero.id} was {activity.gerund}, {prize.label} stayed clean, "
        f"and the silly goat trotted along like a tiny parade leader."
    )


def tell(setting: Setting, activity: Activity, prize_cfg: Prize, hero_name: str = "Mina",
         hero_type: str = "girl", hero_traits: Optional[list[str]] = None, parent_type: str = "mother") -> World:
    world = World(setting)
    world.weather = activity.weather
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, traits=["little"] + (hero_traits or ["aware", "brave"])))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label="the parent"))
    helper = world.add(Entity(id="Goat", kind="character", type="goat", label="the goat"))
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
    wed(world, hero)
    loves(world, hero, activity)
    arrive(world, hero, parent, setting, activity)
    wants(world, hero, activity)

    world.para()
    if warn(world, parent, hero, activity, prize):
        humor(world, hero, helper, activity)
        defy(world, hero, activity)
        grab(world, parent, hero)

    world.para()
    gear_def = compromise(world, parent, hero, activity, prize)
    if gear_def:
        accept(world, parent, hero, activity, prize, gear_def)

    world.facts.update(hero=hero, parent=parent, helper=helper, prize=prize, activity=activity, setting=setting, gear=gear_def, resolved=gear_def is not None)
    return world


SETTINGS = {
    "forest_trail": Setting(place="the forest trail", outdoor=True, affords={"rain", "mud"}),
    "hill_path": Setting(place="the hill path", outdoor=True, affords={"wind_rain", "rain"}),
    "stone_bridge": Setting(place="the stone bridge", outdoor=True, affords={"rain", "river_spray"}),
    "camp_lane": Setting(place="the camp lane", outdoor=True, affords={"mud", "rain"}),
}

ACTIVITIES = {
    "rain": Activity(
        id="rain",
        verb="cross the rainy path",
        gerund="crossing the rainy path",
        rush="dash through the rain",
        mess="wet",
        soil="soaking wet",
        zone={"feet", "legs", "torso"},
        weather="rainy",
        keyword="wednesday",
        tags={"rain", "wet", "wednesday"},
    ),
    "mud": Activity(
        id="mud",
        verb="take the muddy shortcut",
        gerund="taking the muddy shortcut",
        rush="sprint through the mud",
        mess="muddy",
        soil="all muddy",
        zone={"feet", "legs"},
        weather="rainy",
        keyword="aware",
        tags={"mud", "dirty", "aware"},
    ),
    "wind_rain": Activity(
        id="wind_rain",
        verb="climb the windy, rainy hill",
        gerund="climbing the windy, rainy hill",
        rush="race up the slippery hill",
        mess="wet",
        soil="wet and chilly",
        zone={"torso"},
        weather="rainy",
        keyword="aware",
        tags={"rain", "wet", "bravery"},
    ),
    "river_spray": Activity(
        id="river_spray",
        verb="cross by the sprayy bridge",
        gerund="crossing by the sprayy bridge",
        rush="run over the splashing stones",
        mess="wet",
        soil="sprayed wet",
        zone={"feet", "legs"},
        weather="rainy",
        keyword="wednesday",
        tags={"wet", "adventure"},
    ),
}

PRIZES = {
    "satchel": Prize(label="satchel", phrase="a paper satchel with a bright star", type="satchel", region="torso"),
    "map": Prize(label="map", phrase="a folded paper map", type="map", region="torso"),
    "cape": Prize(label="cape", phrase="a cheerful blue cape", type="cape", region="torso"),
}

GEAR = [
    Gear(id="raincoat", label="a raincoat", covers={"torso"}, guards={"wet"}, prep="put on your raincoat first", tail="walked on in the rain"),
    Gear(id="boots", label="rain boots", covers={"feet"}, guards={"wet", "muddy"}, prep="pull on rain boots", tail="marched on in their rain boots", plural=True),
    Gear(id="shell_satchel", label="a waxed satchel cover", covers={"torso"}, guards={"wet", "muddy"}, prep="wrap the satchel in a waxed cover", tail="kept the satchel tucked safely under the cover"),
]

GIRL_NAMES = ["Mina", "Luna", "Nina", "Ruby", "Ivy", "Pia"]
BOY_NAMES = ["Owen", "Theo", "Finn", "Jasper", "Milo", "Eli"]
TRAITS = ["aware", "brave", "cheerful", "curious", "spirited"]


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
    "wednesday": [("What is Wednesday?", "Wednesday is the day in the middle of the week, after Tuesday and before Thursday.")],
    "aware": [("What does it mean to be aware?", "Being aware means noticing what is happening around you.")],
    "bravery": [("What does bravery mean?", "Bravery means doing something scary or hard while still trying your best.")],
    "adventure": [("What is an adventure?", "An adventure is a journey or activity that feels exciting, new, and full of discovery.")],
    "rain": [("Where does rain come from?", "Rain falls from clouds when tiny water drops get too heavy to stay up in the sky.")],
    "wet": [("Why do wet clothes feel cold?", "Wet clothes feel cold because water carries heat away as it dries.")],
    "mud": [("What is mud?", "Mud is wet dirt that can stick to shoes and clothes.")],
}


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, parent, act, prize = f["hero"], f["parent"], f["activity"], f["prize"]
    return [
        f'Write a short adventure story for a young child about "{act.keyword}" on Wednesday.',
        f"Tell a happy ending story where {hero.id} wants to {act.verb} but {hero.pronoun('possessive')} {parent.label_word} worries about {prize.phrase}.",
        f"Write a funny, brave little journey that ends with {prize.label} staying safe.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, parent, prize, act = f["hero"], f["parent"], f["prize"], f["activity"]
    trait = next((t for t in hero.traits if t != "little"), "aware")
    qa = [
        QAItem(
            question=f"Why did {hero.id} go to {world.setting.place} on Wednesday?",
            answer=f"{hero.id} went there because {hero.pronoun()} wanted a brave little adventure and hoped to {act.verb}.",
        ),
        QAItem(
            question=f"What was {hero.id} worried about when {hero.id} wanted to {act.verb}?",
            answer=f"{parent.label_word} worried that the {prize.label} would get {act.soil}.",
        ),
        QAItem(
            question=f"How did {hero.id} act when the path looked tricky?",
            answer=f"{hero.id} stayed aware, laughed at the silly goat, and kept going bravely.",
        ),
    ]
    if f.get("resolved"):
        qa.append(QAItem(
            question=f"What did they do so the {prize.label} would stay safe?",
            answer=f"They used {f['gear'].label} first, so {hero.id} could {act.verb} without ruining the {prize.label}.",
        ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["activity"].tags)
    if world.facts.get("gear"):
        tags.add("bravery")
    out: list[QAItem] = []
    for tag, pairs in KNOWLEDGE.items():
        if tag in tags:
            out.extend(QAItem(question=q, answer=a) for q, a in pairs)
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
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


def explain_rejection(activity: Activity, prize: Prize) -> str:
    noun = prize.label if prize.plural else f"a {prize.label}"
    if not prize_at_risk(activity, prize):
        return f"(No story: {activity.gerund} would not touch {noun}, so there is no real problem to solve.)"
    return f"(No story: nothing in this world safely protects {noun} from {activity.gerund}.)"


def explain_gender(prize_id: str, gender: str) -> str:
    ok = " / ".join(sorted(PRIZES[prize_id].genders))
    return f"(No story: try --gender {ok} for {PRIZES[prize_id].label}.)"


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
    ap = argparse.ArgumentParser(description="Wednesday-aware adventure world with a happy ending.")
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
                 params.name, params.gender, [params.trait, "aware", "brave"], params.parent)
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
    StoryParams(place="forest_trail", activity="rain", prize="satchel", name="Mina", gender="girl", parent="mother", trait="aware"),
    StoryParams(place="camp_lane", activity="mud", prize="map", name="Owen", gender="boy", parent="father", trait="brave"),
    StoryParams(place="hill_path", activity="wind_rain", prize="cape", name="Luna", gender="girl", parent="mother", trait="cheerful"),
]


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
            print(f"  {place:14} {act:12} {prize:8}  [{', '.join(genders)}]")
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
