#!/usr/bin/env python3
"""
storyworlds/worlds/faux_novocaine_sound_effects_space_adventure.py
===================================================================

A small, constraint-checked space-adventure story world about a child astronaut,
a loud sound-effects kit, and a careful compromise.

Seed premise:
- Space adventure tone
- Include the words "faux" and "novocaine"
- Feature sound effects
- Build a short, child-facing simulated story with a real turn and resolution

The world is deliberately tiny:
- A child wants to use a faux space-medical sound-effects kit.
- The captain worries it will wake a sleeping hatchling in the ship's nursery.
- The crew finds a safe compromise: a muffled headset and a quiet display deck.
"""

from __future__ import annotations

import argparse
import copy
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
    traits: list[str] = field(default_factory=list)
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
        for k in ["noise", "sleepiness", "buzz", "joy", "worry", "curiosity", "relief", "care"]:
            self.meters.setdefault(k, 0.0)
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "captain"}
        male = {"boy", "father", "dad", "man", "pilot"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


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
    noise: str
    weather: str = ""
    keyword: str = ""
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
    quiets: set[str]
    prep: str
    tail: str
    plural: bool = False


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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


def _r_noise(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters["noise"] < THRESHOLD:
            continue
        for item in world.entities.values():
            if item.kind != "thing" or not item.caretaker:
                continue
            if item.region not in {"nursery", "deck"}:
                continue
            if item.region == "nursery" and actor.meters["noise"] >= THRESHOLD and not world.covered(actor, "ears"):
                sig = ("wake", item.id)
                if sig in world.fired:
                    continue
                world.fired.add(sig)
                item.meters["buzz"] += 1
                out.append("The loud sound made the nursery feel busy and bright.")
    return out


CAUSAL_RULES = []


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    for rule in CAUSAL_RULES:
        produced.extend(rule(world))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def risk(activity: Activity, prize: Prize) -> bool:
    return prize.region == "nursery" and activity.id == "sound_effects"


def select_gear(activity: Activity, prize: Prize) -> Optional[Gear]:
    for gear in GEAR:
        if prize.region in gear.covers and activity.id in gear.quiets:
            return gear
    return None


def tell(setting: Setting, activity: Activity, prize_cfg: Prize,
         hero_name: str = "Milo", hero_type: str = "boy",
         parent_type: str = "captain") -> World:
    world = World(setting)

    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type=hero_type,
        traits=["little", "curious", "brave"],
    ))
    parent = world.add(Entity(
        id="Captain",
        kind="character",
        type=parent_type,
        label="the captain",
    ))
    prize = world.add(Entity(
        id="prize",
        type=prize_cfg.type,
        label=prize_cfg.label,
        phrase=prize_cfg.phrase,
        caretaker=parent.id,
        region=prize_cfg.region,
        plural=prize_cfg.plural,
    ))

    hero.memes["curiosity"] += 1
    world.say(
        f"{hero.id} was a little astronaut who loved the ship's sound-effects panel."
    )
    world.say(
        f"{hero.id} especially loved the faux novocaine button, which made a silly "
        f"bzzzt-bloop noise that sounded like a tiny space doctor."
    )
    world.say(
        f"On this trip, {hero.id} wanted to press the button and make "
        f"{activity.gerund} noises all through {setting.place}."
    )
    world.say(
        f"That morning, {hero.id}'s {parent.label} had set {prize.phrase} in the nursery."
    )

    world.para()
    world.say(
        f"At first, the idea sounded fun, but the captain worried about the sleeping "
        f"{prize.label} in the nursery."
    )
    if risk(activity, prize):
        hero.memes["worry"] += 1
        hero.meters["noise"] += 1
        world.say(
            f'"If you press it here, the sound will reach the nursery," the captain said. '
            f'"That could wake {prize.it()}."'
        )
        world.say(
            f"{hero.id} wanted to try anyway and reached for the panel with a hopeful grin."
        )
        hero.memes["defiance"] = hero.memes.get("defiance", 0.0) + 1
        world.say(
            f"{hero.id} made a big pretend {activity.rush}, but the captain gently held out a hand."
        )
        world.say(
            f'"We can still have the fun sound," the captain said. "We just need a quieter way."'
        )

    world.para()
    gear_def = select_gear(activity, prize)
    if gear_def is None:
        raise StoryError("No safe gear matches this space sound-effects problem.")

    gear = world.add(Entity(
        id=gear_def.id,
        type="gear",
        label=gear_def.label,
        owner=hero.id,
        caretaker=parent.id,
        protective=True,
        covers=set(gear_def.covers),
        plural=gear_def.plural,
    ))
    gear.worn_by = hero.id

    hero.memes["relief"] += 1
    hero.memes["joy"] += 1
    hero.memes["worry"] = 0.0
    world.say(
        f'The captain smiled and said, "{gear_def.prep}."'
    )
    world.say(
        f"Then {hero.id} wore {gear.label} and tried again in the observation deck."
    )
    world.say(
        f"This time, the faux novocaine squeak came out soft and funny, like a little comet bouncing in the dark."
    )
    world.say(
        f"{hero.id} pressed the button, the sound stayed gentle, and the nursery stayed quiet."
    )
    world.say(
        f"At the end, {hero.id} was laughing, the captain was smiling, and {prize.label} kept sleeping peacefully."
    )

    world.facts.update(
        hero=hero,
        parent=parent,
        prize=prize,
        activity=activity,
        gear=gear_def,
        setting=setting,
        resolved=True,
        conflict=True,
    )
    return world


SETTINGS = {
    "ship": Setting(place="the starship", affords={"sound_effects"}),
    "deck": Setting(place="the observation deck", affords={"sound_effects"}),
    "moonbase": Setting(place="the moonbase", affords={"sound_effects"}),
}

ACTIVITIES = {
    "sound_effects": Activity(
        id="sound_effects",
        verb="make space sound effects",
        gerund="making space sound effects",
        rush="dash to the sound panel",
        noise="bzzzt-bloop",
        keyword="faux",
        tags={"sound", "space", "faux", "novocaine"},
    ),
}

PRIZES = {
    "hatchling": Prize(
        label="sleeping hatchling",
        phrase="a sleeping hatchling in the nursery",
        type="hatchling",
        region="nursery",
    ),
    "robot": Prize(
        label="repair robot",
        phrase="a repair robot on the deck",
        type="robot",
        region="deck",
    ),
}

GEAR = [
    Gear(
        id="headset",
        label="a muffled headset",
        covers={"ears"},
        quiets={"sound_effects"},
        prep="put on a muffled headset first",
        tail="walked back to the observation deck",
    ),
]

GIRL_NAMES = ["Nova", "Mina", "Zuri", "Luna", "Aya"]
BOY_NAMES = ["Milo", "Jett", "Tomas", "Leo", "Pico"]
TRAITS = ["curious", "brave", "playful", "bright"]


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


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    return [
        "Write a short space adventure for a preschooler about faux novocaine sound effects and a safe compromise.",
        f"Tell a gentle story where {hero.id} wants to use a sound-effects panel on a starship, but the captain worries about a sleeping hatchling.",
        "Write a child-facing story with a noisy space toy, a worried guardian, and a quieter way to keep playing.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    parent = f["parent"]
    prize = f["prize"]
    gear = f["gear"]
    activity = f["activity"]
    return [
        QAItem(
            question=f"What did {hero.id} want to do on the ship?",
            answer=f"{hero.id} wanted to {activity.verb} and make the faux novocaine button go bzzzt-bloop.",
        ),
        QAItem(
            question=f"Why did {parent.label} worry about the nursery?",
            answer=f"{parent.label.capitalize()} worried because the loud sound might wake the {prize.label} in the nursery.",
        ),
        QAItem(
            question=f"What helped {hero.id} play without waking the {prize.label}?",
            answer=f"{gear.label} helped because it made the sound softer, so {hero.id} could play in the observation deck instead of near the nursery.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended happily, with {hero.id} laughing, the captain smiling, and the {prize.label} still asleep.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a sound effect?",
            answer="A sound effect is a special noise made to sound like a real action, like a zap, whoosh, or beep.",
        ),
        QAItem(
            question="What does faux mean?",
            answer="Faux means fake or pretend, so something faux is not the real thing.",
        ),
        QAItem(
            question="What is novocaine used for?",
            answer="Novocaine is a medicine doctors use to numb pain, so a person feels less hurting during some dental work.",
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
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.protective:
            bits.append(f"covers={sorted(e.covers)}")
        elif e.region:
            bits.append(f"region={e.region}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="ship", activity="sound_effects", prize="hatchling", name="Milo", gender="boy", parent="captain", trait="curious"),
    StoryParams(place="deck", activity="sound_effects", prize="hatchling", name="Nova", gender="girl", parent="captain", trait="playful"),
]


def explain_rejection() -> str:
    return "(No story: this world only supports the sound-effects adventure, and the loud version needs a safe gear fix.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Space adventure story world with faux novocaine sound effects.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["captain"])
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
    if args.place and args.place not in SETTINGS:
        raise StoryError("Unknown place.")
    if args.activity and args.activity not in ACTIVITIES:
        raise StoryError("Unknown activity.")
    if args.prize and args.prize not in PRIZES:
        raise StoryError("Unknown prize.")

    combos = [
        ("ship", "sound_effects", "hatchling"),
        ("deck", "sound_effects", "hatchling"),
    ]
    combos = [c for c in combos
              if (args.place is None or c[0] == args.place)
              and (args.activity is None or c[1] == args.activity)
              and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError(explain_rejection())

    place, activity, prize = rng.choice(combos)
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or "captain"
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, activity=activity, prize=prize, name=name, gender=gender, parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], ACTIVITIES[params.activity], PRIZES[params.prize], params.name, params.gender, params.parent)
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
% A story is compatible when the sound-effects activity can be safely performed
% with a quieting gear item that covers the relevant place.
compatible(P, A, R) :- place(P), activity(A), prize(R), risk(A, R), fix(A, R).

risk(sound_effects, hatchling) :- place(ship).
risk(sound_effects, hatchling) :- place(deck).

fix(sound_effects, hatchling) :- gear(headset), quiets(headset, sound_effects), covers(headset, ears).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("place", pid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", pid, a))
    for aid in ACTIVITIES:
        lines.append(asp.fact("activity", aid))
    for pid, pr in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("worn_on", pid, pr.region))
    for g in GEAR:
        lines.append(asp.fact("gear", g.id))
        for c in sorted(g.covers):
            lines.append(asp.fact("covers", g.id, c))
        for q in sorted(g.quiets):
            lines.append(asp.fact("quiets", g.id, q))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show compatible/3."))
    return sorted(set(asp.atoms(model, "compatible")))


def asp_verify() -> int:
    py = {("ship", "sound_effects", "hatchling"), ("deck", "sound_effects", "hatchling")}
    cl = set(asp_valid_combos())
    if cl == py:
        print(f"OK: clingo gate matches Python ({len(cl)} combos).")
        return 0
    print("MISMATCH")
    print("python only:", sorted(py - cl))
    print("clingo only:", sorted(cl - py))
    return 1


def main() -> None:
    args = build_parser().parse_args()
    if args.verify:
        sys.exit(asp_verify())
    if args.show_asp:
        print(asp_program("#show compatible/3."))
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
        header = f"### variant {i + 1}" if len(samples) > 1 and not args.all else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
