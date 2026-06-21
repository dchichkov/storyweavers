#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/dadda_junk_immature_problem_solving_quest_curiosity.py
=================================================================================

A standalone storyworld for a tiny child-facing whodunit: Dadda prepares a small
quest, the first clue goes missing, and two children solve the case by following
real evidence instead of making an immature guess.

Seed words and features:
- words: dadda, junk, immature
- features: Problem Solving, Quest, Curiosity
- style: Whodunit

Run it
------
python storyworlds/worlds/gpt-5.4/dadda_junk_immature_problem_solving_quest_curiosity.py
python storyworlds/worlds/gpt-5.4/dadda_junk_immature_problem_solving_quest_curiosity.py --place backyard --item paper_clue --culprit wind --method flutter
python storyworlds/worlds/gpt-5.4/dadda_junk_immature_problem_solving_quest_curiosity.py --method accuse_friend
python storyworlds/worlds/gpt-5.4/dadda_junk_immature_problem_solving_quest_curiosity.py --all --qa
python storyworlds/worlds/gpt-5.4/dadda_junk_immature_problem_solving_quest_curiosity.py --verify
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
SENSE_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
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

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Place:
    id: str
    label: str
    opening: str
    junk_spot: str
    features: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class MissingItem:
    id: str
    label: str
    phrase: str
    material: str
    light: bool
    shiny: bool
    tags: set[str] = field(default_factory=set)


@dataclass
class Culprit:
    id: str
    label: str
    phrase: str
    stash_name: str
    stash_template: str
    needs_place: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Method:
    id: str
    label: str
    sense: int
    fits: set[str] = field(default_factory=set)
    needs_place: set[str] = field(default_factory=set)
    clue_text: str = ""
    solve_text: str = ""
    qa_text: str = ""
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


PLACES = {
    "backyard": Place(
        id="backyard",
        label="the backyard",
        opening="The backyard smelled like sun-warmed grass, and the stepping stones made a perfect path for a mystery.",
        junk_spot="a leaning pile of garden junk beside the shed",
        features={"outdoor", "soft_ground", "breezy", "high_perch", "junk"},
        tags={"yard", "junk"},
    ),
    "porch": Place(
        id="porch",
        label="the front porch",
        opening="The front porch creaked softly, with flowerpots on one side and a little bench on the other.",
        junk_spot="a wooden crate of old junk under the bench",
        features={"outdoor", "breezy", "high_perch", "junk"},
        tags={"porch", "junk"},
    ),
    "garage": Place(
        id="garage",
        label="the garage",
        opening="The garage was cool and dusty, with tool hooks on the wall and boxes stacked like tiny towers.",
        junk_spot="a big hill of harmless junk near the worktable",
        features={"indoor", "soft_ground", "junk"},
        tags={"garage", "junk"},
    ),
}

ITEMS = {
    "paper_clue": MissingItem(
        id="paper_clue",
        label="paper clue",
        phrase="a folded paper clue with a moon drawn on it",
        material="paper",
        light=True,
        shiny=False,
        tags={"paper", "clue"},
    ),
    "ribbon_badge": MissingItem(
        id="ribbon_badge",
        label="ribbon badge",
        phrase="a blue ribbon badge for the winner",
        material="ribbon",
        light=True,
        shiny=True,
        tags={"ribbon", "badge"},
    ),
    "brass_key": MissingItem(
        id="brass_key",
        label="brass key",
        phrase="a small brass key for the treasure box",
        material="metal",
        light=False,
        shiny=True,
        tags={"key", "shiny"},
    ),
}

CULPRITS = {
    "puppy": Culprit(
        id="puppy",
        label="puppy",
        phrase="the wiggly puppy",
        stash_name="basket",
        stash_template="inside the puppy's basket beside {junk_spot}",
        needs_place={"soft_ground", "junk"},
        tags={"animal", "tracks"},
    ),
    "wind": Culprit(
        id="wind",
        label="wind",
        phrase="a sneaky gust of wind",
        stash_name="junk_pile",
        stash_template="under a curled tin edge in {junk_spot}",
        needs_place={"breezy", "junk"},
        tags={"weather", "breeze"},
    ),
    "crow": Culprit(
        id="crow",
        label="crow",
        phrase="the glossy black crow",
        stash_name="high_shelf",
        stash_template="on a high ledge above {junk_spot}",
        needs_place={"outdoor", "high_perch", "junk"},
        tags={"bird", "high"},
    ),
}

METHODS = {
    "tracks": Method(
        id="tracks",
        label="follow the little tracks",
        sense=3,
        fits={"puppy"},
        needs_place={"soft_ground"},
        clue_text="On the ground, they spotted a row of tiny prints curving away from the stool.",
        solve_text="The prints led them straight to the puppy's basket.",
        qa_text="They followed the little tracks to the puppy's basket.",
        tags={"tracks", "problem_solving"},
    ),
    "flutter": Method(
        id="flutter",
        label="watch where the fluttering bits went",
        sense=3,
        fits={"wind"},
        needs_place={"breezy"},
        clue_text="A corner of something light kept trembling whenever the breeze slipped by.",
        solve_text="The fluttering edge showed them exactly where the missing thing had been tucked by the wind.",
        qa_text="They watched the fluttering edge and saw where the wind had pushed it.",
        tags={"wind", "problem_solving"},
    ),
    "look_up": Method(
        id="look_up",
        label="look up high for shiny things",
        sense=3,
        fits={"crow"},
        needs_place={"high_perch"},
        clue_text="Up above, something gave a tiny blink of light from a high place.",
        solve_text="When they looked up together, they saw the missing thing resting on a high ledge.",
        qa_text="They looked up high and spotted the missing thing on a ledge.",
        tags={"crow", "problem_solving"},
    ),
    "accuse_friend": Method(
        id="accuse_friend",
        label="blame the other child first",
        sense=1,
        fits=set(),
        needs_place=set(),
        clue_text="",
        solve_text="",
        qa_text="",
        tags={"blame"},
    ),
}


def culprit_can_take(item: MissingItem, culprit: Culprit) -> bool:
    if culprit.id == "puppy":
        return item.light
    if culprit.id == "wind":
        return item.material in {"paper", "ribbon"}
    if culprit.id == "crow":
        return item.shiny
    return False


def place_allows(place: Place, culprit: Culprit) -> bool:
    return culprit.needs_place <= place.features


def method_works(place: Place, culprit: Culprit, method: Method) -> bool:
    return method.sense >= SENSE_MIN and culprit.id in method.fits and method.needs_place <= place.features


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for place_id, place in PLACES.items():
        for item_id, item in ITEMS.items():
            for culprit_id, culprit in CULPRITS.items():
                if not culprit_can_take(item, culprit):
                    continue
                if not place_allows(place, culprit):
                    continue
                for method_id, method in METHODS.items():
                    if method_works(place, culprit, method):
                        combos.append((place_id, item_id, culprit_id, method_id))
    return combos


def outcome_of(place_id: str, item_id: str, culprit_id: str, method_id: str) -> str:
    place = PLACES[place_id]
    item = ITEMS[item_id]
    culprit = CULPRITS[culprit_id]
    method = METHODS[method_id]
    return "solved" if culprit_can_take(item, culprit) and place_allows(place, culprit) and method_works(place, culprit, method) else "unsolved"


def explain_bad_method(method_id: str) -> str:
    if method_id == "accuse_friend":
        return "(Refusing method 'accuse_friend': a detective story should use clues, not an immature blame-first guess. Try tracks, flutter, or look_up.)"
    return f"(Refusing method '{method_id}': it is not a sensible detective method here.)"


def explain_rejection(place: Place, item: MissingItem, culprit: Culprit, method: Optional[Method] = None) -> str:
    if not culprit_can_take(item, culprit):
        return f"(No story: {culprit.label} would not reasonably carry or move the {item.label}.)"
    if not place_allows(place, culprit):
        return f"(No story: {culprit.label} does not fit the evidence and hiding places available at {place.label}.)"
    if method is not None and not method_works(place, culprit, method):
        return f"(No story: {method.label} would not reveal {culprit.label} at {place.label}.)"
    return "(No story: this combination does not make a clear whodunit.)"


def culprit_clue(place: Place, culprit: Culprit, item: MissingItem) -> str:
    if culprit.id == "puppy":
        return f"The clue card had been on a low stool, easy for curious paws to reach."
    if culprit.id == "wind":
        return f"The {item.label} was light enough for a busy breeze to push."
    return f"The {item.label} had a bit of shine, just the sort of thing a crow might fancy."


def stash_text(place: Place, culprit: Culprit) -> str:
    return culprit.stash_template.format(junk_spot=place.junk_spot)


def move_item(world: World, culprit: Culprit, item_ent: Entity) -> None:
    item_ent.meters["missing"] += 1
    item_ent.attrs["stash"] = stash_text(world.place, culprit)
    item_ent.attrs["moved_by"] = culprit.id
    world.facts["missing"] = True
    sig = ("missing", culprit.id, item_ent.id)
    if sig not in world.fired:
        world.fired.add(sig)
        for eid in ("hero", "partner"):
            if eid in world.entities:
                world.get(eid).memes["curiosity"] += 1
        item_ent.meters["distance"] += 1


def introduce(world: World, hero: Entity, partner: Entity, dadda: Entity, item: MissingItem) -> None:
    world.say(
        f"{hero.id} and {partner.id} were helping their dadda build a tiny mystery quest at {world.place.label}."
    )
    world.say(world.place.opening)
    world.say(
        f"Dadda set out {item.phrase} on a stool and whispered, "
        f'"When you find this first clue, the quest begins."'
    )


def discovery(world: World, hero: Entity, partner: Entity, item_ent: Entity) -> None:
    hero.memes["surprise"] += 1
    partner.memes["surprise"] += 1
    world.say(
        f"But when {hero.id} reached for the {item_ent.label}, it was gone."
    )
    world.say(
        f'"A mystery before the quest!" {partner.id} gasped. Both children leaned close, full of curiosity.'
    )


def warning(world: World, dadda: Entity, hero: Entity, partner: Entity, culprit: Culprit, item: MissingItem) -> None:
    world.say(
        f'{partner.id} opened {partner.pronoun("possessive")} mouth to guess, but Dadda lifted one finger. '
        f'"Real detectives do not blame people before they have clues," dadda said softly.'
    )
    world.say(
        f'"A blame-first guess is immature detective work. Start with what the world shows you."'
    )
    world.say(culprit_clue(world.place, culprit, item))


def investigate(world: World, hero: Entity, partner: Entity, method: Method) -> None:
    hero.memes["focus"] += 1
    partner.memes["focus"] += 1
    world.say(
        f"So the two detectives began to {method.label}. {method.clue_text}"
    )


def solve(world: World, hero: Entity, partner: Entity, dadda: Entity, culprit: Culprit, item_ent: Entity, method: Method) -> None:
    item_ent.meters["missing"] = 0.0
    item_ent.meters["found"] += 1
    hero.memes["relief"] += 1
    partner.memes["relief"] += 1
    hero.memes["joy"] += 1
    partner.memes["joy"] += 1
    world.say(method.solve_text)
    world.say(
        f"There, {hero.id} found the {item_ent.label} {item_ent.attrs['stash']}."
    )
    if culprit.id == "puppy":
        world.say(
            "The puppy thumped its tail as if it had been playing a game all along."
        )
    elif culprit.id == "wind":
        world.say(
            "The breeze gave one last small puff, as if it were admitting the trick."
        )
    else:
        world.say(
            "Above them, the crow gave a croaky caw and hopped away from the ledge."
        )
    world.say(
        f'Dadda smiled. "Now that is good problem solving," {dadda.pronoun()} said.'
    )


def ending(world: World, hero: Entity, partner: Entity, dadda: Entity, item_ent: Entity) -> None:
    world.say(
        f'With the {item_ent.label} safe again, Dadda tapped the card and said, "Quest first clue restored."'
    )
    world.say(
        f"{hero.id} held the clue, {partner.id} held the treasure box, and together they marched past {world.place.junk_spot} toward the next secret."
    )


def tell(place: Place, item: MissingItem, culprit: Culprit, method: Method, hero_name: str, hero_gender: str, partner_name: str, partner_gender: str, dadda_type: str) -> World:
    world = World(place=place)
    hero = world.add(Entity(id="hero", kind="character", type=hero_gender, label=hero_name, attrs={"name": hero_name}))
    partner = world.add(Entity(id="partner", kind="character", type=partner_gender, label=partner_name, attrs={"name": partner_name}))
    dadda = world.add(Entity(id="dadda", kind="character", type=dadda_type, label="dadda", attrs={"name": "Dadda"}))
    item_ent = world.add(Entity(id="item", kind="thing", type="clue", label=item.label, attrs={"phrase": item.phrase}, tags=set(item.tags)))
    culprit_ent = world.add(Entity(id="culprit", kind="thing", type=culprit.id, label=culprit.label, tags=set(culprit.tags)))

    world.facts.update(
        place=place,
        item_cfg=item,
        culprit_cfg=culprit,
        method_cfg=method,
        hero=hero,
        partner=partner,
        dadda=dadda,
        item=item_ent,
        culprit=culprit_ent,
    )

    introduce(world, hero, partner, dadda, item)
    move_item(world, culprit, item_ent)
    discovery(world, hero, partner, item_ent)

    world.para()
    warning(world, dadda, hero, partner, culprit, item)
    investigate(world, hero, partner, method)

    world.para()
    solve(world, hero, partner, dadda, culprit, item_ent, method)
    ending(world, hero, partner, dadda, item_ent)

    world.facts.update(
        outcome="solved",
        stash=item_ent.attrs.get("stash", ""),
        quest_started=item_ent.meters["found"] >= THRESHOLD,
    )
    return world


def pair_noun(hero: Entity, partner: Entity) -> str:
    if hero.type == "girl" and partner.type == "girl":
        return "two little detectives"
    if hero.type == "boy" and partner.type == "boy":
        return "two little detectives"
    return "two little detectives"


GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Nora", "Ella"]
BOY_NAMES = ["Ben", "Max", "Theo", "Sam", "Leo", "Finn"]


@dataclass
class StoryParams:
    place: str
    item: str
    culprit: str
    method: str
    hero_name: str
    hero_gender: str
    partner_name: str
    partner_gender: str
    dadda_type: str
    seed: Optional[int] = None


CURATED = [
    StoryParams(
        place="backyard",
        item="paper_clue",
        culprit="wind",
        method="flutter",
        hero_name="Lily",
        hero_gender="girl",
        partner_name="Ben",
        partner_gender="boy",
        dadda_type="father",
    ),
    StoryParams(
        place="garage",
        item="ribbon_badge",
        culprit="puppy",
        method="tracks",
        hero_name="Mia",
        hero_gender="girl",
        partner_name="Theo",
        partner_gender="boy",
        dadda_type="father",
    ),
    StoryParams(
        place="porch",
        item="brass_key",
        culprit="crow",
        method="look_up",
        hero_name="Nora",
        hero_gender="girl",
        partner_name="Max",
        partner_gender="boy",
        dadda_type="father",
    ),
]


KNOWLEDGE = {
    "tracks": [
        (
            "What can tracks tell you?",
            "Tracks can show where someone or something went. Careful detectives follow them instead of guessing."
        )
    ],
    "wind": [
        (
            "Can wind move light things?",
            "Yes. A strong little gust can push paper or ribbon into a new place, especially near loose junk or corners."
        )
    ],
    "crow": [
        (
            "Why might a crow take something shiny?",
            "Crows are curious birds, and shiny things can catch their eye. A crow may carry one to a high spot to inspect it."
        )
    ],
    "quest": [
        (
            "What is a quest?",
            "A quest is a little adventure with a goal. It often has clues, steps, or a treasure to find."
        )
    ],
    "problem_solving": [
        (
            "What is problem solving?",
            "Problem solving means looking at what happened, thinking carefully, and trying a smart next step. It works better than blaming someone without proof."
        )
    ],
    "junk": [
        (
            "What does junk mean?",
            "Junk means old odds and ends that are not being used right now. Even a junk pile can hide a clue."
        )
    ],
}


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    partner = f["partner"]
    item = f["item_cfg"]
    culprit = f["culprit_cfg"]
    return [
        'Write a short whodunit for a 3-to-5-year-old that includes the words "dadda", "junk", and "immature".',
        f"Tell a gentle mystery where {hero.label} and {partner.label} are about to start a quest, but the {item.label} goes missing and the clue points to {culprit.label}.",
        "Write a child-facing story about curiosity and problem solving where a family solves a tiny mystery by following evidence instead of making an immature accusation.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    partner = f["partner"]
    item = f["item"]
    culprit = f["culprit_cfg"]
    method = f["method_cfg"]
    place = f["place"]
    return [
        (
            "Who is the story about?",
            f"It is about {pair_noun(hero, partner)}, {hero.label} and {partner.label}, and their dadda. They were getting ready for a little quest when the first clue disappeared."
        ),
        (
            f"What went missing before the quest began?",
            f"The missing thing was the {item.label}. Dadda had set it out as the first clue, so the mystery started before the quest even began."
        ),
        (
            "Why did Dadda say blaming first would be immature?",
            "Dadda wanted the children to use real clues instead of guessing. A blame-first guess can hurt feelings and miss the true answer."
        ),
        (
            f"How did the children solve the mystery?",
            f"They chose to {method.label}, and {method.qa_text} That clue matched what the world around them was showing."
        ),
        (
            f"Where did they find the {item.label}?",
            f"They found it {f['stash']}. That hiding place fit the real culprit and proved their careful problem solving worked."
        ),
        (
            "How did the story end?",
            f"The clue was safe again, and the quest could finally begin. The ending shows the change clearly: the mystery was solved, and the children walked on together with confidence."
        ),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"quest", "problem_solving", "junk"}
    method = world.facts["method_cfg"]
    culprit = world.facts["culprit_cfg"]
    if method.id == "tracks":
        tags.add("tracks")
    if culprit.id == "wind":
        tags.add("wind")
    if culprit.id == "crow":
        tags.add("crow")
    out: list[tuple[str, str]] = []
    for key in ["quest", "problem_solving", "junk", "tracks", "wind", "crow"]:
        if key in tags:
            out.extend(KNOWLEDGE[key])
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
    for ent in world.entities.values():
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if ent.label:
            bits.append(f"label={ent.label!r}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        attrs = {k: v for k, v in ent.attrs.items() if v}
        if attrs:
            bits.append(f"attrs={attrs}")
        if ent.tags:
            bits.append(f"tags={sorted(ent.tags)}")
        lines.append(f"  {ent.id:8} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired={sorted(world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
% basic compatibility
culprit_can_take(C, I) :- culprit(C), item(I), can_take(C, I).
place_allows(P, C) :- place(P), culprit(C), needs_place(C, F), has_feature(P, F),
                      not missing_place_feature(P, C).
missing_place_feature(P, C) :- needs_place(C, F), not has_feature(P, F).

method_works(P, C, M) :- place(P), culprit(C), method(M),
                         sensible(M), fits(M, C),
                         not missing_method_feature(P, M).
missing_method_feature(P, M) :- method_needs(M, F), not has_feature(P, F).
sensible(M) :- method(M), sense(M, S), sense_min(N), S >= N.

valid(P, I, C, M) :- place(P), item(I), culprit(C), method(M),
                     culprit_can_take(C, I), place_allows(P, C), method_works(P, C, M).

outcome(P, I, C, M, solved) :- valid(P, I, C, M).
outcome(P, I, C, M, unsolved) :- place(P), item(I), culprit(C), method(M), not valid(P, I, C, M).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for place_id, place in PLACES.items():
        lines.append(asp.fact("place", place_id))
        for feat in sorted(place.features):
            lines.append(asp.fact("has_feature", place_id, feat))
    for item_id in ITEMS:
        lines.append(asp.fact("item", item_id))
    for culprit_id, culprit in CULPRITS.items():
        lines.append(asp.fact("culprit", culprit_id))
        for feat in sorted(culprit.needs_place):
            lines.append(asp.fact("needs_place", culprit_id, feat))
        for item_id, item in ITEMS.items():
            if culprit_can_take(item, culprit):
                lines.append(asp.fact("can_take", culprit_id, item_id))
    for method_id, method in METHODS.items():
        lines.append(asp.fact("method", method_id))
        lines.append(asp.fact("sense", method_id, method.sense))
        for culprit_id in sorted(method.fits):
            lines.append(asp.fact("fits", method_id, culprit_id))
        for feat in sorted(method.needs_place):
            lines.append(asp.fact("method_needs", method_id, feat))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(place_id: str, item_id: str, culprit_id: str, method_id: str) -> str:
    import asp
    extra = "\n".join(
        [
            asp.fact("chosen_place", place_id),
            asp.fact("chosen_item", item_id),
            asp.fact("chosen_culprit", culprit_id),
            asp.fact("chosen_method", method_id),
            "selected_outcome(O) :- outcome(P,I,C,M,O), chosen_place(P), chosen_item(I), chosen_culprit(C), chosen_method(M).",
        ]
    )
    model = asp.one_model(asp_program(extra, "#show selected_outcome/1."))
    atoms = asp.atoms(model, "selected_outcome")
    return atoms[0][0] if atoms else "?"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A tiny whodunit storyworld: a missing quest clue, a real culprit, and a clue-based solution."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--culprit", choices=CULPRITS)
    ap.add_argument("--method", choices=METHODS)
    ap.add_argument("--hero-name")
    ap.add_argument("--partner-name")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--partner-gender", choices=["girl", "boy"])
    ap.add_argument("--dadda-type", choices=["father", "mother"], default=None)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid combos from the ASP twin")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run smoke tests")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [name for name in pool if name != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.method and METHODS[args.method].sense < SENSE_MIN:
        raise StoryError(explain_bad_method(args.method))
    if args.place and args.item and args.culprit:
        place = PLACES[args.place]
        item = ITEMS[args.item]
        culprit = CULPRITS[args.culprit]
        if not culprit_can_take(item, culprit) or not place_allows(place, culprit):
            method = METHODS[args.method] if args.method else None
            raise StoryError(explain_rejection(place, item, culprit, method))
    if args.place and args.culprit and args.method:
        place = PLACES[args.place]
        culprit = CULPRITS[args.culprit]
        method = METHODS[args.method]
        item = ITEMS[args.item] if args.item else next(iter(ITEMS.values()))
        if not method_works(place, culprit, method):
            raise StoryError(explain_rejection(place, item, culprit, method))

    combos = [
        combo
        for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.item is None or combo[1] == args.item)
        and (args.culprit is None or combo[2] == args.culprit)
        and (args.method is None or combo[3] == args.method)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, item_id, culprit_id, method_id = rng.choice(sorted(combos))
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    partner_gender = args.partner_gender or rng.choice(["girl", "boy"])
    hero_name = args.hero_name or pick_name(rng, hero_gender)
    partner_name = args.partner_name or pick_name(rng, partner_gender, avoid=hero_name)
    return StoryParams(
        place=place_id,
        item=item_id,
        culprit=culprit_id,
        method=method_id,
        hero_name=hero_name,
        hero_gender=hero_gender,
        partner_name=partner_name,
        partner_gender=partner_gender,
        dadda_type=args.dadda_type or "father",
    )


def generate(params: StoryParams) -> StorySample:
    try:
        place = PLACES[params.place]
        item = ITEMS[params.item]
        culprit = CULPRITS[params.culprit]
        method = METHODS[params.method]
    except KeyError as exc:
        raise StoryError(f"(Invalid parameter key: {exc})") from exc

    if method.sense < SENSE_MIN:
        raise StoryError(explain_bad_method(params.method))
    if not culprit_can_take(item, culprit):
        raise StoryError(explain_rejection(place, item, culprit, method))
    if not place_allows(place, culprit):
        raise StoryError(explain_rejection(place, item, culprit, method))
    if not method_works(place, culprit, method):
        raise StoryError(explain_rejection(place, item, culprit, method))

    world = tell(
        place=place,
        item=item,
        culprit=culprit,
        method=method,
        hero_name=params.hero_name,
        hero_gender=params.hero_gender,
        partner_name=params.partner_name,
        partner_gender=params.partner_gender,
        dadda_type=params.dadda_type,
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
    python_set = set(valid_combos())
    clingo_set = set(asp_valid_combos())
    if python_set == clingo_set:
        print(f"OK: gate matches valid_combos() ({len(python_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))

    cases = list(python_set)
    cases.extend(
        [
            ("backyard", "brass_key", "wind", "flutter"),
            ("garage", "paper_clue", "crow", "look_up"),
            ("porch", "ribbon_badge", "puppy", "accuse_friend"),
        ]
    )
    seen_cases: set[tuple[str, str, str, str]] = set()
    checked = 0
    for place_id, item_id, culprit_id, method_id in cases:
        case = (place_id, item_id, culprit_id, method_id)
        if case in seen_cases:
            continue
        seen_cases.add(case)
        py = outcome_of(place_id, item_id, culprit_id, method_id)
        asp = asp_outcome(place_id, item_id, culprit_id, method_id)
        checked += 1
        if py != asp:
            rc = 1
            print(f"MISMATCH outcome for {case}: python={py} asp={asp}")
    if rc == 0:
        print(f"OK: outcome model matches on {checked} scenarios.")

    try:
        sample = generate(CURATED[0])
        if not sample.story or "dadda" not in sample.story.lower():
            raise StoryError("smoke test story missing expected content")
        print("OK: smoke test generate() succeeded.")
    except Exception as exc:
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/4.\n#show outcome/5."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, item, culprit, method) combos:\n")
        for place_id, item_id, culprit_id, method_id in combos:
            print(f"  {place_id:9} {item_id:12} {culprit_id:7} {method_id}")
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
            header = f"### {p.hero_name} & {p.partner_name}: {p.item} at {p.place} ({p.culprit}, {p.method})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
