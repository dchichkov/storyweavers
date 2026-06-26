#!/usr/bin/env python3
"""
grease_conflict_dialogue_comedy.py
==================================

A small standalone story world about a slippery grease mishap, a comic
argument, and a chatty fix.

Premise:
- A child is excited to help with a snack-time job or a little machine.
- Grease makes things slippery and messy.
- A parent or helper worries, and the two talk it out.
- A silly misunderstanding becomes a cooperative cleanup.

The world model tracks physical meters and emotional memes:
- grease, slip, dirty, shine, cleanup, laugh
- delight, worry, conflict, stubbornness, relief, affection

The story engine uses the state to build a short comedy with dialogue.
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
    plural: bool = False
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for k in ["grease", "dirty", "slip", "shine", "cleanup"]:
            self.meters.setdefault(k, 0.0)
        for k in ["joy", "worry", "conflict", "stubbornness", "relief", "affection", "laughter"]:
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


@dataclass
class Setting:
    place: str
    indoor: bool
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
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.zone = set(self.zone)
        clone.facts = dict(self.facts)
        return clone


def _rule_grease_spill(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters["grease"] < THRESHOLD:
            continue
        for item in world.worn_items(actor):
            if item.protective or item.region not in world.zone:
                continue
            if world.covered(actor, item.region):
                continue
            sig = ("grease", actor.id, item.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            item.meters["grease"] += 1
            item.meters["dirty"] += 1
            out.append(f"{actor.pronoun('possessive').capitalize()} {item.label} got greasy and dirty.")
    return out


def _rule_cleanup(world: World) -> list[str]:
    out: list[str] = []
    for item in world.entities.values():
        if item.meters["dirty"] < THRESHOLD or not item.caretaker:
            continue
        sig = ("cleanup", item.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        carer = world.get(item.caretaker)
        carer.meters["cleanup"] += 1
        out.append(f"That meant more cleanup for {carer.label}.")
    return out


def _rule_conflict(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.memes["worry"] < THRESHOLD or actor.memes["stubbornness"] < THRESHOLD:
            continue
        sig = ("conflict", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["conflict"] += 1
        out.append("__conflict__")
    return out


def _rule_relief(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.memes["conflict"] < THRESHOLD:
            continue
        if actor.memes["relief"] >= THRESHOLD:
            continue
        if actor.meters["cleanup"] >= THRESHOLD:
            sig = ("relief", actor.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            actor.memes["relief"] += 1
            out.append(f"{actor.id} finally looked less worried.")
    return out


CAUSAL_RULES = [_rule_grease_spill, _rule_cleanup, _rule_conflict, _rule_relief]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                for s in sents:
                    if s != "__conflict__":
                        produced.append(s)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def predict_mess(world: World, actor: Entity, activity: Activity, prize_id: str) -> dict:
    sim = world.copy()
    _do_activity(sim, sim.get(actor.id), activity, narrate=False)
    prize = sim.entities[prize_id]
    return {
        "soiled": prize.meters["dirty"] >= THRESHOLD,
        "cleanup": sum(e.meters["cleanup"] for e in sim.characters()),
    }


def prize_at_risk(activity: Activity, prize: Prize) -> bool:
    return prize.region in activity.zone


def select_gear(activity: Activity, prize: Prize) -> Optional[Gear]:
    for gear in GEAR:
        if activity.mess in gear.guards and prize.region in gear.covers:
            return gear
    return None


def activity_delight(activity: Activity) -> str:
    return {
        "pan": "the pan made a funny sizzling whisper",
        "bike": "the chain clicked like a tiny bug marching in boots",
        "machine": "the little machine hummed like a sleepy bee",
    }.get(activity.id, "it sounded like a goofy little adventure")


def setting_detail(setting: Setting, activity: Activity) -> str:
    if setting.indoor:
        return f"{setting.place.capitalize()} was warm and bright, with a neat spot for the job."
    return f"{setting.place.capitalize()} felt breezy and busy, like it was waiting for trouble and laughter."


def _do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    if activity.id not in world.setting.affords:
        return
    world.zone = set(activity.zone)
    actor.meters[activity.mess] += 1
    actor.memes["joy"] += 1
    propagate(world, narrate=narrate)


def introduce(world: World, hero: Entity) -> None:
    world.say(f"{hero.id} was a little {hero.type} who loved helping with anything shiny or silly.")


def loves_activity(world: World, hero: Entity, activity: Activity) -> None:
    world.say(f"{hero.pronoun().capitalize()} loved {activity.gerund}, because {activity_delight(activity)}.")


def buys(world: World, parent: Entity, hero: Entity, prize: Entity) -> None:
    world.say(f"One day, {parent.label} bought {hero.pronoun('object')} {prize.phrase}.")


def loves_prize(world: World, hero: Entity, prize: Entity) -> None:
    hero.memes["affection"] += 1
    prize.worn_by = hero.id
    world.say(f"{hero.id} adored {hero.pronoun('possessive')} {prize.label} and wore {prize.it()} everywhere.")


def arrive(world: World, hero: Entity, parent: Entity, activity: Activity) -> None:
    world.say(f"One day, {hero.id} and {hero.pronoun('possessive')} {parent.label} went to {world.setting.place}.")
    world.say(setting_detail(world.setting, activity))


def wants(world: World, hero: Entity, parent: Entity, activity: Activity) -> None:
    hero.memes["stubbornness"] += 1
    world.say(f"{hero.id} wanted to {activity.verb} right away.")
    world.say(f'"Can I do it now?" {hero.id} asked.')


def warn(world: World, parent: Entity, hero: Entity, activity: Activity, prize: Entity) -> bool:
    pred = predict_mess(world, hero, activity, prize.id)
    if not pred["soiled"]:
        return False
    world.facts["predicted_soil"] = activity.soil
    world.facts["predicted_cleanup"] = pred["cleanup"]
    world.say(f'"Careful," {parent.label} said. "That grease will make your {prize.label} {activity.soil}."')
    return True


def defies(world: World, hero: Entity, activity: Activity) -> None:
    world.say(f'{hero.id} made a brave face. "It will be fine!" {hero.id} said.')
    world.say(f"{hero.id} tried to {activity.rush}.")


def grab_conflict(world: World, parent: Entity, hero: Entity, activity: Activity) -> None:
    hero.memes["worry"] += 1
    propagate(world, narrate=False)
    world.say(
        f'But {hero.pronoun("possessive")} {parent.label} gave a tiny sigh and said, '
        f'"Not before we fix the grease."'
    )
    world.say(f'"You always say that," {hero.id} muttered, with a very dramatic frown.')


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
        f'{parent.label} pointed at the {prize.label} and then at the grease. '
        f'"How about we {gear_def.prep} and try again?"'
    )
    return gear_def


def accept(world: World, parent: Entity, hero: Entity, activity: Activity, prize: Entity, gear_def: Gear) -> None:
    hero.memes["joy"] += 1
    hero.memes["relief"] += 1
    hero.memes["conflict"] = 0.0
    world.say(f'{hero.id} blinked, then grinned. "Oh. That is actually clever," {hero.id} said.')
    world.say(
        f'They {gear_def.tail}. Soon {hero.id} was {activity.gerund}, '
        f"{prize.label} stayed clean, and even the grease looked embarrassed."
    )


def tell(
    setting: Setting,
    activity: Activity,
    prize_cfg: Prize,
    hero_name: str = "Milo",
    hero_type: str = "boy",
    parent_type: str = "mother",
    hero_traits: Optional[list[str]] = None,
) -> World:
    world = World(setting)
    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type=hero_type,
        label=hero_name,
    ))
    parent = world.add(Entity(
        id="Parent",
        kind="character",
        type=parent_type,
        label="Mom" if parent_type == "mother" else "Dad",
    ))
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
    buys(world, parent, hero, prize)
    loves_prize(world, hero, prize)

    world.para()
    arrive(world, hero, parent, activity)
    wants(world, hero, parent, activity)
    warn(world, parent, hero, activity, prize)
    defies(world, hero, activity)
    grab_conflict(world, parent, hero, activity)

    world.para()
    gear_def = compromise(world, parent, hero, activity, prize)
    if gear_def:
        accept(world, parent, hero, activity, prize, gear_def)

    world.facts.update(
        hero=hero,
        parent=parent,
        prize=prize,
        activity=activity,
        setting=setting,
        gear=gear_def,
        resolved=gear_def is not None,
        conflict=hero.memes["conflict"] >= THRESHOLD,
    )
    return world


SETTINGS = {
    "kitchen": Setting(place="the kitchen", indoor=True, affords={"pan", "machine"}),
    "garage": Setting(place="the garage", indoor=True, affords={"bike", "machine"}),
    "workshop": Setting(place="the workshop", indoor=True, affords={"machine", "bike"}),
}

ACTIVITIES = {
    "pan": Activity(
        id="pan",
        verb="flip the pancakes",
        gerund="flipping pancakes",
        rush="dash to the pan",
        mess="grease",
        soil="all greasy",
        zone={"hands", "torso"},
        keyword="grease",
        tags={"grease", "cooking"},
    ),
    "bike": Activity(
        id="bike",
        verb="oil the bike chain",
        gerund="oiling the bike chain",
        rush="lean over the bike",
        mess="grease",
        soil="spotty with grease",
        zone={"hands", "torso"},
        keyword="grease",
        tags={"grease", "bike"},
    ),
    "machine": Activity(
        id="machine",
        verb="help with the little machine",
        gerund="helping with the little machine",
        rush="poke the machine",
        mess="grease",
        soil="smudged with grease",
        zone={"hands", "torso"},
        keyword="grease",
        tags={"grease", "machine"},
    ),
}

PRIZES = {
    "shirt": Prize(label="shirt", phrase="a bright shirt", type="shirt", region="torso"),
    "apron": Prize(label="apron", phrase="a neat apron", type="apron", region="torso"),
    "gloves": Prize(label="gloves", phrase="small yellow gloves", type="gloves", region="hands", plural=True),
}

GEAR = [
    Gear(
        id="apron",
        label="an old apron",
        covers={"torso"},
        guards={"grease"},
        prep="put on an old apron first",
        tail="put on the old apron",
    ),
    Gear(
        id="gloves",
        label="clean gloves",
        covers={"hands"},
        guards={"grease"},
        prep="wear clean gloves first",
        tail="slipped on the clean gloves",
        plural=True,
    ),
    Gear(
        id="overall",
        label="a long overall",
        covers={"torso", "hands"},
        guards={"grease"},
        prep="wear the long overall",
        tail="pulled on the long overall",
    ),
]

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Nina", "Ella"]
BOY_NAMES = ["Milo", "Toby", "Finn", "Noah", "Eli"]
TRAITS = ["curious", "cheerful", "silly", "bold", "helpful"]


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
    "grease": [
        ("What is grease?", "Grease is a slippery oily stuff that can make things messy and hard to hold."),
    ],
    "cooking": [
        ("Why do some people wear an apron while cooking?", "An apron helps keep clothes from getting splashed or stained while cooking."),
    ],
    "bike": [
        ("Why do bike chains need oil?", "Bike chains need oil so the metal parts can move smoothly and not squeak or stick."),
    ],
    "machine": [
        ("Why do machines need care?", "Machines need care so their moving parts can work smoothly and safely."),
    ],
}

KNOWLEDGE_ORDER = ["grease", "cooking", "bike", "machine"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, parent, act, prize = f["hero"], f["parent"], f["activity"], f["prize"]
    return [
        f'Write a short comedy for a child about "{act.keyword}" and a little argument that ends kindly.',
        f"Tell a playful story where {hero.id} wants to {act.verb}, but {parent.label} worries about {hero.pronoun('possessive')} {prize.label}.",
        f"Write a gentle dialogue story about grease, a careful warning, and a smart compromise.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, parent, prize, act = f["hero"], f["parent"], f["prize"], f["activity"]
    qa = [
        QAItem(
            question=f"Who is the story about?",
            answer=f"It is about {hero.id}, a little {hero.type}, and {hero.pronoun('possessive')} {parent.label}.",
        ),
        QAItem(
            question=f"What did {hero.id} want to do?",
            answer=f"{hero.id} wanted to {act.verb}.",
        ),
        QAItem(
            question=f"Why did {parent.label} worry?",
            answer=f"{parent.label} worried because the grease could make {hero.pronoun('possessive')} {prize.label} {act.soil}.",
        ),
    ]
    if f.get("resolved"):
        gear = f["gear"]
        qa.append(
            QAItem(
                question=f"How did they solve the problem?",
                answer=f"They used {gear.label} so {hero.id} could keep helping without ruining the {prize.label}.",
            )
        )
        qa.append(
            QAItem(
                question=f"How did {hero.id} feel at the end?",
                answer=f"{hero.id} felt happy and relieved after the two of them found a funny, safe plan.",
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
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="kitchen", activity="pan", prize="shirt", name="Milo", gender="boy", parent="mother", trait="silly"),
    StoryParams(place="garage", activity="bike", prize="gloves", name="Lily", gender="girl", parent="father", trait="curious"),
    StoryParams(place="workshop", activity="machine", prize="apron", name="Toby", gender="boy", parent="mother", trait="helpful"),
]


def explain_rejection(activity: Activity, prize: Prize) -> str:
    noun = prize.label if prize.plural else f"a {prize.label}"
    if not prize_at_risk(activity, prize):
        return f"(No story: {activity.gerund} does not really threaten {noun}, so there is no honest grease problem.)"
    return f"(No story: no gear in this world can protect {noun} from {activity.gerund}.)"


def explain_gender(prize_id: str, gender: str) -> str:
    ok = " / ".join(sorted(PRIZES[prize_id].genders))
    return f"(No story: a {PRIZES[prize_id].label} is not constrained by gender here; try {ok}.)"


ASP_RULES = r"""
prize_at_risk(A, P) :- zone(A, R), worn_on(P, R).
protects(G, A, P) :- prize_at_risk(A, P), gear(G), guards(G, M), mess_of(A, M), covers(G, R), worn_on(P, R).
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
            lines.append(asp.fact("zone", aid, r))
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
    ap = argparse.ArgumentParser(description="A comedy story world about grease, conflict, and dialogue.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
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
                 params.name, params.gender, params.parent, [params.trait, "silly"])
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
            print(f"  {place:10} {act:8} {prize:8} [{', '.join(genders)}]")
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
