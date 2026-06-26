#!/usr/bin/env python3
"""
storyworlds/worlds/exaggerate_rural_pick_gerund_inner_monologue_surprise.py
===========================================================================

A small adventure-flavored story world about a rural child, a careful pick, an
inner monologue, and a surprise.

Seed premise:
- In a rural place, a child wants to pick something growing outside.
- The child imagines the scene in an exaggerated inner monologue.
- A guardian worries about a favorite item getting scratched, stained, or soaked.
- A reasonable gear-based compromise makes the adventure safe.
- A small surprise at the end proves the trip changed the world.

This world keeps the number of valid stories intentionally small:
only combinations where the chosen activity could honestly damage the prize,
and where the available gear actually solves that problem, are allowed.
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
        for k in ["wet", "dirty", "scratched", "tired"]:
            self.meters.setdefault(k, 0.0)
        for k in ["joy", "fear", "care", "surprise", "love", "resolve", "conflict", "inner_monologue"]:
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
    indoor: bool = False
    affords: set[str] = field(default_factory=set)
    rural: bool = False


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


def _r_soil(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        for mess in ["wet", "dirty", "scratched"]:
            if actor.meters[mess] < THRESHOLD:
                continue
            for item in world.worn_items(actor):
                if item.protective or item.region not in world.zone:
                    continue
                if world.covered(actor, item.region):
                    continue
                sig = ("soil", item.id, mess)
                if sig in world.fired:
                    continue
                world.fired.add(sig)
                item.meters[mess] += 1
                item.meters["dirty"] += 1
                if mess == "scratched":
                    item.meters["scratched"] += 1
                out.append(f"{actor.pronoun('possessive').capitalize()} {item.label} got {mess}.")
    return out


def _r_work(world: World) -> list[str]:
    out: list[str] = []
    for item in world.entities.values():
        if item.meters["dirty"] < THRESHOLD or not item.caretaker:
            continue
        sig = ("work", item.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        caretaker = world.get(item.caretaker)
        caretaker.memes["care"] += 1
        out.append(f"That would mean more work for {caretaker.label_word}.")
    return out


def _r_surprise(world: World) -> list[str]:
    hero = next((e for e in world.characters() if e.kind == "character" and e.type in {"girl", "boy"}), None)
    if hero is None:
        return []
    if world.facts.get("surprise_seen"):
        return []
    if world.facts.get("activity_done") and world.facts.get("compromise_done"):
        world.facts["surprise_seen"] = True
        hero.memes["surprise"] += 1
        return ["__surprise__"]
    return []


CAUSAL_RULES: list[Rule] = [
    Rule("soil", "physical", _r_soil),
    Rule("work", "physical", _r_work),
    Rule("surprise", "story", _r_surprise),
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
                produced.extend(s for s in sents if s != "__surprise__")
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
    world.facts["activity_done"] = True
    propagate(world, narrate=narrate)


def activity_flavor(activity: Activity) -> str:
    return {
        "berries": "the brambles looked like a thorny maze from a treasure map",
        "apples": "the orchard branches seemed to hide a secret behind every leaf",
        "herbs": "the garden rows smelled like a pocketful of green wind",
    }.get(activity.id, "the day felt ready for a small adventure")


def setting_detail(setting: Setting, activity: Activity) -> str:
    if setting.rural:
        return f"Far from town, {setting.place} stretched quiet and open under a big sky."
    return f"{setting.place.capitalize()} looked calm and ready for a careful adventure."


def introduce(world: World, hero: Entity) -> None:
    trait = next((t for t in hero.traits if t != "little"), "")
    desc = f"little {trait} {hero.type}".strip()
    world.say(f"{hero.id} was a {desc} who loved wandering where the paths turned dusty and wide.")


def loves_activity(world: World, hero: Entity, activity: Activity) -> None:
    world.say(
        f"{hero.pronoun().capitalize()} loved {activity.gerund}, and {activity_flavor(activity)}."
    )
    world.say(
        f"In {hero.id}'s own head, the bushes were always bigger, braver, and more dramatic than they really were."
    )


def arrive(world: World, hero: Entity, parent: Entity, activity: Activity) -> None:
    day = "One breezy afternoon, " if world.setting.rural else "One day, "
    world.say(
        f"{day}{hero.id} and {hero.pronoun('possessive')} {parent.label_word} went to {world.setting.place}."
    )
    world.say(setting_detail(world.setting, activity))


def wants(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["inner_monologue"] += 1
    world.say(
        f'{hero.id} thought, "This is going to be the greatest picking quest ever," '
        f"while {hero.pronoun('subject')} stepped closer to the plants."
    )


def warn(world: World, parent: Entity, hero: Entity, activity: Activity, prize: Entity) -> bool:
    pred = predict_mess(world, hero, activity, prize.id)
    if not pred["soiled"]:
        return False
    world.say(
        f'"If you {activity.verb}, your {prize.label} will get {activity.soil}," '
        f"{hero.pronoun('possessive')} {parent.label_word} said."
    )
    return True


def defies(world: World, hero: Entity, activity: Activity) -> None:
    world.say(
        f"{hero.id} gave a tiny huff and, in {hero.pronoun('possessive')} own mind, made the bushes sound like a dragon's cave."
    )
    world.say(f"{hero.pronoun().capitalize()} tried to {activity.rush}.")


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
    world.facts["compromise_done"] = True
    world.say(
        f'{hero.pronoun("possessive").capitalize()} {parent.label_word} smiled and said, '
        f'"How about we {gear_def.prep} first?"'
    )
    return gear_def


def accept(world: World, parent: Entity, hero: Entity, activity: Activity, prize: Entity, gear_def: Gear) -> None:
    hero.memes["joy"] += 1
    hero.memes["love"] += 1
    hero.memes["conflict"] = 0.0
    world.say(
        f"{hero.id}'s eyes widened, and {hero.pronoun()} nodded fast. "
        f'"That sounds even better," {hero.pronoun()} said.'
    )
    world.say(
        f"They {gear_def.tail}. Soon {hero.id} was {activity.gerund}, {prize.label} stayed clean, "
        f"and the path felt like the start of a real expedition."
    )


def surprise_end(world: World, hero: Entity, activity: Activity, prize: Entity) -> None:
    world.say(
        f"Then came a surprise: tucked near the last patch, {hero.id} found a tiny bundle of {prize.label} hidden under a leaf."
    )
    world.say(
        f"{hero.pronoun('subject').capitalize()} laughed, because the day had turned into a treasure hunt after all."
    )


def tell(setting: Setting, activity: Activity, prize_cfg: Prize, hero_name: str = "Maya",
         hero_type: str = "girl", hero_traits: Optional[list[str]] = None,
         parent_type: str = "mother") -> World:
    world = World(setting)
    world.weather = activity.weather

    hero = world.add(Entity(
        id=hero_name, kind="character", type=hero_type,
        traits=["little"] + (hero_traits or ["curious", "brave"])
    ))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label="the parent"))
    prize = world.add(Entity(
        id="prize", type=prize_cfg.type, label=prize_cfg.label, phrase=prize_cfg.phrase,
        owner=hero.id, caretaker=parent.id, region=prize_cfg.region, plural=prize_cfg.plural
    ))

    introduce(world, hero)
    loves_activity(world, hero, activity)
    world.say(f"That morning, {parent.label_word} had bought {hero.pronoun('object')} {prize.phrase}.")
    world.say(f"{hero.id} loved {prize.it()} and wore {prize.it()} proudly for the outing.")

    world.para()
    arrive(world, hero, parent, activity)
    wants(world, hero, activity)
    warn(world, parent, hero, activity, prize)
    defies(world, hero, activity)

    world.para()
    gear_def = compromise(world, parent, hero, activity, prize)
    if gear_def:
        accept(world, parent, hero, activity, prize, gear_def)

    _do_activity(world, hero, activity, narrate=True)
    if gear_def:
        surprise_end(world, hero, activity, prize)

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
    "orchard": Setting(place="the hill orchard", rural=True, affords={"apples"}),
    "bramble_patch": Setting(place="the blackberry patch", rural=True, affords={"berries"}),
    "kitchen_garden": Setting(place="the kitchen garden", rural=True, affords={"herbs"}),
}

ACTIVITIES = {
    "apples": Activity(
        id="apples",
        verb="pick the apples",
        gerund="picking apples",
        rush="dash under the branches",
        mess="scratched",
        soil="scratched and smudged",
        zone={"torso", "arms"},
        weather="sunny",
        keyword="apples",
        tags={"apples", "fruit"},
    ),
    "berries": Activity(
        id="berries",
        verb="pick the blackberries",
        gerund="picking blackberries",
        rush="plunge into the brambles",
        mess="scratched",
        soil="scratched and dirty",
        zone={"arms", "hands", "torso"},
        weather="sunny",
        keyword="berries",
        tags={"berries", "fruit", "thorns"},
    ),
    "herbs": Activity(
        id="herbs",
        verb="pick the herbs",
        gerund="picking herbs",
        rush="kneel into the garden rows",
        mess="dirty",
        soil="dirty and dusty",
        zone={"hands", "torso"},
        weather="sunny",
        keyword="herbs",
        tags={"herbs", "garden"},
    ),
}

PRIZES = {
    "shirt": Prize("shirt", "a clean shirt with blue buttons", "shirt", "torso"),
    "coat": Prize("coat", "a favorite coat with brass snaps", "coat", "torso"),
    "gloves": Prize("gloves", "soft new gloves", "gloves", "hands", plural=True),
}

GEAR = [
    Gear("gardening_gloves", "gardening gloves", {"hands", "arms"}, {"scratched"}, "put on the gardening gloves", "went home for the gardening gloves", plural=True),
    Gear("smock", "an old smock", {"torso"}, {"dirty", "scratched"}, "put on an old smock", "went back for the old smock"),
    Gear("sleeves", "long sleeves", {"arms", "torso"}, {"scratched"}, "pull on long sleeves", "went back for the long sleeves"),
]

GIRL_NAMES = ["Maya", "Nora", "Ivy", "June", "Lina", "Rose"]
BOY_NAMES = ["Evan", "Toby", "Finn", "Owen", "Luke", "Jasper"]
TRAITS = ["curious", "brave", "stubborn", "cheerful", "spirited", "bold"]


def valid_combos() -> list[tuple[str, str]]:
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
    "apples": [("What are apples?", "Apples are round fruits that grow on trees. People can pick them when they are ripe.")],
    "berries": [("What are blackberries?", "Blackberries are small, juicy fruits that grow on thorny bushes.")],
    "herbs": [("What are herbs?", "Herbs are plants people use for cooking because they smell strong and fresh.")],
    "gardening_gloves": [("Why wear gardening gloves?", "Gardening gloves help protect your hands from dirt and scratches.")],
    "smock": [("What is a smock for?", "A smock is a loose cover that helps keep clothes clean while you work or play.")],
    "sleeves": [("Why wear long sleeves in bushes?", "Long sleeves can help protect your arms from scratches.")],
    "fruit": [("What is fruit?", "Fruit is the part of a plant that grows around seeds and is often sweet to eat.")],
    "thorns": [("What are thorns?", "Thorns are sharp points on some plants that can scratch skin.")],
    "garden": [("What makes a garden special?", "A garden is a place where plants are grown and cared for.")],
}
KNOWLEDGE_ORDER = ["apples", "berries", "herbs", "fruit", "thorns", "garden", "gardening_gloves", "smock", "sleeves"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, parent, act, prize = f["hero"], f["parent"], f["activity"], f["prize_cfg"]
    return [
        f'Write an adventure story for a child named {hero.id} about {act.gerund} in a rural place.',
        f"Tell a story where {hero.id} wants to {act.verb} but {hero.pronoun('possessive')} {parent.label_word} worries about {prize.phrase}.",
        f"Write a gentle adventure with an exaggerated inner monologue and a surprise ending using the word '{act.keyword}'.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, parent, prize, act = f["hero"], f["parent"], f["prize"], f["activity"]
    qa = [
        QAItem(
            question=f"Who is the story about?",
            answer=f"The story is about {hero.id}, a little {next(t for t in hero.traits if t != 'little')} {hero.type}, and {hero.pronoun('possessive')} {parent.label_word}.",
        ),
        QAItem(
            question=f"What did {hero.id} want to do in {world.setting.place}?",
            answer=f"{hero.id} wanted to {act.verb}, and {hero.pronoun('subject')} imagined it as a grand adventure.",
        ),
        QAItem(
            question=f"Why did {parent.label_word} worry about {prize.label}?",
            answer=f"{parent.label_word.capitalize()} worried because {act.verb} could leave {prize.label} {act.soil}.",
        ),
    ]
    if f.get("resolved"):
        qa.append(QAItem(
            question=f"How did the family make the trip safe?",
            answer=f"They used {f['gear'].label} so {hero.id} could keep {prize.label} clean while still going on the adventure.",
        ))
        qa.append(QAItem(
            question=f"What surprise happened at the end?",
            answer=f"{hero.id} found a hidden bundle of {prize.label} tucked near the last patch, which made the day feel like a treasure hunt.",
        ))
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
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams("bramble_patch", "berries", "shirt", "Maya", "girl", "mother", "curious"),
    StoryParams("orchard", "apples", "coat", "Evan", "boy", "father", "brave"),
    StoryParams("kitchen_garden", "herbs", "gloves", "Nora", "girl", "mother", "spirited"),
]


def explain_rejection(activity: Activity, prize: Prize) -> str:
    if not prize_at_risk(activity, prize):
        return f"(No story: {activity.gerund} would not honestly damage {prize.label}.)"
    return f"(No story: no gear in this world can reasonably solve {activity.gerund} plus {prize.label}.)"


def explain_gender(prize_id: str, gender: str) -> str:
    ok = " / ".join(sorted(PRIZES[prize_id].genders))
    return f"(No story: a {PRIZES[prize_id].label} isn't a typical {gender}'s item here; try --gender {ok}.)"


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
        if s.rural:
            lines.append(asp.fact("rural", sid))
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
        if p.plural:
            lines.append(asp.fact("prize_plural", pid))
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
    ap = argparse.ArgumentParser(description="Adventure story world: a rural pick, an inner monologue, and a surprise.")
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
    return StoryParams(place, activity, prize_id, name, gender, parent, trait)


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
            print(f"  {place:14} {act:10} {prize:8}  [{', '.join(genders)}]")
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
