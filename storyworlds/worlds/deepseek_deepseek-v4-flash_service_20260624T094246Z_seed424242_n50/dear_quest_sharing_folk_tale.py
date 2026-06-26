#!/usr/bin/env python3
"""
storyworlds/worlds/dear_quest_sharing_folk_tale.py
===================================================

A standalone story world for a folk tale about a dear (deer) who goes on a
quest and learns the power of sharing.
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
from results import QAItem, StoryError, StorySample

THRESHOLD = 1.0

# ---------------------------------------------------------------------------
# Entity
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "character"
    type: str = "deer"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        return {"subject": "it", "object": "it", "possessive": "its"}.get(case, "it")

    def it(self) -> str:
        return "them" if self.plural else "it"

# ---------------------------------------------------------------------------
# Domain data classes
# ---------------------------------------------------------------------------
@dataclass
class Setting:
    place: str = "the forest"
    indoor: bool = False
    affords: set[str] = field(default_factory=set)

@dataclass
class Quest:
    id: str
    verb: str          # "find the golden apple"
    gerund: str        # "searching for the golden apple"
    rush: str          # "dash toward the tree"
    reward: str        # description of the treasure
    moral: str         # lesson
    keyword: str = ""
    tags: set[str] = field(default_factory=set)

@dataclass
class Treasure:
    label: str
    phrase: str
    type: str
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

def _r_greed_tension(world: World) -> list[str]:
    out = []
    for actor in world.characters():
        if actor.memes["greed"] >= THRESHOLD and actor.memes["desire"] >= THRESHOLD:
            sig = ("tension", actor.id)
            if sig not in world.fired:
                world.fired.add(sig)
                actor.memes["conflict"] += 1
                out.append("__tension__")
    return out

def _r_sharing_resolves(world: World) -> list[str]:
    out = []
    for actor in world.characters():
        if actor.memes["generosity"] >= THRESHOLD and actor.memes["conflict"] >= THRESHOLD:
            sig = ("resolve", actor.id)
            if sig not in world.fired:
                world.fired.add(sig)
                actor.memes["joy"] += 2
                actor.memes["conflict"] = 0.0
                out.append(f"{actor.id} felt a warm glow spreading through {actor.pronoun('possessive')} heart.")
    return out

CAUSAL_RULES = [
    Rule("greed_tension", "emotional", _r_greed_tension),
    Rule("sharing_resolves", "emotional", _r_sharing_resolves),
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
                produced.extend(s for s in sents if s != "__tension__")
    if narrate:
        for s in produced:
            world.say(s)
    return produced

# ---------------------------------------------------------------------------
# Prediction
# ---------------------------------------------------------------------------
def predict_outcome(world: World, hero: Entity) -> dict:
    sim = world.copy()
    sim.entities[hero.id].memes["generosity"] += 1
    propagate(sim, narrate=False)
    resolved = sim.entities[hero.id].memes["conflict"] == 0.0
    return {"resolved": resolved}

# ---------------------------------------------------------------------------
# Storytelling verbs
# ---------------------------------------------------------------------------
def introduce(world: World, hero: Entity) -> None:
    trait = next((t for t in hero.traits if t != "little"), "curious")
    world.say(f"In a {world.setting.place.removeprefix('the ')}, there lived a little {trait} deer named {hero.id}.")

def loves_quest(world: World, hero: Entity, quest: Quest) -> None:
    hero.memes["love_adventure"] += 1
    world.say(f"{hero.id} loved hearing tales of {quest.gerund} and dreamed of doing it {hero.pronoun('possessive')}self.")

def elder_speaks(world: World, elder: Entity, hero: Entity, quest: Quest, treasure: Treasure) -> None:
    world.say(f"One morning, {elder.id} the wise owl came to {hero.id}. 'The {treasure.label} can be found only if you share it,' hooted the owl.")
    world.say(f"'{quest.reward} waits at the old oak, but it will be real only when you give some away.'")

def arrives(world: World, hero: Entity, elder: Entity, quest: Quest) -> None:
    world.say(f"{hero.id} and {elder.id} went to the old oak tree in the {world.setting.place.removeprefix('the ')}.")
    world.say(f"At the top, a {quest.reward} glowed softly.")

def wants(world: World, hero: Entity, quest: Quest) -> None:
    hero.memes["desire"] += 1
    world.say(f"{hero.id} wanted to {quest.verb} and keep the {quest.reward} all to {hero.pronoun('possessive')}self. 'It is mine!' whispered the deer.")

def warn(world: World, elder: Entity, hero: Entity, treasure: Treasure, quest: Quest) -> bool:
    pred = predict_outcome(world, hero)
    if not pred["resolved"]:
        return False
    world.say(f"'{hero.id}, remember the rule: only sharing makes the treasure belong to you,' said {elder.id} gently.")
    return True

def defies(world: World, hero: Entity, quest: Quest) -> None:
    hero.memes["greed"] += 1
    hero.memes["desire"] += 1
    world.say(f"{hero.id} did not listen. It lept and tried to {quest.rush} and grab the {quest.reward}.")

def stop_attempt(world: World, elder: Entity, hero: Entity) -> None:
    hero.memes["grabbed_by"] += 1
    world.say(f"But {elder.id} fluttered down and blocked the path. 'A little bit of patience, dear one.'")

def pout(world: World, hero: Entity) -> None:
    if hero.memes.get("conflict", 0.0) >= THRESHOLD:
        world.say(f"{hero.id} stamped its hoof. 'I want it all for me!'")

def share_decision(world: World, hero: Entity, elder: Entity, friends: list[Entity], treasure: Treasure) -> bool:
    # The hero decides to share
    hero.memes["generosity"] += 1
    propagate(world, narrate=False)
    if world.entities[hero.id].memes.get("conflict", 0.0) != 0.0:
        return False
    world.say(f"Then {hero.id} looked at the gathered friends—{', '.join(f.id for f in friends)}—and remembered the wise owl's words.")
    world.say(f"'{hero.pronoun('possessive').capitalize()} heart softened. 'Maybe... maybe we can share the {treasure.label}.'")
    return True

def resolution(world: World, hero: Entity, elder: Entity, friends: list[Entity], treasure: Treasure, quest: Quest) -> None:
    world.say(f"{hero.id} picked the {treasure.label} and gave a piece to each friend. As it shared, the fruit glowed brighter and doubled.")
    world.say(f"Soon there was enough for everyone, and even the hungry squirrel had a bite. The forest laughed with joy.")
    world.say(f"{hero.id} never forgot that {quest.moral}.")

# ---------------------------------------------------------------------------
# The tale
# ---------------------------------------------------------------------------
def tell(setting: Setting, quest: Quest, treasure_cfg: Treasure,
         hero_name: str = "Deary", hero_traits: Optional[list[str]] = None) -> World:
    world = World(setting)
    hero = world.add(Entity(
        id=hero_name, kind="character", type="deer", traits=(["little"] + (hero_traits or ["curious", "stubborn"])),
    ))
    elder = world.add(Entity(id="Ollie", kind="character", type="owl", label="wise old owl"))
    friends = [
        world.add(Entity(id="Squeaky", kind="character", type="squirrel", label="squirrel")),
        world.add(Entity(id="Hopper", kind="character", type="rabbit", label="rabbit")),
    ]
    treasure = world.add(Entity(
        id="treasure", kind="thing", type=treasure_cfg.type, label=treasure_cfg.label,
        phrase=treasure_cfg.phrase, plural=treasure_cfg.plural,
    ))

    introduce(world, hero)
    loves_quest(world, hero, quest)
    elder_speaks(world, elder, hero, quest, treasure_cfg)
    world.para()
    arrives(world, hero, elder, quest)
    wants(world, hero, quest)
    warn(world, elder, hero, treasure_cfg, quest)
    defies(world, hero, quest)
    stop_attempt(world, elder, hero)
    world.para()
    pout(world, hero)
    shared = share_decision(world, hero, elder, friends, treasure_cfg)
    if shared:
        resolution(world, hero, elder, friends, treasure_cfg, quest)

    world.facts.update(hero=hero, elder=elder, friends=friends,
                       treasure=treasure, treasure_cfg=treasure_cfg,
                       quest=quest, setting=setting,
                       shared=shared)
    return world

# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "forest": Setting(place="the forest", indoor=False, affords={"golden_apple", "shiny_stone"}),
    "meadow": Setting(place="the meadow", indoor=False, affords={"golden_apple"}),
    "mountain": Setting(place="the mountain", indoor=False, affords={"shiny_stone"}),
}
QUESTS = {
    "golden_apple": Quest(
        id="golden_apple",
        verb="find the golden apple",
        gerund="searching for the golden apple",
        rush="climb up the old oak",
        reward="golden apple",
        moral="sharing makes the treasure grow",
        keyword="apple",
        tags={"apple", "golden"},
    ),
    "shiny_stone": Quest(
        id="shiny_stone",
        verb="find the shiny stone",
        gerund="hunting for the shiny stone",
        rush="scamper up the rocky path",
        reward="shiny stone",
        moral="a shared joy is a double joy",
        keyword="stone",
        tags={"stone", "shiny"},
    ),
}
TREASURES = {
    "apple": Treasure(label="apple", phrase="a golden apple that smelled like sunshine", type="apple"),
    "stone": Treasure(label="stone", phrase="a shiny stone that flickered like a star", type="stone"),
}
HERO_NAMES = ["Deary", "Dottie", "Bambi", "Flora", "Fawn"]
TRAITS = ["curious", "stubborn", "playful", "brave", "gentle"]

def valid_combos() -> list[tuple[str, str, str]]:
    """Return all (setting, quest, treasure) triples that are reasonable."""
    combos = []
    for s_name, setting in SETTINGS.items():
        for q_name in setting.affords:
            q = QUESTS[q_name]
            # simple mapping: golden_apple -> apple, shiny_stone -> stone
            if q_name == "golden_apple":
                t_name = "apple"
            elif q_name == "shiny_stone":
                t_name = "stone"
            else:
                continue
            combos.append((s_name, q_name, t_name))
    return combos

# ---------------------------------------------------------------------------
# StoryParams
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    quest: str
    treasure: str
    name: str
    trait: str
    seed: Optional[int] = None

# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
KNOWLEDGE = {
    "apple": [
        ("What is a golden apple?",
         "A golden apple is a magical fruit that shines and smells wonderful, usually found in folk tales."),
    ],
    "stone": [
        ("What makes a stone shiny?",
         "Shiny stones look bright because water or minerals reflect light from their surface."),
    ],
    "sharing": [
        ("Why is sharing important?",
         "Sharing means giving a part of what you have to others. It makes everyone feel happy and connected."),
        ("What can happen when you share?",
         "When you share, the joy often grows, and sometimes the thing you share becomes even bigger or better."),
    ],
    "quest": [
        ("What is a quest?",
         "A quest is a big adventure or journey to find something special, like a treasure or a magical item."),
    ],
}
KNOWLEDGE_ORDER = ["apple", "stone", "sharing", "quest"]

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    quest = f["quest"]
    return [
        f'Write a short folk tale for children about a deer named {hero.id} going on a {quest.gerund} and learning about sharing.',
        f'Tell a story with the words "dear" and "quest" where a young deer discovers the magic of sharing a {quest.reward}.',
        f'Create a gentle tale from the forest where a deer must choose between keeping a treasure alone and sharing it with friends.',
    ]

def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    elder = f["elder"]
    quest = f["quest"]
    treasure_cfg = f["treasure_cfg"]
    place = f["setting"].place
    qa = [
        QAItem(
            question=f"Who went on a quest to the old oak in the {place}?",
            answer=f"A little deer named {hero.id} went with {elder.id}, the wise owl, on a quest to find the {treasure_cfg.phrase}."
        ),
        QAItem(
            question=f"What lesson did the wise owl {elder.id} teach {hero.id}?",
            answer=f"The owl said that the {treasure_cfg.label} would be real only if {hero.id} shared it with others."
        ),
    ]
    if f.get("shared"):
        qa.append(QAItem(
            question=f"How did {hero.id} finally get the {treasure_cfg.label}?",
            answer=f"{hero.id} decided to share the {treasure_cfg.label} with the squirrel and the rabbit. As soon as it gave pieces away, the fruit glowed and grew, giving everyone enough."
        ))
    return qa

def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["quest"].tags)
    out = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags or tag == "sharing":
            out.extend(QAItem(q, a) for q, a in KNOWLEDGE.get(tag, []))
    return out

def format_qa(sample):
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
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A treasure is associated with a quest type.
quest_treasure(Quest, Treasure) :- setting_affords(Place, Quest), treasure(Treasure).

% Valid only if the quest reward matches the treasure type (simple mapping).
valid(Place, Quest, Treasure) :- setting_affords(Place, Quest),
                                 quest(Quest), treasure(Treasure),
                                 quest_treasure(Quest, Treasure).
"""
def asp_facts() -> str:
    import asp
    lines = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        for a in s.affords:
            lines.append(asp.fact("setting_affords", pid, a))
    for qid, q in QUESTS.items():
        lines.append(asp.fact("quest", qid))
        # map quest to treasure
        if qid == "golden_apple":
            lines.append(asp.fact("quest_treasure", qid, "apple"))
        elif qid == "shiny_stone":
            lines.append(asp.fact("quest_treasure", qid, "stone"))
    for tid, t in TREASURES.items():
        lines.append(asp.fact("treasure", tid))
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
        print(f"OK: ASP matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between ASP and valid_combos():")
    print(" only in ASP:", sorted(clingo_set - python_set))
    print(" only in Python:", sorted(python_set - clingo_set))
    return 1

# ---------------------------------------------------------------------------
# Standard interface
# ---------------------------------------------------------------------------
def build_parser():
    ap = argparse.ArgumentParser(description="Folk tale about a dear deer on a quest of sharing.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--treasure", choices=TREASURES)
    ap.add_argument("--name")
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--all", action="store_true", help="curated set")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap

def resolve_params(args, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.quest is None or c[1] == args.quest)
              and (args.treasure is None or c[2] == args.treasure)]
    if not combos:
        raise StoryError("No valid combination matches the given options.")
    place, quest, treasure = rng.choice(sorted(combos))
    name = args.name or rng.choice(HERO_NAMES)
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, quest=quest, treasure=treasure, name=name, trait=trait)

def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], QUESTS[params.quest],
                 TREASURES[params.treasure], params.name,
                 [params.trait, "stubborn"])
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
        w = sample.world
        print("\n--- World model state ---")
        for e in w.entities.values():
            m = {k:v for k,v in {**e.meters, **e.memes}.items() if v}
            if m:
                print(f"  {e.id:8} {e.type:8} {m}")
    if qa:
        print("\n" + format_qa(sample))

def main():
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, quest, treasure) combos:")
        for c in combos:
            print(f"  {c[0]:9} {c[1]:15} {c[2]}")
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples = []
    if args.all:
        curated = [
            StoryParams(place="forest", quest="golden_apple", treasure="apple", name="Deary", trait="curious"),
            StoryParams(place="meadow", quest="golden_apple", treasure="apple", name="Dottie", trait="brave"),
        ]
        for p in curated:
            samples.append(generate(p))
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n*50, 50):
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
        if args.all or len(samples) > 1:
            header = f"### {sample.params.name}: {sample.params.quest} at {sample.params.place}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")

if __name__ == "__main__":
    main()
