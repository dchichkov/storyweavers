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

# Make the shared result containers importable when this script is run directly
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from storyworlds.results import QAItem, StoryError, StorySample

# Threshold at which an accumulated effect is "embedded enough" to be narrated.
THRESHOLD = 1.0

# Physical meter keys for magical interactions.
MAGIC_KEYS = {"magic_charge", "stability", "glow", "humidity"}

# Emotional meme keys tied to wonder and responsibility.
MEME_KEYS = {"wonder", "awe", "caution", "impulse"}

# Body regions for magical item wear/protection (metaphorical here).
REGIONS = {"back", "hands", "head"}

# ---------------------------------------------------------------------------
# Entities: characters and magical objects share one representation.
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
        female = {"witch", "queen", "goddess"}
        male = {"giant", "knight", "hermit"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

    @property
    def label_word(self) -> str:
        return {"witch": "wise woman", "giant": "tall friend", "queen": "sovereign"}.get(self.type, self.type)

# ---------------------------------------------------------------------------
# Parametrization knobs -- the swappable vocabulary of this magical domain.
# ---------------------------------------------------------------------------
@dataclass
class Setting:
    place: str = "the Enchanted Meadow"
    indoor: bool = False
    affords: set[str] = field(default_factory=set)

@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    magical_effect: str
    magical_cost: str
    zone: set[str]
    keyword: str = ""
    tags: set[str] = field(default_factory=set)

@dataclass
class Prize:
    label: str
    phrase: str
    type: str
    region: str
    plural: bool = False
    genders: set[str] = field(default_factory=lambda: {"girl", "boy", "child"})
    magical_cores: dict[str, str] = field(default_factory=dict)

# ---------------------------------------------------------------------------
# World: entity store + narration history.
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
        return self.entities.get(eid)

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

# ---------------------------------------------------------------------------
# Causal rules: forward-chained to fixpoint via magical physics.
# ---------------------------------------------------------------------------
@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]

def _r_stability_drop(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.memes["impulse"] < THRESHOLD:
            continue
        for item in world.entities.values():
            if item.plural or "magic" not in item.label:
                continue
            if world.covered(actor, "hands") or world.covered(actor, "head"):
                continue
            if ("bale" in item.label or "straw" in item.label) and item.meters["stability"] >= 0.7:
                continue
            sig = ("stability", item.id, actor.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            drop = 0.3 + actor.memes["impulse"] * 0.1
            item.meters["stability"] -= drop
            item.meters["magic_charge"] *= 0.8
            out.append(
                f"{actor.pronoun('subject').capitalize()} clumsy fingers jostled "
                f"{actor.pronoun('possessive')} bundle, sending {item.label} wobbling! "
                f"The enchanted straw trembled and its magic flickered."
            )
    return out

def _r_awe_response(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        charge = actor.meters.get("magic_charge", 0)
        if charge < THRESHOLD or actor.memes["wonder"] < THRESHOLD:
            continue
        sig = ("awe", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["awe"] += charge * 0.5
        factor = 1.0 + (charge - THRESHOLD) * 0.3
        actor.meters["glow"] = min(5.0, actor.meters.get("glow", 1.0) * factor)
        out.append(
            f"{actor.id}'s breath caught as the golden light from "
            f"{actor.pronoun('possessive')} enchanted straw blazed above the skyline."
        )
    return out

def _r_caution_change(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.memes.get("caution", 0) < THRESHOLD and actor.memes.get("impulse", 0) >= THRESHOLD:
            sig = ("tension", actor.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            actor.memes["caution"] += 0.8
            out.append(
                f"{actor.pronoun('subject').capitalize()} heard the old tales warning: "
                f"Misusing magic straw could summon the Stormborn and ruin all one holds dear."
            )
    return out

CAUSAL_RULES: list[Rule] = [
    Rule(name="stability", tag="physical", apply=_r_stability_drop),
    Rule(name="awe", tag="emotional", apply=_r_awe_response),
    Rule(name="caution", tag="social", apply=_r_caution_change),
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

# ---------------------------------------------------------------------------
# Constraint: the magical straw must stay whole for the tall tale promise to hold.
# ---------------------------------------------------------------------------
def story_viable(activity: Activity, prize: Prize) -> bool:
    return "bale" in prize.magical_cores or activity.magical_effect == "harvest_golden_straw"

def select_gear(activity: Activity, prize: Prize) -> Optional[GearDef]:
    if "stable_hands" in ACTIVITIES[activity.id].tags:
        return next((g for g in GEAR if "stabilizer" in g.id), None)
    return next((g for g in GEAR if prize.magical_cores.get(g.id)), None)

# ---------------------------------------------------------------------------
# Prediction: run the world forward on a copy to foresee magical misuse.
# ---------------------------------------------------------------------------
def predict_magic_misfire(world: World, actor: Entity, act: Activity, prize_id: str) -> dict:
    sim = world.copy()
    hero = sim.get(actor.id)
    hero.memes["impulse"] += 1.5
    _do_activity(sim, hero, act, narrate=False)
    prize = sim.entities.get(prize_id)
    return {
        "broken": bool(prize and prize.meters.get("stability", 1.0) <= 0.0),
        "storm": sum(e.memes.get("awe", 0) for e in sim.characters()) >= 8.0,
    }

# ---------------------------------------------------------------------------
# Verbs: each mutates magical state and (optionally) narrates tall-tale prose.
# ---------------------------------------------------------------------------
def magical_effect_desc(activity: Activity) -> str:
    return {
        "harvest_golden_straw": "every golden strand hummed like plucked harp strings",
        "bind_enchanted_bale": "the bale’s straw glowed as if spun from midday sunbeams",
        "carry_toward_spring": "the enchanted straw smelled of rain-washed clover and distant fern",
    }.get(activity.id, "the air filled with faint, sunlit chimes")

def setting_detail(setting: Setting, activity: Activity) -> str:
    return {
        "Enchanted Meadow": "Golden buttercups nodded under a sky veined with harmless comet-dust.",
        "Whispering Vale": "The vale itself seemed to lean in, ear-tipped shadows voicing quiet warnings.",
        "Village Well": "Clear water sparkled above veins of quicksilver that sang when touched.",
    }.get(setting.place, "The glade waited, quiet and wondering.")

def prize_condition(prize: Entity) -> str:
    return {
        "magic_bale": "glowing like a captured moonbeam",
        "enchanted_straw": "humming in the gentle breeze",
        "golden_bundle": "shimmering under the child’s breathless gaze",
    }.get(prize.label, f"wearing {prize.it()} like a sacred mantle")

def _do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    if activity.id not in world.setting.affords:
        return
    world.zone = set(activity.zone)
    actor.meters["magic_charge"] += 0.5
    actor.memes["wonder"] += 1.3
    actor.memes["impulse"] += 0.6
    propagate(world, narrate=narrate)

def introduce(world: World, hero: Entity) -> None:
    trait = next((t for t in hero.traits if t != "little"), "")
    desc = f"little {trait} {hero.type}".strip()
    world.say(f"{hero.pronoun().capitalize()} was a {desc} overflowing with questions about the strange straw waiting in the meadow.")

def loves_magic(world: World, hero: Entity, activity: Activity) -> None:
    where = "inside the warm cottage" if world.setting.indoor else "beneath the whispering boughs"
    world.say(
        f"{hero.pronoun().capitalize()} loved exploring {where} and discovering what the "
        f"enchanted straw could do; {magical_effect_desc(activity)}."
    )

def buys_from_cottage(world: World, parent: Entity, hero: Entity, prize: Entity) -> None:
    world.say(
        f"From the cottage’s rafters {hero.id}'s {parent.label_word} lowered "
        f"{hero.pronoun('possessive')} {prize.phrase} down the step-ladder of mist."
    )

def loves_prize(world: World, hero: Entity, prize: Entity) -> None:
    hero.memes["wonder"] += 1.1
    prize.worn_by = hero.id
    world.say(
        f"{hero.id} clutched {prize.it()} and felt its warm hum rising through "
        f"{hero.pronoun('possessive')} fingertips. {hero.pronoun().capitalize()} "
        f"wore {prize.it()} as if the day had been woven just for such wonders."
    )

def arrive(world: World, hero: Entity, parent: Entity, activity: Activity) -> None:
    day = {"moonlit": "When the three moons nestled close low over ", "sunlit": "At the crest of the sun's arch above "}.get(world.weather, "One breathless morning ")
    go = "clambered softly into" if world.setting.indoor else "sauntered happily toward"
    world.say(
        f"{day}{world.setting.place}, {hero.id} and {hero.pronoun('possessive')} "
        f"{parent.label_word} {go} where the bale waited between the elderberry and thorn."
    )
    world.say(setting_detail(world.setting, activity))

def feels_pull(world: World, hero: Entity, activity: Activity) -> None:
    world.say(
        f"{hero.id}’s fingers tingled, urging {hero.pronoun()} to seize the straw "
        f"and {activity.verb} into the bright fields beyond."
    )

def warn_with_tales(world: World, parent: Entity, hero: Entity, activity: Activity, prize: Entity) -> bool:
    act_desc = activity.magical_cost.replace("ruin ", "unravel ").replace("lose ", "scatter ")
    world.facts["predicted_misuse"] = activity.magical_effect
    clause = f"You must not let the magic straw {act_desc}"
    if "storm" in act_desc:
        clause += ", or the Stormborn will wake and undo this vale forever"
    world.say(f'"{clause}," {hero.pronoun("possessive")} {parent.label_word} said softly, eyes dim with memory.')
    return True

def tugs_forward(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["impulse"] += 1.2
    world.say(
        f"Despite the warning, {hero.id} simply had to know "
        f"what would happen if {hero.pronoun()} {activity.rush}."
    )
    world.say(f"{hero.pronoun().capitalize()} lunged suddenly toward the golden bale!")

def grandparent_seizes(world: World, elder: Entity, hero: Entity) -> None:
    hero.memes["caution"] += 1.0
    propagate(world, narrate=False)
    world.para()
    world.say(
        f"In the nick of time, {elder.label_word} stretched out a verdant hand "
        f"and seized {hero.pronoun('possessive')} wrist, stilling the eager reach."
    )
    world.say(
        f'"Whoa, whoa, tiny spark," {elder.pronoun("subject")} rumbled with '
        f'kind laughter. "Magic straw is not a toy — not unless you {{activity.verb}} '
        f'with care and clear intent."'
    )

def pout_and_argue(world: World, hero: Entity, activity: Activity, elder: Entity) -> None:
    world.say(
        f"{hero.id} kicked the clover petals, arms crossed tight. "
        f'"But I need to know if it’s really magic!" {hero.pronoun()} declared.'
    )

def advice_with_offer(world: World, elder: Entity, hero: Entity, activity: Activity) -> Optional[Gear]:
    sole_option = next((g for g in GEAR if "cContext" in g.id or prize.type in g.guards), None)
    if sole_option is None:
        return None
    gear = world.add(Entity(
        id=sole_option.id, type="gear", label=sole_option.label,
        owner=hero.id, caretaker=elder.id, protective=True,
        covers=set(sole_option.covers), plural=sole_option.plural,
    ))
    gear.worn_by = hero.id
    sample = predict_magic_misfire(world, hero, activity, "prize")
    if sample["broken"] or sample["storm"]:
        gear.worn_by = None
        del world.entities[gear.id]
        return None
    advise = sole_option.prep.format(activity=activity.gerund)
    world.say(
        f"{elder.label_word} smiled knowingly and placed "
        f"{gear.label} gently upon {hero.pronoun('possessive')} shoulders. "
        f'"First, we {advise}."'
    )
    return gear

def accept_wisdom(world: World, elder: Entity, hero: Entity, activity: Activity, prize: Entity,
                 gear_def: Gear) -> None:
    hero.memes["wonder"] = min(5.0, hero.memes.get("wonder", 1.0) + 1.2)
    hero.memes["caution"] += 0.7
    world.say(
        f"{hero.id}'s eyes sparkled then softened. {hero.pronoun().capitalize()} "
        f"bowed {hero.pronoun('possessive')} head and {hero.pronoun()} whispered, "
        f'"Thank you for the {{gear_def.tail}}."'
    )
    world.para()
    world.say(
        f"They {{activity.verb}} together at twilight. {{prize_condition(prize)}} "
        f"remained intact under star-forged heavens, and {elder.label_word} "
        f"laughed beside {hero.pronoun('object')} in the shimmering meadow."
    )

# ---------------------------------------------------------------------------
# The screenplay: tall-tale beats driven by magical cause and curiosity.
# ---------------------------------------------------------------------------
def tell(setting: Setting, activity: Activity, prize_cfg: Prize,
         hero_name: str = "Pip", hero_type: str = "child",
         hero_traits: Optional[list[str]] = None, parent_type: str = "grandparent") -> World:
    world = World(setting)
    world.weather = "moonlit" if setting.place == "Whispering Vale" else "sunlit"

    hero = world.add(Entity(
        id=hero_name, kind="character", type=hero_type,
        traits=["little", "curious"] + (hero_traits or ["impetuous", "hopeful"]),
    ))
    elder = world.add(Entity(id="Elder", kind="character", type=parent_type,
                         label="the ancient one", phrase="wise hand"))
    prize = world.add(Entity(
        id="prize", type=prize_cfg.type, label=prize_cfg.label,
        phrase=prize_cfg.phrase, owner=hero.id, caretaker=elder.id,
        region=prize_cfg.region, plural=prize_cfg.plural,
    ))

    # Prologue — who, what stirs wonder, and the magical object arrives.
    world.say(f"Once upon a time, in the days when the sky still whispered to the earth,")
    introduce(world, hero)
    loves_magic(world, hero, activity)
    buys_from_cottage(world, elder, hero, prize)
    loves_prize(world, hero, prize)

    # Conflict — impulse vs. the loom of cautions told by elder.
    world.para()
    arrive(world, hero, elder, activity)
    feels_pull(world, hero, activity)
    warn_with_tales(world, elder, hero, activity, prize)
    tugs_forward(world, hero, activity)
    grandparent_seizes(world, elder, hero)

    world.para()
    pout_and_argue(world, hero, activity, elder)

    # Resolution — elder’s wise compromise reveals the proper magic use.
    world.para()
    gear_def = advice_with_offer(world, elder, hero, activity, prize)
    if gear_def:
        accept_wisdom(world, elder, hero, activity, prize, gear_def)

    # Facts for the Q&A generators.
    world.facts.update(hero=hero, elder=elder, prize=prize, prize_cfg=prize_cfg,
                       activity=activity, setting=setting, gear=gear_def,
                       conflict=hero.memes.get("impulse", 0) > THRESHOLD,
                       resolved=(gear_def is not None and hero.memes.get("wonder", 0) >= 3.0))
    return world

# ---------------------------------------------------------------------------
# Content registries.
# ---------------------------------------------------------------------------
SETTINGS = {
    "meadow": Setting(place="the Enchanted Meadow", indoor=False,
                      affords={"harvest_baubles", "gilded_tether", "bind_enchanted_bale"}),
    "vale": Setting(place="Whispering Vale", indoor=False,
                   affords={"carry_toward_spring", "hum_of_bale", "chant_about_straw"}),
    "cottage": Setting(place="the Crooked Cottage", indoor=True,
                      affords={"weave_with_glow", "bind_by_hand", "store_magic_straw"}),
}

ACTIVITIES = {
    "harvest_golden_straw": Activity(
        id="harvest_golden_straw", verb="harvest the golden straw",
        gerund="harvesting the golden straw", rush="plunge toward the gleaming straw",
        magical_effect="harvest_golden_straw", magical_cost="ruin all coherent magic",
        zone={"hands"}, keyword="glowing straw", tags={"bale", "harvest", "gold"},
    ),
    "bind_enchanted_bale": Activity(
        id="bind_enchanted_bale", verb="bind the enchanted bale",
        gerund="binding the enchanted bale", rush="bolt for the bundle of straw",
        magical_effect="bind_enchanted_bale", magical_cost="ruin the steady hum",
        zone={"hands", "back"}, keyword="bale", tags={"bale", "bind", "hum"},
    ),
    "carry_toward_spring": Activity(
        id="carry_toward_spring", verb="carry the straw to the spring",
        gerund="carrying the golden straw to the spring",
        rush="dash straight for the spring",
        magical_effect="carry_toward_spring", magical_cost="unravel the vale’s veining songs",
        zone={"hands", "head"}, keyword="spring", tags={"spring", "flow", "amenity"},
    ),
    "weave_with_glow": Activity(
        id="weave_with_glow", verb="weave with the glowing strands",
        gerund="weaving glowing strands into a cloak", rush="rip the straw upward",
        magical_effect="reinforce protective patterns", magical_cost="fray the fabric of trust",
        zone={"hands"}, keyword="weave", tags={"cloak", "safe", "amenity"},
    ),
}

GEAR = [
    Gear(
        id="stabilizer_bracers", label="gleaming bracers",
        covers={"hands", "wrists"}, guards={"golden", "harmonic"},
        prep="slide {hero.pronoun('possessive')} hands into the gleaming bracers",
        tail="showed the child how bracers steadied every motion",
    ),
    Gear(
        id="humming_crown", label="humming circlet", region="head",
        covers={"head"}, guards={"steady", "calm"},
        prep="place the humming circlet upon {hero.pronoun('possessive')} brow",
        tail="demonstrated how the circlet muffled sudden impulses",
    ),
    Gear(
        id="mantle_shawl", label="silvered shawl",
        covers={"back", "shoulders"}, guards={"harmonic", "flow"},
        prep="wrap {hero.pronoun('possessive')} shoulders in the silvered shawl",
        tail="pulled the silvered shawl close and chanted soft syllables",
    ),
]

PRIZES = {
    "magic_bale": Prize(
        label="magic bale",
        phrase="glowing bale of enchanted straw",
        type="bale", region="back", plural=True,
        magical_cores={"stabilizer_bracers": "strengthens", "humming_crown": "focuses"},
    ),
    "enchanted_straw": Prize(
        label="enchanted straw",
        phrase="single gleaming strand",
        type="strand", region="hands", plural=False,
        magical_cores={"humming_crown": "focusses", "mantle_shawl": "protects"},
    ),
    "golden_bundle": Prize(
        label="golden bundle",
        phrase="bundle of golden straw",
        type="bundle", region="back", plural=True,
        magical_cores={"stabilizer_bracers": "reinforces", "mantle_shawl": "anchors"},
    ),
}

GIRL_NAMES = ["Lumi", "Elspeth", "Tessa", "Sylvie", "Briar", "Thistle"]
BOY_NAMES = ["Pip", "Reed", "Juniper", "Ash", "Rowan", "Clover"]
TRAITS = ["wondering", "impetuous", "dreamy", "quiet", "laughing"]

def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            act = ACTIVITIES[act_id]
            for prize_id, prize in PRIZES.items():
                if story_viable(act, prize):
                    combos.append((place, act_id, prize_id))
    return sorted(set(combos))

# ---------------------------------------------------------------------------
# Per-world parameters.
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
# Q&A generation — tall-tale flavored.
# ---------------------------------------------------------------------------
KNOWLEDGE = {
    "bale": [("What is a bale of enchanted straw?",
              "A bale of enchanted straw is a bundle of golden filaments that hum "
              "like tiny harps and can weave wonders when handled with care.")],
    "amenity": [("What is an amenity in magic stories?",
                 "An amenity is something that helps or protects the magic user — "
                 "like gloves that steady the hands or a circlet that guides the thoughts.")],
    "hum": [("Why can enchanted straw hum?",
             "Every stroke of wind through enchanted straw sets its fibres vibrating "
             "like harp strings, turning motion into melody and memory.")],
    "spring": [("Why does straw matter by a spring?",
                 "A spring’s water echoes the straw’s song; together they can mend "
                 "sundered veils between this vale and the realm of dreams.")],
    "circlet": [("What does a humming circlet do?",
                  "A humming circlet listens to a child’s impulses and softens them "
                  "so magic leaps bloom rather than bolts wild.")],
    "bracers": [("What are the gleaming bracers for?",
                  "The gleaming bracers steady the fingers so every motion stays purposeful "
                  "and the enchanted straw spells what it wishes instead of what it feels.")],
    "shimmer": [("Why does the meadow shimmer at twilight?",
                  "Twilight catches the meadow’s crown of barley-magic still hazed "
                  "with moon-dust droplets left by sun-chasing dewdrops.")],
}

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    kw = f["activity"].keyword or "magic"
    return [
        f"Write a tall tale for children about a '{kw}' that sings and a child "
        f"who must learn its proper use before magic turns mischief.",
        f"Tell a wildly exaggerated yet child-facing story where a {hero.type} named {hero.id} "
        f"finds a glowing straw and nearly lets loose the Stormborn by mistake.",
        f'Compose a magical anecdote using the words "bale" and "amenity" '
        f"that ends with the sky once again quiet and kind."
    ]

def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, elder = f["hero"], f["elder"]
    act, prize = f["activity"], f["prize"]
    sub, obj, pos = hero.pronoun("subject"), hero.pronoun("object"), hero.pronoun("possessive")
    trait = next((t for t in hero.traits if t != "little"), hero.type)
    where = "inside the Crooked Cottage" if world.setting.indoor else "outside in the Enchanted Meadow"
    qa: list[QAItem] = [
        QAItem(
            question=(
                f"Who discovers the enchanted bale on a starry evening at {world.setting.place}, "
                f"and which elder tries to teach the proper handling of magic straw?"
            ),
            answer=(
                f"It is a little {trait} {hero.type} named {hero.id}, "
                f"and {elder.label_word} is the elder who teaches safe handling of "
                f"{pos} {prize.phrase}. Together they venture {where} beneath the shimmering sky."
            ),
        ),
        QAItem(
            question=(
                f"Why did {trait} {hero.id} want to {act.verb} despite all warnings, "
                f"and what did the elder use to calm the eager impulse?"
            ),
            answer=(
                f"Because {pos} wonder that {hero.id} felt was stronger than {pos} caution. "
                f"The elder used {f['gear'].label if f.get('gear') else 'wise words'} "
                f"to steady {hero.pronoun('possessive')} hands and guide {obj} thoughts."
            ),
        ),
        QAItem(
            question=(
                f"What did the magic bale do after {hero.id} learned to handle it properly, "
                f"and how did the vale itself respond?"
            ),
            answer=(
                f"After learning, {act.gerund} together, the golden bundle continued glowing "
                f"and humming; the vale’s barley-magic shimmered brighter and the "
                f"whispering winds sang harmonies of protection."
            ),
        ),
    ]
    if f.get("conflict"):
        qa.append(QAItem(
            question=(
                f"What happened when {trait} {hero.id} tried to {act.rush.replace(',', '')} "
                f"and why did the elder intervene immediately?"
            ),
            answer=(
                f"{hero.id} lunged toward {pos} {prize.label} so quickly that "
                f"air crackled like summer lightning. The elder’s verdant hand seized {obj} "
                f"wrist to still the dangerous reach — lest {act.magical_cost} come true."
            ),
        ))
    if f.get("resolved") and f.get("gear"):
        qa.append(QAItem(
            question=(
                f"How did the {f['gear'].label.lstrip('a ')} help {hero.id} "
                f"perform {act.keyword or act.magical_effect} without wrecking the vale’s magic?"
            ),
            answer=(
                f"The {f['gear'].label} steadied {hero.pronoun('possessive')} hands and "
                f"muted {hero.pronoun('possessive')} rash impulses, letting {hero.id} "
                f"practice {act.gerund} safely while the meadow’s magic stayed whole."
            ),
        ))
    return qa

def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    tags = set(f["activity"].tags)
    if f.get("gear"):
        tags.add(f["gear"].id)
    out: list[QAItem] = []
    for tag in ["bale", "amenity", "hum", "spring", "circlet", "bracers", "shimmer"]:
        if tag in tags:
            out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE[tag])
    return out

def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts for this tall tale =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Questions grounded in this story’s magic ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) Child-facing magical facts ===")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)

# ---------------------------------------------------------------------------
# CLI / trace for tall-tale diagnostics.
# ---------------------------------------------------------------------------
def dump_trace(world: World) -> str:
    lines = ["---- magical world model -----"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"magical={dict(meters)}")
        if memes:
            bits.append(f"feelings={dict(memes)}")
        if e.protective:
            bits.append(f"wards={sorted(e.covers)}")
        elif e.region:
            bits.append(f"region={e.region}")
        lines.append(f"  {e.id:8} | {e.type:9} | {' '.join(bits)}")
    lines.append(f"  recorded rules fired: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)

# Curated tall tales for --all.
CURATED = [
    StoryParams(
        place="meadow", activity="bind_enchanted_bale", prize="magic_bale",
        name="Lumi", gender="girl", trait="wondering",
    ),
    StoryParams(
        place="vale", activity="carry_toward_spring", prize="enchanted_straw",
        name="Pip", gender="boy", trait="impetuous",
    ),
    StoryParams(
        place="cottage", activity="weave_with_glow", prize="golden_bundle",
        name="Tessa", gender="girl", trait="dreamy",
    ),
]

def explain_rejection(activity: Activity, prize: Prize) -> str:
    noun = "a" if prize.plural else "an"
    where = "on the back" if "back" in prize.region else "in the hands"
    if "bale" not in str(activity.tags) and "bale" not in prize.magical_cores:
        return f"(No tally: {activity.id} does not touch any bale; pick a bale adventure.)"
    return f"(No tall tale: nothing guards {noun} {prize.label} {where} from {activity.gerund}.)"

# ---------------------------------------------------------------------------
# ASP twin: enforce the magical tall-tale reasonableness gate in logic.
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A prize is magical if it contains at least one core compatible with the zone.
magical(P, R) :- prize(P), worn_on(P, R), magical_cores(P, C), guards(C, _).

% Activity is bale-oriented when it has the bale tag or relates to a prize’s core.
bale_activity(A) :- activity(A), tag(A, bale).
bale_activity(A) :- activity(A), wears_magic(P, _), activity(A), prize(P).

% A story is valid when the activity is bale-oriented, the prize magical, and
% there exists gear that both stabilizes the zone and guards the magical core.
valid(Place, Activity, Prize) :-
    setting(Place), affords(Place, Activity), prize(Prize),
    bale_activity(Activity), magical(Prize, Zone),
    magical_cores(Prize, CoreId), gear(Gear), guards(Gear, _),
    covers(Gear, Zone), worn_on(Prize, Zone),
    not (predicted_mess(Activity, Prize)).
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
        for t in sorted(a.tags):
            lines.append(asp.fact("tag", aid, t))
    for pid, pr in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("worn_on", pid, pr.region))
        if pr.plural:
            lines.append(asp.fact("prize_plural", pid))
        for g, desc in pr.magical_cores.items():
            lines.append(asp.fact("magical_cores", pid, g))
    for g in GEAR:
        lines.append(asp.fact("gear", g.id))
        for m in sorted(g.guards):
            lines.append(asp.fact("guards", g.id, m))
        for r in sorted(g.covers):
            lines.append(asp.fact("covers", g.id, r))
    return "\n".join(lines)

def asp_program(show: str) -> str:
    from asp import earth
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"

def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))

def asp_verify() -> int:
    clingo_set, python_set = set(asp_valid_combos()), set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: ASP gate matches tall-tale constraints ({len(clingo_set)} combos).")
        return 0
    print("TALL-TALE GATE MISMATCH:")
    if clingo_set - python_set:
        for triple in sorted(clingo_set - python_set):
            print("  only ASP:", triple)
    if python_set - clingo_set:
        for triple in sorted(python_set - clingo_set):
            print("  only Python:", triple)
    return 1

# ---------------------------------------------------------------------------
# Standard storyworld interface.
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Tall-Tale Magical Domain: bale of straw, the right amenity, "
                    "and learning proper magic handling. Unspecified options are randomized.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("-n", type=int, default=1, help="how many magic tales to spin")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--all", action="store_true", help="print curated bards’ tales instead")
    ap.add_argument("--trace", action="store_true", help="dump the magical state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list ASP-valid tall tales")
    ap.add_argument("--verify", action="store_true", help="check ASP twin against Python")
    ap.add_argument("--show-asp", action="store_true", help="print the ASP program")
    return ap

def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.activity and args.prize:
        act, pr = ACTIVITIES[args.activity], PRIZES[args.prize]
        if not story_viable(act, pr):
            raise StoryError(explain_rejection(act, pr))
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.activity is None or c[1] == args.activity)
              and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError("(No tall-tale scenario matches given choices.)")
    place, activity, prize_id = rng.choice(sorted(combos))
    prize = PRIZES[prize_id]
    name = args.name or rng.choice(GIRL_NAMES + BOY_NAMES)
    gender = args.gender or rng.choice(["girl", "boy"])
    trait = rng.choice(TRAITS)
    return StoryParams(
        place=place, activity=activity, prize=prize_id, name=name, gender=gender, trait=trait,
    )

def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], ACTIVITIES[params.activity],
                 PRIZES[params.prize], params.name, params.gender,
                 [params.trait, "impetuous"], "grandparent")
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
        print(format_qa(sample))

def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        import asp, sys
        sys.exit(asp_verify())
    if args.asp:
        combo_count = len(asp.valid_combos())
        print(f"{combo_count} ASP-approved Tall-Tale settings:\n")
        for place, act, prize in sorted(asp.valid_combos()):
            print(f"  {place:12} | {act:22} | {prize}")
        return
    seed_base = args.seed if args.seed is not None else random.randrange(1 << 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            seed = seed_base + i
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
    for idx, sample in enumerate(samples):
        hdr = ""
        if args.all:
            p = sample.params
            hdr = f"### The Magic Bale of {p.name}: {p.activity} at {p.place}"
        elif len(samples) > 1:
            hdr = f"### Tall Tale Variant {idx+1}"
        emit(sample, trace=args.trace, qa=args.qa, header=hdr)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")

if __name__ == "__main__":
    main()
