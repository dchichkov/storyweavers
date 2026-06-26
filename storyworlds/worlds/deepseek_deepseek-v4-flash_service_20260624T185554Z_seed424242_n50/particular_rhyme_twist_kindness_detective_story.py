#!/usr/bin/env python3
"""
storyworlds/worlds/particular_rhyme_twist_kindness_detective_story.py
=====================================================================

A small simulated story domain: a child detective solves a missing-pie
mystery with a twist and a kindness resolution.  The style is child-friendly
detective story with occasional rhyme.  The seed word "particular" appears.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


# ---------------------------------------------------------------------------
# Entity
# ---------------------------------------------------------------------------
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
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "grandma", "aunt"}
        male = {"boy", "father", "grandpa", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

    @property
    def label_word(self) -> str:
        return {"grandma": "nana", "suspect_fox": "fox", "suspect_owl": "owl"}.get(self.type, self.type)


# ---------------------------------------------------------------------------
# Parametrization knobs
# ---------------------------------------------------------------------------
@dataclass
class Setting:
    place: str = "the meadow"
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
    guards: set[str]
    prep: str
    tail: str
    plural: bool = False


# ---------------------------------------------------------------------------
# World
# ---------------------------------------------------------------------------
class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.zone: set[str] = set()
        self.weather: str = ""
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
        chunks = [" ".join(p) for p in self.paragraphs if p]
        return "\n\n".join(chunks)

    def copy(self) -> "World":
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.zone = set(self.zone)
        clone.weather = self.weather
        clone.paragraphs = [[]]
        return clone


# ---------------------------------------------------------------------------
# Causal rules
# ---------------------------------------------------------------------------
@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_suspicion(world: World) -> list[str]:
    """When the detective finds a clue pointing at a suspect, suspicion rises."""
    out = []
    for actor in world.characters():
        if actor.meters["clue_found"] >= THRESHOLD:
            for suspect in world.characters():
                if suspect.kind != "suspect":
                    continue
                if suspect.meters["blamed"] < THRESHOLD and actor.memes["suspicion"] > 0:
                    sig = ("suspect", suspect.id)
                    if sig not in world.fired:
                        world.fired.add(sig)
                        suspect.meters["blamed"] += 1
                        out.append(f"{suspect.label_word} looked a little guilty.")
    return out


def _r_twist(world: World) -> list[str]:
    """When kindness is offered, the true kind intent is revealed."""
    out = []
    for suspect in world.characters():
        if suspect.kind != "suspect":
            continue
        if world.facts.get("kind_offer", False) and suspect.meters["blamed"] >= THRESHOLD:
            sig = ("twist", suspect.id)
            if sig not in world.fired:
                world.fired.add(sig)
                suspect.memes["innocent"] += 1
                out.append("__twist__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="suspicion", tag="detective", apply=_r_suspicion),
    Rule(name="twist", tag="kindness", apply=_r_twist),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if s != "__twist__")
    if narrate:
        for s in produced:
            world.say(s)
    return produced


# ---------------------------------------------------------------------------
# Constraint helpers
# ---------------------------------------------------------------------------
def clue_points_to(suspect: str, setting: Setting) -> bool:
    """Clue type depends on setting."""
    return True  # simplified, always plausible


def select_gear(activity: Activity, prize: Prize) -> Optional[Gear]:
    for gear in GEAR:
        if activity.mess in gear.guards and prize.region in gear.covers:
            return gear
    return None


# ---------------------------------------------------------------------------
# Story verbs
# ---------------------------------------------------------------------------
def introduce_detective(world: World, hero: Entity) -> None:
    world.say(f"{hero.id} was a little {hero.type} detective with a nose for clues.")
    world.say("On a particular morning, Grandma baked a sweet berry pie.")


def loves_mysteries(world: World, hero: Entity) -> None:
    world.say(f"{hero.pronoun().capitalize()} loved mysteries — they rhymed and twisted like a tale.")


def arrival(world: World, hero: Entity, parent: Entity, setting: Setting) -> None:
    world.say(f"One {world.weather} day, {hero.id} and {hero.pronoun('possessive')} {parent.label_word} went to {setting.place}.")
    world.say("The pie was gone! Only a scarf lay near the table.")


def investigate(world: World, hero: Entity, activity: Activity) -> None:
    hero.meters["clue_found"] += 1
    world.say(f"{hero.id} picked up the scarf and thought, \"This is a clue — whose scarf?\"")
    world.say(f"{hero.pronoun().capitalize()} decided to {activity.verb}.")


def question_suspect(world: World, hero: Entity, suspect: Entity) -> None:
    hero.memes["suspicion"] += 0.5
    world.say(f"{hero.id} went to the {suspect.label_word} and asked, \"Did you take the pie?\"")
    world.say(f"The {suspect.label_word} looked away. \"I… it's not what you think,\" {suspect.pronoun()} said.")


def blame_suspect(world: World, hero: Entity, suspect: Entity) -> None:
    hero.memes["suspicion"] += 1
    world.say(f"\"I think you did it!\" {hero.id} declared. But something felt off.")


def twist_reveal(world: World, hero: Entity, suspect: Entity, prize: Prize) -> None:
    world.say(f"Then the {suspect.label_word} whispered, \"I found the pie earlier — I wanted to share it with everyone.\"")
    world.say(f"\"Oh!\" {hero.id} gasped. \"You were being kind, not stealing!\"")
    world.say(f"The {suspect.label_word} smiled and pointed to a basket where the {prize.label} sat safely.")


def kindness_resolve(world: World, hero: Entity, parent: Entity, suspect: Entity, prize: Prize) -> None:
    world.facts["kind_offer"] = True
    hero.memes["joy"] += 1
    hero.memes["suspicion"] = 0
    world.say(f"{hero.id} hugged the {suspect.label_word}. {hero.pronoun().capitalize()} said, \"Let's share the pie together!\"")
    world.say(f"Grandma smiled. They all ate warm berry pie and laughed under the sun.")
    world.say(f"{hero.id} learned that a twist can hide kindness, and a detective's best tool is an open heart.")


# ---------------------------------------------------------------------------
# Tell
# ---------------------------------------------------------------------------
def tell(setting: Setting, activity: Activity, prize_cfg: Prize,
         hero_name: str = "Sam", hero_type: str = "boy",
         hero_traits: list[str] = None, parent_type: str = "mother",
         suspect_type: str = "fox") -> World:
    if hero_traits is None:
        hero_traits = ["curious", "clever"]
    world = World(setting)
    world.weather = "sunny"

    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type,
                            traits=["little"] + hero_traits))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label="the parent"))
    suspect = world.add(Entity(id="Suspect", kind="suspect", type="suspect_" + suspect_type,
                               label=suspect_type, traits=["shy", "kind"]))
    prize = world.add(Entity(id="prize", type=prize_cfg.type, label=prize_cfg.label,
                             phrase=prize_cfg.phrase, owner="Grandma", caretaker=parent.id,
                             region=prize_cfg.region, plural=prize_cfg.plural))

    # Act 1
    introduce_detective(world, hero)
    loves_mysteries(world, hero)

    # Act 2
    world.para()
    arrival(world, hero, parent, setting)
    investigate(world, hero, activity)
    world.para()
    question_suspect(world, hero, suspect)
    blame_suspect(world, hero, suspect)
    propagate(world)

    # Act 3
    world.para()
    twist_reveal(world, hero, suspect, prize)
    kindness_resolve(world, hero, parent, suspect, prize)
    propagate(world)

    world.facts.update(hero=hero, parent=parent, prize=prize, prize_cfg=prize_cfg,
                       activity=activity, setting=setting, suspect=suspect,
                       suspect_type=suspect_type)
    return world


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "meadow": Setting(place="the meadow", affords={"investigate"}),
    "kitchen": Setting(place="Grandma's kitchen", affords={"investigate"}),
    "garden": Setting(place="the garden", affords={"investigate"}),
}

ACTIVITIES = {
    "investigate": Activity(
        id="investigate",
        verb="follow the clue",
        gerund="following clues",
        rush="hunt for clues",
        mess="clue",
        soil="found the scarf",
        zone={"hands"},
        keyword="clue",
        tags={"mystery"},
    ),
}

PRIZES = {
    "pie": Prize(label="pie", phrase="a warm berry pie", type="pie", region="table", genders={"girl", "boy"}),
    "cake": Prize(label="cake", phrase="a chocolate cake", type="cake", region="table", genders={"girl", "boy"}),
}

GEAR = [
    Gear(id="magnifier", label="a magnifying glass", covers={"hands"}, guards={"clue"},
         prep="use my magnifying glass",
         tail="used the magnifying glass")
]

SUSPECTS = ["fox", "owl", "rabbit"]

GIRL_NAMES = ["Emma", "Lily", "Mia", "Zoe"]
BOY_NAMES = ["Sam", "Max", "Leo", "Noah"]
TRAITS = ["curious", "brave", "kind", "clever"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place in SETTINGS:
        for act_id in SETTINGS[place].affords:
            act = ACTIVITIES[act_id]
            for prize_id, prize in PRIZES.items():
                combos.append((place, act_id, prize_id))
    return combos


# ---------------------------------------------------------------------------
# StoryParams
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    name: str
    gender: str
    parent: str
    trait: str
    suspect: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
KNOWLEDGE = {
    "mystery": [("What is a mystery?", "A mystery is a puzzle where you must find the truth.")],
    "clue": [("What is a clue?", "A clue is a small piece of information that helps solve a mystery.")],
    "detective": [("What does a detective do?", "A detective looks for clues and asks questions to solve a case.")],
    "kindness": [("Why is kindness important?", "Kindness helps everyone feel good and can turn a problem into a happy ending.")],
}
KNOWLEDGE_ORDER = ["mystery", "clue", "detective", "kindness"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, parent, act, prize = f["hero"], f["parent"], f["activity"], f["prize_cfg"]
    return [
        f"Write a short detective story for children that includes the word '{act.keyword}' and ends with a kind twist.",
        f"Tell a story where a little detective named {hero.id} solves a missing {prize.label} mystery with a surprise.",
        f"A story about a curious child, a missing {prize.label}, and a lesson in kindness.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, parent, prize, act = f["hero"], f["parent"], f["prize"], f["activity"]
    suspect = f["suspect"]
    sub, pos = (hero.pronoun("subject"), hero.pronoun("possessive"))
    qa = [
        QAItem(
            question=f"Who is the detective in the story?",
            answer=f"The detective is a little {hero.type} named {hero.id}. {sub} loves solving mysteries."
        ),
        QAItem(
            question=f"What was missing in {hero.id}'s story?",
            answer=f"{pos.capitalize()} grandma's {prize.label} was missing from {f['setting'].place}."
        ),
        QAItem(
            question=f"Who did {hero.id} first suspect?",
            answer=f"{sub.capitalize()} suspected the {f['suspect_type']} because of a scarf clue."
        ),
        QAItem(
            question=f"What twist happened at the end?",
            answer=f"The {f['suspect_type']} had actually found the {prize.label} and wanted to share it. {sub} learned that kindness was the real answer."
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = world.facts["activity"].tags
    out = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags or tag == "kindness":
            out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE[tag])
    return out


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


# ---------------------------------------------------------------------------
# CLI / trace
# ---------------------------------------------------------------------------
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
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="meadow", activity="investigate", prize="pie", name="Sam",
                gender="boy", parent="mother", trait="curious", suspect="fox"),
    StoryParams(place="kitchen", activity="investigate", prize="cake", name="Mia",
                gender="girl", parent="mother", trait="brave", suspect="owl"),
    StoryParams(place="garden", activity="investigate", prize="pie", name="Noah",
                gender="boy", parent="father", trait="clever", suspect="rabbit"),
]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% Valid combination: any setting and prize is fine, but we need gear.
valid(Place, A, P) :- setting(Place), activity(A), prize(P).
% For simplicity, all combos valid with any suspect.
valid_story(Place, A, P, G) :- valid(Place, A, P), gender(G).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid in SETTINGS:
        lines.append(asp.fact("setting", pid))
    for aid in ACTIVITIES:
        lines.append(asp.fact("activity", aid))
    for pid in PRIZES:
        lines.append(asp.fact("prize", pid))
        for g in PRIZES[pid].genders:
            lines.append(asp.fact("gender", g, pid))
    return "\n".join(lines)


def asp_verify() -> int:
    import asp
    py_combos = set(valid_combos())
    asp_prog = asp_facts() + "\n" + ASP_RULES + "\n#show valid/3.\n"
    model = asp.one_model(asp_prog)
    asp_combos = set(asp.atoms(model, "valid")) if model else set()
    if py_combos == asp_combos:
        print(f"OK: clingo gate matches valid_combos() ({len(py_combos)} combos).")
        return 0
    print("MISMATCH")
    return 1


# ---------------------------------------------------------------------------
# Standard storyworld interface
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Detective story world: a missing pie, a twist, kindness.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--suspect", choices=SUSPECTS)
    ap.add_argument("--name")
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    # ASP modes
    ap.add_argument("--asp", action="store_true", help="list valid combos (no gender check)")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_combos()
    if args.place:
        combos = [c for c in combos if c[0] == args.place]
    if args.activity:
        combos = [c for c in combos if c[1] == args.activity]
    if args.prize:
        combos = [c for c in combos if c[2] == args.prize]
    if not combos:
        raise StoryError("No valid combination.")
    place, activity, prize_id = rng.choice(sorted(combos))
    prize = PRIZES[prize_id]
    gender = args.gender or rng.choice(sorted(prize.genders))
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    suspect = args.suspect or rng.choice(SUSPECTS)
    return StoryParams(place=place, activity=activity, prize=prize_id,
                       name=name, gender=gender, parent=parent, trait=trait,
                       suspect=suspect)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], ACTIVITIES[params.activity],
                 PRIZES[params.prize], params.name, params.gender,
                 [params.trait], params.parent, params.suspect)
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
        print(asp_facts() + ASP_RULES + "\n#show valid_story/4.")
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("Valid combos (place, activity, prize):")
        for c in sorted(valid_combos()):
            print(f"  {c[0]:9} {c[1]:11} {c[2]}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: missing {p.prize} at {p.place} (suspect: {p.suspect})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
