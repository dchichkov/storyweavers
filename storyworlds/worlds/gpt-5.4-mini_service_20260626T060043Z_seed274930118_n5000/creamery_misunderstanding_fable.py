#!/usr/bin/env python3
"""
storyworlds/worlds/creamery_misunderstanding_fable.py
======================================================

A small fable-style story world about a creamery, a misunderstanding, and a
gentle repair. The premise is classical: one character wants something small and
kind, another character misreads the plan, tension grows, and the truth clears
the air.

The world is built from a simulated premise rather than a fixed paragraph:
- a character brings a dairy item to the creamery,
- another character misunderstands the request or the delivery,
- the misunderstanding creates a risky choice or a social bruise,
- a simple explanation resolves the trouble,
- the ending proves what changed.

The story should feel like a short fable: concrete, child-facing, and causal.
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
# Entities
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    traits: list[str] = field(default_factory=list)
    plural: bool = False

    def pronoun(self, case: str = "subject") -> str:
        female = {"cow", "goat", "hen", "girl", "mother", "woman"}
        male = {"bull", "ram", "boy", "father", "man", "donkey"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class Setting:
    place: str
    indoor: bool = True
    affords: set[str] = field(default_factory=set)


@dataclass
class ObjectCfg:
    id: str
    label: str
    phrase: str
    type: str
    region: str
    plural: bool = False


@dataclass
class Action:
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
class Fix:
    id: str
    label: str
    prep: str
    tail: str


@dataclass
class StoryParams:
    place: str
    action: str
    object: str
    name: str
    animal: str
    helper: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------
class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.trace: list[str] = []
        self.misunderstood: bool = False
        self.resolved: bool = False

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)
            self.trace.append(text)

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
        clone.misunderstood = self.misunderstood
        clone.resolved = self.resolved
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "creamery": Setting(place="the creamery", indoor=True, affords={"carry", "clean", "taste"}),
    "yard": Setting(place="the yard", indoor=False, affords={"carry"}),
    "kitchen": Setting(place="the kitchen", indoor=True, affords={"clean", "taste"}),
}

ACTIONS = {
    "carry": Action(
        id="carry",
        verb="carry the cream jug",
        gerund="carrying the cream jug",
        rush="hurry to the shelf",
        mess="spill",
        soil="spilled",
        zone={"floor", "table"},
        keyword="cream",
        tags={"cream", "milk"},
    ),
    "clean": Action(
        id="clean",
        verb="wipe the cream pot",
        gerund="wiping the cream pot",
        rush="dash for the cloth",
        mess="smear",
        soil="smudged",
        zone={"table"},
        keyword="cloth",
        tags={"clean", "cloth"},
    ),
    "taste": Action(
        id="taste",
        verb="taste the fresh cream",
        gerund="tasting the cream",
        rush="lean over the bowl",
        mess="spill",
        soil="dripped",
        zone={"mouth", "table"},
        keyword="cream",
        tags={"cream", "taste"},
    ),
}

OBJECTS = {
    "jug": ObjectCfg(
        id="jug",
        label="cream jug",
        phrase="a shiny cream jug",
        type="jug",
        region="hands",
    ),
    "cloth": ObjectCfg(
        id="cloth",
        label="clean cloth",
        phrase="a clean cloth for the table",
        type="cloth",
        region="hands",
    ),
    "bowl": ObjectCfg(
        id="bowl",
        label="cream bowl",
        phrase="a little cream bowl",
        type="bowl",
        region="table",
    ),
}

FIXES = {
    "explain": Fix(
        id="explain",
        label="a clear explanation",
        prep="stop and explain the plan",
        tail="listened to the truth",
    ),
    "label": Fix(
        id="label",
        label="a label on the jug",
        prep="put a label on the jug",
        tail="read the label together",
    ),
}

ANIMALS = {
    "cow": {"girl", "boy"},
    "goat": {"girl", "boy"},
    "hen": {"girl"},
    "donkey": {"boy", "girl"},
}

GIRL_NAMES = ["Mina", "Nora", "Lina", "Elsa", "Molly", "Pia"]
BOY_NAMES = ["Owen", "Bram", "Theo", "Ari", "Milo", "Finn"]
TRAITS = ["kind", "careful", "curious", "gentle", "patient", "thoughtful"]


# ---------------------------------------------------------------------------
# Reasonableness
# ---------------------------------------------------------------------------
def action_at_risk(action: Action, obj: ObjectCfg) -> bool:
    return obj.region in action.zone or obj.type in {"jug", "bowl", "cloth"}


def select_fix(action: Action, obj: ObjectCfg) -> Optional[Fix]:
    if action.id == "carry" and obj.id in {"jug", "bowl"}:
        return FIXES["label"]
    if action.id in {"clean", "taste"}:
        return FIXES["explain"]
    return None


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            action = ACTIONS[act_id]
            for obj_id, obj in OBJECTS.items():
                if action_at_risk(action, obj) and select_fix(action, obj):
                    out.append((place, act_id, obj_id))
    return out


# ---------------------------------------------------------------------------
# Simulation helpers
# ---------------------------------------------------------------------------
def introduce(world: World, hero: Entity, helper: Entity, obj: Entity) -> None:
    world.say(
        f"{hero.id} was a {hero.traits[0]} {hero.type} who liked to help at {world.setting.place}."
    )
    world.say(
        f"One morning, {hero.id} brought {hero.pronoun('object')} {obj.phrase} to share with {helper.label_word}."
    )


def setup_misunderstanding(world: World, hero: Entity, helper: Entity, action: Action, obj: Entity) -> None:
    hero.memes["hope"] = hero.memes.get("hope", 0) + 1
    helper.memes["worry"] = helper.memes.get("worry", 0) + 1
    world.say(
        f"{hero.id} wanted to {action.verb}, but {helper.id} thought {hero.id} meant to waste the cream."
    )
    world.say(
        f'"Wait," said {helper.id}, "that will make a mess!"'
    )
    world.misunderstood = True


def tension(world: World, hero: Entity, helper: Entity, action: Action, obj: Entity) -> None:
    hero.memes["hurt"] = hero.memes.get("hurt", 0) + 1
    world.say(
        f"{hero.id} felt small and sad, because {hero.pronoun("possessive")} good idea had been mistaken.'
    )
    world.say(
        f"{hero.id} hurried to {action.rush}, and the cream wobbled in {hero.pronoun('possessive')} hands."
    )


def reveal(world: World, hero: Entity, helper: Entity, action: Action, obj: Entity, fix: Fix) -> None:
    world.say(
        f"Then {hero.id} stopped and smiled."
    )
    world.say(
        f'"I only wanted to help," {hero.id} said. "{action.verb} is how I can be useful here."'
    )
    world.say(
        f"{helper.id} saw the truth at last and chose {fix.label}."
    )
    world.say(
        f"They {fix.prep}, and {helper.id} laughed at the mistake instead of frowning at it."
    )
    world.resolved = True


def ending(world: World, hero: Entity, helper: Entity, action: Action, obj: Entity) -> None:
    hero.memes["joy"] = hero.memes.get("joy", 0) + 1
    helper.memes["peace"] = helper.memes.get("peace", 0) + 1
    world.say(
        f"In the end, {hero.id} was {action.gerund}, and {obj.label_word} stayed safe and neat."
    )
    world.say(
        f"{helper.id} learned that a kind plan can look strange before it is explained."
    )


def tell(setting: Setting, action: Action, obj_cfg: ObjectCfg, hero_name: str, animal: str, helper_type: str, trait: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=animal, traits=[trait, "helpful"]))
    helper = world.add(Entity(id="Helper", kind="character", type=helper_type, label="the helper"))
    obj = world.add(Entity(id="Object", type=obj_cfg.type, label=obj_cfg.label, phrase=obj_cfg.phrase))

    world.facts.update(hero=hero, helper=helper, obj=obj, action=action, setting=setting, obj_cfg=obj_cfg)

    introduce(world, hero, helper, obj)
    world.para()
    setup_misunderstanding(world, hero, helper, action, obj)
    tension(world, hero, helper, action, obj)
    world.para()
    fix = select_fix(action, obj_cfg)
    if fix is None:
        raise StoryError("No reasonable fix for this story.")
    reveal(world, hero, helper, action, obj, fix)
    ending(world, hero, helper, action, obj)
    world.facts["fix"] = fix
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, helper, action, obj = f["hero"], f["helper"], f["action"], f["obj_cfg"]
    return [
        f'Write a short fable about a {hero.type} at a creamery where a misunderstanding about {obj.label} causes trouble.',
        f"Tell a gentle animal story in which {hero.id} tries to {action.verb} but {helper.label_word} misreads the plan.",
        f'Write a child-friendly fable that includes the word "creamery" and ends with the misunderstanding being cleared up.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, helper, action, obj = f["hero"], f["helper"], f["action"], f["obj_cfg"]
    return [
        QAItem(
            question=f"Who was the story about at {world.setting.place}?",
            answer=f"It was about {hero.id}, a {hero.type} who came to {world.setting.place} to help.",
        ),
        QAItem(
            question=f"What did {hero.id} want to do with the {obj.label}?",
            answer=f"{hero.id} wanted to {action.verb}, which was meant to be helpful and careful.",
        ),
        QAItem(
            question=f"Why did {helper.id} get upset at first?",
            answer=f"{helper.id} thought {hero.id} was about to make a mess, so {helper.id} misunderstood the plan.",
        ),
        QAItem(
            question=f"How did the misunderstanding end?",
            answer=f"{hero.id} explained the plan, {helper.id} understood, and they chose {f['fix'].label} to clear things up.",
        ),
    ]


WORLD_KNOWLEDGE = {
    "creamery": [
        (
            "What is a creamery?",
            "A creamery is a place where milk and cream are made, stored, or turned into dairy foods.",
        )
    ],
    "cream": [
        (
            "What is cream?",
            "Cream is the rich, smooth part of milk that can be used to make butter, ice cream, or other foods.",
        )
    ],
    "label": [
        (
            "What does a label do?",
            "A label tells people what something is, so they do not mistake it for something else.",
        )
    ],
    "mistake": [
        (
            "What is a misunderstanding?",
            "A misunderstanding happens when someone thinks something means one thing, but it really means another.",
        )
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["action"].tags) | {"creamery", "label", "mistake"}
    out: list[QAItem] = []
    for tag, items in WORLD_KNOWLEDGE.items():
        if tag in tags:
            out.extend(QAItem(question=q, answer=a) for q, a in items)
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
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP
# ---------------------------------------------------------------------------
ASP_RULES = r"""
prize_at_risk(A, O) :- action(A), object(O), action_zone(A, R), object_region(O, R).
needs_fix(A, O) :- prize_at_risk(A, O), has_fix(A, O).
valid(Place, A, O) :- setting(Place), affords(Place, A), needs_fix(A, O).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", pid, a))
    for aid, a in ACTIONS.items():
        lines.append(asp.fact("action", aid))
        for r in sorted(a.zone):
            lines.append(asp.fact("action_zone", aid, r))
    for oid, o in OBJECTS.items():
        lines.append(asp.fact("object", oid))
        lines.append(asp.fact("object_region", oid, o.region))
    for aid, a in ACTIONS.items():
        for oid, o in OBJECTS.items():
            if action_at_risk(a, o) and select_fix(a, o):
                lines.append(asp.fact("has_fix", aid, oid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    return 1


# ---------------------------------------------------------------------------
# Params / generation
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A creamery fable about a misunderstanding.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--action", choices=ACTIONS)
    ap.add_argument("--object", dest="object_", choices=OBJECTS)
    ap.add_argument("--animal", choices=sorted(ANIMALS))
    ap.add_argument("--helper", choices=["cow", "goat", "hen", "donkey"])
    ap.add_argument("--name")
    ap.add_argument("--trait", choices=TRAITS)
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
    place = args.place or rng.choice(list(SETTINGS))
    action_id = args.action or rng.choice(sorted(SETTINGS[place].affords))
    obj_id = args.object_ or rng.choice(list(OBJECTS))
    action = ACTIONS[action_id]
    obj = OBJECTS[obj_id]
    if not action_at_risk(action, obj):
        raise StoryError("That action and object do not create a believable misunderstanding.")
    if select_fix(action, obj) is None:
        raise StoryError("No reasonable fix exists for that action and object.")

    animal = args.animal or rng.choice(list(ANIMALS))
    helper = args.helper or rng.choice(["cow", "goat", "hen", "donkey"])
    if args.trait:
        trait = args.trait
    else:
        trait = rng.choice(TRAITS)

    name = args.name or rng.choice(GIRL_NAMES if animal in {"cow", "goat", "hen"} else BOY_NAMES)
    return StoryParams(place=place, action=action_id, object=obj_id, name=name, animal=animal, helper=helper, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], ACTIONS[params.action], OBJECTS[params.object],
                 params.name, params.animal, params.helper, params.trait)
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


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.traits:
            bits.append(f"traits={e.traits}")
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.label:
            bits.append(f"label={e.label!r}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  misunderstood={world.misunderstood} resolved={world.resolved}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="creamery", action="carry", object="jug", name="Mina", animal="cow", helper="goat", trait="careful"),
    StoryParams(place="creamery", action="clean", object="cloth", name="Owen", animal="donkey", helper="cow", trait="curious"),
    StoryParams(place="kitchen", action="taste", object="bowl", name="Nora", animal="hen", helper="goat", trait="gentle"),
]


def asp_verify_stories() -> int:
    return asp_verify()


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify_stories())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for p, a, o in combos:
            print(f"  {p:10} {a:8} {o:8}")
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
            header = f"### {p.name}: {p.action} at {p.place} (object: {p.object})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
