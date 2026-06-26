#!/usr/bin/env python3
"""
storyworlds/worlds/crotch_aversion_yum_dim_garden_center_sound.py
===================================================================

A small fairy-tale story world set at a garden center, built from the seed words
"crotch", "aversion", and "yum-dim", with sound effects woven into the prose.

Premise:
- A child loves the magic of a garden center.
- A scratchy new garment makes the child wary of kneeling and planting.
- The parent foresees a miserable, itchy moment and offers a softer plan.
- A gentle compromise lets the child help in the garden center while the story
  ends on a bright, happy sound.

This script follows the Storyweavers standalone world contract.
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
        if not self.meters:
            self.meters = {"soil": 0.0}
        if not self.memes:
            self.memes = {"joy": 0.0, "aversion": 0.0, "worry": 0.0, "comfort": 0.0, "resolve": 0.0, "startle": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "princess"}
        male = {"boy", "father", "dad", "man", "prince"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the garden center"
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
    sound: str = ""
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
        clone.facts = dict(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_soil(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters.get("soil", 0.0) < THRESHOLD:
            continue
        for item in world.worn_items(actor):
            if item.protective or item.region not in world.zone:
                continue
            if world.covered(actor, item.region):
                continue
            sig = ("soil", item.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            item.meters["soil"] = item.meters.get("soil", 0.0) + 1
            out.append(f"The {item.label} got dusty and brown.")
    return out


def _r_worry(world: World) -> list[str]:
    out: list[str] = []
    for item in world.entities.values():
        if item.meters.get("soil", 0.0) < THRESHOLD or not item.caretaker:
            continue
        sig = ("worry", item.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        carer = world.get(item.caretaker)
        carer.memes["worry"] = carer.memes.get("worry", 0.0) + 1
        out.append(f"That would give {carer.label} extra work.")
    return out


def _r_aversion(world: World) -> list[str]:
    for actor in world.characters():
        if actor.memes.get("startle", 0.0) < THRESHOLD or actor.memes.get("aversion", 0.0) < THRESHOLD:
            continue
        sig = ("aversion", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["resolve"] = actor.memes.get("resolve", 0.0) + 1
        return ["__aversion__"]
    return []


CAUSAL_RULES: list[Rule] = [
    Rule("soil", "physical", _r_soil),
    Rule("worry", "physical", _r_worry),
    Rule("aversion", "social", _r_aversion),
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
                produced.extend(s for s in sents if s != "__aversion__")
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def delight(activity: Activity) -> str:
    return {
        "planting": "The spade went tsk-tsk, and the seed tray smelled like rain and earth.",
        "watering": "The watering can made a cheerful tip-tap sound.",
        "potting": "The little pots went clink, clink, as if they were tiny bells.",
    }.get(activity.id, "The garden center sang softly with bright little sounds.")


def _do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    world.zone = set(activity.zone)
    actor.meters["soil"] = actor.meters.get("soil", 0.0) + 1
    actor.memes["joy"] = actor.memes.get("joy", 0.0) + 1
    world.say(f"{delight(activity)}")
    propagate(world, narrate=narrate)


def predict_mess(world: World, actor: Entity, activity: Activity, prize_id: str) -> dict:
    sim = world.copy()
    _do_activity(sim, sim.get(actor.id), activity, narrate=False)
    prize = sim.entities.get(prize_id)
    return {
        "soiled": bool(prize and prize.meters.get("soil", 0.0) >= THRESHOLD),
        "workload": sum(e.memes.get("worry", 0.0) for e in sim.characters()),
    }


def prize_at_risk(activity: Activity, prize: Prize) -> bool:
    return prize.region in activity.zone


def select_gear(activity: Activity, prize: Prize) -> Optional[Gear]:
    for gear in GEAR:
        if activity.mess in gear.guards and prize.region in gear.covers:
            return gear
    return None


def act_introduction(world: World, hero: Entity) -> None:
    trait = next((t for t in hero.traits if t != "little"), "curious")
    world.say(
        f"Once, in the garden center, there lived a little {trait} {hero.type} named {hero.id}."
    )


def loves_place(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["joy"] = hero.memes.get("joy", 0.0) + 1
    world.say(
        f"{hero.pronoun().capitalize()} loved the garden center, "
        f"where leaves shone, flower pots waited, and {activity.keyword} things seemed possible."
    )


def buy_prize(world: World, parent: Entity, hero: Entity, prize: Entity) -> None:
    world.say(f"{hero.pronoun('possessive').capitalize()} {parent.label} brought home {hero.pronoun('object')} {prize.phrase}.")


def love_prize(world: World, hero: Entity, prize: Entity) -> None:
    hero.memes["joy"] = hero.memes.get("joy", 0.0) + 1
    prize.worn_by = hero.id
    world.say(f"{hero.id} loved {hero.pronoun('possessive')} {prize.label}, and wore {prize.it()} as proudly as a tiny knight.")


def arrive(world: World, hero: Entity, parent: Entity, activity: Activity) -> None:
    world.say(f"One bright day, {hero.id} and {hero.pronoun('possessive')} {parent.label} went to {world.setting.place}.")
    world.say(f"The place was full of green hats of fern, red cheeks of roses, and the little sound of {activity.sound}.")


def want(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["aversion"] = hero.memes.get("aversion", 0.0) + 1
    world.say(f"{hero.id} wanted to {activity.verb}, but {hero.pronoun('possessive')} heart had a strong aversion to the scratchy seam at the crotch.")
    world.say(f"{hero.pronoun().capitalize()} drew back with a tiny, nervous, \"yum-dim,\" as if the thought itself wore spines.")


def warn(world: World, parent: Entity, hero: Entity, activity: Activity, prize: Entity) -> bool:
    pred = predict_mess(world, hero, activity, prize.id)
    if not pred["soiled"]:
        return False
    world.facts["predicted_soil"] = activity.soil
    world.facts["predicted_worry"] = pred["workload"]
    world.say(
        f"\"You'll get your {prize.label} {activity.soil},\" {hero.pronoun('possessive')} {parent.label} said."
    )
    world.say("\"And then the washing basket will groan, yum-dim, all evening.\"")
    return True


def startle(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["startle"] = hero.memes.get("startle", 0.0) + 1
    world.say(f"{hero.id} heard that and took a little step back.")
    world.say(f"{hero.pronoun().capitalize()} tried to {activity.rush}, but hesitated at once.")


def gentle_hold(world: World, parent: Entity, hero: Entity) -> None:
    hero.memes["resolve"] = hero.memes.get("resolve", 0.0) + 1
    world.say(
        f"But {hero.pronoun('possessive')} {parent.label} held out a warm hand and said, "
        f"\"We can choose the softer way.\""
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
        f"{hero.pronoun('possessive').capitalize()} {parent.label} smiled and said, "
        f"\"How about we {gear_def.prep} and then {activity.verb}?\""
    )
    return gear_def


def accept(world: World, parent: Entity, hero: Entity, activity: Activity, prize: Entity, gear_def: Gear) -> None:
    hero.memes["joy"] = hero.memes.get("joy", 0.0) + 1
    hero.memes["comfort"] = hero.memes.get("comfort", 0.0) + 1
    hero.memes["aversion"] = 0.0
    world.say(f"{hero.id} nodded, and {hero.pronoun().capitalize()} grinned like sunrise after rain.")
    world.say(
        f"They {gear_def.tail}. Soon {hero.id} was {activity.gerund}, "
        f"{hero.pronoun('possessive')} {prize.label} stayed clean, and the garden center sounded like a happy little song."
    )


def tell(
    setting: Setting,
    activity: Activity,
    prize_cfg: Prize,
    hero_name: str = "Pip",
    hero_type: str = "boy",
    hero_traits: Optional[list[str]] = None,
    parent_type: str = "mother",
) -> World:
    world = World(setting)
    world.weather = activity.weather

    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, traits=["little"] + (hero_traits or ["gentle", "curious"])))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label="the parent"))
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

    act_introduction(world, hero)
    loves_place(world, hero, activity)
    buy_prize(world, parent, hero, prize)
    love_prize(world, hero, prize)

    world.para()
    arrive(world, hero, parent, activity)
    want(world, hero, activity)
    warn(world, parent, hero, activity, prize)
    startle(world, hero, activity)
    gentle_hold(world, parent, hero)

    world.para()
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
        resolved=gear_def is not None,
        conflict=hero.memes.get("aversion", 0.0) >= THRESHOLD,
    )
    return world


SETTINGS = {
    "garden_center": Setting(place="the garden center", indoor=False, affords={"planting", "watering", "potting"}),
}

ACTIVITIES = {
    "planting": Activity(
        id="planting",
        verb="plant the tiny seedlings",
        gerund="planting tiny seedlings",
        rush="rush to the seed table",
        mess="soil",
        soil="all muddy",
        zone={"hands", "crotch"},
        weather="sunny",
        keyword="seedlings",
        sound="tsk-tsk",
        tags={"soil", "seedlings"},
    ),
    "watering": Activity(
        id="watering",
        verb="water the hanging baskets",
        gerund="watering hanging baskets",
        rush="dash for the watering can",
        mess="wet",
        soil="dripping wet",
        zone={"torso", "crotch"},
        weather="sunny",
        keyword="water",
        sound="tip-tap",
        tags={"water", "wet"},
    ),
    "potting": Activity(
        id="potting",
        verb="repot the little fern",
        gerund="potting a fern",
        rush="hurry to the potting bench",
        mess="soil",
        soil="dusty and brown",
        zone={"crotch"},
        weather="sunny",
        keyword="fern",
        sound="clink-clink",
        tags={"pot", "soil"},
    ),
}

GEAR = [
    Gear(
        id="apron",
        label="a soft garden apron",
        covers={"crotch", "torso"},
        guards={"soil", "wet"},
        prep="put on a soft garden apron first",
        tail="went back to fetch the soft garden apron",
    ),
    Gear(
        id="kneepad",
        label="a padded kneeling pad",
        covers={"crotch"},
        guards={"soil"},
        prep="set a padded kneeling pad down first",
        tail="picked up the padded kneeling pad",
    ),
]

PRIZES = {
    "overalls": Prize(label="overalls", phrase="new green overalls", type="overalls", region="crotch", plural=True),
    "tunic": Prize(label="tunic", phrase="a bright little tunic", type="tunic", region="crotch"),
    "apron": Prize(label="apron", phrase="a tidy apron with blue strings", type="apron", region="crotch"),
}

GIRL_NAMES = ["Lily", "Mina", "Nora", "Rose", "Ivy"]
BOY_NAMES = ["Pip", "Toby", "Finn", "Theo", "Eli"]
TRAITS = ["gentle", "curious", "brave", "sprightly", "dreamy"]


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
    "soil": [("What is soil?", "Soil is the dark earth where plants grow their roots and drink up water.")],
    "water": [("Why do plants need water?", "Plants need water to stay alive and to help their roots drink and grow.")],
    "fern": [("What is a fern?", "A fern is a green plant with feathery leaves that grow in a curl at first.")],
    "apron": [("What does an apron do?", "An apron helps keep clothes cleaner when you cook, paint, or work with dirt.")],
    "garden": [("What is a garden center?", "A garden center is a shop where people can find plants, seeds, pots, and tools for growing things.")],
}
KNOWLEDGE_ORDER = ["garden", "soil", "water", "fern", "apron"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, parent, act, prize = f["hero"], f["parent"], f["activity"], f["prize_cfg"]
    return [
        f'Write a short fairy-tale story for a young child set in a garden center, with the word "{act.keyword}".',
        f"Tell a gentle story where {hero.id} loves the garden center, but a scratchy {prize.label} makes {hero.pronoun('possessive')} crotch feel unhappy.",
        f'Write a story that includes a little sound like "{act.sound}" and ends with a kinder plan.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, parent, prize, act = f["hero"], f["parent"], f["prize"], f["activity"]
    trait = next((t for t in hero.traits if t != "little"), hero.type)
    qa = [
        QAItem(
            question=f"Where does {hero.id} go in the story?",
            answer=f"{hero.id} goes to {world.setting.place}, where flowers, pots, and little tools wait in neat rows.",
        ),
        QAItem(
            question=f"What did {hero.id} want to do before the worry began?",
            answer=f"{hero.id} wanted to {act.verb}, because the garden center felt magical and busy and full of life.",
        ),
        QAItem(
            question=f"Why did {hero.id} feel an aversion?",
            answer=(
                f"{hero.id} felt an aversion because {hero.pronoun('possessive')} new {prize.label} was scratchy at the crotch, "
                f"and {hero.id} did not want dirt and rubbing to make it worse."
            ),
        ),
        QAItem(
            question=f"What sound did the story use when things felt small and tense?",
            answer=f'The story used a tiny sound effect, "{act.sound}," to show {hero.id} feeling unsure and delicate.',
        ),
    ]
    if f.get("resolved"):
        gear = f["gear"]
        qa.append(
            QAItem(
                question=f"How did the parent help {hero.id} in the end?",
                answer=(
                    f"The parent offered {gear.label}, which covered the at-risk spot and kept the messy soil from ruining the {prize.label}. "
                    f"That let {hero.id} join the work without dread."
                ),
            )
        )
        qa.append(
            QAItem(
                question=f"How did {hero.id} feel at the end?",
                answer=(
                    f"{hero.id} felt happy and comforted. The aversion faded, and the garden center ended with a bright, cheerful sound instead of a worried one."
                ),
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    tags = set(f["activity"].tags)
    if f.get("gear"):
        tags.add(f["gear"].id)
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
    StoryParams(place="garden_center", activity="planting", prize="overalls", name="Pip", gender="boy", parent="mother", trait="gentle"),
    StoryParams(place="garden_center", activity="watering", prize="tunic", name="Mina", gender="girl", parent="father", trait="curious"),
    StoryParams(place="garden_center", activity="potting", prize="apron", name="Theo", gender="boy", parent="mother", trait="brave"),
]


def explain_rejection(activity: Activity, prize: Prize) -> str:
    noun = prize.label if prize.plural else f"a {prize.label}"
    if not prize_at_risk(activity, prize):
        return f"(No story: {activity.gerund} does not reach the {prize.region}, so the {noun} would stay safe.)"
    return f"(No story: nothing in the gear basket can protect {noun} from {activity.gerund} in this way.)"


def explain_gender(prize_id: str, gender: str) -> str:
    ok = " / ".join(sorted(PRIZES[prize_id].genders))
    return f"(No story: a {PRIZES[prize_id].label} is not a typical {gender}'s item here; try --gender {ok}.)"


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
    ap = argparse.ArgumentParser(description="Fairy-tale story world set in a garden center.")
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
    world = tell(SETTINGS[params.place], ACTIVITIES[params.activity], PRIZES[params.prize], params.name, params.gender, [params.trait, "stubborn"], params.parent)
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
            print(f"  {place:13} {act:10} {prize:8}  [{', '.join(genders)}]")
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
