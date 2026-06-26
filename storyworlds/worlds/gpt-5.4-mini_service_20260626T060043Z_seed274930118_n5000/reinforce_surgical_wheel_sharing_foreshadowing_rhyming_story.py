#!/usr/bin/env python3
"""
storyworlds/worlds/reinforce_surgical_wheel_sharing_foreshadowing_rhyming_story.py
===================================================================================

A small standalone story world with a rhyming, child-friendly repair tale.

Premise:
- A child loves a little wagon with one wobbly wheel.
- The wheel makes a warning squeak, foreshadowing trouble.
- The child wants to use it right away, but a grown-up insists on reinforcing
  the wheel first.
- A careful fix and a sharing compromise let everyone enjoy the wagon safely.

This world is intentionally small and constraint-checked. It models a simple
physical object with meters and feelings with memes, then turns those states
into prose, Q&A, trace output, and an ASP parity check.
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
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for k in ["wobble", "stress", "fixed", "shared_use", "joy", "worry", "pride"]:
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


@dataclass
class Setting:
    place: str
    indoor: bool = False
    affords: set[str] = field(default_factory=set)


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    risk: str
    clue: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    label: str
    phrase: str
    type: str
    repair_need: str
    shareable: bool = True


@dataclass
class Gear:
    id: str
    label: str
    prep: str
    tail: str
    fixes: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.lines: list[str] = []
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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


def _r_wobble(world: World) -> list[str]:
    out: list[str] = []
    wheel = world.entities.get("wheel")
    if not wheel:
        return out
    if wheel.meters["wobble"] < THRESHOLD:
        return out
    sig = ("wobble",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    wheel.memes["worry"] += 1
    out.append("The wheel gave a squeak and a sway, like trouble was near on the way.")
    return out


def _r_reinforce(world: World) -> list[str]:
    out: list[str] = []
    wheel = world.entities.get("wheel")
    if not wheel:
        return out
    if wheel.meters["fixed"] < THRESHOLD:
        return out
    sig = ("reinforce",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    wheel.meters["wobble"] = 0.0
    wheel.memes["worry"] = 0.0
    wheel.memes["pride"] += 1
    out.append("The wheel stood straighter now, strong as a song and ready for play.")
    return out


def _r_share(world: World) -> list[str]:
    out: list[str] = []
    wagon = world.entities.get("wagon")
    if not wagon:
        return out
    if wagon.meters["shared_use"] < THRESHOLD:
        return out
    sig = ("share",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    wagon.memes["joy"] += 1
    out.append("Two friends could take turns, and the ride felt fair and bright.")
    return out


RULES = [
    _r_wobble,
    _r_reinforce,
    _r_share,
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in RULES:
            bits = rule(world)
            if bits:
                changed = True
                out.extend(bits)
    if narrate:
        for s in out:
            world.say(s)
    return out


def foreshadow_line(activity: Activity, prize: Prize) -> str:
    return f"At first, the wheel went creak and clack, a tiny hint that it might crack."


def build_story(world: World, hero: Entity, parent: Entity, friend: Entity, prize: Entity, activity: Activity, gear: Gear) -> None:
    world.say(
        f"{hero.id} was a little {hero.type} who loved to spin and play, "
        f"with rhymes in the air and sunshine in the day."
    )
    world.say(
        f"{hero.id} and {friend.id} liked to {activity.gerund}, "
        f"and {prize.label} was their favorite ride."
    )
    world.say(foreshadow_line(activity, prize))
    world.para()

    world.say(
        f"One day at {world.setting.place}, {hero.id} wanted to {activity.verb} right away, "
        f"but {prize.label} had a wobble that made {parent.label if parent.label else parent.id} say, "
        f"\"Not yet, not today.\""
    )
    prize.meters["wobble"] += 1
    hero.memes["worry"] += 1
    propagate(world, narrate=True)

    world.say(
        f"{hero.id} frowned and tried to {activity.rush}, "
        f"but the wheel shook with a shaky little sigh."
    )
    world.say(
        f"{parent.id} pointed to the loose spot and said, "
        f"\"We'll reinforce it first, then you can roll on by.\""
    )
    world.para()

    world.say(
        f"{parent.id} brought out {gear.label}, and together they {gear.prep}, "
        f"so the wheel could be snug and steady."
    )
    prize.meters["fixed"] += 1
    prop = propagate(world, narrate=True)

    world.say(
        f"{hero.id}'s face brightened like a kite in the sky, "
        f"and the frown on {hero.pronoun('possessive')} face slipped away."
    )

    wagon = world.get("wagon")
    wagon.meters["shared_use"] += 1
    hero.memes["joy"] += 1
    friend.memes["joy"] += 1
    wagon.meters["fixed"] += 1
    propagate(world, narrate=True)

    world.say(
        f"Then {hero.id} and {friend.id} shared the wagon wheel by turns, "
        f"and {gear.tail}."
    )
    world.say(
        f"By sunset, the wheel rolled round and right, and everyone smiled at the end of the night."
    )

    world.facts.update(
        hero=hero,
        parent=parent,
        friend=friend,
        prize=prize,
        activity=activity,
        gear=gear,
        prop=prop,
    )


SETTINGS = {
    "garage": Setting(place="the garage", indoor=True, affords={"roll"}),
    "yard": Setting(place="the yard", indoor=False, affords={"roll"}),
    "workshop": Setting(place="the workshop", indoor=True, affords={"roll"}),
}

ACTIVITIES = {
    "roll": Activity(
        id="roll",
        verb="roll the wagon",
        gerund="rolling the wagon",
        rush="dash to the wagon",
        risk="a wobble or a break",
        clue="a little squeak in the wheel",
        keyword="wheel",
        tags={"wheel", "share", "repair"},
    )
}

PRIZES = {
    "wagon": Prize(
        label="wagon",
        phrase="a little red wagon",
        type="wagon",
        repair_need="wheel",
        shareable=True,
    ),
    "cart": Prize(
        label="cart",
        phrase="a wooden handcart",
        type="cart",
        repair_need="wheel",
        shareable=True,
    ),
}

GEAR = [
    Gear(
        id="brace",
        label="a sturdy brace",
        prep="put on a sturdy brace and tightened the wheel",
        tail="the wagon rode smooth and true",
        fixes={"wheel"},
    ),
    Gear(
        id="bolts",
        label="two strong bolts",
        prep="slid in two strong bolts and made the wheel firm",
        tail="the wagon rolled like a happy drum",
        fixes={"wheel"},
    ),
]

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella"]
BOY_NAMES = ["Leo", "Ben", "Max", "Sam", "Finn"]
PARENT_NAMES = ["Mom", "Dad", "Mama", "Papa"]
FRIEND_NAMES = ["Nina", "Ollie", "Toby", "June"]
TRAITS = ["cheerful", "curious", "brave", "gentle", "playful"]


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            for prize_id, prize in PRIZES.items():
                if prize.repair_need == "wheel":
                    out.append((place, act_id, prize_id))
    return out


@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    name: str
    gender: str
    parent: str
    friend: str
    trait: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A rhyming story world about sharing and reinforcing a wheel.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=PARENT_NAMES)
    ap.add_argument("--name")
    ap.add_argument("--friend")
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.activity is None or c[1] == args.activity)
              and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, activity, prize = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(PARENT_NAMES)
    friend = args.friend or rng.choice(FRIEND_NAMES)
    trait = rng.choice(TRAITS)
    return StoryParams(place, activity, prize, name, gender, parent, friend, trait)


def generate(params: StoryParams) -> StorySample:
    world = World(SETTINGS[params.place])
    hero = world.add(Entity(id=params.name, kind="character", type=params.gender))
    parent = world.add(Entity(id=params.parent, kind="character", type="parent", label=params.parent))
    friend = world.add(Entity(id=params.friend, kind="character", type="friend"))
    prize = world.add(Entity(
        id="wagon",
        kind="thing",
        type=PRIZES[params.prize].type,
        label=PRIZES[params.prize].label,
        phrase=PRIZES[params.prize].phrase,
        owner=hero.id,
        caretaker=parent.id,
    ))
    gear = GEAR[0]
    build_story(world, hero, parent, friend, prize, ACTIVITIES[params.activity], gear)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, parent, activity, prize = f["hero"], f["parent"], f["activity"], f["prize"]
    return [
        f'Write a short rhyming story about {hero.id}, {prize.label}, and a careful repair that includes the word "wheel".',
        f"Tell a gentle story where {hero.id} wants to {activity.verb} but {parent.id} asks for a safer fix first.",
        f"Write a child-friendly rhyme about sharing a wagon after a wheel gets reinforced.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, parent, friend, prize, activity, gear = f["hero"], f["parent"], f["friend"], f["prize"], f["activity"], f["gear"]
    return [
        QAItem(
            question=f"What did {hero.id} want to do with the {prize.label}?",
            answer=f"{hero.id} wanted to {activity.verb}, but the wheel had to be fixed first.",
        ),
        QAItem(
            question=f"Why did {parent.id} stop the play for a moment?",
            answer=f"{parent.id} noticed a wobble and knew the wheel needed reinforcement before it could be used safely.",
        ),
        QAItem(
            question=f"What helped the story end happily?",
            answer=f"{gear.label} strengthened the wheel, and then {hero.id} and {friend.id} shared the wagon by turns.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does it mean to reinforce something?",
            answer="To reinforce something means to make it stronger so it can hold up better and last longer.",
        ),
        QAItem(
            question="What is a wheel for?",
            answer="A wheel helps something roll and move more easily along the ground.",
        ),
        QAItem(
            question="What does sharing mean?",
            answer="Sharing means taking turns or letting someone else use something too.",
        ),
        QAItem(
            question="What is foreshadowing?",
            answer="Foreshadowing is a small clue early in a story that hints something important may happen later.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What does it mean to reinforce something?", answer="To reinforce something means to make it stronger so it can hold up better and last longer."),
        QAItem(question="What is a wheel for?", answer="A wheel helps something roll and move more easily along the ground."),
        QAItem(question="What does sharing mean?", answer="Sharing means taking turns or letting someone else use something too."),
        QAItem(question="What is foreshadowing?", answer="Foreshadowing is a small clue early in a story that hints something important may happen later."),
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
        lines.append(f"  {e.id:8} ({e.type}) meters={ {k:v for k,v in e.meters.items() if v} } memes={ {k:v for k,v in e.memes.items() if v} }")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


ASP_RULES = r"""
wobbling(wheel) :- wheel_fact(wheel), wobble(wheel).
needs_reinforce(wheel) :- wobbling(wheel).
shared_ok(wagon) :- fixed(wheel), shareable(wagon).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    lines.append(asp.fact("wheel_fact", "wheel"))
    lines.append(asp.fact("wobble", "wheel"))
    lines.append(asp.fact("shareable", "wagon"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show needs_reinforce/1.\n#show shared_ok/1."))
    atoms = set(asp.atoms(model, "needs_reinforce")) | set(asp.atoms(model, "shared_ok"))
    py = {("needs_reinforce", "wheel"), ("shared_ok", "wagon")}
    if atoms == py:
        print("OK: ASP and Python agree.")
        return 0
    print("MISMATCH:")
    print("  asp:", sorted(atoms))
    print("  py :", sorted(py))
    return 1


def asp_valid_combos() -> list[tuple]:
    return valid_combos()


def asp_valid_stories() -> list[tuple]:
    return [(p, a, pr, "girl") for (p, a, pr) in valid_combos()] + [(p, a, pr, "boy") for (p, a, pr) in valid_combos()]


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
    StoryParams(place="garage", activity="roll", prize="wagon", name="Lily", gender="girl", parent="Mom", friend="Nina", trait="curious"),
    StoryParams(place="workshop", activity="roll", prize="cart", name="Leo", gender="boy", parent="Dad", friend="Ollie", trait="playful"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.verify:
        sys.exit(asp_verify())
    if args.show_asp:
        print(asp_program("#show needs_reinforce/1.\n#show shared_ok/1."))
        return
    if args.asp:
        print(f"{len(asp_valid_combos())} valid combos")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
