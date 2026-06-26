#!/usr/bin/env python3
"""
storyworlds/worlds/permission_behavior_builder_kindness_twist_nursery_rhyme.py
================================================================================

A tiny storyworld about permission, behavior, and a builder, told in a gentle
nursery-rhyme style with a kindness twist.

Seed premise:
- A small builder wants to make something lovely.
- Permission depends on behavior.
- Kindness changes the outcome.
- The ending image proves what changed.

This script keeps a simple classical simulation: a child-sized builder, a
caregiver, a shared building place, a fragile prize, and a helpful twist that
turns a no into a yes.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import re
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
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    indoor: bool = True
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
    keyword: str
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
        return any(region in g.meters.get("covers", []) for g in self.worn_items(actor))

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


def _meter(ent: Entity, key: str) -> float:
    return ent.meters.get(key, 0.0)


def _meme(ent: Entity, key: str) -> float:
    return ent.memes.get(key, 0.0)


def _add_meter(ent: Entity, key: str, amount: float = 1.0) -> None:
    ent.meters[key] = ent.meters.get(key, 0.0) + amount


def _add_meme(ent: Entity, key: str, amount: float = 1.0) -> None:
    ent.memes[key] = ent.memes.get(key, 0.0) + amount


def _r_mess(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if _meter(actor, "messy") < THRESHOLD:
            continue
        for item in world.worn_items(actor):
            if item.region not in world.zone:
                continue
            sig = ("mess", actor.id, item.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            _add_meter(item, "dirty", 1.0)
            _add_meter(item, "messy", 1.0)
            out.append(f"{actor.id}'s {item.label} got a bit messy.")
    return out


def _r_kindness(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if _meme(actor, "kindness") < THRESHOLD:
            continue
        sig = ("kindness", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        _add_meme(actor, "trust", 1.0)
        out.append(f"Kindness made the air feel warm and mild.")
    return out


CAUSAL_RULES = [_r_mess, _r_kindness]


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


def predict_damage(world: World, actor: Entity, activity: Activity, prize_id: str) -> dict:
    sim = world.copy()
    _do_activity(sim, sim.get(actor.id), activity, narrate=False)
    prize = sim.entities[prize_id]
    return {"dirty": _meter(prize, "dirty") >= THRESHOLD}


def _do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    if activity.id not in world.setting.affords:
        return
    world.zone = set(activity.zone)
    _add_meter(actor, "messy", 1.0)
    _add_meme(actor, "joy", 1.0)
    propagate(world, narrate=narrate)


def select_gear(activity: Activity, prize: Prize) -> Optional[Gear]:
    for gear in GEAR:
        if activity.mess in gear.guards and prize.region in gear.covers:
            return gear
    return None


def prize_at_risk(activity: Activity, prize: Prize) -> bool:
    return prize.region in activity.zone


SETTINGS = {
    "nursery": Setting(place="the nursery", indoor=True, affords={"blocks", "paint", "glue"}),
    "workshop": Setting(place="the little workshop", indoor=True, affords={"blocks", "paint", "glue"}),
}

ACTIVITIES = {
    "blocks": Activity(
        id="blocks",
        verb="build a block house",
        gerund="building a block house",
        rush="run to the block table",
        mess="knocked",
        soil="tumbled",
        zone={"hands"},
        keyword="blocks",
        tags={"build", "kindness"},
    ),
    "paint": Activity(
        id="paint",
        verb="paint a bright sign",
        gerund="painting a bright sign",
        rush="grab the paint pots",
        mess="painted",
        soil="spattered",
        zone={"hands", "torso"},
        keyword="paint",
        tags={"color", "kindness"},
    ),
    "glue": Activity(
        id="glue",
        verb="glue ribbon stars",
        gerund="gluing ribbon stars",
        rush="open the glue jar",
        mess="sticky",
        soil="stuck fast",
        zone={"hands"},
        keyword="glue",
        tags={"sticky", "build"},
    ),
}

PRIZES = {
    "cape": Prize("cape", "a soft little cape", "cape", "torso"),
    "apron": Prize("apron", "a clean apron", "apron", "torso"),
    "sash": Prize("sash", "a bright sash", "sash", "torso"),
}

GEAR = [
    Gear(
        id="smock",
        label="smock",
        covers={"torso"},
        guards={"painted", "sticky"},
        prep="put on the smock first",
        tail="put on the smock and went back again",
    ),
    Gear(
        id="gloves",
        label="gloves",
        covers={"hands"},
        guards={"sticky"},
        prep="slip on the little gloves first",
        tail="slipped on the gloves and tiptoed back again",
    ),
    Gear(
        id="apron",
        label="apron",
        covers={"torso"},
        guards={"knocked", "painted", "sticky"},
        prep="tie on the apron first",
        tail="tied on the apron and came back again",
    ),
]

NAMES = ["Pip", "Milo", "Luna", "Nell", "Bea", "Theo", "Wren", "Finn"]
TRAITS = ["cheery", "tiny", "gentle", "spry", "bright"]


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


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            act = ACTIVITIES[act_id]
            for prize_id, prize in PRIZES.items():
                if prize_at_risk(act, prize) and select_gear(act, prize):
                    combos.append((place, act_id, prize_id))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A nursery-rhyme storyworld about permission and kindness.")
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
        if not prize_at_risk(ACTIVITIES[args.activity], PRIZES[args.prize]):
            raise StoryError("That prize would not be at risk in this activity.")
        if not select_gear(ACTIVITIES[args.activity], PRIZES[args.prize]):
            raise StoryError("No reasonable fix exists for that activity and prize.")
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.activity is None or c[1] == args.activity)
              and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError("No valid combination matches the given options.")
    place, activity, prize = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, activity=activity, prize=prize, name=name, gender=gender, parent=parent, trait=trait)


def tell(setting: Setting, activity: Activity, prize_cfg: Prize, name: str, gender: str, traits: list[str], parent_type: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=name, kind="character", type=gender, traits=traits))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label=f"the {parent_type}"))
    prize = world.add(Entity(id="Prize", type=prize_cfg.type, label=prize_cfg.label, phrase=prize_cfg.phrase, caretaker=parent.id, region=prize_cfg.region))
    hero.worn_by = None
    prize.worn_by = hero.id

    world.say(f"{hero.id} was a {hero.traits[0]} little builder, and {hero.id} liked to build.")
    world.say(f"{hero.pronoun().capitalize()} loved {activity.gerund}, and the day felt light as a cloud.")
    world.say(f"{parent.label_word if hasattr(parent, 'label_word') else 'parent'} had given {hero.id} {hero.pronoun('object')} {prize.phrase}.")
    world.para()
    world.say(f"In {setting.place}, {hero.id} wanted to {activity.verb}, but {hero.pronoun('possessive')} {parent.type} asked for good behavior first.")
    world.say(f"\"Show kind behavior, little builder, and ask for permission,\" said {parent.type}.")
    world.say(f"{hero.id} tried to {activity.rush}, and then stopped to think.")
    hero.memes["behaviour"] = 0.0
    hero.memes["kindness"] = 1.0
    world.say(f"{hero.id} chose kindness instead: {hero.pronoun()} helped tidy the table and asked nicely.")
    world.say(f"That sweet behavior gave {hero.id} permission to begin.")
    world.para()
    gear = select_gear(activity, prize)
    if gear is None:
        raise StoryError("Internal world mismatch: no gear.")
    gear_ent = world.add(Entity(id=gear.id, type="gear", label=gear.label, owner=hero.id, caretaker=parent.id))
    gear_ent.meters["covers"] = list(gear.covers)
    world.say(f"{parent.id} smiled and said, \"{gear.prep.capitalize()}.\"")
    world.say(f"So they {gear.tail}, and {hero.id} could {activity.verb} without harming {prize.label}.")
    world.say(f"Soon {hero.id} was {activity.gerund}, and {prize.label} stayed neat and bright.")
    world.facts.update(hero=hero, parent=parent, prize=prize, prize_cfg=prize_cfg, activity=activity, setting=setting, gear=gear, resolved=True)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    act = f["activity"]
    prize = f["prize_cfg"]
    return [
        f'Write a short nursery-rhyme story about permission, behavior, and a builder named {hero.id}.',
        f"Tell a gentle rhyme where {hero.id} wants to {act.verb}, but good behavior earns permission.",
        f"Write a tiny story that includes the words permission, behavior, builder, kindness, and twist.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, parent, prize, act = f["hero"], f["parent"], f["prize"], f["activity"]
    return [
        QAItem(
            question=f"What did {hero.id} want to do at {world.setting.place}?",
            answer=f"{hero.id} wanted to {act.verb} there.",
        ),
        QAItem(
            question=f"Why did the {parent.type} talk about permission?",
            answer=f"Because {hero.id}'s behavior needed to be kind and calm before the fun could start.",
        ),
        QAItem(
            question=f"What changed after kindness showed up?",
            answer=f"Kindness turned the moment around, so {hero.id} got permission and could keep building while {prize.label} stayed safe.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem("What is permission?", "Permission means someone says it is okay to do something."),
        QAItem("What is behavior?", "Behavior is the way someone acts, like being kind, calm, or rough."),
        QAItem("What does a builder do?", "A builder makes or puts things together."),
        QAItem("What is kindness?", "Kindness means choosing gentle, caring actions."),
        QAItem("What is a twist in a story?", "A twist is a surprising turn that changes what happens next."),
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
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id} ({e.type}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="nursery", activity="blocks", prize="apron", name="Pip", gender="boy", parent="mother", trait="cheery"),
    StoryParams(place="workshop", activity="paint", prize="cape", name="Luna", gender="girl", parent="father", trait="gentle"),
    StoryParams(place="nursery", activity="glue", prize="sash", name="Theo", gender="boy", parent="mother", trait="bright"),
]


ASP_RULES = r"""
prize_at_risk(A, P) :- splashes(A, R), worn_on(P, R).
protects(G, A, P) :- prize_at_risk(A, P), mess_of(A, M), guards(G, M), covers(G, R), worn_on(P, R).
has_fix(A, P) :- protects(_, A, P).
valid(Place, A, P) :- affords(Place, A), prize_at_risk(A, P), has_fix(A, P).
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
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("worn_on", pid, p.region))
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


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH")
    print("python-only:", sorted(py - cl))
    print("clingo-only:", sorted(cl - py))
    return 1


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], ACTIVITIES[params.activity], PRIZES[params.prize], params.name, params.gender, [params.trait, "builder"], params.parent)
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
    if args.verify:
        sys.exit(asp_verify())
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.asp:
        combos = asp_valid_combos()
        for c in combos:
            print(c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
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
            s = generate(params)
            if s.story in seen:
                continue
            seen.add(s.story)
            samples.append(s)

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
