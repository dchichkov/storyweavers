#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/lyric_ist_take_professor_twist_nursery_rhyme.py
==============================================================================

A standalone story world for a tiny nursery-rhyme-style tale with a twist:
a child thinks a song has been taken, follows a professor's clues through a
small world, and learns that the professor is secretly the village lyric-ist.

The world model is classical and state-driven:

- a song card goes missing
- the child worries and searches
- clues lead toward a hiding place
- the professor guides the child
- twist: the professor took the card only to mend its last line
- the ending image proves the change: a new rhyme is sung together

The reasonableness gate is small but explicit:
- each clue must actually fit the chosen hiding place
- each professor must be able to reach that place
- the professor's correction gift must suit the place and the tale

The ASP twin mirrors that gate and the simple outcome model.
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Child:
    id: str
    trait: str
    favorite: str
    opening: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Professor:
    id: str
    label: str
    type: str
    title: str
    gait: str
    voice: str
    reach: set[str]
    lyric_style: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Place:
    id: str
    label: str
    phrase: str
    line: str
    reached_by: set[str]
    clue_ids: set[str]
    gift_ids: set[str]
    image: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Clue:
    id: str
    label: str
    phrase: str
    verb: str
    proves: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Gift:
    id: str
    label: str
    phrase: str
    repair_text: str
    ending_line: str
    tags: set[str] = field(default_factory=set)


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


def _r_missing_worry(world: World) -> list[str]:
    child = world.get("child")
    card = world.get("card")
    if card.meters["missing"] < THRESHOLD:
        return []
    sig = ("missing_worry",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child.memes["worry"] += 1
    return []


def _r_clue_hope(world: World) -> list[str]:
    child = world.get("child")
    clue = world.get("clue")
    if clue.meters["noticed"] < THRESHOLD:
        return []
    sig = ("clue_hope",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child.memes["hope"] += 1
    return []


def _r_found_relief(world: World) -> list[str]:
    child = world.get("child")
    card = world.get("card")
    if card.meters["found"] < THRESHOLD:
        return []
    sig = ("found_relief",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child.memes["worry"] = 0.0
    child.memes["relief"] += 1
    child.memes["joy"] += 1
    return []


def _r_repaired_song(world: World) -> list[str]:
    card = world.get("card")
    gift = world.get("gift")
    if gift.meters["used"] < THRESHOLD:
        return []
    sig = ("repaired_song",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    card.meters["repaired"] += 1
    return []


CAUSAL_RULES = [
    Rule("missing_worry", "emotional", _r_missing_worry),
    Rule("clue_hope", "emotional", _r_clue_hope),
    Rule("found_relief", "emotional", _r_found_relief),
    Rule("repaired_song", "physical", _r_repaired_song),
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
                produced.extend(sents)
    if narrate:
        for sent in produced:
            world.say(sent)
    return produced


def clue_fits(place: Place, clue: Clue) -> bool:
    return clue.id in place.clue_ids


def professor_reaches(professor: Professor, place: Place) -> bool:
    return place.id in professor.reach


def gift_fits(place: Place, gift: Gift) -> bool:
    return gift.id in place.gift_ids


def valid_combo(professor: Professor, place: Place, clue: Clue, gift: Gift) -> bool:
    return clue_fits(place, clue) and professor_reaches(professor, place) and gift_fits(place, gift)


def valid_combos() -> list[tuple[str, str, str, str]]:
    out = []
    for prof_id, prof in PROFESSORS.items():
        for place_id, place in PLACES.items():
            for clue_id, clue in CLUES.items():
                for gift_id, gift in GIFTS.items():
                    if valid_combo(prof, place, clue, gift):
                        out.append((prof_id, place_id, clue_id, gift_id))
    return out


def explain_rejection(professor: Professor, place: Place, clue: Clue, gift: Gift) -> str:
    if not clue_fits(place, clue):
        return (
            f"(No story: {clue.phrase} does not honestly point to {place.phrase}. "
            f"Pick a clue that belongs in that place.)"
        )
    if not professor_reaches(professor, place):
        return (
            f"(No story: {professor.title} cannot reasonably reach {place.phrase}. "
            f"Pick a place the professor could really visit.)"
        )
    if not gift_fits(place, gift):
        return (
            f"(No story: {gift.phrase} does not fit the little repair scene at {place.phrase}. "
            f"Choose a gentler finishing gift for that place.)"
        )
    return "(No story: that combination is not reasonable in this world.)"


def predict_twist(world: World) -> dict:
    sim = world.copy()
    card = sim.get("card")
    gift = sim.get("gift")
    card.meters["found"] += 1
    gift.meters["used"] += 1
    propagate(sim, narrate=False)
    return {
        "found": card.meters["found"] >= THRESHOLD,
        "repaired": card.meters["repaired"] >= THRESHOLD,
        "joy": sim.get("child").memes["joy"],
    }


def opening(world: World, child_cfg: Child, parent: Entity) -> None:
    child = world.get("child")
    card = world.get("card")
    child.memes["joy"] += 1
    world.say(
        f"{child.id} had {child_cfg.favorite}, and every evening {child.pronoun()} sang from a tiny song card by the cradle-light."
    )
    world.say(
        f"On this night {child_cfg.opening}, and {child.id} held the card close as {parent.label_word} tucked the blanket neat."
    )
    world.say(
        f'"Hush now, moon now, silver bright,\nKeep my little song tonight."'
    )
    card.meters["sung"] += 1


def loss(world: World) -> None:
    child = world.get("child")
    card = world.get("card")
    card.meters["missing"] += 1
    propagate(world, narrate=False)
    world.say(
        f"But when {child.id} turned the card for the last sweet line, it was gone. Gone from the stool, gone from the quilt, gone from the sleepy room."
    )
    world.say(
        f'"Who did take my song?" {child.id} whispered, with eyes round as buttons.'
    )


def enter_professor(world: World, professor_cfg: Professor) -> None:
    prof = world.get("professor")
    child = world.get("child")
    prof.memes["calm"] += 1
    child.memes["trust"] += 1
    world.say(
        f"Just then came {professor_cfg.title}, {professor_cfg.gait}, with a {professor_cfg.voice} voice and spectacles that caught the moon."
    )
    world.say(
        f'"Take three small steps and one soft look," said the professor. "A missing rhyme leaves little footprints."'
    )


def notice_clue(world: World, clue_cfg: Clue, place_cfg: Place) -> None:
    clue = world.get("clue")
    child = world.get("child")
    clue.meters["noticed"] += 1
    propagate(world, narrate=False)
    world.say(
        f"So {child.id} did {clue_cfg.verb}, and there it was: {clue_cfg.phrase}."
    )
    world.say(
        f'"That means the song went toward {place_cfg.line}," said the professor.'
    )


def search_place(world: World, place_cfg: Place) -> None:
    child = world.get("child")
    prof = world.get("professor")
    child.meters["steps"] += 3
    prof.meters["steps"] += 2
    world.say(
        f"They tiptoed past the pot of mint and under the old clock, until they came to {place_cfg.phrase}."
    )
    world.say(place_cfg.image)


def reveal_twist(world: World, professor_cfg: Professor, gift_cfg: Gift, place_cfg: Place) -> None:
    child = world.get("child")
    prof = world.get("professor")
    card = world.get("card")
    gift = world.get("gift")
    world.say(
        f"There sat the missing card, and beside it lay {gift_cfg.phrase}."
    )
    world.say(
        f'{child.id} blinked. "Professor, did you take it?"'
    )
    prof.memes["shy"] += 1
    prof.memes["care"] += 1
    world.say(
        f'"I did," said {professor_cfg.title}, smoothing {prof.pronoun("possessive")} coat. "I am the village lyric-ist, and your last line limped a little. I took the card to mend it before bedtime."'
    )
    card.meters["found"] += 1
    gift.meters["used"] += 1
    propagate(world, narrate=False)
    world.facts["twist_revealed"] = True
    world.facts["took_it"] = True
    world.facts["reason"] = "repair"
    world.say(
        gift_cfg.repair_text
    )


def ending(world: World, gift_cfg: Gift) -> None:
    child = world.get("child")
    parent = world.get("parent")
    world.say(
        f"Then {child.id} laughed the worry away, for the card was back and the song was better than before."
    )
    world.say(
        f'{parent.label_word.capitalize()} kissed {child.pronoun("possessive")} hair, and all together they sang,\n"{gift_cfg.ending_line}"'
    )
    world.say(
        "So hush now, moon now, over roof and mist: the professor had been the lyric-ist."
    )


def tell(child_cfg: Child, professor_cfg: Professor, place_cfg: Place,
         clue_cfg: Clue, gift_cfg: Gift, parent_type: str = "mother") -> World:
    world = World()
    child = world.add(Entity(id=child_cfg.id, kind="character", type="girl",
                             label=child_cfg.id, role="child", traits=[child_cfg.trait]))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type,
                              label="the parent", role="parent"))
    professor = world.add(Entity(id="Professor", kind="character", type=professor_cfg.type,
                                 label=professor_cfg.label, role="professor",
                                 traits=["gentle", "wise"]))
    card = world.add(Entity(id="card", type="song_card", label="song card"))
    clue = world.add(Entity(id="clue", type="clue", label=clue_cfg.label))
    gift = world.add(Entity(id="gift", type="gift", label=gift_cfg.label))
    place = world.add(Entity(id="place", type="place", label=place_cfg.label))

    world.facts.update(
        child_cfg=child_cfg,
        professor_cfg=professor_cfg,
        place_cfg=place_cfg,
        clue_cfg=clue_cfg,
        gift_cfg=gift_cfg,
        child=child,
        parent=parent,
        professor=professor,
        card=card,
        clue=clue,
        gift=gift,
        place=place,
        twist_revealed=False,
        took_it=False,
        reason="",
    )

    opening(world, child_cfg, parent)
    world.para()
    loss(world)
    enter_professor(world, professor_cfg)
    world.para()
    notice_clue(world, clue_cfg, place_cfg)
    search_place(world, place_cfg)
    world.para()
    reveal_twist(world, professor_cfg, gift_cfg, place_cfg)
    ending(world, gift_cfg)
    return world


CHILDREN = {
    "Mina": Child("Mina", "humming", "a cradle song", "the room was soft and still", tags={"song", "bedtime"}),
    "Poppy": Child("Poppy", "twirling", "a ribbon song", "the lamp made a butter-yellow ring", tags={"song", "bedtime"}),
    "Lark": Child("Lark", "listening", "a moon song", "the window hummed with crickets", tags={"song", "bedtime"}),
}

PROFESSORS = {
    "owl": Professor(
        "owl", "Professor Owl", "owl", "Professor Owl",
        "gliding from the curtain rod", "round and velvety",
        {"reed_nest", "satchel", "bell_loft"}, "midnight couplets",
        tags={"owl", "professor"}
    ),
    "mole": Professor(
        "mole", "Professor Mole", "mole", "Professor Mole",
        "popping up from a flower pot", "muffled and kind",
        {"satchel", "reed_nest"}, "soft underground verses",
        tags={"mole", "professor"}
    ),
    "tortoise": Professor(
        "tortoise", "Professor Tortoise", "tortoise", "Professor Tortoise",
        "padding slow as a clock hand", "dry and careful",
        {"satchel"}, "measured little rhymes",
        tags={"tortoise", "professor"}
    ),
}

PLACES = {
    "reed_nest": Place(
        "reed_nest", "reed nest", "a reed nest by the washstand",
        "the little nest by the washstand",
        {"owl", "mole"}, {"feather", "dew_drop"}, {"blue_ribbon"},
        "The reeds made a tiny rustly cradle, and something pale peeked between them.",
        tags={"nest"}
    ),
    "satchel": Place(
        "satchel", "satchel", "the professor's satchel under the bench",
        "the satchel under the bench",
        {"owl", "mole", "tortoise"}, {"ink_dot", "button"}, {"gold_nib", "blue_ribbon"},
        "The satchel bulged kindly, as if it were hiding a secret instead of a snack.",
        tags={"satchel"}
    ),
    "bell_loft": Place(
        "bell_loft", "bell loft", "the bell loft above the nursery door",
        "the bell loft above the nursery door",
        {"owl"}, {"silver_thread"}, {"gold_nib"},
        "Above them the bell rope swayed, and the moon laid a ladder on the wall.",
        tags={"loft"}
    ),
}

CLUES = {
    "feather": Clue(
        "feather", "feather", "a downy feather with one dab of moonlight on it",
        "look just where the floorboards crossed",
        "nest",
        tags={"feather"}
    ),
    "dew_drop": Clue(
        "dew_drop", "dew drop", "three round dew drops shining on the sill",
        "peer along the sill with a rabbit-quiet face",
        "nest",
        tags={"dew"}
    ),
    "ink_dot": Clue(
        "ink_dot", "ink dot", "a neat black ink dot no bigger than a poppy seed",
        "bend low beside the bench",
        "satchel",
        tags={"ink"}
    ),
    "button": Clue(
        "button", "button", "a brass button that had rolled and winked in the lamplight",
        "pat the rug and listen for a click",
        "satchel",
        tags={"button"}
    ),
    "silver_thread": Clue(
        "silver_thread", "silver thread", "a silver thread dangling where the bell rope swung",
        "look high and hold the candle-shade still",
        "loft",
        tags={"thread"}
    ),
}

GIFTS = {
    "blue_ribbon": Gift(
        "blue_ribbon", "blue ribbon", "a blue ribbon tied around the card",
        'Around the card was a blue ribbon, and on the back the professor had written a new tail line in tidy moonlit letters.',
        "Take this tune and tuck it tight,\nSing it once and sleep all night.",
        tags={"ribbon"}
    ),
    "gold_nib": Gift(
        "gold_nib", "gold nib", "a little gold nib wrapped in tissue",
        'Beside the card was a little gold nib, and the professor had used it to make the last line skip smoothly instead of stumble.',
        "Take this rhyme and hold it light,\nStars will keep your cradle bright.",
        tags={"ink", "nib"}
    ),
}

GIRL_NAMES = ["Mina", "Poppy", "Lark"]
TRAITS = ["humming", "twirling", "listening"]


@dataclass
class StoryParams:
    child: str
    professor: str
    place: str
    clue: str
    gift: str
    parent: str
    seed: Optional[int] = None


KNOWLEDGE = {
    "owl": [("What is an owl?",
             "An owl is a bird with soft feathers and large eyes. Many owls fly quietly at night.")],
    "mole": [("What is a mole?",
              "A mole is a small animal that digs underground. It has strong front paws for scooping soil.")],
    "tortoise": [("What is a tortoise?",
                  "A tortoise is a slow animal with a hard shell. It walks carefully and can live a very long time.")],
    "ink": [("What is ink for?",
             "Ink is the colored liquid used for writing. It helps letters stay on paper.")],
    "feather": [("What is a feather?",
                 "A feather helps a bird stay warm and fly. Feathers are soft and light.")],
    "ribbon": [("What is a ribbon?",
                "A ribbon is a soft strip of cloth used for tying or decorating things.")],
    "song": [("What is a lullaby?",
              "A lullaby is a soft song sung at bedtime. It helps children feel calm and sleepy.")],
    "bedtime": [("Why do bedtime songs help?",
                 "A bedtime song can make the room feel gentle and safe. A calm rhythm helps your body settle down.")],
    "professor": [("What is a professor?",
                   "A professor is a person who studies, teaches, and explains things carefully. In stories, a professor often helps others understand a puzzle.")],
    "lyricist": [("What is a lyric-ist?",
                  "A lyric-ist writes the words of a song. They listen for lines that sound good when people sing them.")],
}

KNOWLEDGE_ORDER = ["song", "bedtime", "professor", "lyricist", "owl", "mole", "tortoise", "ink", "feather", "ribbon"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child_cfg"]
    prof = f["professor_cfg"]
    place = f["place_cfg"]
    clue = f["clue_cfg"]
    return [
        'Write a nursery-rhyme-style story for a 3-to-5-year-old that includes the exact word "lyric-ist" and the word "professor", and uses a gentle twist.',
        f"Tell a bedtime rhyme-story where {child.id}'s song seems to have been taken, {prof.title} gives a clue, and the search leads to {place.phrase}.",
        f'Write a short story with a twist where a child follows {clue.label} clues, asks who did take the song card, and ends by singing a mended rhyme.'
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    parent = f["parent"]
    prof = f["professor_cfg"]
    place = f["place_cfg"]
    clue = f["clue_cfg"]
    gift = f["gift_cfg"]
    qa: list[tuple[str, str]] = [
        ("Who is the story about?",
         f"It is about {child.id}, a child getting ready for bed, and {prof.title} who helps with a missing song. The story also includes {parent.label_word} in the bedtime room."),
        ("What was missing?",
         f"The little song card was missing when {child.id} reached for the last line. That made the bedtime song stop in the middle and worried {child.pronoun('object')}."),
        ("What clue did the child follow?",
         f"{child.id} followed {clue.phrase}. The clue mattered because it pointed toward {place.phrase}."),
        ("Where did they search?",
         f"They searched at {place.phrase}. The trip there turned the worry into a small moonlit adventure."),
    ]
    if f.get("twist_revealed"):
        qa.append((
            "What was the twist?",
            f"The professor had taken the card, but not to be mean. {prof.title} was secretly the village lyric-ist and had taken it only to mend the last line."
        ))
        qa.append((
            "Why did the professor take the card?",
            f"{prof.title} took the card to repair the song so it would sing more smoothly at bedtime. The gift beside it showed care, not stealing."
        ))
        qa.append((
            "How did the story end?",
            f"It ended with the card returned, a repaired rhyme, and everyone singing together. The new ending line and {gift.label} proved that the loss had become a kindness."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = {"song", "bedtime", "professor", "lyricist"}
    prof_id = f["professor_cfg"].id
    clue_id = f["clue_cfg"].id
    gift_id = f["gift_cfg"].id
    if prof_id == "owl":
        tags.add("owl")
    elif prof_id == "mole":
        tags.add("mole")
    elif prof_id == "tortoise":
        tags.add("tortoise")
    if clue_id in {"ink_dot"} or gift_id == "gold_nib":
        tags.add("ink")
    if clue_id == "feather":
        tags.add("feather")
    if gift_id == "blue_ribbon":
        tags.add("ribbon")
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
        if ent.traits:
            bits.append(f"traits={ent.traits}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.attrs:
            bits.append(f"attrs={ent.attrs}")
        lines.append(f"  {ent.id:10} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams("Mina", "owl", "bell_loft", "silver_thread", "gold_nib", "mother"),
    StoryParams("Poppy", "mole", "reed_nest", "feather", "blue_ribbon", "father"),
    StoryParams("Lark", "tortoise", "satchel", "ink_dot", "gold_nib", "mother"),
    StoryParams("Mina", "owl", "satchel", "button", "blue_ribbon", "mother"),
]


ASP_RULES = r"""
fits_clue(P, C) :- place(P), clue(C), place_has_clue(P, C).
fits_gift(P, G) :- place(P), gift(G), place_has_gift(P, G).
reachable(Pr, P) :- professor(Pr), place(P), reaches(Pr, P).

valid(Pr, P, C, G) :- professor(Pr), place(P), clue(C), gift(G),
                      fits_clue(P, C), fits_gift(P, G), reachable(Pr, P).

twist_kind(repair) :- chosen_professor(_), chosen_place(_), chosen_clue(_), chosen_gift(_), valid_choice.
valid_choice :- valid(Pr, P, C, G), chosen_professor(Pr), chosen_place(P), chosen_clue(C), chosen_gift(G).

outcome(twist_repair) :- valid_choice, twist_kind(repair).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for cid in CHILDREN:
        lines.append(asp.fact("child", cid))
    for pid in PROFESSORS:
        lines.append(asp.fact("professor", pid))
    for plid, place in PLACES.items():
        lines.append(asp.fact("place", plid))
        for clue_id in sorted(place.clue_ids):
            lines.append(asp.fact("place_has_clue", plid, clue_id))
        for gift_id in sorted(place.gift_ids):
            lines.append(asp.fact("place_has_gift", plid, gift_id))
    for clue_id in CLUES:
        lines.append(asp.fact("clue", clue_id))
    for gift_id in GIFTS:
        lines.append(asp.fact("gift", gift_id))
    for pid, prof in PROFESSORS.items():
        for place_id in sorted(prof.reach):
            lines.append(asp.fact("reaches", pid, place_id))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp
    extra = "\n".join([
        asp.fact("chosen_professor", params.professor),
        asp.fact("chosen_place", params.place),
        asp.fact("chosen_clue", params.clue),
        asp.fact("chosen_gift", params.gift),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def outcome_of(params: StoryParams) -> str:
    if valid_combo(PROFESSORS[params.professor], PLACES[params.place], CLUES[params.clue], GIFTS[params.gift]):
        return "twist_repair"
    return "?"


def asp_verify() -> int:
    rc = 0
    cset = set(asp_valid_combos())
    pset = set(valid_combos())
    if cset == pset:
        print(f"OK: gate matches valid_combos() ({len(cset)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if cset - pset:
            print("  only in clingo:", sorted(cset - pset))
        if pset - cset:
            print("  only in python:", sorted(pset - cset))
    cases = list(CURATED)
    for params in cases:
        if asp_outcome(params) != outcome_of(params):
            rc = 1
            print("MISMATCH in outcome for:", params)
            break
    else:
        print(f"OK: outcome model matches on {len(cases)} curated scenarios.")
    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("(Verify failed: empty story.)")
        print("OK: smoke test story generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"VERIFY SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Nursery-rhyme story world: a missing song, a professor, and a gentle twist."
    )
    ap.add_argument("--child", choices=CHILDREN)
    ap.add_argument("--professor", choices=PROFESSORS)
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--gift", choices=GIFTS)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid combos from clingo")
    ap.add_argument("--verify", action="store_true", help="check Python/ASP parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.professor and args.place and args.clue and args.gift:
        prof = PROFESSORS[args.professor]
        place = PLACES[args.place]
        clue = CLUES[args.clue]
        gift = GIFTS[args.gift]
        if not valid_combo(prof, place, clue, gift):
            raise StoryError(explain_rejection(prof, place, clue, gift))

    combos = [
        combo for combo in valid_combos()
        if (args.professor is None or combo[0] == args.professor)
        and (args.place is None or combo[1] == args.place)
        and (args.clue is None or combo[2] == args.clue)
        and (args.gift is None or combo[3] == args.gift)
    ]
    if not combos:
        if args.professor and args.place and args.clue and args.gift:
            raise StoryError(explain_rejection(PROFESSORS[args.professor], PLACES[args.place], CLUES[args.clue], GIFTS[args.gift]))
        raise StoryError("(No valid combination matches the given options.)")

    professor, place, clue, gift = rng.choice(sorted(combos))
    child = args.child or rng.choice(sorted(CHILDREN))
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(child, professor, place, clue, gift, parent)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        CHILDREN[params.child],
        PROFESSORS[params.professor],
        PLACES[params.place],
        CLUES[params.clue],
        GIFTS[params.gift],
        params.parent,
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
        print(asp_program("", "#show valid/4.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (professor, place, clue, gift) combos:\n")
        for professor, place, clue, gift in combos:
            print(f"  {professor:9} {place:10} {clue:13} {gift}")
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
            header = f"### {p.child}: {p.professor} at {p.place} ({p.clue}, {p.gift})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
