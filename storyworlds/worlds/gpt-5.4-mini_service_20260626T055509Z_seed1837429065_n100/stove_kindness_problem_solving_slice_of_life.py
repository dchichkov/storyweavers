#!/usr/bin/env python3
"""
storyworlds/worlds/stove_kindness_problem_solving_slice_of_life.py
===================================================================

A small slice-of-life storyworld about a child, a warm stove, kindness, and
simple problem solving.

Seed tale used to shape the world:
---
A child wanted to help make dinner on the stove. The grown-up worried about a
favorite shirt and hot splashes, but the child really wanted to be useful.

A little argument grew, then the grown-up noticed the child was not being
careless on purpose. They found a kinder plan: a safe job, a snug apron, and a
way to help that kept everyone calm.

World model highlights:
---
- The kitchen has a stove that can heat pots and make splashes.
- The hero's mood can shift between eagerness, worry, hurt feelings, and relief.
- Kindness matters: a gentle offer can turn a tense moment into teamwork.
- Problem solving matters: the right helper gear and a safer task can protect
  a favorite shirt while still letting the child help.

Causal state updates:
---
    child wants to help on the stove  -> eagerness +1, hope +1
    hot cooking + no protection       -> shirt gets splashed, worry +1
    parent notices risk               -> caution +1, care +1
    safe compromise accepted          -> joy +1, calm +1, conflict -> 0
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
RISK_METER = "splashed"
HEAT_METER = "heat"
CLEAN_METER = "clean"
MEME_KEYS = {"joy", "care", "worry", "eagerness", "calm", "hurt"}


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
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for k in [RISK_METER, HEAT_METER, CLEAN_METER]:
            self.meters.setdefault(k, 0.0)
        for k in MEME_KEYS:
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def noun(self) -> str:
        return self.label or self.type

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
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
        self.facts: dict = {}
        self.zone: set[str] = set()

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
        clone.facts = dict(self.facts)
        clone.paragraphs = [[]]
        return clone


def _r_splash(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters[RISK_METER] < THRESHOLD:
            continue
        for item in world.worn_items(actor):
            if item.protective or item.region not in world.zone:
                continue
            if world.covered(actor, item.region):
                continue
            sig = ("splash", actor.id, item.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            item.meters[RISK_METER] += 1
            item.meters[CLEAN_METER] -= 1
            out.append(f"{actor.pronoun('possessive').capitalize()} {item.noun()} got splashed.")
    return out


def _r_heat(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters[HEAT_METER] < THRESHOLD:
            continue
        sig = ("heat", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["worry"] += 1
        out.append("The stove felt too hot to trust without care.")
    return out


def _r_calm(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.memes["calm"] < THRESHOLD or actor.memes["worry"] >= THRESHOLD:
            continue
        sig = ("calm", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        out.append(f"{actor.noun()} seemed calm and ready to help.")
    return out


CAUSAL_RULES = [_r_splash, _r_heat, _r_calm]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            lines = rule(world)
            if lines:
                changed = True
                produced.extend(lines)
    if narrate:
        for line in produced:
            world.say(line)
    return produced


def story_is_reasonable(activity: Activity, prize: Prize) -> bool:
    return prize.region in activity.zone


def select_gear(activity: Activity, prize: Prize) -> Optional[Gear]:
    for gear in GEAR:
        if prize.region in gear.covers and activity.mess in gear.guards:
            return gear
    return None


def predict_risk(world: World, hero: Entity, activity: Activity, prize_id: str) -> dict:
    sim = world.copy()
    _do_activity(sim, sim.get(hero.id), activity, narrate=False)
    prize = sim.get(prize_id)
    return {
        "splashed": prize.meters[RISK_METER] >= THRESHOLD,
        "worry": hero.memes["worry"] + sim.get(hero.id).memes["worry"],
    }


def _do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    if activity.id not in world.setting.affords:
        return
    world.zone = set(activity.zone)
    actor.meters[RISK_METER] += 1
    actor.meters[HEAT_METER] += 1
    actor.memes["eagerness"] += 1
    propagate(world, narrate=narrate)


def introduce(world: World, hero: Entity) -> None:
    world.say(
        f"{hero.noun()} was a little {hero.type} who liked helpful jobs and quiet kitchen afternoons."
    )


def loves_helping(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["joy"] += 1
    world.say(
        f"{hero.pronoun().capitalize()} loved helping at the stove, especially {activity.gerund}, "
        f"because it made dinner feel like a shared project."
    )


def setup_kitchen(world: World, parent: Entity, hero: Entity, prize: Entity) -> None:
    world.say(
        f"That evening, {hero.id} and {parent.noun()} were in {world.setting.place}, "
        f"with the stove humming softly and {hero.pronoun('possessive')} {prize.label} nearby."
    )


def wants_to_help(world: World, hero: Entity, parent: Entity, activity: Activity) -> None:
    hero.memes["eagerness"] += 1
    hero.memes["calm"] += 0.5
    world.say(
        f"{hero.id} wanted to {activity.verb} right away, but {hero.pronoun('possessive')} "
        f"{parent.noun()} lifted a careful hand and asked {hero.pronoun('object')} to pause."
    )


def warn(world: World, parent: Entity, hero: Entity, activity: Activity, prize: Entity) -> bool:
    pred = predict_risk(world, hero, activity, prize.id)
    if not pred["splashed"]:
        return False
    world.facts["predicted_soil"] = activity.soil
    world.say(
        f'"If you rush in now, your {prize.label} might get {activity.soil}," '
        f"{parent.pronoun('possessive')} {parent.noun()} said kindly. "
        f'"Let’s solve it together."'
    )
    return True


def child_pushes_back(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["hurt"] += 1
    world.say(
        f"{hero.id} felt a little disappointed and tried to {activity.rush}, "
        f"because {hero.pronoun()} really wanted to be useful."
    )


def offer_support(world: World, parent: Entity, hero: Entity, activity: Activity) -> None:
    hero.memes["care"] += 1
    hero.memes["worry"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Then {parent.noun()} knelt down and said, "
        f'"You can still help. We just need a safer way than reaching straight for the stove."'
    )


def compromise(world: World, parent: Entity, hero: Entity, activity: Activity, prize: Entity) -> Optional[Gear]:
    gear = select_gear(activity, prize)
    if gear is None:
        return None
    gear_ent = world.add(
        Entity(
            id=gear.id,
            type="gear",
            label=gear.label,
            owner=hero.id,
            caretaker=parent.id,
            protective=True,
            covers=set(gear.covers),
            plural=gear.plural,
        )
    )
    gear_ent.worn_by = hero.id
    if not predict_risk(world, hero, activity, prize.id)["splashed"]:
        return None
    world.entities.pop(gear_ent.id, None)
    return None


def resolve_with_gear(world: World, parent: Entity, hero: Entity, activity: Activity, prize: Entity) -> Optional[Gear]:
    gear = select_gear(activity, prize)
    if gear is None:
        return None
    gear_ent = world.add(
        Entity(
            id=gear.id,
            type="gear",
            label=gear.label,
            owner=hero.id,
            caretaker=parent.id,
            protective=True,
            covers=set(gear.covers),
            plural=gear.plural,
        )
    )
    gear_ent.worn_by = hero.id
    world.facts["gear"] = gear
    world.say(
        f"{parent.pronoun('possessive').capitalize()} {parent.noun()} found {gear.label} and showed {hero.id} a safer plan: "
        f"{gear.prep}."
    )
    return gear


def accept(world: World, parent: Entity, hero: Entity, activity: Activity, prize: Entity, gear: Gear) -> None:
    hero.memes["joy"] += 1
    hero.memes["calm"] += 1
    hero.memes["hurt"] = 0
    hero.memes["worry"] = 0
    world.say(
        f"{hero.id}'s face softened, and {hero.pronoun()} nodded. Together they used {gear.label}, "
        f"{gear.tail}, and {hero.id} got to help while {prize.label} stayed clean."
    )
    world.say(
        f"Soon the kitchen felt peaceful again, with the stove doing its warm work and {hero.id} standing proud beside {parent.noun()}."
    )


def tell(setting: Setting, activity: Activity, prize_cfg: Prize, hero_name: str = "Maya", hero_type: str = "girl",
         parent_type: str = "mother") -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label="mom" if parent_type == "mother" else "dad"))
    prize = world.add(
        Entity(
            id="prize",
            type=prize_cfg.type,
            label=prize_cfg.label,
            phrase=prize_cfg.phrase,
            owner=hero.id,
            caretaker=parent.id,
            worn_by=hero.id,
            plural=prize_cfg.plural,
        )
    )

    introduce(world, hero)
    loves_helping(world, hero, activity)
    setup_kitchen(world, parent, hero, prize)

    world.para()
    wants_to_help(world, hero, parent, activity)
    warn(world, parent, hero, activity, prize)
    child_pushes_back(world, hero, activity)
    offer_support(world, parent, hero, activity)

    world.para()
    gear = resolve_with_gear(world, parent, hero, activity, prize)
    if gear:
        accept(world, parent, hero, activity, prize, gear)

    world.facts.update(
        hero=hero,
        parent=parent,
        prize=prize,
        activity=activity,
        setting=setting,
        gear=gear,
        resolved=gear is not None,
    )
    return world


SETTINGS = {
    "kitchen": Setting(place="the kitchen", affords={"soup", "cocoa", "toast"}),
    "tiny_kitchen": Setting(place="the tiny kitchen", affords={"soup", "cocoa"}),
    "grandma_kitchen": Setting(place="Grandma's kitchen", affords={"soup", "toast"}),
}

ACTIVITIES = {
    "soup": Activity(
        id="soup",
        verb="stir the soup on the stove",
        gerund="stirring soup",
        rush="run to the stove and grab the spoon",
        mess="splashed",
        soil="splashed with soup",
        zone={"torso"},
        keyword="soup",
        tags={"soup", "stove", "kindness", "problem_solving"},
    ),
    "cocoa": Activity(
        id="cocoa",
        verb="warm the cocoa on the stove",
        gerund="warming cocoa",
        rush="dash to the pot and reach over the heat",
        mess="splashed",
        soil="spattered with cocoa",
        zone={"torso"},
        keyword="cocoa",
        tags={"cocoa", "stove", "kindness", "problem_solving"},
    ),
    "toast": Activity(
        id="toast",
        verb="butter the toast near the stove",
        gerund="buttering toast",
        rush="lean too close to the warm pan",
        mess="splashed",
        soil="smudged with butter",
        zone={"torso"},
        keyword="toast",
        tags={"toast", "stove", "kindness", "problem_solving"},
    ),
}

PRIZES = {
    "shirt": Prize(label="shirt", phrase="a favorite clean shirt", type="shirt", region="torso"),
    "apron": Prize(label="apron", phrase="a bright apron", type="apron", region="torso"),
}

GEAR = [
    Gear(
        id="apron",
        label="a sturdy apron",
        covers={"torso"},
        guards={"splashed"},
        prep="put on a sturdy apron first",
        tail="putting on the apron before going back to the stove",
    ),
]

GIRL_NAMES = ["Maya", "Ella", "Nora", "Lina", "Sophie", "Ivy"]
BOY_NAMES = ["Theo", "Ben", "Milo", "Noah", "Finn", "Owen"]
TRAITS = ["gentle", "helpful", "thoughtful", "curious", "patient"]


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
    out: list[tuple[str, str, str]] = []
    for place, setting in SETTINGS.items():
        for aid in setting.affords:
            act = ACTIVITIES[aid]
            for pid, prize in PRIZES.items():
                if story_is_reasonable(act, prize) and select_gear(act, prize):
                    out.append((place, aid, pid))
    return out


KNOWLEDGE = {
    "stove": [("What is a stove?", "A stove is a kitchen appliance that makes heat for cooking food in pots and pans.")],
    "apron": [("What does an apron do?", "An apron helps keep clothes cleaner when you cook or do messy work.")],
    "soup": [("What is soup?", "Soup is a warm food made with broth and pieces of vegetables, noodles, or meat.")],
    "cocoa": [("What is cocoa?", "Cocoa is a warm chocolate drink that is often sweet and cozy.")],
    "toast": [("What is toast?", "Toast is bread that has been heated until it turns warm and crisp.")],
    "kindness": [("What is kindness?", "Kindness means being gentle, caring, and helpful to someone else.")],
    "problem_solving": [("What is problem solving?", "Problem solving means finding a smart way to fix a tricky situation.")],
}


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, parent, act, prize = f["hero"], f["parent"], f["activity"], f["prize"]
    return [
        f'Write a short slice-of-life story for a young child about a {hero.type} named {hero.id} helping at the stove.',
        f"Tell a warm story where {hero.id} wants to {act.verb}, but {parent.noun()} worries about {prize.phrase}, and they solve it kindly.",
        f'Write a simple kitchen story that includes the word "stove" and ends with a safe plan that lets {hero.id} help.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, parent, prize, act = f["hero"], f["parent"], f["prize"], f["activity"]
    gear = f.get("gear")
    qas = [
        QAItem(
            question=f"Who wanted to help with {act.keyword} at the stove?",
            answer=f"{hero.id} wanted to help, because {hero.pronoun()} liked being useful in the kitchen.",
        ),
        QAItem(
            question=f"Why did {parent.noun()} worry about {prize.label} near the stove?",
            answer=f"{parent.noun().capitalize()} worried because the {prize.label} could get {act.soil} if the cooking got splashed.",
        ),
        QAItem(
            question=f"What did they do to make the plan safer?",
            answer=f"They used {gear.label} and gave {hero.id} a safer job, so the help could continue without ruining the {prize.label}.",
        ),
    ]
    return qas


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["activity"].tags)
    if world.facts.get("gear"):
        tags.add("apron")
    out: list[QAItem] = []
    for tag in ["stove", "kindness", "problem_solving", "apron", "soup", "cocoa", "toast"]:
        if tag in tags:
            out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE[tag])
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
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.protective:
            bits.append(f"covers={sorted(e.covers)}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="kitchen", activity="soup", prize="shirt", name="Maya", gender="girl", parent="mother", trait="helpful"),
    StoryParams(place="tiny_kitchen", activity="cocoa", prize="shirt", name="Theo", gender="boy", parent="father", trait="gentle"),
    StoryParams(place="grandma_kitchen", activity="toast", prize="shirt", name="Nora", gender="girl", parent="mother", trait="thoughtful"),
]


ASP_RULES = r"""
prize_at_risk(A, P) :- splashes(A, R), worn_on(P, R).
protected(G, A, P) :- prize_at_risk(A, P), guards(G, M), mess_of(A, M), covers(G, R), worn_on(P, R).
valid(Place, A, P) :- affords(Place, A), prize_at_risk(A, P), protected(_, A, P).
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
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("worn_on", pid, p.region))
        for g in sorted(p.genders):
            lines.append(asp.fact("wears", g, pid))
    for g in GEAR:
        lines.append(asp.fact("gear", g.id))
        for c in sorted(g.covers):
            lines.append(asp.fact("covers", g.id, c))
        for m in sorted(g.guards):
            lines.append(asp.fact("guards", g.id, m))
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
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and python:")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


def explain_rejection(activity: Activity, prize: Prize) -> str:
    return f"(No story: {activity.verb} does not threaten a {prize.label} in a way this world can solve safely.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Slice-of-life stove storyworld with kindness and problem solving.")
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
        if not (story_is_reasonable(act, pr) and select_gear(act, pr)):
            raise StoryError(explain_rejection(act, pr))
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.activity is None or c[1] == args.activity)
              and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, activity, prize = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(sorted(PRIZES[prize].genders))
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
        triples = asp_valid_combos()
        stories = asp_valid_stories()
        print(f"{len(triples)} compatible story combos ({len(stories)} gendered):\n")
        for place, act, prize in triples:
            genders = sorted(g for (pl, a, pr, g) in stories if (pl, a, pr) == (place, act, prize))
            print(f"  {place:14} {act:8} {prize:8} [{', '.join(genders)}]")
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
