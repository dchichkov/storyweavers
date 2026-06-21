#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/fortieth_dramatic_tad_moral_value_bad_ending.py
============================================================================

A small mystery-flavored storyworld about a child who turns a real problem into
a pretend mystery by hiding an important object "for just a tad longer." The
choice makes the scene feel dramatic for a moment, but it spoils a special day
and hurts trust.

The world model prefers fewer, stronger variants over loose coverage:
an essential celebration item goes missing, a friend warns that honesty matters,
and the hero either confesses too late or is found out after the damage is done.
Every ending is a bad ending, because the seed explicitly asks for one.

Run it
------
    python storyworlds/worlds/gpt-5.4/fortieth_dramatic_tad_moral_value_bad_ending.py
    python storyworlds/worlds/gpt-5.4/fortieth_dramatic_tad_moral_value_bad_ending.py --place museum --event bell
    python storyworlds/worlds/gpt-5.4/fortieth_dramatic_tad_moral_value_bad_ending.py --item teacup
    python storyworlds/worlds/gpt-5.4/fortieth_dramatic_tad_moral_value_bad_ending.py --all --qa
    python storyworlds/worlds/gpt-5.4/fortieth_dramatic_tad_moral_value_bad_ending.py --verify
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
CAUTION_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    portable: bool = False
    essential: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "librarian", "teacher"}
        male = {"boy", "father", "man", "caretaker"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad", "caretaker": "caretaker"}.get(self.type, self.type)


@dataclass
class Place:
    id: str
    label: str
    phrase: str
    mood: str
    affords: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class EventCfg:
    id: str
    title: str
    opening: str
    crowd: str
    needs_tag: str
    failed_image: str
    tags: set[str] = field(default_factory=set)


@dataclass
class ItemCfg:
    id: str
    label: str
    phrase: str
    tag: str
    reveal: str
    use_text: str
    portable: bool = True
    essential: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class Temptation:
    id: str
    line: str
    motive: str
    intensity: int
    requires_portable: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class FriendTrait:
    id: str
    label: str
    caution: int
    whisper: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    place: str
    event: str
    item: str
    temptation: str
    friend_trait: str
    hero_name: str
    hero_gender: str
    friend_name: str
    friend_gender: str
    adult_type: str
    delay: int = 1
    seed: Optional[int] = None


PLACES = {
    "museum": Place(
        id="museum",
        label="museum",
        phrase="the old town museum",
        mood="The long room smelled like waxed wood, and every glass case seemed to be hiding a clue.",
        affords={"bell", "ribbon"},
        tags={"museum", "mystery"},
    ),
    "library": Place(
        id="library",
        label="library",
        phrase="the library hall",
        mood="The lamps made warm circles on the floor, and the shelves stood like quiet witnesses.",
        affords={"book", "ribbon"},
        tags={"library", "mystery"},
    ),
    "clock_tower": Place(
        id="clock_tower",
        label="clock tower room",
        phrase="the room beneath the old clock tower",
        mood="Above them, the gears clicked and sighed as if the building itself were listening.",
        affords={"bell", "key"},
        tags={"tower", "mystery"},
    ),
}

EVENTS = {
    "bell": EventCfg(
        id="bell",
        title="the fortieth bell-ringing",
        opening="That evening the town was getting ready for the fortieth bell-ringing.",
        crowd="Families were already gathering by the doors, waiting to hear the first clear note.",
        needs_tag="bell",
        failed_image="The rope hung still, and the waiting families drifted home in a disappointed hush.",
        tags={"fortieth", "celebration"},
    ),
    "book": EventCfg(
        id="book",
        title="the fortieth midnight reading",
        opening="That evening the town was getting ready for the fortieth midnight reading.",
        crowd="Children sat on folding chairs with bright eyes, waiting for the first page to be opened.",
        needs_tag="book",
        failed_image="The reading table stayed empty, and one by one the children were taken home.",
        tags={"fortieth", "celebration"},
    ),
    "ribbon": EventCfg(
        id="ribbon",
        title="the fortieth gallery opening",
        opening="That evening the town was getting ready for the fortieth gallery opening.",
        crowd="Neighbors whispered near the doorway, ready to clap when the ribbon was cut.",
        needs_tag="ribbon",
        failed_image="The doorway remained closed, and the clapping never came.",
        tags={"fortieth", "celebration"},
    ),
    "key": EventCfg(
        id="key",
        title="the fortieth tower showing",
        opening="That evening the town was getting ready for the fortieth tower showing.",
        crowd="People below craned their necks, waiting for the old clock face to shine open.",
        needs_tag="key",
        failed_image="The locked panel stayed shut, and the crowd slowly stopped looking up.",
        tags={"fortieth", "celebration"},
    ),
}

ITEMS = {
    "bell_rope": ItemCfg(
        id="bell_rope",
        label="bell rope clasp",
        phrase="the brass bell-rope clasp",
        tag="bell",
        reveal="Without the clasp, the bell rope could not be secured in place.",
        use_text="fasten the bell rope",
        portable=True,
        essential=True,
        tags={"bell", "metal"},
    ),
    "silver_bookmark": ItemCfg(
        id="silver_bookmark",
        label="silver bookmark",
        phrase="the silver bookmark for the first page",
        tag="book",
        reveal="Without it, the special reading copy could not be opened to the marked page.",
        use_text="mark the first page of the old book",
        portable=True,
        essential=True,
        tags={"book", "silver"},
    ),
    "red_ribbon": ItemCfg(
        id="red_ribbon",
        label="red ribbon shears",
        phrase="the red ribbon shears",
        tag="ribbon",
        reveal="Without the shears, nobody could cut the opening ribbon neatly.",
        use_text="cut the ribbon",
        portable=True,
        essential=True,
        tags={"ribbon", "ceremony"},
    ),
    "tower_key": ItemCfg(
        id="tower_key",
        label="tower key",
        phrase="the old tower key",
        tag="key",
        reveal="Without it, the glass panel over the clock's face could not be unlocked.",
        use_text="unlock the tower panel",
        portable=True,
        essential=True,
        tags={"key", "tower"},
    ),
    "teacup": ItemCfg(
        id="teacup",
        label="teacup",
        phrase="a painted teacup from the snack table",
        tag="snack",
        reveal="It was only for drinking juice and had nothing to do with the ceremony.",
        use_text="serve juice",
        portable=True,
        essential=False,
        tags={"snack"},
    ),
}

TEMPTATIONS = {
    "dramatic_reveal": Temptation(
        id="dramatic_reveal",
        line=''"If I keep it for just a tad longer," {hero} whispered, "the mystery will be more dramatic."''',
        motive="wanted the mystery to feel bigger and more exciting",
        intensity=2,
        requires_portable=True,
        tags={"dramatic", "dishonesty"},
    ),
    "private_detective": Temptation(
        id="private_detective",
        line=''"Let me solve it first," {hero} whispered. "Then everyone will gasp."''',
        motive="wanted to be the one who solved the mystery alone",
        intensity=1,
        requires_portable=True,
        tags={"mystery", "dishonesty"},
    ),
    "secret_test": Temptation(
        id="secret_test",
        line=''"I just want to test the clues for a tad," {hero} whispered. "No one will notice yet."''',
        motive="told {hero_obj}self it was only a small secret for a moment",
        intensity=2,
        requires_portable=True,
        tags={"tad", "dishonesty"},
    ),
}

FRIEND_TRAITS = {
    "careful": FriendTrait(
        id="careful",
        label="careful",
        caution=3,
        whisper="That is not a game anymore. Someone needs it.",
        tags={"honesty"},
    ),
    "gentle": FriendTrait(
        id="gentle",
        label="gentle",
        caution=2,
        whisper="Please put it back now. A real clue should help people, not scare them.",
        tags={"honesty"},
    ),
    "curious": FriendTrait(
        id="curious",
        label="curious",
        caution=1,
        whisper="This is strange... but I still think you should tell.",
        tags={"honesty"},
    ),
}

GIRL_NAMES = ["Lila", "Mina", "Nora", "Ivy", "Anna", "Cora", "Elsie", "Ruby"]
BOY_NAMES = ["Theo", "Ben", "Milo", "Owen", "Jude", "Eli", "Sam", "Finn"]


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
        clone.facts = dict(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_hidden_worry(world: World) -> list[str]:
    out: list[str] = []
    item = world.get("item")
    adult = world.get("adult")
    if item.meters["hidden"] >= THRESHOLD:
        sig = ("worry", item.id)
        if sig not in world.fired:
            world.fired.add(sig)
            adult.memes["worry"] += 1
            world.get("hero").memes["guilt"] += 1
            out.append("__worry__")
    return out


def _r_delay_search(world: World) -> list[str]:
    out: list[str] = []
    item = world.get("item")
    room = world.get("room")
    if item.meters["hidden"] >= THRESHOLD and world.facts.get("delay", 0) >= 1:
        sig = ("search", item.id, world.facts.get("delay", 0))
        if sig not in world.fired:
            world.fired.add(sig)
            room.meters["search"] += float(world.facts["delay"])
            out.append("__search__")
    return out


def _r_spoil_event(world: World) -> list[str]:
    out: list[str] = []
    room = world.get("room")
    if room.meters["search"] >= THRESHOLD:
        sig = ("spoiled", "event")
        if sig not in world.fired:
            world.fired.add(sig)
            room.meters["spoiled"] += 1
            world.get("friend").memes["sadness"] += 1
            world.get("hero").memes["guilt"] += 1
            out.append("__spoiled__")
    return out


CAUSAL_RULES = [
    Rule(name="hidden_worry", tag="social", apply=_r_hidden_worry),
    Rule(name="delay_search", tag="social", apply=_r_delay_search),
    Rule(name="spoil_event", tag="social", apply=_r_spoil_event),
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
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def combo_valid(place_id: str, event_id: str, item_id: str, temptation_id: str) -> bool:
    place = PLACES[place_id]
    event = EVENTS[event_id]
    item = ITEMS[item_id]
    temptation = TEMPTATIONS[temptation_id]
    if event_id not in place.affords:
        return False
    if item.tag != event.needs_tag or not item.essential:
        return False
    if temptation.requires_portable and not item.portable:
        return False
    return True


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for place_id in PLACES:
        for event_id in EVENTS:
            for item_id in ITEMS:
                for temptation_id in TEMPTATIONS:
                    if combo_valid(place_id, event_id, item_id, temptation_id):
                        combos.append((place_id, event_id, item_id, temptation_id))
    return combos


def predict_spoil(world: World, delay: int) -> dict:
    sim = world.copy()
    sim.facts["delay"] = delay
    sim.get("item").meters["hidden"] = 1
    propagate(sim, narrate=False)
    return {
        "adult_worry": sim.get("adult").memes["worry"],
        "spoiled": sim.get("room").meters["spoiled"] >= THRESHOLD,
    }


def confession_possible(friend_trait: FriendTrait, delay: int, temptation: Temptation) -> bool:
    return friend_trait.caution >= CAUTION_MIN and delay <= temptation.intensity


def outcome_of(params: StoryParams) -> str:
    trait = FRIEND_TRAITS[params.friend_trait]
    temptation = TEMPTATIONS[params.temptation]
    if confession_possible(trait, params.delay, temptation):
        return "late_confession"
    return "discovered"


def scene_setup(world: World, place: Place, event: EventCfg, hero: Entity, friend: Entity, adult: Entity) -> None:
    world.say(f"{event.opening} {hero.id} and {friend.id} stood in {place.phrase} with {adult.label}.")
    world.say(place.mood)
    world.say(
        f"{adult.label.capitalize()} checked the tables and display stands one more time. "
        f'{event.crowd}'
    )


def mystery_seed(world: World, hero: Entity, friend: Entity, item: ItemCfg) -> None:
    hero.memes["curiosity"] += 1
    friend.memes["curiosity"] += 1
    world.say(
        f"On a velvet cloth near the front rested {item.phrase}. "
        f"It looked small, but it was important enough to feel like the center of every clue."
    )
    world.say(
        f'"That must be the thing everyone is guarding," {friend.id} whispered. '
        f'"It does not look scary at all."'
    )


def hide_item(world: World, hero: Entity, friend: Entity, adult: Entity, item_ent: Entity,
              item_cfg: ItemCfg, temptation: Temptation, delay: int) -> None:
    item_ent.meters["hidden"] += 1
    world.facts["delay"] = delay
    propagate(world, narrate=False)
    line = temptation.line.format(hero=hero.id, hero_obj=hero.pronoun("object"))
    world.say(
        f"When {adult.label} turned to answer a question at the door, {hero.id} slipped "
        f"{item_cfg.phrase} into {hero.pronoun('possessive')} pocket."
    )
    world.say(line)
    world.say(
        f'{friend.id} stared. "{FRIEND_TRAITS[world.facts["friend_trait"].id].whisper}"'
    )
    world.say(
        f'"I will put it back soon," {hero.id} murmured. But soon kept stretching like a shadow.'
    )


def search_begins(world: World, adult: Entity, item_cfg: ItemCfg) -> None:
    adult.memes["searching"] += 1
    world.say(
        f'A minute later, {adult.label} stopped short. "Where is {item_cfg.phrase}?"'
    )
    world.say(
        f"{adult.label.capitalize()} looked under the cloth, inside the case, and even behind the guest book."
    )


def pressure(world: World, hero: Entity, friend: Entity, item_cfg: ItemCfg) -> None:
    if world.get("adult").memes["worry"] >= THRESHOLD:
        world.say(
            f'{friend.id} leaned close. "This is why I warned you," {friend.pronoun()} whispered. '
            f'"They need it to {item_cfg.use_text}."'
        )
    if world.get("room").meters["spoiled"] >= THRESHOLD:
        world.say(
            f"{hero.id}'s pocket suddenly felt as heavy as a stone. "
            f"{hero.pronoun().capitalize()} could hear chairs scraping and grown-ups beginning to wonder aloud."
        )


def late_confession(world: World, hero: Entity, friend: Entity, adult: Entity,
                    event: EventCfg, item_cfg: ItemCfg) -> None:
    hero.memes["honesty"] += 1
    world.say(
        f'At last {hero.id} tugged on {adult.label}\'s sleeve. "I took it," {hero.pronoun()} whispered. '
        f'"I only wanted the mystery to feel more dramatic for a tad."'
    )
    world.say(
        f"{adult.label.capitalize()} opened {adult.pronoun('possessive')} hand, and {hero.id} placed "
        f"{item_cfg.label} into it with shaking fingers."
    )
    world.say(
        f'"Oh, {hero.id}," {adult.label} said quietly. "A mystery is not fun when other people are frightened."'
    )
    world.say(event.failed_image)


def discovered_ending(world: World, hero: Entity, friend: Entity, adult: Entity,
                      event: EventCfg, item_cfg: ItemCfg) -> None:
    world.say(
        f"Before {hero.id} could speak, {adult.label} noticed the stiff shape in "
        f"{hero.pronoun('possessive')} pocket."
    )
    world.say(
        f'"{hero.id}, is that {item_cfg.phrase}?" {adult.label} asked. The room became very still.'
    )
    world.say(
        f"{hero.id} could not make a brave answer now. {hero.pronoun().capitalize()} only nodded while "
        f"{friend.id} looked down at the floor."
    )
    world.say(
        f'"You let everyone search while you knew," {adult.label} said, more sad than loud. '
        f'"That breaks trust."'
    )
    world.say(event.failed_image)


def closing_moral(world: World, hero: Entity, friend: Entity, adult: Entity) -> None:
    world.say(
        f"Nobody shouted. That made the lesson feel even colder. {hero.id} wished "
        f"{hero.pronoun()} had told the truth the very first moment."
    )
    world.say(
        f"{friend.id} walked beside {hero.pronoun('object')} in silence as the lights were lowered. "
        f"The mystery was over, but the sad part stayed."
    )
    world.say(
        f"From then on, {hero.id} understood something simple and hard: honesty may feel small at first, "
        f"but hiding the truth can darken a whole room."
    )


def tell(place: Place, event: EventCfg, item_cfg: ItemCfg, temptation: Temptation,
         friend_trait: FriendTrait, hero_name: str = "Nora", hero_gender: str = "girl",
         friend_name: str = "Theo", friend_gender: str = "boy", adult_type: str = "caretaker",
         delay: int = 1) -> World:
    world = World()
    hero = world.add(Entity(id="hero", kind="character", type=hero_gender, label=hero_name, role="hero"))
    friend = world.add(Entity(id="friend", kind="character", type=friend_gender, label=friend_name,
                              role="friend", traits=[friend_trait.label]))
    adult_label = "the caretaker" if adult_type == "caretaker" else f"the {adult_type}"
    adult = world.add(Entity(id="adult", kind="character", type=adult_type, label=adult_label, role="adult"))
    room = world.add(Entity(id="room", kind="place", type="room", label=place.label))
    item_ent = world.add(Entity(id="item", type="item", label=item_cfg.label, phrase=item_cfg.phrase,
                                portable=item_cfg.portable, essential=item_cfg.essential))

    world.facts.update(
        place=place,
        event=event,
        item_cfg=item_cfg,
        temptation=temptation,
        friend_trait=friend_trait,
        delay=delay,
    )

    scene_setup(world, place, event, hero, friend, adult)
    mystery_seed(world, hero, friend, item_cfg)

    world.para()
    hide_item(world, hero, friend, adult, item_ent, item_cfg, temptation, delay)
    search_begins(world, adult, item_cfg)
    pressure(world, hero, friend, item_cfg)

    world.para()
    outcome = "late_confession" if confession_possible(friend_trait, delay, temptation) else "discovered"
    if outcome == "late_confession":
        late_confession(world, hero, friend, adult, event, item_cfg)
    else:
        discovered_ending(world, hero, friend, adult, event, item_cfg)
    closing_moral(world, hero, friend, adult)

    world.facts.update(
        hero=hero,
        friend=friend,
        adult=adult,
        room=room,
        item=item_ent,
        outcome=outcome,
        spoiled=room.meters["spoiled"] >= THRESHOLD,
        confessed=outcome == "late_confession",
    )
    return world


KNOWLEDGE = {
    "museum": [(
        "What is a museum?",
        "A museum is a place where people keep and show important old things, pictures, or objects so others can learn from them."
    )],
    "library": [(
        "What is a library?",
        "A library is a place full of books where people can read, borrow stories, and learn quietly."
    )],
    "bell": [(
        "Why is a bell-ringing ceremony special?",
        "A bell-ringing ceremony gathers people to hear a shared sound at an important moment. If the bell cannot ring, the whole event feels different."
    )],
    "book": [(
        "Why can a bookmark matter in an old book?",
        "A bookmark can show the exact place to begin reading. In a special event, losing it can slow everyone down and confuse the opening."
    )],
    "ribbon": [(
        "Why do people cut a ribbon at an opening?",
        "Cutting a ribbon is a way to show that a new room or exhibit is officially opening. It is a small action that starts a big moment."
    )],
    "key": [(
        "What does a key do?",
        "A key opens something that is locked. If the key is missing, people may have to wait outside or stop their plans."
    )],
    "honesty": [(
        "Why is honesty important?",
        "Honesty helps people trust each other and solve problems quickly. Even a small lie or hidden secret can make a bigger problem grow."
    )],
    "mystery": [(
        "What is a mystery?",
        "A mystery is a problem with hidden facts that people try to figure out. A real mystery should be solved by telling the truth about the clues."
    )],
    "trust": [(
        "What does it mean to break trust?",
        "Breaking trust means someone believed you would do the right thing, but your choice made that belief weaker. It can take time and honest actions to mend."
    )],
}
KNOWLEDGE_ORDER = ["museum", "library", "bell", "book", "ribbon", "key", "mystery", "honesty", "trust"]


def generation_prompts(world: World) -> list[str]:
    place = world.facts["place"]
    event = world.facts["event"]
    item_cfg = world.facts["item_cfg"]
    temptation = world.facts["temptation"]
    hero = world.facts["hero"]
    friend = world.facts["friend"]
    return [
        f'Write a short mystery story for a 3-to-5-year-old that includes the words "fortieth", "dramatic", and "tad".',
        f"Tell a gentle-but-sad mystery set in {place.phrase}, where {hero.label} hides {item_cfg.phrase} before {event.title} because {hero.pronoun()} wants the mystery to feel more dramatic.",
        f"Write a story with dialogue, a moral about honesty, and a bad ending where {friend.label} warns {hero.label}, but the missing clue still spoils the special event.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    hero = world.facts["hero"]
    friend = world.facts["friend"]
    adult = world.facts["adult"]
    place = world.facts["place"]
    event = world.facts["event"]
    item_cfg = world.facts["item_cfg"]
    temptation = world.facts["temptation"]
    outcome = world.facts["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.label}, {friend.label}, and {adult.label} in {place.phrase}. They are all caught up in a mystery on the night of {event.title}."
        ),
        (
            f"What important thing went missing before {event.title}?",
            f"The missing thing was {item_cfg.phrase}. It mattered because people needed it to {item_cfg.use_text}."
        ),
        (
            f"Why did {hero.label} hide it?",
            f"{hero.label} hid it because {hero.pronoun()} thought the mystery would feel more exciting and more dramatic for a tad. That choice came from wanting a thrilling moment instead of choosing honesty right away."
        ),
        (
            f"What did {friend.label} say?",
            f"{friend.label} warned {hero.label} to put it back and reminded {hero.pronoun('object')} that real clues should help people, not scare them. The warning showed that {friend.label} understood the risk before the grown-up did."
        ),
    ]
    if outcome == "late_confession":
        qa.append((
            f"Did {hero.label} tell the truth in time?",
            f"No. {hero.label} did confess, but only after the searching and worry had already spoiled the moment. The truth came out too late to save the celebration."
        ))
    else:
        qa.append((
            f"How was the secret discovered?",
            f"{adult.label.capitalize()} saw the shape of {item_cfg.label} in {hero.label}'s pocket and asked about it. That is when the hidden truth came out, after everyone had already been searching."
        ))
    qa.append((
        "How did the story end?",
        f"It ended sadly. {event.failed_image} The bad ending shows that a small dishonest choice can grow into a much bigger loss."
    ))
    qa.append((
        "What is the moral of the story?",
        "The moral is that honesty matters right away, not only after trouble grows. Hiding the truth to make something feel exciting can hurt other people and damage trust."
    ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = set(world.facts["place"].tags) | set(world.facts["event"].tags) | set(world.facts["temptation"].tags)
    tags |= {"honesty", "trust"}
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
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.traits:
            bits.append(f"traits={ent.traits}")
        if ent.portable:
            bits.append("portable=True")
        if ent.essential:
            bits.append("essential=True")
        lines.append(f"  {ent.id:8} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        place="museum",
        event="bell",
        item="bell_rope",
        temptation="dramatic_reveal",
        friend_trait="careful",
        hero_name="Nora",
        hero_gender="girl",
        friend_name="Theo",
        friend_gender="boy",
        adult_type="caretaker",
        delay=1,
    ),
    StoryParams(
        place="library",
        event="book",
        item="silver_bookmark",
        temptation="secret_test",
        friend_trait="gentle",
        hero_name="Mina",
        hero_gender="girl",
        friend_name="Ben",
        friend_gender="boy",
        adult_type="librarian",
        delay=2,
    ),
    StoryParams(
        place="museum",
        event="ribbon",
        item="red_ribbon",
        temptation="private_detective",
        friend_trait="curious",
        hero_name="Eli",
        hero_gender="boy",
        friend_name="Ruby",
        friend_gender="girl",
        adult_type="caretaker",
        delay=1,
    ),
    StoryParams(
        place="clock_tower",
        event="key",
        item="tower_key",
        temptation="dramatic_reveal",
        friend_trait="careful",
        hero_name="Sam",
        hero_gender="boy",
        friend_name="Ivy",
        friend_gender="girl",
        adult_type="caretaker",
        delay=2,
    ),
]


def explain_rejection(place_id: str, event_id: str, item_id: str, temptation_id: str) -> str:
    place = PLACES[place_id]
    event = EVENTS[event_id]
    item = ITEMS[item_id]
    temptation = TEMPTATIONS[temptation_id]
    if event_id not in place.affords:
        return (
            f"(No story: {place.phrase} is not set up for {event.title}. Pick a place that can honestly host that event.)"
        )
    if item.tag != event.needs_tag or not item.essential:
        return (
            f"(No story: {item.phrase} is not the essential object for {event.title}, so its loss would not create the right mystery or bad ending.)"
        )
    if temptation.requires_portable and not item.portable:
        return (
            f"(No story: {item.phrase} cannot be secretly pocketed, so the temptation '{temptation.id}' does not fit.)"
        )
    return "(No story: that combination is unreasonable.)"


ASP_RULES = r"""
usable_place(P, E) :- place(P), event(E), affords(P, E).
matching_item(E, I) :- event(E), item(I), needs_tag(E, T), item_tag(I, T), essential(I).
valid(P, E, I, Tm) :- usable_place(P, E), matching_item(E, I), temptation(Tm), portable(I).

strong_warning(F) :- friend_trait(F), caution(F, C), caution_min(M), C >= M.
late_confession :- chosen_friend(F), strong_warning(F),
                   chosen_delay(D), chosen_temptation(Tm), intensity(Tm, I), D <= I.
outcome(late_confession) :- late_confession.
outcome(discovered) :- not late_confession.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for place_id, place in PLACES.items():
        lines.append(asp.fact("place", place_id))
        for event_id in sorted(place.affords):
            lines.append(asp.fact("affords", place_id, event_id))
    for event_id, event in EVENTS.items():
        lines.append(asp.fact("event", event_id))
        lines.append(asp.fact("needs_tag", event_id, event.needs_tag))
    for item_id, item in ITEMS.items():
        lines.append(asp.fact("item", item_id))
        lines.append(asp.fact("item_tag", item_id, item.tag))
        if item.portable:
            lines.append(asp.fact("portable", item_id))
        if item.essential:
            lines.append(asp.fact("essential", item_id))
    for temptation_id, temptation in TEMPTATIONS.items():
        lines.append(asp.fact("temptation", temptation_id))
        lines.append(asp.fact("intensity", temptation_id, temptation.intensity))
    for friend_id, friend in FRIEND_TRAITS.items():
        lines.append(asp.fact("friend_trait", friend_id))
        lines.append(asp.fact("caution", friend_id, friend.caution))
    lines.append(asp.fact("caution_min", CAUTION_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    scenario = "\n".join([
        asp.fact("chosen_friend", params.friend_trait),
        asp.fact("chosen_delay", params.delay),
        asp.fact("chosen_temptation", params.temptation),
    ])
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
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
    for seed in range(30):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
        except StoryError:
            continue
        params.seed = seed
        cases.append(params)

    bad = 0
    for params in cases:
        if asp_outcome(params) != outcome_of(params):
            bad += 1
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("empty story")
        print("OK: generation smoke test passed.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Mystery-flavored storyworld about a child who hides an essential clue and spoils a fortieth celebration."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--event", choices=EVENTS)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--temptation", choices=TEMPTATIONS)
    ap.add_argument("--friend-trait", dest="friend_trait", choices=FRIEND_TRAITS)
    ap.add_argument("--delay", type=int, choices=[1, 2], help="How long the hero waits before telling the truth.")
    ap.add_argument("--adult", dest="adult_type", choices=["caretaker", "librarian", "teacher"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner matches the Python logic")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    options = [name for name in pool if name != avoid]
    return rng.choice(options), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.event and args.item and args.temptation:
        if not combo_valid(args.place, args.event, args.item, args.temptation):
            raise StoryError(explain_rejection(args.place, args.event, args.item, args.temptation))
    if args.item and args.event:
        item = ITEMS[args.item]
        event = EVENTS[args.event]
        if item.tag != event.needs_tag or not item.essential:
            raise StoryError(explain_rejection(args.place or next(iter(PLACES)), args.event, args.item,
                                               args.temptation or next(iter(TEMPTATIONS))))

    combos = [
        combo for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.event is None or combo[1] == args.event)
        and (args.item is None or combo[2] == args.item)
        and (args.temptation is None or combo[3] == args.temptation)
    ]
    if not combos:
        if args.place and args.event and args.item and args.temptation:
            raise StoryError(explain_rejection(args.place, args.event, args.item, args.temptation))
        raise StoryError("(No valid combination matches the given options.)")

    place_id, event_id, item_id, temptation_id = rng.choice(sorted(combos))
    friend_trait = args.friend_trait or rng.choice(sorted(FRIEND_TRAITS))
    hero_name, hero_gender = _pick_name(rng)
    friend_name, friend_gender = _pick_name(rng, avoid=hero_name)
    adult_type = args.adult_type or ("librarian" if place_id == "library" else "caretaker")
    delay = args.delay if args.delay is not None else rng.choice([1, 2])

    return StoryParams(
        place=place_id,
        event=event_id,
        item=item_id,
        temptation=temptation_id,
        friend_trait=friend_trait,
        hero_name=hero_name,
        hero_gender=hero_gender,
        friend_name=friend_name,
        friend_gender=friend_gender,
        adult_type=adult_type,
        delay=delay,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"(Unknown place: {params.place})")
    if params.event not in EVENTS:
        raise StoryError(f"(Unknown event: {params.event})")
    if params.item not in ITEMS:
        raise StoryError(f"(Unknown item: {params.item})")
    if params.temptation not in TEMPTATIONS:
        raise StoryError(f"(Unknown temptation: {params.temptation})")
    if params.friend_trait not in FRIEND_TRAITS:
        raise StoryError(f"(Unknown friend trait: {params.friend_trait})")
    if not combo_valid(params.place, params.event, params.item, params.temptation):
        raise StoryError(explain_rejection(params.place, params.event, params.item, params.temptation))

    world = tell(
        place=PLACES[params.place],
        event=EVENTS[params.event],
        item_cfg=ITEMS[params.item],
        temptation=TEMPTATIONS[params.temptation],
        friend_trait=FRIEND_TRAITS[params.friend_trait],
        hero_name=params.hero_name,
        hero_gender=params.hero_gender,
        friend_name=params.friend_name,
        friend_gender=params.friend_gender,
        adult_type=params.adult_type,
        delay=params.delay,
    )

    # patch display labels for child-facing prose and QA
    world.facts["hero"].label = params.hero_name
    world.facts["friend"].label = params.friend_name

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
        print(f"{len(combos)} compatible (place, event, item, temptation) combos:\n")
        for place, event, item, temptation in combos:
            print(f"  {place:11} {event:7} {item:16} {temptation}")
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
            header = (
                f"### {sample.params.hero_name}: {sample.params.event} at {sample.params.place} "
                f"({sample.params.item}, {outcome_of(sample.params)})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
