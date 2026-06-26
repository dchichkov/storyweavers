#!/usr/bin/env python3
"""
故事世界源文件：
  storyworlds/worlds/catastrophe_dig_gyp_misunderstanding_sound_effects_adventure.py
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

# Threshold at which to narrate an effect
THRESHOLD = 1.0

# Meters that count as a “mess” from digging
MESS_KINDS = {"dirt", "dust", "cobweb"}

# Body regions are less relevant here; we just mark torso for wearables
REGIONS = {"torso"}

# ---------------------------------------------------------------------------
# Entities: characters and physical objects
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
    region: str = "torso"
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mom", "sister"}
        male = {"boy", "dad", "brother"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

# ---------------------------------------------------------------------------
# Parametrization knobs -- swappable lore of this tiny domain
# ---------------------------------------------------------------------------
@dataclass
class Setting:
    place: str = "the woods"
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
    weather: str
    keyword: str = ""
    tags: set[str] = field(default_factory=set)

@dataclass
class Prize:
    label: str
    phrase: str
    type: str
    region: str = "hands"
    plural: bool = False
    genders: set[str] = field(default_factory=lambda: {"boy", "girl"})

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
# World: entity store + narration history
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

    def worn_items(self, actor: Entity) -> list[Entity]:
        return [e for e in self.entities.values() if e.worn_by == actor.id]

    def covered(self, actor: Entity, region: str) -> bool:
        """Is a region shielded by any worn protective item?"""
        return any(g.protective and region in g.covers for g in self.worn_items(actor))

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
        clone.para     # silence predictions
        return clone

# ---------------------------------------------------------------------------
# Causal rules: forward-chained to a fixpoint.
# ---------------------------------------------------------------------------
@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]

def _r_pile_dirt(world: World) -> list[str]:
    """Digging piles dirt/shakes cobwebs onto the digger/torso."""
    out: list[str] = []
    for actor in world.characters():
        if actor.meters.get("digging", 0.0) < THRESHOLD:
            continue
        sig = ("pile", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.meters["dirt"] += 1
        actor.meters["cobweb"] += 0.5
        if world.entities.get("bees") is not None:
            # Trigger rule for bee swarm later
            pass
        out.append(f"{actor.pronoun('subject')} flecked bits of dirt and cobweb onto {actor.pronoun('possessive')} clothes.")
    return out

def _r_bee_swarm(world: World) -> list[str]:
    """If bees present and digging passes threshold, swarm appears."""
    bees = world.entities.get("bees")
    if bees is None:
        return []
    if world.facts.get("bees_trapped", False):
        return []
    for actor in world.characters():
        if actor.meters.get("digging", 0.0) >= THRESHOLD:
            sig = ("swarm", actor.id)
            if sig not in world.fired:
                world.fired.add(sig)
                bees.memes["buzzing"] += 3.0
                out = (
                    f"As soon as {actor.pronoun('subject')} sank the shovel again, "
                    f"a furious buzz filled the air! A swarm of bees burst from the disturbed earth!"
                )
                world.say(out)
                return [out]
    return []

def _r_sound_effects(world: World) -> list[str]:
    """Using a noise tool/skill quiets the swarm."""
    out: list[str] = []
    for actor in world.characters():
        if bees := world.entities.get("bees"):
            if bees.memes.get("buzzing", 0.0) >= THRESHOLD:
                noise = next((e for e in world.entities.values() if e.id == "noise_tool"), None)
                if noise and noise.owner == actor.id:
                    sig = ("calm", actor.id, noise.id)
                    if sig not in world.fired:
                        world.fired.add(sig)
                        bees.memes["buzzing"] -= 2.0
                        out.append(
                            f"{actor.pronoun('subject')} clapped {noise.label} over {actor.pronoun('possessive')} ears "
                            f"and let out a rhythmic — bzzzt-bzzzt — tapping. Gradually the buzz softened..."
                        )
    return out

CAUSAL_RULES: list[Rule] = [
    Rule(name="pile_dirt", tag="physical", apply=_r_pile_dirt),
    Rule(name="bee_swarm", tag="catastrophe", apply=_r_bee_swarm),
    Rule(name="sound_effects", tag="trick", apply=_r_sound_effects),
]

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

# ---------------------------------------------------------------------------
# Constraint helpers -- reasonableness gate
# ---------------------------------------------------------------------------
def prize_at_risk(activity: Activity, prize: Prize) -> bool:
    """A prize is at risk if the activity's zone can mess the wear region."""
    return True  # all prizes are in hands here; digging action overlaps

def select_gear(activity: Activity, prize: Prize) -> Optional[Gear]:
    """Protective sound-maker that quiets the swarm and is compatible with the activity."""
    for gear in GEAR:
        if activity.mess in gear.guards:
            return gear
    return None

# ---------------------------------------------------------------------------
# Verbs: coarse screenplay beats
# ---------------------------------------------------------------------------
def activity_tingle(activity: Activity) -> str:
    return {
        "dig_for_treasure": "the rich scent of damp earth rose into the air",
    }.get(activity.id, "dirt crumbled at the touch")

def setting_detail(setting: Setting, _) -> str:
    if setting.indoor:
        return "The attic was musty and cool."
    if setting.place == "the beach":
        return "Sunlight bleached the sand, and hermit crabs scattered nearby."
    return f"The {setting.place} hummed with unseen life."

def _do_activity(world: World, actor: Entity, activity: Activity) -> None:
    actor.meters["digging"] += 1.5
    world.zone = set(activity.zone)
    propagate(world, narrate=True)

def taunt_prankster(world: World, sibling: Entity, hero: Entity) -> None:
    sibling.memes["mischief"] += 1.0
    world.say(
        f"{sibling.id} smirked. 'It’s just a dumb old prank map — see? "
        f"Three trees in a row! Even Grandpa’s doodles couldn’t be that lopsided!'"
    )

def hand_map(world: World, sibling: Entity, hero: Entity, prize: Entity) -> None:
    hero.memes["intrigue"] += 1.5
    world.say(
        f"{sibling.id} plucked {prize.phrase} from {hero.pronoun('possessive')} bag "
        f"and tossed {hero.pronoun('object')} to {hero.id}. "
        f"'Maybe if you dig *there* you’ll find out it’s all a gyp,' {sibling.pronoun('subject')} giggled."
    )
    world.para()

def marches_to_spot(world: World, hero: Entity, setting: Setting) -> None:
    where = "inside" if setting.indoor else "outside"
    world.say(
        f"{hero.id} marched to a towering oak at the edge of {setting.place} "
        f"and marveled at {activity_tingle(world.facts.get('activity', Activity(id='dig', verb='', gerund='', rush='', mess='dirt', soil='', zone=set(), weather=''))).mess} underfoot."
    )

def shovel_first_strike(world: World, hero: Entity) -> None:
    hero.memes["determination"] += 2.0
    world.say(
        f"{hero.pronoun('subject').capitalize()} raised the shovel, took aim, "
        f"and plunged it into the soft loam."
    )
    _do_activity(world, hero, world.facts["activity"])

def sibling_warns(world: World, sibling: Entity, hero: Entity) -> None:
    world.say(
        f"{sibling.id} called, 'Double-check the map! The treasure symbol’s right over there!' "
        f"Meanwhile, a low tremor rippled under {hero.pronoun('possessive')} sneakers."
    )

def bee_swarm_alert(world: World, hero: Entity) -> None:
    bees = world.entities.get("bees")
    if bees and bees.memes.get("buzzing", 0.0) >= THRESHOLD:
        world.say(
            f"WHUMP. A thick cloud of bees exploded around {hero.id}, "
            f"venom needle-daggers glinting like a tiny, angry galaxy!"
        )

def use_noise_tool(world: World, hero: Entity, gear: Gear) -> None:
    noise = world.add(Entity(
        id="noise_tool",
        type="gear",
        label=gear.label,
        owner=hero.id,
    ))
    world.say(
        f"{hero.id} yanked the lumpy {noise.label} from {hero.pronoun('possessive')} pocket "
        f"and mimicked an old tractor engine — brrrrrrm-brrrm-bzzzt!"
    )
    bees = world.entities.get("bees")
    if bees:
        hero.memes["clever"] += 1.5
        bee_swarm_alert(world, hero)     # fun nod
        world.say(
            f"Slowly, reluctantly, the swarm settled onto a low branch "
            f"like metallic lace pinned to the sky."
        )

def small_reward(world: World, hero: Entity, prize: Entity) -> None:
    hero.memes["pride"] += 2.0
    world.say(
        f"Barely daring to breathe, {hero.id} brushed off the soil "
        f"and revealed… {prize.phrase}!"
    )

def reflection(world: World, sibling: Entity, hero: Entity, prize: Entity) -> None:
    world.para()
    world.say(
        f"Back at the table, {sibling.id} ducked {hero.pronoun('possessive')} head. "
        f"'Okay, that wasn’t a gyp.' {hero.pronoun('subject')} had found small treasure — "
        f"and big adventure."
    )

# ---------------------------------------------------------------------------
# The screenplay: three-act adventure
# ---------------------------------------------------------------------------
def tell(setting: Setting, activity: Activity, prize_cfg: Prize,
         hero_name: str = "Riley", hero_type: str = "kid",
         sibling_type: str = "older sibling") -> World:
    world = World(setting)
    world.weather = "sunny" if not setting.indoor else ""

    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type=hero_type,
        traits=["curious", "brave"],
    ))
    sibling = world.add(Entity(
        id=f"{hero_name}'s sibling",
        kind="character",
        type=sibling_type,
        label="their older sibling",
    ))
    prize = world.add(Entity(
        id="prize",
        type=prize_cfg.type,
        label=prize_cfg.label,
        phrase=prize_cfg.phrase,
        plural=prize_cfg.plural,
    ))
    bees = world.add(Entity(
        id="bees",
        type="swarm",
        label="buzzing cloud of bees",
        traits=["irritable"],
        memes={"buzzing": 0.0},
    ))

    # Act 1 — setup: prank map handed to hero, sibling laughs
    world.say(f"{hero.id} rummaged through the attic shelves.")
    world.say(setting_detail(setting, activity))
    taunt_prankster(world, sibling, hero)
    hand_map(world, sibling, hero, prize)

    # Act 2 — conflict: journey to oak, first strike, swarm erupts
    world.para()
    marches_to_spot(world, hero, setting)
    shovel_first_strike(world, hero)
    sibling_warns(world, sibling, hero)

    # Catastrophe unavoidable here
    world.para()
    bee_swarm_alert(world, hero)

    # Act 3 — resolution: sound effects quiet swarm, small reward
    world.para()
    for gear in GEAR:
        if activity.mess in gear.guards:
            use_noise_tool(world, hero, gear)
            break
    small_reward(world, hero, prize)
    reflection(world, sibling, hero, prize)

    # Record facts for Q&A
    world.facts.update(
        hero=hero,
        sibling=sibling,
        prize=prize,
        prize_cfg=prize_cfg,
        activity=activity,
        setting=setting,
        bees=bees,
        catastrophe=world.facts.get("catastrophe", True),
        resolved=world.entities.get("noise_tool") is not None,
    )
    return world

# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "woods": Setting(place="the deep woods", indoor=False, affords={"dig_for_treasure"}),
    "beach": Setting(place="the beach", indoor=False, affords={"dig_for_treasure"}),
    "backyard": Setting(place="the backyard", indoor=False, affords={"dig_for_treasure"}),
    "attic": Setting(place="the attic", indoor=True, affords=set()),
}

ACTIVITIES = {
    "dig_for_treasure": Activity(
        id="dig_for_treasure",
        verb="dig around the big oak",
        gerund="digging under the old oak",
        rush="race to the old oak",
        mess="dirt",
        soil="covered in dirt",
        zone={"torso"},
        weather="sunny",
        keyword="treasure",
        tags={"treasure", "dig", "misunderstanding", "catastrophe", "sound_effects"},
    ),
}

PRIZES = {
    "treasure_map": Prize(
        label="treasure map",
        phrase="a mysterious treasure map",
        type="map",
    ),
    "gem": Prize(
        label="jewel",
        phrase="a glowing jewel",
        type="jewel",
    ),
    "fake_gold": Prize(
        label="brass medallion",
        phrase="a chipped brass medallion",
        type="medallion",
    ),
    "ordinary_seashell": Prize(
        label="ordinary seashell",
        phrase="an ordinary seashell",
        type="seashell",
    ),
}

GEAR = [
    Gear(
        id="noise_bandana",
        label="noise-canceling bandana",
        covers=set(),
        guards={"buzzing"},
        prep="tie the bandana around your ears",
        tail="the drumbeat of a muffled lull grew under {hero}",
    ),
    Gear(
        id="voice_skills",
        label="mimic skills",
        covers=set(),
        guards={"buzzing"},
        prep="use your mimic voice to imitate an old tractor engine",
        tail="the swarm floated still, hypnotised by the brrrm-bzzzt rhythm",
    ),
]

GIRL_NAMES = ["Aria", "Mira", "Nova", "Luna", "Kiara"]
BOY_NAMES = ["Riley", "Jace", "Dax", "Zane", "Eli"]
TRAITS = ["curious", "clever", "brave"]

def valid_combos() -> list[tuple[str, str, str]]:
    """(place, activity, prize) triples compatible with the reasonableness gate."""
    combos = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            for prize_id, prize in PRIZES.items():
                if prize_at_risk(ACTIVITIES[act_id], prize):
                    if select_gear(ACTIVITIES[act_id], prize):
                        combos.append((place, act_id, prize_id))
    return combos

# ---------------------------------------------------------------------------
# Per-world parameters (domain-specific; generic containers live in results.py)
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    name: str
    gender: str
    trait: str
    seed: Optional[int] = None

# ---------------------------------------------------------------------------
# Q&A generation — three deliberately separate sets
# ---------------------------------------------------------------------------
# (3) Child-level world knowledge
KNOWLEDGE = {
    "buzz": [
        ("What does a bee hive sound like?",
         "A bee hive buzzes — a thick, fuzzy hum that grows louder when the hive is disturbed."),
    ],
    "treasure": [
        ("What is treasure?",
         "Treasure is something precious found in an unexpected place; it doesn’t have to be gold."),
    ],
    "dig": [
        ("Why do people dig holes?",
         "People dig holes to plant gardens, bury time capsules, or explore what’s underneath the earth."),
    ],
    "gyp": [
        ("What does it mean when something is a gyp?",
         "A gyp is a trick or swindle — when something turns out to be worth far less than expected."),
    ],
    "sound_effect": [
        ("What are sound effects?",
         "Sound effects are noises we make with our mouth or tools to mimic real-world sounds, "
         "like engines or thunder, to make stories more exciting."),
    ],
}
KNOWLEDGE_ORDER = ["treasure", "dig", "buzz", "gyp", "sound_effect"]

def generation_prompts(world: World) -> list[str]:
    act = world.facts["activity"]
    return [
        f'Write a short Adventure story (age 4-7) using the words "catastrophe", "dig", "gyp". '
        f'Feature Misunderstanding (someone lies or jokes about a map) and Sound Effects.',
        f"Compose a Tiny Adventure tale where a child chases an old treasure idea, "
        f"encounters a catastrophe, and turns it into triumph using mimic sounds.",
        f'Tell a brief adventure that includes a swarm, digging, and a "gyp" reveal all in one.' ]

def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, sibling, prize, act = f["hero"], f["sibling"], f["prize"], f["activity"]
    trait = next((t for t in hero.traits if t != "little"), hero.type)
    sub, obj, pos = (hero.pronoun("subject"), hero.pronoun("object"),
                     hero.pronoun("possessive"))
    where = "inside" if world.setting.indoor else "outside"
    place = world.setting.place

    qa: list[QAItem] = [
        QAItem(
            question=(
                f"Who handed {hero.id} the treasure map in the {place} and why?"
            ),
            answer=(
                f"An {f['sibling'].type} {f['sibling'].id} handed {hero.id} "
                f"{prize.phrase} as a joke — they thought it was all a gyp."
            ),
        ),
        QAItem(
            question=(
                f"What happened when {hero.id} started {act.gerund}?"
            ),
            answer=(
                f"The very first shovel strike sent a swarm of bees erupting from the earth. "
                f"A true catastrophe!"
            ),
        ),
    ]
    if f.get("resolved"):
        qa.append(QAItem(
            question=(
                f"How did {hero.id} calm the swarm without getting stung?"
            ),
            answer=(
                f"{hero.id} used {GEAR[1].label}: they imitated an old tractor engine "
                f"with their mimic voice, and the bees calmed down like metal filings stilling under magnetic hum."
            ),
        ))
    return qa

def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["activity"].tags)
    out: list[QAItem] = []
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
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)

# ---------------------------------------------------------------------------
# Clingo (ASP) twin — declarative gate mirroring the Python reasonableness check
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A prize in hands is in the “danger zone” for digging adventures.
prize_at_risk(A, P) :- activity(A), prize(P).

% Noise gear neutralises buzzing from a nearby swarm triggered by digging.
can_quiet(G) :- gear(G), guards(G, buzzing).
swarms :- setting(S), outdoors(S).
buzzing :- swarms, prize_at_risk(A, _), digging(A), depth(A)>1.
valid_story(P) :- prize_at_risk(A, P), can_quiet(_).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        if s.indoor:
            lines.append(asp.fact("indoor", pid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", pid, a))
    for aid, a in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        lines.append(asp.fact("digging", aid))
        lines.append(asp.fact("mess_of", aid, a.mess))
    for pid, pr in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        if pr.plural:
            lines.append(asp.fact("prize_plural", pid))
        for g in sorted(pr.genders):
            lines.append(asp.fact("wears", g, pid))
    for g in GEAR:
        lines.append(asp.fact("gear", g.id))
        for m in sorted(g.guards):
            lines.append(asp.fact("guards", g.id, m))
    return "\n".join(lines)

def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"

def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/1."))
    return sorted(set(asp.atoms(model, "valid_story")))

def asp_verify() -> int:
    clingo_set = set(asp_valid_combos())
    python_set = set((p.place, p.activity, p.prize) for p in valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1

# ---------------------------------------------------------------------------
# Standard storyworld interface
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Tiny Adventure world: dig, gyp, misunderstanding, sound effects.")
    ap.add_argument("--place", choices=list(SETTINGS))
    ap.add_argument("--activity", choices=list(ACTIVITIES))
    ap.add_argument("--prize", choices=list(PRIZES))
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--seed", type=int)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap

def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.activity and args.prize:
        act, pr = ACTIVITIES[args.activity], PRIZES[args.prize]
        if not (prize_at_risk(act, pr) and select_gear(act, pr)):
            raise StoryError("Activity and prize are incompatible.")

    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.activity is None or c[1] == args.activity)
              and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError("No matching (place, activity, prize) combination found.")

    place, activity, prize_id = rng.choice(combos)
    sex = rng.choice(["girl", "boy"]) if not args.gender else args.gender
    name = args.name or rng.choice(GIRL_NAMES if sex == "girl" else BOY_NAMES)
    trait = rng.choice(TRAITS)
    return StoryParams(
        place=place,
        activity=activity,
        prize=prize_id,
        name=name,
        gender=sex,
        trait=trait,
    )

def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], ACTIVITIES[params.activity],
                 PRIZES[params.prize], params.name, "kid")
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
    if trace and sample.world:
        print("\n--- world model state ---")
        for e in sample.world.entities.values():
            ms = {k:v for k,v in e.meters.items() if v}
            sm = {k:v for k,v in e.memes.items() if v}
            print(f"  {e.id:12} {e.type:8} "
                  f"meters={dict(ms)} memes={dict(sm)}")
    if qa:
        print("\n" + format_qa(sample))

def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        triples = [ (p.place, p.activity, p.prize) for p in valid_combos() ]
        print(f"{len(triples)} compatible stories:")
        for place, act, prize in sorted(triples):
            print(f"  {place:10} {act:18} {prize}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(1 << 31)
    rng = random.Random(base_seed)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in [
            StoryParams(place="attic", activity="dig_for_treasure", prize="treasure_map", name="Nova", gender="girl", trait="curious"),
            StoryParams(place="beach", activity="dig_for_treasure", prize="ordinary_seashell", name="Dax", gender="boy", trait="clever"),
        ]]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n*50, 50):
            try:
                params = resolve_params(args, rng)
            except StoryError as err:
                print(err)
                return
            params.seed = base_seed + i
            sample = generate(params)
            story_txt = sample.story
            if story_txt in seen:
                i += 1
                continue
            seen.add(story_txt)
            samples.append(sample)
            i += 1

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, s in enumerate(samples):
        header = ""
        if args.all or len(samples) > 1:
            header = f"### adventure {i+1} ###"
        emit(s, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples)-1:
            print("\n"+("="*60)+"\n")

if __name__ == "__main__":
    main()
