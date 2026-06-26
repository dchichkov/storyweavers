#!/usr/bin/env python3
"""
storyworlds/worlds/cafe_transform_plain_conflict_quest_bad_ending.py
====================================================================

A small bedtime-story world about a cafe, a plain thing, and a child who
wants to transform it on a quest that does not go quite right.

The seed image behind this world:
---
A child visits a quiet cafe and sees a plain little treat on the table.
They want it to transform into something special. A grown-up warns that the
cafe is not the place for loud magic or sticky tricks, but the child begins a
quest anyway. The attempt stirs up conflict, and the ending is a gentle bad
ending: the plain thing is left messy, the special change does not happen, and
the child goes home still thinking about what they tried.

World model sketch:
---
    plain_item.meters["plain"] high     -> the item looks ordinary
    questing child.memes["desire"] high -> they keep wanting the change
    risky transform in the cafe         -> item.meters["messy"] rises
    adult warning + child ignores it     -> child.memes["conflict"] rises
    failed transformation               -> item.meters["broken"] rises
    bad ending                          -> child.memes["sad"] rises; plain item remains plain or becomes ruined
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
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "mom", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "dad", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the cafe"
    quiet: bool = True
    affords: set[str] = field(default_factory=set)


@dataclass
class Quest:
    id: str
    verb: str
    noun: str
    goal: str
    risk: str
    outcome: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Target:
    label: str
    phrase: str
    type: str
    owner: Optional[str] = None
    plural: bool = False
    genders: set[str] = field(default_factory=lambda: {"girl", "boy"})


@dataclass
class Tool:
    id: str
    label: str
    prep: str
    tail: str
    helps: set[str]


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


# Registries
SETTINGS = {
    "cafe": Setting(place="the cafe", quiet=True, affords={"transform"}),
    "bakery": Setting(place="the bakery corner", quiet=True, affords={"transform"}),
}

QUESTS = {
    "transform": Quest(
        id="transform",
        verb="transform",
        noun="plain",
        goal="make it look special",
        risk="too much fuss in a quiet place",
        outcome="the change might fail and make a mess",
        tags={"transform", "plain"},
    ),
}

TARGETS = {
    "cookie": Target(
        label="cookie",
        phrase="a plain little cookie",
        type="cookie",
    ),
    "scone": Target(
        label="scone",
        phrase="a plain scone",
        type="scone",
    ),
    "cupcake": Target(
        label="cupcake",
        phrase="a plain cupcake",
        type="cupcake",
        genders={"girl", "boy"},
    ),
}

TOOLS = [
    Tool(
        id="sprinkles",
        label="a tiny bowl of sprinkles",
        prep="use a tiny bowl of sprinkles",
        tail="the sprinkles tumbled everywhere",
        helps={"transform"},
    ),
    Tool(
        id="icing",
        label="a little spoon of icing",
        prep="use a little spoon of icing",
        tail="the icing slipped and dripped",
        helps={"transform"},
    ),
]

GIRL_NAMES = ["Mia", "Lily", "Nora", "Zoe", "Ella"]
BOY_NAMES = ["Leo", "Finn", "Owen", "Theo", "Max"]
TRAITS = ["curious", "gentle", "spirited", "dreamy", "stubborn"]


@dataclass
class StoryParams:
    place: str
    quest: str
    target: str
    name: str
    gender: str
    adult: str
    trait: str
    seed: Optional[int] = None


def _do_quest(world: World, child: Entity, quest: Quest, target: Entity, tool: Tool) -> None:
    child.memes["desire"] = child.memes.get("desire", 0.0) + 1
    child.meters["restless"] = child.meters.get("restless", 0.0) + 1
    target.meters["plain"] = target.meters.get("plain", 0.0) + 1
    target.meters["messy"] = target.meters.get("messy", 0.0) + 1
    target.meters["broken"] = target.meters.get("broken", 0.0) + 1
    child.memes["conflict"] = child.memes.get("conflict", 0.0) + 1
    child.memes["sad"] = child.memes.get("sad", 0.0) + 1
    world.facts["tool"] = tool
    world.facts["failed"] = True


def tell(setting: Setting, quest: Quest, target_cfg: Target,
         hero_name: str, hero_gender: str, adult_type: str, trait: str) -> World:
    world = World(setting)
    child = world.add(Entity(
        id=hero_name,
        kind="character",
        type=hero_gender,
        meters={"restless": 0.0},
        memes={"desire": 0.0, "conflict": 0.0, "sad": 0.0},
    ))
    adult = world.add(Entity(
        id="Adult",
        kind="character",
        type=adult_type,
        label="the grown-up",
        memes={"worry": 0.0},
    ))
    target = world.add(Entity(
        id="Target",
        type=target_cfg.type,
        label=target_cfg.label,
        phrase=target_cfg.phrase,
        owner=child.id,
        meters={"plain": 1.0},
    ))

    world.say(
        f"{child.id} was a little {trait} {child.type} who liked quiet mornings at {setting.place}."
    )
    world.say(
        f"{child.id} found {target_cfg.phrase} on a plate and wished it could {quest.verb} into something special."
    )
    world.say(
        f"{child.pronoun().capitalize()} loved the idea of a tiny quest, because plain things felt a little lonely to {child.pronoun('object')}."
    )

    world.para()
    world.say(
        f"At {setting.place}, {child.id} whispered to {adult.label} that {target_cfg.label} should {quest.verb}."
    )
    world.say(
        f"{adult.label.capitalize()} worried it would be too much fuss for a quiet cafe, and that the change might turn messy."
    )
    world.say(
        f"{child.id} wanted to try anyway, so the little wish grew into a conflict."
    )

    world.para()
    tool = TOOLS[0] if quest.id == "transform" else TOOLS[-1]
    _do_quest(world, child, quest, target, tool)
    world.say(
        f"{child.id} reached for {tool.label} and tried to {quest.verb} the {target.label}."
    )
    world.say(
        f"But {tool.tail}, and the {target.label} did not become special the way {child.pronoun('subject')} hoped."
    )
    world.say(
        f"In the end, the {target.label} stayed plain in the middle of a small sticky mess."
    )
    world.say(
        f"{child.id} felt sleepy and sad, and {adult.label} gently cleaned up the table while the cafe grew quiet again."
    )

    world.facts.update(
        child=child,
        adult=adult,
        target=target,
        quest=quest,
        setting=setting,
        trait=trait,
        failed=True,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    target = f["target"]
    quest = f["quest"]
    return [
        f'Write a bedtime story about {child.id} at {world.setting.place} and a {target.label} that wants to {quest.verb}.',
        f"Tell a gentle story where a little {child.type} tries to {quest.verb} a plain thing in a cafe and meets a conflict.",
        f'Write a short bedtime tale using the word "plain" and ending with a sad but quiet bad ending.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    adult = f["adult"]
    target = f["target"]
    quest = f["quest"]
    trait = f["trait"]
    return [
        QAItem(
            question=f"What did {child.id} want to do to the {target.label}?",
            answer=f"{child.id} wanted to {quest.verb} the {target.label} so it would not look so plain.",
        ),
        QAItem(
            question=f"Why did {adult.label} worry at {world.setting.place}?",
            answer=f"{adult.label.capitalize()} worried because trying to {quest.verb} a snack in a quiet cafe could make a sticky mess.",
        ),
        QAItem(
            question=f"How did {child.id} feel at the end of the story?",
            answer=f"{child.id} felt sad and tired after the failed quest, even though {child.pronoun('subject')} had tried so hard.",
        ),
        QAItem(
            question=f"What was special about the {target.label} before the quest?",
            answer=f"It was just plain at first: a simple little {target.label} waiting on the plate.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a cafe?",
            answer="A cafe is a place where people sit down, drink warm things, and eat small treats.",
        ),
        QAItem(
            question="What does plain mean?",
            answer="Plain means simple, with not much decoration or fancy detail.",
        ),
        QAItem(
            question="What is a quest?",
            answer="A quest is a goal someone tries to reach, step by step, because they want something very much.",
        ),
        QAItem(
            question="What is a conflict?",
            answer="A conflict is a problem where people want different things and feelings get tense.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== story qa ==")
    for qa in sample.story_qa:
        out.append(f"Q: {qa.question}")
        out.append(f"A: {qa.answer}")
    out.append("")
    out.append("== world qa ==")
    for qa in sample.world_qa:
        out.append(f"Q: {qa.question}")
        out.append(f"A: {qa.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id}: {e.type} {' '.join(bits)}")
    return "\n".join(lines)


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for quest_id in setting.affords:
            for target_id, target in TARGETS.items():
                if target.label in {"cookie", "scone", "cupcake"}:
                    combos.append((place, quest_id, target_id))
    return combos


def explain_rejection(quest: Quest, target: Target) -> str:
    return (
        f"(No story: this world only supports a gentle transform quest for a plain snack "
        f"at the cafe, and {target.label} is the right kind of quiet target.)"
    )


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Bedtime cafe storyworld with a plain transform quest and a bad ending.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--target", choices=TARGETS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--adult", choices=["mother", "father"])
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
    if args.quest and args.target:
        quest = QUESTS[args.quest]
        target = TARGETS[args.target]
        if args.quest == "transform" and target.label not in {"cookie", "scone", "cupcake"}:
            raise StoryError(explain_rejection(quest, target))
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.quest is None or c[1] == args.quest)
              and (args.target is None or c[2] == args.target)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, quest_id, target_id = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    adult = args.adult or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, quest=quest_id, target=target_id, name=name, gender=gender, adult=adult, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], QUESTS[params.quest], TARGETS[params.target],
                 params.name, params.gender, params.adult, params.trait)
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


ASP_RULES = r"""
place(cafe).
place(bakery).
quest(transform).
target(cookie).
target(scone).
target(cupcake).

affords(cafe,transform).
affords(bakery,transform).

plain_target(cookie).
plain_target(scone).
plain_target(cupcake).

valid(Place,Quest,Target) :- affords(Place,Quest), quest(Quest), plain_target(Target), target(Target).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid in SETTINGS:
        lines.append(asp.fact("place", pid))
        for q in SETTINGS[pid].affords:
            lines.append(asp.fact("affords", pid, q))
    for qid in QUESTS:
        lines.append(asp.fact("quest", qid))
    for tid in TARGETS:
        lines.append(asp.fact("target", tid))
        lines.append(asp.fact("plain_target", tid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for place, quest_id, target_id in sorted(valid_combos()):
            p = StoryParams(place=place, quest=quest_id, target=target_id,
                            name="Mia", gender="girl", adult="mother", trait="curious")
            samples.append(generate(p))
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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
