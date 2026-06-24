#!/usr/bin/env python3
"""
A tiny storyworld for thyme, promises, and comic repetition.

Seed tale:
A child promises to help with a thyme pot on the kitchen windowsill. The child
keeps repeating the promise, but gets distracted by a little comedy of near-misses
until the promise is finally kept in a funny, satisfying way.

The world tracks:
- physical state: thirsty thyme, water, spoon, bowl, crumbs
- emotional state: promise, worry, patience, laughter, relief

Narrative shape:
- Setup: someone loves thyme and makes a promise
- Tension: the promise is repeated while a comic distraction loop grows
- Turn: the helper uses a simple method
- Resolution: the thyme is saved and the repeated promise becomes true
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
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the kitchen"
    window: bool = True
    affords: set[str] = field(default_factory=set)


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    label: str
    phrase: str
    type: str
    needy: str = "thirsty"


@dataclass
class Helper:
    id: str
    label: str
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
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        return clone

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]


def build_registry():
    settings = {
        "kitchen": Setting(place="the kitchen", window=True, affords={"water"}),
        "garden": Setting(place="the garden", window=True, affords={"water"}),
    }
    activities = {
        "water": Activity(
            id="water",
            verb="water the thyme",
            gerund="watering the thyme",
            rush="dash to the sink",
            keyword="thyme",
            tags={"thyme", "water", "herb"},
        ),
    }
    prizes = {
        "thyme": Prize(label="thyme", phrase="a little thyme pot", type="plant"),
    }
    helpers = {
        "cup": Helper(
            id="cup",
            label="small cup",
            prep="fill a small cup with water first",
            tail="filled the cup, walked back, and poured it slowly",
        ),
        "spoon": Helper(
            id="spoon",
            label="tiny spoon",
            prep="use a tiny spoon for careful watering",
            tail="used the spoon like a very serious rain cloud",
        ),
    }
    return settings, activities, prizes, helpers


SETTINGS, ACTIVITIES, PRIZES, HELPERS = build_registry()

GIRL_NAMES = ["Mia", "Nora", "Lily", "Ava", "Zoe"]
BOY_NAMES = ["Leo", "Ben", "Finn", "Max", "Theo"]
TRAITS = ["cheerful", "curious", "silly", "gentle", "bouncy"]


def is_reasonable(activity: Activity, prize: Prize) -> bool:
    return activity.keyword in prize.label and activity.id == "water"


def choose_helper(activity: Activity, prize: Prize) -> Optional[Helper]:
    if activity.id == "water" and prize.label == "thyme":
        return HELPERS["cup"]
    return None


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            act = ACTIVITIES[act_id]
            for prize_id, prize in PRIZES.items():
                if is_reasonable(act, prize):
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
    trait: str
    seed: Optional[int] = None


def setting_detail(setting: Setting) -> str:
    return f"{setting.place.capitalize()} had a sunny windowsill waiting for little things."


def introduce(world: World, hero: Entity, prize: Entity) -> None:
    world.say(
        f"{hero.id} was a little {next(t for t in hero.meters.keys() if False)}"
    )


def tell(setting: Setting, activity: Activity, prize_cfg: Prize,
         hero_name: str = "Mia", hero_type: str = "girl",
         hero_traits: Optional[list[str]] = None, parent_type: str = "mother") -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label="the parent"))
    thyme = world.add(Entity(
        id="thyme",
        kind="thing",
        type="plant",
        label="thyme",
        phrase="a little thyme pot",
        owner=hero.id,
        caretaker=parent.id,
        meters={"thirst": 2.0, "freshness": 0.5},
        memes={"hope": 1.0},
    ))
    water = world.add(Entity(id="water", kind="thing", type="water", label="water"))
    helper = world.add(Entity(id="cup", kind="thing", type="cup", label="small cup"))

    hero.memes["promise"] = 0.0
    hero.memes["laughter"] = 0.0
    parent.memes["worry"] = 1.0
    parent.memes["patience"] = 1.0

    trait = (hero_traits or ["cheerful"])[0]
    world.say(
        f"{hero.id} was a {trait} {hero.type} who loved the smell of thyme."
    )
    world.say(
        f"{hero.id} kept a little thyme pot on the windowsill and promised to take care of it."
    )

    world.para()
    world.say(setting_detail(setting))
    world.say(
        f"One day, {hero.id} said, \"I promise I will water the thyme.\""
    )
    hero.memes["promise"] += 1
    world.say(
        f"Then {hero.id} said it again, just to be extra sure: \"I promise, I promise.\""
    )
    hero.memes["promise"] += 1

    world.para()
    thyme.meters["thirst"] += 1.0
    hero.memes["distract"] = 1.0
    world.say(
        f"But first {hero.id} found a spoon, then a cup, then a crumb on the floor."
    )
    world.say(
        f"That made {hero.id} giggle, because the crumb looked like a tiny hat."
    )
    hero.memes["laughter"] += 1
    parent.memes["worry"] += 1
    world.say(
        f"\"The thyme is still thirsty,\" {parent.pronoun().capitalize()} reminded {hero.id}, "
        f"and {hero.id} repeated, \"I promise, I promise.\""
    )

    world.para()
    helper_def = choose_helper(activity, prize_cfg)
    if helper_def is None:
        raise StoryError("No reasonable helper exists for this promise story.")
    world.say(
        f"At last, {hero.id}'s {parent.label} smiled and said to {hero.id}, "
        f"\"Let's {helper_def.prep}.\""
    )
    world.say(
        f"{hero.id} nodded, marched to the sink, and came back very carefully."
    )
    world.say(
        f"{hero.id} {helper_def.tail}, and the water made the thyme perk up."
    )
    thyme.meters["thirst"] = max(0.0, thyme.meters["thirst"] - 2.0)
    thyme.meters["freshness"] += 2.0
    hero.memes["promise"] += 1
    hero.memes["relief"] = 1.0
    parent.memes["worry"] = 0.0
    parent.memes["laughter"] = 1.0

    world.para()
    world.say(
        f"\"I did it,\" {hero.id} said, and then grinned. \"I really did it.\""
    )
    world.say(
        f"The thyme stood green and happy, and the whole kitchen felt funny and warm."
    )
    world.facts.update(
        hero=hero,
        parent=parent,
        thyme=thyme,
        helper=helper,
        activity=activity,
        setting=setting,
        resolved=True,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    return [
        'Write a short comedy story for a young child that includes the word "thyme".',
        f"Tell a funny story where {hero.id} makes a promise to help a plant and keeps repeating the promise.",
        "Write a gentle repetitive story about a child, a thyme pot, and a promise kept with care.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    parent = f["parent"]
    thyme = f["thyme"]
    return [
        QAItem(
            question=f"What did {hero.id} promise to do?",
            answer=f"{hero.id} promised to water the thyme pot on the windowsill.",
        ),
        QAItem(
            question=f"Why did {parent.label} remind {hero.id} about the thyme?",
            answer=f"The thyme was thirsty, so {parent.label} wanted {hero.id} to water it before it got too dry.",
        ),
        QAItem(
            question=f"What made the story funny?",
            answer=f"{hero.id} kept repeating the promise and got distracted by tiny things, like a spoon and a crumb that looked like a little hat.",
        ),
        QAItem(
            question=f"What changed by the end?",
            answer=f"The thyme was watered, it looked green and happy, and the promise was finally kept.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is thyme?",
            answer="Thyme is a small herb with tiny leaves that people use for cooking because it smells nice and tastes good.",
        ),
        QAItem(
            question="What is a promise?",
            answer="A promise is a thing someone says they will do, and good promises are kept.",
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
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
promised(H) :- hero(H), says_promise(H).
repeated(H) :- promised(H), repeats_promise(H).
comic(H) :- repeated(H), distracted_by_small_thing(H).
resolved(H) :- comic(H), waters_thyme(H).

#show promised/1.
#show repeated/1.
#show comic/1.
#show resolved/1.
"""


def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("hero", "hero"),
        asp.fact("says_promise", "hero"),
        asp.fact("repeats_promise", "hero"),
        asp.fact("distracted_by_small_thing", "hero"),
        asp.fact("waters_thyme", "hero"),
    ]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program(""))
    atoms = {sym.name for sym in model}
    expected = {"promised", "repeated", "comic", "resolved"}
    if expected.issubset(atoms):
        print("OK: ASP comic-promise chain is reachable.")
        return 0
    print("MISMATCH: ASP chain did not derive all expected atoms.")
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Story world: thyme, promise, repetition, comedy.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
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
    combos = valid_combos()
    if not combos:
        raise StoryError("No valid thyme story combos available.")
    place, activity, prize = rng.choice(combos)
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, activity=activity, prize=prize, name=name, gender=gender, parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.place],
        ACTIVITIES[params.activity],
        PRIZES[params.prize],
        params.name,
        params.gender,
        [params.trait],
        params.parent,
    )
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
        print(asp_program(""))
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for p in [StoryParams("kitchen", "water", "thyme", "Mia", "girl", "mother", "cheerful")]:
            samples.append(generate(p))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 20, 20):
            i += 1
            seed = base_seed + i
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
