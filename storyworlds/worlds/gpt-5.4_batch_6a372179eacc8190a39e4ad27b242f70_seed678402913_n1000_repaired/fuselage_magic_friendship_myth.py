#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/fuselage_magic_friendship_myth.py
============================================================

A small myth-flavored storyworld about a child and a magical friend who find the
fallen fuselage of a sky-boat. They cannot mend it with ordinary hands alone.
Only the right kind of magic, offered through friendship, can make the vessel
whole again.

The world model is intentionally narrow and concrete:

- a realm where a broken sky-boat has fallen
- a specific kind of damage on its fuselage
- a magical repair gift that may or may not fit that damage
- a magical friend who may or may not be able to give that gift

Reasonableness comes first. The story refuses combinations where the chosen
magic does not actually mend the chosen damage, where the realm cannot plausibly
hold that magic, or where the friend cannot offer it. The prose is driven by
world state: fear rises when the boat is found broken, hope rises when the
friend shares true help, and the ending image depends on whether the repaired
craft can fly again.

Run it
------
python storyworlds/worlds/gpt-5.4/fuselage_magic_friendship_myth.py
python storyworlds/worlds/gpt-5.4/fuselage_magic_friendship_myth.py --realm reed_sea --damage split_seam --magic moon_thread --friend owl
python storyworlds/worlds/gpt-5.4/fuselage_magic_friendship_myth.py --magic cloud_cloth --damage bent_frame
python storyworlds/worlds/gpt-5.4/fuselage_magic_friendship_myth.py --all
python storyworlds/worlds/gpt-5.4/fuselage_magic_friendship_myth.py -n 5 --seed 7 --qa
python storyworlds/worlds/gpt-5.4/fuselage_magic_friendship_myth.py --verify
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother"}
        male = {"boy", "man", "father"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class Realm:
    id: str
    place: str
    sky: str
    floor: str
    omen: str
    launch: str
    available_magic: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Damage:
    id: str
    label: str
    phrase: str
    wound_line: str
    need: str
    severity: int
    tags: set[str] = field(default_factory=set)


@dataclass
class MagicGift:
    id: str
    label: str
    phrase: str
    repair_verb: str
    glow: str
    repairs: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class FriendKind:
    id: str
    label: str
    phrase: str
    entrance: str
    gift_line: str
    gives: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
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


def compatible(realm: Realm, damage: Damage, magic: MagicGift, friend: FriendKind) -> bool:
    return (
        damage.id in magic.repairs
        and magic.id in realm.available_magic
        and magic.id in friend.gives
    )


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for realm_id, realm in REALMS.items():
        for damage_id, damage in DAMAGES.items():
            for magic_id, magic in MAGICS.items():
                for friend_id, friend in FRIENDS.items():
                    if compatible(realm, damage, magic, friend):
                        combos.append((realm_id, damage_id, magic_id, friend_id))
    return combos


def explain_rejection(realm: Realm, damage: Damage, magic: MagicGift, friend: FriendKind) -> str:
    if damage.id not in magic.repairs:
        return (
            f"(No story: {magic.label} does not mend {damage.phrase}. "
            f"The repair must fit the wound on the fuselage.)"
        )
    if magic.id not in realm.available_magic:
        return (
            f"(No story: {magic.label} does not belong in {realm.place}. "
            f"Choose magic the realm can plausibly hold.)"
        )
    if magic.id not in friend.gives:
        return (
            f"(No story: the {friend.label} cannot offer {magic.label}. "
            f"The magical friend must actually be able to share the needed gift.)"
        )
    return "(No story: that combination is not reasonable in this world.)"


def propagate(world: World) -> None:
    craft = world.get("craft")
    hero = world.get("hero")
    friend = world.get("friend")

    if craft.meters["broken"] >= THRESHOLD and ("fear",) not in world.fired:
        world.fired.add(("fear",))
        hero.memes["fear"] += 1
        friend.memes["care"] += 1

    if craft.meters["mended"] >= THRESHOLD and ("relief",) not in world.fired:
        world.fired.add(("relief",))
        hero.memes["fear"] = 0.0
        hero.memes["hope"] += 1
        friend.memes["joy"] += 1

    if (
        craft.meters["mended"] >= THRESHOLD
        and hero.memes["friendship"] >= THRESHOLD
        and friend.memes["friendship"] >= THRESHOLD
        and ("flight",) not in world.fired
    ):
        world.fired.add(("flight",))
        craft.meters["flying"] += 1
        craft.meters["glowing"] += 1


def introduce(world: World, realm: Realm, hero: Entity) -> None:
    world.say(
        f"In the elder days, when dawn still listened to children, {hero.id} walked through {realm.place}. "
        f"Above {hero.pronoun('object')}, {realm.sky}. Underfoot, {realm.floor}."
    )
    world.say(
        f"{hero.id} had a heart that leaned toward wonders, and {realm.omen}."
    )


def find_fuselage(world: World, hero: Entity, realm: Realm, damage: Damage) -> None:
    craft = world.get("craft")
    craft.meters["broken"] += 1
    craft.meters["grounded"] += 1
    craft.meters["severity"] = float(damage.severity)
    propagate(world)
    world.say(
        f"Near a ring of old stones, {hero.id} found the fallen fuselage of a sky-boat. "
        f"It was shaped like a silver fish and quiet as a sleeping bell."
    )
    world.say(
        f"But {damage.wound_line}, and because of that wound the vessel could not rise back into the sky."
    )


def try_alone(world: World, hero: Entity, damage: Damage) -> None:
    hero.memes["effort"] += 1
    world.say(
        f"{hero.id} laid both hands on the hurt place and tried to help with courage alone, "
        f"but {damage.need}. The sky-boat only gave a small, sad shiver."
    )


def meet_friend(world: World, hero: Entity, friend_kind: FriendKind) -> None:
    friend = world.get("friend")
    hero.memes["wonder"] += 1
    friend.memes["friendship"] += 1
    world.say(
        f"Then {friend_kind.entrance}. It was {friend.phrase}, and its eyes were bright with old kindness."
    )
    world.say(
        f'"No one lifts a sky-boat alone," said the {friend_kind.label}. "{friend_kind.gift_line}"'
    )


def offer_magic(world: World, hero: Entity, friend_kind: FriendKind, magic: MagicGift) -> None:
    friend = world.get("friend")
    hero.memes["friendship"] += 1
    friend.memes["friendship"] += 1
    hero.memes["trust"] += 1
    friend.memes["trust"] += 1
    world.say(
        f"The {friend_kind.label} placed {magic.phrase} in {hero.id}'s hands. "
        f"It felt cool and alive, as if moonlight had learned how to breathe."
    )
    world.say(
        f"{hero.id} thanked the creature by name, and the thanks itself seemed to make the gift shine more brightly."
    )


def mend(world: World, damage: Damage, magic: MagicGift) -> None:
    craft = world.get("craft")
    craft.meters["broken"] = 0.0
    craft.meters["grounded"] = 0.0
    craft.meters["mended"] += 1
    propagate(world)
    world.say(
        f"Together they {magic.repair_verb} over {damage.phrase}. "
        f"At once {magic.glow}, and the hurt place drew itself closed."
    )
    world.say(
        f"The fuselage gave a soft singing sound, as though it remembered its own true shape."
    )


def launch(world: World, realm: Realm, hero: Entity, friend_kind: FriendKind) -> None:
    craft = world.get("craft")
    propagate(world)
    if craft.meters["flying"] < THRESHOLD:
        raise StoryError("(Story bug: the sky-boat was mended but never gained flight.)")
    world.say(
        f"Then the sky-boat lifted from the earth as lightly as a heron taking one bright step into morning. "
        f"{realm.launch}"
    )
    world.say(
        f"{hero.id} and the {friend_kind.label} stood shoulder to wing beside it, and each saw the other shining in the silver skin."
    )
    world.say(
        f"From that day on, people said the path between earth and sky opens fastest for friends who mend what neither could mend alone."
    )


REALMS = {
    "reed_sea": Realm(
        id="reed_sea",
        place="the Reed Sea, where the marsh shone like a green mirror",
        sky="the clouds drifted low enough to brush the tops of the reeds",
        floor="black water held little stars from the night before",
        omen="the wind kept bending the reeds toward a single hidden place",
        launch="It skimmed above the reeds, scattering drops that flashed like pearls.",
        available_magic={"moon_thread", "cloud_cloth"},
        tags={"marsh", "sky"},
    ),
    "sun_peak": Realm(
        id="sun_peak",
        place="Sun Peak, the mountain that keeps the first fire of morning",
        sky="eagles wheeled through saffron light",
        floor="the stones were warm with ancient sun",
        omen="a golden echo rolled between the cliffs as if calling for help",
        launch="It rose along the cliff-face and turned the whole peak rosy gold.",
        available_magic={"sun_sap", "star_resin"},
        tags={"mountain", "sun"},
    ),
    "cedar_hollow": Realm(
        id="cedar_hollow",
        place="Cedar Hollow, where old trees whisper to the moon",
        sky="the branches opened in a round window above the clearing",
        floor="cedar needles made a soft red-brown carpet",
        omen="even the shy birds had gone quiet around one silver gleam",
        launch="It threaded between the cedar crowns and left a silver trail in the dusk.",
        available_magic={"star_resin", "cloud_cloth"},
        tags={"forest", "moon"},
    ),
}

DAMAGES = {
    "split_seam": Damage(
        id="split_seam",
        label="split seam",
        phrase="a long split seam along its side",
        wound_line="a long seam had burst open from nose to tail",
        need="the torn edges had to be drawn together with something finer than rope",
        severity=1,
        tags={"tear"},
    ),
    "torn_skin": Damage(
        id="torn_skin",
        label="torn skin",
        phrase="a torn place in its silver skin",
        wound_line="a wide flap of silver skin had been ripped back by storm-wind",
        need="the open patch had to be covered with something light enough for the sky",
        severity=2,
        tags={"patch"},
    ),
    "bent_frame": Damage(
        id="bent_frame",
        label="bent frame",
        phrase="a bent rib in its frame",
        wound_line="one shining rib of the frame had been bent inward like a broken branch",
        need="the hidden strength of the hull had to be made straight and strong again",
        severity=3,
        tags={"frame"},
    ),
}

MAGICS = {
    "moon_thread": MagicGift(
        id="moon_thread",
        label="moon thread",
        phrase="a coil of moon thread",
        repair_verb="wound the moon thread",
        glow="a white line of light ran along the seam like a tiny river",
        repairs={"split_seam"},
        tags={"moon_thread", "magic"},
    ),
    "cloud_cloth": MagicGift(
        id="cloud_cloth",
        label="cloud cloth",
        phrase="a folded sheet of cloud cloth",
        repair_verb="smoothed the cloud cloth",
        glow="soft pearl light spread across the patch and settled there",
        repairs={"torn_skin"},
        tags={"cloud_cloth", "magic"},
    ),
    "sun_sap": MagicGift(
        id="sun_sap",
        label="sun sap",
        phrase="a drop of sun sap in a leaf-cup",
        repair_verb="brushed the sun sap",
        glow="gold warmth moved through the hurt beam until the metal stood straight again",
        repairs={"bent_frame"},
        tags={"sun_sap", "magic"},
    ),
    "star_resin": MagicGift(
        id="star_resin",
        label="star resin",
        phrase="a bead of star resin",
        repair_verb="pressed the star resin",
        glow="silver sparks danced through the wound and bound it with a clear, strong gleam",
        repairs={"split_seam", "bent_frame"},
        tags={"star_resin", "magic"},
    ),
}

FRIENDS = {
    "owl": FriendKind(
        id="owl",
        label="owl",
        phrase="an owl with moonlit feathers",
        entrance="a hush passed over the reeds, and an owl drifted down without a sound",
        gift_line="I carry thread stolen from the hems of the moon",
        gives={"moon_thread"},
        tags={"owl", "friend"},
    ),
    "crane": FriendKind(
        id="crane",
        label="crane",
        phrase="a crane taller than a child and pale as mist",
        entrance="from the shining water stepped a crane, each footfall making rings of light",
        gift_line="I know how to lay a cloud where a storm has torn the sky",
        gives={"cloud_cloth"},
        tags={"crane", "friend"},
    ),
    "fox": FriendKind(
        id="fox",
        label="fox",
        phrase="a fox whose tail held embers instead of fur at the tip",
        entrance="from between the stones came a fox, light-footed and bright-eyed",
        gift_line="I keep the warmth that straightens what night has twisted",
        gives={"sun_sap", "star_resin"},
        tags={"fox", "friend"},
    ),
    "otter": FriendKind(
        id="otter",
        label="otter",
        phrase="an otter wearing a necklace of river-shells",
        entrance="the water laughed at the bank, and an otter climbed out carrying silver drops on its whiskers",
        gift_line="The river teaches me both stitching and patching when boats come home hurt",
        gives={"moon_thread", "cloud_cloth"},
        tags={"otter", "friend"},
    ),
}

GIRL_NAMES = ["Iris", "Nella", "Mira", "Tala", "Runa", "Lyra", "Anya", "Dara"]
BOY_NAMES = ["Orin", "Tarin", "Leo", "Soren", "Milo", "Arin", "Cael", "Niko"]
TRAITS = ["gentle", "brave", "patient", "curious", "kind", "steady"]


@dataclass
class StoryParams:
    realm: str
    damage: str
    magic: str
    friend: str
    hero_name: str
    hero_gender: str
    hero_trait: str
    seed: Optional[int] = None


def tell(realm: Realm, damage: Damage, magic: MagicGift, friend_kind: FriendKind,
         hero_name: str, hero_gender: str, hero_trait: str) -> World:
    world = World()
    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type=hero_gender,
        label=hero_name,
        phrase=hero_name,
        role="hero",
        attrs={"trait": hero_trait},
        tags={"hero"},
    ))
    friend = world.add(Entity(
        id="Friend",
        kind="character",
        type="creature",
        label=friend_kind.label,
        phrase=friend_kind.phrase,
        role="friend",
        tags=set(friend_kind.tags),
    ))
    craft = world.add(Entity(
        id="craft",
        kind="thing",
        type="sky_boat",
        label="sky-boat",
        phrase="the fallen sky-boat",
        role="craft",
        tags={"fuselage", "boat"},
    ))

    world.facts["trait"] = hero_trait

    introduce(world, realm, hero)
    world.para()
    find_fuselage(world, hero, realm, damage)
    try_alone(world, hero, damage)
    world.para()
    meet_friend(world, hero, friend_kind)
    offer_magic(world, hero, friend_kind, magic)
    mend(world, damage, magic)
    world.para()
    launch(world, realm, hero, friend_kind)

    world.facts.update(
        realm=realm,
        damage=damage,
        magic=magic,
        friend_kind=friend_kind,
        hero=hero,
        friend=friend,
        craft=craft,
        success=craft.meters["flying"] >= THRESHOLD,
    )
    return world


KNOWLEDGE = {
    "fuselage": [
        (
            "What is a fuselage?",
            "A fuselage is the main body of a flying craft. It is the long middle part that holds the shape together."
        )
    ],
    "magic": [
        (
            "What does magic mean in a story?",
            "Magic in a story is a power that can do unusual things beyond ordinary life. In myths, it often works best when it follows a deeper truth, like courage or kindness."
        )
    ],
    "friendship": [
        (
            "Why can friendship matter in a myth?",
            "Friendship matters in myths because great tasks are often too hard for one person alone. A true friend brings help, trust, and courage at the right moment."
        )
    ],
    "owl": [
        (
            "Why are owls sometimes magical in stories?",
            "Owls are often linked with night, quiet, and hidden wisdom. That makes them feel like creatures who notice secrets other beings miss."
        )
    ],
    "crane": [
        (
            "Why might a crane belong in a myth?",
            "A crane looks graceful and patient, so myths often use it as a sign of balance, travel, or messages between places."
        )
    ],
    "fox": [
        (
            "Why is a fox a common magical helper in stories?",
            "A fox often feels clever, quick, and watchful. In stories, that makes it a good helper when a problem needs both wit and courage."
        )
    ],
    "otter": [
        (
            "Why does an otter fit a water-side myth?",
            "An otter belongs near rivers and marshes, where it moves easily through water. That makes it feel at home in a story about shining pools and hidden gifts."
        )
    ],
    "moon_thread": [
        (
            "What kind of magic might moon thread have?",
            "Moon thread sounds like a magical thread made from moonlight. It suits delicate mending because thread pulls torn edges neatly together."
        )
    ],
    "cloud_cloth": [
        (
            "What kind of thing is cloud cloth in a fantasy story?",
            "Cloud cloth is imagined as light, soft material made from cloud or mist. It feels right for patching something that must stay light enough to fly."
        )
    ],
    "sun_sap": [
        (
            "What does sun sap suggest in a myth?",
            "Sun sap suggests warm golden liquid holding the strength of sunlight. That makes it feel useful for straightening or strengthening something hurt."
        )
    ],
    "star_resin": [
        (
            "What does star resin sound like?",
            "Star resin sounds like a sticky shining drop made from starlight. In a myth, it feels like something that can bind broken parts strongly and beautifully."
        )
    ],
}
KNOWLEDGE_ORDER = [
    "fuselage",
    "magic",
    "friendship",
    "owl",
    "crane",
    "fox",
    "otter",
    "moon_thread",
    "cloud_cloth",
    "sun_sap",
    "star_resin",
]


def generation_prompts(world: World) -> list[str]:
    hero = world.facts["hero"]
    realm = world.facts["realm"]
    damage = world.facts["damage"]
    magic = world.facts["magic"]
    friend_kind = world.facts["friend_kind"]
    return [
        'Write a short myth for a 3-to-5-year-old that includes the word "fuselage" and themes of magic and friendship.',
        f"Tell a gentle myth where a child named {hero.id} finds the broken fuselage of a sky-boat in {realm.place} and a magical {friend_kind.label} helps mend it.",
        f"Write a child-facing myth in which {magic.label} repairs {damage.phrase}, showing that friendship can do what courage alone cannot.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    hero = world.facts["hero"]
    realm = world.facts["realm"]
    damage = world.facts["damage"]
    magic = world.facts["magic"]
    friend_kind = world.facts["friend_kind"]
    craft = world.facts["craft"]

    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id}, a child walking through {realm.place}, and a magical {friend_kind.label} who becomes a true friend. Together they help a fallen sky-boat."
        ),
        (
            "What did the child find?",
            f"{hero.id} found the fallen fuselage of a sky-boat near old stones. The craft had {damage.phrase}, so it could not fly."
        ),
        (
            f"Why could {hero.id} not fix the sky-boat alone?",
            f"{hero.id} tried to help with brave hands, but {damage.need}. The problem needed the right magic, not effort by itself."
        ),
        (
            f"How did the {friend_kind.label} help?",
            f"The {friend_kind.label} shared {magic.phrase} and worked beside {hero.id}. The repair happened because the friend brought the right gift and because they worked together."
        ),
    ]
    if craft.meters["flying"] >= THRESHOLD:
        qa.append(
            (
                "How did the story end?",
                f"The sky-boat rose back into the air, and its fuselage shone again. The ending shows that friendship changed fear into hope and made the broken thing whole."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    friend_kind = world.facts["friend_kind"]
    magic = world.facts["magic"]
    tags = {"fuselage", "magic", "friendship", friend_kind.id, magic.id}
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
    for ent in list(world.entities.values()):
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.tags:
            bits.append(f"tags={sorted(ent.tags)}")
        lines.append(f"  {ent.id:8} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        realm="reed_sea",
        damage="split_seam",
        magic="moon_thread",
        friend="owl",
        hero_name="Iris",
        hero_gender="girl",
        hero_trait="patient",
    ),
    StoryParams(
        realm="reed_sea",
        damage="torn_skin",
        magic="cloud_cloth",
        friend="otter",
        hero_name="Orin",
        hero_gender="boy",
        hero_trait="kind",
    ),
    StoryParams(
        realm="sun_peak",
        damage="bent_frame",
        magic="sun_sap",
        friend="fox",
        hero_name="Mira",
        hero_gender="girl",
        hero_trait="brave",
    ),
    StoryParams(
        realm="cedar_hollow",
        damage="split_seam",
        magic="star_resin",
        friend="fox",
        hero_name="Soren",
        hero_gender="boy",
        hero_trait="steady",
    ),
    StoryParams(
        realm="cedar_hollow",
        damage="torn_skin",
        magic="cloud_cloth",
        friend="crane",
        hero_name="Lyra",
        hero_gender="girl",
        hero_trait="gentle",
    ),
]


ASP_RULES = r"""
compatible(R, D, M, F) :- realm(R), damage(D), magic(M), friend(F),
                          found_in(R, M), repairs(M, D), gives(F, M).
valid(R, D, M, F) :- compatible(R, D, M, F).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for realm_id, realm in REALMS.items():
        lines.append(asp.fact("realm", realm_id))
        for magic_id in sorted(realm.available_magic):
            lines.append(asp.fact("found_in", realm_id, magic_id))
    for damage_id in DAMAGES:
        lines.append(asp.fact("damage", damage_id))
    for magic_id, magic in MAGICS.items():
        lines.append(asp.fact("magic", magic_id))
        for damage_id in sorted(magic.repairs):
            lines.append(asp.fact("repairs", magic_id, damage_id))
    for friend_id, friend in FRIENDS.items():
        lines.append(asp.fact("friend", friend_id))
        for magic_id in sorted(friend.gives):
            lines.append(asp.fact("gives", friend_id, magic_id))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def _smoke_generate() -> None:
    sample = generate(CURATED[0])
    if not sample.story or "fuselage" not in sample.story:
        raise StoryError("(Verify failed: smoke-test story was empty or missed the seed word.)")
    if not sample.prompts or not sample.story_qa or not sample.world_qa:
        raise StoryError("(Verify failed: smoke-test sample missed prompts or QA.)")


def asp_verify() -> int:
    rc = 0
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH between clingo and valid_combos():")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    try:
        _smoke_generate()
        print("OK: smoke-test generation succeeded.")
    except Exception as err:  # pragma: no cover - verification path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    try:
        for params in CURATED:
            sample = generate(params)
            if sample.world is None or not sample.story:
                raise StoryError("curated sample generation returned an empty story")
        print(f"OK: curated generation succeeded on {len(CURATED)} stories.")
    except Exception as err:  # pragma: no cover - verification path
        rc = 1
        print(f"CURATED GENERATION FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Mythic storyworld: a child, a fallen sky-boat fuselage, magic, and friendship."
    )
    ap.add_argument("--realm", choices=REALMS)
    ap.add_argument("--damage", choices=DAMAGES)
    ap.add_argument("--magic", choices=MAGICS)
    ap.add_argument("--friend", choices=FRIENDS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible stories from clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP gate and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.realm and args.damage and args.magic and args.friend:
        realm = REALMS[args.realm]
        damage = DAMAGES[args.damage]
        magic = MAGICS[args.magic]
        friend = FRIENDS[args.friend]
        if not compatible(realm, damage, magic, friend):
            raise StoryError(explain_rejection(realm, damage, magic, friend))

    combos = [
        combo for combo in valid_combos()
        if (args.realm is None or combo[0] == args.realm)
        and (args.damage is None or combo[1] == args.damage)
        and (args.magic is None or combo[2] == args.magic)
        and (args.friend is None or combo[3] == args.friend)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    realm_id, damage_id, magic_id, friend_id = rng.choice(sorted(combos))
    hero_gender = args.gender or rng.choice(["girl", "boy"])
    if args.name:
        hero_name = args.name
    else:
        hero_name = rng.choice(GIRL_NAMES if hero_gender == "girl" else BOY_NAMES)
    hero_trait = rng.choice(TRAITS)
    return StoryParams(
        realm=realm_id,
        damage=damage_id,
        magic=magic_id,
        friend=friend_id,
        hero_name=hero_name,
        hero_gender=hero_gender,
        hero_trait=hero_trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.realm not in REALMS:
        raise StoryError(f"(Invalid realm: {params.realm})")
    if params.damage not in DAMAGES:
        raise StoryError(f"(Invalid damage: {params.damage})")
    if params.magic not in MAGICS:
        raise StoryError(f"(Invalid magic: {params.magic})")
    if params.friend not in FRIENDS:
        raise StoryError(f"(Invalid friend: {params.friend})")

    realm = REALMS[params.realm]
    damage = DAMAGES[params.damage]
    magic = MAGICS[params.magic]
    friend = FRIENDS[params.friend]
    if not compatible(realm, damage, magic, friend):
        raise StoryError(explain_rejection(realm, damage, magic, friend))

    world = tell(
        realm=realm,
        damage=damage,
        magic=magic,
        friend_kind=friend,
        hero_name=params.hero_name,
        hero_gender=params.hero_gender,
        hero_trait=params.hero_trait,
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
        print(asp_program("#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (realm, damage, magic, friend) combos:\n")
        for realm_id, damage_id, magic_id, friend_id in combos:
            print(f"  {realm_id:12} {damage_id:11} {magic_id:11} {friend_id}")
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
            header = f"### {p.hero_name}: {p.damage} in {p.realm} with {p.magic} and {p.friend}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
