#!/usr/bin/env python3
"""
storyworlds/worlds/mystery_spill.py
===================================

A standalone story world from the seed:

    Words: compass, spill, forgive
    Features: Reconciliation, Sound Effects, Moral Value
    Style: Mystery

The world models two children solving a small mystery with a clue object. One
child wants to bring a drink or messy handful too close; a friend predicts the
damage by running the world model forward. If the child spills anyway, repair
and forgiveness only happen when the repair actually matches the damage.

Run it
------
    python storyworlds/worlds/mystery_spill.py
    python storyworlds/worlds/mystery_spill.py --all --trace --qa
    python storyworlds/worlds/mystery_spill.py --object compass --spill sand
    python storyworlds/worlds/mystery_spill.py --object compass --spill juice  # rejected
    python storyworlds/worlds/mystery_spill.py --verify
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
DAMAGES = {"stained", "blurred", "jammed"}
MATERIALS = {"paper", "metal", "chalk"}


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    material: str = ""
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        if self.type == "girl":
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type == "boy":
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Setting:
    phrase: str
    affords: set[str]


@dataclass
class ClueObject:
    id: str
    label: str
    phrase: str
    material: str
    purpose: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Spill:
    id: str
    label: str
    carry: str
    sound: str
    affects: dict[str, str]
    tags: set[str] = field(default_factory=set)


@dataclass
class Repair:
    id: str
    label: str
    fixes: set[str]
    materials: set[str]
    action: str
    result: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Rule:
    name: str
    apply: Callable[["World"], list[str]]


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.active_spill: Optional[Spill] = None
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

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
        clone.active_spill = self.active_spill
        clone.paragraphs = [[]]
        return clone


def _r_spill_damages_object(world: World) -> list[str]:
    if world.active_spill is None:
        return []
    spill = world.active_spill
    clue = world.get("Clue")
    damage = spill.affects.get(clue.material)
    if damage is None:
        return []
    sig = ("damage", spill.id, clue.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    clue.meters[damage] += 1
    friend = world.get(clue.owner or "")
    friend.memes["upset"] += 1
    return [
        f"{spill.sound} The {spill.label} landed on {clue.label}, "
        f"and {clue.label} became {damage}."
    ]


def _r_damage_blocks_mystery(world: World) -> list[str]:
    clue = world.get("Clue")
    if not any(clue.meters[d] >= THRESHOLD for d in DAMAGES):
        return []
    sig = ("blocked", clue.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    clue.meters["hard_to_use"] += 1
    return [f"Now the mystery was harder to solve."]


def _r_repair_restores_trust(world: World) -> list[str]:
    clue = world.get("Clue")
    friend = world.get(clue.owner or "")
    if clue.meters["repaired"] < THRESHOLD or friend.memes["apology"] < THRESHOLD:
        return []
    sig = ("forgive", friend.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    friend.memes["upset"] = 0.0
    friend.memes["forgive"] += 1
    return [f"{friend.id} forgave the mistake, and the mystery team felt whole again."]


CAUSAL_RULES = [
    Rule("spill_damages_object", _r_spill_damages_object),
    Rule("damage_blocks_mystery", _r_damage_blocks_mystery),
    Rule("repair_restores_trust", _r_repair_restores_trust),
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
        for sent in produced:
            world.say(sent)
    return produced


def damage_for(spill: Spill, clue: ClueObject) -> Optional[str]:
    return spill.affects.get(clue.material)


def select_repair(spill: Spill, clue: ClueObject) -> Optional[Repair]:
    damage = damage_for(spill, clue)
    if damage is None:
        return None
    for repair in REPAIRS:
        if damage in repair.fixes and clue.material in repair.materials:
            return repair
    return None


def spill_near(world: World, spill: Spill, narrate: bool = True) -> None:
    world.active_spill = spill
    propagate(world, narrate=narrate)


def predict_spill(world: World, spill: Spill) -> dict:
    sim = world.copy()
    spill_near(sim, spill, narrate=False)
    clue = sim.get("Clue")
    damage = next((d for d in DAMAGES if clue.meters[d] >= THRESHOLD), None)
    return {"damaged": damage is not None, "damage": damage}


def introduce(world: World, hero: Entity, friend: Entity, clue: Entity,
              clue_cfg: ClueObject) -> None:
    world.say(
        f"Once upon a time, {hero.id} and {friend.id} were solving a tiny mystery "
        f"near {world.setting.phrase}."
    )
    world.say(
        f"They used {clue.phrase} to {clue_cfg.purpose}, and {friend.id} guarded it carefully."
    )


def wants_to_carry(world: World, hero: Entity, spill: Spill) -> None:
    hero.memes["desire"] += 1
    world.say(f"{hero.id} wanted to {spill.carry} while they searched.")


def warn(world: World, hero: Entity, friend: Entity, spill: Spill, clue: Entity) -> bool:
    prediction = predict_spill(world, spill)
    if not prediction["damaged"]:
        return False
    world.facts["predicted_damage"] = prediction["damage"]
    world.say(
        f'"Careful," {friend.id} said. "If it spills, {clue.label} will get '
        f'{prediction["damage"]}, and we may lose the clue."'
    )
    return True


def ignore_warning(world: World, hero: Entity, spill: Spill) -> None:
    hero.memes["careless"] += 1
    world.say(f"{hero.id} nodded, but {hero.pronoun()} kept {spill.carry.split(' ', 1)[-1]} close.")


def actual_spill(world: World, hero: Entity, spill: Spill) -> None:
    hero.memes["regret"] += 1
    world.say(f"Then {hero.id} slipped.")
    spill_near(world, spill, narrate=True)


def apologize(world: World, hero: Entity, friend: Entity) -> None:
    friend.memes["apology"] += 1
    hero.memes["honesty"] += 1
    world.say(
        f'"I am sorry," {hero.id} said. "I should have listened."'
    )


def repair_clue(world: World, hero: Entity, friend: Entity, repair: Repair,
                clue: Entity) -> None:
    repaired_damage = next((d for d in DAMAGES if clue.meters[d] >= THRESHOLD), "")
    repair_label = repair.action.format(hero=hero.id, friend=friend.id, clue=clue.label)
    world.say(repair_label)
    for damage in DAMAGES:
        clue.meters[damage] = 0.0
    clue.meters["hard_to_use"] = 0.0
    clue.meters["repaired"] += 1
    world.facts["repaired_damage"] = repaired_damage
    result = repair.result.format(hero=hero.id, friend=friend.id, clue=clue.label)
    world.say(result[:1].upper() + result[1:])
    propagate(world, narrate=True)


def moral(world: World, hero: Entity) -> None:
    world.say(
        f"{hero.id} learned that saying sorry and fixing the harm mattered more than being right. "
        "Soon the clue was back in the mystery pile, and the two friends bent over it together."
    )


def tell(setting: Setting, clue_cfg: ClueObject, spill: Spill, hero_name: str,
         hero_type: str, friend_name: str) -> World:
    repair = select_repair(spill, clue_cfg)
    if repair is None:
        raise StoryError(explain_rejection(setting, spill, clue_cfg))
    world = World(setting)
    hero = world.add(Entity(hero_name, kind="character", type=hero_type, label=hero_name))
    friend_type = "girl" if hero_type == "boy" else "boy"
    friend = world.add(Entity(friend_name, kind="character", type=friend_type, label=friend_name))
    clue = world.add(Entity("Clue", type=clue_cfg.id, label=clue_cfg.label,
                            phrase=clue_cfg.phrase, material=clue_cfg.material,
                            owner=friend.id))

    introduce(world, hero, friend, clue, clue_cfg)
    world.para()
    wants_to_carry(world, hero, spill)
    warn(world, hero, friend, spill, clue)
    ignore_warning(world, hero, spill)
    actual_spill(world, hero, spill)
    world.para()
    apologize(world, hero, friend)
    repair_clue(world, hero, friend, repair, clue)
    moral(world, hero)
    world.facts.update(hero=hero, friend=friend, clue=clue, clue_cfg=clue_cfg,
                       spill=spill, repair=repair, setting=setting)
    return world


SETTINGS = {
    "porch": Setting("the back porch", {"map", "notebook", "compass"}),
    "treehouse": Setting("the treehouse steps", {"map", "clue_card", "compass"}),
    "garden": Setting("the garden path", {"map", "clue_card", "chalk_arrow"}),
    "dock": Setting("the little dock", {"compass", "notebook"}),
}

OBJECTS = {
    "map": ClueObject("map", "the map", "a hand-drawn map", "paper",
                      "follow the mystery trail", {"map", "paper"}),
    "notebook": ClueObject("notebook", "the notebook", "a clue notebook", "paper",
                           "write down every clue", {"notebook", "paper"}),
    "clue_card": ClueObject("clue_card", "the clue card", "a chalky clue card", "chalk",
                            "read the next secret mark", {"chalk", "clue"}),
    "chalk_arrow": ClueObject("chalk_arrow", "the chalk arrow", "a chalk arrow on a slate", "chalk",
                              "see which way to go", {"chalk", "clue"}),
    "compass": ClueObject("compass", "the compass", "a little brass compass", "metal",
                          "find north", {"compass", "metal"}),
}

SPILLS = {
    "juice": Spill("juice", "juice", "carry a cup of berry juice", "Splish!",
                   {"paper": "stained", "chalk": "blurred"}, {"juice", "stain"}),
    "water": Spill("water", "water", "carry a cup of water", "Plip-plop!",
                   {"paper": "blurred", "chalk": "blurred"}, {"water", "blur"}),
    "cocoa": Spill("cocoa", "cocoa", "carry warm cocoa", "Slosh!",
                   {"paper": "stained"}, {"cocoa", "stain"}),
    "sand": Spill("sand", "sand", "carry a handful of sand", "Scritch-scratch!",
                  {"metal": "jammed"}, {"sand", "compass"}),
}

REPAIRS = [
    Repair("blot", "a dry towel", {"stained", "blurred"}, {"paper"},
           "{hero} and {friend} gently blotted {clue} with a dry towel.",
           "{clue} was readable again.", {"towel", "paper"}),
    Repair("redraw", "fresh chalk", {"blurred"}, {"chalk"},
           "{hero} held the card still while {friend} redrew {clue}.",
           "{clue} was clear again.", {"chalk", "teamwork"}),
    Repair("brush", "a soft brush", {"jammed"}, {"metal"},
           "{hero} used a soft brush to sweep sand from {clue}.",
           "{clue} spun freely again.", {"brush", "compass"}),
]

GIRL_NAMES = ["Lina", "Maya", "Nora", "Zoe", "Ava", "Rose"]
BOY_NAMES = ["Ben", "Eli", "Theo", "Max", "Sam", "Finn"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for object_id in setting.affords:
            clue = OBJECTS[object_id]
            for spill_id, spill in SPILLS.items():
                if damage_for(spill, clue) and select_repair(spill, clue):
                    combos.append((place, object_id, spill_id))
    return sorted(combos)


@dataclass
class StoryParams:
    place: str
    object: str
    spill: str
    hero: str
    gender: str
    friend: str
    seed: Optional[int] = None


KNOWLEDGE = {
    "compass": [("What does a compass do?",
                 "A compass points toward north, which can help people find directions.")],
    "metal": [("Why can sand jam small metal tools?",
               "Tiny grains of sand can get into moving parts and stop them from turning smoothly.")],
    "paper": [("Why can paper be damaged by spills?",
               "Paper soaks up liquid, so words and drawings can smear or tear.")],
    "chalk": [("Why does chalk blur with water?",
               "Chalk is powdery, so water can spread it and make the marks fuzzy.")],
    "water": [("Why should water stay away from clues on paper?",
               "Water can blur ink or pencil marks, making clues harder to read.")],
    "stain": [("What is a stain?",
               "A stain is a mark left behind when color or dirt soaks into something.")],
    "forgive": [("What does forgive mean?",
                 "To forgive means to stop being angry after someone is sorry and tries to make things right.")],
    "teamwork": [("Why does teamwork help solve problems?",
                  "Teamwork lets people share ideas and fix mistakes together.")],
}
KNOWLEDGE_ORDER = ["compass", "metal", "paper", "chalk", "water", "stain",
                   "forgive", "teamwork"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, clue, spill = f["hero"], f["clue_cfg"], f["spill"]
    return [
        'Write a mystery story for young children using the words "compass", '
        '"spill", and "forgive".',
        f"Tell a reconciliation story where {hero.id} spills {spill.label} on "
        f"{clue.phrase} and repairs the mistake.",
        "Write a short moral story with sound effects where an apology leads to forgiveness.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero, friend, clue, spill, repair = (
        f["hero"], f["friend"], f["clue_cfg"], f["spill"], f["repair"]
    )
    predicted = f.get("predicted_damage", "damaged")
    fixed = f.get("repaired_damage", predicted)
    return [
        ("Who is the story about?",
         f"It is about {hero.id} and {friend.id}, who were solving a tiny mystery."),
        ("What clue object did they use?",
         f"They used {clue.phrase} to {clue.purpose}."),
        (f"What went wrong with {clue.label}?",
         f"{hero.id} spilled {spill.label} with the sound {spill.sound} {clue.label.capitalize()} became {fixed}."),
        ("How did the warning predict the problem?",
         f"{friend.id} warned that if the {spill.label} spilled, {clue.label} would get {predicted} and they might lose the clue."),
        ("How did they fix the mistake?",
         f"They used {repair.label} to repair {clue.label}. Then {friend.id} forgave {hero.id}, and the mystery team could keep working together."),
        (f"What did {hero.id} learn?",
         f"{hero.id} learned that saying sorry and fixing the harm mattered more than being right. The repaired clue mattered, but the repaired friendship mattered too."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = set(f["clue_cfg"].tags) | set(f["spill"].tags) | set(f["repair"].tags)
    tags.add("forgive")
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
            out.extend(KNOWLEDGE[tag])
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, prompt in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {prompt}")
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
    for ent in world.entities.values():
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if ent.material:
            bits.append(f"material={ent.material}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:8} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams("porch", "map", "juice", "Lina", "girl", "Ben"),
    StoryParams("treehouse", "clue_card", "water", "Theo", "boy", "Maya"),
    StoryParams("dock", "compass", "sand", "Nora", "girl", "Sam"),
    StoryParams("garden", "chalk_arrow", "juice", "Finn", "boy", "Ava"),
    StoryParams("porch", "notebook", "cocoa", "Rose", "girl", "Eli"),
]


def explain_rejection(setting: Setting, spill: Spill, clue: ClueObject) -> str:
    if clue.id not in setting.affords:
        return (f"(No story: {setting.phrase} does not use {clue.phrase}, "
                "so that mystery setup is not available.)")
    if damage_for(spill, clue) is None:
        return (f"(No story: {spill.label} would not plausibly damage "
                f"{clue.phrase} ({clue.material}), so there is no honest conflict.)")
    return (f"(No story: the repair catalog cannot fix {damage_for(spill, clue)} "
            f"damage on {clue.material}.)")


ASP_RULES = r"""
damages(S, O, D) :- affects(S, M, D), material(O, M).
has_repair(O, D) :- material(O, M), fixes(R, D), repair_material(R, M).
valid(P, O, S) :- affords(P, O), damages(S, O, D), has_repair(O, D).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for material in sorted(MATERIALS):
        lines.append(asp.fact("material_kind", material))
    for damage in sorted(DAMAGES):
        lines.append(asp.fact("damage_kind", damage))
    for place, setting in SETTINGS.items():
        lines.append(asp.fact("setting", place))
        for object_id in sorted(setting.affords):
            lines.append(asp.fact("affords", place, object_id))
    for object_id, clue in OBJECTS.items():
        lines.append(asp.fact("object", object_id))
        lines.append(asp.fact("material", object_id, clue.material))
    for spill_id, spill in SPILLS.items():
        lines.append(asp.fact("spill", spill_id))
        for material, damage in sorted(spill.affects.items()):
            lines.append(asp.fact("affects", spill_id, material, damage))
    for repair in REPAIRS:
        lines.append(asp.fact("repair", repair.id))
        for damage in sorted(repair.fixes):
            lines.append(asp.fact("fixes", repair.id, damage))
        for material in sorted(repair.materials):
            lines.append(asp.fact("repair_material", repair.id, material))
    return "\n".join(lines)


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
        description="Story world sketch: compass, spill, forgive. "
                    "Unspecified choices are picked at random (seeded).")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--object", choices=OBJECTS)
    ap.add_argument("--spill", choices=SPILLS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--hero")
    ap.add_argument("--friend")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None,
                    help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible combos from clingo")
    ap.add_argument("--verify", action="store_true",
                    help="check the inline ASP gate matches valid_combos()")
    ap.add_argument("--show-asp", action="store_true",
                    help="print the full ASP program (facts + inline rules)")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.object and args.spill:
        combo = (args.place, args.object, args.spill)
        if combo not in valid_combos():
            raise StoryError(explain_rejection(SETTINGS[args.place], SPILLS[args.spill],
                                               OBJECTS[args.object]))
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.object is None or c[1] == args.object)
              and (args.spill is None or c[2] == args.spill)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, object_id, spill_id = rng.choice(combos)
    gender = args.gender or rng.choice(["girl", "boy"])
    names = GIRL_NAMES if gender == "girl" else BOY_NAMES
    friend_names = BOY_NAMES if gender == "girl" else GIRL_NAMES
    hero = args.hero or rng.choice(names)
    friend = args.friend or rng.choice([n for n in friend_names if n != hero])
    return StoryParams(place, object_id, spill_id, hero, gender, friend)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], OBJECTS[params.object], SPILLS[params.spill],
                 params.hero, params.gender, params.friend)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
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
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, object, spill) combos:\n")
        for place, object_id, spill_id in combos:
            print(f"  {place:10} {object_id:12} {spill_id}")
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
            header = f"### {p.hero}: {p.object} + {p.spill} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
