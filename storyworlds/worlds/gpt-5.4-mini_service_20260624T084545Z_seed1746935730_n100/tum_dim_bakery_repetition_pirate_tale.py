#!/usr/bin/env python3
"""
Storyworld: tum-dim bakery repetition pirate tale.

A small classical simulation about a bakery where a pirate-minded child hears a
repeated tum-dim sound, follows the rhythm, and helps turn a messy worry into a
happy bake.
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

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
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
class World:
    setting: str
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

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


@dataclass
class StoryParams:
    name: str
    gender: str
    parent: str
    treat: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTING = "the bakery"

TUM_DIM_STEPS = ["tum-dim", "tum-dim", "tum-dim"]


@dataclass
class Activity:
    id: str
    noun: str
    verb: str
    gerund: str
    sound: str
    mess: str
    risk: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    id: str
    label: str
    phrase: str
    region: str
    plural: bool = False
    genders: set[str] = field(default_factory=lambda: {"girl", "boy"})


@dataclass
class Gear:
    id: str
    label: str
    prep: str
    tail: str
    protects: set[str]
    guards: set[str]
    plural: bool = False


ACTIVITY = Activity(
    id="treats",
    noun="treats",
    verb="make sweet buns",
    gerund="making sweet buns",
    sound="tum-dim",
    mess="floury",
    risk="floury and dusty",
    tags={"bakery", "tum-dim", "repetition"},
)

PRIZES = {
    "apron": Prize(
        id="apron",
        label="apron",
        phrase="a clean white apron",
        region="torso",
        genders={"girl", "boy"},
    ),
    "cap": Prize(
        id="cap",
        label="cap",
        phrase="a neat baker's cap",
        region="head",
        genders={"girl", "boy"},
    ),
    "coat": Prize(
        id="coat",
        label="coat",
        phrase="a little blue coat",
        region="torso",
        genders={"girl", "boy"},
    ),
}

GEAR = [
    Gear(
        id="sleeves",
        label="long sleeves",
        prep="roll up the sleeves and tie on an old baking apron",
        tail="rolled up the sleeves and tied on the old apron",
        protects={"torso"},
        guards={"floury"},
    ),
    Gear(
        id="cap_cover",
        label="a flour cover",
        prep="set on a flour cover and tuck the cap away",
        tail="set on the flour cover and tucked the cap away",
        protects={"head"},
        guards={"floury"},
    ),
]

GIRL_NAMES = ["Mia", "Lily", "Nora", "Ava", "Zoe", "Ella"]
BOY_NAMES = ["Finn", "Leo", "Theo", "Max", "Sam", "Ben"]
TRAITS = ["brave", "curious", "cheery", "spirited"]


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------

def prize_at_risk(activity: Activity, prize: Prize) -> bool:
    return prize.region in {"torso", "head"} and activity.mess == "floury"


def select_gear(activity: Activity, prize: Prize) -> Optional[Gear]:
    for gear in GEAR:
        if activity.mess in gear.guards and prize.region in gear.protects:
            return gear
    return None


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    if prize_at_risk(ACTIVITY, PRIZES["apron"]) and select_gear(ACTIVITY, PRIZES["apron"]):
        combos.append(("bakery", "treats", "apron"))
    if prize_at_risk(ACTIVITY, PRIZES["cap"]) and select_gear(ACTIVITY, PRIZES["cap"]):
        combos.append(("bakery", "treats", "cap"))
    if prize_at_risk(ACTIVITY, PRIZES["coat"]) and select_gear(ACTIVITY, PRIZES["coat"]):
        combos.append(("bakery", "treats", "coat"))
    return combos


# ---------------------------------------------------------------------------
# Narrative mechanics
# ---------------------------------------------------------------------------

def _activity_loop(world: World, hero: Entity) -> list[str]:
    out = []
    if world.facts.get("baking_started"):
        return out
    world.facts["baking_started"] = True
    for step in TUM_DIM_STEPS:
        hero.meters["tum_dim"] = hero.meters.get("tum_dim", 0.0) + 1.0
        world.facts["repetition_count"] = world.facts.get("repetition_count", 0) + 1
        out.append(step)
    hero.memes["joy"] = hero.memes.get("joy", 0.0) + 1.0
    hero.meters["floury"] = hero.meters.get("floury", 0.0) + 1.0
    return out


def _mess_rule(world: World, hero: Entity, prize: Entity) -> list[str]:
    out = []
    if hero.meters.get("floury", 0.0) < THRESHOLD:
        return out
    if prize.worn_by != hero.id:
        return out
    sig = ("mess", prize.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    prize.meters["floury"] = prize.meters.get("floury", 0.0) + 1.0
    out.append(f"The flour puffed up and got on {hero.pronoun('possessive')} {prize.label}.")
    return out


def _resolve_rule(world: World, hero: Entity, prize: Entity, gear: Gear) -> list[str]:
    out = []
    if hero.memes.get("conflict", 0.0) < THRESHOLD:
        return out
    if world.facts.get("resolved"):
        return out
    world.facts["resolved"] = True
    hero.memes["conflict"] = 0.0
    hero.memes["love"] = hero.memes.get("love", 0.0) + 1.0
    out.append(f"{hero.pronoun().capitalize()} smiled again when the safe plan came.")
    out.append(f"They {gear.tail}, and the bakery smelled sweet and calm.")
    return out


def propagate(world: World, hero: Entity, prize: Entity, gear: Optional[Gear], narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for sent in _activity_loop(world, hero):
            produced.append(sent)
            changed = True
        for sent in _mess_rule(world, hero, prize):
            produced.append(sent)
            changed = True
        if gear is not None:
            for sent in _resolve_rule(world, hero, prize, gear):
                produced.append(sent)
                changed = True
    if narrate:
        for s in produced:
            if s:
                world.say(s)
    return produced


def predict_mess(hero: Entity, prize: Entity) -> bool:
    return hero.meters.get("floury", 0.0) >= THRESHOLD and prize.worn_by == hero.id


def tell(name: str, gender: str, parent: str, treat: str) -> World:
    world = World(setting=SETTING)
    hero = world.add(Entity(id=name, kind="character", type=gender, meters={}, memes={}))
    parent_ent = world.add(Entity(id="Parent", kind="character", type=parent, label=f"the {parent}"))
    prize = world.add(Entity(
        id="prize",
        type=treat,
        label=PRIZES[treat].label,
        phrase=PRIZES[treat].phrase,
        owner=hero.id,
        caretaker=parent_ent.id,
        worn_by=hero.id,
        plural=PRIZES[treat].plural,
        meters={},
        memes={},
    ))

    gear_def = select_gear(ACTIVITY, PRIZES[treat])
    if gear_def is None:
        raise StoryError("No safe baking gear exists for this prize.")

    world.say(f"{name} was a little {gender} pirate in {SETTING}, and {name} loved the sweet tum-dim sound.")
    world.say(f"{name} liked the repeat of {ACTIVITY.sound}, repeat of {ACTIVITY.sound}, repeat of {ACTIVITY.sound}, because it meant the ovens were busy.")
    world.say(f"One day, {name} and {parent_ent.label} went to {SETTING}.")
    world.para()
    world.say(f"{name} wanted to {ACTIVITY.verb}, but {parent_ent.label} pointed at {prize.phrase} and frowned.")
    if predict_mess(hero, prize) or True:
        world.say(f'"If you hop into the {ACTIVITY.noun}, your {prize.label} will get {ACTIVITY.risk}," said {parent_ent.label}.')
    hero.memes["conflict"] = 1.0
    world.say(f"{name} tried to dash toward the bowls anyway, but {parent_ent.label} held up a steady hand.")
    world.para()
    world.say(f"Then {parent_ent.label} said, \"How about we {gear_def.prep} and still {ACTIVITY.verb}?\"")
    propagate(world, hero, prize, gear_def, narrate=True)
    world.say(f"So {name} helped make the buns, listening to tum-dim, tum-dim, tum-dim, until the tray was full.")
    world.say(f"At the end, {name}'s {prize.label} stayed clean, and the bakery smelled warm and sweet.")
    world.facts.update(
        hero=hero,
        parent=parent_ent,
        prize=prize,
        activity=ACTIVITY,
        gear=gear_def,
        resolved=True,
        conflict=True,
        setting=SETTING,
        treat=treat,
        gender=gender,
        name=name,
        parent_type=parent,
    )
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    parent = f["parent"]
    prize = f["prize"]
    return [
        f'Write a pirate-style story for a young child set in a bakery where "{ACTIVITY.sound}" is heard again and again.',
        f"Tell a gentle story about {hero.id}, {hero.pronoun('possessive')} {parent.label}, and a {prize.label} staying clean while sweet buns are made.",
        f'Write a short repetition story that includes "tum-dim" and ends with a happy baking compromise in {SETTING}.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    parent = f["parent"]
    prize = f["prize"]
    gear = f["gear"]
    qa = [
        QAItem(
            question=f"What kind of place was {hero.id} in when the tum-dim sound started?",
            answer=f"{hero.id} was in {SETTING}, where sweet buns were being made.",
        ),
        QAItem(
            question=f"What did {hero.id} want to do before {parent.label} worried about the {prize.label}?",
            answer=f"{hero.id} wanted to {ACTIVITY.verb}.",
        ),
        QAItem(
            question=f"Why did {parent.label} worry about {hero.id}'s {prize.label}?",
            answer=f"{parent.label} worried because the flour could make the {prize.label} get {ACTIVITY.risk}.",
        ),
        QAItem(
            question=f"What safe plan helped {hero.id} keep baking?",
            answer=f"They used {gear.label}, so {hero.id} could keep helping without ruining the {prize.label}.",
        ),
        QAItem(
            question=f"How did {hero.id} feel at the end?",
            answer=f"{hero.id} felt happy, and the story ends with {hero.id} helping the buns while the {prize.label} stayed clean.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does repetition mean in a story?",
            answer="Repetition means saying or doing something again and again. It can make a story feel steady, musical, or easy to remember.",
        ),
        QAItem(
            question="Why do bakers use flour?",
            answer="Bakers use flour to make bread, buns, and other doughy foods. Flour helps the dough become soft and ready to bake.",
        ),
        QAItem(
            question="What does tum-dim sound like?",
            answer="Tum-dim sounds like a quick, bouncy beat, almost like little taps or a spoon knocking against a bowl.",
        ),
    ]


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
        if e.label:
            bits.append(f"label={e.label}")
        lines.append(f"  {e.id:8} ({e.kind:9}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(world.fired)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
activity(treats).
setting(bakery).

sound(treats,tum_dim).
repeats(treats,tum_dim).

mess_of(treats,floury).
risk(treats,floury).

prize(apron). worn_on(apron,torso).
prize(cap). worn_on(cap,head).
prize(coat). worn_on(coat,torso).

gear(sleeves). guards(sleeves,floury). covers(sleeves,torso).
gear(cap_cover). guards(cap_cover,floury). covers(cap_cover,head).

prize_at_risk(A,P) :- risk(A,_), worn_on(P,R), R = torso.
prize_at_risk(A,P) :- risk(A,_), worn_on(P,R), R = head.

protects(G,A,P) :- prize_at_risk(A,P), mess_of(A,M), guards(G,M), worn_on(P,R), covers(G,R).
has_fix(A,P) :- protects(_,A,P).
valid_story(bakery,treats,P) :- prize_at_risk(treats,P), has_fix(treats,P).

#show valid_story/3.
"""


def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("activity", "treats"),
        asp.fact("setting", "bakery"),
        asp.fact("sound", "treats", "tum_dim"),
        asp.fact("repeats", "treats", "tum_dim"),
        asp.fact("mess_of", "treats", "floury"),
        asp.fact("risk", "treats", "floury"),
    ]
    for pid, pr in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("worn_on", pid, pr.region))
    for gear in GEAR:
        lines.append(asp.fact("gear", gear.id))
        for m in sorted(gear.guards):
            lines.append(asp.fact("guards", gear.id, m))
        for r in sorted(gear.protects):
            lines.append(asp.fact("covers", gear.id, r))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


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


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Storyworld: tum-dim bakery repetition pirate tale.")
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--prize", choices=PRIZES)
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
    prize = args.prize or rng.choice(sorted(PRIZES))
    gender = args.gender or rng.choice(sorted(PRIZES[prize].genders))
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(name=name, gender=gender, parent=parent, treat=prize)


def generate(params: StoryParams) -> StorySample:
    world = tell(params.name, params.gender, params.parent, params.treat)
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
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible story combos:\n")
        for item in combos:
            print(" ", item)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for prize in sorted(PRIZES):
            params = StoryParams(
                name="Mia" if prize != "cap" else "Finn",
                gender="girl" if prize != "cap" else "boy",
                parent="mother",
                treat=prize,
            )
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            i += 1

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
