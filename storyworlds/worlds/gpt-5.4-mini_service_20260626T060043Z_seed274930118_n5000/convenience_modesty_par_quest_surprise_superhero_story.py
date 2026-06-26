#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/convenience_modesty_par_quest_surprise_superhero_story.py
================================================================================================

A standalone superhero-style storyworld about a young hero, a small quest,
a surprise turn, and a lesson about convenience and modesty.

The simulated domain is intentionally compact:
- a hero wants an easy, convenient way to complete a quest
- a modest helper worries that flashy shortcuts may cause trouble
- a surprise reveals the true need
- the hero chooses a better path, and the ending proves the change

This script follows the Storyweavers world contract:
- self-contained stdlib script
- eager results import, lazy asp import
- StoryParams, registries, build_parser, resolve_params, generate, emit, main
- default run, -n, --all, --seed, --trace, --qa, --json, --asp, --verify, --show-asp
- inline ASP_RULES twin plus Python reasonableness gate
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


# ---------------------------------------------------------------------------
# Entities and world model
# ---------------------------------------------------------------------------
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
    protective: bool = False
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "aunt"}
        male = {"boy", "man", "father", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class Setting:
    place: str
    afford: set[str] = field(default_factory=set)


@dataclass
class Quest:
    id: str
    noun: str
    verb: str
    gerund: str
    rush: str
    risk: str
    goal: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Surprise:
    id: str
    reveal: str
    twist: str
    fix: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Gear:
    id: str
    label: str
    protects: set[str]
    helps: set[str]
    prep: str
    tail: str
    plural: bool = False


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.quest: Optional[Quest] = None
        self.surprise: Optional[Surprise] = None
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
        clone.quest = self.quest
        clone.surprise = self.surprise
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "city_square": Setting(place="the city square", afford={"quest"}),
    "roof": Setting(place="the rooftop", afford={"quest"}),
    "museum": Setting(place="the museum hall", afford={"quest"}),
    "alley": Setting(place="the lantern alley", afford={"quest"}),
}

QUESTS = {
    "parcel": Quest(
        id="parcel",
        noun="parcel",
        verb="carry the parcel",
        gerund="carrying the parcel",
        rush="dash to the courier gate",
        risk="the parcel could slip from the cape",
        goal="deliver it before sunset",
        keyword="parcel",
        tags={"delivery", "fast", "convenience"},
    ),
    "riddle": Quest(
        id="riddle",
        noun="riddle",
        verb="solve the riddle",
        gerund="solving the riddle",
        rush="run to the clue board",
        risk="the clues could scatter in the wind",
        goal="find the hidden key",
        keyword="riddle",
        tags={"brainy", "quest"},
    ),
    "rescue": Quest(
        id="rescue",
        noun="rescue",
        verb="reach the stranded kitten",
        gerund="reaching the stranded kitten",
        rush="climb the fire stairs",
        risk="a shiny shortcut could shake the ladder",
        goal="bring the kitten down safely",
        keyword="kitten",
        tags={"rescue", "gentle"},
    ),
}

SURPRISES = {
    "locker_note": Surprise(
        id="locker_note",
        reveal="a note inside the locker",
        twist="it asked the hero to choose a quieter way",
        fix="use the hidden side stairs",
        tags={"quiet", "modesty"},
    ),
    "masked_helper": Surprise(
        id="masked_helper",
        reveal="a masked helper on the roof",
        twist="the helper had already brought the missing tool",
        fix="share the job and move carefully",
        tags={"helper", "surprise"},
    ),
    "small_alarm": Surprise(
        id="small_alarm",
        reveal="a tiny alarm on the parcel",
        twist="it would chirp if the box bounced too much",
        fix="carry the box with two hands",
        tags={"careful", "convenience"},
    ),
}

GEAR = [
    Gear(
        id="boots",
        label="soft boots",
        protects={"feet"},
        helps={"quest"},
        prep="put on soft boots first",
        tail="walked down the steps in soft boots",
    ),
    Gear(
        id="belt",
        label="a simple utility belt",
        protects={"torso"},
        helps={"quest"},
        prep="clip on a simple utility belt",
        tail="headed out with a simple utility belt",
    ),
    Gear(
        id="gloves",
        label="light gloves",
        protects={"hands"},
        helps={"quest"},
        prep="pull on light gloves",
        tail="set off with light gloves on",
        plural=True,
    ),
    Gear(
        id="plaincloak",
        label="a plain cloak",
        protects={"torso"},
        helps={"modesty"},
        prep="swap the shiny cape for a plain cloak",
        tail="left wearing a plain cloak",
    ),
]

HERO_NAMES = ["Nova", "Milo", "Iris", "Juno", "Theo", "Lena", "Zeke", "Mara"]
HELPER_NAMES = ["Aunt Bea", "Captain Dot", "Bex", "Uncle Ray"]
TRAITS = ["bright", "kind", "bold", "careful", "cheerful", "curious"]


# ---------------------------------------------------------------------------
# World state helpers
# ---------------------------------------------------------------------------
def quest_at_risk(quest: Quest, setting: Setting) -> bool:
    return "quest" in setting.afford


def select_gear(quest: Quest, surprise: Surprise) -> Optional[Gear]:
    for gear in GEAR:
        if "quest" in gear.helps:
            return gear
    return None


def predict_failure(world: World, hero: Entity, quest: Quest, surprise: Surprise) -> bool:
    sim = world.copy()
    _do_quest(sim, sim.get(hero.id), quest, narrate=False)
    return bool(sim.facts.get("quest_risk"))


def _do_quest(world: World, hero: Entity, quest: Quest, narrate: bool = True) -> None:
    if not quest_at_risk(quest, world.setting):
        return
    hero.memes["drive"] = hero.memes.get("drive", 0.0) + 1
    world.facts["quest_risk"] = quest.risk
    if narrate:
        world.say(f"{hero.id} pressed on with {quest.gerund}.")


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.memes.get("rush", 0.0) < THRESHOLD:
            continue
        for item in world.worn_items(actor):
            if item.protective:
                continue
            sig = ("mess", actor.id, item.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            out.append(f"{actor.id}'s {item.label_word} was in the way.")
    if narrate:
        for s in out:
            world.say(s)
    return out


# ---------------------------------------------------------------------------
# Narrative beats
# ---------------------------------------------------------------------------
def introduce(world: World, hero: Entity) -> None:
    world.say(
        f"{hero.id} was a little {hero.memes.get('trait_word', 'bright')} superhero "
        f"who loved helping people in {world.setting.place}."
    )


def setup(world: World, hero: Entity, helper: Entity, quest: Quest, surprise: Surprise) -> None:
    hero.memes["love"] = hero.memes.get("love", 0.0) + 1
    hero.memes["modesty"] = hero.memes.get("modesty", 0.0) + 1
    world.say(
        f"{hero.id} wanted a quick, convenient way to {quest.verb}, because "
        f"{quest.goal} sounded exciting."
    )
    world.say(
        f"{helper.id} smiled and reminded {hero.id} that a real hero also needed "
        f"modesty, not just speed and shine."
    )
    world.say(
        f"The day already felt like a quest, and nobody knew the surprise waiting nearby: "
        f"{surprise.reveal}."
    )


def warning(world: World, hero: Entity, helper: Entity, quest: Quest, surprise: Surprise) -> bool:
    risk = predict_failure(world, hero, quest, surprise)
    if not risk:
        return False
    world.facts["predicted_risk"] = quest.risk
    world.say(
        f'"If you rush," {helper.id} said, "then {quest.risk}."'
    )
    return True


def defy(world: World, hero: Entity, quest: Quest) -> None:
    hero.memes["rush"] = hero.memes.get("rush", 0.0) + 1
    world.say(f"{hero.id} still wanted the easy route and hurried toward the target.")
    world.say(f"{hero.id} tried to {quest.rush}.")


def surprise_turn(world: World, hero: Entity, quest: Quest, surprise: Surprise) -> None:
    world.say(f"Then the surprise appeared: {surprise.reveal}.")
    world.say(f"It changed the plan, because {surprise.twist}.")
    world.facts["surprise_fix"] = surprise.fix


def choose_better_way(world: World, hero: Entity, helper: Entity, quest: Quest, surprise: Surprise) -> None:
    gear = select_gear(quest, surprise)
    if gear is None:
        raise StoryError("No reasonable gear exists for this quest and surprise.")
    gear_ent = world.add(Entity(
        id=gear.id,
        type="gear",
        label=gear.label,
        protective=True,
        owner=hero.id,
        worn_by=hero.id,
        plural=gear.plural,
    ))
    world.say(
        f"{helper.id} offered a quieter plan: {gear.prep}."
    )
    hero.memes["rush"] = 0.0
    hero.memes["modesty"] = hero.memes.get("modesty", 0.0) + 1
    hero.memes["calm"] = hero.memes.get("calm", 0.0) + 1
    world.say(
        f"{hero.id} agreed, because convenience was nice, but {surprise.fix} was wiser."
    )
    world.say(
        f"With {gear_ent.label}, {hero.id} could keep going without showing off."
    )


def resolve(world: World, hero: Entity, helper: Entity, quest: Quest, surprise: Surprise) -> None:
    hero.memes["joy"] = hero.memes.get("joy", 0.0) + 1
    world.say(
        f"In the end, {hero.id} finished {quest.gerund}, and {quest.goal} came true."
    )
    world.say(
        f"{helper.id} laughed softly as {hero.id} returned home wearing the plain, modest look."
    )
    world.say(
        f"The surprise had turned a flashy shortcut into a careful success."
    )


def tell(setting: Setting, quest: Quest, surprise: Surprise, hero_name: str,
         hero_type: str = "girl", helper_name: str = "Aunt Bea",
         helper_type: str = "woman", trait: str = "bright") -> World:
    world = World(setting)
    world.quest = quest
    world.surprise = surprise

    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type=hero_type,
        memes={"trait_word": trait},
    ))
    helper = world.add(Entity(
        id=helper_name,
        kind="character",
        type=helper_type,
        label=helper_name,
    ))

    world.say(
        f"On a sunny day, {hero.id} met {helper.id} in {setting.place}."
    )
    introduce(world, hero)
    world.para()
    setup(world, hero, helper, quest, surprise)
    warning(world, hero, helper, quest, surprise)
    defy(world, hero, quest)
    surprise_turn(world, hero, quest, surprise)
    world.para()
    choose_better_way(world, hero, helper, quest, surprise)
    resolve(world, hero, helper, quest, surprise)

    world.facts.update(hero=hero, helper=helper, quest=quest, surprise=surprise)
    return world


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------
def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for qid, quest in QUESTS.items():
            if not quest_at_risk(quest, setting):
                continue
            for sid in SURPRISES:
                combos.append((place, qid, sid))
    return combos


def explain_rejection(place: str, quest: Quest) -> str:
    return f"(No story: {quest.verb} does not fit the setting at {place}.)"


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
place(P) :- setting(P).
quest_ok(P,Q) :- setting(P), quest(Q), afford(P,quest).
surprise_ok(S) :- surprise(S).

valid(P,Q,S) :- place(P), quest_ok(P,Q), surprise_ok(S).
#show valid/3.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for a in sorted(setting.afford):
            lines.append(asp.fact("afford", sid, a))
    for qid in QUESTS:
        lines.append(asp.fact("quest", qid))
    for sid in SURPRISES:
        lines.append(asp.fact("surprise", sid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    a, b = set(asp_valid_combos()), set(valid_combos())
    if a == b:
        print(f"OK: clingo gate matches valid_combos() ({len(a)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if a - b:
        print("  only in clingo:", sorted(a - b))
    if b - a:
        print("  only in python:", sorted(b - a))
    return 1


# ---------------------------------------------------------------------------
# Params and generation
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    quest: str
    surprise: str
    name: str
    hero_type: str
    helper: str
    helper_type: str
    trait: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Superhero storyworld with a quest, a surprise, convenience, and modesty.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--surprise", choices=SURPRISES)
    ap.add_argument("--name")
    ap.add_argument("--hero-type", choices=["girl", "boy"])
    ap.add_argument("--helper")
    ap.add_argument("--helper-type", choices=["woman", "man"])
    ap.add_argument("--trait", choices=TRAITS)
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
              and (args.quest is None or c[1] == args.quest)
              and (args.surprise is None or c[2] == args.surprise)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, quest, surprise = rng.choice(sorted(combos))
    hero_type = args.hero_type or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(HERO_NAMES)
    helper = args.helper or rng.choice(HELPER_NAMES)
    helper_type = args.helper_type or rng.choice(["woman", "man"])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place, quest, surprise, name, hero_type, helper, helper_type, trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.place],
        QUESTS[params.quest],
        SURPRISES[params.surprise],
        params.name,
        params.hero_type,
        params.helper,
        params.helper_type,
        params.trait,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, helper = f["hero"], f["helper"]
    quest, surprise = f["quest"], f["surprise"]
    return [
        f'Write a short superhero story for a young child about {hero.id}, a {hero.pronoun("subject")} who wants the convenience of a quick way to {quest.verb}, but learns modesty matters too.',
        f"Tell a child-friendly quest story where {helper.id} warns {hero.id} about the risk of rushing, and a surprise changes the plan.",
        f'Write a simple story that includes the words "convenience" and "modesty" and ends with {hero.id} choosing a careful helper-friendly path.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, helper = f["hero"], f["helper"]
    quest, surprise = f["quest"], f["surprise"]
    return [
        QAItem(
            question=f"What did {hero.id} want to do quickly at {world.setting.place}?",
            answer=f"{hero.id} wanted to {quest.verb} quickly because the whole thing felt like a big superhero quest.",
        ),
        QAItem(
            question=f"Why did {helper.id} remind {hero.id} about modesty?",
            answer=f"{helper.id} reminded {hero.id} that a hero should be modest and careful, not only fast and flashy.",
        ),
        QAItem(
            question=f"What surprise changed the plan?",
            answer=f"The surprise was {surprise.reveal}, and it pushed {hero.id} toward a quieter and safer way.",
        ),
        QAItem(
            question=f"How did the story end for {hero.id}?",
            answer=f"{hero.id} chose the better path, finished {quest.gerund}, and came home looking calm and modest.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    out: list[QAItem] = [
        QAItem(
            question="What does convenience mean?",
            answer="Convenience means something is easy to use or saves time and effort.",
        ),
        QAItem(
            question="What does modesty mean?",
            answer="Modesty means not acting like you are better or more important than everyone else.",
        ),
        QAItem(
            question="What is a quest?",
            answer="A quest is a task or journey that someone works hard to finish, often to help someone or find something.",
        ),
        QAItem(
            question="What is a surprise?",
            answer="A surprise is something unexpected that happens or is revealed without warning.",
        ),
    ]
    return out


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
        if e.protective:
            bits.append("protective=True")
        if e.worn_by:
            bits.append(f"worn_by={e.worn_by}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
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
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, quest, surprise) combos:")
        for c in combos:
            print("  ", c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams("city_square", "parcel", "small_alarm", "Nova", "girl", "Aunt Bea", "woman", "bright"),
            StoryParams("roof", "rescue", "masked_helper", "Theo", "boy", "Captain Dot", "man", "careful"),
            StoryParams("museum", "riddle", "locker_note", "Iris", "girl", "Aunt Bea", "woman", "curious"),
        ]
        samples = [generate(p) for p in curated]
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, helper = f["hero"], f["helper"]
    quest, surprise = f["quest"], f["surprise"]
    return [
        f'Write a short superhero story for a young child about {hero.id}, a {hero.pronoun("subject")} who wants the convenience of a quick way to {quest.verb}, but learns modesty matters too.',
        f"Tell a child-friendly quest story where {helper.id} warns {hero.id} about the risk of rushing, and a surprise changes the plan.",
        f'Write a simple story that includes the words "convenience" and "modesty" and ends with {hero.id} choosing a careful helper-friendly path.',
    ]


if __name__ == "__main__":
    main()
