#!/usr/bin/env python3
"""
storyworlds/worlds/deepseek_deepseek-v4-flash_service_20260624T185554Z_seed424242_n50/antique_problem_solving_sharing_heartwarming.py
======================================================================================================================================

A standalone *story world* sketch for a heartwarming tale about an antique,
shared problem solving, and the joy of fixing something together.

Domain:
- antique: a treasured old item (toy, music box, vase, lamp)
- problem solving: child and grandparent figure out how to repair it
- sharing: they share the effort and the final delight

Initial story (seed) used to build the world model:
---
Once upon a time, there was a little boy named Sam. He loved visiting his Grandpa's
attic, where old things whispered stories. One Saturday, Grandpa showed Sam a
beautiful antique toy train with a broken wheel. "It's been in our family for
a long time," Grandpa said. "But I never knew how to fix it."

Sam looked at the train and then at Grandpa's workbench. He saw small screws,
a tiny wrench, and some glue. "Maybe we can fix it together?" Sam asked.
Grandpa smiled. "That would be wonderful." They examined the wheel carefully.
Sam held the train steady while Grandpa glued the axle. Then they found a
matching screw and tightened it. The train rolled perfectly. Sam's eyes lit up.
"Now we can play with it together!" he said. And from that day, the antique
train was a shared treasure.
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

# Physical meter keys for objects
DAMAGE_KINDS = {"broken", "cracked", "rusty", "sticky"}

# Skills that a character can use
SKILLS = {"careful", "patient", "strong", "resourceful"}


# ---------------------------------------------------------------------------
# Entities
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"            # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    held_by: Optional[str] = None
    material: str = "wood"         # "wood", "metal", "glass", "cloth"
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        male = {"boy", "grandfather", "grandpa", "father"}
        female = {"girl", "grandmother", "grandma", "mother"}
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

    @property
    def label_word(self) -> str:
        return {"grandfather": "grandpa", "grandmother": "grandma",
                "father": "dad", "mother": "mom"}.get(self.type, self.type)


# ---------------------------------------------------------------------------
# Parameterization knobs
# ---------------------------------------------------------------------------
@dataclass
class Setting:
    place: str = "the attic"
    affords: set[str] = field(default_factory=set)   # which problem types this place allows


@dataclass
class Problem:
    """A defect that needs fixing."""
    id: str
    verb: str            # after "wanted to ...", e.g. "fix the broken wheel"
    gerund: str          # after "loved ... and ...", e.g. "fixing things together"
    rush: str            # after "tried to ...", e.g. "reach for the glue"
    damage: str          # damage kind key, one of DAMAGE_KINDS
    symptom: str         # how the antique is described: "a chipped edge", "a loose screw"
    material_needed: str # material requirement: "wood", "metal", "glass", "cloth"
    skill_needed: str    # skill required from one character: "careful", "patient", etc.
    keyword: str = "fix"
    tags: set[str] = field(default_factory=set)


@dataclass
class Antique:
    """The treasured old object that is broken."""
    label: str
    phrase: str
    type: str
    material: str
    plural: bool = False
    genders: set[str] = field(default_factory=lambda: {"boy", "girl"})


@dataclass
class Tool:
    """A tool or method used to repair the antique."""
    id: str
    label: str
    works_on: set[str]          # materials it can fix
    needs_skill: str = ""       # skill required to use it safely
    prep: str                   # "get the small glue bottle"
    tail: str                   # "walked over to the workbench and picked up the glue"
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
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def held_items(self, actor: Entity) -> list[Entity]:
        return [e for e in self.entities.values() if e.held_by == actor.id]

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


def _r_hold_steady(world: World) -> list[str]:
    """If child holds the antique and grandparent holds a tool, the repair is possible."""
    out = []
    for child in world.characters():
        if child.memes["willing_help"] < THRESHOLD:
            continue
        for gp in world.characters():
            if gp.id == child.id:
                continue
            if gp.memes["willing_teach"] < THRESHOLD:
                continue
            # Check child holds the antique and gp holds a tool
            antique = None
            tool = None
            for item in world.held_items(child):
                if item.type in ("antique", "treasure"):
                    antique = item
                    break
            for item in world.held_items(gp):
                if item.type == "tool":
                    tool = item
                    break
            if antique and tool:
                sig = ("repair", child.id, gp.id, antique.id, tool.id)
                if sig in world.fired:
                    continue
                world.fired.add(sig)
                # Repair success: remove damage, add joy
                antique.meters[tool.works_on.intersection(DAMAGE_KINDS).pop()] -= 1
                if antique.meters[tool.works_on.intersection(DAMAGE_KINDS).pop()] < 0:
                    antique.meters[tool.works_on.intersection(DAMAGE_KINDS).pop()] = 0
                child.memes["joy"] += 1
                gp.memes["joy"] += 1
                out.append("Together they fixed the antique.")
    return out


CAUSAL_RULES = [
    Rule(name="hold_steady", tag="physical", apply=_r_hold_steady),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced = []
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
# Constraint helpers
# ---------------------------------------------------------------------------
def antique_has_problem(antique_cfg: Antique, problem: Problem) -> bool:
    """The antique's material must match the problem's material_needed."""
    return antique_cfg.material == problem.material_needed


def select_tool(problem: Problem, antique_cfg: Antique) -> Optional[Tool]:
    """Find a tool that works on the antique's material and matches the skill."""
    for tool in TOOLS:
        if antique_cfg.material in tool.works_on:
            if not tool.needs_skill or tool.needs_skill == problem.skill_needed:
                return tool
    return None


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for prob_id in setting.affords:
            problem = PROBLEMS[prob_id]
            for antique_id, antique in ANTIQUES.items():
                if antique_has_problem(antique, problem) and select_tool(problem, antique):
                    combos.append((place, prob_id, antique_id))
    return combos


# ---------------------------------------------------------------------------
# Prediction
# ---------------------------------------------------------------------------
def predict_repair(world: World, actor: Entity, problem: Problem, tool: Tool) -> dict:
    """Simulate a repair attempt silently; return success and joy."""
    sim = world.copy()
    # Assume child holds antique, grandparent holds tool
    # For simplicity, we just check if the skill condition is met
    child_skill = any(t in SKILLS for t in actor.traits if t in SKILLS)
    gp_skill = True  # grandparent is assumed skilled
    if child_skill or gp_skill:
        return {"succeeds": True, "joy_gain": 1}
    return {"succeeds": False, "joy_gain": 0}


# ---------------------------------------------------------------------------
# Verbs (screenplay)
# ---------------------------------------------------------------------------
def introduce(world: World, hero: Entity) -> None:
    trait = next((t for t in hero.traits if t not in ("little", "curious")), "curious")
    world.say(f"{hero.id} was a little {trait} {hero.type} who loved exploring old things.")


def loves_visits(world: World, hero: Entity, parent: Entity) -> None:
    world.say(f"{hero.pronoun().capitalize()} loved visiting {parent.label_word}'s {world.setting.place}.")


def show_antique(world: World, parent: Entity, hero: Entity, antique_cfg: Antique, problem: Problem) -> None:
    world.say(
        f"One day, {parent.label_word} showed {hero.id} {antique_cfg.phrase}. "
        f'"{parent.pronoun('possessive').capitalize()} been in our family for a long time," {parent.label_word} said. '
        f'"But I never knew how to fix {problem.symptom}."'
    )


def child_offers_help(world: World, hero: Entity, parent: Entity, antique_cfg: Antique) -> None:
    hero.memes["willing_help"] += 1
    world.say(
        f'{hero.id} looked at the {antique_cfg.label} and then at {parent.label_word}\'s workbench. '
        f'"Maybe we can fix {antique_cfg.it()} together?" {hero.id} asked.'
    )


def parent_accepts(world: World, parent: Entity, hero: Entity) -> None:
    parent.memes["willing_teach"] += 1
    world.say(f'{parent.pronoun("possessive").capitalize()} {parent.label_word} smiled. "That would be wonderful."')


def examine(world: World, hero: Entity, parent: Entity, antique_cfg: Antique, problem: Problem) -> None:
    world.say(f"They examined the {problem.symptom} carefully.")
    # Set up held items
    hero_antique = world.get("antique")
    hero_antique.held_by = hero.id
    # We'll let the narrative proceed; tool will be held later.


def fetch_tool(world: World, parent: Entity, hero: Entity, tool: Tool) -> None:
    world.say(
        f'{parent.label_word.capitalize()} {tool.tail}. '
        f'Then {parent.pronoun()} held the tool steady.'
    )
    tool_ent = world.add(Entity(
        id="tool", kind="thing", type="tool", label=tool.label,
        held_by=parent.id, material=tool.works_on.pop() if tool.works_on else "metal"
    ))
    # The rule engine will fire when child holds antique and parent holds tool


def fix_together(world: World, hero: Entity, parent: Entity, antique_cfg: Antique, tool: Tool) -> None:
    hero.memes["joy"] += 1
    parent.memes["joy"] += 1
    world.facts["repaired"] = True
    world.say(
        f"{hero.id} held the {antique_cfg.label} steady while {parent.label_word} {tool.prep}. "
        f"The {antique_cfg.label} was fixed! It was perfect."
    )


def celebrate(world: World, hero: Entity, parent: Entity, antique_cfg: Antique) -> None:
    world.say(
        f'{hero.id}\'s eyes lit up. "Now we can play with {antique_cfg.it()} together!" {hero.pronoun()} said. '
        f'And from that day, the {antique_cfg.label} was a shared treasure.'
    )


# ---------------------------------------------------------------------------
# The screenplay
# ---------------------------------------------------------------------------
def tell(setting: Setting, problem: Problem, antique_cfg: Antique,
         hero_name: str = "Sam", hero_type: str = "boy",
         hero_traits: Optional[list[str]] = None,
         parent_type: str = "grandfather") -> World:
    world = World(setting)

    hero = world.add(Entity(
        id=hero_name, kind="character", type=hero_type,
        traits=["little", "curious"] + (hero_traits or []),
    ))
    parent = world.add(Entity(
        id="Parent", kind="character", type=parent_type, label="the grandparent"
    ))
    antique = world.add(Entity(
        id="antique", kind="thing", type="antique",
        label=antique_cfg.label, phrase=antique_cfg.phrase,
        material=antique_cfg.material, owner=parent.id,
        caretaker=parent.id, plural=antique_cfg.plural,
    ))
    # Add damage
    antique.meters[problem.damage] += 1

    # Act 1: setup
    introduce(world, hero)
    loves_visits(world, hero, parent)
    show_antique(world, parent, hero, antique_cfg, problem)
    child_offers_help(world, hero, parent, antique_cfg)
    parent_accepts(world, parent, hero)

    # Act 2: the fix
    world.para()
    examine(world, hero, parent, antique_cfg, problem)
    tool = select_tool(problem, antique_cfg)
    if tool:
        fetch_tool(world, parent, hero, tool)
        # Trigger repair via rule propagation
        propagate(world, narrate=False)
        fix_together(world, hero, parent, antique_cfg, tool)
    else:
        # Fallback – should not happen in valid combos
        world.say(f"They tried to fix it but lacked the right tool.")

    # Act 3: celebration
    world.para()
    celebrate(world, hero, parent, antique_cfg)

    world.facts.update(
        hero=hero, parent=parent, antique=antique_cfg, problem=problem,
        setting=setting, tool=tool,
        repaired=world.facts.get("repaired", False),
    )
    return world


# ---------------------------------------------------------------------------
# Content registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "attic": Setting(place="the attic", affords={"wheel", "crack", "dusty_spring"}),
    "workshop": Setting(place="the workshop", affords={"wheel", "crack", "rusty_hinge"}),
    "garden_shed": Setting(place="the garden shed", affords={"crack", "rusty_hinge"}),
}

PROBLEMS = {
    "wheel": Problem(
        id="wheel",
        verb="fix the broken wheel",
        gerund="fixing things together",
        rush="try to glue the broken piece",
        damage="broken",
        symptom="a broken wheel",
        material_needed="wood",
        skill_needed="careful",
        keyword="wheel",
        tags={"repair", "wheel"},
    ),
    "crack": Problem(
        id="crack",
        verb="mend the cracked edge",
        gerund="mending old objects",
        rush="try to glue the crack",
        damage="cracked",
        symptom="a crack in the side",
        material_needed="metal",
        skill_needed="patient",
        keyword="crack",
        tags={"repair", "crack"},
    ),
    "sticky": Problem(
        id="dusty_spring",
        verb="clean the dusty spring",
        gerund="cleaning and oiling treasures",
        rush="try to oil the spring",
        damage="sticky",
        symptom="a sticky spring that won't move",
        material_needed="cloth",
        skill_needed="resourceful",
        keyword="spring",
        tags={"clean", "spring"},
    ),
}

ANTIQUES = {
    "train": Antique(
        label="train",
        phrase="a beautiful antique toy train",
        type="train",
        material="wood",
        plural=False,
        genders={"boy", "girl"},
    ),
    "music_box": Antique(
        label="music box",
        phrase="a delicate antique music box",
        type="music_box",
        material="metal",
        plural=False,
        genders={"girl", "boy"},
    ),
    "lamp": Antique(
        label="lamp",
        phrase="an old brass lamp",
        type="lamp",
        material="metal",
        plural=False,
        genders={"boy", "girl"},
    ),
    "doll": Antique(
        label="doll",
        phrase="a porcelain doll with a chipped arm",
        type="doll",
        material="glass",
        plural=False,
        genders={"girl"},
    ),
}

TOOLS = [
    Tool(
        id="glue_brush",
        label="the small glue bottle and brush",
        works_on={"wood", "glass"},
        needs_skill="careful",
        prep="gently applied glue to the broken edge",
        tail="walked over to the workbench and picked up the glue bottle",
    ),
    Tool(
        id="oil_can",
        label="the oil can",
        works_on={"metal", "wood"},
        needs_skill="patient",
        prep="carefully oiled the rusty hinge",
        tail="fetched the oil can from the shelf",
    ),
    Tool(
        id="soft_cloth",
        label="a soft cloth and mild soap",
        works_on={"cloth", "metal"},
        needs_skill="resourceful",
        prep="gently wiped away the sticky residue",
        tail="found a soft cloth in the drawer",
    ),
]

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ella", "Nora"]
BOY_NAMES = ["Sam", "Tim", "Ben", "Max", "Leo"]
TRAITS = ["curious", "careful", "patient", "resourceful", "eager"]


# ---------------------------------------------------------------------------
# StoryParams
# ---------------------------------------------------------------------------
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


# ---------------------------------------------------------------------------
# Q&A generation
# ---------------------------------------------------------------------------
KNOWLEDGE = {
    "repair": [("What does it mean to fix something?",
                "To fix something means to make it work again, like putting back "
                "a broken piece or cleaning a part that is stuck.")],
    "wheel": [("Why might a toy train need a wheel fixed?",
               "A toy train's wheel can break off if the train is old or if the "
               "wheel was bumped. It needs glue and steady hands to fix it.")],
    "crack": [("What is a crack?",
               "A crack is a thin line where something has broken, usually in "
               "wood or metal. It can be mended with the right adhesive.")],
    "spring": [("What does a spring do in a toy?",
                "A spring in a toy makes a part move or bounce. If it gets dusty "
                "and sticky, it won't move properly until cleaned and oiled.")],
    "oil_can": [("What is an oil can used for?",
                 "An oil can holds a special oil that makes rusty or stuck parts "
                 "move smoothly again.")],
    "glue": [("How does glue help fix things?",
              "Glue is a sticky liquid that holds broken pieces together once "
              "it dries.")],
}
KNOWLEDGE_ORDER = ["repair", "wheel", "crack", "spring", "oil_can", "glue"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    parent = f["parent"]
    antique = f["antique"]
    problem = f["problem"]
    kw = problem.keyword
    return [
        f'Write a short heartwarming story for a young child about fixing an old {antique.label} together with a {parent.type}.',
        f"Tell a gentle story where a {hero.type} named {hero.id} and {hero.pronoun('possessive')} {parent.label_word} repair a {antique.label} and share the joy.",
        f'Write a simple story that uses the word "{kw}" and ends with a child and parent sharing a repaired treasure.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, parent, antique, problem = f["hero"], f["parent"], f["antique"], f["problem"]
    pw = parent.label_word
    sub, obj, pos = hero.pronoun("subject"), hero.pronoun("object"), hero.pronoun("possessive")
    place = world.setting.place
    repaired = f.get("repaired", False)
    qa = [
        QAItem(
            question=f"Who is the story about?",
            answer=f"It is about a little {hero.type} named {hero.id} and {pos} {pw}. They explore {place} together."
        ),
        QAItem(
            question=f"What did {hero.id} and {pw} find in {place}?",
            answer=f"They found {antique.phrase} with {problem.symptom}."
        ),
        QAItem(
            question=f"How did {hero.id} and {pw} fix the {antique.label}?",
            answer=f"They worked together: {hero.id} held the {antique.label} steady while {pw} {world.facts['tool'].prep if f.get('tool') else 'carefully repaired it'}. They shared the job and fixed it."
        ),
    ]
    if repaired:
        qa.append(QAItem(
            question=f"What happened after the {antique.label} was fixed?",
            answer=f"{hero.pronoun('possessive').capitalize()} eyes lit up with joy, and they played together with the {antique.label} from that day on."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    tags = set(f["problem"].tags)
    if f.get("tool"):
        tags.add(f["tool"].id)
    out = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
            out.extend(QAItem(q, a) for q, a in KNOWLEDGE[tag])
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


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A problem applies to an antique if the antique's material matches the problem's needed material.
problem_applies(P, A) :- problem(P), antique(A), material_of(A, M), material_needed(P, M).

% A tool can fix a problem if it works on the antique's material and (if any) matches the skill.
can_fix(T, P, A) :- tool(T), problem_applies(P, A),
                    works_on(T, M), material_of(A, M),
                    (needs_skill(T, S) ; not needs_skill(T, _)),
                    (needs_skill(T, S) -> skill_needed(P, S) ; true).

% There is a valid story when a setting affords the problem and a tool can fix it.
valid(Place, P, A) :- affords(Place, P), problem_applies(P, A), can_fix(_, P, A).
valid_story(Place, P, A, Gender) :- valid(Place, P, A), wears(Gender, A).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", pid, a))
    for pid, p in PROBLEMS.items():
        lines.append(asp.fact("problem", pid))
        lines.append(asp.fact("material_needed", pid, p.material_needed))
        if p.skill_needed:
            lines.append(asp.fact("skill_needed", pid, p.skill_needed))
    for aid, a in ANTIQUES.items():
        lines.append(asp.fact("antique", aid))
        lines.append(asp.fact("material_of", aid, a.material))
        if a.plural:
            lines.append(asp.fact("antique_plural", aid))
        for g in sorted(a.genders):
            lines.append(asp.fact("wears", g, aid))
    for t in TOOLS:
        lines.append(asp.fact("tool", t.id))
        for m in sorted(t.works_on):
            lines.append(asp.fact("works_on", t.id, m))
        if t.needs_skill:
            lines.append(asp.fact("needs_skill", t.id, t.needs_skill))
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
    print("MISMATCH:")
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
        description="Heartwarming story about fixing an antique together.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--antique", choices=ANTIQUES)
    ap.add_argument("--gender", choices=["boy", "girl"])
    ap.add_argument("--parent", choices=["grandfather", "grandmother"])
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
    if args.problem and args.antique:
        prob = PROBLEMS[args.problem]
        ant = ANTIQUES[args.antique]
        if not antique_has_problem(ant, prob) or not select_tool(prob, ant):
            raise StoryError(f"(No story: {ant.label} material is {ant.material}, "
                             f"but problem {prob.id} needs {prob.material_needed}. "
                             f"Or no tool available.)")
    if args.gender and args.antique and args.gender not in ANTIQUES[args.antique].genders:
        raise StoryError(f"(No story: a {ANTIQUES[args.antique].label} is not typical for a {args.gender}.)")

    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.problem is None or c[1] == args.problem)
              and (args.antique is None or c[2] == args.antique)]
    if not combos:
        raise StoryError("(No valid combination matches given options.)")

    place, problem_id, antique_id = rng.choice(sorted(combos))
    ant = ANTIQUES[antique_id]
    gender = args.gender or rng.choice(sorted(ant.genders))
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["grandfather", "grandmother"])
    trait = rng.choice(TRAITS)
    return StoryParams(
        place=place, problem=problem_id, antique=antique_id,
        name=name, gender=gender, parent=parent, trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.place], PROBLEMS[params.problem], ANTIQUES[params.antique],
        params.name, params.gender, [params.trait], params.parent,
    )
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
        print("--- world model state ---")
        for e in sample.world.entities.values():
            m = dict(e.meters) if any(e.meters.values()) else {}
            me = dict(e.memes) if any(e.memes.values()) else {}
            print(f"  {e.id:8} ({e.type:7}) meters={m} memes={me}")
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
        print(f"{len(triples)} compatible combos ({len(stories)} with gender):\n")
        for place, prob, ant in triples:
            genders = sorted(g for (pl, pr, a, g) in stories if (pl, pr, a) == (place, prob, ant))
            print(f"  {place:9} {prob:12} {ant:12}  [{', '.join(genders)}]")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples = []
    if args.all:
        # Curated set
        curated = [
            StoryParams("attic", "wheel", "train", "Sam", "boy", "grandfather", "careful"),
            StoryParams("workshop", "crack", "music_box", "Lily", "girl", "grandmother", "patient"),
            StoryParams("garden_shed", "dusty_spring", "lamp", "Ben", "boy", "grandfather", "resourceful"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as e:
                print(e)
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
            header = f"### {p.name}: fixing {p.antique} ({p.problem}) at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i+1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
