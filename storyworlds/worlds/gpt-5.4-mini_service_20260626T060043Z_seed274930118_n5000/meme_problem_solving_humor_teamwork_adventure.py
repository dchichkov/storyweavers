#!/usr/bin/env python3
"""
storyworlds/worlds/meme_problem_solving_humor_teamwork_adventure.py
====================================================================

A small adventure storyworld about a kid, a tricky problem, a funny meme, and
a teamwork fix that actually works.

The seed image behind this world:
- a child on a little adventure trail
- a problem that blocks the way or threatens a prized item
- a teammate uses humor to keep everyone calm
- the group solves the problem together and ends the day a little braver

This script follows the Storyweavers contract:
- typed entities with physical meters and emotional memes
- a narrative driven by state changes, not a frozen paragraph
- an inline ASP twin for the reasonableness gate
- StorySample / QAItem / StoryError imports from storyworlds.results
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

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {}
        if not self.memes:
            self.memes = {}

    def m(self, key: str) -> float:
        return self.meters.get(key, 0.0)

    def e(self, key: str) -> float:
        return self.memes.get(key, 0.0)

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
    indoor: bool = False
    affords: set[str] = field(default_factory=set)


@dataclass
class Problem:
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
        import copy as _copy

        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.zone = set(self.zone)
        clone.weather = self.weather
        clone.paragraphs = [[]]
        return clone


PROBLEM_RULES = ["wet", "muddy", "tangled"]


def _r_soak(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        for mess in PROBLEM_RULES:
            if actor.m(mess) < THRESHOLD:
                continue
            for item in world.worn_items(actor):
                if item.protective or item.region not in world.zone:
                    continue
                if world.covered(actor, item.region):
                    continue
                sig = ("hit", actor.id, item.id, mess)
                if sig in world.fired:
                    continue
                world.fired.add(sig)
                item.meters[mess] = item.m(mess) + 1
                item.meters["spoiled"] = item.m("spoiled") + 1
                out.append(f"{actor.pronoun('possessive').capitalize()} {item.label} got {mess} and spoiled.")
    return out


def _r_teamwork(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.memes.get("teamwork", 0) < THRESHOLD:
            continue
        sig = ("teamwork", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["brave"] = actor.memes.get("brave", 0) + 1
        actor.memes["hope"] = actor.memes.get("hope", 0) + 1
        out.append(f"{actor.id} felt braver because the team stayed together.")
    return out


def _r_humor(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.memes.get("amused", 0) < THRESHOLD:
            continue
        sig = ("humor", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["worry"] = max(0.0, actor.memes.get("worry", 0) - 1)
        actor.memes["focus"] = actor.memes.get("focus", 0) + 1
        out.append(f"A funny meme made everyone laugh long enough to think straight.")
    return out


CAUSAL_RULES = [
    _r_soak,
    _r_teamwork,
    _r_humor,
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def prize_at_risk(problem: Problem, prize: Prize) -> bool:
    return prize.region in problem.zone


def select_gear(problem: Problem, prize: Prize) -> Optional[Gear]:
    for gear in GEAR:
        if problem.mess in gear.guards and prize.region in gear.covers:
            return gear
    return None


def predict_problem(world: World, actor: Entity, problem: Problem, prize_id: str) -> dict:
    sim = world.copy()
    _do_problem(sim, sim.get(actor.id), problem, narrate=False)
    prize = sim.entities.get(prize_id)
    return {
        "spoiled": bool(prize and prize.m("spoiled") >= THRESHOLD),
        "worry": sum(e.memes.get("worry", 0) for e in sim.characters()),
    }


def _do_problem(world: World, actor: Entity, problem: Problem, narrate: bool = True) -> None:
    if problem.id not in world.setting.affords:
        return
    world.zone = set(problem.zone)
    actor.meters[problem.mess] = actor.m(problem.mess) + 1
    actor.memes["worry"] = actor.memes.get("worry", 0) + 1
    propagate(world, narrate=narrate)


def introduce(world: World, hero: Entity) -> None:
    trait = next((t for t in hero.traits if t != "little"), "")
    desc = f"little {trait} {hero.type}".strip()
    world.say(f"{hero.id} was a {desc} who loved little adventures and big questions.")


def enjoys_adventure(world: World, hero: Entity, problem: Problem) -> None:
    hero.memes["curious"] = hero.memes.get("curious", 0) + 1
    world.say(
        f"{hero.pronoun().capitalize()} liked {problem.gerund}, because even a tricky trail could feel like a game."
    )


def arrives(world: World, hero: Entity, helper: Entity, setting: Setting, problem: Problem) -> None:
    day = "One bright morning, "
    go = "went to" if not setting.indoor else "were inside"
    world.say(
        f"{day}{hero.id} and {helper.label} {go} {setting.place}."
    )
    world.say(f"The path looked ready for {problem.gerund}, but it had one stubborn surprise.")


def wants(world: World, hero: Entity, helper: Entity, problem: Problem, prize: Entity) -> None:
    hero.memes["desire"] = hero.memes.get("desire", 0) + 1
    world.say(
        f"{hero.id} wanted to {problem.verb}, but {hero.pronoun('possessive')} {helper.label} worried about {hero.pronoun('possessive')} {prize.label}."
    )


def warn(world: World, helper: Entity, hero: Entity, problem: Problem, prize: Entity) -> bool:
    pred = predict_problem(world, hero, problem, prize.id)
    if not pred["spoiled"]:
        return False
    world.facts["predicted_soil"] = problem.soil
    world.facts["predicted_worry"] = pred["worry"]
    clause = f"You'll get your {prize.label} {problem.soil}"
    if pred["worry"] >= THRESHOLD:
        clause += ", and then we'll have a soggy mess"
    world.say(f'"{clause}," {helper.label} said. "Let us solve this before we rush ahead."')
    return True


def meme_joke(world: World, hero: Entity, helper: Entity) -> None:
    hero.memes["amused"] = hero.memes.get("amused", 0) + 1
    helper.memes["amused"] = helper.memes.get("amused", 0) + 1
    world.say(
        f"{hero.id} pulled out a silly meme from the backpack: a squirrel with a tiny cape and a very serious face."
    )
    world.say(
        f"That made {helper.label} snort a laugh, and the big worry shrank just enough for thinking."
    )


def rethink(world: World, hero: Entity, helper: Entity, problem: Problem) -> None:
    hero.memes["insight"] = hero.memes.get("insight", 0) + 1
    helper.memes["teamwork"] = helper.memes.get("teamwork", 0) + 1
    world.say(
        f"They stopped, looked at the trail, and decided to use their heads before their feet."
    )


def compromise(world: World, helper: Entity, hero: Entity, problem: Problem, prize: Entity) -> Optional[Gear]:
    gear_def = select_gear(problem, prize)
    if gear_def is None:
        return None
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
    if predict_problem(world, hero, problem, prize.id)["spoiled"]:
        gear.worn_by = None
        del world.entities[gear.id]
        return None
    world.say(
        f'{helper.label} smiled and said, "How about we {gear_def.prep} and try again together?"'
    )
    return gear_def


def accept(world: World, helper: Entity, hero: Entity, problem: Problem, prize: Entity, gear_def: Gear) -> None:
    hero.memes["joy"] = hero.memes.get("joy", 0) + 1
    hero.memes["teamwork"] = hero.memes.get("teamwork", 0) + 1
    hero.memes["worry"] = 0.0
    world.say(
        f"{hero.id} grinned, and the two of them followed the plan."
    )
    world.say(
        f"They {gear_def.tail}. Soon {hero.id} was {problem.gerund}, {prize.label} stayed safe, and the whole path felt like an adventure story with a happy ending."
    )


def tell(setting: Setting, problem: Problem, prize_cfg: Prize,
         hero_name: str = "Mina", hero_type: str = "girl",
         hero_traits: Optional[list[str]] = None, helper_type: str = "mother") -> World:
    world = World(setting)
    world.weather = "" if setting.indoor else problem.weather

    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type=hero_type,
        traits=["little"] + (hero_traits or ["curious", "brave"]),
    ))
    helper = world.add(Entity(id="Helper", kind="character", type=helper_type, label="her helper"))
    prize = world.add(Entity(
        id="prize",
        type=prize_cfg.type,
        label=prize_cfg.label,
        phrase=prize_cfg.phrase,
        owner=hero.id,
        caretaker=helper.id,
        region=prize_cfg.region,
        plural=prize_cfg.plural,
    ))

    introduce(world, hero)
    enjoys_adventure(world, hero, problem)
    world.say(f"{hero.id}'s backpack held {prize.phrase}, a snack, and one funny meme card.")
    world.para()
    arrives(world, hero, helper, setting, problem)
    wants(world, hero, helper, problem, prize)
    warn(world, helper, hero, problem, prize)
    meme_joke(world, hero, helper)
    rethink(world, hero, helper, problem)

    world.para()
    gear_def = compromise(world, helper, hero, problem, prize)
    if gear_def:
        accept(world, helper, hero, problem, prize, gear_def)

    world.facts.update(
        hero=hero,
        helper=helper,
        prize=prize,
        prize_cfg=prize_cfg,
        problem=problem,
        setting=setting,
        gear=gear_def,
        resolved=gear_def is not None,
    )
    return world


SETTINGS = {
    "creek": Setting(place="the creek path", indoor=False, affords={"cross_creek", "bridge_latch"}),
    "forest": Setting(place="the pine forest", indoor=False, affords={"lost_sign", "cross_creek"}),
    "hill": Setting(place="the windy hill", indoor=False, affords={"lost_sign", "bridge_latch"}),
    "cave": Setting(place="the cave mouth", indoor=False, affords={"dark_tunnel", "bridge_latch"}),
}

PROBLEMS = {
    "cross_creek": Problem(
        id="cross_creek",
        verb="cross the creek",
        gerund="crossing the creek",
        rush="rush over the slippery stones",
        mess="wet",
        soil="soaked and muddy",
        zone={"feet", "legs"},
        weather="rainy",
        keyword="creek",
        tags={"water", "adventure"},
    ),
    "bridge_latch": Problem(
        id="bridge_latch",
        verb="open the stuck bridge latch",
        gerund="working the bridge latch",
        rush="pull the latch hard",
        mess="tangled",
        soil="all tangled up",
        zone={"hands"},
        weather="",
        keyword="bridge",
        tags={"problem", "adventure"},
    ),
    "lost_sign": Problem(
        id="lost_sign",
        verb="find the missing trail sign",
        gerund="searching for the trail sign",
        rush="run down the wrong path",
        mess="muddy",
        soil="mud-splashed",
        zone={"feet", "legs"},
        weather="sunny",
        keyword="sign",
        tags={"search", "adventure"},
    ),
    "dark_tunnel": Problem(
        id="dark_tunnel",
        verb="walk through the dark tunnel",
        gerund="walking through the tunnel",
        rush="dash into the dark",
        mess="wet",
        soil="damp and splashed",
        zone={"torso", "feet"},
        weather="",
        keyword="tunnel",
        tags={"dark", "adventure"},
    ),
}

GEAR = [
    Gear(id="boots", label="rain boots", covers={"feet"}, guards={"wet", "muddy"}, prep="put on rain boots first", tail="walked back with the rain boots on", plural=True),
    Gear(id="rope", label="a long rope", covers={"hands"}, guards={"tangled"}, prep="hold a long rope while we work", tail="used the rope to steady the latch"),
    Gear(id="lamp", label="a little lamp", covers={"torso", "hands"}, guards={"wet"}, prep="carry a little lamp and stay together", tail="went on with the little lamp glowing"),
    Gear(id="gloves", label="work gloves", covers={"hands"}, guards={"tangled", "muddy"}, prep="put on work gloves first", tail="fixed the problem with their work gloves"),
]

PRIZES = {
    "map": Prize(label="map", phrase="a fold-out trail map", type="map", region="hands"),
    "snack": Prize(label="snack bag", phrase="a shiny snack bag", type="snack_bag", region="hands"),
    "journal": Prize(label="journal", phrase="a paper adventure journal", type="journal", region="hands"),
    "lantern": Prize(label="lantern", phrase="a tiny lantern", type="lantern", region="hands"),
}

NAMES = ["Mina", "Theo", "Lia", "Owen", "Nora", "Ari", "Zoe", "Ben"]
TRAITS = ["curious", "brave", "playful", "quick-thinking", "cheerful"]


@dataclass
class StoryParams:
    place: str
    problem: str
    prize: str
    name: str
    gender: str
    helper: str
    trait: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for pid in setting.affords:
            prob = PROBLEMS[pid]
            for prize_id, prize in PRIZES.items():
                if prize_at_risk(prob, prize) and select_gear(prob, prize):
                    combos.append((place, pid, prize_id))
    return combos


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, helper, prob = f["hero"], f["helper"], f["problem"]
    return [
        f'Write a short adventure story for a small child about "{prob.keyword}" and a funny meme that helps a team solve a problem.',
        f"Tell a gentle teamwork story where {hero.id} and {helper.label} face {prob.gerund} and make a smart plan.",
        f"Write a child-friendly adventure with humor, problem solving, and teamwork, and include the word \"meme\".",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, helper, prize, prob = f["hero"], f["helper"], f["prize"], f["problem"]
    qa = [
        QAItem(
            question=f"Who went on the adventure to {prob.verb}?",
            answer=f"{hero.id} went with {helper.label} on a small adventure at {world.setting.place}.",
        ),
        QAItem(
            question=f"What funny thing helped the team calm down before they solved the problem?",
            answer=f"A silly meme with a squirrel in a cape made them laugh and helped them think clearly.",
        ),
        QAItem(
            question=f"What prize did {hero.id} want to keep safe during the trip?",
            answer=f"{hero.id} wanted to keep {prize.phrase} safe while they solved the problem.",
        ),
    ]
    if f.get("gear"):
        gear = f["gear"]
        qa.append(QAItem(
            question=f"How did {gear.label} help the team?",
            answer=f"They used {gear.label} so {hero.id} could keep going without ruining the prize.",
        ))
    if f.get("resolved"):
        qa.append(QAItem(
            question=f"How did the story end?",
            answer=f"The team solved the problem together, and {hero.id} finished the adventure feeling proud and brave.",
        ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    tags = set(f["problem"].tags)
    if f.get("gear"):
        tags.add(f["gear"].id)
    out: list[QAItem] = []
    if "water" in tags:
        out.append(QAItem(
            question="Why do wet shoes feel heavy?",
            answer="Wet shoes feel heavy because water soaks into them and makes them hold more weight.",
        ))
    if "problem" in tags:
        out.append(QAItem(
            question="What does problem solving mean?",
            answer="Problem solving means looking carefully, thinking of a plan, and trying a safe way to fix a hard situation.",
        ))
    if "adventure" in tags:
        out.append(QAItem(
            question="What is an adventure?",
            answer="An adventure is a trip or task that feels exciting because something new or tricky is happening.",
        ))
    out.append(QAItem(
        question="What is a meme?",
        answer="A meme is a funny picture, phrase, or idea that people share because it makes them smile or laugh.",
    ))
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
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.protective:
            bits.append(f"covers={sorted(e.covers)}")
        elif e.region:
            bits.append(f"region={e.region}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="creek", problem="cross_creek", prize="map", name="Mina", gender="girl", helper="mother", trait="curious"),
    StoryParams(place="forest", problem="lost_sign", prize="journal", name="Theo", gender="boy", helper="father", trait="brave"),
    StoryParams(place="hill", problem="bridge_latch", prize="lantern", name="Lia", gender="girl", helper="mother", trait="playful"),
    StoryParams(place="cave", problem="dark_tunnel", prize="snack", name="Owen", gender="boy", helper="father", trait="cheerful"),
]


def explain_rejection(problem: Problem, prize: Prize) -> str:
    noun = prize.label if prize.plural else f"a {prize.label}"
    if not prize_at_risk(problem, prize):
        return f"(No story: {problem.gerund} does not put {noun} at risk in a way this world can honestly fix.)"
    return f"(No story: nothing in the gear list reasonably protects {noun} from {problem.gerund}.)"


def explain_gender(prize_id: str, gender: str) -> str:
    ok = " / ".join(sorted(PRIZES[prize_id].genders))
    return f"(No story: {PRIZES[prize_id].label} is not a typical {gender}'s item here; try --gender {ok}.)"


ASP_RULES = r"""
prize_at_risk(P, R) :- splashes(P, R), worn_on(T, R).
protects(G, P, T) :- gear(G), prize_at_risk(P, T),
                     mess_of(P, M), guards(G, M),
                     covers(G, R), worn_on(T, R).
has_fix(P, T) :- protects(_, P, T).
valid(Place, P, T) :- affords(Place, P), prize_at_risk(P, T), has_fix(P, T).
valid_story(Place, P, T, Gender) :- valid(Place, P, T), wears(Gender, T).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        if s.indoor:
            lines.append(asp.fact("indoor", pid))
        for p in sorted(s.affords):
            lines.append(asp.fact("affords", pid, p))
    for pid, p in PROBLEMS.items():
        lines.append(asp.fact("problem", pid))
        lines.append(asp.fact("mess_of", pid, p.mess))
        for r in sorted(p.zone):
            lines.append(asp.fact("splashes", pid, r))
    for tid, t in PRIZES.items():
        lines.append(asp.fact("prize", tid))
        lines.append(asp.fact("worn_on", tid, t.region))
        if t.plural:
            lines.append(asp.fact("prize_plural", tid))
        for g in sorted(t.genders):
            lines.append(asp.fact("wears", g, tid))
    for g in GEAR:
        lines.append(asp.fact("gear", g.id))
        for m in sorted(g.guards):
            lines.append(asp.fact("guards", g.id, m))
        for c in sorted(g.covers):
            lines.append(asp.fact("covers", g.id, c))
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
    a, b = set(asp_valid_combos()), set(valid_combos())
    if a == b:
        print(f"OK: clingo gate matches valid_combos() ({len(a)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if a - b:
        print("  only in clingo:", sorted(a - b))
    if b - a:
        print("  only in python:", sorted(b - a))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Adventure storyworld with humor, teamwork, and problem solving.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper", choices=["mother", "father"])
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
    if args.problem and args.prize:
        prob, prize = PROBLEMS[args.problem], PRIZES[args.prize]
        if not (prize_at_risk(prob, prize) and select_gear(prob, prize)):
            raise StoryError(explain_rejection(prob, prize))
    if args.gender and args.prize and args.gender not in PRIZES[args.prize].genders:
        raise StoryError(explain_gender(args.prize, args.gender))

    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.problem is None or c[1] == args.problem)
              and (args.prize is None or c[2] == args.prize)
              and (args.gender is None or args.gender in PRIZES[c[2]].genders)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place, problem, prize = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(NAMES)
    helper = args.helper or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, problem=problem, prize=prize, name=name, gender=gender, helper=helper, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], PROBLEMS[params.problem], PRIZES[params.prize],
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
        print(asp_program("#show valid_story/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        triples, stories = asp_valid_combos(), asp_valid_stories()
        print(f"{len(triples)} compatible (place, problem, prize) combos ({len(stories)} with gender):\n")
        for place, prob, prize in triples:
            genders = sorted(g for (pl, p, pr, g) in stories if (pl, p, pr) == (place, prob, prize))
            print(f"  {place:9} {prob:14} {prize:8}  [{', '.join(genders)}]")
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
            header = f"### {p.name}: {p.problem} at {p.place} (prize: {p.prize})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
