#!/usr/bin/env python3
"""
storyworlds/worlds/begin_sleeve_dialogue_animal_story.py
========================================================

A small animal-story world about a young animal, a tricky sleeve, and a
dialogue-based fix.

Seed tale:
---
A little animal wanted to begin a job outside while wearing a long sleeve.
The sleeve kept dipping into paint, flour, or water. A grown-up warned that it
would make a mess. The little animal tried anyway, then listened to a kind
suggestion: roll up the sleeve, tie it back, or swap to a safer shirt. The
animal felt proud and finished the task clean and happy.
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
    plural: bool = False
    owner: Optional[str] = None
    worn_by: Optional[str] = None
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    traits: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"mess": 0.0, "dirty": 0.0, "work": 0.0}
        if not self.memes:
            self.memes = {"joy": 0.0, "worry": 0.0, "pride": 0.0, "curiosity": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "aunt", "sister"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "uncle", "brother"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Setting:
    place: str
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
class Gear:
    id: str
    label: str
    covers: set[str]
    guards: set[str]
    offer: str
    outcome: str
    plural: bool = False


@dataclass
class StoryParams:
    place: str
    activity: str
    gear: str
    name: str
    animal: str
    parent: str
    trait: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.zone: set[str] = set()
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


def _begin_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    if activity.id not in world.setting.affords:
        raise StoryError(f"The place {world.setting.place} does not reasonably allow {activity.id}.")
    world.zone = set(activity.zone)
    actor.meters["mess"] += 1
    actor.memes["curiosity"] += 1
    if narrate:
        world.say(f"{actor.id} began to {activity.verb}, because {actor.pronoun()} was curious.")


def _mess_sleeve(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters["mess"] < THRESHOLD:
            continue
        for item in world.worn_items(actor):
            if item.protective:
                continue
            if "sleeve" not in item.covers:
                continue
            if item.label != "sleeve" and item.label != "long sleeve":
                continue
            sig = ("mess", actor.id, item.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            item.meters["dirty"] += 1
            actor.memes["worry"] += 1
            out.append(f"{actor.pronoun('possessive').capitalize()} sleeve got messy and damp.")
    return out


def _work(world: World) -> list[str]:
    out: list[str] = []
    for item in world.entities.values():
        if item.meters.get("dirty", 0.0) < THRESHOLD:
            continue
        if not item.owner:
            continue
        sig = ("work", item.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        owner = world.get(item.owner)
        owner.meters["work"] += 1
        out.append(f"That would mean more washing for {owner.pronoun('possessive')} grown-up.")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for fn in (_mess_sleeve, _work):
            sents = fn(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def setting_detail(setting: Setting, activity: Activity) -> str:
    if setting.place == "the kitchen":
        return "The kitchen smelled warm and busy, with a little table waiting nearby."
    if setting.place == "the backyard":
        return "The backyard looked bright, and the work area was spread out with room to move."
    return f"{setting.place.capitalize()} was quiet and ready for a small job."


def introduce(world: World, hero: Entity) -> None:
    trait = next((t for t in hero.traits if t != "little"), "gentle")
    world.say(f"{hero.id} was a little {trait} {hero.type} who liked to begin new jobs right away.")


def loves_activity(world: World, hero: Entity, activity: Activity) -> None:
    world.say(f"{hero.pronoun().capitalize()} loved {activity.gerund}, especially when there was something to make.")


def wears_sleeve(world: World, hero: Entity, sleeve: Entity) -> None:
    sleeve.worn_by = hero.id
    world.say(f"{hero.id} wore {hero.pronoun('possessive')} {sleeve.label} and liked how it felt soft on {hero.pronoun('possessive')} arm.")


def arrives(world: World, hero: Entity, parent: Entity, activity: Activity) -> None:
    world.say(f"One day, {hero.id} and {hero.pronoun('possessive')} {parent.type} went to {world.setting.place}.")
    world.say(setting_detail(world.setting, activity))


def wants(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["curiosity"] += 1
    world.say(f"{hero.id} said, \"I want to begin now!\" and reached for the tools.")


def warn(world: World, parent: Entity, hero: Entity, activity: Activity, sleeve: Entity) -> bool:
    world.say(f"{parent.id} looked at {hero.pronoun('possessive')} sleeve and said, \"That sleeve is too long for {activity.verb}.\"")
    if activity.mess == "wet":
        world.say("\"It might get wet and drip everywhere,\" the grown-up added.")
    elif activity.mess == "paint":
        world.say("\"It might brush through the paint,\" the grown-up added.")
    else:
        world.say("\"It might pick up dirt and crumbs,\" the grown-up added.")
    hero.memes["worry"] += 1
    return True


def try_anyway(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["curiosity"] += 1
    world.say(f"{hero.id} tried anyway and reached out to {activity.rush}.")
    propagate(world, narrate=True)


def dialogue_turn(world: World, parent: Entity, hero: Entity, activity: Activity, sleeve: Entity) -> None:
    world.say(f"\"Can I still begin?\" {hero.id} asked.")
    world.say(f"\"Yes,\" said {parent.id}, \"but let's fix the sleeve first.\"")


def fix_sleeve(world: World, parent: Entity, hero: Entity, gear_def: Gear) -> None:
    gear = world.add(Entity(
        id=gear_def.id,
        kind="thing",
        type="gear",
        label=gear_def.label,
        owner=hero.id,
        protective=True,
        covers=set(gear_def.covers),
    ))
    gear.worn_by = hero.id
    world.say(f"\"How about we {gear_def.offer}?\" asked {parent.id}.")
    world.say(f"{hero.id} smiled and agreed to the plan.")


def finish(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["joy"] += 1
    hero.memes["pride"] += 1
    world.say(f"{hero.id} rolled up the sleeve, began to {activity.verb}, and stayed clean and proud.")
    world.say(f"By the end, {hero.id}'s {activity.keyword} project was done, and the sleeve was safe again.")


SETTINGS = {
    "kitchen": Setting(place="the kitchen", affords={"paint", "flour"}),
    "backyard": Setting(place="the backyard", affords={"water", "mud"}),
    "shed": Setting(place="the shed", affords={"paint"}),
}

ACTIVITIES = {
    "paint": Activity(
        id="paint",
        verb="paint a little birdhouse",
        gerund="painting little birdhouses",
        rush="the blue brush",
        mess="paint",
        soil="spotted with paint",
        zone={"sleeve"},
        keyword="paint",
        tags={"paint", "mess"},
    ),
    "water": Activity(
        id="water",
        verb="wash tiny pots",
        gerund="washing tiny pots",
        rush="the splash bowl",
        mess="wet",
        soil="dripping wet",
        zone={"sleeve"},
        keyword="water",
        tags={"water", "wet"},
    ),
    "flour": Activity(
        id="flour",
        verb="help bake a snack",
        gerund="baking snacks",
        rush="the flour scoop",
        mess="flour",
        soil="dusty with flour",
        zone={"sleeve"},
        keyword="flour",
        tags={"flour", "kitchen"},
    ),
    "mud": Activity(
        id="mud",
        verb="build a mud path",
        gerund="building mud paths",
        rush="the muddy bucket",
        mess="mud",
        soil="smeared with mud",
        zone={"sleeve"},
        keyword="mud",
        tags={"mud"},
    ),
}

GEARS = {
    "roll": Gear(
        id="roll",
        label="a rolled-up cuff",
        covers={"sleeve"},
        guards={"paint", "wet", "flour", "mud"},
        offer="roll up the sleeve first",
        outcome="kept the sleeve dry and clean",
    ),
    "apron": Gear(
        id="apron",
        label="a small apron",
        covers={"sleeve"},
        guards={"paint", "flour"},
        offer="tie on a small apron too",
        outcome="protected the sleeve from spills",
    ),
}

GIRL_NAMES = ["Mina", "Luna", "Poppy", "Nora", "Tilly"]
BOY_NAMES = ["Toby", "Milo", "Sunny", "Pip", "Ollie"]
ANIMALS = ["fox", "rabbit", "bear cub", "mouse", "kitten"]
TRAITS = ["brave", "curious", "playful", "gentle", "spirited"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            act = ACTIVITIES[act_id]
            for gear_id, gear in GEARS.items():
                if act.mess in gear.guards and "sleeve" in gear.covers:
                    combos.append((place, act_id, gear_id))
    return combos


def explain_rejection(activity: Activity, gear: Gear) -> str:
    return f"(No story: {gear.label} does not reasonably fix the sleeve for {activity.gerund}.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal story world about a beginning, a sleeve, and dialogue.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--gear", choices=GEARS)
    ap.add_argument("--name")
    ap.add_argument("--animal", choices=ANIMALS)
    ap.add_argument("--parent", choices=["mother", "father", "aunt", "uncle"])
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
    if args.activity and args.gear:
        act, gear = ACTIVITIES[args.activity], GEARS[args.gear]
        if not (act.mess in gear.guards and "sleeve" in gear.covers):
            raise StoryError(explain_rejection(act, gear))
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.activity is None or c[1] == args.activity)
              and (args.gear is None or c[2] == args.gear)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, activity, gear = rng.choice(sorted(combos))
    animal = args.animal or rng.choice(ANIMALS)
    name = args.name or rng.choice(GIRL_NAMES + BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father", "aunt", "uncle"])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, activity=activity, gear=gear, name=name, animal=animal, parent=parent, trait=trait)


def tell(params: StoryParams) -> World:
    world = World(SETTINGS[params.place])
    hero = world.add(Entity(id=params.name, kind="character", type=params.animal, traits=["little", params.trait]))
    parent = world.add(Entity(id="grownup", kind="character", type=params.parent, label="grown-up"))
    sleeve = world.add(Entity(id="sleeve", kind="thing", type="clothing", label="sleeve", owner=hero.id, worn_by=hero.id, covers={"sleeve"}))
    activity = ACTIVITIES[params.activity]
    gear_def = GEARS[params.gear]

    introduce(world, hero)
    loves_activity(world, hero, activity)
    wears_sleeve(world, hero, sleeve)

    world.para()
    arrives(world, hero, parent, activity)
    wants(world, hero, activity)
    warn(world, parent, hero, activity, sleeve)
    dialogue_turn(world, parent, hero, activity, sleeve)
    try_anyway(world, hero, activity)

    world.para()
    fix_sleeve(world, parent, hero, gear_def)
    finish(world, hero, activity)

    world.facts.update(hero=hero, parent=parent, sleeve=sleeve, activity=activity, gear=gear_def, setting=world.setting)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, act = f["hero"], f["activity"]
    return [
        f'Write a short animal-story tale for a young child about a character named {hero.id} who wants to begin {act.gerund}.',
        f'Write a gentle story with dialogue that includes the word "sleeve" and ends with a clever fix.',
        f"Tell a small animal story where a grown-up and a child talk, then solve a sleeve problem before the work begins.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, parent, act, gear = f["hero"], f["parent"], f["activity"], f["gear"]
    return [
        QAItem(
            question=f"What did {hero.id} want to begin?",
            answer=f"{hero.id} wanted to begin {act.verb}.",
        ),
        QAItem(
            question=f"Why did the grown-up worry about the sleeve?",
            answer=f"The grown-up worried because the sleeve could get {act.soil} while {hero.id} worked.",
        ),
        QAItem(
            question=f"What did the grown-up tell {hero.id} to do first?",
            answer=f"{parent.id} told {hero.id} to use {gear.label} first so the sleeve would stay safe.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended with {hero.id} beginning the job happily after fixing the sleeve.",
        ),
    ]


def world_qa(_: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a sleeve?",
            answer="A sleeve is the part of a shirt or coat that covers an arm.",
        ),
        QAItem(
            question="Why do people roll up a sleeve before messy work?",
            answer="People roll up a sleeve to keep it out of paint, water, flour, or mud.",
        ),
        QAItem(
            question="What does a grown-up do in a helpful story?",
            answer="A grown-up can warn about a problem and then offer a safe way to fix it.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    out.extend(sample.prompts)
    out.append("")
    out.append("== story qa ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== world qa ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.covers:
            bits.append(f"covers={sorted(e.covers)}")
        if e.worn_by:
            bits.append(f"worn_by={e.worn_by}")
        lines.append(f"{e.id}: {e.type} {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
valid_story(P,A,G) :- place(P), affords(P,A), activity(A), gear(G), fixes(G,A).
fixes(G,A) :- guards(G,M), mess_of(A,M), covers(G,sleeve).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    for p, s in SETTINGS.items():
        lines.append(asp.fact("place", p))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", p, a))
    for a, act in ACTIVITIES.items():
        lines.append(asp.fact("activity", a))
        lines.append(asp.fact("mess_of", a, act.mess))
    for g, gear in GEARS.items():
        lines.append(asp.fact("gear", g))
        for m in sorted(gear.guards):
            lines.append(asp.fact("guards", g, m))
        for c in sorted(gear.covers):
            lines.append(asp.fact("covers", g, c))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if py == asp_set:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and python:")
    print("only python:", sorted(py - asp_set))
    print("only asp:", sorted(asp_set - py))
    return 1


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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
    StoryParams(place="kitchen", activity="paint", gear="apron", name="Mina", animal="rabbit", parent="mother", trait="curious"),
    StoryParams(place="backyard", activity="water", gear="roll", name="Toby", animal="fox", parent="father", trait="playful"),
    StoryParams(place="kitchen", activity="flour", gear="apron", name="Pip", animal="mouse", parent="aunt", trait="gentle"),
    StoryParams(place="shed", activity="paint", gear="roll", name="Luna", animal="kitten", parent="uncle", trait="spirited"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.verify:
        sys.exit(asp_verify())
    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.asp:
        for row in asp_valid_combos():
            print(row)
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
