#!/usr/bin/env python3
"""A fairy-tale storyworld about a cozy ship, a reading nook, and inner monologue.

Seed:
    Words: cozy ship
    Setting: reading nook
    Features: Inner Monologue
    Style: Fairy Tale

Internal source tale:
    A child rides in the reading nook of a cozy ship while reading a fairy tale.
    A small physical trouble in the nook makes the child privately imagine a
    much larger enchantment. Instead of obeying the worry, the child studies the
    matching page in the book, checks the real object in front of them, fixes
    it, and proves the voyage is safe by the ending image.
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from storyworlds.results import QAItem, StoryError, StorySample  # noqa: E402


THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict[str, str] = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        if self.kind != "character":
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        if self.type == "girl":
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type == "boy":
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def reflexive(self) -> str:
        if self.type == "girl":
            return "herself"
        if self.type == "boy":
            return "himself"
        return "themself"


@dataclass(frozen=True)
class Ship:
    key: str
    name: str
    captain: str
    nook: str
    window_view: str
    comfort_detail: str
    destination: str
    support_keys: tuple[str, ...]
    tags: tuple[str, ...] = ()


@dataclass(frozen=True)
class Disturbance:
    key: str
    support_key: str
    source_label: str
    source_type: str
    issue_meter: str
    trouble_line: str
    sign_line: str
    worry_thought: str
    worry_body: str
    inspect_line: str
    reveal_line: str
    outcome: str
    lesson: str
    ending_image: str
    tags: tuple[str, ...] = ()


@dataclass(frozen=True)
class Remedy:
    key: str
    support_key: str
    tool_label: str
    action_line: str
    result_line: str
    afterglow_line: str
    tags: tuple[str, ...] = ()


@dataclass(frozen=True)
class Book:
    key: str
    support_key: str
    title: str
    page_detail: str
    whisper_line: str
    closing_line: str
    tags: tuple[str, ...] = ()


@dataclass(frozen=True)
class Event:
    key: str
    subject: str
    detail: str
    consequence: str = ""


@dataclass
class StoryParams:
    ship: str
    disturbance: str
    remedy: str
    book: str
    name: str
    gender: str
    trait: str
    seed: int | None = None


@dataclass(frozen=True)
class Rule:
    name: str
    apply: Callable[["World"], bool]


class World:
    def __init__(
        self,
        params: StoryParams,
        ship: Ship,
        disturbance: Disturbance,
        remedy: Remedy,
        book: Book,
    ) -> None:
        self.params = params
        self.ship = ship
        self.disturbance = disturbance
        self.remedy = remedy
        self.book = book
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.history: list[Event] = []
        self.fired: set[tuple[object, ...]] = set()
        self.fired_names: list[str] = []
        self.facts: dict[str, object] = {
            "support_key": disturbance.support_key,
            "issue_named": False,
            "issue_cleared": False,
        }

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

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
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def record(self, key: str, subject: str, detail: str, consequence: str = "") -> None:
        self.history.append(Event(key, subject, detail, consequence))

    def trace(self) -> str:
        lines = [
            f"params: {self.params}",
            f"support_key: {self.facts['support_key']}",
            f"issue_named: {self.facts['issue_named']}",
            f"issue_cleared: {self.facts['issue_cleared']}",
            f"fired_rules: {', '.join(self.fired_names) if self.fired_names else 'none'}",
        ]
        for entity in self.entities.values():
            meters = {k: v for k, v in entity.meters.items() if v}
            memes = {k: v for k, v in entity.memes.items() if v}
            lines.append(f"  {entity.id} | {entity.kind} | {entity.type} | {entity.label or entity.id}")
            if entity.role:
                lines.append(f"    role={entity.role}")
            if meters:
                lines.append(f"    meters={meters}")
            if memes:
                lines.append(f"    memes={memes}")
        if self.history:
            lines.append("  history:")
            for event in self.history:
                tail = f" -> {event.consequence}" if event.consequence else ""
                lines.append(f"    {event.key}: {event.subject} | {event.detail}{tail}")
        return "\n".join(lines)


def _mark(world: World, name: str, *parts: object) -> bool:
    sig = (name, *parts)
    if sig in world.fired:
        return False
    world.fired.add(sig)
    world.fired_names.append(name)
    return True


def _r_disturbance_surface(world: World) -> bool:
    source = world.get("source")
    ship = world.get("ship")
    book = world.get("book")
    nook = world.get("nook")
    if source.meters[world.disturbance.issue_meter] < THRESHOLD:
        return False
    if not _mark(world, "disturbance_surface", world.disturbance.key):
        return False
    key = world.disturbance.support_key
    if key == "moon":
        book.meters["pages_flutter"] += 1
        ship.meters["silver_path_shiver"] += 1
    elif key == "light":
        book.meters["letters_dim"] += 1
        nook.meters["shadows_stretch"] += 1
    elif key == "shell":
        ship.meters["gentle_sway"] += 1
        book.meters["ribbon_slide"] += 1
    return True


def _r_inner_alarm(world: World) -> bool:
    hero = world.get("hero")
    ship = world.get("ship")
    book = world.get("book")
    nook = world.get("nook")
    signal_present = (
        ship.meters["silver_path_shiver"] >= THRESHOLD
        or ship.meters["gentle_sway"] >= THRESHOLD
        or book.meters["pages_flutter"] >= THRESHOLD
        or book.meters["letters_dim"] >= THRESHOLD
        or book.meters["ribbon_slide"] >= THRESHOLD
        or nook.meters["shadows_stretch"] >= THRESHOLD
    )
    if hero.memes["inner_voice"] < THRESHOLD or not signal_present:
        return False
    if not _mark(world, "inner_alarm", hero.id):
        return False
    hero.memes["worry"] += 1
    hero.memes["wonder"] += 1
    return True


def _r_book_counsel(world: World) -> bool:
    hero = world.get("hero")
    book = world.get("book")
    if hero.memes["worry"] < THRESHOLD or book.meters["opened_to_clue"] < THRESHOLD:
        return False
    if book.attrs.get("support_key") != world.disturbance.support_key:
        return False
    if not _mark(world, "book_counsel", book.id):
        return False
    hero.memes["discernment"] += 1
    hero.memes["worry"] = max(0.0, hero.memes["worry"] - 0.25)
    book.meters["guiding"] += 1
    return True


def _r_true_check(world: World) -> bool:
    hero = world.get("hero")
    source = world.get("source")
    if hero.meters["inspected"] < THRESHOLD or hero.memes["discernment"] < THRESHOLD:
        return False
    if not _mark(world, "true_check", source.id):
        return False
    hero.memes["clarity"] += 1
    source.meters["understood"] += 1
    world.facts["issue_named"] = True
    return True


def _r_fix_lands(world: World) -> bool:
    hero = world.get("hero")
    source = world.get("source")
    if hero.meters["mended"] < THRESHOLD or not world.facts["issue_named"]:
        return False
    if not _mark(world, "fix_lands", source.id):
        return False
    hero.memes["courage"] += 1
    hero.memes["relief"] += 1
    source.meters["steadied"] += 1
    world.facts["issue_cleared"] = True
    return True


def _r_voyage_restored(world: World) -> bool:
    hero = world.get("hero")
    ship = world.get("ship")
    book = world.get("book")
    if not world.facts["issue_cleared"]:
        return False
    if not _mark(world, "voyage_restored", ship.id):
        return False
    ship.meters["steady"] += 1
    ship.meters["cozy"] += 1
    book.meters["readable"] += 1
    hero.memes["peace"] += 1
    return True


RULES = [
    Rule("disturbance_surface", _r_disturbance_surface),
    Rule("inner_alarm", _r_inner_alarm),
    Rule("book_counsel", _r_book_counsel),
    Rule("true_check", _r_true_check),
    Rule("fix_lands", _r_fix_lands),
    Rule("voyage_restored", _r_voyage_restored),
]


def propagate(world: World) -> None:
    changed = True
    while changed:
        changed = False
        for rule in RULES:
            if rule.apply(world):
                changed = True


SHIPS: dict[str, Ship] = {
    "moonpetal": Ship(
        key="moonpetal",
        name="the Moonpetal",
        captain="Captain Elsin",
        nook="the reading nook under a round porthole and a shelf of stitched blankets",
        window_view="Outside, the sea wore a silver road under the moon.",
        comfort_detail="A brass kettle purred near the cushions, and the little mast lantern painted honey on the book spines.",
        destination="Star-Hush Harbor",
        support_keys=("moon", "light"),
        tags=("ship", "reading", "moon", "light"),
    ),
    "hearthfin": Ship(
        key="hearthfin",
        name="the Hearthfin",
        captain="Captain Rowan",
        nook="the reading nook beside the stove bench and the shell-curtained shelf",
        window_view="Outside, the dark water rocked like velvet in a cradle.",
        comfort_detail="Warm quilt squares were tucked into the benches, and a shell bell hung above the narrow map chest.",
        destination="Bellflower Bay",
        support_keys=("light", "shell"),
        tags=("ship", "reading", "light", "shell"),
    ),
    "thistledown": Ship(
        key="thistledown",
        name="the Thistledown",
        captain="Captain Bramble",
        nook="the reading nook tucked by the stern window, with pillows piled like clouds",
        window_view="Outside, the tide breathed softly against the hull.",
        comfort_detail="A basket of ribbon markers rested beside the books, and tiny shells gleamed along the trim.",
        destination="Lantern-Reed Cove",
        support_keys=("moon", "shell"),
        tags=("ship", "reading", "moon", "shell"),
    ),
}


DISTURBANCES: dict[str, Disturbance] = {
    "moon_draft": Disturbance(
        key="moon_draft",
        support_key="moon",
        source_label="the porthole latch",
        source_type="latch",
        issue_meter="ajar",
        trouble_line="the moon-path chart near the captain's chair would not stay smooth enough to read",
        sign_line="A cool breath wandered through the reading nook and made the silver page edges whisper against one another",
        worry_thought="What if moon fairies are unpicking the road on the water",
        worry_body="The thought felt chilly and bright inside the child's chest, like holding a snowflake that would not melt",
        inspect_line="The clue pointed not out to the sea first, but back to the little metal hook beside the round glass",
        reveal_line="There was no fairy hand there after all, only the porthole latch sitting half-open and feeding the draft",
        outcome="moon_path_restored",
        lesson="a worried thought becomes useful when it leads to a true check",
        ending_image="By the time the harbor lights appeared, the moon-road lay flat on the water, and the last page could be read without a single flutter.",
        tags=("moon", "draft", "worry"),
    ),
    "lantern_shadow": Disturbance(
        key="lantern_shadow",
        support_key="light",
        source_label="the lantern shade clip",
        source_type="lantern",
        issue_meter="crooked",
        trouble_line="the chart-room glow kept slipping away from the map whenever the captain tried to read the narrow channel marks",
        sign_line="The reading nook stretched one tall shadow over the book, and the words on the page looked as if they were hiding in dusk",
        worry_thought="What if a shadow witch is nibbling the lantern light",
        worry_body="The thought folded over the child's shoulders like a dark velvet cape",
        inspect_line="The clue asked for a gentle look at the lamp itself, where bright things could go crooked without turning wicked",
        reveal_line="The trouble was small and plain: the lantern shade clip had twisted, and the light was leaning away from the page",
        outcome="lantern_glow_restored",
        lesson="small crooked things can cast large worries until someone straightens them",
        ending_image="Soon the harbor reeds shone amber, the map marks stood clear again, and the reading nook looked golden enough to tuck a story safely inside.",
        tags=("light", "shadow", "worry"),
    ),
    "shell_sway": Disturbance(
        key="shell_sway",
        support_key="shell",
        source_label="the shell-bell cord",
        source_type="cord",
        issue_meter="loose",
        trouble_line="the captain could not keep the ship on the whisper channel because the bell that marked each safe sway had fallen out of rhythm",
        sign_line="The shell bell above the books clicked twice, then not at all, and the ship gave the reading nook one puzzled little lean",
        worry_thought="What if the tide queen has tied the shells into silence",
        worry_body="The thought tugged at the child's middle like a ribbon pulled from both ends",
        inspect_line="The clue did not ask for a grand spell. It asked for listening, and then for fingers brave enough to test one knot",
        reveal_line="The cord had loosened where it met the bell rail, so the shells could not answer the water in a steady pattern",
        outcome="shell_bell_restored",
        lesson="listening closely can be braver than guessing loudly",
        ending_image="When the cove opened ahead, the shell bell answered the tide in tidy little notes, and the cozy ship rocked as gently as a cradle.",
        tags=("shell", "listening", "worry"),
    ),
}


REMEDIES: dict[str, Remedy] = {
    "silver_ribbon": Remedy(
        key="silver_ribbon",
        support_key="moon",
        tool_label="a silver ribbon tie from the bookmark basket",
        action_line="closed the latch, looped the ribbon through the tiny hook, and tested it with one careful tap",
        result_line="At once the wandering draft stopped, and the moon-path chart lay still enough for the captain to follow",
        afterglow_line="The ribbon shone at the glass like a thin piece of captured moonlight.",
        tags=("moon", "repair"),
    ),
    "star_clip": Remedy(
        key="star_clip",
        support_key="light",
        tool_label="a brass star clip from the story lamp tray",
        action_line="set the shade straight again and fastened it with the small brass clip until the lantern sat true",
        result_line="The light gathered itself into one warm pool, and the chart marks returned to their proper places",
        afterglow_line="The clip held like a tiny sun that had decided to stay put.",
        tags=("light", "repair"),
    ),
    "pearl_knot": Remedy(
        key="pearl_knot",
        support_key="shell",
        tool_label="a pearl-colored cord keeper from the sewing tin",
        action_line="retied the cord in a pearl knot and counted the next sway until the bell answered on time",
        result_line="The shells began chiming with the water again, and the captain could feel the safe rhythm under the hull",
        afterglow_line="The knot sat neat and round, like a pale drop of sea foam that had learned patience.",
        tags=("shell", "repair"),
    ),
}


BOOKS: dict[str, Book] = {
    "starlit_ferry": Book(
        key="starlit_ferry",
        support_key="moon",
        title="The Starlit Ferry",
        page_detail="A page showed a ferryman who trusted a silver line only after he checked the clasp that held his sail door shut",
        whisper_line="If I want the true road, I must look for the small thing that lets the draft in",
        closing_line="The child slipped the ribbon marker back into The Starlit Ferry, now knowing that even moonlight likes a well-fastened window.",
        tags=("reading", "moon", "book"),
    ),
    "honey_lantern": Book(
        key="honey_lantern",
        support_key="light",
        title="The Honey Lantern",
        page_detail="A picture showed a tiny keeper turning a lamp straight so the light would stop frightening the corners",
        whisper_line="A shadow can look tall when the lamp is tired, but the answer may be no bigger than a clip",
        closing_line="The child closed The Honey Lantern with a smile, because warm light felt friendlier after it had been set right by hand.",
        tags=("reading", "light", "book"),
    ),
    "listening_bay": Book(
        key="listening_bay",
        support_key="shell",
        title="Listening Bay",
        page_detail="Its picture of a shell bridge said that safe music comes back only when each knot is patient and true",
        whisper_line="The bell is not angry. It is asking me to listen until I hear what slipped loose",
        closing_line="The child laid Listening Bay beside the pillow, glad to know that a patient ear can calm a whole room.",
        tags=("reading", "shell", "book"),
    ),
}


GIRL_NAMES = ["Mira", "Elsie", "Nora", "Lina", "Tansy", "Wren"]
BOY_NAMES = ["Milo", "Theo", "Finn", "Otis", "Alder", "Jules"]
TRAITS = ["careful", "curious", "gentle", "brave", "quiet", "thoughtful"]


def ship_supports(ship: Ship, disturbance: Disturbance) -> bool:
    return disturbance.support_key in ship.support_keys


def remedy_matches(disturbance: Disturbance, remedy: Remedy) -> bool:
    return disturbance.support_key == remedy.support_key


def book_matches(disturbance: Disturbance, book: Book) -> bool:
    return disturbance.support_key == book.support_key


def valid_combo(ship_key: str, disturbance_key: str, remedy_key: str, book_key: str) -> bool:
    if ship_key not in SHIPS or disturbance_key not in DISTURBANCES or remedy_key not in REMEDIES or book_key not in BOOKS:
        return False
    ship = SHIPS[ship_key]
    disturbance = DISTURBANCES[disturbance_key]
    remedy = REMEDIES[remedy_key]
    book = BOOKS[book_key]
    return (
        ship_supports(ship, disturbance)
        and remedy_matches(disturbance, remedy)
        and book_matches(disturbance, book)
    )


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for ship_key in sorted(SHIPS):
        for disturbance_key in sorted(DISTURBANCES):
            for remedy_key in sorted(REMEDIES):
                for book_key in sorted(BOOKS):
                    if valid_combo(ship_key, disturbance_key, remedy_key, book_key):
                        combos.append((ship_key, disturbance_key, remedy_key, book_key))
    return combos


def outcome_of(params: StoryParams) -> str:
    ship = SHIPS[params.ship]
    disturbance = DISTURBANCES[params.disturbance]
    remedy = REMEDIES[params.remedy]
    book = BOOKS[params.book]
    if not ship_supports(ship, disturbance):
        return "ship_mismatch"
    if not remedy_matches(disturbance, remedy):
        return "remedy_mismatch"
    if not book_matches(disturbance, book):
        return "book_mismatch"
    return disturbance.outcome


def explain_rejection(ship: Ship, disturbance: Disturbance, remedy: Remedy, book: Book) -> str:
    if not ship_supports(ship, disturbance):
        return (
            f"No story: {ship.name} does not physically support the "
            f"{disturbance.support_key} disturbance needed for {disturbance.key}."
        )
    if not remedy_matches(disturbance, remedy):
        return (
            f"No story: {remedy.tool_label} fixes a {remedy.support_key} problem, "
            f"but {disturbance.key} is a {disturbance.support_key} disturbance."
        )
    if not book_matches(disturbance, book):
        return (
            f"No story: {book.title} teaches a {book.support_key} clue, "
            f"but {disturbance.key} needs a {disturbance.support_key} clue."
        )
    return "No story: this setup falls outside the cozy-ship world rules."


def build_world(params: StoryParams) -> World:
    ship = SHIPS[params.ship]
    disturbance = DISTURBANCES[params.disturbance]
    remedy = REMEDIES[params.remedy]
    book = BOOKS[params.book]
    if not valid_combo(params.ship, params.disturbance, params.remedy, params.book):
        raise StoryError(explain_rejection(ship, disturbance, remedy, book))

    world = World(params, ship, disturbance, remedy, book)
    hero = world.add(Entity(
        id="hero",
        kind="character",
        type=params.gender,
        label=params.name,
        role="child",
        traits=[params.trait],
    ))
    captain = world.add(Entity(
        id="captain",
        kind="character",
        type="captain",
        label=ship.captain,
        role="captain",
    ))
    ship_entity = world.add(Entity(
        id="ship",
        kind="thing",
        type="ship",
        label=ship.name,
        role="vessel",
    ))
    nook = world.add(Entity(
        id="nook",
        kind="place",
        type="reading_nook",
        label="the reading nook",
        role="setting",
    ))
    book_entity = world.add(Entity(
        id="book",
        kind="thing",
        type="book",
        label=book.title,
        role="book",
        attrs={"support_key": book.support_key},
    ))
    source = world.add(Entity(
        id="source",
        kind="thing",
        type=disturbance.source_type,
        label=disturbance.source_label,
        role="source",
    ))
    tool = world.add(Entity(
        id="tool",
        kind="thing",
        type="tool",
        label=remedy.tool_label,
        role="tool",
    ))

    hero.memes["wonder"] += 1
    ship_entity.meters["cozy"] += 1
    source.meters[disturbance.issue_meter] += 1
    world.facts.update(
        hero_name=params.name,
        hero_trait=params.trait,
        captain_name=ship.captain,
        destination=ship.destination,
        source_label=disturbance.source_label,
        tool_label=remedy.tool_label,
        book_title=book.title,
    )
    propagate(world)
    return world


def _sent_case(text: str) -> str:
    if not text:
        return text
    return text[0].upper() + text[1:]


def _lower_first(text: str) -> str:
    if not text:
        return text
    return text[0].lower() + text[1:]


def _ensure_sentence(text: str) -> str:
    text = text.strip()
    if not text:
        return text
    if text[-1] in ".!?":
        return text
    return f"{text}."


def introduce(world: World) -> None:
    hero = world.get("hero")
    ship = world.ship
    book = world.book
    world.say(
        f"Once upon a hush-blue evening, {hero.label}, a {hero.traits[0]} little "
        f"{hero.type}, curled up in the reading nook aboard {ship.name}, a cozy ship "
        f"bound for {ship.destination}."
    )
    world.say(ship.window_view)
    world.say(
        f"{ship.comfort_detail} In {hero.pronoun('possessive')} lap lay {book.title}, "
        f"open to a page where fairy helpers always checked the world before they trusted a fear."
    )
    world.record("opening", hero.label, f"settled into {ship.nook}", f"reading {book.title}")


def raise_tension(world: World) -> None:
    captain = world.get("captain")
    disturbance = world.disturbance
    world.say(
        f"But before long, {disturbance.trouble_line}. {disturbance.sign_line}."
    )
    world.say(
        f"\"Stay watchful, little reader,\" said {captain.label}. "
        f"\"When a ship whispers, it usually whispers about something real.\""
    )
    world.record("trouble", captain.label, disturbance.trouble_line, disturbance.sign_line)


def inner_monologue(world: World) -> None:
    hero = world.get("hero")
    hero.memes["inner_voice"] += 1
    propagate(world)
    disturbance = world.disturbance
    world.say(
        f"\"{disturbance.worry_thought}?\" {hero.label} thought. {disturbance.worry_body}."
    )
    world.say(
        f"For a blink, {hero.pronoun()} imagined a fairy mischief far bigger than the nook itself."
    )
    world.record("inner_monologue", hero.label, disturbance.worry_thought, "worry rose before the child checked the clue")


def turning_point(world: World) -> None:
    hero = world.get("hero")
    book = world.book
    remedy = world.remedy
    disturbance = world.disturbance
    world.get("book").meters["opened_to_clue"] += 1
    propagate(world)
    if hero.memes["discernment"] < THRESHOLD:
        raise StoryError("No story: the book never grounded the inner monologue in a real clue.")
    world.say(
        f"{hero.label} laid a finger on the page. {book.page_detail}."
    )
    world.say(
        f"\"{book.whisper_line},\" {hero.label} told {hero.reflexive()}."
    )
    world.say(_ensure_sentence(disturbance.inspect_line))
    hero.meters["inspected"] += 1
    propagate(world)
    if not world.facts["issue_named"]:
        raise StoryError("No story: the child inspected the nook but never identified the real cause.")
    world.say(_ensure_sentence(disturbance.reveal_line))
    world.say(
        f"Then {hero.label} took {remedy.tool_label} and {remedy.action_line}."
    )
    hero.meters["mended"] += 1
    propagate(world)
    if not world.facts["issue_cleared"]:
        raise StoryError("No story: the repair never settled the disturbance.")
    world.record("turn", hero.label, disturbance.inspect_line, remedy.action_line)


def resolution(world: World) -> None:
    captain = world.get("captain")
    hero = world.get("hero")
    disturbance = world.disturbance
    remedy = world.remedy
    book = world.book
    world.say(_ensure_sentence(remedy.result_line))
    world.say(
        f"{remedy.afterglow_line} {captain.label} smiled and guided {world.ship.name} onward at once."
    )
    world.say(
        f"When {hero.label} settled back into the reading nook, {_lower_first(book.closing_line)} "
        f"{_sent_case(disturbance.lesson)}."
    )
    world.say(disturbance.ending_image)
    world.record("resolution", captain.label, remedy.result_line, disturbance.ending_image)


def tell(params: StoryParams) -> World:
    world = build_world(params)
    introduce(world)
    world.para()
    raise_tension(world)
    inner_monologue(world)
    world.para()
    turning_point(world)
    resolution(world)
    return world


KNOWLEDGE: dict[str, list[tuple[str, str]]] = {
    "ship": [
        (
            "What is a reading nook on a ship?",
            "It is a small cozy place with books and cushions where someone can rest and think. In this world, it also becomes the best place to notice a true clue.",
        )
    ],
    "moon": [
        (
            "Why can moonlight become a clue in a fairy tale?",
            "Moonlight shows where movement or stillness changes. A silver line on water or glass can reveal that a real object has shifted.",
        )
    ],
    "light": [
        (
            "Why do lanterns matter in gentle sea stories?",
            "Lanterns help people see small but important things. If the light goes crooked, a child can feel scared until someone sets it right again.",
        )
    ],
    "shell": [
        (
            "Why would a shell bell help on a ship?",
            "A shell bell can keep rhythm with the water. In a story, that rhythm helps the crew notice when something tiny has come loose.",
        )
    ],
    "worry": [
        (
            "Can a worried thought ever help?",
            "Yes, if the child does not obey it blindly. The worry can become a reminder to check what is really happening.",
        )
    ],
    "repair": [
        (
            "Why is a small repair important in a fairy tale?",
            "A tiny repair can change the whole feeling of a room or a voyage. It proves that brave care is often stronger than grand guessing.",
        )
    ],
}
KNOWLEDGE_ORDER = ["ship", "moon", "light", "shell", "worry", "repair"]


def generation_prompts(world: World) -> list[str]:
    hero = world.get("hero")
    disturbance = world.disturbance
    remedy = world.remedy
    book = world.book
    return [
        'Write a TinyStories-style fairy tale that includes the words "cozy ship" and takes place in a reading nook.',
        f"Give the child visible inner monologue: {hero.label} privately worries that {disturbance.worry_thought.lower()}, then checks a real clue in {book.title}.",
        f"Resolve the story when {hero.label} uses {remedy.tool_label} and proves the fear was smaller and more physical than it first seemed.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    hero = world.get("hero")
    captain = world.get("captain")
    disturbance = world.disturbance
    remedy = world.remedy
    book = world.book
    ship = world.ship
    return [
        (
            "Who is the story about?",
            f"It is about {hero.label}, a {hero.traits[0]} little {hero.type} riding aboard {ship.name}. The child starts in the reading nook with a book and ends by helping the voyage.",
        ),
        (
            "Where does the story happen?",
            f"It happens on {ship.name}, especially in the reading nook. That small place matters because the clue, the worry, and the repair all begin there.",
        ),
        (
            f"What did {hero.label} think might be happening?",
            f"{hero.label} thought, \"{disturbance.worry_thought}?\" That inner monologue made the trouble feel magical at first, even though the real cause was physical.",
        ),
        (
            "What clue helped the child stop guessing?",
            f"{book.title} helped by showing a matching page: {book.page_detail.lower()}. Because the page matched the trouble, the child looked at the right object instead of chasing a bigger fear.",
        ),
        (
            "What was the real problem in the nook?",
            f"The real problem was {disturbance.source_label}. {_ensure_sentence(disturbance.reveal_line)} That concrete cause is what turned the worry into a solvable task.",
        ),
        (
            "How was the ship helped?",
            f"{hero.label} used {remedy.tool_label} and {remedy.action_line}. {_ensure_sentence(remedy.result_line)} That let {captain.label} guide the ship onward again.",
        ),
        (
            "How did the ending prove something had changed?",
            f"The ending image showed the change clearly: {disturbance.ending_image} The same reading nook that felt uneasy at first had become calm and readable again.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"ship"} | set(world.disturbance.tags) | set(world.remedy.tags) | set(world.book.tags)
    tags.add("repair")
    tags.add("worry")
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
    lines.append("== (2) Story-grounded questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
        world=world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(sample.world.trace())
    if qa:
        print()
        print(format_qa(sample))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Story world: a fairy-tale cozy ship, a reading nook, and an inner monologue grounded by a real clue."
    )
    parser.add_argument("--ship", choices=sorted(SHIPS))
    parser.add_argument("--disturbance", choices=sorted(DISTURBANCES))
    parser.add_argument("--remedy", choices=sorted(REMEDIES))
    parser.add_argument("--book", choices=sorted(BOOKS))
    parser.add_argument("--name")
    parser.add_argument("--gender", choices=["girl", "boy"])
    parser.add_argument("--trait", choices=TRAITS)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--all", action="store_true", help="render every valid combination")
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true", help="list valid combinations from the ASP gate")
    parser.add_argument("--verify", action="store_true", help="compare Python and ASP reasoning and smoke-test generated stories")
    parser.add_argument("--show-asp", action="store_true", help="print the ASP facts and rules")
    return parser


def _pick_name(rng: random.Random, gender: str) -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    return rng.choice(pool)


def resolve_params(args: argparse.Namespace, rng: random.Random, index: int = 0) -> StoryParams:
    combos = [
        combo for combo in valid_combos()
        if (args.ship is None or combo[0] == args.ship)
        and (args.disturbance is None or combo[1] == args.disturbance)
        and (args.remedy is None or combo[2] == args.remedy)
        and (args.book is None or combo[3] == args.book)
    ]
    if not combos:
        ship = SHIPS[args.ship or "moonpetal"]
        disturbance = DISTURBANCES[args.disturbance or "moon_draft"]
        remedy = REMEDIES[args.remedy or "silver_ribbon"]
        book = BOOKS[args.book or "starlit_ferry"]
        raise StoryError(explain_rejection(ship, disturbance, remedy, book))

    ship_key, disturbance_key, remedy_key, book_key = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    return StoryParams(
        ship=ship_key,
        disturbance=disturbance_key,
        remedy=remedy_key,
        book=book_key,
        name=args.name or _pick_name(rng, gender),
        gender=gender,
        trait=args.trait or rng.choice(TRAITS),
        seed=(args.seed or 1000) + index,
    )


ASP_RULES = r"""
valid(S,D,R,B) :-
    ship(S), disturbance(D), remedy(R), book(B),
    ship_support(S,K), disturbance_key(D,K), remedy_key(R,K), book_key(B,K).

outcome(ship_mismatch) :-
    chosen_ship(S), chosen_disturbance(D),
    disturbance_key(D,K), not ship_support(S,K).

outcome(remedy_mismatch) :-
    chosen_ship(S), chosen_disturbance(D), chosen_remedy(R),
    disturbance_key(D,K), ship_support(S,K), remedy_key(R,RK), RK != K.

outcome(book_mismatch) :-
    chosen_ship(S), chosen_disturbance(D), chosen_remedy(R), chosen_book(B),
    disturbance_key(D,K), ship_support(S,K), remedy_key(R,K), book_key(B,BK), BK != K.

outcome(O) :-
    chosen_ship(S), chosen_disturbance(D), chosen_remedy(R), chosen_book(B),
    valid(S,D,R,B), disturbance_outcome(D,O).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp

    lines: list[str] = []
    for ship in SHIPS.values():
        lines.append(asp.fact("ship", ship.key))
        for key in ship.support_keys:
            lines.append(asp.fact("ship_support", ship.key, key))
    for disturbance in DISTURBANCES.values():
        lines.append(asp.fact("disturbance", disturbance.key))
        lines.append(asp.fact("disturbance_key", disturbance.key, disturbance.support_key))
        lines.append(asp.fact("disturbance_outcome", disturbance.key, disturbance.outcome))
    for remedy in REMEDIES.values():
        lines.append(asp.fact("remedy", remedy.key))
        lines.append(asp.fact("remedy_key", remedy.key, remedy.support_key))
    for book in BOOKS.values():
        lines.append(asp.fact("book", book.key))
        lines.append(asp.fact("book_key", book.key, book.support_key))
    return "\n".join(lines)


def asp_program(extra: str = "", show: str = "#show valid/4.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple[str, str, str, str]]:
    import storyworlds.asp as asp

    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import storyworlds.asp as asp

    chosen = "\n".join([
        asp.fact("chosen_ship", params.ship),
        asp.fact("chosen_disturbance", params.disturbance),
        asp.fact("chosen_remedy", params.remedy),
        asp.fact("chosen_book", params.book),
    ])
    model = asp.one_model(asp_program(extra=chosen, show="#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "no_outcome"


CURATED: list[StoryParams] = [
    StoryParams("moonpetal", "moon_draft", "silver_ribbon", "starlit_ferry", "Mira", "girl", "careful"),
    StoryParams("moonpetal", "lantern_shadow", "star_clip", "honey_lantern", "Theo", "boy", "thoughtful"),
    StoryParams("hearthfin", "lantern_shadow", "star_clip", "honey_lantern", "Elsie", "girl", "gentle"),
    StoryParams("hearthfin", "shell_sway", "pearl_knot", "listening_bay", "Milo", "boy", "quiet"),
    StoryParams("thistledown", "moon_draft", "silver_ribbon", "starlit_ferry", "Nora", "girl", "curious"),
    StoryParams("thistledown", "shell_sway", "pearl_knot", "listening_bay", "Otis", "boy", "brave"),
]


def _story_checks(sample: StorySample) -> list[str]:
    problems: list[str] = []
    text = sample.story
    if "cozy ship" not in text:
        problems.append("story text lost required seed words")
    if "reading nook" not in text:
        problems.append("story text lost required setting phrase")
    if text.count("\n\n") < 2:
        problems.append("story is missing a clear beginning, turn, and ending paragraph shape")
    if "thought" not in text:
        problems.append("story is missing visible inner monologue")
    if "{" in text or "}" in text:
        problems.append("story leaked unresolved template markers")
    if len(sample.prompts) < 3 or len(sample.story_qa) < 6 or len(sample.world_qa) < 3:
        problems.append("prompt or QA sets are too thin")
    if "No story:" in text:
        problems.append("story leaked a failure string into prose")
    if "_" in text:
        problems.append("story leaked an internal id into prose")
    return problems


def asp_verify() -> int:
    rc = 0
    py_valid = set(valid_combos())
    asp_valid = set(asp_valid_combos())
    if py_valid == asp_valid:
        print(f"OK: clingo gate matches valid_combos() ({len(py_valid)} combos).")
    else:
        rc = 1
        print("ASP/Python mismatch in valid combos:")
        if py_valid - asp_valid:
            print("  only in Python:", sorted(py_valid - asp_valid))
        if asp_valid - py_valid:
            print("  only in ASP:", sorted(asp_valid - py_valid))

    cases: list[StoryParams] = list(CURATED)
    cases.extend([
        StoryParams("hearthfin", "moon_draft", "silver_ribbon", "starlit_ferry", "Mira", "girl", "careful"),
        StoryParams("moonpetal", "shell_sway", "pearl_knot", "listening_bay", "Theo", "boy", "quiet"),
        StoryParams("thistledown", "moon_draft", "star_clip", "starlit_ferry", "Nora", "girl", "gentle"),
        StoryParams("moonpetal", "lantern_shadow", "star_clip", "listening_bay", "Milo", "boy", "brave"),
    ])
    empty = build_parser().parse_args([])
    for seed in range(60):
        params = resolve_params(empty, random.Random(seed), index=seed)
        params.seed = seed
        cases.append(params)

    mismatches = [params for params in cases if asp_outcome(params) != outcome_of(params)]
    if not mismatches:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"Outcome mismatch on {len(mismatches)}/{len(cases)} scenarios.")
        for params in mismatches[:5]:
            print(" ", params, asp_outcome(params), outcome_of(params))

    invalids = cases[len(CURATED):len(CURATED) + 4]
    for params in invalids:
        if outcome_of(params) == "ship_mismatch":
            pass
    for params in invalids:
        if outcome_of(params) == DISTURBANCES[params.disturbance].outcome:
            continue
        try:
            generate(params)
        except StoryError:
            continue
        rc = 1
        print("Expected StoryError for invalid params but generation succeeded:", params)

    issues: list[str] = []
    for params in CURATED:
        sample = generate(params)
        issues.extend(f"{params.name}: {problem}" for problem in _story_checks(sample))
    if not issues:
        print(f"OK: curated stories passed shape and QA checks ({len(CURATED)} samples).")
    else:
        rc = 1
        print("QUALITY CHECK FAILURES:")
        for issue in issues:
            print(" ", issue)
    return rc


def _sample_all(args: argparse.Namespace) -> list[StorySample]:
    base_seed = args.seed or 7
    samples: list[StorySample] = []
    for index, combo in enumerate(valid_combos(), start=1):
        gender = args.gender or ("girl" if index % 2 else "boy")
        params = StoryParams(
            ship=combo[0],
            disturbance=combo[1],
            remedy=combo[2],
            book=combo[3],
            name=args.name or _pick_name(random.Random(base_seed + index), gender),
            gender=gender,
            trait=args.trait or TRAITS[(index - 1) % len(TRAITS)],
            seed=base_seed + index,
        )
        samples.append(generate(params))
    return samples


def main() -> int:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return 0
    if args.verify:
        return asp_verify()
    if args.asp:
        for combo in asp_valid_combos():
            print("\t".join(combo))
        return 0

    base_seed = args.seed if args.seed is not None else random.randrange(1, 1_000_000)
    try:
        if args.all:
            samples = _sample_all(args)
        else:
            samples = []
            seen: set[str] = set()
            i = 0
            while len(samples) < args.n and i < max(args.n * 80, 80):
                params = resolve_params(args, random.Random(base_seed + i), index=i)
                sample = generate(params)
                i += 1
                if sample.story in seen:
                    continue
                seen.add(sample.story)
                samples.append(sample)
            if len(samples) < args.n:
                raise StoryError("Could not generate enough unique stories with these constraints.")

        if args.json:
            if len(samples) == 1:
                print(samples[0].to_json())
            else:
                print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
            return 0

        for idx, sample in enumerate(samples):
            header = ""
            if args.all:
                p = sample.params
                header = (
                    f"### ship={p.ship} disturbance={p.disturbance} "
                    f"remedy={p.remedy} book={p.book}"
                )
            elif len(samples) > 1:
                header = f"### variant {idx + 1}"
            emit(sample, trace=args.trace, qa=args.qa, header=header)
            if idx < len(samples) - 1:
                print("\n" + "=" * 72 + "\n")
        return 0
    except StoryError as err:
        print(err)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
