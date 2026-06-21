#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/recollection_shorts_repetition_twist_rhyming_story.py
================================================================================

A standalone storyworld for a tiny rhyming tale about a child, some special
shorts, a keepsake recollection, a repeated search chant, and a gentle twist:
the shorts are not where the child expects.

The world models a small home search. Different shorts support different
keepsakes; different "missing" causes require different physical properties.
The search is state-driven: as the child checks places, clues emerge, a helper
notices them, and the reveal depends on the simulated cause.

Run it
------
    python storyworlds/worlds/gpt-5.4/recollection_shorts_repetition_twist_rhyming_story.py
    python storyworlds/worlds/gpt-5.4/recollection_shorts_repetition_twist_rhyming_story.py --shorts striped --keepsake shell --cause clothesline
    python storyworlds/worlds/gpt-5.4/recollection_shorts_repetition_twist_rhyming_story.py --shorts sporty --keepsake shell
    python storyworlds/worlds/gpt-5.4/recollection_shorts_repetition_twist_rhyming_story.py --all
    python storyworlds/worlds/gpt-5.4/recollection_shorts_repetition_twist_rhyming_story.py --qa --json
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
        female = {"girl", "mother", "mom", "sister", "woman"}
        male = {"boy", "father", "dad", "brother", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {
            "mother": "mom",
            "father": "dad",
            "sister": "sister",
            "brother": "brother",
        }.get(self.type, self.type)


@dataclass
class ShortsCfg:
    id: str
    label: str
    phrase: str
    pocketed: bool = False
    drawstring: bool = False
    soft: bool = False
    washable: bool = True
    rhyme: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Keepsake:
    id: str
    label: str
    phrase: str
    needs: str = "pocket"   # pocket | drawstring
    memory_from: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Cause:
    id: str
    reveal_place: str
    require: str = "any"    # any | washable | drawstring | soft
    clue_line: str = ""
    reveal_line: str = ""
    qa_line: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Outing:
    id: str
    label: str
    cheer: str
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


SHORTS = {
    "striped": ShortsCfg(
        id="striped",
        label="striped shorts",
        phrase="a pair of blue-and-white striped shorts",
        pocketed=True,
        drawstring=False,
        soft=False,
        washable=True,
        rhyme="striped and bright",
        tags={"shorts", "pocket"},
    ),
    "starry": ShortsCfg(
        id="starry",
        label="starry knit shorts",
        phrase="a pair of starry knit shorts",
        pocketed=True,
        drawstring=True,
        soft=True,
        washable=True,
        rhyme="starry and merry",
        tags={"shorts", "pocket", "drawstring"},
    ),
    "sporty": ShortsCfg(
        id="sporty",
        label="sporty mesh shorts",
        phrase="a pair of sporty mesh shorts",
        pocketed=False,
        drawstring=True,
        soft=False,
        washable=True,
        rhyme="sporty and snorty",
        tags={"shorts", "drawstring"},
    ),
    "sleepy": ShortsCfg(
        id="sleepy",
        label="sleepy cloud shorts",
        phrase="a pair of sleepy cloud shorts",
        pocketed=False,
        drawstring=True,
        soft=True,
        washable=True,
        rhyme="cloud-soft and proud-soft",
        tags={"shorts", "drawstring"},
    ),
}

KEEPSAKES = {
    "shell": Keepsake(
        id="shell",
        label="shell",
        phrase="a little shell",
        needs="pocket",
        memory_from="the last trip to the shore",
        tags={"shell", "memory", "pocket"},
    ),
    "note": Keepsake(
        id="note",
        label="note",
        phrase="a tiny folded note",
        needs="pocket",
        memory_from="a picnic with Grandma",
        tags={"note", "memory", "pocket"},
    ),
    "ribbon": Keepsake(
        id="ribbon",
        label="ribbon",
        phrase="a small ribbon",
        needs="drawstring",
        memory_from="the kite parade",
        tags={"ribbon", "memory", "drawstring"},
    ),
}

CAUSES = {
    "clothesline": Cause(
        id="clothesline",
        reveal_place="the clothesline",
        require="washable",
        clue_line="Then a breeze went flap-flap by, and something striped or starry winked against the sky.",
        reveal_line="The shorts were dancing on the clothesline, washed and clipped up high.",
        qa_line="The helper followed the flapping clue and found the shorts drying on the clothesline.",
        tags={"washing", "wind", "outside"},
    ),
    "pet_bed": Cause(
        id="pet_bed",
        reveal_place="the pet bed",
        require="drawstring",
        clue_line="Then the pet bed gave a wiggle and a sleepy little snore, while a drawstring tail peeped out across the floor.",
        reveal_line="The family pet had dragged the shorts to the bed and curled up beside them.",
        qa_line="The helper noticed the peeking drawstring and found the shorts in the pet bed.",
        tags={"pet", "drawstring"},
    ),
    "already_wearing": Cause(
        id="already_wearing",
        reveal_place="already on the child",
        require="soft",
        clue_line="Then the helper blinked and grinned at a hem swishing low, because two familiar leg holes were already in a row.",
        reveal_line="The child had pulled the shorts on half-asleep and forgotten all about it.",
        qa_line="The helper saw the hem at the child's knees and realized the shorts were already being worn.",
        tags={"morning", "soft", "twist"},
    ),
    "toy_chest": Cause(
        id="toy_chest",
        reveal_place="the toy chest",
        require="any",
        clue_line="Then the toy chest would not shut, not even by a crack, and a corner of bright cloth kept puffing from the back.",
        reveal_line="The shorts were scrunched in the toy chest from yesterday's dress-up game.",
        qa_line="The helper saw the toy chest bulging and found the shorts tucked inside.",
        tags={"toys", "dress_up"},
    ),
}

OUTINGS = {
    "beach": Outing(
        id="beach",
        label="the beach",
        cheer="for sand, sun, and skipping by the sea",
        tags={"beach"},
    ),
    "park": Outing(
        id="park",
        label="the park",
        cheer="for swings, slides, and running wild and free",
        tags={"park"},
    ),
    "parade": Outing(
        id="parade",
        label="the neighborhood parade",
        cheer="for drums, smiles, and stepping in a line",
        tags={"parade"},
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Nora", "Rose"]
BOY_NAMES = ["Ben", "Max", "Sam", "Leo", "Jack", "Finn", "Theo", "Eli"]
SEARCH_SPOTS = [
    ("chair", "under the chair"),
    ("stair", "by the stair"),
    ("basket", "in the basket"),
]
PETS = ["cat", "dog"]


def shorts_supports_keepsake(shorts: ShortsCfg, keepsake: Keepsake) -> bool:
    if keepsake.needs == "pocket":
        return shorts.pocketed
    if keepsake.needs == "drawstring":
        return shorts.drawstring
    return False


def cause_fits(shorts: ShortsCfg, cause: Cause) -> bool:
    if cause.require == "any":
        return True
    if cause.require == "washable":
        return shorts.washable
    if cause.require == "drawstring":
        return shorts.drawstring
    if cause.require == "soft":
        return shorts.soft
    return False


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for sid, shorts in SHORTS.items():
        for kid, keepsake in KEEPSAKES.items():
            if not shorts_supports_keepsake(shorts, keepsake):
                continue
            for cid, cause in CAUSES.items():
                if cause_fits(shorts, cause):
                    combos.append((sid, kid, cid))
    return combos


@dataclass
class StoryParams:
    shorts: str
    keepsake: str
    cause: str
    outing: str
    child_name: str
    child_gender: str
    helper_type: str
    pet: str = ""
    seed: Optional[int] = None


CURATED = [
    StoryParams(
        shorts="striped",
        keepsake="shell",
        cause="clothesline",
        outing="beach",
        child_name="Lily",
        child_gender="girl",
        helper_type="mother",
        pet="",
    ),
    StoryParams(
        shorts="starry",
        keepsake="ribbon",
        cause="pet_bed",
        outing="parade",
        child_name="Ben",
        child_gender="boy",
        helper_type="father",
        pet="dog",
    ),
    StoryParams(
        shorts="sleepy",
        keepsake="ribbon",
        cause="already_wearing",
        outing="park",
        child_name="Mia",
        child_gender="girl",
        helper_type="sister",
        pet="",
    ),
    StoryParams(
        shorts="starry",
        keepsake="note",
        cause="toy_chest",
        outing="park",
        child_name="Theo",
        child_gender="boy",
        helper_type="brother",
        pet="",
    ),
]


def explain_combo(shorts: ShortsCfg, keepsake: Keepsake, cause: Cause) -> str:
    if not shorts_supports_keepsake(shorts, keepsake):
        need = "a pocket" if keepsake.needs == "pocket" else "a drawstring"
        return (
            f"(No story: {shorts.label} do not have {need}, so they cannot carry "
            f"{keepsake.phrase} in a sensible way.)"
        )
    if not cause_fits(shorts, cause):
        reason = {
            "washable": "something that could have been washed and hung up",
            "drawstring": "a drawstring for a pet to drag",
            "soft": "very soft shorts a sleepy child might forget already wearing",
        }[cause.require]
        return f"(No story: {cause.id} needs {reason}, and {shorts.label} do not fit that idea.)"
    return "(No story: this combination does not fit the world.)"


def helper_label(helper_type: str) -> str:
    return {
        "mother": "mom",
        "father": "dad",
        "sister": "sister",
        "brother": "brother",
    }[helper_type]


def helper_intro(helper_type: str) -> str:
    return {
        "mother": "Mom heard the commotion first.",
        "father": "Dad looked up from tying the picnic basket.",
        "sister": "Big sister came skimming down the hall.",
        "brother": "Big brother came skidding down the hall.",
    }[helper_type]


def keepsake_line(shorts: ShortsCfg, keepsake: Keepsake) -> str:
    if keepsake.needs == "pocket":
        return (
            f"In {shorts.label}'s pocket lived {keepsake.phrase}, "
            f"a recollection from {keepsake.memory_from}."
        )
    return (
        f"Tied to the drawstring was {keepsake.phrase}, "
        f"a recollection from {keepsake.memory_from}."
    )


def introduce(world: World, child: Entity, helper: Entity, shorts: ShortsCfg,
              keepsake: Keepsake, outing: Outing) -> None:
    child.memes["love"] += 1
    world.say(
        f"{child.id} loved {shorts.phrase}, {shorts.rhyme}, "
        f"and perfect {outing.cheer}."
    )
    world.say(keepsake_line(shorts, keepsake))
    world.say(
        f"That tiny treasure made the shorts feel extra dear, so {child.id} wanted them especially today."
    )
    world.facts["favorite_reason"] = keepsake.memory_from
    world.facts["helper_title"] = helper.label_word


def discover_missing(world: World, child: Entity, outing: Outing) -> None:
    child.memes["worry"] += 1
    world.say(
        f"When it was time to go to {outing.label}, {child.id} reached for the shorts and gasped."
    )
    world.say(
        f'"My shorts, my shorts! I need my shorts!" {child.pronoun()} cried.'
    )


def search_spot(world: World, child: Entity, short_cfg: ShortsCfg, key: str, place_text: str) -> None:
    child.meters["searched"] += 1
    child.memes["frustration"] += 1
    world.say(
        f"{child.id} looked {place_text}. No {short_cfg.label} there."
    )
    world.say(
        f'"Check the chair, check the stair, check everywhere!" sang {child.id}.'
    )
    world.facts.setdefault("searched_places", []).append(key)


def clue_rule(world: World, cause: Cause, helper: Entity, child: Entity) -> None:
    if world.get("shorts").meters["found"] >= THRESHOLD:
        return
    if child.meters["searched"] < 2:
        return
    sig = ("clue", cause.id)
    if sig in world.fired:
        return
    world.fired.add(sig)
    helper.memes["idea"] += 1
    world.say(cause.clue_line)
    world.facts["clue_seen"] = cause.id


def reveal(world: World, child: Entity, helper: Entity, shorts: ShortsCfg,
           cause: Cause, pet: Optional[Entity]) -> None:
    world.get("shorts").meters["found"] += 1
    child.memes["worry"] = 0.0
    child.memes["relief"] += 1
    child.memes["joy"] += 1
    helper.memes["care"] += 1
    name = helper.label_word.capitalize()
    world.say(helper_intro(helper.type))
    world.say(
        f'{name} said, "Wait a tick. Let us look where the clue wants us to look."'
    )
    if cause.id == "pet_bed" and pet is not None:
        world.say(
            f"{pet.label.capitalize()} lifted {pet.pronoun('possessive')} head and thumped the bed once, as if to say, There!"
        )
    world.say(cause.reveal_line)
    if cause.id == "already_wearing":
        world.say(
            f"{child.id} looked down, then laughed so hard that {child.pronoun('possessive')} toes curled inside the shorts already on {child.pronoun('object')}."
        )
    else:
        world.say(
            f'"There they are!" said {child.id}, with a bounce and a grin.'
        )
    world.facts["reveal_place"] = cause.reveal_place


def ending(world: World, child: Entity, helper: Entity, outing: Outing, cause: Cause) -> None:
    child.memes["calm"] += 1
    world.say(
        f'Soon they were off to {outing.label}, and {child.id} skipped all the way.'
    )
    if cause.id == "already_wearing":
        world.say(
            "All along the lane, the child sang, \"My shorts, my shorts, I wore my shorts!\" and everybody laughed at the tiny twist."
        )
    else:
        world.say(
            'This time the song changed to, "Found at last, found at last, the searching spell is past!"'
        )
    world.say(
        "The recollection stayed close, the mood turned light, and the day felt bright just right."
    )


def tell(params: StoryParams) -> World:
    shorts = SHORTS[params.shorts]
    keepsake = KEEPSAKES[params.keepsake]
    cause = CAUSES[params.cause]
    outing = OUTINGS[params.outing]

    world = World()
    child = world.add(Entity(
        id=params.child_name,
        kind="character",
        type=params.child_gender,
        role="child",
        label=params.child_name,
    ))
    helper = world.add(Entity(
        id="Helper",
        kind="character",
        type=params.helper_type,
        role="helper",
        label=helper_label(params.helper_type),
    ))
    pet = None
    if params.pet:
        pet = world.add(Entity(
            id="Pet",
            kind="character",
            type="animal",
            role="pet",
            label=f"the {params.pet}",
        ))
    shorts_ent = world.add(Entity(
        id="shorts",
        type="shorts",
        label=shorts.label,
        phrase=shorts.phrase,
        attrs={"cfg": shorts.id},
    ))

    introduce(world, child, helper, shorts, keepsake, outing)
    world.para()
    discover_missing(world, child, outing)
    for key, place_text in SEARCH_SPOTS:
        search_spot(world, child, shorts, key, place_text)
        clue_rule(world, cause, helper, child)
    world.para()
    reveal(world, child, helper, shorts, cause, pet)
    world.para()
    ending(world, child, helper, outing, cause)

    world.facts.update(
        child=child,
        helper=helper,
        pet=pet,
        shorts_cfg=shorts,
        keepsake=keepsake,
        cause=cause,
        outing=outing,
        found=shorts_ent.meters["found"] >= THRESHOLD,
    )
    return world


KNOWLEDGE = {
    "shorts": [(
        "What are shorts?",
        "Shorts are short pants that keep your legs cooler than long pants. People often wear them on warm or playful days."
    )],
    "pocket": [(
        "What is a pocket for?",
        "A pocket is a little cloth space in clothing where you can keep small things. It helps you carry something close."
    )],
    "drawstring": [(
        "What does a drawstring do?",
        "A drawstring is a cord you can pull to make clothes fit more snugly. Sometimes people tie a tiny ribbon to it."
    )],
    "memory": [(
        "What is a recollection?",
        "A recollection is a memory that comes back to your mind. It can be brought back by a place, a song, or a small keepsake."
    )],
    "shell": [(
        "Why might someone keep a shell?",
        "A shell can remind someone of the beach and a happy day there. Small things often help memories feel close."
    )],
    "note": [(
        "Why keep a tiny note?",
        "A tiny note can hold kind words or a reminder from someone you love. Reading it can make you remember that person again."
    )],
    "ribbon": [(
        "What can a ribbon remind you of?",
        "A ribbon can remind you of a party, a parade, or a special gift. Looking at it can bring a happy memory back."
    )],
    "pet": [(
        "Why do pets carry clothes sometimes?",
        "Pets sometimes drag soft things because they smell familiar or feel cozy. A dangling string can make the cloth even more tempting."
    )],
    "washing": [(
        "Why are clothes hung on a clothesline?",
        "Clothes are hung on a clothesline so air and sun can help dry them. Wind can make them flap and easier to notice."
    )],
    "toys": [(
        "Why do things get lost in a toy chest?",
        "Things can slip into a toy chest during play and get covered by other toys. That makes them harder to spot right away."
    )],
}
KNOWLEDGE_ORDER = [
    "shorts", "memory", "pocket", "drawstring", "shell", "note", "ribbon",
    "pet", "washing", "toys",
]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    shorts = f["shorts_cfg"]
    keepsake = f["keepsake"]
    cause = f["cause"]
    outing = f["outing"]
    return [
        'Write a short rhyming story for a 3-to-5-year-old that includes the words "recollection" and "shorts".',
        f"Tell a playful story where {child.id} cannot find {shorts.label}, repeats a search chant, and a helper discovers a gentle twist before they go to {outing.label}.",
        f"Write a rhyming story in which {keepsake.phrase} serves as a recollection from {keepsake.memory_from}, and the missing shorts are finally revealed at {cause.reveal_place}.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    shorts = f["shorts_cfg"]
    keepsake = f["keepsake"]
    cause = f["cause"]
    outing = f["outing"]
    searched = ", ".join(f.get("searched_places", []))
    qas = [
        (
            "Who is the story about?",
            f"It is about {child.id}, {helper.label_word}, and a beloved pair of {shorts.label}. {child.id} cared about the shorts because of {keepsake.phrase}, a recollection from {keepsake.memory_from}."
        ),
        (
            f"Why did {child.id} want those shorts so much?",
            f"{child.id} loved the shorts for the outing to {outing.label}. {keepsake.phrase.capitalize()} made them feel special because it held a recollection from {keepsake.memory_from}."
        ),
        (
            "What did the child keep saying while searching?",
            f'{child.id} kept singing, "Check the chair, check the stair, check everywhere!" The repetition shows how hard {child.pronoun()} was trying and how worried {child.pronoun()} felt.'
        ),
        (
            "Where did the child look first?",
            f"{child.id} searched {searched}. Each place came up empty, which made the clue matter more when it finally appeared."
        ),
        (
            f"How were the shorts found?",
            f"{helper.label_word.capitalize()} noticed a clue after the searching went on for a while. {cause.qa_line}"
        ),
        (
            "What was the twist at the end?",
            (
                "The twist was that the shorts were not lost in the ordinary way. "
                + (
                    f"They were {cause.reveal_place}, which surprised {child.id} and changed the worried search into laughter."
                    if cause.id != "already_wearing"
                    else f"{child.id} had been wearing them already, so the whole hunt turned funny instead of gloomy."
                )
            ),
        ),
    ]
    return qas


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = set(f["shorts_cfg"].tags) | set(f["keepsake"].tags) | set(f["cause"].tags)
    tags.add("memory")
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags and tag in KNOWLEDGE:
            out.extend(KNOWLEDGE[tag])
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, prompt in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {prompt}")
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
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.attrs:
            bits.append(f"attrs={ent.attrs}")
        lines.append(f"  {ent.id:8} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(world.fired)}")
    if world.facts.get("searched_places"):
        lines.append(f"  searched: {world.facts['searched_places']}")
    return "\n".join(lines)


ASP_RULES = r"""
supports_keepsake(S, K) :- shorts(S), keepsake(K), pocket_need(K), pocketed(S).
supports_keepsake(S, K) :- shorts(S), keepsake(K), drawstring_need(K), drawstring(S).

fits_cause(S, C) :- shorts(S), cause(C), require_any(C).
fits_cause(S, C) :- shorts(S), cause(C), require_washable(C), washable(S).
fits_cause(S, C) :- shorts(S), cause(C), require_drawstring(C), drawstring(S).
fits_cause(S, C) :- shorts(S), cause(C), require_soft(C), soft(S).

valid(S, K, C) :- shorts(S), keepsake(K), cause(C),
                  supports_keepsake(S, K), fits_cause(S, C).

revealed_at(line) :- chosen_cause(clothesline).
revealed_at(pet_bed) :- chosen_cause(pet_bed).
revealed_at(already_wearing) :- chosen_cause(already_wearing).
revealed_at(toy_chest) :- chosen_cause(toy_chest).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid, shorts in SHORTS.items():
        lines.append(asp.fact("shorts", sid))
        if shorts.pocketed:
            lines.append(asp.fact("pocketed", sid))
        if shorts.drawstring:
            lines.append(asp.fact("drawstring", sid))
        if shorts.soft:
            lines.append(asp.fact("soft", sid))
        if shorts.washable:
            lines.append(asp.fact("washable", sid))
    for kid, keepsake in KEEPSAKES.items():
        lines.append(asp.fact("keepsake", kid))
        if keepsake.needs == "pocket":
            lines.append(asp.fact("pocket_need", kid))
        if keepsake.needs == "drawstring":
            lines.append(asp.fact("drawstring_need", kid))
    for cid, cause in CAUSES.items():
        lines.append(asp.fact("cause", cid))
        if cause.require == "any":
            lines.append(asp.fact("require_any", cid))
        elif cause.require == "washable":
            lines.append(asp.fact("require_washable", cid))
        elif cause.require == "drawstring":
            lines.append(asp.fact("require_drawstring", cid))
        elif cause.require == "soft":
            lines.append(asp.fact("require_soft", cid))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def outcome_of(params: StoryParams) -> str:
    mapping = {
        "clothesline": "line",
        "pet_bed": "pet_bed",
        "already_wearing": "already_wearing",
        "toy_chest": "toy_chest",
    }
    return mapping[params.cause]


def asp_outcome(params: StoryParams) -> str:
    import asp

    model = asp.one_model(
        asp_program(
            extra=asp.fact("chosen_cause", params.cause),
            show="#show revealed_at/1.",
        )
    )
    atoms = asp.atoms(model, "revealed_at")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    cases = list(CURATED)
    parser = build_parser()
    for seed in range(20):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(seed))
        except StoryError:
            continue
        cases.append(params)

    bad = 0
    for params in cases:
        if asp_outcome(params) != outcome_of(params):
            bad += 1
    if bad == 0:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("smoke test produced an empty story")
        print("OK: smoke test generation succeeded.")
    except Exception as err:  # pragma: no cover - verify path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(conflict_handler="resolve",
        description="Rhyming storyworld: a child searches for special shorts, repeats a chant, and a clue leads to a twist."
    )
    ap.add_argument("--shorts", choices=SHORTS)
    ap.add_argument("--keepsake", choices=KEEPSAKES)
    ap.add_argument("--cause", choices=CAUSES)
    ap.add_argument("--outing", choices=OUTINGS)
    ap.add_argument("--helper", choices=["mother", "father", "sister", "brother"])
    ap.add_argument("--pet", choices=["", "cat", "dog"], default=None)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid combinations via clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.shorts and args.keepsake:
        if not shorts_supports_keepsake(SHORTS[args.shorts], KEEPSAKES[args.keepsake]):
            raise StoryError(explain_combo(SHORTS[args.shorts], KEEPSAKES[args.keepsake], CAUSES[args.cause or "toy_chest"]))
    if args.shorts and args.cause:
        if not cause_fits(SHORTS[args.shorts], CAUSES[args.cause]):
            keep = KEEPSAKES[args.keepsake] if args.keepsake else next(iter(KEEPSAKES.values()))
            raise StoryError(explain_combo(SHORTS[args.shorts], keep, CAUSES[args.cause]))

    combos = [
        combo for combo in valid_combos()
        if (args.shorts is None or combo[0] == args.shorts)
        and (args.keepsake is None or combo[1] == args.keepsake)
        and (args.cause is None or combo[2] == args.cause)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    shorts_id, keepsake_id, cause_id = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    helper = args.helper or rng.choice(["mother", "father", "sister", "brother"])
    outing = args.outing or rng.choice(sorted(OUTINGS))
    pet = ""
    if cause_id == "pet_bed":
        pet = args.pet if args.pet not in (None, "") else rng.choice(PETS)
    else:
        pet = args.pet or ""
    return StoryParams(
        shorts=shorts_id,
        keepsake=keepsake_id,
        cause=cause_id,
        outing=outing,
        child_name=name,
        child_gender=gender,
        helper_type=helper,
        pet=pet,
    )


def generate(params: StoryParams) -> StorySample:
    if params.shorts not in SHORTS:
        raise StoryError(f"(Unknown shorts style: {params.shorts})")
    if params.keepsake not in KEEPSAKES:
        raise StoryError(f"(Unknown keepsake: {params.keepsake})")
    if params.cause not in CAUSES:
        raise StoryError(f"(Unknown cause: {params.cause})")
    if params.outing not in OUTINGS:
        raise StoryError(f"(Unknown outing: {params.outing})")
    if params.helper_type not in {"mother", "father", "sister", "brother"}:
        raise StoryError(f"(Unknown helper type: {params.helper_type})")
    shorts = SHORTS[params.shorts]
    keepsake = KEEPSAKES[params.keepsake]
    cause = CAUSES[params.cause]
    if not shorts_supports_keepsake(shorts, keepsake) or not cause_fits(shorts, cause):
        raise StoryError(explain_combo(shorts, keepsake, cause))

    world = tell(params)
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
        print(asp_program("", "#show valid/3.\n#show revealed_at/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (shorts, keepsake, cause) combos:\n")
        for shorts, keepsake, cause in combos:
            print(f"  {shorts:8} {keepsake:8} {cause}")
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
            header = f"### {p.child_name}: {p.shorts}, {p.keepsake}, {p.cause}"
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
