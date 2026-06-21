#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/stationary_esquire_market_humor_problem_solving_rhyming.py

A tiny storyworld about a child at a market, a funny paper stall, and a gusty
problem that must be solved sensibly. The stories lean child-facing, playful,
and lightly rhymed. They always include the seed words "stationary" and
"esquire".

Premise
-------
A child visits a market stall that sells paper goods. The stallkeeper styles
themself as an "esquire" for laughs. A breeze makes the loose papers skitter,
so the child and the stallkeeper must keep the stationery stationary. The turn
comes from picking a reasonable anchoring method that matches the wind.

Run it
------
python storyworlds/worlds/gpt-5.4/stationary_esquire_market_humor_problem_solving_rhyming.py
python storyworlds/worlds/gpt-5.4/stationary_esquire_market_humor_problem_solving_rhyming.py --paper poster --wind blustery --anchor stone_weights
python storyworlds/worlds/gpt-5.4/stationary_esquire_market_humor_problem_solving_rhyming.py --anchor feather
python storyworlds/worlds/gpt-5.4/stationary_esquire_market_humor_problem_solving_rhyming.py --all --qa
python storyworlds/worlds/gpt-5.4/stationary_esquire_market_humor_problem_solving_rhyming.py --verify
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
    phrase: str = ""
    role: str = ""
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
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
class PaperGood:
    id: str
    label: str = ""
    phrase: str = ""
    need: str = ""
    rhyme_line: str = ""
    size: int = 1
    tags: set[str] = field(default_factory=set)


@dataclass
class Wind:
    id: str
    label: str = ""
    phrase: str = ""
    strength: int = 1
    sound: str = ""
    motion: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Anchor:
    id: str
    label: str = ""
    phrase: str = ""
    sense: int = 2
    hold: int = 1
    action: str = ""
    fail_action: str = ""
    qa_text: str = ""
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
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


def hazard_strength(paper: PaperGood, wind: Wind) -> int:
    return paper.size + wind.strength


def sensible_anchors() -> list[Anchor]:
    return [a for a in ANCHORS.values() if a.sense >= SENSE_MIN]


def problem_at_risk(paper: PaperGood, wind: Wind) -> bool:
    return hazard_strength(paper, wind) >= 2


def will_hold(anchor: Anchor, paper: PaperGood, wind: Wind) -> bool:
    return anchor.hold >= hazard_strength(paper, wind)


def explain_rejection(anchor_id: str) -> str:
    a = ANCHORS[anchor_id]
    better = ", ".join(sorted(x.id for x in sensible_anchors()))
    return (
        f"(Refusing anchor '{anchor_id}': it is too silly to count as a sensible fix "
        f"(sense={a.sense} < {SENSE_MIN}). Try one of: {better}.)"
    )


def explain_no_story(paper: PaperGood, wind: Wind) -> str:
    return (
        f"(No story: {paper.label} in {wind.phrase} would not create enough trouble "
        f"to need a problem-solving beat.)"
    )


def introduce(world: World, child: Entity, keeper: Entity, paper: PaperGood, market: Entity) -> None:
    child.memes["curious"] += 1
    keeper.memes["showmanship"] += 1
    world.say(
        f"At the busy {market.label}, {child.id} skipped past fruit and bells "
        f"until {child.pronoun()} found a paper stall bright as a shell."
    )
    world.say(
        f"Behind it stood {keeper.id}, who gave a tiny bow and said, "
        f'"{keeper.id}, esquire, at your service today!"'
    )
    world.say(
        f"{child.id} laughed. {paper.rhyme_line} {child.pronoun().capitalize()} had come for {paper.phrase}, "
        f"because {paper.need}."
    )


def breeze_problem(world: World, child: Entity, keeper: Entity, paper: PaperGood, wind: Wind) -> None:
    paper_ent = world.get("paper")
    stall = world.get("stall")
    paper_ent.meters["lifted"] += 1
    paper_ent.meters["at_risk"] += 1
    stall.meters["mess"] += 1
    child.memes["surprise"] += 1
    keeper.memes["worry"] += 1
    world.say(
        f"Then came {wind.phrase}: {wind.sound}, {wind.motion}, and up popped the {paper.label}."
    )
    world.say(
        f'"Oh dear," said {keeper.id}, "to sell stationery, we must keep it stationary!"'
    )


def chase(world: World, child: Entity, keeper: Entity, paper: PaperGood) -> None:
    paper_ent = world.get("paper")
    child.memes["helpful"] += 1
    keeper.memes["fluster"] += 1
    paper_ent.meters["scattered"] += 1
    world.say(
        f"One sheet slid by a basket, one sheet slid by a pear, "
        f"and {child.id} darted after both with a hop and a care."
    )
    world.say(
        f"{keeper.id} caught another with {keeper.pronoun('possessive')} elbow and grinned, "
        f"though the whole little stall looked tickled by wind."
    )


def think(world: World, child: Entity, keeper: Entity, anchor: Anchor) -> None:
    child.memes["thinking"] += 1
    keeper.memes["thinking"] += 1
    world.say(
        f'{child.id} tapped {child.pronoun("possessive")} chin. "{anchor.label.capitalize()}!" '
        f'{child.pronoun().capitalize()} said. "That might do the trick quite quick."'
    )


def solve(world: World, child: Entity, keeper: Entity, anchor: Anchor, paper: PaperGood, wind: Wind) -> None:
    paper_ent = world.get("paper")
    stall = world.get("stall")
    paper_ent.meters["still"] += 1
    paper_ent.meters["at_risk"] = 0.0
    stall.meters["mess"] = 0.0
    child.memes["joy"] += 1
    keeper.memes["relief"] += 1
    keeper.memes["pride"] += 1
    world.say(
        f"Together they {anchor.action}. At once the {paper.label} stopped its skate, "
        f"and every page lay flat and neat instead of tempting fate."
    )
    world.say(
        f'{keeper.id} spread both hands and sang, "Behold the market art! '
        f'Now all my stationery can stay stationary from the start."'
    )


def fail_then_recover(world: World, child: Entity, keeper: Entity, anchor: Anchor, paper: PaperGood, wind: Wind) -> None:
    paper_ent = world.get("paper")
    stall = world.get("stall")
    child.memes["worry"] += 1
    child.memes["thinking"] += 1
    keeper.memes["worry"] += 1
    paper_ent.meters["scattered"] += 1
    world.say(
        f"They tried to {anchor.fail_action}, but {wind.label} was too spry. "
        f"Up bounced a corner, then another corner tried to fly."
    )
    world.say(
        f'"This fix is kind, but not enough," said {keeper.id}. "{paper.label.capitalize()} needs a heavier friend."'
    )
    better = best_backup_anchor(paper, wind)
    paper_ent.meters["still"] += 1
    paper_ent.meters["at_risk"] = 0.0
    stall.meters["mess"] = 0.0
    child.memes["joy"] += 1
    keeper.memes["relief"] += 1
    world.facts["backup_anchor"] = better
    world.say(
        f"So {child.id} and {keeper.id} {better.action}. Then the pages settled down, "
        f"and not one flutter dared to dash into the town."
    )


def ending(world: World, child: Entity, keeper: Entity, paper: PaperGood) -> None:
    child.memes["satisfied"] += 1
    world.say(
        f"{keeper.id} rolled up {paper.phrase} with a ribbon loop so slight, "
        f"and handed it to {child.id} with a bow both grand and bright."
    )
    world.say(
        f"{child.id} waved and skipped away through the market's merry choir, "
        f"pleased that a small smart plan had helped the papers all retire."
    )


def tell(
    paper: PaperGood,
    wind: Wind,
    anchor: Anchor,
    child_name: str = "Mina",
    child_gender: str = "girl",
    keeper_name: str = "Bramble",
    keeper_gender: str = "man",
    title_style: str = "grand",
    market_name: str = "morning market",
) -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="child", label=child_name))
    keeper = world.add(
        Entity(
            id=keeper_name,
            kind="character",
            type=keeper_gender,
            role="keeper",
            label=keeper_name,
            attrs={"title_style": title_style},
        )
    )
    market = world.add(Entity(id="market", type="place", label=market_name, role="place"))
    stall = world.add(Entity(id="stall", type="stall", label="paper stall", role="stall"))
    paper_ent = world.add(Entity(id="paper", type="paper", label=paper.label, phrase=paper.phrase, role="paper"))

    introduce(world, child, keeper, paper, market)
    world.para()
    breeze_problem(world, child, keeper, paper, wind)
    chase(world, child, keeper, paper)
    world.para()
    think(world, child, keeper, anchor)

    if will_hold(anchor, paper, wind):
        outcome = "held"
        solve(world, child, keeper, anchor, paper, wind)
    else:
        outcome = "backup"
        fail_then_recover(world, child, keeper, anchor, paper, wind)

    world.para()
    ending(world, child, keeper, paper)

    world.facts.update(
        child=child,
        keeper=keeper,
        market=market,
        stall=stall,
        paper_cfg=paper,
        paper=paper_ent,
        wind=wind,
        anchor=anchor,
        outcome=outcome,
        title_style=title_style,
        hazard=hazard_strength(paper, wind),
        solved=paper_ent.meters["still"] >= THRESHOLD,
    )
    return world


PAPERS = {
    "poster": PaperGood(
        id="poster",
        label="poster",
        phrase="a parade poster",
        need="the jam band parade would march by at noon",
        rhyme_line="The colors were bold and the letters were spry.",
        size=2,
        tags={"paper", "poster", "market"},
    ),
    "card": PaperGood(
        id="card",
        label="card",
        phrase="a birthday card",
        need="a cousin's party would start very soon",
        rhyme_line="The corners were crisp and the daisies looked high.",
        size=1,
        tags={"paper", "card", "market"},
    ),
    "menu": PaperGood(
        id="menu",
        label="menu",
        phrase="a lunch menu",
        need="the soup stall next door had a fresh pumpkin stew",
        rhyme_line="Its noodle-like letters went loopety-loop by.",
        size=1,
        tags={"paper", "menu", "market"},
    ),
    "map": PaperGood(
        id="map",
        label="map",
        phrase="a treasure map for the market game",
        need="the children wanted clues for a playful treasure hunt",
        rhyme_line="Its dotted red pathway looked tricky to spy.",
        size=2,
        tags={"paper", "map", "market"},
    ),
}

WINDS = {
    "soft": Wind(
        id="soft",
        label="soft breeze",
        phrase="a soft breeze",
        strength=1,
        sound="shush-shush",
        motion="the awnings gave one gentle flap",
        tags={"wind", "breeze"},
    ),
    "gusty": Wind(
        id="gusty",
        label="gusty breeze",
        phrase="a gusty breeze",
        strength=2,
        sound="whoof-whoof",
        motion="the hanging ribbons kicked and clapped",
        tags={"wind", "gusty"},
    ),
    "blustery": Wind(
        id="blustery",
        label="blustery wind",
        phrase="a blustery wind",
        strength=3,
        sound="fwish-fwash",
        motion="the awnings billowed like sails on a map",
        tags={"wind", "blustery"},
    ),
}

ANCHORS = {
    "stone_weights": Anchor(
        id="stone_weights",
        label="stone weights",
        phrase="smooth stone weights",
        sense=3,
        hold=5,
        action="set smooth stone weights on the corners",
        fail_action="balance smooth stone weights on the corners",
        qa_text="They set smooth stone weights on the corners",
        tags={"anchor", "stone", "weight"},
    ),
    "wood_clip": Anchor(
        id="wood_clip",
        label="wood clip",
        phrase="a wooden clip bar",
        sense=3,
        hold=4,
        action="slide the pages under a wooden clip bar",
        fail_action="slide the pages under a wooden clip bar",
        qa_text="They slid the pages under a wooden clip bar",
        tags={"anchor", "clip"},
    ),
    "string_ties": Anchor(
        id="string_ties",
        label="string ties",
        phrase="little string ties",
        sense=2,
        hold=3,
        action="tie the stack with little string ties and tuck it to the board",
        fail_action="tie the stack with little string ties",
        qa_text="They tied the stack with string and tucked it to the board",
        tags={"anchor", "string"},
    ),
    "feather": Anchor(
        id="feather",
        label="feather",
        phrase="a feather",
        sense=1,
        hold=1,
        action="pat a feather over the pages",
        fail_action="pat a feather over the pages",
        qa_text="They tried using a feather",
        tags={"anchor", "silly"},
    ),
}

CHILD_NAMES = ["Mina", "Tess", "Nora", "Avi", "Luca", "Pip", "June", "Eli"]
KEEPER_NAMES = ["Bramble", "Quill", "Poppy", "Moss", "Cedric", "Dot"]
TITLE_STYLES = ["grand", "playful"]
MARKET_NAMES = ["morning market", "sunny market", "Saturday market", "corner market"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for paper_id, paper in PAPERS.items():
        for wind_id, wind in WINDS.items():
            if not problem_at_risk(paper, wind):
                continue
            for anchor_id, anchor in ANCHORS.items():
                if anchor.sense >= SENSE_MIN:
                    combos.append((paper_id, wind_id, anchor_id))
    return combos


@dataclass
class StoryParams:
    paper: str
    wind: str
    anchor: str
    child_name: str
    child_gender: str
    keeper_name: str
    keeper_gender: str
    title_style: str
    market_name: str
    seed: Optional[int] = None


def best_backup_anchor(paper: PaperGood, wind: Wind) -> Anchor:
    options = [a for a in sensible_anchors() if will_hold(a, paper, wind)]
    if not options:
        raise StoryError("(No backup anchor can actually hold these papers in this wind.)")
    return max(options, key=lambda a: (a.hold, a.sense, a.id))


KNOWLEDGE = {
    "stationery": [
        (
            "What is stationery?",
            "Stationery is paper you use for writing or signs, like cards, posters, and note paper. People keep it neat so it does not wrinkle or blow away."
        )
    ],
    "stationary": [
        (
            "What does stationary mean?",
            "Stationary means not moving. If papers stay still on a table, they are stationary."
        )
    ],
    "market": [
        (
            "What is a market?",
            "A market is a place where many sellers bring goods to tables or stalls. People walk around, look, talk, and buy what they need."
        )
    ],
    "wind": [
        (
            "Why can wind move paper?",
            "Paper is light, so moving air can push under it and lift the edges. That is why loose pages skitter when a breeze comes by."
        )
    ],
    "clip": [
        (
            "What does a clip do?",
            "A clip squeezes papers together so they do not slide apart. It helps keep pages tidy and easier to carry."
        )
    ],
    "weight": [
        (
            "Why do weights help keep paper still?",
            "A weight presses the paper down so the wind has a harder time lifting it. Heavier things are harder for a breeze to shove around."
        )
    ],
    "string": [
        (
            "Why tie papers with string?",
            "String holds the pages together so they act like one bundle instead of many loose sheets. A tidy bundle is easier to control."
        )
    ],
    "problem_solving": [
        (
            "What is problem solving?",
            "Problem solving means noticing what is wrong, thinking of a helpful plan, and trying it. If the first idea is too weak, you can choose a better one."
        )
    ],
    "esquire": [
        (
            "What does esquire mean in this story?",
            "Here it is a funny, fancy title the stallkeeper uses while bowing at the market. It makes the child laugh and sets a playful mood."
        )
    ],
}
KNOWLEDGE_ORDER = [
    "market",
    "stationery",
    "stationary",
    "wind",
    "weight",
    "clip",
    "string",
    "problem_solving",
    "esquire",
]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    keeper = f["keeper"]
    paper = f["paper_cfg"]
    wind = f["wind"]
    anchor = f["anchor"]
    outcome = f["outcome"]
    if outcome == "held":
        return [
            'Write a short rhyming story for a 3-to-5-year-old set in a market that includes the words "stationary" and "esquire".',
            f"Tell a funny market story where {keeper.id} calls {keeper.pronoun('object')}self an esquire, a {wind.label} bothers {paper.label}, and {child.id} helps solve the problem with {anchor.label}.",
            f"Write a playful problem-solving poem-story about keeping stationery stationary at a market stall.",
        ]
    return [
        'Write a short rhyming story for a 3-to-5-year-old set in a market that includes the words "stationary" and "esquire".',
        f"Tell a humorous story where {child.id} and {keeper.id}, a self-important little esquire, first try {anchor.label} on some {paper.label} in {wind.phrase}, then think of a better fix.",
        "Write a rhyming story with a small failed idea, a smarter second idea, and a happy ending at a market paper stall.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    keeper = f["keeper"]
    paper = f["paper_cfg"]
    wind = f["wind"]
    anchor = f["anchor"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id}, a child at the market, and {keeper.id}, the stallkeeper who jokingly called {keeper.pronoun('object')}self an esquire. They work together when the paper stall gets into trouble."
        ),
        (
            f"Why did {child.id} come to the market stall?",
            f"{child.id} came for {paper.phrase}. The paper mattered because {paper.need}."
        ),
        (
            "What was the problem at the stall?",
            f"{wind.label.capitalize()} kept lifting and sliding the {paper.label}. The trouble was funny because the stall sold stationery, but the papers would not stay stationary."
        ),
    ]
    if f["outcome"] == "held":
        qa.append(
            (
                "How did they solve the problem?",
                f"{anchor.qa_text}, and that held the pages still. The plan worked because it was strong enough for the wind and the size of the paper."
            )
        )
    else:
        better = f["backup_anchor"]
        qa.append(
            (
                "Did the first idea work right away?",
                f"No. They first tried {anchor.label}, but the wind was too strong for it. Then they switched to {better.label}, which gave the papers a steadier hold."
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"The pages finally settled down, and {keeper.id} neatly handed {paper.phrase} to {child.id}. The happy ending shows that a smarter second plan can fix a wiggly problem."
            )
        )
    qa.append(
        (
            "Why is the wordplay in the story funny?",
            'It plays with two sound-alike words: "stationery" for paper goods and "stationary" for staying still. The joke fits the problem because the papers keep trying to move.'
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"market", "stationery", "stationary", "wind", "problem_solving", "esquire"}
    anchor = f["anchor"]
    if "stone" in anchor.tags:
        tags.add("weight")
    if "clip" in anchor.tags:
        tags.add("clip")
    if "string" in anchor.tags:
        tags.add("string")
    if f["outcome"] == "backup":
        better = f["backup_anchor"]
        if "stone" in better.tags:
            tags.add("weight")
        if "clip" in better.tags:
            tags.add("clip")
        if "string" in better.tags:
            tags.add("string")
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
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if e.role:
            bits.append(f"role={e.role}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  facts: outcome={world.facts.get('outcome')} hazard={world.facts.get('hazard')}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        paper="card",
        wind="gusty",
        anchor="string_ties",
        child_name="Mina",
        child_gender="girl",
        keeper_name="Bramble",
        keeper_gender="man",
        title_style="grand",
        market_name="morning market",
    ),
    StoryParams(
        paper="poster",
        wind="blustery",
        anchor="wood_clip",
        child_name="Avi",
        child_gender="boy",
        keeper_name="Quill",
        keeper_gender="man",
        title_style="playful",
        market_name="Saturday market",
    ),
    StoryParams(
        paper="menu",
        wind="soft",
        anchor="stone_weights",
        child_name="June",
        child_gender="girl",
        keeper_name="Poppy",
        keeper_gender="woman",
        title_style="grand",
        market_name="corner market",
    ),
    StoryParams(
        paper="map",
        wind="gusty",
        anchor="stone_weights",
        child_name="Luca",
        child_gender="boy",
        keeper_name="Moss",
        keeper_gender="man",
        title_style="playful",
        market_name="sunny market",
    ),
]


ASP_RULES = r"""
problem(P, W) :- paper(P), wind(W), size(P, Sz), strength(W, St), Sz + St >= 2.
sensible(A) :- anchor(A), sense(A, S), sense_min(M), S >= M.
valid(P, W, A) :- problem(P, W), sensible(A).

hazard(V) :- chosen_paper(P), chosen_wind(W), size(P, Sz), strength(W, St), V = Sz + St.
held :- chosen_anchor(A), hold(A, H), hazard(V), H >= V.
outcome(held) :- held.
outcome(backup) :- not held.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for pid, paper in PAPERS.items():
        lines.append(asp.fact("paper", pid))
        lines.append(asp.fact("size", pid, paper.size))
    for wid, wind in WINDS.items():
        lines.append(asp.fact("wind", wid))
        lines.append(asp.fact("strength", wid, wind.strength))
    for aid, anchor in ANCHORS.items():
        lines.append(asp.fact("anchor", aid))
        lines.append(asp.fact("sense", aid, anchor.sense))
        lines.append(asp.fact("hold", aid, anchor.hold))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp

    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(a for (a,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen_paper", params.paper),
            asp.fact("chosen_wind", params.wind),
            asp.fact("chosen_anchor", params.anchor),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def validate_params(params: StoryParams) -> None:
    if params.paper not in PAPERS:
        raise StoryError(f"(Unknown paper '{params.paper}'.)")
    if params.wind not in WINDS:
        raise StoryError(f"(Unknown wind '{params.wind}'.)")
    if params.anchor not in ANCHORS:
        raise StoryError(f"(Unknown anchor '{params.anchor}'.)")
    paper = PAPERS[params.paper]
    wind = WINDS[params.wind]
    anchor = ANCHORS[params.anchor]
    if not problem_at_risk(paper, wind):
        raise StoryError(explain_no_story(paper, wind))
    if anchor.sense < SENSE_MIN:
        raise StoryError(explain_rejection(params.anchor))


def outcome_of(params: StoryParams) -> str:
    validate_params(params)
    return "held" if will_hold(ANCHORS[params.anchor], PAPERS[params.paper], WINDS[params.wind]) else "backup"


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

    c_sens = set(asp_sensible())
    p_sens = {a.id for a in sensible_anchors()}
    if c_sens == p_sens:
        print(f"OK: sensible anchors match ({sorted(c_sens)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible anchors: clingo={sorted(c_sens)} python={sorted(p_sens)}")

    cases = list(CURATED)
    for seed in range(50):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
            params.seed = seed
            cases.append(params)
        except StoryError:
            continue
    bad = sum(1 for p in cases if asp_outcome(p) != outcome_of(p))
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("(Smoke test failed: empty story.)")
        print("OK: smoke test generated a normal story.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Storyworld: a rhyming market tale about keeping stationery stationary."
    )
    ap.add_argument("--paper", choices=sorted(PAPERS))
    ap.add_argument("--wind", choices=sorted(WINDS))
    ap.add_argument("--anchor", choices=sorted(ANCHORS))
    ap.add_argument("--child-name")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--keeper-name")
    ap.add_argument("--keeper-gender", choices=["woman", "man"])
    ap.add_argument("--title-style", choices=sorted(TITLE_STYLES))
    ap.add_argument("--market-name", choices=sorted(MARKET_NAMES))
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible combinations from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.anchor and ANCHORS[args.anchor].sense < SENSE_MIN:
        raise StoryError(explain_rejection(args.anchor))
    if args.paper and args.wind:
        paper = PAPERS[args.paper]
        wind = WINDS[args.wind]
        if not problem_at_risk(paper, wind):
            raise StoryError(explain_no_story(paper, wind))

    combos = [
        combo
        for combo in valid_combos()
        if (args.paper is None or combo[0] == args.paper)
        and (args.wind is None or combo[1] == args.wind)
        and (args.anchor is None or combo[2] == args.anchor)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    paper_id, wind_id, anchor_id = rng.choice(sorted(combos))
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    keeper_gender = args.keeper_gender or rng.choice(["woman", "man"])
    child_name = args.child_name or rng.choice(CHILD_NAMES)
    keeper_name = args.keeper_name or rng.choice([n for n in KEEPER_NAMES if n != child_name] or KEEPER_NAMES)
    title_style = args.title_style or rng.choice(TITLE_STYLES)
    market_name = args.market_name or rng.choice(MARKET_NAMES)
    return StoryParams(
        paper=paper_id,
        wind=wind_id,
        anchor=anchor_id,
        child_name=child_name,
        child_gender=child_gender,
        keeper_name=keeper_name,
        keeper_gender=keeper_gender,
        title_style=title_style,
        market_name=market_name,
    )


def generate(params: StoryParams) -> StorySample:
    validate_params(params)
    world = tell(
        paper=PAPERS[params.paper],
        wind=WINDS[params.wind],
        anchor=ANCHORS[params.anchor],
        child_name=params.child_name,
        child_gender=params.child_gender,
        keeper_name=params.keeper_name,
        keeper_gender=params.keeper_gender,
        title_style=params.title_style,
        market_name=params.market_name,
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
        print(asp_program("", "#show valid/3.\n#show sensible/1.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible anchors: {', '.join(asp_sensible())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (paper, wind, anchor) combos:\n")
        for paper, wind, anchor in combos:
            print(f"  {paper:7} {wind:9} {anchor}")
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
            header = f"### {p.child_name} at {p.market_name}: {p.paper}, {p.wind}, {p.anchor} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
