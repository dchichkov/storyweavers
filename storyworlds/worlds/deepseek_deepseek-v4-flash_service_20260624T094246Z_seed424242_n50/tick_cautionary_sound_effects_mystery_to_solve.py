#!/usr/bin/env python3
"""
storyworlds/worlds/tick_cautionary_sound_effects_mystery_to_solve.py
=====================================================================

A standalone story world sketch: a child hears a mysterious ticking sound in the
woods, wants to solve the mystery alone, and learns a cautionary lesson about
listening to a parent's warning. The story includes sound effects (tick-toc,
tap, rustle) and ends with a friendly discovery.
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
MESS_KINDS = {"muddy", "torn", "scratched"}
REGIONS = {"feet", "legs", "torso"}


# ---------------------------------------------------------------------------
# Entities
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
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


# ---------------------------------------------------------------------------
# Parametrization
# ---------------------------------------------------------------------------
@dataclass
class Setting:
    place: str
    indoor: bool = False
    affords: set[str] = field(default_factory=set)


@dataclass
class Mystery:
    id: str
    sound: str                   # onomatopoeia: "tick-tick", "tap-tap", "rustle"
    sound_desc: str              # "a gentle ticking", "a soft tapping"
    source: str                  # what makes it: "a kind woodpecker", "a hidden clock"
    source_label: str            # child-friendly: "woodpecker", "songbird"
    danger: str                  # what could go wrong: "get lost", "fall"
    caution: str                 # lesson: "always stay with your grown-up"
    keyword: str = "mystery"

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
    def __init__(self, setting: Setting):
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.mystery: Optional[Mystery] = None

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
        clone.mystery = self.mystery
        clone.paragraphs = [[]]
        return clone

    def covered(self, actor: Entity, region: str) -> bool:
        return any(g.protective and region in g.covers
                   for g in self.entities.values()
                   if g.worn_by == actor.id)


# ---------------------------------------------------------------------------
# Rules
# ---------------------------------------------------------------------------
@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_spoil_gear(world: World) -> list[str]:
    """If the child gets muddy/torn/scratched while wandering, spoil gear."""
    out = []
    for actor in world.characters():
        for mess in MESS_KINDS:
            if actor.meters[mess] < THRESHOLD:
                continue
            for item in world.entities.values():
                if item.worn_by != actor.id or item.protective:
                    continue
                if world.covered(actor, item.region):
                    continue
                sig = ("spoil", item.id, mess)
                if sig in world.fired:
                    continue
                world.fired.add(sig)
                item.meters[mess] += 1
                item.meters["dirty"] += 1
                out.append(f"{actor.pronoun('possessive').capitalize()} {item.label} got {mess}.")
    return out


def _r_caretaker_worry(world: World) -> list[str]:
    out = []
    for item in list(world.entities.values()):
        if item.meters["dirty"] < THRESHOLD or not item.caretaker:
            continue
        sig = ("worry", item.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        carer = world.get(item.caretaker)
        carer.meters["worry"] += 1
        out.append(f"That would worry {carer.label}.")
    return out


CAUSAL_RULES = [
    Rule(name="spoil", tag="physical", apply=_r_spoil_gear),
    Rule(name="worry", tag="social", apply=_r_caretaker_worry),
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
                produced.extend(s for s in sents if s != "__marker__")
    if narrate:
        for s in produced:
            world.say(s)
    return produced


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def mystery_at_risk(activity: Mystery, prize: Prize) -> bool:
    # The mystery always puts the prize (e.g. a favorite toy/shirt) at risk
    # because the child might get lost/dirty.
    return True


def select_gear(activity: Mystery, prize: Prize) -> Optional[Gear]:
    """Gear that protects against the danger (e.g. getting lost -> flashlight or map)."""
    for gear in GEAR:
        if activity.danger in gear.guards and prize.region in gear.covers:
            return gear
    return None


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for myst_id in setting.affords:
            myst = MYSTERIES[myst_id]
            for prize_id, prize in PRIZES.items():
                if mystery_at_risk(myst, prize) and select_gear(myst, prize):
                    combos.append((place, myst_id, prize_id))
    return combos


# ---------------------------------------------------------------------------
# Storytelling
# ---------------------------------------------------------------------------
def tell(setting: Setting, mystery: Mystery, prize_cfg: Prize,
         hero_name: str = "Ella", hero_type: str = "girl",
         traits: Optional[list[str]] = None,
         parent_type: str = "mother") -> World:
    world = World(setting)
    world.mystery = mystery

    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type,
                            traits=["curious"] + (traits or ["brave", "stubborn"])))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label="grown-up"))
    prize = world.add(Entity(id="prize", type=prize_cfg.type, label=prize_cfg.label,
                             phrase=prize_cfg.phrase, owner=hero.id, caretaker=parent.id,
                             region=prize_cfg.region, plural=prize_cfg.plural))

    # Act 1
    world.say(f"Deep in the {setting.place.rstrip('s')}, a little {hero_type} named {hero_name} lived with {hero.pronoun('possessive')} {parent.label_word}.")
    world.say(f"{hero.pronoun().capitalize()} loved exploring every nook and cranny, listening to the sounds of the wild.")

    # Act 2 – the mystery
    world.para()
    world.say(f"One afternoon, {hero_name} heard {mystery.sound_desc}: *{mystery.sound.upper()}*")
    world.say(f"The curious {hero_type} {hero.pronoun()} wanted to find out what made that sound.")
    world.say(f"But {hero.pronoun('possessive')} {parent.label_word} said, \"Stay close. The woods can {mystery.caution}.\"")

    # Act 3 – defiance and consequence
    world.para()
    world.say(f"{hero_name} {hero.pronoun()} could not resist. While {parent.label_word} {world.setting.place}, {hero.pronoun()} slipped away toward the sound.")
    world.say(f"The path grew narrow. Trees rustled. *{mystery.sound}* came from behind a big rock.")
    world.say(f"But now {hero_name} was lost.")

    # Act 4 – resolution
    world.para()
    world.say(f"The sun dipped lower. {hero_name} felt scared. \"I should have listened,\" {hero.pronoun()} whispered.")
    world.say(f"Then the sound came again, close. {hero_name} followed it and found {mystery.source}.")
    world.say(f"\"Oh, it's just a {mystery.source_label}!\" {hero.pronoun()} laughed. {mystery.source_description()}")

    # Parent finds them
    world.para()
    gear_def = select_gear(mystery, prize_cfg)
    if gear_def:
        world.say(f"{parent.label_word.capitalize()} came with {gear_def.label}. \"Next time, let's go together,\" {hero.pronoun('possessive')} {parent.label_word} said.")
        world.say(f"{hero_name} hugged {parent.label_word}. \"I will. The mystery was {mystery.source_label} all along.\"")
        # Actually mark the gear as used
        g_entity = world.add(Entity(id=gear_def.id, type="gear", label=gear_def.label,
                                    owner=hero.id, caretaker=parent.id,
                                    protective=True, covers=set(gear_def.covers),
                                    plural=gear_def.plural))
        g_entity.worn_by = hero.id
    else:
        world.say(f"{hero_name} hugged {parent.label_word}. \"I won't sneak away again. The mystery was {mystery.source_label}.\"")

    # Record facts
    world.facts.update(hero=hero, parent=parent, prize=prize, prize_cfg=prize_cfg,
                       mystery=mystery, setting=setting)

    return world


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "forest": Setting(place="the quiet forest", indoor=False, affords={"tick", "tap", "rustle"}),
    "woods": Setting(place="the deep woods", indoor=False, affords={"tick", "tap"}),
    "garden": Setting(place="the old garden", indoor=False, affords={"tick", "rustle"}),
}

MYSTERIES: dict[str, Mystery] = {
    "tick": Mystery(
        id="tick",
        sound="tick-tick",
        sound_desc="a gentle tick-tick like a tiny clock",
        source="a kind woodpecker with a red head",
        source_label="woodpecker",
        danger="get lost",
        caution="stay on the path and never go alone",
        keyword="tick",
        tags={"tick", "woodpecker", "clock"},
    ),
    "tap": Mystery(
        id="tap",
        sound="tap-tap",
        sound_desc="a soft tap-tap like raindrops on a leaf",
        source="a friendly squirrel tapping a nut against a tree",
        source_label="squirrel",
        danger="fall into a hole",
        caution="watch your step and never wander off",
        keyword="tap",
        tags={"tap", "squirrel"},
    ),
    "rustle": Mystery(
        id="rustle",
        sound="rustle-rustle",
        sound_desc="a quiet rustle like dry leaves moving",
        source="a mother deer browsing berries",
        source_label="deer",
        danger="scare the animals",
        caution="be quiet and stay with your grown-up",
        keyword="rustle",
        tags={"rustle", "deer"},
    ),
}

PRIZES = {
    "shoes": Prize(label="shoes", phrase="new red boots", type="shoes", region="feet", plural=True),
    "shirt": Prize(label="shirt", phrase="a striped explorer shirt", type="shirt", region="torso"),
    "hat": Prize(label="hat", phrase="a woolly cap with a pom-pom", type="hat", region="torso"),
}

GEAR = [
    Gear(id="lantern", label="a warm lantern",
         covers={"feet", "torso"}, guards={"get lost"},
         prep="light the lantern so we both see the way",
         tail="walked together with the lantern glowing"),
    Gear(id="whistle", label="a bright whistle",
         covers={"torso"}, guards={"get lost", "scare"},
         prep="tie the whistle around your neck and blow if you get scared",
         tail="blew the whistle and the grown-up found them"),
]

GIRL_NAMES = ["Ella", "Maya", "Zoe", "Ava", "Lily", "Lucy"]
BOY_NAMES = ["Max", "Sam", "Leo", "Eli", "Noah", "Finn"]
TRAITS = ["brave", "curious", "patient", "spirited", "lively", "gentle"]


# ---------------------------------------------------------------------------
# Params
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    mystery: str
    prize: str
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
KNOWLEDGE = {
    "tick": [("What makes a tick-tick sound in the woods?",
              "A woodpecker makes a tick-tick sound when it pecks at tree bark.")],
    "tap": [("What animal might tap on a tree?",
             "A squirrel sometimes taps a nut against a tree to open it.")],
    "rustle": [("Why do leaves rustle?",
                "Leaves rustle because the wind moves them or an animal walks through them.")],
    "woodpecker": [("What does a woodpecker eat?",
                    "Woodpeckers eat bugs they find under tree bark.")],
    "squirrel": [("What do squirrels like to eat?",
                  "Squirrels eat nuts, seeds, and fruit.")],
    "deer": [("Where do deer live?",
              "Deer live in forests and woods and eat leaves and berries.")],
}

KNOWLEDGE_ORDER = ["tick", "tap", "rustle", "woodpecker", "squirrel", "deer"]


def generation_prompts(world: World) -> list[str]:
    m = world.facts["mystery"]
    return [
        f"Write a short cautionary tale for a 4-year-old about a child who hears a {m.sound} in the {world.facts['setting'].place} and learns why staying with an adult is important.",
        f"Tell a gentle story with the word '{m.sound}' and a mystery that turns out to be a friendly {m.source_label}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    h, p, m, s = world.facts["hero"], world.facts["parent"], world.facts["mystery"], world.facts["setting"]
    qa = [
        QAItem(
            question=f"What sound did {h.id} hear in {s.place}?",
            answer=f"{h.pronoun().capitalize()} heard {m.sound_desc}: {m.sound.upper()}."
        ),
        QAItem(
            question=f"Why did {p.label_word} tell {h.id} to stay close?",
            answer=f"{p.label_word.capitalize()} warned {h.pronoun('object')} because the woods can be confusing and it is easy to {m.caution}."
        ),
        QAItem(
            question=f"What happened when {h.id} followed the sound alone?",
            answer=f"{h.pronoun().capitalize()} got lost and felt scared until {h.pronoun()} found {m.source}."
        ),
        QAItem(
            question=f"What was making the {m.sound} sound all along?",
            answer=f"It was a friendly {m.source_label}. {m['source_description']() if hasattr(m, 'source_description') else 'It was just a natural creature.'}"
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = world.facts["mystery"].tags
    out = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
            out.extend(QAItem(q, a) for q, a in KNOWLEDGE[tag])
    return out


# ---------------------------------------------------------------------------
# ASP Twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A prize is at risk when the mystery's danger can harm it (always true for simplicity).
at_risk(M, P) :- mystery(M), prize(P).

% Gear is compatible when it guards the danger and covers the prize region.
protects(G, M, P) :- gear(G), mystery(M), prize(P),
                     guards(G, D), danger_of(M, D),
                     covers(G, R), worn_on(P, R).

has_fix(M, P) :- protects(_, M, P).

valid(Place, M, P) :- affords(Place, M), at_risk(M, P), has_fix(M, P).
valid_story(Place, M, P, Gender) :- valid(Place, M, P), wears(Gender, P).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid, st in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        if st.indoor:
            lines.append(asp.fact("indoor", pid))
        for m in sorted(st.affords):
            lines.append(asp.fact("affords", pid, m))
    for mid, m in MYSTERIES.items():
        lines.append(asp.fact("mystery", mid))
        lines.append(asp.fact("danger_of", mid, m.danger))
        lines.append(asp.fact("sound_of", mid, m.sound))
    for pid, pr in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("worn_on", pid, pr.region))
        if pr.plural:
            lines.append(asp.fact("prize_plural", pid))
        for g in sorted(pr.genders):
            lines.append(asp.fact("wears", g, pid))
    for g in GEAR:
        lines.append(asp.fact("gear", g.id))
        for d in sorted(g.guards):
            lines.append(asp.fact("guards", g.id, d))
        for r in sorted(g.covers):
            lines.append(asp.fact("covers", g.id, r))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH:")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


# ---------------------------------------------------------------------------
# Standard interface
# ---------------------------------------------------------------------------
def build_parser():
    ap = argparse.ArgumentParser(description="Ticking mystery story world")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
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


def resolve_params(args, rng):
    if args.mystery and args.prize:
        m, p = MYSTERIES[args.mystery], PRIZES[args.prize]
        if not (mystery_at_risk(m, p) and select_gear(m, p)):
            raise StoryError("Incompatible mystery and prize.")
    if args.gender and args.prize and args.gender not in PRIZES[args.prize].genders:
        raise StoryError(f"Gender mismatch for prize {args.prize}")

    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.mystery is None or c[1] == args.mystery)
              and (args.prize is None or c[2] == args.prize)
              and (args.gender is None or args.gender in PRIZES[c[2]].genders)]
    if not combos:
        raise StoryError("No valid combination for given options.")

    place, mystery_id, prize_id = rng.choice(sorted(combos))
    prize = PRIZES[prize_id]
    gender = args.gender or rng.choice(sorted(prize.genders))
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, mystery=mystery_id, prize=prize_id,
                       name=name, gender=gender, parent=parent, trait=trait)


def generate(params):
    world = tell(SETTINGS[params.place], MYSTERIES[params.mystery],
                 PRIZES[params.prize], params.name, params.gender,
                 [params.trait, "stubborn"], params.parent)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def emit(sample, *, trace=False, qa=False, header=""):
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world:
        print("--- trace ---")
        for e in sample.world.entities.values():
            meters = {k: v for k, v in e.meters.items() if v}
            memes = {k: v for k, v in e.memes.items() if v}
            parts = []
            if meters:
                parts.append(f"meters={dict(meters)}")
            if memes:
                parts.append(f"memes={dict(memes)}")
            print(f"  {e.id:8} ({e.type:7}) {' '.join(parts)}")
    if qa:
        print()
        for i, p in enumerate(sample.prompts, 1):
            print(f"Prompt {i}: {p}")
        for item in sample.story_qa:
            print(f"Q: {item.question}\nA: {item.answer}\n")
        for item in sample.world_qa:
            print(f"WQ: {item.question}\nWA: {item.answer}\n")


def main():
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for c in combos:
            print(f"  {c[0]:8} {c[1]:8} {c[2]:8}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples = []
    if args.all:
        curated = [
            StoryParams("forest", "tick", "shoes", "Maya", "girl", "mother", "brave"),
            StoryParams("woods", "tap", "shirt", "Max", "boy", "father", "curious"),
            StoryParams("garden", "rustle", "hat", "Zoe", "girl", "mother", "gentle"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < args.n * 50:
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as e:
                print(e)
                return
            params.seed = seed
            s = generate(params)
            if s.story in seen:
                continue
            seen.add(s.story)
            samples.append(s)

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = f"### Story {i+1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 60 + "\n")


if __name__ == "__main__":
    main()
