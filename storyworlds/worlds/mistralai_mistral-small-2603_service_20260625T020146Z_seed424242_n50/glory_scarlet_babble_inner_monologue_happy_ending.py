#!/usr/bin/env python3

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
MESS_KINDS = {"foamy", "stained"}
REGIONS = {"hands", "clothes"}

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
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)

@dataclass
class Setting:
    place: str = "the garden"
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
    region: str
    genders: set[str] = field(default_factory=lambda: {"girl", "boy"})
    plural: bool = False

@dataclass
class Gear:
    id: str
    label: str
    covers: set[str]
    guards: set[str]
    prep: str
    tail: str
    plural: bool = False

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
        clone.zone = set(self.zone)
        clone.weather = self.weather
        clone.paragraphs = [[]]
        return clone

@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]

def _r_soak(world: World) -> list[str]:
    out: list[str] = []
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
                    f"became {mess} and stained."
                )
    return out

def _r_workload(world: World) -> list[str]:
    out: list[str] = []
    for item in list(world.entities.values()):
        if item.meters["dirty"] < THRESHOLD or not item.caretaker:
            continue
        sig = ("work", item.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        carer = world.get(item.caretaker)
        carer.meters["workload"] += 1
        out.append(f"That meant more tidy-up for {carer.label}.")
    return out

def _r_conflict(world: World) -> list[str]:
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

CAUSAL_RULES: list[Rule] = [
    Rule(name="soak", tag="physical", apply=_r_soak),
    Rule(name="workload", tag="physical", apply=_r_workload),
    Rule(name="conflict", tag="social", apply=_r_conflict),
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
                produced.extend(s for s in sents if s != "__conflict__")
    if narrate:
        for s in produced:
            world.say(s)
    return produced

def activity_glow(activity: Activity) -> str:
    acts = {
        "scarlet_bubbles": "a scarlet sheen lit paths with joyous red",
    }
    return acts.get(activity.id, "the air seemed alive with hidden cheer")

def setting_detail(setting: Setting, activity: Activity) -> str:
    if setting.indoor:
        return "Sunbeams striped the painted walls, waiting for playful hands."
    if activity.keyword == "glory":
        return "Golden light painted petals on stone and leaf alike."
    return "Blossoms nodded beside the path where laughter could easily echo."

def prize_clean(hero: Entity, prize: Entity) -> str:
    return f"{hero.pronoun('possessive')} {prize.label} stayed unstained and bright"

def _do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    if activity.id not in world.setting.affords:
        return
    world.zone = set(activity.zone)
    actor.meters[activity.mess] += 1
    actor.memes["joy"] += 1
    propagate(world, narrate=narrate)

def introduce_child(world: World, hero: Entity) -> None:
    trait = next((t for t in hero.traits if t != "little"), "")
    hero.memes["love_bubbles"] += 1.2
    world.say(
        f"In {world.setting.place}, {hero.id} skipped in glee.\n"
        f"A {trait} {hero.type} who found the world too slowly.\n"
        f"Wherever sparkles dared to show, there {hero.id} would eagerly go."
    )

def loves_scarlet_bubbles(world: World, hero: Entity, activity: Activity) -> None:
    world.say(
        f"Each morning {hero.id} would beg the sky\n"
        f"For one more glimpse of glory high.\n"
        f"Of red as deep as sunset’s flame\n"
        f"To chase in playful games that whispered the child’s name.\n"
        f"{hero.pronoun().capitalize()} loved blowing bubbles that shimmered {activity.keyword}."
    )

def introduces_apron(world: World, parent: Entity, hero: Entity, prize: Prize) -> None:
    world.say(
        f"That week inside a shop so bright\n"
        f"{parent.label_word} spied the perfect sight:\n"
        f"A {prize.type} with pockets wide,\n"
        f"To keep the child both clean and spry."
    )

def loves_prize(world: World, hero: Entity, prize: Entity) -> None:
    prize.worn_by = hero.id
    world.say(
        f"{hero.id} hugged the cloth so tight.\n"
        f"{hero.pronoun().capitalize()} twirled to show the cloth’s delight.\n"
        f"Now every bubble’s kiss could land\n"
        f"Without a mark upon {hero.pronoun('possessive')} hand."
    )

def arrive_outdoors(world: World, hero: Entity, parent: Entity) -> None:
    hero.memes["desire"] += 0.8
    world.say(
        f"One golden noon with laughter broad,\n"
        f"{hero.id} and {parent.label_word} stepped on the road.\n"
        f"Toward the garden, scarlet bright,\n"
        f"Where wonder hid in afternoon’s soft light."
    )
    world.weather = world.setting.weather
    world.say(setting_detail(world.setting, ACTIVITIES["scarlet_bubbles"]))

def wants_to_play(world: World, hero: Entity, parent: Entity, activity: Activity) -> None:
    world.say(
        f"{hero.id} pointed to the pot so red,\n"
        f"‘{hero.pronoun().capitalize()} will stir and blow,’ the child said.\n"
        f"Yet {hero.pronoun('possessive')} {parent.label_word} just shook {hero.pronoun('possessive')} head."
    )

def warn_stain(world: World, parent: Entity, hero: Entity, activity: Activity, prize_id: str) -> bool:
    pred = predict_mess(world, hero, activity, prize_id)
    if not pred["soiled"]:
        return False
    lit = {"scarlet": "scarlet", "foamy": "foamy pink"}[activity.keyword]
    worry = f"Your pretty {lit} apron will bear a mark"
    if pred["workload"] >= THRESHOLD:
        worry += f", then I’ll chase the stain right after dark"
    world.facts["predicted_soil"] = activity.soil
    world.facts["predicted_workload"] = pred["workload"]
    world.say(
        f'"{worry}," {parent.pronoun("possessive")} {parent.label_word} declared with care.\n'
        f'"We’ll think first, then we’ll play—beware!"'
    )
    return True

def predict_mess(world: World, actor: Entity, activity: Activity, prize_id: str) -> dict:
    sim = world.copy()
    _do_activity(sim, sim.get(actor.id), activity, narrate=False)
    prize = sim.entities.get(prize_id)
    return {
        "soiled": bool(prize and prize.meters["dirty"] >= THRESHOLD),
        "workload": sum(e.meters["workload"] for e in sim.characters()),
    }

def defies(parent: Entity, hero: Entity, activity: Activity) -> None:
    hero.memes["defiance"] += 1.3
    world.say(
        f'{hero.id} tossed {hero.pronoun("possessive")} curls and pouted wide.\n'
        f"‘The magic’s mine!’ {hero.pronoun()} cried.\n"
        f"{hero.pronoun().capitalize()} bolted quick to grab the pot\nof swirling scarlet glory—what a plot!"
    )

def grab_hand_softly(parent: Entity, hero: Entity) -> None:
    hero.memes["grabbed_by"] += 1
    propagate(None, narrate=False)  # avoids world; we'll narrate manually below
    world.say(
        f"{parent.label_word} reached and gently caught {hero.pronoun('possessive')} fling.\n"
        f'"Bubble-magic calls so loud,’ {parent.pronoun('subject')} softly sing.\n'
        f'"Yet wonder waits when hands are slow,\nand safety shields what scarlet bestows."'
    )

def pout_conflict(hero: Entity) -> None:
    if hero.memes["conflict"] >= THRESHOLD:
        world.say(
            f'{hero.id} stamped a foot so small and red.\n'
            f'{hero.pronoun().capitalize()} crossed arms in tempered thread.\n'
            f"‘No fair! The magic shines—it’s mine!\nI want the glory bright as wine!’"
        )

def compromise_gloves_cloth(world: World, parent: Entity, hero: Entity,
                          activity: Activity, prize_id: str) -> Optional[Gear]:
    gear_def = select_gear(activity, PRIZES[prize_id])
    if gear_def is None:
        return None

    gloves = world.add(Entity(
        id=gear_def.id,
        type="gear",
        label=gear_def.label,
        owner=hero.id,
        caretaker=parent.id,
        protective=True,
        covers=set(gear_def.covers),
        plural=gear_def.plural,
    ))
    gloves.worn_by = hero.id

    if predict_mess(world, hero, activity, prize_id)["soiled"]:
        gloves.worn_by = None
        del world.entities[gloves.id]
        return None

    world.say(
        f'"How about we {gear_def.prep},\n'
        f"and blow red clouds without a skip?\n"
        f'Then {activity.gerund} will fill the air\n'
        f"with glory bright beyond compare."'
    )
    return gear_def

def select_gear(activity: Activity, prize: Prize) -> Optional[Gear]:
    if activity.mess not in {"foamy", "stained"}:
        return None
    for gear in GEAR:
        if activity.mess in gear.guards and prize.region in gear.covers:
            return gear
    return None

def resolve_inner_conflict(world: World, parent: Entity, hero: Entity) -> None:
    hero.memes["joy"] += 1.5
    hero.memes["love"] += 1.2
    hero.memes["conflict"] = 0.0
    world.say(
        f"{hero.id} peeked up with eyes just clear.\n"
        f"‘Bubble glory stays—no need for fear!\n"
        f"With {parent.pronoun('possessive')} help, the red clouds rise,\n"
        f"and apron kisses bubbles—pure surprise!’\n"
        f"{hero.pronoun().capitalize()} clapped in joyful, tinkling sound,\n"
        f"no trace of temper left to be found."
    )

def blissful_play(world: World, hero: Entity, activity: Activity, gear_def: Gear) -> None:
    world.say(
        f"They sought the garden, now serene and gold.\n"
        f"{hero.id} in gloves held scarlet light to behold.\n"
        f"{hero.pronoun().capitalize()} blew until the air was sweet\n"
        f"with red-edged spheres that spun on heat.\n"
        f"{prize_clean(hero, world.get('prize'))}, soft and neat,\n"
        f"while laughter rang to each vibrant beat."
    )

def tell(setting: Setting, activity: Activity, prize_cfg: Prize,
         hero_name: str = "Lily", hero_type: str = "girl",
         hero_traits: Optional[list[str]] = None, parent_type: str = "mother") -> World:
    world = World(setting)
    world.weather = setting.weather if not setting.indoor else ""

    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type=hero_type,
        traits=["little"] + (hero_traits or ["joyous", "impatient"]),
    ))
    parent = world.add(Entity(
        id="Parent",
        kind="character",
        type=parent_type,
        label="the kind parent",
    ))
    prize = world.add(Entity(
        id="prize",
        type=prize_cfg.type,
        label=prize_cfg.label,
        phrase=prize_cfg.phrase,
        owner=hero.id,
        caretaker=parent.id,
        region=prize_cfg.region,
    ))

    introduce_child(world, hero)
    world.para()
    loves_scarlet_bubbles(world, hero, activity)
    world.say(setting_detail(setting, activity))
    world.para()
    introduces_apron(world, parent, hero, prize_cfg)
    loves_prize(world, hero, prize)
    world.para()
    arrive_outdoors(world, hero, parent)
    world.para()
    wants_to_play(world, hero, parent, activity)

    if warn_stain(world, parent, hero, activity, prize.id):
        world.para()
        defies(parent, hero, activity)
        grab_hand_softly(parent, hero)
        world.para()
        pout_conflict(hero)

    world.para()
    gear_def = compromise_gloves_cloth(world, parent, hero, activity, prize.id)
    if gear_def:
        resolve_inner_conflict(world, parent, hero)
        world.para()
        blissful_play(world, hero, activity, gear_def)

    world.facts.update(
        hero=hero,
        parent=parent,
        prize=prize,
        prize_cfg=prize_cfg,
        activity=activity,
        setting=setting,
        gear=gear_def is not None,
        conflict=hero.memes.get("conflict", 0) >= THRESHOLD,
        resolved=gear_def is not None
    )
    return world

SETTINGS = {
    "garden": Setting(place="the sunlit garden", indoor=False, affords={"scarlet_bubbles"}),
    "backyard": Setting(place="the quiet backyard", indoor=False, affords={"scarlet_bubbles"}),
}

ACTIVITIES = {
    "scarlet_bubbles": Activity(
        id="scarlet_bubbles",
        verb="blow scarlet bubbles",
        gerund="blowing scarlet bubbles",
        rush="race to grab the pot of scarlet bubbles",
        mess="foamy",
        soil="stained pink",
        zone={"hands", "clothes"},
        weather="sunny",
        keyword="glory scarlet babble",
        tags={"glory", "scarlet", "babble", "bubbles"},
    ),
}

PRIZES = {
    "apron": Prize(
        label="apron",
        phrase="a little embroidered apron",
        type="apron",
        region="clothes",
        genders={"girl", "boy"},
    ),
}

GEAR = [
    Gear(
        id="gloves",
        label="bubble-proof gloves",
        covers={"hands"},
        guards={"foamy", "stained"},
        prep="pop on bubble-proof gloves",
        tail="returned to play with clean delight",
    ),
    Gear(
        id="coverall",
        label="sturdy coverall",
        covers={"hands", "clothes"},
        guards={"foamy", "stained"},
        prep="zip into a sturdy coverall",
        tail="went to fetch the zippered suit",
    ),
]

GIRL_NAMES = ["Lily", "Scarlet", "Rose", "Daisy", "Glory", "Violet", "Poppy", "Joy"]
BOY_NAMES = ["Leo", "Bliss", "Rudy", "Robin", "Scar", "Babble", "Glee", "Bright"]
TRAITS = ["joyous", "impatient", "playful", "dreamy", "eager", "sprightly", "fidgety"]

def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        if "scarlet_bubbles" in setting.affords:
            activity = ACTIVITIES["scarlet_bubbles"]
            for prize_id, prize in PRIZES.items():
                if select_gear(activity, prize):
                    combos.append((place, activity.id, prize_id))
    return combos

KNOWLEDGE = {
    "glory": [("What does glory mean?",
               "Glory means a beautiful or radiant splendor; in this tale, it’s the shimmering "
               "scarlet light seen when scarlet bubbles catch the sun.")],
    "scarlet": [("What color is scarlet?",
                 "Scarlet is a vivid red color, like the robes worn by nobles in old stories "
                 "and the bright poppies in a summer field.")],
    "babble": [("Why do children babble?",
                "Babble is the talk of little children when their words aren’t clear yet; "
                "here it also sounds like the happy sounds bubbles make when they pop.")],
    "bubble": [("What makes bubbles shimmer?",
                "Bubbles catch light to make rainbows on their surface; the scarlet ones here "
                "reflect a deep red from special liquid.")],
    "apron": [("Why wear an apron?",
               "An apron protects clothes from spills and stains while cooking or playing with "
               "messy things like paint or bubble liquid.")],
    "gloves": [("What are bubble-proof gloves for?",
                "Bubble-proof gloves keep hands clean and dry so soapy water or colored liquid "
                "cannot stain your skin.")],
}

KNOWLEDGE_ORDER = ["glory", "scarlet", "babble", "bubble", "apron", "gloves"]

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, parent, act = f["hero"], f["parent"], f["activity"]
    kw = act.keyword.replace(" ", " ")
    return [
        f'Write a short rhyming tale (3–7 couplets) for toddlers on “trying first, then playing” '
        f'that uses both “{kw.split()[0]}” and “{kw.split()[1]}.”',
        f"Tell a gentle rhyming story where a {hero.type} named {hero.id} chases a shimmering "
        f"scarlet joy only to learn patience with {parent.label_word}'s calm advice, "
        f"ending with clean laughter.",
        f'Create a simple rhymed poem about "babble" that shows a child turning frowns into '
        f'giggles through a small compromise.',
    ]

def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, parent = f["hero"], f["parent"]
    act = f["activity"]
    pos = hero.pronoun("possessive")
    subj = hero.pronoun("subject")
    pw = parent.label_word
    where = "inside" if world.setting.indoor else "in the garden"

    qa: list[QAItem] = [
        QAItem(
            question=f"What little {hero.traits[1]} {hero.type} chased red bubble light?",
            answer=f"It was {hero.id}, a {hero.traits[0]} {hero.type} who loved "
                   f"{act.gerund} {where}. The child wanted every scarlet gleam.",
        ),
        QAItem(
            question=f"What new item did {hero.id}'s {pw} buy for an outing?",
            answer=f"{pw.capitalize()} bought {pos} a little embroidered apron "
                   f"so {hero.pronoun()} could play without leaving stains behind.",
        ),
    ]

    if f.get("conflict"):
        qa.append(QAItem(
            question=(f"Why did {hero.id}'s {pw} hesitate to let the child {act.verb}?"),
            answer=(
                f"Because if {hero.id} played right then, {hero.pronoun('possessive')} "
                f"apron would end up {f.get('predicted_soil', 'scarlet-stained')}, "
                f"and {pw} would have to tidy up just after dark."
            ),
        ))

    if f.get("resolved"):
        qa.append(QAItem(
            question="How did the gloves help the child chase scarlet bubbles happily?",
            answer=(
                f"By wearing bubble-proof gloves, {hero.id} could {act.gerund} without "
                f"getting {pos} hands or {pos} clothes stained, so the apron stayed clean "
                f"and {subj} giggled at the red clouds filling the air."
            ),
        ))
        qa.append(QAItem(
            question="How did the child feel once {pw} agreed to the glove plan?",
            answer=(
                f"{hero.id} felt joy lift both spirits free. The earlier temper melted "
                f"like bubbles on the breeze, and with {pw} beside, {hero.pronoun()} "
                f"blew red sparkles without fear."
            ),
        ))
    return qa

def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    tags = f["activity"].tags
    out: list[QAItem] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags or tag in {"bubble"}:
            out.extend(QAItem(q, a) for q, a in KNOWLEDGE.get(tag, []))
    return out

def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Tiny asks that would create this rhyme =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions — what the text rhymes about ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) Child-level world knowledge — independent of the tale ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)

def dump_trace(world: World) -> str:
    lines = ["--- inner world state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.protective:
            bits.append(f"shields={sorted(e.covers)}")
        elif e.region:
            bits.append(f"worn_at={e.region}")
        lines.append(f"  {e.id:9} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired: {sorted({n for n,*_ in world.fired})}")
    return "\n".join(lines)

CURATED = [
    StoryParams(place="garden", activity="scarlet_bubbles", prize="apron",
                name="Glory", gender="girl", parent="mother", trait="joyous"),
    StoryParams(place="backyard", activity="scarlet_bubbles", prize="apron",
                name="Babble", gender="boy", parent="father", trait="eager"),
]

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

ASP_RULES = r"""
prize_at_risk(A, P) :- splashes(A, R), worn_on(P, R).
protects(G, A, P) :- gear(G), prize_at_risk(A, P),
                     mess_of(A, M), guards(G, M),
                     covers(G, R), worn_on(P, R).
has_fix(A, P) :- protects(_, A, P).
valid(Place, A, P) :- affords(Place, A), prize_at_risk(A, P), has_fix(A, P).
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

def asp_program(show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"

def asp_verify() -> int:
    try:
        import asp
        clingo_set = set(asp.atoms(asp.one_model(asp_program("#show valid/3.")), "valid"))
        python_set = set(valid_combos())
        if clingo_set != python_set:
            print("MISMATCH between ASP gate and Python combos!")
            return 1
        print(f"OK: {len(clingo_set)} valid combos match.")
        return 0
    except Exception as e:
        print(f"ASP verification failed: {e}")
        return 1

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Toddler rhyming world: glory, scarlet, babble, and clean compromise.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices={"scarlet_bubbles"})
    ap.add_argument("--prize", choices={"apron"})
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

def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.activity and args.prize:
        act = ACTIVITIES[args.activity]
        pr = PRIZES[args.prize]
        if not select_gear(act, pr):
            raise StoryError(
                f"No gear protects {pr.label} from {act.gerund}. "
                "Add gloves or a coverall first."
            )
    if args.gender and args.prize:
        if args.gender not in PRIZES[args.prize].genders:
            raise StoryError(
                f"A {PRIZES[args.prize].label} isn't typical for {args.gender}s "
                "here; try boy or girl."
            )

    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.activity is None or c[1] == args.activity)
              and (args.prize is None or c[2] == args.prize)
              and (args.gender is None or args.gender in PRIZES[c[2]].genders)]
    if not combos:
        raise StoryError("No valid combination matches the given options.")

    place, activity, prize_id = rng.choice(sorted(combos))
    prize = PRIZES[prize_id]
    gender = args.gender or rng.choice(sorted(prize.genders))
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(
        place=place,
        activity=activity,
        prize=prize_id,
        name=name,
        gender=gender,
        parent=parent,
        trait=trait,
    )

def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.place],
        ACTIVITIES[params.activity],
        PRIZES[params.prize],
        params.name,
        params.gender,
        [params.trait],
        params.parent,
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
        print("\n" + dump_trace(sample.world))
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
        try:
            import asp
            models = asp.solve(asp_program("#show valid/3."), models=1)
            print(f"{len(models)} compatible triples found.")
        except Exception as e:
            print(f"Could not run ASP: {e}")
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
            header = f"### {p.name}: red bubbles & clean apron"
        elif len(samples) > 1:
            header = f"### rhyme {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")

if __name__ == "__main__":
    main()
