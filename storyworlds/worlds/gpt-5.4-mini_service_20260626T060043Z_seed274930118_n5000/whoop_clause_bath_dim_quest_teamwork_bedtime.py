#!/usr/bin/env python3
"""
storyworlds/worlds/whoop_clause_bath_dim_quest_teamwork_bedtime.py
===================================================================

A small bedtime-story world about a child, a bath-time quest, and a teamwork
compromise.

Premise:
- A child wants to chase a tiny "quest" at bedtime.
- The quest is fun, but it can make the child bath-dim: damp, sleepy, and a
  little messy from splashes.
- A parent worries about wet pajamas and a late night.

Turn:
- The child resists a bedtime clause: "first bath, then quest".
- The parent turns the rule into a teamwork plan.

Resolution:
- They work together: bath first, then a short quest with a towel-cape,
  ending with the child cozy, clean, and proud.

The story intentionally stays small and constraint-checked. The central fix is
not arbitrary: the teamwork plan must genuinely prevent the bath-dim outcome
from ruining bedtime clothes and softness.
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


# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
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
        for k in ("wet", "dirty", "tired", "calm", "joy", "conflict", "helpful", "whoop"):
            self.meters.setdefault(k, 0.0)
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
    place: str = "the bathroom"
    indoors: bool = True
    affords: set[str] = field(default_factory=set)


@dataclass
class Quest:
    id: str
    noun: str
    verb: str
    gerund: str
    spark: str
    splash: str
    keyword: str = "quest"


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
        import copy
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "bathroom": Setting(place="the bathroom", indoors=True, affords={"tub", "foam", "bubble"}),
    "bedroom": Setting(place="the bedroom", indoors=True, affords={"toyquest"}),
}

QUESTS = {
    "tubquest": Quest(
        id="tubquest",
        noun="tub quest",
        verb="follow the tub quest",
        gerund="following the tub quest",
        spark="a shiny bath toy",
        splash="bath-dim",
        keyword="whoop",
    ),
    "toyquest": Quest(
        id="toyquest",
        noun="toy quest",
        verb="search for the tiny toy",
        gerund="searching for the tiny toy",
        spark="a moon-shaped toy",
        splash="bath-dim",
        keyword="clause",
    ),
}

GEAR = [
    Gear(
        id="towelcape",
        label="a towel-cape",
        covers={"torso"},
        guards={"wet"},
        prep="wrap up in a towel-cape first",
        tail="wrapped the towel-cape around the child",
    ),
    Gear(
        id="drypajamas",
        label="dry pajamas",
        covers={"torso", "legs"},
        guards={"wet"},
        prep="change into dry pajamas first",
        tail="pulled on dry pajamas",
        plural=True,
    ),
]

CHILD_NAMES = ["Milo", "Nina", "Toby", "Luna", "Finn", "Maya"]
PARENT_NAMES = ["mom", "dad"]


@dataclass
class StoryParams:
    place: str
    quest: str
    name: str
    gender: str
    parent: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------
def quest_at_risk(quest: Quest) -> bool:
    return True


def select_gear(quest: Quest) -> Optional[Gear]:
    for g in GEAR:
        if "wet" in g.guards:
            return g
    return None


def valid_combos() -> list[tuple[str, str]]:
    return [(place, quest_id) for place in SETTINGS for quest_id in QUESTS]


def explain_rejection(quest: Quest) -> str:
    return f"(No story: the quest would not be safe to narrate with the available bedtime gear.)"


# ---------------------------------------------------------------------------
# Story beats
# ---------------------------------------------------------------------------
def introduce(world: World, child: Entity, quest: Quest) -> None:
    world.say(
        f"{child.id} was a little {child.type} who loved bedtime and also loved a tiny {quest.noun}."
    )
    world.say(
        f"At night, {child.pronoun('subject')} whispered the word {quest.keyword} like a secret spell."
    )


def setup(world: World, child: Entity, parent: Entity, quest: Quest) -> None:
    child.memes["joy"] += 1
    world.say(
        f"One sleepy evening, {child.id} found {quest.spark} and said, "
        f'"Whoop!"'
    )
    world.say(
        f"{child.pronoun('possessive').capitalize()} {parent.label_word} smiled, but pointed to the bath and said, "
        f'"First a bath, then the quest."'
    )
    child.memes["conflict"] += 1


def bath_dim(world: World, child: Entity, quest: Quest) -> None:
    child.meters["wet"] += 1
    child.memes["whoop"] += 1
    world.say(
        f"{child.id} splashed through the water anyway, and soon {child.pronoun('subject')} was bath-dim and giggly."
    )
    world.say(
        f"The tiny {quest.noun} bobbed nearby, but bedtime was getting closer."
    )


def teamwork_plan(world: World, child: Entity, parent: Entity, quest: Quest) -> Gear:
    gear = select_gear(quest)
    if gear is None:
        raise StoryError("No compatible teamwork plan exists for this quest.")
    world.say(
        f"Then {child.pronoun('possessive')} {parent.label_word} made a teamwork plan: {gear.prep}, then look for the {quest.noun} together."
    )
    return gear


def accept(world: World, child: Entity, parent: Entity, quest: Quest, gear: Gear) -> None:
    child.memes["conflict"] = 0
    child.memes["calm"] += 1
    child.memes["joy"] += 1
    gear_ent = world.add(Entity(
        id=gear.id,
        type="gear",
        label=gear.label,
        protective=True,
        covers=set(gear.covers),
        plural=gear.plural,
        owner=child.id,
        caretaker=parent.id,
        worn_by=child.id,
    ))
    world.say(
        f"{child.id} agreed, and together they {gear.tail}."
    )
    world.say(
        f"Hand in hand, they found the {quest.spark}, and the quest felt easier because they shared it."
    )
    world.say(
        f"By the end, {child.id} was dry, sleepy, and smiling, with {gear_ent.label} folded neatly by the bed."
    )


def tell(setting: Setting, quest: Quest, child_name: str = "Milo", child_type: str = "boy", parent_type: str = "mother") -> World:
    world = World(setting)
    child = world.add(Entity(id=child_name, kind="character", type=child_type))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type))
    child.meters["wet"] = 0
    introduce(world, child, quest)
    setup(world, child, parent, quest)
    world.para()
    bath_dim(world, child, quest)
    world.para()
    gear = teamwork_plan(world, child, parent, quest)
    accept(world, child, parent, quest, gear)
    world.facts.update(child=child, parent=parent, quest=quest, gear=gear, resolved=True)
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child, parent, quest = f["child"], f["parent"], f["quest"]
    return [
        f'Write a bedtime story about {child.id}, a whoop, and a small quest that needs teamwork.',
        f"Tell a gentle story where {child.id} wants to {quest.verb} but {parent.label_word} asks for a bath first.",
        f'Write a child-friendly story that uses the words "whoop" and "clause" and ends with everyone cozy in bed.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child, parent, quest = f["child"], f["parent"], f["quest"]
    return [
        QAItem(
            question=f"What did {child.id} want to do before bedtime?",
            answer=f"{child.id} wanted to {quest.verb}, and {quest.keyword} was the silly word {child.pronoun('subject')} kept saying.",
        ),
        QAItem(
            question=f"Why did {parent.label_word} make a bedtime clause about the bath?",
            answer=f"{parent.label_word.capitalize()} wanted the child clean and calm before the quest, so the bath came first.",
        ),
        QAItem(
            question=f"How did the story turn into teamwork?",
            answer=f"{child.id} and {parent.label_word} chose a plan together, so the bath and the quest could both happen safely.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended with {child.id} dry, sleepy, and smiling beside the bed.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a bath for?",
            answer="A bath helps wash off dirt and soap the body clean before bed.",
        ),
        QAItem(
            question="What does teamwork mean?",
            answer="Teamwork means two or more people help each other and share the job.",
        ),
        QAItem(
            question="What does whoop sound like?",
            answer="Whoop is a happy shout, like when something fun and surprising happens.",
        ),
        QAItem(
            question="What does a bedtime clause mean in this story?",
            answer="It means a bedtime rule that says what must happen first, like bath before play.",
        ),
    ]


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
    lines = ["--- world trace ---"]
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
        lines.append(f"  {e.id} ({e.type}) {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
quest_valid(P, Q) :- place(P), quest(Q).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for p in SETTINGS:
        lines.append(asp.fact("place", p))
    for q in QUESTS:
        lines.append(asp.fact("quest", q))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show quest_valid/2."))
    return sorted(set(asp.atoms(model, "quest_valid")))


def asp_verify() -> int:
    import asp
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP matches Python ({len(py)} combos).")
        return 0
    print("MISMATCH")
    if py - cl:
        print("only in python:", sorted(py - cl))
    if cl - py:
        print("only in ASP:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Bedtime story world about whoop, clause, bath-dim, quest, and teamwork.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--parent", choices=PARENT_NAMES)
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
    if args.quest and args.quest not in QUESTS:
        raise StoryError("Unknown quest.")
    combos = valid_combos()
    place = args.place or rng.choice(sorted(SETTINGS))
    quest = args.quest or rng.choice(sorted(QUESTS))
    if (place, quest) not in combos:
        raise StoryError("No valid story for those choices.")
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(CHILD_NAMES)
    parent = args.parent or rng.choice(PARENT_NAMES)
    return StoryParams(place=place, quest=quest, name=name, gender=gender, parent=parent)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], QUESTS[params.quest], params.name, params.gender, params.parent)
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


CURATED = [
    StoryParams(place="bathroom", quest="tubquest", name="Milo", gender="boy", parent="mother"),
    StoryParams(place="bedroom", quest="toyquest", name="Luna", gender="girl", parent="father"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show quest_valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_valid_combos())
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story in seen:
                i += 1
                continue
            seen.add(sample.story)
            samples.append(sample)
            i += 1

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for idx, sample in enumerate(samples):
        header = f"### variant {idx + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
