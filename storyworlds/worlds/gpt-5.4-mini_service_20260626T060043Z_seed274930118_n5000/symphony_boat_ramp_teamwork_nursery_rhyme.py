#!/usr/bin/env python3
"""
symphony_boat_ramp_teamwork_nursery_rhyme.py
============================================

A small storyworld about a symphony at the boat ramp, where teamwork helps a
little group keep the music going in a nursery-rhyme style.

The seed premise:
- A child or small crew wants to make a symphony near a boat ramp.
- A problem arises because the ramp is slippery, the stage gear is awkward, or
  the music stand drifts.
- Teamwork lets everyone use simple, coordinated actions to finish the song.

The world model tracks:
- physical meters: balance, wetness, drift, load, progress, harmony
- emotional memes: worry, trust, joy, pride, focus, teamwork

The prose is driven by state changes, not a frozen paragraph.
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
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    carried_by: Optional[str] = None
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
    place: str = "the boat ramp"
    affords: set[str] = field(default_factory=set)
    waterside: bool = True


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    mess: str
    soil: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Gear:
    id: str
    label: str
    prep: str
    tail: str
    guards: set[str] = field(default_factory=set)
    helps: set[str] = field(default_factory=set)
    plural: bool = False


@dataclass
class StoryParams:
    place: str
    activity: str
    gear: str
    name: str
    gender: str
    helper: str
    trait: str
    seed: Optional[int] = None


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


SETTINGS = {
    "boat_ramp": Setting(place="the boat ramp", affords={"symphony"}, waterside=True),
}

ACTIVITIES = {
    "symphony": Activity(
        id="symphony",
        verb="play a symphony",
        gerund="playing a symphony",
        rush="hurry to the ramp",
        mess="drift",
        soil="all out of order",
        keyword="symphony",
        tags={"music", "teamwork"},
    ),
}

GEAR = {
    "sandbags": Gear(
        id="sandbags",
        label="sandbags",
        prep="set out the sandbags together",
        tail="lined up the sandbags by the edge",
        guards={"drift", "slip"},
        helps={"balance"},
        plural=True,
    ),
    "music_stand": Gear(
        id="music_stand",
        label="a music stand with a wide base",
        prep="steady the music stand first",
        tail="kept the music stand steady",
        guards={"drift"},
    ),
    "rope": Gear(
        id="rope",
        label="a short rope",
        prep="tie the little cart with a short rope",
        tail="tied the little cart safely",
        guards={"drift"},
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Ava", "Zoe", "Nora", "Ruby"]
BOY_NAMES = ["Leo", "Finn", "Theo", "Max", "Sam", "Eli"]
TRAITS = ["cheery", "curious", "brave", "gentle", "busy", "lively"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A nursery-rhyme storyworld about teamwork at the boat ramp.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--gear", choices=GEAR)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--helper", choices=["mother", "father", "friend", "grandparent"])
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


def _default_name(gender: str, rng: random.Random) -> str:
    return rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or "boat_ramp"
    activity = args.activity or "symphony"
    gear = args.gear or rng.choice(list(GEAR))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or _default_name(gender, rng)
    helper = args.helper or rng.choice(["mother", "father", "friend", "grandparent"])
    trait = args.trait or rng.choice(TRAITS)
    if place not in SETTINGS:
        raise StoryError("The boat ramp is the only setting in this little world.")
    if activity != "symphony":
        raise StoryError("This world only supports a symphony story.")
    if gear not in GEAR:
        raise StoryError("Unknown gear choice.")
    return StoryParams(place=place, activity=activity, gear=gear, name=name, gender=gender, helper=helper, trait=trait)


def _meter(e: Entity, key: str, delta: float) -> None:
    e.meters[key] = e.meters.get(key, 0.0) + delta


def _meme(e: Entity, key: str, delta: float) -> None:
    e.memes[key] = e.memes.get(key, 0.0) + delta


def _propagate(world: World) -> None:
    crew = [e for e in world.entities.values() if e.kind == "character"]
    for c in crew:
        if c.meters.get("balance", 0) < THRESHOLD and c.memes.get("teamwork", 0) >= THRESHOLD:
            sig = ("steady", c.id)
            if sig not in world.fired:
                world.fired.add(sig)
                _meter(c, "balance", 1)
                _meme(c, "joy", 1)
                world.say(f"Together, they found their feet and stood as steady as a row of reeds.")
    stage = world.entities.get("stage")
    if stage and stage.meters.get("drift", 0) >= THRESHOLD and any(e.meters.get("balance", 0) >= THRESHOLD for e in crew):
        sig = ("stabilize", stage.id)
        if sig not in world.fired:
            world.fired.add(sig)
            stage.meters["drift"] = 0
            world.say("The little stage stopped wobbling when everyone held one side and then the other.")


def _rhyme_opening(hero: Entity, helper: Entity, setting: Setting) -> str:
    return (
        f"At {setting.place}, where the water lapped low, {hero.id} was a {hero.pronoun('subject')} with a heart aglow. "
        f"{hero.pronoun('subject').capitalize()} loved a symphony bright and clear, and {helper.id} came near with a smile so dear."
    )


def _do_setup(world: World, hero: Entity, helper: Entity, activity: Activity) -> None:
    world.say(_rhyme_opening(hero, helper, world.setting))
    world.say(f"{hero.pronoun('subject').capitalize()} loved {activity.gerund}; the notes went up like birds in spring.")
    world.say(f"{helper.id} brought a tiny stage cart and said, \"We can make it work if we all help sing.\"")


def _need(team: Entity, gear: Entity) -> None:
    _meme(team, "worry", 1)
    _meter(team, "balance", 0)
    _meter(gear, "drift", 1)


def _problem(world: World, hero: Entity, helper: Entity, stage: Entity) -> None:
    _meme(hero, "worry", 1)
    _meme(helper, "focus", 1)
    stage.meters["drift"] = 1
    world.say(f"But the ramp was slick, and the music stand slid with a wink and a skip.")
    world.say(f"{hero.id} wanted to rush, yet {helper.id} held up a hand and said, \"Slow is how we go.\"")


def _teamwork_fix(world: World, hero: Entity, helper: Entity, stage: Entity, gear: Gear) -> None:
    _meme(hero, "teamwork", 1)
    _meme(helper, "teamwork", 1)
    _meme(hero, "trust", 1)
    _meme(helper, "trust", 1)
    world.say(f"Then they {gear.prep}, one-two-three, and each small job fit perfectly.")
    world.say(f"{helper.id} held the cart, {hero.id} held the score, and the others kept watch by the shore.")
    world.say(f"With their shared care, they {gear.tail}, and the little stage stood firm once more.")
    _propagate(world)
    _meme(hero, "joy", 1)
    _meme(helper, "joy", 1)
    _meme(hero, "pride", 1)
    _meme(helper, "pride", 1)
    world.say(f"At last the symphony rang out sweet, and the ramp seemed to tap along with their feet.")
    world.say(f"{hero.id} smiled wide; the tune floated clean, as neat as a ribbon and bright as a bean.")


def tell_world(params: StoryParams) -> World:
    world = World(SETTINGS[params.place])
    hero = world.add(Entity(id=params.name, kind="character", type=params.gender, label=params.name))
    helper = world.add(Entity(id=params.helper, kind="character", type="adult", label=params.helper))
    stage = world.add(Entity(id="stage", type="thing", label="music stand cart"))
    gear = world.add(Entity(id=params.gear, type="thing", label=GEAR[params.gear].label))
    _do_setup(world, hero, helper, ACTIVITIES[params.activity])
    world.para()
    _problem(world, hero, helper, stage)
    world.say(f"That was when they chose {gear.label}, because teamwork can turn a wobble into a song.")
    world.para()
    _teamwork_fix(world, hero, helper, stage, GEAR[params.gear])
    world.facts.update(hero=hero, helper=helper, stage=stage, gear=gear, activity=ACTIVITIES[params.activity], setting=world.setting)
    return world


def valid_combos() -> list[tuple[str, str, str]]:
    return [("boat_ramp", "symphony", gear_id) for gear_id in GEAR]


def generate(params: StoryParams) -> StorySample:
    world = tell_world(params)
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
    hero = f["hero"]
    helper = f["helper"]
    act = f["activity"]
    return [
        "Write a nursery-rhyme style story about teamwork at a boat ramp.",
        f"Tell a gentle tale where {hero.id} and {helper.id} work together to keep a {act.keyword} from wobbling.",
        "Make the ending cheerful, musical, and easy for small children to follow.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    gear = f["gear"]
    return [
        QAItem(
            question=f"Who was the story about?",
            answer=f"It was about {hero.id}, who came to the boat ramp with {helper.id} to make a symphony.",
        ),
        QAItem(
            question=f"What problem made the music hard at first?",
            answer="The ramp was slick, so the music stand and cart wanted to slide and wobble.",
        ),
        QAItem(
            question=f"What helped the group fix the problem?",
            answer=f"They used {gear.label} and careful teamwork, with everyone doing a small job.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer="The stage stood steady, the symphony rang out, and everyone felt happy and proud.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is teamwork?",
            answer="Teamwork means people work together and help each other to finish something.",
        ),
        QAItem(
            question="What is a symphony?",
            answer="A symphony is a long piece of music played by a group of instruments together.",
        ),
        QAItem(
            question="What is a boat ramp?",
            answer="A boat ramp is a sloped place where boats can move into or out of the water.",
        ),
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
    lines.append("== (3) World knowledge ==")
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
        lines.append(f"  {e.id:10} ({e.type}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
% Facts are emitted from registries.
% valid_story(P,A,G) holds when the place supports the activity and the gear is available.
valid_story(P,A,G) :- setting(P), affords(P,A), gear(G).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        for a in sorted(setting.affords):
            lines.append(asp.fact("affords", pid, a))
    for aid in ACTIVITIES:
        lines.append(asp.fact("activity", aid))
    for gid in GEAR:
        lines.append(asp.fact("gear", gid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_stories())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    if py - cl:
        print("  only in python:", sorted(py - cl))
    return 1


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
        stories = asp_valid_stories()
        print(f"{len(stories)} compatible stories:")
        for t in stories:
            print(" ", t)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for gear in GEAR:
            params = StoryParams(place="boat_ramp", activity="symphony", gear=gear, name="Lily", gender="girl", helper="mother", trait="cheery")
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            i += 1
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
