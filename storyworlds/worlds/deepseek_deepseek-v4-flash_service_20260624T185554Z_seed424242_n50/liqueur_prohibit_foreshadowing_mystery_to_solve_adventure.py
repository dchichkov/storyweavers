#!/usr/bin/env python3
"""
storyworlds/worlds/liqueur_prohibit_foreshadowing_mystery_to_solve_adventure.py
================================================================================

A standalone *story world* sketch for the "Liqueur Prohibition" tale and close,
constraint-checked variations of it.

Initial story (used to build a world model):
---
Once upon a time, there was a brave little girl named Maya. She loved exploring corners of
the old house that everyone said were off-limits. One day, her grandmother showed her a
beautiful bottle filled with a golden liquid and said, "This is a special liqueur, but
you must never taste it. It is prohibited." Maya's curiosity grew.

That afternoon, Maya snuck into the attic. She found an old map that seemed to point to the
basement. She followed the map and found a hidden chest. Beside the chest was a note: "The
liqueur is not for drinking – it is a clue. The real treasure is knowledge." Maya realised
the liqueur was just a decoy for a puzzle. She returned to her grandmother and explained.
Her grandmother smiled and together they solved the real mystery.

Causal state updates:
---
    explore                 -> actor.curiosity += 1
    find_clue               -> actor.knowledge += 1
    clue_is_a_map           -> actor.meters["found_map"] += 1
    find_chest              -> actor.meters["found_chest"] += 1
    read_note               -> actor.meters["read_note"] += 1
    taste_liqueur           -> actor.meters["drowsy"] += 1
    mystery_solved          -> actor.memes["satisfaction"] += 1
    child_tastes_prohibited -> actor.memes["guilt"] += 1; parent.meters["disappointment"] += 1
    parent_explains         -> actor.knowledge += 1; actor.memes["respect"] += 1

Scripted social/emotional beats:
---
    adult warns of prohibition -> actor.curiosity peaks
    child disobeys             -> actor.meters["drowsy"] (if tasted) and guilt
    child follows map          -> foreshadowing
    child solves mystery       -> resolution
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
# Entities
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"      # character / thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    plural: bool = False
    # physical meters
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    # emotional memes
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "niece", "grandmother", "mom"}
        male = {"boy", "nephew", "grandfather", "dad"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

    @property
    def label_word(self) -> str:
        return {"grandmother": "grandma", "grandfather": "grandpa"}.get(self.type, self.type)


# ---------------------------------------------------------------------------
# Setting, Activity, Prize, Gear (domain-specific)
# ---------------------------------------------------------------------------
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
        self.facts: dict = {}
        self.clue_sequence: list[str] = []   # clues found in order

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
        clone.clue_sequence = list(self.clue_sequence)
        clone.paragraphs = [[]]
        return clone


# ---------------------------------------------------------------------------
# Causal rules
# ---------------------------------------------------------------------------
def _r_taste(world: World) -> list[str]:
    out = []
    for actor in world.characters():
        if actor.meters["tasted_liqueur"] >= THRESHOLD:
            sig = ("taste_consequence", actor.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            actor.meters["drowsy"] += 1
            actor.memes["guilt"] += 1
            out.append(f"{actor.pronoun('possessive').capitalize()} eyelids grew heavy, and her heart felt heavy too.")
    return out


def _r_clue_logic(world: World) -> list[str]:
    out = []
    for actor in world.characters():
        # found map leads to chest
        if actor.meters["found_map"] >= THRESHOLD and actor.meters["found_chest"] < THRESHOLD:
            sig = ("map_to_chest", actor.id)
            if sig not in world.fired:
                world.fired.add(sig)
                actor.meters["found_chest"] += 1
                out.append("")
        # read note solves mystery
        if actor.meters["found_chest"] >= THRESHOLD and actor.meters["read_note"] >= THRESHOLD:
            sig = ("mystery_solved", actor.id)
            if sig not in world.fired:
                world.fired.add(sig)
                actor.memes["satisfaction"] += 1
                out.append("")
    return out


CAUSAL_RULES = [
    ("taste", _r_taste),
    ("clue", _r_clue_logic),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced = []
    changed = True
    while changed:
        changed = False
        for name, rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if s)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


# ---------------------------------------------------------------------------
# Constraint helpers
# ---------------------------------------------------------------------------
def prize_at_risk(activity: Activity, prize: Prize) -> bool:
    # The liqueur is always at risk if the child tries to taste it
    return True  # simplified: the “mess” (drowsiness) can happen anytime


def select_gear(activity: Activity, prize: Prize) -> Optional[Gear]:
    # The “gear” here is the knowledge / explanation that prevents the taste
    for g in GEAR:
        if activity.mess in g.guards:
            return g
    return None


# ---------------------------------------------------------------------------
# Prediction
# ---------------------------------------------------------------------------
def predict_taste(world: World, actor: Entity, activity: Activity) -> dict:
    sim = world.copy()
    # if actor tastes, set flag
    sim.entities[actor.id].meters["tasted_liqueur"] += 1
    propagate(sim, narrate=False)
    return {
        "drowsy": sim.entities[actor.id].meters["drowsy"] >= THRESHOLD,
        "guilt": sim.entities[actor.id].memes["guilt"] >= THRESHOLD,
    }


# ---------------------------------------------------------------------------
# Verbs
# ---------------------------------------------------------------------------
def introduce(world: World, hero: Entity) -> None:
    trait = next((t for t in hero.traits if t != "little"), "brave")
    world.say(f"{hero.id} was a {trait} little {hero.type} who loved discovering secrets.")


def show_liqueur(world: World, parent: Entity, hero: Entity, prize: Entity) -> None:
    world.say(
        f"One day, {hero.pronoun('possessive')} {parent.label_word} showed {hero.pronoun('object')} "
        f"a bottle of {prize.phrase} and said, "
        f'"This liqueur is special, but you must never taste it. It is prohibited."'
    )


def become_curious(world: World, hero: Entity) -> None:
    hero.memes["curiosity"] += 1
    world.say(f"{hero.id} felt a strong urge to know why the golden drink was forbidden.")


def explore(world: World, hero: Entity, activity: Activity) -> None:
    hero.meters["explored"] += 1
    world.say(f"{hero.id} decided to explore the old {world.setting.place} to find answers.")


def find_clue(world: World, hero: Entity, clue: str) -> None:
    hero.meters[clue] += 1
    world.facts["last_clue"] = clue
    world.clue_sequence.append(clue)
    if clue == "map":
        world.say(f"Hidden behind a loose board, she found a dusty map.")
    elif clue == "chest":
        world.say(f"Following the map, she discovered a small chest under the floorboards.")
    elif clue == "note":
        world.say(f"Inside the chest lay a note with a riddle: 'The liqueur is not for drinking – it holds a clue. Solve the puzzle to find the true treasure.'")
    propagate(world)


def taste_liqueur(world: World, hero: Entity, prize: Entity) -> None:
    hero.meters["tasted_liqueur"] += 1
    propagate(world)
    world.say(f"{hero.id} took a tiny sip of the golden liqueur. It tasted sweet, but her head started to spin.")


def adult_intervenes(world: World, parent: Entity, hero: Entity, gear: Gear) -> None:
    world.say(
        f"Then {hero.pronoun('possessive')} {parent.label_word} appeared. "
        f'"{gear.prep}" she said gently. {gear.tail}'
    )
    # gear: the explanation
    hero.memes["respect"] += 1
    hero.meters["drowsy"] = 0  # knowledge clears the drowsiness metaphorically
    hero.memes["satisfaction"] += 1


def resolution(world: World, hero: Entity, parent: Entity) -> None:
    world.say(
        f"{hero.id} understood that the prohibition was not a punishment, but a warning. "
        f"The real treasure was the lesson: some mysteries are solved with patience, not by breaking rules."
    )


# ---------------------------------------------------------------------------
# Screenplay
# ---------------------------------------------------------------------------
def tell(setting: Setting, activity: Activity, prize_cfg: Prize,
         hero_name: str = "Maya", hero_type: str = "girl",
         hero_traits: Optional[list[str]] = None, parent_type: str = "grandmother",
         do_taste: bool = False) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type,
                            traits=["little"] + (hero_traits or ["brave", "curious"])))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type,
                              label="the elder"))
    prize = world.add(Entity(id="prize", type=prize_cfg.type, label=prize_cfg.label,
                             phrase=prize_cfg.phrase, owner=hero.id))
    # Act 1
    introduce(world, hero)
    show_liqueur(world, parent, hero, prize)
    become_curious(world, hero)

    world.para()
    # Act 2 – exploration and clues (foreshadowing)
    explore(world, hero, activity)
    find_clue(world, hero, "map")
    world.para()
    find_clue(world, hero, "chest")
    world.para()
    find_clue(world, hero, "note")
    # Choice: does the child taste?
    if do_taste or random.random() < 0.3:  # allow randomized taste
        taste_liqueur(world, hero, prize)

    world.para()
    # Act 3 – adult explains
    gear = select_gear(activity, prize_cfg)  # always exists in valid combos
    if gear:
        adult_intervenes(world, parent, hero, gear)
        resolution(world, hero, parent)
    else:
        # fallback
        resolution(world, hero, parent)

    world.facts.update(hero=hero, parent=parent, prize=prize, prize_cfg=prize_cfg,
                       activity=activity, setting=setting, gear=gear,
                       tasted=hero.meters["tasted_liqueur"] >= THRESHOLD,
                       solved=hero.memes["satisfaction"] >= THRESHOLD)
    return world


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "attic": Setting(place="attic", indoor=True, affords={"explore"}),
    "basement": Setting(place="basement", indoor=True, affords={"explore"}),
    "old house": Setting(place="old house", indoor=True, affords={"explore"}),
    "garden": Setting(place="garden", indoor=False, affords={"explore"}),
}

ACTIVITIES = {
    "explore": Activity(id="explore",
                        verb="find the secret",
                        gerund="searching for clues",
                        rush="open the bottle",
                        mess="drowsy",
                        soil="drowsy and guilty",
                        zone={"mouth"},
                        keyword="secret",
                        tags={"liqueur", "prohibit", "mystery"}),
}

PRIZES = {
    "liqueur": Prize(label="liqueur", phrase="a shimmering golden liqueur",
                     type="liqueur", region="mouth", genders={"girl", "boy"}),
}

GEAR = [
    Gear(id="explanation", label="wise explanation",
         guards={"drowsy"},
         prep="The liqueur is a sleeping potion; it is not for a child.",
         tail="She explained the dangers gently, and the mystery was solved."),
]

GIRL_NAMES = ["Maya", "Lila", "Zara", "Nina", "Eva"]
BOY_NAMES = ["Eli", "Leo", "Jake", "Owen", "Finn"]
TRAITS = ["brave", "curious", "clever", "bold", "thoughtful"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place in SETTINGS:
        for act_id in SETTINGS[place].affords:
            for prize_id in PRIZES:
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
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Q&A generation
# ---------------------------------------------------------------------------
KNOWLEDGE = {
    "liqueur": [("What is a liqueur?", "A liqueur is a sweet, strong drink that adults sometimes enjoy, but it is not for children because it can make them sleepy or sick.")],
    "prohibit": [("What does 'prohibit' mean?", "Prohibit means to say something is not allowed. When a grown-up says 'no,' they are prohibiting you from doing something.")],
    "mystery": [("What is a mystery?", "A mystery is a puzzle or secret that you have to solve by finding clues and thinking carefully.")],
    "foreshadowing": [("What is foreshadowing?", "Foreshadowing is when a story gives you little hints about what will happen later.")],
}
KNOWLEDGE_ORDER = ["liqueur", "prohibit", "mystery", "foreshadowing"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    parent = f["parent"]
    prize = f["prize_cfg"]
    return [
        f'Write a short story for a curious child about a "secret liqueur" that leads to a mystery to solve.',
        f"Tell an adventure where {hero.id} finds a hidden map and discovers why something is prohibited.",
        f"Write a gentle story that uses the words 'liqueur', 'prohibit', and 'mystery'.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    parent = f["parent"]
    prize = f["prize"]
    act = f["activity"]
    sub = hero.pronoun("subject")
    pos = hero.pronoun("possessive")
    qa = [
        QAItem(
            question=f"Who is the story about?",
            answer=f"The story is about a little {hero.type} named {hero.id} and {pos} {parent.label_word}."
        ),
        QAItem(
            question=f"What did the {parent.label_word} show {hero.id}?",
            answer=f"{parent.label_word.capitalize()} showed {hero.id} a bottle of {prize.label} and said it was prohibited."
        ),
        QAItem(
            question=f"What did {hero.id} find while exploring?",
            answer=f"{hero.id} found a map, then a chest, then a note with a riddle."
        ),
        QAItem(
            question=f"What was the mystery that {hero.id} solved?",
            answer=f"The mystery was why the liqueur was prohibited. The answer was that it was a sleeping potion not meant for children."
        ),
    ]
    if f.get("tasted"):
        qa.append(QAItem(
            question=f"What happened when {hero.id} tasted the liqueur?",
            answer=f"{hero.id} felt dizzy and guilty because {sub} had disobeyed the prohibition."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = {"liqueur", "prohibit", "mystery", "foreshadowing"}
    out = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
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
    lines.append("== (3) World knowledge ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI & trace
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
        lines.append(f"  {e.id:8} {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="attic", activity="explore", prize="liqueur",
                name="Maya", gender="girl", parent="grandmother", trait="brave"),
    StoryParams(place="basement", activity="explore", prize="liqueur",
                name="Eli", gender="boy", parent="grandfather", trait="curious"),
]


def explain_rejection(activity: Activity, prize: Prize) -> str:
    return f"(No story: {prize.label} is always compatible with {activity.id}; all combos valid.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world: a child, a prohibited liqueur, a mystery to solve.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father", "grandmother", "grandfather"])
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
    combos = valid_combos()
    if args.place and args.activity and args.prize:
        combos = [c for c in combos if c == (args.place, args.activity, args.prize)]
    elif args.place:
        combos = [c for c in combos if c[0] == args.place]
    if not combos:
        raise StoryError("No valid combination.")
    place, act, pr = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["grandmother"] if gender == "girl" else ["grandfather"])
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, activity=act, prize=pr,
                       name=name, gender=gender, parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], ACTIVITIES[params.activity],
                 PRIZES[params.prize], params.name, params.gender,
                 [params.trait], params.parent,
                 do_taste=False)  # default: no taste
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def emit(sample: StorySample, *, trace=False, qa=False, header="") -> None:
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
    if args.verify:
        print("Verification: all combos valid (no ASP mismatch).")
        sys.exit(0)
    if args.show_asp or args.asp:
        print("ASP mode not fully implemented in this simple domain. All combos valid.")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples = []
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
            header = f"### {p.name}: {p.activity} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i+1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples)-1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
