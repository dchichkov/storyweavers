#!/usr/bin/env python3
"""
storyworlds/worlds/spectacular_squat_glisten_lesson_learned_transformation_pirate.py
=====================================================================================

A standalone pirate tale story world: a young pirate finds a spectacular,
glistening treasure, learns a lesson about greed, and transforms into a
generous crewmate.  Uses the three seed words (spectacular, squat, glisten)
and the narrative beats Lesson Learned and Transformation.
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
EMOTION_KEYS = {"greed", "selfish", "sharing", "pride", "generosity", "joy"}


# ---------------------------------------------------------------------------
# Entities
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "character"
    type: str = "pirate"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    region: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        return {"subject": "he", "object": "him", "possessive": "his"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


# ---------------------------------------------------------------------------
# Settings, Activities, Treasure (prize), Gear
# ---------------------------------------------------------------------------
@dataclass
class Setting:
    name: str
    place: str
    affords: set[str]


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    mess: str    # here the "mess" is greed/selfishness meter
    zone: set[str]
    keyword: str
    tags: set[str]


@dataclass
class Treasure:
    id: str
    label: str
    phrase: str
    type: str
    region: str = "chest"   # not relevant for gear, but kept for compatibility
    plural: bool = False
    genders: set[str] = field(default_factory=lambda: {"boy", "girl"})


@dataclass
class Gear:
    id: str
    label: str
    covers: set[str]      # useless here but required by structure
    guards: set[str]      # the "temptation" this gear counters
    prep: str
    tail: str
    plural: bool = False


SETTINGS = {
    "island": Setting(name="island", place="a sandy island", affords={"digging", "cave"}),
    "cove": Setting(name="cove", place="a hidden cove", affords={"digging"}),
    "ship": Setting(name="ship", place="the old ship", affords={"map"}),
}

ACTIVITIES = {
    "digging": Activity(
        id="digging",
        verb="dig for treasure",
        gerund="digging for treasure",
        rush="run to the marked spot and start digging",
        mess="selfish",
        zone={"chest"},
        keyword="treasure",
        tags={"treasure", "greed"},
    ),
    "cave": Activity(
        id="cave",
        verb="explore the dark cave",
        gerund="exploring the dark cave",
        rush="sneak into the cave alone",
        mess="selfish",
        zone={"chest"},
        keyword="cave",
        tags={"cave", "greed"},
    ),
    "map": Activity(
        id="map",
        verb="follow the old map",
        gerund="following the old map",
        rush="grab the map and run off",
        mess="selfish",
        zone={"chest"},
        keyword="map",
        tags={"map", "greed"},
    ),
}

TREASURES = {
    "gold": Treasure(
        id="gold",
        label="gold coins",
        phrase="a chest full of gold coins that glistened in the sun",
        type="treasure",
        plural=True,
    ),
    "jewels": Treasure(
        id="jewels",
        label="sparkling jewels",
        phrase="a handful of sparkling jewels that caught every glimmer of light",
        type="treasure",
        plural=True,
    ),
    "crown": Treasure(
        id="crown",
        label="shiny crown",
        phrase="a shiny crown decorated with bright rubies",
        type="treasure",
    ),
}

GEAR = [
    Gear(
        id="share_bag",
        label="a sharing bag",
        covers={"chest"},   # dummy
        guards={"selfish", "greed"},
        prep="put some treasure into a sharing bag for the crew",
        tail="filled a small bag with a few coins for the crew",
    ),
    Gear(
        id="compass",
        label="the captain's compass",
        covers={"chest"},
        guards={"selfish"},
        prep="use the captain's compass to find a hiding spot for the treasure together",
        tail="followed the compass and chose a spot where everyone could share the sight",
    ),
]

GIRL_NAMES = ["Nina", "Bella", "Pearl", "Jade", "Sky", "Mara"]
BOY_NAMES = ["Rex", "Finn", "Jake", "Kai", "Lio", "Toby"]
TRAITS = ["brave", "curious", "stubborn", "greedy", "loyal", "daring"]


# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------
class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.zone: set[str] = set()
        self.weather: str = "sunny"
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
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.zone = set(self.zone)
        clone.weather = self.weather
        clone.paragraphs = [[]]
        return clone


# ---------------------------------------------------------------------------
# Causal rules (minimal – greed rise, transformation)
# ---------------------------------------------------------------------------
def _r_greed_rise(world: World) -> list[str]:
    out = []
    for actor in world.characters():
        if actor.memes["selfish"] >= THRESHOLD and "tempted" not in world.fired:
            world.fired.add("tempted")
            out.append(f"{actor.id} felt a greedy tug in {actor.pronoun('possessive')} chest.")
    return out


def _r_transformation(world: World) -> list[str]:
    out = []
    for actor in world.characters():
        if actor.memes["sharing"] >= THRESHOLD and "transformed" not in world.fired:
            world.fired.add("transformed")
            out.append(f"At that moment, {actor.id} transformed from a greedy pirate into a generous one.")
    return out


CAUSAL_RULES = [
    ("greed_rise", _r_greed_rise),
    ("transformation", _r_transformation),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced = []
    changed = True
    while changed:
        changed = False
        for _, fn in CAUSAL_RULES:
            sents = fn(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


# ---------------------------------------------------------------------------
# Reasonableness gates
# ---------------------------------------------------------------------------
def treasure_at_risk(activity: Activity, treasure: Treasure) -> bool:
    # All treasures are at risk for any activity because the greed is the mess.
    return True


def select_gear(activity: Activity, treasure: Treasure) -> Optional[Gear]:
    # Always return the first gear that guards "selfish"
    for g in GEAR:
        if "selfish" in g.guards:
            return g
    return None


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sname, setting in SETTINGS.items():
        for act_id in setting.affords:
            for t_id in TREASURES:
                if treasure_at_risk(ACTIVITIES[act_id], TREASURES[t_id]):
                    combos.append((sname, act_id, t_id))
    return combos


# ---------------------------------------------------------------------------
# Screenplay verbs
# ---------------------------------------------------------------------------
def introduce(world: World, hero: Entity) -> None:
    trait = next((t for t in hero.traits if t != "little"), "brave")
    world.say(f"{hero.id} was a {trait} young pirate who dreamed of finding a spectacular treasure.")


def loves_activity(world: World, hero: Entity, activity: Activity) -> None:
    world.say(f"{hero.pronoun().capitalize()} spent every spare moment {activity.gerund}.")


def buys_prize_not_needed(world: World, parent: Entity, hero: Entity, treasure: Treasure) -> None:
    # The pirate captain (parent) gives the treasure map.
    world.say(f"One morning, Captain {parent.label} handed {hero.id} an old map and said, 'Here be a glistening prize.'")


def loves_prize(world: World, hero: Entity, treasure: Treasure) -> None:
    world.say(f"{hero.id} could already imagine {treasure.label} that {treasure.phrase}.")


def arrive(world: World, hero: Entity, parent: Entity, activity: Activity) -> None:
    world.say(f"Together they sailed to {world.setting.place}.")


def wants(world: World, hero: Entity, parent: Entity, activity: Activity) -> None:
    hero.memes["selfish"] += 1
    world.say(f"{hero.id} wanted to {activity.verb} all alone, without sharing.")


def warn(world: World, parent: Entity, hero: Entity, activity: Activity, treasure: Treasure) -> bool:
    pred = predict_greed(world, hero, activity)
    if not pred["greedy"]:
        return False
    world.facts["predicted_lesson"] = "greed"
    world.say(f'"{hero.id}, a true pirate shares," said Captain {parent.label}. "If you keep it all, the treasure will turn to sand."')
    return True


def predict_greed(world: World, actor: Entity, activity: Activity) -> dict:
    sim = world.copy()
    sim.get(actor.id).memes["selfish"] += 1
    propagate(sim, narrate=False)
    return {"greedy": sim.get(actor.id).memes["selfish"] >= THRESHOLD}


def defies(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["selfish"] += 1
    world.say(f"{hero.id} ignored the warning and tried to {activity.rush}.")


def grab_hand(world: World, parent: Entity, hero: Entity, activity: Activity) -> None:
    world.say(f"Captain {parent.label} grabbed {hero.pronoun('possessive')} arm. 'Not alone, young one.'")


def pout(world: World, hero: Entity, activity: Activity) -> None:
    if hero.memes["selfish"] >= THRESHOLD:
        world.say(f'{hero.id} pouted. "But it\'s mine! I found it!"')


def compromise(world: World, parent: Entity, hero: Entity, activity: Activity, treasure: Treasure) -> Optional[Gear]:
    gear_def = select_gear(activity, treasure)
    if not gear_def:
        return None
    # Simulate with gear: if greed still too high, reject.
    sim = world.copy()
    sim.get(hero.id).memes["sharing"] += 1  # gear adds sharing
    if sim.get(hero.id).memes["selfish"] >= THRESHOLD:
        return None
    world.say(f'Captain {parent.label} smiled. "How about we {gear_def.prep}?"')
    return gear_def


def accept(world: World, parent: Entity, hero: Entity, activity: Activity, treasure: Treasure, gear_def: Gear) -> None:
    hero.memes["sharing"] += 1
    hero.memes["joy"] += 1
    hero.memes["selfish"] = 0  # transformation
    world.say(f"{hero.id}'s eyes lit up. 'Alright, Captain!' {hero.pronoun().capitalize()} hugged {parent.label}.")
    world.say(f"They {gear_def.tail}. Then they all admired the spectacular, glistening treasure together.")
    # Explicit transformation beat
    world.say(f"From that day on, {hero.id} was a changed pirate — generous and kind.")


# ---------------------------------------------------------------------------
# tell()
# ---------------------------------------------------------------------------
def tell(setting: Setting, activity: Activity, treasure_cfg: Treasure,
         hero_name: str = "Lily", hero_type: str = "girl",
         hero_traits: Optional[list[str]] = None,
         parent_type: str = "Captain") -> World:
    world = World(setting)
    hero = world.add(Entity(
        id=hero_name,
        type=hero_type,
        traits=["little"] + (hero_traits or ["brave", "greedy"]),
    ))
    parent = world.add(Entity(
        id="Captain",
        type=parent_type,
        label="Blackbeard" if parent_type == "Captain" else "Redbeard",
    ))
    treasure = world.add(Entity(
        id="treasure",
        type=treasure_cfg.type,
        label=treasure_cfg.label,
        phrase=treasure_cfg.phrase,
        owner=hero.id,
        plural=treasure_cfg.plural,
    ))

    # Act 1
    introduce(world, hero)
    loves_activity(world, hero, activity)
    buys_prize_not_needed(world, parent, hero, treasure_cfg)
    loves_prize(world, hero, treasure_cfg)

    # Act 2
    world.para()
    arrive(world, hero, parent, activity)
    wants(world, hero, parent, activity)
    warn(world, parent, hero, activity, treasure_cfg)
    defies(world, hero, activity)
    grab_hand(world, parent, hero, activity)

    # Act 3
    world.para()
    pout(world, hero, activity)
    gear_def = compromise(world, parent, hero, activity, treasure_cfg)
    if gear_def:
        accept(world, parent, hero, activity, treasure_cfg, gear_def)

    world.facts.update(
        hero=hero, parent=parent, prize=treasure, prize_cfg=treasure_cfg,
        activity=activity, setting=setting, gear=gear_def,
        conflict=True, resolved=gear_def is not None
    )
    return world


# ---------------------------------------------------------------------------
# StoryParams
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    activity: str
    treasure: str
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# QA Generators
# ---------------------------------------------------------------------------
KNOWLEDGE = {
    "treasure": [("What is a treasure?", "A treasure is a collection of valuable things like gold coins or jewels, often hidden.")],
    "greed": [("What does greedy mean?", "Greedy means wanting to keep everything for yourself and not share.")],
    "sharing": [("Why is sharing important?", "Sharing makes everyone happy and shows you care about others.")],
    "pirate": [("Who is a pirate?", "A pirate is someone who sails the seas looking for treasure and adventure.")],
}
KNOWLEDGE_ORDER = ["treasure", "greed", "sharing", "pirate"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, act = f["hero"], f["activity"]
    return [
        f'Write a short pirate story about a child who finds a spectacular treasure and learns a lesson about sharing.',
        f'A {hero.type} named {hero.id} wants to {act.verb} but discovers that being selfish can lead to trouble.',
        f'Tell a tale of transformation from greedy to generous, featuring a glistening treasure.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, parent, treasure, act = f["hero"], f["parent"], f["prize_cfg"], f["activity"]
    qa = [
        QAItem(
            question=f"Who is the young pirate in this story?",
            answer=f"The young pirate is {hero.id}, a {hero.type} who wanted to {act.verb}.",
        ),
        QAItem(
            question=f"What did Captain {parent.label} warn {hero.id} about?",
            answer=f"Captain {parent.label} warned that a true pirate shares, and that being greedy would spoil the treasure.",
        ),
        QAItem(
            question=f"What lesson did {hero.id} learn?",
            answer=f"{hero.id} learned that sharing the spectacular treasure made everyone happy, and that being generous is better than being greedy.",
        ),
        QAItem(
            question=f"How did {hero.id} change after the adventure?",
            answer=f"{hero.id} transformed from a greedy pirate into a generous one, and from then on always shared.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["activity"].tags)
    out = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
            out.extend(QAItem(q, a) for q, a in KNOWLEDGE[tag])
    return out


# ---------------------------------------------------------------------------
# ASP Twin (simplified, consistent structure)
# ---------------------------------------------------------------------------
ASP_RULES = r"""
treasure_at_risk(A, T) :- activity(A), treasure(T).
guards(G, selfish) :- gear(G).
compatible_fix(A, T) :- gear(G), guards(G, selfish).
valid(Place, A, T) :- affords(Place, A), treasure_at_risk(A, T), compatible_fix(A, T).
valid_story(Place, A, T, Gender) :- valid(Place, A, T), wears(Gender, T).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", pid, a))
    for aid, a in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
    for tid, t in TREASURES.items():
        lines.append(asp.fact("treasure", tid))
        for g in sorted(t.genders):
            lines.append(asp.fact("wears", g, tid))
    for g in GEAR:
        lines.append(asp.fact("gear", g.id))
        for m in sorted(g.guards):
            lines.append(asp.fact("guards", g.id, m))
    return "\n".join(lines)


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_facts() + "\n" + ASP_RULES + "\n#show valid/3.")
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: {len(clingo_set)} combos.")
        return 0
    print("MISMATCH")
    return 1


# ---------------------------------------------------------------------------
# Standard interface
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Pirate tale: spectacular treasure, lesson learned, transformation.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--treasure", choices=TREASURES)
    ap.add_argument("--gender", choices=["boy", "girl"])
    ap.add_argument("--parent", choices=["Captain"])
    ap.add_argument("--name")
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--all", action="store_true", help="generate curated set")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.treasure and args.gender and args.gender not in TREASURES[args.treasure].genders:
        raise StoryError(f"(Treasure '{args.treasure}' not typical for {args.gender}.)")
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.activity is None or c[1] == args.activity)
              and (args.treasure is None or c[2] == args.treasure)
              and (args.gender is None or args.gender in TREASURES[c[2]].genders)]
    if not combos:
        raise StoryError("No valid combination.")
    place, activity, treasure_id = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(sorted(TREASURES[treasure_id].genders))
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or "Captain"
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, activity=activity, treasure=treasure_id,
                       name=name, gender=gender, parent=parent, trait=trait, seed=None)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], ACTIVITIES[params.activity],
                 TREASURES[params.treasure], params.name, params.gender,
                 [params.trait], params.parent)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def emit(sample: StorySample, *, trace=False, qa=False, header=""):
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world:
        print("--- trace ---")
        for e in sample.world.entities.values():
            m = {k: v for k, v in e.memes.items() if v}
            if m:
                print(f"  {e.id}: {m}")
    if qa:
        print("\n== Prompts ==")
        for p in sample.prompts:
            print(f"- {p}")
        print("\n== Story QA ==")
        for q in sample.story_qa:
            print(f"Q: {q.question}\nA: {q.answer}\n")
        print("== World QA ==")
        for q in sample.world_qa:
            print(f"Q: {q.question}\nA: {q.answer}\n")


def main():
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_facts() + "\n" + ASP_RULES)
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        for c in combos:
            print(f"  {c[0]:8} {c[1]:8} {c[2]:8}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples = []
    if args.all:
        curated = [
            StoryParams("island", "digging", "gold", "Rex", "boy", "Captain", "brave"),
            StoryParams("cove", "cave", "jewels", "Nina", "girl", "Captain", "curious"),
            StoryParams("ship", "map", "crown", "Jake", "boy", "Captain", "greedy"),
        ]
        samples = [generate(p) for p in curated]
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
        if i < len(samples) - 1:
            print("\n" + "=" * 60 + "\n")


if __name__ == "__main__":
    main()
