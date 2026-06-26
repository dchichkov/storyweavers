#!/usr/bin/env python3
"""
storyworlds/worlds/befriend_happy_ending_dialogue_sound_effects_bedtime.py
=======================================================================

A standalone story world sketch about a child who wants to befriend a shy
night-time creature (a little owl).  The tension is about being too loud,
the compromise uses a whisper scarf, and the happy ending comes when the
owl answers back.  The story includes dialogue and sound effects, written
in a gentle, bedtime-story style.

Causal model
------------
    do activity (call to the owl)   -> actor.meters["loud"] += 1
                                       actor.memes["hope"] += 1
    actor loud + worn item uncovered -> item.meters["scared"] += 1
                                       (the owl won't come)
    worn item scared                 -> actor.memes["sadness"] += 1
    parent suggests gear             -> actor.memes["joy"] += 1  if gear works

ASP twin reasons about compatibility between activity, prize region, and gear.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Callable, Optional

# Make the shared result containers importable
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0

MESS_KINDS = {"loud", "bright", "rushed"}

REGIONS = {"head", "hands", "feet"}


# ---------------------------------------------------------------------------
# Entities
# ---------------------------------------------------------------------------
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
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

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


# ---------------------------------------------------------------------------
# Parameters
# ---------------------------------------------------------------------------
@dataclass
class Setting:
    place: str = "the backyard"
    indoor: bool = False
    time: str = "night"
    affords: set[str] = field(default_factory=set)


@dataclass
class Activity:
    id: str
    verb: str             # "call to the owl"
    gerund: str           # "calling to the owl"
    rush: str             # "shout loudly"
    mess: str             # one of MESS_KINDS
    soil: str             # "too loud for the shy owl"
    zone: set[str]        # {"head"} because the voice comes from the head
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


# ---------------------------------------------------------------------------
# World
# ---------------------------------------------------------------------------
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
        chunks = [" ".join(p) for p in self.paragraphs if p]
        return "\n\n".join(chunks)

    def copy(self) -> "World":
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.zone = set(self.zone)
        clone.paragraphs = [[]]
        return clone


# ---------------------------------------------------------------------------
# Causal rules
# ---------------------------------------------------------------------------
@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_scare_owl(world: World) -> list[str]:
    """If the actor is loud and the worn prize is uncovered, the prize gets 'scared'."""
    out: list[str] = []
    for actor in world.characters():
        if actor.meters["loud"] < THRESHOLD:
            continue
        for item in world.worn_items(actor):
            if item.protective or item.region not in world.zone:
                continue
            if world.covered(actor, item.region):
                continue
            sig = ("scare", item.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            item.meters["scared"] += 1
            out.append(
                f"{actor.pronoun('possessive').capitalize()} {item.label} "
                f"felt too loud and the owl stayed hidden."
            )
    return out


def _r_sadness(world: World) -> list[str]:
    """If the prize is scared, the child becomes sad."""
    out: list[str] = []
    for item in list(world.entities.values()):
        if item.meters["scared"] < THRESHOLD:
            continue
        sig = ("sad", item.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        owner = world.get(item.owner) if item.owner else None
        if owner:
            owner.memes["sadness"] += 1
            out.append(f"That made {owner.id} feel sad.")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="scare_owl", tag="physical", apply=_r_scare_owl),
    Rule(name="sadness", tag="emotional", apply=_r_sadness),
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


# ---------------------------------------------------------------------------
# Reasonableness helpers
# ---------------------------------------------------------------------------
def prize_at_risk(activity: Activity, prize: Prize) -> bool:
    return prize.region in activity.zone


def select_gear(activity: Activity, prize: Prize) -> Optional[Gear]:
    for gear in GEAR:
        if activity.mess in gear.guards and prize.region in gear.covers:
            return gear
    return None


# ---------------------------------------------------------------------------
# Prediction
# ---------------------------------------------------------------------------
def predict_mess(world: World, actor: Entity, activity: Activity, prize_id: str) -> dict:
    sim = world.copy()
    _do_activity(sim, sim.get(actor.id), activity, narrate=False)
    prize = sim.entities.get(prize_id)
    return {
        "scared": bool(prize and prize.meters["scared"] >= THRESHOLD),
        "sadness": sum(e.memes["sadness"] for e in sim.characters()),
    }


# ---------------------------------------------------------------------------
# Story prose helpers (sound effects, dialogue, bedtime style)
# ---------------------------------------------------------------------------
def introduce(world: World, hero: Entity) -> None:
    world.say(
        f"On a quiet night, {hero.id} sat by the window. "
        f"Beyond the glass, the stars twinkled and the moon smiled softly."
    )


def loves_activity(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["hope"] += 1
    world.say(
        f"{hero.pronoun().capitalize()} loved {activity.gerund} at bedtime. "
        f"\"Whoo… whoo…\" {hero.pronoun()} would whisper, hoping the owl would answer."
    )


def buys(world: World, parent: Entity, hero: Entity, prize: Prize) -> None:
    world.say(
        f"That week, {hero.id}'s {parent.label_word} had given "
        f"{hero.pronoun('object')} {prize.phrase}. "
        f"\"It will keep you brave,\" {hero.pronoun('possessive')} {parent.label_word} said."
    )


def loves_prize(world: World, hero: Entity, prize: Entity) -> None:
    hero.memes["attachment"] += 1
    prize.worn_by = hero.id
    world.say(
        f"{hero.id} hugged {prize.it()} close and wore {prize.it()} every evening."
    )


def arrive(world: World, hero: Entity, parent: Entity) -> None:
    world.say(
        f"That night, {hero.id} and {hero.pronoun('possessive')} "
        f"{parent.label_word} stepped into {world.setting.place}."
    )


def wants(world: World, hero: Entity, parent: Entity, activity: Activity) -> None:
    hero.memes["desire"] += 1
    world.say(
        f"{hero.id} wanted to {activity.verb} right by the old oak tree. "
        f"\"Wait,\" said {hero.pronoun('possessive')} {parent.label_word}. \"Listen first.\""
    )


def warn(world: World, parent: Entity, hero: Entity, activity: Activity, prize: Entity) -> bool:
    pred = predict_mess(world, hero, activity, prize.id)
    if not pred["scared"]:
        return False
    world.facts["predicted_soil"] = activity.soil
    world.facts["predicted_sadness"] = pred["sadness"]
    clause = f"If you shout, your {prize.label} will feel too loud and the owl will hide."
    if pred["sadness"] >= THRESHOLD:
        clause += " You would be sad then."
    world.say(f'"{clause}" {hero.pronoun("possessive")} {parent.label_word} said gently.')
    return True


def defies(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["defiance"] += 1
    world.say(
        f"But {hero.id} was too excited. {hero.pronoun().capitalize()} took a deep breath and "
        f"{activity.rush} — "
    )
    world.say("\"WHOO-hoo!\"")   # sound effect


def grab_hand(world: World, parent: Entity, hero: Entity) -> None:
    hero.memes["grabbed_by"] += 1
    world.say(
        f" — but {hero.pronoun('possessive')} {parent.label_word} softly took "
        f"{hero.pronoun('possessive')} hand. \"Shhh, little one. Let me show you another way.\""
    )


def pout(world: World, hero: Entity) -> None:
    if hero.memes["sadness"] >= THRESHOLD:
        world.say(
            f"{hero.id} hung {hero.pronoun('possessive')} head. \"But I want to be friends with the owl,\" "
            f"{hero.pronoun()} whispered."
        )


def compromise(world: World, parent: Entity, hero: Entity, activity: Activity,
               prize: Entity) -> Optional[Gear]:
    gear_def = select_gear(activity, prize)
    if gear_def is None:
        return None
    gear = world.add(Entity(
        id=gear_def.id, type="gear", label=gear_def.label,
        owner=hero.id, caretaker=parent.id, protective=True,
        covers=set(gear_def.covers), plural=gear_def.plural,
    ))
    gear.worn_by = hero.id
    if predict_mess(world, hero, activity, prize.id)["scared"]:
        gear.worn_by = None
        del world.entities[gear.id]
        return None
    world.say(
        f'{hero.pronoun("possessive").capitalize()} {parent.label_word} smiled and reached '
        f'for {gear_def.label}. "Here, try this. {gear_def.prep}."'
    )
    return gear_def


def accept(world: World, parent: Entity, hero: Entity, activity: Activity,
           prize: Entity, gear_def: Gear) -> None:
    hero.memes["joy"] += 1
    hero.memes["sadness"] = 0.0
    world.say(
        f"{hero.id}'s eyes lit up. \"Okay!\" {hero.pronoun()} put on {gear_def.label} "
        f"and took {hero.pronoun('possessive')} {parent.label_word}'s hand."
    )
    world.say(
        f"They {gear_def.tail}. Now {hero.id} whispered softly: \"Hoo… hoo…\""
    )
    world.say(
        "And then — from the dark leaves — came a tiny answer: \"Hoo-hoo!\""
    )
    world.say(
        f"{hero.id} hugged {hero.pronoun('possessive')} {parent.label_word}. "
        "\"I made a friend!\" And that night, they walked home under the stars, the owl's song still hanging in the air."
    )


def tell(setting: Setting, activity: Activity, prize_cfg: Prize,
         hero_name: str = "Lily", hero_type: str = "girl",
         hero_traits: Optional[list[str]] = None, parent_type: str = "mother") -> World:
    world = World(setting)

    hero = world.add(Entity(
        id=hero_name, kind="character", type=hero_type,
        traits=["little"] + (hero_traits or ["brave", "curious"]),
    ))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label="the parent"))
    prize = world.add(Entity(
        id="prize", type=prize_cfg.type, label=prize_cfg.label,
        phrase=prize_cfg.phrase, owner=hero.id, caretaker=parent.id,
        region=prize_cfg.region, plural=prize_cfg.plural,
    ))

    # Act 1 – Nighttime introduction
    introduce(world, hero)
    loves_activity(world, hero, activity)
    buys(world, parent, hero, prize_cfg)
    loves_prize(world, hero, prize)

    # Act 2 – Tension
    world.para()
    arrive(world, hero, parent)
    wants(world, hero, parent, activity)
    warn(world, parent, hero, activity, prize)
    defies(world, hero, activity)
    grab_hand(world, parent, hero)
    propagate(world, narrate=False)

    # Act 3 – Resolution
    world.para()
    pout(world, hero)
    gear_def = compromise(world, parent, hero, activity, prize)
    if gear_def:
        accept(world, parent, hero, activity, prize, gear_def)

    world.facts.update(hero=hero, parent=parent, prize=prize, prize_cfg=prize_cfg,
                       activity=activity, setting=setting, gear=gear_def,
                       conflict=False, resolved=gear_def is not None)
    return world


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "backyard": Setting(place="the backyard", time="night", affords={"befriend_owl"}),
    "porch":   Setting(place="the porch",    time="night", affords={"befriend_owl"}),
    "garden":  Setting(place="the garden",   time="night", affords={"befriend_owl"}),
}

ACTIVITIES = {
    "befriend_owl": Activity(
        id="befriend_owl",
        verb="call to the owl",
        gerund="calling to the owl",
        rush="shout as loud as she could",
        mess="loud",
        soil="too loud for the shy owl",
        zone={"head"},
        keyword="owl",
        tags={"owl", "night", "friend"},
    ),
}

PRIZES = {
    "nightcap": Prize(
        label="nightcap",
        phrase="a soft red nightcap",
        type="nightcap",
        region="head",
    ),
    "scarf": Prize(
        label="scarf",
        phrase="a striped scarf",
        type="scarf",
        region="head",
    ),
}

GEAR = [
    Gear(
        id="whisper_scarf",
        label="a whisper scarf",
        covers={"head"},
        guards={"loud"},
        prep="wrap this scarf around your neck",
        tail="wrapped the whisper scarf around her neck",
    ),
]

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ella", "Lucy", "Rose"]
BOY_NAMES = ["Ben", "Max", "Sam", "Leo", "Jack", "Finn"]
TRAITS = ["brave", "curious", "gentle", "eager", "sweet"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            act = ACTIVITIES[act_id]
            for prize_id, prize in PRIZES.items():
                if prize_at_risk(act, prize) and select_gear(act, prize):
                    combos.append((place, act_id, prize_id))
    return combos


# ---------------------------------------------------------------------------
# Params dataclass
# ---------------------------------------------------------------------------
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


# ---------------------------------------------------------------------------
# Q&A generation
# ---------------------------------------------------------------------------
KNOWLEDGE = {
    "owl":     [("What sound does an owl make?",
                 "Owls often say 'hoo' or 'whoo'. It is their way of calling to each other at night.")],
    "night":   [("Why do some animals come out at night?",
                 "Many animals like owls, bats, and fireflies are nocturnal – they sleep during the day and are active when it is dark.")],
    "friend":  [("How can you be gentle when meeting a shy animal?",
                 "You can speak softly, move slowly, and offer something kind like a smile or a treat. That helps the animal feel safe.")],
}
KNOWLEDGE_ORDER = ["owl", "night", "friend"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    activity = f["activity"]
    prize_cfg = f["prize_cfg"]
    return [
        f'Write a short bedtime story about a little {hero.type} named {hero.id} who wants to befriend a shy owl at night.',
        f'Tell a gentle story with sound effects (like "Hoo!" and "Shh") and dialogue where a child and parent find a kind way to call the owl.',
        f'Create a story that ends happily with the child making a new nighttime friend after learning to whisper instead of shout.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, parent, prize, act = f["hero"], f["parent"], f["prize"], f["activity"]
    qa: list[QAItem] = [
        QAItem(
            question=f"Who is the story about?",
            answer=f"It is about a little {hero.type} named {hero.id} and {hero.pronoun('possessive')} {parent.label_word}."
        ),
        QAItem(
            question=f"What did {hero.id} want to do at night?",
            answer=f"{hero.id} wanted to {act.verb} in {world.setting.place}."
        ),
        QAItem(
            question=f"Why did {hero.pronoun('possessive')} {parent.label_word} stop {hero.pronoun('object')} from shouting?",
            answer=f"Because the shout would scare the owl away, and {hero.pronoun('possessive')} {prize.label} would feel too loud."
        ),
    ]
    if f.get("resolved") and f.get("gear"):
        gear = f["gear"]
        qa.append(QAItem(
            question=f"How did {gear.label} help {hero.id} make friends with the owl?",
            answer=f"The {gear.label} muffled the sound. With it, {hero.id} could whisper and the owl heard and answered."
        ))
        qa.append(QAItem(
            question=f"Did {hero.id} feel happy at the end?",
            answer=f"Yes, {hero.id} felt happy. The owl called back, and {hero.pronoun()} hugged {hero.pronoun('possessive')} {parent.label_word}."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = world.facts["activity"].tags
    out = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
            out.extend(QAItem(q=question, a=answer) for question, answer in KNOWLEDGE[tag])
    return out


# ---------------------------------------------------------------------------
# CLI, trace, ASP
# ---------------------------------------------------------------------------
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


CURATED = [
    StoryParams(
        place="backyard", activity="befriend_owl", prize="nightcap",
        name="Lily", gender="girl", parent="mother", trait="brave",
    ),
    StoryParams(
        place="porch", activity="befriend_owl", prize="scarf",
        name="Ben", gender="boy", parent="father", trait="curious",
    ),
]


def explain_rejection(activity: Activity, prize: Prize) -> str:
    noun = prize.label if prize.plural else f"a {prize.label}"
    if not prize_at_risk(activity, prize):
        return (f"(No story: calling to the owl affects {sorted(activity.zone)}, "
                f"but {noun} is worn on the {prize.region}. It wouldn't get scared, so no tension. "
                f"Try a prize worn on {sorted(activity.zone)}.)")
    return (f"(No story: nothing in the gear catalog protects {noun} "
            f"({prize.region}) from being too loud. The compromise must cover that region.)")


def explain_gender(prize_id: str, gender: str) -> str:
    ok = " / ".join(sorted(PRIZES[prize_id].genders))
    return f"(No story: a {PRIZES[prize_id].label} isn't typical for a {gender}; try --gender {ok}.)"


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
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
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


# ---------------------------------------------------------------------------
# Standard interface
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world: a child, an owl, a whisper scarf. Bedtime style.")
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
    return StoryParams(place=place, activity=activity, prize=prize_id,
                        name=name, gender=gender, parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], ACTIVITIES[params.activity],
                 PRIZES[params.prize], params.name, params.gender,
                 [params.trait], params.parent)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False,
         header: str = "") -> None:
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
        print(f"{len(triples)} compatible (place, activity, prize) combos "
              f"({len(stories)} with gender):\n")
        for place, act, prize in triples:
            genders = sorted(g for (pl, a, pr, g) in stories
                             if (pl, a, pr) == (place, act, prize))
            print(f"  {place:9} {act:14} {prize:8}  [{', '.join(genders)}]")
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
