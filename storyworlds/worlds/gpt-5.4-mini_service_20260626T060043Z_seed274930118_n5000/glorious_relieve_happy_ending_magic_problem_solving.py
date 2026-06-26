#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/glorious_relieve_happy_ending_magic_problem_solving.py
====================================================================================================

A heartwarming story world about a child, a magical helper, and a problem that
can be solved gently and well.

Seed impression:
---
A child faces a small but important disappointment: something lovely is broken
right before a happy moment. A magical helper, or a simple magical object, helps
the child think clearly, repair the problem, and end the day in a warm, shining
way.

World idea:
---
In a cozy home and courtyard, a child wants a glorious lantern to glow for an
evening gathering. The lantern is torn and dim, which makes the child worry.
A tiny magic helper appears, but the fix still requires thoughtful problem
solving: the child, caregiver, and helper find the right tape, the right knot,
and the right charm. The lantern becomes bright again, the worry eases, and the
night ends with a happy ending image.

Narrative instruments:
---
- glorious, relieve
- Happy Ending
- Magic
- Problem Solving

Style:
---
Heartwarming, concrete, child-facing, and gently authored.
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
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "grandmother", "grandma"}
        male = {"boy", "father", "dad", "man", "grandfather", "grandpa"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad", "grandmother": "grandma", "grandfather": "grandpa"}.get(self.type, self.type)


@dataclass
class Setting:
    place: str = "the courtyard"
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
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


MESS_KINDS = {"torn", "dim", "dusty", "smudged"}


def _r_damage(world: World) -> list[str]:
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
                sig = ("damage", item.id, mess)
                if sig in world.fired:
                    continue
                world.fired.add(sig)
                item.meters[mess] += 1
                item.meters["broken"] += 1
                out.append(f"{actor.pronoun('possessive').capitalize()} {item.label} got {mess} and worse.")
    return out


def _r_relieve(world: World) -> list[str]:
    out: list[str] = []
    for ent in world.entities.values():
        if ent.memes["worry"] < THRESHOLD:
            continue
        if ent.memes["relieved"] >= THRESHOLD:
            continue
        if ent.meters["fixed"] < THRESHOLD:
            continue
        sig = ("relieve", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        ent.memes["relieved"] += 1
        ent.memes["worry"] = max(0.0, ent.memes["worry"] - 1.0)
        out.append(f"The worry eased from {ent.id}.")
    return out


CAUSAL_RULES = [
    Rule("damage", "physical", _r_damage),
    Rule("relieve", "social", _r_relieve),
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


def predict_damage(world: World, actor: Entity, activity: Activity, prize_id: str) -> dict:
    sim = world.copy()
    _do_activity(sim, sim.get(actor.id), activity, narrate=False)
    prize = sim.entities.get(prize_id)
    return {
        "broken": bool(prize and prize.meters["broken"] >= THRESHOLD),
        "worry": sum(e.memes["worry"] for e in sim.characters()),
    }


def setting_detail(setting: Setting, activity: Activity) -> str:
    if setting.indoor:
        return f"The room was cozy, and a small table waited under the lamp."
    if activity.weather == "night":
        return f"The evening air was soft, and {setting.place} glowed under the first lights."
    return f"{setting.place.capitalize()} looked ready for a gentle kind of magic."


def introduce(world: World, hero: Entity) -> None:
    trait = next((t for t in hero.traits if t != "little"), "")
    desc = f"little {trait} {hero.type}".strip()
    world.say(f"{hero.id} was a {desc} who liked beautiful things that shone softly.")


def loves_activity(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["love_play"] += 1
    world.say(f"{hero.pronoun().capitalize()} loved {activity.gerund}, especially when the night felt calm and kind.")


def has_prize(world: World, hero: Entity, prize: Entity) -> None:
    prize.worn_by = hero.id
    hero.memes["love"] += 1
    world.say(f"{hero.id} treasured {hero.pronoun('possessive')} {prize.label} and held {prize.it()} carefully.")


def arrives(world: World, hero: Entity, helper: Entity, activity: Activity) -> None:
    day = "One evening, "
    go = "went to"
    world.say(f"{day}{hero.id} and {helper.id} {go} {world.setting.place}.")
    world.say(setting_detail(world.setting, activity))


def wants(world: World, hero: Entity, helper: Entity, activity: Activity, prize: Entity) -> None:
    hero.memes["desire"] += 1
    world.say(f"{hero.id} wanted everything to feel glorious, but the {prize.label} had a problem.")
    world.say(f"{hero.pronoun().capitalize()} hoped to {activity.verb} before the gathering began.")


def warn(world: World, helper: Entity, hero: Entity, activity: Activity, prize: Entity) -> bool:
    pred = predict_damage(world, hero, activity, prize.id)
    if not pred["broken"]:
        return False
    helper.memes["care"] += 1
    hero.memes["worry"] += 1
    world.facts["predicted_worry"] = pred["worry"]
    world.say(f'"If we rush, your {prize.label} will get {activity.soil}," {helper.id} said softly.')
    world.say(f'"But we can solve it together," {helper.id} added.')
    return True


def confuse(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["worry"] += 1
    world.say(f"{hero.id} frowned and looked at the broken part, unsure what to do next.")


def magic_help(world: World, helper: Entity, hero: Entity, prize: Entity) -> None:
    helper.memes["magic"] += 1
    hero.memes["hope"] += 1
    world.say(f"Then {helper.id} lifted a hand, and a tiny magic spark floated down like a star.")
    world.say(f"The spark did not fix everything by itself; it made the next step clear.")


def problem_solving(world: World, hero: Entity, helper: Entity, prize: Entity, gear_def: Gear) -> Optional[Gear]:
    gear = world.add(Entity(
        id=gear_def.id,
        type="gear",
        label=gear_def.label,
        owner=hero.id,
        caretaker=helper.id,
        protective=True,
        covers=set(gear_def.covers),
        plural=gear_def.plural,
    ))
    gear.worn_by = hero.id
    world.say(f"{hero.id} found {gear_def.label} and used {gear_def.prep}.")
    return gear_def


def repair(world: World, hero: Entity, helper: Entity, activity: Activity, prize: Entity, gear_def: Gear) -> None:
    hero.memes["joy"] += 1
    hero.memes["worry"] = 0.0
    prize.meters["fixed"] += 1
    prize.meters["broken"] = 0.0
    world.say(
        f"Together they straightened the paper, smoothed the edges, and tied the last knot."
    )
    world.say(
        f"The little magic spark settled into the {prize.label}, and soon it was bright again."
    )
    world.say(
        f"{hero.id} smiled so wide that even the night seemed to smile back."
    )
    world.say(
        f"They {gear_def.tail}, and the {prize.label} glowed {activity.keyword} and glorious."
    )
    world.say(
        f"By the end, the problem was gone, the worry had been relieved, and the night felt full of happy ending magic."
    )


def tell(setting: Setting, activity: Activity, prize_cfg: Prize, hero_name: str = "Mina",
         hero_type: str = "girl", hero_traits: Optional[list[str]] = None,
         helper_type: str = "grandmother") -> World:
    world = World(setting)
    world.weather = activity.weather

    hero = world.add(Entity(
        id=hero_name, kind="character", type=hero_type,
        traits=["little"] + (hero_traits or ["gentle", "bright"]),
    ))
    helper = world.add(Entity(
        id="Helper", kind="character", type=helper_type, label="Grandma"
    ))
    prize = world.add(Entity(
        id="lantern", type=prize_cfg.type, label=prize_cfg.label,
        phrase=prize_cfg.phrase, owner=hero.id, caretaker=helper.id,
        region=prize_cfg.region, plural=prize_cfg.plural,
    ))

    introduce(world, hero)
    loves_activity(world, hero, activity)
    has_prize(world, hero, prize)

    world.para()
    arrives(world, hero, helper, activity)
    wants(world, hero, helper, activity, prize)
    warn(world, helper, hero, activity, prize)
    confuse(world, hero, activity)
    magic_help(world, helper, hero, prize)

    world.para()
    gear_def = problem_solving(world, hero, helper, prize, GEAR[0])
    if gear_def:
        repair(world, hero, helper, activity, prize, gear_def)

    world.facts.update(
        hero=hero,
        helper=helper,
        prize=prize,
        prize_cfg=prize_cfg,
        activity=activity,
        setting=setting,
        gear=gear_def,
        resolved=True,
    )
    return world


SETTINGS = {
    "courtyard": Setting(place="the courtyard", indoor=False, affords={"lantern"}),
    "attic": Setting(place="the attic", indoor=True, affords={"lantern"}),
    "porch": Setting(place="the porch", indoor=False, affords={"lantern"}),
}

ACTIVITIES = {
    "lantern": Activity(
        id="lantern",
        verb="light the lantern",
        gerund="lighting lanterns",
        rush="carry the lantern out quickly",
        mess="torn",
        soil="torn and dim",
        zone={"torso"},
        weather="night",
        keyword="glorious",
        tags={"magic", "glorious", "problem_solving"},
    ),
}

PRIZES = {
    "lantern": Prize(
        label="lantern",
        phrase="a glorious paper lantern",
        type="lantern",
        region="torso",
    ),
}

GEAR = [
    Gear(
        id="tape",
        label="a roll of silver tape",
        covers={"torso"},
        guards={"torn", "dim"},
        prep="carefully tape the tear and hold the edges together",
        tail="walked back inside with the lantern held high",
    ),
]

GIRL_NAMES = ["Mina", "Lena", "Ivy", "Nora", "Lila", "Etta"]
BOY_NAMES = ["Finn", "Owen", "Theo", "Ben", "Milo", "Eli"]
TRAITS = ["gentle", "curious", "bright", "hopeful", "patient"]


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
    helper: str
    trait: str
    seed: Optional[int] = None


KNOWLEDGE = {
    "magic": [("What is magic in a story?",
               "Magic is a special kind of impossible help that can make something wonderful happen in a surprising way.")],
    "glorious": [("What does glorious mean?",
                 "Glorious means wonderfully bright, grand, or beautiful, like something that makes people smile just by looking at it.")],
    "tape": [("What can tape do?",
              "Tape can hold pieces together when something has a small tear or crack.")],
    "lantern": [("What is a lantern?",
                 "A lantern is a light in a case or frame that can shine in the dark.")],
    "problem_solving": [("What is problem solving?",
                         "Problem solving means thinking carefully about a trouble and choosing steps that help fix it.")],
    "relieve": [("What does it mean to relieve worry?",
                 "To relieve worry means to make someone feel less scared, tense, or upset.")],
}
KNOWLEDGE_ORDER = ["magic", "glorious", "tape", "lantern", "problem_solving", "relieve"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, helper, act, prize = f["hero"], f["helper"], f["activity"], f["prize_cfg"]
    return [
        f'Write a heartwarming story for a young child that includes the word "{act.keyword}" and ends happily.',
        f"Tell a gentle story about {hero.id} and {helper.id} solving a lantern problem with a little magic.",
        f"Write a story where a {prize.label} is broken at first, but careful problem solving makes it glow again.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, helper, prize, act = f["hero"], f["helper"], f["prize"], f["activity"]
    place = world.setting.place
    trait = next((t for t in hero.traits if t != "little"), hero.type)
    qa = [
        QAItem(
            question=f"What did {hero.id} want to do at {place}?",
            answer=f"{hero.id} wanted to {act.verb} with the {prize.label}, because {hero.id} hoped the night would look {act.keyword} and beautiful.",
        ),
        QAItem(
            question=f"Why did {helper.id} worry about the {prize.label}?",
            answer=f"{helper.id} worried because the {prize.label} was already broken, and if they hurried it could get {act.soil}.",
        ),
        QAItem(
            question=f"What helped {hero.id} and {helper.id} fix the problem?",
            answer=f"A tiny bit of magic helped them calm down and think clearly, and then they used careful problem solving with {GEAR[0].label}.",
        ),
        QAItem(
            question=f"How did {hero.id} feel at the end?",
            answer=f"{hero.id} felt happy and relieved, because the {prize.label} was bright again and the story ended in a warm happy ending.",
        ),
        QAItem(
            question=f"Who was the story about?",
            answer=f"It was about a little {trait} {hero.type} named {hero.id} and {helper.id}, who worked together kindly.",
        ),
    ]
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
        lines.append(f"  {e.id:8} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="courtyard", activity="lantern", prize="lantern", name="Mina", gender="girl", helper="grandmother", trait="gentle"),
    StoryParams(place="attic", activity="lantern", prize="lantern", name="Finn", gender="boy", helper="grandmother", trait="patient"),
    StoryParams(place="porch", activity="lantern", prize="lantern", name="Lena", gender="girl", helper="grandmother", trait="hopeful"),
]


def explain_rejection(activity: Activity, prize: Prize) -> str:
    noun = prize.label if prize.plural else f"a {prize.label}"
    verb = "sit" if prize.plural else "sits"
    if not prize_at_risk(activity, prize):
        return f"(No story: {activity.gerund} does not reach the place where {noun} {verb}.)"
    return f"(No story: no gear in this world can reasonably fix {noun} for that activity.)"


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
    for g in GEAR:
        lines.append(asp.fact("gear", g.id))
        for m in sorted(g.guards):
            lines.append(asp.fact("guards", g.id, m))
        for r in sorted(g.covers):
            lines.append(asp.fact("covers", g.id, r))
    return "\n".join(lines)


ASP_RULES = r"""
prize_at_risk(A, P) :- splashes(A, R), worn_on(P, R).
protects(G, A, P) :- gear(G), prize_at_risk(A, P), mess_of(A, M), guards(G, M), covers(G, R), worn_on(P, R).
has_fix(A, P) :- protects(_, A, P).
valid(Place, A, P) :- affords(Place, A), prize_at_risk(A, P), has_fix(A, P).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


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
    ap = argparse.ArgumentParser(
        description="Heartwarming story world: glorious magic problem solving that can relieve worry."
    )
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper", choices=["grandmother"])
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
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.activity is None or c[1] == args.activity)
              and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, activity, prize_id = rng.choice(sorted(combos))
    prize = PRIZES[prize_id]
    gender = args.gender or rng.choice(sorted(prize.genders))
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    helper = args.helper or "grandmother"
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, activity=activity, prize=prize_id, name=name, gender=gender, helper=helper, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], ACTIVITIES[params.activity], PRIZES[params.prize],
                 params.name, params.gender, [params.trait, "stubborn"], params.helper)
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
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, activity, prize) combos:\n")
        for place, act, prize in combos:
            print(f"  {place:10} {act:10} {prize:10}")
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
