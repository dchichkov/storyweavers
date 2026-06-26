#!/usr/bin/env python3
"""
Winter sharing, sound effects, surprise, and heartwarming domain.
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
MESS_KINDS = {"damp", "messy"}
REGIONS = {"neck", "hands", "feet"}

# ---------------------------------------------------------------------------
# Entities: characters and physical objects share one representation.
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"            # "character" | "thing"
    type: str = "thing"            # girl, boy, mother, father, scarf, mittens ...
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
        female = {"girl", "mother", "mom", "grandmother", "woman"}
        male = {"boy", "father", "dad", "grandfather", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad", "aunt": "aunt", "grandma": "grandma"}.get(self.type, self.type)

# ---------------------------------------------------------------------------
# Domain-specific configuration structures.
# ---------------------------------------------------------------------------
@dataclass
class Setting:
    place: str
    indoor: bool = False
    affords: set[str] = field(default_factory=set)  # activities supported here
    weather: str = ""

@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    mess: str
    soil: str
    zones: set[str]  # body regions exposed to winter conditions
    weather: str
    keyword: str = ""
    sound_effect: str = ""
    tags: set[str] = field(default_factory=set)

@dataclass
class Prize:
    label: str
    phrase: str
    type: str
    region: str
    plural: bool = False
    genders: set[str] = field(default_factory=lambda: {"girl", "boy"})
    warmth_factor: float = 1.0

# ---------------------------------------------------------------------------
# World model (state + narrator).
# ---------------------------------------------------------------------------
class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.exposed_zones: set[str] = set()
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

    def has_warm_cover(self, actor: Entity, zones: set[str]) -> bool:
        covered = set()
        for item in self.worn_items(actor):
            if item.region in zones:
                covered.add(item.region)
        return all(z in covered for z in zones)

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
        clone.exposed_zones = set(self.exposed_zones)
        clone.paragraphs = [[]]
        return clone

# ---------------------------------------------------------------------------
# Causal rules: forward-chained to fixpoint.
# ---------------------------------------------------------------------------
ACTIVITY_CAUSE_COLD = 1.0

@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]

def _rule_cold_exposure(world: World) -> list[str]:
    produced: list[str] = []
    if world.setting.indoor or not world.exposed_zones:
        return produced
    for actor in world.characters():
        if actor.meters["outdoor_time"] < THRESHOLD:
            continue
        if world.has_warm_cover(actor, world.exposed_zones):
            continue
        actor.meters["cold"] += ACTIVITY_CAUSE_COLD
        produced.append(f'{actor.pronoun().capitalize()} felt the sharp nip of the winter air.')
    return produced

def _rule_remove_outdoor_time(world: World) -> list[str]:
    produced: list[str] = []
    for actor in world.characters():
        if actor.meters["outdoor_time"] >= THRESHOLD:
            actor.meters["outdoor_time"] -= THRESHOLD
            if actor.meters["outdoor_time"] < 0:
                actor.meters["outdoor_time"] = 0
        else:
            actor.meters["outdoor_time"] = 0
    return produced

def _rule_warmth_from_fire(world: World) -> list[str]:
    produced: list[str] = []
    if not world.setting.indoor or not world.facts.get("fireplace"):
        return produced
    for actor in world.characters():
        if actor.meters["cold"] > 0.1:
            actor.meters["cold"] -= 0.5
            actor.meters["warm"] += 1.0
            produced.append(f'Close to the fireplace, {actor.pronoun()} began to feel cozy.')
    return produced

def _rule_shared_warmth(world: World) -> list[str]:
    produced: list[str] = []
    if not world.facts.get("sharing_scarf"):
        return produced
    for actor in world.characters():
        actor.memes["love"] += 0.7
        actor.memes["joy"] += 0.5
        if actor.meters["cold"] > 0:
            actor.meters["cold"] -= 0.4
    produced.append("A moment of shared warmth around the scarf strengthened their bond.")
    return produced

CAUSAL_RULES: list[Rule] = [
    Rule(name="cold_exposure", tag="physical", apply=_rule_cold_exposure),
    Rule(name="remove_outdoor", tag="physical", apply=_rule_remove_outdoor_time),
    Rule(name="warm_fire", tag="physical", apply=_rule_warmth_from_fire),
    Rule(name="share_warmth", tag="social", apply=_rule_shared_warmth),
]

def propagate(world: World) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(sents)
    return produced

# ---------------------------------------------------------------------------
# Utility verbs used in the screenplay.
# ---------------------------------------------------------------------------
def activity_delight(activity: Activity) -> str:
    return {
        "sledding": "the sled swooshed down the snowy hill with a crisp crunch",
        "build_snowman": "the little snowballs packed tight in the cold hands",
        "snowball_fight": "laughter and the soft thud of snowballs all around",
    }.get(activity.id, "the winter air felt full of playful energy")

def setting_detail(setting: Setting, activity: Activity) -> str:
    if setting.indoor:
        fire = "the fireplace crackled happily"
        return f"{setting.place.replace('the ', '').capitalize()} glowed in the soft light of {fire}."
    if activity.weather == "snowy":
        return f"{setting.place.capitalize()} sparkled under a blanket of fresh snow."
    return setting.place.capitalize()

def outside_sounds(activity: Activity) -> str:
    return activity.sound_effect or f"the winter breeze whispered and the snow crunched softly"

def seems_perfect_for(activity: Activity, prize: Prize) -> str:
    bonus = {
        ("sledding", "scarf"): " to keep the neck warm while racing downhill",
        ("build_snowman", "mittens"): " to keep the hands cozy while shaping snow",
    }.get((activity.id, prize.label), "")
    return f"{prize.phrase} seemed perfect{bonus}."

def _do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    world.exposed_zones = set(activity.zones)
    actor.meters["joy"] += 1.0
    actor.meters["outdoor_time"] += 1.0
    if narrate:
        world.say(f"{actor.pronoun().capitalize()} loved {activity.gerund}.")
        world.say(outside_sounds(activity))
    propagate(world)

def introduce(world: World, hero: Entity) -> None:
    trait = next((t for t in hero.traits if t != "little" and t != "sweet"), "")
    desc = f"little {trait} {hero.type}".strip()
    world.say(f"{hero.id} was a {desc} who adored the first snowfall of every year.")

def receives_gift_from(world: World, hero: Entity, parent: Entity, prize: Prize, giver: str) -> None:
    hero.memes["surprise"] += 1.0
    hero.memes["love"] += 1.5
    world.say(
        f"That morning, {parent.pronoun('possessive')} {parent.label_word} {giver} "
        f"brought a surprise for {hero.id}: {prize.phrase}."
    )
    world.say(f"{hero.pronoun().capitalize()} gasped and hugged {giver} tightly.")

def tries_to_go_outside_now(world: World, hero: Entity, parent: Entity, activity: Activity) -> None:
    hero.memes["desire"] += 1.0
    world.say(
        f"{hero.pronoun().capitalize()} begged {hero.pronoun('possessive')} {parent.label_word} "
        f"to go {activity.verb} right away."
    )

def warns_about_cold(world: World, parent: Entity, hero: Entity, activity: Activity, prize: Prize) -> None:
    pred = predict_outdoor_conditions(world, hero, activity, prize.id)
    if pred["risky"]:
        world.facts["body_zones_need"] = activity.zones
        world.facts["scarf_needed"] = prize.label if "neck" in activity.zones else ""
        clause = f"You'll catch a chilly cold on your neck if you go without "
        clause += f"the {prize.label} today."
        world.say(f'"{clause}" {parent.pronoun("possessive")} {parent.label_word} said firmly.')
        world.facts["parent_warned"] = True

def defies_warning(world: World, hero: Entity) -> None:
    hero.memes["defiance"] += 1.0
    world.say(f"{hero.id} frowned but headed for the door anyway, {hero.pronoun()} still eager.")

def grabs_hand_to_hold(world: World, parent: Entity, hero: Entity, prize: Prize) -> None:
    hero.memes["grabbed_by"] += 1.0
    world.say(
        f'{parent.pronoun().capitalize()} gently grabbed {hero.pronoun("object")} hand. '
        f'"Wait for the {prize.label}; then we can go and {hero.pronoun("it")} will be safe."'
    )
    propagate(world)

def puts_on_warm_item(world: World, hero: Entity, item: Entity) -> None:
    item.worn_by = hero.id
    hero.memes["joy"] -= 0.3   # reluctant compliance
    hero.memes["love"] += 0.6   # protective warmth
    world.say(
        f'{hero.id} slipped {hero.pronoun("possessive").capitalize()} arms into '
        f"{item.phrase} and felt a little happier already."
    )

def surprise_visit(world: World, hero: Entity, friend: Entity, activity: Activity) -> None:
    friend.memes["excitement"] += 1.5
    world.paragraphs.append([])
    world.say(f"Just then, {friend.id} hopped over the fence with a shout!")
    world.say(f'"Let\'s go {activity.verb} together!" {friend.pronoun()} laughed.')
    world.facts["friend_joined"] = True

def play_together(world: World, hero: Entity, friend: Entity, activity: Activity) -> None:
    hero.memes["joy"] += 1.2
    world.say(
        f"Together, {hero.id} and {friend.id} spent a joyful time "
        f"{activity.gerund}, giggling all the way."
    )

def realizes_need_for_warmth(world: World, hero: Entity, prize: Entity) -> None:
    hero.memes["realization"] += 1.0
    world.say(
        f"{hero.pronoun().capitalize()} noticed {hero.pronoun('possessive')} "
        f"{prize.label} was the only thing keeping the sharp wind away."
    )

def go_indoors_together(world: World, hero: Entity, parent: Entity) -> None:
    world.paragraphs.append([])
    world.say(
        f"{hero.id} and {hero.pronoun('possessive')} {parent.label_word} "
        f"went back inside to shake off the cold."
    )

def share_hot_chocolate(world: World, hero: Entity, parent: Entity, friend: Optional[Entity] = None) -> None:
    world.facts["fireplace"] = True
    world.facts["sharing_scarf"] = True
    world.say(
        "Inside, a warm mug of hot chocolate with marshmallows waited on the table."
    )
    actor = friend or parent
    world.say(
        f"{hero.id} carefully draped {hero.pronoun('possessive')} {world.get('scarf').phrase} "
        f"around {actor.pronoun()} shoulders while sipping."
    )
    world.facts["shared_moment"] = True

def ends_with_heartwarming_moment(world: World) -> None:
    world.paragraphs.append([])
    world.say(
        "The crackling fire, the gentle hum of satisfied laughter, and the softly glowing "
        "scarf wrapped round shoulders made the room feel like a haven."
    )

# ---------------------------------------------------------------------------
# Prediction helper (forward simulate small state changes).
# ---------------------------------------------------------------------------
def predict_outdoor_conditions(world: World, actor: Entity, activity: Activity, prize_id: str) -> dict:
    sim = world.copy()
    _do_activity(sim, sim.get(actor.id), activity, narrate=False)
    if activity.zones - {world.get(prize_id).region}:
        return {"risky": True, "missing": sorted(activity.zones - {world.get(prize_id).region})}
    return {"risky": False}

def prize_at_risk(activity: Activity, prize: Prize) -> bool:
    return prize.region in activity.zones

# ---------------------------------------------------------------------------
# Main screenplay: three-act winter tale.
# ---------------------------------------------------------------------------
def tell(setting: Setting, activity: Activity, prize_cfg: Prize,
         name: str = "Emma", gender: str = "girl",
         hero_traits: Optional[list[str]] = None,
         parent_type: str = "mother",
         giver_type: str = "grandmother") -> World:
    world = World(setting)
    world.setting.weather = activity.weather

    hero = world.add(Entity(
        id=name,
        kind="character",
        type=gender,
        traits=["little", "playful"] + (hero_traits or ["eager", "curious"]),
    ))
    parent = world.add(Entity(
        id="Parent", kind="character", type=parent_type, label="mom"
    ))
    giver = world.add(Entity(
        id="Grandma", kind="character", type=giver_type, label="grandma"
    ))
    prize = world.add(Entity(
        id="scarf",
        type=prize_cfg.type,
        label=prize_cfg.label,
        phrase=prize_cfg.phrase,
        region=prize_cfg.region,
        plural=prize_cfg.plural,
    ))

    # Act 1 — gift and early excitement
    world.paragraphs.append([])
    introduce(world, hero)
    receives_gift_from(world, hero, parent, prize_cfg, giver.label_word)
    world.para()

    # Act 2 — conflict over outdoor play
    world.setting = SETTINGS["backyard"]
    world.say(setting_detail(world.setting, activity))
    tries_to_go_outside_now(world, hero, parent, activity)
    warns_about_cold(world, parent, hero, activity, prize_cfg)

    defies_warning(world, hero)
    grabs_hand_to_hold(world, parent, hero, prize_cfg)

    # compromise: wear the prize
    world.para()
    realizes_need_for_warmth(world, hero, prize)
    puts_on_warm_item(world, hero, prize)
    _do_activity(world, hero, activity)

    # surprise visit
    friend = world.add(Entity(
        id="Jake", kind="character", type="boy", label="Jake"
    ))
    surprise_visit(world, hero, friend, activity)
    play_together(world, hero, friend, activity)

    # Act 3 — cozy indoor resolution
    world.para()
    go_indoors_together(world, hero, parent)
    share_hot_chocolate(world, hero, parent, friend)
    ends_with_heartwarming_moment(world)

    # Record facts for Q&A generators
    world.facts.update(
        hero=hero, parent=parent, giver=giver, friend=friend,
        prize=prize, activity=activity, fire_place=True,
        shared_scarf=True, cold_scene=hero.meters.get("cold", 0) > 0.5
    )
    return world

# ---------------------------------------------------------------------------
# Global registries — clean, constraint-valid domain vocabulary.
# ---------------------------------------------------------------------------
SETTINGS = {
    "backyard": Setting(
        place="the backyard",
        indoor=False,
        affords={"sledding"},
        weather="snowy"
    ),
    "living_room": Setting(
        place="the cozy living room",
        indoor=True,
        affords=set()
    ),
}

ACTIVITIES = {
    "sledding": Activity(
        id="sledding",
        verb="go sledding",
        gerund="sledding down the snowy hill",
        rush="race to the sled",
        mess="snowy",
        soil="damp",
        zones={"neck"},
        weather="snowy",
        sound_effect="the crisp crunch of snow underfoot and a swoosh as the sled sped downward",
        keyword="sled",
        tags={"winter", "snow", "play"},
    ),
    "build_snowman": Activity(
        id="build_snowman",
        verb="build a snowman",
        gerund="building a snowman together",
        rush="dig out the snow",
        mess="snowy",
        soil="snowy",
        zones={"hands"},
        weather="snowy",
        sound_effect="soft padding as hands packed snow tight",
        keyword="snowman",
        tags={"winter", "joy"},
    ),
}

PRIZES = {
    "scarf": Prize(
        label="scarf",
        phrase="a bright red knitted scarf with tiny snowflakes",
        type="scarf",
        region="neck",
        plural=False,
        genders={"girl", "boy"},
        warmth_factor=0.3,
    ),
    "mittens": Prize(
        label="mittens",
        phrase="soft fluffy mittens",
        type="mittens",
        region="hands",
        plural=True,
        genders={"girl", "boy"},
        warmth_factor=0.2,
    ),
    "wool_hat": Prize(
        label="wool hat",
        phrase="a snug wool hat with a pom-pom",
        type="hat",
        region="head",
        plural=False,
        genders={"girl", "boy"},
        warmth_factor=0.4,
    ),
}

GIRL_NAMES = ["Emma", "Olivia", "Ava", "Sophia", "Isabella"]
BOY_NAMES = ["James", "Benjamin", "Lucas", "Mason", "Ethan"]
TRAITS = ["eager", "curious", "sweet", "playful", "chatty"]

def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for aid in setting.affords:
            act = ACTIVITIES[aid]
            for pid, pr in PRIZES.items():
                if prize_at_risk(act, pr):
                    combos.append((place, aid, pid))
    return sorted(set(combos))

# ---------------------------------------------------------------------------
# Q&A generation — three separate pillars.
# ---------------------------------------------------------------------------
KNOWLEDGE = {
    "winter": [
        ("What season is it in the story?",
         "It is wintertime, with fresh snow covering everything outside."),
    ],
    "scarf": [
        ("What keeps a neck warm in winter?",
         "A scarf wraps snugly around the neck to trap heat and block cold wind."),
    ],
    "hot_chocolate": [
        ("Why is hot chocolate good on a cold day?",
         "Sipping warm, sweet liquid helps the body warm up from the inside out."),
    ],
    "snow": [
        ("Why does snow sparkle?",
         "Fresh snow scatters sunlight in many directions, creating tiny glittery reflections."),
    ],
    "sled": [
        ("What sounds does a sled make on snow?",
         "Sleds usually swoosh downhill with a gentle crunch as they glide over the snow."),
    ],
}
KNOWLEDGE_ORDER = ["winter", "sled", "snow", "scarf", "hot_chocolate"]

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, act = f["hero"], f["activity"]
    kw = act.keyword or act.mess
    return [
        f'Write a gentle winter story for a 3-to-5-year-old about sharing and surprise '
        f'that includes the word "{kw}".',
        f'Tell a heartwarming tale where a {hero.type} named {hero.id} receives a '
        f'cozy gift, heads outside to play, and discovers friendship and warmth '
        f'when a surprise visit happens.',
        f'Craft a simple story that uses sound descriptions and ends with a '
        f'parent, child, and friend sharing hot cocoa by a fire.',
    ]

def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    sub, obj, pos = (hero.pronoun("subject"), hero.pronoun("object"), hero.pronoun("possessive"))
    prize = f["prize"]
    act = f["activity"]
    giver = f["giver"]
    pword = f["parent"].label_word
    traits = [t for t in hero.traits if t not in ("little", "playful")]
    qa: list[QAItem] = [
        QAItem(
            question=(
                f"Who is the story about when {hero.id} goes down the snowy hill "
                f"wearing {pos} {prize.label}?"
            ),
            answer=(
                f"It is about a little {traits[0] if traits else hero.type} named "
                f"{hero.id}. On a snowy morning, {hero.pronoun()} received "
                f"a cozy {prize.label} from {giver.label_word}, then headed outside "
                f"to play with {obj}."
            ),
        ),
        QAItem(
            question=(
                f"What did {hero.id} feel when {pos} {giver.label_word} gave "
                f"{hero.pronoun('object')} the {prize.label}?"
            ),
            answer=(
                f"{hero.id} felt happy and surprised. {hero.pronoun().capitalize()} "
                f"hugged {giver.label_word} tightly and looked forward to wearing "
                f"the new gift outdoors."
            ),
        ),
    ]
    if f.get("cold_scene"):
        qa.append(QAItem(
            question=(
                f"Why did {hero.id}'s {pword} insist on wearing the {prize.label} "
                f"before going outside?"
            ),
            answer=(
                f"Even though it was exciting to play right away, the winter air "
                f"would have made {hero.pronoun()} feel too cold on {pos} neck "
                f"without it. The {prize.label} kept {hero.pronoun()} safe and warm."
            ),
        ))
    if f.get("friend_joined"):
        qa.append(QAItem(
            question=(
                f"What surprise happened while {hero.id} and {pos} {pword} "
                f"were playing outside?"
            ),
            answer=(
                f"A friend named Jake showed up with a sled and invited {hero.id} "
                f"to play together. The unexpected visit made the fun even better."
            ),
        ))
    if f.get("shared_scarf"):
        qa.append(QAItem(
            question=("How did everyone feel when they shared the hot chocolate indoors?"),
            answer=(
                f"Wrapped in cozy blankets with warm mugs in hand, they all felt "
                f"happy, safe, and full of love for one another. The room glowed "
                f"with happiness."
            ),
        ))
    return qa

def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    tags = set()
    for act in ACTIVITIES.values():
        tags.update(act.tags)
    qa: list[QAItem] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
            qa.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE.get(tag, []))
    return qa

def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts ==="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("\n== (2) Story questions ===")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("\n== (3) World-knowledge questions ===")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)

# ---------------------------------------------------------------------------
# ASP Twin (clingo gate)
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% Compatible story iff the prize covers the activity’s exposed zones
prize_at_risk(P) :- zones(A,Z), prize_region(P,R), in_list(R,Z).
covered(P) :- prize_at_risk(P).
valid_story(Place,Activity,Prize) :-
    setting_place(Place),
    affords(Place,Activity),
    prize_at_zone(Prize,Region),
    zones(Activity,Zones),
    cover_all(Zones,Region).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("setting_place", pid))
        if s.indoor:
            lines.append(asp.fact("indoor", pid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", pid, a))
    for aid, a in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        for r in sorted(a.zones):
            lines.append(asp.fact("zones", aid, r))
    for pid, pr in PRIZES.items():
        lines.append(asp.fact("prize_at_zone", pid, pr.region))
    return "\n".join(lines)

def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"

def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))

def asp_verify() -> int:
    clingo_set, python_set = set(asp_valid_combos()), set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo matches Python ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if clingo_set - python_set:
        print("  only in clingo  :", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in Python  :", sorted(python_set - clingo_set))
    return 1

# ---------------------------------------------------------------------------
# CLI / trace
# ---------------------------------------------------------------------------
def dump_trace(world: World) -> str:
    lines = ["--- world state ---"]
    for e in world.entities.values():
        m = {k: v for k, v in e.meters.items() if v}
        x = {k: v for k, v in e.memes.items() if v}
        fields = []
        if m:
            fields.append(f"m={dict(m)}")
        if x:
            fields.append(f"e={dict(x)}")
        if e.worn_by:
            fields.append(f"worn_by={e.worn_by}")
        lines.append(f"  {e.id:10} ({e.type}) {'; '.join(fields)}")
    lines.append(f"  fired={sorted([n for n, *_ in world.fired])}")
    lines.append(f"  keys={list(world.facts.keys())}")
    return "\n".join(lines)

# Curated set of heartwarming tales
CURATED = [
    StoryParams(
        place="backyard",
        activity="sledding",
        prize="scarf",
        name="Emma",
        gender="girl",
        parent="mom",
        trait="eager",
    ),
    StoryParams(
        place="backyard",
        activity="build_snowman",
        prize="mittens",
        name="Lucas",
        gender="boy",
        parent="dad",
        trait="curious",
    ),
]

# ---------------------------------------------------------------------------
# Standard storyworld interface
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

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Winter sharing, sound effects, surprise, and heartwarming stories.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mom", "dad"])
    ap.add_argument("--name")
    ap.add_argument("--trait")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--all", action="store_true", help="render curated set")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON")
    ap.add_argument("--asp", action="store_true", help="list ASP-valid combos")
    ap.add_argument("--verify", action="store_true", help="check ASP gate")
    ap.add_argument("--show-asp", action="store_true", help="print full ASP program")
    return ap

def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.activity and args.prize:
        act, pr = ACTIVITIES[args.activity], PRIZES[args.prize]
        if not prize_at_risk(act, pr):
            raise StoryError(
                f"No story: '{act.verb}' does not risk making the {pr.label} "
                f"({pr.region}) messy in winter conditions."
            )
    combos = [
        c for c in valid_combos()
        if (args.place is None or c[0] == args.place)
        and (args.activity is None or c[1] == args.activity)
        and (args.prize is None or c[2] == args.prize)
    ]
    if not combos:
        raise StoryError("(No valid combination matches given constraints.)")

    place, act_id, prize_id = rng.choice(combos)
    prize = PRIZES[prize_id]
    gender = args.gender or rng.choice(sorted(prize.genders))
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or ("mom" if gender == "girl" else "dad")
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(
        place=place, activity=act_id, prize=prize_id,
        name=name, gender=gender, parent=parent, trait=trait
    )

def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.place],
        ACTIVITIES[params.activity],
        PRIZES[params.prize],
        params.name,
        params.gender,
        [params.trait],
        giver_type="grandmother"
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
        print("\n" + format_qa(sample))

def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        triples = asp_valid_combos()
        print(f"{len(triples)} ASP-verified winter tales:\n")
        for place, act, prize in triples:
            print(f"  • {place:10} | {act:14} | {prize}")
        return

    seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 30, 30):
            i += 1
            try:
                params = resolve_params(args, random.Random(seed + i))
            except StoryError as err:
                print(err)
                return
            params.seed = seed + i
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

    for idx, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.gender} {p.trait} {p.activity} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 60 + "\n")

if __name__ == "__main__":
    main()
