#!/usr/bin/env python3
"""
storyworlds/worlds/naughty_pile_inner_monologue_sound_effects_sharing.py
====================================================================

A standalone *story world* sketch for tall-tale mischief built around "naughty" and "pile".

Style: exaggerated Tall Tale with inner monologue *thought bubbles*, sound effects
(*CRASH! THUD! PLINK!*), and themes of sharing vs. naughty pile behavior.
Example Seed (mini-tall tale):
---
Once upon a time—did I mention I’m only FIVE FEET TALL?—there was a backyard so big
*SLURP-SLURP* the grass swallowed shoes whole.  That’s where the biggest pile of leaves
ever made by a pack of tiny humans was growing taller than the swings!

Little Milo, a boy with stretchy fingers and a heart full of *BOING!* ideas,
noticed it first.  “A LEAF MOUNTAIN!”, he shouted, already up one knee.
The pile’s peak was shuffling like a mischief volcano.  And volcanoes, as we all
know, *GROOOWL* when they’re about to choose dire fun.

Milo *did the naughty* before anyone could say “tidy”: he grabbed a rake and
*WHACK-WHACK-WHACK!* sent leaf-stars flying across the sky.  **SPLATTER!**
on Mom’s clean sheets dripping from the clothesline like technicolor rain.

Inside, big sister Lina heard the *CLANG!* of the rake against the fence
and felt her stomach flip-flop like a pancake on Sunday morning:
*“Ohhh no—Milo’s naughty again.  If Dad finds out, he’ll GROWL like a bear
with heartburn and Mom will SCOWL so hard you could iron a shirt on her frown.”*

Lina tiptoed outside clutching the emergency-sharing basket (three old yogurt
cups and a measuring cup full of *PING!* acorn caps).  “Share the leaf mountain!”
she called.  Milo froze.  His *SPINNY-BRAINY* monologue screamed:
*“Uhoh. Sharing means NO LAUGHTER-TRAIN.  NO KA-BOOM jumps.  NO making
mommy-mad mudpies later when she thinks we’re tucked in.  But if I say DON’T
WORRY I’m shaking like a bowl of jelly locked in the fridge.”*

Then the entire pile chose that exact millisecond to THUD like a thousand
drumsticks hit the ground.  The leaf-mountain roared *WWWWOOOOOSH!*
and WHOOSHed four feet of Milo sky-high—right into the arms of
the same sheet that had once been Mom’s Sunday-white.  The fabric enveloped him
like a giant green hug.  When the leaf-blizzard settled, there lay
Milo—wrapped in clean cloth—giggling with acorn caps stuck to his soggy
socks and a perfect *whoopee cushion* impression coming from the trapped air.
Lina grinned (secretly thrilled by the sheet-parachute).  “Share the leaf storm?”
she asked again.  Milo burbled through sheet-flaps, “OK, OK, BUT I still get
to pick *which* pieces of sky fall first next time!”

Moral aside: piles are fine so long as you share the *kaboom* part.
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

# Make the shared result containers importable when this script is run directly
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402
import asp  # lazily imported inside helpers

# Narrative constants
INNER_MONOLOGUE_FONT = "*"
SOUND_EFFECT_FONT = "**"
THRESHOLD = 2.0  # physical/memetic thresholds at which we narrate

# Shared counters for the Tall Tale style
# Physical meters
METER_KINDS = {"pile_mass", "mess_level", "wetness", "tangled"}
# Emotional memes
MEME_KINDS = {"defiance", "joy", "guilt", "share_itch", "naughty_glow"}

# Region names for worn-item coverage checks (used during pile avalanches)
REGIONS = {"hands", "arms", "torso"}

# ---------------------------------------------------------------------------
# Entities: characters, piles, wrappable hazards (sheets, baskets, etc.)
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "object"
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
    protective: bool = False

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "sister"}
        male = {"boy", "father", "dad", "brother", "kid"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad", "sister": "Lina"}.get(self.type, self.type)

# ---------------------------------------------------------------------------
# Parametrization knobs -- the swappable vocabulary of this little Tall Tale domain.
# ---------------------------------------------------------------------------
@dataclass
class Setting:
    place: str = "the backyard"
    indoor: bool = False
    affords: set[str] = field(default_factory=set)   # which pile activities this place supports

@dataclass
class Activity:
    """What the tiny humans love to do with piles."""
    id: str
    verb: str            # after "wanted to ..."             : "build a pile"
    gerund: str          # after "loved playing ... and ..." : "building piles"
    rush: str            # after "tried to ..."              : "grab the rake"
    mess_kind: str       # mess kind key, one of METER_KINDS  : "mess_level"
    disorder_factor: str  # how the pile collapses            : "avalanche"
    keyword: str = ""    # topic word for generation prompts   : "leaf mountain"
    tags: set[str] = field(default_factory=set)

@dataclass
class Prize:
    """The thing being piled; its risk of being ruined by messy-play."""
    label: str
    phrase: str
    type: str = "object"
    plural: bool = False
    genders: set[str] = field(default_factory=lambda: {"girl", "boy"})

@dataclass
class Gear:
    """Protective contraptions that let tiny humans share the pile fun."""
    id: str
    label: str
    covers: set[str]
    prep: str            # body of the offer: "fetch your sharing basket"
    tail: str            # closing clause: "ran to fetch her basket"
    plural: bool = False

# ---------------------------------------------------------------------------
# World: entity store + narration history + loud inner-monologue bubbles.
# ---------------------------------------------------------------------------
class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        # Tall Tale color state
        self.internal_volume = 3   # decibels of chaos (escalates after crashes)
        self.hero_monologue = []  # list[(speaker_id, mono_text)]

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities.get(eid)

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def pile(self) -> Optional[Entity]:
        for e in self.entities.values():
            if e.type == "pile" or e.type == "leaves":
                return e
        return None

    def add_monologue(self, speaker: Entity, text: str) -> None:
        mono = INNER_MONOLOGUE_FONT + text + INNER_MONOLOGUE_FONT
        self.hero_monologue.append((speaker.id, mono))

    def say(self, text: str, effect: bool = False) -> None:
        if text:
            lines = text.split("\n")
            for line in lines:
                if effect:
                    line = SOUND_EFFECT_FONT + line + SOUND_EFFECT_FONT
                if self.internal_volume >= 3:
                    rep = "!" if self.internal_volume == 3 else "!!"
                    self.paragraphs[-1].append(line + rep)
                else:
                    self.paragraphs[-1].append(line)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        chunks = []
        # Monologue bubbles deliberately interleaved with story paragraphs, Tall Tale style
        for para in self.paragraphs:
            if para:
                chunks.append(" ".join(para))
        for speaker_id, mono in self.hero_monologue:
            chunks.append(f'    {speaker_id} thought: {mono}')
        return "\n\n".join(chunks)

    def copy(self) -> "World":
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.internal_volume = self.internal_volume
        clone.hero_monologue = self.hero_monologue.copy()
        clone.facts = self.facts.copy()
        return clone

# ---------------------------------------------------------------------------
# Causal rules: forward-chained to a fixpoint.  Tall Tale style: every rule
# can escalate the internal_volume and trigger bigger sound effects.
# ---------------------------------------------------------------------------
@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]

def _r_pile_collapse(world: World) -> list[str]:
    """pile_mass > threshold -> avalanche noise + mess to all nearby."""
    p = world.pile()
    if not p or p.meters["pile_mass"] < THRESHOLD:
        return []
    sig = ("collapse", p.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    # Escalate chaos volume
    world.internal_volume = min(10, world.internal_volume + 2)
    vol = "!" * world.internal_volume
    return [
        f"The {p.label} wobbled{vol}",
        f"A leaf avalanche roared {SOUND_EFFECT_FONT}WWWWOOOOOSH!{SOUND_EFFECT_FONT}{vol}",
        "Leaves flew everywhere like confetti in a gust from a sneeze."
    ]

def _r_mess_grow(world: World) -> list[str]:
    """Characters inside messy zones -> their items get tangled."""
    out: list[str] = []
    for actor in world.characters():
        if actor.meters["mess_level"] > THRESHOLD:
            sig = ("mess", actor.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            # Every item near the actor (hands/arms) gets messier
            for item in world.entities.values():
                if item.worn_by == actor.id and item.region in {"hands", "arms"}:
                    item.meters["tangled"] += 1
                    out.append(f"{actor.pronoun('possessive').capitalize()} {item.label} got so tangled it would take a week to *PLINK* un-snarl.")
    return out

def _r_defiance_surge(world: World) -> list[str]:
    """Naughty behavior triggers louder internal monologue and share_itch meme flip."""
    for actor in world.characters():
        if actor.memes["defiance"] > THRESHOLD and world.internal_volume >= 4:
            if sig := ("def_echo", actor.id) not in world.fired:
                world.fired.add(("def_echo", actor.id))
                defiant_words = {
                    "Milo": "*SPINNY-BRAINY* monologue screamed:",
                    "Lina": "**STUBBORN-WISPERS** echoed inside:"
                }.get(actor.id, "Their inner voice howled:")
                world.add_monologue(actor, f"{defiant_words} 'I DO NOT WANT TO SHARE!'")
                return [f"{actor.pronoun('subject')} turned even naughtier."]
    return []

CAUSAL_RULES: list[Rule] = [
    Rule(name="collapse", tag="physical", apply=_r_pile_collapse),
    Rule(name="mess_grow", tag="physical", apply=_r_mess_grow),
    Rule(name="defiance_surge", tag="social", apply=_r_defiance_surge),
]

def propagate(world: World, narrate: bool = True) -> list[str]:
    """Apply all rules until nothing new fires (enforces THRESHOLD fixpoint)."""
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate and produced:
        for s in produced:
            world.say(s, effect=True)
    return produced

# ---------------------------------------------------------------------------
# Verbs: Tall Tale screenplay beats with inner monologue + sound effects
# ---------------------------------------------------------------------------
def naughty_verb(activity: Activity) -> str:
    return {
        "rake": "WHACK-WHACK-WHACK!",
        "jump": "KA-BOING!",
        "hurl": "SPLATAPULT!",
    }.get(activity.id.split("_")[0], "OOPSIE!")

def pile_wobble_text(size: float) -> str:
    levels = {0: "wobbles", 2: "shudders", 4: "groans", 6: "wails"}
    return levels.get(int(size//2), "roars")

# Core screenplay verbs
def spot_pile(world: World, actor: Entity, phrase: str) -> None:
    world.say(f"{actor.id} spotted a {phrase} taller than {actor.label_word}'s nose!")

def loves_activity(world: World, actor: Entity, activity: Activity) -> None:
    actor.memes["joy"] += 4
    sound = naughty_verb(activity)
    world.say(
        f"{actor.pronoun().capitalize()} loved {activity.gerund} so much "
        f"that even the {sound} made {actor.pronoun()} giggle."
    )

def gather_materials(world: World, actor: Entity, prize: Entity) -> None:
    world.say(
        f"{actor.id} {actor.pronoun('subject')} scurried for {prize.phrase}. "
        "*PING-PLINK!* went the acorn cups as {actor.pronoun('subject')} snatched them up."
    )

def naughty_strike(world: World, actor: Entity, activity: Activity) -> None:
    actor.memes["naughty_glow"] += 1
    actor.memes["defiance"] += 1.5
    actor.meters["mess_level"] += 0.8
    world.say(
        f"{actor.pronoun('subject').capitalize()} decided to be {SOUND_EFFECT_FONT}naughty{SOUND_EFFECT_FONT}! "
        f"{naughty_verb(activity)}"
    )
    # Inner monologue escalation
    fear = {
        "Milo": "If Mom sees this, she’ll GROWL like a bear with a frozen popsicle lodged in its molar!",
        "Lina": "**MENTAL-SCOLD** filled the air around her ears: 'Share the leaf sky? But WHO picks which pieces fall first?!'"
    }
    world.add_monologue(actor, fear.get(actor.id, "The tiny humans’ rulebook just burnt to a crisp."))

def watch_trouble(world: World, actor: Entity) -> None:
    worry = actor.memes.get("defiance", 0) * 0.8
    if worry < THRESHOLD:
        return
    world.say(
        f"{actor.pronoun('subject').capitalize()} gulped; {actor.pronoun('possessive')} "
        f"stomach flip-flopped like a pancake on Sunday morning."
    )

def sibling_share_offer(world: World, sharer: Entity, target: Entity, item: Entity) -> bool:
    if target.id == sharer.id:
        return False
    world.say(
        f"{sharer.id} held out {sharer.pronoun('possessive')} emergency-sharing {item.label}: "
        f'"Share the leaf mountain!"'
    )
    world.add_monologue(sharer, "*BUT-IF-I-SHARE-I-LOSE-THE-KABOOM* my tiny brain honked loudly.")
    return True

def share_attempt(world: World, sharer: Entity, target: Entity, gear: Entity) -> None:
    sharer.memes["share_itch"] += 2
    sharer.memes["defiance"] -= 0.7
    gear.meters["tangled"] = 0  # basket untangles
    world.say(
        f"They teamed up and {gear.label} {SOUND_EFFECT_FONT}PLINK-PLONK!{SOUND_EFFECT_FONT} "
        f"as leaves were bundled safe and sound."
    )
    world.internal_volume = max(1, world.internal_volume - 2)

def chaos_resolution(world: World, actor: Entity) -> None:
    """Successful sharing ends with a satisfying Tall Tale wrap-up."""
    vol = "!" * max(1, world.internal_volume)
    world.say(
        f"When the {SOUND_EFFECT_FONT}GIGANTIC-leaf-snack{SOUND_EFFECT_FONT} settled, "
        f"{actor.pronoun('subject')} found {actor.pronoun('object')} wrapped in a giant green hug! "
        f"Life is good{vol}"
    )
    world.add_monologue(actor, "*OK-FINE-we-shared-BUT-next-time-I-get-TO-pick-the-sky-fragments*")

# ---------------------------------------------------------------------------
# The screenplay: classic Tall Tale three-act with booming sentences and
# exclamation-mark avalanches, driven entirely by the verbs above.
# ---------------------------------------------------------------------------
def tell(place: Setting, activity: Activity, prize: Prize,
         name: str = "Milo", sibling: str = "Lina",
         trait: str = "stretchy-fingered") -> World:
    world = World(place)
    hero = world.add(Entity(
        id=name, kind="character", type="boy",
        traits=["tiny human", "stretchy-fingered", "heart-full-of-boing"],
        label=f"{name} the tiny naughty"
    ))
    sibling_e = world.add(Entity(
        id=sibling, kind="character", type="sister", label=sibling,
    ))
    leaf_pile = world.add(Entity(
        id="leaf_mountain", type="pile", label="leaf mountain",
        phrase="biggest pile of leaves ever made by tiny humans",
        meters={"pile_mass": 3.2}
    ))
    sheet = world.add(Entity(
        id="sheet", type="bedsheet", label="sheet",
        phrase="Mom’s Sunday-white bedsheet", plural=False
    ))
    basket = world.add(Entity(
        id="basket", type="gear", label="sharing basket",
        phrase="emergency-sharing basket", plural=False
    ))

    # Act 1: Setup – a magnificent leaf mountain glimpsed through Tall Tale eyes
    world.say("Once upon a time—did I mention I’m **ONLY FIVE FEET TALL?!**—in "
              f"a backyard so big *SLURP-SLURP* the grass swallowed shoes whole.")
    spot_pile(world, hero, leaf_pile.phrase)
    loves_activity(world, hero, activity)
    gather_materials(world, hero, prize)
    hero.meters["pile_mass"] = 1.1

    # Act 2: Conflict – the naughty verb triggers avalanche!!
    world.para()
    world.internal_volume = 3
    naughty_strike(world, hero, activity)
    watch_trouble(world, sibling_e)
    sibling_share_offer(world, sibling_e, hero, basket)
    # Rules fire during the tension: collapse if pile mass > threshold
    propagate(world, narrate=True)
    if hero.memes["defiance"] >= THRESHOLD:
        hero.meters["mess_level"] += 1.1

    # Act 3: Resolution – only sharing and a giant green hug can calm the chaos
    world.para()
    share_attempt(world, sibling_e, hero, basket)
    chaos_resolution(world, sibling_e)

    # Collect facts for Q&A
    world.facts.update(
        hero=hero, sibling=sibling_e, pile=leaf_pile, sheet=sheet,
        activity=activity, prize=prize, internal_volume=world.internal_volume
    )
    return world

# ---------------------------------------------------------------------------
# Content registries. Tall Tale world: exaggerated everything.
# ---------------------------------------------------------------------------
SETTINGS = {
    "backyard": Setting(place="backyard", indoor=False, affords={"rake_pile", "jump_pile"}),
    "living_room": Setting(place="living room", indoor=True, affords={"toy_pile"}),
    "park": Setting(place="park", indoor=False, affords={"trash_pile"}),
}

ACTIVITIES = {
    "rake_pile": Activity(
        id="rake_pile",
        verb="build a pile",
        gerund="building piles",
        rush="grab the rake",
        mess_kind="mess_level",
        disorder_factor="avalanche",
        keyword="leaf mountain",
        tags={"naughty", "pile", "raking"}
    ),
    "jump_pile": Activity(
        id="jump_pile",
        verb="jump into piles",
        gerund="jumping into piles",
        rush="dive toward the pile",
        mess_kind="mess_level",
        disorder_factor="crash",
        keyword="jumping pile",
        tags={"naughty", "pile", "crashing"}
    ),
    "toy_pile": Activity(
        id="toy_pile",
        verb="cover the floor",
        gerund="covering the floor",
        rush="build an epic tower",
        mess_kind="tangled",
        disorder_factor="topple",
        keyword="toy castle",
        tags={"play", "pile", "indoor"}
    ),
    "trash_pile": Activity(
        id="trash_pile",
        verb="make a junk tower",
        gerund="making junk towers",
        rush="balance junk on head",
        mess_kind="wetness",
        disorder_factor="slump",
        keyword="junk pile",
        tags={"naughty", "pile", "outdoor"}
    ),
}

PRIZES = {
    "leaves": Prize(label="leaves", phrase="armful of golden leaves", plural=True),
    "toys": Prize(label="toys", phrase="bucket of toys", plural=True),
    "trash": Prize(label="trash", phrase="bag of recyclables", type="bag"),
    "socks": Prize(label="socks", phrase="pile of clean socks", plural=True),
}

GEAR = [
    Gear(
        id="basket",
        label="sharing basket",
        covers={"hands"},
        prep="fetch your sharing basket",
        tail="ran to fetch her emergency-sharing basket",
    ),
    Gear(
        id="sheet",
        label="giant sheet",
        covers={"torso"},
        prep="wrap yourself in a sheet-parachute",
        tail="found a giant green hug in the sheet-parachute",
    ),
]

NAMES = ["Milo", "Lina", "Ziggy", "Pip", "Twyla", "Bram", "Noni", "Taro"]
TRAITS = ["stretchy-fingered", "heart-full-of-boing", "troublemaker", "careful"]

def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            act = ACTIVITIES[act_id]
            for prize_id in PRIZES:
                # Tall Tales allow more combos – every pile activity can potentially be naughty!
                combos.append((place, act_id, prize_id))
    return combos

# ---------------------------------------------------------------------------
# Per-world parameters
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    name: str
    sibling: str
    trait: str
    seed: Optional[int] = None

# ---------------------------------------------------------------------------
# Q&A generation – three separate sets grounded in the Tall Tale model
# ---------------------------------------------------------------------------
KNOWLEDGE = {
    "naughty": [("What does naughty mean?",
                "Naughty means doing something playful that might get you in trouble, "
                "like building a pile that’s taller than your head.")],
    "pile": [("What is a pile?",
              "A pile is stuff stacked up higher than it was before. Tall piles make "
              "loud sounds when they fall!")],
    "inner_monologue": [("What does inner monologue mean?",
                         "Inner monologue is when someone thinks thoughts inside their own head "
                         "so loudly that it sounds like words *in bubbles* in a comic.")],
    "sharing": [("Why is sharing important?",
                 "Sharing lets everyone play safely together, even when naughty ideas "
                 "want to *KABOOM!*")],
}

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    act = f["activity"]
    return [
        f"Write an exaggerated Tall Tale for a 3-to-5-year-old full of "
        f"sound effects, inner monologue bubbles, and the words 'naughty' and 'pile' "
        f"about building a {act.keyword}.",
        f'Produce a story where "{f["hero"].id}" acts naughty, '
        f'"{f["sibling"]}" tries sharing, and there is a giant loud crash followed '
        f"by a satisfying hug at the end.",
        f'Invent a story that includes the phrase "**GIGANTIC-leaf-snack**" and '
        f"inner thoughts marked between asterisks *like this*."
    ]

def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, sibling = f["hero"], f["sibling"]
    act, prize = f["activity"], f["prize"]
    verb = act.verb
    vol = "!" * max(1, world.internal_volume)
    qa: list[QAItem] = [
        QAItem(
            question="Who is the tiny naughty character in the story?",
            answer=f"The tiny naughty character is {hero.id}, a {hero.traits[0]} boy."
        ),
        QAItem(
            question="What happened when the pile collapsed?",
            answer=f"The pile wobbled so hard that it released a {SOUND_EFFECT_FONT}WWWWOOOOOSH!{SOUND_EFFECT_FONT}{vol} "
                   f"avalanche of leaves!"
        ),
        QAItem(
            question="Why did the sibling try to share?",
            answer=(
                f"{sibling} held out the sharing basket because even though {hero.id} acted naughty "
                f"by {verb}, it’s better when everyone can play loudly together and then "
                f"wind up wrapped in a giant green hug at the end!"
            )
        )
    ]
    # Add inner-monologue-specific Q&A
    if world.hero_monologue:
        q, a = world.hero_monologue[-1]
        qa.append(QAItem(
            question=f"What was {q}’s very last inner thought right before the resolution?",
            answer=a
        ))
    return qa

def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts.get("activity", Activity(id="", gerund="", keyword="")).tags
    tags.update(["naughty", "pile", "inner_monologue", "sharing"])
    out: list[QAItem] = []
    for tag in ["naughty", "pile", "inner_monologue", "sharing", "tall_tale"]:
        if tag in tags:
            out.extend(QAItem(q, a) for q, a in KNOWLEDGE.get(tag, []))
    return out

def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Tall Tale prompts – the asks that would yield this roaring story =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions – answerable from text and inner monologues ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions – what every Tiny Human should know ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)

# ---------------------------------------------------------------------------
# ASP Twin – the declarative gate that mirrors valid_combos() in clingo
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A canBuildPile if place affords the activity (Tall Tale expansion relaxed)
canBuildPile(Place, Activity) :- affords(Place, Activity).

% Prizes can be shared if gear exists (sharing basket always exists here)
canSharePrize(Activity, Prize) :- activity(Activity), prize(Prize).

valid_tall_tale(Place, Activity, Prize, Name) :-
    canBuildPile(Place, Activity),
    canSharePrize(Activity, Prize),
    wears(Name, trophy).

% Wearing trophies is relaxed in Tall Tales (any tiny human can wear anything)
wears(tiny_human, _).
"""

def asp_facts() -> str:
    lines: list[str] = []
    import asp
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
        if pr.plural:
            lines.append(asp.fact("prize_plural", pid))
    for name in NAMES:
        lines.append(asp.fact("wears", "tiny_human", name))
    return "\n".join(lines)

def asp_program(show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"

def asp_valid_stories() -> list[tuple]:
    model = asp.one_model(asp_program("#show valid_tall_tale/4."))
    return sorted(set(asp.atoms(model, "valid_tall_tale")))

def asp_verify() -> int:
    clingo_set, python_set = set(asp_valid_stories()), set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo Tall Tale gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH loud enough to wake the household:")
    if clingo_set - python_set:
        print("  clingo-only booms:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  python-only echoes:", sorted(python_set - clingo_set))
    return 1

# ---------------------------------------------------------------------------
# Standard storyworld interface
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Tall Tale world: naughty piles, inner monologue bubbles, "
                    "sound effects, and sharing! Unspecified choices are picked at random.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--name")
    ap.add_argument("--sibling")
    ap.add_argument("--trait")
    ap.add_argument("-n", type=int, default=1, help="number of Tall Tales to tell")
    ap.add_argument("--seed", type=int, default=None,
                    help="base seed for reproducible random booms")
    ap.add_argument("--all", action="store_true",
                   help="render the curated Tall Tale set instead")
    ap.add_argument("--trace", action="store_true",
                   help="dump world-model, inner bubble logs, and volume levels")
    ap.add_argument("--qa", action="store_true",
                   help="include the three Q&A tower of terror")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of **BOOM** text")
    ap.add_argument("--asp", action="store_true",
                   help="print the clingo-compatible Tall Tale gate output")
    ap.add_argument("--verify", action="store_true",
                   help="check the ASP gate matches valid_combos() with a *GIGANTIC!* boom")
    ap.add_argument("--show-asp", action="store_true",
                   help="print the full ASP program for brave clingo warriors")
    return ap

def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if not any([args.place, args.activity, args.prize]):
        combos = valid_combos()
    else:
        combos = [c for c in valid_combos()
                  if (args.place is None or c[0] == args.place)
                  and (args.activity is None or c[1] == args.activity)
                  and (args.prize is None or c[2] == args.prize)]
        if not combos:
            raise StoryError("(No match: naughty piles in that place? Try --place backyard!)")

    place, activity, prize_id = rng.choice(combos)
    prize = PRIZES[prize_id]
    name = args.name or rng.choice(NAMES)
    sibling = args.sibling or (rng.choice([n for n in NAMES if n != name]))
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(
        place=place,
        activity=activity,
        prize=prize_id,
        name=name,
        sibling=sibling,
        trait=trait,
    )

def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.place],
        ACTIVITIES[params.activity],
        PRIZES[params.prize],
        name=params.name,
        sibling=params.sibling,
        trait=params.trait,
    )
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
        print("\n--- world model state ---")
        w = sample.world
        print(f"internal_volume={w.internal_volume}")
        print("characters:")
        for c in w.characters():
            print(f"  {c.id}: mess={c.meters['mess_level']:.1f} defiance={c.memes['defiance']:.1f}")
        print("pile:")
        p = w.pile()
        if p:
            print(f"  {p.type} mass={p.meters['pile_mass']:.1f}")
        print("fired rules:", sorted(set(n for n, *_ in w.fired)))
    if qa:
        print()
        print(format_qa(sample))

def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    lines.append(f"internal_volume={world.internal_volume}")
    lines.append("characters:")
    for c in world.characters():
        meters = {k: v for k, v in c.meters.items() if v}
        memes = {k: v for k, v in c.memes.items() if v}
        lines.append(f"  {c.id:8} meters={dict(meters)}  memes={dict(memes)}")
    p = world.pile()
    if p:
        lines.append(f"pile id={p.id} mass={p.meters.get('pile_mass', 0):.1f}")
    lines.append("fired rules: " + ", ".join(sorted(set(n for n, *_ in world.fired))))
    return "\n".join(lines)

# Curated set for --all booms
CURATED = [
    StoryParams(
        place="backyard",
        activity="rake_pile",
        prize="leaves",
        name="Milo",
        sibling="Lina",
        trait="stretchy-fingered",
    ),
    StoryParams(
        place="living_room",
        activity="toy_pile",
        prize="toys",
        name="Ziggy",
        sibling="Pip",
        trait="careful",
    ),
    StoryParams(
        place="park",
        activity="trash_pile",
        prize="trash",
        name="Twyla",
        sibling="Bram",
        trait="troublemaker",
    ),
]

def explain_rejection(act: Activity, prize: Prize) -> str:
    return "(Tall Tale rules relaxed: every pile can be naughty! Try --place backyard again.)"

def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid_tall_tale/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        stories = asp_valid_stories()
        print(f"{len(stories)} compatible (place, activity, prize, name) Tall Tale piles:\n")
        for t in stories:
            print(f"  {t}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen_tales: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 20, 70):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as err:
                print(err)
                return
            params.seed = seed
            sample = generate(params)
            tale_hash = "\n".join(sample.story.splitlines()[:5])  # short form check
            if tale_hash in seen_tales:
                continue
            seen_tales.add(tale_hash)
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
            header = f"### Tall Tale #{i+1}: {p.name}&{p.sibling} {p.activity} in the {p.place}"
        elif len(samples) > 1:
            header = f"### Tall Tale variant {i + 1} **BOOM**"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 80 + "\n")

if __name__ == "__main__":
    main()
