#!/usr/bin/env python3
"""
storyworlds/worlds/antique_problem_solving_sharing_heartwarming.py
===================================================================

A standalone story world sketch about a child, an antique family heirloom,
a problem to solve together, and the heartwarming moment of sharing.
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
from results import QAItem, StoryError, StorySample

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
        female = {"girl", "mother", "mom", "woman", "aunt"}
        male = {"boy", "father", "dad", "man", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad", "aunt": "aunt", "uncle": "uncle"}.get(self.type, self.type)


@dataclass
class Setting:
    place: str = "the attic"
    indoor: bool = True
    affords: set[str] = field(default_factory=set)


@dataclass
class Problem:
    """A problem the child wants to solve with the antique."""
    id: str
    verb: str
    gerund: str
    rush: str
    mess: str
    soil: str
    zone: set[str]
    keyword: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Antique:
    """The treasured family heirloom."""
    label: str
    phrase: str
    type: str
    region: str
    plural: bool = False
    genders: set[str] = field(default_factory=lambda: {"girl", "boy"})


@dataclass
class Tool:
    """A tool that helps solve the problem and protects the antique."""
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
        chunks = [" ".join(p) for p in self.paragraphs if p]
        return "\n\n".join(chunks)

    def copy(self) -> "World":
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.zone = set(self.zone)
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
        for mess in {"dusty", "scratchy"}:
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
                item.meters["damaged"] += 1
                out.append(
                    f"{actor.pronoun('possessive').capitalize()} {item.label} "
                    f"got {mess} and needed care."
                )
    return out


def _r_workload(world: World) -> list[str]:
    out: list[str] = []
    for item in list(world.entities.values()):
        if item.meters["damaged"] < THRESHOLD or not item.caretaker:
            continue
        sig = ("work", item.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        carer = world.get(item.caretaker)
        carer.meters["workload"] += 1
        out.append(f"That would mean more work for {carer.label}.")
    return out


def _r_grab_conflict(world: World) -> list[str]:
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


CAUSAL_RULES: list[Rule] = [
    Rule(name="soak", tag="physical", apply=_r_soak),
    Rule(name="workload", tag="physical", apply=_r_workload),
    Rule(name="grab_conflict", tag="social", apply=_r_grab_conflict),
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


def antique_at_risk(problem: Problem, antique: Antique) -> bool:
    return antique.region in problem.zone


def select_tool(problem: Problem, antique: Antique) -> Optional[Tool]:
    for tool in TOOLS:
        if problem.mess in tool.guards and antique.region in tool.covers:
            return tool
    return None


def predict_mess(world: World, actor: Entity, problem: Problem, antique_id: str) -> dict:
    sim = world.copy()
    _do_problem(sim, sim.get(actor.id), problem, narrate=False)
    antique = sim.entities.get(antique_id)
    return {
        "damaged": bool(antique and antique.meters["damaged"] >= THRESHOLD),
        "workload": sum(e.meters["workload"] for e in sim.characters()),
    }


def problem_delight(problem: Problem) -> str:
    return {
        "dust": "the soft dust motes danced in the light like tiny stars",
        "scratch": "the gentle rubbing sound felt like a secret conversation",
        "polish": "the warm glow made the metal shine like honey",
    }.get(problem.id, "it felt like solving a wonderful riddle")


def setting_detail(setting: Setting, problem: Problem) -> str:
    if setting.indoor:
        return f"The {setting.place.removeprefix('the ')} was quiet, and the old chest waited patiently."
    return f"{setting.place.capitalize()} looked wide and full of secrets."


def antique_was_preserved(hero: Entity, antique: Entity) -> str:
    return f"{hero.pronoun('possessive')} {antique.label} stayed just as beautiful"


def _do_problem(world: World, actor: Entity, problem: Problem, narrate: bool = True) -> None:
    if problem.id not in world.setting.affords:
        return
    world.zone = set(problem.zone)
    actor.meters[problem.mess] += 1
    actor.memes["joy"] += 1
    propagate(world, narrate=narrate)


def introduce(world: World, hero: Entity) -> None:
    trait = next((t for t in hero.traits if t != "little"), "")
    desc = f"little {trait} {hero.type}".strip()
    world.say(f"{hero.id} was a {desc} who loved exploring old things.")


def loves_problem(world: World, hero: Entity, problem: Problem) -> None:
    hero.memes["love_play"] += 1
    where = "inside" if world.setting.indoor else "outside"
    world.say(
        f"{hero.pronoun().capitalize()} loved solving problems {where} and {problem.gerund}; "
        f"{problem_delight(problem)}."
    )


def inherits(world: World, parent: Entity, hero: Entity, antique: Entity) -> None:
    world.say(
        f"That week, {hero.id}'s {parent.label_word} brought out "
        f"{antique.phrase} from the old chest."
    )


def loves_antique(world: World, hero: Entity, antique: Entity) -> None:
    hero.memes["love"] += 1
    antique.worn_by = hero.id
    world.say(
        f"{hero.id} loved {hero.pronoun('possessive')} {antique.label} and "
        f"wore {antique.it()} as if the sun had chosen {hero.pronoun('object')}."
    )


def arrive(world: World, hero: Entity, parent: Entity, problem: Problem) -> None:
    day = "One bright morning, "
    go = "were in" if world.setting.indoor else "went to"
    world.say(
        f"{day}{hero.id} and {hero.pronoun('possessive')} "
        f"{parent.label_word} {go} {world.setting.place}."
    )
    world.say(setting_detail(world.setting, problem))


def wants(world: World, hero: Entity, parent: Entity, problem: Problem) -> None:
    hero.memes["desire"] += 1
    world.say(
        f"{hero.id} wanted to {problem.verb} right away, but "
        f"{hero.pronoun('possessive')} {parent.label_word} held up a gentle hand."
    )


def warn(world: World, parent: Entity, hero: Entity, problem: Problem, antique: Entity) -> bool:
    pred = predict_mess(world, hero, problem, antique.id)
    if not pred["damaged"]:
        return False
    world.facts["predicted_damage"] = problem.soil
    world.facts["predicted_workload"] = pred["workload"]
    clause = f"We need to be careful with your {antique.label}, it could get {problem.soil}"
    if pred["workload"] >= THRESHOLD:
        clause += f", and then I'd have to fix {antique.it()}"
    world.say(f'"{clause}," {hero.pronoun("possessive")} {parent.label_word} said. "Let\'s think first."')
    return True


def defies(world: World, hero: Entity, problem: Problem) -> None:
    hero.memes["defiance"] += 1
    world.say(f"{hero.id} heard the warning, but the wish to solve was still tugging hard.")
    world.say(f"{hero.pronoun().capitalize()} tried to {problem.rush},")


def grab_hand(world: World, parent: Entity, hero: Entity, problem: Problem) -> None:
    hero.memes["grabbed_by"] += 1
    propagate(world, narrate=False)
    world.say(
        f"but {hero.pronoun('possessive')} {parent.label_word} grabbed "
        f"{hero.pronoun('possessive')} hand and said, "
        f'"You can want to {problem.verb}, and we can still choose the safe way."'
    )


def pout(world: World, hero: Entity, problem: Problem) -> None:
    if hero.memes["conflict"] >= THRESHOLD:
        world.say(
            f'{hero.id} pouted and crossed {hero.pronoun("possessive")} arms. '
            f'"But I really want to {problem.verb}!" {hero.pronoun()} said.'
        )


def compromise(world: World, parent: Entity, hero: Entity, problem: Problem,
               antique: Entity) -> Optional[Tool]:
    tool_def = select_tool(problem, antique)
    if tool_def is None:
        return None
    tool = world.add(Entity(
        id=tool_def.id, type="tool", label=tool_def.label,
        owner=hero.id, caretaker=parent.id, protective=True,
        covers=set(tool_def.covers), plural=tool_def.plural,
    ))
    tool.worn_by = hero.id
    if predict_mess(world, hero, problem, antique.id)["damaged"]:
        tool.worn_by = None
        del world.entities[tool.id]
        return None
    world.say(
        f'{hero.pronoun("possessive").capitalize()} {parent.label_word} looked at the '
        f'{antique.label}, then back at {hero.id}, and smiled. '
        f'"How about we {tool_def.prep} and {problem.verb} together?"'
    )
    return tool_def


def accept(world: World, parent: Entity, hero: Entity, problem: Problem, antique: Entity,
           tool_def: Tool) -> None:
    hero.memes["joy"] += 1
    hero.memes["love"] += 1
    hero.memes["conflict"] = 0.0
    world.say(
        f"{hero.id}'s face lit up and {hero.pronoun()} hugged "
        f"{hero.pronoun('possessive')} {parent.label_word}. "
        f'"Yay, let\'s solve it together!" {hero.pronoun()} said.'
    )
    world.say(
        f"They {tool_def.tail}. Soon {hero.id} was {problem.gerund}, "
        f"{antique_was_preserved(hero, antique)}, and {parent.label_word} was smiling beside "
        f"{hero.pronoun('object')}."
    )


def tell(setting: Setting, problem: Problem, antique_cfg: Antique,
         hero_name: str = "Lily", hero_type: str = "girl",
         hero_traits: Optional[list[str]] = None, parent_type: str = "mother") -> World:
    world = World(setting)
    world.weather = ""

    hero = world.add(Entity(
        id=hero_name, kind="character", type=hero_type,
        traits=["little"] + (hero_traits or ["curious", "patient"]),
    ))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label="the parent"))
    antique = world.add(Entity(
        id="antique", type=antique_cfg.type, label=antique_cfg.label,
        phrase=antique_cfg.phrase, owner=hero.id, caretaker=parent.id,
        region=antique_cfg.region, plural=antique_cfg.plural,
    ))

    introduce(world, hero)
    loves_problem(world, hero, problem)
    inherits(world, parent, hero, antique)
    loves_antique(world, hero, antique)

    world.para()
    arrive(world, hero, parent, problem)
    wants(world, hero, parent, problem)
    warn(world, parent, hero, problem, antique)
    defies(world, hero, problem)
    grab_hand(world, parent, hero, problem)

    world.para()
    pout(world, hero, problem)
    tool_def = compromise(world, parent, hero, problem, antique)
    if tool_def:
        accept(world, parent, hero, problem, antique, tool_def)

    world.facts.update(hero=hero, parent=parent, antique=antique, antique_cfg=antique_cfg,
                       problem=problem, setting=setting, tool=tool_def,
                       conflict=hero.memes["grabbed_by"] >= THRESHOLD,
                       resolved=tool_def is not None)
    return world


SETTINGS = {
    "attic": Setting(place="the attic", indoor=True, affords={"dust", "polish"}),
    "workshop": Setting(place="the workshop", indoor=True, affords={"scratch", "polish"}),
    "garden": Setting(place="the garden", indoor=False, affords={"dust"}),
    "library": Setting(place="the library", indoor=True, affords={"dust", "scratch"}),
}

PROBLEMS = {
    "dust": Problem(
        id="dust",
        verb="dust the old things",
        gerund="dusting the antiques",
        rush="rush to the dusty shelf",
        mess="dusty",
        soil="dusty and dull",
        zone={"feet", "legs", "torso"},
        keyword="dust",
        tags={"dust", "clean"},
    ),
    "scratch": Problem(
        id="scratch",
        verb="polish the scratch",
        gerund="polishing the scratches",
        rush="reach for the polishing cloth",
        mess="scratchy",
        soil="scratched and sad",
        zone={"torso"},
        keyword="scratch",
        tags={"scratch", "polish"},
    ),
    "polish": Problem(
        id="polish",
        verb="polish the metal",
        gerund="polishing the metal",
        rush="grab the polish",
        mess="dusty",
        soil="dull and tarnished",
        zone={"torso", "legs"},
        keyword="polish",
        tags={"polish", "shine"},
    ),
}

TOOLS = [
    Tool(
        id="apron",
        label="a soft apron",
        covers={"torso", "legs"},
        guards={"dusty", "scratchy"},
        prep="put on the soft apron from the hook",
        tail="wrapped the soft apron around themselves and got to work",
    ),
    Tool(
        id="gloves",
        label="special gloves",
        covers={"feet"},
        guards={"dusty"},
        prep="put on the special gloves from the drawer",
        tail="put on the special gloves and began",
    ),
    Tool(
        id="cloth",
        label="a clean polishing cloth",
        covers={"torso"},
        guards={"scratchy"},
        prep="take the clean polishing cloth",
        tail="took the clean polishing cloth and worked gently",
    ),
]

ANTIQUES = {
    "brooch": Antique(
        label="brooch",
        phrase="an antique brooch with tiny flowers",
        type="brooch",
        region="torso",
        genders={"girl", "boy"},
    ),
    "pocket_watch": Antique(
        label="pocket watch",
        phrase="an antique pocket watch with a golden chain",
        type="pocket_watch",
        region="torso",
        genders={"girl", "boy"},
    ),
    "locket": Antique(
        label="locket",
        phrase="an antique locket with a hidden photo",
        type="locket",
        region="torso",
        genders={"girl", "boy"},
    ),
    "medal": Antique(
        label="medal",
        phrase="an antique medal from a great-great-grandparent",
        type="medal",
        region="torso",
        genders={"girl", "boy"},
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Anna", "Maya", "Nora", "Rose"]
BOY_NAMES = ["Tim", "Ben", "Max", "Sam", "Leo", "Jack", "Finn", "Noah", "Eli", "Theo"]
TRAITS = ["curious", "patient", "gentle", "careful", "thoughtful", "kind"]


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for prob_id in setting.affords:
            prob = PROBLEMS[prob_id]
            for antique_id, antique in ANTIQUES.items():
                if antique_at_risk(prob, antique) and select_tool(prob, antique):
                    combos.append((place, prob_id, antique_id))
    return combos


@dataclass
class StoryParams:
    place: str
    problem: str
    antique: str
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


KNOWLEDGE = {
    "dust": [("What is dust?",
              "Dust is tiny bits of dirt and fluff that settle on surfaces over time.")],
    "scratch": [("How can a scratch happen?",
                 "A scratch happens when something sharp rubs against a surface and leaves a mark.")],
    "polish": [("What does polish do?",
                "Polish makes metal or wood shine by smoothing out small marks and adding a glow.")],
    "clean": [("Why do we clean antiques gently?",
               "Antiques are old and can break easily, so we clean them softly to keep them safe.")],
    "antique": [("What is an antique?",
                 "An antique is a very old object that has been passed down through a family.")],
    "apron": [("What is an apron for?",
               "An apron protects your clothes from dust and dirt while you work.")],
    "gloves": [("Why wear gloves when cleaning?",
                "Gloves keep your hands clean and also protect delicate surfaces from oils on your skin.")],
    "cloth": [("What is a polishing cloth for?",
               "A polishing cloth is used to gently rub surfaces to make them shine without scratching.")],
}
KNOWLEDGE_ORDER = ["dust", "scratch", "polish", "clean", "antique", "apron", "gloves", "cloth"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, parent, prob, antique = f["hero"], f["parent"], f["problem"], f["antique_cfg"]
    kw = prob.keyword or prob.mess
    return [
        f'Write a short story for a 3-to-5-year-old on the theme "a child, an antique, sharing a problem" that includes the word "{kw}".',
        f"Tell a gentle story where a {hero.type} named {hero.id} wants to {prob.verb} an {antique.label} but {hero.pronoun('possessive')} {parent.label_word} helps {hero.pronoun('object')} solve the problem together.",
        f'Write a simple story that uses the noun "{kw}" and ends with a parent and child sharing a happy moment while caring for an antique.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, parent, antique, prob = f["hero"], f["parent"], f["antique"], f["problem"]
    pw = parent.label_word
    sub, obj, pos = (hero.pronoun("subject"), hero.pronoun("object"),
                     hero.pronoun("possessive"))
    where = "inside" if world.setting.indoor else "outside"
    place = world.setting.place
    trait = next((t for t in hero.traits if t != "little"), hero.type)
    day = "bright morning"
    qa: list[QAItem] = [
        QAItem(
            question=(
                f"Who is the story about when {hero.id} visits {place} to "
                f"{prob.verb} {pos} {antique.label}?"
            ),
            answer=(
                f"It is about a little {trait} {hero.type} named {hero.id} and "
                f"{pos} {pw}. They go to {place} on a {day}, and {hero.id} is "
                f"caring for {pos} {antique.label}."
            ),
        ),
        QAItem(
            question=(
                f"What did {trait} {hero.id} love to do {where} in {place} before "
                f"{pw} helped with {pos} {antique.label}?"
            ),
            answer=(
                f"{trait.capitalize()} {hero.id} loved solving problems {where} and "
                f"{prob.gerund}. That careful work became important because {pos} "
                f"{antique.label} needed gentle care."
            ),
        ),
        QAItem(
            question=(
                f"What {antique.label} did {hero.id}'s {pw} bring out for the "
                f"{trait} {hero.type} before "
                f"the {prob.keyword or prob.mess} work at {place}?"
            ),
            answer=(
                f"{pos.capitalize()} {pw} brought out {antique.phrase}. "
                f"{hero.id} loved {antique.it()} and wore {antique.it()} with pride."
            ),
        ),
    ]
    if f.get("conflict"):
        soil = f.get("predicted_damage", "damaged")
        work = f.get("predicted_workload", 0)
        why = (f"{pos.capitalize()} {pw} was careful because if {hero.id} went to "
               f"{prob.verb}, {pos} {antique.label} would get {soil}")
        why += (f", and then {pw} would have to fix {antique.it()}. "
                if work >= THRESHOLD else ". ")
        why += (f"When {hero.id} tried to {prob.rush.rstrip(', ')}, {pos} {pw} "
                f"held {pos} hand and reminded {obj} they could solve the problem "
                f"together.")
        qa.append(QAItem(
            question=(
                f"Why did {hero.id}'s {pw} want to be careful with {pos} {antique.label} "
                f"when {trait} {hero.id} wanted to {prob.verb} at {place}?"
            ),
            answer=why,
        ))
    if f.get("resolved"):
        tool = f["tool"]
        tool_plan = tool.label
        if tool_plan.startswith(("a ", "an ")):
            tool_plan = tool_plan.split(" ", 1)[1]
        qa.append(QAItem(
            question=(
                f"How did {tool.label} help {trait} {hero.id} {prob.verb} at {place} "
                f"without damaging {pos} {antique.label}?"
            ),
            answer=(
                f"They agreed to use {tool.label} first, so {hero.id} could "
                f"{prob.verb} at {place} without damaging {pos} {antique.label}. "
                f"The plan let {obj} solve the problem while {pos} {antique.label} stayed safe."
            ),
        ))
        qa.append(QAItem(
            question=(
                f"How did {trait} {hero.id} feel after {pw} agreed to the {tool_plan} "
                f"plan for {prob.keyword or prob.mess} at {place}?"
            ),
            answer=(
                f"{hero.id} felt happy and hugged {pos} {pw} once they agreed "
                f"on the plan for {pos} {antique.label}. At the end, {sub} was "
                f"{prob.gerund} with {pw} smiling nearby."
            ),
        ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    tags = set(f["problem"].tags)
    if f.get("tool"):
        tags.add(f["tool"].id)
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
    StoryParams(
        place="attic",
        problem="dust",
        antique="brooch",
        name="Lily",
        gender="girl",
        parent="mother",
        trait="curious",
    ),
    StoryParams(
        place="workshop",
        problem="scratch",
        antique="pocket_watch",
        name="Tim",
        gender="boy",
        parent="father",
        trait="patient",
    ),
    StoryParams(
        place="library",
        problem="polish",
        antique="locket",
        name="Mia",
        gender="girl",
        parent="aunt",
        trait="gentle",
    ),
    StoryParams(
        place="garden",
        problem="dust",
        antique="medal",
        name="Ben",
        gender="boy",
        parent="uncle",
        trait="careful",
    ),
]


def explain_rejection(problem: Problem, antique: Antique) -> str:
    noun = antique.label if antique.plural else f"a {antique.label}"
    verb = "sit" if antique.plural else "sits"
    if not antique_at_risk(problem, antique):
        return (f"(No story: {problem.gerund} touches {sorted(problem.zone)}, "
                f"but {noun} {verb} on the {antique.region} -- it wouldn't get "
                f"{problem.mess}, so the parent has no honest warning. "
                f"Try an antique worn on {sorted(problem.zone)}.)")
    return (f"(No story: nothing in the tool catalog protects {noun} "
            f"({antique.region}) from {problem.gerund}. The compromise must actually "
            f"cover the at-risk item, so this argument is rejected.)")


def explain_gender(antique_id: str, gender: str) -> str:
    ok = " / ".join(sorted(ANTIQUES[antique_id].genders))
    return (f"(No story: a {ANTIQUES[antique_id].label} isn't a typical {gender}'s "
            f"item here; try --gender {ok}.)")


ASP_RULES = r"""
antique_at_risk(A, P) :- touches(P, R), worn_on(A, R).
protects(T, P, A) :- tool(T), antique_at_risk(P, A), mess_of(P, M), guards(T, M), covers(T, R), worn_on(A, R).
has_fix(P, A) :- protects(_, P, A).
valid(Place, P, A) :- affords(Place, P), antique_at_risk(P, A), has_fix(P, A).
valid_story(Place, P, A, Gender) :- valid(Place, P, A), wears(Gender, A).
"""


def asp_facts() -> str:
    import asp as _asp
    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(_asp.fact("setting", pid))
        if s.indoor:
            lines.append(_asp.fact("indoor", pid))
        for a in sorted(s.affords):
            lines.append(_asp.fact("affords", pid, a))
    for aid, a in PROBLEMS.items():
        lines.append(_asp.fact("problem", aid))
        lines.append(_asp.fact("mess_of", aid, a.mess))
        for r in sorted(a.zone):
            lines.append(_asp.fact("touches", aid, r))
    for pid, pr in ANTIQUES.items():
        lines.append(_asp.fact("antique", pid))
        lines.append(_asp.fact("worn_on", pid, pr.region))
        if pr.plural:
            lines.append(_asp.fact("antique_plural", pid))
        for g in sorted(pr.genders):
            lines.append(_asp.fact("wears", g, pid))
    for t in TOOLS:
        lines.append(_asp.fact("tool", t.id))
        for m in sorted(t.guards):
            lines.append(_asp.fact("guards", t.id, m))
        for r in sorted(t.covers):
            lines.append(_asp.fact("covers", t.id, r))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp as _asp
    model = _asp.one_model(asp_program("#show valid/3."))
    return sorted(set(_asp.atoms(model, "valid")))


def asp_valid_stories() -> list[tuple]:
    import asp as _asp
    model = _asp.one_model(asp_program("#show valid_story/4."))
    return sorted(set(_asp.atoms(model, "valid_story")))


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
        description="Story world sketch: a child, an antique, solving a problem together.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--antique", choices=ANTIQUES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father", "aunt", "uncle"])
    ap.add_argument("--name")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP gate matches valid_combos()")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program (facts + inline rules)")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.problem and args.antique:
        prob, ant = PROBLEMS[args.problem], ANTIQUES[args.antique]
        if not (antique_at_risk(prob, ant) and select_tool(prob, ant)):
            raise StoryError(explain_rejection(prob, ant))
    if args.gender and args.antique and args.gender not in ANTIQUES[args.antique].genders:
        raise StoryError(explain_gender(args.antique, args.gender))

    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.problem is None or c[1] == args.problem)
              and (args.antique is None or c[2] == args.antique)
              and (args.gender is None or args.gender in ANTIQUES[c[2]].genders)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place, problem_id, antique_id = rng.choice(sorted(combos))
    antique = ANTIQUES[antique_id]
    gender = args.gender or rng.choice(sorted(antique.genders))
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father", "aunt", "uncle"])
    trait = rng.choice(TRAITS)
    return StoryParams(
        place=place,
        problem=problem_id,
        antique=antique_id,
        name=name,
        gender=gender,
        parent=parent,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], PROBLEMS[params.problem],
                 ANTIQUES[params.antique], params.name, params.gender,
                 [params.trait, "careful"], params.parent)
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
        triples, stories = asp_valid_combos(), asp_valid_stories()
        print(f"{len(triples)} compatible (place, problem, antique) combos "
              f"({len(stories)} with gender):\n")
        for place, prob, antique in triples:
            genders = sorted(g for (pl, p, a, g) in stories
                             if (pl, p, a) == (place, prob, antique))
            print(f"  {place:9} {prob:8} {antique:12}  [{', '.join(genders)}]")
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
            header = f"### {p.name}: {p.problem} at {p.place} (antique: {p.antique})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
