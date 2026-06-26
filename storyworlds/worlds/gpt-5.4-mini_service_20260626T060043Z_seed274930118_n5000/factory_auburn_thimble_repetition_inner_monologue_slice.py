#!/usr/bin/env python3
"""
storyworlds/worlds/factory_auburn_thimble_repetition_inner_monologue_slice.py
=============================================================================

A small slice-of-life story world about a quiet factory shift, a careful
little task, and the comfort of repetition.

Seed image:
---
An auburn-haired child helps in a small factory where thread, cloth, and little
metal thimbles live in neat rows. The work is simple but fussy: one steady
stitch at a time, a lot of looking, a lot of thinking, and a small problem that
is solved by patience and the right tool.

World model:
---
The hero works at a family factory in an ordinary, child-sized way. Sewing
creates small finger-risk; a thimble prevents the prick and helps the task feel
calm. Repetition is modeled as a steady meter that grows when the hero repeats
the same careful motion. Inner monologue is modeled as a membrane of self-talk
that rises under uncertainty and settles once the work pattern becomes smooth.
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
    protective: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "aunt"}
        male = {"boy", "man", "father", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str = "the factory"
    detail: str = "a small room with humming machines and folded cloth"
    affords: set[str] = field(default_factory=set)


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    risk: str
    outcome: str
    keyword: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    label: str
    phrase: str
    type: str
    owner_use: str
    genders: set[str] = field(default_factory=lambda: {"girl", "boy"})


@dataclass
class Gear:
    id: str
    label: str
    purpose: str
    fit: str
    prep: str
    tail: str


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
        return clone

    def worn_items(self, actor: Entity) -> list[Entity]:
        return [e for e in self.entities.values() if e.worn_by == actor.id]


def _r_focus(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.entities.values():
        if actor.kind != "character":
            continue
        if actor.memes.get("focus", 0.0) >= THRESHOLD and actor.meters.get("repetition", 0.0) < THRESHOLD:
            actor.meters["repetition"] = 1.0
            out.append(f"{actor.id} settled into a steady rhythm.")
    return out


def _r_thimble_comfort(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.entities.values():
        if actor.kind != "character":
            continue
        if actor.meters.get("repetition", 0.0) >= THRESHOLD and any(it.protective for it in world.worn_items(actor)):
            if actor.memes.get("worry", 0.0) >= THRESHOLD:
                actor.memes["worry"] = 0.0
                actor.memes["calm"] = actor.memes.get("calm", 0.0) + 1.0
                out.append(f"The careful little motions made {actor.id} feel calm.")
    return out


CAUSAL_RULES = [_r_focus, _r_thimble_comfort]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            lines = rule(world)
            if lines:
                changed = True
                produced.extend(lines)
    if narrate:
        for line in produced:
            world.say(line)
    return produced


def tell_story(world: World, hero: Entity, grownup: Entity, prize: Entity, gear: Gear, activity: Activity) -> None:
    world.say(
        f"{hero.id} was an auburn-haired child who liked the factory best when the machines were only humming."
    )
    world.say(
        f"She loved {activity.gerund} in little careful rows, because each finished seam looked neat and sure."
    )
    world.say(
        f"Her {grownup.pronoun('possessive')} {grownup.label or grownup.type} kept a brass {gear.label} in a tin cup by the worktable."
    )

    world.para()
    world.say(
        f"One quiet morning at the factory, {hero.id} wanted to {activity.verb} before the tea got cold."
    )
    world.say(
        f"She picked up {prize.phrase} and looked at the cloth again and again, thinking, "
        f"'{activity.keyword or activity.gerund.capitalize()}. One stitch, then another.'"
    )
    hero.memes["focus"] = hero.memes.get("focus", 0.0) + 1.0
    hero.memes["worry"] = hero.memes.get("worry", 0.0) + 1.0
    world.say(
        f"But the needle kept tapping her finger, and that little prick made the work feel less easy."
    )

    world.para()
    world.say(
        f"Her {grownup.label or grownup.type} noticed the pause and said, '{gear.prep}.'"
    )
    prize.worn_by = hero.id
    gear_ent = world.add(Entity(
        id=gear.id,
        kind="thing",
        type="gear",
        label=gear.label,
        protective=True,
        owner=hero.id,
        worn_by=hero.id,
    ))
    hero.memes["worry"] += 0.0
    hero.memes["hope"] = hero.memes.get("hope", 0.0) + 1.0
    world.say(
        f"{hero.id} slid the {gear_ent.label} on and tried again, slower this time, like she was counting the stitches in her head."
    )
    propagate(world, narrate=True)

    world.say(
        f"One stitch. Another stitch. Then another."
    )
    hero.memes["focus"] += 1.0
    propagate(world, narrate=True)

    world.para()
    world.say(
        f"At last the row was finished, the cloth lay smooth on the table, and {hero.id} smiled at the neat little line she had made."
    )
    world.say(
        f"The factory still hummed, but now it sounded friendly, like it was pleased with the day's small work."
    )

    world.facts.update(hero=hero, grownup=grownup, prize=prize, gear=gear, activity=activity)


SETTINGS = {
    "factory": Setting(
        place="the factory",
        detail="a small room with humming machines, folded cloth, and a tea mug cooling on the bench",
        affords={"stitch"},
    ),
    "workroom": Setting(
        place="the workroom",
        detail="a tidy room beside the factory floor where thread, buttons, and scraps lived in jars",
        affords={"stitch"},
    ),
}

ACTIVITIES = {
    "stitch": Activity(
        id="stitch",
        verb="stitch the fabric labels",
        gerund="stitching fabric labels",
        rush="rush through the stitching",
        risk="the needle might prick her finger",
        outcome="the labels stayed neat and smooth",
        keyword="stitch",
        tags={"factory", "thread", "careful"},
    ),
}

PRIZES = {
    "thimble": Prize(
        label="thimble",
        phrase="a little brass thimble",
        type="thimble",
        owner_use="finger",
        genders={"girl", "boy"},
    ),
}

GEAR = [
    Gear(
        id="thimble",
        label="thimble",
        purpose="protects a finger from the needle",
        fit="finger",
        prep="put on the thimble before you sew",
        tail="kept the thimble on while she finished the last row",
    ),
]

GIRL_NAMES = ["Mina", "Ivy", "Nora", "Ella", "June", "Lena"]
BOY_NAMES = ["Owen", "Theo", "Finn", "Jude", "Eli", "Milo"]
TRAITS = ["patient", "quiet", "careful", "thoughtful", "gentle"]


@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    name: str
    gender: str
    grownup: str
    trait: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    return [(place, "stitch", "thimble") for place in SETTINGS]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Slice-of-life factory story world with repetition and inner monologue.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--grownup", choices=["mother", "aunt"])
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
    if args.activity and args.prize and (args.activity != "stitch" or args.prize != "thimble"):
        raise StoryError("This world only supports stitching with a thimble.")
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)]
    if not combos:
        raise StoryError("No valid story combination matches the requested options.")
    place, activity, prize = rng.choice(combos)
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    grownup = args.grownup or rng.choice(["mother", "aunt"])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, activity=activity, prize=prize, name=name, gender=gender, grownup=grownup, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = World(SETTINGS[params.place])
    hero = world.add(Entity(id=params.name, kind="character", type=params.gender))
    grownup = world.add(Entity(id="grownup", kind="character", type=params.grownup, label=f"her {params.grownup}"))
    prize = world.add(Entity(id="prize", kind="thing", type="thimble", label="thimble", phrase="a little brass thimble", owner=hero.id))
    gear = GEAR[0]
    tell_story(world, hero, grownup, prize, gear, ACTIVITIES[params.activity])
    story = world.render()
    prompts = [
        f"Write a gentle slice-of-life story set in a factory, with an auburn-haired child, a thimble, repetition, and quiet inner monologue.",
        f"Tell a short story about {params.name} at {world.setting.place} where careful sewing turns into a calm routine.",
        f"Write a child-friendly story in which a little bit of worry is solved by a thimble and a patient rhythm.",
    ]
    story_qa = [
        QAItem(
            question=f"Why did {params.name} want the thimble?",
            answer=f"{params.name} wanted the thimble because stitching at the factory kept tapping her finger, and the thimble helped protect it while she worked."
        ),
        QAItem(
            question=f"What was {params.name} thinking while she sewed?",
            answer=f"She kept thinking, 'One stitch, then another,' because repeating the careful motion helped her stay calm and finish the row."
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended with the fabric labels finished neatly, the factory humming softly, and {params.name} feeling proud of the work she had done."
        ),
    ]
    world_qa = [
        QAItem(
            question="What is a thimble for?",
            answer="A thimble is a small metal cap you wear on a finger to help protect it while sewing."
        ),
        QAItem(
            question="Why can repetition feel comforting?",
            answer="Repetition can feel comforting because doing the same careful action again and again can make a task feel steady and familiar."
        ),
        QAItem(
            question="What is a factory?",
            answer="A factory is a place where people make things, often with tools and machines that help them work."
        ),
    ]
    return StorySample(params=params, story=story, prompts=prompts, story_qa=story_qa, world_qa=world_qa, world=world)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


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
    lines.append("== (3) World knowledge questions ==")
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
        if e.protective:
            bits.append("protective=True")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
valid_place(factory).
valid_place(workroom).

valid_activity(stitch).

valid_prize(thimble).

valid_story(P, A, R) :- valid_place(P), valid_activity(A), valid_prize(R), affords(P, A), fits(R, A).

#show valid_story/3.
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, setting in SETTINGS.items():
        lines.append(asp.fact("place", pid))
        for act in sorted(setting.affords):
            lines.append(asp.fact("affords", pid, act))
    for aid in ACTIVITIES:
        lines.append(asp.fact("activity", aid))
    for rid in PRIZES:
        lines.append(asp.fact("prize", rid))
    return "\n".join(lines)


def asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program())
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


def main() -> None:
    args = build_parser().parse_args()
    if args.verify:
        sys.exit(asp_verify())
    if args.show_asp:
        print(asp_program())
        return
    if args.asp:
        print(asp_valid_combos())
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(StoryParams(place=p, activity="stitch", prize="thimble", name="Mina", gender="girl", grownup="mother", trait="careful")) for p in SETTINGS]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 20, 20):
            seed = base_seed + i
            i += 1
            params = resolve_params(args, random.Random(seed))
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
        if len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
