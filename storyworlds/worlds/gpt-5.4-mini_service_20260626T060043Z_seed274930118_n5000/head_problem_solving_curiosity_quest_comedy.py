#!/usr/bin/env python3
"""
storyworlds/worlds/head_problem_solving_curiosity_quest_comedy.py
==================================================================

A small story world about a curious child, a goofy quest, and a problem that
needs a sensible fix. The core premise is comedic: a hat gets stuck on the head
of a garden statue, and the child and parent must solve the puzzle without
making the statue look even sillier.
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
REGIONS = {"head", "hand", "feet", "torso"}
MESS_KINDS = {"sticky", "smudged", "wobbly"}


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
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_sticky(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters["sticky"] < THRESHOLD:
            continue
        for item in world.worn_items(actor):
            if item.protective or item.region not in world.zone:
                continue
            if world.covered(actor, item.region):
                continue
            sig = ("sticky", item.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            item.meters["sticky"] += 1
            item.meters["smudged"] += 1
            out.append(f"{actor.pronoun('possessive').capitalize()} {item.label} got sticky and smudged.")
    return out


def _r_worry(world: World) -> list[str]:
    out: list[str] = []
    for item in world.entities.values():
        if item.meters["smudged"] < THRESHOLD or not item.caretaker:
            continue
        sig = ("worry", item.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        carer = world.get(item.caretaker)
        carer.memes["worry"] += 1
        out.append(f"That gave {carer.label} a little worry.")
    return out


def _r_conflict(world: World) -> list[str]:
    for actor in world.characters():
        if actor.memes["blocked"] < THRESHOLD or actor.memes["curiosity"] < THRESHOLD:
            continue
        sig = ("conflict", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["frustration"] += 1
        return ["__conflict__"]
    return []


CAUSAL_RULES = [
    Rule("sticky", "physical", _r_sticky),
    Rule("worry", "social", _r_worry),
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
    return {"soiled": bool(prize and prize.meters["smudged"] >= THRESHOLD)}


def activity_delight(activity: Activity) -> str:
    return {
        "search": "every new clue felt like a tiny joke the world was telling",
        "climb": "being up high made the whole garden look like a puzzle",
        "reach": "stretching for the answer felt brave and a little funny",
        "tug": "the careful tug felt like trying to wake up a sleepy noodle",
    }.get(activity.id, "it made the day feel like a puzzle")


def setting_detail(setting: Setting, activity: Activity) -> str:
    if setting.indoor:
        return f"The {setting.place} was quiet, except for one very loud clue."
    if activity.id == "search":
        return f"The {setting.place} was full of hiding spots, and every bush looked suspicious."
    return f"{setting.place.capitalize()} looked ready for a small and silly rescue."


def _do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    if activity.id not in world.setting.affords:
        return
    world.zone = set(activity.zone)
    actor.memes["curiosity"] += 1
    actor.meters[activity.mess] += 1
    propagate(world, narrate=narrate)


def introduce(world: World, hero: Entity) -> None:
    trait = next((t for t in hero.traits if t != "little"), "")
    world.say(f"{hero.id} was a little {trait} {hero.type} who liked asking why.")
    world.say(f"{hero.id} thought every strange thing in the world ought to have an answer.")


def loves_quest(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["quest"] += 1
    world.say(
        f"{hero.pronoun().capitalize()} loved {activity.gerund}, because a good question "
        f"always felt like the start of a quest."
    )
    world.say(activity_delight(activity) + ".")


def finds_problem(world: World, hero: Entity, helper: Entity, problem: Entity) -> None:
    world.say(
        f"One day, {hero.id} and {hero.pronoun('possessive')} {helper.label_word} found "
        f"a very funny problem: {problem.phrase}."
    )
    world.say(f"It sat there on the {problem.region} like it had paid rent.")


def wants_help(world: World, hero: Entity, helper: Entity, activity: Activity) -> None:
    hero.memes["desire"] += 1
    world.say(
        f"{hero.id} wanted to help right away, but {hero.pronoun('possessive')} "
        f"{helper.label_word} said, \"Let's make a plan first.\""
    )
    world.say(f"So they began a tiny quest across {world.setting.place}.")


def warn(world: World, helper: Entity, hero: Entity, activity: Activity, problem: Entity) -> bool:
    pred = predict_mess(world, hero, activity, problem.id)
    if not pred["soiled"]:
        return False
    world.say(
        f"\"If you {activity.verb}, the {problem.label} might get even worse,\" "
        f"{helper.pronoun('possessive')} {helper.label_word} said."
    )
    return True


def search_clue(world: World, hero: Entity, activity: Activity, clue: Entity) -> None:
    hero.memes["curiosity"] += 1
    world.say(
        f"{hero.id} searched for clues and found {clue.phrase}, which was not the answer "
        f"but was still impressively weird."
    )


def wrong_try(world: World, hero: Entity, helper: Entity, activity: Activity) -> None:
    hero.memes["blocked"] += 1
    world.say(f"{hero.id} tried a clever idea, then had to stop and think again.")
    world.say(f"{hero.pronoun().capitalize()} asked, \"What if we try the opposite of the loud idea?\"")


def solve(world: World, helper: Entity, hero: Entity, activity: Activity, problem: Entity, gear_def: Gear) -> None:
    hero.memes["frustration"] = 0.0
    hero.memes["joy"] += 1
    world.say(
        f"{helper.id} picked up {gear_def.label}, and {hero.id} noticed a better trick: "
        f"if they used it gently, the problem would loosen without a drama."
    )
    world.say(
        f"They did exactly that. Soon the {problem.label} was free, {hero.id} was grinning, "
        f"and the quest had a splendidly silly ending."
    )


def tell(setting: Setting, activity: Activity, prize_cfg: Prize,
         hero_name: str = "Mina", hero_type: str = "girl",
         hero_traits: Optional[list[str]] = None, helper_type: str = "father") -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type,
                            traits=["little"] + (hero_traits or ["curious", "cheerful"])))
    helper = world.add(Entity(id="Helper", kind="character", type=helper_type, label="the parent"))
    problem = world.add(Entity(id="Problem", type=prize_cfg.type, label=prize_cfg.label,
                               phrase=prize_cfg.phrase, owner=hero.id, caretaker=helper.id,
                               region=prize_cfg.region, plural=prize_cfg.plural))
    clue = world.add(Entity(id="Clue", type="thing", label="clue", phrase="a crumbly trail of breadcrumbs"))
    tool = world.add(Entity(id="Tool", type="thing", label="tool", phrase="a long spoon"))
    world.facts["hero"] = hero
    world.facts["helper"] = helper
    world.facts["problem"] = problem
    world.facts["activity"] = activity
    world.facts["setting"] = setting
    world.facts["clue"] = clue
    world.facts["tool"] = tool

    introduce(world, hero)
    loves_quest(world, hero, activity)
    finds_problem(world, hero, helper, problem)

    world.para()
    wants_help(world, hero, helper, activity)
    warn(world, helper, hero, activity, problem)
    search_clue(world, hero, activity, clue)
    wrong_try(world, hero, helper, activity)

    world.para()
    gear_def = select_gear(activity, problem)
    if gear_def is None:
        raise StoryError("No reasonable rescue tool fits this problem.")
    solve(world, helper, hero, activity, problem, gear_def)

    world.facts["gear"] = gear_def
    world.facts["resolved"] = True
    return world


SETTINGS = {
    "garden": Setting(place="the garden", indoor=False, affords={"search", "climb", "reach", "tug"}),
    "yard": Setting(place="the yard", indoor=False, affords={"search", "climb", "reach", "tug"}),
    "shed": Setting(place="the shed", indoor=True, affords={"search", "reach"}),
    "workshop": Setting(place="the workshop", indoor=True, affords={"search", "tug"}),
}

ACTIVITIES = {
    "search": Activity(
        id="search",
        verb="search for clues",
        gerund="searching for clues",
        rush="dash around searching",
        mess="wobbly",
        soil="more wobbly",
        zone={"head"},
        weather="",
        keyword="head",
        tags={"head", "quest"},
    ),
    "climb": Activity(
        id="climb",
        verb="climb up",
        gerund="climbing up",
        rush="scramble higher",
        mess="wobbly",
        soil="more wobbly",
        zone={"head"},
        weather="",
        keyword="head",
        tags={"head", "quest"},
    ),
    "reach": Activity(
        id="reach",
        verb="reach for the answer",
        gerund="reaching for the answer",
        rush="stretch up fast",
        mess="smudged",
        soil="smudged",
        zone={"head"},
        weather="",
        keyword="head",
        tags={"head", "problem"},
    ),
    "tug": Activity(
        id="tug",
        verb="tug gently",
        gerund="tugging gently",
        rush="pull too hard",
        mess="sticky",
        soil="sticky",
        zone={"head"},
        weather="",
        keyword="head",
        tags={"head", "problem"},
    ),
}

GEAR = [
    Gear(
        id="ladder",
        label="a little ladder",
        covers={"head"},
        guards={"wobbly"},
        prep="bring the little ladder",
        tail="used the little ladder",
    ),
    Gear(
        id="spoon",
        label="a long spoon",
        covers={"head"},
        guards={"sticky"},
        prep="find the long spoon",
        tail="used the long spoon",
    ),
    Gear(
        id="towel",
        label="a soft towel",
        covers={"head"},
        guards={"smudged"},
        prep="grab a soft towel",
        tail="used the soft towel",
    ),
]

PRIZES = {
    "hat": Prize(label="hat", phrase="a bright red hat", type="hat", region="head"),
    "bucket": Prize(label="bucket", phrase="a shiny bucket", type="bucket", region="head"),
    "helmet": Prize(label="helmet", phrase="a toy helmet", type="helmet", region="head"),
}

GIRL_NAMES = ["Mina", "Lena", "Pia", "Tess", "Ruby", "Nina"]
BOY_NAMES = ["Owen", "Jude", "Milo", "Ben", "Theo", "Finn"]
TRAITS = ["curious", "clever", "cheerful", "bold", "bouncy", "spry"]


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
    "head": [("What is the head for?", "The head holds the brain and the senses, like your eyes, ears, and mouth.")],
    "quest": [("What is a quest?", "A quest is a journey to find, fix, or reach something important.")],
    "problem": [("What is a problem?", "A problem is something that is hard or wrong and needs a solution.")],
    "ladder": [("What is a ladder used for?", "A ladder helps people reach higher places safely.")],
    "spoon": [("What is a spoon for?", "A spoon is usually for eating, but a long spoon can also help reach things.")],
    "towel": [("What does a towel do?", "A towel soaks up water and can help keep things dry or clean.")],
}
KNOWLEDGE_ORDER = ["head", "quest", "problem", "ladder", "spoon", "towel"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, helper, act, problem = f["hero"], f["helper"], f["activity"], f["problem"]
    return [
        f'Write a funny short story for a young child about a curious {hero.type} named {hero.id} who goes on a quest to solve a problem with {problem.phrase}.',
        f"Tell a comedy where {hero.id} and {helper.label_word} must {act.verb} to get {problem.label} off the head without making a bigger mess.",
        f'Write a simple story that includes the word "head" and ends with a silly rescue and a happy laugh.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, helper, problem, act = f["hero"], f["helper"], f["problem"], f["activity"]
    qa = [
        QAItem(
            question=f"Who went on the quest in {world.setting.place}?",
            answer=f"{hero.id} and {helper.label_word} went together, because {hero.id} was curious and wanted to solve the problem.",
        ),
        QAItem(
            question=f"What problem made the story start?",
            answer=f"They found {problem.phrase}, which was stuck on the {problem.region} and looked very silly.",
        ),
        QAItem(
            question=f"Why did {hero.id} keep looking around so much?",
            answer=f"{hero.id} liked asking why and was looking for clues to solve the problem safely.",
        ),
        QAItem(
            question=f"What did {hero.id} want to do before the grown-up made a plan?",
            answer=f"{hero.id} wanted to {act.verb}, but that was not the safest first move, so they paused to think.",
        ),
    ]
    if f.get("resolved"):
        gear = f["gear"]
        qa.append(
            QAItem(
                question=f"How did {gear.label} help?",
                answer=f"They used {gear.label} gently, and that was the clever fix that freed the {problem.label}.",
            )
        )
        qa.append(
            QAItem(
                question=f"How did the story end?",
                answer=f"It ended with the {problem.label} free, {hero.id} smiling, and everyone laughing at how funny the rescue had been.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["activity"].tags)
    tags.add(world.facts["gear"].id)
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
    StoryParams(place="garden", activity="search", prize="hat", name="Mina", gender="girl", parent="father", trait="curious"),
    StoryParams(place="yard", activity="climb", prize="bucket", name="Owen", gender="boy", parent="mother", trait="clever"),
    StoryParams(place="shed", activity="reach", prize="helmet", name="Ruby", gender="girl", parent="father", trait="bouncy"),
]


def explain_rejection(activity: Activity, prize: Prize) -> str:
    if not prize_at_risk(activity, prize):
        return f"(No story: {activity.gerund} does not actually bother a {prize.label} on the head.)"
    return f"(No story: no suitable rescue tool is available for a {prize.label} in this setup.)"


def explain_gender(prize_id: str, gender: str) -> str:
    ok = " / ".join(sorted(PRIZES[prize_id].genders))
    return f"(No story: a {PRIZES[prize_id].label} isn't a typical {gender}'s item here; try --gender {ok}.)"


ASP_RULES = r"""
prize_at_risk(A, P) :- zones(A, R), wears_on(P, R).
rescues(G, A, P) :- tool(G), prize_at_risk(A, P), guards(G, M), mess_of(A, M), covers(G, R), wears_on(P, R).
has_fix(A, P) :- rescues(_, A, P).
valid(Place, A, P) :- affords(Place, A), prize_at_risk(A, P), has_fix(A, P).
valid_story(Place, A, P, Gender) :- valid(Place, A, P), fits_gender(P, Gender).
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
            lines.append(asp.fact("zones", aid, r))
    for pid, pr in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("wears_on", pid, pr.region))
        for g in sorted(pr.genders):
            lines.append(asp.fact("fits_gender", pid, g))
    for g in GEAR:
        lines.append(asp.fact("tool", g.id))
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
    ap = argparse.ArgumentParser(description="A curious comedy quest about fixing a silly head problem.")
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
    place, activity, prize_id = rng.choice(sorted(combos))
    prize = PRIZES[prize_id]
    gender = args.gender or rng.choice(sorted(prize.genders))
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, activity=activity, prize=prize_id, name=name, gender=gender, parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], ACTIVITIES[params.activity], PRIZES[params.prize],
                 params.name, params.gender, [params.trait, "bright"], params.parent)
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
            print(f"  {place:9} {act:8} {prize:8}  [{', '.join(genders)}]")
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
