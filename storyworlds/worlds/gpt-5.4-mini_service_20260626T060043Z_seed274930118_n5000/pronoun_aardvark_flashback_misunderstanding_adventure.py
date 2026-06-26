#!/usr/bin/env python3
"""
Story world: an adventure with an aardvark, a pronoun misunderstanding, and a
flashback that reveals how the friends trusted each other all along.

The world is small and classical: a traveler and an aardvark explore a place,
a clue is misunderstood, memory brings the truth back, and the pair makes a
safer choice together.
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
# Core world model
# ---------------------------------------------------------------------------

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    portable: bool = True
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    traits: list[str] = field(default_factory=list)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "aunt"}
        male = {"boy", "man", "father", "uncle"}
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
    danger: str
    zone: set[str]
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Gear:
    id: str
    label: str
    covers: set[str]
    prep: str
    tail: str
    plural: bool = False


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

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
        import copy as _copy

        w = World(self.setting)
        w.entities = _copy.deepcopy(self.entities)
        w.facts = _copy.deepcopy(self.facts)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        return w


@dataclass
class Rule:
    name: str
    apply: callable


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "canyon": Setting(place="the canyon trail", affords={"search", "climb"}),
    "ruins": Setting(place="the old ruins", affords={"search"}),
    "forest": Setting(place="the pine forest", affords={"search", "cross"}),
}

ACTIVITIES = {
    "search": Activity(
        id="search",
        verb="search for the trail marker",
        gerund="searching for the trail marker",
        danger="lost and mixed up",
        zone={"path"},
        keyword="trail",
        tags={"trail", "map"},
    ),
    "cross": Activity(
        id="cross",
        verb="cross the narrow bridge",
        gerund="crossing the narrow bridge",
        danger="wobbly and scary",
        zone={"bridge"},
        keyword="bridge",
        tags={"bridge"},
    ),
    "climb": Activity(
        id="climb",
        verb="climb the rock steps",
        gerund="climbing the rock steps",
        danger="scraped and dusty",
        zone={"rocks"},
        keyword="steps",
        tags={"rocks"},
    ),
}

GEAR = [
    Gear(
        id="lantern",
        label="a bright lantern",
        covers={"path", "bridge", "rocks"},
        prep="carry a bright lantern",
        tail="walked on with the lantern lit",
    ),
    Gear(
        id="rope",
        label="a sturdy rope",
        covers={"bridge", "rocks"},
        prep="tie on a sturdy rope",
        tail="crossed carefully with the rope secured",
    ),
    Gear(
        id="boots",
        label="high boots",
        covers={"path", "rocks"},
        prep="put on high boots",
        tail="kept their feet steady in the dust",
        plural=True,
    ),
]

PRIZES = {
    "map": {
        "label": "map",
        "phrase": "an old paper map with a red line",
        "region": "path",
        "plural": False,
    },
    "compass": {
        "label": "compass",
        "phrase": "a small brass compass",
        "region": "path",
        "plural": False,
    },
}

NAMES = {
    "girl": ["Mina", "Luna", "Tess", "Ivy", "Nora"],
    "boy": ["Jasper", "Owen", "Theo", "Finn", "Eli"],
}
AARDVARK_NAMES = ["Arlo", "Bram", "Milo", "Pip", "Tiko"]
TRAITS = ["brave", "curious", "steady", "eager"]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
prize_at_risk(A, P) :- zone_of(A, Z), prize_zone(P, Z).
has_fix(A, P) :- prize_at_risk(A, P), gear(G), covers(G, Z), zone_of(A, Z).
valid(Place, A, P) :- affords(Place, A), prize_at_risk(A, P), has_fix(A, P).
valid_story(Place, A, P, HeroKind) :- valid(Place, A, P), hero_kind(HeroKind).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if setting.indoor:
            lines.append(asp.fact("indoor", sid))
        for a in sorted(setting.affords):
            lines.append(asp.fact("affords", sid, a))
    for aid, act in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        for z in sorted(act.zone):
            lines.append(asp.fact("zone_of", aid, z))
    for pid, prize in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("prize_zone", pid, prize["region"]))
    for gear in GEAR:
        lines.append(asp.fact("gear", gear.id))
        for z in sorted(gear.covers):
            lines.append(asp.fact("covers", gear.id, z))
    lines.append(asp.fact("hero_kind", "girl"))
    lines.append(asp.fact("hero_kind", "boy"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            act = ACTIVITIES[act_id]
            for prize_id, prize in PRIZES.items():
                if prize["region"] in act.zone and any(prize["region"] in g.covers for g in GEAR):
                    combos.append((place, act_id, prize_id))
    return combos


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


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
# World logic
# ---------------------------------------------------------------------------

def story_prompt_word(activity: Activity) -> str:
    return activity.keyword


def _apply_confusion(world: World) -> list[str]:
    out = []
    hero = world.get("hero")
    aardvark = world.get("aardvark")
    if hero.memes.get("confused", 0) >= THRESHOLD and aardvark.memes.get("misunderstood", 0) >= THRESHOLD:
        sig = ("confusion",)
        if sig not in world.fired:
            world.fired.add(sig)
            hero.memes["worry"] = hero.memes.get("worry", 0) + 1
            aardvark.memes["worry"] = aardvark.memes.get("worry", 0) + 1
            out.append("The misunderstanding made them both feel uneasy.")
    return out


CAUSAL_RULES = [Rule("confusion", _apply_confusion)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def predict_risk(world: World, act: Activity, prize_id: str) -> bool:
    sim = world.copy()
    sim.get("hero").meters[act.id] = sim.get("hero").meters.get(act.id, 0) + 1
    prize = sim.get(prize_id)
    return prize.meters.get("safe", 0) < THRESHOLD and prize["region"] if False else True


def reasonableness_check(setting: Setting, act: Activity, prize: dict) -> bool:
    return act.id in setting.affords and prize["region"] in act.zone and any(prize["region"] in g.covers for g in GEAR)


# ---------------------------------------------------------------------------
# Story rendering
# ---------------------------------------------------------------------------

def tell(setting: Setting, activity: Activity, prize_id: str, hero_name: str, hero_type: str, aardvark_name: str, trait: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id="hero", kind="character", type=hero_type, label=hero_name, traits=[trait, "stubborn"]))
    aardvark = world.add(Entity(id="aardvark", kind="character", type="aardvark", label=aardvark_name, traits=["helpful", "quiet"]))
    prize = world.add(Entity(id="prize", type=prize_id, label=PRIZES[prize_id]["label"], phrase=PRIZES[prize_id]["phrase"], owner="hero", caretaker="aardvark"))
    gear = world.add(Entity(id="gear", type="gear", label="lantern", phrase="a bright lantern"))
    gear.worn_by = "hero"

    hero.memes["curiosity"] = 1
    aardvark.memes["curiosity"] = 1

    world.say(f"{hero_name} was a {trait} little adventurer who liked {activity.gerund}.")
    world.say(f"{aardvark_name} was an aardvark with a soft snout and a patient way of listening.")
    world.say(f"Together they carried {prize.phrase} and set out at {setting.place}.")

    world.para()
    world.say(f"At {setting.place}, {hero_name} wanted to {activity.verb}, but the path could get {activity.danger}.")
    world.say(f"{hero_name} pointed at the trail and said, \"Let's follow it before we lose it.\"")
    world.say(f"{aardvark_name} heard the word \"it\" and looked around, not sure whether {hero_name} meant the map or the trail marker.")
    hero.memes["confused"] = 1
    aardvark.memes["misunderstood"] = 1
    propagate(world)

    world.para()
    world.say(f"Then {hero_name} had a flashback.")
    world.say(f"{hero_name} remembered being lost once before, when {aardvark_name} had quietly led the way home by sniffing the wind and stepping around the bad spots.")
    world.say(f"That memory made the truth clear: {aardvark_name} was not ignoring the plan. {aardvark_name} was waiting for a clearer name.")
    hero.memes["worry"] = max(hero.memes.get("worry", 0), 0)
    aardvark.memes["worry"] = max(aardvark.memes.get("worry", 0), 0)

    world.para()
    world.say(f"{hero_name} smiled and said, \"I mean the trail marker, not you.\"")
    world.say(f"Then {hero_name} used names instead of pronouns, and {aardvark_name} nodded at once.")
    world.say(f"They took the lantern, found the marker, and walked on together with the prize safe and the path clear.")

    world.facts.update(
        hero=hero,
        aardvark=aardvark,
        prize=prize,
        activity=activity,
        setting=setting,
        gear=gear,
        resolved=True,
    )
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

KNOWLEDGE = {
    "aardvark": [
        (
            "What is an aardvark?",
            "An aardvark is an animal with a long snout and strong claws that likes to dig for food.",
        )
    ],
    "pronoun": [
        (
            "What is a pronoun?",
            "A pronoun is a word like he, she, it, or they that can stand in for a name.",
        )
    ],
    "flashback": [
        (
            "What is a flashback in a story?",
            "A flashback is a memory scene that shows something from earlier in the story or even before it.",
        )
    ],
    "misunderstanding": [
        (
            "What is a misunderstanding?",
            "A misunderstanding happens when people hear the same words but think they mean different things.",
        )
    ],
    "lantern": [
        (
            "What does a lantern help with?",
            "A lantern helps people see better in the dark or on a dim trail.",
        )
    ],
    "map": [
        (
            "Why is a map useful?",
            "A map shows where things are and helps travelers find their way.",
        )
    ],
}


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    aardvark = f["aardvark"]
    activity = f["activity"]
    return [
        f'Write a short adventure story for a young child that includes the words "pronoun" and "aardvark".',
        f"Tell a gentle adventure where {hero.label} and the aardvark {aardvark.label} misunderstand a pronoun while {activity.verb}.",
        f"Write a story with a flashback that helps two friends fix a misunderstanding on a trail.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    aardvark = f["aardvark"]
    prize = f["prize"]
    activity = f["activity"]
    place = f["setting"].place
    gear = f["gear"]
    return [
        QAItem(
            question=f"Who was the adventure about at {place}?",
            answer=f"It was about {hero.label} and the aardvark {aardvark.label}, who explored together.",
        ),
        QAItem(
            question=f"What did {hero.label} want to do at {place}?",
            answer=f"{hero.label} wanted to {activity.verb} while keeping {prize.label} safe.",
        ),
        QAItem(
            question=f"Why did {aardvark.label} look confused at first?",
            answer=f"{aardvark.label} thought the pronoun \"it\" might mean the map or the trail marker, so there was a misunderstanding.",
        ),
        QAItem(
            question=f"What helped the friends fix the misunderstanding?",
            answer=f"A flashback reminded {hero.label} how {aardvark.label} had helped before, and then they used names instead of pronouns.",
        ),
        QAItem(
            question=f"How did the lantern help?",
            answer=f"The lantern helped them see the trail marker clearly, so they could keep going on the adventure.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = {"aardvark", "pronoun", "flashback", "misunderstanding", "lantern", "map"}
    out: list[QAItem] = []
    for tag in tags:
        out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE[tag])
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
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Parameters and generation
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    hero_name: str
    hero_type: str
    aardvark_name: str
    trait: str
    seed: Optional[int] = None


CURATED = [
    StoryParams("canyon", "search", "map", "Mina", "girl", "Arlo", "brave"),
    StoryParams("forest", "search", "compass", "Jasper", "boy", "Bram", "curious"),
    StoryParams("ruins", "search", "map", "Nora", "girl", "Milo", "steady"),
]


def explain_rejection(activity: Activity, prize: dict) -> str:
    return f"(No story: {activity.verb} does not fit a prize that sits on the wrong part of the path.)"


def valid_story_combo(place: str, activity: str, prize: str) -> bool:
    return prize in PRIZES and place in SETTINGS and activity in ACTIVITIES and prize == prize and prize and True


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.place not in SETTINGS:
        raise StoryError("Unknown place.")
    if args.activity and args.activity not in ACTIVITIES:
        raise StoryError("Unknown activity.")
    if args.prize and args.prize not in PRIZES:
        raise StoryError("Unknown prize.")

    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.activity is None or c[1] == args.activity)
              and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place, activity, prize = rng.choice(sorted(combos))
    hero_type = args.hero_type or rng.choice(["girl", "boy"])
    hero_name = args.hero_name or rng.choice(NAMES[hero_type])
    aardvark_name = args.aardvark_name or rng.choice(AARDVARK_NAMES)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(
        place=place,
        activity=activity,
        prize=prize,
        hero_name=hero_name,
        hero_type=hero_type,
        aardvark_name=aardvark_name,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.place],
        ACTIVITIES[params.activity],
        params.prize,
        params.hero_name,
        params.hero_type,
        params.aardvark_name,
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


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Adventure story world with an aardvark, a pronoun misunderstanding, and a flashback.")
    ap.add_argument("--place", choices=list(SETTINGS))
    ap.add_argument("--activity", choices=list(ACTIVITIES))
    ap.add_argument("--prize", choices=list(PRIZES))
    ap.add_argument("--hero-type", choices=["girl", "boy"])
    ap.add_argument("--hero-name")
    ap.add_argument("--aardvark-name")
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


def asp_valid_stories() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid_story/4."))
    return sorted(set(asp.atoms(model, "valid_story")))


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for x in combos:
            print(" ", x)
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
            except StoryError as e:
                print(e)
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
            header = f"### {p.hero_name}: {p.activity} at {p.place} with {p.aardvark_name}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
