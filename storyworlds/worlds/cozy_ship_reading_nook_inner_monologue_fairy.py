#!/usr/bin/env python3
"""A fairy-tale storyworld about a cozy ship in a reading nook.

Seed:
    Words: cozy ship
    Setting: reading nook
    Features: Inner Monologue
    Style: Fairy Tale

Internal source tale:
    A child climbs into a cozy ship built inside a reading nook to read a fairy
    tale. One small physical disturbance makes the child privately imagine a
    larger enchantment. A gentle nudge leads the child to inspect the nook,
    discover the real cause, mend it, and finish the story in a visibly calmer
    harbor of blankets and pages.
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        if self.kind != "character":
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        female = {"girl", "woman", "grandmother", "aunt", "sister"}
        male = {"boy", "man", "uncle", "brother", "grandfather"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def kin_word(self) -> str:
        words = {
            "grandmother": "grandmother",
            "aunt": "aunt",
            "uncle": "uncle",
            "sister": "sister",
            "brother": "brother",
        }
        return words.get(self.type, self.type)

    @property
    def title_word(self) -> str:
        return self.kin_word.capitalize()


@dataclass(frozen=True)
class Nook:
    id: str
    label: str
    scene: str
    window_detail: str
    final_image: str
    supports: set[str] = field(default_factory=set)
    ships: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass(frozen=True)
class ShipKind:
    id: str
    label: str
    phrase: str
    sail_detail: str
    anchor_detail: str
    ending_pose: str
    sensitive_to: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass(frozen=True)
class Unrest:
    id: str
    issue: str
    omen: str
    thought: str
    nudge: str
    inspect: str
    reveal: str
    lesson: str
    tags: set[str] = field(default_factory=set)


@dataclass(frozen=True)
class Remedy:
    id: str
    label: str
    guards: set[str]
    action: str
    result: str
    ending: str
    tags: set[str] = field(default_factory=set)


@dataclass(frozen=True)
class Book:
    id: str
    title: str
    quest: str
    page_detail: str
    closing_line: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    nook: str
    ship: str
    unrest: str
    remedy: str
    book: str
    name: str
    gender: str
    helper: str
    trait: str
    seed: Optional[int] = None


class World:
    def __init__(self, params: StoryParams) -> None:
        self.params = params
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.fired_names: list[str] = []
        self.facts: dict[str, object] = {}

    def copy(self) -> "World":
        return copy.deepcopy(self)

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, entity_id: str) -> Entity:
        return self.entities[entity_id]

    def say(self, sentence: str) -> None:
        sentence = sentence.strip()
        if sentence:
            self.paragraphs[-1].append(sentence)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(par) for par in self.paragraphs if par)

    def trace(self) -> str:
        lines = [
            f"params: {self.params}",
            f"active issue: {self.facts.get('issue', 'none')}",
            f"fired rules: {', '.join(self.fired_names) if self.fired_names else 'none'}",
        ]
        for ent in self.entities.values():
            meters = {k: v for k, v in ent.meters.items() if v}
            memes = {k: v for k, v in ent.memes.items() if v}
            lines.append(f"  {ent.id} | {ent.kind} | {ent.type} | {ent.label}")
            if meters:
                lines.append(f"    meters={meters}")
            if memes:
                lines.append(f"    memes={memes}")
        return "\n".join(lines)


@dataclass(frozen=True)
class Rule:
    name: str
    apply: Callable[[World], bool]


def sentence_case(text: str) -> str:
    if not text:
        return text
    return text[0].upper() + text[1:]


def lower_first(text: str) -> str:
    if not text:
        return text
    return text[0].lower() + text[1:]


def _mark(world: World, name: str, *parts: object) -> bool:
    sig = (name, *parts)
    if sig in world.fired:
        return False
    world.fired.add(sig)
    world.fired_names.append(name)
    return True


def _r_draft_flutter(world: World) -> bool:
    window = world.get("window")
    book = world.get("book")
    ship = world.get("ship")
    if window.meters["ajar"] < THRESHOLD:
        return False
    if not _mark(world, "draft_flutter", window.id):
        return False
    book.meters["pages_lifting"] += 1
    ship.meters["sail_trembling"] += 1
    return True


def _r_shadow_grow(world: World) -> bool:
    lantern = world.get("lantern")
    ship = world.get("ship")
    book = world.get("book")
    if lantern.meters["shade_crooked"] < THRESHOLD:
        return False
    if not _mark(world, "shadow_grow", lantern.id):
        return False
    ship.meters["shadow_tall"] += 1
    book.meters["page_dim"] += 1
    return True


def _r_anchor_slip(world: World) -> bool:
    anchor = world.get("anchor")
    ship = world.get("ship")
    book = world.get("book")
    if anchor.meters["loose"] < THRESHOLD:
        return False
    if not _mark(world, "anchor_slip", anchor.id):
        return False
    ship.meters["listing"] += 1
    book.meters["sliding"] += 1
    return True


def _r_inner_worry(world: World) -> bool:
    hero = world.get("hero")
    ship = world.get("ship")
    book = world.get("book")
    if hero.memes["inner_voice"] < THRESHOLD:
        return False
    if (
        ship.meters["sail_trembling"] < THRESHOLD
        and ship.meters["shadow_tall"] < THRESHOLD
        and ship.meters["listing"] < THRESHOLD
        and book.meters["pages_lifting"] < THRESHOLD
        and book.meters["page_dim"] < THRESHOLD
        and book.meters["sliding"] < THRESHOLD
    ):
        return False
    if not _mark(world, "inner_worry", hero.id):
        return False
    hero.memes["worry"] += 1
    hero.memes["wonder"] += 1
    return True


def _r_checked_truth(world: World) -> bool:
    hero = world.get("hero")
    issue = world.facts.get("issue")
    if hero.memes["checked"] < THRESHOLD or not isinstance(issue, str):
        return False
    if not _mark(world, "checked_truth", hero.id, issue):
        return False
    hero.memes["clarity"] += 1
    hero.memes["worry"] = max(0.0, hero.memes["worry"] - 0.5)
    return True


def _r_ship_steadies(world: World) -> bool:
    hero = world.get("hero")
    ship = world.get("ship")
    book = world.get("book")
    if not world.facts.get("issue_cleared"):
        return False
    if not _mark(world, "ship_steadies", ship.id):
        return False
    ship.meters["steady"] += 1
    ship.meters["cozy"] += 1
    book.meters["readable"] += 1
    hero.memes["courage"] += 1
    hero.memes["peace"] += 1
    return True


RULES = [
    Rule("draft_flutter", _r_draft_flutter),
    Rule("shadow_grow", _r_shadow_grow),
    Rule("anchor_slip", _r_anchor_slip),
    Rule("inner_worry", _r_inner_worry),
    Rule("checked_truth", _r_checked_truth),
    Rule("ship_steadies", _r_ship_steadies),
]


def propagate(world: World) -> None:
    changed = True
    while changed:
        changed = False
        for rule in RULES:
            if rule.apply(world):
                changed = True


NOOKS = {
    "round_window": Nook(
        id="round_window",
        label="the round-window reading nook",
        scene="cushions curved into a little prow beneath shelves of fairy books",
        window_detail="A brass-rimmed round window watched over the blankets like a moon",
        final_image="the round window shone above the blankets like a pearl above a sleeping harbor",
        supports={"draft", "shadow"},
        ships={"quilt_sloop", "bookshelf_brig"},
        tags={"reading_nook", "window"},
    ),
    "hearth_cove": Nook(
        id="hearth_cove",
        label="the hearth-cove reading nook",
        scene="a warm rug, a low lamp, and stacked pillows made a harbor by the bricks",
        window_detail="The nearest light was a star-lantern hanging from a wooden peg",
        final_image="the hearth-cove glowed so softly that even the shadows looked ready for bed",
        supports={"shadow", "slip"},
        ships={"velvet_galleon", "quilt_sloop"},
        tags={"reading_nook", "lantern"},
    ),
    "eaves_hollow": Nook(
        id="eaves_hollow",
        label="the eaves reading nook",
        scene="a slanted roof tucked the cushions close, and old storybooks leaned like tiny houses",
        window_detail="A narrow attic window and a chair leg kept the blankets honest",
        final_image="the eaves nook rested as still as a nest while the last page glimmered",
        supports={"draft", "slip"},
        ships={"patchwork_skiff", "bookshelf_brig"},
        tags={"reading_nook", "attic"},
    ),
}


SHIPS = {
    "quilt_sloop": ShipKind(
        id="quilt_sloop",
        label="Quilt Sloop",
        phrase="a cozy ship stitched from quilts, pillows, and one pale-blue blanket sail",
        sail_detail="the blanket sail bowed over the cushions like a sleepy wing",
        anchor_detail="a satin ribbon tied the prow to a chair leg so the ship would not drift over the rug sea",
        ending_pose="the little quilt ship rested with its prow straight and its sail smooth",
        sensitive_to={"draft", "slip"},
        tags={"cozy_ship", "blanket", "ribbon"},
    ),
    "velvet_galleon": ShipKind(
        id="velvet_galleon",
        label="Velvet Galleon",
        phrase="a cozy ship with velvet cushions for decks and a paper star lantern near its mast",
        sail_detail="its velvet sides swallowed sound the way a cave swallows echoes",
        anchor_detail="a braided cord held the prow in place beside the hearth",
        ending_pose="the velvet galleon glowed with a friendly edge instead of a looming one",
        sensitive_to={"shadow", "slip"},
        tags={"cozy_ship", "lantern", "velvet"},
    ),
    "bookshelf_brig": ShipKind(
        id="bookshelf_brig",
        label="Bookshelf Brig",
        phrase="a cozy ship tucked beneath the bookshelves, with a ribbon sail and biscuit-tin lantern",
        sail_detail="the ribbon sail liked to whisper whenever the air forgot its manners",
        anchor_detail="a neat loop of cord hugged the bookcase rung like an anchor ring",
        ending_pose="the bookshelf brig looked snug enough to sail only through stories",
        sensitive_to={"draft", "shadow"},
        tags={"cozy_ship", "books", "lantern"},
    ),
    "patchwork_skiff": ShipKind(
        id="patchwork_skiff",
        label="Patchwork Skiff",
        phrase="a cozy ship made from patchwork blankets, a cushion stern, and a twine bowline",
        sail_detail="the patchwork sides puffed up like warm bread around the reader",
        anchor_detail="its twine bowline kept the skiff from tilting when the reader turned a page too fast",
        ending_pose="the patchwork skiff sat level again, ready for another chapter-voyage",
        sensitive_to={"draft", "slip"},
        tags={"cozy_ship", "patchwork", "knot"},
    ),
}


UNRESTS = {
    "draft_whisper": Unrest(
        id="draft_whisper",
        issue="draft",
        omen="one silver page lifted like a flag and the small sail of blankets gave a chilly shiver",
        thought="If I read this part aloud, the window-wind may steal the silver words before the ending can find its harbor.",
        nudge="Little captain, let your eyes test the room before your fear names the magic.",
        inspect="The child held one hand near the round edge of the nook and felt a thin cool thread brush the knuckles.",
        reveal="The window latch stood a thumb-width open, so the draft was real and ordinary, not a spell at all.",
        lesson="Fear grows smaller when a child looks for the true cause with open eyes.",
        tags={"draft", "window", "inner_voice"},
    ),
    "lantern_shadow": Unrest(
        id="lantern_shadow",
        issue="shadow",
        omen="a huge shadow climbed across the sail, and the bright picture on the page turned dim at the edges",
        thought="Perhaps a cave giant has stepped aboard and wants to swallow the happy ending before I can reach it.",
        nudge="Not every large shadow belongs to a giant. Sometimes light itself asks to be set right.",
        inspect="The child looked up instead of shrinking down and saw that the lantern's paper shade had turned crooked on its peg.",
        reveal="The shadow seemed monstrous only because the lantern had slipped sideways and thrown the light wrong.",
        lesson="A brave look can untangle a frightening shape into one simple thing.",
        tags={"shadow", "lantern", "inner_voice"},
    ),
    "anchor_sigh": Unrest(
        id="anchor_sigh",
        issue="slip",
        omen="the prow leaned, the book slid against one knee, and the blankets sighed as if the ship wished to drift away",
        thought="Maybe the cozy ship longs for the dark sea under the floorboards and will leave before my story can find its ending.",
        nudge="If a ship feels restless, follow what is tied and what is loose before you trust the saddest thought.",
        inspect="The child traced the ribbon and twine near the prow until the fingers found a knot that had eased open.",
        reveal="The ship was not trying to escape; its anchor knot had simply loosened while the blankets were being fluffed.",
        lesson="A worried story in the heart can soften when the hands find the true knot.",
        tags={"slip", "knot", "inner_voice"},
    ),
}


REMEDIES = {
    "latch_window": Remedy(
        id="latch_window",
        label="latching the window",
        guards={"draft"},
        action="pressed the brass moon-latch until it clicked and kissed the window shut",
        result="At once the page settled down and the little sail forgot its shiver.",
        ending="The words stayed aboard long enough to shine.",
        tags={"draft", "window"},
    ),
    "straighten_lantern": Remedy(
        id="straighten_lantern",
        label="straightening the lantern",
        guards={"shadow"},
        action="reached up with the helper and set the star-lantern straight on its peg",
        result="The giant shadow folded itself back into a small honest shape beside the mast.",
        ending="The page brightened, and the brave part of the tale could be read without a monster anywhere near it.",
        tags={"shadow", "lantern"},
    ),
    "retie_anchor": Remedy(
        id="retie_anchor",
        label="retying the anchor ribbon",
        guards={"slip"},
        action="retied the anchor ribbon and twine in a firm bow against the chair leg",
        result="The prow lifted true again, and the blankets stopped trying to slide under the reader.",
        ending="The ship could hold still while the story sailed on.",
        tags={"slip", "knot"},
    ),
}


BOOKS = {
    "moon_map": Book(
        id="moon_map",
        title="The Moon Map",
        quest="a prince was following a silver map toward a harbor in the sky",
        page_detail="its moon-bright page showed a harbor drawn in silver loops",
        closing_line="Soon the child read the moon-map chapter in a voice quiet and bright as a bell under a blanket.",
        tags={"fairy_tale", "map"},
    ),
    "pearl_stair": Book(
        id="pearl_stair",
        title="The Pearl Stair",
        quest="a princess was searching for a stair of pearls hidden inside an ordinary shell",
        page_detail="its next page held a pearl stair curling up through painted water",
        closing_line="Soon the child read about the pearl stair until the last shell on the page opened into light.",
        tags={"fairy_tale", "pearl"},
    ),
    "thimble_crown": Book(
        id="thimble_crown",
        title="The Thimble Crown",
        quest="a tailor-wren was carrying a tiny crown to the valley of kind kings",
        page_detail="its bright page showed a bird holding a thimble crown in its beak",
        closing_line="Soon the child read on until the little crown reached the valley it had been promised.",
        tags={"fairy_tale", "crown"},
    ),
}


GIRL_NAMES = ["Elsie", "Mira", "Nora", "Lina", "Poppy", "Wren"]
BOY_NAMES = ["Theo", "Milo", "Rowan", "Jasper", "Finn", "Ari"]
TRAITS = ["bookish", "dreamy", "gentle", "thoughtful", "brave"]
HELPERS = ["grandmother", "aunt", "uncle", "sister"]


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for nook_id, nook in NOOKS.items():
        for ship_id in sorted(nook.ships):
            ship = SHIPS[ship_id]
            for unrest_id, unrest in UNRESTS.items():
                if unrest.issue not in nook.supports:
                    continue
                if unrest.issue not in ship.sensitive_to:
                    continue
                for remedy_id, remedy in REMEDIES.items():
                    if unrest.issue in remedy.guards:
                        combos.append((nook_id, ship_id, unrest_id, remedy_id))
    return combos


def compatible(nook: Nook, ship: ShipKind, unrest: Unrest, remedy: Remedy) -> bool:
    return (
        ship.id in nook.ships
        and unrest.issue in nook.supports
        and unrest.issue in ship.sensitive_to
        and unrest.issue in remedy.guards
    )


def explain_rejection(nook: Nook, ship: ShipKind, unrest: Unrest, remedy: Remedy) -> str:
    if ship.id not in nook.ships:
        return (
            f"(No story: {nook.label} does not host the {ship.label}, so the reading-nook world is not grounded.)"
        )
    if unrest.issue not in nook.supports:
        return (
            f"(No story: {nook.label} does not plausibly create the '{unrest.issue}' trouble in this seed domain.)"
        )
    if unrest.issue not in ship.sensitive_to:
        return (
            f"(No story: the {ship.label} is not modeled as vulnerable to the '{unrest.issue}' disturbance.)"
        )
    if unrest.issue not in remedy.guards:
        return (
            f"(No story: {remedy.label} does not resolve the '{unrest.issue}' disturbance, so the turn would be weak.)"
        )
    return "(No story: the requested combination is not reasonable in this world.)"


def build_world(params: StoryParams) -> World:
    world = World(params)
    hero = world.add(
        Entity(
            id="hero",
            kind="character",
            type=params.gender,
            label=params.name,
            role="hero",
            traits=[params.trait],
        )
    )
    helper = world.add(
        Entity(
            id="helper",
            kind="character",
            type=params.helper,
            label=params.helper,
            role="helper",
        )
    )
    world.add(Entity(id="ship", label=SHIPS[params.ship].label))
    world.add(Entity(id="book", label=BOOKS[params.book].title))
    world.add(Entity(id="window", label="window"))
    world.add(Entity(id="lantern", label="lantern"))
    world.add(Entity(id="anchor", label="anchor ribbon"))
    world.facts.update(
        hero=hero,
        helper=helper,
        nook=NOOKS[params.nook],
        ship_cfg=SHIPS[params.ship],
        unrest=UNRESTS[params.unrest],
        remedy=REMEDIES[params.remedy],
        book_cfg=BOOKS[params.book],
        issue=UNRESTS[params.unrest].issue,
    )
    hero.memes["imagination"] += 1
    hero.memes["love_of_stories"] += 1
    world.get("ship").meters["cozy"] += 1
    world.get("book").meters["openable"] += 1
    return world


def introduce(world: World) -> None:
    hero: Entity = world.facts["hero"]  # type: ignore[assignment]
    helper: Entity = world.facts["helper"]  # type: ignore[assignment]
    nook: Nook = world.facts["nook"]  # type: ignore[assignment]
    ship_cfg: ShipKind = world.facts["ship_cfg"]  # type: ignore[assignment]
    book_cfg: Book = world.facts["book_cfg"]  # type: ignore[assignment]
    world.say(
        f"Once upon a time, there was a little {hero.traits[0]} {hero.type} named {hero.label}."
    )
    world.say(
        f"In {nook.label}, {ship_cfg.phrase} waited among {nook.scene}. "
        f"{nook.window_detail}."
    )
    world.say(
        f"{hero.label} climbed into the cozy ship with {book_cfg.title}, where {ship_cfg.sail_detail}. "
        f"Nearby, {helper.title_word} kept a gentle watch and let the voyage belong to {hero.label}."
    )


def stir_disturbance(world: World) -> None:
    unrest: Unrest = world.facts["unrest"]  # type: ignore[assignment]
    window = world.get("window")
    lantern = world.get("lantern")
    anchor = world.get("anchor")
    if unrest.issue == "draft":
        window.meters["ajar"] += 1
    elif unrest.issue == "shadow":
        lantern.meters["shade_crooked"] += 1
    elif unrest.issue == "slip":
        anchor.meters["loose"] += 1
    else:
        raise StoryError(f"(No story: unsupported issue {unrest.issue!r}.)")
    propagate(world)


def describe_disturbance(world: World) -> None:
    hero: Entity = world.facts["hero"]  # type: ignore[assignment]
    ship = world.get("ship")
    book_cfg: Book = world.facts["book_cfg"]  # type: ignore[assignment]
    unrest: Unrest = world.facts["unrest"]  # type: ignore[assignment]
    book = world.get("book")
    world.say(
        f"When {hero.label} opened {book_cfg.title}, {book_cfg.page_detail}, and {unrest.omen}."
    )
    if ship.meters["sail_trembling"] >= THRESHOLD and book.meters["pages_lifting"] >= THRESHOLD:
        world.facts["visible_clue"] = "the lifting page and the trembling sail"
    elif ship.meters["shadow_tall"] >= THRESHOLD and book.meters["page_dim"] >= THRESHOLD:
        world.facts["visible_clue"] = "the giant shadow and the dim page edge"
    elif ship.meters["listing"] >= THRESHOLD and book.meters["sliding"] >= THRESHOLD:
        world.facts["visible_clue"] = "the leaning prow and the sliding book"
    else:
        world.facts["visible_clue"] = "the small strange change in the nook"


def inner_monologue(world: World) -> None:
    hero: Entity = world.facts["hero"]  # type: ignore[assignment]
    unrest: Unrest = world.facts["unrest"]  # type: ignore[assignment]
    hero.memes["inner_voice"] += 1
    propagate(world)
    world.say(f'{hero.label} thought, "{unrest.thought}"')
    world.say(
        f"The thought sounded very grand inside {hero.pronoun('possessive')} chest, "
        f"which is the way worried thoughts often speak when a child is alone with a story."
    )
    world.facts["private_thought"] = unrest.thought


def nudge_and_inspect(world: World) -> None:
    hero: Entity = world.facts["hero"]  # type: ignore[assignment]
    helper: Entity = world.facts["helper"]  # type: ignore[assignment]
    unrest: Unrest = world.facts["unrest"]  # type: ignore[assignment]
    world.say(f'{helper.title_word} said, "{unrest.nudge}"')
    hero.memes["checked"] += 1
    propagate(world)
    world.say(unrest.inspect)
    world.say(unrest.reveal)
    world.facts["truth_line"] = unrest.reveal


def apply_remedy(world: World) -> None:
    hero: Entity = world.facts["hero"]  # type: ignore[assignment]
    helper: Entity = world.facts["helper"]  # type: ignore[assignment]
    remedy: Remedy = world.facts["remedy"]  # type: ignore[assignment]
    issue = world.facts["issue"]
    action_line = remedy.action
    if issue == "draft":
        window = world.get("window")
        window.meters["ajar"] = 0.0
        window.meters["latched"] += 1
        world.get("book").meters["pages_lifting"] = 0.0
        world.get("ship").meters["sail_trembling"] = 0.0
    elif issue == "shadow":
        lantern = world.get("lantern")
        lantern.meters["shade_crooked"] = 0.0
        lantern.meters["straight"] += 1
        world.get("ship").meters["shadow_tall"] = 0.0
        world.get("book").meters["page_dim"] = 0.0
        action_line = f"reached up with {helper.title_word} and set the star-lantern straight on its peg"
    elif issue == "slip":
        anchor = world.get("anchor")
        anchor.meters["loose"] = 0.0
        anchor.meters["firm"] += 1
        world.get("ship").meters["listing"] = 0.0
        world.get("book").meters["sliding"] = 0.0
    else:
        raise StoryError(f"(No story: unsupported issue {issue!r}.)")
    world.facts["issue_cleared"] = True
    propagate(world)
    world.say(f"{hero.label} {action_line}.")
    world.say(remedy.result)
    world.facts["remedy_line"] = action_line


def conclude(world: World) -> None:
    hero: Entity = world.facts["hero"]  # type: ignore[assignment]
    nook: Nook = world.facts["nook"]  # type: ignore[assignment]
    ship_cfg: ShipKind = world.facts["ship_cfg"]  # type: ignore[assignment]
    unrest: Unrest = world.facts["unrest"]  # type: ignore[assignment]
    remedy: Remedy = world.facts["remedy"]  # type: ignore[assignment]
    book_cfg: Book = world.facts["book_cfg"]  # type: ignore[assignment]
    ship = world.get("ship")
    if ship.meters["steady"] < THRESHOLD:
        raise StoryError("(No story: the ship never steadied, so the ending would not prove change.)")
    world.say(
        f"{book_cfg.closing_line} {remedy.ending}"
    )
    world.say(
        f"In the end, {ship_cfg.ending_pose}, and {nook.final_image}. "
        f"{hero.label} learned that {unrest.lesson.lower()}"
    )
    world.facts["resolved"] = True
    world.facts["ending_image"] = f"{ship_cfg.ending_pose}, and {nook.final_image}"


def tell(params: StoryParams) -> World:
    nook = NOOKS[params.nook]
    ship = SHIPS[params.ship]
    unrest = UNRESTS[params.unrest]
    remedy = REMEDIES[params.remedy]
    if not compatible(nook, ship, unrest, remedy):
        raise StoryError(explain_rejection(nook, ship, unrest, remedy))
    world = build_world(params)
    introduce(world)
    world.para()
    stir_disturbance(world)
    describe_disturbance(world)
    inner_monologue(world)
    world.para()
    nudge_and_inspect(world)
    apply_remedy(world)
    conclude(world)
    return world


KNOWLEDGE = {
    "reading_nook": [
        (
            "Why can a reading nook feel special to a child?",
            "A reading nook is small, soft, and easy to notice with all the senses. That makes it feel like a safe place where imagination can grow.",
        )
    ],
    "draft": [
        (
            "What can a draft do to a page or blanket sail?",
            "A draft can lift loose pages and shake light fabric. Small moving air can feel magical until someone finds the open window.",
        )
    ],
    "shadow": [
        (
            "Why can a lamp make a shadow look bigger than it really is?",
            "When light is tilted the wrong way, a shadow can stretch and loom. The object may stay small even when the shadow looks huge.",
        )
    ],
    "window": [
        (
            "Why does shutting a latch help in a cozy room?",
            "A shut latch keeps cold moving air from sneaking in. That helps pages, curtains, and blanket sails stay calm.",
        )
    ],
    "lantern": [
        (
            "How can setting a lantern straight change a room?",
            "A straight lantern throws light where it belongs. When the light behaves, scary shapes often become ordinary things again.",
        )
    ],
    "knot": [
        (
            "Why do knots matter in a blanket fort or play ship?",
            "A good knot holds soft parts in place so they do not sag or slide. Even pretend ships need real ties to stay steady.",
        )
    ],
    "slip": [
        (
            "What happens when an anchor ribbon comes loose?",
            "The tied part can lean or drift because it has lost its hold. Fixing the knot returns balance to the whole structure.",
        )
    ],
    "inner_voice": [
        (
            "What is inner monologue in a story?",
            "Inner monologue is the private talk a character hears inside the mind. It lets readers feel a worry, hope, or guess before the character speaks aloud.",
        )
    ],
    "fairy_tale": [
        (
            "What makes a story feel like a fairy tale?",
            "A fairy tale often begins with a simple promise, uses glowing or enchanted images, and ends with a clear change in the heart or home. Ordinary objects can feel magical while still following the story's truth.",
        )
    ],
}
KNOWLEDGE_ORDER = [
    "reading_nook",
    "inner_voice",
    "draft",
    "window",
    "shadow",
    "lantern",
    "slip",
    "knot",
    "fairy_tale",
]


def generation_prompts(world: World) -> list[str]:
    hero: Entity = world.facts["hero"]  # type: ignore[assignment]
    nook: Nook = world.facts["nook"]  # type: ignore[assignment]
    ship_cfg: ShipKind = world.facts["ship_cfg"]  # type: ignore[assignment]
    unrest: Unrest = world.facts["unrest"]  # type: ignore[assignment]
    remedy: Remedy = world.facts["remedy"]  # type: ignore[assignment]
    book_cfg: Book = world.facts["book_cfg"]  # type: ignore[assignment]
    return [
        "Write a child-facing fairy tale set in a reading nook where a cozy ship feels almost real.",
        f"Tell a story in which {hero.label} privately imagines danger after {unrest.omen}, then discovers the true cause and fixes it by {remedy.label}.",
        f"Write a gentle fairy tale around {book_cfg.title}, where {nook.label} and the {ship_cfg.label} change visibly after one grounded repair.",
    ]


def story_qa_pairs(world: World) -> list[tuple[str, str]]:
    hero: Entity = world.facts["hero"]  # type: ignore[assignment]
    helper: Entity = world.facts["helper"]  # type: ignore[assignment]
    nook: Nook = world.facts["nook"]  # type: ignore[assignment]
    ship_cfg: ShipKind = world.facts["ship_cfg"]  # type: ignore[assignment]
    unrest: Unrest = world.facts["unrest"]  # type: ignore[assignment]
    remedy: Remedy = world.facts["remedy"]  # type: ignore[assignment]
    book_cfg: Book = world.facts["book_cfg"]  # type: ignore[assignment]
    clue = str(world.facts["visible_clue"])
    truth = str(world.facts["truth_line"])
    ending = str(world.facts["ending_image"])
    remedy_line = str(world.facts["remedy_line"])
    return [
        (
            "Who is the story about, and where does it begin?",
            f"It is about {hero.label}, a little {hero.traits[0]} {hero.type}. The story begins in {nook.label}, where {ship_cfg.phrase} is waiting for a reading voyage.",
        ),
        (
            "What disturbed the cozy ship?",
            f"The first sign was {clue}. That disturbance came from the '{unrest.issue}' trouble in the nook, so the ship felt changed before the child understood why.",
        ),
        (
            f"What did {hero.label} think in private?",
            f"{hero.label} secretly thought, \"{unrest.thought}\" The inner monologue made the moment feel larger and more magical than the ordinary cause really was.",
        ),
        (
            "How did the child learn the truth?",
            f"{helper.title_word} gave a gentle nudge to look closely instead of trusting the first fear. Then they discovered that {lower_first(truth)}",
        ),
        (
            "How was the problem fixed?",
            f"{hero.label} fixed it by {remedy.label}. Then {hero.label} {remedy_line}.",
        ),
        (
            "What changed at the end?",
            f"At the end, the ship and book were calm enough for {book_cfg.title} to continue. {sentence_case(ending)}.",
        ),
    ]


def world_knowledge_pairs(world: World) -> list[tuple[str, str]]:
    nook: Nook = world.facts["nook"]  # type: ignore[assignment]
    ship_cfg: ShipKind = world.facts["ship_cfg"]  # type: ignore[assignment]
    unrest: Unrest = world.facts["unrest"]  # type: ignore[assignment]
    remedy: Remedy = world.facts["remedy"]  # type: ignore[assignment]
    book_cfg: Book = world.facts["book_cfg"]  # type: ignore[assignment]
    tags = set(nook.tags) | set(ship_cfg.tags) | set(unrest.tags) | set(remedy.tags) | set(book_cfg.tags)
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
            out.extend(KNOWLEDGE[tag])
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for idx, prompt in enumerate(sample.prompts, 1):
        lines.append(f"{idx}. {prompt}")
    lines.append("")
    lines.append("== (2) Story-grounded QA ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge QA ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    return "--- world model state ---\n" + world.trace()


CURATED = [
    StoryParams("round_window", "bookshelf_brig", "draft_whisper", "latch_window", "moon_map", "Lina", "girl", "grandmother", "bookish"),
    StoryParams("hearth_cove", "velvet_galleon", "lantern_shadow", "straighten_lantern", "pearl_stair", "Theo", "boy", "aunt", "dreamy"),
    StoryParams("eaves_hollow", "patchwork_skiff", "anchor_sigh", "retie_anchor", "thimble_crown", "Nora", "girl", "uncle", "brave"),
    StoryParams("hearth_cove", "quilt_sloop", "anchor_sigh", "retie_anchor", "moon_map", "Milo", "boy", "sister", "gentle"),
    StoryParams("round_window", "bookshelf_brig", "lantern_shadow", "straighten_lantern", "pearl_stair", "Elsie", "girl", "grandmother", "thoughtful"),
]


ASP_RULES = r"""
compatible_issue(N,S,U,R) :- hosts_ship(N,S), unrest_issue(U,I), supports(N,I), sensitive(S,I), guards(R,I).
valid(N,S,U,R) :- compatible_issue(N,S,U,R).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for nook_id, nook in NOOKS.items():
        lines.append(asp.fact("nook", nook_id))
        for issue in sorted(nook.supports):
            lines.append(asp.fact("supports", nook_id, issue))
        for ship_id in sorted(nook.ships):
            lines.append(asp.fact("hosts_ship", nook_id, ship_id))
    for ship_id, ship in SHIPS.items():
        lines.append(asp.fact("ship", ship_id))
        for issue in sorted(ship.sensitive_to):
            lines.append(asp.fact("sensitive", ship_id, issue))
    for unrest_id, unrest in UNRESTS.items():
        lines.append(asp.fact("unrest", unrest_id))
        lines.append(asp.fact("unrest_issue", unrest_id, unrest.issue))
    for remedy_id, remedy in REMEDIES.items():
        lines.append(asp.fact("remedy", remedy_id))
        for issue in sorted(remedy.guards):
            lines.append(asp.fact("guards", remedy_id, issue))
    for book_id in BOOKS:
        lines.append(asp.fact("book", book_id))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple[str, str, str, str]]:
    import asp

    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def verify_generated_stories() -> list[str]:
    errors: list[str] = []
    books = sorted(BOOKS)
    helper_cycle = list(HELPERS)
    for idx, (nook_id, ship_id, unrest_id, remedy_id) in enumerate(sorted(valid_combos())):
        gender = "girl" if idx % 2 == 0 else "boy"
        names = GIRL_NAMES if gender == "girl" else BOY_NAMES
        params = StoryParams(
            nook=nook_id,
            ship=ship_id,
            unrest=unrest_id,
            remedy=remedy_id,
            book=books[idx % len(books)],
            name=names[idx % len(names)],
            gender=gender,
            helper=helper_cycle[idx % len(helper_cycle)],
            trait=TRAITS[idx % len(TRAITS)],
            seed=idx,
        )
        sample = generate(params)
        if "cozy ship" not in sample.story.lower():
            errors.append(f"missing literal 'cozy ship' in {params}")
        if "reading nook" not in sample.story.lower():
            errors.append(f"missing literal 'reading nook' in {params}")
        if "Once upon a time" not in sample.story:
            errors.append(f"missing fairy-tale opening in {params}")
        if "thought" not in sample.story:
            errors.append(f"missing inner-monologue cue in {params}")
        if len(sample.story.split("\n\n")) < 3:
            errors.append(f"story too flat; expected three paragraphs in {params}")
        if len(sample.story_qa) < 5:
            errors.append(f"too few story QA items in {params}")
        if len(sample.world_qa) < 3:
            errors.append(f"too few world QA items in {params}")
    return errors


def asp_verify() -> int:
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    status = 0
    if clingo_set != python_set:
        status = 1
        print("MISMATCH between ASP and Python valid combinations:")
        if clingo_set - python_set:
            print("  only in ASP:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in Python:", sorted(python_set - clingo_set))
    else:
        print(f"OK: ASP gate matches Python valid_combos() ({len(clingo_set)} combos).")
    errors = verify_generated_stories()
    if errors:
        status = 1
        print("Generated-story verification failed:")
        for err in errors:
            print(f"  - {err}")
    else:
        print(f"OK: generated stories passed structural checks ({len(python_set)} exercised combos).")
    return status


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world: a child in a reading nook checks a worry before letting it become fairy-tale fear."
    )
    ap.add_argument("--nook", choices=sorted(NOOKS))
    ap.add_argument("--ship", choices=sorted(SHIPS))
    ap.add_argument("--unrest", choices=sorted(UNRESTS))
    ap.add_argument("--remedy", choices=sorted(REMEDIES))
    ap.add_argument("--book", choices=sorted(BOOKS))
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--name")
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.nook and args.ship and args.unrest and args.remedy:
        nook = NOOKS[args.nook]
        ship = SHIPS[args.ship]
        unrest = UNRESTS[args.unrest]
        remedy = REMEDIES[args.remedy]
        if not compatible(nook, ship, unrest, remedy):
            raise StoryError(explain_rejection(nook, ship, unrest, remedy))
    combos = [
        combo
        for combo in valid_combos()
        if (args.nook is None or combo[0] == args.nook)
        and (args.ship is None or combo[1] == args.ship)
        and (args.unrest is None or combo[2] == args.unrest)
        and (args.remedy is None or combo[3] == args.remedy)
    ]
    if not combos:
        raise StoryError("(No valid cozy-ship story matches the given options.)")
    nook_id, ship_id, unrest_id, remedy_id = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    helper = args.helper or rng.choice(HELPERS)
    book = args.book or rng.choice(sorted(BOOKS))
    trait = rng.choice(TRAITS)
    return StoryParams(nook_id, ship_id, unrest_id, remedy_id, book, name, gender, helper, trait)


def generate(params: StoryParams) -> StorySample:
    nook = NOOKS[params.nook]
    ship = SHIPS[params.ship]
    unrest = UNRESTS[params.unrest]
    remedy = REMEDIES[params.remedy]
    if not compatible(nook, ship, unrest, remedy):
        raise StoryError(explain_rejection(nook, ship, unrest, remedy))
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa_pairs(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_pairs(world)],
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


def main(argv: Optional[list[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    if args.show_asp:
        print(asp_program("#show valid/4."))
        return 0
    if args.verify:
        return asp_verify()
    if args.asp:
        for combo in asp_valid_combos():
            print(combo)
        return 0

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        seen: set[str] = set()
        attempts = 0
        while len(samples) < args.n and attempts < max(50, args.n * 50):
            seed = base_seed + attempts
            attempts += 1
            params = resolve_params(args, random.Random(seed))
            params.seed = seed
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
    if args.json:
        payload = [sample.to_dict() for sample in samples]
        print(json.dumps(payload[0] if len(payload) == 1 else payload, indent=2, ensure_ascii=False))
        return 0
    for idx, sample in enumerate(samples, 1):
        header = f"--- story {idx} ---" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx != len(samples):
            print()
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except StoryError as exc:
        print(exc)
        sys.exit(2)
