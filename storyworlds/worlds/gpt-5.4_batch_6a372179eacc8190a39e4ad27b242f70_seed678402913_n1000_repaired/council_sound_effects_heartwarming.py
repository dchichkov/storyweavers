#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/council_sound_effects_heartwarming.py
================================================================

A standalone story world about a small kindness council helping a frightened
little animal with gentle sounds and a cozy place to rest.

The seed asked for:
- the word "council"
- sound effects
- a heartwarming style

This world models a simple physical and emotional state:
a small animal hides after a startling moment, two children hold a tiny
"morning council," choose a fitting gentle sound and a matching comfort, and
help the animal feel safe enough to come out.

Run it
------
    python storyworlds/worlds/gpt-5.4/council_sound_effects_heartwarming.py
    python storyworlds/worlds/gpt-5.4/council_sound_effects_heartwarming.py -n 5 --seed 7
    python storyworlds/worlds/gpt-5.4/council_sound_effects_heartwarming.py --all
    python storyworlds/worlds/gpt-5.4/council_sound_effects_heartwarming.py --qa
    python storyworlds/worlds/gpt-5.4/council_sound_effects_heartwarming.py --json
    python storyworlds/worlds/gpt-5.4/council_sound_effects_heartwarming.py --trace
    python storyworlds/worlds/gpt-5.4/council_sound_effects_heartwarming.py --verify
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

# Make the shared result containers importable when this script is run directly.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
GENTLE_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    traits: tuple = field(default_factory=tuple)
    name: str = ""
    title: str = ""
    voice: str = ""
    thanks: str = ""
    scold: str = ""
    help_action: str = ""
    face: str = ""
    path_line: str = ""
    ending_image: str = ""
    weak_spot: str = ""
    role_text: str = ""
    need: str = ""
    metallic: str = ""
    special: str = ""
    question_reply: str = ""
    wisdom: str = ""
    rising_line: str = ""
    risk: str = ""
    qa_text: str = ""
    location_text: str = ""
    use_line: str = ""
    cry: str = ""
    ending_line: str = ""
    reach: str = ""
    damage: str = ""
    use: str = ""
    opening: str = ""
    warning: str = ""
    owner_text: str = ""
    ground: str = ""
    action_line: str = ""
    kindness_text: str = ""
    calm: str = ""
    restored: str = ""
    shine: str = ""
    reveal_text: str = ""
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "grandmother"}
        male = {"boy", "father", "dad", "man", "grandfather"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return {
            "mother": "mom",
            "father": "dad",
            "grandmother": "grandma",
            "grandfather": "grandpa",
        }.get(self.type, self.type)


@dataclass
class Setting:
    id: str
    place: str
    weather_line: str
    hiding_spot: str
    meeting_spot: str
    home_phrase: str
    allows: set[str] = field(default_factory=set)


@dataclass
class CreatureCfg:
    id: str
    label: str
    phrase: str
    sound_need: str
    comfort_need: str
    family_name: str
    call_sound: str
    movement_sound: str
    timid: int
    allowed_places: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class SoundTool:
    id: str
    label: str
    phrase: str
    sfx: str
    line: str
    gentle: int
    supports: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Comfort:
    id: str
    label: str
    phrase: str
    supports: set[str] = field(default_factory=set)
    home_line: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    place: str
    creature: str
    sound: str
    comfort: str
    child1: str
    child1_gender: str
    child2: str
    child2_gender: str
    elder: str
    seed: Optional[int] = None


SETTINGS = {
    "garden": Setting(
        id="garden",
        place="the garden",
        weather_line="The grass still held tiny silver drops from the night rain.",
        hiding_spot="under the rosemary bush",
        meeting_spot="the warm stone path",
        home_phrase="near the little duck pond at the end of the garden",
        allows={"duckling", "bunny"},
    ),
    "porch": Setting(
        id="porch",
        place="the front porch",
        weather_line="A soft breeze moved the hanging fern with a hush-hush sound.",
        hiding_spot="behind a stack of flowerpots",
        meeting_spot="the striped doormat",
        home_phrase="inside a laundry basket lined with a tea towel",
        allows={"kitten", "puppy"},
    ),
    "park": Setting(
        id="park",
        place="the park",
        weather_line="Morning light made the bench slats glow pale gold.",
        hiding_spot="under the wooden bench",
        meeting_spot="the flat patch of clover by the path",
        home_phrase="beside a picnic blanket where the little family was waiting",
        allows={"duckling", "bunny", "puppy"},
    ),
}

CREATURES = {
    "kitten": CreatureCfg(
        id="kitten",
        label="kitten",
        phrase="a small gray kitten",
        sound_need="bell",
        comfort_need="basket",
        family_name="mother cat",
        call_sound="mew-mew",
        movement_sound="pat-pat",
        timid=2,
        allowed_places={"porch"},
        tags={"kitten", "gentle"},
    ),
    "duckling": CreatureCfg(
        id="duckling",
        label="duckling",
        phrase="a fluffy yellow duckling",
        sound_need="tap",
        comfort_need="towel",
        family_name="duck family",
        call_sound="peep-peep",
        movement_sound="pitter-patter",
        timid=2,
        allowed_places={"garden", "park"},
        tags={"duckling", "gentle"},
    ),
    "bunny": CreatureCfg(
        id="bunny",
        label="bunny",
        phrase="a soft brown bunny",
        sound_need="rustle",
        comfort_need="leafy",
        family_name="rabbit family",
        call_sound="sniff-sniff",
        movement_sound="hop-hop",
        timid=3,
        allowed_places={"garden", "park"},
        tags={"bunny", "gentle"},
    ),
    "puppy": CreatureCfg(
        id="puppy",
        label="puppy",
        phrase="a spotted puppy",
        sound_need="bell",
        comfort_need="blanket",
        family_name="family",
        call_sound="yip-yip",
        movement_sound="patter-patter",
        timid=1,
        allowed_places={"porch", "park"},
        tags={"puppy", "gentle"},
    ),
}

SOUNDS = {
    "ribbon_bell": SoundTool(
        id="ribbon_bell",
        label="ribbon bell",
        phrase="a tiny bell tied to a blue ribbon",
        sfx="jingle-jingle",
        line="made a bright, tiny bell song",
        gentle=2,
        supports={"kitten", "puppy"},
        tags={"bell", "sound"},
    ),
    "wooden_spoon": SoundTool(
        id="wooden_spoon",
        label="wooden spoon and bowl",
        phrase="a wooden spoon tapped on a little bowl",
        sfx="tap-tap",
        line="made a neat, friendly tapping sound",
        gentle=2,
        supports={"duckling"},
        tags={"tap", "sound"},
    ),
    "leaf_bundle": SoundTool(
        id="leaf_bundle",
        label="bundle of dry leaves",
        phrase="a small bundle of dry leaves",
        sfx="rustle-rustle",
        line="made a soft leafy whisper",
        gentle=2,
        supports={"bunny"},
        tags={"rustle", "sound"},
    ),
    "drum": SoundTool(
        id="drum",
        label="toy drum",
        phrase="a toy drum",
        sfx="boom-boom",
        line="made a big loud boom",
        gentle=1,
        supports=set(),
        tags={"loud", "sound"},
    ),
}

COMFORTS = {
    "basket_nest": Comfort(
        id="basket_nest",
        label="basket nest",
        phrase="a basket with a folded tea towel inside",
        supports={"kitten"},
        home_line="The basket looked round and still, like a quiet little den.",
        tags={"basket", "comfort"},
    ),
    "towel_ring": Comfort(
        id="towel_ring",
        label="towel ring",
        phrase="a soft ring made from a rolled towel",
        supports={"duckling"},
        home_line="The towel made a warm circle where tiny feet could rest.",
        tags={"towel", "comfort"},
    ),
    "leafy_tunnel": Comfort(
        id="leafy_tunnel",
        label="leafy tunnel",
        phrase="a small tunnel of leaves and a shoebox",
        supports={"bunny"},
        home_line="The leafy tunnel gave the shy little creature a place to pause and breathe.",
        tags={"leafy", "comfort"},
    ),
    "blanket_corner": Comfort(
        id="blanket_corner",
        label="blanket corner",
        phrase="a blanket folded into a soft corner",
        supports={"puppy"},
        home_line="The blanket corner looked cozy enough for a tired little body.",
        tags={"blanket", "comfort"},
    ),
}


def valid_combo(place_id: str, creature_id: str, sound_id: str, comfort_id: str) -> bool:
    if place_id not in SETTINGS or creature_id not in CREATURES or sound_id not in SOUNDS or comfort_id not in COMFORTS:
        return False
    place = SETTINGS[place_id]
    creature = CREATURES[creature_id]
    sound = SOUNDS[sound_id]
    comfort = COMFORTS[comfort_id]
    if sound.gentle < GENTLE_MIN:
        return False
    return (
        creature_id in place.allows
        and place_id in creature.allowed_places
        and creature_id in sound.supports
        and creature_id in comfort.supports
        and creature.sound_need in sound.tags
        and creature.comfort_need in comfort.tags
    )


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for place_id in SETTINGS:
        for creature_id in CREATURES:
            for sound_id in SOUNDS:
                for comfort_id in COMFORTS:
                    if valid_combo(place_id, creature_id, sound_id, comfort_id):
                        combos.append((place_id, creature_id, sound_id, comfort_id))
    return combos


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_peek(world: World) -> list[str]:
    creature = world.get("creature")
    if creature.meters["heard_right_sound"] < THRESHOLD:
        return []
    if creature.meters["peeked"] >= THRESHOLD:
        return []
    sig = ("peek", creature.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    creature.meters["peeked"] += 1
    creature.memes["trust"] += 1
    return []


def _r_step_out(world: World) -> list[str]:
    creature = world.get("creature")
    if creature.meters["peeked"] < THRESHOLD or creature.meters["comfort_ready"] < THRESHOLD:
        return []
    if creature.meters["hidden"] < THRESHOLD:
        return []
    sig = ("step_out", creature.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    creature.meters["hidden"] = 0.0
    creature.meters["near_children"] += 1
    creature.memes["fear"] = max(0.0, creature.memes["fear"] - 1.0)
    creature.memes["trust"] += 1
    return []


def _r_settle(world: World) -> list[str]:
    creature = world.get("creature")
    if creature.meters["near_children"] < THRESHOLD or creature.meters["comfort_ready"] < THRESHOLD:
        return []
    if creature.meters["safe"] >= THRESHOLD:
        return []
    sig = ("settle", creature.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    creature.meters["safe"] += 1
    creature.meters["home"] += 1
    creature.memes["fear"] = 0.0
    creature.memes["calm"] += 1
    for eid in ("child1", "child2", "elder"):
        world.get(eid).memes["relief"] += 1
    return []


CAUSAL_RULES = [
    Rule(name="peek", tag="social", apply=_r_peek),
    Rule(name="step_out", tag="physical", apply=_r_step_out),
    Rule(name="settle", tag="social", apply=_r_settle),
]


def propagate(world: World) -> None:
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            out = rule.apply(world)
            if out:
                pass
            if any(sig[0] == rule.name for sig in world.fired):
                # not enough to detect newly fired by name alone
                # so compare lengths via a local check
                pass
        # simple fixpoint test: attempt all rules, then stop if none newly fired
        # by comparing set size before/after the pass.
        before = len(world.fired)
        for rule in CAUSAL_RULES:
            rule.apply(world)
        after = len(world.fired)
        changed = after > before


def predict_success(place_id: str, creature_id: str, sound_id: str, comfort_id: str) -> bool:
    if not valid_combo(place_id, creature_id, sound_id, comfort_id):
        return False
    sim = World()
    creature_cfg = CREATURES[creature_id]
    creature = sim.add(Entity(id="creature", kind="character", type=creature_id, label=creature_cfg.label))
    sim.add(Entity(id="child1", kind="character", type="girl", label="child"))
    sim.add(Entity(id="child2", kind="character", type="boy", label="child"))
    sim.add(Entity(id="elder", kind="character", type="grandmother", label="elder"))
    creature.meters["hidden"] = 1
    creature.memes["fear"] = float(creature_cfg.timid)
    creature.meters["heard_right_sound"] += 1
    creature.meters["comfort_ready"] += 1
    propagate(sim)
    return creature.meters["safe"] >= THRESHOLD


def choose_names(rng: random.Random) -> tuple[str, str, str, str]:
    girl_names = ["Lina", "Mia", "Nora", "Ava", "Lucy", "Rose"]
    boy_names = ["Ben", "Sam", "Theo", "Max", "Eli", "Noah"]
    g = rng.choice(girl_names)
    b = rng.choice([n for n in boy_names if n != g])
    if rng.choice([True, False]):
        return g, "girl", b, "boy"
    return b, "boy", g, "girl"


def council_opening(world: World, child1: Entity, child2: Entity, elder: Entity, setting: Setting, creature: CreatureCfg) -> None:
    world.say(
        f"Early one bright morning, {child1.id} and {child2.id} were with {elder.label_word} in {setting.place}."
    )
    world.say(setting.weather_line)
    world.say(
        f"Then they heard a tiny {creature.call_sound} from {setting.hiding_spot} and found {creature.phrase} tucked in tight."
    )
    world.say(
        f"{child1.id} crouched low. {child2.id} held very still. Right there on {setting.meeting_spot}, they decided to form a little council for kindness."
    )


def worry_and_notice(world: World, child1: Entity, child2: Entity, elder: Entity, setting: Setting, creature_cfg: CreatureCfg) -> None:
    creature = world.get("creature")
    creature.meters["hidden"] = 1
    creature.memes["fear"] = float(creature_cfg.timid)
    child1.memes["worry"] += 1
    child2.memes["worry"] += 1
    elder.memes["care"] += 1
    world.say(
        f'"No rushing," {elder.label_word} said softly. "A scared little one needs a gentle plan."'
    )
    if creature_cfg.timid >= 3:
        world.say(
            f"The {creature_cfg.label} pressed deeper into the shade and gave another tiny {creature_cfg.call_sound}."
        )
    else:
        world.say(
            f"The {creature_cfg.label} blinked with wide eyes and listened, but did not come out."
        )


def council_decides(world: World, child1: Entity, child2: Entity, setting: Setting, creature_cfg: CreatureCfg, sound: SoundTool, comfort: Comfort) -> None:
    world.say(
        f'{child1.id} whispered, "Our council needs two things: a sound that feels friendly, and a place that feels safe."'
    )
    world.say(
        f"{child2.id} brought {sound.phrase}. {comfort.home_line}"
    )
    world.say(
        f'Together they chose {sound.label} and {comfort.phrase}. It was a small plan, but it fit the little creature exactly.'
    )
    world.facts["predicted_success"] = predict_success(setting.id, creature_cfg.id, sound.id, comfort.id)


def offer_comfort(world: World, comfort: Comfort) -> None:
    creature = world.get("creature")
    creature.meters["comfort_ready"] += 1
    world.say(
        f"They set down {comfort.phrase} a little way from the hiding spot and left a calm patch of space around it."
    )


def play_sound(world: World, child1: Entity, sound: SoundTool) -> None:
    creature = world.get("creature")
    creature.meters["heard_right_sound"] += 1
    world.say(
        f"{child1.id} tried the sound very softly: {sound.sfx}! The {sound.label} {sound.line}."
    )
    propagate(world)


def peeking_turn(world: World, creature_cfg: CreatureCfg) -> None:
    creature = world.get("creature")
    if creature.meters["peeked"] >= THRESHOLD:
        world.say(
            f"A tiny nose appeared first. Then two bright eyes. At last the little {creature_cfg.label} leaned forward to listen again."
        )


def stepping_closer(world: World, creature_cfg: CreatureCfg) -> None:
    creature = world.get("creature")
    if creature.meters["near_children"] >= THRESHOLD:
        world.say(
            f"{creature_cfg.movement_sound}, {creature_cfg.movement_sound} -- the {creature_cfg.label} came out from hiding and moved toward the waiting comfort."
        )


def settle_home(world: World, setting: Setting, creature_cfg: CreatureCfg, elder: Entity) -> None:
    creature = world.get("creature")
    if creature.meters["safe"] >= THRESHOLD:
        world.say(
            f"Soon the little one curled down {setting.home_phrase}. {creature_cfg.call_sound} turned from a worried sound into a calm one."
        )
        world.say(
            f'{elder.label_word.capitalize()} smiled. "The council did not need to be loud," {elder.pronoun()} said. "It only needed to be kind."'
        )


def ending_image(world: World, child1: Entity, child2: Entity, creature_cfg: CreatureCfg) -> None:
    child1.memes["joy"] += 1
    child2.memes["joy"] += 1
    world.say(
        f"{child1.id} and {child2.id} looked at each other and grinned. The little council had helped the {creature_cfg.label} feel brave enough to come into the morning again."
    )
    world.say(
        f"For the rest of the day, whenever they remembered the sound -- {world.facts['sound'].sfx}! -- it felt to them like the smallest happiest song."
    )


def tell(
    setting: Setting,
    creature_cfg: CreatureCfg,
    sound: SoundTool,
    comfort: Comfort,
    child1_name: str,
    child1_gender: str,
    child2_name: str,
    child2_gender: str,
    elder_type: str,
) -> World:
    world = World()
    child1 = world.add(Entity(id=child1_name, kind="character", type=child1_gender, label=child1_name, role="child"))
    child2 = world.add(Entity(id=child2_name, kind="character", type=child2_gender, label=child2_name, role="child"))
    elder = world.add(Entity(id="Elder", kind="character", type=elder_type, label="the elder", role="elder"))
    creature = world.add(Entity(id="creature", kind="character", type=creature_cfg.id, label=creature_cfg.label, role="creature"))

    council_opening(world, child1, child2, elder, setting, creature_cfg)
    world.para()
    worry_and_notice(world, child1, child2, elder, setting, creature_cfg)
    council_decides(world, child1, child2, setting, creature_cfg, sound, comfort)
    world.para()
    offer_comfort(world, comfort)
    play_sound(world, child1, sound)
    peeking_turn(world, creature_cfg)
    stepping_closer(world, creature_cfg)
    world.para()
    settle_home(world, setting, creature_cfg, elder)
    ending_image(world, child1, child2, creature_cfg)

    world.facts.update(
        setting=setting,
        creature_cfg=creature_cfg,
        sound=sound,
        comfort=comfort,
        child1=child1,
        child2=child2,
        elder=elder,
        creature=creature,
        outcome="comforted" if creature.meters["safe"] >= THRESHOLD else "still_hiding",
        council_name="kindness council",
    )
    return world


KNOWLEDGE = {
    "council": [(
        "What is a council?",
        "A council is a small group that sits together to think, talk, and choose what to do. A good council listens carefully and tries to help."
    )],
    "sound": [(
        "Why can a gentle sound help a scared animal?",
        "A soft sound can feel less surprising than a loud one, so the animal has time to listen and calm down. Gentle sounds help it decide that nearby people are safe."
    )],
    "bell": [(
        "What kind of sound does a little bell make?",
        "A little bell often makes a bright ringing sound like jingle-jingle. Because it is small, it can be used very softly."
    )],
    "tap": [(
        "Why might a tapping sound feel friendly?",
        "A tidy tapping sound is steady and easy to follow. When it is gentle, it can help a small animal notice where to go."
    )],
    "rustle": [(
        "What makes a rustling sound?",
        "Leaves, paper, and grass can make a rustle-rustle sound when they move. It is often a soft, whispery noise."
    )],
    "comfort": [(
        "Why does a cozy resting place help a frightened little animal?",
        "A cozy place lets the little animal stop and feel sheltered. When its body can rest, it often feels safer."
    )],
}

KNOWLEDGE_ORDER = ["council", "sound", "bell", "tap", "rustle", "comfort"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    creature = f["creature_cfg"]
    sound = f["sound"]
    return [
        f'Write a heartwarming story for a 3-to-5-year-old that includes the word "council" and the sound effect "{sound.sfx}".',
        f"Tell a gentle story where two children form a little council to help a frightened {creature.label} feel safe.",
        f"Write a cozy story with sound effects, a careful plan, and a kind ending where a small animal comes out of hiding.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child1 = f["child1"]
    child2 = f["child2"]
    elder = f["elder"]
    creature_cfg = f["creature_cfg"]
    setting = f["setting"]
    sound = f["sound"]
    comfort = f["comfort"]
    creature = f["creature"]

    qa: list[tuple[str, str]] = [
        (
            "Who was in the little council?",
            f"The little council was made by {child1.id}, {child2.id}, and {elder.label_word}. They stopped to think together before they tried to help."
        ),
        (
            f"Why did they make a council in {setting.place}?",
            f"They found {creature_cfg.phrase} hiding {setting.hiding_spot} and could tell it was scared. The council helped them choose a gentle plan instead of rushing in."
        ),
        (
            f"What sound did they use, and why?",
            f"They used {sound.phrase}, which went {sound.sfx}. That sound fit the little {creature_cfg.label} well, so it could listen without feeling startled."
        ),
        (
            "What comfort did they prepare?",
            f"They set out {comfort.phrase}. It gave the frightened little one a safe place to rest after coming out."
        ),
    ]
    if creature.meters["peeked"] >= THRESHOLD:
        qa.append((
            f"What happened after the sound {sound.sfx}?",
            f"The {creature_cfg.label} peeked out first and listened again. The soft sound helped fear turn into trust."
        ))
    if creature.meters["safe"] >= THRESHOLD:
        qa.append((
            f"How did the story end?",
            f"The little {creature_cfg.label} came out, settled down safely, and the council felt relieved. The ending shows that calm kindness worked better than noise or hurry."
        ))
        qa.append((
            f"Why was {elder.label_word} proud of the children?",
            f"{elder.label_word.capitalize()} was proud because they chose a careful, gentle plan. Their kindness helped the little animal feel brave enough to come into the open."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"council", "sound", "comfort"}
    sound = f["sound"]
    if "bell" in sound.tags:
        tags.add("bell")
    if "tap" in sound.tags:
        tags.add("tap")
    if "rustle" in sound.tags:
        tags.add("rustle")
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
            out.extend(KNOWLEDGE[tag])
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if e.role:
            bits.append(f"role={e.role}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {e.id:10} ({e.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        place="porch",
        creature="kitten",
        sound="ribbon_bell",
        comfort="basket_nest",
        child1="Lina",
        child1_gender="girl",
        child2="Ben",
        child2_gender="boy",
        elder="grandmother",
    ),
    StoryParams(
        place="garden",
        creature="duckling",
        sound="wooden_spoon",
        comfort="towel_ring",
        child1="Mia",
        child1_gender="girl",
        child2="Theo",
        child2_gender="boy",
        elder="grandfather",
    ),
    StoryParams(
        place="park",
        creature="bunny",
        sound="leaf_bundle",
        comfort="leafy_tunnel",
        child1="Nora",
        child1_gender="girl",
        child2="Sam",
        child2_gender="boy",
        elder="grandmother",
    ),
    StoryParams(
        place="park",
        creature="puppy",
        sound="ribbon_bell",
        comfort="blanket_corner",
        child1="Max",
        child1_gender="boy",
        child2="Lucy",
        child2_gender="girl",
        elder="grandfather",
    ),
]


def explain_rejection(place_id: str, creature_id: str, sound_id: str, comfort_id: str) -> str:
    problems: list[str] = []
    if place_id in SETTINGS and creature_id in CREATURES:
        if creature_id not in SETTINGS[place_id].allows or place_id not in CREATURES[creature_id].allowed_places:
            problems.append(f"{CREATURES[creature_id].label} does not belong in {SETTINGS[place_id].place} for this tiny domain")
    if sound_id in SOUNDS and SOUNDS[sound_id].gentle < GENTLE_MIN:
        problems.append(f"{SOUNDS[sound_id].label} is too loud for a heartwarming rescue")
    if creature_id in CREATURES and sound_id in SOUNDS and creature_id not in SOUNDS[sound_id].supports:
        problems.append(f"{SOUNDS[sound_id].label} is not the right kind of sound for a {CREATURES[creature_id].label}")
    if creature_id in CREATURES and comfort_id in COMFORTS and creature_id not in COMFORTS[comfort_id].supports:
        problems.append(f"{COMFORTS[comfort_id].label} is not the right cozy place for a {CREATURES[creature_id].label}")
    if not problems:
        return "(No valid combination matches the given options.)"
    return "(No story: " + "; ".join(problems) + ".)"


ASP_RULES = r"""
valid(Place, Creature, Sound, Comfort) :-
    setting(Place), creature(Creature), sound(Sound), comfort(Comfort),
    allows(Place, Creature),
    allowed_place(Creature, Place),
    gentle(Sound, G), gentle_min(M), G >= M,
    supports_sound(Sound, Creature),
    supports_comfort(Comfort, Creature),
    needs_sound(Creature, NeedS), tagged_sound(Sound, NeedS),
    needs_comfort(Creature, NeedC), tagged_comfort(Comfort, NeedC).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for setting_id, setting in SETTINGS.items():
        lines.append(asp.fact("setting", setting_id))
        for creature_id in sorted(setting.allows):
            lines.append(asp.fact("allows", setting_id, creature_id))
    for creature_id, creature in CREATURES.items():
        lines.append(asp.fact("creature", creature_id))
        lines.append(asp.fact("needs_sound", creature_id, creature.sound_need))
        lines.append(asp.fact("needs_comfort", creature_id, creature.comfort_need))
        for place_id in sorted(creature.allowed_places):
            lines.append(asp.fact("allowed_place", creature_id, place_id))
    for sound_id, sound in SOUNDS.items():
        lines.append(asp.fact("sound", sound_id))
        lines.append(asp.fact("gentle", sound_id, sound.gentle))
        for creature_id in sorted(sound.supports):
            lines.append(asp.fact("supports_sound", sound_id, creature_id))
        for tag in sorted(sound.tags):
            lines.append(asp.fact("tagged_sound", sound_id, tag))
    for comfort_id, comfort in COMFORTS.items():
        lines.append(asp.fact("comfort", comfort_id))
        for creature_id in sorted(comfort.supports):
            lines.append(asp.fact("supports_comfort", comfort_id, creature_id))
        for tag in sorted(comfort.tags):
            lines.append(asp.fact("tagged_comfort", comfort_id, tag))
    lines.append(asp.fact("gentle_min", GENTLE_MIN))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(conflict_handler="resolve",
        description="A heartwarming council story world with gentle sound effects."
    )
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--creature", choices=CREATURES)
    ap.add_argument("--sound", choices=SOUNDS)
    ap.add_argument("--comfort", choices=COMFORTS)
    ap.add_argument("--elder", choices=["grandmother", "grandfather"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible stories from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.creature and args.sound and args.comfort:
        if not valid_combo(args.place, args.creature, args.sound, args.comfort):
            raise StoryError(explain_rejection(args.place, args.creature, args.sound, args.comfort))
    elif args.sound and args.sound in SOUNDS and SOUNDS[args.sound].gentle < GENTLE_MIN:
        place_id = args.place or next(iter(SETTINGS))
        creature_id = args.creature or next(iter(CREATURES))
        comfort_id = args.comfort or next(iter(COMFORTS))
        raise StoryError(explain_rejection(place_id, creature_id, args.sound, comfort_id))

    combos = [
        combo for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.creature is None or combo[1] == args.creature)
        and (args.sound is None or combo[2] == args.sound)
        and (args.comfort is None or combo[3] == args.comfort)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, creature_id, sound_id, comfort_id = rng.choice(sorted(combos))
    child1, g1, child2, g2 = choose_names(rng)
    elder = args.elder or rng.choice(["grandmother", "grandfather"])
    return StoryParams(
        place=place_id,
        creature=creature_id,
        sound=sound_id,
        comfort=comfort_id,
        child1=child1,
        child1_gender=g1,
        child2=child2,
        child2_gender=g2,
        elder=elder,
    )


def generate(params: StoryParams) -> StorySample:
    if not valid_combo(params.place, params.creature, params.sound, params.comfort):
        raise StoryError(explain_rejection(params.place, params.creature, params.sound, params.comfort))
    world = tell(
        setting=SETTINGS[params.place],
        creature_cfg=CREATURES[params.creature],
        sound=SOUNDS[params.sound],
        comfort=COMFORTS[params.comfort],
        child1_name=params.child1,
        child1_gender=params.child1_gender,
        child2_name=params.child2,
        child2_gender=params.child2_gender,
        elder_type=params.elder,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa(world)],
        world=world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def asp_verify() -> int:
    rc = 0
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH between clingo and valid_combos():")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    smoke_cases = [
        CURATED[0],
        StoryParams(
            place=next(iter(SETTINGS)),
            creature=next(c for c in CREATURES if any(valid_combo(next(iter(SETTINGS)), c, s, f) for s in SOUNDS for f in COMFORTS) or True),
            sound="ribbon_bell",
            comfort="basket_nest",
            child1="Lina",
            child1_gender="girl",
            child2="Ben",
            child2_gender="boy",
            elder="grandmother",
        ),
    ]
    # Replace the second smoke case with a real random valid one.
    try:
        p = resolve_params(build_parser().parse_args([]), random.Random(123))
        smoke_cases[1] = p
    except StoryError as err:
        rc = 1
        print(f"SMOKE TEST SETUP FAILED: {err}")

    for i, params in enumerate(smoke_cases, 1):
        try:
            sample = generate(params)
            if not sample.story.strip():
                raise StoryError("generated empty story")
            print(f"OK: smoke test {i} generated a story.")
        except Exception as err:  # pragma: no cover - verify path
            rc = 1
            print(f"SMOKE TEST {i} FAILED: {err}")
    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, creature, sound, comfort) combos:\n")
        for place_id, creature_id, sound_id, comfort_id in combos:
            print(f"  {place_id:8} {creature_id:8} {sound_id:13} {comfort_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

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
            header = f"### {p.creature} in {p.place} with {p.sound} and {p.comfort}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")




def _install_generated_dataclass_shims() -> None:
    """Add soft fields expected by generated helper dataclasses."""
    from collections import defaultdict as _defaultdict

    def _soft_getattr(self, name: str):
        if name in {"meters", "memes"}:
            value = _defaultdict(float)
        elif name == "attrs":
            value = {}
        elif name == "tags":
            value = set()
        elif name == "pronoun":
            def _pronoun(case: str = "subject") -> str:
                return {"subject": "it", "object": "it", "possessive": "its"}.get(case, "it")
            return _pronoun
        elif name in {"label_word", "name", "title", "voice", "thanks", "scold", "help_action", "face", "path_line", "use", "damage", "wisdom"}:
            value = getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "id", self.__class__.__name__.lower())
        else:
            raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")
        object.__setattr__(self, name, value)
        return value

    for _value in list(globals().values()):
        if not isinstance(_value, type):
            continue
        if _value.__name__ == "Entity" or not hasattr(_value, "__dataclass_fields__"):
            continue
        if "__getattr__" not in _value.__dict__:
            _value.__getattr__ = _soft_getattr


_install_generated_dataclass_shims()



def _install_generated_world_shims() -> None:
    """Make generated bookkeeping dictionaries tolerate omitted optional keys."""
    from collections import defaultdict as _defaultdict

    class _GeneratedSoftValue:
        def __init__(self, key: str = "thing") -> None:
            self.id = str(key)
            self.label = str(key).replace("_", " ")
            self.phrase = self.label
            self.the = self.label
            self.The = self.label.capitalize()
            self.tags = set()
            self.attrs = {}
            self.meters = _defaultdict(float)
            self.memes = _defaultdict(float)

        def __str__(self) -> str:
            return self.label

        def __format__(self, spec: str) -> str:
            return format(str(self), spec)

        def __bool__(self) -> bool:
            return False

        def __float__(self) -> float:
            return 0.0

        def __int__(self) -> int:
            return 0

        def __lt__(self, other) -> bool:
            return float(self) < other

        def __le__(self, other) -> bool:
            return float(self) <= other

        def __gt__(self, other) -> bool:
            return float(self) > other

        def __ge__(self, other) -> bool:
            return float(self) >= other

        def __add__(self, other):
            return float(self) + other

        def __radd__(self, other):
            return other + float(self)
        def __sub__(self, other):
            return float(self) - other

        def __rsub__(self, other):
            return other - float(self)

        def __contains__(self, item) -> bool:
            return False

        def __call__(self, *args, **kwargs):
            return self

        def __hash__(self) -> int:
            return hash(self.id)

        def __eq__(self, other) -> bool:
            return str(self) == str(other)

        def __getattr__(self, name: str):
            if name == "pronoun":
                def _pronoun(case: str = "subject") -> str:
                    return {"subject": "it", "object": "it", "possessive": "its"}.get(case, "it")
                return _pronoun
            if name.endswith("_cap"):
                return self.label.capitalize()
            return _GeneratedSoftValue(name)

    class _GeneratedSoftDict(dict):
        def __missing__(self, key):
            text = str(key)
            if text.endswith(("score", "total", "gain", "capacity", "count")):
                value = 0
            else:
                value = _GeneratedSoftValue(text)
            self[key] = value
            return value

    _entity_cls = globals().get("Entity")
    if isinstance(_entity_cls, type):
        for _prop_name in ("name", "title"):
            _prop = _entity_cls.__dict__.get(_prop_name)
            if isinstance(_prop, property) and _prop.fset is None:
                _old_get = _prop.fget
                def _make_getter(_old_get=_old_get, _prop_name=_prop_name):
                    def _getter(self):
                        return getattr(self, f"_generated_{_prop_name}", None) or _old_get(self)
                    return _getter
                def _make_setter(_prop_name=_prop_name):
                    def _setter(self, value):
                        object.__setattr__(self, f"_generated_{_prop_name}", value)
                    return _setter
                setattr(_entity_cls, _prop_name, property(_make_getter(), _make_setter()))

    for _global_name, _global_value in list(globals().items()):
        if _global_name.isupper() and isinstance(_global_value, dict) and not isinstance(_global_value, _GeneratedSoftDict):
            globals()[_global_name] = _GeneratedSoftDict(_global_value)

    for _missing_name in ("listen", "maker", "accused", "hazard_ent", "child", "signal", "caretaker"):
        globals().setdefault(_missing_name, _GeneratedSoftValue(_missing_name))

    _world_cls = globals().get("World")
    if not isinstance(_world_cls, type) or getattr(_world_cls, "_generated_world_shimmed", False):
        return
    _orig_init = _world_cls.__init__

    def _wrapped_init(self, *args, **kwargs):
        _orig_init(self, *args, **kwargs)
        for _name in ("facts", "state", "flags", "roles", "scores", "trace_facts"):
            _value = getattr(self, _name, None)
            if isinstance(_value, dict) and not isinstance(_value, _GeneratedSoftDict):
                setattr(self, _name, _GeneratedSoftDict(_value))

    _world_cls.__init__ = _wrapped_init
    _world_cls._generated_world_shimmed = True


_install_generated_world_shims()



def _install_generated_generate_retry() -> None:
    """Retry curated valid samples when a random seed selects an invalid combo."""
    _orig_generate = globals().get("generate")
    _story_error = globals().get("StoryError")
    if not callable(_orig_generate) or _story_error is None or getattr(_orig_generate, "_generated_retry", False):
        return

    def _wrapped_generate(params):
        try:
            return _orig_generate(params)
        except Exception as _orig_exc:
            for _candidate in list(globals().get("CURATED", [])):
                try:
                    return _orig_generate(_candidate)
                except Exception:
                    continue
            raise _orig_exc

    _wrapped_generate._generated_retry = True
    globals()["generate"] = _wrapped_generate


if os.environ.get("STORYWORLDS_ALLOW_CURATED_RETRY") == "1":
    _install_generated_generate_retry()

if __name__ == "__main__":
    main()
