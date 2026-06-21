#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/rind_belligerent_don_twist_inner_monologue_ghost.py
================================================================================

A small ghost-story-flavored storyworld about a child who hears a haunted sound
on an autumn night, imagines a belligerent ghost, and then discovers a harmless
twist: the "spirit" is really a bit of dried rind being moved by some ordinary
cause.

The world model tracks physical state (drafts, scratches, sounds, lantern light)
and emotional state (fear, courage, relief, trust). The prose is rendered from
that state, not from a frozen template. Every story includes:
- rind
- belligerent
- don
- Inner Monologue
- a Twist
- a ghost-story mood

Run it
------
    python storyworlds/worlds/gpt-5.4/rind_belligerent_don_twist_inner_monologue_ghost.py
    python storyworlds/worlds/gpt-5.4/rind_belligerent_don_twist_inner_monologue_ghost.py --all
    python storyworlds/worlds/gpt-5.4/rind_belligerent_don_twist_inner_monologue_ghost.py --qa
    python storyworlds/worlds/gpt-5.4/rind_belligerent_don_twist_inner_monologue_ghost.py --trace
    python storyworlds/worlds/gpt-5.4/rind_belligerent_don_twist_inner_monologue_ghost.py --verify
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
_THIS = os.path.abspath(__file__)
_WORLD_DIR = os.path.dirname(_THIS)                  # .../storyworlds/worlds/gpt-5.4
_STORYWORLDS_DIR = os.path.dirname(os.path.dirname(_WORLD_DIR))  # .../storyworlds
sys.path.insert(0, _STORYWORLDS_DIR)
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
CAUTIOUS_TRAITS = {"cautious", "careful", "gentle"}
BRAVE_TRAITS = {"bold", "curious", "steady"}


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
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
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "grandmother", "woman", "aunt"}
        male = {"boy", "father", "grandfather", "man", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {
            "grandmother": "grandma",
            "grandfather": "grandpa",
            "mother": "mom",
            "father": "dad",
        }.get(self.type, self.type)


@dataclass
class Setting:
    id: str
    place: str
    bed_spot: str
    dark_path: str
    mood: str
    features: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Source:
    id: str
    label: str
    phrase: str
    location: str
    setup: str
    sound: str
    clue: str
    motion_need: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Cause:
    id: str
    label: str
    phrase: str
    action: str
    provides: set[str] = field(default_factory=set)
    needs: set[str] = field(default_factory=set)
    reveal: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Cover:
    id: str
    label: str
    phrase: str
    warmth: str
    plural: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class Lamp:
    id: str
    label: str
    phrase: str
    glow: str
    tags: set[str] = field(default_factory=set)


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
        clone = World(self.setting)
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


def _r_noise(world: World) -> list[str]:
    out: list[str] = []
    cause = world.get("cause")
    source = world.get("source")
    room = world.get("room")
    child = world.get("child")
    if cause.meters["active"] < THRESHOLD:
        return out
    if source.attrs.get("motion_need") != cause.attrs.get("provides"):
        return out
    sig = ("noise", source.id, cause.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    source.meters["sounding"] += 1
    room.meters["spooky"] += 1
    child.memes["fear"] += 1
    out.append("__noise__")
    return out


def _r_escalate(world: World) -> list[str]:
    out: list[str] = []
    room = world.get("room")
    child = world.get("child")
    if room.meters["spooky"] < THRESHOLD:
        return out
    sig = ("escalate",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["imagination"] += 1
    out.append("__imagination__")
    return out


def _r_reveal(world: World) -> list[str]:
    out: list[str] = []
    source = world.get("source")
    child = world.get("child")
    room = world.get("room")
    if source.meters["understood"] < THRESHOLD:
        return out
    sig = ("reveal",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    room.meters["spooky"] = 0.0
    child.memes["fear"] = 0.0
    child.memes["relief"] += 1
    child.memes["wonder"] += 1
    out.append("__relief__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="noise", tag="physical", apply=_r_noise),
    Rule(name="escalate", tag="emotional", apply=_r_escalate),
    Rule(name="reveal", tag="emotional", apply=_r_reveal),
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
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for sent in produced:
            world.say(sent)
    return produced


def valid_combo(setting: Setting, source: Source, cause: Cause) -> bool:
    return cause.needs.issubset(setting.features) and source.motion_need in cause.provides


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for sid, setting in SETTINGS.items():
        for oid, source in SOURCES.items():
            for cid, cause in CAUSES.items():
                if valid_combo(setting, source, cause):
                    combos.append((sid, oid, cid))
    return combos


def plan_mode(trait: str, cause_id: str) -> str:
    if trait in CAUTIOUS_TRAITS or cause_id == "cat":
        return "wake_elder"
    return "look_first"


def initial_courage(trait: str) -> float:
    if trait in BRAVE_TRAITS:
        return 2.0
    if trait in CAUTIOUS_TRAITS:
        return 0.5
    return 1.0


def predict_noise(world: World) -> dict:
    sim = world.copy()
    sim.get("cause").meters["active"] += 1
    propagate(sim, narrate=False)
    return {
        "sound": sim.get("source").meters["sounding"] >= THRESHOLD,
        "spooky": sim.get("room").meters["spooky"] >= THRESHOLD,
        "fear": sim.get("child").memes["fear"],
    }


def introduce(world: World, child: Entity, elder: Entity, source: Source) -> None:
    world.say(
        f"On a late autumn evening, {child.id} was in {world.setting.bed_spot} at "
        f"{world.setting.place}. {world.setting.mood}"
    )
    world.say(
        f"Before bed, {elder.label_word.capitalize()} had left {source.phrase} "
        f"{source.location}. {source.setup}"
    )
    child.memes["trust"] += 1
    child.memes["calm"] += 1


def first_sound(world: World, child: Entity, source: Source, cause: Cause) -> None:
    world.get("cause").meters["active"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Then, from {source.location}, there came {source.sound}. It sounded so odd "
        f"that the dark seemed to lean closer."
    )
    world.say(
        f"{child.id} held still under the blanket and listened to it again."
    )
    world.facts["noise_pred"] = predict_noise(world)


def inner_monologue(world: World, child: Entity, source: Source) -> None:
    world.say(
        f'*That cannot be just the house,* {child.id} thought. *What if a belligerent '
        f'ghost has found the {source.label}?*'
    )
    if child.memes["fear"] > child.memes["courage"]:
        world.say(
            f'*I do not want to look,* {child.pronoun()} thought, *but listening from bed '
            f'feels even worse.*'
        )
    else:
        world.say(
            f'*If I keep hiding, the sound will only grow bigger in my head,* '
            f'{child.pronoun()} thought.'
        )


def don_cover(world: World, child: Entity, cover: Cover, lamp: Lamp) -> None:
    child.meters["bundled"] += 1
    child.memes["courage"] += 1
    world.get("lamp").meters["lit"] += 1
    world.say(
        f"So {child.id} slipped out of bed to don {cover.phrase} and picked up "
        f"{lamp.phrase}. {lamp.glow}"
    )


def wake_elder(world: World, child: Entity, elder: Entity) -> None:
    child.memes["trust"] += 1
    elder.memes["care"] += 1
    world.say(
        f"{child.id} padded across the floor and touched {elder.label_word}'s sleeve. "
        f'"There is something in the dark," {child.pronoun()} whispered.'
    )
    world.say(
        f"{elder.label_word.capitalize()} sat up at once, not cross at all, only calm and listening."
    )


def look_first(world: World, child: Entity) -> None:
    child.memes["courage"] += 1
    world.say(
        f"{child.id} took three tiny steps into {world.setting.dark_path}. Every board seemed "
        f"to know {child.pronoun("possessive")} name."
    )


def corridor_beat(world: World, child: Entity, elder: Entity, mode: str) -> None:
    if mode == "wake_elder":
        world.say(
            f"Together they followed the sound, slow and careful, while the little light "
            f"made the walls look less haunted."
        )
    else:
        world.say(
            f"The sound came once more, and {child.id}'s knees nearly turned to paper. "
            f"Just then {elder.label_word} called softly from behind, asking why a lamp was awake."
        )
        world.say(
            f"{child.id} pointed toward the dark instead of answering, and {elder.label_word} came along."
        )


def reveal_truth(world: World, child: Entity, elder: Entity, source: Source, cause: Cause) -> None:
    source_ent = world.get("source")
    source_ent.meters["understood"] += 1
    propagate(world, narrate=False)
    world.say(
        f"At {source.location}, the twist was plain at last: there was no ghost at all. "
        f"{cause.reveal}."
    )
    world.say(
        f"The strange sound had only been {source.phrase} making {source.clue}."
    )
    world.say(
        f'{elder.label_word.capitalize()} smiled. "A noisy house can borrow a ghost face for a minute," '
        f'{elder.pronoun()} said, "but it is still only a house."'
    )


def ending(world: World, child: Entity, source: Source, cover: Cover, lamp: Lamp) -> None:
    child.memes["warmth"] += 1
    world.say(
        f"{child.id} let out a long breath and laughed at last. The fear went out of the night as "
        f"quickly as it had come."
    )
    world.say(
        f"When {child.pronoun()} went back to bed, {lamp.label} left a soft gold line on "
        f"{cover.label}, and {source.phrase} no longer sounded haunted at all."
    )


def tell(
    setting: Setting,
    source: Source,
    cause: Cause,
    cover: Cover,
    lamp: Lamp,
    child_name: str = "Mira",
    child_type: str = "girl",
    elder_type: str = "grandmother",
    elder_name: str = "Elder",
    trait: str = "careful",
) -> World:
    world = World(setting)
    child = world.add(
        Entity(
            id=child_name,
            kind="character",
            type=child_type,
            role="child",
            traits=[trait],
        )
    )
    elder = world.add(
        Entity(
            id=elder_name,
            kind="character",
            type=elder_type,
            role="elder",
            label="the elder",
        )
    )
    room = world.add(Entity(id="room", kind="thing", type="room", label="the room"))
    source_ent = world.add(
        Entity(
            id="source",
            kind="thing",
            type="source",
            label=source.label,
            phrase=source.phrase,
            attrs={"motion_need": source.motion_need},
            tags=set(source.tags),
        )
    )
    cause_ent = world.add(
        Entity(
            id="cause",
            kind="thing",
            type="cause",
            label=cause.label,
            phrase=cause.phrase,
            attrs={"provides": source.motion_need},
            tags=set(cause.tags),
        )
    )
    world.add(Entity(id="cover", kind="thing", type="cover", label=cover.label, phrase=cover.phrase))
    world.add(Entity(id="lamp", kind="thing", type="lamp", label=lamp.label, phrase=lamp.phrase))

    child.memes["courage"] = initial_courage(trait)
    child.memes["fear"] = 0.0
    child.memes["imagination"] = 0.0

    introduce(world, child, elder, source)

    world.para()
    first_sound(world, child, source, cause)
    inner_monologue(world, child, source)
    don_cover(world, child, cover, lamp)

    mode = plan_mode(trait, cause.id)
    world.para()
    if mode == "wake_elder":
        wake_elder(world, child, elder)
    else:
        look_first(world, child)
    corridor_beat(world, child, elder, mode)

    world.para()
    reveal_truth(world, child, elder, source, cause)
    ending(world, child, source, cover, lamp)

    world.facts.update(
        child=child,
        elder=elder,
        room=room,
        setting=setting,
        source_cfg=source,
        source=source_ent,
        cause_cfg=cause,
        cause=cause_ent,
        cover=COVERS[cover.id],
        lamp=LAMPS[lamp.id],
        trait=trait,
        mode=mode,
    )
    return world


SETTINGS = {
    "cottage": Setting(
        id="cottage",
        place="a little orchard cottage",
        bed_spot="a narrow bedroom under the eaves",
        dark_path="the crooked upstairs hall",
        mood="The windows held moonlight, and the whole place smelled faintly of apples and cold wood.",
        features={"draft"},
        tags={"house", "night"},
    ),
    "farmhouse": Setting(
        id="farmhouse",
        place="an old farmhouse by the pumpkin field",
        bed_spot="a loft room with a patchwork quilt",
        dark_path="the stair landing above the kitchen",
        mood="Downstairs, the beams gave small creaks as if the house were talking in its sleep.",
        features={"draft", "porch"},
        tags={"house", "night"},
    ),
    "manor": Setting(
        id="manor",
        place="a sleepy manor at the edge of town",
        bed_spot="a room beside a long wallpapered corridor",
        dark_path="the long corridor with its faded portraits",
        mood="Shadows lay in the corners like folded velvet, and every tick of the clock sounded far away.",
        features={"draft", "cat"},
        tags={"house", "night"},
    ),
    "attic_house": Setting(
        id="attic_house",
        place="a tall house with a windy attic",
        bed_spot="a snug attic bed under a sloping roof",
        dark_path="the back stairs above the pantry",
        mood="The rafters sighed softly, and the night pressed against the roof like a listening ear.",
        features={"draft", "cat"},
        tags={"house", "night"},
    ),
}

SOURCES = {
    "orange_bell": Source(
        id="orange_bell",
        label="orange-rind bell-string",
        phrase="a string of dried orange rind with a tiny brass bell",
        location="above the kitchen window",
        setup="Grandma said the rind made the room smell bright even after the fruit was gone.",
        sound="a thin cling-cling followed by a dry papery scrape",
        clue="its own soft little bell-song",
        motion_need="sway",
        tags={"rind", "bell", "orange"},
    ),
    "pumpkin_mask": Source(
        id="pumpkin_mask",
        label="pumpkin-rind mask",
        phrase="a small pumpkin-rind mask with spoon eyes",
        location="on the back porch hook",
        setup="In daylight it looked silly, but in moonlight its cut mouth seemed ready to whisper.",
        sound="a hollow clack and a tiny shiver of metal",
        clue="that thin porch clatter",
        motion_need="sway",
        tags={"rind", "pumpkin", "porch"},
    ),
    "lemon_basket": Source(
        id="lemon_basket",
        label="lemon-rind basket",
        phrase="a basket of curled lemon rind",
        location="beside the pantry door",
        setup="The pieces had dried into crisp yellow curls that could whisper against wicker.",
        sound="a hush-hush rustle with one sudden tap",
        clue="a papery rustle against the basket",
        motion_need="scratch",
        tags={"rind", "lemon", "pantry"},
    ),
}

CAUSES = {
    "wind": Cause(
        id="wind",
        label="wind",
        phrase="the night wind",
        action="nudged",
        provides={"sway"},
        needs={"draft"},
        reveal="The night wind was slipping through the crack of the window and nudging it back and forth",
        tags={"wind", "night"},
    ),
    "cat": Cause(
        id="cat",
        label="cat",
        phrase="the house cat",
        action="batting",
        provides={"scratch"},
        needs={"cat"},
        reveal="The house cat was there on the floor, batting at the basket with one very busy paw",
        tags={"cat", "night"},
    ),
    "porch_wind": Cause(
        id="porch_wind",
        label="porch wind",
        phrase="the porch wind",
        action="rocking",
        provides={"sway"},
        needs={"porch"},
        reveal="A little porch wind was rocking it gently on its hook",
        tags={"wind", "porch", "night"},
    ),
}

COVERS = {
    "shawl": Cover(
        id="shawl",
        label="shawl",
        phrase="a wool shawl",
        warmth="soft and warm",
        tags={"clothes"},
    ),
    "robe": Cover(
        id="robe",
        label="robe",
        phrase="a thick night robe",
        warmth="heavy and warm",
        tags={"clothes"},
    ),
    "coat": Cover(
        id="coat",
        label="coat",
        phrase="a little blue coat",
        warmth="snug and warm",
        tags={"clothes"},
    ),
}

LAMPS = {
    "lantern": Lamp(
        id="lantern",
        label="lantern",
        phrase="a tin lantern",
        glow="Its yellow light shook a little in her hand.",
        tags={"light"},
    ),
    "candle_lamp": Lamp(
        id="candle_lamp",
        label="candle lamp",
        phrase="a glass candle lamp",
        glow="The small flame made a brave, steady circle in the dark.",
        tags={"light"},
    ),
    "flashlight": Lamp(
        id="flashlight",
        label="flashlight",
        phrase="a flashlight",
        glow="A neat white beam opened a path through the shadows.",
        tags={"light"},
    ),
}

GIRL_NAMES = ["Mira", "Nora", "Elsie", "Ada", "Wren", "Ivy"]
BOY_NAMES = ["Jon", "Theo", "Bram", "Hugo", "Eli", "Milo"]
TRAITS = ["careful", "cautious", "gentle", "curious", "bold", "steady"]


@dataclass
class StoryParams:
    setting: str
    source: str
    cause: str
    cover: str
    lamp: str
    child_name: str
    child_type: str
    elder_type: str
    trait: str
    seed: Optional[int] = None


CURATED = [
    StoryParams(
        setting="cottage",
        source="orange_bell",
        cause="wind",
        cover="shawl",
        lamp="lantern",
        child_name="Mira",
        child_type="girl",
        elder_type="grandmother",
        trait="careful",
    ),
    StoryParams(
        setting="farmhouse",
        source="pumpkin_mask",
        cause="porch_wind",
        cover="robe",
        lamp="candle_lamp",
        child_name="Theo",
        child_type="boy",
        elder_type="grandfather",
        trait="bold",
    ),
    StoryParams(
        setting="manor",
        source="lemon_basket",
        cause="cat",
        cover="coat",
        lamp="flashlight",
        child_name="Nora",
        child_type="girl",
        elder_type="grandmother",
        trait="gentle",
    ),
    StoryParams(
        setting="attic_house",
        source="orange_bell",
        cause="wind",
        cover="robe",
        lamp="flashlight",
        child_name="Bram",
        child_type="boy",
        elder_type="grandfather",
        trait="steady",
    ),
]


KNOWLEDGE = {
    "rind": [
        (
            "What is rind?",
            "Rind is the outer skin or peel of some fruits and vegetables. When it dries, it can turn light and papery.",
        )
    ],
    "wind": [
        (
            "Why can wind make strange sounds at night?",
            "Wind can push loose things, tap windows, and whistle through cracks. In the dark, ordinary sounds can seem much bigger and stranger.",
        )
    ],
    "cat": [
        (
            "Why do cats make little noises in the house at night?",
            "Cats often prowl, bat at things, and squeeze into small places when the house is quiet. Their paws and whiskers can turn tiny movements into surprising sounds.",
        )
    ],
    "lantern": [
        (
            "What does a lantern do?",
            "A lantern makes a small steady light you can carry. That helps people see shapes clearly instead of guessing in the dark.",
        )
    ],
    "ghost": [
        (
            "Why can a dark room feel haunted even when nothing dangerous is there?",
            "When you cannot see clearly, your mind may fill in the missing parts with scary ideas. A better look often turns the mystery back into an ordinary thing.",
        )
    ],
}


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    source = f["source_cfg"]
    cause = f["cause_cfg"]
    setting = f["setting"]
    return [
        f'Write a short ghost story for a 3-to-5-year-old that includes the words "rind", "belligerent", and "don".',
        f"Tell a gentle spooky story where {child.id} hears a ghostly noise at {setting.place}, imagines a belligerent ghost in an inner monologue, and learns the sound came from {source.phrase}.",
        f"Write a twist ending story in which a child dons warm clothes, follows a mysterious sound, and discovers that {cause.phrase} was only moving {source.phrase}.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    elder = f["elder"]
    source = f["source_cfg"]
    cause = f["cause_cfg"]
    mode = f["mode"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id}, a child who heard a strange sound in the night, and {elder.label_word} who helped make sense of it.",
        ),
        (
            "What made the night feel scary at first?",
            f"The sound from {source.location} seemed ghostly because it came through the dark before {child.id} could see what was making it. That let fear and imagination grow faster than the facts.",
        ),
        (
            f"What did {child.id} think was happening?",
            f"{child.id} imagined that a belligerent ghost might have found the {source.label}. That thought came from the inner monologue, not from anything truly supernatural.",
        ),
        (
            f"Why did {child.id} don {f['cover'].phrase} and carry {f['lamp'].phrase}?",
            f"{child.pronoun('subject').capitalize()} wanted warmth and enough light to face the noise. The extra light helped turn a guessed danger into something real and understandable.",
        ),
    ]
    if mode == "wake_elder":
        qa.append(
            (
                f"Did {child.id} go alone?",
                f"No. {child.id} woke {elder.label_word} first because the sound felt too strange to face alone. Trusting a calm grown-up helped the fear shrink before the truth was even found.",
            )
        )
    else:
        qa.append(
            (
                f"Did {child.id} go alone?",
                f"{child.id} looked first and then {elder.label_word} joined in. That shows {child.pronoun('subject')} was frightened but also brave enough to take the first steps.",
            )
        )
    qa.append(
        (
            "What was the twist?",
            f"The twist was that there was no ghost at all. {cause.reveal}, and that simple movement made the eerie sound.",
        )
    )
    qa.append(
        (
            "How did the story end?",
            f"It ended with relief instead of terror. Once {child.id} understood the noise, the same night seemed gentle again, and the room no longer felt haunted.",
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags: set[str] = {"rind", "ghost"}
    tags |= set(world.facts["cause_cfg"].tags)
    if "light" in world.facts["lamp"].tags:
        tags.add("lantern")
    out: list[tuple[str, str]] = []
    for key in ["rind", "wind", "cat", "lantern", "ghost"]:
        if key in tags and key in KNOWLEDGE:
            out.extend(KNOWLEDGE[key])
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
    for ent in list(world.entities.values()):
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {ent.id:8} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


def explain_rejection(setting: Setting, source: Source, cause: Cause) -> str:
    if not cause.needs.issubset(setting.features):
        missing = sorted(cause.needs - setting.features)
        return (
            f"(No story: {setting.place} lacks the feature(s) {missing} needed for {cause.label}. "
            f"Without that cause, the ghostly sound would never start.)"
        )
    if source.motion_need not in cause.provides:
        return (
            f"(No story: {cause.label} does not make the kind of motion needed for {source.label}. "
            f"This world only tells mysteries whose sounds can really happen.)"
        )
    return "(No story: that combination does not make a reasonable haunting.)"


ASP_RULES = r"""
valid(S, O, C) :- setting(S), source(O), cause(C), cause_ok(S, C), motion_match(O, C).

look_first :- trait(T), brave_trait(T), chosen_cause(C), C != cat.
wake_elder :- trait(T), cautious_trait(T).
wake_elder :- chosen_cause(cat).
wake_elder :- not look_first.
plan(look_first) :- look_first, not wake_elder.
plan(wake_elder) :- wake_elder.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for feat in sorted(setting.features):
            lines.append(asp.fact("feature", sid, feat))
    for oid, source in SOURCES.items():
        lines.append(asp.fact("source", oid))
        lines.append(asp.fact("needs_motion", oid, source.motion_need))
    for cid, cause in CAUSES.items():
        lines.append(asp.fact("cause", cid))
        for need in sorted(cause.needs):
            lines.append(asp.fact("needs_feature", cid, need))
        for prov in sorted(cause.provides):
            lines.append(asp.fact("provides_motion", cid, prov))
    for sid, setting in SETTINGS.items():
        for cid, cause in CAUSES.items():
            if cause.needs.issubset(setting.features):
                lines.append(asp.fact("cause_ok", sid, cid))
    for oid, source in SOURCES.items():
        for cid, cause in CAUSES.items():
            if source.motion_need in cause.provides:
                lines.append(asp.fact("motion_match", oid, cid))
    for trait in sorted(BRAVE_TRAITS):
        lines.append(asp.fact("brave_trait", trait))
    for trait in sorted(CAUTIOUS_TRAITS):
        lines.append(asp.fact("cautious_trait", trait))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_plan(trait: str, cause_id: str) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("trait", trait),
            asp.fact("chosen_cause", cause_id),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show plan/1."))
    atoms = asp.atoms(model, "plan")
    return atoms[0][0] if atoms else "?"


def _smoke_emit(sample: StorySample) -> None:
    if not sample.story.strip():
        raise StoryError("Smoke test failed: generated empty story.")
    if "rind" not in sample.story.lower():
        raise StoryError("Smoke test failed: story omitted required seed word 'rind'.")
    if "belligerent" not in sample.story.lower():
        raise StoryError("Smoke test failed: story omitted required seed word 'belligerent'.")
    if " don " not in f" {sample.story.lower()} ":
        raise StoryError("Smoke test failed: story omitted required seed word 'don'.")


def asp_verify() -> int:
    rc = 0
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: ASP gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if clingo_set - python_set:
            print("  only in asp:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    cases = list(CURATED)
    for seed in range(30):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
            cases.append(params)
        except StoryError:
            continue
    bad = 0
    for params in cases:
        py = plan_mode(params.trait, params.cause)
        asp_res = asp_plan(params.trait, params.cause)
        if py != asp_res:
            bad += 1
    if bad == 0:
        print(f"OK: ASP plan matches Python plan on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} plan outcomes differ.")

    try:
        sample = generate(CURATED[0])
        _smoke_emit(sample)
        print("OK: smoke-test story generation succeeded.")
    except Exception as err:  # pragma: no cover - verification path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(conflict_handler="resolve",
        description="Ghost-story storyworld: a child hears a haunted sound and finds a harmless twist."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--source", choices=SOURCES)
    ap.add_argument("--cause", choices=CAUSES)
    ap.add_argument("--cover", choices=COVERS)
    ap.add_argument("--lamp", choices=LAMPS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--elder", choices=["grandmother", "grandfather"])
    ap.add_argument("--name")
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible ASP-derived combos")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.setting and args.source and args.cause:
        if not valid_combo(SETTINGS[args.setting], SOURCES[args.source], CAUSES[args.cause]):
            raise StoryError(explain_rejection(SETTINGS[args.setting], SOURCES[args.source], CAUSES[args.cause]))

    combos = [
        combo
        for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.source is None or combo[1] == args.source)
        and (args.cause is None or combo[2] == args.cause)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, source_id, cause_id = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    elder = args.elder or rng.choice(["grandmother", "grandfather"])
    cover = args.cover or rng.choice(sorted(COVERS))
    lamp = args.lamp or rng.choice(sorted(LAMPS))
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(
        setting=setting_id,
        source=source_id,
        cause=cause_id,
        cover=cover,
        lamp=lamp,
        child_name=name,
        child_type=gender,
        elder_type=elder,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError(f"(Unknown setting: {params.setting})")
    if params.source not in SOURCES:
        raise StoryError(f"(Unknown source: {params.source})")
    if params.cause not in CAUSES:
        raise StoryError(f"(Unknown cause: {params.cause})")
    if params.cover not in COVERS:
        raise StoryError(f"(Unknown cover: {params.cover})")
    if params.lamp not in LAMPS:
        raise StoryError(f"(Unknown lamp: {params.lamp})")
    if not valid_combo(SETTINGS[params.setting], SOURCES[params.source], CAUSES[params.cause]):
        raise StoryError(
            explain_rejection(SETTINGS[params.setting], SOURCES[params.source], CAUSES[params.cause])
        )

    world = tell(
        setting=SETTINGS[params.setting],
        source=SOURCES[params.source],
        cause=CAUSES[params.cause],
        cover=COVERS[params.cover],
        lamp=LAMPS[params.lamp],
        child_name=params.child_name,
        child_type=params.child_type,
        elder_type=params.elder_type,
        elder_name="Elder",
        trait=params.trait,
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/3.\n#show plan/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, source, cause) combos:\n")
        for setting_id, source_id, cause_id in combos:
            print(f"  {setting_id:12} {source_id:13} {cause_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.child_name}: {p.source} by {p.cause} at {p.setting}"
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
