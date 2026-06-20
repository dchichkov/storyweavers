#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/cucumber_rhyme_magic_pirate_tale.py
==============================================================

A standalone story world for a tiny "pirate tale" domain where two children play
at being pirates, discover a sleeping bit of sea-magic, and learn that the right
rhyme must be both *kind* and *matching*.  The seed word "cucumber" is built
into every valid story: the magic only wakes for a cool green cucumber offering,
not for glittery but unsuitable treasure.

The domain is intentionally small and constrained:

- The children build a pirate game in a bright room.
- A rolled map leads them to a magical sea chest guarded by a drowsy sea sprite.
- One child is tempted to try a greedy shortcut rhyme or the wrong offering.
- The world model predicts whether the charm will soothe the guardian or stir up
  trouble.
- A calm grown-up (or older helper) nudges them toward the matching cucumber
  offering and a sharing rhyme.
- The chest opens only when the rhyme and the gift fit the guardian's need.

Reasonableness gate:
- Every valid story uses cucumber in one of a few concrete forms.
- Only gifts that are cool/green/crisp enough for the sea guardian count.
- A rhyme must match the intended mood: "share" rhymes are accepted by the
  friendly guardian; "snatch" rhymes are refused.
- Invalid explicit choices raise StoryError with a clear explanation.

Run it
------
    python storyworlds/worlds/gpt-5.4/cucumber_rhyme_magic_pirate_tale.py
    python storyworlds/worlds/gpt-5.4/cucumber_rhyme_magic_pirate_tale.py --all
    python storyworlds/worlds/gpt-5.4/cucumber_rhyme_magic_pirate_tale.py --gift cucumber_slices --rhyme share
    python storyworlds/worlds/gpt-5.4/cucumber_rhyme_magic_pirate_tale.py --gift gold_coin
    python storyworlds/worlds/gpt-5.4/cucumber_rhyme_magic_pirate_tale.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/cucumber_rhyme_magic_pirate_tale.py --verify
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

# Make the shared result containers importable when this script is run directly:
# add storyworlds/ to the path so "results" resolves from this nested directory.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
SENSE_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"            # "character" | "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "sister"}
        male = {"boy", "father", "dad", "man", "brother"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Setting:
    id: str
    scene: str
    rig: str
    goal: str
    dark_spot: str
    closing: str


@dataclass
class Guardian:
    id: str
    label: str
    mood: str
    need: str
    likes_cool: bool = True
    opening_image: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Gift:
    id: str
    label: str
    phrase: str
    cool: bool
    green: bool
    crisp: bool
    cucumber: bool
    pretty: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class RhymeSpell:
    id: str
    opener: str
    second: str
    mood: str              # "share" | "snatch"
    sense: int
    success_line: str
    fail_line: str
    qa_text: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Treasure:
    id: str
    label: str
    image: str
    shareable: bool = True
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()

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


SETTINGS = {
    "cabin": Setting(
        "cabin",
        "a snug pirate cabin",
        "The sofa was their ship, a striped blanket became the sail, a mop was the mast, and a blue towel on the floor was the rolling sea.",
        "the moon-marked sea chest",
        "the space under the window seat",
        "sailed their pretend ship across the quiet room",
    ),
    "attic": Setting(
        "attic",
        "a creaky pirate deck",
        "The old trunk was their ship, a broom became the tiller, a pillow was the lookout nest, and a faded rug turned into a stormy map sea.",
        "the shell-locked captain's chest",
        "the corner behind the big travel box",
        "sailed their pretend ship under the attic beams",
    ),
    "playroom": Setting(
        "playroom",
        "a bright pirate cove",
        "The play table was their ship, two chairs made the railing, a scarf became the flag, and a blue mat spread out like a little bay.",
        "the star-stamped treasure chest",
        "the nook beside the toy shelf",
        "sailed their pretend ship past the toy cove",
    ),
}

GUARDIANS = {
    "sprite": Guardian(
        "sprite",
        "sea sprite",
        "sleepy",
        "a cool green snack and a gentle voice",
        True,
        "A pearl-blue sea sprite sat on the lid, no bigger than a teacup, yawning into its fins.",
        tags={"magic", "guardian"},
    ),
    "mermaid": Guardian(
        "mermaid",
        "little mermaid",
        "drowsy",
        "something crisp from the garden and words about sharing",
        True,
        "A tiny mermaid, shiny as a spoonful of water, leaned against the latch and blinked slowly.",
        tags={"magic", "guardian"},
    ),
    "crab": Guardian(
        "crab",
        "moon crab",
        "grumpy",
        "a cool crunch and a polite rhyme",
        True,
        "A silver moon crab clicked one claw on the lid as if it were keeping sleepy watch.",
        tags={"magic", "guardian"},
    ),
}

GIFTS = {
    "cucumber_slices": Gift(
        "cucumber_slices", "cucumber slices", "a little plate of cucumber slices",
        cool=True, green=True, crisp=True, cucumber=True,
        tags={"cucumber", "food", "cool"},
    ),
    "cucumber_boats": Gift(
        "cucumber_boats", "cucumber boats", "three tiny cucumber boats",
        cool=True, green=True, crisp=True, cucumber=True, pretty=True,
        tags={"cucumber", "food", "boat", "cool"},
    ),
    "cucumber_coin": Gift(
        "cucumber_coin", "a cucumber coin", "one round cucumber coin",
        cool=True, green=True, crisp=True, cucumber=True,
        tags={"cucumber", "food", "cool"},
    ),
    "gold_coin": Gift(
        "gold_coin", "a gold coin", "a shiny gold coin from the costume box",
        cool=False, green=False, crisp=False, cucumber=False, pretty=True,
        tags={"coin", "treasure"},
    ),
    "seashell": Gift(
        "seashell", "a seashell", "a pink seashell",
        cool=False, green=False, crisp=False, cucumber=False, pretty=True,
        tags={"shell", "treasure"},
    ),
}

RHYMES = {
    "share": RhymeSpell(
        "share",
        '“Green and clean from the cucumber sea,',
        'open, dear chest, and share with me.”',
        mood="share",
        sense=3,
        success_line="The words chimed together like spoons tapping cups.",
        fail_line="The rhyme itself was lovely, but it needed the right cool green gift.",
        qa_text="said a sharing rhyme",
        tags={"rhyme", "share"},
    ),
    "kind": RhymeSpell(
        "kind",
        '“Cool little cucumber, crisp and bright,',
        'open with kindness, not with fright.”',
        mood="share",
        sense=3,
        success_line="The rhyme floated softly through the room, almost like a song.",
        fail_line="The words were kind, but without a cucumber gift the magic kept dozing.",
        qa_text="said a kind cucumber rhyme",
        tags={"rhyme", "share"},
    ),
    "snatch": RhymeSpell(
        "snatch",
        '“Quick little magic, jump to my hand,',
        'open this chest on my command.”',
        mood="snatch",
        sense=1,
        success_line="",
        fail_line="The rhyme snapped through the air like a tugged rope, and the guardian frowned at its grabby sound.",
        qa_text="said a grabby command rhyme",
        tags={"rhyme", "greedy"},
    ),
}

TREASURES = {
    "stickers": Treasure(
        "stickers", "sticker stars",
        "Inside were sticker stars, a paper crown, and a note that said, “Best pirates share the sparkle.”",
        tags={"treasure", "sharing"},
    ),
    "berries": Treasure(
        "berries", "berry jewels",
        "Inside were berry jewels made from red glass pebbles and a tiny card that read, “Kind crews find the sweetest treasure.”",
        tags={"treasure", "sharing"},
    ),
    "marbles": Treasure(
        "marbles", "moon marbles",
        "Inside were moon marbles, a silver ribbon, and a rolled-up note that said, “A gentle rhyme opens bright things.”",
        tags={"treasure", "sharing"},
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Ava", "Nora", "Zoe", "Lucy", "Rose", "Maya"]
BOY_NAMES = ["Tom", "Ben", "Max", "Finn", "Leo", "Sam", "Theo", "Eli"]
TRAITS = ["careful", "gentle", "curious", "bold", "thoughtful", "cheerful"]


def gift_fits_guardian(gift: Gift, guardian: Guardian) -> bool:
    return guardian.likes_cool and gift.cucumber and gift.cool and gift.green and gift.crisp


def rhyme_fits_guardian(rhyme: RhymeSpell, guardian: Guardian) -> bool:
    return rhyme.mood == "share" and rhyme.sense >= SENSE_MIN


def valid_combo(gift: Gift, rhyme: RhymeSpell, guardian: Guardian) -> bool:
    return gift_fits_guardian(gift, guardian) and rhyme_fits_guardian(rhyme, guardian)


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for gid, gift in GIFTS.items():
        for rid, rhyme in RHYMES.items():
            for kid, guardian in GUARDIANS.items():
                if valid_combo(gift, rhyme, guardian):
                    combos.append((gid, rid, kid))
    return combos


def explain_gift(gift: Gift, guardian: Guardian) -> str:
    return (
        f"(No story: {guardian.label} asks for {guardian.need}, but {gift.label} is not that. "
        f"Use a cucumber gift that is cool, green, and crisp.)"
    )


def explain_rhyme(rhyme: RhymeSpell, guardian: Guardian) -> str:
    return (
        f"(No story: the {guardian.label} will not answer a grabby rhyme. "
        f"Choose a gentle sharing rhyme instead.)"
    )


@dataclass
class StoryParams:
    setting: str
    guardian: str
    gift: str
    rhyme: str
    treasure: str
    instigator: str
    instigator_gender: str
    helper: str
    helper_gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


def introduce(world: World, a: Entity, b: Entity, setting: Setting) -> None:
    for kid in (a, b):
        kid.memes["joy"] += 1
    world.say(
        f"One bright afternoon, {a.id} and {b.id} turned the room into {setting.scene}. "
        f"{setting.rig}"
    )
    world.say(
        f'“Captain {a.id} and Mate {b.id}!” {a.id} cried. “Today we hunt {setting.goal}!”'
    )


def discover(world: World, setting: Setting, guardian: Guardian) -> None:
    world.say(
        f"At last they found the chest tucked in {setting.dark_spot}. Moony dust glimmered on the latch."
    )
    world.say(guardian.opening_image)
    world.say(
        f"It looked as if the chest would open only for {guardian.need}."
    )


def temptation(world: World, a: Entity, gift: Gift, rhyme: RhymeSpell) -> None:
    a.memes["eagerness"] += 1
    world.say(
        f'{a.id} leaned close. “I know what to do,” {a.pronoun()} whispered. '
        f'{a.pronoun("possessive").capitalize()} hand reached for {gift.phrase}.'
    )
    world.say(
        f'Then {a.pronoun()} tried a rhyme: {rhyme.opener} {rhyme.second}'
    )


def warn(world: World, b: Entity, parent: Entity, gift: Gift, rhyme: RhymeSpell, guardian: Guardian) -> None:
    b.memes["caution"] += 1
    bad_gift = not gift_fits_guardian(gift, guardian)
    bad_rhyme = not rhyme_fits_guardian(rhyme, guardian)
    if bad_gift and bad_rhyme:
        world.say(
            f'{b.id} shook {b.pronoun("possessive")} head. “That sounds too grabby, and {gift.label} is not the cool green snack {guardian.label} wants,” {b.pronoun()} said.'
        )
    elif bad_gift:
        world.say(
            f'{b.id} peered at the gift. “The words are gentle, but {guardian.label} asked for something cool and green. {gift.label.capitalize()} will not do,” {b.pronoun()} said.'
        )
    elif bad_rhyme:
        world.say(
            f'{b.id} bit {b.pronoun("possessive")} lip. “That rhyme sounds snatchy. {parent.label_word.capitalize()} always says magic listens better to kind words,” {b.pronoun()} said.'
        )
    else:
        world.say(
            f'{b.id} smiled. “That sounds right. It is kind, and the cucumber looks just the way sea magic likes it,” {b.pronoun()} said.'
        )


def stir_magic(world: World, guardian_ent: Entity, gift: Gift, rhyme: RhymeSpell, guardian: Guardian) -> None:
    if gift_fits_guardian(gift, guardian) and rhyme_fits_guardian(rhyme, guardian):
        guardian_ent.meters["calm"] += 1
        guardian_ent.meters["awake"] += 1
        guardian_ent.memes["trust"] += 1
        world.say(rhyme.success_line)
        world.say(
            f"The {guardian.label} sniffed the cucumber, gave a pleased little nod, and the lock glowed sea-green."
        )
    else:
        guardian_ent.meters["ruffled"] += 1
        guardian_ent.memes["alarm"] += 1
        if rhyme.fail_line:
            world.say(rhyme.fail_line)
        if not gift_fits_guardian(gift, guardian):
            world.say(
                f'The {guardian.label} looked at {gift.label} and only tucked its chin more tightly. Plain treasure was not what it needed.'
            )
        world.say(
            f"A sprinkle of blue sparks puffed from the latch, and the chest stayed shut."
        )


def parent_guides(
    world: World,
    parent: Entity,
    a: Entity,
    b: Entity,
    right_gift: Gift,
    right_rhyme: RhymeSpell,
    guardian: Guardian,
) -> None:
    for kid in (a, b):
        kid.memes["relief"] += 1
    world.say(
        f'{parent.label_word.capitalize()} came over, saw the blue sparks, and knelt beside the chest.'
    )
    world.say(
        f'“Pirate magic likes a match,” {parent.pronoun()} said softly. “Try the cool green cucumber, and use words that sound like sharing, not snatching.”'
    )
    world.say(
        f'{b.id} set out {right_gift.phrase}, and together they said, {right_rhyme.opener} {right_rhyme.second}'
    )


def open_chest(
    world: World,
    guardian_ent: Entity,
    guardian: Guardian,
    treasure: Treasure,
    a: Entity,
    b: Entity,
    setting: Setting,
) -> None:
    guardian_ent.meters["calm"] += 1
    guardian_ent.meters["awake"] += 1
    guardian_ent.memes["trust"] += 1
    world.say(
        f"The {guardian.label} brightened like moonlight on water. With one tap, the latch clicked open."
    )
    world.say(treasure.image)
    world.say(
        f'{a.id} and {b.id} split the treasure between them, and then {setting.closing} with their prize tucked safe beside them.'
    )


def close_lesson(world: World, parent: Entity, a: Entity, b: Entity) -> None:
    for kid in (a, b):
        kid.memes["lesson"] += 1
        kid.memes["joy"] += 1
    world.say(
        f'{parent.label_word.capitalize()} smiled. “See? The best pirate magic is kind magic,” {parent.pronoun()} said.'
    )
    world.say(
        f'{a.id} nodded, and {b.id} tapped the empty cucumber plate like a tiny drum. From then on, whenever a game needed a spell, they chose words meant to share.'
    )


def tell(
    setting: Setting,
    guardian: Guardian,
    gift: Gift,
    rhyme: RhymeSpell,
    treasure: Treasure,
    instigator: str,
    instigator_gender: str,
    helper: str,
    helper_gender: str,
    parent_type: str,
    trait: str,
) -> World:
    world = World()
    a = world.add(Entity(id=instigator, kind="character", type=instigator_gender, role="instigator", traits=["bold"]))
    b = world.add(Entity(id=helper, kind="character", type=helper_gender, role="helper", traits=[trait]))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, role="parent", label="the parent"))
    guardian_ent = world.add(Entity(id="guardian", type="magic_being", label=guardian.label))

    introduce(world, a, b, setting)
    discover(world, setting, guardian)

    world.para()
    temptation(world, a, gift, rhyme)
    warn(world, b, parent, gift, rhyme, guardian)

    world.para()
    stir_magic(world, guardian_ent, gift, rhyme, guardian)

    direct_success = gift_fits_guardian(gift, guardian) and rhyme_fits_guardian(rhyme, guardian)
    if direct_success:
        open_chest(world, guardian_ent, guardian, treasure, a, b, setting)
        outcome = "direct"
    else:
        world.para()
        # All repaired stories use cucumber, kind rhyme, and sharing resolution.
        right_gift = next(g for g in GIFTS.values() if g.id == "cucumber_slices")
        right_rhyme = next(r for r in RHYMES.values() if r.id == "share")
        parent_guides(world, parent, a, b, right_gift, right_rhyme, guardian)
        world.para()
        open_chest(world, guardian_ent, guardian, treasure, a, b, setting)
        outcome = "guided"

    world.para()
    close_lesson(world, parent, a, b)

    world.facts.update(
        setting=setting,
        guardian_cfg=guardian,
        guardian=guardian_ent,
        gift=gift,
        rhyme=rhyme,
        treasure=treasure,
        instigator=a,
        helper=b,
        parent=parent,
        direct_success=direct_success,
        outcome=outcome,
        repaired=(outcome == "guided"),
        used_cucumber=gift.cucumber or True,
    )
    return world


KNOWLEDGE = {
    "cucumber": [(
        "What is a cucumber?",
        "A cucumber is a long green vegetable that is cool and crunchy to eat. People often slice it into little rounds."
    )],
    "rhyme": [(
        "What is a rhyme?",
        "A rhyme is when words have matching end sounds, like a little song. Rhymes can make a spell feel easy to remember."
    )],
    "magic": [(
        "What does magic mean in a pretend story?",
        "In a pretend story, magic is something wonderful that cannot happen in ordinary life, like a chest opening to a kind rhyme. It helps show how feelings and choices matter."
    )],
    "sharing": [(
        "Why is sharing a good treasure rule?",
        "Sharing lets everyone enjoy the good thing together. It also turns a grabby moment into a friendly one."
    )],
    "pirate": [(
        "What is a pirate tale?",
        "A pirate tale is an adventure story with ships, treasure, maps, and brave searching. In children's stories it is usually make-believe and playful."
    )],
    "guardian": [(
        "What is a guardian?",
        "A guardian is someone or something that watches over a place or object. In stories, a guardian often lets kind people pass."
    )],
}
KNOWLEDGE_ORDER = ["cucumber", "rhyme", "magic", "sharing", "pirate", "guardian"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    a = f["instigator"]
    b = f["helper"]
    guardian = f["guardian_cfg"]
    gift = f["gift"]
    outcome = f["outcome"]
    if outcome == "direct":
        return [
            'Write a pirate tale for a 3-to-5-year-old that includes the word "cucumber", a magic rhyme, and a treasure chest that opens kindly.',
            f"Tell a playful pirate story where {a.id} and {b.id} find a magical chest guarded by a {guardian.label} and open it with {gift.label} and a sharing rhyme.",
            "Write a gentle adventure where pirate play turns magical, the rhyme matters, and the ending shows the children sharing the treasure.",
        ]
    return [
        'Write a pirate tale for a 3-to-5-year-old that includes the word "cucumber", a magic rhyme, and a wrong first try before a kind fix.',
        f"Tell a magical pirate story where {a.id} tries the wrong charm for a {guardian.label}, then a grown-up helps the children use cucumber and a kinder rhyme.",
        "Write a simple treasure story where pirate magic works only after the children stop trying to snatch and start trying to share.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    a = f["instigator"]
    b = f["helper"]
    parent = f["parent"]
    setting = f["setting"]
    guardian = f["guardian_cfg"]
    gift = f["gift"]
    rhyme = f["rhyme"]
    treasure = f["treasure"]
    out = f["outcome"]

    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {a.id} and {b.id}, two children pretending to be pirates, and {a.id}'s {parent.label_word} who helps at the magical chest."
        ),
        (
            "What were they playing?",
            f"They turned the room into {setting.scene} and went looking for {setting.goal}. The pirate game is what led them to the hidden chest."
        ),
        (
            "What was guarding the chest?",
            f"A {guardian.label} was guarding it. The little guardian would only trust a gentle match of gift and rhyme."
        ),
    ]
    if out == "direct":
        qa.append((
            "How did they open the chest?",
            f"They used {gift.label} and {rhyme.qa_text}. The cucumber fit what the guardian wanted, and the rhyme sounded kind instead of grabby."
        ))
        qa.append((
            "What changed at the end?",
            f"The chest opened, the children shared the treasure, and the game became even brighter instead of tense. Their kind choice is what turned the magic friendly."
        ))
    else:
        bad_reason_parts = []
        if not gift_fits_guardian(gift, guardian):
            bad_reason_parts.append(f"{gift.label} was not the cool green cucumber gift the guardian wanted")
        if not rhyme_fits_guardian(rhyme, guardian):
            bad_reason_parts.append("the first rhyme sounded too grabby")
        reason = " and ".join(bad_reason_parts) if bad_reason_parts else "their first try did not match"
        qa.append((
            "Why did the first try fail?",
            f"The first try failed because {reason}. The chest stayed shut until the children matched the magic more carefully."
        ))
        qa.append((
            f"How did {parent.label_word} help?",
            f"{parent.label_word.capitalize()} told them to use the cool green cucumber and words about sharing. That guidance gave them both the right gift and the right kind of rhyme."
        ))
        qa.append((
            "How did the story end?",
            f"In the end the chest opened, the guardian trusted them, and the children shared the treasure. The final picture proves that kind pirate magic works better than snatching."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"cucumber", "rhyme", "magic", "sharing", "pirate", "guardian"}
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
        if e.traits:
            bits.append(f"traits={e.traits}")
        lines.append(f"  {e.id:10} ({e.type:11}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
% A gift is fitting when it is cucumber and cool/green/crisp.
fit_gift(G, K) :- gift(G), guardian(K), cucumber(G), cool(G), green(G), crisp(G), likes_cool(K).

% A rhyme is fitting when it is a sharing rhyme with enough common sense.
fit_rhyme(R, K) :- rhyme(R), guardian(K), mood(R, share), sense(R, S), sense_min(M), S >= M.

valid(G, R, K) :- fit_gift(G, K), fit_rhyme(R, K).

outcome(direct) :- chosen_gift(G), chosen_rhyme(R), chosen_guardian(K), valid(G, R, K).
outcome(guided) :- chosen_gift(G), chosen_rhyme(R), chosen_guardian(K), not valid(G, R, K).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for gid, g in GUARDIANS.items():
        lines.append(asp.fact("guardian", gid))
        if g.likes_cool:
            lines.append(asp.fact("likes_cool", gid))
    for gid, g in GIFTS.items():
        lines.append(asp.fact("gift", gid))
        if g.cucumber:
            lines.append(asp.fact("cucumber", gid))
        if g.cool:
            lines.append(asp.fact("cool", gid))
        if g.green:
            lines.append(asp.fact("green", gid))
        if g.crisp:
            lines.append(asp.fact("crisp", gid))
    for rid, r in RHYMES.items():
        lines.append(asp.fact("rhyme", rid))
        lines.append(asp.fact("mood", rid, r.mood))
        lines.append(asp.fact("sense", rid, r.sense))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join([
        asp.fact("chosen_gift", params.gift),
        asp.fact("chosen_rhyme", params.rhyme),
        asp.fact("chosen_guardian", params.guardian),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def outcome_of(params: StoryParams) -> str:
    return "direct" if valid_combo(GIFTS[params.gift], RHYMES[params.rhyme], GUARDIANS[params.guardian]) else "guided"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: pirate play, cucumber magic, and a rhyme that must be kind."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--guardian", choices=GUARDIANS)
    ap.add_argument("--gift", choices=GIFTS)
    ap.add_argument("--rhyme", choices=RHYMES)
    ap.add_argument("--treasure", choices=TREASURES)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible gift/rhyme/guardian triples from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run smoke tests")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_kids(rng: random.Random) -> tuple[str, str, str, str]:
    g1 = rng.choice(["girl", "boy"])
    pool1 = GIRL_NAMES if g1 == "girl" else BOY_NAMES
    a = rng.choice(pool1)
    g2 = rng.choice(["girl", "boy"])
    pool2 = [n for n in (GIRL_NAMES if g2 == "girl" else BOY_NAMES) if n != a]
    b = rng.choice(pool2)
    return a, g1, b, g2


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    guardian_id = args.guardian or rng.choice(sorted(GUARDIANS))
    guardian = GUARDIANS[guardian_id]

    if args.gift:
        gift = GIFTS[args.gift]
        if not gift_fits_guardian(gift, guardian):
            raise StoryError(explain_gift(gift, guardian))
    if args.rhyme:
        rhyme = RHYMES[args.rhyme]
        if args.gift and args.guardian and not rhyme_fits_guardian(rhyme, guardian) and not gift_fits_guardian(GIFTS[args.gift], guardian):
            # explicit invalid pair already bad; keep a specific message by gift first above
            raise StoryError(explain_rhyme(rhyme, guardian))
        if args.guardian and not rhyme_fits_guardian(rhyme, guardian) and args.gift is None:
            raise StoryError(explain_rhyme(rhyme, guardian))

    setting = args.setting or rng.choice(sorted(SETTINGS))
    treasure = args.treasure or rng.choice(sorted(TREASURES))
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    instigator, ig, helper, hg = _pick_kids(rng)

    if args.gift is None and args.rhyme is None:
        valid = sorted(valid_combos())
        gift_id, rhyme_id, guardian_id = rng.choice(valid)
    elif args.gift is not None and args.rhyme is None:
        fitting_rhymes = [rid for rid, r in RHYMES.items() if valid_combo(GIFTS[args.gift], r, guardian)]
        if not fitting_rhymes:
            raise StoryError(explain_gift(GIFTS[args.gift], guardian))
        gift_id = args.gift
        rhyme_id = rng.choice(sorted(fitting_rhymes))
    elif args.gift is None and args.rhyme is not None:
        fitting_gifts = [gid for gid, g in GIFTS.items() if valid_combo(g, RHYMES[args.rhyme], guardian)]
        if not fitting_gifts:
            raise StoryError(explain_rhyme(RHYMES[args.rhyme], guardian))
        gift_id = rng.choice(sorted(fitting_gifts))
        rhyme_id = args.rhyme
    else:
        gift_id = args.gift
        rhyme_id = args.rhyme
        if not valid_combo(GIFTS[gift_id], RHYMES[rhyme_id], guardian):
            if not gift_fits_guardian(GIFTS[gift_id], guardian):
                raise StoryError(explain_gift(GIFTS[gift_id], guardian))
            raise StoryError(explain_rhyme(RHYMES[rhyme_id], guardian))

    return StoryParams(
        setting=setting,
        guardian=guardian_id,
        gift=gift_id,
        rhyme=rhyme_id,
        treasure=treasure,
        instigator=instigator,
        instigator_gender=ig,
        helper=helper,
        helper_gender=hg,
        parent=parent,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.setting],
        GUARDIANS[params.guardian],
        GIFTS[params.gift],
        RHYMES[params.rhyme],
        TREASURES[params.treasure],
        params.instigator,
        params.instigator_gender,
        params.helper,
        params.helper_gender,
        params.parent,
        params.trait,
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


CURATED = [
    StoryParams("cabin", "sprite", "cucumber_slices", "share", "stickers", "Tom", "boy", "Lily", "girl", "mother", "careful"),
    StoryParams("attic", "mermaid", "cucumber_boats", "kind", "berries", "Mia", "girl", "Ben", "boy", "father", "gentle"),
    StoryParams("playroom", "crab", "cucumber_coin", "share", "marbles", "Finn", "boy", "Zoe", "girl", "mother", "thoughtful"),
]


def asp_verify() -> int:
    rc = 0
    clingo_set, python_set = set(asp_valid_combos()), set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: ASP gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    cases = list(CURATED)
    for s in range(30):
        rng = random.Random(s)
        try:
            params = resolve_params(build_parser().parse_args([]), rng)
            params.seed = s
            cases.append(params)
        except StoryError:
            rc = 1
            print(f"Unexpected StoryError while resolving random case at seed {s}.")
            break

    mismatch = 0
    for params in cases:
        if asp_outcome(params) != outcome_of(params):
            mismatch += 1
    if mismatch == 0:
        print(f"OK: ASP outcome matches Python on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {mismatch}/{len(cases)} outcomes differ.")

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("Smoke test generated an empty story.")
        print("OK: smoke test story generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/3.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (gift, rhyme, guardian) combos:\n")
        for gift, rhyme, guardian in combos:
            print(f"  {gift:17} {rhyme:7} {guardian}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
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
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.instigator} & {p.helper}: {p.gift}, {p.rhyme}, {p.guardian}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
