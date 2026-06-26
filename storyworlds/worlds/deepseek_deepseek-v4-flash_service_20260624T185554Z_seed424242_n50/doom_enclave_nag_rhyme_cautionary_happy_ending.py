#!/usr/bin/env python3
"""
storyworlds/worlds/doom_enclave_nag_rhyme_cautionary_happy_ending.py
====================================================================

A folk tale in rhyme: a nagging crow warns a little one about a doom that
threatens the enclave.  The story begins with love for a risky activity, a
worn prize that could be ruined, a warning, defiance, a parent's intervention,
and a happy compromise that saves the day.
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
MESS_KINDS = {"wet", "muddy", "sandy", "scratched"}
REGIONS = {"feet", "legs", "torso"}

# ---------------------------------------------------------------------------
# Rhyming helpers – a small internal set of rhyme pairs used by the storyteller.
# ---------------------------------------------------------------------------
RHYMES: dict[str, list[str]] = defaultdict(list)
_RHYME_PAIRS = [
    ("day", "play"), ("day", "away"), ("gate", "late"), ("gate", "fate"),
    ("home", "roam"), ("home", "alone"), ("stream", "dream"), ("stream", "gleam"),
    ("child", "wild"), ("child", "mild"), ("doom", "room"), ("doom", "bloom"),
    ("wall", "all"), ("wall", "call"), ("shoes", "choose"), ("shoes", "blues"),
    ("coat", "boat"), ("coat", "note"), ("crow", "blow"), ("crow", "know"),
    ("tall", "small"), ("tall", "fall"), ("hand", "land"), ("hand", "stand"),
    ("good", "wood"), ("good", "hood"), ("rain", "pain"), ("rain", "gain"),
    ("bright", "light"), ("bright", "might"), ("dear", "fear"), ("dear", "near"),
    ("fly", "sky"), ("fly", "why"), ("plain", "again"), ("plain", "train"),
]
for a, b in _RHYME_PAIRS:
    RHYMES[a].append(b)
    RHYMES[b].append(a)

def pick_rhyme(word: str, used: set[str]) -> str:
    """Return a word that rhymes with `word` and is not in `used` (if possible)."""
    candidates = [w for w in RHYMES.get(word, []) if w not in used]
    return random.choice(candidates) if candidates else word  # fallback

def couplet(line1: str, line2: Optional[str] = None) -> str:
    """Return two rhyming lines (AABB form).  if line2 is None, generate one."""
    if line2 is None:
        # the caller will supply the second line separately; just return line1
        return line1
    return f"{line1}\n{line2}"

# ---------------------------------------------------------------------------
# Entity
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"            # "character" | "thing"
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
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

# ---------------------------------------------------------------------------
# Content registries
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
    covers: set[str]
    guards: set[str]
    prep: str
    tail: str
    plural: bool = False

# ––– settings –––
SETTINGS = {
    "enclave": Setting(
        place="the hidden enclave",
        affords={"river_play", "harvest"},
    ),
    "valley": Setting(
        place="the whispering valley",
        affords={"river_play", "harvest"},
    ),
}
# ––– activities –––
ACTIVITIES = {
    "river_play": Activity(
        id="river_play",
        verb="splash in the river",
        gerund="splashing in the river",
        rush="run into the river",
        mess="wet",
        soil="sopping wet",
        zone={"feet", "legs"},
        weather="rainy",
        keyword="river",
        tags={"water", "wet"},
    ),
    "harvest": Activity(
        id="harvest",
        verb="pick the golden grain",
        gerund="gathering gold grain",
        rush="run to the field",
        mess="scratch",
        soil="torn and scratched",
        zone={"torso"},
        weather="sunny",
        keyword="harvest",
        tags={"grain", "scratch"},
    ),
}
# ––– prizes –––
PRIZES = {
    "tunic": Prize(
        label="tunic",
        phrase="a fine linen tunic",
        type="tunic",
        region="torso",
    ),
    "shoes": Prize(
        label="shoes",
        phrase="new leather shoes",
        type="shoes",
        region="feet",
        plural=True,
    ),
}
# ––– gear (protective) –––
GEAR = [
    Gear(
        id="waders",
        label="sturdy waders",
        covers={"legs", "feet"},
        guards={"wet"},
        prep="put on the waders first",
        tail="went to fetch the waders",
    ),
    Gear(
        id="burlap_sack",
        label="a burlap sack",
        covers={"torso"},
        guards={"scratch"},
        prep="wrap yourself in a burlap sack",
        tail="ran to get the burlap sack",
    ),
]
# ––– name/trait pools –––
GIRL_NAMES = ["Lara", "Mira", "Ella", "Tilly", "Nell"]
BOY_NAMES = ["Toby", "Finn", "Rory", "Bram", "Cale"]
TRAITS = ["brave", "curious", "stubborn", "gleeful", "bright"]

# ––– nag character –––
NAG_NAMES = ["Crow", "Old Meg", "The Watcher"]

def prize_at_risk(activity: Activity, prize: Prize) -> bool:
    return prize.region in activity.zone

def select_gear(activity: Activity, prize: Prize) -> Optional[Gear]:
    for gear in GEAR:
        if activity.mess in gear.guards and prize.region in gear.covers:
            return gear
    return None

def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            act = ACTIVITIES[act_id]
            for prize_id, prize in PRIZES.items():
                if prize_at_risk(act, prize) and select_gear(act, prize):
                    combos.append((place, act_id, prize_id))
    return combos

# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------
class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[str] = []
        self.zone: set[str] = set()
        self.weather: str = ""
        self.facts: dict = {}
        self.used_rhymes: set[str] = set()

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
        return any(g.protective and region in g.covers for g in self.worn_items(actor))

    def say(self, line: str) -> None:
        if line:
            self.paragraphs.append(line)

    def render(self) -> str:
        return "\n".join(self.paragraphs)

    def copy(self) -> "World":
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.zone = set(self.zone)
        clone.weather = self.weather
        clone.paragraphs = []
        clone.used_rhymes = set(self.used_rhymes)
        return clone

# ––– causal rules –––
def _r_soak(world: World) -> list[str]:
    out = []
    for actor in world.characters():
        for mess in MESS_KINDS:
            if actor.meters[mess] < THRESHOLD:
                continue
            for item in world.worn_items(actor):
                if item.protective or item.region not in world.zone:
                    continue
                if world.covered(actor, item.region):
                    continue
                sig = ("soak", item.id, mess)
                if sig in world.fired:
                    continue
                world.fired.add(sig)
                item.meters[mess] += 1
                item.meters["dirty"] += 1
                out.append(
                    f"{actor.pronoun('possessive').capitalize()} {item.label} "
                    f"grew {mess} and soiled."
                )
    return out

def _r_workload(world: World) -> list[str]:
    out = []
    for item in list(world.entities.values()):
        if item.meters["dirty"] < THRESHOLD or not item.caretaker:
            continue
        sig = ("work", item.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        carer = world.get(item.caretaker)
        carer.meters["workload"] += 1
        out.append(f"More toil for {carer.label}, a weary load.")
    return out

def _r_grab_conflict(world: World) -> list[str]:
    for actor in world.characters():
        if actor.memes["grabbed_by"] < THRESHOLD or actor.memes["defiance"] < THRESHOLD:
            continue
        sig = ("conflict", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["conflict"] += 1
        return ["__conflict__"]
    return []

CAUSAL_RULES = [
    ("soak", "physical", _r_soak),
    ("workload", "physical", _r_workload),
    ("grab_conflict", "social", _r_grab_conflict),
]

def propagate(world: World, narrate: bool = True) -> list[str]:
    produced = []
    changed = True
    while changed:
        changed = False
        for _, _, rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if s != "__conflict__")
    if narrate:
        for s in produced:
            world.say(s)
    return produced

# ---------------------------------------------------------------------------
# Forward prediction (parent's world model)
# ---------------------------------------------------------------------------
def predict_mess(world: World, actor: Entity, activity: Activity, prize_id: str) -> dict:
    sim = world.copy()
    _do_activity(sim, sim.get(actor.id), activity, narrate=False)
    prize = sim.entities.get(prize_id)
    return {
        "soiled": bool(prize and prize.meters["dirty"] >= THRESHOLD),
        "workload": sum(e.meters["workload"] for e in sim.characters()),
    }

# ---------------------------------------------------------------------------
# Storytelling functions (rhyme generation)
# ---------------------------------------------------------------------------
def _line_rhyme(line: str, world: World) -> str:
    """Return a rhyming companion line for the given line."""
    words = line.strip().split()
    if not words:
        return ""
    last = words[-1].strip(".,!?").lower()
    rhyme = pick_rhyme(last, world.used_rhymes)
    world.used_rhymes.add(rhyme)
    # replace the last word with its rhyme, adjusting plural if needed
    if last == "gate":
        return line.rsplit(last, 1)[0] + "late."
    if last == "shoes":
        return line.rsplit(last, 1)[0] + "blues."
    if last == "day":
        return line.rsplit(last, 1)[0] + "play."
    if last == "wall":
        return line.rsplit(last, 1)[0] + "call."
    # generic fallback
    return line.rsplit(last, 1)[0] + rhyme + "."

def activity_delight(activity: Activity) -> str:
    if activity.id == "river_play":
        return "the cool water made the day feel bright"
    return "the golden grain shone in the light"

def setting_detail(setting: Setting, activity: Activity) -> str:
    if setting.indoor:
        return f"Within {setting.place}, the hearth was small."
    if activity.weather == "rainy":
        return f"The sky hung grey above the wall."
    return f"The sun smiled on the valley tall."

def introduce(world: World, hero: Entity, nag: Entity) -> None:
    trait = next((t for t in hero.traits if t != "little"), "")
    world.say(f"Little {trait} {hero.id} loved to roam,")
    world.say(f"Through {world.setting.place}, their second home.")
    # nag introduction
    world.say(f"But {nag.id} the {nag.type} watched from the gate,")
    world.say(f"And croaked a warning: 'It is late!'")

def loves_activity(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["love_play"] += 1
    where = "inside" if world.setting.indoor else "outside"
    a = activity.gerund
    world.say(f"{hero.pronoun().capitalize()} loved to go {where} and {a},")
    world.say(f"For {activity_delight(activity)} each day.")

def buys(world: World, parent: Entity, hero: Entity, prize: Entity) -> None:
    world.say(f"Then {parent.label_word} bought with gentle care")
    world.say(f"{prize.phrase}, beyond compare.")

def loves_prize(world: World, hero: Entity, prize: Entity) -> None:
    hero.memes["love"] += 1
    prize.worn_by = hero.id
    world.say(f"{hero.id} wore {prize.it()} proud and tall,")
    world.say(f"As if {prize.it()} belonged to one and all.")

def arrive(world: World, hero: Entity, parent: Entity, activity: Activity) -> None:
    day = {"rainy": "One rainy day, ", "sunny": "One sunny day, "}.get(world.weather, "One day, ")
    go = "were in" if world.setting.indoor else "went to"
    world.say(f"{day}{hero.id} and {parent.label_word} {go} {world.setting.place}.")
    world.say(setting_detail(world.setting, activity))

def wants(world: World, hero: Entity, parent: Entity, activity: Activity) -> None:
    hero.memes["desire"] += 1
    v = activity.verb
    world.say(f"{hero.id} wished to {v}, right there,")
    world.say(f"But {parent.label_word} said, 'Child, beware.'")

def nag_warning(world: World, nag: Entity, activity: Activity) -> None:
    world.say(f"'{nag.id} the {nag.type} calls doom!' they said,")
    world.say(f"'The {activity.keyword} will rise! Take higher ground instead!'")

def warn(world: World, parent: Entity, hero: Entity, activity: Activity, prize: Entity) -> bool:
    pred = predict_mess(world, hero, activity, prize.id)
    if not pred["soiled"]:
        return False
    world.facts["predicted_soil"] = activity.soil
    world.facts["predicted_workload"] = pred["workload"]
    clause = f"Your {prize.label} will get {activity.soil}"
    if pred["workload"] >= THRESHOLD:
        clause += ", and I'll have to clean that toil."
    world.say(f'"{clause}" the {parent.label_word} said with a sigh,')
    world.say('"The nag's warning is not a lie."')
    return True

def defies(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["defiance"] += 1
    world.say(f"{hero.id} heard the warning, but the wish was strong,")
    world.say(f"{hero.pronoun().capitalize()} tried to {activity.rush} along.")

def grab_hand(world: World, parent: Entity, hero: Entity) -> None:
    hero.memes["grabbed_by"] += 1
    propagate(world, narrate=False)
    world.say(f"But the hand of {parent.label_word} held fast,")
    world.say(f'And said, "We choose a way that will last."')

def pout(world: World, hero: Entity) -> None:
    if hero.memes["conflict"] >= THRESHOLD:
        world.say(f"{hero.id} pouted, arms crossed tight,")
        world.say('"But I want to play with all my might!"')

def compromise(world: World, parent: Entity, hero: Entity, activity: Activity,
               prize: Entity) -> Optional[Gear]:
    gear_def = select_gear(activity, prize)
    if gear_def is None:
        return None
    gear = world.add(Entity(
        id=gear_def.id, type="gear", label=gear_def.label,
        owner=hero.id, caretaker=parent.id, protective=True,
        covers=set(gear_def.covers), plural=gear_def.plural,
    ))
    gear.worn_by = hero.id
    if predict_mess(world, hero, activity, prize.id)["soiled"]:
        gear.worn_by = None
        del world.entities[gear.id]
        return None
    prep = gear_def.prep
    world.say(f'Then {parent.label_word} smiled: "Let us {prep},"')
    world.say(f'And together they {gear_def.tail}.')
    return gear_def

def accept(world: World, parent: Entity, hero: Entity, activity: Activity,
           prize: Entity, gear_def: Gear) -> None:
    hero.memes["joy"] += 1
    hero.memes["love"] += 1
    hero.memes["conflict"] = 0.0
    world.say(f"{hero.id} laughed and hugged {parent.label_word} dear,")
    world.say(f'"We are safe because we chose to hear!"')
    world.say(f"They {activity.gerund} in the {activity.keyword} light,")
    world.say(f"And {prize.label} stayed clean and bright.")

# ---------------------------------------------------------------------------
# The tell screenplay
# ---------------------------------------------------------------------------
def tell(setting: Setting, activity: Activity, prize_cfg: Prize,
         hero_name: str = "Lara", hero_type: str = "girl",
         hero_traits: Optional[list[str]] = None,
         parent_type: str = "mother", nag_name: str = "Crow") -> World:
    world = World(setting)
    world.weather = "" if setting.indoor else activity.weather

    hero = world.add(Entity(
        id=hero_name, kind="character", type=hero_type,
        traits=["little"] + (hero_traits or ["brave", "stubborn"]),
    ))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label="the parent"))
    prize = world.add(Entity(
        id="prize", type=prize_cfg.type, label=prize_cfg.label,
        phrase=prize_cfg.phrase, owner=hero.id, caretaker=parent.id,
        region=prize_cfg.region, plural=prize_cfg.plural,
    ))
    nag = world.add(Entity(
        id=nag_name, kind="character", type="crow",
        label=nag_name, traits=["wise", "persistent"],
    ))

    # Act 1
    introduce(world, hero, nag)
    loves_activity(world, hero, activity)
    buys(world, parent, hero, prize)
    loves_prize(world, hero, prize)

    # Act 2
    world.say("")
    arrive(world, hero, parent, activity)
    wants(world, hero, parent, activity)
    nag_warning(world, nag, activity)
    warn(world, parent, hero, activity, prize)
    defies(world, hero, activity)
    grab_hand(world, parent, hero)

    # Act 3
    world.say("")
    pout(world, hero)
    gear_def = compromise(world, parent, hero, activity, prize)
    if gear_def:
        accept(world, parent, hero, activity, prize, gear_def)

    world.facts.update(hero=hero, parent=parent, prize=prize, prize_cfg=prize_cfg,
                       activity=activity, setting=setting, gear=gear_def, nag=nag,
                       conflict=hero.memes["grabbed_by"] >= THRESHOLD,
                       resolved=gear_def is not None)
    return world

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
    nag: str
    seed: Optional[int] = None

# ---------------------------------------------------------------------------
# Knowledge base (child world knowledge)
# ---------------------------------------------------------------------------
KNOWLEDGE = {
    "water": [
        ("Why does water make clothes wet?",
         "Water soaks into the tiny holes in the cloth, making it feel damp and heavy."),
    ],
    "wet": [
        ("What happens when you stay in wet clothes too long?",
         "You can get cold and shiver because wet cloth pulls heat away from your skin."),
    ],
    "grain": [
        ("What is golden grain?",
         "It is the seed of plants like wheat or barley, used to make bread and porridge."),
    ],
    "scratch": [
        ("Why do scratches hurt?",
         "Because a sharp edge tears the skin a little, and your body feels that as pain."),
    ],
    "crow": [
        ("Why do crows caw loudly?",
         "Crows call out to warn other animals about danger or to tell them where food is."),
    ],
}
KNOWLEDGE_ORDER = ["water", "wet", "grain", "scratch", "crow"]

# ---------------------------------------------------------------------------
# Q&A generation
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, parent, act, prize = f["hero"], f["parent"], f["activity"], f["prize_cfg"]
    kw = act.keyword or act.mess
    return [
        f'Write a rhyming folk tale about a {hero.type} named {hero.id} who '
        f'loves to {act.verb} in {world.setting.place}, and a wise {f["nag"].type} '
        f'that warns of doom.',
        f'A cautionary rhyme: a {prize.label} is at risk, a {f["nag"].type} nags, '
        f'and a parent finds a compromise.',
        f'Create a happy-ending folk tale in rhyme using the word "{kw}".',
    ]

def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, parent, prize, act, nag = f["hero"], f["parent"], f["prize"], f["activity"], f["nag"]
    pw = parent.label_word
    sub, obj, pos = hero.pronoun("subject"), hero.pronoun("object"), hero.pronoun("possessive")
    place = world.setting.place
    trait = next((t for t in hero.traits if t != "little"), hero.type)
    day = {"rainy": "rainy day", "sunny": "sunny day"}.get(world.weather, "play day")
    qa = [
        QAItem(
            question=f"Who warned about the doom in the story of {hero.id} at {place}?",
            answer=f"A wise {nag.type} named {nag.id} croaked a warning from the gate."
        ),
        QAItem(
            question=f"Why did {pw} stop {hero.id} from {act.gerund} right away?",
            answer=f"Because {pos} {prize.label} would get {act.soil}, as the {nag.type} had foretold."
        ),
        QAItem(
            question=f"Did {hero.id} and {pw} finally find a way to play safely?",
            answer=f"Yes, they used {f['gear'].label if f.get('gear') else 'something'} to protect the {prize.label}, and then {sub} could {act.verb} happily."
        ),
    ]
    if f.get("resolved"):
        qa.append(QAItem(
            question=f"How did the story of {hero.id} end?",
            answer=f"It ended happily: {hero.id} hugged {pos} {pw} and played without ruining the {prize.label}."
        ))
    return qa

def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    tags = set(f["activity"].tags)
    out = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
            out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE[tag])
    return out

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
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)

CURATED = [
    StoryParams(place="enclave", activity="river_play", prize="tunic",
                name="Lara", gender="girl", parent="mother", trait="brave",
                nag="Crow"),
    StoryParams(place="valley", activity="harvest", prize="shoes",
                name="Toby", gender="boy", parent="father", trait="curious",
                nag="Old Meg"),
]

def explain_rejection(activity: Activity, prize: Prize) -> str:
    noun = prize.label if prize.plural else f"a {prize.label}"
    if not prize_at_risk(activity, prize):
        return (f"(No story: {activity.gerund} splashes {sorted(activity.zone)}, "
                f"but {noun} sits on {prize.region} – no honest risk.)")
    return (f"(No story: no gear protects {noun} from {activity.gerund}.)")

def explain_gender(prize_id: str, gender: str) -> str:
    ok = " / ".join(sorted(PRIZES[prize_id].genders))
    return f"(No story: a {prize_id} isn't for a {gender}; try {ok}.)"

# ---------------------------------------------------------------------------
# ASP twin (inline clingo)
# ---------------------------------------------------------------------------
ASP_RULES = r"""
prize_at_risk(A, P) :- splashes(A, R), worn_on(P, R).
protects(G, A, P) :- gear(G), prize_at_risk(A, P),
                     mess_of(A, M), guards(G, M),
                     covers(G, R), worn_on(P, R).
has_fix(A, P) :- protects(_, A, P).
valid(Place, A, P) :- affords(Place, A), prize_at_risk(A, P), has_fix(A, P).
valid_story(Place, A, P, Gender) :- valid(Place, A, P), wears(Gender, P).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        if s.indoor:
            lines.append(asp.fact("indoor", pid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", pid, a))
    for aid, a in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        lines.append(asp.fact("mess_of", aid, a.mess))
        for r in sorted(a.zone):
            lines.append(asp.fact("splashes", aid, r))
    for pid, pr in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("worn_on", pid, pr.region))
        if pr.plural:
            lines.append(asp.fact("prize_plural", pid))
        for g in sorted(pr.genders):
            lines.append(asp.fact("wears", g, pid))
    for g in GEAR:
        lines.append(asp.fact("gear", g.id))
        for m in sorted(g.guards):
            lines.append(asp.fact("guards", g.id, m))
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
    print("MISMATCH between clingo and valid_combos():")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1

# ---------------------------------------------------------------------------
# Standard interface
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Folk tale in rhyme: a child, a nag, a doom, a happy ending.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--nag", choices=NAG_NAMES)
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
    if args.activity and args.prize:
        act, pr = ACTIVITIES[args.activity], PRIZES[args.prize]
        if not (prize_at_risk(act, pr) and select_gear(act, pr)):
            raise StoryError(explain_rejection(act, pr))
    if args.gender and args.prize and args.gender not in PRIZES[args.prize].genders:
        raise StoryError(explain_gender(args.prize, args.gender))

    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.activity is None or c[1] == args.activity)
              and (args.prize is None or c[2] == args.prize)
              and (args.gender is None or args.gender in PRIZES[c[2]].genders)]
    if not combos:
        raise StoryError("No valid combination matches.")

    place, activity, prize_id = rng.choice(sorted(combos))
    prize = PRIZES[prize_id]
    gender = args.gender or rng.choice(sorted(prize.genders))
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    nag = args.nag or rng.choice(NAG_NAMES)
    return StoryParams(
        place=place, activity=activity, prize=prize_id,
        name=name, gender=gender, parent=parent, trait=trait, nag=nag,
    )

def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], ACTIVITIES[params.activity],
                 PRIZES[params.prize], params.name, params.gender,
                 [params.trait, "stubborn"], params.parent, params.nag)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )

def emit(sample: StorySample, *, trace: bool = False, qa: bool = False,
         header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print("== Prompts ==")
        for p in sample.prompts:
            print(f"  - {p}")
        print("== Story QA ==")
        for item in sample.story_qa:
            print(f"Q: {item.question}\nA: {item.answer}\n")
        print("== World Knowledge ==")
        for item in sample.world_qa:
            print(f"Q: {item.question}\nA: {item.answer}\n")

def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        triples = asp_valid_combos()
        print(f"{len(triples)} compatible (place, activity, prize) combos:\n")
        for place, act, prize in triples:
            print(f"  {place:9} {act:8} {prize}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

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
            header = f"### {p.name}: {p.activity} at {p.place} (prize: {p.prize})"
        elif len(samples) > 1:
            header = f"### variant {i+1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")

if __name__ == "__main__":
    main()
