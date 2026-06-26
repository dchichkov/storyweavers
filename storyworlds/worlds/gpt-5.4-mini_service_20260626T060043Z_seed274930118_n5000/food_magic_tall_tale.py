#!/usr/bin/env python3
"""
storyworlds/worlds/food_magic_tall_tale.py
=========================================

A small tall-tale storyworld about food, magic, and a very big helping of
trouble before a clever compromise.

The seed tale behind this world:
---
A hungry child loves a magical supper that can make a plain kitchen feel bigger
than a barn. One day the child wants to use the magic food right away, but a
grown-up worries the spell will splatter the child's good clothes. The child
pouts, then agrees to put on a proper apron and use the magic food the careful
way. In the end, the meal stays tasty, the clothes stay clean, and the kitchen
feels like a tiny kingdom.
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

    def __post_init__(self):
        if not self.meters:
            self.meters = {"mess": 0.0, "dirty": 0.0, "workload": 0.0}
        if not self.memes:
            self.memes = {"joy": 0.0, "desire": 0.0, "defiance": 0.0, "conflict": 0.0, "grabbed_by": 0.0}

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
    place: str = "the kitchen"
    indoor: bool = True
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


def _mess_word(activity: Activity) -> str:
    return {
        "sticky": "sticky",
        "sugary": "sugary",
        "splashy": "splashy",
    }.get(activity.mess, activity.mess)


def _r_soak(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters["mess"] < THRESHOLD:
            continue
        for item in world.worn_items(actor):
            if item.protective or item.region not in world.zone or world.covered(actor, item.region):
                continue
            sig = ("mess", item.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            item.meters["dirty"] += 1
            out.append(f"{actor.pronoun('possessive').capitalize()} {item.label} got sticky and dirty.")
    return out


def _r_work(world: World) -> list[str]:
    out: list[str] = []
    for item in list(world.entities.values()):
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
    ("soak", _r_soak),
    ("work", _r_work),
    ("conflict", _r_conflict),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
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
    return {"soiled": bool(prize and prize.meters["dirty"] >= THRESHOLD),
            "workload": sum(e.meters["workload"] for e in sim.characters())}


def activity_delight(activity: Activity) -> str:
    return {
        "soup": "the magic bubbles bounced like tiny moons",
        "cake": "the frosting smelled like a birthday cloud",
        "pie": "the sweet crust looked ready to sing",
        "bread": "the warm loaf puffed up like a sunbeam",
    }.get(activity.id, "the magic food felt fit for a wonder")


def setting_detail(setting: Setting, activity: Activity) -> str:
    return f"The {setting.place.removeprefix('the ')} stood warm and bright, like a room waiting for a story."


def _do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    if activity.id not in world.setting.affords:
        return
    world.zone = set(activity.zone)
    actor.meters["mess"] += 1
    actor.memes["joy"] += 1
    propagate(world, narrate=narrate)


def introduce(world: World, hero: Entity) -> None:
    trait = next((t for t in hero.traits if t != "little"), "")
    world.say(f"{hero.id} was a little {trait} {hero.type} who could smell supper from three rooms away.")


def loves_food(world: World, hero: Entity, activity: Activity, food: Entity) -> None:
    hero.memes["joy"] += 1
    world.say(
        f"{hero.id} loved {activity.gerund}; {activity_delight(activity)}. "
        f"{hero.pronoun().capitalize()} also adored {food.phrase} and watched it like it held the whole sunset inside."
    )


def buys(world: World, parent: Entity, hero: Entity, food: Entity) -> None:
    world.say(f"That very week, {hero.pronoun('possessive')} {parent.label_word} bought {hero.pronoun('object')} {food.phrase}.")


def loves_food_item(world: World, hero: Entity, food: Entity) -> None:
    hero.memes["desire"] += 1
    food.worn_by = hero.id
    world.say(f"{hero.id} loved {hero.pronoun('possessive')} {food.label} and carried {food.it()} like a prize from a treasure hunt.")


def arrive(world: World, hero: Entity, parent: Entity, activity: Activity) -> None:
    world.say(f"One day, {hero.id} and {hero.pronoun('possessive')} {parent.label_word} were in {world.setting.place}.")
    world.say(setting_detail(world.setting, activity))


def wants(world: World, hero: Entity, parent: Entity, activity: Activity) -> None:
    hero.memes["desire"] += 1
    world.say(f"{hero.id} wanted to {activity.verb} right away, but {hero.pronoun('possessive')} {parent.label_word} held up a steady hand.")


def warn(world: World, parent: Entity, hero: Entity, activity: Activity, food: Entity) -> bool:
    pred = predict_mess(world, hero, activity, food.id)
    if not pred["soiled"]:
        return False
    world.facts["predicted_soil"] = activity.soil
    clause = f"You'll get your {food.label} {activity.soil}"
    if pred["workload"] >= THRESHOLD:
        clause += f", and then I'll have more work to do"
    world.say(f"\"{clause},\" {hero.pronoun('possessive')} {parent.label_word} said. \"Let's do it the careful way.\"")
    return True


def defies(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["defiance"] += 1
    world.say(f"{hero.id} huffed so hard it might have blown the dust right off the moon.")
    world.say(f"{hero.pronoun().capitalize()} tried to {activity.rush},")


def grab_hand(world: World, parent: Entity, hero: Entity, activity: Activity) -> None:
    hero.memes["grabbed_by"] += 1
    propagate(world, narrate=False)
    world.say(f"but {hero.pronoun('possessive')} {parent.label_word} grabbed {hero.pronoun('possessive')} hand and said,")
    world.say(f"\"You can want to {activity.verb}, and we can still choose the safe way.\"")


def pout(world: World, hero: Entity, activity: Activity) -> None:
    if hero.memes["conflict"] >= THRESHOLD:
        world.say(f'{hero.id} pouted and crossed {hero.pronoun("possessive")} arms. "But I want to {activity.verb}!" {hero.pronoun()} said.')


def compromise(world: World, parent: Entity, hero: Entity, activity: Activity, food: Entity) -> Optional[Gear]:
    gear_def = select_gear(activity, food)
    if gear_def is None:
        return None
    gear = world.add(Entity(id=gear_def.id, type="gear", label=gear_def.label, owner=hero.id,
                            caretaker=parent.id, protective=True, covers=set(gear_def.covers), plural=gear_def.plural))
    gear.worn_by = hero.id
    if predict_mess(world, hero, activity, food.id)["soiled"]:
        gear.worn_by = None
        del world.entities[gear.id]
        return None
    world.say(f"{hero.pronoun('possessive').capitalize()} {parent.label_word} smiled and said,")
    world.say(f"\"How about we {gear_def.prep} and {activity.verb} together?\"")
    return gear_def


def accept(world: World, parent: Entity, hero: Entity, activity: Activity, food: Entity, gear_def: Gear) -> None:
    hero.memes["joy"] += 1
    hero.memes["conflict"] = 0.0
    hero.memes["love"] += 1
    world.say(f"{hero.id}'s face lit up, and {hero.pronoun()} hugged {hero.pronoun('possessive')} {parent.label_word}.")
    world.say(f"\"Yay, let's do it!\" {hero.pronoun()} said.")
    world.say(f"They {gear_def.tail}. Soon {hero.id} was {activity.gerund}, {food.label} stayed clean, and the kitchen felt as grand as a palace hall.")


def tell(setting: Setting, activity: Activity, prize_cfg: Prize, hero_name: str = "Mabel",
         hero_type: str = "girl", hero_traits: Optional[list[str]] = None, parent_type: str = "mother") -> World:
    world = World(setting)
    world.weather = ""
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, traits=["little"] + (hero_traits or ["bright", "stubborn"])))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label="the parent"))
    food = world.add(Entity(id="food", type=prize_cfg.type, label=prize_cfg.label, phrase=prize_cfg.phrase,
                            owner=hero.id, caretaker=parent.id, region=prize_cfg.region, plural=prize_cfg.plural))
    introduce(world, hero)
    loves_food(world, hero, activity, food)
    buys(world, parent, hero, food)
    loves_food_item(world, hero, food)
    world.para()
    arrive(world, hero, parent, activity)
    wants(world, hero, parent, activity)
    warn(world, parent, hero, activity, food)
    defies(world, hero, activity)
    grab_hand(world, parent, hero, activity)
    world.para()
    pout(world, hero, activity)
    gear_def = compromise(world, parent, hero, activity, food)
    if gear_def:
        accept(world, parent, hero, activity, food, gear_def)
    world.facts.update(hero=hero, parent=parent, prize=food, prize_cfg=prize_cfg, activity=activity,
                       setting=setting, gear=gear_def, conflict=hero.memes["grabbed_by"] >= THRESHOLD,
                       resolved=gear_def is not None)
    return world


SETTINGS = {
    "kitchen": Setting(place="the kitchen", indoor=True, affords={"soup", "cake", "bread"}),
    "bakery": Setting(place="the bakery", indoor=True, affords={"cake", "bread", "pie"}),
    "barn": Setting(place="the barn kitchen", indoor=True, affords={"soup", "bread"}),
}

ACTIVITIES = {
    "soup": Activity(id="soup", verb="stir the magic soup", gerund="stirring the magic soup",
                     rush="rush to the bubbling pot", mess="splashy", soil="splashed and drippy",
                     zone={"torso", "hands"}, weather="", keyword="soup", tags={"food", "magic", "soup"}),
    "cake": Activity(id="cake", verb="bake the magic cake", gerund="baking the magic cake",
                     rush="dash to the oven", mess="sticky", soil="sticky with frosting",
                     zone={"hands", "torso"}, weather="", keyword="cake", tags={"food", "magic", "cake"}),
    "bread": Activity(id="bread", verb="knead the magic bread", gerund="kneading the magic bread",
                      rush="pounce on the dough", mess="sticky", soil="sticky with dough",
                      zone={"hands", "torso"}, weather="", keyword="bread", tags={"food", "magic", "bread"}),
    "pie": Activity(id="pie", verb="glaze the magic pie", gerund="glazing the magic pie",
                    rush="hurry to the pie plate", mess="sticky", soil="spattered with syrup",
                    zone={"hands", "torso"}, weather="", keyword="pie", tags={"food", "magic", "pie"}),
}

PRIZES = {
    "apron": Prize(label="apron", phrase="a clean apron with bright blue trim", type="apron", region="torso"),
    "shirt": Prize(label="shirt", phrase="a clean white shirt", type="shirt", region="torso"),
    "cap": Prize(label="cap", phrase="a brand-new cook's cap", type="cap", region="head"),
}

GEAR = [
    Gear(id="apron", label="an apron", covers={"torso"}, guards={"sticky", "splashy"}, prep="put on an apron first", tail="tied on the apron"),
    Gear(id="mitts", label="oven mitts", covers={"hands"}, guards={"sticky", "splashy"}, prep="pull on oven mitts first", tail="slipped on the oven mitts", plural=True),
    Gear(id="cap", label="a cook's cap", covers={"head"}, guards={"sticky"}, prep="set on a cook's cap first", tail="set the cap straight"),
]

GIRL_NAMES = ["Mabel", "Dot", "Ruby", "Sadie", "Nell", "June"]
BOY_NAMES = ["Hank", "Jesse", "Tom", "Will", "Bert", "Abe"]
TRAITS = ["hungry", "bright", "bold", "cheerful", "curious", "stubborn"]


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
    "food": [("What is food?", "Food is something people eat to get energy and grow strong.")],
    "soup": [("What is soup?", "Soup is a warm food made with broth and bits of vegetables, meat, or noodles.")],
    "cake": [("What is cake?", "Cake is a sweet baked food, often eaten for birthdays and celebrations.")],
    "bread": [("What is bread?", "Bread is a food made from dough that is baked until it becomes soft or crusty.")],
    "pie": [("What is pie?", "Pie is a baked food with a crust and a filling, such as fruit or custard.")],
    "magic": [("What does magic mean in a story?", "Magic is something wonderful and impossible that can happen in a story.")],
    "sticky": [("Why do sticky foods make a mess?", "Sticky foods can cling to hands and clothes, so they can leave messy spots.")],
    "apron": [("What is an apron for?", "An apron is worn over clothes to help keep them clean while cooking or making a mess.")],
}
KNOWLEDGE_ORDER = ["food", "magic", "soup", "cake", "bread", "pie", "sticky", "apron"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, parent, act, prize = f["hero"], f["parent"], f["activity"], f["prize_cfg"]
    return [
        f'Write a tall-tale story for a small child about "{act.keyword}" and magical food in {f["setting"].place}.',
        f"Tell a funny, big-hearted story where {hero.id} wants to {act.verb} but {hero.pronoun('possessive')} {parent.label_word} worries about {prize.phrase}.",
        f'Write a simple story with a magical food problem, a warning, and a safe compromise using the word "{act.keyword}".',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, parent, prize, act = f["hero"], f["parent"], f["prize"], f["activity"]
    qa = [
        QAItem(
            question=f"Who is the story about?",
            answer=f"It's about {hero.id}, a little {next(t for t in hero.traits if t != 'little')} {hero.type}, and {hero.pronoun('possessive')} {parent.label_word}.",
        ),
        QAItem(
            question=f"What magical food did {hero.id} love?",
            answer=f"{hero.id} loved {prize.phrase}, and it was part of the magical cooking day.",
        ),
        QAItem(
            question=f"What did {hero.id} want to do with the food?",
            answer=f"{hero.id} wanted to {act.verb} right away.",
        ),
    ]
    if f.get("conflict"):
        qa.append(QAItem(
            question=f"Why did {parent.label_word} worry?",
            answer=f"{parent.label_word.capitalize()} worried because if {hero.id} went to {act.verb}, {prize.label} would be {act.soil}, and the grown-up would have more work to do.",
        ))
    if f.get("resolved"):
        gear = f["gear"]
        qa.append(QAItem(
            question=f"How did {gear.label} help?",
            answer=f"They used {gear.label} so {hero.id} could {act.verb} without ruining {hero.pronoun('possessive')} {prize.label}.",
        ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["activity"].tags)
    if world.facts.get("gear"):
        tags.add(world.facts["gear"].label.split()[-1].lower())
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
    lines.append(f"  fired rules: {sorted(n for n, _ in world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="kitchen", activity="soup", prize="shirt", name="Mabel", gender="girl", parent="mother", trait="hungry"),
    StoryParams(place="bakery", activity="cake", prize="apron", name="Hank", gender="boy", parent="father", trait="curious"),
    StoryParams(place="barn", activity="bread", prize="shirt", name="June", gender="girl", parent="mother", trait="bold"),
]


def explain_rejection(activity: Activity, prize: Prize) -> str:
    noun = prize.label if prize.plural else f"a {prize.label}"
    if not prize_at_risk(activity, prize):
        return f"(No story: {activity.gerund} splashes {sorted(activity.zone)}, but {noun} sits on the {prize.region}, so it would stay clean. Pick a prize worn where the mess reaches.)"
    return f"(No story: nothing in the gear catalog really protects {noun} from {activity.gerund}. The compromise has to fit the mess and the body part at risk.)"


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
    ap = argparse.ArgumentParser(description="A tall-tale storyworld about magical food and a careful compromise.")
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
            print(f"  {place:8} {act:7} {prize:7}  [{', '.join(genders)}]")
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
