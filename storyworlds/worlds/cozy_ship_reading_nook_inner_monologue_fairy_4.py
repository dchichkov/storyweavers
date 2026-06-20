#!/usr/bin/env python3
"""A fairy-tale storyworld about a cozy ship in a reading nook.

Seed:
    Words: cozy ship
    Setting: reading nook
    Features: Inner Monologue
    Style: Fairy Tale

Internal source tale:
    A child settles into a cozy ship built inside a reading nook and opens a
    fairy tale. A small physical trouble in the nook makes the child quietly
    imagine a larger enchantment. Instead of fleeing the feeling, the child and
    a gentle helper inspect the nook, mend the real cause, and finish the tale
    in a visibly steadier harbor of blankets, pages, and lamplight.
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, Optional

STORYWORLDS = Path(__file__).resolve().parents[1]
if str(STORYWORLDS) not in sys.path:
    sys.path.insert(0, str(STORYWORLDS))

from results import QAItem, StoryError, StorySample


@dataclass(frozen=True)
class Nook:
    key: str
    label: str
    scene: str
    harbor_image: str
    supports: tuple[str, ...]


@dataclass(frozen=True)
class ShipKind:
    key: str
    label: str
    build_phrase: str
    sail_detail: str
    anchor_detail: str
    resting_pose: str
    supports: tuple[str, ...]


@dataclass(frozen=True)
class Disturbance:
    key: str
    kind: str
    label: str
    source: str
    omen: str
    thought: str
    inspection: str
    reveal: str
    risk: str


@dataclass(frozen=True)
class Remedy:
    key: str
    kind: str
    label: str
    action: str
    helper_action: str
    result: str
    ending_mark: str


@dataclass(frozen=True)
class Book:
    key: str
    title: str
    quest: str
    page_detail: str
    closing_line: str
    echoes: tuple[str, ...]


@dataclass
class StoryParams:
    nook: str
    ship: str
    disturbance: str
    remedy: str
    book: str
    name: str
    gender: str
    helper: str
    trait: str
    seed: Optional[int] = None


@dataclass
class Entity:
    key: str
    kind: str
    label: str
    tags: dict[str, str] = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def add_meter(self, name: str, amount: float) -> None:
        self.meters[name] = round(self.meters.get(name, 0.0) + amount, 2)

    def set_meter(self, name: str, amount: float) -> None:
        self.meters[name] = round(amount, 2)

    def add_meme(self, name: str, amount: float) -> None:
        self.memes[name] = round(self.memes.get(name, 0.0) + amount, 2)


@dataclass
class World:
    params: StoryParams
    nook: Nook
    ship: ShipKind
    disturbance: Disturbance
    remedy: Remedy
    book: Book
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict[str, str] = field(default_factory=dict)
    history: list[dict[str, str]] = field(default_factory=list)
    fired: list[str] = field(default_factory=list)

    def add_event(self, kind: str, detail: str, *, effect: str = "") -> None:
        event = {"kind": kind, "detail": detail}
        if effect:
            event["effect"] = effect
        self.history.append(event)

    def trace(self) -> str:
        lines = ["--- world model state ---"]
        lines.append(f"  params: {self.params}")
        lines.append(f"  fired: {self.fired}")
        for key, ent in self.entities.items():
            lines.append(f"  {key}: {ent.kind} | {ent.label}")
            if ent.tags:
                lines.append(f"    tags={dict(sorted(ent.tags.items()))}")
            if ent.meters:
                lines.append(f"    meters={dict(sorted(ent.meters.items()))}")
            if ent.memes:
                lines.append(f"    memes={dict(sorted(ent.memes.items()))}")
        lines.append("  facts:")
        for key, value in sorted(self.facts.items()):
            lines.append(f"    {key}={value}")
        lines.append("  history:")
        for item in self.history:
            lines.append(f"    {item}")
        return "\n".join(lines)


NOOKS: dict[str, Nook] = {
    "bay_window": Nook(
        key="bay_window",
        label="the bay-window reading nook",
        scene="a round rug like a still sea beneath pearl shelves and a curved window",
        harbor_image="the bay-window nook glimmered like a stitched harbor beside the glass",
        supports=("draft", "shadow"),
    ),
    "stair_cubby": Nook(
        key="stair_cubby",
        label="the stair-cubby reading nook",
        scene="a quilt cave under the stairs with a low lamp shelf and a basket of books",
        harbor_image="the stair-cubby glowed like a tiny harbor hidden inside a hill",
        supports=("shadow", "slip"),
    ),
    "attic_eaves": Nook(
        key="attic_eaves",
        label="the attic-eaves reading nook",
        scene="a nest of pillows beneath the slanted roof, with old trunks standing like cliffs",
        harbor_image="the attic-eaves nook looked like a moon harbor tucked under the rafters",
        supports=("draft", "slip"),
    ),
}


SHIPS: dict[str, ShipKind] = {
    "blanket_galleon": ShipKind(
        key="blanket_galleon",
        label="blanket galleon",
        build_phrase="blankets over a wicker frame",
        sail_detail="a gauze sail the color of watered silk",
        anchor_detail="a teacup anchor hanging from a ribbon bow",
        resting_pose="the blanket galleon rested straight and snug among the cushions",
        supports=("draft", "slip"),
    ),
    "pillow_swan": ShipKind(
        key="pillow_swan",
        label="pillow swan ship",
        build_phrase="pillows curved into a swan-necked hull",
        sail_detail="a moon-pale paper sail tucked near the swan neck",
        anchor_detail="a tassel anchor hidden beneath the side pillow",
        resting_pose="the pillow swan ship floated level as if listening to a lullaby",
        supports=("shadow", "slip"),
    ),
    "story_skiff": ShipKind(
        key="story_skiff",
        label="storybook skiff",
        build_phrase="a low crate covered with quilts and ribbon rails",
        sail_detail="a ribbon sail stitched with tiny stars",
        anchor_detail="a twined yarn anchor tucked beside the bow",
        resting_pose="the storybook skiff waited neat and light at the edge of the rug-sea",
        supports=("draft", "shadow"),
    ),
}


DISTURBANCES: dict[str, Disturbance] = {
    "silver_draft": Disturbance(
        key="silver_draft",
        kind="draft",
        label="a silver draft",
        source="window",
        omen="A silver draft slipped through the nook, puffed the sail, and nudged the pages with cool fingers.",
        thought="What if the wind has heard about {quest} and wants to carry my cozy ship away before I reach the ending?",
        inspection="The child pressed a hand near the window latch and felt a tiny thread of cold air.",
        reveal="The window had been left a finger-width open, just enough for the draft to tease the sail.",
        risk="the pages could flutter loose and the small harbor would stop feeling settled",
    ),
    "crooked_lantern": Disturbance(
        key="crooked_lantern",
        kind="shadow",
        label="a crooked lantern shadow",
        source="lantern",
        omen="The lantern by the shelf tipped a tall shadow over the mast until the whole ship looked watched.",
        thought="What if a giant from {title} has stretched one long finger into my harbor to test whether I am brave?",
        inspection="The child peered at the lamp shelf and saw that the paper shade had turned sideways on its hook.",
        reveal="The shade was crooked, so the lantern threw one long shadow instead of a round glow.",
        risk="the page could grow dim and the nook could stop feeling welcoming",
    ),
    "wandering_anchor": Disturbance(
        key="wandering_anchor",
        kind="slip",
        label="a wandering anchor",
        source="anchor",
        omen="The little anchor slid from its quilt loop, and the ship tipped so the book crept toward one knee.",
        thought="What if the anchor has forgotten its promise and my cozy ship will drift from its pillow harbor before the tale is done?",
        inspection="The child lifted the quilt edge and heard the anchor tap softly against the frame.",
        reveal="The anchor ribbon had come loose from its loop, so the ship could not sit level.",
        risk="the ship could keep leaning and the open book might slide to the floor",
    ),
}


REMEDIES: dict[str, Remedy] = {
    "sash_latch": Remedy(
        key="sash_latch",
        kind="draft",
        label="a curtain sash at the latch",
        action="tucked the curtain sash around the latch and drew the window snug",
        helper_action="The helper held the book safe while the child reached carefully.",
        result="The sail settled at once, and the pages lay down like calm fish in a quiet stream.",
        ending_mark="The curtains hung like harbor flags that had decided to rest.",
    ),
    "turn_the_shade": Remedy(
        key="turn_the_shade",
        kind="shadow",
        label="a straightened shade",
        action="turned the lantern shade until the glow became round again",
        helper_action="The helper steadied the lamp shelf so the child could move slowly and safely.",
        result="The tall shadow folded away from the mast, and the book brightened across the child's lap.",
        ending_mark="The lantern shone like a pearl moon above the berth.",
    ),
    "retie_the_bow": Remedy(
        key="retie_the_bow",
        kind="slip",
        label="a patient ribbon bow",
        action="threaded the anchor ribbon back through its loop and tied a patient bow",
        helper_action="The helper lifted the quilt edge while the child guided the ribbon home.",
        result="The hull stopped leaning, and the book stayed open without creeping away.",
        ending_mark="The anchor rested by the bow like a sleeping cup.",
    ),
}


BOOKS: dict[str, Book] = {
    "star_harbor": Book(
        key="star_harbor",
        title="The Star Harbor Ferry",
        quest="a ferry carrying moon-crumbs toward a harbor star",
        page_detail="silver waves bowed before a patient captain who never hurried the tide",
        closing_line="The ferry found its harbor because the captain noticed the smallest sign on the water.",
        echoes=("draft", "slip"),
    ),
    "lantern_queen": Book(
        key="lantern_queen",
        title="The Lantern Queen of Lullaby Bay",
        quest="a queen trimming one true lamp so lost boats could come home",
        page_detail="one brave lamp was keeping a misty bay from going dark",
        closing_line="The queen's lamp stayed bright because kind hands kept tending it.",
        echoes=("shadow",),
    ),
    "pearl_map": Book(
        key="pearl_map",
        title="The Pearl Map of Pillow Isles",
        quest="a child captain following a pearl map from soft islands to morning",
        page_detail="a pearl map only glimmered when the captain grew still enough to read it",
        closing_line="The pearl map revealed the next kind step only to the still-hearted.",
        echoes=("draft", "shadow", "slip"),
    ),
}


HEROES = {
    "girl": ("Mira", "Lina", "June", "Elsie", "Nora"),
    "boy": ("Theo", "Finn", "Oliver", "Milo", "Sam"),
}

HELPERS = ("grandmother", "aunt", "mother", "father", "uncle")
TRAITS = ("dreamy", "careful", "soft-voiced", "patient", "bright-eyed")


def pronouns(gender: str) -> tuple[str, str, str]:
    if gender == "boy":
        return ("he", "his", "him")
    return ("she", "her", "her")


def _title(word: str) -> str:
    return word.replace("_", " ").title()


def _sentence_case(text: str) -> str:
    if not text:
        return text
    return text[0].upper() + text[1:]


def _strip_period(text: str) -> str:
    return text[:-1] if text.endswith(".") else text


def valid_combo(nook: str, ship: str, disturbance: str, remedy: str, book: str) -> bool:
    if nook not in NOOKS or ship not in SHIPS or disturbance not in DISTURBANCES or remedy not in REMEDIES or book not in BOOKS:
        return False
    chosen_nook = NOOKS[nook]
    chosen_ship = SHIPS[ship]
    chosen_disturbance = DISTURBANCES[disturbance]
    chosen_remedy = REMEDIES[remedy]
    chosen_book = BOOKS[book]
    kind = chosen_disturbance.kind
    return (
        kind in chosen_nook.supports
        and kind in chosen_ship.supports
        and kind in chosen_book.echoes
        and chosen_remedy.kind == kind
    )


def explain_rejection(nook: str, ship: str, disturbance: str, remedy: str, book: str) -> str:
    if nook not in NOOKS:
        return f"No story: unknown nook {nook!r}."
    if ship not in SHIPS:
        return f"No story: unknown ship {ship!r}."
    if disturbance not in DISTURBANCES:
        return f"No story: unknown disturbance {disturbance!r}."
    if remedy not in REMEDIES:
        return f"No story: unknown remedy {remedy!r}."
    if book not in BOOKS:
        return f"No story: unknown book {book!r}."
    chosen_nook = NOOKS[nook]
    chosen_ship = SHIPS[ship]
    chosen_disturbance = DISTURBANCES[disturbance]
    chosen_remedy = REMEDIES[remedy]
    chosen_book = BOOKS[book]
    kind = chosen_disturbance.kind
    if kind not in chosen_nook.supports:
        return f"No story: {chosen_nook.label} cannot reasonably create a {chosen_disturbance.label}."
    if kind not in chosen_ship.supports:
        return f"No story: the {chosen_ship.label} is not built to show a {chosen_disturbance.label} in a readable way."
    if kind not in chosen_book.echoes:
        return f"No story: {chosen_book.title} does not fit a {chosen_disturbance.label} mood."
    if chosen_remedy.kind != kind:
        return f"No story: {chosen_remedy.label} does not solve a {chosen_disturbance.label}."
    return "No story: the requested reading-nook tale is not reasonable."


def valid_combos() -> list[tuple[str, str, str, str, str]]:
    rows: list[tuple[str, str, str, str, str]] = []
    for nook in NOOKS:
        for ship in SHIPS:
            for disturbance in DISTURBANCES:
                for remedy in REMEDIES:
                    for book in BOOKS:
                        if valid_combo(nook, ship, disturbance, remedy, book):
                            rows.append((nook, ship, disturbance, remedy, book))
    return rows


def build_world(params: StoryParams) -> World:
    if not valid_combo(params.nook, params.ship, params.disturbance, params.remedy, params.book):
        raise StoryError(
            explain_rejection(params.nook, params.ship, params.disturbance, params.remedy, params.book)
        )
    world = World(
        params=params,
        nook=NOOKS[params.nook],
        ship=SHIPS[params.ship],
        disturbance=DISTURBANCES[params.disturbance],
        remedy=REMEDIES[params.remedy],
        book=BOOKS[params.book],
    )
    world.entities["hero"] = Entity(
        key="hero",
        kind="character",
        label=params.name,
        tags={"gender": params.gender, "trait": params.trait, "role": "reader-captain"},
        meters={"breath_steady": 1.0},
        memes={"coziness": 1.4, "curiosity": 1.0},
    )
    world.entities["helper"] = Entity(
        key="helper",
        kind="character",
        label=_title(params.helper),
        tags={"relation": params.helper, "role": "steady helper"},
        memes={"kindness": 1.2},
    )
    world.entities["nook"] = Entity(
        key="nook",
        kind="place",
        label=world.nook.label,
        meters={"warmth": 1.3, "stillness": 1.2},
        memes={"safety": 1.2},
    )
    world.entities["ship"] = Entity(
        key="ship",
        kind="object",
        label=world.ship.label,
        tags={"state": "moored"},
        meters={"steady": 1.2, "tilt": 0.0, "shadow": 0.0, "flutter": 0.0},
        memes={"wonder": 1.0, "coziness": 1.3},
    )
    world.entities["book"] = Entity(
        key="book",
        kind="object",
        label=world.book.title,
        tags={"state": "open"},
        meters={"brightness": 1.0, "pages_settled": 1.0},
        memes={"story_magic": 1.1},
    )
    world.entities["window"] = Entity(
        key="window",
        kind="object",
        label="the window latch",
        tags={"state": "closed"},
        meters={"draft": 0.0},
    )
    world.entities["lantern"] = Entity(
        key="lantern",
        kind="object",
        label="the reading lantern",
        tags={"state": "round_glow"},
        meters={"shadow": 0.0},
    )
    world.entities["anchor"] = Entity(
        key="anchor",
        kind="object",
        label="the little anchor",
        tags={"state": "fastened"},
        meters={"loose": 0.0},
    )
    world.facts["setting"] = world.nook.label
    world.facts["ship_phrase"] = world.ship.label
    world.facts["book_title"] = world.book.title
    world.facts["problem_kind"] = world.disturbance.kind
    world.facts["repair_kind"] = world.remedy.kind
    return world


def _disturb(world: World) -> None:
    hero = world.entities["hero"]
    ship = world.entities["ship"]
    book = world.entities["book"]
    source = world.entities[world.disturbance.source]
    nook = world.entities["nook"]

    world.fired.append("disturbance")
    world.facts["omen"] = world.disturbance.omen
    world.facts["risk"] = world.disturbance.risk

    hero.add_meme("worry", 0.9)
    hero.add_meme("wonder", 0.6)
    nook.add_meter("stillness", -0.4)
    ship.add_meter("steady", -0.5)
    book.add_meter("pages_settled", -0.4)

    if world.disturbance.kind == "draft":
        source.tags["state"] = "ajar"
        source.set_meter("draft", 1.0)
        ship.add_meter("flutter", 1.0)
    elif world.disturbance.kind == "shadow":
        source.tags["state"] = "crooked"
        source.set_meter("shadow", 1.0)
        ship.add_meter("shadow", 1.0)
        book.add_meter("brightness", -0.4)
    else:
        source.tags["state"] = "loose"
        source.set_meter("loose", 1.0)
        ship.add_meter("tilt", 1.0)
        book.add_meter("pages_settled", -0.2)

    world.add_event("disturbance", world.disturbance.omen, effect=world.disturbance.risk)


def _inner_monologue(world: World) -> None:
    hero = world.entities["hero"]
    hero.add_meme("imagination", 1.0)
    hero.add_meter("breath_steady", -0.2)
    thought = world.disturbance.thought.format(
        quest=world.book.quest,
        title=world.book.title,
    )
    world.fired.append("inner_monologue")
    world.facts["thought"] = thought
    world.add_event("inner_monologue", thought)


def _inspect(world: World) -> None:
    hero = world.entities["hero"]
    helper = world.entities["helper"]
    hero.add_meme("care", 0.8)
    hero.add_meme("courage", 0.6)
    helper.add_meme("guidance", 0.9)
    world.fired.append("inspection")
    world.facts["inspection"] = world.disturbance.inspection
    world.facts["reveal"] = world.disturbance.reveal
    world.add_event("inspection", world.disturbance.inspection, effect=world.disturbance.reveal)


def _repair(world: World) -> None:
    hero = world.entities["hero"]
    nook = world.entities["nook"]
    ship = world.entities["ship"]
    book = world.entities["book"]
    source = world.entities[world.disturbance.source]

    world.fired.append("repair")
    world.facts["helper_action"] = world.remedy.helper_action
    world.facts["repair_action"] = world.remedy.action
    world.facts["repair_result"] = world.remedy.result
    world.facts["ending_mark"] = world.remedy.ending_mark

    hero.add_meme("relief", 1.2)
    hero.add_meme("trust", 0.8)
    hero.add_meter("breath_steady", 0.5)
    nook.add_meter("stillness", 0.7)
    ship.add_meter("steady", 0.8)
    book.add_meter("pages_settled", 0.8)
    book.add_meter("brightness", 0.3)

    if world.disturbance.kind == "draft":
        source.tags["state"] = "snug"
        source.set_meter("draft", 0.0)
        ship.set_meter("flutter", 0.0)
    elif world.disturbance.kind == "shadow":
        source.tags["state"] = "round_glow"
        source.set_meter("shadow", 0.0)
        ship.set_meter("shadow", 0.0)
    else:
        source.tags["state"] = "fastened"
        source.set_meter("loose", 0.0)
        ship.set_meter("tilt", 0.0)

    ship.tags["state"] = "resting"
    world.add_event("repair", world.remedy.action, effect=world.remedy.result)


def simulate(world: World) -> World:
    if world.history:
        return world
    _disturb(world)
    _inner_monologue(world)
    _inspect(world)
    _repair(world)
    return world


def render_story(world: World) -> str:
    simulate(world)
    she, her, _ = pronouns(world.params.gender)
    hero = world.entities["hero"]
    helper = world.entities["helper"]

    opening = (
        f"Once upon a hush-soft evening, {world.params.name}, a {world.params.trait} child, climbed into the cozy ship in "
        f"{world.nook.label}. It was a {world.ship.label} made from {world.ship.build_phrase}, with {world.ship.sail_detail} "
        f"and {world.ship.anchor_detail}. Around it lay {world.nook.scene}, and in {her} lap rested {world.book.title}, open "
        f"to a page where {world.book.page_detail}."
    )
    trouble = (
        f"{world.disturbance.omen} {world.params.name}'s heart gave one small jump. Inside, {she} thought, "
        f"\"{world.facts['thought']}\""
    )
    turn = (
        f"{helper.label} did not laugh at the worried thought. {world.disturbance.inspection} "
        f"{world.disturbance.reveal} {world.remedy.helper_action} Together they {world.remedy.action}."
    )
    if hero.memes.get("relief", 0.0) > hero.memes.get("worry", 0.0):
        lesson_tail = "Then the child understood that a gentle check can quiet a frightening guess."
    else:
        lesson_tail = "Even after the fix, the child kept listening carefully to the room."
    ending = (
        f"{world.remedy.result} Soon {world.params.name} read on about {world.book.quest}. "
        f"{world.book.closing_line} By the end, {world.nook.harbor_image}. "
        f"{_strip_period(_sentence_case(world.remedy.ending_mark))}, and {world.ship.resting_pose}. {lesson_tail}"
    )
    return "\n\n".join([opening, trouble, turn, ending])


def generation_prompts(world: World) -> list[str]:
    return [
        'Write a fairy-tale story for children that includes the words "cozy ship" and takes place in a reading nook.',
        f"Tell an inner-monologue bedtime tale where {world.params.name} reads {world.book.title} inside a {world.ship.label}.",
        f"Write a gentle fairy story where {world.disturbance.label} is solved by {world.remedy.label} instead of panic.",
    ]


def story_qa(world: World) -> list[QAItem]:
    simulate(world)
    return [
        QAItem(
            "What troubled the cozy ship at the beginning?",
            f"{world.disturbance.omen} That mattered because {world.disturbance.risk}.",
        ),
        QAItem(
            "What did the child think inside?",
            f"{world.params.name} privately thought, \"{world.facts['thought']}\" The thought came from the way the real disturbance brushed against the fairy tale in the child's lap.",
        ),
        QAItem(
            "How did the helper change the middle of the story?",
            f"{world.entities['helper'].label} treated the worry seriously instead of brushing it aside. {world.remedy.helper_action} "
            f"That steady help gave the child time to inspect the nook until the true cause was clear.",
        ),
        QAItem(
            "What was the real cause, and how was it fixed?",
            f"{world.disturbance.reveal} Then they {world.remedy.action}. {world.remedy.result}",
        ),
        QAItem(
            "How can you tell the ending is calmer than the beginning?",
            f"By the ending, {world.nook.harbor_image}. {_strip_period(_sentence_case(world.remedy.ending_mark))}, and {world.ship.resting_pose}. "
            f"The final picture proves that the ship, the room, and the reader all feel steadier.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    simulate(world)
    items = [
        QAItem(
            "Why can a tiny room change feel big to a child who is reading a fairy tale?",
            "Stories can make ordinary sounds and shadows feel important. A child may connect the room to the tale, especially when imagination is already busy.",
        ),
        QAItem(
            "Why is it helpful to inspect a cozy space before deciding something magical is wrong?",
            "A calm check can reveal a simple physical cause, like a draft or a loose ribbon. That helps a child feel capable instead of trapped inside a scary guess.",
        ),
        QAItem(
            "Why does a gentle helper matter in a story like this?",
            "A gentle helper keeps the child from feeling foolish about being afraid. That steadiness makes it easier to look closely and solve the real problem together.",
        ),
    ]
    if world.disturbance.kind == "draft":
        items.append(
            QAItem(
                "Why might a draft bother reading time?",
                "A draft can scatter pages and make a reading nook feel less snug. Closing the source helps the body and the story settle again.",
            )
        )
    elif world.disturbance.kind == "shadow":
        items.append(
            QAItem(
                "Why can changing a lamp shade change the whole mood of a room?",
                "Light shapes how shadows fall. When a lamp glows evenly, the room can feel safer and easier to read in.",
            )
        )
    else:
        items.append(
            QAItem(
                "Why does securing a small anchor or ribbon matter in a blanket fort?",
                "Loose parts can make the structure tilt or shift. Fastening them keeps the pretend world comfortable and the real objects from sliding.",
            )
        )
    return items


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    story = render_story(world)
    return StorySample(
        params=params,
        story=story,
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


ASP_RULES = r"""
combo(N,S,D,R,B) :-
    nook(N),
    ship(S),
    disturbance(D),
    remedy(R),
    book(B),
    disturbance_kind(D,K),
    nook_support(N,K),
    ship_support(S,K),
    book_echo(B,K),
    remedy_kind(R,K).

ok :- chosen(N,S,D,R,B), combo(N,S,D,R,B).

#show combo/5.
#show ok/0.
"""


def asp_facts(params: StoryParams | None = None) -> str:
    import asp

    rows: list[str] = []
    for key, nook in NOOKS.items():
        rows.append(asp.fact("nook", key))
        for support in nook.supports:
            rows.append(asp.fact("nook_support", key, support))
    for key, ship in SHIPS.items():
        rows.append(asp.fact("ship", key))
        for support in ship.supports:
            rows.append(asp.fact("ship_support", key, support))
    for key, disturbance in DISTURBANCES.items():
        rows.append(asp.fact("disturbance", key))
        rows.append(asp.fact("disturbance_kind", key, disturbance.kind))
    for key, remedy in REMEDIES.items():
        rows.append(asp.fact("remedy", key))
        rows.append(asp.fact("remedy_kind", key, remedy.kind))
    for key, book in BOOKS.items():
        rows.append(asp.fact("book", key))
        for echo in book.echoes:
            rows.append(asp.fact("book_echo", key, echo))
    if params is not None:
        rows.append(
            asp.fact(
                "chosen",
                params.nook,
                params.ship,
                params.disturbance,
                params.remedy,
                params.book,
            )
        )
    return "\n".join(rows) + "\n"


def asp_program(params: StoryParams | None = None) -> str:
    return asp_facts(params) + ASP_RULES


def asp_valid_combos() -> set[tuple[str, str, str, str, str]]:
    import asp

    combos: set[tuple[str, str, str, str, str]] = set()
    for model in asp.solve(asp_program(), models=0):
        combos.update(asp.atoms(model, "combo"))
    return combos


def asp_verify(params: StoryParams) -> bool:
    import asp

    model = asp.one_model(asp_program(params))
    return bool(asp.atoms(model, "ok"))


def verify() -> str:
    python_combos = set(valid_combos())
    asp_combos = asp_valid_combos()
    if python_combos != asp_combos:
        only_python = sorted(python_combos - asp_combos)
        only_asp = sorted(asp_combos - python_combos)
        raise StoryError(f"ASP/Python mismatch. only_python={only_python} only_asp={only_asp}")

    exercised = 0
    for i, combo in enumerate(sorted(python_combos)):
        nook, ship, disturbance, remedy, book = combo
        params = StoryParams(
            nook=nook,
            ship=ship,
            disturbance=disturbance,
            remedy=remedy,
            book=book,
            name="Mira",
            gender="girl",
            helper="grandmother",
            trait="careful",
            seed=i,
        )
        if not asp_verify(params):
            raise StoryError(f"ASP rejected Python-valid combo: {combo}")
        sample = generate(params)
        if "cozy ship" not in sample.story:
            raise StoryError(f"Generated story missing seed phrase for combo: {combo}")
        if "reading nook" not in sample.story:
            raise StoryError(f"Generated story missing setting phrase for combo: {combo}")
        if "thought" not in sample.story:
            raise StoryError(f"Generated story missing inner monologue framing for combo: {combo}")
        if len(sample.story_qa) < 5 or len(sample.world_qa) < 3:
            raise StoryError(f"Generated QA too thin for combo: {combo}")
        exercised += 1
    return f"OK: ASP and Python agree on {len(python_combos)} valid cozy-ship stories; exercised {exercised} samples."


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate cozy ship fairy-tale storyworld samples.")
    parser.add_argument("--nook", choices=sorted(NOOKS))
    parser.add_argument("--ship", choices=sorted(SHIPS))
    parser.add_argument("--disturbance", choices=sorted(DISTURBANCES))
    parser.add_argument("--remedy", choices=sorted(REMEDIES))
    parser.add_argument("--book", choices=sorted(BOOKS))
    parser.add_argument("--name")
    parser.add_argument("--gender", choices=sorted(HEROES))
    parser.add_argument("--helper", choices=HELPERS)
    parser.add_argument("--trait", choices=TRAITS)
    parser.add_argument("--seed", type=int)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def _matching_combos(args: argparse.Namespace) -> list[tuple[str, str, str, str, str]]:
    rows: list[tuple[str, str, str, str, str]] = []
    for combo in valid_combos():
        nook, ship, disturbance, remedy, book = combo
        if args.nook and args.nook != nook:
            continue
        if args.ship and args.ship != ship:
            continue
        if args.disturbance and args.disturbance != disturbance:
            continue
        if args.remedy and args.remedy != remedy:
            continue
        if args.book and args.book != book:
            continue
        rows.append(combo)
    return rows


def _make_params(
    args: argparse.Namespace,
    rng: random.Random,
    combo: tuple[str, str, str, str, str],
    seed: int | None,
) -> StoryParams:
    gender = args.gender or rng.choice(sorted(HEROES))
    name = args.name or rng.choice(HEROES[gender])
    helper = args.helper or rng.choice(HELPERS)
    trait = args.trait or rng.choice(TRAITS)
    nook, ship, disturbance, remedy, book = combo
    return StoryParams(
        nook=nook,
        ship=ship,
        disturbance=disturbance,
        remedy=remedy,
        book=book,
        name=name,
        gender=gender,
        helper=helper,
        trait=trait,
        seed=seed,
    )


def resolve_params(args: argparse.Namespace, rng: random.Random | None = None) -> StoryParams:
    rng = rng or random.Random(args.seed)
    combos = _matching_combos(args)
    if not combos:
        nook = args.nook or next(iter(NOOKS))
        ship = args.ship or next(iter(SHIPS))
        disturbance = args.disturbance or next(iter(DISTURBANCES))
        remedy = args.remedy or next(iter(REMEDIES))
        book = args.book or next(iter(BOOKS))
        raise StoryError(explain_rejection(nook, ship, disturbance, remedy, book))
    seed = getattr(rng, "story_seed", args.seed)
    return _make_params(args, rng, rng.choice(combos), seed)


def format_qa(sample: StorySample) -> str:
    lines = ["", "== (1) Generation prompts =="]
    lines.extend(f"{i}. {prompt}" for i, prompt in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== (2) Story-grounded QA ==")
    for qa in sample.story_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge QA ==")
    for qa in sample.world_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    return "\n".join(lines)


def emit(sample: StorySample, args: argparse.Namespace, header: str | None = None) -> None:
    if header:
        print(header)
    print(sample.story)
    if args.trace and sample.world is not None:
        print(sample.world.trace())
    if args.qa:
        print(format_qa(sample))


def _json_dump(samples: list[StorySample]) -> None:
    if len(samples) == 1:
        print(samples[0].to_json())
        return
    print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))


def _samples_for_all(args: argparse.Namespace) -> list[StorySample]:
    rows: list[StorySample] = []
    base_seed = args.seed if args.seed is not None else 1000
    for i, combo in enumerate(valid_combos()):
        story_seed = base_seed + i
        rng = random.Random(story_seed)
        rng.story_seed = story_seed
        rows.append(generate(_make_params(args, rng, combo, story_seed)))
    return rows


def _samples_for_n(args: argparse.Namespace) -> list[StorySample]:
    base_seed = args.seed if args.seed is not None else random.randrange(1, 1_000_000)
    target = max(1, args.n)
    rows: list[StorySample] = []
    seen: set[str] = set()
    i = 0
    while len(rows) < target and i < target * 40:
        story_seed = base_seed + i
        rng = random.Random(story_seed)
        rng.story_seed = story_seed
        sample = generate(resolve_params(args, rng))
        if sample.story not in seen:
            seen.add(sample.story)
            rows.append(sample)
        i += 1
    return rows


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        if args.show_asp:
            print(asp_program())
            return 0
        if args.verify:
            print(verify())
            return 0
        if args.asp:
            for combo in sorted(asp_valid_combos()):
                print("\t".join(combo))
            return 0

        samples = _samples_for_all(args) if args.all else _samples_for_n(args)
        if args.json:
            _json_dump(samples)
            return 0
        for i, sample in enumerate(samples):
            header = None
            if args.all:
                header = (
                    f"### {sample.params.name}: {sample.params.ship} / "
                    f"{sample.params.disturbance} / {sample.params.book}"
                )
            elif len(samples) > 1:
                header = f"### variant {i + 1}"
            emit(sample, args, header)
            if i != len(samples) - 1:
                print("\n" + "=" * 70 + "\n")
        return 0
    except StoryError as exc:
        print(exc, file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
