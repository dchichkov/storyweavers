#!/usr/bin/env python3
"""A fairy-tale storyworld about a cozy ship moored in a reading nook.

Seed:
    Words: cozy ship
    Setting: reading nook
    Features: Inner Monologue
    Style: Fairy Tale

Internal source tale:
    A child curls into a little ship built inside a reading nook and begins a
    fairy book about keeping a tiny harbor true. A small real-world wobble in
    the nook feels, through the child's inner monologue, like a spell trying to
    unmoor the ship. The child pauses, names the fear, investigates with a kind
    household helper, fixes the physical cause, and finishes the evening with a
    clearer heart and a visibly steadier harbor.
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from storyworlds.results import QAItem, StoryError, StorySample


@dataclass(frozen=True)
class Nook:
    key: str
    label: str
    scene: str
    ending_image: str
    supports: tuple[str, ...]


@dataclass(frozen=True)
class Ship:
    key: str
    label: str
    build: str
    sail: str
    berth_image: str
    supports: tuple[str, ...]


@dataclass(frozen=True)
class Trouble:
    key: str
    kind: str
    label: str
    source: str
    omen: str
    thought: str
    inspect: str
    reveal: str
    risk: str
    ending_change: str


@dataclass(frozen=True)
class Remedy:
    key: str
    kind: str
    label: str
    helper_action: str
    action: str
    result: str
    image: str


@dataclass(frozen=True)
class Book:
    key: str
    title: str
    quest: str
    page_image: str
    lesson: str
    echoes: tuple[str, ...]


@dataclass
class StoryParams:
    nook: str
    ship: str
    trouble: str
    remedy: str
    book: str
    hero: str
    gender: str
    helper: str
    trait: str
    seed: int | None = None


@dataclass
class Entity:
    key: str
    kind: str
    label: str
    location: str
    tags: dict[str, str] = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def set_meter(self, name: str, value: float) -> None:
        self.meters[name] = round(value, 2)

    def add_meter(self, name: str, amount: float) -> None:
        self.meters[name] = round(self.meters.get(name, 0.0) + amount, 2)

    def add_meme(self, name: str, amount: float) -> None:
        self.memes[name] = round(self.memes.get(name, 0.0) + amount, 2)


@dataclass
class Event:
    key: str
    detail: str
    effect: str = ""


@dataclass
class World:
    params: StoryParams
    nook: Nook
    ship: Ship
    trouble: Trouble
    remedy: Remedy
    book: Book
    entities: dict[str, Entity] = field(default_factory=dict)
    history: list[Event] = field(default_factory=list)
    facts: dict[str, str] = field(default_factory=dict)
    fired: list[str] = field(default_factory=list)

    def event(self, key: str, detail: str, effect: str = "") -> None:
        self.history.append(Event(key=key, detail=detail, effect=effect))
        self.fired.append(key)

    def trace(self) -> str:
        rows = ["--- world model state ---", f"params={self.params}"]
        for key, ent in self.entities.items():
            rows.append(
                f"{key}: kind={ent.kind} label={ent.label} location={ent.location} "
                f"tags={dict(sorted(ent.tags.items()))} "
                f"meters={dict(sorted(ent.meters.items()))} "
                f"memes={dict(sorted(ent.memes.items()))}"
            )
        rows.append(f"facts={json.dumps(self.facts, sort_keys=True)}")
        rows.append(f"fired={self.fired}")
        rows.append("history:")
        for item in self.history:
            rows.append(
                f"  {item.key}: {item.detail}" + (f" -> {item.effect}" if item.effect else "")
            )
        return "\n".join(rows)


NOOKS = {
    "window_berth": Nook(
        key="window_berth",
        label="the window-berth reading nook",
        scene="a crescent bench under the window, ringed with quilts, candle-color pillows, and a low basket of books",
        ending_image="the window-berth looked like a harbor painted in warm milk and gold",
        supports=("draft", "glimmer"),
    ),
    "lantern_alcove": Nook(
        key="lantern_alcove",
        label="the lantern-alcove reading nook",
        scene="a curtained corner with a lamp shelf, deep cushions, and a wool rug soft as moss",
        ending_image="the lantern-alcove glowed like a pocket kingdom where boats could sleep",
        supports=("glimmer", "tilt"),
    ),
    "stair_cove": Nook(
        key="stair_cove",
        label="the stair-cove reading nook",
        scene="a tucked space beneath the stairs, with braided blankets and shelves that leaned close like friendly cliffs",
        ending_image="the stair-cove held its hush like a snug harbor inside a hill",
        supports=("draft", "tilt"),
    ),
}


SHIPS = {
    "quilt_ferry": Ship(
        key="quilt_ferry",
        label="quilt ferry",
        build="folded quilts over a toy chest hull",
        sail="a pale sail sewn from an old sleeve",
        berth_image="the quilt ferry rested with its bow tucked into the cushions",
        supports=("draft", "tilt"),
    ),
    "pillow_moonboat": Ship(
        key="pillow_moonboat",
        label="pillow moonboat",
        build="round pillows laced into a moon-curved hull",
        sail="a silver napkin sail with a star button at the mast",
        berth_image="the pillow moonboat lay curved and dreamy beside the book basket",
        supports=("glimmer", "tilt"),
    ),
    "basket_skiff": Ship(
        key="basket_skiff",
        label="basket skiff",
        build="a wicker basket lined with blankets and ribbon rails",
        sail="a ribbon sail that trembled at the smallest breath",
        berth_image="the basket skiff sat as neatly as a toy boat on story-water",
        supports=("draft", "glimmer"),
    ),
}


TROUBLES = {
    "whispering_draft": Trouble(
        key="whispering_draft",
        kind="draft",
        label="a whispering draft",
        source="window",
        omen="A cool thread of air slipped through the nook and made the little sail shiver against the pages.",
        thought="If the wind has found {title}, perhaps it means to tug my cozy ship away before I learn how the harbor is saved.",
        inspect="The child held still, then reached toward the window and felt a narrow ribbon of cold at the latch.",
        reveal="The window was open just a finger-width, enough for the air to tease the fort and the book.",
        risk="the pages could keep fluttering and the harbor-feeling of the nook could break apart",
        ending_change="the sail stopped trembling",
    ),
    "wandering_glimmer": Trouble(
        key="wandering_glimmer",
        kind="glimmer",
        label="a wandering glimmer",
        source="lantern",
        omen="The lamplight slid across the mast and made a bright bead wander over the wall like a wake that would not rest.",
        thought="What if a wake-spirit from {quest} is circling my cozy ship to see whether I can keep my courage lit?",
        inspect="The child followed the moving gleam and saw the glass charm hanging from the lamp hook swinging to and fro.",
        reveal="A hanging glass charm had begun to sway, so the lamp kept sending the light skimming across the nook.",
        risk="the shifting gleam could make the room feel watchful instead of gentle",
        ending_change="the lamplight became round and still",
    ),
    "sleepy_tilt": Trouble(
        key="sleepy_tilt",
        kind="tilt",
        label="a sleepy tilt",
        source="mast",
        omen="The ship leaned to one side, and the open book started inching across the blanket like a slow little passenger.",
        thought="If my cozy ship keeps bowing like this, perhaps some drowsy giant under the quilts is trying to roll us out of the harbor of stories.",
        inspect="The child lifted the blanket edge and found one mast cushion slumped halfway off the chest beneath it.",
        reveal="A support cushion had slipped, so the fort was tipping instead of lying level.",
        risk="the book could slide down and the child could stop trusting the ship to hold still",
        ending_change="the hull stood level again",
    ),
}


REMEDIES = {
    "latch_the_curtain": Remedy(
        key="latch_the_curtain",
        kind="draft",
        label="a curtain tie at the latch",
        helper_action="The helper kept one hand on the open book so nothing precious could skitter away.",
        action="looped the curtain tie around the latch and pressed the window snug",
        result="The pages softened back onto the child's lap, and the nook breathed warm again.",
        image="The tied curtain hung like a quiet harbor flag that had finished flapping.",
    ),
    "still_the_charm": Remedy(
        key="still_the_charm",
        kind="glimmer",
        label="a quieted lamp charm",
        helper_action="The helper raised the lamp a little higher while the child reached slowly with steady fingers.",
        action="caught the swinging charm and wrapped its string once around the lamp hook",
        result="The roaming bead of light disappeared, and the walls kept one calm circle of gold.",
        image="The lamp stood above the berth like a moon that had chosen not to wander.",
    ),
    "square_the_cushion": Remedy(
        key="square_the_cushion",
        kind="tilt",
        label="a squared mast cushion",
        helper_action="The helper held the ship frame steady so the child could work without hurrying.",
        action="nudged the sleepy cushion back beneath the mast corner and patted it flat",
        result="The book stopped creeping, and the ship felt trustworthy under every blanket fold.",
        image="The mast corner sat plump and true, as if it had remembered its promise.",
    ),
}


BOOKS = {
    "harbor_of_sparrows": Book(
        key="harbor_of_sparrows",
        title="The Harbor of Sparrows",
        quest="a small captain guiding sparrow boats home through evening air",
        page_image="sparrow-wing boats were settling onto a painted harbor where every rope had to be noticed",
        lesson="Tiny signs matter because a safe harbor is built from patient noticing.",
        echoes=("draft", "glimmer"),
    ),
    "moon_mast_queen": Book(
        key="moon_mast_queen",
        title="The Moon-Mast Queen",
        quest="a queen keeping one silver mast bright so lost sailors would not despair",
        page_image="a silver mast stood over dark water while one queen watched for the smallest change in light",
        lesson="Gentle bravery is often the work of keeping one clear light steady.",
        echoes=("glimmer",),
    ),
    "pillow_bay_map": Book(
        key="pillow_bay_map",
        title="The Map of Pillow Bay",
        quest="a map-reader learning which soft island can hold fast in a turning tide",
        page_image="a child reader was studying a map whose safest path only appeared when the boat lay level",
        lesson="The next kind step becomes visible when the heart and the boat grow steady.",
        echoes=("draft", "tilt"),
    ),
}


HEROES = {
    "girl": ("Mira", "Nell", "Ivy", "June", "Tessa"),
    "boy": ("Theo", "Milo", "Finn", "Owen", "Jasper"),
}

HELPERS = ("mother", "father", "grandmother", "grandfather", "aunt")
TRAITS = ("thoughtful", "soft-voiced", "careful", "dreamy", "patient")


def pronouns(gender: str) -> tuple[str, str, str]:
    if gender == "boy":
        return ("he", "his", "him")
    return ("she", "her", "her")


def titled(word: str) -> str:
    return word.replace("_", " ").title()


def lower_first(text: str) -> str:
    if not text:
        return text
    return text[0].lower() + text[1:]


def sentence_case(text: str) -> str:
    if not text:
        return text
    return text[0].upper() + text[1:]


def ensure_period(text: str) -> str:
    return text if text.endswith(".") else text + "."


def valid_combo(nook: str, ship: str, trouble: str, remedy: str, book: str) -> bool:
    if nook not in NOOKS or ship not in SHIPS or trouble not in TROUBLES or remedy not in REMEDIES or book not in BOOKS:
        return False
    trouble_kind = TROUBLES[trouble].kind
    return (
        trouble_kind in NOOKS[nook].supports
        and trouble_kind in SHIPS[ship].supports
        and trouble_kind in BOOKS[book].echoes
        and REMEDIES[remedy].kind == trouble_kind
    )


def explain_rejection(nook: str, ship: str, trouble: str, remedy: str, book: str) -> str:
    if nook not in NOOKS:
        return f"No story: unknown nook {nook!r}."
    if ship not in SHIPS:
        return f"No story: unknown ship {ship!r}."
    if trouble not in TROUBLES:
        return f"No story: unknown trouble {trouble!r}."
    if remedy not in REMEDIES:
        return f"No story: unknown remedy {remedy!r}."
    if book not in BOOKS:
        return f"No story: unknown book {book!r}."
    trouble_kind = TROUBLES[trouble].kind
    if trouble_kind not in NOOKS[nook].supports:
        return f"No story: {NOOKS[nook].label} cannot naturally produce {TROUBLES[trouble].label}."
    if trouble_kind not in SHIPS[ship].supports:
        return f"No story: the {SHIPS[ship].label} does not show {TROUBLES[trouble].label} clearly."
    if trouble_kind not in BOOKS[book].echoes:
        return f"No story: {BOOKS[book].title} does not fit the mood of {TROUBLES[trouble].label}."
    if REMEDIES[remedy].kind != trouble_kind:
        return f"No story: {REMEDIES[remedy].label} does not solve {TROUBLES[trouble].label}."
    return "No story: the requested cozy-ship tale is not reasonable."


def valid_combos() -> list[tuple[str, str, str, str, str]]:
    rows: list[tuple[str, str, str, str, str]] = []
    for nook in NOOKS:
        for ship in SHIPS:
            for trouble in TROUBLES:
                for remedy in REMEDIES:
                    for book in BOOKS:
                        if valid_combo(nook, ship, trouble, remedy, book):
                            rows.append((nook, ship, trouble, remedy, book))
    return rows


def build_world(params: StoryParams) -> World:
    if not valid_combo(params.nook, params.ship, params.trouble, params.remedy, params.book):
        raise StoryError(
            explain_rejection(params.nook, params.ship, params.trouble, params.remedy, params.book)
        )
    world = World(
        params=params,
        nook=NOOKS[params.nook],
        ship=SHIPS[params.ship],
        trouble=TROUBLES[params.trouble],
        remedy=REMEDIES[params.remedy],
        book=BOOKS[params.book],
    )
    world.entities["hero"] = Entity(
        key="hero",
        kind="character",
        label=params.hero,
        location=world.nook.label,
        tags={"gender": params.gender, "trait": params.trait, "role": "reader captain"},
        meters={"breath": 1.0, "steadiness": 1.0},
        memes={"coziness": 1.5, "curiosity": 1.0, "wonder": 0.9},
    )
    world.entities["helper"] = Entity(
        key="helper",
        kind="character",
        label=titled(params.helper),
        location=world.nook.label,
        tags={"role": "household helper"},
        memes={"kindness": 1.4, "patience": 1.2},
    )
    world.entities["nook"] = Entity(
        key="nook",
        kind="place",
        label=world.nook.label,
        location=world.nook.label,
        tags={"setting": "reading nook"},
        meters={"warmth": 1.4, "stillness": 1.2},
        memes={"safety": 1.3},
    )
    world.entities["ship"] = Entity(
        key="ship",
        kind="object",
        label=world.ship.label,
        location=world.nook.label,
        tags={"state": "moored"},
        meters={"balance": 1.1, "motion": 0.0, "glow": 1.0},
        memes={"coziness": 1.4, "pretend_sea": 1.0},
    )
    world.entities["book"] = Entity(
        key="book",
        kind="object",
        label=world.book.title,
        location=world.nook.label,
        tags={"state": "open"},
        meters={"settled_pages": 1.1, "clarity": 1.0},
        memes={"story_magic": 1.3},
    )
    world.entities["window"] = Entity(
        key="window",
        kind="object",
        label="the window latch",
        location=world.nook.label,
        tags={"state": "closed"},
        meters={"draft": 0.0},
    )
    world.entities["lantern"] = Entity(
        key="lantern",
        kind="object",
        label="the reading lamp",
        location=world.nook.label,
        tags={"state": "steady"},
        meters={"glimmer": 0.0},
    )
    world.entities["mast"] = Entity(
        key="mast",
        kind="object",
        label="the mast corner",
        location=world.nook.label,
        tags={"state": "square"},
        meters={"tilt": 0.0},
    )
    world.facts["setting"] = "reading nook"
    world.facts["seed_words"] = "cozy ship"
    world.facts["style"] = "fairy tale"
    world.facts["feature"] = "inner monologue"
    world.facts["problem_kind"] = world.trouble.kind
    return world


def disturb(world: World) -> None:
    hero = world.entities["hero"]
    nook = world.entities["nook"]
    ship = world.entities["ship"]
    book = world.entities["book"]
    source = world.entities[world.trouble.source]

    hero.add_meme("worry", 1.0)
    hero.add_meme("imagination", 0.8)
    hero.add_meter("breath", -0.3)
    nook.add_meter("stillness", -0.4)
    ship.add_meter("motion", 0.7)
    ship.add_meter("balance", -0.3)
    book.add_meter("settled_pages", -0.3)

    if world.trouble.kind == "draft":
        source.tags["state"] = "ajar"
        source.set_meter("draft", 1.0)
    elif world.trouble.kind == "glimmer":
        source.tags["state"] = "wandering"
        source.set_meter("glimmer", 1.0)
        ship.add_meter("glow", -0.3)
        book.add_meter("clarity", -0.2)
    else:
        source.tags["state"] = "slumped"
        source.set_meter("tilt", 1.0)
        ship.add_meter("balance", -0.6)
        book.add_meter("settled_pages", -0.2)

    world.facts["omen"] = world.trouble.omen
    world.facts["risk"] = world.trouble.risk
    world.event("disturbance", world.trouble.omen, world.trouble.risk)


def inner_monologue(world: World) -> None:
    hero = world.entities["hero"]
    thought = world.trouble.thought.format(title=world.book.title, quest=world.book.quest)
    hero.add_meme("reflection", 0.9)
    hero.add_meme("fear_story", 0.7)
    world.facts["thought"] = thought
    world.event("inner_monologue", thought)


def inspect(world: World) -> None:
    hero = world.entities["hero"]
    helper = world.entities["helper"]
    hero.add_meme("courage", 0.8)
    hero.add_meme("attention", 0.9)
    helper.add_meme("guidance", 0.8)
    world.facts["inspect"] = world.trouble.inspect
    world.facts["reveal"] = world.trouble.reveal
    world.event("inspection", world.trouble.inspect, world.trouble.reveal)


def repair(world: World) -> None:
    hero = world.entities["hero"]
    nook = world.entities["nook"]
    ship = world.entities["ship"]
    book = world.entities["book"]
    source = world.entities[world.trouble.source]

    hero.add_meme("relief", 1.3)
    hero.add_meme("trust", 0.9)
    hero.add_meter("breath", 0.5)
    hero.add_meter("steadiness", 0.4)
    nook.add_meter("stillness", 0.7)
    ship.set_meter("motion", 0.0)
    ship.set_meter("balance", 1.3)
    book.set_meter("settled_pages", 1.3)
    book.add_meter("clarity", 0.4)

    if world.trouble.kind == "draft":
        source.tags["state"] = "snug"
        source.set_meter("draft", 0.0)
    elif world.trouble.kind == "glimmer":
        source.tags["state"] = "still"
        source.set_meter("glimmer", 0.0)
        ship.set_meter("glow", 1.2)
    else:
        source.tags["state"] = "square"
        source.set_meter("tilt", 0.0)

    ship.tags["state"] = "steady"
    world.facts["helper_action"] = world.remedy.helper_action
    world.facts["repair_action"] = world.remedy.action
    world.facts["repair_result"] = world.remedy.result
    world.event("repair", world.remedy.action, world.remedy.result)


def simulate(world: World) -> World:
    if world.history:
        return world
    disturb(world)
    inner_monologue(world)
    inspect(world)
    repair(world)
    return world


def render_story(world: World) -> str:
    simulate(world)
    she, her, _ = pronouns(world.params.gender)
    hero = world.entities["hero"]
    helper = world.entities["helper"]
    calm_win = hero.memes.get("relief", 0.0) > hero.memes.get("worry", 0.0)

    opening = (
        f"Once upon an evening gentle as wool, {world.params.hero}, a {world.params.trait} child, climbed into a cozy ship in "
        f"the reading nook called {world.nook.label}. The little vessel was a {world.ship.label}, fashioned from {world.ship.build}, "
        f"with {world.ship.sail}. Around it stretched {world.nook.scene}. In {her} lap lay {world.book.title}, open to a page where "
        f"{world.book.page_image}."
    )
    trouble = (
        f"{world.trouble.omen} {world.params.hero} did not cry out, but inside {she} thought, "
        f"\"{world.facts['thought']}\""
    )
    turn = (
        f"Instead of leaping from the berth, {she} listened for what was truly happening. {helper.label} came close and treated the worry kindly. "
        f"{world.trouble.inspect} {world.trouble.reveal} {world.remedy.helper_action} Together they {world.remedy.action}."
    )
    ending_lesson = (
        world.book.lesson
        if calm_win
        else "Even after the fix, the child kept learning how careful looking can outshine a frightening guess."
    )
    ending = (
        f"{world.remedy.result} Soon {world.params.hero} read on about {world.book.quest}. "
        f"In the end, {world.nook.ending_image}. {world.remedy.image} {sentence_case(world.ship.berth_image)}, and {world.trouble.ending_change}. "
        f"{ending_lesson}"
    )
    return "\n\n".join([opening, trouble, turn, ending])


def generation_prompts(world: World) -> list[str]:
    return [
        'Write a fairy-tale story for children that includes the words "cozy ship" and takes place in a reading nook.',
        f"Tell an inner-monologue story about {world.params.hero} reading {world.book.title} inside a {world.ship.label}.",
        f"Write a gentle tale where {world.trouble.label} is solved by {world.remedy.label} through careful noticing.",
    ]


def story_qa(world: World) -> list[QAItem]:
    simulate(world)
    return [
        QAItem(
            "What problem disturbed the cozy ship?",
            f"{world.trouble.omen} This mattered because {world.trouble.risk}.",
        ),
        QAItem(
            "What did the child think during the tense moment?",
            f"{world.params.hero} imagined, \"{world.facts['thought']}\" The thought came from the way the real trouble echoed the fairy book in the child's lap.",
        ),
        QAItem(
            "How did the helper change the middle of the story?",
            f"{world.entities['helper'].label} treated the worry as worth noticing instead of something silly. {world.remedy.helper_action} That calm help made room for a true inspection.",
        ),
        QAItem(
            "What was the real cause, and how was it fixed?",
            f"{world.trouble.reveal} Then they {world.remedy.action}. {world.remedy.result}",
        ),
        QAItem(
            "How can you tell the ending is calmer than the beginning?",
            f"By the end, {lower_first(world.nook.ending_image)}. {world.remedy.image} {sentence_case(world.ship.berth_image)}, and {world.trouble.ending_change}. Those final details show that the room, the ship, and the child have all steadied.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    simulate(world)
    items = [
        QAItem(
            "Why can a tiny change in a reading nook feel magical to a child?",
            "A child who is deep in a story often lets the room and the book blend together. Then a draft, a moving light, or a tilt can feel like part of the tale instead of just part of the furniture.",
        ),
        QAItem(
            "Why does inner monologue help this kind of fairy tale?",
            "Inner monologue lets the reader hear the fear before the problem is solved. That makes the later calm inspection feel earned rather than sudden.",
        ),
        QAItem(
            "Why is a gentle helper important in a small household adventure?",
            "A gentle helper keeps worry from turning into shame. With that safety, a child can look closely, learn the real cause, and remember the lesson afterward.",
        ),
    ]
    if world.trouble.kind == "draft":
        items.append(
            QAItem(
                "Why does closing a small draft change more than the air?",
                "It keeps pages from fluttering and helps a blanket fort feel sheltered again. The body relaxes when the room stops whispering cold surprises.",
            )
        )
    elif world.trouble.kind == "glimmer":
        items.append(
            QAItem(
                "Why can steady light make a room feel kinder?",
                "Still light lets the eyes understand the space without guessing at every flicker. When the light settles, the imagination can stop treating the wall like a warning.",
            )
        )
    else:
        items.append(
            QAItem(
                "Why does leveling a fort matter in pretend play?",
                "A level fort lets the body trust the pretend world again. That physical steadiness makes it easier for the mind to return to the story instead of guarding against the slide.",
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
combo(N,S,T,R,B) :-
    nook(N),
    ship(S),
    trouble(T),
    remedy(R),
    book(B),
    trouble_kind(T,K),
    nook_support(N,K),
    ship_support(S,K),
    book_echo(B,K),
    remedy_kind(R,K).

ok :- chosen(N,S,T,R,B), combo(N,S,T,R,B).

#show combo/5.
#show ok/0.
"""


def asp_facts(params: StoryParams | None = None) -> str:
    import storyworlds.asp as asp

    rows: list[str] = []
    for key, nook in NOOKS.items():
        rows.append(asp.fact("nook", key))
        for support in nook.supports:
            rows.append(asp.fact("nook_support", key, support))
    for key, ship in SHIPS.items():
        rows.append(asp.fact("ship", key))
        for support in ship.supports:
            rows.append(asp.fact("ship_support", key, support))
    for key, trouble in TROUBLES.items():
        rows.append(asp.fact("trouble", key))
        rows.append(asp.fact("trouble_kind", key, trouble.kind))
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
                params.trouble,
                params.remedy,
                params.book,
            )
        )
    return "\n".join(rows) + "\n"


def asp_program(params: StoryParams | None = None) -> str:
    return asp_facts(params) + ASP_RULES


def asp_valid_combos() -> set[tuple[str, str, str, str, str]]:
    import storyworlds.asp as asp

    combos: set[tuple[str, str, str, str, str]] = set()
    for model in asp.solve(asp_program(), models=0):
        combos.update(asp.atoms(model, "combo"))
    return combos


def asp_verify(params: StoryParams) -> bool:
    import storyworlds.asp as asp

    model = asp.one_model(asp_program(params))
    return bool(asp.atoms(model, "ok"))


def verify() -> str:
    python_combos = set(valid_combos())
    asp_combos = asp_valid_combos()
    if python_combos != asp_combos:
        raise StoryError(
            f"ASP/Python mismatch. only_python={sorted(python_combos - asp_combos)} "
            f"only_asp={sorted(asp_combos - python_combos)}"
        )

    exercised = 0
    for i, combo in enumerate(sorted(python_combos)):
        params = StoryParams(
            nook=combo[0],
            ship=combo[1],
            trouble=combo[2],
            remedy=combo[3],
            book=combo[4],
            hero="Mira",
            gender="girl",
            helper="grandmother",
            trait="thoughtful",
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
            raise StoryError(f"Generated story missing inner-monologue framing for combo: {combo}")
        if len(sample.story_qa) < 5 or len(sample.world_qa) < 4:
            raise StoryError(f"Generated QA too thin for combo: {combo}")
        exercised += 1
    return f"OK: ASP and Python agree on {len(python_combos)} valid cozy-ship stories; exercised {exercised} samples."


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate cozy ship fairy-tale storyworld samples.")
    parser.add_argument("--nook", choices=sorted(NOOKS))
    parser.add_argument("--ship", choices=sorted(SHIPS))
    parser.add_argument("--trouble", choices=sorted(TROUBLES))
    parser.add_argument("--remedy", choices=sorted(REMEDIES))
    parser.add_argument("--book", choices=sorted(BOOKS))
    parser.add_argument("--hero")
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


def matching_combos(args: argparse.Namespace) -> list[tuple[str, str, str, str, str]]:
    rows: list[tuple[str, str, str, str, str]] = []
    for combo in valid_combos():
        if args.nook and args.nook != combo[0]:
            continue
        if args.ship and args.ship != combo[1]:
            continue
        if args.trouble and args.trouble != combo[2]:
            continue
        if args.remedy and args.remedy != combo[3]:
            continue
        if args.book and args.book != combo[4]:
            continue
        rows.append(combo)
    return rows


def make_params(
    args: argparse.Namespace,
    rng: random.Random,
    combo: tuple[str, str, str, str, str],
    seed: int | None,
) -> StoryParams:
    gender = args.gender or rng.choice(sorted(HEROES))
    hero = args.hero or rng.choice(HEROES[gender])
    helper = args.helper or rng.choice(HELPERS)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(
        nook=combo[0],
        ship=combo[1],
        trouble=combo[2],
        remedy=combo[3],
        book=combo[4],
        hero=hero,
        gender=gender,
        helper=helper,
        trait=trait,
        seed=seed,
    )


def resolve_params(args: argparse.Namespace, rng: random.Random | None = None) -> StoryParams:
    rng = rng or random.Random(args.seed)
    combos = matching_combos(args)
    if not combos:
        nook = args.nook or next(iter(NOOKS))
        ship = args.ship or next(iter(SHIPS))
        trouble = args.trouble or next(iter(TROUBLES))
        remedy = args.remedy or next(iter(REMEDIES))
        book = args.book or next(iter(BOOKS))
        raise StoryError(explain_rejection(nook, ship, trouble, remedy, book))
    story_seed = getattr(rng, "story_seed", args.seed)
    return make_params(args, rng, rng.choice(combos), story_seed)


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


def json_dump(samples: list[StorySample]) -> None:
    if len(samples) == 1:
        print(samples[0].to_json())
        return
    print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))


def samples_for_all(args: argparse.Namespace) -> list[StorySample]:
    rows: list[StorySample] = []
    base_seed = args.seed if args.seed is not None else 1000
    for i, combo in enumerate(valid_combos()):
        story_seed = base_seed + i
        rng = random.Random(story_seed)
        rng.story_seed = story_seed
        rows.append(generate(make_params(args, rng, combo, story_seed)))
    return rows


def samples_for_n(args: argparse.Namespace) -> list[StorySample]:
    base_seed = args.seed if args.seed is not None else random.randrange(1, 1_000_000)
    target = max(1, args.n)
    rows: list[StorySample] = []
    seen: set[str] = set()
    attempts = 0
    while len(rows) < target and attempts < target * 40:
        story_seed = base_seed + attempts
        rng = random.Random(story_seed)
        rng.story_seed = story_seed
        sample = generate(resolve_params(args, rng))
        if sample.story not in seen:
            seen.add(sample.story)
            rows.append(sample)
        attempts += 1
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

        samples = samples_for_all(args) if args.all else samples_for_n(args)
        if args.json:
            json_dump(samples)
            return 0
        for i, sample in enumerate(samples):
            header = None
            if args.all:
                header = (
                    f"### {sample.params.hero}: {sample.params.ship} / "
                    f"{sample.params.trouble} / {sample.params.book}"
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
