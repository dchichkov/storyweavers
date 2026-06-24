#!/usr/bin/env python3
"""
hydro_cautionary_slice_of_life.py
=================================

A small cautionary slice-of-life story world about a child, a sunny day,
and the steady relief of bringing hydro along before play.

The core premise:
- A child wants to go out and have fun right away.
- A parent notices the day is hot and cautions that water is needed.
- If the child ignores the warning, thirst rises and the outing feels worse.
- A sensible compromise is to fill the hydro bottle first, then continue.

This world keeps the simulation tiny and state-driven: physical meters track
thirst, heat, and water; emotional memes track worry, impatience, and relief.
The story text is authored from the evolving world state rather than from a
single template with swapped nouns.
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
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    portable: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def name_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Setting:
    place: str = "the park"
    heat: str = "warm"
    affords: set[str] = field(default_factory=set)


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    risk: str
    weather: str
    heat_bump: float
    thirst_bump: float
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Gear:
    id: str
    label: str
    prep: str
    tail: str


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


def add_meter(ent: Entity, key: str, amount: float) -> None:
    ent.meters[key] = ent.meters.get(key, 0.0) + amount


def add_meme(ent: Entity, key: str, amount: float) -> None:
    ent.memes[key] = ent.memes.get(key, 0.0) + amount


def _r_heat(world: World) -> list[str]:
    out: list[str] = []
    for hero in world.characters():
        if hero.meters.get("outside", 0.0) < THRESHOLD:
            continue
        sig = ("heat", hero.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        add_meter(hero, "heat", 1.0)
        add_meter(hero, "thirst", 1.0)
        out.append(f"The warm air made {hero.id} feel a little drier.")
    return out


def _r_thirst_warning(world: World) -> list[str]:
    out: list[str] = []
    hero = next((e for e in world.characters() if e.kind == "character" and e.type in {"girl", "boy"}), None)
    if not hero:
        return out
    if hero.meters.get("thirst", 0.0) < THRESHOLD:
        return out
    sig = ("worry", hero.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    add_meme(hero, "unease", 1.0)
    out.append(f"{hero.id} started to feel prickly and tired.")
    return out


def _r_hydro_relief(world: World) -> list[str]:
    out: list[str] = []
    hero = next((e for e in world.characters() if e.kind == "character" and e.type in {"girl", "boy"}), None)
    bottle = world.entities.get("hydro")
    if not hero or not bottle:
        return out
    if hero.meters.get("hydrated", 0.0) < THRESHOLD:
        return out
    sig = ("relief", hero.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.meters["thirst"] = max(0.0, hero.meters.get("thirst", 0.0) - 1.0)
    add_meme(hero, "relief", 1.0)
    out.append(f"After a few sips, {hero.id} felt steadier again.")
    return out


CAUSAL_RULES = [_r_heat, _r_thirst_warning, _r_hydro_relief]


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


SETTINGS = {
    "park": Setting(place="the park", heat="warm", affords={"walk", "play", "bike"}),
    "yard": Setting(place="the backyard", heat="hot", affords={"walk", "play"}),
    "sidewalk": Setting(place="the sidewalk", heat="hot", affords={"walk", "bike"}),
}

ACTIVITIES = {
    "play": Activity(
        id="play",
        verb="play outside",
        gerund="playing outside",
        rush="run out to play",
        risk="get thirsty",
        weather="sunny",
        heat_bump=1.0,
        thirst_bump=1.0,
        keyword="hydro",
        tags={"sun", "thirst"},
    ),
    "bike": Activity(
        id="bike",
        verb="ride their bike",
        gerund="riding their bike",
        rush="dash out with the bike",
        risk="get tired and thirsty",
        weather="sunny",
        heat_bump=1.0,
        thirst_bump=1.0,
        keyword="hydro",
        tags={"sun", "thirst"},
    ),
    "walk": Activity(
        id="walk",
        verb="take a walk",
        gerund="taking a walk",
        rush="hurry down the path",
        risk="get dry and tired",
        weather="sunny",
        heat_bump=0.5,
        thirst_bump=0.5,
        keyword="hydro",
        tags={"sun", "thirst"},
    ),
}

GEAR = [
    Gear(id="hydro", label="the hydro bottle", prep="fill the hydro bottle first", tail="stopped at home to fill the hydro bottle"),
    Gear(id="shade", label="a shady hat", prep="put on a shady hat first", tail="went back for the shady hat"),
]

NAMES = {
    "girl": ["Maya", "Nora", "Lena", "Ivy", "Zoe"],
    "boy": ["Theo", "Finn", "Ari", "Leo", "Ben"],
}

TRAITS = ["curious", "spirited", "playful", "gentle", "restless"]


@dataclass
class StoryParams:
    place: str
    activity: str
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


def reasonability_gate(setting: Setting, activity: Activity) -> bool:
    return activity.id in setting.affords


def select_gear(activity: Activity) -> Optional[Gear]:
    return GEAR[0] if activity.keyword == "hydro" else None


def predict(world: World, hero: Entity, activity: Activity) -> dict:
    sim = world.copy()
    _do_activity(sim, sim.get(hero.id), activity, narrate=False)
    h = sim.get(hero.id)
    return {
        "thirst": h.meters.get("thirst", 0.0),
        "hydrated": h.meters.get("hydrated", 0.0),
    }


def _do_activity(world: World, hero: Entity, activity: Activity, narrate: bool = True) -> None:
    if activity.id not in world.setting.affords:
        return
    add_meter(hero, "outside", 1.0)
    add_meter(hero, "heat", activity.heat_bump)
    add_meter(hero, "thirst", activity.thirst_bump)
    add_meme(hero, "eagerness", 1.0)
    propagate(world, narrate=narrate)


def introduce(world: World, hero: Entity) -> None:
    trait = next((t for t in ["curious", "spirited", "playful", "gentle", "restless"] if t in hero.memes), "")
    world.say(f"{hero.id} was a little {hero.type} who loved simple days and small adventures.")


def setup(world: World, hero: Entity, parent: Entity, activity: Activity) -> None:
    world.say(f"{hero.id} liked {activity.gerund} on bright days, especially at {world.setting.place}.")
    world.say(f"That morning, {hero.id}'s {parent.name_word()} handed over a clean hydro bottle.")
    add_meter(world.get("hydro"), "water", 1.0)
    add_meter(hero, "hydrated", 0.0)


def warning(world: World, parent: Entity, hero: Entity, activity: Activity) -> None:
    world.say(f"\"Take the hydro bottle with you,\" {parent.pronoun('subject')} said. \"It is a hot day.\"")


def ignore_warning(world: World, hero: Entity, activity: Activity) -> None:
    add_meme(hero, "impatience", 1.0)
    world.say(f"{hero.id} almost rushed off anyway, because {hero.pronoun('subject')} wanted to {activity.verb} right away.")


def compromise(world: World, parent: Entity, hero: Entity, activity: Activity) -> Optional[Gear]:
    gear = select_gear(activity)
    if gear is None:
        return None
    world.say(f"{hero.pronoun('possessive').capitalize()} {parent.name_word()} pointed at the bottle and smiled.")
    world.say(f"\"How about we {gear.prep}? Then you can still {activity.verb}.\"")
    return gear


def accept(world: World, hero: Entity, parent: Entity, activity: Activity, gear: Gear) -> None:
    bottle = world.get("hydro")
    add_meter(hero, "hydrated", 1.0)
    add_meme(hero, "relief", 1.0)
    hero.memes["impatience"] = max(0.0, hero.memes.get("impatience", 0.0) - 1.0)
    world.say(f"{hero.id} nodded, filled the hydro bottle, and went out feeling smarter.")
    world.say(f"Soon {hero.id} was {activity.gerund}, and every sip kept the day easy.")
    world.say(f"By the time they came back, the hydro bottle was empty and the outing had gone well.")


def tell(params: StoryParams) -> World:
    setting = SETTINGS[params.place]
    activity = ACTIVITIES[params.activity]
    world = World(setting)
    hero = world.add(Entity(id=params.name, kind="character", type=params.gender))
    parent = world.add(Entity(id="parent", kind="character", type=params.parent))
    bottle = world.add(Entity(id="hydro", type="bottle", label="hydro bottle", phrase="a blue hydro bottle", owner=hero.id, caretaker=parent.id, portable=True))
    world.facts.update(hero=hero, parent=parent, activity=activity, setting=setting, bottle=bottle)

    introduce(world, hero)
    setup(world, hero, parent, activity)
    world.para()
    warning(world, parent, hero, activity)
    ignore_warning(world, hero, activity)
    _do_activity(world, hero, activity, narrate=True)
    world.para()
    if hero.meters.get("thirst", 0.0) >= THRESHOLD:
        world.say(f"Then {hero.id} slowed down and noticed {hero.pronoun('possessive')} mouth felt dry.")
    gear = compromise(world, parent, hero, activity)
    if gear is not None:
        accept(world, hero, parent, activity, gear)

    hero.memes["resolved"] = 1.0
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = f["hero"]
    activity: Activity = f["activity"]
    parent: Entity = f["parent"]
    return [
        f'Write a short slice-of-life story for a child named {hero.id} about the word "hydro".',
        f"Tell a gentle cautionary story where {hero.id} wants to {activity.verb} but {parent.name_word()} reminds {hero.id} to bring the hydro bottle.",
        f'Write a simple story about a hot day, a child, and a hydro bottle that ends with a calm compromise.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    parent: Entity = f["parent"]
    activity: Activity = f["activity"]
    setting: Setting = f["setting"]
    qa = [
        QAItem(
            question=f"Where did {hero.id} want to {activity.verb}?",
            answer=f"{hero.id} wanted to {activity.verb} at {setting.place} on a hot day.",
        ),
        QAItem(
            question=f"Why did {parent.name_word()} tell {hero.id} to take the hydro bottle?",
            answer=f"{parent.pronoun('subject').capitalize()} knew it was hot, so the hydro bottle would help keep {hero.id} from getting too thirsty.",
        ),
        QAItem(
            question=f"What changed after {hero.id} filled the hydro bottle?",
            answer=f"{hero.id} felt steadier, the day stopped feeling so rough, and {hero.id} could keep {activity.gerund} without getting worn out.",
        ),
    ]
    if world.get("hydro").meters.get("water", 0.0) >= THRESHOLD:
        qa.append(QAItem(
            question=f"What did the hydro bottle do for {hero.id}?",
            answer=f"It gave {hero.id} water to drink, which helped with thirst on the warm day.",
        ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does it mean to be thirsty?",
            answer="Being thirsty means your body wants water and your mouth can feel dry.",
        ),
        QAItem(
            question="Why is it smart to bring water on a hot day?",
            answer="Water helps your body stay comfortable when the sun makes you lose more moisture.",
        ),
        QAItem(
            question="What is a hydro bottle for?",
            answer="A hydro bottle is for carrying water so you can drink when you need it.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts ==", *[f"- {p}" for p in sample.prompts], "", "== story qa =="]
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    out = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.portable:
            bits.append("portable=True")
        out.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    out.append(f"  fired rules: {sorted({name for name, *_ in world.fired})}")
    return "\n".join(out)


CURATED = [
    StoryParams(place="park", activity="play", name="Maya", gender="girl", parent="mother", trait="curious"),
    StoryParams(place="yard", activity="walk", name="Theo", gender="boy", parent="father", trait="restless"),
    StoryParams(place="sidewalk", activity="bike", name="Ivy", gender="girl", parent="father", trait="spirited"),
]


ASP_RULES = r"""
% A setting supports an activity when it affords that activity.
supports(S, A) :- affords(S, A).

% Hot, sunny activities raise thirst; hydro helps resolve thirst.
needs_water(A) :- thirsting(A).
safe_choice(A) :- needs_water(A), has_gear(hydro).

valid_story(S, A) :- supports(S, A), safe_choice(A).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for aid, a in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        if a.tags & {"sun", "thirst"}:
            lines.append(asp.fact("thirsting", aid))
    lines.append(asp.fact("has_gear", "hydro"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = {(p.place, p.activity) for p in CURATED if reasonability_gate(SETTINGS[p.place], ACTIVITIES[p.activity])}
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches Python gate ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and Python gates")
    print("only in clingo:", sorted(cl - py))
    print("only in python:", sorted(py - cl))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Cautionary slice-of-life story world about hydro and hot days.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [(p, a) for p in SETTINGS for a in ACTIVITIES if reasonability_gate(SETTINGS[p], ACTIVITIES[a])]
    if args.place:
        combos = [(p, a) for p, a in combos if p == args.place]
    if args.activity:
        combos = [(p, a) for p, a in combos if a == args.activity]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, activity = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(NAMES[gender])
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, activity=activity, name=name, gender=gender, parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        print(asp.one_model(asp_program("#show valid_story/2.")))
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
